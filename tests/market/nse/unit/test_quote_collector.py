"""Unit tests for market.nse.collectors.quote module.

QuoteCollector の動作を検証するテストスイート。
DataCollector ABC を継承した NSE QuoteCollector のテスト。

Test TODO List:
- [x] QuoteCollector: デフォルト値で初期化（session なし）
- [x] QuoteCollector: DI パターンで session 注入
- [x] _get_session(): 注入なし時に新規セッション生成（should_close=True）
- [x] _get_session(): 注入あり時に既存セッション返却（should_close=False）
- [x] fetch(): symbol で単一銘柄取得
- [x] fetch(): symbol 未指定で ValueError
- [x] fetch(): API エラー時に例外を伝播
- [x] validate(): 有効な DataFrame で True
- [x] validate(): 空 DataFrame で False
- [x] validate(): 必須カラム不足で False
- [x] fetch_quote(): 単一銘柄のクオートを取得
- [x] fetch_quote(): セッションを正しくクローズ
- [x] Module exports: __all__ completeness
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.nse.collectors.quote import QuoteCollector
from market.nse.session import NseSession
from market.nse.types import StockQuote

# =============================================================================
# Helper: create mock session and response
# =============================================================================


def _make_quote_json(
    *,
    symbol: str = "RELIANCE",
    company_name: str = "Reliance Industries Limited",
    series: str = "EQ",
) -> dict:
    """Create a mock NSE API quote JSON response."""
    return {
        "info": {
            "symbol": symbol,
            "companyName": company_name,
            "isin": "INE002A01018",
            "isFNOSec": True,
            "isSLBSec": False,
            "isSuspended": False,
            "listingDate": "1995-11-29",
            "segment": "EQUITY",
        },
        "metadata": {
            "series": series,
            "pdSectorPe": 25.0,
            "pdSymbolPe": 28.0,
            "pdSectorInd": "NIFTY 50",
        },
        "priceInfo": {
            "lastPrice": 2470.25,
            "change": 25.25,
            "pChange": 1.03,
            "previousClose": 2445.00,
            "open": 2450.00,
            "vwap": 2462.0,
            "lowerCP": "2200.75",
            "upperCP": "2689.75",
            "basePrice": 2445.00,
            "intraDayHighLow": {"min": 2440.00, "max": 2480.50},
            "weekHighLow": {
                "min": 2100.00,
                "minDate": "19-Mar-2025",
                "max": 2900.00,
                "maxDate": "03-Feb-2025",
            },
            "totalTradedVolume": 5000000,
            "totalTradedValue": 12345678900.00,
        },
        "securityInfo": {
            "faceValue": 10,
            "issuedSize": 6765990200,
            "boardStatus": "Main",
            "tradingStatus": "Active",
        },
        "industryInfo": {
            "macro": "Oil & Gas",
            "sector": "Oil Gas & Consumable Fuels",
            "industry": "Oil & Gas - Refining & Marketing",
            "basicIndustry": "Refineries & Marketing",
        },
    }


def _make_mock_session(
    *,
    response_json: dict | None = None,
) -> MagicMock:
    """Create a mock NseSession with pre-configured responses.

    Parameters
    ----------
    response_json : dict | None
        JSON response for get_with_retry(). Uses default quote if None.

    Returns
    -------
    MagicMock
        A mock NseSession instance.
    """
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    mock_response.json.return_value = response_json or _make_quote_json()
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


# =============================================================================
# Tests: Initialization
# =============================================================================


class TestQuoteCollectorInit:
    def test_正常系_デフォルト値で初期化(self) -> None:
        collector = QuoteCollector()
        assert collector._session_instance is None

    def test_正常系_session注入で初期化(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = QuoteCollector(session=mock_session)
        assert collector._session_instance is mock_session


# =============================================================================
# Tests: _get_session
# =============================================================================


class TestGetSession:
    def test_正常系_注入なし時に新規セッション生成(self) -> None:
        collector = QuoteCollector()
        with patch("market.nse.collectors._base.NseSession") as mock_cls:
            mock_instance = MagicMock(spec=NseSession)
            mock_cls.return_value = mock_instance
            session, should_close = collector._get_session()
        assert should_close is True
        assert session is mock_instance

    def test_正常系_注入あり時に既存セッション返却(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = QuoteCollector(session=mock_session)
        session, should_close = collector._get_session()
        assert should_close is False
        assert session is mock_session


# =============================================================================
# Tests: fetch()
# =============================================================================


class TestFetch:
    def test_正常系_symbol指定でDataFrame取得(self) -> None:
        mock_session = _make_mock_session()
        collector = QuoteCollector(session=mock_session)
        df = collector.fetch(symbol="RELIANCE")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "symbol" in df.columns
        assert df["symbol"].iloc[0] == "RELIANCE"

    def test_異常系_symbol未指定でValueError(self) -> None:
        collector = QuoteCollector(session=MagicMock(spec=NseSession))
        with pytest.raises(ValueError, match="symbol is required"):
            collector.fetch()

    def test_異常系_APIエラー時に例外を伝播(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        mock_session.get_with_retry.side_effect = RuntimeError("API Error")
        collector = QuoteCollector(session=mock_session)
        with pytest.raises(RuntimeError, match="API Error"):
            collector.fetch(symbol="RELIANCE")


# =============================================================================
# Tests: validate()
# =============================================================================


class TestValidate:
    def test_正常系_有効なDataFrameでTrue(self) -> None:
        collector = QuoteCollector(session=MagicMock(spec=NseSession))
        df = pd.DataFrame(
            {
                "symbol": ["RELIANCE"],
                "company_name": ["Reliance Industries Limited"],
            }
        )
        assert collector.validate(df) is True

    def test_異常系_空DataFrameでFalse(self) -> None:
        collector = QuoteCollector(session=MagicMock(spec=NseSession))
        assert collector.validate(pd.DataFrame()) is False

    def test_異常系_必須カラム不足でFalse(self) -> None:
        collector = QuoteCollector(session=MagicMock(spec=NseSession))
        df = pd.DataFrame({"price": [2470.25]})
        assert collector.validate(df) is False


# =============================================================================
# Tests: fetch_quote()
# =============================================================================


class TestFetchQuote:
    def test_正常系_単一銘柄のクオートを取得(self) -> None:
        mock_session = _make_mock_session()
        collector = QuoteCollector(session=mock_session)
        quote = collector.fetch_quote("RELIANCE")
        assert isinstance(quote, StockQuote)
        assert quote.symbol == "RELIANCE"
        assert quote.company_name == "Reliance Industries Limited"

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        mock_session = _make_mock_session()
        collector = QuoteCollector(session=mock_session)
        collector.fetch_quote("RELIANCE")
        call_args = mock_session.get_with_retry.call_args
        assert "quote-equity" in call_args[0][0]
        assert call_args[1]["params"]["symbol"] == "RELIANCE"

    def test_正常系_注入セッションは_クローズしない(self) -> None:
        mock_session = _make_mock_session()
        collector = QuoteCollector(session=mock_session)
        collector.fetch_quote("RELIANCE")
        mock_session.close.assert_not_called()

    def test_正常系_非注入セッションはクローズする(self) -> None:
        mock_new_session = _make_mock_session()
        with patch(
            "market.nse.collectors._base.NseSession", return_value=mock_new_session
        ):
            collector = QuoteCollector()
            collector.fetch_quote("RELIANCE")
        mock_new_session.close.assert_called_once()


# =============================================================================
# Tests: Module exports
# =============================================================================


class TestModuleExports:
    def test_正常系_all完全性(self) -> None:
        from market.nse.collectors import quote as module

        assert "QuoteCollector" in module.__all__
