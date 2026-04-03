"""Unit tests for market.pipeline.collector_yfinance.YFinanceCollector.

All external dependencies (YFinanceFetcher, YFinanceStorage) are replaced
with MagicMocks via DI. No real Yahoo Finance API calls are made.

Key tests:
- Incremental collection logic (latest_date → start_date calculation)
- First-run vs. incremental path
- collect_batch() with empty/non-empty symbol lists
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pandas as pd
import pytest

from market.pipeline.collector_yfinance import (
    PERIOD_TO_DAYS,
    YFinanceCollector,
    _result_to_records,
    _to_yf_daily_record,
)
from market.pipeline.errors import CollectorError
from market.pipeline.models import YFDailyPriceRecord

# =============================================================================
# Helper factories
# =============================================================================


def _make_mock_result(
    symbol: str = "AAPL",
    is_empty: bool = False,
    rows: list[dict] | None = None,
) -> MagicMock:
    """Create a mock MarketDataResult with optional DataFrame data."""
    result = MagicMock()
    result.symbol = symbol
    result.is_empty = is_empty

    if rows is None or is_empty:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(
            rows,
            index=pd.to_datetime([r["date"] for r in rows]),
        )
        df.index.name = "Date"
    result.data = df
    return result


# =============================================================================
# Private helper function tests
# =============================================================================


class TestToYfDailyRecord:
    """Tests for _to_yf_daily_record()."""

    def test_正常系_有効な行をYFDailyPriceRecordに変換できる(self) -> None:
        row = MagicMock()
        row.get = lambda k, default=None: {
            "open": 170.0, "high": 175.0, "low": 169.0, "close": 173.0,
            "volume": 50_000_000, "adj close": 173.0,
        }.get(k, default)

        record = _to_yf_daily_record("AAPL", "2026-04-03", row, "2026-04-03T20:00:00")
        assert record is not None
        assert isinstance(record, YFDailyPriceRecord)
        assert record.symbol == "AAPL"
        assert record.close == pytest.approx(173.0)

    def test_正常系_NaNを含む行はNoneを返す(self) -> None:
        row = MagicMock()
        row.get = lambda k, default=None: {
            "open": float("nan"), "high": 175.0, "low": 169.0, "close": 173.0,
            "volume": 50_000_000,
        }.get(k, default)

        record = _to_yf_daily_record("AAPL", "2026-04-03", row, "2026-04-03T20:00:00")
        assert record is None


class TestResultToRecords:
    """Tests for _result_to_records()."""

    def test_正常系_空のResultは空リストを返す(self) -> None:
        result = _make_mock_result(is_empty=True)
        records = _result_to_records(result, "2026-04-03T20:00:00")
        assert records == []

    def test_正常系_有効なデータを持つResultはレコードリストを返す(self) -> None:
        rows = [
            {"date": "2026-04-01", "open": 170.0, "high": 175.0, "low": 169.0,
             "close": 173.0, "volume": 50_000_000},
        ]
        result = _make_mock_result("AAPL", rows=rows)
        records = _result_to_records(result, "2026-04-03T20:00:00")
        assert len(records) == 1
        assert records[0].symbol == "AAPL"


# =============================================================================
# YFinanceCollector tests
# =============================================================================


class TestYFinanceCollectorInit:
    """Tests for YFinanceCollector initialization."""

    def test_正常系_DI経由で初期化できる(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        assert collector is not None


class TestYFinanceCollectorCollectDaily:
    """Tests for YFinanceCollector.collect_daily() incremental logic."""

    def test_正常系_初回実行はperiodベースのstartDateを使用(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        """get_latest_date() が None の場合、period ベースの start_date が使われる."""
        mock_yfinance_storage.get_latest_date.return_value = None
        mock_yfinance_fetcher.fetch.return_value = []

        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        result = collector.collect_daily("AAPL", period="1mo")

        # Verify start_date is approximately 31 days ago
        expected_start = (date.today() - timedelta(days=31)).isoformat()
        assert result["start_date"] == expected_start
        assert result["symbol"] == "AAPL"

    def test_正常系_インクリメンタル実行は最新日付の翌日をstartDateに使用(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        """既存データがある場合、latest_date + 1日が start_date になる."""
        mock_yfinance_storage.get_latest_date.return_value = "2026-04-01"
        mock_yfinance_fetcher.fetch.return_value = []

        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        result = collector.collect_daily("AAPL", period="1y")

        assert result["start_date"] == "2026-04-02"

    def test_正常系_データが取得できた場合はupsertが呼ばれる(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        mock_yfinance_storage.get_latest_date.return_value = None
        rows = [
            {"date": "2026-04-01", "open": 170.0, "high": 175.0, "low": 169.0,
             "close": 173.0, "volume": 50_000_000},
        ]
        mock_result = _make_mock_result("AAPL", rows=rows)
        mock_yfinance_fetcher.fetch.return_value = [mock_result]
        mock_yfinance_storage.upsert.return_value = 1

        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        result = collector.collect_daily("AAPL", period="1mo")

        mock_yfinance_storage.upsert.assert_called_once()
        assert result["records_upserted"] == 1

    def test_正常系_空のResultはupsertを呼ばない(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        mock_yfinance_storage.get_latest_date.return_value = None
        mock_result = _make_mock_result(is_empty=True)
        mock_yfinance_fetcher.fetch.return_value = [mock_result]

        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        result = collector.collect_daily("AAPL")

        mock_yfinance_storage.upsert.assert_not_called()
        assert result["records_upserted"] == 0

    def test_異常系_不明なperiodはCollectorErrorを発生させる(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        with pytest.raises(CollectorError, match="Unknown period"):
            collector.collect_daily("AAPL", period="100y")

    def test_正常系_APIエラーはerrorsリストに記録される(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        mock_yfinance_storage.get_latest_date.return_value = None
        mock_yfinance_fetcher.fetch.side_effect = Exception("Network error")

        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        result = collector.collect_daily("AAPL")

        assert len(result["errors"]) == 1
        assert result["records_upserted"] == 0


class TestYFinanceCollectorCollectBatch:
    """Tests for YFinanceCollector.collect_batch()."""

    def test_正常系_空リストはno_op(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        result = collector.collect_batch([])
        assert result["total_symbols"] == 0
        assert result["records_upserted"] == 0
        mock_yfinance_fetcher.fetch.assert_not_called()

    def test_正常系_複数シンボルをバッチ処理できる(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        mock_yfinance_fetcher.fetch.return_value = []
        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        result = collector.collect_batch(["AAPL", "MSFT"])
        assert result["total_symbols"] == 2
        mock_yfinance_fetcher.fetch.assert_called_once()

    def test_異常系_不明なperiodはCollectorErrorを発生させる(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        with pytest.raises(CollectorError, match="Unknown period"):
            collector.collect_batch(["AAPL"], period="999y")

    def test_正常系_APIエラーはerrorsリストに記録される(
        self,
        mock_yfinance_fetcher: MagicMock,
        mock_yfinance_storage: MagicMock,
    ) -> None:
        mock_yfinance_fetcher.fetch.side_effect = Exception("Network error")
        collector = YFinanceCollector(
            fetcher=mock_yfinance_fetcher,
            storage=mock_yfinance_storage,
        )
        result = collector.collect_batch(["AAPL"])
        assert len(result["errors"]) == 1
        assert result["records_upserted"] == 0


class TestPeriodToDays:
    """Tests for PERIOD_TO_DAYS constant."""

    def test_正常系_1moは31日(self) -> None:
        assert PERIOD_TO_DAYS["1mo"] == 31

    def test_正常系_1yは365日(self) -> None:
        assert PERIOD_TO_DAYS["1y"] == 365

    def test_正常系_すべての期間が正の整数(self) -> None:
        for period, days in PERIOD_TO_DAYS.items():
            assert days > 0, f"{period} should have positive days"
