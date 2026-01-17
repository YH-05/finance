"""Risk calculator for portfolio risk metrics.

This module provides the RiskCalculator class for computing various
risk metrics from portfolio returns data.
"""

import math
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats

from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Threshold for considering standard deviation as effectively zero
# This handles floating-point precision issues
_EPSILON = 1e-15


class RiskCalculator:
    """Risk metrics calculator for portfolio returns.

    This class computes various risk metrics from daily returns data,
    including volatility, Sharpe ratio, Sortino ratio, and downside deviation.

    Parameters
    ----------
    returns : pd.Series
        Time series of daily returns
    risk_free_rate : float, default=0.0
        Annual risk-free rate
    annualization_factor : int, default=252
        Factor for annualization (252 for daily, 52 for weekly, 12 for monthly)

    Attributes
    ----------
    _returns : pd.Series
        Internal storage of returns data
    _risk_free_rate : float
        Annual risk-free rate
    _annualization_factor : int
        Annualization factor

    Raises
    ------
    ValueError
        If returns is empty or annualization_factor is not positive

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> np.random.seed(42)
    >>> returns = pd.Series(np.random.normal(0.001, 0.02, 252))
    >>> calc = RiskCalculator(returns, risk_free_rate=0.02)
    >>> vol = calc.volatility()
    >>> vol > 0
    True
    """

    def __init__(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        annualization_factor: int = 252,
    ) -> None:
        """Initialize RiskCalculator with returns data.

        Parameters
        ----------
        returns : pd.Series
            Time series of daily returns
        risk_free_rate : float, default=0.0
            Annual risk-free rate
        annualization_factor : int, default=252
            Factor for annualization (252 for daily, 52 for weekly, 12 for monthly)

        Raises
        ------
        ValueError
            If returns is empty or annualization_factor is not positive
        """
        logger.debug(
            "Initializing RiskCalculator",
            returns_length=len(returns),
            risk_free_rate=risk_free_rate,
            annualization_factor=annualization_factor,
        )

        if len(returns) == 0:
            logger.error("Cannot initialize with empty returns")
            raise ValueError("returns must not be empty")

        if annualization_factor <= 0:
            logger.error(
                "Invalid annualization_factor",
                annualization_factor=annualization_factor,
            )
            raise ValueError(
                f"annualization_factor must be positive, got {annualization_factor}"
            )

        self._returns = returns
        self._risk_free_rate = risk_free_rate
        self._annualization_factor = annualization_factor

        logger.info(
            "RiskCalculator initialized successfully",
            returns_count=len(returns),
            risk_free_rate=risk_free_rate,
            annualization_factor=annualization_factor,
        )

    def volatility(self) -> float:
        """Calculate annualized volatility.

        Volatility is the annualized standard deviation of returns.

        Returns
        -------
        float
            Annualized volatility

        Notes
        -----
        Formula: volatility = std(returns) * sqrt(annualization_factor)

        Examples
        --------
        >>> calc = RiskCalculator(returns)
        >>> vol = calc.volatility()
        >>> vol >= 0  # Volatility is always non-negative
        True
        """
        logger.debug("Calculating volatility")

        std = float(self._returns.std())

        # Handle floating-point precision: treat very small std as zero
        if std < _EPSILON:
            logger.debug(
                "Standard deviation below threshold, returning 0",
                daily_std=std,
                threshold=_EPSILON,
            )
            return 0.0

        volatility = std * np.sqrt(self._annualization_factor)

        logger.debug(
            "Volatility calculated",
            daily_std=std,
            annualized_volatility=volatility,
        )

        return float(volatility)

    def sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio.

        The Sharpe ratio measures risk-adjusted return relative to
        the risk-free rate.

        Returns
        -------
        float
            Sharpe ratio (can be inf if volatility is zero)

        Notes
        -----
        Formula:
        - daily_rf = risk_free_rate / annualization_factor
        - excess_return = mean(returns) - daily_rf
        - sharpe = (excess_return / std(returns)) * sqrt(annualization_factor)

        Examples
        --------
        >>> calc = RiskCalculator(returns, risk_free_rate=0.02)
        >>> sharpe = calc.sharpe_ratio()
        """
        logger.debug("Calculating Sharpe ratio")

        daily_rf = self._risk_free_rate / self._annualization_factor
        excess_returns = self._returns - daily_rf

        mean_excess = float(excess_returns.mean())
        std_excess = float(excess_returns.std())

        # Handle floating-point precision: treat very small std as zero
        if std_excess < _EPSILON:
            # Zero standard deviation means infinite Sharpe if positive return
            if mean_excess > _EPSILON:
                sharpe = float("inf")
            elif mean_excess < -_EPSILON:
                sharpe = float("-inf")
            else:
                sharpe = float("nan")
            logger.warning(
                "Standard deviation below threshold in Sharpe ratio calculation",
                result=sharpe,
                std_excess=std_excess,
                threshold=_EPSILON,
            )
            return sharpe

        sharpe = float((mean_excess / std_excess) * np.sqrt(self._annualization_factor))

        logger.debug(
            "Sharpe ratio calculated",
            mean_excess_return=float(mean_excess),
            std_excess_return=float(std_excess),
            sharpe_ratio=sharpe,
        )

        return sharpe

    def sortino_ratio(self) -> float:
        """Calculate Sortino ratio.

        The Sortino ratio measures risk-adjusted return using only
        downside deviation (standard deviation of negative returns).

        Returns
        -------
        float
            Sortino ratio (can be inf if downside deviation is zero)

        Notes
        -----
        Formula:
        - daily_rf = risk_free_rate / annualization_factor
        - excess_return = mean(returns) - daily_rf
        - downside_std = std(returns[returns < 0])
        - sortino = (excess_return / downside_std) * sqrt(annualization_factor)

        Examples
        --------
        >>> calc = RiskCalculator(returns, risk_free_rate=0.02)
        >>> sortino = calc.sortino_ratio()
        """
        logger.debug("Calculating Sortino ratio")

        daily_rf = self._risk_free_rate / self._annualization_factor
        excess_return = self._returns.mean() - daily_rf

        # Calculate downside deviation
        negative_returns = self._returns[self._returns < 0]

        if len(negative_returns) == 0:
            # No negative returns means zero downside deviation
            if excess_return > _EPSILON:
                sortino = float("inf")
            elif excess_return < -_EPSILON:
                sortino = float("-inf")
            else:
                sortino = float("nan")
            logger.debug(
                "No negative returns, sortino ratio is infinite or nan",
                result=sortino,
            )
            return sortino

        # Single negative return has no standard deviation
        if len(negative_returns) == 1:
            if excess_return > _EPSILON:
                sortino = float("inf")
            elif excess_return < -_EPSILON:
                sortino = float("-inf")
            else:
                sortino = float("nan")
            logger.debug(
                "Only one negative return, sortino ratio is infinite or nan",
                result=sortino,
            )
            return sortino

        downside_std = float(negative_returns.std())

        # Handle floating-point precision: treat very small std as zero
        # Also handle NaN case
        if math.isnan(downside_std) or downside_std < _EPSILON:
            # All negative returns are the same
            if excess_return > _EPSILON:
                sortino = float("inf")
            elif excess_return < -_EPSILON:
                sortino = float("-inf")
            else:
                sortino = float("nan")
            logger.warning(
                "Downside standard deviation below threshold or NaN",
                result=sortino,
                downside_std=downside_std,
                threshold=_EPSILON,
            )
            return sortino

        sortino = float(
            (excess_return / downside_std) * np.sqrt(self._annualization_factor)
        )

        logger.debug(
            "Sortino ratio calculated",
            excess_return=float(excess_return),
            downside_std=float(downside_std),
            sortino_ratio=sortino,
        )

        return sortino

    def downside_deviation(self) -> float:
        """Calculate annualized downside deviation.

        Downside deviation measures the volatility of negative returns only,
        providing a more focused view of downside risk.

        Returns
        -------
        float
            Annualized downside deviation (0 if no negative returns)

        Notes
        -----
        Formula:
        - downside_returns = returns[returns < 0]
        - downside_deviation = std(downside_returns) * sqrt(annualization_factor)

        Examples
        --------
        >>> calc = RiskCalculator(returns)
        >>> dd = calc.downside_deviation()
        >>> dd >= 0  # Downside deviation is always non-negative
        True
        """
        logger.debug("Calculating downside deviation")

        negative_returns = self._returns[self._returns < 0]

        if len(negative_returns) == 0:
            logger.debug("No negative returns, downside deviation is 0")
            return 0.0

        # Single negative return has no standard deviation (NaN from pandas)
        if len(negative_returns) == 1:
            logger.debug(
                "Only one negative return, downside deviation is 0",
                negative_returns_count=1,
            )
            return 0.0

        downside_std = float(negative_returns.std())

        # Handle floating-point precision: treat very small std as zero
        # Also handle NaN case (shouldn't happen after the len==1 check, but be safe)
        if math.isnan(downside_std) or downside_std < _EPSILON:
            logger.debug(
                "Downside standard deviation below threshold or NaN, returning 0",
                downside_std=downside_std,
                threshold=_EPSILON,
            )
            return 0.0

        downside_dev = downside_std * np.sqrt(self._annualization_factor)

        logger.debug(
            "Downside deviation calculated",
            negative_returns_count=len(negative_returns),
            daily_downside_std=downside_std,
            annualized_downside_deviation=downside_dev,
        )

        return float(downside_dev)

    def max_drawdown(self) -> float:
        """Calculate maximum drawdown (MDD).

        Maximum drawdown measures the largest peak-to-trough decline
        in cumulative returns.

        Returns
        -------
        float
            Maximum drawdown (negative value, e.g., -0.15 = -15%)

        Notes
        -----
        Formula:
        - cumulative = (1 + returns).cumprod()
        - running_max = cumulative.cummax()
        - drawdown = (cumulative - running_max) / running_max
        - max_drawdown = min(drawdown)

        Examples
        --------
        >>> calc = RiskCalculator(returns)
        >>> mdd = calc.max_drawdown()
        >>> -1.0 <= mdd <= 0.0  # MDD is always in [-1, 0]
        True
        """
        logger.debug("Calculating max drawdown")

        cumulative = (1 + self._returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        mdd = float(drawdown.min())

        logger.debug(
            "Max drawdown calculated",
            max_drawdown=mdd,
            returns_count=len(self._returns),
        )

        return mdd

    def var(
        self,
        confidence: float = 0.95,
        method: Literal["historical", "parametric"] = "historical",
    ) -> float:
        """Calculate Value at Risk (VaR).

        VaR measures the potential loss in value of a portfolio over
        a defined period for a given confidence interval.

        Parameters
        ----------
        confidence : float, default=0.95
            Confidence level (e.g., 0.95 = 95%)
        method : {"historical", "parametric"}, default="historical"
            Calculation method:
            - "historical": Uses empirical distribution (percentile)
            - "parametric": Assumes normal distribution

        Returns
        -------
        float
            VaR value (typically negative, representing potential loss)

        Raises
        ------
        ValueError
            If method is not "historical" or "parametric"

        Notes
        -----
        Formula (Historical):
            var = percentile(returns, (1 - confidence) * 100)

        Formula (Parametric):
            var = mean(returns) + z_score * std(returns)
            where z_score = norm.ppf(1 - confidence)

        Examples
        --------
        >>> calc = RiskCalculator(returns)
        >>> var_95 = calc.var(confidence=0.95)
        >>> var_99 = calc.var(confidence=0.99)
        >>> var_99 <= var_95  # Higher confidence = larger potential loss
        True
        """
        logger.debug(
            "Calculating VaR",
            confidence=confidence,
            method=method,
        )

        if method not in ("historical", "parametric"):
            logger.error(
                "Invalid VaR method",
                method=method,
            )
            raise ValueError(
                f"method must be 'historical' or 'parametric', got {method!r}"
            )

        if method == "historical":
            var = float(np.percentile(self._returns, (1 - confidence) * 100))
        else:
            z_score = stats.norm.ppf(1 - confidence)
            var = float(self._returns.mean() + z_score * self._returns.std())

        logger.debug(
            "VaR calculated",
            confidence=confidence,
            method=method,
            var=var,
        )

        return var

    def _align_with_benchmark(
        self,
        benchmark_returns: pd.Series,
    ) -> tuple[pd.Series, pd.Series]:
        """Align portfolio and benchmark returns by common dates.

        Parameters
        ----------
        benchmark_returns : pd.Series
            Benchmark returns time series

        Returns
        -------
        tuple[pd.Series, pd.Series]
            Aligned (portfolio_returns, benchmark_returns)

        Raises
        ------
        ValueError
            If benchmark_returns is empty or no common dates exist
        """
        if len(benchmark_returns) == 0:
            logger.error("benchmark_returns is empty")
            raise ValueError("benchmark_returns must not be empty")

        aligned = pd.DataFrame(
            {
                "portfolio": self._returns,
                "benchmark": benchmark_returns,
            }
        ).dropna()

        if len(aligned) == 0:
            logger.error(
                "No common dates between portfolio and benchmark",
                portfolio_dates=len(self._returns),
                benchmark_dates=len(benchmark_returns),
            )
            raise ValueError(
                "No common or overlapping dates between portfolio and benchmark returns"
            )

        logger.debug(
            "Aligned portfolio and benchmark returns",
            common_dates=len(aligned),
        )

        return pd.Series(aligned["portfolio"]), pd.Series(aligned["benchmark"])

    def beta(self, benchmark_returns: pd.Series) -> float:
        """Calculate beta relative to a benchmark.

        Beta measures the sensitivity of portfolio returns to benchmark returns.
        A beta > 1 indicates higher volatility than the benchmark.

        Parameters
        ----------
        benchmark_returns : pd.Series
            Benchmark returns time series

        Returns
        -------
        float
            Beta value (NaN if benchmark variance is zero)

        Raises
        ------
        ValueError
            If benchmark_returns is empty or no common dates exist

        Notes
        -----
        Formula: beta = cov(portfolio, benchmark) / var(benchmark)

        Examples
        --------
        >>> calc = RiskCalculator(portfolio_returns)
        >>> beta = calc.beta(benchmark_returns)
        >>> beta > 0  # Typically positive for equity portfolios
        True
        """
        logger.debug("Calculating beta")

        portfolio_aligned, benchmark_aligned = self._align_with_benchmark(
            benchmark_returns
        )

        covariance = portfolio_aligned.cov(benchmark_aligned)
        benchmark_variance = benchmark_aligned.var()

        if benchmark_variance < _EPSILON:
            logger.warning(
                "Benchmark variance is effectively zero, returning NaN",
                benchmark_variance=benchmark_variance,
            )
            return float("nan")

        beta = float(covariance / benchmark_variance)

        logger.debug(
            "Beta calculated",
            covariance=covariance,
            benchmark_variance=benchmark_variance,
            beta=beta,
        )

        return beta

    def treynor_ratio(self, benchmark_returns: pd.Series) -> float:
        """Calculate Treynor ratio.

        The Treynor ratio measures return per unit of systematic risk (beta).

        Parameters
        ----------
        benchmark_returns : pd.Series
            Benchmark returns time series

        Returns
        -------
        float
            Treynor ratio (NaN if beta is zero or NaN)

        Raises
        ------
        ValueError
            If benchmark_returns is empty or no common dates exist

        Notes
        -----
        Formula: treynor = (annualized_return - risk_free_rate) / beta

        Examples
        --------
        >>> calc = RiskCalculator(portfolio_returns, risk_free_rate=0.02)
        >>> treynor = calc.treynor_ratio(benchmark_returns)
        """
        logger.debug("Calculating Treynor ratio")

        beta = self.beta(benchmark_returns)

        if math.isnan(beta):
            logger.warning("Beta is NaN, returning NaN for Treynor ratio")
            return float("nan")

        if abs(beta) < _EPSILON:
            annualized_return = float(self._returns.mean()) * self._annualization_factor
            excess_return = annualized_return - self._risk_free_rate

            if excess_return > _EPSILON:
                treynor = float("inf")
            elif excess_return < -_EPSILON:
                treynor = float("-inf")
            else:
                treynor = float("nan")

            logger.warning(
                "Beta is effectively zero",
                beta=beta,
                result=treynor,
            )
            return treynor

        annualized_return = float(self._returns.mean()) * self._annualization_factor
        treynor = (annualized_return - self._risk_free_rate) / beta

        logger.debug(
            "Treynor ratio calculated",
            annualized_return=annualized_return,
            risk_free_rate=self._risk_free_rate,
            beta=beta,
            treynor_ratio=treynor,
        )

        return float(treynor)

    def information_ratio(self, benchmark_returns: pd.Series) -> float:
        """Calculate Information ratio.

        The Information ratio measures active return per unit of tracking error.

        Parameters
        ----------
        benchmark_returns : pd.Series
            Benchmark returns time series

        Returns
        -------
        float
            Information ratio (NaN or inf if tracking error is zero)

        Raises
        ------
        ValueError
            If benchmark_returns is empty or no common dates exist

        Notes
        -----
        Formula: IR = mean(active_returns) / std(active_returns) * sqrt(annualization_factor)
        where active_returns = portfolio_returns - benchmark_returns

        Examples
        --------
        >>> calc = RiskCalculator(portfolio_returns)
        >>> ir = calc.information_ratio(benchmark_returns)
        >>> ir > 0  # Positive if outperforming benchmark
        True
        """
        logger.debug("Calculating Information ratio")

        portfolio_aligned, benchmark_aligned = self._align_with_benchmark(
            benchmark_returns
        )

        active_returns = portfolio_aligned - benchmark_aligned
        active_mean = float(active_returns.mean())
        active_std = float(active_returns.std())

        if active_std < _EPSILON:
            if active_mean > _EPSILON:
                ir = float("inf")
            elif active_mean < -_EPSILON:
                ir = float("-inf")
            else:
                ir = float("nan")

            logger.warning(
                "Tracking error is effectively zero",
                active_std=active_std,
                result=ir,
            )
            return ir

        ir = (active_mean / active_std) * np.sqrt(self._annualization_factor)

        logger.debug(
            "Information ratio calculated",
            active_mean=active_mean,
            tracking_error=active_std,
            information_ratio=ir,
        )

        return float(ir)
