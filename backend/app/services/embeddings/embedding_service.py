import logging
from typing import Any

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Zero-PyTorch cloud embedding service using Pinecone Serverless Inference API.
    Falls back gracefully to lightweight local SentenceTransformer if Pinecone is not configured.
    """
    _instance = None
    _pc = None
    _local_model = None
    _dimension = 1024  # Default for multilingual-e5-large on Pinecone

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_client(self):
        if self._pc is None and settings.PINECONE_API_KEY:
            try:
                from pinecone import Pinecone
                self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                self._dimension = 1024
                logger.info(f"Initialized Pinecone Inference EmbeddingService with model: {settings.PINECONE_EMBED_MODEL}")
            except Exception as e:
                logger.warning(f"Could not initialize Pinecone client ({e}).")

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """Generate normalized embeddings for text list using Pinecone Inference API."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        self._ensure_client()

        # Primary: High-speed Cloud Inference via Pinecone (0 MB local RAM usage)
        if self._pc is not None:
            try:
                all_embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    res = self._pc.inference.embed(
                        model=settings.PINECONE_EMBED_MODEL,
                        inputs=batch,
                        parameters={"input_type": "passage", "truncate": "END"},
                    )
                    for item in res:
                        all_embeddings.append(item.values)
                arr = np.array(all_embeddings, dtype=np.float32)
                # Normalize vectors for cosine similarity
                norms = np.linalg.norm(arr, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                return arr / norms
            except Exception as e:
                logger.error(f"Pinecone inference embed failed ({e}), attempting local fallback...")

        # Fallback: Local SentenceTransformer if available
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(settings.EMBEDDING_MODEL, device=settings.DEVICE)
            self._dimension = self._local_model.get_sentence_embedding_dimension()

        embeddings = self._local_model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string using query input type."""
        self._ensure_client()
        if self._pc is not None:
            try:
                res = self._pc.inference.embed(
                    model=settings.PINECONE_EMBED_MODEL,
                    inputs=[query],
                    parameters={"input_type": "query", "truncate": "END"},
                )
                vec = np.array(res[0].values, dtype=np.float32)
                norm = np.linalg.norm(vec)
                return vec / norm if norm > 0 else vec
            except Exception as e:
                logger.error(f"Pinecone query embed failed ({e}), falling back...")

        return self.embed_texts([query])[0]
