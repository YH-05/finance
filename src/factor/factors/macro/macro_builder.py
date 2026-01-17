"""Macro factor builder implementation.

This module provides the MacroFactorBuilder class that orchestrates
the construction of all macroeconomic factors with proper
orthogonalization ordering.
"""

import pandas as pd

from ...core.orthogonalization import Orthogonalizer
from ...utils.logging_config import get_logger
from .flight_to_quality import HY_SPREAD_SERIES, IG_SPREAD_SERIES, FlightToQualityFactor
from .inflation import INFLATION_SERIES, InflationFactor
from .interest_rate import TREASURY_YIELD_SERIES, InterestRateFactor

logger = get_logger(__name__)

# Factor names in the output DataFrame
FACTOR_NAMES = [
    "Factor_Market",
    "Factor_Level",
    "Factor_Slope",
    "Factor_Curvature",
    "Factor_FtoQ",
    "Factor_Inflation",
]


class MacroFactorBuilder:
    """Builder for constructing all macro factors with proper orthogonalization.

    This class orchestrates the construction of macro factors:
    1. Market factor (excess return, not orthogonalized)
    2. Interest rate factors (Level, Slope, Curvature) - orthogonalized against Market
    3. Flight-to-quality factor (FtoQ) - orthogonalized against Market + interest rate
    4. Inflation factor - orthogonalized against all previous factors

    Parameters
    ----------
    pca_components : int, default=3
        Number of PCA components for interest rate factors.
    min_samples : int, default=20
        Minimum number of samples for calculations.

    Examples
    --------
    >>> builder = MacroFactorBuilder()
    >>> data = {
    ...     'market_return': market_series,
    ...     'risk_free': rf_series,
    ...     'yields': yield_df,
    ...     'spreads': spread_df,
    ...     'inflation': inflation_df,
    ... }
    >>> factors = builder.build_all_factors(data)
    >>> factors.columns
    Index(['Factor_Market', 'Factor_Level', 'Factor_Slope',
           'Factor_Curvature', 'Factor_FtoQ', 'Factor_Inflation'], dtype='object')
    """

    def __init__(
        self,
        pca_components: int = 3,
        min_samples: int = 20,
    ) -> None:
        """Initialize MacroFactorBuilder.

        Parameters
        ----------
        pca_components : int, default=3
            Number of PCA components for interest rate factors.
        min_samples : int, default=20
            Minimum number of samples for calculations.
        """
        self.pca_components = pca_components
        self.min_samples = min_samples

        # Initialize individual factor calculators
        self._interest_rate_factor = InterestRateFactor(
            n_components=pca_components,
            min_samples=min_samples,
        )
        self._ftoq_factor = FlightToQualityFactor(min_samples=min_samples)
        self._inflation_factor = InflationFactor(min_samples=min_samples)
        self._orthogonalizer = Orthogonalizer(min_samples=min_samples)

        logger.debug(
            "MacroFactorBuilder initialized",
            pca_components=pca_components,
            min_samples=min_samples,
        )

    def build_all_factors(
        self,
        data: dict[str, pd.DataFrame | pd.Series],
    ) -> pd.DataFrame:
        """Build all macro factors from input data.

        Constructs all macro factors with proper orthogonalization order:
        1. Market factor (from market return - risk free)
        2. Interest rate factors (orthogonalized against Market)
        3. FtoQ factor (orthogonalized against Market + interest rate)
        4. Inflation factor (orthogonalized against all previous)

        Parameters
        ----------
        data : dict[str, pd.DataFrame | pd.Series]
            Input data dictionary containing:
            - 'market_return': pd.Series with market returns
            - 'risk_free': pd.Series with risk-free rate
            - 'yields': pd.DataFrame with Treasury yield series
            - 'spreads': pd.DataFrame with HY/IG spread series
            - 'inflation': pd.DataFrame with T10YIE series

        Returns
        -------
        pd.DataFrame
            DataFrame with all macro factors:
            - Factor_Market: Market excess return
            - Factor_Level: Interest rate level (orthogonalized)
            - Factor_Slope: Interest rate slope (orthogonalized)
            - Factor_Curvature: Interest rate curvature (orthogonalized)
            - Factor_FtoQ: Flight-to-quality (orthogonalized)
            - Factor_Inflation: Inflation expectations (orthogonalized)

        Raises
        ------
        KeyError
            If required data is missing from input dictionary.
        ValueError
            If data validation fails.

        Examples
        --------
        >>> builder = MacroFactorBuilder()
        >>> factors = builder.build_all_factors(data)
        >>> factors.shape
        (252, 6)
        """
        logger.info("Building all macro factors")

        # Validate input data
        self._validate_input_data(data)

        # 1. Calculate market factor (not orthogonalized)
        market_factor = self._calculate_market_factor(data)

        # 2. Calculate interest rate factors (orthogonalized against market)
        # Note: _validate_input_data ensures these are DataFrames
        yields_df: pd.DataFrame = data["yields"]  # type: ignore[assignment]
        interest_rate_factors = self._interest_rate_factor.calculate(
            yields_df,
            market_factor=market_factor,
        )

        # 3. Calculate FtoQ factor (orthogonalized against market + interest rate)
        control_for_ftoq = pd.DataFrame(
            {
                "Factor_Market": market_factor,
                "Level": interest_rate_factors["Level"],
                "Slope": interest_rate_factors["Slope"],
                "Curvature": interest_rate_factors["Curvature"],
            }
        )
        spreads_df: pd.DataFrame = data["spreads"]  # type: ignore[assignment]
        ftoq_result = self._ftoq_factor.calculate(
            spreads_df,
            control_factors=control_for_ftoq,
        )

        # 4. Calculate inflation factor (orthogonalized against all previous)
        control_for_inflation = control_for_ftoq.copy()
        control_for_inflation["FtoQ"] = ftoq_result["FtoQ"]
        inflation_df: pd.DataFrame = data["inflation"]  # type: ignore[assignment]
        inflation_result = self._inflation_factor.calculate(
            inflation_df,
            control_factors=control_for_inflation,
        )

        # Combine all factors into single DataFrame
        result = self._combine_factors(
            market_factor,
            interest_rate_factors,
            ftoq_result,
            inflation_result,
        )

        logger.info(
            "All macro factors built",
            output_shape=result.shape,
            columns=list(result.columns),
        )

        return result

    def _validate_input_data(
        self,
        data: dict[str, pd.DataFrame | pd.Series],
    ) -> None:
        """Validate that all required data is present.

        Parameters
        ----------
        data : dict[str, pd.DataFrame | pd.Series]
            Input data dictionary.

        Raises
        ------
        KeyError
            If required data keys are missing.
        ValueError
            If data format is invalid.
        """
        required_keys = ["market_return", "risk_free", "yields", "spreads", "inflation"]
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            msg = f"Missing required data keys: {missing_keys}"
            logger.error(msg, missing_keys=missing_keys)
            raise KeyError(msg)

        # Validate yields DataFrame has required columns
        yields = data["yields"]
        if not isinstance(yields, pd.DataFrame):
            raise ValueError("'yields' must be a DataFrame")

        # Validate spreads DataFrame has required columns
        spreads = data["spreads"]
        if not isinstance(spreads, pd.DataFrame):
            raise ValueError("'spreads' must be a DataFrame")

        spread_missing = [
            s for s in [HY_SPREAD_SERIES, IG_SPREAD_SERIES] if s not in spreads.columns
        ]
        if spread_missing:
            raise KeyError(f"Missing spread series in 'spreads': {spread_missing}")

        # Validate inflation DataFrame has required column
        inflation = data["inflation"]
        if not isinstance(inflation, pd.DataFrame):
            raise ValueError("'inflation' must be a DataFrame")

        if INFLATION_SERIES not in inflation.columns:
            raise KeyError(f"Missing {INFLATION_SERIES} in 'inflation'")

        logger.debug("Input data validation passed")

    def _calculate_market_factor(
        self,
        data: dict[str, pd.DataFrame | pd.Series],
    ) -> pd.Series:
        """Calculate market factor as excess return.

        Parameters
        ----------
        data : dict[str, pd.DataFrame | pd.Series]
            Input data dictionary.

        Returns
        -------
        pd.Series
            Market excess return series.
        """
        market_return = data["market_return"]
        risk_free = data["risk_free"]

        # Calculate excess return
        excess_return = market_return - risk_free
        excess_return.name = "Factor_Market"

        logger.debug(
            "Market factor calculated",
            data_points=len(excess_return),
        )

        return excess_return

    def _combine_factors(
        self,
        market_factor: pd.Series,
        interest_rate_factors: pd.DataFrame,
        ftoq_result: pd.DataFrame,
        inflation_result: pd.DataFrame,
    ) -> pd.DataFrame:
        """Combine all individual factors into a single DataFrame.

        Parameters
        ----------
        market_factor : pd.Series
            Market excess return factor.
        interest_rate_factors : pd.DataFrame
            Interest rate factors (Level, Slope, Curvature).
        ftoq_result : pd.DataFrame
            Flight-to-quality factor.
        inflation_result : pd.DataFrame
            Inflation factor.

        Returns
        -------
        pd.DataFrame
            Combined factor DataFrame with standardized column names.
        """
        # Create result DataFrame with standardized column names
        result = pd.DataFrame(
            {
                "Factor_Market": market_factor,
                "Factor_Level": interest_rate_factors["Level"],
                "Factor_Slope": interest_rate_factors["Slope"],
                "Factor_Curvature": interest_rate_factors["Curvature"],
                "Factor_FtoQ": ftoq_result["FtoQ"],
                "Factor_Inflation": inflation_result["Inflation"],
            }
        )

        return result

    def get_factor_names(self) -> list[str]:
        """Get the list of factor names produced by this builder.

        Returns
        -------
        list[str]
            List of factor names.
        """
        return FACTOR_NAMES.copy()

    def get_required_series(self) -> list[str]:
        """Get all required FRED series IDs.

        Returns
        -------
        list[str]
            Combined list of all required FRED series.
        """
        series = []

        # Treasury yields
        series.extend(TREASURY_YIELD_SERIES)

        # Credit spreads
        series.extend([HY_SPREAD_SERIES, IG_SPREAD_SERIES])

        # Inflation
        series.append(INFLATION_SERIES)

        return series


__all__ = ["FACTOR_NAMES", "MacroFactorBuilder"]
