"""Configuration module for the data extraction pipeline.

This module centralizes all configuration constants and settings,
making them easy to modify and maintain.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImageFilterConfig:
    """Configuration for image quality filters."""

    min_width: int = 300
    min_height: int = 300
    min_size_bytes: int = 10240  # 10 KB
    max_repetitions: int = 1
    min_unique_colors: int = 50
    max_aspect_ratio: float = 4.0
    min_aspect_ratio: float = 0.25


@dataclass
class PathConfig:
    """Configuration for file and directory paths."""

    # Base directories
    data_dir: Path = Path("data")
    output_dir: Path = Path("output_images")
    extracted_images_dir: Path = Path("extracted_images")
    temp_dir: Path = Path("temp")

    # Specific files
    exam_pdf_name: str = "prova.pdf"
    final_output_path: Path = Path("src/final_output.json")
    temp_text_file: str = "extracted_text.txt"

    @property
    def exam_pdf_path(self) -> Path:
        """Get the full path to the exam PDF."""
        return self.data_dir / self.exam_pdf_name

    @property
    def temp_text_path(self) -> Path:
        """Get the full path to the temporary text file."""
        return self.temp_dir / self.temp_text_file


@dataclass
class LLMConfig:
    """Configuration for Large Language Model settings."""

    model_name: str = "gemini-2.5-flash"
    temperature: float = 0
    max_concurrent_requests: int = 10
    requests_per_minute: int = 50
    max_retries: int = 3
    retry_base_delay: float = 2.0

    def __post_init__(self) -> None:
        """Override with environment variables if set."""
        self.model_name = os.getenv("LLM_MODEL", self.model_name)
        env_temp = os.getenv("LLM_TEMPERATURE", self.temperature)
        self.temperature = float(env_temp)
        env_max = os.getenv(
            "MAX_CONCURRENT_REQUESTS", self.max_concurrent_requests
        )
        self.max_concurrent_requests = int(env_max)
        env_rpm = os.getenv("LLM_RPM", self.requests_per_minute)
        self.requests_per_minute = int(env_rpm)
        env_retries = os.getenv("LLM_MAX_RETRIES", self.max_retries)
        self.max_retries = int(env_retries)
        env_delay = os.getenv("LLM_RETRY_BASE_DELAY", self.retry_base_delay)
        self.retry_base_delay = float(env_delay)


@dataclass
class QuestionConfig:
    """Configuration for question parsing and structuring."""

    # Regex patterns
    question_split_pattern: str = r"(QUESTÃO\s+\d+)"
    normalize_pattern: str = r"(\d+)"
    clean_pattern: str = r"(?i)(.+?)(?:\s?\1){3,}"

    # Answer key configuration
    answer_key_separator: str = "--- Answer Key ---"


@dataclass
class AppConfig:
    """Main application configuration."""

    image_filter: ImageFilterConfig = field(default_factory=ImageFilterConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    question: QuestionConfig = field(default_factory=QuestionConfig)


# Global configuration instance
CONFIG = AppConfig()
