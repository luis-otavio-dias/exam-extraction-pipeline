"""Pydantic models for question and exam data structures.

This module defines the data models used throughout the application,
providing type safety, validation, and IDE support.
"""

from typing import Any, ClassVar

from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
    """Model for question answer options."""

    A: str = ""
    B: str = ""
    C: str = ""
    D: str = ""
    E: str = ""


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

    question: str = Field(..., description="Question identifier")
    image: bool = Field(default=False, description="Has images")
    images: list[str] = Field(
        default_factory=list, description="List of image paths"
    )
    passage_text: str = Field(default="", description="Question passage text")
    sources: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Source URLs or references",
    )
    statement: str = Field(..., description="Question statement")
    options: QuestionOption = Field(..., description="Answer options")
    correct_option: str = Field(
        ..., pattern=r"^[A-E]$", description="Correct answer"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "question": "QUESTÃO 01",
                "image": True,
                "images": ["QUESTÃO 01_img123.jpeg"],
                "passage_text": "",
                "sources": ["http://example.com"],
                "statement": "Qual é a resposta correta?",
                "options": {
                    "A": "Opção A",
                    "B": "Opção B",
                    "C": "Opção C",
                    "D": "Opção D",
                    "E": "Opção E",
                },
                "correct_option": "A",
            }
        }


class ExamData(BaseModel):
    """Model for complete exam data.

    Attributes:
        questions: List of all questions in the exam
        metadata: Additional metadata about the exam
    """

    questions: list[Question] = Field(..., description="List of questions")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Exam metadata"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "questions": [],
                "metadata": {
                    "total_questions": 50,
                    "exam_date": "2026-01-22",
                    "exam_type": "Multiple Choice",
                },
            }
        }
