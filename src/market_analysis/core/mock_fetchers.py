"""Mock data fetchers for testing.

This module provides mock implementations of data fetchers
for testing without requiring actual API access.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Generator

import numpy as np
import pandas as pd

from ..types import (
    DataSource,
    FetchOptions,
    IdentifierType,
    Interval,
    MarketDataResult,
)
from ..utils.logging_config import get_logger
from .base_fetcher import BaseDataFetcher
from .bloomberg_fetcher import (
    BloombergFetcher,
    _is_valid_bloomberg_symbol,
)
from .factset_fetcher import FACTSET_SYMBOL_PATTERN

logger = get_logger(__name__, module="mock_fetchers")


def generate_mock_ohlcv(
    symbol: str,
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
    interval: Interval = Interval.DAILY,
    base_price: float = 100.0,
    volatility: float = 0.02,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate mock OHLCV data for testing.

    Parameters
    ----------
    symbol : str
        Symbol name (used for reproducible randomness)
    start_date : datetime | str | None
        Start date (default: 1 year ago)
    end_date : datetime | str | None
        End date (default: today)
    interval : Interval
        Data interval
    base_price : float
        Starting price (default: 100.0)
    volatility : float
        Daily volatility (default: 0.02 = 2%)
    seed : int | None
        Random seed for reproducibility

    Returns
    -------
    pd.DataFrame
        DataFrame with OHLCV columns and DatetimeIndex
    """
    # Set random seed
    if seed is None:
        # Use symbol hash for reproducibility
        seed = hash(symbol) % 2**32
    rng = np.random.default_rng(seed)

    # Parse dates
    if end_date is None:
        end = datetime.now()
    elif isinstance(end_date, str):
        end = pd.to_datetime(end_date)
    else:
        end = end_date

    if start_date is None:
        start = end - timedelta(days=365)
    elif isinstance(start_date, str):
        start = pd.to_datetime(start_date)
    else:
        start = start_date

    # Generate date range based on interval
    if interval == Interval.DAILY:
        dates = pd.bdate_range(start=start, end=end)
    elif interval == Interval.WEEKLY:
        dates = pd.date_range(start=start, end=end, freq="W")
    elif interval == Interval.MONTHLY:
        dates = pd.date_range(start=start, end=end, freq="ME")
    elif interval == Interval.HOURLY:
        dates = pd.date_range(start=start, end=end, freq="h")
    else:
        dates = pd.bdate_range(start=start, end=end)

    if len(dates) == 0:
        return pd.DataFrame(
            columns=pd.Index(["open", "high", "low", "close", "volume"]),
            index=pd.DatetimeIndex([], name="date"),
        )

    n_points = len(dates)

    # Generate random returns
    returns = rng.normal(0, volatility, n_points)

    # Calculate close prices
    close = base_price * np.cumprod(1 + returns)

    # Generate OHLC from close
    daily_range = volatility * 1.5
    open_prices = close * (1 + rng.uniform(-daily_range / 2, daily_range / 2, n_points))
    high = np.maximum(open_prices, close) * (1 + rng.uniform(0, daily_range, n_points))
    low = np.minimum(open_prices, close) * (1 - rng.uniform(0, daily_range, n_points))

    # Generate volume (random with some trend)
    base_volume = 1_000_000
    volume = (base_volume * rng.uniform(0.5, 2.0, n_points)).astype(int)

    df = pd.DataFrame(
        {
            "open": open_prices,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )

    return df


def generate_mock_financial_data(
    symbols: list[str],
    fields: list[str],
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate mock financial data for testing.

    Parameters
    ----------
    symbols : list[str]
        List of symbols
    fields : list[str]
        List of financial fields
    seed : int | None
        Random seed for reproducibility

    Returns
    -------
    pd.DataFrame
        DataFrame with symbols as index and fields as columns
    """
    if seed is None:
        seed = 42
    rng = np.random.default_rng(seed)

    data: dict[str, dict[str, float]] = {}

    # Field-specific value ranges
    field_ranges: dict[str, tuple[float, float]] = {
        "PX_LAST": (50, 500),
        "PE_RATIO": (5, 50),
        "DIVIDEND_YIELD": (0, 5),
        "MARKET_CAP": (1e9, 1e12),
        "FF_ROIC": (0.05, 0.30),
        "FF_ROE": (0.05, 0.35),
        "FF_SALES": (1e6, 1e11),
        "EPS_BASIC": (1, 20),
    }

    default_range = (10, 100)

    for symbol in symbols:
        data[symbol] = {}
        for field in fields:
            min_val, max_val = field_ranges.get(field, default_range)
            data[symbol][field] = rng.uniform(min_val, max_val)

    return pd.DataFrame.from_dict(data, orient="index")


def generate_mock_constituents(
    universe_code: str,
    n_constituents: int = 50,
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate mock index constituents data.

    Parameters
    ----------
    universe_code : str
        Universe/index code
    n_constituents : int
        Number of constituents to generate
    start_date : datetime | str | None
        Start date
    end_date : datetime | str | None
        End date
    seed : int | None
        Random seed

    Returns
    -------
    pd.DataFrame
        DataFrame with constituents data
    """
    if seed is None:
        seed = hash(universe_code) % 2**32
    rng = np.random.default_rng(seed)

    # Parse dates
    if end_date is None:
        end = datetime.now()
    elif isinstance(end_date, str):
        end = pd.to_datetime(end_date)
    else:
        end = end_date

    if start_date is None:
        start = end - timedelta(days=365)
    elif isinstance(start_date, str):
        start = pd.to_datetime(start_date)
    else:
        start = start_date

    dates = pd.date_range(start=start, end=end, freq="ME")

    # Generate symbols
    symbols = [f"MOCK{i:03d}-US" for i in range(n_constituents)]

    sectors = [
        "Information Technology",
        "Health Care",
        "Financials",
        "Consumer Discretionary",
        "Communication Services",
        "Industrials",
        "Consumer Staples",
        "Energy",
        "Utilities",
        "Materials",
        "Real Estate",
    ]

    rows = []
    for date in dates:
        # Randomly vary weights (should sum to 100)
        raw_weights = rng.uniform(0.5, 5, n_constituents)
        weights = (raw_weights / raw_weights.sum()) * 100

        for i, symbol in enumerate(symbols):
            rows.append(
                {
                    "date": date,
                    "P_SYMBOL": symbol,
                    "SEDOL": f"SEDOL{i:04d}",
                    "Asset ID": f"ASSET{i:05d}",
                    "FG_COMPANY_NAME": f"Mock Company {i}",
                    "GICS Sector": rng.choice(sectors),
                    "GICS Industry Group": f"Industry {i % 20}",
                    "Weight (%)": weights[i],
                    "Universe": universe_code,
                }
            )

    return pd.DataFrame(rows)


class MockBloombergFetcher(BaseDataFetcher):
    """Mock Bloomberg fetcher for testing.

    Generates realistic-looking mock data without requiring
    Bloomberg Terminal access.

    Parameters
    ----------
    base_price : float
        Base price for generated data (default: 100.0)
    volatility : float
        Volatility for generated data (default: 0.02)
    seed : int | None
        Random seed for reproducibility

    Examples
    --------
    >>> fetcher = MockBloombergFetcher(seed=42)
    >>> options = FetchOptions(symbols=["AAPL US Equity"])
    >>> results = fetcher.fetch(options)
    >>> results[0].symbol
    'AAPL US Equity'
    """

    def __init__(
        self,
        base_price: float = 100.0,
        volatility: float = 0.02,
        seed: int | None = None,
    ) -> None:
        self._base_price = base_price
        self._volatility = volatility
        self._seed = seed

        logger.debug(
            "Initializing MockBloombergFetcher",
            base_price=base_price,
            volatility=volatility,
            seed=seed,
        )

    @property
    def source(self) -> DataSource:
        """Return the data source type.

        Returns
        -------
        DataSource
            DataSource.BLOOMBERG
        """
        return DataSource.BLOOMBERG

    def validate_symbol(self, symbol: str) -> bool:
        """Validate that a symbol is valid for Bloomberg.

        Parameters
        ----------
        symbol : str
            The symbol to validate

        Returns
        -------
        bool
            True if the symbol matches Bloomberg format
        """
        if not symbol or not symbol.strip():
            return False
        return _is_valid_bloomberg_symbol(symbol.strip())

    @contextmanager
    def session(self) -> Generator[None, None, None]:
        """Mock session context manager.

        Yields
        ------
        None
            No actual session is created
        """
        logger.debug("Mock Bloomberg session started")
        yield None
        logger.debug("Mock Bloomberg session ended")

    def fetch(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch mock market data.

        Parameters
        ----------
        options : FetchOptions
            Fetch options

        Returns
        -------
        list[MarketDataResult]
            List of mock results
        """
        self._validate_options(options)

        logger.info(
            "Fetching mock Bloomberg data",
            symbols=options.symbols,
        )

        results: list[MarketDataResult] = []

        for symbol in options.symbols:
            df = generate_mock_ohlcv(
                symbol=symbol,
                start_date=options.start_date,
                end_date=options.end_date,
                interval=options.interval,
                base_price=self._base_price,
                volatility=self._volatility,
                seed=self._seed,
            )

            result = self._create_result(
                symbol=symbol,
                data=df,
                from_cache=False,
                metadata={
                    "mock": True,
                    "interval": options.interval.value,
                    "source": "mock_bloomberg",
                },
            )
            results.append(result)

        return results

    def fetch_financial(
        self,
        symbols: list[str],
        fields: list[str],
    ) -> pd.DataFrame:
        """Fetch mock financial data.

        Parameters
        ----------
        symbols : list[str]
            List of symbols
        fields : list[str]
            List of fields

        Returns
        -------
        pd.DataFrame
            Mock financial data
        """
        logger.info(
            "Fetching mock financial data",
            symbols=symbols,
            fields=fields,
        )

        return generate_mock_financial_data(
            symbols=symbols,
            fields=fields,
            seed=self._seed,
        )

    @staticmethod
    def convert_identifier(
        identifier: str,
        from_type: IdentifierType,
        to_type: IdentifierType = IdentifierType.TICKER,
    ) -> str:
        """Convert identifier (mock implementation).

        Returns the same format as BloombergFetcher.convert_identifier.
        """
        return BloombergFetcher.convert_identifier(identifier, from_type, to_type)


class MockFactSetFetcher(BaseDataFetcher):
    """Mock FactSet fetcher for testing.

    Generates realistic-looking mock data without requiring
    FactSet data files.

    Parameters
    ----------
    base_price : float
        Base price for generated data (default: 100.0)
    volatility : float
        Volatility for generated data (default: 0.02)
    n_constituents : int
        Number of constituents for index data (default: 50)
    seed : int | None
        Random seed for reproducibility

    Examples
    --------
    >>> fetcher = MockFactSetFetcher(seed=42)
    >>> options = FetchOptions(symbols=["AAPL-US"])
    >>> results = fetcher.fetch(options)
    >>> results[0].symbol
    'AAPL-US'
    """

    def __init__(
        self,
        base_price: float = 100.0,
        volatility: float = 0.02,
        n_constituents: int = 50,
        seed: int | None = None,
    ) -> None:
        self._base_price = base_price
        self._volatility = volatility
        self._n_constituents = n_constituents
        self._seed = seed

        logger.debug(
            "Initializing MockFactSetFetcher",
            base_price=base_price,
            volatility=volatility,
            n_constituents=n_constituents,
            seed=seed,
        )

    @property
    def source(self) -> DataSource:
        """Return the data source type.

        Returns
        -------
        DataSource
            DataSource.FACTSET
        """
        return DataSource.FACTSET

    def validate_symbol(self, symbol: str) -> bool:
        """Validate that a symbol is valid for FactSet.

        Parameters
        ----------
        symbol : str
            The symbol to validate

        Returns
        -------
        bool
            True if the symbol matches FactSet format
        """
        if not symbol or not symbol.strip():
            return False
        return bool(FACTSET_SYMBOL_PATTERN.match(symbol.strip()))

    def fetch(
        self,
        options: FetchOptions,
    ) -> list[MarketDataResult]:
        """Fetch mock market data.

        Parameters
        ----------
        options : FetchOptions
            Fetch options

        Returns
        -------
        list[MarketDataResult]
            List of mock results
        """
        self._validate_options(options)

        logger.info(
            "Fetching mock FactSet data",
            symbols=options.symbols,
        )

        results: list[MarketDataResult] = []

        for symbol in options.symbols:
            df = generate_mock_ohlcv(
                symbol=symbol,
                start_date=options.start_date,
                end_date=options.end_date,
                interval=options.interval,
                base_price=self._base_price,
                volatility=self._volatility,
                seed=self._seed,
            )

            result = self._create_result(
                symbol=symbol,
                data=df,
                from_cache=False,
                metadata={
                    "mock": True,
                    "interval": options.interval.value,
                    "source": "mock_factset",
                },
            )
            results.append(result)

        return results

    def load_constituents(
        self,
        universe_code: str,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
    ) -> pd.DataFrame:
        """Load mock index constituents.

        Parameters
        ----------
        universe_code : str
            Universe/index code
        start_date : str | datetime | None
            Start date
        end_date : str | datetime | None
            End date

        Returns
        -------
        pd.DataFrame
            Mock constituents data
        """
        logger.info(
            "Loading mock constituents",
            universe_code=universe_code,
        )

        return generate_mock_constituents(
            universe_code=universe_code,
            n_constituents=self._n_constituents,
            start_date=start_date,
            end_date=end_date,
            seed=self._seed,
        )

    def load_financial_data(
        self,
        factor_list: list[str],
        db_path: Any = None,
    ) -> pd.DataFrame:
        """Load mock financial data.

        Parameters
        ----------
        factor_list : list[str]
            List of factors to load
        db_path : Any
            Ignored (for API compatibility)

        Returns
        -------
        pd.DataFrame
            Mock financial data in wide format
        """
        logger.info(
            "Loading mock financial data",
            factors=factor_list,
        )

        if self._seed is None:
            seed = 42
        else:
            seed = self._seed
        rng = np.random.default_rng(seed)

        # Generate mock data
        n_dates = 12  # 12 months of data
        n_symbols = self._n_constituents

        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=n_dates, freq="ME")
        symbols = [f"MOCK{i:03d}-US" for i in range(n_symbols)]

        rows = []
        for date in dates:
            for symbol in symbols:
                row: dict[str, Any] = {"date": date, "P_SYMBOL": symbol}
                for factor in factor_list:
                    row[factor] = rng.uniform(0.01, 0.30)
                rows.append(row)

        return pd.DataFrame(rows)


__all__ = [
    "MockBloombergFetcher",
    "MockFactSetFetcher",
    "generate_mock_constituents",
    "generate_mock_financial_data",
    "generate_mock_ohlcv",
]
