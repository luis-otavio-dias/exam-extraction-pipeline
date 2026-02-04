import re

from config import CONFIG

# Compiled regex patterns from config
RE_QUESTION_SPLIT = re.compile(CONFIG.question.question_split_pattern)
RE_NORMALIZE_Q = re.compile(CONFIG.question.normalize_pattern)
RE_CLEAN_PATTERN = re.compile(CONFIG.question.clean_pattern)


class TextProcessor:
    """Processes extracted text for further analysis."""

    def __init__(self) -> None:
        self.clean_pattern = re.compile(CONFIG.question.clean_pattern)

    def clean_repetitive_patterns(self, text: str) -> str:
        """Clean repetitive patterns from the text.

        Args:
            text: The raw extracted text.
        Returns:
            Cleaned text with repetitive patterns removed.
        """

        return re.sub(self.clean_pattern, r"\1", text).strip()

    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned and normalized text
        """
        text = self.clean_repetitive_patterns(text)

        # Example cleaning: remove extra whitespace and normalize line breaks
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
