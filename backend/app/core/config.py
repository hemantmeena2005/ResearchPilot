import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App & API
    APP_NAME: str = "ResearchPilot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Groq LLM API
    GROQ_API_KEY: str = Field(default="", description="Groq API Key")
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_TIMEOUT_SECONDS: float = 45.0
    GROQ_MAX_RETRIES: int = 3

    # Storage paths
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/researchpilot.db"
    UPLOAD_DIR: str = "./data/uploads"
    INDEX_DIR: str = "./data/indexes"
    MAX_UPLOAD_MB: int = 25

    # Document Chunking
    CHUNK_SIZE: int = 600  # Words/tokens target
    CHUNK_OVERLAP: int = 80

    # Local ML Models
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    DEVICE: str = "cpu"  # 'cpu', 'cuda', or 'mps'

    # Retrieval & Evidence
    TOP_K: int = 8
    BM25_TOP_K: int = 8
    USE_HYBRID: bool = True
    USE_RERANKER: bool = True
    CONFIDENCE_THRESHOLD: float = 0.35
    CONTEXT_TOKEN_BUDGET: int = 3500

    def ensure_directories(self) -> None:
        """Create necessary data directories if they do not exist."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.INDEX_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.DATABASE_URL.replace("sqlite+aiosqlite:///", "")), exist_ok=True)


settings = Settings()
settings.ensure_directories()
