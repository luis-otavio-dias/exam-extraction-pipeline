from pathlib import Path

from langchain_core.prompts import PromptTemplate

from utils.file_operations import async_read_text


class PromptLoader:
    """Loads and formats prompt templates from files."""

    def __init__(self, base_path: Path = Path("src/prompts")) -> None:
        self.base_path = base_path

    async def async_load(self, prompt_path: str, **variables: str) -> str:
        """Asynchronously load and format a prompt template from a file.
        Args:
            prompt_path: The relative path to the prompt template file.
            **variables: Variables to format the prompt template.
        Returns:
            str: The formatted prompt string.
        """
        full_path = self.base_path / prompt_path

        template = await async_read_text(full_path)

        prompt = PromptTemplate(
            template=template,
            input_variables=list(variables.keys()),
        )

        return prompt.format(**variables)

    def load(self, prompt_path: str, **variables: str) -> str:
        """Load and format a prompt template from a file.
        Args:
            prompt_path: The relative path to the prompt template file.
            **variables: Variables to format the prompt template.
        Returns:
            str: The formatted prompt string.
        """
        full_path = self.base_path / prompt_path

        template = full_path.read_text()

        prompt = PromptTemplate(
            template=template,
            input_variables=list(variables.keys()),
        )

        return prompt.format(**variables)
