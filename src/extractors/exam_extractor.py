import re
from pathlib import Path
from typing import Any, cast

import fitz
from fitz import Page

from config import CONFIG
from extractors.image_extractor import PDFImageExtractor
from extractors.text_extractor import PDFTextExtractor


class ExamExtractor:
    def __init__(self) -> None:
        self.text_extractor = PDFTextExtractor()
        self.image_extractor = PDFImageExtractor()
        self.question_pattern = re.compile(
            CONFIG.question.question_split_pattern, re.IGNORECASE
        )

    def extract_content(
        self,
        exam_pdf_path: Path,
        answer_key_pdf_path: Path,
        images_output_dir: Path,
    ) -> dict[str, Any]:
        return {
            "text": self.extract_exam_text(exam_pdf_path, answer_key_pdf_path),
            "images_map": self.map_images_to_questions(
                exam_pdf_path,
                images_output_dir,
            ),
        }

    # def extract_questions(self):
    #     questions = []
    #     for item in self.exam_data.get("questions", []):
    #         question = {
    #             "id": item.get("id"),
    #             "text": item.get("text"),
    #             "choices": item.get("choices", []),
    #             "correct_answer": item.get("correct_answer"),
    #         }
    #         questions.append(question)
    #     return questions

    # def extract_metadata(self):
    #     metadata = {
    #         "exam_title": self.exam_data.get("title"),
    #         "exam_date": self.exam_data.get("date"),
    #         "total_questions": len(self.exam_data.get("questions", [])),
    #     }
    #     return metadata

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
        image_counts = self.image_extractor.count_image_occurrences(doc)

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

                img_filename = self.image_extractor.extract_and_filter_image(
                    doc, xref, image_counts, current_question, output_dir
                )

                if (
                    img_filename
                    and img_filename not in question_map[current_question]
                ):
                    question_map[current_question].append(img_filename)

        doc.close()
        return question_map

    def extract_exam_text(
        self,
        exam_pdf_path: Path,
        answer_key_pdf_path: Path,
        exam_start_page: int | None = None,
        exam_end_page: int | None = None,
        answer_key_separator: str = "\n\n--- Answer Key ---\n\n",
    ) -> str:
        """Extract text from exam PDF and answer key PDF.

        Args:
            exam_pdf_path: Path to the exam PDF file
            answer_key_pdf_path: Path to the answer key PDF file
            exam_start_page: Starting page for exam (inclusive, 0-indexed)
            exam_end_page: Ending page for exam (exclusive, 0-indexed)
            answer_key_separator: Separator text between exam and answer key

        Returns:
            Combined text from exam and answer key
        """
        exam_text = self.text_extractor.extract_text(
            exam_pdf_path, start_page=exam_start_page, end_page=exam_end_page
        )

        if answer_key_pdf_path.exists():
            answer_key_text = self.text_extractor.extract_text(
                pdf_path=answer_key_pdf_path
            )
            exam_text += answer_key_separator + answer_key_text

        return exam_text
