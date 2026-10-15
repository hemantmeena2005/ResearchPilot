import logging
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.services import bm25_retriever, embedding_service, faiss_manager
from app.db.session import get_db
from app.models.entities import ChunkModel, DocumentModel
from app.schemas.research import ChunkResponse, DocumentResponse
from app.services.documents.chunker import TextChunker
from app.services.documents.pdf_parser import PDFParser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

chunker = TextChunker(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)


async def sync_bm25(db: AsyncSession):
    """Sync all chunks to BM25 retriever corpus."""
    result = await db.execute(
        select(ChunkModel, DocumentModel.title, DocumentModel.original_filename)
        .join(DocumentModel, ChunkModel.document_id == DocumentModel.id)
    )
    rows = result.all()
    all_chunks = []
    for chunk, doc_title, orig_fn in rows:
        all_chunks.append({
            "id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "content": chunk.content,
            "document_title": doc_title or orig_fn,
            "filename": orig_fn,
        })
    bm25_retriever.update_corpus(all_chunks)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload and index a scientific PDF paper."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF files (.pdf) are permitted.",
        )

    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB}MB.",
        )

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}.pdf"
    stored_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create document database record
    doc_record = DocumentModel(
        id=doc_id,
        filename=safe_filename,
        original_filename=file.filename,
        file_path=stored_path,
        file_size_bytes=file_size,
        status="processing",
    )
    db.add(doc_record)
    await db.commit()
    await db.refresh(doc_record)

    # Process PDF and extract text
    try:
        parsed_data = PDFParser.parse_pdf(stored_path)
        meta = parsed_data["metadata"]
        doc_record.title = meta["title"]
        doc_record.authors = meta["authors"]
        doc_record.publication_year = meta["publication_year"]
        doc_record.page_count = parsed_data["page_count"]

        # Chunk document text
        chunks_data = chunker.chunk_document(doc_id, parsed_data["pages"])
        if not chunks_data:
            raise ValueError("No text passages could be extracted from document.")

        doc_record.chunk_count = len(chunks_data)

        # Generate local embeddings
        chunk_texts = [c["content"] for c in chunks_data]
        embeddings = embedding_service.embed_texts(chunk_texts)

        # Add to FAISS Vector Index
        meta_items = [
            {
                "id": c["id"],
                "document_id": doc_id,
                "document_title": doc_record.title,
                "filename": doc_record.original_filename,
                "page_number": c["page_number"],
                "chunk_index": c["chunk_index"],
                "content": c["content"],
                "section_name": c["section_name"],
            }
            for c in chunks_data
        ]
        assigned_positions = faiss_manager.add_vectors(embeddings, meta_items)

        # Save chunks into SQLite
        chunk_models = []
        for c, pos in zip(chunks_data, assigned_positions):
            chunk_models.append(
                ChunkModel(
                    id=c["id"],
                    document_id=doc_id,
                    chunk_index=c["chunk_index"],
                    page_number=c["page_number"],
                    content=c["content"],
                    token_count=c["token_count"],
                    section_name=c["section_name"],
                    faiss_position=pos,
                )
            )
        db.add_all(chunk_models)
        doc_record.status = "indexed"
        await db.commit()
        await db.refresh(doc_record)

        # Update BM25 retriever corpus
        await sync_bm25(db)

        return doc_record

    except Exception as e:
        logger.error(f"Error processing PDF {file.filename}: {e}")
        doc_record.status = "failed"
        doc_record.error_message = str(e)
        await db.commit()
        await db.refresh(doc_record)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process research document: {e!s}",
        )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all research documents."""
    result = await db.execute(select(DocumentModel).order_by(DocumentModel.created_at.desc()))
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Get single document details."""
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
async def get_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all chunks and page numbers for a document."""
    result = await db.execute(
        select(ChunkModel).where(ChunkModel.document_id == document_id).order_by(ChunkModel.chunk_index.asc())
    )
    return result.scalars().all()


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a document, its database records, uploaded PDF, and FAISS vector index entries."""
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Delete physical file
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Failed to remove physical file: {e}")

    # Remove from FAISS index
    faiss_manager.remove_document(document_id)

    # Delete from database
    await db.delete(doc)
    await db.commit()

    # Re-sync BM25 corpus
    await sync_bm25(db)
