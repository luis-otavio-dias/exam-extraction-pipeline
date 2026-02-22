import asyncio
from asyncio import Semaphore
from pathlib import Path

import anyio
import fitz
from aiolimiter import AsyncLimiter
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError

from config import CONFIG
from extractors.text_extractor import PDFTextExtractor
from models.question import ExamDiagnostic
from prompts.loader import PromptLoader
from utils.llm import load_google_generative_ai_model

_MIN_PAGES_FOR_MIDDLE_SAMPLE = 2


class DiagnosticProcessor:
    """Processor for analyzing and diagnosing question extraction results."""

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        requests_per_minute: int | None = None,
        max_concurrent_requests: int | None = None,
    ) -> None:
        self.llm: BaseChatModel = llm or load_google_generative_ai_model(
            model_name=CONFIG.llm.model_name,
            temperature=CONFIG.llm.temperature,
        )
        self.parser = JsonOutputParser(pydantic_object=ExamDiagnostic)
        self.prompt = PromptLoader()
        rpm = requests_per_minute or CONFIG.llm.requests_per_minute
        concurrency = max_concurrent_requests or min(
            CONFIG.llm.max_concurrent_requests, rpm
        )
        self.text_extractor = PDFTextExtractor()
        self.semaphore = Semaphore(concurrency)
        self.rate_limiter = AsyncLimiter(max_rate=rpm, time_period=60)
        self.max_retries = CONFIG.llm.max_retries
        self.retry_base_delay = CONFIG.llm.retry_base_delay

    def extract_sample(self, pdf_path: Path) -> str:
        """Extract a sample of text from the PDF for diagnostic purposes."""

        with fitz.open(pdf_path) as pdf:
            total = pdf.page_count
            if total == 0:
                return ""

            if total > _MIN_PAGES_FOR_MIDDLE_SAMPLE:
                end_page = total // 2
            else:
                end_page = total

        return self.text_extractor.extract_text(
            pdf_path=pdf_path,
            start_page=0,
            end_page=end_page,
            page_marker=None,
        )

    async def diagnose(
        self,
        prompt_path: str,
        exam_pdf_path: Path,
        answer_key_pdf_path: Path | None,
    ) -> ExamDiagnostic | None:
        """Run diagnostic analysis on the extracted exam data."""

        exam_sample = self.extract_sample(exam_pdf_path)

        answer_sample = ""
        if answer_key_pdf_path:
            async_path = anyio.Path(answer_key_pdf_path)
            if await async_path.exists():
                answer_sample = self.extract_sample(answer_key_pdf_path)

        prompt = await self.prompt.async_load(
            prompt_path=prompt_path,
            exam_sample=exam_sample,
            answer_sample=answer_sample,
            format_instructions=self.parser.get_format_instructions(),
        )

        for attempt in range(1, self.max_retries + 1):
            async with self.rate_limiter, self.semaphore:
                content = None

                try:
                    response = await self.llm.ainvoke(prompt)
                    content = response.content

                    if not isinstance(content, str):
                        content = str(content)

                    parsed = self.parser.invoke(content)
                    return ExamDiagnostic.model_validate(parsed)

                except (ValidationError, Exception) as e:
                    is_validation_error = isinstance(e, ValidationError)
                    error_type = (
                        "ValidationError"
                        if is_validation_error
                        else "Exception"
                    )

                    if attempt < self.max_retries:
                        delay = self.retry_base_delay * (2 ** (attempt - 1))
                        print(
                            f"[Attempt {attempt}/{self.max_retries}] "
                            f"{error_type}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        print(
                            f"[Attempt {attempt}/{self.max_retries}] "
                            f"{error_type}: {e}. "
                            f"Giving up."
                        )
                        if content:
                            print(f"LLM Response Content: {content[:500]}...")
                        return None
        return None
