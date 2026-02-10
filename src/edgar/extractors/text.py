"""Text extraction from SEC EDGAR Filing objects.

This module provides the TextExtractor class for extracting and cleaning
text content from Filing objects returned by the edgartools library.

Features
--------
- Extract clean plain text from Filing objects
- Extract Markdown-formatted text from Filing objects
- Token counting using tiktoken (cl100k_base encoding)
- CacheManager integration for avoiding redundant extractions
- Text cleaning (whitespace normalization, newline consolidation)

Notes
-----
Filing objects are typed as ``Any`` because the edgartools library installs
as ``edgar`` in site-packages, which conflicts with our ``src/edgar`` package.
The Filing objects are expected to have ``.text()`` and ``.markdown()`` methods,
as well as an ``accession_number`` attribute.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import tiktoken

from edgar.errors import EdgarError
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from edgar.cache import CacheManager

logger = get_logger(__name__)

# tiktoken encoding for token counting (GPT-4 / Claude compatible)
_TIKTOKEN_ENCODING = "cl100k_base"

# Cache key prefixes
_CACHE_KEY_TEXT = "text"
_CACHE_KEY_MARKDOWN = "markdown"


def _clean_text(text: str) -> str:
    """Clean extracted text by normalizing whitespace and newlines.

    Applies the following transformations:
    1. Consecutive spaces (not newlines) are collapsed to a single space
    2. Three or more consecutive newlines are collapsed to two newlines
    3. Leading and trailing whitespace is stripped

    Parameters
    ----------
    text : str
        Raw text to clean

    Returns
    -------
    str
        Cleaned text with normalized whitespace
    """
    # Collapse consecutive spaces (excluding newlines) to a single space
    cleaned = re.sub(r"[^\S\n]+", " ", text)

    # Collapse 3+ consecutive newlines to exactly 2 newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Strip leading/trailing whitespace
    return cleaned.strip()


def _build_cache_key(prefix: str, accession_number: str) -> str:
    """Build a cache key from a prefix and accession number.

    Parameters
    ----------
    prefix : str
        Cache key prefix (e.g., "text", "markdown")
    accession_number : str
        Filing accession number

    Returns
    -------
    str
        Formatted cache key
    """
    return f"{prefix}_{accession_number}"


class TextExtractor:
    """Extractor for clean text content from SEC EDGAR Filing objects.

    Wraps the edgartools Filing ``.text()`` and ``.markdown()`` methods
    to provide cleaned, normalized text output with optional caching
    and token counting.

    Parameters
    ----------
    cache : CacheManager | None
        Optional cache manager for caching extracted text.
        When provided, extracted text is cached using the filing's
        accession number as the key. Cache is checked before extraction
        to avoid redundant API calls.

    Attributes
    ----------
    _cache : CacheManager | None
        The cache manager instance, or None if caching is disabled
    _encoding : tiktoken.Encoding
        The tiktoken encoding used for token counting

    Examples
    --------
    >>> extractor = TextExtractor()
    >>> text = extractor.extract_text(filing)
    >>> token_count = extractor.count_tokens(text)

    >>> # With caching
    >>> from edgar.cache import CacheManager
    >>> cache = CacheManager()
    >>> extractor = TextExtractor(cache=cache)
    >>> text = extractor.extract_text(filing)  # cached on first call
    """

    def __init__(self, cache: CacheManager | None = None) -> None:
        self._cache = cache
        self._encoding = tiktoken.get_encoding(_TIKTOKEN_ENCODING)

        logger.debug(
            "Initializing TextExtractor",
            cache_enabled=cache is not None,
            encoding=_TIKTOKEN_ENCODING,
        )

    def extract_text(self, filing: Any) -> str:
        """Extract clean plain text from a Filing object.

        Calls ``filing.text()`` and applies text cleaning to normalize
        whitespace and newlines. If a cache manager is configured,
        checks the cache first and stores the result after extraction.

        Parameters
        ----------
        filing : Any
            An edgartools Filing object with a ``.text()`` method
            and ``accession_number`` attribute

        Returns
        -------
        str
            Cleaned plain text content of the filing

        Raises
        ------
        EdgarError
            If the filing does not have a ``.text()`` method,
            or if text extraction fails

        Examples
        --------
        >>> extractor = TextExtractor()
        >>> text = extractor.extract_text(filing)
        >>> len(text) > 0
        True
        """
        accession_number = self._get_accession_number(filing)
        cache_key = _build_cache_key(_CACHE_KEY_TEXT, accession_number)

        logger.info(
            "Extracting text from filing",
            accession_number=accession_number,
        )

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.info(
                "Text extraction cache hit",
                accession_number=accession_number,
                text_length=len(cached),
            )
            return cached

        # Extract text
        try:
            raw_text = filing.text()
        except AttributeError as e:
            raise EdgarError(
                "Filing object does not have a .text() method",
                context={"accession_number": accession_number},
            ) from e
        except Exception as e:
            raise EdgarError(
                f"Failed to extract text from filing '{accession_number}': {e}",
                context={"accession_number": accession_number},
            ) from e

        cleaned = _clean_text(raw_text)
        token_count = self.count_tokens(cleaned)

        logger.info(
            "Text extraction completed",
            accession_number=accession_number,
            text_length=len(cleaned),
            token_count=token_count,
        )

        # Save to cache
        self._save_to_cache(cache_key, cleaned)

        return cleaned

    def extract_markdown(self, filing: Any) -> str:
        """Extract Markdown-formatted text from a Filing object.

        Calls ``filing.markdown()`` and applies text cleaning to normalize
        whitespace and newlines. If a cache manager is configured,
        checks the cache first and stores the result after extraction.

        Parameters
        ----------
        filing : Any
            An edgartools Filing object with a ``.markdown()`` method
            and ``accession_number`` attribute

        Returns
        -------
        str
            Cleaned Markdown-formatted text content of the filing

        Raises
        ------
        EdgarError
            If the filing does not have a ``.markdown()`` method,
            or if text extraction fails

        Examples
        --------
        >>> extractor = TextExtractor()
        >>> markdown = extractor.extract_markdown(filing)
        >>> "# " in markdown or len(markdown) > 0
        True
        """
        accession_number = self._get_accession_number(filing)
        cache_key = _build_cache_key(_CACHE_KEY_MARKDOWN, accession_number)

        logger.info(
            "Extracting markdown from filing",
            accession_number=accession_number,
        )

        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.info(
                "Markdown extraction cache hit",
                accession_number=accession_number,
                text_length=len(cached),
            )
            return cached

        # Extract markdown
        try:
            raw_markdown = filing.markdown()
        except AttributeError as e:
            raise EdgarError(
                "Filing object does not have a .markdown() method",
                context={"accession_number": accession_number},
            ) from e
        except Exception as e:
            raise EdgarError(
                f"Failed to extract markdown from filing '{accession_number}': {e}",
                context={"accession_number": accession_number},
            ) from e

        cleaned = _clean_text(raw_markdown)
        token_count = self.count_tokens(cleaned)

        logger.info(
            "Markdown extraction completed",
            accession_number=accession_number,
            text_length=len(cleaned),
            token_count=token_count,
        )

        # Save to cache
        self._save_to_cache(cache_key, cleaned)

        return cleaned

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Uses the cl100k_base tiktoken encoding, which is compatible
        with GPT-4 and similar LLM tokenizers.

        Parameters
        ----------
        text : str
            Text to count tokens for

        Returns
        -------
        int
            Number of tokens in the text

        Examples
        --------
        >>> extractor = TextExtractor()
        >>> extractor.count_tokens("Hello, world!")
        4
        """
        return len(self._encoding.encode(text))

    def _get_accession_number(self, filing: Any) -> str:
        """Extract the accession number from a Filing object.

        Parameters
        ----------
        filing : Any
            An edgartools Filing object

        Returns
        -------
        str
            The filing's accession number

        Raises
        ------
        EdgarError
            If the filing does not have an ``accession_number`` attribute
        """
        accession_number = getattr(filing, "accession_number", None)
        if accession_number is None:
            raise EdgarError(
                "Filing object does not have an 'accession_number' attribute",
            )
        return str(accession_number)

    def _get_from_cache(self, cache_key: str) -> str | None:
        """Retrieve text from cache if available.

        Parameters
        ----------
        cache_key : str
            The cache key to look up

        Returns
        -------
        str | None
            Cached text, or None if not found or caching is disabled
        """
        if self._cache is None:
            return None

        try:
            return self._cache.get_cached_text(cache_key)
        except Exception:
            logger.warning(
                "Failed to read from cache, proceeding without cache",
                cache_key=cache_key,
                exc_info=True,
            )
            return None

    def _save_to_cache(self, cache_key: str, text: str) -> None:
        """Save extracted text to cache.

        Parameters
        ----------
        cache_key : str
            The cache key to save under
        text : str
            The text content to cache
        """
        if self._cache is None:
            return

        try:
            self._cache.save_text(cache_key, text)
            logger.debug("Text saved to cache", cache_key=cache_key)
        except Exception:
            logger.warning(
                "Failed to save to cache, continuing without caching",
                cache_key=cache_key,
                exc_info=True,
            )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"TextExtractor(cache_enabled={self._cache is not None})"


__all__ = [
    "TextExtractor",
]
