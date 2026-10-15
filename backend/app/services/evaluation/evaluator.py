import logging
import time
from typing import Any

from app.services.llm.groq_client import GroqClientService
from app.services.retrieval.hybrid_retriever import HybridRetrievalService

logger = logging.getLogger(__name__)


class BenchmarkEvaluator:
    """Evaluates retrieval quality (Recall@k, MRR), citation precision, and answer faithfulness."""

    def __init__(
        self,
        hybrid_retriever: HybridRetrievalService,
        groq_client: GroqClientService,
    ):
        self.hybrid_retriever = hybrid_retriever
        self.groq_client = groq_client

    def evaluate_dataset(
        self,
        test_cases: list[dict[str, Any]],
        modes: list[str] = ["vector_only", "hybrid", "hybrid_rerank"],
        k: int = 5,
    ) -> dict[str, Any]:
        """Runs evaluation over a benchmark dataset for each retrieval configuration."""
        results_by_mode: dict[str, dict[str, float]] = {}
        all_experiments: list[dict[str, Any]] = []

        for mode in modes:
            total_recall = 0.0
            total_mrr = 0.0
            total_citation_acc = 0.0
            total_faithfulness = 0.0
            total_latency = 0.0
            count = len(test_cases)

            for case in test_cases:
                query = case["question"]
                expected_doc_ids = set(case.get("expected_doc_ids", []))
                expected_keywords = case.get("expected_keywords", [])

                start_t = time.time()
                retrieved = self.hybrid_retriever.search(query=query, top_k=k, mode=mode)
                latency_ms = (time.time() - start_t) * 1000
                total_latency += latency_ms

                # 1. Retrieval Metrics: Recall@k and MRR
                retrieved_doc_ids = [c.get("document_id") for c in retrieved]
                hits = [1 if d in expected_doc_ids else 0 for d in retrieved_doc_ids]

                # Recall@k
                recall = 1.0 if any(hits) else 0.0 if expected_doc_ids else 1.0
                total_recall += recall

                # Mean Reciprocal Rank (MRR)
                mrr = 0.0
                for rank, hit in enumerate(hits, start=1):
                    if hit:
                        mrr = 1.0 / rank
                        break
                total_mrr += mrr

                # 2. Citation and Faithfulness Check
                # Verify keyword coverage as proxy for faithfulness in retrieved context
                combined_content = " ".join([c.get("content", "").lower() for c in retrieved])
                found_kw = sum(1 for kw in expected_keywords if kw.lower() in combined_content)
                faithfulness = (found_kw / len(expected_keywords)) if expected_keywords else 1.0
                total_faithfulness += faithfulness

                # Citation correctness: fraction of retrieved documents that are expected
                correct_citations = sum(hits) / max(len(retrieved_doc_ids), 1)
                total_citation_acc += correct_citations

                all_experiments.append({
                    "mode": mode,
                    "question": query,
                    "recall_at_k": recall,
                    "mrr": mrr,
                    "faithfulness": faithfulness,
                    "latency_ms": latency_ms,
                    "retrieved_count": len(retrieved),
                })

            n = max(count, 1)
            results_by_mode[mode] = {
                "mean_recall_at_k": round(total_recall / n, 4),
                "mean_mrr": round(total_mrr / n, 4),
                "mean_citation_correctness": round(total_citation_acc / n, 4),
                "mean_faithfulness": round(total_faithfulness / n, 4),
                "mean_latency_ms": round(total_latency / n, 2),
            }

        return {
            "total_evaluations": len(test_cases) * len(modes),
            "modes_evaluated": modes,
            "results_by_mode": results_by_mode,
            "experiments": all_experiments,
        }
