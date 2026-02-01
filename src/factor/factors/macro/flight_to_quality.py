"""Flight-to-quality factor implementation.

This module provides the FlightToQualityFactor class that calculates
a flight-to-quality factor based on the spread between High Yield
and Investment Grade corporate bond spreads.
"""

import pandas as pd
from utils_core.logging import get_logger

from ...core.orthogonalization import Orthogonalizer
from ...errors import InsufficientDataError
from .base import BaseMacroFactor

logger = get_logger(__name__)

# FRED credit spread series IDs
HY_SPREAD_SERIES = "BAMLH0A0HYM2"  # ICE BofA US High Yield OAS
IG_SPREAD_SERIES = "BAMLC0A0CM"  # ICE BofA US Corporate (IG) OAS


class FlightToQualityFactor(BaseMacroFactor):
    """Flight-to-quality factor based on HY-IG spread.

    Calculates a flight-to-quality factor from the difference between
    High Yield and Investment Grade corporate bond spreads. When
    investors flee to quality:
    - HY spreads widen significantly
    - IG spreads widen less
    - HY-IG spread increases
    - This corresponds to a positive FtoQ factor

    The factor is calculated as:
    1. FtoQ = HY_Spread - IG_Spread (HY-IG spread)
    2. FtoQ_Shock = diff(FtoQ) (change in spread)
    3. Factor_FtoQ = orthogonalize(FtoQ_Shock, control_factors)

    Parameters
    ----------
    min_samples : int, default=20
        Minimum number of samples required for orthogonalization.

    Examples
    --------
    >>> factor = FlightToQualityFactor()
    >>> result = factor.calculate(spread_data)
    >>> result.columns
    Index(['FtoQ'], dtype='object')
    """

    def __init__(self, min_samples: int = 20) -> None:
        """Initialize FlightToQualityFactor.

        Parameters
        ----------
        min_samples : int, default=20
            Minimum number of samples for calculations.
        """
        self.min_samples = min_samples
        self._orthogonalizer = Orthogonalizer(min_samples=min_samples)
        logger.debug(
            "FlightToQualityFactor initialized",
            min_samples=min_samples,
        )

    @property
    def name(self) -> str:
        """Return the factor name.

        Returns
        -------
        str
            'FlightToQuality'
        """
        return "FlightToQuality"

    @property
    def required_series(self) -> list[str]:
        """Return the list of required FRED credit spread series.

        Returns
        -------
        list[str]
            List containing HY and IG spread series IDs.
        """
        return [HY_SPREAD_SERIES, IG_SPREAD_SERIES]

    def calculate(
        self,
        data: pd.DataFrame,
        control_factors: pd.DataFrame | None = None,
        **kwargs: pd.Series | pd.DataFrame | None,
    ) -> pd.DataFrame:
        """Calculate flight-to-quality factor from spread data.

        Computes the FtoQ factor as the change in HY-IG spread,
        optionally orthogonalized against control factors
        (Market, Level, Slope, Curvature).

        Parameters
        ----------
        data : pd.DataFrame
            Credit spread data with HY and IG spread columns.
            Index should be DatetimeIndex.
            Must contain BAMLH0A0HYM2 and BAMLC0A0CM columns.
        control_factors : pd.DataFrame | None, default=None
            Control factors for orthogonalization.
            Expected columns: Factor_Market, Level, Slope, Curvature.
            If provided, FtoQ will be orthogonalized against these.
        **kwargs : pd.Series | pd.DataFrame | None
            Additional keyword arguments (unused).

        Returns
        -------
        pd.DataFrame
            DataFrame with column ['FtoQ'] containing the
            orthogonalized (if control_factors provided) factor.

        Raises
        ------
        KeyError
            If required spread series are missing from data.
        ValueError
            If data validation fails.

        Examples
        --------
        >>> factor = FlightToQualityFactor()
        >>> spread_data = pd.DataFrame({
        ...     'BAMLH0A0HYM2': [4.5, 4.6, 4.4],
        ...     'BAMLC0A0CM': [1.5, 1.55, 1.45],
        ... }, index=pd.date_range('2020-01-01', periods=3))
        >>> result = factor.calculate(spread_data)
        """
        logger.debug(
            "Calculating flight-to-quality factor",
            data_shape=data.shape,
            has_control_factors=control_factors is not None,
        )

        # Validate required columns
        missing = [s for s in self.required_series if s not in data.columns]
        if missing:
            msg = f"Missing required series: {missing}"
            logger.error(msg, missing_series=missing)
            raise KeyError(msg)

        # Calculate HY-IG spread
        hy_spread = data[HY_SPREAD_SERIES]
        ig_spread = data[IG_SPREAD_SERIES]
        ftoq_spread = hy_spread - ig_spread

        # Calculate shock (change)
        ftoq_shock = ftoq_spread.diff()
        ftoq_shock.name = "FtoQ"

        # Drop NaN from diff
        ftoq_shock = ftoq_shock.dropna()

        if len(ftoq_shock) < self.min_samples:
            raise InsufficientDataError(
                f"Insufficient data after differencing: {len(ftoq_shock)} < {self.min_samples}",
                required=self.min_samples,
                available=len(ftoq_shock),
                factor_name=self.name,
            )

        # Orthogonalize if control factors provided
        if control_factors is not None:
            ftoq_factor = self._orthogonalize(ftoq_shock, control_factors)
        else:
            ftoq_factor = ftoq_shock

        result = pd.DataFrame({"FtoQ": ftoq_factor})

        logger.info(
            "Flight-to-quality factor calculated",
            output_shape=result.shape,
        )

        return result

    def _orthogonalize(
        self,
        ftoq_shock: pd.Series,
        control_factors: pd.DataFrame,
    ) -> pd.Series:
        """Orthogonalize FtoQ shock against control factors.

        Parameters
        ----------
        ftoq_shock : pd.Series
            The raw FtoQ shock series.
        control_factors : pd.DataFrame
            The control factors to orthogonalize against.

        Returns
        -------
        pd.Series
            Orthogonalized FtoQ factor.
        """
        logger.debug(
            "Orthogonalizing FtoQ against control factors",
            control_columns=list(control_factors.columns),
        )

        try:
            ortho_result = self._orthogonalizer.orthogonalize(
                ftoq_shock,
                control_factors,
            )
            result = ortho_result.orthogonalized_data.iloc[:, 0]
            result.name = "FtoQ"
            return result
        except Exception as e:
            logger.warning(
                "Failed to orthogonalize FtoQ, using raw values",
                error=str(e),
            )
            return ftoq_shock


__all__ = ["HY_SPREAD_SERIES", "IG_SPREAD_SERIES", "FlightToQualityFactor"]
