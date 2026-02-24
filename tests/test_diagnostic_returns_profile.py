import json
from pathlib import Path

import pytest

from models.question import ExamProfile
from processors.exam_diagnostic_processor import ExamDiagnosticProcessor


@pytest.fixture
async def profile() -> ExamProfile | None:
    processor = ExamDiagnosticProcessor()

    return await processor.diagnose(
        prompt_path="diagnostic/v3.md",
        exam_pdf_path=Path("data/prova.pdf"),
        answer_key_pdf_path=Path("data/gabarito.pdf"),
    )


async def test_diagnostic_returns_profile(profile: ExamProfile) -> None:

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

    serialized = json.dumps(data)
    assert isinstance(serialized, str)
    assert len(serialized) > 0


async def test_diagnostic_profile_fields_are_not_empty(
    profile: ExamProfile,
) -> None:
    data = profile.model_dump()

    assert data["exam_name_base"] not in (None, "")
    assert data["exam_name_sigle"] not in (None, "")
    assert data["exam_variant"] not in (None, "")
    assert data["exam_year"] not in (None, "")
    assert data["exam_style"] not in (None, "")
    assert data["exam_type"] not in (None, "")
    assert data["answer_key_location"] not in (None, "")
    assert data["total_questions"] not in (None, "")


async def test_diagnostic_total_questions_is_positive_int(
    profile: ExamProfile,
) -> None:
    data = profile.model_dump()

    total_questions = data["total_questions"]
    assert isinstance(total_questions, int)
    assert total_questions > 0


async def test_diagnostic_exam_year_is_valid(profile: ExamProfile) -> None:
    data = profile.model_dump()

    min_year = 1900
    max_year = 2100
    exam_year = data["exam_year"]
    assert isinstance(exam_year, int)
    assert min_year <= exam_year <= max_year


async def test_diagnostic_profile_round_trip_json(
    profile: ExamProfile,
) -> None:
    data = profile.model_dump()

    serialized = json.dumps(data, ensure_ascii=False)
    deserialized = json.loads(serialized)

    assert deserialized == data
