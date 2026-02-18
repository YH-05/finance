"""Tests for ca_strategy orchestrator module.

Orchestrator integrates Phase 1-5 of the CA Strategy pipeline:
1. Extraction: Transcript -> Claims (via ClaimExtractor)
2. Scoring: Claims -> ScoredClaims (via ClaimScorer)
3. Neutralization: Scores -> Ranked DataFrame (via ScoreAggregator + SectorNeutralizer)
4. Portfolio Construction: Ranked -> Portfolio (via PortfolioBuilder)
5. Output Generation: Portfolio -> Files (via OutputGenerator)

All tests use mocks to avoid LLM API calls and external dependencies.
"""

from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from dev.ca_strategy._config import ConfigRepository
from dev.ca_strategy.orchestrator import Orchestrator
from dev.ca_strategy.types import (
    BenchmarkWeight,
    Claim,
    ConfidenceAdjustment,
    PortfolioHolding,
    PortfolioResult,
    RuleEvaluation,
    ScoredClaim,
    SectorAllocation,
    StockScore,
    UniverseConfig,
    UniverseTicker,
)

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def config_dir(tmp_path: Path) -> Path:
    """Create config directory with universe.json and benchmark_weights.json."""
    config = tmp_path / "config"
    config.mkdir()

    universe_data = {
        "tickers": [
            {"ticker": "AAPL", "gics_sector": "Information Technology"},
            {"ticker": "MSFT", "gics_sector": "Information Technology"},
            {"ticker": "JPM", "gics_sector": "Financials"},
        ]
    }
    (config / "universe.json").write_text(
        json.dumps(universe_data, ensure_ascii=False, indent=2)
    )

    benchmark_data = {
        "weights": {
            "Information Technology": 0.60,
            "Financials": 0.40,
        }
    }
    (config / "benchmark_weights.json").write_text(
        json.dumps(benchmark_data, ensure_ascii=False, indent=2)
    )

    return config


@pytest.fixture()
def kb_base_dir(tmp_path: Path) -> Path:
    """Create KB base directory structure."""
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "kb1_rules_transcript").mkdir()
    (kb / "kb2_patterns_transcript").mkdir()
    (kb / "kb3_fewshot_transcript").mkdir()
    (kb / "system_prompt_transcript.md").write_text("system prompt")
    (kb / "dogma.md").write_text("dogma content")
    return kb


@pytest.fixture()
def workspace_dir(tmp_path: Path) -> Path:
    """Create workspace directory."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture()
def orchestrator(
    config_dir: Path,
    kb_base_dir: Path,
    workspace_dir: Path,
) -> Orchestrator:
    """Create an Orchestrator instance with test directories."""
    return Orchestrator(
        config_path=config_dir,
        kb_base_dir=kb_base_dir,
        workspace_dir=workspace_dir,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_rule_evaluation() -> RuleEvaluation:
    """Create a RuleEvaluation with defaults."""
    return RuleEvaluation(
        applied_rules=["rule_6"],
        results={"rule_6": True},
        confidence=0.8,
        adjustments=[],
    )


def _make_claims() -> dict[str, list[Claim]]:
    """Create sample claims for testing."""
    rule_eval = _make_rule_evaluation()
    return {
        "AAPL": [
            Claim(
                id="AAPL-CA-001",
                claim_type="competitive_advantage",
                claim="Strong ecosystem",
                evidence="iPhone + Mac + Services",
                rule_evaluation=rule_eval,
            )
        ],
        "JPM": [
            Claim(
                id="JPM-CA-001",
                claim_type="competitive_advantage",
                claim="Scale advantage",
                evidence="Largest US bank",
                rule_evaluation=rule_eval,
            )
        ],
    }


def _make_scored_claims() -> dict[str, list[ScoredClaim]]:
    """Create sample scored claims for testing."""
    rule_eval = _make_rule_evaluation()
    return {
        "AAPL": [
            ScoredClaim(
                id="AAPL-CA-001",
                claim_type="competitive_advantage",
                claim="Strong ecosystem",
                evidence="iPhone + Mac + Services",
                rule_evaluation=rule_eval,
                final_confidence=0.85,
                adjustments=[
                    ConfidenceAdjustment(
                        source="pattern_I",
                        adjustment=0.1,
                        reasoning="Network effects",
                    )
                ],
            )
        ],
        "JPM": [
            ScoredClaim(
                id="JPM-CA-001",
                claim_type="competitive_advantage",
                claim="Scale advantage",
                evidence="Largest US bank",
                rule_evaluation=rule_eval,
                final_confidence=0.7,
                adjustments=[],
            )
        ],
    }


def _make_stock_scores() -> dict[str, StockScore]:
    """Create sample stock scores."""
    return {
        "AAPL": StockScore(
            ticker="AAPL",
            aggregate_score=0.85,
            claim_count=1,
            structural_weight=0.5,
        ),
        "JPM": StockScore(
            ticker="JPM",
            aggregate_score=0.7,
            claim_count=1,
            structural_weight=0.4,
        ),
    }


def _make_ranked_df() -> pd.DataFrame:
    """Create a sample ranked DataFrame."""
    return pd.DataFrame(
        {
            "ticker": ["AAPL", "JPM"],
            "aggregate_score": [0.85, 0.7],
            "gics_sector": ["Information Technology", "Financials"],
            "sector_zscore": [1.0, 0.5],
            "sector_rank": [1, 1],
            "as_of_date": [date(2015, 9, 30), date(2015, 9, 30)],
            "claim_count": [1, 1],
            "structural_weight": [0.5, 0.4],
        }
    )


def _make_portfolio_result() -> PortfolioResult:
    """Create sample portfolio result."""
    return PortfolioResult(
        holdings=[
            PortfolioHolding(
                ticker="AAPL",
                weight=0.6,
                sector="Information Technology",
                score=0.85,
                rationale_summary="Sector rank 1, score 0.85",
            ),
            PortfolioHolding(
                ticker="JPM",
                weight=0.4,
                sector="Financials",
                score=0.7,
                rationale_summary="Sector rank 1, score 0.70",
            ),
        ],
        sector_allocations=[
            SectorAllocation(
                sector="Information Technology",
                benchmark_weight=0.6,
                actual_weight=0.6,
                stock_count=1,
            ),
            SectorAllocation(
                sector="Financials",
                benchmark_weight=0.4,
                actual_weight=0.4,
                stock_count=1,
            ),
        ],
        as_of_date=date(2015, 9, 30),
    )


# ===========================================================================
# Orchestrator initialization
# ===========================================================================
class TestOrchestratorInit:
    """Orchestrator initialization tests."""

    def test_正常系_有効なパスでインスタンスを作成できる(
        self,
        config_dir: Path,
        kb_base_dir: Path,
        workspace_dir: Path,
    ) -> None:
        orch = Orchestrator(
            config_path=config_dir,
            kb_base_dir=kb_base_dir,
            workspace_dir=workspace_dir,
        )
        assert orch is not None

    def test_正常系_str型のパスでもインスタンスを作成できる(
        self,
        config_dir: Path,
        kb_base_dir: Path,
        workspace_dir: Path,
    ) -> None:
        orch = Orchestrator(
            config_path=str(config_dir),
            kb_base_dir=str(kb_base_dir),
            workspace_dir=str(workspace_dir),
        )
        assert orch is not None

    def test_異常系_config_pathが存在しない場合FileNotFoundError(
        self,
        kb_base_dir: Path,
        workspace_dir: Path,
        tmp_path: Path,
    ) -> None:
        with pytest.raises(FileNotFoundError, match="config_path"):
            Orchestrator(
                config_path=tmp_path / "nonexistent",
                kb_base_dir=kb_base_dir,
                workspace_dir=workspace_dir,
            )


# ===========================================================================
# ConfigRepository
# ===========================================================================
class TestConfigRepository:
    """ConfigRepository loading tests."""

    def test_正常系_universe_jsonを読み込める(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        universe = orchestrator._config.universe
        assert isinstance(universe, UniverseConfig)
        assert len(universe.tickers) == 3

    def test_正常系_benchmark_weights_jsonを読み込める(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        benchmark = orchestrator._config.benchmark
        assert isinstance(benchmark, list)
        assert len(benchmark) == 2
        assert all(isinstance(bw, BenchmarkWeight) for bw in benchmark)

    def test_正常系_universeのticker情報が正しい(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        universe = orchestrator._config.universe
        tickers = {t.ticker for t in universe.tickers}
        assert tickers == {"AAPL", "MSFT", "JPM"}

    def test_正常系_benchmark_weightsが合計1になる(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        benchmark = orchestrator._config.benchmark
        total = sum(bw.weight for bw in benchmark)
        assert abs(total - 1.0) < 1e-10

    def test_異常系_universe_jsonが存在しない場合FileNotFoundError(
        self,
        config_dir: Path,
    ) -> None:
        (config_dir / "universe.json").unlink()
        repo = ConfigRepository(config_dir)
        with pytest.raises(FileNotFoundError, match=r"universe\.json"):
            _ = repo.universe

    def test_異常系_benchmark_weights_jsonが存在しない場合FileNotFoundError(
        self,
        config_dir: Path,
    ) -> None:
        (config_dir / "benchmark_weights.json").unlink()
        repo = ConfigRepository(config_dir)
        with pytest.raises(FileNotFoundError, match=r"benchmark_weights\.json"):
            _ = repo.benchmark


# ===========================================================================
# _save_execution_log
# ===========================================================================
class TestSaveExecutionLog:
    """Execution log persistence tests."""

    def test_正常系_execution_log_jsonが作成される(
        self,
        orchestrator: Orchestrator,
        workspace_dir: Path,
    ) -> None:
        orchestrator._save_execution_log(
            phase="phase1",
            status="completed",
            error=None,
        )
        log_path = workspace_dir / "execution_log.json"
        assert log_path.exists()

    def test_正常系_ログにphase情報が含まれる(
        self,
        orchestrator: Orchestrator,
        workspace_dir: Path,
    ) -> None:
        orchestrator._save_execution_log(
            phase="phase1",
            status="completed",
            error=None,
        )
        log_path = workspace_dir / "execution_log.json"
        data = json.loads(log_path.read_text())
        assert any(entry["phase"] == "phase1" for entry in data["phases"])

    def test_正常系_エラー情報がログに記録される(
        self,
        orchestrator: Orchestrator,
        workspace_dir: Path,
    ) -> None:
        orchestrator._save_execution_log(
            phase="phase2",
            status="failed",
            error="API timeout",
        )
        log_path = workspace_dir / "execution_log.json"
        data = json.loads(log_path.read_text())
        phase_entry = next(e for e in data["phases"] if e["phase"] == "phase2")
        assert phase_entry["status"] == "failed"
        assert phase_entry["error"] == "API timeout"

    def test_正常系_複数Phase分のログが蓄積される(
        self,
        orchestrator: Orchestrator,
        workspace_dir: Path,
    ) -> None:
        orchestrator._save_execution_log("phase1", "completed", None)
        orchestrator._save_execution_log("phase2", "completed", None)
        orchestrator._save_execution_log("phase3", "failed", "Error")

        log_path = workspace_dir / "execution_log.json"
        data = json.loads(log_path.read_text())
        assert len(data["phases"]) == 3


# ===========================================================================
# run_full_pipeline
# ===========================================================================
class TestRunFullPipeline:
    """Full pipeline execution tests using mocks."""

    @patch.object(Orchestrator, "_run_phase5_output_generation")
    @patch.object(Orchestrator, "_run_phase4_portfolio_construction")
    @patch.object(Orchestrator, "_run_phase3_neutralization")
    @patch.object(Orchestrator, "_run_phase2_scoring")
    @patch.object(Orchestrator, "_run_phase1_extraction")
    def test_正常系_Phase1から5が順序通りに実行される(
        self,
        mock_phase1: MagicMock,
        mock_phase2: MagicMock,
        mock_phase3: MagicMock,
        mock_phase4: MagicMock,
        mock_phase5: MagicMock,
        orchestrator: Orchestrator,
    ) -> None:
        # Setup return values
        mock_phase1.return_value = _make_claims()
        mock_phase2.return_value = _make_scored_claims()
        mock_phase3.return_value = _make_ranked_df()
        mock_phase4.return_value = _make_portfolio_result()

        orchestrator.run_full_pipeline()

        mock_phase1.assert_called_once()
        mock_phase2.assert_called_once()
        mock_phase3.assert_called_once()
        mock_phase4.assert_called_once()
        mock_phase5.assert_called_once()

    @patch.object(Orchestrator, "_run_phase5_output_generation")
    @patch.object(Orchestrator, "_run_phase4_portfolio_construction")
    @patch.object(Orchestrator, "_run_phase3_neutralization")
    @patch.object(Orchestrator, "_run_phase2_scoring")
    @patch.object(Orchestrator, "_run_phase1_extraction")
    def test_正常系_Phase1の出力がPhase2に渡される(
        self,
        mock_phase1: MagicMock,
        mock_phase2: MagicMock,
        mock_phase3: MagicMock,
        mock_phase4: MagicMock,
        mock_phase5: MagicMock,
        orchestrator: Orchestrator,
    ) -> None:
        claims = _make_claims()
        mock_phase1.return_value = claims
        mock_phase2.return_value = _make_scored_claims()
        mock_phase3.return_value = _make_ranked_df()
        mock_phase4.return_value = _make_portfolio_result()

        orchestrator.run_full_pipeline()

        # Phase 2 should receive claims from Phase 1
        mock_phase2.assert_called_once_with(claims)

    @patch.object(Orchestrator, "_run_phase1_extraction")
    def test_異常系_Phase1でエラーが発生した場合ログに記録される(
        self,
        mock_phase1: MagicMock,
        orchestrator: Orchestrator,
        workspace_dir: Path,
    ) -> None:
        mock_phase1.side_effect = RuntimeError("Phase 1 failed")

        with pytest.raises(RuntimeError, match="Phase 1 failed"):
            orchestrator.run_full_pipeline()

        log_path = workspace_dir / "execution_log.json"
        assert log_path.exists()
        data = json.loads(log_path.read_text())
        phase_entry = next(e for e in data["phases"] if e["phase"] == "phase1")
        assert phase_entry["status"] == "failed"


# ===========================================================================
# run_from_checkpoint
# ===========================================================================
class TestRunFromCheckpoint:
    """Checkpoint-based resumption tests."""

    @patch.object(Orchestrator, "_run_phase5_output_generation")
    @patch.object(Orchestrator, "_run_phase4_portfolio_construction")
    @patch.object(Orchestrator, "_run_phase3_neutralization")
    @patch.object(Orchestrator, "_run_phase2_scoring")
    @patch.object(Orchestrator, "_run_phase1_extraction")
    def test_正常系_phase3から再開するとphase1と2はスキップされる(
        self,
        mock_phase1: MagicMock,
        mock_phase2: MagicMock,
        mock_phase3: MagicMock,
        mock_phase4: MagicMock,
        mock_phase5: MagicMock,
        orchestrator: Orchestrator,
        workspace_dir: Path,
    ) -> None:
        # Write checkpoint data for phase1 and phase2
        checkpoint_dir = workspace_dir / "checkpoints"
        checkpoint_dir.mkdir()

        claims = _make_claims()
        claims_serialized = {
            ticker: [c.model_dump() for c in claim_list]
            for ticker, claim_list in claims.items()
        }
        (checkpoint_dir / "phase1_claims.json").write_text(
            json.dumps(claims_serialized, ensure_ascii=False, indent=2)
        )

        scored = _make_scored_claims()
        scored_serialized = {
            ticker: [c.model_dump() for c in claim_list]
            for ticker, claim_list in scored.items()
        }
        (checkpoint_dir / "phase2_scored.json").write_text(
            json.dumps(scored_serialized, ensure_ascii=False, indent=2)
        )

        mock_phase3.return_value = _make_ranked_df()
        mock_phase4.return_value = _make_portfolio_result()

        orchestrator.run_from_checkpoint(phase=3)

        mock_phase1.assert_not_called()
        mock_phase2.assert_not_called()
        mock_phase3.assert_called_once()
        mock_phase4.assert_called_once()
        mock_phase5.assert_called_once()

    def test_異常系_無効なphase番号でValueError(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        with pytest.raises(ValueError, match="phase must be between 1 and 5"):
            orchestrator.run_from_checkpoint(phase=0)

    def test_異常系_6以上のphase番号でValueError(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        with pytest.raises(ValueError, match="phase must be between 1 and 5"):
            orchestrator.run_from_checkpoint(phase=6)


# ===========================================================================
# Individual phase methods (mock-based)
# ===========================================================================
class TestPhase1Extraction:
    """Phase 1 extraction method tests."""

    @patch("dev.ca_strategy.orchestrator.ClaimExtractor")
    @patch("dev.ca_strategy.orchestrator.TranscriptLoader")
    def test_正常系_TranscriptLoaderとClaimExtractorが使用される(
        self,
        mock_loader_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        orchestrator: Orchestrator,
    ) -> None:
        mock_loader = MagicMock()
        mock_loader.load_batch.return_value = {"AAPL": []}
        mock_loader_cls.return_value = mock_loader

        mock_extractor = MagicMock()
        mock_extractor.extract_batch.return_value = _make_claims()
        mock_extractor_cls.return_value = mock_extractor

        result = orchestrator._run_phase1_extraction()

        mock_loader_cls.assert_called_once()
        mock_extractor_cls.assert_called_once()
        assert isinstance(result, dict)


class TestPhase2Scoring:
    """Phase 2 scoring method tests."""

    @patch("dev.ca_strategy.orchestrator.ClaimScorer")
    def test_正常系_ClaimScorerが使用される(
        self,
        mock_scorer_cls: MagicMock,
        orchestrator: Orchestrator,
    ) -> None:
        mock_scorer = MagicMock()
        mock_scorer.score_batch.return_value = _make_scored_claims()
        mock_scorer_cls.return_value = mock_scorer

        claims = _make_claims()
        result = orchestrator._run_phase2_scoring(claims)

        mock_scorer_cls.assert_called_once()
        assert isinstance(result, dict)


class TestPhase3Neutralization:
    """Phase 3 neutralization method tests."""

    def test_正常系_scored_claimsからDataFrameを生成する(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        scored = _make_scored_claims()
        scores = _make_stock_scores()

        with patch(
            "dev.ca_strategy.orchestrator.SectorNeutralizer"
        ) as mock_neutralizer_cls:
            mock_neutralizer = MagicMock()
            mock_neutralizer.neutralize.return_value = _make_ranked_df()
            mock_neutralizer_cls.return_value = mock_neutralizer

            result = orchestrator._run_phase3_neutralization(scored, scores)
            assert isinstance(result, pd.DataFrame)


class TestPhase4PortfolioConstruction:
    """Phase 4 portfolio construction method tests."""

    def test_正常系_PortfolioBuilderが使用される(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        ranked = _make_ranked_df()
        benchmark = [
            BenchmarkWeight(sector="Information Technology", weight=0.6),
            BenchmarkWeight(sector="Financials", weight=0.4),
        ]

        with patch("dev.ca_strategy.orchestrator.PortfolioBuilder") as mock_builder_cls:
            mock_builder = MagicMock()
            mock_builder.build.return_value = _make_portfolio_result()
            mock_builder_cls.return_value = mock_builder

            result = orchestrator._run_phase4_portfolio_construction(ranked, benchmark)
            assert len(result.holdings) > 0
            assert len(result.sector_allocations) > 0


class TestPhase5OutputGeneration:
    """Phase 5 output generation method tests."""

    def test_正常系_OutputGeneratorが使用される(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        portfolio = _make_portfolio_result()
        scored = _make_scored_claims()
        scores = _make_stock_scores()

        with patch("dev.ca_strategy.orchestrator.OutputGenerator") as mock_gen_cls:
            mock_gen = MagicMock()
            mock_gen_cls.return_value = mock_gen

            orchestrator._run_phase5_output_generation(portfolio, scored, scores)
            mock_gen.generate_all.assert_called_once()
