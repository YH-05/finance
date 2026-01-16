"""Orthogonalization algorithms for factor analysis.

This module provides methods to orthogonalize factors by removing
correlations with other factors using OLS regression residuals.
"""

from typing import Any

import pandas as pd

from ..errors import InsufficientDataError, OrthogonalizationError
from ..types import OrthogonalizationResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Lazy import for statsmodels to avoid heavy import cost
_sm: Any = None


def _get_statsmodels() -> Any:
    """Lazy import of statsmodels."""
    global _sm
    if _sm is None:
        import statsmodels.api as sm

        _sm = sm
    return _sm


class Orthogonalizer:
    """Orthogonalize factors using OLS regression residuals.

    This class provides methods to remove correlations between factors
    by regressing one factor against control factors and using the
    residuals as the orthogonalized factor.

    Parameters
    ----------
    min_samples : int, default=20
        Minimum number of samples required for regression

    Examples
    --------
    >>> orthogonalizer = Orthogonalizer()
    >>> result = orthogonalizer.orthogonalize(
    ...     factor_to_clean=momentum,
    ...     control_factors=market_factor
    ... )
    >>> orthogonalized_momentum = result.orthogonalized_data
    """

    def __init__(self, min_samples: int = 20) -> None:
        """Initialize Orthogonalizer.

        Parameters
        ----------
        min_samples : int, default=20
            Minimum number of samples for OLS regression
        """
        self.min_samples = min_samples
        logger.debug("Orthogonalizer initialized", min_samples=min_samples)

    def orthogonalize(
        self,
        factor_to_clean: pd.Series,
        control_factors: pd.Series | pd.DataFrame,
        *,
        add_constant: bool = True,
    ) -> OrthogonalizationResult:
        """Orthogonalize a factor against control factors using OLS.

        Regresses factor_to_clean on control_factors and returns
        the residuals as the orthogonalized factor.

        Parameters
        ----------
        factor_to_clean : pd.Series
            The factor to orthogonalize
        control_factors : pd.Series | pd.DataFrame
            One or more control factors to regress against
        add_constant : bool, default=True
            Whether to add a constant (intercept) to the regression

        Returns
        -------
        OrthogonalizationResult
            Result containing orthogonalized data and regression statistics

        Raises
        ------
        InsufficientDataError
            If fewer than min_samples valid observations exist
        OrthogonalizationError
            If the regression fails (e.g., singular matrix)

        Examples
        --------
        >>> orthogonalizer = Orthogonalizer()
        >>> momentum = pd.Series([0.1, 0.2, 0.15, 0.3], name="momentum")
        >>> market = pd.Series([0.05, 0.1, 0.08, 0.15], name="market")
        >>> result = orthogonalizer.orthogonalize(momentum, market)
        >>> result.r_squared  # Proportion of variance explained
        0.85
        """
        sm = _get_statsmodels()

        logger.debug(
            "Orthogonalizing factor",
            factor_name=factor_to_clean.name,
            control_count=1
            if isinstance(control_factors, pd.Series)
            else control_factors.shape[1],
        )

        # Combine data and drop NaN rows
        data = pd.concat([factor_to_clean, control_factors], axis=1).dropna()

        if len(data) < self.min_samples:
            raise InsufficientDataError(
                f"Insufficient data for orthogonalization: {len(data)} < {self.min_samples}",
                required=self.min_samples,
                available=len(data),
                factor_name=str(factor_to_clean.name),
            )

        # Split into dependent and independent variables
        Y = data.iloc[:, 0]
        X = data.iloc[:, 1:]

        if add_constant:
            X = sm.add_constant(X, has_constant="add")

        # Run OLS regression
        try:
            model = sm.OLS(Y, X).fit()
        except Exception as e:
            raise OrthogonalizationError(
                f"OLS regression failed: {e}",
                factor_name=str(factor_to_clean.name),
                control_factors=list(control_factors.columns)
                if isinstance(control_factors, pd.DataFrame)
                else [str(control_factors.name)],
                method="ols",
                cause=e,
            ) from e

        # Get residuals (orthogonalized series)
        residuals = pd.Series(model.resid, index=Y.index, name=factor_to_clean.name)

        # Get control factor names
        control_names = (
            list(control_factors.columns)
            if isinstance(control_factors, pd.DataFrame)
            else [str(control_factors.name)]
        )

        result = OrthogonalizationResult(
            original_factor=str(factor_to_clean.name or "unnamed"),
            orthogonalized_data=pd.DataFrame(residuals),
            control_factors=control_names,
            method="ols",
            r_squared=float(model.rsquared),
            residual_std=float(residuals.std()),
        )

        logger.info(
            "Orthogonalization completed",
            factor=result.original_factor,
            r_squared=f"{result.r_squared:.4f}",
            observations=len(data),
        )

        return result

    def orthogonalize_cascade(
        self,
        factors: dict[str, pd.Series],
        order: list[str],
    ) -> dict[str, OrthogonalizationResult]:
        """Perform sequential (cascade) orthogonalization.

        Orthogonalizes factors in sequence, where each factor is
        orthogonalized against all previous factors in the order.

        Parameters
        ----------
        factors : dict[str, pd.Series]
            Dictionary mapping factor names to their values
        order : list[str]
            Order in which to orthogonalize factors.
            The first factor is kept as-is, subsequent factors
            are orthogonalized against all preceding ones.

        Returns
        -------
        dict[str, OrthogonalizationResult]
            Dictionary mapping factor names to their orthogonalization results.
            The first factor has r_squared=0 and residual_std=1.

        Raises
        ------
        ValueError
            If order contains factor names not in factors dict

        Examples
        --------
        >>> orthogonalizer = Orthogonalizer()
        >>> factors = {
        ...     "market": market_series,
        ...     "level": level_series,
        ...     "slope": slope_series,
        ... }
        >>> order = ["market", "level", "slope"]
        >>> results = orthogonalizer.orthogonalize_cascade(factors, order)
        >>> # "level" is orthogonalized against "market"
        >>> # "slope" is orthogonalized against "market" and "level"
        """
        # Validate that all factors in order exist
        missing = [f for f in order if f not in factors]
        if missing:
            raise ValueError(f"Factors not found in dict: {missing}")

        logger.debug(
            "Starting cascade orthogonalization",
            factor_count=len(order),
            order=order,
        )

        results: dict[str, OrthogonalizationResult] = {}
        orthogonalized: dict[str, pd.Series] = {}

        for i, factor_name in enumerate(order):
            factor_series = factors[factor_name]

            if i == 0:
                # First factor is kept as-is
                orthogonalized[factor_name] = factor_series
                results[factor_name] = OrthogonalizationResult(
                    original_factor=factor_name,
                    orthogonalized_data=pd.DataFrame(factor_series),
                    control_factors=[],
                    method="none",
                    r_squared=0.0,
                    residual_std=float(factor_series.std()),
                )
                logger.debug(f"First factor '{factor_name}' kept as-is")
            else:
                # Get all preceding factors (already orthogonalized)
                control_names = order[:i]
                control_data = pd.DataFrame(
                    {name: orthogonalized[name] for name in control_names}
                )

                # Orthogonalize against all preceding factors
                result = self.orthogonalize(factor_series, control_data)
                result.control_factors = control_names

                # Store orthogonalized series for next iterations
                orthogonalized[factor_name] = result.orthogonalized_data.iloc[:, 0]
                results[factor_name] = result

                logger.debug(
                    f"Factor '{factor_name}' orthogonalized",
                    controls=control_names,
                    r_squared=f"{result.r_squared:.4f}",
                )

        logger.info(
            "Cascade orthogonalization completed",
            factors_processed=len(order),
        )

        return results


__all__ = ["Orthogonalizer"]
