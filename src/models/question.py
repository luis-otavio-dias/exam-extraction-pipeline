"""Pydantic models for question and exam data structures.

This module defines the data models used throughout the application,
providing type safety, validation, and IDE support.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class QuestionOption(BaseModel):
    """Model for question answer options."""

    label: str = Field(
        ..., pattern=r"^[A-E]$", description="Option label (A-E)"
    )
    text: str = Field(..., description="Full text of the option")


class Question(BaseModel):
    """Model for a single exam question.

    Attributes:
        question: Question identifier (e.g., "QUESTÃO 01")
        image: Whether the question includes images
        images: List of image file paths associated with this question
        passage_text: Text passage/context for the question
        sources: List of source URLs or references (max 5)
        statement: The actual question statement
        options: Answer options A-E
        correct_option: The correct answer (A-E)
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "",
                "question": "QUESTÃO 01",
                "passage_text": "",
                "sources": ["http://example.com"],
                "image": True,
                "images": ["QUESTÃO 01_img123.jpeg"],
                "statement": "Qual é a resposta correta?",
                "options": [
                    {"label": "A", "text": "Opção A"},
                    {"label": "B", "text": "Opção B"},
                    {"label": "C", "text": "Opção C"},
                    {"label": "D", "text": "Opção D"},
                    {"label": "E", "text": "Opção E"},
                ],
                "correct_option": "C",
                "metadata": {
                    "area": "Ciências Humanas",
                    "topic": "História",
                },
            }
        }
    )

    question_id: str = Field(
        default="", description="Unique identifier for the question"
    )
    question: str = Field(..., description="Question identifier")
    passage_text: str = Field(default="", description="Question passage text")
    sources: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Source URLs or references",
    )
    image: bool = Field(default=False, description="Has images")
    images: list[str] = Field(
        default_factory=list, description="List of image paths"
    )
    statement: str = Field(..., description="Question statement")
    options: list[QuestionOption] = Field(..., description="Answer options")
    correct_option: str = Field(
        ..., pattern=r"^[A-E]$", description="Correct answer label (A-E)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional question metadata (area, topic, etc.)",
    )


class ExamProfile(BaseModel):
    """Model for diagnostic analysis results of an exam PDF."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exam_name_base": "Exame Nacional do Ensino Médio",
                "exam_name_sigle": "ENEM",
                "exam_variant": "2024 - 1º Dia - Caderno Azul",
                "exam_year": 2024,
                "exam_type": "multiple_choice",
                "exam_style": "enem",
                "answer_key_location": "separate_document",
                "total_questions": 95,
            },
        }
    )

    exam_name_base: str = Field(
        default="unknown",
        description="Official full institutional name of the exam",
    )
    exam_name_sigle: str = Field(
        default="unknown",
        description="Common acronym or short name of the exam or institution",
    )
    exam_variant: str = Field(
        default="unknown",
        description=(
            "Specific variant or edition of the exam"
            " (e.g., '2024 - 1º Dia - Caderno Azul')"
        ),
    )
    exam_year: int = Field(
        default=0, description="Year the exam was administered"
    )
    exam_style: Literal[
        "enem_like", "vestibular", "concurso", "internal_exam", "unknown"
    ] = Field(default="unknown", description="Style of the exam")
    exam_type: Literal["multiple_choice", "open_ended", "mixed", "unknown"] = (
        Field(default="unknown", description="Type of the exam")
    )
    answer_key_location: Literal[
        "same_document", "separate_document", "not_found"
    ] = Field(default="not_found", description="Where the answer key is")
    total_questions: int = Field(
        default=0, description="Estimated total number of questions"
    )


class Exam(BaseModel):
    """Model for complete exam data.

    Attributes:
        questions: List of all questions in the exam
        metadata: Additional metadata about the exam
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata": {
                    "exam_name_base": "Exame Nacional do Ensino Médio",
                    "exam_name_sigle": "ENEM",
                    "exam_variant": "2024 - 1º Dia - Caderno Azul",
                    "exam_year": 2024,
                    "exam_type": "multiple_choice",
                    "exam_style": "enem",
                    "answer_key_location": "separate_document",
                    "total_questions": 95,
                },
                "questions": [],
            }
        }
    )

    metadata: ExamProfile = Field(
        default_factory=ExamProfile, description="Exam profile metadata"
    )
    questions: list[Question] = Field(..., description="List of questions")
