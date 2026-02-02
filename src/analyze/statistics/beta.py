"""Beta analysis for statistical analysis.

This module provides beta analyzers for calculating beta coefficients
between assets and a benchmark using different methods.

Classes
-------
RollingBetaAnalyzer : Rolling beta analysis class inheriting from StatisticalAnalyzer
KalmanBetaAnalyzer : Kalman filter-based time-varying beta estimation

Examples
--------
>>> import pandas as pd
>>> from analyze.statistics.beta import RollingBetaAnalyzer, KalmanBetaAnalyzer
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


class KalmanBetaAnalyzer(StatisticalAnalyzer):
    """Analyzer for calculating time-varying beta using Kalman filter.

    This class inherits from StatisticalAnalyzer and provides functionality
    to estimate time-varying beta coefficients between a target benchmark column
    and other asset columns in a DataFrame using Kalman filtering.

    The Kalman filter approach treats beta as a latent state that evolves
    over time following a random walk process, which allows the model to
    capture the dynamic relationship between assets and benchmarks.

    State-space model:
    - Observation equation: r_asset,t = beta_t * r_market,t + epsilon_t
    - State equation: beta_t = beta_{t-1} + eta_t

    Parameters
    ----------
    transition_covariance : float, default=0.001
        The covariance of the state transition noise (Q matrix).
        Controls how much the beta is allowed to change between observations.
        Smaller values result in smoother beta estimates.
    em_iterations : int, default=10
        Number of EM algorithm iterations for parameter estimation.

    Attributes
    ----------
    transition_covariance : float
        The state transition covariance.
    em_iterations : int
        The number of EM iterations.

    Notes
    -----
    This analyzer requires the optional `pykalman` package. If not installed,
    an ImportError will be raised when calling calculate().

    Install with: ``pip install pykalman`` or ``uv add pykalman``

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> np.random.seed(42)
    >>> n = 50
    >>> market = np.random.randn(n) * 0.01
    >>> asset = 2.0 * market + np.random.randn(n) * 0.001
    >>> df = pd.DataFrame({"AAPL": asset, "SPY": market})
    >>> analyzer = KalmanBetaAnalyzer()
    >>> result = analyzer.analyze(df, target_column="SPY")
    >>> result.columns.tolist()
    ['AAPL']
    """

    _transition_covariance: float
    _em_iterations: int
    _min_observations: int = 10  # Minimum data points for Kalman filter

    def __init__(
        self,
        transition_covariance: float = 0.001,
        em_iterations: int = 10,
    ) -> None:
        """Initialize KalmanBetaAnalyzer.

        Parameters
        ----------
        transition_covariance : float, default=0.001
            The covariance of the state transition noise.
            Controls smoothness of beta estimates.
        em_iterations : int, default=10
            Number of EM algorithm iterations for parameter estimation.

        Examples
        --------
        >>> analyzer = KalmanBetaAnalyzer()
        >>> analyzer.transition_covariance
        0.001
        >>> analyzer.em_iterations
        10
        >>> analyzer = KalmanBetaAnalyzer(transition_covariance=0.01, em_iterations=20)
        >>> analyzer.transition_covariance
        0.01
        """
        self._transition_covariance = transition_covariance
        self._em_iterations = em_iterations
        logger.debug(
            "KalmanBetaAnalyzer initialized",
            transition_covariance=transition_covariance,
            em_iterations=em_iterations,
        )

    @property
    def transition_covariance(self) -> float:
        """Return the state transition covariance.

        Returns
        -------
        float
            The transition covariance value.
        """
        return self._transition_covariance

    @property
    def em_iterations(self) -> int:
        """Return the number of EM iterations.

        Returns
        -------
        int
            The number of EM algorithm iterations.
        """
        return self._em_iterations

    def validate_input(self, df: pd.DataFrame) -> bool:
        """Validate the input DataFrame for Kalman beta calculation.

        This method checks that the DataFrame meets the requirements for
        Kalman beta calculation:
        - DataFrame is not empty
        - Has at least 2 numeric columns
        - Has enough rows for Kalman filter (minimum 10 observations)

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
        >>> analyzer = KalmanBetaAnalyzer()
        >>> df = pd.DataFrame({"A": range(50), "B": range(50)})
        >>> analyzer.validate_input(df)
        True
        >>> analyzer.validate_input(pd.DataFrame())
        False
        """
        logger.debug(
            "Validating input for Kalman beta",
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

        # Check for minimum observations
        if len(df) < self._min_observations:
            logger.warning(
                "Insufficient rows for Kalman filter",
                rows=len(df),
                min_required=self._min_observations,
            )
            return False

        logger.debug("Input validation passed")
        return True

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        """Calculate time-varying beta using Kalman filter.

        This method estimates the time-varying beta coefficient between
        each numeric column in the DataFrame and the specified target column
        (benchmark) using a Kalman filter with random walk dynamics.

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
            DataFrame containing Kalman-filtered beta values for each column
            against the target column. The target column is excluded from results.

        Raises
        ------
        ValueError
            If target_column is not provided or not found in the DataFrame.
        ImportError
            If pykalman is not installed.

        Examples
        --------
        >>> import pandas as pd
        >>> import numpy as np
        >>> np.random.seed(42)
        >>> n = 50
        >>> market = np.random.randn(n) * 0.01
        >>> asset = 2.0 * market + np.random.randn(n) * 0.001
        >>> df = pd.DataFrame({"AAPL": asset, "SPY": market})
        >>> analyzer = KalmanBetaAnalyzer()
        >>> result = analyzer.calculate(df, target_column="SPY")
        >>> result["AAPL"].iloc[-1]  # Beta should be approximately 2.0
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
            "Calculating Kalman beta",
            target_column=target_column,
            transition_covariance=self._transition_covariance,
            em_iterations=self._em_iterations,
            input_rows=len(df),
            input_columns=len(df.columns),
        )

        # Import pykalman (optional dependency)
        try:
            from pykalman import KalmanFilter  # type: ignore[import-not-found]
        except ImportError as e:
            msg = (
                "pykalman is required for KalmanBetaAnalyzer. "
                "Install with: pip install pykalman"
            )
            logger.error(msg)
            raise ImportError(msg) from e

        # Get target (benchmark) series as numpy array
        benchmark = np.asarray(df[target_column].values, dtype=np.float64)

        # Get numeric columns excluding target
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        other_cols = [col for col in numeric_cols if col != target_column]

        # Calculate Kalman beta for each column
        result_data: dict[str, pd.Series] = {}
        for col in other_cols:
            # Convert to numpy array explicitly to avoid type issues
            asset = np.asarray(df[col].values, dtype=np.float64)

            # Use scipy.stats.linregress for initial beta estimate
            from scipy.stats import linregress

            slope_init, _, _, _, _ = linregress(benchmark, asset)

            # Set up observation matrices (time-varying)
            # Observation equation: y_t = beta_t * X_t + epsilon_t
            observation_matrices = benchmark.reshape(-1, 1, 1)

            # Calculate observation covariance from asset variance
            asset_variance = float(np.var(asset))

            # Initialize Kalman filter
            kf = KalmanFilter(
                transition_matrices=np.array([[1.0]]),  # Random walk
                observation_matrices=observation_matrices,
                transition_covariance=np.array([[self._transition_covariance]]),
                observation_covariance=np.array([[asset_variance]]),
                initial_state_mean=np.array([slope_init]),
                initial_state_covariance=np.array([[1.0]]),
                n_dim_state=1,
                n_dim_obs=1,
            )

            # Use EM algorithm to refine parameters
            kf = kf.em(asset.reshape(-1, 1), n_iter=self._em_iterations)

            # Apply Kalman filter
            state_means, _ = kf.filter(asset.reshape(-1, 1))

            # Store results as a Series with the original index
            result_data[col] = pd.Series(
                state_means.flatten(), index=df.index, name=col
            )

            logger.debug(
                "Kalman beta calculated",
                column=col,
                target_column=target_column,
                final_beta=float(state_means[-1, 0]),
            )

        result = pd.DataFrame(result_data, index=df.index)

        logger.info(
            "Kalman beta calculation completed",
            output_columns=list(result.columns),
            output_rows=len(result),
        )

        return result


__all__ = ["KalmanBetaAnalyzer", "RollingBetaAnalyzer"]
