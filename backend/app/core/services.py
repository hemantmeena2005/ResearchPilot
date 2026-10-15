from app.services.embeddings.embedding_service import EmbeddingService
from app.services.evaluation.evaluator import BenchmarkEvaluator
from app.services.llm.groq_client import GroqClientService
from app.services.reranking.reranker import CrossEncoderReranker
from app.services.research.intelligence import ResearchIntelligenceService
from app.services.research.rag_pipeline import RAGPipeline
from app.services.retrieval.bm25_retriever import BM25Retriever
from app.services.retrieval.faiss_manager import FAISSIndexManager
from app.services.retrieval.hybrid_retriever import HybridRetrievalService

# Single shared instances across the entire application runtime
embedding_service = EmbeddingService()
faiss_manager = FAISSIndexManager()
bm25_retriever = BM25Retriever()
reranker = CrossEncoderReranker()

hybrid_retriever = HybridRetrievalService(
    embedding_service=embedding_service,
    faiss_manager=faiss_manager,
    bm25_retriever=bm25_retriever,
    reranker=reranker,
)

groq_client = GroqClientService()
rag_pipeline = RAGPipeline(hybrid_retriever=hybrid_retriever, groq_client=groq_client)
intelligence_service = ResearchIntelligenceService(groq_client=groq_client)
benchmark_evaluator = BenchmarkEvaluator(hybrid_retriever=hybrid_retriever, groq_client=groq_client)
