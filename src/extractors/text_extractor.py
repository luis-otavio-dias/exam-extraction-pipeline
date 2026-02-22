"""Text extraction module for PDF files.

This module provides functionality to extract text from PDF files
with page range support and normalization.
"""

from pathlib import Path
from typing import cast

import fitz


class PDFTextExtractor:
    """Handles PDF text extraction with page range support."""

    @staticmethod
    def normalize_page_range(
        start_page: int | None,
        end_page: int | None,
        total_pages: int,
    ) -> tuple[int, int]:
        """Normalize and validate page range.

        Args:
            start_page: Starting page (inclusive, 0-indexed)
            end_page: Ending page (exclusive, 0-indexed)
            total_pages: Total number of pages in document

        Returns:
            Tuple of (start, end) normalized to valid range
        """
        start = 0 if start_page is None or start_page < 0 else start_page
        end = (
            total_pages
            if end_page is None or end_page > total_pages
            else end_page
        )

        # Ensure start doesn't exceed end
        if start >= end:
            return 0, 0

        return start, end

    def extract_text(
        self,
        pdf_path: Path,
        start_page: int | None = None,
        end_page: int | None = None,
        page_marker: str | None = "\n\n --- Page {page_num} --- \n\n",
    ) -> str:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            start_page: Starting page (inclusive, 0-indexed)
            end_page: Ending page (exclusive, 0-indexed)

        Returns:
            Extracted text with page markers
        """
        if not pdf_path.exists():
            msg = f"PDF file not found: {pdf_path}"
            raise FileNotFoundError(msg)

        if pdf_path.suffix.lower() != ".pdf":
            msg = f"Not a PDF file: {pdf_path}"
            raise ValueError(msg)

        text = ""

        with fitz.open(pdf_path) as pdf:
            total_pages = pdf.page_count
            start, end = self.normalize_page_range(
                start_page, end_page, total_pages
            )

            if start >= end:
                return ""

            for page_num in range(start, end):
                page = pdf[page_num]
                page_text = cast("str", page.get_text())

                if page_marker is not None:
                    formatted_marker = page_marker.format(
                        page_num=page_num + 1
                    )
                    text += f"{formatted_marker} {page_text}"
                else:
                    text += page_text

        return text
