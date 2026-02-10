"""Shared test fixtures for the edgar package tests.

Provides mock objects for edgartools Filing and Company classes,
and temporary directories for cache testing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
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
