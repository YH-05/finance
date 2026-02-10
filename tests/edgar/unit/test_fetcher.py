"""Unit tests for edgar.fetcher module.

Tests for EdgarFetcher class including fetch() and fetch_latest() methods
with mocked edgartools Company class and configuration.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from edgar.errors import EdgarError, FilingNotFoundError
from edgar.fetcher import EdgarFetcher
from edgar.types import FilingType


class TestEdgarFetcherFetch:
    """Tests for EdgarFetcher.fetch() method."""

    def test_正常系_有効なCIKで10K取得成功(self) -> None:
        """fetch() should return filings for a valid CIK.

        Verify that fetch() calls Company(cik), get_filings(form=),
        and latest(limit) in the correct order.
        """
        mock_filing_list = [MagicMock(), MagicMock()]
        mock_filings = MagicMock()
        mock_filings.latest.return_value = mock_filing_list

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings

        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            result = fetcher.fetch("0000320193", FilingType.FORM_10K, limit=5)

        assert len(result) == 2
        mock_company_cls.assert_called_once_with("0000320193")
        mock_company.get_filings.assert_called_once_with(form="10-K")
        mock_filings.latest.assert_called_once_with(5)

    def test_正常系_有効なTickerで10Q取得成功(self) -> None:
        """fetch() should return filings for a valid ticker symbol.

        Verify that fetch() passes the ticker string directly to Company().
        """
        mock_filing_list = [MagicMock()]
        mock_filings = MagicMock()
        mock_filings.latest.return_value = mock_filing_list

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            result = fetcher.fetch("AAPL", FilingType.FORM_10Q, limit=3)

        assert len(result) == 1
        mock_company_cls.assert_called_once_with("AAPL")
        mock_company.get_filings.assert_called_once_with(form="10-Q")

    def test_正常系_limitで取得件数制限(self) -> None:
        """fetch() should pass limit to filings.latest().

        Verify that the limit parameter is forwarded correctly
        to the edgartools latest() method.
        """
        mock_filings = MagicMock()
        mock_filings.latest.return_value = []

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            fetcher.fetch("AAPL", FilingType.FORM_10K, limit=20)

        mock_filings.latest.assert_called_once_with(20)

    def test_正常系_デフォルトlimitは10件(self) -> None:
        """fetch() should use default limit of 10 when not specified.

        Verify that the default limit parameter value is 10.
        """
        mock_filings = MagicMock()
        mock_filings.latest.return_value = []

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            fetcher.fetch("AAPL", FilingType.FORM_10K)

        mock_filings.latest.assert_called_once_with(10)

    def test_異常系_identity未設定でEdgarError(self) -> None:
        """fetch() should raise EdgarError when identity is not configured.

        Verify that fetch() checks identity configuration before
        attempting to fetch filings.
        """
        fetcher = EdgarFetcher()

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=False)
            with pytest.raises(EdgarError, match="identity is not configured"):
                fetcher.fetch("AAPL", FilingType.FORM_10K)

    def test_異常系_not_foundエラーでFilingNotFoundError(self) -> None:
        """fetch() should raise FilingNotFoundError for 'not found' errors.

        Verify that ValueError containing 'not found' from edgartools
        is wrapped in FilingNotFoundError.
        """
        mock_company_cls = MagicMock(
            side_effect=ValueError("Company not found in EDGAR")
        )

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            with pytest.raises(FilingNotFoundError):
                fetcher.fetch("INVALID", FilingType.FORM_10K)

    def test_異常系_no_cikエラーでFilingNotFoundError(self) -> None:
        """fetch() should raise FilingNotFoundError for 'no cik' errors.

        Verify that errors containing 'no cik' from edgartools
        are wrapped in FilingNotFoundError.
        """
        mock_company_cls = MagicMock(side_effect=ValueError("No CIK found for ticker"))

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            with pytest.raises(FilingNotFoundError):
                fetcher.fetch("ZZZZZ", FilingType.FORM_10K)

    def test_異常系_予期しないエラーでEdgarError(self) -> None:
        """fetch() should wrap unexpected errors in EdgarError.

        Verify that non-domain errors (e.g., network timeouts) are
        wrapped in EdgarError with the original error preserved.
        """
        mock_company_cls = MagicMock(side_effect=RuntimeError("Network timeout"))

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            with pytest.raises(EdgarError, match="Failed to fetch filings"):
                fetcher.fetch("AAPL", FilingType.FORM_10K)

    def test_異常系_EdgarErrorはそのまま再送出される(self) -> None:
        """fetch() should re-raise EdgarError without wrapping.

        Verify that EdgarError raised during fetching is propagated
        directly without being wrapped in another EdgarError.
        """
        original_error = EdgarError("edgartools module error")
        mock_company_cls = MagicMock(side_effect=original_error)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            with pytest.raises(EdgarError) as exc_info:
                fetcher.fetch("AAPL", FilingType.FORM_10K)

        assert exc_info.value is original_error

    def test_エッジケース_Filingが0件で空リスト(self) -> None:
        """fetch() should return empty list when no filings found.

        Verify that fetch() returns an empty list when the company
        has no filings matching the specified form type.
        """
        mock_filings = MagicMock()
        mock_filings.latest.return_value = []

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            result = fetcher.fetch("AAPL", FilingType.FORM_10K)

        assert result == []

    def test_エッジケース_13Fフォームタイプで取得成功(self) -> None:
        """fetch() should correctly pass 13F form type value.

        Verify that fetch() handles all supported FilingType values
        including FORM_13F.
        """
        mock_filings = MagicMock()
        mock_filings.latest.return_value = [MagicMock()]

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            result = fetcher.fetch("AAPL", FilingType.FORM_13F, limit=1)

        assert len(result) == 1
        mock_company.get_filings.assert_called_once_with(form="13F")


class TestEdgarFetcherFetchLatest:
    """Tests for EdgarFetcher.fetch_latest() method."""

    def test_正常系_fetch_latestで最新Filing取得成功(self) -> None:
        """fetch_latest() should return the first filing from fetch().

        Verify that fetch_latest() calls fetch(limit=1) and returns
        the first element.
        """
        mock_filing = MagicMock()
        mock_filings = MagicMock()
        mock_filings.latest.return_value = [mock_filing]

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            result = fetcher.fetch_latest("AAPL", FilingType.FORM_10K)

        assert result is mock_filing
        mock_filings.latest.assert_called_once_with(1)

    def test_エッジケース_fetch_latestでFiling0件でNone(self) -> None:
        """fetch_latest() should return None when no filings found.

        Verify that fetch_latest() returns None instead of raising
        an error when the company has no filings.
        """
        mock_filings = MagicMock()
        mock_filings.latest.return_value = []

        mock_company = MagicMock()
        mock_company.get_filings.return_value = mock_filings
        mock_company_cls = MagicMock(return_value=mock_company)

        fetcher = EdgarFetcher()
        fetcher._company_cls = mock_company_cls

        with patch("edgar.fetcher.load_config") as mock_config:
            mock_config.return_value = MagicMock(is_identity_configured=True)
            result = fetcher.fetch_latest("AAPL", FilingType.FORM_10K)

        assert result is None


class TestEdgarFetcherInit:
    """Tests for EdgarFetcher initialization."""

    def test_正常系_初期化時にcompany_clsはNone(self) -> None:
        """EdgarFetcher should initialize with _company_cls as None.

        Verify lazy loading: Company class is not loaded during init.
        """
        fetcher = EdgarFetcher()
        assert fetcher._company_cls is None

    def test_正常系_get_company_clsで遅延ロード(self) -> None:
        """_get_company_cls() should lazy-load and cache the Company class.

        Verify that _get_company_cls() calls _import_edgartools_company()
        once and caches the result.
        """
        mock_cls = MagicMock()
        fetcher = EdgarFetcher()

        with patch("edgar.fetcher._import_edgartools_company", return_value=mock_cls):
            result1 = fetcher._get_company_cls()
            result2 = fetcher._get_company_cls()

        assert result1 is mock_cls
        assert result2 is mock_cls
