import asyncio
import re
from asyncio import Semaphore

from aiolimiter import AsyncLimiter
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError

from config import CONFIG
from models.question import ExamProfile, Question
from prompts.loader import PromptLoader
from utils.build_question_id import build_question_id, extract_question_number
from utils.llm import load_google_generative_ai_model


class QuestionProcessor:
    """Processes extracted questions for further analysis."""

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        requests_per_minute: int | None = None,
        max_concurrent_requests: int | None = None,
    ) -> None:
        self.question_split_pattern = CONFIG.question.question_split_pattern
        self.answer_key_separator = CONFIG.question.answer_key_separator
        self.re_question_split = re.compile(
            self.question_split_pattern, re.IGNORECASE
        )

        self.llm: BaseChatModel = llm or load_google_generative_ai_model(
            model_name=CONFIG.llm.model_name,
            temperature=CONFIG.llm.temperature,
        )

        rpm = requests_per_minute or CONFIG.llm.requests_per_minute
        concurrency = max_concurrent_requests or min(
            CONFIG.llm.max_concurrent_requests, rpm
        )

        self.parser = JsonOutputParser(pydantic_object=Question)
        self.semaphore = Semaphore(concurrency)
        self.rate_limiter = AsyncLimiter(max_rate=rpm, time_period=60)
        self.max_retries = CONFIG.llm.max_retries
        self.retry_base_delay = CONFIG.llm.retry_base_delay
        self.prompt = PromptLoader()

    def split_into_questions(self, text: str) -> list[str]:
        """Split the exam text into chunks based on question delimiters.

        Args:
            text: The full exam text.

        Returns:
            A list of question chunks.
        """
        parts = self.re_question_split.split(text)
        chunks: list[str] = []

        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                header = parts[i]
                content = parts[i + 1]
                clean_content = re.sub(r"\n{3,}", "\n\n", content.strip())
                chunks.append(f"{header}\n{clean_content}")
        return chunks

    def split_answer_key(self, text: str) -> tuple[str, str]:
        """Split the exam text into exam content and answer key.

        Args:
            text: The full exam text.
        Returns:
            A tuple containing the exam text and the answer key text.
        """
        parts = text.split(self.answer_key_separator, 1)
        exam_text = parts[0]
        answer_key_text = (
            parts[1] if len(parts) > 1 else "No answer key found."
        )
        return exam_text, answer_key_text

    async def process_question_chunk(
        self,
        prompt_path: str,
        chunk: str,
        answer_key_text: str,
        exam_metadata: ExamProfile,
    ) -> Question | None:
        """Process a single question chunk using the LLM and parse the output.
        Args:
            chunk: The question chunk to process.
            answer_key_text: The answer key text for reference.
            llm: The language model to use for processing.
            parser: The output parser to structure the response.
            semaphore: Semaphore to limit concurrent LLM requests.
        Returns:
            dict: Representing the structured question data.
            None: If processing fails.
        """
        if "QUESTÃO" not in chunk:
            return None

        prompt = await self.prompt.async_load(
            prompt_path=prompt_path,
            chunk=chunk,
            answer_key_text=answer_key_text,
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

                    question = Question.model_validate(parsed)

                    question_id = build_question_id(
                        exam_name_base=exam_metadata.exam_name_base,
                        exam_name_sigle=exam_metadata.exam_name_sigle,
                        exam_variant=exam_metadata.exam_variant,
                        exam_year=exam_metadata.exam_year,
                        question_number=extract_question_number(
                            question.question
                        ),
                    )

                    question.question_id = question_id
                    return question.model_copy(
                        update={"question_id": question_id}
                    )

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

    async def structure_questions(
        self,
        prompt_path: str,
        question_chunks: list[str],
        answer_key_text: str,
        exam_metadata: ExamProfile,
    ) -> list[Question]:
        """Structure a list of question chunks using the LLM.
        Args:
            question_chunks: List of question chunks to process.
            answer_key_text: The answer key text for reference.
        Returns:
            list: List of structured question data dictionaries.
        """

        results = await asyncio.gather(
            *[
                self.process_question_chunk(
                    prompt_path,
                    chunk,
                    answer_key_text,
                    exam_metadata,
                )
                for chunk in question_chunks
            ]
        )

        valid_results = [res for res in results if res is not None]

        final_data = []
        for res in valid_results:
            if isinstance(res, list):
                final_data.extend(res)
            else:
                final_data.append(res)

        return final_data

    def attach_images_to_questions(
        self,
        structured_questions: list[Question],
        question_image_map: dict[str, list[str]],
    ) -> None:
        """Determine if the question contains image information and
        update the question data accordingly.

        Args:
            structured_questions: List of Question objects to update
            with image info.
            question_image_map: Mapping of question identifiers to image URLs.
        """

        for question in structured_questions:
            if question.image:
                for q_name, images in question_image_map.items():
                    if q_name in question.question:
                        question.images = images
                        break
