import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services import intelligence_service, rag_pipeline
from app.db.session import get_db
from app.models.entities import ChunkModel, ConversationModel, DocumentModel, MessageModel
from app.schemas.research import (
    GapAnalysisRequest,
    GapAnalysisResponse,
    PaperCompareRequest,
    PaperCompareResponse,
    PaperSummaryRequest,
    PaperSummaryResponse,
    ResearchQueryRequest,
    ResearchQueryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["research"])


@router.post("/query", response_model=ResearchQueryResponse)
async def query_research(
    req: ResearchQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run evidence-grounded research query with hybrid retrieval, reranking, and citation validation."""
    response = rag_pipeline.run(
        query=req.query,
        document_ids=req.document_ids,
        retrieval_mode=req.retrieval_mode or "hybrid_rerank",
        top_k=req.top_k or 8,
        conversation_id=req.conversation_id,
    )

    # Persist message to conversation if conversation_id is provided
    if req.conversation_id:
        conv_res = await db.execute(
            select(ConversationModel).where(ConversationModel.id == req.conversation_id)
        )
        conv = conv_res.scalar_one_or_none()
        if conv:
            # Save user message
            user_msg = MessageModel(
                conversation_id=conv.id,
                role="user",
                content=req.query,
                query_category=response.query_category,
            )
            # Save assistant message
            asst_msg = MessageModel(
                conversation_id=conv.id,
                role="assistant",
                content=response.answer,
                query_category=response.query_category,
                citations=[c.model_dump() for c in response.citations],
                latency_ms=response.latency_ms,
                token_usage=response.token_usage,
                is_evidence_sufficient=response.is_evidence_sufficient,
            )
            db.add_all([user_msg, asst_msg])
            await db.commit()

    return response


@router.post("/compare", response_model=PaperCompareResponse)
async def compare_papers(
    req: PaperCompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """Multi-paper structured comparison across methods, datasets, results, and limitations."""
    papers_data = []
    for doc_id in req.document_ids:
        doc_res = await db.execute(select(DocumentModel).where(DocumentModel.id == doc_id))
        doc = doc_res.scalar_one_or_none()
        if not doc:
            continue

        chunks_res = await db.execute(
            select(ChunkModel).where(ChunkModel.document_id == doc_id).order_by(ChunkModel.chunk_index.asc())
        )
        chunks = chunks_res.scalars().all()

        papers_data.append({
            "document_id": doc.id,
            "title": doc.title,
            "original_filename": doc.original_filename,
            "publication_year": doc.publication_year,
            "chunks": [{"page_number": c.page_number, "content": c.content} for c in chunks],
        })

    if len(papers_data) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 valid uploaded papers are required for comparison.",
        )

    return intelligence_service.compare_papers(papers_data, req.focus_aspects)


@router.post("/summarize", response_model=PaperSummaryResponse)
async def summarize_paper(
    req: PaperSummaryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate structured summary distinguishing author-acknowledged vs inferred limitations."""
    doc_res = await db.execute(select(DocumentModel).where(DocumentModel.id == req.document_id))
    doc = doc_res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    chunks_res = await db.execute(
        select(ChunkModel).where(ChunkModel.document_id == req.document_id).order_by(ChunkModel.chunk_index.asc())
    )
    chunks = chunks_res.scalars().all()

    paper_data = {
        "document_id": doc.id,
        "title": doc.title,
        "original_filename": doc.original_filename,
        "chunks": [{"page_number": c.page_number, "content": c.content} for c in chunks],
    }

    return intelligence_service.summarize_paper(paper_data)


@router.post("/gap-analysis", response_model=GapAnalysisResponse)
async def analyze_research_gaps(
    req: GapAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze research gaps, unexplored hypotheses, and methodology caveats across papers."""
    papers_data = []
    for doc_id in req.document_ids:
        doc_res = await db.execute(select(DocumentModel).where(DocumentModel.id == doc_id))
        doc = doc_res.scalar_one_or_none()
        if not doc:
            continue

        chunks_res = await db.execute(
            select(ChunkModel).where(ChunkModel.document_id == doc_id).order_by(ChunkModel.chunk_index.asc())
        )
        chunks = chunks_res.scalars().all()
        papers_data.append({
            "document_id": doc.id,
            "title": doc.title,
            "original_filename": doc.original_filename,
            "chunks": [{"page_number": c.page_number, "content": c.content} for c in chunks],
        })

    if not papers_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid indexed documents must be selected for gap analysis.",
        )

    return intelligence_service.analyze_gaps(papers_data)
