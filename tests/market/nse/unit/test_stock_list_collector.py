"""Unit tests for market.nse.collectors.stock_list module.

StockListCollector の動作を検証するテストスイート。
DataCollector ABC を継承した NSE StockListCollector のテスト。

Test TODO List:
- [x] StockListCollector: デフォルト値で初期化（session なし）
- [x] StockListCollector: DI パターンで session 注入
- [x] fetch(): CSV ダウンロードで株式リスト取得
- [x] validate(): 有効な DataFrame で True
- [x] validate(): 空 DataFrame で False
- [x] validate(): 必須カラム不足で False
- [x] fetch_stock_list(): EQUITY_L.csv を DataFrame で取得
- [x] fetch_stock_list(): 正しい URL にリクエスト
- [x] fetch_stock_list(): セッションを正しくクローズ
- [x] fetch_preopen(): プレオープンデータを DataFrame で取得
- [x] fetch_preopen(): 正しいエンドポイントにリクエスト
- [x] fetch_market_turnover(): マーケットターンオーバーを辞書で取得
- [x] fetch_market_turnover(): 正しいエンドポイントにリクエスト
- [x] Module exports: __all__ completeness
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.nse.collectors.stock_list import StockListCollector
from market.nse.session import NseSession

# =============================================================================
# Helper: create mock CSV content and JSON responses
# =============================================================================


def _make_equity_csv() -> str:
    """Create a mock EQUITY_L.csv content."""
    return (
        "SYMBOL,NAME OF COMPANY,SERIES,DATE OF LISTING,"
        "PAID UP VALUE,MARKET LOT,ISIN NUMBER,FACE VALUE\n"
        "RELIANCE,Reliance Industries Limited,EQ,29-NOV-1995,"
        "10,1,INE002A01018,10\n"
        "INFY,Infosys Limited,EQ,08-FEB-1995,"
        "5,1,INE009A01021,5\n"
    )


def _make_preopen_json() -> dict:
    """Create a mock NSE /api/market-data-pre-open JSON response."""
    return {
        "data": [
            {
                "symbol": "RELIANCE",
                "iep": 2450.0,
                "chn": 25.0,
                "perChn": 1.03,
                "pCls": 2425.0,
                "trdQnty": 50000,
                "iVal": 122500000.0,
                "sumVal": 123000000.0,
                "sumQnty": 50200,
                "finQnty": 50000,
                "sbrdQnty": 0,
            }
        ]
    }


def _make_market_turnover_json() -> dict:
    """Create a mock NSE /api/market-turnover JSON response."""
    return {
        "CM": {
            "tradedQty": "50000000",
            "turnOver": "1250000000.00",
            "deliverableQty": "25000000",
        },
        "FO": {
            "tradedQty": "80000000",
            "turnOver": "3500000000.00",
        },
    }


def _make_mock_session_csv() -> MagicMock:
    """Create a mock NseSession returning CSV bytes."""
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    mock_response.content = _make_equity_csv().encode("utf-8")
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


def _make_mock_session_json(response_json: dict) -> MagicMock:
    """Create a mock NseSession returning a JSON dict."""
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    mock_response.json.return_value = response_json
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


# =============================================================================
# Tests: Initialization
# =============================================================================


class TestStockListCollectorInit:
    def test_正常系_デフォルト値で初期化(self) -> None:
        collector = StockListCollector()
        assert collector._session_instance is None

    def test_正常系_session注入で初期化(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = StockListCollector(session=mock_session)
        assert collector._session_instance is mock_session


# =============================================================================
# Tests: fetch()
# =============================================================================


class TestFetch:
    def test_正常系_CSVダウンロードで株式リスト取得(self) -> None:
        mock_session = _make_mock_session_csv()
        collector = StockListCollector(session=mock_session)
        df = collector.fetch()
        assert isinstance(df, pd.DataFrame)
        assert "symbol" in df.columns
        assert len(df) == 2

    def test_異常系_APIエラー時に例外を伝播(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        mock_session.get_with_retry.side_effect = RuntimeError("API Error")
        collector = StockListCollector(session=mock_session)
        with pytest.raises(RuntimeError, match="API Error"):
            collector.fetch()


# =============================================================================
# Tests: validate()
# =============================================================================


class TestValidate:
    def test_正常系_有効なDataFrameでTrue(self) -> None:
        collector = StockListCollector(session=MagicMock(spec=NseSession))
        df = pd.DataFrame({"symbol": ["RELIANCE", "INFY"]})
        assert collector.validate(df) is True

    def test_異常系_空DataFrameでFalse(self) -> None:
        collector = StockListCollector(session=MagicMock(spec=NseSession))
        assert collector.validate(pd.DataFrame()) is False

    def test_異常系_必須カラム不足でFalse(self) -> None:
        collector = StockListCollector(session=MagicMock(spec=NseSession))
        df = pd.DataFrame({"price": [2470.25]})
        assert collector.validate(df) is False


# =============================================================================
# Tests: fetch_stock_list()
# =============================================================================


class TestFetchStockList:
    def test_正常系_EQUITY_CSVをDataFrameで取得(self) -> None:
        mock_session = _make_mock_session_csv()
        collector = StockListCollector(session=mock_session)
        df = collector.fetch_stock_list()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "symbol" in df.columns
        symbols = df["symbol"].tolist()
        assert "RELIANCE" in symbols
        assert "INFY" in symbols

    def test_正常系_正しいURLにリクエスト(self) -> None:
        mock_session = _make_mock_session_csv()
        collector = StockListCollector(session=mock_session)
        collector.fetch_stock_list()
        call_args = mock_session.get_with_retry.call_args
        assert "EQUITY_L.csv" in call_args[0][0]

    def test_正常系_注入セッションはクローズしない(self) -> None:
        mock_session = _make_mock_session_csv()
        collector = StockListCollector(session=mock_session)
        collector.fetch_stock_list()
        mock_session.close.assert_not_called()

    def test_正常系_非注入セッションはクローズする(self) -> None:
        mock_new_session = _make_mock_session_csv()
        with patch(
            "market.nse.collectors._base.NseSession", return_value=mock_new_session
        ):
            collector = StockListCollector()
            collector.fetch_stock_list()
        mock_new_session.close.assert_called_once()


# =============================================================================
# Tests: fetch_preopen()
# =============================================================================


class TestFetchPreopen:
    def test_正常系_プレオープンデータをDataFrameで取得(self) -> None:
        mock_session = _make_mock_session_json(_make_preopen_json())
        collector = StockListCollector(session=mock_session)
        df = collector.fetch_preopen()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "symbol" in df.columns
        assert df["symbol"].iloc[0] == "RELIANCE"

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        mock_session = _make_mock_session_json(_make_preopen_json())
        collector = StockListCollector(session=mock_session)
        collector.fetch_preopen()
        call_args = mock_session.get_with_retry.call_args
        assert "market-data-pre-open" in call_args[0][0]
        assert call_args[1]["params"]["key"] == "ALL"


# =============================================================================
# Tests: fetch_market_turnover()
# =============================================================================


class TestFetchMarketTurnover:
    def test_正常系_マーケットターンオーバーを辞書で取得(self) -> None:
        turnover_json = _make_market_turnover_json()
        mock_session = _make_mock_session_json(turnover_json)
        collector = StockListCollector(session=mock_session)
        turnover = collector.fetch_market_turnover()
        assert isinstance(turnover, dict)
        assert "CM" in turnover

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        mock_session = _make_mock_session_json(_make_market_turnover_json())
        collector = StockListCollector(session=mock_session)
        collector.fetch_market_turnover()
        call_args = mock_session.get_with_retry.call_args
        assert "market-turnover" in call_args[0][0]


# =============================================================================
# Tests: Module exports
# =============================================================================


class TestModuleExports:
    def test_正常系_all完全性(self) -> None:
        from market.nse.collectors import stock_list as module

        assert "StockListCollector" in module.__all__
