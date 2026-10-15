from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# Document schemas
class DocumentBase(BaseModel):
    title: str | None = None
    authors: str | None = None
    publication_year: int | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    original_filename: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    page_number: int
    content: str
    token_count: int
    section_name: str | None = None


# Citation & Evidence schemas
class CitationItem(BaseModel):
    document_id: str
    document_title: str
    filename: str
    page_number: int
    chunk_id: str
    excerpt: str
    relevance_score: float | None = None
    claim_association: str | None = None


# Research query & chat schemas
class ResearchQueryRequest(BaseModel):
    query: str
    document_ids: list[str] | None = Field(default=None, description="Scope query to specific documents")
    conversation_id: str | None = None
    retrieval_mode: str | None = Field(default="hybrid_rerank", description="vector_only, hybrid, hybrid_rerank")
    top_k: int | None = 8


class ResearchQueryResponse(BaseModel):
    answer: str
    query_category: str
    citations: list[CitationItem]
    is_evidence_sufficient: bool
    latency_ms: float
    retrieval_mode: str
    rewritten_query: str | None = None
    token_usage: dict[str, int] | None = None
    conversation_id: str | None = None


# Paper Comparison schemas
class PaperCompareRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=2, max_length=10)
    focus_aspects: list[str] | None = Field(
        default=["problem", "methodology", "dataset_and_eval", "results", "limitations"]
    )


class PaperComparisonAspect(BaseModel):
    aspect: str
    comparison_summary: str
    per_paper_breakdown: dict[str, str]
    citations: list[CitationItem]


class PaperCompareResponse(BaseModel):
    title: str
    document_summaries: dict[str, str]
    aspects: list[PaperComparisonAspect]
    agreements: list[str]
    contradictions: list[str]
    open_questions: list[str]
    latency_ms: float


# Research Gap & Summarize schemas
class GapAnalysisRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1)


class ResearchGapItem(BaseModel):
    title: str
    gap_description: str
    evidence_and_rationale: str
    source_papers: list[str]
    citations: list[CitationItem]


class GapAnalysisResponse(BaseModel):
    research_directions: list[ResearchGapItem]
    methodology_caveats: list[str]
    latency_ms: float


class PaperSummaryRequest(BaseModel):
    document_id: str


class PaperSummaryResponse(BaseModel):
    document_id: str
    title: str
    problem_statement: str
    main_contribution: str
    proposed_method: str
    experimental_results: str
    author_acknowledged_limitations: list[str]
    inferred_limitations: list[str]
    future_work: list[str]
    citations: list[CitationItem]


# Conversation Schemas
class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    query_category: str | None = None
    citations: list[CitationItem] = []
    is_evidence_sufficient: bool = True
    latency_ms: float | None = None
    created_at: datetime


class ConversationCreate(BaseModel):
    title: str | None = "New Research Session"
    selected_doc_ids: list[str] | None = []


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    selected_doc_ids: list[str]
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []


# Evaluation Schemas
class EvaluationSummaryResponse(BaseModel):
    total_evaluations: int
    modes_evaluated: list[str]
    mean_recall_at_k: dict[str, float]
    mean_mrr: dict[str, float]
    mean_citation_correctness: dict[str, float]
    mean_faithfulness: dict[str, float]
    mean_latency_ms: dict[str, float]
    experiments: list[dict[str, Any]]
