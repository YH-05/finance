"""Yahoo Finance daily price data collector.

This module provides the ``YFinanceCollector`` class that coordinates
data fetching from ``YFinanceFetcher``, conversion of OHLCV DataFrames
to ``YFDailyPriceRecord`` dataclasses, and persistence via ``YFinanceStorage``.

Key components
--------------
- ``PERIOD_TO_DAYS`` -- Maps period strings (e.g. ``"1y"``) to integer day counts.
- ``YFinanceCollector`` -- DI-based orchestrator (fetcher + storage).

Supported collection methods
-----------------------------
- ``collect_daily(symbol, period='1y')`` -- Collect daily price data for one symbol,
  using incremental updates based on the latest stored date.
- ``collect_batch(symbols)`` -- Bulk-fetch OHLCV data for multiple symbols in
  a single ``FetchOptions`` call.

Examples
--------
>>> collector = YFinanceCollector()
>>> result = collector.collect_daily("AAPL", period="1y")
>>> result["symbol"]
'AAPL'

See Also
--------
market.yfinance.fetcher : YFinanceFetcher providing ``fetch()``.
market.pipeline.storage_yfinance : YFinanceStorage for persistence.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any, Final

import pandas as pd

from market.pipeline.errors import CollectorError
from market.pipeline.models import YFDailyPriceRecord
from market.pipeline.storage_yfinance import YFinanceStorage
from market.yfinance.fetcher import YFinanceFetcher
from market.yfinance.types import FetchOptions, Interval
from utils_core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Maps period strings to the equivalent number of calendar days.
#: Used to compute ``start_date`` when no prior data exists in storage.
PERIOD_TO_DAYS: Final[dict[str, int]] = {
    "1mo": 31,
    "3mo": 92,
    "6mo": 183,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
    "10y": 3650,
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _to_yf_daily_record(
    symbol: str,
    row_date: str,
    row: Any,
    fetched_at: str,
) -> YFDailyPriceRecord | None:
    """Convert a single DataFrame row to a ``YFDailyPriceRecord``.

    Returns ``None`` if required OHLCV columns are missing or non-finite.
    """
    try:
        open_val = float(row.get("open") or float("nan"))
        high_val = float(row.get("high") or float("nan"))
        low_val = float(row.get("low") or float("nan"))
        close_val = float(row.get("close") or float("nan"))
        volume_val = int(row.get("volume") or 0)
    except (TypeError, ValueError):
        return None

    # Reject rows with NaN in required fields
    if any(pd.isna(v) for v in [open_val, high_val, low_val, close_val]):
        return None

    # adj_close is optional
    adj_close: float | None
    raw_adj = row.get("adj close") or row.get("adj_close") or row.get("adjusted_close")
    if raw_adj is not None and not pd.isna(raw_adj):
        try:
            adj_close = float(raw_adj)
        except (TypeError, ValueError):
            adj_close = None
    else:
        adj_close = None

    return YFDailyPriceRecord(
        symbol=symbol,
        date=row_date,
        open=open_val,
        high=high_val,
        low=low_val,
        close=close_val,
        adjusted_close=adj_close,
        volume=volume_val,
        fetched_at=fetched_at,
    )


def _result_to_records(
    result: Any,
    fetched_at: str,
) -> list[YFDailyPriceRecord]:
    """Convert a ``MarketDataResult`` to a list of ``YFDailyPriceRecord``."""
    records: list[YFDailyPriceRecord] = []

    if result.is_empty:
        return records

    df: pd.DataFrame = result.data
    symbol: str = result.symbol

    for idx, row in df.iterrows():
        # Index is a DatetimeIndex; convert to ISO date string.
        # AIDEV-NOTE: Intentional skip for graceful degradation on malformed index values.
        try:
            row_date = pd.Timestamp(str(idx)).date().isoformat()
        except Exception:  # nosec B112
            continue

        record = _to_yf_daily_record(symbol, row_date, row, fetched_at)
        if record is not None:
            records.append(record)

    return records


# ---------------------------------------------------------------------------
# YFinanceCollector
# ---------------------------------------------------------------------------


class YFinanceCollector:
    """Orchestrator for Yahoo Finance daily price data collection.

    Fetches OHLCV data from ``YFinanceFetcher``, converts each row to a
    ``YFDailyPriceRecord``, and persists via ``YFinanceStorage``.

    Supports both incremental single-symbol collection (``collect_daily``)
    and bulk multi-symbol collection (``collect_batch``).

    Parameters
    ----------
    fetcher : YFinanceFetcher | None
        Yahoo Finance data fetcher. When ``None``, a default
        ``YFinanceFetcher()`` is created.
    storage : YFinanceStorage | None
        Storage layer for daily price records. When ``None``, a default
        ``YFinanceStorage()`` is created.

    Examples
    --------
    >>> collector = YFinanceCollector()
    >>> result = collector.collect_daily("AAPL", period="1mo")
    >>> result["symbol"]
    'AAPL'
    """

    def __init__(
        self,
        fetcher: YFinanceFetcher | None = None,
        storage: YFinanceStorage | None = None,
    ) -> None:
        """Initialize the collector with optional DI parameters."""
        self._fetcher = fetcher or YFinanceFetcher()
        self._storage = storage or YFinanceStorage()
        logger.debug(
            "YFinanceCollector initialized",
            fetcher_type=type(self._fetcher).__name__,
            storage_type=type(self._storage).__name__,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect_daily(
        self,
        symbol: str,
        period: str = "1y",
    ) -> dict[str, Any]:
        """Collect daily OHLCV data for a single symbol with incremental updates.

        Determines the start date by:

        1. Calling ``storage.get_latest_date(symbol)`` to find the last stored date.
        2. If a date is found, ``start_date = latest_date + 1 day``.
        3. If no date is found (first run), ``start_date = today - PERIOD_TO_DAYS[period]``.

        Then constructs a ``FetchOptions`` with ``symbols=[symbol]`` and
        ``start_date``, calls ``fetcher.fetch()``, converts results to
        ``YFDailyPriceRecord`` instances, and upserts via storage.

        Parameters
        ----------
        symbol : str
            Ticker symbol in yfinance format (e.g. ``"AAPL"``, ``"BRK-B"``).
        period : str
            Lookback period string for the first-run case.
            Must be one of ``PERIOD_TO_DAYS`` keys. Default ``"1y"``.

        Returns
        -------
        dict[str, Any]
            Summary dict with keys:
            - ``"symbol"``: the ticker symbol
            - ``"records_upserted"``: total records persisted
            - ``"start_date"``: ISO date string used for fetching
            - ``"errors"``: list of error strings

        Raises
        ------
        CollectorError
            If ``period`` is not in ``PERIOD_TO_DAYS``.

        Examples
        --------
        >>> collector = YFinanceCollector(fetcher=mock, storage=mock)
        >>> result = collector.collect_daily("AAPL", period="1mo")
        >>> result["symbol"]
        'AAPL'
        """
        if period not in PERIOD_TO_DAYS:
            raise CollectorError(
                f"Unknown period: {period!r}. Must be one of {list(PERIOD_TO_DAYS.keys())}",
                context={"symbol": symbol, "period": period},
            )

        # Determine start date
        latest_date = self._storage.get_latest_date(symbol)
        if latest_date is not None:
            # Incremental: start the day after the latest stored date
            latest_dt = date.fromisoformat(latest_date)
            start_date = (latest_dt + timedelta(days=1)).isoformat()
        else:
            # First run: fall back to period-based lookback
            days_back = PERIOD_TO_DAYS[period]
            start_date = (date.today() - timedelta(days=days_back)).isoformat()

        logger.info(
            "Collecting daily prices",
            symbol=symbol,
            period=period,
            latest_date=latest_date,
            start_date=start_date,
        )

        errors: list[str] = []
        records_upserted = 0
        fetched_at = datetime.now(UTC).isoformat()

        try:
            options = FetchOptions(
                symbols=[symbol],
                start_date=start_date,
                interval=Interval.DAILY,
            )
            results = self._fetcher.fetch(options)
        except Exception as exc:
            msg = f"Failed to fetch yfinance data for {symbol}: {exc}"
            logger.warning(msg, symbol=symbol, error=str(exc))
            errors.append(msg)
            return {
                "symbol": symbol,
                "records_upserted": 0,
                "start_date": start_date,
                "errors": errors,
            }

        for result in results:
            if result.is_empty:
                logger.debug("Empty result for symbol", symbol=result.symbol)
                continue

            price_records = _result_to_records(result, fetched_at)
            if price_records:
                upserted = self._storage.upsert(price_records)
                records_upserted += upserted

        logger.info(
            "Daily price collection completed",
            symbol=symbol,
            records_upserted=records_upserted,
            start_date=start_date,
        )

        return {
            "symbol": symbol,
            "records_upserted": records_upserted,
            "start_date": start_date,
            "errors": errors,
        }

    def collect_batch(
        self,
        symbols: list[str],
        period: str = "1y",
    ) -> dict[str, Any]:
        """Bulk-collect daily OHLCV data for multiple symbols.

        Passes all ``symbols`` as a single ``FetchOptions.symbols`` list,
        issues one ``fetcher.fetch()`` call, and processes each result.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols to fetch (e.g. ``["AAPL", "MSFT"]``).
            Empty list is a no-op.
        period : str
            Lookback period for first-run symbols. Default ``"1y"``.

        Returns
        -------
        dict[str, Any]
            Summary dict with keys:
            - ``"total_symbols"``: number of symbols requested
            - ``"records_upserted"``: total records persisted
            - ``"errors"``: list of error strings

        Examples
        --------
        >>> collector = YFinanceCollector(fetcher=mock, storage=mock)
        >>> result = collector.collect_batch(["AAPL", "MSFT"])
        >>> result["total_symbols"]
        2
        """
        if not symbols:
            logger.debug("collect_batch called with empty symbols list")
            return {"total_symbols": 0, "records_upserted": 0, "errors": []}

        if period not in PERIOD_TO_DAYS:
            raise CollectorError(
                f"Unknown period: {period!r}. Must be one of {list(PERIOD_TO_DAYS.keys())}",
                context={"symbols": symbols, "period": period},
            )

        days_back = PERIOD_TO_DAYS[period]
        start_date = (date.today() - timedelta(days=days_back)).isoformat()

        logger.info(
            "Batch collecting daily prices",
            symbol_count=len(symbols),
            period=period,
            start_date=start_date,
        )

        errors: list[str] = []
        records_upserted = 0
        fetched_at = datetime.now(UTC).isoformat()

        try:
            options = FetchOptions(
                symbols=symbols,
                start_date=start_date,
                interval=Interval.DAILY,
            )
            results = self._fetcher.fetch(options)
        except Exception as exc:
            msg = f"Failed to batch fetch yfinance data: {exc}"
            logger.warning(msg, symbol_count=len(symbols), error=str(exc))
            errors.append(msg)
            return {
                "total_symbols": len(symbols),
                "records_upserted": 0,
                "errors": errors,
            }

        for result in results:
            if result.is_empty:
                logger.debug("Empty result for symbol", symbol=result.symbol)
                continue

            price_records = _result_to_records(result, fetched_at)
            if price_records:
                upserted = self._storage.upsert(price_records)
                records_upserted += upserted

        logger.info(
            "Batch price collection completed",
            total_symbols=len(symbols),
            records_upserted=records_upserted,
            error_count=len(errors),
        )

        return {
            "total_symbols": len(symbols),
            "records_upserted": records_upserted,
            "errors": errors,
        }


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "PERIOD_TO_DAYS",
    "YFinanceCollector",
]
