"""Image extraction module for PDF files.

This module provides functionality to extract images from PDF files
with configurable quality filters and question mapping.
"""

import re
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import fitz
from fitz import Document, Page
from PIL import Image
from pypdf import PdfReader

from config import CONFIG, ImageFilterConfig


class PDFImageExtractor:
    """Handles PDF image extraction with configurable filters."""

    def __init__(self, filter_config: ImageFilterConfig | None = None) -> None:
        """Initialize the image extractor.

        Args:
            filter_config: Configuration for image quality filters.
                          If None, uses default from CONFIG.
        """
        self.filter_config = filter_config or CONFIG.image_filter
        self.question_pattern = re.compile(
            CONFIG.question.question_split_pattern, re.IGNORECASE
        )

    def count_image_occurrences(self, doc: Document) -> dict[int, int]:
        """Count occurrences of each image in the PDF document.

        Args:
            doc: The PDF document.

        Returns:
            Dictionary mapping image xref to its occurrence count.
        """
        image_counts = {}

        for page in doc.pages():
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                image_counts[xref] = image_counts.get(xref, 0) + 1

        return image_counts

    def passes_filters(
        self,
        image: Image.Image,
        image_bytes: bytes,
        xref: int,
        image_counts: dict[int, int],
    ) -> bool:
        """Check if an image passes the defined quality filters.

        Args:
            image: PIL Image object
            image_bytes: Raw image bytes
            xref: Image xref identifier
            image_counts: Dictionary of image occurrence counts

        Returns:
            True if image passes all filters, False otherwise.
        """

        if image_counts[xref] > self.filter_config.max_repetitions:
            return False

        if len(image_bytes) < self.filter_config.min_size_bytes:
            return False

        width, height = image.size
        if (
            width < self.filter_config.min_width
            or height < self.filter_config.min_height
        ):
            return False

        aspect_ratio = width / height
        if (
            aspect_ratio > self.filter_config.max_aspect_ratio
            or aspect_ratio < self.filter_config.min_aspect_ratio
        ):
            return False

        image_rgb = image.convert("RGB")
        colors = image_rgb.getcolors(maxcolors=10000)
        if colors and len(colors) < self.filter_config.min_unique_colors:
            return False

        # Check for palette mode with transparency (likely icon/logo)
        return not (image.mode == "P" and "transparency" in image.info)

    def save_image(
        self,
        image_bytes: bytes,
        output_path: Path,
        filename: str,
    ) -> None:
        """Save image to the specified output path.

        Args:
            image_bytes: Raw image bytes
            output_path: Directory to save the image
            filename: Name of the file to save
        """
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / filename
        with file_path.open("wb") as f:
            f.write(image_bytes)

    def extract_jpegs(
        self,
        pdf_path: Path,
        output_dir: Path,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> int:
        """Extract JPEG images from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images
            start_page: Starting page (inclusive, 0-indexed)
            end_page: Ending page (exclusive, 0-indexed)

        Returns:
            Number of images saved
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        with pdf_path.open("rb") as pdf:
            reader = PdfReader(pdf)
            total_pages = len(reader.pages)

            start = 0 if start_page is None or start_page < 0 else start_page
            end = (
                total_pages
                if end_page is None or end_page > total_pages
                else end_page
            )

            saved = 0
            for page_index in range(start, end):
                page = reader.pages[page_index]
                for image_file_object in page.images:
                    if ".png" not in image_file_object.name:
                        img_name = (
                            f"page_{page_index + 1}_{image_file_object.name}"
                        )
                        self.save_image(
                            image_file_object.data, output_dir, img_name
                        )
                        saved += 1

            return saved

    def extract_and_filter_image(
        self,
        doc: Document,
        xref: int,
        image_counts: dict[int, int],
        current_question: str,
        output_dir: Path,
    ) -> str | None:
        """Extract and filter a single image if it passes quality checks.

        Args:
            doc: The PDF document
            xref: Image xref identifier
            image_counts: Dictionary of image occurrence counts
            current_question: Question identifier this image belongs to
            output_dir: Directory to save the image

        Returns:
            Image filename if image was saved, None otherwise
        """
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]

        try:
            image = Image.open(BytesIO(image_bytes))

            if self.passes_filters(image, image_bytes, xref, image_counts):
                img_filename = (
                    f"{current_question}_img{xref}.{base_image['ext']}"
                )
                self.save_image(image_bytes, output_dir, img_filename)
                return img_filename

        except Exception as e:
            print(f"Error processing xref {xref}: {e}")

        return None

    def map_questions(
        self,
        question_map: dict[str, list[str]],
        page: Page,
    ) -> list[tuple[str, float]]:
        """Extract question identifiers from a PDF page and populate
        question_map.

        This method scans text blocks in the page to identify question
        patterns, extracts their names and vertical positions, and initializes
        entries in the question_map dictionary.

        Args:
            question_map: Dictionary to populate with question names as keys
            and empty lists as values. Modified in-place.
            page: The PDF page to extract questions from.

        Returns:
            List of tuples containing (question_name, y_position) sorted by
            vertical position on the page.
            Example: [('QUESTÃO 01', 120.5), ('QUESTÃO 02', 350.8)]
        """

        text_dict = cast("dict[str, Any]", page.get_text("dict"))
        text_blocks = text_dict["blocks"]
        questions = []

        for block in text_blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        match = self.question_pattern.search(span["text"])
                        if match:
                            digit_match = re.search(r"\d+", match.group(1))
                            if digit_match:
                                q_num = int(digit_match.group())
                                q_name = f"QUESTÃO {q_num:02d}"
                                questions.append((q_name, block["bbox"][1]))
                                if q_name not in question_map:
                                    question_map[q_name] = []

        questions.sort(key=lambda x: x[1])

        return questions

    def map_images_to_questions(
        self, pdf_path: Path, output_dir: Path
    ) -> dict[str, list[str]]:
        """Extract images and map them to questions based on position.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images

        Returns:
            Dictionary mapping question identifiers to image paths
            Example: {'QUESTÃO 01': ['QUESTÃO 01_img3.jpeg'], 'QUESTÃO 02': []}
        """
        doc = fitz.open(pdf_path)
        question_map = {}
        output_dir.mkdir(parents=True, exist_ok=True)
        image_counts = self.count_image_occurrences(doc)

        for page in doc.pages():
            questions = self.map_questions(question_map, page)
            if not questions:
                continue

            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                img_rects = page.get_image_rects(xref)

                if not img_rects:
                    continue

                img_y = img_rects[0].y0

                current_question = None
                for i, (q_name, q_y) in enumerate(questions):
                    if i + 1 < len(questions):
                        next_q_y = questions[i + 1][1]
                    else:
                        next_q_y = float("inf")

                    if q_y <= img_y < next_q_y:
                        current_question = q_name
                        break

                if not current_question:
                    continue

                img_filename = self.extract_and_filter_image(
                    doc, xref, image_counts, current_question, output_dir
                )

                if (
                    img_filename
                    and img_filename not in question_map[current_question]
                ):
                    question_map[current_question].append(img_filename)

        doc.close()
        return question_map
