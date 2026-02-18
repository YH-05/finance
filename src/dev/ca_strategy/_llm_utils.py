"""Shared LLM utility functions for the CA Strategy pipeline.

Extracted from ClaimExtractor and ClaimScorer to eliminate code
duplication (DRY-001).  Provides file I/O helpers and LLM response
parsing utilities used by both Phase 1 and Phase 2.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import anthropic

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)


def load_directory(directory: Path) -> dict[str, str]:
    """Load all markdown files from a directory.

    Parameters
    ----------
    directory : Path
        Directory containing .md files.

    Returns
    -------
    dict[str, str]
        Mapping of filename (without extension) to file content.
    """
    result: dict[str, str] = {}
    if not directory.exists():
        logger.warning("Directory not found", path=str(directory))
        return result

    for filepath in sorted(directory.glob("*.md")):
        try:
            content = filepath.read_text(encoding="utf-8")
            result[filepath.stem] = content
            logger.debug(
                "KB file loaded",
                file=filepath.name,
                length=len(content),
            )
        except OSError:
            logger.warning(
                "Failed to read KB file",
                path=str(filepath),
                exc_info=True,
            )

    return result


def load_file(filepath: Path) -> str:
    """Load a single text file.

    Parameters
    ----------
    filepath : Path
        Path to the file.

    Returns
    -------
    str
        File content, or empty string if the file does not exist.
    """
    if not filepath.exists():
        logger.warning("File not found", path=str(filepath))
        return ""

    try:
        return filepath.read_text(encoding="utf-8")
    except OSError:
        logger.warning(
            "Failed to read file",
            path=str(filepath),
            exc_info=True,
        )
        return ""


def extract_text_from_response(message: anthropic.types.Message) -> str:
    """Extract text content from a Claude API response.

    Parameters
    ----------
    message : anthropic.types.Message
        The API response message.

    Returns
    -------
    str
        Concatenated text content from all TextBlock content blocks.
    """
    texts: list[str] = []
    for block in message.content:
        if hasattr(block, "text"):
            texts.append(block.text)
    return "\n".join(texts)


def strip_code_block(text: str) -> str:
    """Strip markdown code block delimiters from text.

    Handles both ````` `json ... ``` ````` and plain text.

    Parameters
    ----------
    text : str
        Text that may be wrapped in code block markers.

    Returns
    -------
    str
        Text with code block markers removed.
    """
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


__all__ = [
    "extract_text_from_response",
    "load_directory",
    "load_file",
    "strip_code_block",
]
