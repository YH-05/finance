"""Interest rate factor implementation.

This module provides the InterestRateFactor class that calculates
Level, Slope, and Curvature factors from yield curve data using PCA.
"""

from typing import cast

import pandas as pd

from ...core.orthogonalization import Orthogonalizer
from ...core.pca import YieldCurvePCA
from ...errors import InsufficientDataError
from ...utils.logging_config import get_logger
from .base import BaseMacroFactor

logger = get_logger(__name__)

# FRED Treasury yield series IDs (from shortest to longest maturity)
TREASURY_YIELD_SERIES = [
    "DGS1MO",  # 1 Month
    "DGS3MO",  # 3 Month
    "DGS6MO",  # 6 Month
    "DGS1",  # 1 Year
    "DGS2",  # 2 Year
    "DGS3",  # 3 Year
    "DGS5",  # 5 Year
    "DGS7",  # 7 Year
    "DGS10",  # 10 Year
    "DGS20",  # 20 Year
    "DGS30",  # 30 Year
]


class InterestRateFactor(BaseMacroFactor):
    """Interest rate factor using yield curve PCA.

    Calculates three factors from yield curve data:
    - Level: Overall level of interest rates (PC1)
    - Slope: Steepness of the yield curve (PC2)
    - Curvature: Curvature/butterfly of the yield curve (PC3)

    These factors are calculated using PCA on yield changes and
    optionally orthogonalized against a market factor.

    Parameters
    ----------
    n_components : int, default=3
        Number of principal components to extract.
        Typically 3 for Level, Slope, Curvature.
    min_samples : int, default=20
        Minimum number of samples required for PCA and orthogonalization.

    Examples
    --------
    >>> factor = InterestRateFactor()
    >>> result = factor.calculate(yield_data)
    >>> result.columns
    Index(['Level', 'Slope', 'Curvature'], dtype='object')
    """

    def __init__(
        self,
        n_components: int = 3,
        min_samples: int = 20,
    ) -> None:
        """Initialize InterestRateFactor.

        Parameters
        ----------
        n_components : int, default=3
            Number of principal components to extract.
        min_samples : int, default=20
            Minimum number of samples for calculations.
        """
        self.n_components = n_components
        self.min_samples = min_samples
        self._pca = YieldCurvePCA(n_components=n_components)
        self._orthogonalizer = Orthogonalizer(min_samples=min_samples)
        logger.debug(
            "InterestRateFactor initialized",
            n_components=n_components,
            min_samples=min_samples,
        )

    @property
    def name(self) -> str:
        """Return the factor name.

        Returns
        -------
        str
            'InterestRate'
        """
        return "InterestRate"

    @property
    def required_series(self) -> list[str]:
        """Return the list of required FRED Treasury yield series.

        Returns
        -------
        list[str]
            List of FRED Treasury yield series IDs from DGS1MO to DGS30.
        """
        return TREASURY_YIELD_SERIES.copy()

    def calculate(
        self,
        data: pd.DataFrame,
        market_factor: pd.Series | None = None,
        **kwargs: pd.Series | pd.DataFrame | None,
    ) -> pd.DataFrame:
        """Calculate Level, Slope, and Curvature factors from yield data.

        Performs PCA on yield changes to extract the three main factors
        explaining yield curve movements. Optionally orthogonalizes
        against a market factor.

        Parameters
        ----------
        data : pd.DataFrame
            Yield curve data with Treasury series as columns.
            Index should be DatetimeIndex.
            Columns should include at least some of the required series.
        market_factor : pd.Series | None, default=None
            Market factor series for orthogonalization.
            If provided, the interest rate factors will be orthogonalized
            against this market factor.
        **kwargs : pd.Series | pd.DataFrame | None
            Additional keyword arguments (unused).

        Returns
        -------
        pd.DataFrame
            DataFrame with columns ['Level', 'Slope', 'Curvature']
            containing the orthogonalized (if market_factor provided)
            interest rate factors.

        Raises
        ------
        InsufficientDataError
            If data has fewer rows than required for PCA.
        KeyError
            If required yield series are missing from data.

        Examples
        --------
        >>> factor = InterestRateFactor()
        >>> yield_data = pd.DataFrame(...)  # with DGS columns
        >>> result = factor.calculate(yield_data)
        >>> result.columns
        Index(['Level', 'Slope', 'Curvature'], dtype='object')
        """
        logger.debug(
            "Calculating interest rate factors",
            data_shape=data.shape,
            has_market_factor=market_factor is not None,
        )

        # Extract available yield columns (in maturity order)
        available_series = [s for s in TREASURY_YIELD_SERIES if s in data.columns]
        if len(available_series) < self.n_components:
            msg = (
                f"Insufficient yield series: need at least {self.n_components}, "
                f"got {len(available_series)}"
            )
            raise InsufficientDataError(
                msg,
                required=self.n_components,
                available=len(available_series),
                factor_name=self.name,
            )

        yield_data = cast(pd.DataFrame, data[available_series])

        # Perform PCA on yield changes
        try:
            pca_result = self._pca.fit_transform(
                yield_data,
                use_changes=True,
                align_signs=True,
            )
        except InsufficientDataError:
            raise
        except Exception as e:
            logger.error("PCA failed", error=str(e), exc_info=True)
            raise InsufficientDataError(
                f"Failed to perform PCA on yield data: {e}",
                required=self.n_components,
                available=len(yield_data),
                factor_name=self.name,
            ) from e

        # Get the PCA scores (Level, Slope, Curvature)
        result = pca_result.scores.copy()

        # Orthogonalize against market factor if provided
        if market_factor is not None:
            result = self._orthogonalize_factors(result, market_factor)

        logger.info(
            "Interest rate factors calculated",
            output_shape=result.shape,
            columns=list(result.columns),
        )

        return result

    def _orthogonalize_factors(
        self,
        factors: pd.DataFrame,
        market_factor: pd.Series,
    ) -> pd.DataFrame:
        """Orthogonalize interest rate factors against market factor.

        Parameters
        ----------
        factors : pd.DataFrame
            The raw PCA factors (Level, Slope, Curvature).
        market_factor : pd.Series
            The market factor to orthogonalize against.

        Returns
        -------
        pd.DataFrame
            Orthogonalized factors.
        """
        logger.debug("Orthogonalizing interest rate factors against market")

        result_data: dict[str, pd.Series] = {}
        for col in factors.columns:
            factor_series = cast(pd.Series, factors[col])
            factor_series.name = col

            try:
                ortho_result = self._orthogonalizer.orthogonalize(
                    factor_series,
                    market_factor,
                )
                result_data[col] = ortho_result.orthogonalized_data.iloc[:, 0]
            except Exception as e:
                logger.warning(
                    f"Failed to orthogonalize {col}, using raw values",
                    error=str(e),
                )
                result_data[col] = factor_series

        result = pd.DataFrame(result_data)
        return result


__all__ = ["InterestRateFactor", "TREASURY_YIELD_SERIES"]
