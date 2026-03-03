import asyncio
import logging
import time
from pathlib import Path

from config import CONFIG
from extractors.exam_extractor import ExamExtractor
from models.question import Exam
from processors import (
    ExamDiagnosticProcessor,
    QuestionProcessor,
    TextProcessor,
)
from utils.file_operations import async_write_json

logger = logging.getLogger(__name__)


async def run_pipeline(
    exam_pdf_path: Path,
    answer_key_pdf_path: Path | None,
    images_output_dir: Path,
    *,
    output_path: Path | None = None,
) -> Exam:
    """Run the full exam extraction pipeline.

    Args:
        exam_pdf_path: Path to the exam PDF file.
        answer_key_pdf_path: Path to the answer key PDF (or None).
        images_output_dir: Directory to store extracted images.
        output_path: If provided, write the result JSON to this path.

    Returns:
        The constructed Exam object.

    Raises:
        RuntimeError: If the exam diagnostic fails.
    """
    start = time.perf_counter()
    exam_extractor = ExamExtractor()
    text_processor = TextProcessor()
    exam_diagnostic_processor = ExamDiagnosticProcessor()

    question_processor = QuestionProcessor(
        requests_per_minute=50,
        max_concurrent_requests=30,
    )

    logger.info("Running exam diagnostic...")
    exam_metadata = await exam_diagnostic_processor.diagnose(
        prompt_path="diagnostic/v3.md",
        exam_pdf_path=exam_pdf_path,
        answer_key_pdf_path=answer_key_pdf_path,
    )

    if exam_metadata is None:
        msg = "Failed to diagnose the exam."
        raise RuntimeError(msg)

    logger.info("Starting exam processing pipeline...")

    logger.info("Extracting content from PDFs...")
    exam_data = await asyncio.to_thread(
        exam_extractor.extract_content,
        exam_pdf_path=exam_pdf_path,
        answer_key_pdf_path=answer_key_pdf_path,
        images_output_dir=images_output_dir,
    )

    logger.info("Cleaning text...")
    cleaned_exam_text = text_processor.clean_text(exam_data["text"])

    logger.info("Splitting exam into exam content and answer key...")
    exam_text, answer_key_text = question_processor.split_answer_key(
        cleaned_exam_text
    )

    logger.info("Splitting exam into question chunks...")
    question_chunks = question_processor.split_into_questions(exam_text)

    logger.info("Extracted %d question chunks.", len(question_chunks))

    logger.info("Structuring questions using LLM...")
    structured_questions = await question_processor.structure_questions(
        "structure_questions/v4.md",
        question_chunks,
        answer_key_text,
        exam_metadata,
    )

    logger.info("Attaching images to questions...")
    question_processor.attach_images_to_questions(
        structured_questions, exam_data["images_map"]
    )

    exam = Exam(
        metadata=exam_metadata,
        questions=structured_questions,
    )

    if output_path is not None:
        logger.info("Writing output to %s...", output_path)
        await async_write_json(output_path, exam.model_dump())

    end = time.perf_counter()

    logger.info("Pipeline completed in %.2f seconds.", end - start)
    logger.info(
        "Successfully processed %d questions.",
        len(structured_questions),
    )

    return exam


async def run_pipeline_cli() -> None:
    """CLI entry-point that uses the default hardcoded paths."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    await run_pipeline(
        exam_pdf_path=Path("data/prova.pdf"),
        answer_key_pdf_path=Path("data/gabarito.pdf"),
        images_output_dir=CONFIG.paths.extracted_images_dir,
        output_path=CONFIG.paths.final_output_path,
    )


if __name__ == "__main__":
    asyncio.run(run_pipeline_cli())
