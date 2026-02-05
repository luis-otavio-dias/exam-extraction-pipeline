import asyncio
import re
from asyncio import Semaphore
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from config import CONFIG
from prompts.loader import PromptLoader
from utils.llm import load_google_generative_ai_model


class QuestionProcessor:
    """Processes extracted questions for further analysis."""

    def __init__(self) -> None:
        self.question_split_pattern = CONFIG.question.question_split_pattern
        self.answer_key_separator = CONFIG.question.answer_key_separator
        self.re_question_split = re.compile(
            self.question_split_pattern, re.IGNORECASE
        )

        self.llm = load_google_generative_ai_model(
            model_name=CONFIG.llm.model_name,
            temperature=CONFIG.llm.temperature,
        )

        self.parser = JsonOutputParser()
        self.semaphore = Semaphore(CONFIG.llm.max_concurrent_requests)
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
        chunk: str,
        answer_key_text: str,
        llm: BaseChatModel,
        parser: JsonOutputParser,
        semaphore: Semaphore,
    ) -> dict[str, Any] | None:
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
            prompt_path="structure_questions/v1.md",
            chunk=chunk,
            answer_key_text=answer_key_text,
        )

        async with semaphore:
            try:
                response = await llm.ainvoke(prompt)
                content = response.content

                if not isinstance(content, str):
                    content = str(content)

                return parser.invoke(content)
            except Exception as e:
                print(f"Error processing chunk: {e}")
                return None

    async def structure_questions(
        self, question_chunks: list[str], answer_key_text: str
    ) -> list[dict[str, Any]]:
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
                    chunk,
                    answer_key_text,
                    self.llm,
                    self.parser,
                    self.semaphore,
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
        structured_questions: list[dict[str, Any]],
        question_image_map: dict[str, list[str]],
    ) -> None:
        """Determine if the question contains image information and
        update the question data accordingly.

        Args:
            structured_questions: List of question dictionaries to update
            with image info.
            question_image_map: Mapping of question identifiers to image URLs.
        """

        for question in structured_questions:
            # has_url = any(
            #     "http" in str(source) for source in question.get(
            #         "sources", []
            #     )
            # )
            # is_text_empty = not question.get("passage_text", "").strip()

            # if has_url and is_text_empty:
            #     question["image"] = True

            has_image = question.get("image", False)

            if has_image:
                for q_name, images in question_image_map.items():
                    if q_name in question.get("question", ""):
                        question["images"] = images
                        break
