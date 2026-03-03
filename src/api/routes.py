"""API routes for the exam extraction pipeline."""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api.dependencies import verify_api_key
from models.question import ExamResponse, ProcessingResponse
from pipeline import run_pipeline
from utils.image_encoding import build_exam_response

logger = logging.getLogger(__name__)

router = APIRouter()

_ALLOWED_CONTENT_TYPES = frozenset(
    {"application/pdf", "application/octet-stream"}
)


def _validate_pdf(upload: UploadFile, label: str) -> None:
    """Raise 422 if the upload does not look like a PDF."""
    if upload.content_type not in _ALLOWED_CONTENT_TYPES:
        msg = f"{label} must be a PDF file (got {upload.content_type})."
        raise HTTPException(status_code=422, detail=msg)


async def _save_upload(upload: UploadFile, dest: Path) -> None:
    """Persist an UploadFile to *dest* asynchronously."""
    content = await upload.read()
    await asyncio.to_thread(dest.write_bytes, content)


@router.post(
    "/process-exam",
    summary="Process exam PDF(s) and return structured questions",
)
async def process_exam(
    exam_pdf: Annotated[UploadFile, File(description="The exam PDF file")],
    answer_key_pdf: Annotated[
        UploadFile | None,
        File(description="Optional answer-key PDF"),
    ] = None,
    _api_key: Annotated[str, Depends(verify_api_key)] = "",
) -> ProcessingResponse:
    """Receive exam PDF(s), run the extraction pipeline, return results.

    - ``exam_pdf`` - required.
    - ``answer_key_pdf`` - optional (omit when the answer key is embedded
      in the exam document itself).

    Returns a ``ProcessingResponse`` with ``status`` and ``data``
    (an ``ExamResponse`` object that includes base64-encoded images).
    """
    _validate_pdf(exam_pdf, "exam_pdf")
    if answer_key_pdf is not None:
        _validate_pdf(answer_key_pdf, "answer_key_pdf")

    temp_dir = Path(tempfile.mkdtemp(prefix="exam_pipeline_"))
    try:
        exam_path = temp_dir / "exam.pdf"
        await _save_upload(exam_pdf, exam_path)

        answer_key_path: Path | None = None
        if answer_key_pdf is not None:
            answer_key_path = temp_dir / "answer_key.pdf"
            await _save_upload(answer_key_pdf, answer_key_path)

        images_dir = temp_dir / "images"
        images_dir.mkdir()

        logger.info(
            "Starting pipeline - exam=%s answer_key=%s",
            exam_path,
            answer_key_path,
        )

        exam = await run_pipeline(
            exam_pdf_path=exam_path,
            answer_key_pdf_path=answer_key_path,
            images_output_dir=images_dir,
        )

        exam_response: ExamResponse = build_exam_response(exam, images_dir)

        return ProcessingResponse(status="success", data=exam_response)

    except Exception:
        logger.exception("Pipeline failed")
        raise

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info("Cleaned up temp dir %s", temp_dir)
