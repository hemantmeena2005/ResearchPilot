import logging
from typing import Any

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.reranking.reranker import CrossEncoderReranker
from app.services.retrieval.bm25_retriever import BM25Retriever
from app.services.retrieval.faiss_manager import FAISSIndexManager

logger = logging.getLogger(__name__)


class HybridRetrievalService:
    """Combines Vector (FAISS) and Keyword (BM25) search using Reciprocal Rank Fusion (RRF),
    followed by optional Cross-Encoder reranking.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        faiss_manager: FAISSIndexManager,
        bm25_retriever: BM25Retriever,
        reranker: CrossEncoderReranker,
    ):
        self.embedding_service = embedding_service
        self.faiss_manager = faiss_manager
        self.bm25_retriever = bm25_retriever
        self.reranker = reranker

    def search(
        self,
        query: str,
        top_k: int = 8,
        mode: str = "hybrid_rerank",  # 'vector_only', 'hybrid', 'hybrid_rerank'
        filter_document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute hybrid search pipeline."""
        if mode == "vector_only":
            return self._vector_search(query, top_k, filter_document_ids)

        # 1. Vector Search Candidates
        query_vec = self.embedding_service.embed_query(query)
        vector_results = self.faiss_manager.search(
            query_vec, top_k=top_k * 2, filter_document_ids=filter_document_ids
        )

        # 2. BM25 Keyword Search Candidates
        bm25_results = self.bm25_retriever.search(
            query, top_k=top_k * 2, filter_document_ids=filter_document_ids
        )

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF formula: Score(d) = sum(1 / (k + rank_i(d)))
        rrf_constant = 60
        fused_scores: dict[str, float] = {}
        chunk_map: dict[str, dict[str, Any]] = {}

        for rank, (meta, score) in enumerate(vector_results):
            cid = meta["id"]
            chunk_map[cid] = meta
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (rrf_constant + rank + 1))

        for rank, (meta, score) in enumerate(bm25_results):
            cid = meta["id"]
            chunk_map[cid] = meta
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (rrf_constant + rank + 1))

        # Sort combined chunks by RRF score
        sorted_chunk_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)
        fused_candidates = []
        for cid in sorted_chunk_ids:
            chunk = dict(chunk_map[cid])
            chunk["rrf_score"] = fused_scores[cid]
            fused_candidates.append(chunk)

        if mode == "hybrid":
            return fused_candidates[:top_k]

        # 4. Cross-Encoder Reranking
        if mode == "hybrid_rerank" and self.reranker.available:
            rerank_candidates = fused_candidates[: top_k * 2]
            return self.reranker.rerank(query, rerank_candidates, top_k=top_k)

        return fused_candidates[:top_k]

    def _vector_search(
        self,
        query: str,
        top_k: int,
        filter_document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        query_vec = self.embedding_service.embed_query(query)
        results = self.faiss_manager.search(
            query_vec, top_k=top_k, filter_document_ids=filter_document_ids
        )
        return [dict(meta, vector_score=score) for meta, score in results]
