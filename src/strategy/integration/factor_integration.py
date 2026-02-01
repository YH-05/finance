"""Factor package integration for strategy package.

This module provides integration between the factor package and
the strategy package's risk calculation functionality.

Classes
-------
FactorBasedRiskCalculator
    Risk calculator considering factor exposures

Functions
---------
create_factor_risk_calculator
    Factory function to create a FactorBasedRiskCalculator

Examples
--------
>>> from strategy.integration import create_factor_risk_calculator
>>> calculator = create_factor_risk_calculator()
>>> risk = calculator.calculate_risk(returns)
"""

from typing import Any

import numpy as np
import pandas as pd
from utils_core.logging import get_logger

logger = get_logger(__name__)


class FactorBasedRiskCalculator:
    """Risk calculator enhanced with factor analysis.

    This class combines traditional risk metrics with factor exposure
    analysis from the factor package.

    Examples
    --------
    >>> calculator = FactorBasedRiskCalculator()
    >>> risk = calculator.calculate_risk(returns)
    >>> "volatility" in risk
    True
    """

    def __init__(self, annualization_factor: int = 252) -> None:
        """Initialize FactorBasedRiskCalculator.

        Parameters
        ----------
        annualization_factor : int
            Factor for annualization (default: 252 for daily data)
        """
        logger.debug(
            "Initializing FactorBasedRiskCalculator",
            annualization_factor=annualization_factor,
        )
        self._annualization_factor = annualization_factor
        logger.info("FactorBasedRiskCalculator initialized")

    @property
    def annualization_factor(self) -> int:
        """Get the annualization factor.

        Returns
        -------
        int
            The annualization factor
        """
        return self._annualization_factor

    def calculate_risk(
        self,
        returns: pd.Series,
        include_factor_exposure: bool = True,
    ) -> dict[str, Any]:
        """Calculate comprehensive risk metrics.

        Parameters
        ----------
        returns : pd.Series
            Returns time series
        include_factor_exposure : bool
            Whether to include factor exposure analysis (default: True)

        Returns
        -------
        dict[str, Any]
            Dictionary containing risk metrics:
            - volatility: Annualized volatility
            - sharpe_ratio: Sharpe ratio (assuming 0 risk-free rate)
            - max_drawdown: Maximum drawdown
            - factor_exposure: Factor exposure dict (if include_factor_exposure)

        Examples
        --------
        >>> calculator = FactorBasedRiskCalculator()
        >>> risk = calculator.calculate_risk(returns)
        >>> risk["volatility"] >= 0
        True
        """
        logger.debug(
            "Calculating risk metrics",
            returns_length=len(returns),
            include_factor_exposure=include_factor_exposure,
        )

        if returns.empty:
            logger.warning("Empty returns series provided")
            return {
                "volatility": float("nan"),
                "sharpe_ratio": float("nan"),
                "max_drawdown": float("nan"),
                "factor_exposure": {},
            }

        result: dict[str, Any] = {}

        # Calculate volatility
        daily_std = float(returns.std())
        result["volatility"] = daily_std * np.sqrt(self._annualization_factor)

        # Calculate Sharpe ratio (assuming 0 risk-free rate)
        mean_return = float(returns.mean())
        if daily_std > 0:
            result["sharpe_ratio"] = (mean_return / daily_std) * np.sqrt(
                self._annualization_factor
            )
        else:
            result["sharpe_ratio"] = float("nan")

        # Calculate max drawdown
        result["max_drawdown"] = self._calculate_max_drawdown(returns)

        # Calculate factor exposure if requested
        if include_factor_exposure:
            result["factor_exposure"] = self.calculate_factor_exposure(returns)

        logger.info(
            "Risk metrics calculated",
            volatility=result["volatility"],
            sharpe_ratio=result["sharpe_ratio"],
            max_drawdown=result["max_drawdown"],
        )

        return result

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown.

        Parameters
        ----------
        returns : pd.Series
            Returns time series

        Returns
        -------
        float
            Maximum drawdown (negative value)
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())

    def calculate_factor_exposure(
        self,
        returns: pd.Series,
    ) -> dict[str, float]:
        """Calculate factor exposure metrics.

        This method computes exposure to common factors like momentum
        and volatility using the factor package's capabilities.

        Parameters
        ----------
        returns : pd.Series
            Returns time series

        Returns
        -------
        dict[str, float]
            Dictionary of factor exposures:
            - momentum_exposure: Exposure to momentum factor
            - volatility_exposure: Exposure to volatility factor

        Examples
        --------
        >>> calculator = FactorBasedRiskCalculator()
        >>> exposure = calculator.calculate_factor_exposure(returns)
        >>> "momentum_exposure" in exposure
        True
        """
        logger.debug("Calculating factor exposure", returns_length=len(returns))

        if returns.empty or len(returns) < 5:
            logger.warning("Insufficient data for factor exposure calculation")
            return {
                "momentum_exposure": float("nan"),
                "volatility_exposure": float("nan"),
            }

        result: dict[str, float] = {}

        # Calculate momentum exposure (average of rolling returns)
        if len(returns) >= 20:
            momentum = returns.rolling(window=20).mean()
            result["momentum_exposure"] = (
                float(momentum.iloc[-1]) if not momentum.empty else float("nan")
            )
        else:
            result["momentum_exposure"] = float(returns.mean())

        # Calculate volatility exposure (rolling volatility)
        if len(returns) >= 20:
            rolling_vol = returns.rolling(window=20).std()
            result["volatility_exposure"] = (
                float(rolling_vol.iloc[-1]) if not rolling_vol.empty else float("nan")
            )
        else:
            result["volatility_exposure"] = float(returns.std())

        logger.debug(
            "Factor exposure calculated",
            momentum_exposure=result["momentum_exposure"],
            volatility_exposure=result["volatility_exposure"],
        )

        return result

    def calculate_factor_attribution(
        self,
        portfolio_returns: pd.Series,
        factor_returns: dict[str, pd.Series],
    ) -> dict[str, float]:
        """Calculate factor attribution for portfolio returns.

        Parameters
        ----------
        portfolio_returns : pd.Series
            Portfolio returns time series
        factor_returns : dict[str, pd.Series]
            Dictionary of factor name to factor returns series

        Returns
        -------
        dict[str, float]
            Factor attribution results:
            - {factor_name}_beta: Beta to each factor
            - residual_return: Alpha (unexplained return)
            - r_squared: R-squared of the attribution

        Examples
        --------
        >>> calculator = FactorBasedRiskCalculator()
        >>> attribution = calculator.calculate_factor_attribution(
        ...     portfolio_returns,
        ...     {"market": market_returns, "momentum": momentum_returns}
        ... )
        >>> "market_beta" in attribution
        True
        """
        logger.debug(
            "Calculating factor attribution",
            portfolio_length=len(portfolio_returns),
            factors=list(factor_returns.keys()),
        )

        if portfolio_returns.empty or not factor_returns:
            logger.warning("Insufficient data for factor attribution")
            return {"residual_return": float("nan"), "r_squared": float("nan")}

        result: dict[str, float] = {}

        # Align all series to common index
        all_series = [portfolio_returns, *factor_returns.values()]
        aligned = pd.concat(all_series, axis=1).dropna()

        if len(aligned) < 5:
            logger.warning("Insufficient overlapping data points")
            return {"residual_return": float("nan"), "r_squared": float("nan")}

        portfolio_aligned = aligned.iloc[:, 0]

        # Calculate beta and correlation for each factor
        for i, (factor_name, _) in enumerate(factor_returns.items()):
            factor_aligned = aligned.iloc[:, i + 1]

            # Calculate beta
            covariance = portfolio_aligned.cov(factor_aligned)
            variance = factor_aligned.var()

            if variance > 0:
                result[f"{factor_name}_beta"] = float(covariance / variance)
            else:
                result[f"{factor_name}_beta"] = float("nan")

        # Calculate simple R-squared (using first factor for simplicity)
        if factor_returns:
            first_factor = next(iter(factor_returns.keys()))
            first_beta = result.get(f"{first_factor}_beta", 0.0)
            factor_aligned = aligned.iloc[:, 1]

            if not np.isnan(first_beta):
                explained = first_beta * factor_aligned
                residual = portfolio_aligned - explained
                result["residual_return"] = float(residual.mean())

                total_var = portfolio_aligned.var()
                if total_var > 0:
                    residual_var = residual.var()
                    result["r_squared"] = float(1 - residual_var / total_var)
                else:
                    result["r_squared"] = float("nan")
            else:
                result["residual_return"] = float(portfolio_aligned.mean())
                result["r_squared"] = float("nan")
        else:
            result["residual_return"] = float("nan")
            result["r_squared"] = float("nan")

        logger.info(
            "Factor attribution calculated",
            factors=list(factor_returns.keys()),
            r_squared=result.get("r_squared"),
        )

        return result


def create_factor_risk_calculator(
    annualization_factor: int = 252,
) -> FactorBasedRiskCalculator:
    """Factory function to create a FactorBasedRiskCalculator.

    Parameters
    ----------
    annualization_factor : int
        Factor for annualization (default: 252)

    Returns
    -------
    FactorBasedRiskCalculator
        A new FactorBasedRiskCalculator instance

    Examples
    --------
    >>> calculator = create_factor_risk_calculator()
    >>> isinstance(calculator, FactorBasedRiskCalculator)
    True
    """
    logger.debug("Creating FactorBasedRiskCalculator via factory function")
    return FactorBasedRiskCalculator(annualization_factor=annualization_factor)


__all__ = [
    "FactorBasedRiskCalculator",
    "create_factor_risk_calculator",
]
