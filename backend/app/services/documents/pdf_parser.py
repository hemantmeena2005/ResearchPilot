import re
from typing import Any

import pymupdf as fitz


class PDFParser:
    """PDF parsing service using PyMuPDF to extract text, page numbers, and paper metadata."""

    @staticmethod
    def extract_metadata(doc: fitz.Document) -> dict[str, Any]:
        """Extract title, authors, and creation metadata from PDF document headers."""
        meta = doc.metadata or {}
        title = meta.get("title", "").strip()
        author = meta.get("author", "").strip()
        year = None

        creation_date = meta.get("creationDate", "")
        if creation_date:
            match = re.search(r"D:(\d{4})", creation_date)
            if match:
                try:
                    year = int(match.group(1))
                except ValueError:
                    pass

        # If title is empty or generic, attempt to extract from the first page text
        if not title and len(doc) > 0:
            first_page_text = doc[0].get_text("text").strip()
            lines = [line.strip() for line in first_page_text.split("\n") if len(line.strip()) > 3]
            if lines:
                title = lines[0][:200]

        return {
            "title": title or "Untitled Research Document",
            "authors": author or "Unknown Authors",
            "publication_year": year,
        }

    @classmethod
    def parse_pdf(cls, file_path: str) -> dict[str, Any]:
        """Parse PDF file into page-level text items with robust error detection."""
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Corrupted or invalid PDF file: {e!s}")

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise ValueError("PDF document is empty (0 pages).")

        pages = []
        total_text_len = 0

        for page_idx in range(page_count):
            page = doc[page_idx]
            text = page.get_text("text")
            cleaned_text = cls.clean_text(text)
            total_text_len += len(cleaned_text)

            pages.append({
                "page_number": page_idx + 1,
                "text": cleaned_text,
            })

        metadata = cls.extract_metadata(doc)
        doc.close()

        # Handle image-only or scanned PDFs gracefully
        if total_text_len < 50:
            raise ValueError(
                "PDF contains insufficient extractable text. It may be a scanned or image-only document. "
                "OCR is not enabled for this file."
            )

        return {
            "metadata": metadata,
            "page_count": page_count,
            "pages": pages,
        }

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize line breaks, hyphenated line wraps, and multiple spaces."""
        if not text:
            return ""
        # Remove hyphenated linebreaks (e.g., 'trans- \nformer' -> 'transformer')
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
        # Normalize whitespace while preserving paragraphs
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return "\n".join(lines).strip()
