import logging
import re
from typing import Any

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class BM25Retriever:
    """Exact keyword retrieval service using BM25Okapi with tokenizer and doc filters."""

    def __init__(self):
        self.corpus_chunks: list[dict[str, Any]] = []
        self.tokenized_corpus: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Simple, fast lowercase alphanumeric tokenizer for research text."""
        return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())

    def update_corpus(self, chunks: list[dict[str, Any]]):
        """Re-index BM25 with updated chunks list."""
        self.corpus_chunks = chunks
        self.tokenized_corpus = [self.tokenize(c.get("content", "")) for c in chunks]
        if self.tokenized_corpus and any(len(doc) > 0 for doc in self.tokenized_corpus):
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.bm25 = None

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_document_ids: list[str] | None = None,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search BM25 keyword index and return scored chunk metadata."""
        if not self.bm25 or not self.corpus_chunks:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        scored_pairs = list(zip(self.corpus_chunks, scores))

        # Filter by document IDs if specified
        if filter_document_ids:
            doc_id_set = set(filter_document_ids)
            scored_pairs = [pair for pair in scored_pairs if pair[0].get("document_id") in doc_id_set]

        # Sort descending by BM25 score
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        # Filter zero/negative scores and limit to top_k
        results = [(meta, float(sc)) for meta, sc in scored_pairs[:top_k] if sc > 0.0]
        return results
