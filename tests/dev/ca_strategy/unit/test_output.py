"""Tests for ca_strategy output module.

OutputGenerator produces portfolio output files:
- portfolio_weights.json: Holdings, sector allocation, data sources
- portfolio_weights.csv: Excel-viewable format
- portfolio_summary.md: Sector allocation table, selection criteria
- rationale/{TICKER}_rationale.md: Per-stock rationale files
- evaluation_summary.md: Performance, analyst correlation, transparency (when evaluation is provided)
- evaluation_results.json: Structured evaluation data (when evaluation is provided)
"""

from __future__ import annotations

import csv
import json
from datetime import date
from typing import TYPE_CHECKING

import pytest

from dev.ca_strategy.output import OutputGenerator
from dev.ca_strategy.types import (
    AnalystCorrelation,
    BenchmarkWeight,
    ConfidenceAdjustment,
    EvaluationResult,
    PerformanceMetrics,
    PortfolioHolding,
    PortfolioResult,
    RuleEvaluation,
    ScoredClaim,
    SectorAllocation,
    StockScore,
    TransparencyMetrics,
)

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_holdings() -> list[PortfolioHolding]:
    """Create sample portfolio holdings."""
    return [
        PortfolioHolding(
            ticker="AAPL",
            weight=0.25,
            sector="Information Technology",
            score=0.9,
            rationale_summary="Strong competitive advantage in ecosystem",
        ),
        PortfolioHolding(
            ticker="MSFT",
            weight=0.15,
            sector="Information Technology",
            score=0.8,
            rationale_summary="Cloud platform dominance",
        ),
        PortfolioHolding(
            ticker="JPM",
            weight=0.30,
            sector="Financials",
            score=0.85,
            rationale_summary="Leading banking franchise",
        ),
        PortfolioHolding(
            ticker="JNJ",
            weight=0.30,
            sector="Health Care",
            score=0.88,
            rationale_summary="Diversified health care portfolio",
        ),
    ]


def _make_sector_allocations() -> list[SectorAllocation]:
    """Create sample sector allocations."""
    return [
        SectorAllocation(
            sector="Information Technology",
            benchmark_weight=0.40,
            actual_weight=0.40,
            stock_count=2,
        ),
        SectorAllocation(
            sector="Financials",
            benchmark_weight=0.30,
            actual_weight=0.30,
            stock_count=1,
        ),
        SectorAllocation(
            sector="Health Care",
            benchmark_weight=0.30,
            actual_weight=0.30,
            stock_count=1,
        ),
    ]


def _make_scored_claims() -> dict[str, list[ScoredClaim]]:
    """Create sample scored claims per ticker."""
    rule_eval = RuleEvaluation(
        applied_rules=["rule_6"],
        results={"rule_6": True},
        confidence=0.8,
        adjustments=[],
    )
    return {
        "AAPL": [
            ScoredClaim(
                id="AAPL-CA-001",
                claim_type="competitive_advantage",
                claim="Apple has a strong ecosystem lock-in",
                evidence="iPhone + Mac + Services integration",
                rule_evaluation=rule_eval,
                final_confidence=0.9,
                adjustments=[
                    ConfidenceAdjustment(
                        source="pattern_I",
                        adjustment=0.1,
                        reasoning="Network effects present",
                    )
                ],
            )
        ],
        "MSFT": [
            ScoredClaim(
                id="MSFT-CA-001",
                claim_type="competitive_advantage",
                claim="Azure cloud platform growth",
                evidence="Enterprise cloud market share gains",
                rule_evaluation=rule_eval,
                final_confidence=0.8,
                adjustments=[],
            )
        ],
        "JPM": [
            ScoredClaim(
                id="JPM-CA-001",
                claim_type="competitive_advantage",
                claim="Scale advantage in banking",
                evidence="Largest US bank by assets",
                rule_evaluation=rule_eval,
                final_confidence=0.85,
                adjustments=[],
            )
        ],
        "JNJ": [
            ScoredClaim(
                id="JNJ-CA-001",
                claim_type="competitive_advantage",
                claim="Diversified portfolio across pharma/devices/consumer",
                evidence="Three business segments with leading positions",
                rule_evaluation=rule_eval,
                final_confidence=0.88,
                adjustments=[],
            )
        ],
    }


def _make_stock_scores() -> dict[str, StockScore]:
    """Create sample stock scores."""
    return {
        "AAPL": StockScore(
            ticker="AAPL",
            aggregate_score=0.9,
            claim_count=3,
            structural_weight=0.6,
        ),
        "MSFT": StockScore(
            ticker="MSFT",
            aggregate_score=0.8,
            claim_count=2,
            structural_weight=0.5,
        ),
        "JPM": StockScore(
            ticker="JPM",
            aggregate_score=0.85,
            claim_count=2,
            structural_weight=0.4,
        ),
        "JNJ": StockScore(
            ticker="JNJ",
            aggregate_score=0.88,
            claim_count=3,
            structural_weight=0.5,
        ),
    }


def _make_portfolio_result() -> PortfolioResult:
    """Create a complete portfolio result."""
    return PortfolioResult(
        holdings=_make_holdings(),
        sector_allocations=_make_sector_allocations(),
        as_of_date=date(2015, 9, 30),
    )


# ===========================================================================
# OutputGenerator
# ===========================================================================
class TestOutputGenerator:
    """OutputGenerator class tests."""

    # -----------------------------------------------------------------------
    # Instantiation
    # -----------------------------------------------------------------------
    def test_正常系_インスタンスを作成できる(self) -> None:
        gen = OutputGenerator()
        assert isinstance(gen, OutputGenerator)

    # -----------------------------------------------------------------------
    # generate_all – file creation
    # -----------------------------------------------------------------------
    def test_正常系_portfolio_weights_jsonが生成される(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        json_path = tmp_path / "portfolio_weights.json"
        assert json_path.exists()

    def test_正常系_portfolio_weights_csvが生成される(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        csv_path = tmp_path / "portfolio_weights.csv"
        assert csv_path.exists()

    def test_正常系_portfolio_summary_mdが生成される(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        md_path = tmp_path / "portfolio_summary.md"
        assert md_path.exists()

    def test_正常系_各銘柄のrationale_mdが生成される(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        rationale_dir = tmp_path / "rationale"
        assert rationale_dir.exists()
        for h in _make_holdings():
            rationale_file = rationale_dir / f"{h.ticker}_rationale.md"
            assert rationale_file.exists(), f"Missing rationale for {h.ticker}"

    # -----------------------------------------------------------------------
    # portfolio_weights.json structure
    # -----------------------------------------------------------------------
    def test_正常系_jsonにholdingsが含まれる(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        data = json.loads((tmp_path / "portfolio_weights.json").read_text())
        assert "holdings" in data
        assert len(data["holdings"]) == 4

    def test_正常系_jsonにsector_allocationが含まれる(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        data = json.loads((tmp_path / "portfolio_weights.json").read_text())
        assert "sector_allocation" in data
        assert len(data["sector_allocation"]) == 3

    def test_正常系_jsonにdata_sourcesが含まれる(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        data = json.loads((tmp_path / "portfolio_weights.json").read_text())
        assert "data_sources" in data

    def test_正常系_json_holdingsに必須フィールドが含まれる(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        data = json.loads((tmp_path / "portfolio_weights.json").read_text())
        for holding in data["holdings"]:
            assert "ticker" in holding
            assert "weight" in holding
            assert "sector" in holding
            assert "score" in holding

    # -----------------------------------------------------------------------
    # portfolio_weights.csv structure
    # -----------------------------------------------------------------------
    def test_正常系_csvが有効なCSV形式である(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        csv_path = tmp_path / "portfolio_weights.csv"
        with csv_path.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 4
            for row in rows:
                assert "ticker" in row
                assert "weight" in row

    # -----------------------------------------------------------------------
    # portfolio_summary.md content
    # -----------------------------------------------------------------------
    def test_正常系_summaryにセクター配分表が含まれる(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        content = (tmp_path / "portfolio_summary.md").read_text()
        assert "Information Technology" in content
        assert "Financials" in content
        assert "Health Care" in content

    def test_正常系_summaryに銘柄数が含まれる(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        content = (tmp_path / "portfolio_summary.md").read_text()
        # Should mention total holdings count
        assert "4" in content

    # -----------------------------------------------------------------------
    # rationale file content
    # -----------------------------------------------------------------------
    def test_正常系_rationaleにCA評価が含まれる(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        aapl_rationale = (tmp_path / "rationale" / "AAPL_rationale.md").read_text()
        # Should mention the claim or competitive advantage
        assert "AAPL" in aapl_rationale
        assert (
            "competitive" in aapl_rationale.lower()
            or "ecosystem" in aapl_rationale.lower()
        )

    def test_正常系_rationaleにスコア情報が含まれる(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        aapl_rationale = (tmp_path / "rationale" / "AAPL_rationale.md").read_text()
        assert "0.9" in aapl_rationale

    # -----------------------------------------------------------------------
    # Edge cases
    # -----------------------------------------------------------------------
    def test_エッジケース_空のポートフォリオでも出力される(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=PortfolioResult(
                holdings=[],
                sector_allocations=[],
                as_of_date=date(2015, 9, 30),
            ),
            claims={},
            scores={},
            output_dir=tmp_path,
        )

        assert (tmp_path / "portfolio_weights.json").exists()
        assert (tmp_path / "portfolio_weights.csv").exists()
        assert (tmp_path / "portfolio_summary.md").exists()

    def test_正常系_出力ディレクトリが存在しなくても自動作成される(
        self, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "nested" / "output"
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=output_dir,
        )

        assert (output_dir / "portfolio_weights.json").exists()

    def test_正常系_claimsに含まれない銘柄でもrationale生成される(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        # Remove JNJ from claims but keep in holdings
        claims = _make_scored_claims()
        del claims["JNJ"]

        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=claims,
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        # JNJ rationale should still exist (with limited info)
        jnj_path = tmp_path / "rationale" / "JNJ_rationale.md"
        assert jnj_path.exists()


# ---------------------------------------------------------------------------
# Helpers for evaluation tests
# ---------------------------------------------------------------------------
def _make_evaluation_result() -> EvaluationResult:
    """Create a sample EvaluationResult for testing."""
    return EvaluationResult(
        threshold=0.5,
        portfolio_size=10,
        performance=PerformanceMetrics(
            sharpe_ratio=1.2,
            max_drawdown=-0.15,
            beta=0.95,
            information_ratio=0.8,
            cumulative_return=0.25,
        ),
        analyst_correlation=AnalystCorrelation(
            spearman_correlation=0.6,
            sample_size=8,
            p_value=0.05,
            hit_rate=0.7,
        ),
        transparency=TransparencyMetrics(
            mean_claim_count=3.5,
            mean_structural_weight=0.65,
            coverage_rate=0.9,
        ),
        as_of_date=date(2015, 9, 30),
    )


def _make_evaluation_result_no_analyst() -> EvaluationResult:
    """Create an EvaluationResult with insufficient analyst data."""
    return EvaluationResult(
        threshold=0.7,
        portfolio_size=5,
        performance=PerformanceMetrics(
            sharpe_ratio=0.8,
            max_drawdown=-0.10,
            beta=1.05,
            information_ratio=0.4,
            cumulative_return=0.12,
        ),
        analyst_correlation=AnalystCorrelation(
            spearman_correlation=None,
            sample_size=1,
            p_value=None,
            hit_rate=None,
        ),
        transparency=TransparencyMetrics(
            mean_claim_count=2.0,
            mean_structural_weight=0.5,
            coverage_rate=1.0,
        ),
        as_of_date=date(2015, 9, 30),
    )


# ===========================================================================
# TestEvaluationOutput
# ===========================================================================
class TestEvaluationOutput:
    """Tests for evaluation output: evaluation_summary.md and evaluation_results.json."""

    # -----------------------------------------------------------------------
    # evaluation=None の後方互換性
    # -----------------------------------------------------------------------
    def test_正常系_evaluationなしで既存4ファイルが生成される(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        assert (tmp_path / "portfolio_weights.json").exists()
        assert (tmp_path / "portfolio_weights.csv").exists()
        assert (tmp_path / "portfolio_summary.md").exists()
        assert (tmp_path / "rationale").exists()

    def test_正常系_evaluationなしでevaluation_summaryは生成されない(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        assert not (tmp_path / "evaluation_summary.md").exists()

    def test_正常系_evaluationなしでevaluation_resultsは生成されない(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
        )

        assert not (tmp_path / "evaluation_results.json").exists()

    # -----------------------------------------------------------------------
    # evaluation_summary.md の生成
    # -----------------------------------------------------------------------
    def test_正常系_evaluationありでevaluation_summary_mdが生成される(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result(),
        )

        assert (tmp_path / "evaluation_summary.md").exists()

    def test_正常系_evaluation_summaryにパフォーマンスセクションが含まれる(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result(),
        )

        content = (tmp_path / "evaluation_summary.md").read_text()
        assert "Sharpe Ratio" in content
        assert "Max Drawdown" in content
        assert "Beta" in content
        assert "Information Ratio" in content

    def test_正常系_evaluation_summaryにアナリスト相関セクションが含まれる(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result(),
        )

        content = (tmp_path / "evaluation_summary.md").read_text()
        assert "Analyst Correlation" in content
        assert "Sample Size" in content

    def test_正常系_evaluation_summaryに透明性セクションが含まれる(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result(),
        )

        content = (tmp_path / "evaluation_summary.md").read_text()
        assert "Transparency" in content
        assert "Mean Claim Count" in content
        assert "Coverage Rate" in content

    def test_正常系_evaluation_summaryにthresholdが含まれる(
        self, tmp_path: Path
    ) -> None:
        eval_result = _make_evaluation_result()
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=eval_result,
        )

        content = (tmp_path / "evaluation_summary.md").read_text()
        assert str(eval_result.threshold) in content

    def test_正常系_アナリストデータ不足時にNA表示される(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result_no_analyst(),
        )

        content = (tmp_path / "evaluation_summary.md").read_text()
        assert "N/A" in content

    # -----------------------------------------------------------------------
    # evaluation_results.json の生成
    # -----------------------------------------------------------------------
    def test_正常系_evaluationありでevaluation_results_jsonが生成される(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result(),
        )

        assert (tmp_path / "evaluation_results.json").exists()

    def test_正常系_evaluation_resultsのJSON構造が正しい(self, tmp_path: Path) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result(),
        )

        data = json.loads((tmp_path / "evaluation_results.json").read_text())
        assert "threshold" in data
        assert "portfolio_size" in data
        assert "performance" in data
        assert "analyst_correlation" in data
        assert "transparency" in data

    def test_正常系_evaluation_resultsのperformanceフィールドが正しい(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        eval_result = _make_evaluation_result()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=eval_result,
        )

        data = json.loads((tmp_path / "evaluation_results.json").read_text())
        perf = data["performance"]
        assert "sharpe_ratio" in perf
        assert "max_drawdown" in perf
        assert "beta" in perf
        assert "information_ratio" in perf
        assert "cumulative_return" in perf

    def test_正常系_evaluation_resultsのthresholdが正確に記録される(
        self, tmp_path: Path
    ) -> None:
        eval_result = _make_evaluation_result()
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=eval_result,
        )

        data = json.loads((tmp_path / "evaluation_results.json").read_text())
        assert data["threshold"] == eval_result.threshold
        assert data["portfolio_size"] == eval_result.portfolio_size

    def test_正常系_アナリストデータ不足時にNullが記録される(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result_no_analyst(),
        )

        data = json.loads((tmp_path / "evaluation_results.json").read_text())
        corr = data["analyst_correlation"]
        assert corr["spearman_correlation"] is None
        assert corr["p_value"] is None
        assert corr["hit_rate"] is None

    def test_正常系_evaluationありで既存4ファイルも生成される(
        self, tmp_path: Path
    ) -> None:
        gen = OutputGenerator()
        gen.generate_all(
            portfolio=_make_portfolio_result(),
            claims=_make_scored_claims(),
            scores=_make_stock_scores(),
            output_dir=tmp_path,
            evaluation=_make_evaluation_result(),
        )

        # All standard files must still exist
        assert (tmp_path / "portfolio_weights.json").exists()
        assert (tmp_path / "portfolio_weights.csv").exists()
        assert (tmp_path / "portfolio_summary.md").exists()
        assert (tmp_path / "rationale").exists()
        # Plus evaluation files
        assert (tmp_path / "evaluation_summary.md").exists()
        assert (tmp_path / "evaluation_results.json").exists()
