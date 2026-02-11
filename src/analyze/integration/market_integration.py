"""Market data integration for analyze package.

This module provides integration between the market package data sources
and the analyze package analysis functions. It enables a unified workflow
for fetching market data and performing technical and statistical analysis.

Classes
-------
MarketDataAnalyzer
    Main class for fetching market data and running analysis

Functions
---------
analyze_market_data
    Analyze a DataFrame of market data with technical indicators and statistics
fetch_and_analyze
    Convenience function to fetch market data and run analysis

Examples
--------
>>> from analyze.integration import MarketDataAnalyzer
>>> analyzer = MarketDataAnalyzer()
>>> results = analyzer.fetch_and_analyze(
...     symbols=["AAPL", "GOOGL"],
...     start_date="2024-01-01",
...     end_date="2024-12-31",
... )
>>> results["AAPL"]["technical_indicators"]["rsi"]
<Series with RSI values>
"""

from datetime import datetime
from typing import Any, cast

import pandas as pd
import yfinance as yf

from analyze.statistics.descriptive import describe
from analyze.technical.indicators import TechnicalIndicators
from analyze.types import TickerInfo, map_quote_type_to_asset_class
from market.errors import DataFetchError, ErrorCode
from market.yfinance import FetchOptions, YFinanceFetcher
from market.yfinance.types import Interval
from utils_core.logging import get_logger

logger = get_logger(__name__)


class MarketDataAnalyzer:
    """Analyzer for market data with integrated data fetching.

    This class provides a unified interface for fetching market data
    from various sources (YFinance, FRED) and analyzing it using
    the analyze package's technical and statistical functions.

    Parameters
    ----------
    fetcher : YFinanceFetcher | None
        Custom fetcher instance. If None, a default fetcher is created.

    Attributes
    ----------
    fetcher : YFinanceFetcher
        The data fetcher instance

    Examples
    --------
    >>> analyzer = MarketDataAnalyzer()
    >>> results = analyzer.fetch_and_analyze(
    ...     symbols=["AAPL"],
    ...     start_date="2024-01-01",
    ... )
    >>> print(results["AAPL"]["statistics"].mean)
    150.5
    """

    def __init__(
        self,
        fetcher: YFinanceFetcher | None = None,
    ) -> None:
        """Initialize MarketDataAnalyzer.

        Parameters
        ----------
        fetcher : YFinanceFetcher | None
            Custom fetcher instance. If None, creates a default fetcher.
        """
        logger.debug("Initializing MarketDataAnalyzer")
        self._fetcher = fetcher or YFinanceFetcher()
        logger.info("MarketDataAnalyzer initialized")

    @property
    def fetcher(self) -> YFinanceFetcher:
        """Get the data fetcher instance.

        Returns
        -------
        YFinanceFetcher
            The data fetcher
        """
        return self._fetcher

    def fetch_and_analyze(
        self,
        symbols: list[str],
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        interval: Interval = Interval.DAILY,
    ) -> dict[str, dict[str, Any]]:
        """Fetch market data and run analysis.

        Parameters
        ----------
        symbols : list[str]
            List of stock symbols to fetch
        start_date : datetime | str | None
            Start date for data range
        end_date : datetime | str | None
            End date for data range
        interval : Interval
            Data interval (default: DAILY)

        Returns
        -------
        dict[str, dict[str, Any]]
            Dictionary keyed by symbol containing analysis results.
            Each result contains:
            - raw_data: The original DataFrame
            - technical_indicators: Dict of indicator Series
            - statistics: DescriptiveStats for close prices
            - data_empty: bool indicating if data was empty

        Raises
        ------
        ValueError
            If symbols list is empty

        Examples
        --------
        >>> analyzer = MarketDataAnalyzer()
        >>> result = analyzer.fetch_and_analyze(["AAPL"], "2024-01-01")
        >>> result["AAPL"]["statistics"].mean
        175.5
        """
        logger.info(
            "Starting fetch and analyze",
            symbols=symbols,
            start_date=str(start_date),
            end_date=str(end_date),
            interval=interval.value,
        )

        if not symbols:
            logger.error("Empty symbols list provided")
            raise ValueError("symbols must not be empty")

        # Fetch data from market package
        options = FetchOptions(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

        logger.debug("Fetching market data", symbol_count=len(symbols))
        results = self._fetcher.fetch(options)

        # Analyze each result
        analysis_results: dict[str, dict[str, Any]] = {}

        for result in results:
            symbol = result.symbol
            logger.debug("Analyzing symbol", symbol=symbol)

            if result.is_empty:
                logger.warning("Empty data for symbol", symbol=symbol)
                analysis_results[symbol] = {
                    "raw_data": result.data,
                    "technical_indicators": {},
                    "statistics": None,
                    "data_empty": True,
                }
                continue

            # Run analysis
            analysis = analyze_market_data(result.data)
            analysis_results[symbol] = {
                "raw_data": result.data,
                **analysis,
                "data_empty": False,
            }
            logger.debug(
                "Analysis completed for symbol",
                symbol=symbol,
                row_count=len(result.data),
            )

        logger.info(
            "Fetch and analyze completed",
            total_symbols=len(symbols),
            analyzed_count=len(
                [r for r in analysis_results.values() if not r.get("data_empty")]
            ),
        )

        return analysis_results

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        """Get metadata information for a single ticker.

        Fetches basic information about a financial instrument using
        the yfinance API, including name, sector, industry, and asset class.

        Parameters
        ----------
        ticker : str
            Ticker symbol to look up (e.g., "AAPL", "VOO", "^GSPC").

        Returns
        -------
        TickerInfo
            Metadata about the ticker.

        Raises
        ------
        DataFetchError
            If the ticker info cannot be fetched or is empty.

        Examples
        --------
        >>> analyzer = MarketDataAnalyzer()
        >>> info = analyzer.get_ticker_info("AAPL")
        >>> info.ticker
        'AAPL'
        >>> info.sector
        'Technology'
        """
        logger.debug("Fetching ticker info", ticker=ticker)

        try:
            yf_ticker = yf.Ticker(ticker)
            info: dict[str, Any] = yf_ticker.info

            if not info:
                logger.error("Empty info returned for ticker", ticker=ticker)
                raise DataFetchError(
                    f"No info available for ticker: {ticker}",
                    symbol=ticker,
                    source="yfinance",
                    code=ErrorCode.DATA_NOT_FOUND,
                )

            name = info.get("shortName") or info.get("longName") or ticker
            sector = info.get("sector")
            industry = info.get("industry")
            quote_type = info.get("quoteType")
            asset_class = map_quote_type_to_asset_class(quote_type)

            ticker_info = TickerInfo(
                ticker=ticker,
                name=str(name),
                sector=str(sector) if sector else None,
                industry=str(industry) if industry else None,
                asset_class=asset_class,
            )

            logger.debug(
                "Ticker info fetched",
                ticker=ticker,
                name=ticker_info.name,
                sector=ticker_info.sector,
                asset_class=ticker_info.asset_class,
            )

            return ticker_info

        except DataFetchError:
            raise
        except Exception as e:
            logger.error(
                "Failed to fetch ticker info",
                ticker=ticker,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DataFetchError(
                f"Failed to fetch ticker info for {ticker}: {e}",
                symbol=ticker,
                source="yfinance",
                code=ErrorCode.API_ERROR,
                cause=e,
            ) from e

    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
        """Get metadata information for multiple tickers.

        Fetches basic information for each ticker in the provided list.

        Parameters
        ----------
        tickers : list[str]
            List of ticker symbols to look up.

        Returns
        -------
        dict[str, TickerInfo]
            Dictionary mapping ticker symbols to their TickerInfo.

        Raises
        ------
        ValueError
            If tickers list is empty.
        DataFetchError
            If fetching info fails for any ticker.

        Examples
        --------
        >>> analyzer = MarketDataAnalyzer()
        >>> infos = analyzer.get_ticker_infos(["AAPL", "GOOGL"])
        >>> infos["AAPL"].name
        'Apple Inc.'
        """
        logger.info("Fetching ticker infos", tickers=tickers, count=len(tickers))

        if not tickers:
            logger.error("Empty tickers list provided")
            raise ValueError("tickers must not be empty")

        result: dict[str, TickerInfo] = {}

        for ticker in tickers:
            result[ticker] = self.get_ticker_info(ticker)

        logger.info(
            "Ticker infos fetched",
            tickers=tickers,
            count=len(result),
        )

        return result


def analyze_market_data(
    data: pd.DataFrame,
    sma_windows: list[int] | None = None,
    ema_windows: list[int] | None = None,
    rsi_period: int = 14,
) -> dict[str, Any]:
    """Analyze market data DataFrame with technical indicators and statistics.

    Parameters
    ----------
    data : pd.DataFrame
        Market data DataFrame with OHLCV columns
    sma_windows : list[int] | None
        Windows for SMA calculation (default: [20, 50])
    ema_windows : list[int] | None
        Windows for EMA calculation (default: [12, 26])
    rsi_period : int
        Period for RSI calculation (default: 14)

    Returns
    -------
    dict[str, Any]
        Analysis results containing:
        - technical_indicators: Dict of indicator name to pd.Series
        - statistics: DescriptiveStats for close prices

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     "close": [100.0, 101.0, 102.0, 103.0, 104.0]
    ... })
    >>> result = analyze_market_data(data)
    >>> "returns" in result["technical_indicators"]
    True
    """
    logger.debug(
        "Analyzing market data",
        row_count=len(data),
        columns=list(data.columns),
    )

    if sma_windows is None:
        sma_windows = [20, 50]

    if ema_windows is None:
        ema_windows = [12, 26]

    # Get close prices for analysis
    if "close" in data.columns:
        close_prices = cast("pd.Series", data["close"])
    else:
        close_prices = pd.Series(dtype=float)

    if close_prices.empty:
        logger.warning("No close prices found in data")
        return {
            "technical_indicators": {},
            "statistics": None,
        }

    # Calculate technical indicators
    logger.debug("Calculating technical indicators")
    technical_indicators: dict[str, pd.Series] = {}

    # Returns
    technical_indicators["returns"] = TechnicalIndicators.calculate_returns(
        close_prices
    )

    # SMAs
    for window in sma_windows:
        if len(close_prices) >= window:
            technical_indicators[f"sma_{window}"] = TechnicalIndicators.calculate_sma(
                close_prices, window
            )

    # EMAs
    for window in ema_windows:
        if len(close_prices) >= window:
            technical_indicators[f"ema_{window}"] = TechnicalIndicators.calculate_ema(
                close_prices, window
            )

    # RSI
    if len(close_prices) >= rsi_period:
        technical_indicators["rsi"] = TechnicalIndicators.calculate_rsi(
            close_prices, rsi_period
        )

    # Volatility (need at least 2 data points for returns)
    if len(close_prices) >= 20:
        returns = technical_indicators["returns"]
        technical_indicators["volatility"] = TechnicalIndicators.calculate_volatility(
            returns, window=20
        )

    # Calculate statistics on close prices
    logger.debug("Calculating descriptive statistics")
    statistics = describe(close_prices)

    logger.info(
        "Market data analysis completed",
        indicator_count=len(technical_indicators),
        statistics_count=statistics.count,
    )

    return {
        "technical_indicators": technical_indicators,
        "statistics": statistics,
    }


def fetch_and_analyze(
    symbols: list[str],
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
    interval: Interval = Interval.DAILY,
) -> dict[str, dict[str, Any]]:
    """Convenience function to fetch market data and run analysis.

    This is a shorthand for creating a MarketDataAnalyzer and calling
    fetch_and_analyze on it.

    Parameters
    ----------
    symbols : list[str]
        List of stock symbols to fetch
    start_date : datetime | str | None
        Start date for data range
    end_date : datetime | str | None
        End date for data range
    interval : Interval
        Data interval (default: DAILY)

    Returns
    -------
    dict[str, dict[str, Any]]
        Dictionary keyed by symbol containing analysis results

    Examples
    --------
    >>> results = fetch_and_analyze(["AAPL"], "2024-01-01")
    >>> results["AAPL"]["statistics"].mean
    175.5
    """
    logger.info("fetch_and_analyze called", symbols=symbols)
    analyzer = MarketDataAnalyzer()
    return analyzer.fetch_and_analyze(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
    )


__all__ = [
    "MarketDataAnalyzer",
    "analyze_market_data",
    "fetch_and_analyze",
]
