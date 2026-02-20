import json
from pathlib import Path

from config import CONFIG
from extractors.exam_extractor import ExamExtractor
from processors import QuestionProcessor


def test_final_output_precision() -> None:
    exam_extractor = ExamExtractor()
    question_processor = QuestionProcessor()

    question_image_map = exam_extractor.map_images_to_questions(
        pdf_path=Path("data/prova.pdf"),
        output_dir=CONFIG.paths.extracted_images_dir,
    )

    # structured_questions =
    json_path = Path("data/expected_output.json")
    with json_path.open("r") as f:
        structured_questions_list = json.load(f)

    all_questions = [
        chunk_result["question_content"]
        for chunk_result in structured_questions_list
        if isinstance(chunk_result, dict)
        and "question_content" in chunk_result
    ]

    final_output = {
        "prompt_version": "structure_questions/v3.md",
        "questions": all_questions,
    }

    question_processor.attach_images_to_questions(
        final_output["questions"], question_image_map
    )

    json_output_path = Path("data/fixed_expected_output.json")
    with json_output_path.open("w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    test_final_output_precision()
