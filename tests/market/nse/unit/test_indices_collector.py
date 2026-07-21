"""Unit tests for market.nse.collectors.indices module.

IndicesCollector の動作を検証するテストスイート。
DataCollector ABC を継承した NSE IndicesCollector のテスト。

Test TODO List:
- [x] IndicesCollector: デフォルト値で初期化（session なし）
- [x] IndicesCollector: DI パターンで session 注入
- [x] fetch(): index_name で構成銘柄取得
- [x] fetch(): index_name 未指定で ValueError
- [x] validate(): 有効な DataFrame で True
- [x] validate(): 空 DataFrame で False
- [x] validate(): 必須カラム不足で False
- [x] fetch_index(): インデックス構成銘柄を DataFrame で取得
- [x] fetch_index(): 正しいエンドポイントにリクエスト
- [x] fetch_index(): セッションを正しくクローズ
- [x] fetch_all_indices(): 全インデックス概要を取得
- [x] fetch_market_status(): マーケットステータスを取得
- [x] fetch_index_constituents_archive(): 静的CSVから構成銘柄を DataFrame で取得
- [x] fetch_index_constituents_archive(): 正しいURLにリクエスト
- [x] fetch_index_constituents_archive(): index_name のファイル名マッピング
- [x] fetch_index_constituents_archive(): 未知の index_name で ValueError
- [x] fetch_index_constituents_archive(): 空 CSV で空 DataFrame
- [x] fetch_index_constituents_archive(): Symbol 列の前後空白除去
- [x] fetch_index_constituents_archive(): セッションを正しくクローズ
- [x] Module exports: __all__ completeness
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.nse.collectors.indices import IndicesCollector
from market.nse.session import NseSession
from market.nse.types import MarketStatus

# =============================================================================
# Helper: create mock session and responses
# =============================================================================


def _make_equity_stock_indices_json(
    *,
    index_name: str = "NIFTY 50",
    symbols: list[str] | None = None,
) -> dict:
    """Create a mock NSE /api/equity-stockIndices JSON response."""
    if symbols is None:
        symbols = ["RELIANCE", "INFY"]

    data: list[dict] = [
        # First entry is the index metadata (priority=1, no series)
        {
            "symbol": index_name,
            "open": 22500.00,
            "dayHigh": 22750.50,
            "dayLow": 22450.00,
            "lastPrice": 22700.25,
            "previousClose": 22450.00,
            "change": 250.25,
            "pChange": 1.11,
            "totalTradedVolume": 250000000,
            "totalTradedValue": 5625000000.00,
            "yearHigh": 24200.00,
            "yearLow": 19800.00,
            "priority": 1,
        }
    ]
    for sym in symbols:
        data.append(
            {
                "symbol": sym,
                "series": "EQ",
                "open": "2450.00",
                "dayHigh": "2480.50",
                "dayLow": "2440.00",
                "lastPrice": "2470.25",
                "previousClose": "2445.00",
                "change": "25.25",
                "pChange": "1.03",
                "totalTradedVolume": "5000000",
                "totalTradedValue": "12345678900.00",
                "yearHigh": "2900.00",
                "yearLow": "2100.00",
                "priority": 0,
            }
        )

    return {
        "name": index_name,
        "timestamp": "02-Apr-2026 15:30:00",
        "data": data,
    }


def _make_all_indices_json() -> dict:
    """Create a mock NSE /api/allIndices JSON response."""
    return {
        "data": [
            {
                "indexSymbol": "NIFTY 50",
                "current": 22371.8,
                "variation": -307.6,
                "percentChange": -1.36,
                "open": 22383.4,
                "high": 22406.0,
                "low": 22182.55,
                "previousClose": 22679.4,
                "yearHigh": 26373.2,
                "yearLow": 21743.65,
            }
        ]
    }


def _make_market_status_json() -> dict:
    """Create a mock NSE /api/marketStatus JSON response."""
    return {
        "marketState": [
            {
                "market": "Capital Market",
                "marketStatus": "Open",
                "tradeDate": "02-Apr-2026",
                "index": "NIFTY 50",
                "last": "22371.80",
                "variation": "-307.60",
                "percentChange": "-1.36",
            }
        ]
    }


def _make_mock_session(
    *,
    response_json: dict | None = None,
) -> MagicMock:
    """Create a mock NseSession with pre-configured responses."""
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    mock_response.json.return_value = (
        response_json
        if response_json is not None
        else _make_equity_stock_indices_json()
    )
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


_INDEX_ARCHIVE_CSV_SAMPLE: str = (
    "Company Name,Industry,Symbol,Series,ISIN Code\n"
    "Reliance Industries Limited,Oil Gas & Consumable Fuels,RELIANCE,EQ,INE002A01018\n"
    "Infosys Limited,Information Technology,INFY,EQ,INE009A01021\n"
)
"""Sample NSE index constituents archive CSV content (ind_niftyXXXlist.csv format)."""


def _make_mock_csv_session(*, csv_content: str | None = None) -> MagicMock:
    """Create a mock NseSession returning archive CSV content."""
    mock_session = MagicMock(spec=NseSession)
    mock_response = MagicMock()
    content = csv_content if csv_content is not None else _INDEX_ARCHIVE_CSV_SAMPLE
    mock_response.content = content.encode("utf-8")
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


# =============================================================================
# Tests: Initialization
# =============================================================================


class TestIndicesCollectorInit:
    def test_正常系_デフォルト値で初期化(self) -> None:
        collector = IndicesCollector()
        assert collector._session_instance is None

    def test_正常系_session注入で初期化(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        collector = IndicesCollector(session=mock_session)
        assert collector._session_instance is mock_session


# =============================================================================
# Tests: fetch()
# =============================================================================


class TestFetch:
    def test_正常系_index_name指定でDataFrame取得(self) -> None:
        mock_session = _make_mock_session()
        collector = IndicesCollector(session=mock_session)
        df = collector.fetch(index_name="NIFTY 50")
        assert isinstance(df, pd.DataFrame)
        assert "symbol" in df.columns

    def test_異常系_index_name未指定でValueError(self) -> None:
        collector = IndicesCollector(session=MagicMock(spec=NseSession))
        with pytest.raises(ValueError, match="index_name is required"):
            collector.fetch()

    def test_異常系_APIエラー時に例外を伝播(self) -> None:
        mock_session = MagicMock(spec=NseSession)
        mock_session.get_with_retry.side_effect = RuntimeError("API Error")
        collector = IndicesCollector(session=mock_session)
        with pytest.raises(RuntimeError, match="API Error"):
            collector.fetch(index_name="NIFTY 50")


# =============================================================================
# Tests: validate()
# =============================================================================


class TestValidate:
    def test_正常系_有効なDataFrameでTrue(self) -> None:
        collector = IndicesCollector(session=MagicMock(spec=NseSession))
        df = pd.DataFrame({"symbol": ["RELIANCE", "INFY"]})
        assert collector.validate(df) is True

    def test_異常系_空DataFrameでFalse(self) -> None:
        collector = IndicesCollector(session=MagicMock(spec=NseSession))
        assert collector.validate(pd.DataFrame()) is False

    def test_異常系_必須カラム不足でFalse(self) -> None:
        collector = IndicesCollector(session=MagicMock(spec=NseSession))
        df = pd.DataFrame({"price": [2470.25]})
        assert collector.validate(df) is False


# =============================================================================
# Tests: fetch_index()
# =============================================================================


class TestFetchIndex:
    def test_正常系_インデックス構成銘柄をDataFrameで取得(self) -> None:
        mock_session = _make_mock_session()
        collector = IndicesCollector(session=mock_session)
        df = collector.fetch_index("NIFTY 50")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # RELIANCE, INFY
        assert "symbol" in df.columns
        symbols = df["symbol"].tolist()
        assert "RELIANCE" in symbols

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        mock_session = _make_mock_session()
        collector = IndicesCollector(session=mock_session)
        collector.fetch_index("NIFTY BANK")
        call_args = mock_session.get_with_retry.call_args
        assert "equity-stockIndices" in call_args[0][0]
        assert call_args[1]["params"]["index"] == "NIFTY BANK"

    def test_正常系_注入セッションはクローズしない(self) -> None:
        mock_session = _make_mock_session()
        collector = IndicesCollector(session=mock_session)
        collector.fetch_index("NIFTY 50")
        mock_session.close.assert_not_called()

    def test_正常系_非注入セッションはクローズする(self) -> None:
        mock_new_session = _make_mock_session()
        with patch(
            "market.nse.collectors._base.NseSession", return_value=mock_new_session
        ):
            collector = IndicesCollector()
            collector.fetch_index("NIFTY 50")
        mock_new_session.close.assert_called_once()


# =============================================================================
# Tests: fetch_index_constituents_archive()
# =============================================================================


class TestFetchIndexConstituentsArchive:
    def test_正常系_静的CSVから構成銘柄をDataFrameで取得(self) -> None:
        mock_session = _make_mock_csv_session()
        collector = IndicesCollector(session=mock_session)
        df = collector.fetch_index_constituents_archive("NIFTY 50")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == [
            "company_name",
            "industry",
            "symbol",
            "series",
            "isin",
        ]
        assert df["symbol"].tolist() == ["RELIANCE", "INFY"]

    def test_正常系_正しいURLにリクエストNIFTY50(self) -> None:
        mock_session = _make_mock_csv_session()
        collector = IndicesCollector(session=mock_session)
        collector.fetch_index_constituents_archive("NIFTY 50")
        call_args = mock_session.get_with_retry.call_args
        assert (
            call_args[0][0]
            == "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"
        )

    def test_正常系_NIFTY_TOTAL_MKTの不規則なファイル名マッピング(self) -> None:
        mock_session = _make_mock_csv_session()
        collector = IndicesCollector(session=mock_session)
        collector.fetch_index_constituents_archive("NIFTY TOTAL MKT")
        call_args = mock_session.get_with_retry.call_args
        assert (
            call_args[0][0]
            == "https://nsearchives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv"
        )

    def test_正常系_NIFTY500のファイル名マッピング(self) -> None:
        mock_session = _make_mock_csv_session()
        collector = IndicesCollector(session=mock_session)
        collector.fetch_index_constituents_archive("NIFTY 500")
        call_args = mock_session.get_with_retry.call_args
        assert (
            call_args[0][0]
            == "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
        )

    def test_異常系_未知のindex_nameでValueError(self) -> None:
        collector = IndicesCollector(session=MagicMock(spec=NseSession))
        with pytest.raises(ValueError, match="Unknown index_name"):
            collector.fetch_index_constituents_archive("NIFTY JUNK")

    def test_エッジケース_空CSVで空DataFrame(self) -> None:
        mock_session = _make_mock_csv_session(
            csv_content="Company Name,Industry,Symbol,Series,ISIN Code\n"
        )
        collector = IndicesCollector(session=mock_session)
        df = collector.fetch_index_constituents_archive("NIFTY 50")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_エッジケース_Symbol列の前後空白を除去(self) -> None:
        csv_content = (
            "Company Name,Industry,Symbol,Series,ISIN Code\n"
            "Reliance Industries Limited,Oil Gas,  RELIANCE  ,EQ,INE002A01018\n"
        )
        mock_session = _make_mock_csv_session(csv_content=csv_content)
        collector = IndicesCollector(session=mock_session)
        df = collector.fetch_index_constituents_archive("NIFTY 50")
        assert df["symbol"].iloc[0] == "RELIANCE"

    def test_正常系_注入セッションはクローズしない(self) -> None:
        mock_session = _make_mock_csv_session()
        collector = IndicesCollector(session=mock_session)
        collector.fetch_index_constituents_archive("NIFTY 50")
        mock_session.close.assert_not_called()

    def test_正常系_非注入セッションはクローズする(self) -> None:
        mock_new_session = _make_mock_csv_session()
        with patch(
            "market.nse.collectors._base.NseSession", return_value=mock_new_session
        ):
            collector = IndicesCollector()
            collector.fetch_index_constituents_archive("NIFTY 50")
        mock_new_session.close.assert_called_once()


# =============================================================================
# Tests: fetch_all_indices()
# =============================================================================


class TestFetchAllIndices:
    def test_正常系_全インデックス概要をDataFrameで取得(self) -> None:
        mock_session = _make_mock_session(response_json=_make_all_indices_json())
        collector = IndicesCollector(session=mock_session)
        df = collector.fetch_all_indices()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "index_symbol" in df.columns
        assert df["index_symbol"].iloc[0] == "NIFTY 50"

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        mock_session = _make_mock_session(response_json=_make_all_indices_json())
        collector = IndicesCollector(session=mock_session)
        collector.fetch_all_indices()
        call_args = mock_session.get_with_retry.call_args
        assert "allIndices" in call_args[0][0]


# =============================================================================
# Tests: fetch_market_status()
# =============================================================================


class TestFetchMarketStatus:
    def test_正常系_マーケットステータスを取得(self) -> None:
        mock_session = _make_mock_session(response_json=_make_market_status_json())
        collector = IndicesCollector(session=mock_session)
        statuses = collector.fetch_market_status()
        assert isinstance(statuses, list)
        assert len(statuses) == 1
        assert isinstance(statuses[0], MarketStatus)
        assert statuses[0].market == "Capital Market"

    def test_正常系_正しいエンドポイントにリクエスト(self) -> None:
        mock_session = _make_mock_session(response_json=_make_market_status_json())
        collector = IndicesCollector(session=mock_session)
        collector.fetch_market_status()
        call_args = mock_session.get_with_retry.call_args
        assert "marketStatus" in call_args[0][0]


# =============================================================================
# Tests: Module exports
# =============================================================================


class TestModuleExports:
    def test_正常系_all完全性(self) -> None:
        from market.nse.collectors import indices as module

        assert "IndicesCollector" in module.__all__
