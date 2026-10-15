import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services import benchmark_evaluator
from app.db.session import get_db
from app.models.entities import DocumentModel
from app.schemas.research import EvaluationSummaryResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/summary", response_model=EvaluationSummaryResponse)
async def get_evaluation_summary(db: AsyncSession = Depends(get_db)):
    """Run/retrieve empirical evaluation benchmark comparing Vector-Only, Hybrid, and Hybrid+Reranker."""
    # Fetch all active documents to formulate test cases
    docs_res = await db.execute(select(DocumentModel).where(DocumentModel.status == "indexed"))
    docs = docs_res.scalars().all()

    # Built-in academic research benchmark questions
    benchmark_dataset = [
        {
            "question": "What is the primary methodology and model architecture proposed?",
            "expected_doc_ids": [d.id for d in docs],
            "expected_keywords": ["method", "model", "architecture", "algorithm", "proposed"],
        },
        {
            "question": "What datasets and evaluation metrics are used in the experiments?",
            "expected_doc_ids": [d.id for d in docs],
            "expected_keywords": ["dataset", "metric", "accuracy", "benchmark", "evaluation", "results"],
        },
        {
            "question": "What are the explicitly acknowledged limitations or failure modes?",
            "expected_doc_ids": [d.id for d in docs],
            "expected_keywords": ["limitation", "constraint", "future", "failure", "computation"],
        },
    ]

    eval_result = benchmark_evaluator.evaluate_dataset(
        test_cases=benchmark_dataset,
        modes=["vector_only", "hybrid", "hybrid_rerank"],
        k=5,
    )

    by_mode = eval_result["results_by_mode"]
    return EvaluationSummaryResponse(
        total_evaluations=eval_result["total_evaluations"],
        modes_evaluated=eval_result["modes_evaluated"],
        mean_recall_at_k={m: by_mode[m]["mean_recall_at_k"] for m in by_mode},
        mean_mrr={m: by_mode[m]["mean_mrr"] for m in by_mode},
        mean_citation_correctness={m: by_mode[m]["mean_citation_correctness"] for m in by_mode},
        mean_faithfulness={m: by_mode[m]["mean_faithfulness"] for m in by_mode},
        mean_latency_ms={m: by_mode[m]["mean_latency_ms"] for m in by_mode},
        experiments=eval_result["experiments"],
    )
