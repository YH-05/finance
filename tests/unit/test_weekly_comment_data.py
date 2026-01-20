"""Unit tests for scripts/weekly_comment_data.py module.

This module tests the weekly comment data collection functionality
using mocked yfinance data to avoid network dependencies.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path  # noqa: TC003
from unittest.mock import MagicMock, patch

import pandas as pd


class TestCalculatePeriodReturn:
    """Tests for calculate_period_return function."""

    def test_正常系_期間リターンを計算できる(self) -> None:
        from scripts.weekly_comment_data import calculate_period_return

        # Create sample price series
        dates = pd.date_range("2026-01-14", periods=8, freq="D")
        prices = pd.Series(
            [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0], index=dates
        )

        result = calculate_period_return(prices, date(2026, 1, 14), date(2026, 1, 21))

        # (107 - 100) / 100 = 0.07
        assert result is not None
        assert abs(result - 0.07) < 0.001

    def test_エッジケース_空の価格シリーズでNoneを返す(self) -> None:
        from scripts.weekly_comment_data import calculate_period_return

        prices = pd.Series([], dtype=float)
        result = calculate_period_return(prices, date(2026, 1, 14), date(2026, 1, 21))

        assert result is None

    def test_エッジケース_開始価格が0の場合Noneを返す(self) -> None:
        from scripts.weekly_comment_data import calculate_period_return

        dates = pd.date_range("2026-01-14", periods=8, freq="D")
        prices = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], index=dates)

        result = calculate_period_return(prices, date(2026, 1, 14), date(2026, 1, 21))

        assert result is None


class TestFetchWeeklyReturns:
    """Tests for fetch_weekly_returns function with mocked yfinance."""

    @patch("scripts.weekly_comment_data.yf.download")
    def test_正常系_複数ティッカーの週次リターンを取得できる(
        self, mock_download: MagicMock
    ) -> None:
        from scripts.weekly_comment_data import fetch_weekly_returns

        # Create mock return data
        dates = pd.date_range("2026-01-10", periods=15, freq="D")
        mock_df = pd.DataFrame(
            {
                ("Close", "AAPL"): [150.0 + i for i in range(15)],
                ("Close", "MSFT"): [300.0 + i * 2 for i in range(15)],
            },
            index=dates,
        )
        mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)
        mock_download.return_value = mock_df

        tickers = {"AAPL": "Apple", "MSFT": "Microsoft"}
        result = fetch_weekly_returns(tickers, date(2026, 1, 14), date(2026, 1, 21))

        assert len(result) == 2
        assert any(r["ticker"] == "AAPL" for r in result)
        assert any(r["ticker"] == "MSFT" for r in result)

    @patch("scripts.weekly_comment_data.yf.download")
    def test_異常系_yfinanceエラー時は空リストを返す(
        self, mock_download: MagicMock
    ) -> None:
        from scripts.weekly_comment_data import fetch_weekly_returns

        mock_download.side_effect = Exception("Network error")

        tickers = {"AAPL": "Apple"}
        result = fetch_weekly_returns(tickers, date(2026, 1, 14), date(2026, 1, 21))

        assert result == []

    @patch("scripts.weekly_comment_data.yf.download")
    def test_エッジケース_空のティッカー辞書では空リストを返す(
        self, mock_download: MagicMock
    ) -> None:
        from scripts.weekly_comment_data import fetch_weekly_returns

        result = fetch_weekly_returns({}, date(2026, 1, 14), date(2026, 1, 21))

        assert result == []
        mock_download.assert_not_called()


class TestCollectIndicesData:
    """Tests for collect_indices_data function."""

    @patch("scripts.weekly_comment_data.fetch_weekly_returns")
    def test_正常系_指数データを収集できる(self, mock_fetch: MagicMock) -> None:
        from scripts.weekly_comment_data import collect_indices_data

        mock_fetch.return_value = [
            {
                "ticker": "^GSPC",
                "name": "S&P 500",
                "weekly_return": 0.025,
                "latest_close": 6000.0,
            }
        ]

        result = collect_indices_data(date(2026, 1, 14), date(2026, 1, 21))

        assert result["as_of"] == "2026-01-21"
        assert result["period"]["start"] == "2026-01-14"
        assert result["period"]["end"] == "2026-01-21"
        assert "indices" in result


class TestCollectMag7Data:
    """Tests for collect_mag7_data function."""

    @patch("scripts.weekly_comment_data.fetch_weekly_returns")
    def test_正常系_MAG7データを収集できる(self, mock_fetch: MagicMock) -> None:
        from scripts.weekly_comment_data import collect_mag7_data

        # First call for MAG7, second for SOX
        mock_fetch.side_effect = [
            [
                {
                    "ticker": "TSLA",
                    "name": "Tesla",
                    "weekly_return": 0.037,
                    "latest_close": 300.0,
                },
                {
                    "ticker": "AAPL",
                    "name": "Apple",
                    "weekly_return": -0.032,
                    "latest_close": 200.0,
                },
            ],
            [
                {
                    "ticker": "^SOX",
                    "name": "SOX Index",
                    "weekly_return": 0.031,
                    "latest_close": 5000.0,
                }
            ],
        ]

        result = collect_mag7_data(date(2026, 1, 14), date(2026, 1, 21))

        assert result["as_of"] == "2026-01-21"
        assert "mag7" in result
        assert "sox" in result
        # MAG7 should be sorted by return (descending)
        assert result["mag7"][0]["ticker"] == "TSLA"


class TestCollectSectorsData:
    """Tests for collect_sectors_data function."""

    @patch("scripts.weekly_comment_data.fetch_weekly_returns")
    def test_正常系_セクターデータを収集できる(self, mock_fetch: MagicMock) -> None:
        from scripts.weekly_comment_data import collect_sectors_data

        mock_fetch.return_value = [
            {"ticker": "XLK", "name": "Information Technology", "weekly_return": 0.025},
            {"ticker": "XLF", "name": "Financial Services", "weekly_return": 0.018},
            {"ticker": "XLE", "name": "Energy", "weekly_return": 0.012},
            {"ticker": "XLV", "name": "Healthcare", "weekly_return": -0.029},
            {"ticker": "XLU", "name": "Utilities", "weekly_return": -0.022},
            {"ticker": "XLB", "name": "Basic Materials", "weekly_return": -0.015},
        ]

        result = collect_sectors_data(date(2026, 1, 14), date(2026, 1, 21))

        assert result["as_of"] == "2026-01-21"
        assert "top_sectors" in result
        assert "bottom_sectors" in result
        assert "all_sectors" in result
        assert len(result["top_sectors"]) == 3
        assert len(result["bottom_sectors"]) == 3
        # Top sectors should be sorted by return (descending)
        assert (
            result["top_sectors"][0]["weekly_return"]
            > result["bottom_sectors"][0]["weekly_return"]
        )


class TestSaveAllData:
    """Tests for save_all_data function."""

    @patch("scripts.weekly_comment_data.collect_indices_data")
    @patch("scripts.weekly_comment_data.collect_mag7_data")
    @patch("scripts.weekly_comment_data.collect_sectors_data")
    def test_正常系_全データファイルを保存できる(
        self,
        mock_sectors: MagicMock,
        mock_mag7: MagicMock,
        mock_indices: MagicMock,
        tmp_path: Path,
    ) -> None:
        from scripts.weekly_comment_data import save_all_data

        mock_indices.return_value = {"as_of": "2026-01-21", "indices": []}
        mock_mag7.return_value = {"as_of": "2026-01-21", "mag7": [], "sox": None}
        mock_sectors.return_value = {
            "as_of": "2026-01-21",
            "top_sectors": [],
            "bottom_sectors": [],
            "all_sectors": [],
        }

        results = save_all_data(tmp_path, date(2026, 1, 14), date(2026, 1, 21))

        # Check all files were created
        assert results["indices.json"] is True
        assert results["mag7.json"] is True
        assert results["sectors.json"] is True
        assert results["metadata.json"] is True

        # Check files exist
        assert (tmp_path / "indices.json").exists()
        assert (tmp_path / "mag7.json").exists()
        assert (tmp_path / "sectors.json").exists()
        assert (tmp_path / "metadata.json").exists()


class TestCreateParser:
    """Tests for create_parser function."""

    def test_正常系_パーサーを作成できる(self) -> None:
        from scripts.weekly_comment_data import create_parser

        parser = create_parser()

        args = parser.parse_args([])
        assert args.output is not None
        assert args.start is None
        assert args.end is None
        assert args.date is None

    def test_正常系_引数を解析できる(self) -> None:
        from scripts.weekly_comment_data import create_parser

        parser = create_parser()

        args = parser.parse_args(
            [
                "--output",
                "/tmp/test",
                "--start",
                "2026-01-14",
                "--end",
                "2026-01-21",
            ]
        )

        assert args.output == "/tmp/test"
        assert args.start == "2026-01-14"
        assert args.end == "2026-01-21"
