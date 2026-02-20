"""Phase 6 strategy evaluation module for the CA Strategy pipeline.

Evaluates the equal-weight portfolio on three axes:

1. **Performance** — Sharpe ratio, max drawdown, beta, information ratio,
   and cumulative return relative to a benchmark.
2. **Analyst Correlation** — Spearman rank correlation and hit rate between
   strategy scores and KY/AK analyst scores.
3. **Transparency** — Mean claim count, structural weight, and coverage rate
   for portfolio holdings.

All evaluation is based on ``pd.Series`` inputs; yfinance data fetching is
handled by the caller (e.g. Orchestrator).
"""

from __future__ import annotations

import statistics
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from strategy.risk.calculator import RiskCalculator
from utils_core.logging import get_logger

from .types import (
    AnalystCorrelation,
    EvaluationResult,
    PerformanceMetrics,
    TransparencyMetrics,
)

if TYPE_CHECKING:
    from .types import (
        AnalystScore,
        PortfolioResult,
        ScoredClaim,
        StockScore,
    )

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MIN_SAMPLE_SIZE_WARNING: int = 30
"""Minimum sample size for analyst correlation (log warning if below)."""

_HIT_RATE_PERCENTILE: float = 0.20
"""Top-percentile fraction for hit rate calculation (top 20%)."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
class StrategyEvaluator:
    """Evaluate the CA Strategy equal-weight portfolio on 3 axes.

    Parameters
    ----------
    risk_free_rate : float, default=0.0
        Annual risk-free rate used in Sharpe ratio calculation.
    annualization_factor : int, default=252
        Factor for annualizing daily returns (252 trading days/year).

    Examples
    --------
    >>> evaluator = StrategyEvaluator()
    >>> result = evaluator.evaluate(
    ...     portfolio=portfolio_result,
    ...     scores=stock_scores,
    ...     portfolio_returns=portfolio_series,
    ...     benchmark_returns=benchmark_series,
    ...     analyst_scores={},
    ... )
    >>> result.performance.sharpe_ratio
    0.85
    """

    def __init__(
        self,
        risk_free_rate: float = 0.0,
        annualization_factor: int = 252,
    ) -> None:
        self._risk_free_rate = risk_free_rate
        self._annualization_factor = annualization_factor
        logger.debug(
            "StrategyEvaluator initialized",
            risk_free_rate=risk_free_rate,
            annualization_factor=annualization_factor,
        )

    def evaluate(
        self,
        portfolio: PortfolioResult,
        scores: dict[str, StockScore],
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        analyst_scores: dict[str, AnalystScore],
        threshold: float = 0.5,
    ) -> EvaluationResult:
        """Evaluate the equal-weight portfolio.

        Parameters
        ----------
        portfolio : PortfolioResult
            Equal-weight portfolio from PortfolioBuilder.build_equal_weight().
        scores : dict[str, StockScore]
            Aggregated stock scores (all universe tickers).
        portfolio_returns : pd.Series
            Daily portfolio returns time series.
        benchmark_returns : pd.Series
            Daily benchmark returns time series.
        analyst_scores : dict[str, AnalystScore]
            KY/AK analyst scores keyed by ticker.  Empty dict if unavailable.
        threshold : float, default=0.5
            Score threshold used to build the portfolio (for reporting).

        Returns
        -------
        EvaluationResult
            Structured evaluation result with performance, correlation,
            and transparency metrics.
        """
        logger.info(
            "Evaluating strategy",
            portfolio_size=len(portfolio.holdings),
            threshold=threshold,
        )

        performance = self._compute_performance(portfolio_returns, benchmark_returns)
        analyst_correlation = self._compute_analyst_correlation(
            portfolio=portfolio,
            scores=scores,
            analyst_scores=analyst_scores,
        )
        transparency = self._compute_transparency(
            portfolio=portfolio,
            scores=scores,
        )

        # Derive as_of_date from the last date in benchmark_returns index
        as_of_date: date
        if len(benchmark_returns) > 0:
            last_idx = benchmark_returns.index[-1]
            as_of_date = last_idx.date() if hasattr(last_idx, "date") else date.today()
        else:
            as_of_date = date.today()

        result = EvaluationResult(
            threshold=threshold,
            portfolio_size=len(portfolio.holdings),
            performance=performance,
            analyst_correlation=analyst_correlation,
            transparency=transparency,
            as_of_date=as_of_date,
        )

        logger.info(
            "Strategy evaluation completed",
            threshold=threshold,
            sharpe=performance.sharpe_ratio,
            sample_size=analyst_correlation.sample_size,
        )

        return result

    # -----------------------------------------------------------------------
    # Performance evaluation
    # -----------------------------------------------------------------------
    def _compute_performance(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> PerformanceMetrics:
        """Compute risk/performance metrics.

        Parameters
        ----------
        portfolio_returns : pd.Series
            Daily portfolio returns.
        benchmark_returns : pd.Series
            Daily benchmark returns.

        Returns
        -------
        PerformanceMetrics
            Structured performance metrics.
        """
        calc = RiskCalculator(
            returns=portfolio_returns,
            risk_free_rate=self._risk_free_rate,
            annualization_factor=self._annualization_factor,
        )

        sharpe = calc.sharpe_ratio()
        max_dd = calc.max_drawdown()
        beta = calc.beta(benchmark_returns)
        ir = calc.information_ratio(benchmark_returns)
        cumulative_return = float((1 + portfolio_returns).prod() - 1)

        logger.debug(
            "Performance metrics computed",
            sharpe=sharpe,
            max_drawdown=max_dd,
            beta=beta,
            information_ratio=ir,
            cumulative_return=cumulative_return,
        )

        return PerformanceMetrics(
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            beta=beta,
            information_ratio=ir,
            cumulative_return=cumulative_return,
        )

    # -----------------------------------------------------------------------
    # Analyst correlation
    # -----------------------------------------------------------------------
    def _compute_analyst_correlation(
        self,
        portfolio: PortfolioResult,
        scores: dict[str, StockScore],
        analyst_scores: dict[str, AnalystScore],
    ) -> AnalystCorrelation:
        """Compute Spearman correlation with analyst scores.

        Parameters
        ----------
        portfolio : PortfolioResult
            Portfolio holdings.
        scores : dict[str, StockScore]
            Strategy scores for universe tickers.
        analyst_scores : dict[str, AnalystScore]
            KY/AK analyst scores keyed by ticker.

        Returns
        -------
        AnalystCorrelation
            Structured analyst correlation results.
        """
        # Collect tickers with both strategy and non-None analyst scores
        portfolio_tickers = {h.ticker for h in portfolio.holdings}

        paired: list[tuple[float, float]] = []
        for ticker in portfolio_tickers:
            if ticker not in analyst_scores or ticker not in scores:
                continue
            analyst = analyst_scores[ticker]
            # Average KY and AK scores if both available
            analyst_vals = [v for v in [analyst.ky, analyst.ak] if v is not None]
            if not analyst_vals:
                continue
            analyst_avg = statistics.fmean(analyst_vals)
            strategy_score = scores[ticker].aggregate_score
            paired.append((strategy_score, analyst_avg))

        sample_size = len(paired)

        if sample_size < _MIN_SAMPLE_SIZE_WARNING:
            logger.warning(
                "Analyst correlation sample size below recommended minimum",
                sample_size=sample_size,
                minimum=_MIN_SAMPLE_SIZE_WARNING,
            )

        if sample_size < 2:
            return AnalystCorrelation(
                spearman_correlation=None,
                sample_size=sample_size,
                p_value=None,
                hit_rate=None,
            )

        strategy_scores_list = [p[0] for p in paired]
        analyst_scores_list = [p[1] for p in paired]

        # Compute Spearman correlation manually using rank approach
        from scipy import stats as scipy_stats

        spearman_result = scipy_stats.spearmanr(
            strategy_scores_list, analyst_scores_list
        )
        corr = float(spearman_result.statistic)
        pval = float(spearman_result.pvalue)

        # Compute hit rate: top-20% strategy stocks also in top-20% analyst
        hit_rate = self._compute_hit_rate(
            strategy_scores_list, analyst_scores_list, _HIT_RATE_PERCENTILE
        )

        logger.debug(
            "Analyst correlation computed",
            spearman=corr,
            p_value=pval,
            sample_size=sample_size,
            hit_rate=hit_rate,
        )

        return AnalystCorrelation(
            spearman_correlation=corr,
            sample_size=sample_size,
            p_value=pval,
            hit_rate=hit_rate,
        )

    @staticmethod
    def _compute_hit_rate(
        strategy_scores: list[float],
        analyst_scores: list[float],
        top_fraction: float,
    ) -> float:
        """Compute hit rate: fraction of top-N% strategy stocks in top-N% analyst.

        Parameters
        ----------
        strategy_scores : list[float]
            Strategy scores in same order as analyst_scores.
        analyst_scores : list[float]
            Analyst scores.
        top_fraction : float
            Top percentile fraction (e.g. 0.20 = top 20%).

        Returns
        -------
        float
            Hit rate in [0.0, 1.0].
        """
        n = len(strategy_scores)
        top_n = max(1, round(n * top_fraction))

        # Identify top-N indices by strategy score and analyst score
        strategy_top = set(
            sorted(range(n), key=lambda i: strategy_scores[i], reverse=True)[:top_n]
        )
        analyst_top = set(
            sorted(range(n), key=lambda i: analyst_scores[i], reverse=True)[:top_n]
        )

        overlap = len(strategy_top & analyst_top)
        return overlap / top_n

    # -----------------------------------------------------------------------
    # Transparency metrics
    # -----------------------------------------------------------------------
    def _compute_transparency(
        self,
        portfolio: PortfolioResult,
        scores: dict[str, StockScore],
    ) -> TransparencyMetrics:
        """Compute transparency metrics for portfolio holdings.

        Parameters
        ----------
        portfolio : PortfolioResult
            Portfolio holdings.
        scores : dict[str, StockScore]
            Strategy scores for universe tickers.

        Returns
        -------
        TransparencyMetrics
            Structured transparency metrics.
        """
        portfolio_tickers = [h.ticker for h in portfolio.holdings]
        n_holdings = len(portfolio_tickers)

        if n_holdings == 0:
            return TransparencyMetrics(
                mean_claim_count=0.0,
                mean_structural_weight=0.0,
                coverage_rate=0.0,
            )

        claim_counts: list[float] = []
        structural_weights: list[float] = []
        coverage_count = 0

        for ticker in portfolio_tickers:
            if ticker in scores:
                stock_score = scores[ticker]
                claim_counts.append(float(stock_score.claim_count))
                structural_weights.append(stock_score.structural_weight)
                coverage_count += 1

        if not claim_counts:
            return TransparencyMetrics(
                mean_claim_count=0.0,
                mean_structural_weight=0.0,
                coverage_rate=0.0,
            )

        mean_claim_count = statistics.fmean(claim_counts)
        mean_structural_weight = statistics.fmean(structural_weights)
        coverage_rate = coverage_count / n_holdings

        logger.debug(
            "Transparency metrics computed",
            mean_claim_count=mean_claim_count,
            mean_structural_weight=mean_structural_weight,
            coverage_rate=coverage_rate,
        )

        return TransparencyMetrics(
            mean_claim_count=mean_claim_count,
            mean_structural_weight=mean_structural_weight,
            coverage_rate=coverage_rate,
        )


__all__ = ["StrategyEvaluator"]
