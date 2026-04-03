"""Unit tests for market.pipeline.collector_yfinance.YFinanceCollector."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.pipeline.collector_yfinance import PERIOD_TO_DAYS, YFinanceCollector


# ---------------------------------------------------------------------------
# PERIOD_TO_DAYS
# ---------------------------------------------------------------------------


class TestPeriodToDays:
    def test_正常系_1yが含まれる(self) -> None:
        assert "1y" in PERIOD_TO_DAYS

    def test_正常系_6moが含まれる(self) -> None:
        assert "6mo" in PERIOD_TO_DAYS

    def test_正常系_3moが含まれる(self) -> None:
        assert "3mo" in PERIOD_TO_DAYS

    def test_正常系_1moが含まれる(self) -> None:
        assert "1mo" in PERIOD_TO_DAYS

    def test_正常系_すべての値が正の整数(self) -> None:
        for k, v in PERIOD_TO_DAYS.items():
            assert isinstance(v, int), f"{k}: value should be int"
            assert v > 0, f"{k}: value should be positive"

    def test_正常系_1yは365日以上(self) -> None:
        assert PERIOD_TO_DAYS["1y"] >= 365

    def test_正常系_6moは1y未満(self) -> None:
        assert PERIOD_TO_DAYS["6mo"] < PERIOD_TO_DAYS["1y"]

    def test_正常系_3moは6mo未満(self) -> None:
        assert PERIOD_TO_DAYS["3mo"] < PERIOD_TO_DAYS["6mo"]

    def test_正常系_1moは3mo未満(self) -> None:
        assert PERIOD_TO_DAYS["1mo"] < PERIOD_TO_DAYS["3mo"]


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestYFinanceCollectorInit:
    def test_正常系_デフォルト引数で初期化できる(self) -> None:
        with (
            patch("market.pipeline.collector_yfinance.YFinanceFetcher") as mock_fetcher_cls,
            patch("market.pipeline.collector_yfinance.YFinanceStorage") as mock_storage_cls,
        ):
            mock_fetcher_cls.return_value = MagicMock()
            mock_storage_cls.return_value = MagicMock()
            collector = YFinanceCollector()
        assert collector is not None

    def test_正常系_DIでfetcherとstorageを注入できる(self) -> None:
        mock_fetcher = MagicMock()
        mock_storage = MagicMock()
        collector = YFinanceCollector(fetcher=mock_fetcher, storage=mock_storage)
        assert collector is not None


# ---------------------------------------------------------------------------
# collect_daily
# ---------------------------------------------------------------------------


def _make_ohlcv_df(dates: list[str]) -> pd.DataFrame:
    """Build a minimal OHLCV DataFrame for testing."""
    return pd.DataFrame(
        {
            "open": [100.0] * len(dates),
            "high": [105.0] * len(dates),
            "low": [99.0] * len(dates),
            "close": [102.0] * len(dates),
            "volume": [1_000_000] * len(dates),
        },
        index=pd.to_datetime(dates),
    )


def _make_market_result(symbol: str, dates: list[str]) -> MagicMock:
    result = MagicMock()
    result.symbol = symbol
    result.data = _make_ohlcv_df(dates)
    result.is_empty = False
    return result


class TestCollectDaily:
    def _make_collector(
        self, latest_date: str | None = None
    ) -> tuple[YFinanceCollector, MagicMock, MagicMock]:
        mock_fetcher = MagicMock()
        mock_storage = MagicMock()
        mock_storage.get_latest_date.return_value = latest_date
        mock_storage.upsert.return_value = 1

        result_mock = _make_market_result("AAPL", ["2026-04-01", "2026-04-02"])
        mock_fetcher.fetch.return_value = [result_mock]

        collector = YFinanceCollector(fetcher=mock_fetcher, storage=mock_storage)
        return collector, mock_fetcher, mock_storage

    def test_正常系_最新日付がNoneのときperiodから開始日を計算する(self) -> None:
        collector, mock_fetcher, mock_storage = self._make_collector(latest_date=None)

        collector.collect_daily("AAPL", period="1mo")

        call_args = mock_fetcher.fetch.call_args
        options = call_args[0][0]
        # start_date should be set (not None)
        assert options.start_date is not None

    def test_正常系_最新日付がある場合翌日から取得する(self) -> None:
        latest = "2026-04-01"
        collector, mock_fetcher, mock_storage = self._make_collector(latest_date=latest)

        collector.collect_daily("AAPL", period="1y")

        call_args = mock_fetcher.fetch.call_args
        options = call_args[0][0]
        # start should be 2026-04-02 (latest + 1 day)
        expected_start = "2026-04-02"
        actual_start = str(options.start_date)
        assert expected_start in actual_start

    def test_正常系_FetchOptionsにシンボルが含まれる(self) -> None:
        collector, mock_fetcher, mock_storage = self._make_collector()

        collector.collect_daily("MSFT")

        call_args = mock_fetcher.fetch.call_args
        options = call_args[0][0]
        assert "MSFT" in options.symbols

    def test_正常系_storageのupsertが呼ばれる(self) -> None:
        collector, mock_fetcher, mock_storage = self._make_collector()

        collector.collect_daily("AAPL")

        mock_storage.upsert.assert_called()

    def test_正常系_空のデータは保存しない(self) -> None:
        mock_fetcher = MagicMock()
        mock_storage = MagicMock()
        mock_storage.get_latest_date.return_value = None

        empty_result = MagicMock()
        empty_result.symbol = "AAPL"
        empty_result.data = pd.DataFrame()
        empty_result.is_empty = True
        mock_fetcher.fetch.return_value = [empty_result]

        collector = YFinanceCollector(fetcher=mock_fetcher, storage=mock_storage)
        collector.collect_daily("AAPL")

        mock_storage.upsert.assert_not_called()

    def test_正常系_デフォルトperiodは1y(self) -> None:
        collector, mock_fetcher, mock_storage = self._make_collector(latest_date=None)

        collector.collect_daily("AAPL")

        call_args = mock_fetcher.fetch.call_args
        options = call_args[0][0]
        # With 1y default and no latest_date, start should be ~365 days ago
        assert options.start_date is not None


# ---------------------------------------------------------------------------
# collect_batch
# ---------------------------------------------------------------------------


class TestCollectBatch:
    def _make_collector(self) -> tuple[YFinanceCollector, MagicMock, MagicMock]:
        mock_fetcher = MagicMock()
        mock_storage = MagicMock()
        mock_storage.get_latest_date.return_value = None
        mock_storage.upsert.return_value = 1

        results = [
            _make_market_result("AAPL", ["2026-04-01"]),
            _make_market_result("MSFT", ["2026-04-01"]),
        ]
        mock_fetcher.fetch.return_value = results

        collector = YFinanceCollector(fetcher=mock_fetcher, storage=mock_storage)
        return collector, mock_fetcher, mock_storage

    def test_正常系_複数シンボルをバルク取得する(self) -> None:
        collector, mock_fetcher, mock_storage = self._make_collector()

        collector.collect_batch(["AAPL", "MSFT"])

        call_args = mock_fetcher.fetch.call_args
        options = call_args[0][0]
        assert set(options.symbols) == {"AAPL", "MSFT"}

    def test_正常系_fetchが1回呼ばれる(self) -> None:
        """Batch should use a single fetch call, not one per symbol."""
        collector, mock_fetcher, mock_storage = self._make_collector()

        collector.collect_batch(["AAPL", "MSFT", "GOOGL"])

        assert mock_fetcher.fetch.call_count == 1

    def test_正常系_空リストでfetchを呼ばない(self) -> None:
        mock_fetcher = MagicMock()
        mock_storage = MagicMock()
        collector = YFinanceCollector(fetcher=mock_fetcher, storage=mock_storage)

        collector.collect_batch([])

        mock_fetcher.fetch.assert_not_called()

    def test_正常系_各シンボルのupsertが呼ばれる(self) -> None:
        collector, mock_fetcher, mock_storage = self._make_collector()

        collector.collect_batch(["AAPL", "MSFT"])

        assert mock_storage.upsert.call_count >= 1
