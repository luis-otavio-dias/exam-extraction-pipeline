from pathlib import Path

import pytest

from processors.diagnostic_processor import DiagnosticProcessor


@pytest.mark.asyncio
async def test_diagnostic_returns_profile() -> None:
    processor = DiagnosticProcessor()

    profile = await processor.diagnose(
        prompt_path="diagnostic/v3.md",
        exam_pdf_path=Path("data/prova.pdf"),
        answer_key_pdf_path=Path("data/gabarito.pdf"),
    )

    assert profile is not None

    data = profile.model_dump()

    assert "exam_name_base" in data
    assert "exam_name_sigle" in data
    assert "exam_variant" in data
    assert "exam_year" in data
    assert "exam_style" in data
    assert "exam_type" in data
    assert "answer_key_location" in data
    assert "total_questions" in data
