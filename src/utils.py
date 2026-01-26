"""Backward compatibility shim for utils module.

This module maintains backward compatibility by re-exporting
utilities from the new utils package structure.
"""

from utils.file_operations import async_read_text, async_write_json
from utils.llm import load_google_generative_ai_model

__all__ = [
    "async_read_text",
    "async_write_json",
    "load_google_generative_ai_model",
]
