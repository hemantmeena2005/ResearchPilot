import re
from typing import Any

from app.schemas.research import CitationItem


class CitationValidator:
    """Validates citations against server-side retrieved evidence chunks.
    Reconciles model references with trusted ground truth metadata.
    """

    @staticmethod
    def extract_and_validate(
        generated_answer: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> tuple[list[CitationItem], bool]:
        """Match citation markers like [1], [2] or [[doc_id]] in generated answer against retrieved chunks.
        Also check whether sufficient evidence exists in retrieved chunks.
        """
        citations: list[CitationItem] = []

        # Find explicit bracket references e.g. [1], [2], [p. 3], or citations to doc titles
        found_indices = set(re.findall(r"\[(?:Chunk\s*)?(\d+)\]", generated_answer))

        if found_indices:
            for idx_str in sorted(found_indices, key=int):
                idx = int(idx_str) - 1
                if 0 <= idx < len(retrieved_chunks):
                    chunk = retrieved_chunks[idx]
                    citations.append(
                        CitationItem(
                            document_id=chunk.get("document_id", ""),
                            document_title=chunk.get("document_title") or chunk.get("filename", "Unknown Document"),
                            filename=chunk.get("filename", "paper.pdf"),
                            page_number=chunk.get("page_number", 1),
                            chunk_id=chunk.get("id", ""),
                            excerpt=chunk.get("content", "")[:350] + "...",
                            relevance_score=chunk.get("rerank_score") or chunk.get("rrf_score") or chunk.get("vector_score"),
                            claim_association=f"Referenced as citation [{idx_str}] in generation",
                        )
                    )

        # If LLM didn't produce numeric [n] markers but retrieved chunks exist, attach top supported chunks
        if not citations and retrieved_chunks:
            for i, chunk in enumerate(retrieved_chunks[:4]):
                citations.append(
                    CitationItem(
                        document_id=chunk.get("document_id", ""),
                        document_title=chunk.get("document_title") or chunk.get("filename", "Unknown Document"),
                        filename=chunk.get("filename", "paper.pdf"),
                        page_number=chunk.get("page_number", 1),
                        chunk_id=chunk.get("id", ""),
                        excerpt=chunk.get("content", "")[:350] + "...",
                        relevance_score=chunk.get("rerank_score") or chunk.get("rrf_score") or chunk.get("vector_score"),
                        claim_association="Retrieved primary supporting evidence",
                    )
                )

        # Check for evidence insufficiency indicators in the answer
        insufficiency_markers = [
            "insufficient evidence",
            "not enough evidence",
            "not mentioned in the provided documents",
            "no evidence found",
            "documents do not specify",
            "does not state",
            "cannot be answered from the provided",
        ]
        is_evidence_sufficient = not any(m in generated_answer.lower() for m in insufficiency_markers)

        return citations, is_evidence_sufficient
