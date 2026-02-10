"""Shared test fixtures for the edgar package tests.

Provides mock objects for edgartools Filing and Company classes,
cache mocks, fetcher helpers, and temporary directories for cache testing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture
def mock_filing() -> MagicMock:
    """Create a mock Filing object mimicking edgartools Filing.

    The mock has:
    - accession_number: "0001234567-24-000001"
    - text() method returning sample filing text with section headers
    - markdown() method returning sample markdown text
    - full_text attribute

    Returns
    -------
    MagicMock
        A mock Filing object with realistic filing text content
    """
    filing = MagicMock()
    filing.accession_number = "0001234567-24-000001"

    sample_text = (
        "UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n\n"
        "Item 1. Business\n\n"
        "We are a technology company that develops innovative products.\n\n"
        "Item 1A. Risk Factors\n\n"
        "Our business faces various risks including market competition.\n\n"
        "Item 7. Management's Discussion and Analysis\n\n"
        "Revenue increased 10% year over year driven by strong demand.\n\n"
        "Item 8. Financial Statements and Supplementary Data\n\n"
        "See accompanying notes to financial statements.\n"
    )

    filing.text.return_value = sample_text
    filing.markdown.return_value = f"# Filing\n\n{sample_text}"
    filing.full_text = sample_text

    return filing


@pytest.fixture
def mock_filing_no_sections() -> MagicMock:
    """Create a mock Filing with no recognizable sections.

    Returns
    -------
    MagicMock
        A mock Filing object with plain text (no Item headers)
    """
    filing = MagicMock()
    filing.accession_number = "0009876543-24-000002"
    filing.text.return_value = "Some plain text without section headers."
    filing.markdown.return_value = "# Filing\n\nSome plain text."
    filing.full_text = "Some plain text without section headers."
    return filing


@pytest.fixture
def mock_company() -> MagicMock:
    """Create a mock Company object mimicking edgartools Company.

    The mock has:
    - get_filings() returning a mock Filings object with latest() method

    Returns
    -------
    MagicMock
        A mock Company object with get_filings().latest() chain
    """
    company = MagicMock()

    mock_filings = MagicMock()
    mock_filing_list = [MagicMock(), MagicMock()]
    for i, f in enumerate(mock_filing_list):
        f.accession_number = f"000123456{i}-24-00000{i + 1}"
    mock_filings.latest.return_value = mock_filing_list

    company.get_filings.return_value = mock_filings
    return company


@pytest.fixture
def test_cache_db(tmp_path: Path) -> Path:
    """Create a temporary directory for test cache database.

    Parameters
    ----------
    tmp_path : Path
        pytest built-in temporary directory fixture

    Returns
    -------
    Path
        Path to the temporary cache directory
    """
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def mock_cache_hit() -> MagicMock:
    """Create a mock cache that returns cached text (cache hit).

    The mock returns "Cached text" for get_cached_text() calls,
    simulating a successful cache lookup.

    Returns
    -------
    MagicMock
        A mock cache object with get_cached_text returning "Cached text"
    """
    cache = MagicMock()
    cache.get_cached_text.return_value = "Cached text"
    return cache


@pytest.fixture
def mock_cache_miss() -> MagicMock:
    """Create a mock cache that returns None (cache miss).

    The mock returns None for get_cached_text() calls,
    simulating a cache miss.

    Returns
    -------
    MagicMock
        A mock cache object with get_cached_text returning None
    """
    cache = MagicMock()
    cache.get_cached_text.return_value = None
    return cache


@pytest.fixture
def mock_filings_chain() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Create a mock company_cls -> company -> filings chain for fetcher tests.

    Provides the standard three-level mock chain used by EdgarFetcher:
    company_cls(cik) -> company.get_filings(form=) -> filings.latest(limit)

    The filings.latest() returns an empty list by default. Tests should
    configure the return value as needed.

    Returns
    -------
    tuple[MagicMock, MagicMock, MagicMock]
        A tuple of (mock_company_cls, mock_company, mock_filings)
    """
    mock_filings = MagicMock()
    mock_filings.latest.return_value = []

    mock_company = MagicMock()
    mock_company.get_filings.return_value = mock_filings

    mock_company_cls = MagicMock(return_value=mock_company)

    return mock_company_cls, mock_company, mock_filings


@pytest.fixture
def patched_identity_config() -> Generator[MagicMock, None, None]:
    """Patch load_config to return is_identity_configured=True.

    Provides a context where the SEC EDGAR identity configuration
    check always passes, which is needed for most fetcher tests.

    Yields
    ------
    MagicMock
        The patched load_config mock
    """
    with patch("edgar.fetcher.load_config") as mock_config:
        mock_config.return_value = MagicMock(is_identity_configured=True)
        yield mock_config
