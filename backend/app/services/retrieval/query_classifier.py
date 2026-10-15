from typing import Any


class QueryClassifier:
    """Classifies user queries into research-specific categories using deterministic heuristics."""

    @staticmethod
    def classify(query: str) -> dict[str, Any]:
        q = query.lower().strip()

        # Comparison
        if any(w in q for w in ["compare", "versus", "vs", "difference between", "how do they differ", "contrast"]):
            return {
                "category": "comparison",
                "needs_multi_doc": True,
                "suggested_top_k": 12,
            }

        # Limitations & Weaknesses
        if any(w in q for w in ["limitation", "drawback", "weakness", "shortcoming", "fail", "flaw", "constraint"]):
            return {
                "category": "limitation_analysis",
                "needs_multi_doc": False,
                "suggested_top_k": 8,
            }

        # Research Gaps & Future Work
        if any(w in q for w in ["future work", "research gap", "open problem", "next step", "potential direction", "unanswered"]):
            return {
                "category": "research_gap_exploration",
                "needs_multi_doc": False,
                "suggested_top_k": 8,
            }

        # Summary & Overview
        if any(w in q for w in ["summarize", "summary", "overview", "main contribution", "high level", "in simple terms"]):
            return {
                "category": "summary",
                "needs_multi_doc": False,
                "suggested_top_k": 8,
            }

        # Methodology / Implementation
        if any(w in q for w in ["method", "methodology", "architecture", "dataset", "metric", "how does it work", "algorithm"]):
            return {
                "category": "methodology",
                "needs_multi_doc": False,
                "suggested_top_k": 8,
            }

        # Multi-hop / Reasoning
        if any(w in q for w in ["why does", "what causes", "how does the result lead to", "relationship between"]):
            return {
                "category": "multi_hop_reasoning",
                "needs_multi_doc": False,
                "suggested_top_k": 10,
            }

        # Default: Factual lookup
        return {
            "category": "factual_lookup",
            "needs_multi_doc": False,
            "suggested_top_k": 6,
        }
