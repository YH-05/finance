"""Shared helper functions for SEC EDGAR filing extractors.

This module provides common utilities used by both TextExtractor and
SectionExtractor for accessing filing attributes. Centralising these
helpers eliminates duplication across extractor modules.

Functions
---------
get_accession_number
    Extract the accession number from a Filing object.
get_filing_text
    Extract full text content from a Filing object.
"""

from __future__ import annotations

from typing import Any

from utils_core.logging import get_logger

logger = get_logger(__name__)


def get_accession_number(filing: Any) -> str | None:
    """Extract the accession number from a filing object.

    Checks both ``accession_number`` and ``accession_no`` attributes
    to handle different edgartools API versions.

    Parameters
    ----------
    filing : Any
        An edgartools Filing object or similar

    Returns
    -------
    str | None
        The accession number, or None if not available
    """
    try:
        if hasattr(filing, "accession_number"):
            return str(filing.accession_number)
        if hasattr(filing, "accession_no"):
            return str(filing.accession_no)
        logger.debug("Filing object has no accession number attribute")
        return None
    except Exception as e:
        logger.warning(
            "Failed to get accession number",
            error=str(e),
        )
        return None


def get_filing_text(filing: Any) -> str | None:
    """Extract full text content from a filing object.

    Attempts multiple methods to obtain the filing text, handling
    various edgartools API versions and object structures.

    The methods are tried in order:
    1. ``filing.text()`` method
    2. ``filing.full_text`` attribute
    3. ``str(filing.obj())`` for parsed HTML content

    Parameters
    ----------
    filing : Any
        An edgartools Filing object or similar

    Returns
    -------
    str | None
        The full text content of the filing, or None if extraction fails
    """
    # AIDEV-NOTE: edgartools Filing objects may expose text via different
    # methods depending on the version. We try multiple approaches.
    try:
        # Method 1: filing.text() method
        if hasattr(filing, "text") and callable(filing.text):
            raw_text = filing.text()
            if raw_text:
                result = str(raw_text)
                logger.debug(
                    "Extracted filing text via text() method",
                    text_length=len(result),
                )
                return result

        # Method 2: filing.full_text attribute
        if hasattr(filing, "full_text"):
            raw_text = filing.full_text
            if raw_text:
                result = str(raw_text)
                logger.debug(
                    "Extracted filing text via full_text attribute",
                    text_length=len(result),
                )
                return result

        # Method 3: str(filing.obj()) for parsed HTML content
        if hasattr(filing, "obj") and callable(filing.obj):
            obj = filing.obj()
            if obj:
                text = str(obj)
                logger.debug(
                    "Extracted filing text via obj() method",
                    text_length=len(text),
                )
                return text

        logger.warning(
            "Could not extract text from filing: no compatible method found",
        )
        return None

    except Exception as e:
        logger.warning(
            "Failed to extract text from filing",
            error=str(e),
            error_type=type(e).__name__,
        )
        return None


__all__ = [
    "get_accession_number",
    "get_filing_text",
]
