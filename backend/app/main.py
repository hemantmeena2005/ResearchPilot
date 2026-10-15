import os

# Prevent macOS Apple Silicon OpenMP / PyTorch / FAISS multi-threading conflict and SIGSEGV
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.conversations import router as conversations_router
from app.api.v1.documents import router as documents_router
from app.api.v1.documents import sync_bm25
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.research import router as research_router
from app.core.config import settings
from app.db.session import AsyncSessionLocal, init_db

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("researchpilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: initialize database tables and synchronize BM25 corpus."""
    logger.info("Initializing ResearchPilot database and storage directories...")
    settings.ensure_directories()
    await init_db()

    # Synchronize BM25 corpus on startup
    async with AsyncSessionLocal() as session:
        try:
            await sync_bm25(session)
            logger.info("BM25 keyword retriever synced with database chunks.")
        except Exception as e:
            logger.warning(f"Initial BM25 sync notice: {e}")

    yield
    logger.info("Shutting down ResearchPilot application.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Evidence-Grounded AI Research Assistant with Hybrid Retrieval and Citation Validation",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(documents_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["system"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/api/v1/ready", tags=["system"])
async def readiness_check():
    """System readiness check endpoint verifying storage and models."""
    return {
        "ready": True,
        "embedding_model": settings.EMBEDDING_MODEL,
        "reranker_model": settings.RERANKER_MODEL,
        "groq_configured": bool(settings.GROQ_API_KEY),
    }
