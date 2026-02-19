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

    from dev.ca_strategy.cost import CostTracker

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


def build_kb_section(header: str, items: list[tuple[str, str]]) -> list[str]:
    """Build a knowledge base section for a prompt.

    Generates a header line followed by subsections for each item.
    Used to assemble KB1-T, KB2-T, and KB3-T blocks in prompt construction.

    Parameters
    ----------
    header : str
        Markdown section header (e.g. "## KB1-T ルール集（全ルール）").
    items : list[tuple[str, str]]
        Ordered list of (name, content) pairs.

    Returns
    -------
    list[str]
        Parts to extend into the prompt parts list.
    """
    parts: list[str] = [header + "\n"]
    for name, content in items:
        parts.append(f"### {name}\n\n{content}\n")
    return parts


def call_llm(
    client: anthropic.Anthropic,
    *,
    model: str,
    system: str,
    user_content: str,
    max_tokens: int,
    temperature: float,
    cost_tracker: CostTracker,
    phase: str,
) -> str:
    """Call Claude API, record cost, and return extracted text.

    Consolidates the common LLM call pattern used by both
    ClaimExtractor (Phase 1) and ClaimScorer (Phase 2).

    Parameters
    ----------
    client : anthropic.Anthropic
        Anthropic client instance.
    model : str
        Model ID (e.g. ``claude-sonnet-4-20250514``).
    system : str
        System prompt.
    user_content : str
        User message content.
    max_tokens : int
        Maximum output tokens.
    temperature : float
        Temperature setting.
    cost_tracker : CostTracker
        Cost tracker for recording token usage.
    phase : str
        Pipeline phase identifier (e.g. ``"phase1"``).

    Returns
    -------
    str
        Extracted text from LLM response.
    """
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )

    cost_tracker.record(
        phase=phase,
        tokens_input=message.usage.input_tokens,
        tokens_output=message.usage.output_tokens,
    )

    return extract_text_from_response(message)


__all__ = [
    "build_kb_section",
    "call_llm",
    "extract_text_from_response",
    "load_directory",
    "load_file",
    "strip_code_block",
]
