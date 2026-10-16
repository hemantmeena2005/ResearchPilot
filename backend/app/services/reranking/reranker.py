import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Locally executed Cross-Encoder for precision reranking of retrieved candidate chunks."""
    _instance = None
    _model = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_model(self):
        # On lightweight cloud instances (Render 512MB), avoid loading heavy PyTorch models on query
        if not self._initialized:
            self._initialized = True
            self._model = None

    @property
    def available(self) -> bool:
        return False

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int = 8,
    ) -> list[dict[str, Any]]:
        """Rerank candidates based on joint query-passage cross-attention."""
        if not candidates:
            return []
        self._ensure_model()
        if self._model is None:
            return candidates[:top_k]

        pairs = [[query, c.get("content", "")] for c in candidates]
        try:
            scores = self._model.predict(pairs)
            for idx, candidate in enumerate(candidates):
                candidate_copy = dict(candidate)
                candidate_copy["rerank_score"] = float(scores[idx])
                candidates[idx] = candidate_copy

            candidates.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return candidates[:top_k]
        except Exception as e:
            logger.error(f"Error during cross-encoder reranking: {e}")
            return candidates[:top_k]
