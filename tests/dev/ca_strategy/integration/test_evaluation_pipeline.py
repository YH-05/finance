"""Integration tests for the ca_strategy evaluation pipeline.

Tests the End-to-End flow:
    PortfolioBuilder.build_equal_weight()
    → StrategyEvaluator.evaluate()
    → OutputGenerator.generate_all(evaluation=...)

Verifies:
- Multiple thresholds (0.3, 0.5, 0.7) can be processed
- Output files (evaluation_summary.md, evaluation_results.json) are generated
- External APIs (RiskCalculator, yfinance) are properly mocked

All tests use ``tmp_path`` for output directory isolation and
``unittest.mock.patch`` to avoid external API calls.
"""

from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import numpy as np
import pytest

from dev.ca_strategy.output import OutputGenerator
from dev.ca_strategy.portfolio_builder import PortfolioBuilder, RankedStock
from dev.ca_strategy.types import (
    BenchmarkWeight,
    PortfolioHolding,
    PortfolioResult,
    ScoredClaim,
    SectorAllocation,
    StockScore,
)

# ---------------------------------------------------------------------------
# Constants for pseudo-return generation
# ---------------------------------------------------------------------------
_SEED_PORTFOLIO: int = 42
_SEED_BENCHMARK: int = 100
_RETURN_DAYS: int = 252

_PORTFOLIO_MU: float = 0.0005
_PORTFOLIO_SIGMA: float = 0.015

_BENCHMARK_MU: float = 0.0003
_BENCHMARK_SIGMA: float = 0.012

_THRESHOLDS: list[float] = [0.3, 0.5, 0.7]
_AS_OF_DATE: date = date(2015, 9, 30)


# ---------------------------------------------------------------------------
# Fixtures — scored claims and stock scores
# ---------------------------------------------------------------------------
def _make_scored_claim(
    ticker: str,
    claim_text: str = "Test competitive advantage claim",
    final_confidence: float = 0.75,
) -> ScoredClaim:
    """Create a minimal ScoredClaim for testing."""
    from dev.ca_strategy.types import ConfidenceAdjustment, RuleEvaluation

    return ScoredClaim(
        id=f"{ticker}-claim-1",
        claim_type="competitive_advantage",
        claim=claim_text,
        evidence="Test evidence",
        rule_evaluation=RuleEvaluation(
            applied_rules=["rule_1"],
            results={"rule_1": True},
            confidence=final_confidence,
            adjustments=[],
        ),
        final_confidence=final_confidence,
        adjustments=[],
    )


def _make_ranked_stock(
    ticker: str,
    aggregate_score: float,
    sector: str = "Information Technology",
    sector_rank: int = 1,
) -> RankedStock:
    """Create a RankedStock typed dict for testing."""
    return RankedStock(
        ticker=ticker,
        aggregate_score=aggregate_score,
        gics_sector=sector,
        sector_rank=sector_rank,
        claim_count=3,
        structural_weight=0.6,
    )


@pytest.fixture()
def scored_claims() -> dict[str, list[ScoredClaim]]:
    """Scored claims for 6 test tickers across 3 sectors."""
    tickers_by_sector = {
        "Information Technology": [("AAPL", 0.85), ("MSFT", 0.75), ("GOOGL", 0.45)],
        "Financials": [("JPM", 0.80), ("GS", 0.35)],
        "Health Care": [("JNJ", 0.60)],
    }
    claims: dict[str, list[ScoredClaim]] = {}
    for _sector, stocks in tickers_by_sector.items():
        for ticker, confidence in stocks:
            claims[ticker] = [_make_scored_claim(ticker, final_confidence=confidence)]
    return claims


@pytest.fixture()
def stock_scores() -> dict[str, StockScore]:
    """Aggregated stock scores for 6 tickers."""
    scores_data = {
        "AAPL": (0.85, "Information Technology"),
        "MSFT": (0.75, "Information Technology"),
        "GOOGL": (0.45, "Information Technology"),
        "JPM": (0.80, "Financials"),
        "GS": (0.35, "Financials"),
        "JNJ": (0.60, "Health Care"),
    }
    return {
        ticker: StockScore(
            ticker=ticker,
            aggregate_score=score,
            claim_count=3,
            structural_weight=0.6,
        )
        for ticker, (score, _sector) in scores_data.items()
    }


@pytest.fixture()
def ranked_stocks() -> list[RankedStock]:
    """Ranked stocks for portfolio construction testing."""
    stocks = [
        ("AAPL", 0.85, "Information Technology", 1),
        ("MSFT", 0.75, "Information Technology", 2),
        ("GOOGL", 0.45, "Information Technology", 3),
        ("JPM", 0.80, "Financials", 1),
        ("GS", 0.35, "Financials", 2),
        ("JNJ", 0.60, "Health Care", 1),
    ]
    return [
        _make_ranked_stock(ticker, score, sector, rank)
        for ticker, score, sector, rank in stocks
    ]


@pytest.fixture()
def portfolio_result() -> PortfolioResult:
    """A minimal PortfolioResult with 3 holdings."""
    holdings = [
        PortfolioHolding(
            ticker="AAPL",
            weight=0.40,
            sector="Information Technology",
            score=0.85,
            rationale_summary="Sector rank 1, score 0.85",
        ),
        PortfolioHolding(
            ticker="JPM",
            weight=0.35,
            sector="Financials",
            score=0.80,
            rationale_summary="Sector rank 1, score 0.80",
        ),
        PortfolioHolding(
            ticker="JNJ",
            weight=0.25,
            sector="Health Care",
            score=0.60,
            rationale_summary="Sector rank 1, score 0.60",
        ),
    ]
    sector_allocations = [
        SectorAllocation(
            sector="Information Technology",
            benchmark_weight=0.40,
            actual_weight=0.40,
            stock_count=1,
        ),
        SectorAllocation(
            sector="Financials",
            benchmark_weight=0.35,
            actual_weight=0.35,
            stock_count=1,
        ),
        SectorAllocation(
            sector="Health Care",
            benchmark_weight=0.25,
            actual_weight=0.25,
            stock_count=1,
        ),
    ]
    return PortfolioResult(
        holdings=holdings,
        sector_allocations=sector_allocations,
        as_of_date=_AS_OF_DATE,
    )


@pytest.fixture()
def pseudo_portfolio_returns() -> "np.ndarray[Any, np.dtype[np.floating[Any]]]":
    """Pseudo portfolio daily returns (seed=42)."""
    rng = np.random.default_rng(_SEED_PORTFOLIO)
    return rng.normal(_PORTFOLIO_MU, _PORTFOLIO_SIGMA, _RETURN_DAYS)


@pytest.fixture()
def pseudo_benchmark_returns() -> "np.ndarray[Any, np.dtype[np.floating[Any]]]":
    """Pseudo benchmark daily returns (seed=100)."""
    rng = np.random.default_rng(_SEED_BENCHMARK)
    return rng.normal(_BENCHMARK_MU, _BENCHMARK_SIGMA, _RETURN_DAYS)


# ===========================================================================
# PortfolioBuilder.build_equal_weight() — End-to-End
# ===========================================================================
class TestBuildEqualWeightEndToEnd:
    """build_equal_weight() → PortfolioResult flow."""

    def test_正常系_閾値0_5で等ウェイトポートフォリオが構築できる(
        self,
        ranked_stocks: list[RankedStock],
        tmp_path: Path,
    ) -> None:
        """Stocks with aggregate_score > 0.5 are selected with equal weight."""
        builder = PortfolioBuilder()
        portfolio = builder.build_equal_weight(
            ranked=ranked_stocks,
            threshold=0.5,
            as_of_date=_AS_OF_DATE,
        )

        # AAPL (0.85), MSFT (0.75), JPM (0.80), JNJ (0.60) → 4 stocks
        selected_tickers = {h.ticker for h in portfolio.holdings}
        assert "AAPL" in selected_tickers
        assert "MSFT" in selected_tickers
        assert "JPM" in selected_tickers
        assert "JNJ" in selected_tickers
        # Excluded: GOOGL (0.45), GS (0.35)
        assert "GOOGL" not in selected_tickers
        assert "GS" not in selected_tickers

    def test_正常系_等ウェイトポートフォリオの全ウェイト合計が1_0である(
        self,
        ranked_stocks: list[RankedStock],
        tmp_path: Path,
    ) -> None:
        """Sum of all holdings weights equals 1.0."""
        builder = PortfolioBuilder()
        portfolio = builder.build_equal_weight(
            ranked=ranked_stocks,
            threshold=0.5,
            as_of_date=_AS_OF_DATE,
        )
        total_weight = sum(h.weight for h in portfolio.holdings)
        assert abs(total_weight - 1.0) < 1e-9

    def test_正常系_閾値より高いスコアの銘柄のみが選択される(
        self,
        ranked_stocks: list[RankedStock],
        tmp_path: Path,
    ) -> None:
        """Only stocks with aggregate_score > threshold are selected."""
        builder = PortfolioBuilder()

        for threshold in _THRESHOLDS:
            portfolio = builder.build_equal_weight(
                ranked=ranked_stocks,
                threshold=threshold,
                as_of_date=_AS_OF_DATE,
            )
            for holding in portfolio.holdings:
                # Find the original score for this ticker
                original_stock = next(
                    s for s in ranked_stocks if s["ticker"] == holding.ticker
                )
                assert original_stock["aggregate_score"] > threshold, (
                    f"Ticker {holding.ticker} with score "
                    f"{original_stock['aggregate_score']:.2f} should not be "
                    f"included at threshold {threshold}"
                )

    @pytest.mark.parametrize("threshold", _THRESHOLDS)
    def test_正常系_複数閾値で等ウェイトポートフォリオの全ウェイト合計が1_0である(
        self,
        threshold: float,
        ranked_stocks: list[RankedStock],
        tmp_path: Path,
    ) -> None:
        """Weight sum equals 1.0 for each threshold (parametrized)."""
        builder = PortfolioBuilder()
        portfolio = builder.build_equal_weight(
            ranked=ranked_stocks,
            threshold=threshold,
            as_of_date=_AS_OF_DATE,
        )
        if not portfolio.holdings:
            # Empty portfolio when threshold exceeds all scores
            assert portfolio.holdings == []
        else:
            total_weight = sum(h.weight for h in portfolio.holdings)
            assert abs(total_weight - 1.0) < 1e-9

    def test_正常系_閾値が全銘柄スコアを超える場合に空PortfolioResultが返る(
        self,
        ranked_stocks: list[RankedStock],
        tmp_path: Path,
    ) -> None:
        """Empty portfolio returned when threshold exceeds all scores."""
        builder = PortfolioBuilder()
        portfolio = builder.build_equal_weight(
            ranked=ranked_stocks,
            threshold=0.99,  # Above all scores
            as_of_date=_AS_OF_DATE,
        )
        assert portfolio.holdings == []

    def test_正常系_等ウェイトポートフォリオの各銘柄ウェイトが均等である(
        self,
        ranked_stocks: list[RankedStock],
        tmp_path: Path,
    ) -> None:
        """Each holding should have equal weight (1/N)."""
        builder = PortfolioBuilder()
        portfolio = builder.build_equal_weight(
            ranked=ranked_stocks,
            threshold=0.5,
            as_of_date=_AS_OF_DATE,
        )
        n = len(portfolio.holdings)
        assert n > 0
        expected_weight = 1.0 / n
        for holding in portfolio.holdings:
            assert abs(holding.weight - expected_weight) < 1e-9


# ===========================================================================
# StrategyEvaluator.evaluate() — mocked RiskCalculator
# ===========================================================================
class TestStrategyEvaluatorMocked:
    """StrategyEvaluator.evaluate() with mocked external calls."""

    def test_正常系_モック済みRiskCalculatorでevaluateが実行できる(
        self,
        portfolio_result: PortfolioResult,
        stock_scores: dict[str, StockScore],
        pseudo_portfolio_returns: "np.ndarray[Any, np.dtype[np.floating[Any]]]",
        pseudo_benchmark_returns: "np.ndarray[Any, np.dtype[np.floating[Any]]]",
        tmp_path: Path,
    ) -> None:
        """evaluate() returns EvaluationResult with mocked risk calculations."""
        import pandas as pd

        from dev.ca_strategy.evaluator import StrategyEvaluator

        portfolio_series = pd.Series(pseudo_portfolio_returns)
        benchmark_series = pd.Series(pseudo_benchmark_returns)

        with patch("dev.ca_strategy.evaluator.RiskCalculator") as mock_risk_calc_cls:
            mock_calc = MagicMock()
            mock_calc.sharpe_ratio.return_value = 0.85
            mock_calc.max_drawdown.return_value = -0.12
            mock_calc.beta.return_value = 0.95
            mock_calc.information_ratio.return_value = 0.40
            mock_risk_calc_cls.return_value = mock_calc

            evaluator = StrategyEvaluator()
            result = evaluator.evaluate(
                portfolio=portfolio_result,
                scores=stock_scores,
                portfolio_returns=portfolio_series,
                benchmark_returns=benchmark_series,
                analyst_scores={},
            )

        assert result is not None

    def test_正常系_EvaluationResultがパフォーマンス指標を含む(
        self,
        portfolio_result: PortfolioResult,
        stock_scores: dict[str, StockScore],
        pseudo_portfolio_returns: "np.ndarray[Any, np.dtype[np.floating[Any]]]",
        pseudo_benchmark_returns: "np.ndarray[Any, np.dtype[np.floating[Any]]]",
        tmp_path: Path,
    ) -> None:
        """EvaluationResult contains performance metrics."""
        import pandas as pd

        from dev.ca_strategy.evaluator import StrategyEvaluator
        from dev.ca_strategy.types import EvaluationResult

        portfolio_series = pd.Series(pseudo_portfolio_returns)
        benchmark_series = pd.Series(pseudo_benchmark_returns)

        with patch("dev.ca_strategy.evaluator.RiskCalculator") as mock_risk_calc_cls:
            mock_calc = MagicMock()
            mock_calc.sharpe_ratio.return_value = 0.85
            mock_calc.max_drawdown.return_value = -0.12
            mock_calc.beta.return_value = 0.95
            mock_calc.information_ratio.return_value = 0.40
            mock_risk_calc_cls.return_value = mock_calc

            evaluator = StrategyEvaluator()
            result = evaluator.evaluate(
                portfolio=portfolio_result,
                scores=stock_scores,
                portfolio_returns=portfolio_series,
                benchmark_returns=benchmark_series,
                analyst_scores={},
            )

        assert isinstance(result, EvaluationResult)
        assert result.performance is not None

    def test_正常系_アナリストスコアが全空の場合でもevaluateが成功する(
        self,
        portfolio_result: PortfolioResult,
        stock_scores: dict[str, StockScore],
        pseudo_portfolio_returns: "np.ndarray[Any, np.dtype[np.floating[Any]]]",
        pseudo_benchmark_returns: "np.ndarray[Any, np.dtype[np.floating[Any]]]",
        tmp_path: Path,
    ) -> None:
        """evaluate() handles empty analyst_scores without error."""
        import pandas as pd

        from dev.ca_strategy.evaluator import StrategyEvaluator

        portfolio_series = pd.Series(pseudo_portfolio_returns)
        benchmark_series = pd.Series(pseudo_benchmark_returns)

        with patch("dev.ca_strategy.evaluator.RiskCalculator") as mock_risk_calc_cls:
            mock_calc = MagicMock()
            mock_calc.sharpe_ratio.return_value = 0.50
            mock_calc.max_drawdown.return_value = -0.08
            mock_calc.beta.return_value = 1.02
            mock_calc.information_ratio.return_value = 0.20
            mock_risk_calc_cls.return_value = mock_calc

            evaluator = StrategyEvaluator()
            result = evaluator.evaluate(
                portfolio=portfolio_result,
                scores=stock_scores,
                portfolio_returns=portfolio_series,
                benchmark_returns=benchmark_series,
                analyst_scores={},  # No analyst scores
            )

        assert result is not None


# ===========================================================================
# OutputGenerator with evaluation — output file verification
# ===========================================================================
class TestOutputGeneratorWithEvaluation:
    """OutputGenerator.generate_all(evaluation=...) → file existence tests."""

    def test_正常系_評価なしでgenerate_allが既存ファイルを生成する(
        self,
        portfolio_result: PortfolioResult,
        scored_claims: dict[str, list[ScoredClaim]],
        stock_scores: dict[str, StockScore],
        tmp_path: Path,
    ) -> None:
        """generate_all() without evaluation creates standard output files."""
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=portfolio_result,
            claims=scored_claims,
            scores=stock_scores,
            output_dir=tmp_path,
        )

        assert (tmp_path / "portfolio_weights.json").exists()
        assert (tmp_path / "portfolio_weights.csv").exists()
        assert (tmp_path / "portfolio_summary.md").exists()

    def test_正常系_evaluation付きgenerate_allがevaluation_summaryを生成する(
        self,
        portfolio_result: PortfolioResult,
        scored_claims: dict[str, list[ScoredClaim]],
        stock_scores: dict[str, StockScore],
        tmp_path: Path,
    ) -> None:
        """generate_all() with evaluation creates evaluation_summary.md."""
        from dev.ca_strategy.types import (
            AnalystCorrelation,
            EvaluationResult,
            PerformanceMetrics,
            TransparencyMetrics,
        )

        mock_evaluation = EvaluationResult(
            threshold=0.5,
            portfolio_size=3,
            performance=PerformanceMetrics(
                sharpe_ratio=0.85,
                max_drawdown=-0.12,
                beta=0.95,
                information_ratio=0.40,
                cumulative_return=0.15,
            ),
            analyst_correlation=AnalystCorrelation(
                spearman_correlation=None,
                sample_size=0,
                p_value=None,
                hit_rate=None,
            ),
            transparency=TransparencyMetrics(
                mean_claim_count=3.0,
                mean_structural_weight=0.6,
                coverage_rate=1.0,
            ),
            as_of_date=_AS_OF_DATE,
        )

        gen = OutputGenerator()
        gen.generate_all(
            portfolio=portfolio_result,
            claims=scored_claims,
            scores=stock_scores,
            output_dir=tmp_path,
            evaluation=mock_evaluation,
        )

        assert (tmp_path / "evaluation_summary.md").exists()

    def test_正常系_evaluation付きgenerate_allがevaluation_results_jsonを生成する(
        self,
        portfolio_result: PortfolioResult,
        scored_claims: dict[str, list[ScoredClaim]],
        stock_scores: dict[str, StockScore],
        tmp_path: Path,
    ) -> None:
        """generate_all() with evaluation creates evaluation_results.json."""
        from dev.ca_strategy.types import (
            AnalystCorrelation,
            EvaluationResult,
            PerformanceMetrics,
            TransparencyMetrics,
        )

        mock_evaluation = EvaluationResult(
            threshold=0.5,
            portfolio_size=3,
            performance=PerformanceMetrics(
                sharpe_ratio=0.85,
                max_drawdown=-0.12,
                beta=0.95,
                information_ratio=0.40,
                cumulative_return=0.15,
            ),
            analyst_correlation=AnalystCorrelation(
                spearman_correlation=None,
                sample_size=0,
                p_value=None,
                hit_rate=None,
            ),
            transparency=TransparencyMetrics(
                mean_claim_count=3.0,
                mean_structural_weight=0.6,
                coverage_rate=1.0,
            ),
            as_of_date=_AS_OF_DATE,
        )

        gen = OutputGenerator()
        gen.generate_all(
            portfolio=portfolio_result,
            claims=scored_claims,
            scores=stock_scores,
            output_dir=tmp_path,
            evaluation=mock_evaluation,
        )

        assert (tmp_path / "evaluation_results.json").exists()

    def test_正常系_evaluation_results_jsonが有効なJSON構造を持つ(
        self,
        portfolio_result: PortfolioResult,
        scored_claims: dict[str, list[ScoredClaim]],
        stock_scores: dict[str, StockScore],
        tmp_path: Path,
    ) -> None:
        """evaluation_results.json contains required top-level keys."""
        from dev.ca_strategy.types import (
            AnalystCorrelation,
            EvaluationResult,
            PerformanceMetrics,
            TransparencyMetrics,
        )

        mock_evaluation = EvaluationResult(
            threshold=0.5,
            portfolio_size=3,
            performance=PerformanceMetrics(
                sharpe_ratio=0.85,
                max_drawdown=-0.12,
                beta=0.95,
                information_ratio=0.40,
                cumulative_return=0.15,
            ),
            analyst_correlation=AnalystCorrelation(
                spearman_correlation=None,
                sample_size=0,
                p_value=None,
                hit_rate=None,
            ),
            transparency=TransparencyMetrics(
                mean_claim_count=3.0,
                mean_structural_weight=0.6,
                coverage_rate=1.0,
            ),
            as_of_date=_AS_OF_DATE,
        )

        gen = OutputGenerator()
        gen.generate_all(
            portfolio=portfolio_result,
            claims=scored_claims,
            scores=stock_scores,
            output_dir=tmp_path,
            evaluation=mock_evaluation,
        )

        results_path = tmp_path / "evaluation_results.json"
        data = json.loads(results_path.read_text(encoding="utf-8"))

        assert "threshold" in data
        assert "portfolio_size" in data
        assert "performance" in data

    def test_正常系_evaluation_Noneで後方互換性が維持される(
        self,
        portfolio_result: PortfolioResult,
        scored_claims: dict[str, list[ScoredClaim]],
        stock_scores: dict[str, StockScore],
        tmp_path: Path,
    ) -> None:
        """generate_all(evaluation=None) behaves identically to no evaluation."""
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=portfolio_result,
            claims=scored_claims,
            scores=stock_scores,
            output_dir=tmp_path,
            evaluation=None,
        )

        # Standard files should exist
        assert (tmp_path / "portfolio_weights.json").exists()
        assert (tmp_path / "portfolio_summary.md").exists()

        # Evaluation files should NOT be generated
        assert not (tmp_path / "evaluation_summary.md").exists()
        assert not (tmp_path / "evaluation_results.json").exists()


# ===========================================================================
# Full pipeline integration — build_equal_weight → evaluate → generate_all
# ===========================================================================
class TestFullEvaluationPipeline:
    """End-to-End: build_equal_weight() → evaluate() → generate_all()."""

    @pytest.mark.parametrize("threshold", _THRESHOLDS)
    def test_正常系_複数閾値でエンドツーエンドパイプラインが成功する(
        self,
        threshold: float,
        ranked_stocks: list[RankedStock],
        scored_claims: dict[str, list[ScoredClaim]],
        stock_scores: dict[str, StockScore],
        tmp_path: Path,
    ) -> None:
        """Full pipeline runs successfully for each threshold."""
        import pandas as pd

        from dev.ca_strategy.evaluator import StrategyEvaluator
        from dev.ca_strategy.types import (
            AnalystCorrelation,
            EvaluationResult,
            PerformanceMetrics,
            TransparencyMetrics,
        )

        rng_p = np.random.default_rng(_SEED_PORTFOLIO)
        rng_b = np.random.default_rng(_SEED_BENCHMARK)
        portfolio_returns = pd.Series(
            rng_p.normal(_PORTFOLIO_MU, _PORTFOLIO_SIGMA, _RETURN_DAYS)
        )
        benchmark_returns = pd.Series(
            rng_b.normal(_BENCHMARK_MU, _BENCHMARK_SIGMA, _RETURN_DAYS)
        )

        # Step 1: build_equal_weight
        builder = PortfolioBuilder()
        portfolio = builder.build_equal_weight(
            ranked=ranked_stocks,
            threshold=threshold,
            as_of_date=_AS_OF_DATE,
        )

        # When all scores are below threshold, skip evaluation
        if not portfolio.holdings:
            return

        # Step 2: evaluate (mocked RiskCalculator)
        with patch("dev.ca_strategy.evaluator.RiskCalculator") as mock_risk_calc_cls:
            mock_calc = MagicMock()
            mock_calc.sharpe_ratio.return_value = 0.85
            mock_calc.max_drawdown.return_value = -0.12
            mock_calc.beta.return_value = 0.95
            mock_calc.information_ratio.return_value = 0.40
            mock_risk_calc_cls.return_value = mock_calc

            evaluator = StrategyEvaluator()
            evaluation = evaluator.evaluate(
                portfolio=portfolio,
                scores=stock_scores,
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
                analyst_scores={},
            )

        # Step 3: generate_all with evaluation
        output_dir = tmp_path / f"threshold_{threshold:.1f}"
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=portfolio,
            claims=scored_claims,
            scores=stock_scores,
            output_dir=output_dir,
            evaluation=evaluation,
        )

        # Verify output files exist
        assert (output_dir / "portfolio_weights.json").exists()
        assert (output_dir / "portfolio_summary.md").exists()
        assert (output_dir / "evaluation_summary.md").exists()
        assert (output_dir / "evaluation_results.json").exists()

    def test_正常系_閾値0_3で出力ファイルが正しく生成される(
        self,
        ranked_stocks: list[RankedStock],
        scored_claims: dict[str, list[ScoredClaim]],
        stock_scores: dict[str, StockScore],
        tmp_path: Path,
    ) -> None:
        """Threshold 0.3: output files include evaluation sections."""
        import pandas as pd

        from dev.ca_strategy.evaluator import StrategyEvaluator

        rng_p = np.random.default_rng(_SEED_PORTFOLIO)
        rng_b = np.random.default_rng(_SEED_BENCHMARK)
        portfolio_returns = pd.Series(
            rng_p.normal(_PORTFOLIO_MU, _PORTFOLIO_SIGMA, _RETURN_DAYS)
        )
        benchmark_returns = pd.Series(
            rng_b.normal(_BENCHMARK_MU, _BENCHMARK_SIGMA, _RETURN_DAYS)
        )

        builder = PortfolioBuilder()
        portfolio = builder.build_equal_weight(
            ranked=ranked_stocks,
            threshold=0.3,
            as_of_date=_AS_OF_DATE,
        )
        assert len(portfolio.holdings) > 0

        with patch("dev.ca_strategy.evaluator.RiskCalculator") as mock_risk_calc_cls:
            mock_calc = MagicMock()
            mock_calc.sharpe_ratio.return_value = 0.70
            mock_calc.max_drawdown.return_value = -0.15
            mock_calc.beta.return_value = 1.00
            mock_calc.information_ratio.return_value = 0.30
            mock_risk_calc_cls.return_value = mock_calc

            evaluator = StrategyEvaluator()
            evaluation = evaluator.evaluate(
                portfolio=portfolio,
                scores=stock_scores,
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
                analyst_scores={},
                threshold=0.3,
            )

        output_dir = tmp_path / "threshold_0.3"
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=portfolio,
            claims=scored_claims,
            scores=stock_scores,
            output_dir=output_dir,
            evaluation=evaluation,
        )

        # Verify evaluation_results.json contains threshold field
        results = json.loads(
            (output_dir / "evaluation_results.json").read_text(encoding="utf-8")
        )
        assert results["threshold"] == pytest.approx(0.3, rel=1e-3)

    def test_正常系_evaluation_summary_mdがパフォーマンスセクションを含む(
        self,
        ranked_stocks: list[RankedStock],
        scored_claims: dict[str, list[ScoredClaim]],
        stock_scores: dict[str, StockScore],
        tmp_path: Path,
    ) -> None:
        """evaluation_summary.md contains performance section."""
        import pandas as pd

        from dev.ca_strategy.evaluator import StrategyEvaluator

        rng_p = np.random.default_rng(_SEED_PORTFOLIO)
        rng_b = np.random.default_rng(_SEED_BENCHMARK)
        portfolio_returns = pd.Series(
            rng_p.normal(_PORTFOLIO_MU, _PORTFOLIO_SIGMA, _RETURN_DAYS)
        )
        benchmark_returns = pd.Series(
            rng_b.normal(_BENCHMARK_MU, _BENCHMARK_SIGMA, _RETURN_DAYS)
        )

        builder = PortfolioBuilder()
        portfolio = builder.build_equal_weight(
            ranked=ranked_stocks,
            threshold=0.5,
            as_of_date=_AS_OF_DATE,
        )
        assert len(portfolio.holdings) > 0

        with patch("dev.ca_strategy.evaluator.RiskCalculator") as mock_risk_calc_cls:
            mock_calc = MagicMock()
            mock_calc.sharpe_ratio.return_value = 0.85
            mock_calc.max_drawdown.return_value = -0.12
            mock_calc.beta.return_value = 0.95
            mock_calc.information_ratio.return_value = 0.40
            mock_risk_calc_cls.return_value = mock_calc

            evaluator = StrategyEvaluator()
            evaluation = evaluator.evaluate(
                portfolio=portfolio,
                scores=stock_scores,
                portfolio_returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
                analyst_scores={},
            )

        output_dir = tmp_path / "threshold_0.5"
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=portfolio,
            claims=scored_claims,
            scores=stock_scores,
            output_dir=output_dir,
            evaluation=evaluation,
        )

        summary_text = (output_dir / "evaluation_summary.md").read_text(
            encoding="utf-8"
        )
        # Should contain performance-related content
        assert (
            "Performance" in summary_text
            or "Sharpe" in summary_text
            or "performance" in summary_text
        )
