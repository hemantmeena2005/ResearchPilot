import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow():
    return datetime.now(UTC)


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    title = Column(String(512), nullable=True)
    authors = Column(Text, nullable=True)  # JSON or comma-separated
    publication_year = Column(Integer, nullable=True)
    status = Column(String(50), default="processing")  # processing, indexed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    chunks = relationship("ChunkModel", back_populates="document", cascade="all, delete-orphan")


class ChunkModel(Base):
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    section_name = Column(String(255), nullable=True)
    faiss_position = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    document = relationship("DocumentModel", back_populates="chunks")


class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), default="New Research Session")
    selected_doc_ids = Column(JSON, default=list)  # list of doc UUIDs
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    query_category = Column(String(50), nullable=True)
    citations = Column(JSON, default=list)  # list of validated citation objects
    latency_ms = Column(Float, nullable=True)
    token_usage = Column(JSON, nullable=True)
    is_evidence_sufficient = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("ConversationModel", back_populates="messages")


class EvaluationRecordModel(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_name = Column(String(100), nullable=False)
    retrieval_mode = Column(String(50), nullable=False)  # vector_only, hybrid, hybrid_rerank
    question = Column(Text, nullable=False)
    ground_truth_doc_ids = Column(JSON, default=list)
    retrieved_chunk_ids = Column(JSON, default=list)
    recall_at_k = Column(Float, default=0.0)
    mrr = Column(Float, default=0.0)
    citation_correctness = Column(Float, default=0.0)
    faithfulness_score = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    token_usage = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
