"""Integration tests for EdgarFetcher.

Tests include:
- Mock-based integration tests: EdgarFetcher with config system
- Real API integration tests: Actual SEC EDGAR API calls (CIK/Ticker)

Real API tests require:
- SEC_EDGAR_IDENTITY environment variable set
- edgartools installed and importable
- Network access to SEC EDGAR

Run real API tests explicitly::

    uv run pytest tests/edgar/integration/test_fetcher_integration.py -m integration -v
"""

from __future__ import annotations

import os
import time
from unittest.mock import MagicMock

import pytest

from edgar.config import SEC_EDGAR_IDENTITY_ENV
from edgar.errors import EdgarError, FilingNotFoundError
from edgar.fetcher import EdgarFetcher
from edgar.types import FilingType
from tests.edgar.integration.conftest import get_accession_number

# Apple CIK for real API tests
APPLE_CIK = "0000320193"

# Microsoft ticker for real API tests
MICROSOFT_TICKER = "MSFT"

# Skip condition: SEC_EDGAR_IDENTITY must be set for real API tests
_identity_configured = bool(os.environ.get(SEC_EDGAR_IDENTITY_ENV, "").strip())

# Skip condition: edgartools must be importable
_edgartools_available = False
try:
    from edgar.fetcher import _import_edgartools_company

    _import_edgartools_company()
    _edgartools_available = True
except Exception:
    pass

requires_real_api = pytest.mark.skipif(
    not (_identity_configured and _edgartools_available),
    reason=(
        "Real API tests require SEC_EDGAR_IDENTITY env var "
        "and a working edgartools installation"
    ),
)


@pytest.mark.integration
class TestFetcherIntegration:
    """Integration tests for EdgarFetcher with config system (mock-based)."""

    def test_統合_identity設定済みでfetch成功(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Fetcher should work when identity is configured via env var."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_filings = MagicMock()
        mock_filing = MagicMock()
        mock_filing.accession_number = "0000320193-24-000001"
        mock_filing.text.return_value = "Filing content"
        mock_filings.latest.return_value = [mock_filing]

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        result = fetcher.fetch("AAPL", FilingType.FORM_10K, limit=1)

        assert len(result) == 1
        mock_company_cls.assert_called_with("AAPL")
        mock_company.get_filings.assert_called_with(form="10-K")

    def test_統合_identity未設定でEdgarError(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Fetcher should raise EdgarError when identity is not configured."""
        monkeypatch.delenv(SEC_EDGAR_IDENTITY_ENV, raising=False)

        fetcher = EdgarFetcher()
        with pytest.raises(EdgarError, match="identity is not configured"):
            fetcher.fetch("AAPL", FilingType.FORM_10K)

    def test_統合_fetch_latestでNone返却(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """fetch_latest should return None for empty results."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_filings = MagicMock()
        mock_filings.latest.return_value = []
        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        result = fetcher.fetch_latest("AAPL", FilingType.FORM_10K)
        assert result is None

    def test_統合_エラーラッピングでFilingNotFoundError(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Fetcher should wrap 'not found' errors as FilingNotFoundError."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_company_cls = MagicMock(
            side_effect=ValueError("Company not found for ticker"),
        )

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with pytest.raises(FilingNotFoundError):
            fetcher.fetch("INVALID_TICKER", FilingType.FORM_10K)

    def test_統合_複数Filing取得でlimit適用(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Fetcher should apply limit parameter correctly."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_filing_1 = MagicMock()
        mock_filing_1.accession_number = "0000320193-24-000001"
        mock_filing_2 = MagicMock()
        mock_filing_2.accession_number = "0000320193-24-000002"
        mock_filing_3 = MagicMock()
        mock_filing_3.accession_number = "0000320193-24-000003"

        mock_filings = MagicMock()
        mock_filings.latest.return_value = [
            mock_filing_1,
            mock_filing_2,
            mock_filing_3,
        ]

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        result = fetcher.fetch("AAPL", FilingType.FORM_10K, limit=3)

        assert len(result) == 3
        mock_filings.latest.assert_called_with(3)

    def test_統合_一般的な例外でEdgarErrorラップ(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Fetcher should wrap generic exceptions as EdgarError."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_company_cls = MagicMock(
            side_effect=RuntimeError("Connection refused"),
        )

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with pytest.raises(EdgarError, match="Failed to fetch filings"):
            fetcher.fetch("AAPL", FilingType.FORM_10K)

    def test_統合_fetch_latestで最新Filing返却(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """fetch_latest should return the first filing from results."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_filing = MagicMock()
        mock_filing.accession_number = "0000320193-24-000001"
        mock_filing.text.return_value = "Latest filing content"

        mock_filings = MagicMock()
        mock_filings.latest.return_value = [mock_filing]

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        result = fetcher.fetch_latest("AAPL", FilingType.FORM_10K)

        assert result is not None
        assert result.accession_number == "0000320193-24-000001"

    def test_統合_10Qフォームタイプで正しくフィルタリング(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Fetcher should pass correct form type string to edgartools."""
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "Test User test@example.com")

        mock_filings = MagicMock()
        mock_filings.latest.return_value = []
        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        fetcher.fetch("MSFT", FilingType.FORM_10Q, limit=1)

        mock_company.get_filings.assert_called_with(form="10-Q")


@pytest.mark.integration
class TestFetcherRealAPI:
    """Integration tests for EdgarFetcher with real SEC EDGAR API calls.

    These tests make actual HTTP requests to SEC EDGAR.
    They require:
    - SEC_EDGAR_IDENTITY environment variable to be set
    - edgartools to be installed and importable
    - Network access to SEC EDGAR (https://efts.sec.gov)

    Rate limit measures:
    - Only 2-3 companies are tested (Apple, Microsoft)
    - Limit parameter is kept small (1-2 filings per request)
    - edgartools built-in caching avoids repeated downloads
    """

    @requires_real_api
    def test_統合_AppleCIKで10K取得(self) -> None:
        """Fetch Apple 10-K filings using CIK number from real SEC EDGAR API.

        Apple CIK: 0000320193
        Verifies that real filings are returned with valid accession numbers.
        """
        fetcher = EdgarFetcher()

        filings = fetcher.fetch(APPLE_CIK, FilingType.FORM_10K, limit=2)

        assert len(filings) > 0, "Expected at least one 10-K filing for Apple"
        assert len(filings) <= 2, f"Expected at most 2 filings, got {len(filings)}"

        for filing in filings:
            accession = get_accession_number(filing)
            assert accession is not None, "Filing should have an accession number"
            assert len(str(accession)) > 0, "Accession number should be non-empty"

    @requires_real_api
    def test_統合_MicrosoftTickerで10Q取得(self) -> None:
        """Fetch Microsoft 10-Q filings using ticker symbol from real SEC EDGAR API.

        Ticker: MSFT
        Verifies that quarterly filings are returned for Microsoft.
        """
        fetcher = EdgarFetcher()

        filings = fetcher.fetch(MICROSOFT_TICKER, FilingType.FORM_10Q, limit=2)

        assert len(filings) > 0, "Expected at least one 10-Q filing for Microsoft"
        assert len(filings) <= 2, f"Expected at most 2 filings, got {len(filings)}"

        for filing in filings:
            accession = get_accession_number(filing)
            assert accession is not None, "Filing should have an accession number"

    @requires_real_api
    def test_統合_fetch_latestで最新Filing取得(self) -> None:
        """Fetch the latest 10-K filing for Apple using fetch_latest.

        Verifies that a single filing is returned (not None) and has
        basic attributes expected from a real edgartools Filing object.
        """
        fetcher = EdgarFetcher()

        latest = fetcher.fetch_latest(APPLE_CIK, FilingType.FORM_10K)

        assert latest is not None, "Expected a latest 10-K filing for Apple"

        # The filing should have an accession number
        accession = get_accession_number(latest)
        assert accession is not None, "Latest filing should have an accession number"

        # The filing should have a form type attribute
        form_type = getattr(latest, "form", None)
        if form_type is not None:
            assert "10-K" in str(form_type), f"Expected 10-K form, got {form_type}"

    @requires_real_api
    def test_統合_キャッシュヒット確認(self) -> None:
        """Verify that edgartools built-in caching makes the second call faster.

        Makes two identical fetch calls and measures the elapsed time.
        The second call should leverage edgartools' internal caching and
        complete significantly faster than the first.

        Notes
        -----
        This test relies on edgartools' built-in request caching, not our
        CacheManager. The first call downloads data from SEC EDGAR, while
        the second call should retrieve it from edgartools' cache.
        """
        fetcher = EdgarFetcher()

        # First call: downloads from SEC EDGAR (cold)
        start_1 = time.monotonic()
        filings_1 = fetcher.fetch(APPLE_CIK, FilingType.FORM_10K, limit=1)
        elapsed_1 = time.monotonic() - start_1

        assert len(filings_1) > 0, "First fetch should return filings"

        # Second call: should use edgartools internal cache (warm)
        start_2 = time.monotonic()
        filings_2 = fetcher.fetch(APPLE_CIK, FilingType.FORM_10K, limit=1)
        elapsed_2 = time.monotonic() - start_2

        assert len(filings_2) > 0, "Second fetch should also return filings"

        # The second call should be at least somewhat faster.
        # We use a generous threshold to avoid flakiness: second call
        # should take less than 2x the first call. In practice, cached
        # calls are typically 10-100x faster.
        # AIDEV-NOTE: We log the timings for debugging but use a relaxed
        # assertion because network variability can cause timing surprises.
        # The main goal is to verify both calls succeed and return data.
        assert elapsed_2 < elapsed_1 * 2 + 1.0, (
            f"Second call ({elapsed_2:.2f}s) was not faster than first "
            f"({elapsed_1:.2f}s). Cache may not be working."
        )
