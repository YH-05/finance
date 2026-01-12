"""Analysis API for technical analysis and correlation.

This module provides a unified interface for technical analysis operations
including moving averages, returns, volatility, and correlation analysis.
"""

from typing import Literal, Self, cast

import pandas as pd

from ..analysis import Analyzer, CorrelationAnalyzer
from ..errors import AnalysisError, ErrorCode, ValidationError
from ..types import AnalysisResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="analysis_api")

type CorrelationMethod = Literal["pearson", "spearman", "kendall"]


class Analysis:
    """Technical analysis class with method chaining support.

    Provides methods to add technical indicators to price data and
    perform correlation analysis between multiple instruments.

    Parameters
    ----------
    data : pd.DataFrame
        OHLCV DataFrame with at least a 'close' column
    symbol : str
        Symbol identifier for the data

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({"close": [100, 102, 101, 103, 105, 104, 106]})
    >>> analysis = Analysis(df)
    >>> result = (
    ...     analysis
    ...     .add_sma(period=3)
    ...     .add_ema(period=3)
    ...     .add_returns()
    ...     .add_volatility(period=3)
    ... )
    >>> result.data.columns.tolist()
    ['close', 'sma_3', 'ema_3', 'returns', 'volatility']
    """

    def __init__(
        self,
        data: pd.DataFrame | None,
        symbol: str = "",
    ) -> None:
        """Initialize the Analysis instance.

        Parameters
        ----------
        data : pd.DataFrame | None
            OHLCV DataFrame with at least a 'close' column
        symbol : str, default=""
            Symbol identifier for the data

        Raises
        ------
        ValidationError
            If data is empty or missing required columns
        """
        logger.debug(
            "Initializing Analysis",
            symbol=symbol,
            rows=len(data) if data is not None else 0,
        )

        if data is None or data.empty:
            logger.error("Empty data provided")
            raise ValidationError(
                "Data cannot be empty",
                field="data",
                value="empty DataFrame",
                code=ErrorCode.INVALID_PARAMETER,
            )

        self._analyzer = Analyzer(data, symbol=symbol)
        self._symbol = symbol

        logger.info(
            "Analysis initialized",
            symbol=symbol,
            rows=len(data),
        )

    @property
    def data(self) -> pd.DataFrame:
        """Get the DataFrame with all added indicators.

        Returns
        -------
        pd.DataFrame
            Copy of the data with indicators added as columns
        """
        return self._analyzer.data

    @property
    def indicators(self) -> list[str]:
        """Get list of added indicator names.

        Returns
        -------
        list[str]
            List of indicator column names that have been added
        """
        return list(self._analyzer.indicators.keys())

    def add_sma(
        self,
        period: int = 20,
        column: str = "close",
    ) -> Self:
        """Add Simple Moving Average indicator.

        Parameters
        ----------
        period : int, default=20
            Window size for SMA calculation
        column : str, default="close"
            Column to calculate SMA on

        Returns
        -------
        Self
            Returns self for method chaining

        Raises
        ------
        ValidationError
            If period is invalid

        Examples
        --------
        >>> analysis.add_sma(period=20).add_sma(period=50).add_sma(period=200)
        """
        logger.debug("Adding SMA", period=period, column=column)

        if period < 1:
            logger.error("Invalid period", period=period)
            raise ValidationError(
                f"Period must be positive, got {period}",
                field="period",
                value=str(period),
                code=ErrorCode.INVALID_PARAMETER,
            )

        self._analyzer.add_sma(window=period)
        return self

    def add_ema(
        self,
        period: int = 20,
        column: str = "close",
    ) -> Self:
        """Add Exponential Moving Average indicator.

        Parameters
        ----------
        period : int, default=20
            Span for EMA calculation
        column : str, default="close"
            Column to calculate EMA on

        Returns
        -------
        Self
            Returns self for method chaining

        Raises
        ------
        ValidationError
            If period is invalid

        Examples
        --------
        >>> analysis.add_ema(period=12).add_ema(period=26)
        """
        logger.debug("Adding EMA", period=period, column=column)

        if period < 1:
            logger.error("Invalid period", period=period)
            raise ValidationError(
                f"Period must be positive, got {period}",
                field="period",
                value=str(period),
                code=ErrorCode.INVALID_PARAMETER,
            )

        self._analyzer.add_ema(window=period)
        return self

    def add_returns(
        self,
        column: str = "close",
    ) -> Self:
        """Add daily returns indicator.

        Parameters
        ----------
        column : str, default="close"
            Column to calculate returns on

        Returns
        -------
        Self
            Returns self for method chaining

        Examples
        --------
        >>> analysis.add_returns()
        """
        logger.debug("Adding returns", column=column)

        self._analyzer.add_returns()
        return self

    def add_volatility(
        self,
        period: int = 20,
        column: str = "close",
        annualize: bool = True,
    ) -> Self:
        """Add volatility indicator.

        Parameters
        ----------
        period : int, default=20
            Rolling window size for volatility calculation
        column : str, default="close"
            Column to calculate volatility on
        annualize : bool, default=True
            Whether to annualize volatility (multiply by sqrt(252))

        Returns
        -------
        Self
            Returns self for method chaining

        Raises
        ------
        ValidationError
            If period is invalid

        Examples
        --------
        >>> analysis.add_volatility(period=20)
        """
        logger.debug(
            "Adding volatility", period=period, column=column, annualize=annualize
        )

        if period < 2:
            logger.error("Invalid period", period=period)
            raise ValidationError(
                f"Period must be at least 2, got {period}",
                field="period",
                value=str(period),
                code=ErrorCode.INVALID_PARAMETER,
            )

        self._analyzer.add_volatility(window=period, annualize=annualize)
        return self

    def result(self) -> AnalysisResult:
        """Get the analysis result.

        Returns
        -------
        AnalysisResult
            Result object containing data, indicators, and statistics

        Examples
        --------
        >>> result = analysis.add_sma(20).add_returns().result()
        >>> result.symbol
        'AAPL'
        """
        return self._analyzer.result()

    @staticmethod
    def correlation(
        dataframes: list[pd.DataFrame],
        symbols: list[str] | None = None,
        column: str = "close",
        method: CorrelationMethod = "pearson",
    ) -> pd.DataFrame:
        """Calculate correlation matrix for multiple instruments.

        Parameters
        ----------
        dataframes : list[pd.DataFrame]
            List of DataFrames, one per instrument
        symbols : list[str] | None
            List of symbol names for column labels.
            If None, uses default labels (Symbol_0, Symbol_1, etc.)
        column : str, default="close"
            Column to use for correlation calculation
        method : {"pearson", "spearman", "kendall"}, default="pearson"
            Correlation method to use

        Returns
        -------
        pd.DataFrame
            Symmetric correlation matrix

        Raises
        ------
        ValidationError
            If fewer than 2 DataFrames provided
        AnalysisError
            If correlation calculation fails

        Examples
        --------
        >>> corr = Analysis.correlation(
        ...     [df_aapl, df_googl, df_msft],
        ...     symbols=["AAPL", "GOOGL", "MSFT"]
        ... )
        >>> corr.loc["AAPL", "GOOGL"]
        0.85
        """
        logger.info(
            "Calculating correlation matrix",
            num_dataframes=len(dataframes),
            symbols=symbols,
            method=method,
        )

        if len(dataframes) < 2:
            logger.error("Insufficient DataFrames", count=len(dataframes))
            raise ValidationError(
                f"At least 2 DataFrames required, got {len(dataframes)}",
                field="dataframes",
                value=str(len(dataframes)),
                code=ErrorCode.INVALID_PARAMETER,
            )

        if symbols is None:
            symbols = [f"Symbol_{i}" for i in range(len(dataframes))]
        elif len(symbols) != len(dataframes):
            logger.error(
                "Symbol count mismatch",
                symbols_count=len(symbols),
                df_count=len(dataframes),
            )
            raise ValidationError(
                f"Number of symbols ({len(symbols)}) must match "
                f"number of DataFrames ({len(dataframes)})",
                field="symbols",
                value=str(len(symbols)),
                code=ErrorCode.INVALID_PARAMETER,
            )

        # Extract the specified column from each DataFrame
        try:
            price_data: dict[str, pd.Series] = {}
            for i, df in enumerate(dataframes):
                col = column.lower()
                # Try to find the column (case-insensitive)
                actual_col = None
                for c in df.columns:
                    if c.lower() == col:
                        actual_col = c
                        break

                if actual_col is None:
                    logger.error(
                        "Column not found",
                        column=column,
                        available=list(df.columns),
                        symbol=symbols[i],
                    )
                    raise AnalysisError(
                        f"Column '{column}' not found in DataFrame for {symbols[i]}",
                        operation="correlation",
                        code=ErrorCode.INVALID_PARAMETER,
                    )

                price_data[symbols[i]] = cast(pd.Series, df[actual_col])

            # Create combined DataFrame
            combined = pd.DataFrame(price_data)

            # Calculate correlation matrix
            correlation_matrix = CorrelationAnalyzer.calculate_correlation_matrix(
                combined, method=method
            )

            logger.info(
                "Correlation matrix calculated",
                shape=correlation_matrix.shape,
                method=method,
            )

            return correlation_matrix

        except (ValidationError, AnalysisError):
            raise
        except Exception as e:
            logger.error(
                "Correlation calculation failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise AnalysisError(
                f"Failed to calculate correlation: {e}",
                operation="correlation",
                code=ErrorCode.CALCULATION_ERROR,
                cause=e,
            ) from e

    @staticmethod
    def rolling_correlation(
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        period: int = 20,
        column: str = "close",
    ) -> pd.Series:
        """Calculate rolling correlation between two instruments.

        Parameters
        ----------
        df1 : pd.DataFrame
            First instrument's DataFrame
        df2 : pd.DataFrame
            Second instrument's DataFrame
        period : int, default=20
            Rolling window size
        column : str, default="close"
            Column to use for correlation calculation

        Returns
        -------
        pd.Series
            Rolling correlation values

        Raises
        ------
        ValidationError
            If period is invalid
        AnalysisError
            If calculation fails

        Examples
        --------
        >>> rolling_corr = Analysis.rolling_correlation(df_aapl, df_spy, period=20)
        >>> rolling_corr.iloc[-1]
        0.92
        """
        logger.info(
            "Calculating rolling correlation",
            period=period,
            column=column,
        )

        if period < 2:
            logger.error("Invalid period", period=period)
            raise ValidationError(
                f"Period must be at least 2, got {period}",
                field="period",
                value=str(period),
                code=ErrorCode.INVALID_PARAMETER,
            )

        try:
            # Find the column (case-insensitive)
            def get_column(df: pd.DataFrame, col_name: str) -> pd.Series:
                col_lower = col_name.lower()
                for c in df.columns:
                    if c.lower() == col_lower:
                        return cast(pd.Series, df[c])
                raise AnalysisError(
                    f"Column '{col_name}' not found in DataFrame",
                    operation="rolling_correlation",
                    code=ErrorCode.INVALID_PARAMETER,
                )

            series1 = get_column(df1, column)
            series2 = get_column(df2, column)

            # Align series by index
            aligned = pd.concat([series1, series2], axis=1).dropna()
            if len(aligned) < period:
                logger.warning(
                    "Insufficient overlapping data",
                    available=len(aligned),
                    required=period,
                )

            result = CorrelationAnalyzer.calculate_rolling_correlation(
                aligned.iloc[:, 0],
                aligned.iloc[:, 1],
                window=period,
            )

            logger.info(
                "Rolling correlation calculated",
                period=period,
                valid_values=result.notna().sum(),
            )

            return result

        except (ValidationError, AnalysisError):
            raise
        except Exception as e:
            logger.error(
                "Rolling correlation calculation failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise AnalysisError(
                f"Failed to calculate rolling correlation: {e}",
                operation="rolling_correlation",
                code=ErrorCode.CALCULATION_ERROR,
                cause=e,
            ) from e

    @staticmethod
    def beta(
        stock: pd.DataFrame,
        benchmark: pd.DataFrame,
        column: str = "close",
    ) -> float:
        """Calculate beta coefficient against a benchmark.

        Beta measures the sensitivity of an asset's returns to benchmark returns.
        - Beta > 1: Higher volatility than benchmark
        - Beta < 1: Lower volatility than benchmark
        - Beta = 1: Same volatility as benchmark

        Parameters
        ----------
        stock : pd.DataFrame
            Stock DataFrame
        benchmark : pd.DataFrame
            Benchmark DataFrame (e.g., S&P 500)
        column : str, default="close"
            Column to use for calculation

        Returns
        -------
        float
            Beta coefficient

        Raises
        ------
        AnalysisError
            If calculation fails

        Examples
        --------
        >>> beta = Analysis.beta(df_aapl, df_spy)
        >>> beta
        1.15
        """
        logger.info("Calculating beta", column=column)

        try:
            # Find the column (case-insensitive)
            def get_column(df: pd.DataFrame, col_name: str) -> pd.Series:
                col_lower = col_name.lower()
                for c in df.columns:
                    if c.lower() == col_lower:
                        return cast(pd.Series, df[c])
                raise AnalysisError(
                    f"Column '{col_name}' not found in DataFrame",
                    operation="beta",
                    code=ErrorCode.INVALID_PARAMETER,
                )

            stock_prices = get_column(stock, column)
            benchmark_prices = get_column(benchmark, column)

            # Calculate returns
            stock_returns = stock_prices.pct_change().dropna()
            benchmark_returns = benchmark_prices.pct_change().dropna()

            # Align returns by index
            aligned = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()

            if len(aligned) < 2:
                logger.warning(
                    "Insufficient overlapping data for beta calculation",
                    available=len(aligned),
                )
                return float("nan")

            beta_value = CorrelationAnalyzer.calculate_beta(
                aligned.iloc[:, 0],
                aligned.iloc[:, 1],
            )

            logger.info("Beta calculated", beta=beta_value)

            return beta_value

        except AnalysisError:
            raise
        except Exception as e:
            logger.error(
                "Beta calculation failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise AnalysisError(
                f"Failed to calculate beta: {e}",
                operation="beta",
                code=ErrorCode.CALCULATION_ERROR,
                cause=e,
            ) from e


__all__ = [
    "Analysis",
]
