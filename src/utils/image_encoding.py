"""Utility to convert extracted images to base64 for API responses."""

import base64
import logging
import mimetypes
from pathlib import Path

from models.question import (
    Exam,
    ExamResponse,
    ImagePayload,
    Question,
    QuestionResponse,
)

logger = logging.getLogger(__name__)


def _encode_single_image(
    images_dir: Path, filename: str
) -> ImagePayload | None:
    """Read a single image file and return its base64 payload."""
    image_path = images_dir / filename
    if not image_path.is_file():
        logger.warning("Image file not found: %s", image_path)
        return None

    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = "image/jpeg"

    content = image_path.read_bytes()
    return ImagePayload(
        filename=filename,
        content_base64=base64.b64encode(content).decode("ascii"),
        mime_type=mime_type,
    )


def _convert_question(
    question: Question, images_dir: Path
) -> QuestionResponse:
    """Convert a Question (with filenames) to QuestionResponse (base64)."""
    image_payloads: list[ImagePayload] = []
    for filename in question.images:
        payload = _encode_single_image(images_dir, filename)
        if payload is not None:
            image_payloads.append(payload)

    return QuestionResponse(
        question_id=question.question_id,
        question=question.question,
        passage_text=question.passage_text,
        sources=question.sources,
        image=question.image,
        images=image_payloads,
        statement=question.statement,
        options=question.options,
        correct_option=question.correct_option,
        metadata=question.metadata,
    )


def build_exam_response(exam: Exam, images_dir: Path) -> ExamResponse:
    """Convert an Exam (filenames) to an ExamResponse (base64 images).

    Args:
        exam: The pipeline-produced Exam object.
        images_dir: Directory where extracted images were saved.

    Returns:
        ExamResponse with all images encoded as base64.
    """
    questions = [_convert_question(q, images_dir) for q in exam.questions]
    return ExamResponse(metadata=exam.metadata, questions=questions)
