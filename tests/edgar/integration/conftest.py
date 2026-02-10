"""Shared test fixtures and helpers for edgar integration tests.

Provides mock Filing and Company objects used across E2E test modules,
particularly for batch extraction tests that require multi-company mock setups.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_accession_number(filing: object) -> str | None:
    """Extract accession number from an edgartools Filing object.

    edgartools versions differ in attribute naming: some use ``accession_no``
    while others use ``accession_number``.  This helper tries both to keep
    test assertions portable across versions.

    Parameters
    ----------
    filing : object
        An edgartools Filing object (or mock thereof).

    Returns
    -------
    str | None
        The accession number string, or ``None`` if neither attribute exists.
    """
    return getattr(filing, "accession_no", None) or getattr(
        filing, "accession_number", None
    )


# ---------------------------------------------------------------------------
# Sample filing text constants
# ---------------------------------------------------------------------------

SAMPLE_10K_TEXT = (
    "UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n"
    "Washington, D.C. 20549\n\n"
    "FORM 10-K\n\n"
    "Item 1. Business\n\n"
    "Apple Inc. designs, manufactures, and markets smartphones, "
    "personal computers, tablets, wearables, and accessories worldwide.\n\n"
    "Item 1A. Risk Factors\n\n"
    "The Company's business, reputation, results of operations, "
    "financial condition, and stock price can be affected by a number "
    "of factors.\n\n"
    "Item 7. Management's Discussion and Analysis of Financial "
    "Condition and Results of Operations\n\n"
    "The following discussion should be read in conjunction with the "
    "consolidated financial statements.\n\n"
    "Item 8. Financial Statements and Supplementary Data\n\n"
    "See the consolidated financial statements and notes thereto.\n"
)

SAMPLE_10Q_TEXT = (
    "UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n"
    "Washington, D.C. 20549\n\n"
    "FORM 10-Q\n\n"
    "Item 1. Business\n\n"
    "Microsoft Corporation develops, licenses, and supports software, "
    "services, devices, and solutions worldwide.\n\n"
    "Item 1A. Risk Factors\n\n"
    "We operate in a rapidly changing environment that involves a number "
    "of risks, some of which are beyond our control.\n\n"
    "Item 7. Management's Discussion and Analysis of Financial "
    "Condition and Results of Operations\n\n"
    "Revenue was $56.2 billion and increased 16%.\n\n"
    "Item 8. Financial Statements and Supplementary Data\n\n"
    "Refer to the financial statements and notes included herein.\n"
)

# ---------------------------------------------------------------------------
# Individual mock filing fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_filing_aapl() -> MagicMock:
    """Create a mock Apple 10-K Filing object.

    Returns
    -------
    MagicMock
        A mock Filing with Apple's accession number and 10-K sample text.
    """
    filing = MagicMock()
    filing.accession_number = "0000320193-24-000001"
    filing.text.return_value = SAMPLE_10K_TEXT
    return filing


@pytest.fixture
def mock_filing_msft() -> MagicMock:
    """Create a mock Microsoft 10-Q Filing object.

    Returns
    -------
    MagicMock
        A mock Filing with Microsoft's accession number and 10-Q sample text.
    """
    filing = MagicMock()
    filing.accession_number = "0000789019-24-000001"
    filing.text.return_value = SAMPLE_10Q_TEXT
    return filing


# ---------------------------------------------------------------------------
# Batch test fixtures (company chain mocks)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_batch_filings(
    mock_filing_aapl: MagicMock,
    mock_filing_msft: MagicMock,
) -> dict[str, MagicMock]:
    """Create a complete set of mocks for batch extraction tests.

    Builds the company -> filings -> filing chain for both AAPL and MSFT,
    plus a ``company_cls`` mock that returns them in order.

    Parameters
    ----------
    mock_filing_aapl : MagicMock
        Apple mock filing fixture.
    mock_filing_msft : MagicMock
        Microsoft mock filing fixture.

    Returns
    -------
    dict[str, MagicMock]
        Dictionary containing:
        - ``filing_aapl``: Apple mock filing
        - ``filing_msft``: Microsoft mock filing
        - ``company_aapl``: Apple mock company
        - ``company_msft``: Microsoft mock company
        - ``company_cls``: Mock class returning [company_aapl, company_msft]
    """
    # Apple company chain
    mock_filings_aapl = MagicMock()
    mock_filings_aapl.latest.return_value = [mock_filing_aapl]
    mock_company_aapl = MagicMock()
    mock_company_aapl.get_filings.return_value = mock_filings_aapl

    # Microsoft company chain
    mock_filings_msft = MagicMock()
    mock_filings_msft.latest.return_value = [mock_filing_msft]
    mock_company_msft = MagicMock()
    mock_company_msft.get_filings.return_value = mock_filings_msft

    # Company class mock returning both in order
    mock_company_cls = MagicMock(
        side_effect=[mock_company_aapl, mock_company_msft],
    )

    return {
        "filing_aapl": mock_filing_aapl,
        "filing_msft": mock_filing_msft,
        "company_aapl": mock_company_aapl,
        "company_msft": mock_company_msft,
        "company_cls": mock_company_cls,
    }
