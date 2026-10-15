import logging
import time

from app.schemas.research import ResearchQueryResponse
from app.services.llm.groq_client import GroqClientService
from app.services.research.citation_validator import CitationValidator
from app.services.retrieval.hybrid_retriever import HybridRetrievalService
from app.services.retrieval.query_classifier import QueryClassifier

logger = logging.getLogger(__name__)


class RAGPipeline:
    """End-to-end evidence-grounded Research RAG pipeline."""

    def __init__(
        self,
        hybrid_retriever: HybridRetrievalService,
        groq_client: GroqClientService,
    ):
        self.hybrid_retriever = hybrid_retriever
        self.groq_client = groq_client

    def run(
        self,
        query: str,
        document_ids: list[str] | None = None,
        retrieval_mode: str = "hybrid_rerank",
        top_k: int = 8,
        conversation_id: str | None = None,
    ) -> ResearchQueryResponse:
        start_time = time.time()

        # 1. Query classification
        classification = QueryClassifier.classify(query)
        category = classification["category"]
        effective_top_k = max(top_k, classification.get("suggested_top_k", top_k))

        # 2. Hybrid Retrieval + Reranking
        retrieved_chunks = self.hybrid_retriever.search(
            query=query,
            top_k=effective_top_k,
            mode=retrieval_mode,
            filter_document_ids=document_ids,
        )

        # 3. Context Construction & Untrusted Content Safeguard
        context_parts = []
        for idx, chunk in enumerate(retrieved_chunks):
            doc_label = chunk.get("document_title") or chunk.get("filename", "Paper")
            page_num = chunk.get("page_number", 1)
            # Tag each chunk with a deterministic index [Chunk 1], [Chunk 2] for citation tracking
            context_parts.append(
                f"[Chunk {idx + 1}] (Document: '{doc_label}', Page {page_num}):\n{chunk.get('content', '')}"
            )

        context_str = "\n\n".join(context_parts)

        # 4. Prompt Engineering for Groundedness & Citation
        system_prompt = (
            "You are ResearchPilot, an elite scientific research assistant and peer-review analyst.\n"
            "Your objective is to provide evidence-grounded answers based EXCLUSIVELY on the provided research paper excerpts.\n\n"
            "PRESENTATION & FORMATTING GUIDELINES:\n"
            "1. STRUCTURE & HEADINGS: Use clear, prominent Markdown headings (## and ###) to organize topics logically like a top-tier research report.\n"
            "2. COMPARISON TABLES: Whenever comparing methods, performance metrics, benchmarks (e.g. PSNR, SSIM, accuracy, datasets), or papers, ALWAYS format them as a clean Markdown table with headers.\n"
            "3. KEY TAKEAWAYS: Highlight critical conclusions and insights in structured bullet points or callouts for quick readability.\n"
            "4. EVIDENCE GROUNDING: Ground every substantive claim using bracketed citation markers like [1], [2] corresponding to [Chunk 1], [Chunk 2].\n"
            "5. INSUFFICIENT EVIDENCE: If the excerpts do NOT contain sufficient information to answer the question with certainty, EXPLICITLY state: "
            "'The provided research documents contain insufficient evidence to confirm this claim.' Do not fabricate details.\n"
            "6. OBJECTIVE TONE: Distinguish established empirical facts from speculative interpretations."
        )

        user_prompt = (
            f"USER RESEARCH QUESTION:\n{query}\n\n"
            f"RETRIEVED RESEARCH CONTEXT:\n{context_str if context_str else '[No matching research excerpts found in indexed documents.]'}\n\n"
            "Please answer the question thoroughly with citations to the chunk numbers:"
        )

        # 5. Groq LLM Generation
        generation_res = self.groq_client.generate_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.15,
        )

        generated_text = generation_res.get("content", "")
        latency_ms = (time.time() - start_time) * 1000

        # 6. Citation Validation and Grounding Verification
        citations, is_evidence_sufficient = CitationValidator.extract_and_validate(
            generated_text, retrieved_chunks
        )

        return ResearchQueryResponse(
            answer=generated_text,
            query_category=category,
            citations=citations,
            is_evidence_sufficient=is_evidence_sufficient,
            latency_ms=latency_ms,
            retrieval_mode=retrieval_mode,
            rewritten_query=None,
            token_usage=generation_res.get("token_usage"),
            conversation_id=conversation_id,
        )
