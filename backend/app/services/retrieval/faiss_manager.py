import json
import logging
import os
from typing import Any

import faiss
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class FAISSIndexManager:
    """Persistent FAISS Vector Index with metadata mapping and document-level filtering."""

    def __init__(self, index_dir: str | None = None, dimension: int = 384):
        self.index_dir = index_dir or settings.INDEX_DIR
        self.dimension = dimension
        self.index_path = os.path.join(self.index_dir, "faiss.index")
        self.mapping_path = os.path.join(self.index_dir, "metadata_map.json")

        self.index: faiss.Index | None = None
        self.metadata_entries: list[dict[str, Any]] = []  # position -> chunk_metadata
        self._load_or_create()

    def _load_or_create(self):
        os.makedirs(self.index_dir, exist_ok=True)
        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            try:
                logger.info(f"Loading persistent FAISS index from {self.index_path}")
                self.index = faiss.read_index(self.index_path)
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    self.metadata_entries = json.load(f)
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors.")
                return
            except Exception as e:
                logger.error(f"Failed to read existing index: {e}. Reinitializing clean index.")

        # Inner Product on normalized vectors equals Cosine Similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata_entries = []

    def save(self):
        """Persist FAISS index and chunk metadata mapping to disk."""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.mapping_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata_entries, f, ensure_ascii=False)
            logger.info(f"Saved FAISS index ({self.index.ntotal} vectors) to {self.index_dir}")

    def add_vectors(self, embeddings: np.ndarray, chunks_metadata: list[dict[str, Any]]) -> list[int]:
        """Add batch of vectors and record position mappings."""
        if len(embeddings) == 0:
            return []

        # Adjust index dimension dynamically if needed (e.g. switching between 384 and 1024)
        embed_dim = embeddings.shape[1]
        if self.index is None or (self.index.ntotal == 0 and self.index.d != embed_dim):
            self.dimension = embed_dim
            self.index = faiss.IndexFlatIP(self.dimension)
        elif self.index.d != embed_dim:
            # Dimension changed (e.g. from local 384 to cloud 1024) - reset index for new embedding space
            logger.warning(f"Embedding dimension changed from {self.index.d} to {embed_dim}. Reinitializing FAISS index.")
            self.dimension = embed_dim
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata_entries = []

        start_pos = self.index.ntotal
        self.index.add(embeddings)
        assigned_positions = []

        for idx, meta in enumerate(chunks_metadata):
            pos = start_pos + idx
            assigned_positions.append(pos)
            meta_copy = dict(meta)
            meta_copy["faiss_position"] = pos
            self.metadata_entries.append(meta_copy)

        self.save()
        return assigned_positions

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filter_document_ids: list[str] | None = None,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search similar vectors with cosine score and optional document filtering."""
        if self.index is None or self.index.ntotal == 0:
            return []

        # If filtering is active, retrieve more candidates to ensure sufficient filtered results
        search_k = min(self.index.ntotal, top_k * 4 if filter_document_ids else top_k)
        query_arr = np.array([query_vector], dtype=np.float32)

        distances, indices = self.index.search(query_arr, search_k)
        results: list[tuple[dict[str, Any], float]] = []

        filter_set = set(filter_document_ids) if filter_document_ids else None

        for pos, score in zip(indices[0], distances[0]):
            if pos < 0 or pos >= len(self.metadata_entries):
                continue
            meta = self.metadata_entries[pos]

            # Filter out deleted documents or documents not in filter_set
            if filter_set and meta.get("document_id") not in filter_set:
                continue

            results.append((meta, float(score)))
            if len(results) >= top_k:
                break

        return results

    def remove_document(self, document_id: str):
        """Remove document chunks from index by rebuilding without the deleted document."""
        if not any(m.get("document_id") == document_id for m in self.metadata_entries):
            return

        retained_entries = []
        for meta in self.metadata_entries:
            if meta.get("document_id") != document_id:
                retained_entries.append(meta)

        # In FAISS IndexFlat, selective deletion requires rebuild for clean consistency
        self.rebuild(retained_entries)

    def rebuild(self, entries: list[dict[str, Any]], embeddings: np.ndarray | None = None):
        """Rebuild index with new entries and optional precomputed embeddings."""
        new_index = faiss.IndexFlatIP(self.dimension)
        if embeddings is not None and len(embeddings) > 0:
            new_index.add(embeddings)

        self.index = new_index
        self.metadata_entries = entries
        self.save()
