import logging

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Local embedding service using SentenceTransformers.
    Loads lazily upon first request, runs entirely locally, and normalizes vectors for cosine similarity.
    """
    _instance = None
    _model = None
    _dimension = 384  # Default for all-MiniLM-L6-v2

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_model(self):
        if self._model is None:
            logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL} on {settings.DEVICE}...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL, device=settings.DEVICE)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded successfully. Vector dimension: {self._dimension}")

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Generate normalized embeddings for a list of text strings."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        self._ensure_model()
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string."""
        return self.embed_texts([query])[0]
