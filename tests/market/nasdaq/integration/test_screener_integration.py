"""Integration tests for NASDAQ ScreenerCollector end-to-end workflows.

ScreenerCollector の E2E フローを検証する統合テストスイート。
NasdaqSession をモック化し、API レスポンスから CSV 出力まで通しで確認。

Test TODO List:
- [x] fetch → validate → collect の完全フロー
- [x] fetch → download_csv の CSV 保存フロー
- [x] fetch_by_category → download_by_category のカテゴリ一括フロー
- [x] 空レスポンスでのグレースフルハンドリング
"""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from market.nasdaq.collector import ScreenerCollector
from market.nasdaq.session import NasdaqSession
from market.nasdaq.types import Exchange, ScreenerFilter, Sector

# =============================================================================
# Helper: create mock responses
# =============================================================================


def _make_response(rows: list[dict[str, str]]) -> MagicMock:
    """Create a mock HTTP response with the given row data.

    Parameters
    ----------
    rows : list[dict[str, str]]
        Stock row data for the API response.

    Returns
    -------
    MagicMock
        A mock response object with json() configured.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"table": {"rows": rows}}}
    mock_response.status_code = 200
    return mock_response


_SAMPLE_ROWS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
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
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "lastsale": "$175.98",
        "netchange": "0.55",
        "pctchange": "0.314%",
        "marketCap": "2,100,000,000,000",
        "country": "United States",
        "ipoyear": "2004",
        "volume": "15,789,012",
        "sector": "Technology",
        "industry": "Computer Software",
        "url": "/market-activity/stocks/googl",
    },
    {
        "symbol": "JPM",
        "name": "JPMorgan Chase & Co.",
        "lastsale": "$195.42",
        "netchange": "1.10",
        "pctchange": "0.566%",
        "marketCap": "570,000,000,000",
        "country": "United States",
        "ipoyear": "1969",
        "volume": "8,456,789",
        "sector": "Finance",
        "industry": "Major Banks",
        "url": "/market-activity/stocks/jpm",
    },
]


# =============================================================================
# Integration tests
# =============================================================================


class TestCollectWorkflow:
    """fetch → validate → collect の完全フロー。"""

    def test_正常系_collectで取得と検証を一括実行(self) -> None:
        """collect() が fetch() + validate() を正しく呼び出すこと。"""
        mock_session = MagicMock(spec=NasdaqSession)
        mock_session.get_with_retry.return_value = _make_response(_SAMPLE_ROWS)

        collector = ScreenerCollector(session=mock_session)
        df = collector.collect()

        # Verify fetch was called
        mock_session.get_with_retry.assert_called_once()

        # Verify DataFrame contents
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert set(df["symbol"].tolist()) == {"AAPL", "GOOGL", "JPM"}

        # Verify numeric cleaning was applied
        assert df["last_sale"].iloc[0] == 227.63
        assert df["market_cap"].iloc[0] == 3435123456789
        assert df["volume"].iloc[0] == 48123456


class TestCsvDownloadWorkflow:
    """fetch → download_csv の CSV 保存フロー。"""

    def test_正常系_フィルタ付きCSV保存(self, tmp_path: Path) -> None:
        """ScreenerFilter を使用した CSV 保存が正常に動作すること。"""
        mock_session = MagicMock(spec=NasdaqSession)
        mock_session.get_with_retry.return_value = _make_response(_SAMPLE_ROWS)

        collector = ScreenerCollector(session=mock_session)
        filter_ = ScreenerFilter(exchange=Exchange.NASDAQ, sector=Sector.TECHNOLOGY)

        path = collector.download_csv(
            filter=filter_,
            output_dir=tmp_path,
            filename="nasdaq_tech.csv",
        )

        # Verify file was created
        assert path.exists()
        assert path.name == "nasdaq_tech.csv"

        # Verify content is readable
        df = pd.read_csv(path, encoding="utf-8-sig")
        assert len(df) == 3
        assert "symbol" in df.columns

        # Verify filter params were passed
        call_kwargs = mock_session.get_with_retry.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["exchange"] == "nasdaq"
        assert params["sector"] == "technology"


class TestCategoryWorkflow:
    """fetch_by_category → download_by_category のカテゴリ一括フロー。"""

    def test_正常系_カテゴリ一括取得とCSV保存(self, tmp_path: Path) -> None:
        """Exchange カテゴリで一括取得・CSV保存できること。"""
        mock_session = MagicMock(spec=NasdaqSession)
        mock_session.get_with_retry.return_value = _make_response(_SAMPLE_ROWS)

        collector = ScreenerCollector(session=mock_session)
        paths = collector.download_by_category(Exchange, output_dir=tmp_path)

        # Exchange has 3 members: NASDAQ, NYSE, AMEX
        assert len(paths) == 3

        # Verify all files exist and are valid CSVs
        for path in paths:
            assert path.exists()
            df = pd.read_csv(path, encoding="utf-8-sig")
            assert len(df) == 3
            assert "symbol" in df.columns

        # Verify API was called 3 times (once per Exchange member)
        assert mock_session.get_with_retry.call_count == 3


class TestEmptyResponseHandling:
    """空レスポンスでのグレースフルハンドリング。"""

    def test_正常系_空レスポンスでバリデーション失敗(self) -> None:
        """空の rows でも例外なく処理され validate() が False を返すこと。"""
        mock_session = MagicMock(spec=NasdaqSession)
        mock_session.get_with_retry.return_value = _make_response([])

        collector = ScreenerCollector(session=mock_session)
        df = collector.fetch()

        # DataFrame should be empty but have the correct columns
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "symbol" in df.columns

        # Validation should fail for empty DataFrame
        assert collector.validate(df) is False
