"""Integration tests for EdgarFetcher.

Tests the interaction between EdgarFetcher and its dependencies
(config, error handling) using mock edgartools.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from edgar.config import SEC_EDGAR_IDENTITY_ENV
from edgar.errors import EdgarError, FilingNotFoundError
from edgar.fetcher import EdgarFetcher
from edgar.types import FilingType


@pytest.mark.integration
class TestFetcherIntegration:
    """Integration tests for EdgarFetcher with config system."""

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
