import asyncio
import time
from pathlib import Path

from rich import print

from config import CONFIG
from extractors.exam_extractor import ExamExtractor
from processors import QuestionProcessor, TextProcessor
from utils.file_operations import async_write_json


async def run_pipeline() -> None:
    start = time.perf_counter()
    exam_extractor = ExamExtractor()
    text_processor = TextProcessor()
    question_processor = QuestionProcessor(
        requests_per_minute=20,
        max_concurrent_requests=10,
    )

    output_path = CONFIG.paths.final_output_path

    exam_data = exam_extractor.extract_content(
        exam_pdf_path=Path("data/prova.pdf"),
        answer_key_pdf_path=Path("data/gabarito.pdf"),
        images_output_dir=CONFIG.paths.extracted_images_dir,
    )

    cleaned_exam_text = text_processor.clean_text(exam_data["text"])

    exam_text, answer_key_text = question_processor.split_answer_key(
        cleaned_exam_text
    )

    question_chunks = question_processor.split_into_questions(exam_text)

    structured_questions = await question_processor.structure_questions(
        "structure_questions/v3.md", question_chunks, answer_key_text
    )

    question_processor.attach_images_to_questions(
        structured_questions, exam_data["images_map"]
    )

    await async_write_json(output_path, structured_questions)
    end = time.perf_counter()

    print(f"Pipeline completed in {end - start:.2f} seconds.")
    print(f"Successfully processed {len(structured_questions)} questions.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
