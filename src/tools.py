import asyncio
import json
import re
from asyncio import Semaphore
from io import BytesIO
from pathlib import Path
from typing import Any

import fitz
from fitz import Document
from langchain.tools import BaseTool, tool
from langchain_core.output_parsers import JsonOutputParser
from PIL import Image
from pypdf import PdfReader

from prompts import STRUCTURE_QUESTION_PROMPT
from utils import load_google_generative_ai_model

RE_QUESTION_SPLIT = re.compile(r"(QUESTÃO\s+\d+)")
RE_NORMALIZE_Q = re.compile(r"(\d+)")


def _count_img_occurrences(doc: Document) -> dict[int, int]:
    """
    Count occurrences of each image in the PDF document.
    Args:
        doc (Document): The PDF document.
    Returns:
        dict[int, int]: A dictionary mapping image xref to its
        occurrence count.
    """
    image_counts = {}

    for page in doc.pages():
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]

            image_counts[xref] = image_counts.get(xref, 0) + 1
    return image_counts


def _img_passes_filters(  # noqa: PLR0913
    image: Image.Image,
    image_bytes: bytes,
    xref: int,
    image_counts: dict[int, int],
    min_width: int = 300,
    min_height: int = 300,
    min_size_bytes: int = 10240,
    max_repetitions: int = 1,
    min_unique_colors: int = 50,
) -> bool:
    """Check if an image passes the defined filters."""
    if image_counts[xref] > max_repetitions:
        return False

    if len(image_bytes) < min_size_bytes:
        return False

    width, height = image.size
    if width < min_width or height < min_height:
        return False

    aspcet_ratio = width / height
    max_aspect_ratio = 4.0
    min_aspect_ratio = 0.25
    if aspcet_ratio > max_aspect_ratio or aspcet_ratio < min_aspect_ratio:
        return False

    image_rgb = image.convert("RGB")
    colors = image_rgb.getcolors(maxcolors=10000)
    if colors and len(colors) < min_unique_colors:
        return False

    return not (image.mode == "P" and "transparency" in image.info)


def _save_image(
    image_bytes: bytes,
    page_num: int,
    xref: int,
    ext: str,
    output_path: Path,
) -> None:
    """Save image in the specified output path."""
    img_name = f"page_{page_num + 1}_img_{xref}.{ext}"
    out_path = output_path / img_name
    with out_path.open("wb") as f:
        f.write(image_bytes)


def _pdf_extract_text_impl(
    pdf_path: Path,
    start_page: int | None = None,
    end_page: int | None = None,
) -> str:
    """
    Extract and returns text from a PDF file between start_page and end_page.
    Returns the extracted text as a string containing the text of each page
    separated by line breaks and identified by the page number.
    Args:
        pdf_path (Path): Path to the PDF file.
        start_page (int): Initial page (inclusive).
        end_page (int): End page (exclusive).
    Returns:
        str: Extracted text from the PDF.
    """
    text = ""

    with fitz.open(pdf_path) as pdf:
        total_pages = pdf.page_count

        start: int = 0 if start_page is None or start_page < 0 else start_page

        end: int = (
            total_pages
            if end_page is None or end_page > total_pages
            else end_page
        )

        if start >= end:
            return ""

        for page_num in range(start, end):
            page = pdf[page_num]
            page_text = page.get_text()
            text += f"\n\n --- Page {page_num + 1} --- \n\n{page_text}"

    return text


@tool
async def pdf_extract_jpegs(
    pdf_path: Path,
    output_dir: Path = Path("output_images"),
    start_page: int | None = None,
    end_page: int | None = None,
) -> str:
    """
    Extracts JPEG images from a PDF file and saves them to a specified
    directory.

    Args:
        pdf_path (Path): Path to the PDF file.
        output_dir (Path): Path to the output directory.
        start_page (int): Initial page (inclusive).
        end_page (int): End page (exclusive).

    Returns:
        str: Message indicating the number of images extracted and the output
        directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    def _extract() -> int:
        with pdf_path.open("rb") as pdf:
            reader = PdfReader(pdf)
            total_pages = len(reader.pages)

            start: int = (
                0 if start_page is None or start_page < 0 else start_page
            )

            end: int = (
                total_pages
                if end_page is None or end_page > total_pages
                else end_page
            )

            saved = 0
            for page_index in range(start, end):
                page = reader.pages[page_index]
                for image_file_object in page.images:
                    if image_file_object.name.find(".png") == -1:
                        img_name = (
                            f"page_{page_index+1}_{image_file_object.name}"
                        )

                        out_path = output_dir / img_name
                        with out_path.open("wb") as fp:
                            fp.write(image_file_object.data)
                        saved += 1
            return saved

    saved = await asyncio.to_thread(_extract)

    if saved == 0:
        return "No JPEG images found in the specified page range."
    return f"{saved} JPEG images saved in '{output_dir.resolve()}'"


@tool
async def extract_images_from_pdf(
    pdf_path: Path,
    output_dir: Path,
) -> str:
    """
    Extracts images from a PDF file and saves them to a specified directory.

    Args:
        pdf_path (Path): Path to the PDF file.
        output_dir (Path): Path to the output directory.

    Returns:
        str: Message indicating the number of images extracted and the output
        directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    def _extract() -> int:
        doc = fitz.open(pdf_path)
        image_counts = _count_img_occurrences(doc)
        saved = 0

        for i, page in enumerate(doc.pages()):
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                try:
                    image = Image.open(BytesIO(image_bytes))

                    if _img_passes_filters(
                        image,
                        image_bytes,
                        xref,
                        image_counts,
                    ):
                        _save_image(
                            image_bytes,
                            i,
                            xref,
                            base_image["ext"],
                            output_dir,
                        )
                    saved += 1
                except Exception as e:
                    print(f"Error processing the xref {xref}: {e}")
        return saved

    saved = await asyncio.to_thread(_extract)

    if saved == 0:
        return "No JPEG images found in the specified page range."
    return f"{saved} JPEG images saved in '{output_dir.resolve()}'"


@tool
def extract_exam_pdf_text(
    exam_pdf_path: Path,
    answer_key_pdf_path: Path,
    exam_start_page: int | None = None,
    exam_end_page: int | None = None,
) -> str:
    """
    Extracts text from an exam PDF and an answer key PDF, saving it to a
    temporary .txt file. Returns the path to this temporary file. The
    resulting file path should be used as input for structure_questions.

    Args:
        exam_pdf_path (Path): Path to the exam PDF file.
        answer_key_pdf_path (Path): Path to the answer key PDF file.
        start_page (int): Initial page (inclusive).
        end_page (int): End page (exclusive).

    Returns:
        str: Path to the temporary .txt file containing the extracted text.
    """

    exam_text = _pdf_extract_text_impl(
        exam_pdf_path, start_page=exam_start_page, end_page=exam_end_page
    )

    if answer_key_pdf_path.exists():
        answer_key_text = _pdf_extract_text_impl(pdf_path=answer_key_pdf_path)
        exam_text += "\n\n--- Answer Key ---\n\n" + answer_key_text

    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / "extracted_text.txt"

    with temp_file.open("w", encoding="utf-8") as f:
        f.write(exam_text)

    return str(temp_file)


def _chunk_by_questions(text: str) -> list[str]:
    """
    Split the exam text into chunks based on question delimiters.
    Args:
        text (str): The full exam text.
    Returns:
        list[str]: A list of question chunks.
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


@tool
async def structure_questions(extracted_text_path: str) -> str:
    """
    Receive a string that is the path to the .txt file generated by the
    extract_exam_pdf_text tool. Use the content of this file for extracting
    the questions in JSON format.
    This tool MUST NOT be used with any other text.

    Args:
        extracted_text_path (str): Path to the .txt file generated by the
        extract_exam_pdf_text tool.
    Returns:
        str: Message indicating success and the path to the saved JSON file.
    """
    extracted_text = await asyncio.to_thread(
        Path(extracted_text_path).read_text, encoding="utf-8"
    )

    parts = extracted_text.split("\n\n--- Answer Key ---\n\n", 1)
    exam_text = parts[0]
    answer_key_text = parts[1] if parts[1] else "No answer key found."

    question_chunks = _chunk_by_questions(exam_text)

    llm = load_google_generative_ai_model(
        model_name="gemini-2.5-flash", temperature=0
    )

    parser = JsonOutputParser()
    semaphore = Semaphore(30)

    async def _process_chunk(
        chunk: str,
        answer_key_text: str = answer_key_text,
    ) -> dict[str, Any] | None:
        if "QUESTÃO" not in chunk:
            return None

        prompt = STRUCTURE_QUESTION_PROMPT.format(
            chunk=chunk, answer_key_text=answer_key_text
        )

        async with semaphore:
            try:
                # await asyncio.sleep(0.1)
                response = await llm.ainvoke(prompt)
                content = response.content

                if not isinstance(content, str):
                    content = str(content)

                return parser.invoke(content)
            except Exception as e:
                print(f"Error processing chunk: {e}")
                return None

    results = await asyncio.gather(
        *[_process_chunk(chunk) for chunk in question_chunks]
    )

    valid_results = [res for res in results if res is not None]

    final_data = []
    for res in valid_results:
        if isinstance(res, list):
            final_data.extend(res)
        else:
            final_data.append(res)

    for question in final_data:
        has_url = any(
            "http" in str(source) for source in question.get("sources", [])
        )
        is_text_empty = not question.get("passage_text", "").strip()

        if has_url and is_text_empty:
            question["image"] = True

    output_path = Path("src/final_output.json")

    def _save_json() -> None:
        output_path.parent.mkdir(exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)

    await asyncio.to_thread(_save_json)

    return f"Successfully extracted {len(final_data)} questions\
          and saved to {output_path}"


TOOLS: list[BaseTool] = [
    pdf_extract_jpegs,
    extract_images_from_pdf,
    extract_exam_pdf_text,
    structure_questions,
]
TOOLS_BY_NAME: dict[str, BaseTool] = {tool.name: tool for tool in TOOLS}
