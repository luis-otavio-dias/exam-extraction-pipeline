"""Image extraction module for PDF files.

This module provides functionality to extract images from PDF files
with configurable quality filters and question mapping.
"""

import re
from io import BytesIO
from pathlib import Path

from fitz import Document
from PIL import Image

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
