"""Tests for ca_strategy evaluator module.

StrategyEvaluator evaluates the equal-weight portfolio on 3 axes:
- Performance: Sharpe/MaxDD/Beta/IR via RiskCalculator
- Analyst Correlation: Spearman rank correlation with KY/AK scores (non-None only)
- Transparency: claim_count/structural_weight statistics for portfolio holdings

Key behaviors:
- evaluate() returns an EvaluationResult
- Analyst correlation only uses tickers where at least one of KY or AK is not None
- Hit rate is fraction of top-20% strategy stocks also in top-20% analyst scores
- Sample size < 30 triggers a warning log
- Sample size < 2 returns None for correlation/p_value/hit_rate
- Empty portfolio returns zero-valued transparency metrics
"""

from __future__ import annotations

import logging
import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from dev.ca_strategy.evaluator import StrategyEvaluator
from dev.ca_strategy.types import (
    AnalystCorrelation,
    AnalystScore,
    EvaluationResult,
    PerformanceMetrics,
    PortfolioHolding,
    PortfolioResult,
    SectorAllocation,
    StockScore,
    TransparencyMetrics,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_AS_OF_DATE: date = date(2024, 9, 30)

_TICKERS = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"]


def _make_returns(n: int = 252, mean: float = 0.001, std: float = 0.02) -> pd.Series:
    """Create a reproducible daily return series."""
    rng = np.random.default_rng(0)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.Series(rng.normal(mean, std, n), index=idx)


def _make_portfolio(tickers: list[str] | None = None) -> PortfolioResult:
    """Create a minimal valid PortfolioResult."""
    if tickers is None:
        tickers = _TICKERS
    n = len(tickers)
    weight = round(1.0 / n, 6) if n > 0 else 0.0
    holdings = [
        PortfolioHolding(
            ticker=t,
            weight=weight,
            sector="Information Technology",
            score=0.8,
            rationale_summary=f"Score 0.8 for {t}",
        )
        for t in tickers
    ]
    sector_allocations = [
        SectorAllocation(
            sector="Information Technology",
            benchmark_weight=1.0,
            actual_weight=1.0,
            stock_count=n,
        )
    ]
    return PortfolioResult(
        holdings=holdings,
        sector_allocations=sector_allocations,
        as_of_date=_AS_OF_DATE,
    )


def _make_stock_scores(
    tickers: list[str] | None = None,
    claim_count: int = 5,
    structural_weight: float = 0.6,
) -> dict[str, StockScore]:
    """Create StockScore map for given tickers."""
    if tickers is None:
        tickers = _TICKERS
    rng = np.random.default_rng(1)
    return {
        t: StockScore(
            ticker=t,
            aggregate_score=float(rng.uniform(0.3, 0.9)),
            claim_count=claim_count,
            structural_weight=structural_weight,
        )
        for t in tickers
    }


def _make_analyst_scores(
    tickers: list[str] | None = None,
    ky: int | None = 5,
    ak: int | None = 5,
    vary: bool = True,
) -> dict[str, AnalystScore]:
    """Create AnalystScore map for given tickers.

    Parameters
    ----------
    tickers : list[str] | None
        List of tickers. Defaults to _TICKERS.
    ky : int | None
        Base KY value. When vary=True, each ticker gets ky + offset.
    ak : int | None
        Base AK value. When vary=True, each ticker gets ak + offset.
    vary : bool
        If True, vary scores across tickers to avoid constant-input issue
        (constant inputs make Spearman correlation undefined / NaN).
    """
    if tickers is None:
        tickers = _TICKERS
    result: dict[str, AnalystScore] = {}
    for i, t in enumerate(tickers):
        ky_val = (ky + i) if (vary and ky is not None) else ky
        ak_val = (ak + i) if (vary and ak is not None) else ak
        result[t] = AnalystScore(ticker=t, ky=ky_val, ak=ak_val)
    return result


def _make_evaluator(**kwargs: object) -> StrategyEvaluator:
    """Create a StrategyEvaluator with optional overrides."""
    return StrategyEvaluator(**kwargs)  # type: ignore[arg-type]


# ===========================================================================
# StrategyEvaluator – instantiation
# ===========================================================================
class TestStrategyEvaluatorInit:
    """StrategyEvaluator instantiation tests."""

    def test_正常系_デフォルト設定で作成できる(self) -> None:
        evaluator = StrategyEvaluator()
        assert isinstance(evaluator, StrategyEvaluator)

    def test_正常系_カスタムリスクフリーレートで作成できる(self) -> None:
        evaluator = StrategyEvaluator(risk_free_rate=0.05)
        assert evaluator._risk_free_rate == 0.05

    def test_正常系_カスタム年率化係数で作成できる(self) -> None:
        evaluator = StrategyEvaluator(annualization_factor=52)
        assert evaluator._annualization_factor == 52


# ===========================================================================
# StrategyEvaluator.evaluate – return type
# ===========================================================================
class TestEvaluateReturnType:
    """evaluate() returns EvaluationResult."""

    def test_正常系_EvaluationResultを返す(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)
        analyst_scores = _make_analyst_scores()

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert isinstance(result, EvaluationResult)

    def test_正常系_performanceがPerformanceMetrics型である(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)
        analyst_scores = _make_analyst_scores()

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert isinstance(result.performance, PerformanceMetrics)

    def test_正常系_analyst_correlationがAnalystCorrelation型である(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)
        analyst_scores = _make_analyst_scores()

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert isinstance(result.analyst_correlation, AnalystCorrelation)

    def test_正常系_transparencyがTransparencyMetrics型である(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)
        analyst_scores = _make_analyst_scores()

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert isinstance(result.transparency, TransparencyMetrics)

    def test_正常系_thresholdが設定される(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
            threshold=0.7,
        )

        assert result.threshold == 0.7

    def test_正常系_portfolio_sizeがholdingsの数と一致する(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert result.portfolio_size == len(portfolio.holdings)


# ===========================================================================
# StrategyEvaluator – performance metrics
# ===========================================================================
class TestPerformanceMetrics:
    """Performance evaluation via RiskCalculator."""

    def test_正常系_SharpeRatioが計算される(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns(mean=0.002, std=0.015)
        benchmark_returns = _make_returns(mean=0.001, std=0.015)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        # Sharpe ratio should be a finite float
        assert isinstance(result.performance.sharpe_ratio, float)
        assert not math.isnan(result.performance.sharpe_ratio)

    def test_正常系_MaxDrawdownが非正値である(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert result.performance.max_drawdown <= 0.0

    def test_正常系_Betaが計算される(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert isinstance(result.performance.beta, float)

    def test_正常系_InformationRatioが計算される(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns(mean=0.002)
        benchmark_returns = _make_returns(mean=0.001)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert isinstance(result.performance.information_ratio, float)

    def test_正常系_累積リターンが独自計算される(self) -> None:
        """Cumulative return = (1 + returns).prod() - 1."""
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = pd.Series([0.01, 0.02, -0.01, 0.005])
        benchmark_returns = pd.Series([0.005, 0.01, -0.005, 0.002])

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        expected_cumulative = float((1 + portfolio_returns).prod() - 1)
        assert abs(result.performance.cumulative_return - expected_cumulative) < 1e-10

    def test_正常系_全正リターンで累積リターンが正値(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = pd.Series([0.01] * 50)
        benchmark_returns = pd.Series([0.005] * 50)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert result.performance.cumulative_return > 0.0

    def test_正常系_as_of_dateがbenchmark_returnsの最終日付(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        idx = pd.date_range("2024-01-01", periods=10, freq="B")
        portfolio_returns = pd.Series([0.001] * 10, index=idx)
        benchmark_returns = pd.Series([0.001] * 10, index=idx)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert result.as_of_date == idx[-1].date()


# ===========================================================================
# StrategyEvaluator – analyst correlation
# ===========================================================================
class TestAnalystCorrelation:
    """Spearman correlation with KY/AK analyst scores."""

    def test_正常系_Spearman相関が計算される(self) -> None:
        evaluator = _make_evaluator()
        # Build portfolio with enough tickers for correlation
        # Use KY-only scores (ak=None) to avoid averaging to constant values
        tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"]
        portfolio = _make_portfolio(tickers)
        scores = {
            t: StockScore(
                ticker=t, aggregate_score=s, claim_count=3, structural_weight=0.5
            )
            for t, s in zip(tickers, [0.9, 0.7, 0.5, 0.8, 0.6], strict=True)
        }
        # Use KY-only scores to ensure non-constant analyst values
        analyst_scores = {
            t: AnalystScore(ticker=t, ky=k, ak=None)
            for t, k in zip(tickers, [1, 3, 2, 5, 4], strict=True)
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert result.analyst_correlation.spearman_correlation is not None
        assert -1.0 <= result.analyst_correlation.spearman_correlation <= 1.0

    def test_正常系_p_valueが計算される(self) -> None:
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        analyst_scores = {
            t: AnalystScore(ticker=t, ky=k, ak=k)
            for t, k in zip(tickers, [1, 2, 3, 4, 5], strict=True)
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert result.analyst_correlation.p_value is not None
        assert 0.0 <= result.analyst_correlation.p_value <= 1.0

    def test_正常系_hit_rateが計算される(self) -> None:
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        analyst_scores = _make_analyst_scores(tickers, ky=3, ak=4)
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert result.analyst_correlation.hit_rate is not None
        assert 0.0 <= result.analyst_correlation.hit_rate <= 1.0

    def test_正常系_KYのみ有効でもAKなしの銘柄を含む(self) -> None:
        """KY非Noneのみでも相関計算に含まれる。"""
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT", "GOOGL"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        # AK is None for all
        analyst_scores = {
            t: AnalystScore(ticker=t, ky=k, ak=None)
            for t, k in zip(tickers, [1, 2, 3], strict=True)
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        # All 3 tickers have KY, so sample_size = 3
        assert result.analyst_correlation.sample_size == 3

    def test_正常系_AKのみ有効でKYなしの銘柄を含む(self) -> None:
        """AK非Noneのみでも相関計算に含まれる。"""
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT", "GOOGL"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        # KY is None for all
        analyst_scores = {
            t: AnalystScore(ticker=t, ky=None, ak=k)
            for t, k in zip(tickers, [1, 2, 3], strict=True)
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert result.analyst_correlation.sample_size == 3

    def test_エッジケース_全KY_AK空の場合にNone値を返す(self) -> None:
        """全銘柄でKY/AKが両方Noneの場合、相関はNoneを返す。"""
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        # Both KY and AK are None for all tickers
        analyst_scores = {t: AnalystScore(ticker=t, ky=None, ak=None) for t in tickers}
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        corr = result.analyst_correlation
        assert corr.sample_size == 0
        assert corr.spearman_correlation is None
        assert corr.p_value is None
        assert corr.hit_rate is None

    def test_エッジケース_analyst_scoresが空辞書の場合にsample_sizeが0(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert result.analyst_correlation.sample_size == 0
        assert result.analyst_correlation.spearman_correlation is None
        assert result.analyst_correlation.p_value is None

    def test_エッジケース_sample_size_1でNone値を返す(self) -> None:
        """sample_size < 2 では相関が None。"""
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        # Only AAPL has non-None analyst scores
        analyst_scores = {
            "AAPL": AnalystScore(ticker="AAPL", ky=5, ak=3),
            "MSFT": AnalystScore(ticker="MSFT", ky=None, ak=None),
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert result.analyst_correlation.sample_size == 1
        assert result.analyst_correlation.spearman_correlation is None
        assert result.analyst_correlation.p_value is None

    def test_正常系_sample_sizeがポートフォリオの有効銘柄数と一致する(self) -> None:
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT", "GOOGL"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        analyst_scores = _make_analyst_scores(tickers, ky=3, ak=4)
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        assert result.analyst_correlation.sample_size == 3


# ===========================================================================
# StrategyEvaluator – hit rate
# ===========================================================================
class TestHitRate:
    """Hit rate calculation."""

    def test_正常系_完全一致でhit_rateが1(self) -> None:
        """Top-20% strategy == top-20% analyst → hit rate = 1.0."""
        # Use 5 tickers; top-20% = top 1
        tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"]
        portfolio = _make_portfolio(tickers)
        # AAPL has highest strategy score
        scores = {
            t: StockScore(
                ticker=t, aggregate_score=s, claim_count=3, structural_weight=0.5
            )
            for t, s in zip(tickers, [0.9, 0.5, 0.4, 0.3, 0.2], strict=True)
        }
        # AAPL also has highest analyst score (KY=10 is highest rank value)
        analyst_scores = {
            t: AnalystScore(ticker=t, ky=k, ak=None)
            for t, k in zip(tickers, [10, 5, 4, 3, 2], strict=True)
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        evaluator = _make_evaluator()
        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        # Both agree that AAPL is top 20% → hit rate = 1.0
        assert result.analyst_correlation.hit_rate == 1.0

    def test_正常系_全不一致でhit_rateが0(self) -> None:
        """Top-20% strategy != top-20% analyst → hit rate = 0.0."""
        tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"]
        portfolio = _make_portfolio(tickers)
        # AAPL has highest strategy score
        scores = {
            t: StockScore(
                ticker=t, aggregate_score=s, claim_count=3, structural_weight=0.5
            )
            for t, s in zip(tickers, [0.9, 0.5, 0.4, 0.3, 0.2], strict=True)
        }
        # JNJ has highest analyst score (lowest strategy score)
        analyst_scores = {
            t: AnalystScore(ticker=t, ky=k, ak=None)
            for t, k in zip(tickers, [1, 2, 3, 4, 10], strict=True)
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        evaluator = _make_evaluator()
        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores=analyst_scores,
        )

        # Strategy top 20% = AAPL, Analyst top 20% = JNJ → no overlap
        assert result.analyst_correlation.hit_rate == 0.0


# ===========================================================================
# StrategyEvaluator – transparency metrics
# ===========================================================================
class TestTransparencyMetrics:
    """Transparency metrics: claim_count/structural_weight statistics."""

    def test_正常系_mean_claim_countが正しく計算される(self) -> None:
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT"]
        portfolio = _make_portfolio(tickers)
        scores = {
            "AAPL": StockScore(
                ticker="AAPL", aggregate_score=0.9, claim_count=4, structural_weight=0.6
            ),
            "MSFT": StockScore(
                ticker="MSFT", aggregate_score=0.8, claim_count=6, structural_weight=0.4
            ),
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        # mean_claim_count = (4 + 6) / 2 = 5.0
        assert abs(result.transparency.mean_claim_count - 5.0) < 1e-10

    def test_正常系_mean_structural_weightが正しく計算される(self) -> None:
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT"]
        portfolio = _make_portfolio(tickers)
        scores = {
            "AAPL": StockScore(
                ticker="AAPL", aggregate_score=0.9, claim_count=4, structural_weight=0.6
            ),
            "MSFT": StockScore(
                ticker="MSFT", aggregate_score=0.8, claim_count=6, structural_weight=0.4
            ),
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        # mean_structural_weight = (0.6 + 0.4) / 2 = 0.5
        assert abs(result.transparency.mean_structural_weight - 0.5) < 1e-10

    def test_正常系_coverage_rateが全銘柄スコアありで1(self) -> None:
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert result.transparency.coverage_rate == 1.0

    def test_正常系_coverage_rateが部分スコアありで正しい比率(self) -> None:
        """Only AAPL has a score entry; MSFT is missing → coverage_rate = 0.5."""
        evaluator = _make_evaluator()
        tickers = ["AAPL", "MSFT"]
        portfolio = _make_portfolio(tickers)
        scores = {
            "AAPL": StockScore(
                ticker="AAPL", aggregate_score=0.9, claim_count=3, structural_weight=0.5
            ),
        }
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert abs(result.transparency.coverage_rate - 0.5) < 1e-10

    def test_エッジケース_holdingsが空の場合にゼロ値を返す(self) -> None:
        """Empty portfolio returns zero transparency metrics."""
        evaluator = _make_evaluator()
        portfolio = _make_portfolio([])  # no holdings
        scores: dict[str, StockScore] = {}
        portfolio_returns = pd.Series([0.001, 0.002, -0.001])
        benchmark_returns = pd.Series([0.0005, 0.001, -0.0005])

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert result.transparency.mean_claim_count == 0.0
        assert result.transparency.mean_structural_weight == 0.0
        assert result.transparency.coverage_rate == 0.0

    def test_エッジケース_scoresが空辞書の場合にゼロ値を返す(self) -> None:
        """Portfolio holdings with no scores → zero transparency."""
        evaluator = _make_evaluator()
        portfolio = _make_portfolio(["AAPL", "MSFT"])
        scores: dict[str, StockScore] = {}  # no scores at all
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        assert result.transparency.mean_claim_count == 0.0
        assert result.transparency.mean_structural_weight == 0.0
        assert result.transparency.coverage_rate == 0.0


# ===========================================================================
# StrategyEvaluator – sample size warning
# ===========================================================================
class TestSampleSizeWarning:
    """Sample size < 30 triggers warning log."""

    def test_正常系_sample_size30未満で警告ログが出力される(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        evaluator = _make_evaluator()
        # Use only 5 tickers → sample_size = 5 < 30
        tickers = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"]
        portfolio = _make_portfolio(tickers)
        scores = _make_stock_scores(tickers)
        analyst_scores = _make_analyst_scores(tickers, ky=3, ak=4)
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        with caplog.at_level(logging.WARNING):
            evaluator.evaluate(
                portfolio=portfolio,
                scores=scores,
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
                analyst_scores=analyst_scores,
            )

        # Warning should mention sample size
        warning_messages = [
            r.message for r in caplog.records if r.levelno == logging.WARNING
        ]
        assert any(
            "sample" in str(m).lower() or "size" in str(m).lower()
            for m in warning_messages
        )

    def test_正常系_sample_size0でも警告ログが出力される(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        # No analyst scores → sample_size = 0
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        with caplog.at_level(logging.WARNING):
            evaluator.evaluate(
                portfolio=portfolio,
                scores=scores,
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
                analyst_scores={},
            )

        # Warning about small sample size (0 < 30)
        warning_messages = [
            r.message for r in caplog.records if r.levelno == logging.WARNING
        ]
        assert any(
            "sample" in str(m).lower() or "size" in str(m).lower()
            for m in warning_messages
        )


# ===========================================================================
# StrategyEvaluator – EvaluationResult immutability
# ===========================================================================
class TestEvaluationResultImmutability:
    """EvaluationResult must be frozen (immutable)."""

    def test_正常系_EvaluationResultはイミュータブルである(self) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = _make_returns()
        benchmark_returns = _make_returns(mean=0.0005)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        with pytest.raises(Exception, match="frozen"):
            result.threshold = 0.99


# ===========================================================================
# StrategyEvaluator – as_of_date derivation
# ===========================================================================
class TestAsOfDate:
    """as_of_date is derived from the last index of benchmark_returns."""

    def test_正常系_benchmark_returnsにインデックスがある場合に最終日付を使用する(
        self,
    ) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        idx = pd.date_range("2023-06-01", periods=20, freq="B")
        portfolio_returns = pd.Series([0.001] * 20, index=idx)
        benchmark_returns = pd.Series([0.0005] * 20, index=idx)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        expected_date = idx[-1].date()
        assert result.as_of_date == expected_date

    def test_エッジケース_benchmark_returnsが無インデックスの場合にdate_todayを使用する(
        self,
    ) -> None:
        evaluator = _make_evaluator()
        portfolio = _make_portfolio()
        scores = _make_stock_scores()
        portfolio_returns = pd.Series([0.001] * 5)
        benchmark_returns = pd.Series([0.0005] * 5)

        result = evaluator.evaluate(
            portfolio=portfolio,
            scores=scores,
            portfolio_returns=portfolio_returns,
            benchmark_returns=benchmark_returns,
            analyst_scores={},
        )

        # Without DatetimeIndex, as_of_date falls back to date.today()
        assert isinstance(result.as_of_date, date)
