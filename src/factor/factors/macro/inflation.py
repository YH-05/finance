"""Inflation factor implementation.

This module provides the InflationFactor class that calculates
an inflation expectations factor based on the 10-Year Breakeven
Inflation Rate (T10YIE).
"""

from typing import cast

import pandas as pd
from utils_core.logging import get_logger

from ...core.orthogonalization import Orthogonalizer
from ...errors import InsufficientDataError
from .base import BaseMacroFactor

logger = get_logger(__name__)

# FRED inflation expectation series ID
INFLATION_SERIES = "T10YIE"  # 10-Year Breakeven Inflation Rate


class InflationFactor(BaseMacroFactor):
    """Inflation expectations factor based on 10-Year Breakeven.

    Calculates an inflation factor from the 10-Year Breakeven
    Inflation Rate (T10YIE). When inflation expectations rise:
    - T10YIE increases
    - This corresponds to a positive Inflation factor

    The factor is calculated as:
    1. Inflation_Shock = diff(T10YIE) (change in inflation expectations)
    2. Factor_Inflation = orthogonalize(Inflation_Shock, control_factors)

    The inflation factor is orthogonalized against all previous factors
    in the factor model (Market, Level, Slope, Curvature, FtoQ).

    Parameters
    ----------
    min_samples : int, default=20
        Minimum number of samples required for orthogonalization.

    Examples
    --------
    >>> factor = InflationFactor()
    >>> result = factor.calculate(inflation_data)
    >>> result.columns
    Index(['Inflation'], dtype='object')
    """

    def __init__(self, min_samples: int = 20) -> None:
        """Initialize InflationFactor.

        Parameters
        ----------
        min_samples : int, default=20
            Minimum number of samples for calculations.
        """
        self.min_samples = min_samples
        self._orthogonalizer = Orthogonalizer(min_samples=min_samples)
        logger.debug(
            "InflationFactor initialized",
            min_samples=min_samples,
        )

    @property
    def name(self) -> str:
        """Return the factor name.

        Returns
        -------
        str
            'Inflation'
        """
        return "Inflation"

    @property
    def required_series(self) -> list[str]:
        """Return the list of required FRED inflation series.

        Returns
        -------
        list[str]
            List containing the 10-Year Breakeven Inflation Rate series ID.
        """
        return [INFLATION_SERIES]

    def calculate(
        self,
        data: pd.DataFrame,
        control_factors: pd.DataFrame | None = None,
        **kwargs: pd.Series | pd.DataFrame | None,
    ) -> pd.DataFrame:
        """Calculate inflation factor from T10YIE data.

        Computes the Inflation factor as the change in 10-Year
        Breakeven Inflation Rate, optionally orthogonalized against
        control factors (Market, Level, Slope, Curvature, FtoQ).

        Parameters
        ----------
        data : pd.DataFrame
            Inflation expectation data with T10YIE column.
            Index should be DatetimeIndex.
            Must contain T10YIE column.
        control_factors : pd.DataFrame | None, default=None
            Control factors for orthogonalization.
            Expected columns: Factor_Market, Level, Slope, Curvature, FtoQ.
            If provided, Inflation will be orthogonalized against these.
        **kwargs : pd.Series | pd.DataFrame | None
            Additional keyword arguments (unused).

        Returns
        -------
        pd.DataFrame
            DataFrame with column ['Inflation'] containing the
            orthogonalized (if control_factors provided) factor.

        Raises
        ------
        KeyError
            If T10YIE series is missing from data.
        ValueError
            If data validation fails.

        Examples
        --------
        >>> factor = InflationFactor()
        >>> inflation_data = pd.DataFrame({
        ...     'T10YIE': [2.2, 2.25, 2.18],
        ... }, index=pd.date_range('2020-01-01', periods=3))
        >>> result = factor.calculate(inflation_data)
        """
        logger.debug(
            "Calculating inflation factor",
            data_shape=data.shape,
            has_control_factors=control_factors is not None,
        )

        # Validate required column
        if INFLATION_SERIES not in data.columns:
            msg = f"Missing required series: {INFLATION_SERIES}"
            logger.error(msg)
            raise KeyError(msg)

        # Get inflation expectation data
        inflation_data = cast("pd.Series", data[INFLATION_SERIES])

        # Calculate shock (change)
        inflation_shock = inflation_data.diff()
        inflation_shock.name = "Inflation"

        # Drop NaN from diff
        inflation_shock = inflation_shock.dropna()

        if len(inflation_shock) < self.min_samples:
            raise InsufficientDataError(
                f"Insufficient data after differencing: {len(inflation_shock)} < {self.min_samples}",
                required=self.min_samples,
                available=len(inflation_shock),
                factor_name=self.name,
            )

        # Orthogonalize if control factors provided
        if control_factors is not None:
            inflation_factor = self._orthogonalize(inflation_shock, control_factors)
        else:
            inflation_factor = inflation_shock

        result = pd.DataFrame({"Inflation": inflation_factor})

        logger.info(
            "Inflation factor calculated",
            output_shape=result.shape,
        )

        return result

    def _orthogonalize(
        self,
        inflation_shock: pd.Series,
        control_factors: pd.DataFrame,
    ) -> pd.Series:
        """Orthogonalize inflation shock against control factors.

        Parameters
        ----------
        inflation_shock : pd.Series
            The raw inflation shock series.
        control_factors : pd.DataFrame
            The control factors to orthogonalize against.

        Returns
        -------
        pd.Series
            Orthogonalized inflation factor.
        """
        logger.debug(
            "Orthogonalizing Inflation against control factors",
            control_columns=list(control_factors.columns),
        )

        try:
            ortho_result = self._orthogonalizer.orthogonalize(
                inflation_shock,
                control_factors,
            )
            result = ortho_result.orthogonalized_data.iloc[:, 0]
            result.name = "Inflation"
            return result
        except Exception as e:
            logger.warning(
                "Failed to orthogonalize Inflation, using raw values",
                error=str(e),
            )
            return inflation_shock


__all__ = ["INFLATION_SERIES", "InflationFactor"]
