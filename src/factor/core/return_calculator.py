"""Return calculation algorithms for factor analysis.

This module provides return calculation methods including:
- Multi-period returns (1M, 3M, 6M, 1Y, 3Y, 5Y)
- Forward returns
- Annualized returns
- Active returns (relative to benchmark)
"""

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
from utils_core.logging import get_logger

from ..errors import ValidationError

logger = get_logger(__name__)


# Type aliases
type PeriodName = Literal["1M", "3M", "6M", "1Y", "3Y", "5Y"]


@dataclass
class ReturnConfig:
    """Configuration for return calculations.

    Parameters
    ----------
    periods_months : list[int]
        List of periods in months for return calculation.
        Default: [1, 3, 6, 12, 36, 60] for 1M, 3M, 6M, 1Y, 3Y, 5Y
    min_periods : int
        Minimum number of periods required for calculation. Default: 1
    annualize : bool
        Whether to calculate annualized returns. Default: True
    """

    periods_months: list[int] = field(default_factory=lambda: [1, 3, 6, 12, 36, 60])
    min_periods: int = 1
    annualize: bool = True


class ReturnCalculator:
    """Calculator for various return metrics.

    Provides methods for calculating returns, forward returns,
    and active returns for financial time series data.

    Parameters
    ----------
    config : ReturnConfig | None
        Configuration for return calculations. If None, uses defaults.

    Examples
    --------
    >>> calculator = ReturnCalculator()
    >>> returns = calculator.calculate_returns(price_df)
    """

    def __init__(self, config: ReturnConfig | None = None) -> None:
        """Initialize ReturnCalculator.

        Parameters
        ----------
        config : ReturnConfig | None
            Configuration for calculations. Uses defaults if None.
        """
        self.config = config or ReturnConfig()
        logger.debug(
            "ReturnCalculator initialized",
            periods=self.config.periods_months,
            annualize=self.config.annualize,
        )

    def calculate_returns(
        self,
        prices: pd.DataFrame,
        *,
        date_column: str = "date",
        symbol_column: str = "symbol",
        price_column: str = "price",
    ) -> pd.DataFrame:
        """Calculate multi-period returns from price data.

        Parameters
        ----------
        prices : pd.DataFrame
            Price data with date, symbol, and price columns
        date_column : str, default="date"
            Name of the date column
        symbol_column : str, default="symbol"
            Name of the symbol column
        price_column : str, default="price"
            Name of the price column

        Returns
        -------
        pd.DataFrame
            DataFrame with MultiIndex (symbol, date) containing:
            - Original price
            - Return_{period} for each period
            - Forward_Return_{period} for each period
            - Annualized versions if config.annualize is True

        Raises
        ------
        ValidationError
            If required columns are missing

        Examples
        --------
        >>> calculator = ReturnCalculator()
        >>> prices = pd.DataFrame({
        ...     "date": pd.date_range("2020-01-01", periods=24, freq="ME"),
        ...     "symbol": ["AAPL"] * 24,
        ...     "price": [100 + i * 2 for i in range(24)]
        ... })
        >>> returns = calculator.calculate_returns(prices)
        """
        # Validate required columns
        required_cols = [date_column, symbol_column, price_column]
        missing_cols = [c for c in required_cols if c not in prices.columns]
        if missing_cols:
            raise ValidationError(
                f"Missing required columns: {missing_cols}",
                field="columns",
                value=missing_cols,
            )

        logger.debug(
            "Calculating returns",
            data_shape=prices.shape,
            periods=self.config.periods_months,
        )

        # Ensure date column is in the DataFrame
        if date_column not in prices.columns:
            df_reset = prices.reset_index()
        else:
            df_reset = prices.copy()

        # Get all unique symbols and dates
        all_symbols = df_reset[symbol_column].unique().tolist()
        all_dates = df_reset[date_column].unique().tolist()

        # Create complete MultiIndex for all symbol-date combinations
        new_index = pd.MultiIndex.from_product(
            [all_symbols, all_dates], names=[symbol_column, date_column]
        )

        # Reindex to create a regular time series with NaN for missing values
        df_regular = df_reset.set_index([symbol_column, date_column]).reindex(new_index)

        # Sort by date within each symbol
        df_regular = df_regular.sort_index(level=date_column)

        # Calculate returns for each period
        for period_month in self.config.periods_months:
            period_name = self._get_period_name(period_month)

            # Calculate past returns
            df_regular[f"Return_{period_name}"] = df_regular.groupby(
                level=symbol_column
            )[price_column].pct_change(period_month)

            # Calculate forward returns
            df_regular[f"Forward_Return_{period_name}"] = df_regular.groupby(
                level=symbol_column
            )[f"Return_{period_name}"].shift(-period_month)

            # Calculate annualized versions
            if self.config.annualize:
                annualization_factor = 12 / period_month
                df_regular[f"Return_{period_name}_annualized"] = (
                    df_regular[f"Return_{period_name}"] * annualization_factor
                )
                df_regular[f"Forward_Return_{period_name}_annualized"] = (
                    df_regular[f"Forward_Return_{period_name}"] * annualization_factor
                )

        logger.info(
            "Returns calculated",
            symbols=len(all_symbols),
            dates=len(all_dates),
            periods=len(self.config.periods_months),
        )

        return df_regular

    def calculate_forward_returns(
        self,
        data: pd.DataFrame | pd.Series,
        periods: int,
        *,
        symbol_column: str | None = None,
    ) -> pd.DataFrame | pd.Series:
        """Calculate forward returns for a specific period.

        Parameters
        ----------
        data : pd.DataFrame | pd.Series
            Return data (not prices). For DataFrame, returns are calculated
            per symbol group if symbol_column is provided.
        periods : int
            Number of periods to shift forward
        symbol_column : str | None
            Column name for grouping by symbol (for DataFrame only)

        Returns
        -------
        pd.DataFrame | pd.Series
            Forward returns with same shape as input

        Examples
        --------
        >>> calculator = ReturnCalculator()
        >>> returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        >>> forward = calculator.calculate_forward_returns(returns, periods=2)
        """
        logger.debug(
            "Calculating forward returns",
            periods=periods,
            data_shape=data.shape if hasattr(data, "shape") else len(data),
        )

        if isinstance(data, pd.Series):
            return data.shift(-periods)

        if symbol_column and symbol_column in data.columns:
            # Group by symbol and shift
            return data.groupby(symbol_column).shift(-periods)

        return data.shift(-periods)

    def annualize_return(
        self,
        returns: pd.DataFrame | pd.Series,
        period_months: int,
        *,
        method: Literal["simple", "compound"] = "simple",
    ) -> pd.DataFrame | pd.Series:
        """Annualize returns from a specific period.

        Parameters
        ----------
        returns : pd.DataFrame | pd.Series
            Return data for the given period
        period_months : int
            The period length in months (e.g., 3 for quarterly returns)
        method : {"simple", "compound"}, default="simple"
            - "simple": Multiply by annualization factor (12 / period_months)
            - "compound": (1 + r)^(12/period_months) - 1

        Returns
        -------
        pd.DataFrame | pd.Series
            Annualized returns with same shape as input

        Examples
        --------
        >>> calculator = ReturnCalculator()
        >>> quarterly_return = pd.Series([0.05, 0.03, 0.04])  # 5%, 3%, 4%
        >>> annual = calculator.annualize_return(quarterly_return, 3, method="simple")
        """
        if period_months <= 0:
            raise ValidationError(
                f"period_months must be positive, got {period_months}",
                field="period_months",
                value=period_months,
            )

        logger.debug(
            "Annualizing returns",
            period_months=period_months,
            method=method,
        )

        annualization_factor = 12 / period_months

        if method == "simple":
            return returns * annualization_factor
        else:  # compound
            return (1 + returns) ** annualization_factor - 1

    def calculate_active_return(
        self,
        returns: pd.DataFrame,
        benchmark_column: str,
        *,
        return_columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """Calculate active returns relative to a benchmark.

        Active return = Asset return - Benchmark return

        Parameters
        ----------
        returns : pd.DataFrame
            DataFrame containing asset returns and benchmark returns.
            Can be in wide format (assets as columns) or long format.
        benchmark_column : str
            Name of the column containing benchmark returns
        return_columns : list[str] | None
            Columns to calculate active returns for. If None, uses all
            numeric columns except the benchmark column.

        Returns
        -------
        pd.DataFrame
            DataFrame with active returns

        Raises
        ------
        ValidationError
            If benchmark column is missing

        Examples
        --------
        >>> calculator = ReturnCalculator()
        >>> returns = pd.DataFrame({
        ...     "AAPL": [0.05, 0.03, 0.04],
        ...     "MSFT": [0.04, 0.02, 0.05],
        ...     "SPY": [0.03, 0.02, 0.03]  # Benchmark
        ... })
        >>> active = calculator.calculate_active_return(returns, "SPY")
        """
        if benchmark_column not in returns.columns:
            raise ValidationError(
                f"Benchmark column '{benchmark_column}' not found",
                field="benchmark_column",
                value=benchmark_column,
            )

        logger.debug(
            "Calculating active returns",
            benchmark=benchmark_column,
            data_shape=returns.shape,
        )

        result = returns.copy()

        # Determine which columns to process
        if return_columns is None:
            # Use all numeric columns except benchmark
            numeric_cols = result.select_dtypes(include=[np.number]).columns
            return_columns = [c for c in numeric_cols if c != benchmark_column]

        benchmark_returns = result[benchmark_column]

        # Calculate active returns
        for col in return_columns:
            if col in result.columns:
                result[f"{col}_active"] = result[col] - benchmark_returns

        logger.info(
            "Active returns calculated",
            columns=len(return_columns),
            benchmark=benchmark_column,
        )

        return result

    def calculate_cagr(
        self,
        prices: pd.Series,
        years: int,
    ) -> pd.Series:
        """Calculate Compound Annual Growth Rate (CAGR).

        CAGR = (End Value / Start Value)^(1/years) - 1

        Parameters
        ----------
        prices : pd.Series
            Price series (monthly frequency assumed)
        years : int
            Number of years for CAGR calculation

        Returns
        -------
        pd.Series
            Rolling CAGR with same index as input

        Raises
        ------
        ValidationError
            If years is not positive

        Examples
        --------
        >>> calculator = ReturnCalculator()
        >>> prices = pd.Series([100, 110, 121, 133.1, 146.41])  # ~10% annual
        >>> cagr = calculator.calculate_cagr(prices, years=1)
        """
        if years <= 0:
            raise ValidationError(
                f"years must be positive, got {years}",
                field="years",
                value=years,
            )

        if prices.empty:
            return pd.Series(dtype=float)

        logger.debug("Calculating CAGR", years=years, data_points=len(prices))

        # Period T = years * 12 months
        periods = years * 12

        # Start value (lagged)
        v_start = prices.shift(periods)

        # End value (current)
        v_end = prices

        # CAGR = (v_end / v_start)^(1/years) - 1
        # Handle zero/negative values
        cagr = np.where(
            v_start > 0,
            (v_end / v_start) ** (1 / years) - 1,
            np.nan,
        )

        return pd.Series(cagr, index=prices.index)

    @staticmethod
    def _get_period_name(period_months: int) -> str:
        """Convert period in months to human-readable name."""
        if period_months >= 36:
            return f"{period_months // 12}Y"
        return f"{period_months}M"


__all__ = ["ReturnCalculator", "ReturnConfig"]
