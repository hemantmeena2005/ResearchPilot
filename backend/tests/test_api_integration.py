import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db, AsyncSessionLocal
from app.models.entities import DocumentModel
from sqlalchemy import select


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_health_and_ready_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        res_ready = await client.get("/api/v1/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["ready"] is True


@pytest.mark.asyncio
async def test_document_upload_and_indexing_pipeline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload sample PDF
        sample_path = "evaluation/samples/paper_dense_retrieval.pdf"
        assert os.path.exists(sample_path)

        with open(sample_path, "rb") as f:
            files = {"file": ("paper_dense_retrieval.pdf", f, "application/pdf")}
            res = await client.post("/api/v1/documents", files=files)

        assert res.status_code == 201
        doc_data = res.json()
        assert doc_data["status"] == "indexed"
        assert doc_data["page_count"] == 3
        assert doc_data["chunk_count"] > 0
        doc_id = doc_data["id"]

        # 2. Query Research RAG Pipeline
        query_payload = {
            "query": "What are the limitations acknowledged by the authors?",
            "document_ids": [doc_id],
            "retrieval_mode": "hybrid_rerank",
            "top_k": 5,
        }
        q_res = await client.post("/api/v1/research/query", json=query_payload)
        assert q_res.status_code == 200
        q_data = q_res.json()
        assert q_data["query_category"] == "limitation_analysis"
        assert len(q_data["citations"]) > 0
        assert q_data["citations"][0]["document_id"] == doc_id

        # 3. Paper Summary
        sum_res = await client.post("/api/v1/research/summarize", json={"document_id": doc_id})
        assert sum_res.status_code == 200
        assert "document_id" in sum_res.json()

        # 4. Evaluation Benchmark
        eval_res = await client.get("/api/v1/evaluation/summary")
        assert eval_res.status_code == 200
        assert "mean_recall_at_k" in eval_res.json()
