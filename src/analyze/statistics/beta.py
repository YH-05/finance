"""Rolling beta analysis for statistical analysis.

This module provides the RollingBetaAnalyzer class for calculating
rolling beta coefficients between assets and a benchmark.

Classes
-------
RollingBetaAnalyzer : Rolling beta analysis class inheriting from StatisticalAnalyzer

Examples
--------
>>> import pandas as pd
>>> from analyze.statistics.beta import RollingBetaAnalyzer
>>> df = pd.DataFrame({
...     "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02],
...     "SPY": [0.01, 0.02, -0.01, 0.03, 0.01],
... })
>>> analyzer = RollingBetaAnalyzer(window=5)
>>> result = analyzer.analyze(df, target_column="SPY")
"""

from typing import Any, Literal, cast

import numpy as np
import pandas as pd

from utils_core.logging import get_logger

from .base import StatisticalAnalyzer

logger = get_logger(__name__)


class RollingBetaAnalyzer(StatisticalAnalyzer):
    """Analyzer for calculating rolling beta coefficients.

    This class inherits from StatisticalAnalyzer and provides functionality
    to calculate rolling beta coefficients between a target benchmark column
    and other asset columns in a DataFrame.

    Rolling beta measures the sensitivity of asset returns to benchmark returns
    over a rolling window, which is useful for understanding how the
    relationship between assets and benchmarks changes over time.

    Parameters
    ----------
    window : int, default=60
        Rolling window size in observations. Default is 60, representing
        approximately 60 trading days (about 3 months for daily data).
    freq : {"W", "M"}, default="M"
        Data frequency indicator. "W" for weekly, "M" for monthly.
        This is used for informational purposes and documentation.
    window_years : {3, 5}, default=3
        Window duration in years for reference. This is used for
        informational purposes and documentation.

    Attributes
    ----------
    window : int
        The rolling window size.
    freq : {"W", "M"}
        The data frequency indicator.
    window_years : {3, 5}
        The window duration in years.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
    ...     "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
    ... })
    >>> analyzer = RollingBetaAnalyzer(window=5)
    >>> result = analyzer.analyze(df, target_column="SPY")
    >>> result.columns.tolist()
    ['AAPL']
    """

    _window: int
    _freq: Literal["W", "M"]
    _window_years: Literal[3, 5]

    def __init__(
        self,
        window: int = 60,
        freq: Literal["W", "M"] = "M",
        window_years: Literal[3, 5] = 3,
    ) -> None:
        """Initialize RollingBetaAnalyzer.

        Parameters
        ----------
        window : int, default=60
            Rolling window size in observations.
        freq : {"W", "M"}, default="M"
            Data frequency indicator.
        window_years : {3, 5}, default=3
            Window duration in years for reference.

        Examples
        --------
        >>> analyzer = RollingBetaAnalyzer()
        >>> analyzer.window
        60
        >>> analyzer.freq
        'M'
        >>> analyzer.window_years
        3
        >>> analyzer = RollingBetaAnalyzer(window=120, freq="W", window_years=5)
        >>> analyzer.window
        120
        """
        self._window = window
        self._freq = freq
        self._window_years = window_years
        logger.debug(
            "RollingBetaAnalyzer initialized",
            window=window,
            freq=freq,
            window_years=window_years,
        )

    @property
    def window(self) -> int:
        """Return the rolling window size.

        Returns
        -------
        int
            The rolling window size in observations.
        """
        return self._window

    @property
    def freq(self) -> Literal["W", "M"]:
        """Return the data frequency indicator.

        Returns
        -------
        {"W", "M"}
            The data frequency indicator.
        """
        return self._freq

    @property
    def window_years(self) -> Literal[3, 5]:
        """Return the window duration in years.

        Returns
        -------
        {3, 5}
            The window duration in years.
        """
        return self._window_years

    def validate_input(self, df: pd.DataFrame) -> bool:
        """Validate the input DataFrame for rolling beta calculation.

        This method checks that the DataFrame meets the requirements for
        rolling beta calculation:
        - DataFrame is not empty
        - Has at least 2 numeric columns
        - Has enough rows for window size

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid for calculation, False otherwise.

        Examples
        --------
        >>> analyzer = RollingBetaAnalyzer(window=5)
        >>> df = pd.DataFrame({"A": [1, 2, 3, 4, 5, 6], "B": [2, 4, 6, 8, 10, 12]})
        >>> analyzer.validate_input(df)
        True
        >>> analyzer.validate_input(pd.DataFrame())
        False
        """
        logger.debug(
            "Validating input for rolling beta",
            rows=len(df) if not df.empty else 0,
            columns=list(df.columns) if not df.empty else [],
        )

        # Check if DataFrame is empty
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return False

        # Check for at least 2 numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) < 2:
            logger.warning(
                "Insufficient numeric columns for beta calculation",
                numeric_columns=len(numeric_cols),
            )
            return False

        # Check for sufficient rows
        if len(df) < self._window:
            logger.warning(
                "Insufficient rows for window size",
                rows=len(df),
                window=self._window,
            )
            return False

        logger.debug("Input validation passed")
        return True

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        """Calculate rolling beta with a target benchmark column.

        This method calculates the rolling beta coefficient between
        each numeric column in the DataFrame and the specified target column
        (benchmark).

        Beta is calculated as: Cov(asset, benchmark) / Var(benchmark)

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame with time series data. Each column represents
            a different asset or series. Values should be returns (not prices).
        **kwargs : Any
            Additional keyword arguments. Required:
            - target_column (str): The column name to use as benchmark
              for beta calculation.

        Returns
        -------
        pd.DataFrame
            DataFrame containing rolling beta values for each column
            against the target column. The target column is excluded from results.
            Earlier values will be NaN until window size is reached.

        Raises
        ------
        ValueError
            If target_column is not provided or not found in the DataFrame.

        Examples
        --------
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "AAPL": [0.02, 0.04, -0.02, 0.06, 0.02, 0.04, -0.02, 0.06, 0.02, 0.04],
        ...     "SPY": [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.03, 0.01, 0.02],
        ... })
        >>> analyzer = RollingBetaAnalyzer(window=5)
        >>> result = analyzer.calculate(df, target_column="SPY")
        >>> result["AAPL"].iloc[-1]  # Beta should be approximately 2.0
        2.0
        """
        target_column = kwargs.get("target_column")

        if target_column is None:
            msg = "target_column is required"
            logger.error(msg)
            raise ValueError(msg)

        if target_column not in df.columns:
            msg = f"target_column '{target_column}' not found in DataFrame"
            logger.error(msg, available_columns=list(df.columns))
            raise ValueError(msg)

        logger.info(
            "Calculating rolling beta",
            target_column=target_column,
            window=self._window,
            freq=self._freq,
            window_years=self._window_years,
            input_rows=len(df),
            input_columns=len(df.columns),
        )

        # Get target (benchmark) series
        benchmark = df[target_column]

        # Get numeric columns excluding target
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        other_cols = [col for col in numeric_cols if col != target_column]

        # Calculate rolling beta for each column
        result_data: dict[str, pd.Series] = {}
        for col in other_cols:
            asset = df[col]

            # Calculate rolling covariance and variance
            rolling_cov = cast(
                "pd.Series",
                asset.rolling(window=self._window).cov(benchmark),
            )
            rolling_var = cast(
                "pd.Series",
                benchmark.rolling(window=self._window).var(),
            )

            # Handle zero variance by replacing with NaN
            rolling_var = rolling_var.replace(0, np.nan)

            # Beta = Cov(asset, benchmark) / Var(benchmark)
            rolling_beta = cast("pd.Series", rolling_cov / rolling_var)
            result_data[col] = rolling_beta

            logger.debug(
                "Rolling beta calculated",
                column=col,
                target_column=target_column,
                valid_values=rolling_beta.notna().sum(),
            )

        result = pd.DataFrame(result_data, index=df.index)

        logger.info(
            "Rolling beta calculation completed",
            output_columns=list(result.columns),
            output_rows=len(result),
        )

        return result


__all__ = ["RollingBetaAnalyzer"]
