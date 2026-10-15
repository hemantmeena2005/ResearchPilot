import hashlib
import re
from typing import Any


class TextChunker:
    """Configurable text chunker preserving page boundaries, sentence integrity, and deterministic IDs."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.chunk_size = chunk_size  # In words approx
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document_id: str, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chunks = []
        chunk_index = 0

        for page_data in pages:
            page_num = page_data["page_number"]
            text = page_data["text"]

            if not text.strip():
                continue

            # Split page text into sentences or paragraphs
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            sentences = []
            for p in paragraphs:
                s_list = re.split(r"(?<=[.!?])\s+", p)
                for s in s_list:
                    if s.strip():
                        sentences.append(s.strip())

            current_chunk_words: list[str] = []
            current_section = self._detect_section(text)

            for sentence in sentences:
                words = sentence.split()
                if len(current_chunk_words) + len(words) > self.chunk_size and current_chunk_words:
                    chunk_text = " ".join(current_chunk_words)
                    chunk_id = self._generate_stable_id(document_id, page_num, chunk_index, chunk_text)

                    chunks.append({
                        "id": chunk_id,
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "page_number": page_num,
                        "content": chunk_text,
                        "token_count": len(current_chunk_words),
                        "section_name": current_section,
                    })
                    chunk_index += 1

                    # Retain overlap words
                    if self.chunk_overlap > 0:
                        current_chunk_words = current_chunk_words[-self.chunk_overlap:] + words
                    else:
                        current_chunk_words = words
                else:
                    current_chunk_words.extend(words)

            if current_chunk_words:
                chunk_text = " ".join(current_chunk_words)
                chunk_id = self._generate_stable_id(document_id, page_num, chunk_index, chunk_text)
                chunks.append({
                    "id": chunk_id,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "page_number": page_num,
                    "content": chunk_text,
                    "token_count": len(current_chunk_words),
                    "section_name": current_section,
                })
                chunk_index += 1

        return chunks

    @staticmethod
    def _detect_section(text: str) -> str:
        """Heuristic detection of common academic paper sections."""
        first_lines = text[:300].upper()
        candidates = [
            "ABSTRACT",
            "INTRODUCTION",
            "RELATED WORK",
            "METHODOLOGY",
            "METHODS",
            "ARCHITECTURE",
            "EXPERIMENTS",
            "RESULTS",
            "DISCUSSION",
            "LIMITATIONS",
            "CONCLUSION",
            "FUTURE WORK",
            "REFERENCES",
        ]
        for c in candidates:
            if re.search(r"\b" + c + r"\b", first_lines):
                return c.title()
        return "Body Content"

    @staticmethod
    def _generate_stable_id(document_id: str, page_num: int, chunk_idx: int, content: str) -> str:
        """Generate a deterministic UUID-compatible hash for unchanged chunk content."""
        hasher = hashlib.sha256()
        hasher.update(f"{document_id}:{page_num}:{chunk_idx}:{content[:100]}".encode())
        digest = hasher.hexdigest()
        # Format as UUID 8-4-4-4-12
        return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"
