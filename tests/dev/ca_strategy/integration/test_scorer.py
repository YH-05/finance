"""Integration tests for ca_strategy scorer module (Phase 2).

These tests make actual Claude API calls and require:
- ANTHROPIC_API_KEY environment variable to be set
- Network access to the Anthropic API

Run manually with:
    uv run pytest tests/dev/ca_strategy/integration/test_scorer.py -v -s

These tests are marked with @pytest.mark.integration and are excluded
from the default test suite.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from dev.ca_strategy.cost import CostTracker
from dev.ca_strategy.scorer import ClaimScorer
from dev.ca_strategy.types import (
    Claim,
    RuleEvaluation,
)

# Skip all tests in this module if ANTHROPIC_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set (integration test requires real API)",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_KB1_DIR = _PROJECT_ROOT / "analyst" / "transcript_eval" / "kb1_rules_transcript"
_KB2_DIR = _PROJECT_ROOT / "analyst" / "transcript_eval" / "kb2_patterns_transcript"
_KB3_DIR = _PROJECT_ROOT / "analyst" / "transcript_eval" / "kb3_fewshot_transcript"
_DOGMA_PATH = (
    _PROJECT_ROOT / "analyst" / "Competitive_Advantage" / "analyst_YK" / "dogma.md"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def cost_tracker() -> CostTracker:
    """Create a fresh CostTracker."""
    return CostTracker()


@pytest.fixture
def scorer(cost_tracker: CostTracker) -> ClaimScorer:
    """Create a ClaimScorer with real KB files."""
    return ClaimScorer(
        kb1_dir=_KB1_DIR,
        kb2_dir=_KB2_DIR,
        kb3_dir=_KB3_DIR,
        dogma_path=_DOGMA_PATH,
        cost_tracker=cost_tracker,
    )


@pytest.fixture
def sample_claims() -> list[Claim]:
    """Create sample claims for integration testing."""
    return [
        Claim(
            id="AAPL-CA-001",
            claim_type="competitive_advantage",
            claim="Proprietary silicon design capability enables performance-per-watt leadership",
            evidence=(
                "CEO Tim Cook: Our proprietary silicon design gives us a "
                "fundamental performance advantage that competitors cannot easily "
                "replicate. The M-series chips deliver 2x the performance per watt "
                "compared to industry alternatives."
            ),
            rule_evaluation=RuleEvaluation(
                applied_rules=["rule_1_t", "rule_4_t", "rule_7_t"],
                results={"rule_1_t": True, "rule_4_t": True, "rule_7_t": True},
                confidence=0.7,
                adjustments=["Capability, not result", "Quantitative evidence"],
            ),
        ),
        Claim(
            id="AAPL-CA-002",
            claim_type="competitive_advantage",
            claim="Revenue grew 30% year-over-year",
            evidence="CFO Luca Maestri: Revenue grew 30% year-over-year to $74.6 billion.",
            rule_evaluation=RuleEvaluation(
                applied_rules=["rule_1_t"],
                results={"rule_1_t": False},
                confidence=0.3,
                adjustments=["Result, not capability - should be downgraded"],
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------
class TestScorerIntegration:
    """Integration tests that call the real Claude API."""

    @pytest.mark.integration
    def test_正常系_実APIでスコアリングができる(
        self,
        scorer: ClaimScorer,
        sample_claims: list[Claim],
    ) -> None:
        """Verify that the scorer can call Claude API and parse the response."""
        scored = scorer._score_single_ticker(
            claims=sample_claims,
            ticker="AAPL",
        )

        # Should return scored claims
        assert len(scored) > 0, "Expected at least 1 scored claim from the LLM"

        # Each scored claim should have required fields
        for claim in scored:
            assert claim.id
            assert 0.0 <= claim.final_confidence <= 1.0
            assert isinstance(claim.adjustments, list)

    @pytest.mark.integration
    def test_正常系_Phase2コストが記録される(
        self,
        scorer: ClaimScorer,
        sample_claims: list[Claim],
        cost_tracker: CostTracker,
    ) -> None:
        """Verify that Phase 2 token costs are recorded after an API call."""
        scorer._score_single_ticker(
            claims=sample_claims,
            ticker="AAPL",
        )

        phase2_cost = cost_tracker.get_phase_cost("phase2")
        assert phase2_cost > 0, "Expected phase2 cost to be recorded after API call"

    @pytest.mark.integration
    def test_正常系_出力ファイルが保存される(
        self,
        scorer: ClaimScorer,
        sample_claims: list[Claim],
        tmp_path: Path,
    ) -> None:
        """Verify that scored claims are saved to output files."""
        claims_map = {"AAPL": sample_claims}
        scorer.score_batch(
            claims=claims_map,
            output_dir=tmp_path,
        )

        output_file = tmp_path / "AAPL" / "scored.json"
        assert output_file.exists(), "Expected scored.json to be created"
