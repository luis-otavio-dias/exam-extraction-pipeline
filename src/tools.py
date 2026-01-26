"""Define custom LangChain tools for PDF extraction and question structuring.

This module provides tools to extract images and text from PDF files,
and to structure questions using a Large Language Model (LLM).
"""

import asyncio
import json
import re
from asyncio import Semaphore
from pathlib import Path
from typing import Any

from langchain.tools import BaseTool, tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from config import CONFIG
from extractors import PDFImageExtractor, PDFTextExtractor
from prompts import STRUCTURE_QUESTION_PROMPT
from utils import (
    async_read_text,
    async_write_json,
    load_google_generative_ai_model,
)

# Compiled regex patterns from config
RE_QUESTION_SPLIT = re.compile(CONFIG.question.question_split_pattern)
RE_NORMALIZE_Q = re.compile(CONFIG.question.normalize_pattern)


def _chunk_by_questions(text: str) -> list[str]:
    """Split the exam text into chunks based on question delimiters.

    Args:
        text: The full exam text.

    Returns:
        A list of question chunks.
    """
    parts = RE_QUESTION_SPLIT.split(text)
    chunks: list[str] = []

    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            header = parts[i]
            content = parts[i + 1]
            clean_content = re.sub(r"\n{3,}", "\n\n", content.strip())
            chunks.append(f"{header}\n{clean_content}")
    return chunks


async def _process_question_chunk(
    chunk: str,
    answer_key_text: str,
    llm: BaseChatModel,
    parser: JsonOutputParser,
    semaphore: Semaphore,
) -> dict[str, Any] | None:
    if "QUESTÃO" not in chunk:
        return None

    prompt = STRUCTURE_QUESTION_PROMPT.format(
        chunk=chunk, answer_key_text=answer_key_text
    )

    async with semaphore:
        try:
            response = await llm.ainvoke(prompt)
            content = response.content

            if not isinstance(content, str):
                content = str(content)

            return parser.invoke(content)
        except Exception as e:
            print(f"Error processing chunk: {e}")
            return None


def _attach_image_to_question(
    question: dict[str, Any],
    question_image_map: dict[str, list[str]],
) -> None:
    """Determine if the question contains image information and
    update the question data accordingly.

    Args:
        question: The dictionary to update with image info.
    """

    has_url = any(
        "http" in str(source) for source in question.get("sources", [])
    )
    is_text_empty = not question.get("passage_text", "").strip()

    if has_url and is_text_empty:
        question["image"] = True

    has_image = question.get("image", False)

    if has_image:
        for q_name, images in question_image_map.items():
            if q_name in question.get("question", ""):
                question["images"] = images
                break


@tool
async def pdf_extract_jpegs(
    pdf_path: Path,
    output_dir: Path | None = None,
    start_page: int | None = None,
    end_page: int | None = None,
) -> str:
    """Extract JPEG images from a PDF file and save them to a directory.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Path to the output directory (default: from CONFIG).
        start_page: Initial page (inclusive, 0-indexed).
        end_page: End page (exclusive, 0-indexed).

    Returns:
        Message indicating the number of images extracted.
    """
    if output_dir is None:
        output_dir = CONFIG.paths.output_dir

    extractor = PDFImageExtractor()

    def _extract() -> int:
        return extractor.extract_jpegs(
            pdf_path, output_dir, start_page, end_page
        )

    saved = await asyncio.to_thread(_extract)

    if saved == 0:
        return "No JPEG images found in the specified page range."
    return f"{saved} JPEG images saved in '{output_dir.resolve()}'"


@tool
async def extract_images_from_pdf(
    pdf_path: Path,
    output_dir: Path,
) -> str | dict[str, list[str]]:
    """Extract images from a PDF file and map them to questions.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Path to the output directory.

    Returns:
        Dictionary mapping questions to their associated image paths.
        Example: '{"QUESTÃO 01": ["QUESTÃO 01_img3.jpeg"], "QUESTÃO 02": []}'
    """
    extractor = PDFImageExtractor()

    def _extract() -> dict[str, list[str]]:
        return extractor.map_images_to_questions(pdf_path, output_dir)

    question_image_map = await asyncio.to_thread(_extract)

    total_images = sum(len(images) for images in question_image_map.values())

    if total_images == 0:
        return json.dumps(
            {"message": "No images found matching the criteria.", "data": {}}
        )

    return question_image_map


@tool
def extract_exam_pdf_text(
    exam_pdf_path: Path,
    answer_key_pdf_path: Path,
    exam_start_page: int | None = None,
    exam_end_page: int | None = None,
) -> str:
    """Extract text from an exam PDF and an answer key PDF.

    Args:
        exam_pdf_path: Path to the exam PDF file.
        answer_key_pdf_path: Path to the answer key PDF file.
        exam_start_page: Initial page (inclusive, 0-indexed).
        exam_end_page: End page (exclusive, 0-indexed).

    Returns:
        Path to the temporary .txt file containing the extracted text.
    """
    extractor = PDFTextExtractor()

    exam_text = extractor.extract_exam_text(
        exam_pdf_path,
        answer_key_pdf_path,
        exam_start_page,
        exam_end_page,
        CONFIG.question.answer_key_separator,
    )

    temp_file = CONFIG.paths.temp_text_path

    with temp_file.open("w", encoding="utf-8") as f:
        f.write(exam_text)

    return str(temp_file)


@tool
async def structure_questions(extracted_text_path: str) -> str:
    """Structure questions from extracted text using LLM.

    Receive a string that is the path to the .txt file generated by the
    extract_exam_pdf_text tool. Use the content of this file for extracting
    the questions in JSON format.
    This tool MUST NOT be used with any other text.

    Args:
        extracted_text_path: Path to the .txt file generated by
        extract_exam_pdf_text tool.

    Returns:
        Message indicating success and the path to the saved JSON file.
    """
    extracted_text = await async_read_text(Path(extracted_text_path))

    parts = extracted_text.split(CONFIG.question.answer_key_separator, 1)
    exam_text = parts[0]
    answer_key_text = parts[1] if len(parts) > 1 else "No answer key found."

    question_chunks = _chunk_by_questions(exam_text)

    llm = load_google_generative_ai_model(
        model_name=CONFIG.llm.model_name, temperature=CONFIG.llm.temperature
    )

    parser = JsonOutputParser()
    semaphore = Semaphore(CONFIG.llm.max_concurrent_requests)

    results = await asyncio.gather(
        *[
            _process_question_chunk(
                chunk, answer_key_text, llm, parser, semaphore
            )
            for chunk in question_chunks
        ]
    )

    valid_results = [res for res in results if res is not None]

    final_data = []
    for res in valid_results:
        if isinstance(res, list):
            final_data.extend(res)
        else:
            final_data.append(res)

    # Map images to questions and update final data
    extractor = PDFImageExtractor()
    question_image_map = extractor.map_images_to_questions(
        CONFIG.paths.exam_pdf_path, CONFIG.paths.extracted_images_dir
    )

    for question in final_data:
        _attach_image_to_question(question, question_image_map)

    output_path = CONFIG.paths.final_output_path

    await async_write_json(output_path, final_data)

    return (
        f"Successfully extracted {len(final_data)} questions "
        f"and saved to {output_path}"
    )


TOOLS: list[BaseTool] = [
    pdf_extract_jpegs,
    extract_images_from_pdf,
    extract_exam_pdf_text,
    structure_questions,
]
TOOLS_BY_NAME: dict[str, BaseTool] = {tool.name: tool for tool in TOOLS}
