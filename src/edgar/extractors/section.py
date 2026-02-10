"""Section extractor for SEC EDGAR filing data.

This module provides the SectionExtractor class for extracting section-level
text from SEC EDGAR filings. It identifies sections (Item 1, Item 1A, Item 7,
Item 8) using regex-based pattern matching on filing full text.

Features
--------
- Extract specific sections by SectionKey
- List available sections in a filing
- CacheManager integration with section-specific cache keys
- Graceful handling of missing sections (returns None, no exceptions)

Notes
-----
Filing objects are expected to have an ``accession_number`` attribute
and a ``text()`` method or similar to obtain the full text content.
Since edgartools installs as ``edgar`` in site-packages (conflicting with
our ``src/edgar`` package), we use try/except when accessing filing
attributes and methods.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from utils_core.logging import get_logger

from ..types import SectionKey
from ._helpers import get_accession_number, get_filing_text

if TYPE_CHECKING:
    from ..cache import CacheManager

logger = get_logger(__name__)

# Regex patterns for identifying section boundaries in SEC filings.
# Each pattern matches a section header line (e.g., "Item 1. Business").
# Patterns are case-insensitive and allow for flexible whitespace/punctuation.
SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    SectionKey.ITEM_1.value: re.compile(
        r"(?i)item\s+1[\.\s]+business",
    ),
    SectionKey.ITEM_1A.value: re.compile(
        r"(?i)item\s+1a[\.\s]+risk\s+factors",
    ),
    SectionKey.ITEM_7.value: re.compile(
        r"(?i)item\s+7[\.\s]+management",
    ),
    SectionKey.ITEM_8.value: re.compile(
        r"(?i)item\s+8[\.\s]+financial\s+statements",
    ),
}

# Ordered list of all known section keys, used to determine section boundaries.
# The order matches the typical 10-K filing structure.
_ORDERED_SECTION_KEYS: list[str] = [
    SectionKey.ITEM_1.value,
    SectionKey.ITEM_1A.value,
    SectionKey.ITEM_7.value,
    SectionKey.ITEM_8.value,
]


def _build_cache_key(accession_number: str, section_key: str) -> str:
    """Build a cache key for a specific section of a filing.

    Parameters
    ----------
    accession_number : str
        The filing's accession number
    section_key : str
        The section key identifier (e.g., "item_1")

    Returns
    -------
    str
        The cache key in format ``section_{accession_number}_{section_key}``
    """
    return f"section_{accession_number}_{section_key}"


def _find_section_positions(text: str) -> dict[str, int]:
    """Find the start positions of all recognized sections in the text.

    Parameters
    ----------
    text : str
        The full filing text content

    Returns
    -------
    dict[str, int]
        Mapping of section key to start position in the text
    """
    positions: dict[str, int] = {}
    for key, pattern in SECTION_PATTERNS.items():
        match = pattern.search(text)
        if match:
            positions[key] = match.start()
            logger.debug(
                "Found section",
                section_key=key,
                position=match.start(),
            )
    return positions


def _extract_section_text(
    text: str,
    section_key: str,
    positions: dict[str, int],
) -> str | None:
    """Extract the text of a specific section using position boundaries.

    The section text spans from the section header to the start of the
    next section (or end of document if it is the last section).

    Parameters
    ----------
    text : str
        The full filing text content
    section_key : str
        The section key to extract
    positions : dict[str, int]
        Mapping of all found section keys to their start positions

    Returns
    -------
    str | None
        The extracted section text, or None if the section is not found
    """
    if section_key not in positions:
        return None

    start = positions[section_key]

    # Find the next section's start position to determine the end boundary.
    # Sort positions by their offset to find what comes after this section.
    sorted_positions = sorted(positions.items(), key=lambda item: item[1])
    end = len(text)

    for i, (key, _pos) in enumerate(sorted_positions):
        if key == section_key and i + 1 < len(sorted_positions):
            end = sorted_positions[i + 1][1]
            break

    section_text = text[start:end].strip()

    if not section_text:
        return None

    logger.debug(
        "Extracted section text",
        section_key=section_key,
        start=start,
        end=end,
        text_length=len(section_text),
    )
    return section_text


class SectionExtractor:
    """Extractor for section-level text from SEC EDGAR filings.

    Uses regex-based pattern matching to identify and extract sections
    (Item 1, Item 1A, Item 7, Item 8) from filing full text content.
    Optionally integrates with CacheManager for caching extracted sections.

    Parameters
    ----------
    cache : CacheManager | None
        Optional cache manager for caching extracted section text.
        If None, caching is disabled.

    Attributes
    ----------
    _cache : CacheManager | None
        The cache manager instance, or None if caching is disabled

    Examples
    --------
    >>> extractor = SectionExtractor()
    >>> text = extractor.extract_section(filing, "item_1")
    >>> sections = extractor.list_sections(filing)
    """

    def __init__(self, cache: CacheManager | None = None) -> None:
        """Initialize SectionExtractor.

        Parameters
        ----------
        cache : CacheManager | None
            Optional cache manager for section-level caching
        """
        self._cache = cache
        logger.debug(
            "Initializing SectionExtractor",
            cache_enabled=cache is not None,
        )

    def extract_section(self, filing: Any, section_key: str) -> str | None:
        """Extract the text of a specified section from a filing.

        Looks up the section by key in the filing's full text using
        regex pattern matching. If a CacheManager is configured, cached
        results are returned when available.

        Parameters
        ----------
        filing : Any
            An edgartools Filing object (or compatible object with
            ``accession_number`` attribute and text extraction methods)
        section_key : str
            The section identifier (e.g., "item_1", "item_1a", "item_7",
            "item_8"). Must be a valid SectionKey value.

        Returns
        -------
        str | None
            The extracted section text, or None if the section is not
            found in the filing or extraction fails

        Examples
        --------
        >>> extractor = SectionExtractor()
        >>> business = extractor.extract_section(filing, "item_1")
        >>> if business:
        ...     print(business[:100])
        """
        logger.info(
            "Extracting section",
            section_key=section_key,
        )

        # Validate section key
        if section_key not in SECTION_PATTERNS:
            logger.warning(
                "Unknown section key",
                section_key=section_key,
                valid_keys=list(SECTION_PATTERNS.keys()),
            )
            return None

        # Check cache
        accession_number = get_accession_number(filing)
        if self._cache is not None and accession_number is not None:
            cache_key = _build_cache_key(accession_number, section_key)
            cached = self._cache.get_cached_text(cache_key)
            if cached is not None:
                logger.info(
                    "Section retrieved from cache",
                    section_key=section_key,
                    accession_number=accession_number,
                    text_length=len(cached),
                )
                return cached

        # Extract full text from filing
        text = get_filing_text(filing)
        if text is None:
            logger.warning(
                "Could not extract text from filing for section extraction",
                section_key=section_key,
            )
            return None

        # Find section positions and extract target section
        positions = _find_section_positions(text)
        section_text = _extract_section_text(text, section_key, positions)

        if section_text is None:
            logger.warning(
                "Section not found in filing",
                section_key=section_key,
                available_sections=list(positions.keys()),
            )
            return None

        # Save to cache
        if self._cache is not None and accession_number is not None:
            try:
                cache_key = _build_cache_key(accession_number, section_key)
                self._cache.save_text(cache_key, section_text)
                logger.debug(
                    "Section text saved to cache",
                    cache_key=cache_key,
                    text_length=len(section_text),
                )
            except Exception as e:
                logger.warning(
                    "Failed to save section text to cache",
                    section_key=section_key,
                    error=str(e),
                )

        logger.info(
            "Section extracted successfully",
            section_key=section_key,
            text_length=len(section_text),
        )
        return section_text

    def list_sections(self, filing: Any) -> list[str]:
        """List the sections available in a filing.

        Scans the filing's full text for recognized section headers
        and returns the list of found section keys.

        Parameters
        ----------
        filing : Any
            An edgartools Filing object (or compatible object with
            text extraction methods)

        Returns
        -------
        list[str]
            List of section key strings found in the filing
            (e.g., ["item_1", "item_1a", "item_7", "item_8"]).
            Returns an empty list if no sections are found or
            text extraction fails.

        Examples
        --------
        >>> extractor = SectionExtractor()
        >>> sections = extractor.list_sections(filing)
        >>> "item_1" in sections
        True
        """
        logger.info("Listing sections in filing")

        text = get_filing_text(filing)
        if text is None:
            logger.warning(
                "Could not extract text from filing for section listing",
            )
            return []

        positions = _find_section_positions(text)

        # Return keys in the canonical order defined by _ORDERED_SECTION_KEYS
        found_keys = [key for key in _ORDERED_SECTION_KEYS if key in positions]

        logger.info(
            "Sections listed",
            found_sections=found_keys,
            found_count=len(found_keys),
        )
        return found_keys

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SectionExtractor(cache_enabled={self._cache is not None})"


__all__ = [
    "SECTION_PATTERNS",
    "SectionExtractor",
]
