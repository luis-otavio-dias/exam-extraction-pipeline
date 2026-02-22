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
        requests_per_minute=50,
        max_concurrent_requests=30,
    )

    output_path = CONFIG.paths.final_output_path

    print("[bold green]Starting exam processing pipeline...[/bold green]\n")

    print("[bold blue]Extracting content from PDFs...[/bold blue]\n")
    exam_data = exam_extractor.extract_content(
        exam_pdf_path=Path("data/prova.pdf"),
        answer_key_pdf_path=Path("data/gabarito.pdf"),
        images_output_dir=CONFIG.paths.extracted_images_dir,
    )

    print("[bold blue]Cleaning text...[/bold blue]\n")
    cleaned_exam_text = text_processor.clean_text(exam_data["text"])

    print(
        "[bold blue]Splitint exam into exam content "
        "and answer key. [/bold blue]\n"
    )
    exam_text, answer_key_text = question_processor.split_answer_key(
        cleaned_exam_text
    )

    print("[bold blue]Splitting exam into question chunks...[/bold blue]\n")
    question_chunks = question_processor.split_into_questions(exam_text)

    print(
        f"[bold green]Extracted {len(question_chunks)} "
        "question chunks.[/bold green]\n"
    )

    print("[bold blue]Structuring questions using LLM... [/bold blue]\n")
    structured_questions = await question_processor.structure_questions(
        "structure_questions/v4.md", question_chunks, answer_key_text
    )

    print("[bold blue]Attaching images to questions... [/bold blue]\n")
    question_processor.attach_images_to_questions(
        structured_questions, exam_data["images_map"]
    )

    serialized_questions = [q.model_dump() for q in structured_questions]

    print(f"[bold green]Writing output to {output_path}...[/bold green]\n")
    await async_write_json(output_path, serialized_questions)
    end = time.perf_counter()

    print(f"Pipeline completed in {end - start:.2f} seconds.")
    print(
        f"[bold green]Successfully processed {len(structured_questions)} "
        "questions.[/bold green]"
    )


if __name__ == "__main__":
    asyncio.run(run_pipeline())
