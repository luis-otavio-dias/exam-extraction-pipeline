"""Async file operations utilities.

This module provides async wrappers for file I/O operations.
"""

import asyncio
import json
from pathlib import Path
from typing import Any


async def async_read_text(path: Path, encoding: str = "utf-8") -> str:
    """Asynchronously read text from a file.

    Args:
        path: Path to the file to read
        encoding: File encoding (default: utf-8)

    Returns:
        Content of the file as string
    """
    return await asyncio.to_thread(path.read_text, encoding=encoding)


async def async_write_json(
    path: Path,
    data: Any,
    indent: int = 4,
    *,
    ensure_ascii: bool = False,
    **kwargs: Any,
) -> None:
    """Asynchronously write JSON data to a file.

    Args:
        path: Path to the file to write
        data: Data to serialize as JSON
        indent: JSON indentation (default: 4)
        ensure_ascii: Whether to escape non-ASCII characters (default: False)
        **kwargs: Additional arguments to pass to json.dump
    """

    def _write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(
                data, f, indent=indent, ensure_ascii=ensure_ascii, **kwargs
            )

    await asyncio.to_thread(_write)


async def async_write_text(
    path: Path, content: str, encoding: str = "utf-8"
) -> None:
    """Asynchronously write text to a file.

    Args:
        path: Path to the file to write
        content: Text content to write
        encoding: File encoding (default: utf-8)
    """

    def _write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding=encoding) as f:
            f.write(content)

    await asyncio.to_thread(_write)
