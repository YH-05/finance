"""Unit tests for market.nasdaq.collector module.

ScreenerCollector の動作を検証するテストスイート。
DataCollector ABC を継承した NASDAQ Stock Screener コレクターのテスト。

Test TODO List:
- [x] ScreenerCollector: デフォルト値で初期化（session なし）
- [x] ScreenerCollector: DI パターンで session 注入
- [x] _get_session(): 注入なし時に新規セッション生成（should_close=True）
- [x] _get_session(): 注入あり時に既存セッション返却（should_close=False）
- [x] fetch(): フィルタなしで全銘柄取得
- [x] fetch(): ScreenerFilter でフィルタリング
- [x] fetch(): API エラー時に例外を伝播
- [x] validate(): 有効な DataFrame で True
- [x] validate(): 空 DataFrame で False
- [x] validate(): 必須カラム不足で False
- [x] fetch_by_category(): カテゴリ全値で一括取得
- [x] fetch_by_category(): ポライトディレイ挿入確認
- [x] download_csv(): CSV ファイル保存（utf-8-sig）
- [x] download_csv(): ファイル名規則準拠
- [x] download_by_category(): カテゴリ一括 CSV 保存
"""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.nasdaq.collector import ScreenerCollector
from market.nasdaq.errors import NasdaqAPIError
from market.nasdaq.session import NasdaqSession
from market.nasdaq.types import (
    Exchange,
    FilterCategory,
    MarketCap,
    ScreenerFilter,
    Sector,
)

# =============================================================================
# Helper: create a mock NASDAQ API JSON response
# =============================================================================


def _make_api_response(rows: list[dict[str, str]] | None = None) -> dict:
    """Create a mock NASDAQ Screener API JSON response.

    Parameters
    ----------
    rows : list[dict[str, str]] | None
        Optional list of row dicts. If None, uses a default 2-row dataset.

    Returns
    -------
    dict
        A dict matching the NASDAQ Screener API response structure.
    """
    if rows is None:
        rows = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc. Common Stock",
                "lastsale": "$227.63",
                "netchange": "-1.95",
                "pctchange": "-0.849%",
                "marketCap": "3,435,123,456,789",
                "country": "United States",
                "ipoyear": "1980",
                "volume": "48,123,456",
                "sector": "Technology",
                "industry": "Computer Manufacturing",
                "url": "/market-activity/stocks/aapl",
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation Common Stock",
                "lastsale": "$415.50",
                "netchange": "2.30",
                "pctchange": "0.557%",
                "marketCap": "3,100,000,000,000",
                "country": "United States",
                "ipoyear": "1986",
                "volume": "22,456,789",
                "sector": "Technology",
                "industry": "Computer Software",
                "url": "/market-activity/stocks/msft",
            },
        ]
    return {"data": {"table": {"rows": rows}}}


def _make_mock_session(response_json: dict | None = None) -> MagicMock:
    """Create a mock NasdaqSession with a pre-configured get_with_retry response.

    Parameters
    ----------
    response_json : dict | None
        JSON response to return from get_with_retry. If None, uses default.

    Returns
    -------
    MagicMock
        A mock NasdaqSession instance.
    """
    mock_session = MagicMock(spec=NasdaqSession)
    mock_response = MagicMock()
    mock_response.json.return_value = response_json or _make_api_response()
    mock_response.status_code = 200
    mock_session.get_with_retry.return_value = mock_response
    return mock_session


# =============================================================================
# Initialization tests
# =============================================================================


class TestScreenerCollectorInit:
    """ScreenerCollector 初期化のテスト。"""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """session なしでデフォルト初期化されること。"""
        collector = ScreenerCollector()

        assert collector._session_instance is None
        assert collector.name == "ScreenerCollector"

    def test_正常系_DIパターンでsession注入できる(self) -> None:
        """DI パターンで NasdaqSession を注入できること。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)

        assert collector._session_instance is mock_session


# =============================================================================
# _get_session tests
# =============================================================================


class TestGetSession:
    """_get_session() ヘルパーのテスト。"""

    def test_正常系_注入なし時に新規セッション生成(self) -> None:
        """session 未注入時に新規 NasdaqSession を生成し should_close=True。"""
        collector = ScreenerCollector()

        with patch("market.nasdaq.collector.NasdaqSession") as mock_cls:
            mock_cls.return_value = MagicMock(spec=NasdaqSession)
            session, should_close = collector._get_session()

        assert should_close is True
        mock_cls.assert_called_once()

    def test_正常系_注入あり時に既存セッション返却(self) -> None:
        """session 注入時に既存セッションを返し should_close=False。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)

        session, should_close = collector._get_session()

        assert session is mock_session
        assert should_close is False


# =============================================================================
# fetch tests
# =============================================================================


class TestFetch:
    """fetch() メソッドのテスト。"""

    def test_正常系_フィルタなしで全銘柄取得(self) -> None:
        """フィルタ None で API を呼び出し DataFrame を返すこと。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)

        df = collector.fetch()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "symbol" in df.columns
        assert "name" in df.columns
        assert df["symbol"].iloc[0] == "AAPL"
        mock_session.get_with_retry.assert_called_once()

    def test_正常系_ScreenerFilterでフィルタリング(self) -> None:
        """ScreenerFilter を渡した場合にパラメータが適用されること。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)
        filter_ = ScreenerFilter(exchange=Exchange.NASDAQ, sector=Sector.TECHNOLOGY)

        df = collector.fetch(filter=filter_)

        assert isinstance(df, pd.DataFrame)
        # Verify the params were passed
        call_kwargs = mock_session.get_with_retry.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params is not None
        assert params["exchange"] == "nasdaq"
        assert params["sector"] == "technology"

    def test_異常系_APIエラー時に例外伝播(self) -> None:
        """API エラー時に NasdaqAPIError が伝播すること。"""
        mock_session = MagicMock(spec=NasdaqSession)
        mock_session.get_with_retry.side_effect = NasdaqAPIError(
            "API returned HTTP 500",
            url="https://api.nasdaq.com/api/screener/stocks",
            status_code=500,
            response_body='{"error": "Internal Server Error"}',
        )
        collector = ScreenerCollector(session=mock_session)

        with pytest.raises(NasdaqAPIError, match="HTTP 500"):
            collector.fetch()


# =============================================================================
# validate tests
# =============================================================================


class TestValidate:
    """validate() メソッドのテスト。"""

    def test_正常系_有効なDataFrameでTrue(self) -> None:
        """symbol と name を含む非空 DataFrame で True を返すこと。"""
        collector = ScreenerCollector()
        df = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT"],
                "name": ["Apple Inc.", "Microsoft Corp."],
            }
        )

        assert collector.validate(df) is True

    def test_異常系_空DataFrameでFalse(self) -> None:
        """空の DataFrame で False を返すこと。"""
        collector = ScreenerCollector()
        df = pd.DataFrame()

        assert collector.validate(df) is False

    def test_異常系_必須カラム不足でFalse(self) -> None:
        """symbol カラムがない場合に False を返すこと。"""
        collector = ScreenerCollector()
        df = pd.DataFrame({"other_col": ["value1"]})

        assert collector.validate(df) is False


# =============================================================================
# fetch_by_category tests
# =============================================================================


class TestFetchByCategory:
    """fetch_by_category() メソッドのテスト。"""

    def test_正常系_カテゴリ全値で一括取得(self) -> None:
        """Exchange の全値で fetch を呼び出し dict を返すこと。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)

        result = collector.fetch_by_category(Exchange)

        assert isinstance(result, dict)
        # Exchange has 3 values: NASDAQ, NYSE, AMEX
        assert len(result) == 3
        assert "nasdaq" in result
        assert "nyse" in result
        assert "amex" in result
        for key, df in result.items():
            assert isinstance(df, pd.DataFrame)

    def test_正常系_ポライトディレイ挿入確認(self) -> None:
        """リクエスト間にポライトディレイが挿入されること。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)

        with patch("market.nasdaq.collector.time.sleep") as mock_sleep:
            collector.fetch_by_category(Exchange)

        # There should be sleep calls between requests (n-1 sleeps for n requests)
        assert mock_sleep.call_count >= len(Exchange) - 1


# =============================================================================
# download_csv tests
# =============================================================================


class TestDownloadCsv:
    """download_csv() メソッドのテスト。"""

    def test_正常系_CSVファイル保存(self, tmp_path: Path) -> None:
        """CSV ファイルが utf-8-sig エンコーディングで保存されること。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)

        output_path = collector.download_csv(
            filter=None,
            output_dir=tmp_path,
            filename="test_stocks.csv",
        )

        assert output_path.exists()
        # Verify utf-8-sig encoding (BOM)
        raw_bytes = output_path.read_bytes()
        assert raw_bytes[:3] == b"\xef\xbb\xbf"  # UTF-8 BOM
        # Verify content
        df = pd.read_csv(output_path, encoding="utf-8-sig")
        assert len(df) == 2
        assert "symbol" in df.columns

    def test_正常系_ファイル名規則準拠(self, tmp_path: Path) -> None:
        """指定ファイル名で保存されること。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)

        output_path = collector.download_csv(
            filter=ScreenerFilter(exchange=Exchange.NASDAQ),
            output_dir=tmp_path,
            filename="nasdaq_stocks.csv",
        )

        assert output_path.name == "nasdaq_stocks.csv"
        assert output_path.parent == tmp_path


# =============================================================================
# download_by_category tests
# =============================================================================


class TestDownloadByCategory:
    """download_by_category() メソッドのテスト。"""

    def test_正常系_カテゴリ一括CSV保存(self, tmp_path: Path) -> None:
        """カテゴリ一括保存でファイル名規則に準拠すること。"""
        mock_session = _make_mock_session()
        collector = ScreenerCollector(session=mock_session)

        paths = collector.download_by_category(
            Exchange,
            output_dir=tmp_path,
        )

        assert isinstance(paths, list)
        assert len(paths) == len(Exchange)

        # Check filename pattern: {category}_{value}_{YYYY-MM-DD}.csv
        today_str = date.today().isoformat()
        for path in paths:
            assert path.exists()
            name = path.name
            assert name.startswith("exchange_")
            assert name.endswith(f"_{today_str}.csv")
            # Verify utf-8-sig encoding
            raw_bytes = path.read_bytes()
            assert raw_bytes[:3] == b"\xef\xbb\xbf"
