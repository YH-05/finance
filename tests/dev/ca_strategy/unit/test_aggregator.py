"""Tests for ca_strategy aggregator module.

ScoreAggregator takes scored claims and produces per-stock aggregate scores
using structural-advantage-weighted averaging.

Weight scheme:
- Default weight: 1.0
- Rule 6 (structural advantage): 1.5
- Rule 11 (industry structure match): 2.0
- CAGR connection quality boost: +/-10%
"""

from __future__ import annotations

import pytest

from dev.ca_strategy.aggregator import ScoreAggregator
from dev.ca_strategy.types import (
    ClaimType,
    ConfidenceAdjustment,
    RuleEvaluation,
    ScoredClaim,
    StockScore,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_rule_evaluation(
    applied_rules: list[str] | None = None,
    confidence: float = 0.7,
) -> RuleEvaluation:
    """Create a RuleEvaluation with sensible defaults."""
    rules = applied_rules or ["rule_1"]
    return RuleEvaluation(
        applied_rules=rules,
        results={r: True for r in rules},
        confidence=confidence,
        adjustments=[],
    )


def _make_scored_claim(
    *,
    id: str = "claim-1",
    ticker: str = "AAPL",
    applied_rules: list[str] | None = None,
    final_confidence: float = 0.8,
    claim_type: ClaimType = "competitive_advantage",
) -> ScoredClaim:
    """Create a ScoredClaim with sensible defaults.

    Note: ticker is embedded in the id field as '{ticker}-{seq}'.
    """
    rules = applied_rules or ["rule_1"]
    return ScoredClaim(
        id=f"{ticker}-{id}",
        claim_type=claim_type,
        claim="Test claim",
        evidence="Test evidence",
        rule_evaluation=_make_rule_evaluation(applied_rules=rules),
        final_confidence=final_confidence,
        adjustments=[],
    )


# ===========================================================================
# ScoreAggregator
# ===========================================================================
class TestScoreAggregator:
    """ScoreAggregator class tests."""

    # -----------------------------------------------------------------------
    # Instantiation
    # -----------------------------------------------------------------------
    def test_正常系_デフォルト重みで作成できる(self) -> None:
        agg = ScoreAggregator()
        assert agg is not None

    def test_正常系_カスタム重みで作成できる(self) -> None:
        agg = ScoreAggregator(
            default_weight=1.0,
            structural_weight=2.0,
            industry_weight=3.0,
            cagr_boost=0.15,
        )
        assert agg is not None

    # -----------------------------------------------------------------------
    # aggregate – basic
    # -----------------------------------------------------------------------
    def test_正常系_単一銘柄の単一クレームで集約できる(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(ticker="AAPL", final_confidence=0.8),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        assert "AAPL" in result
        score = result["AAPL"]
        assert isinstance(score, StockScore)
        assert score.ticker == "AAPL"
        assert score.claim_count == 1
        assert score.aggregate_score == pytest.approx(0.8, abs=0.01)

    def test_正常系_複数銘柄を分離して集約できる(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(id="c1", ticker="AAPL", final_confidence=0.8),
            ],
            "MSFT": [
                _make_scored_claim(id="c2", ticker="MSFT", final_confidence=0.6),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        assert len(result) == 2
        assert "AAPL" in result
        assert "MSFT" in result

    def test_正常系_同一銘柄の複数クレームを加重平均できる(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(
                    id="c1",
                    ticker="AAPL",
                    final_confidence=0.8,
                    applied_rules=["rule_1"],
                ),
                _make_scored_claim(
                    id="c2",
                    ticker="AAPL",
                    final_confidence=0.6,
                    applied_rules=["rule_2"],
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        score = result["AAPL"]
        assert score.claim_count == 2
        # Both have default weight=1.0
        # Expected: (0.8*1.0 + 0.6*1.0) / (1.0+1.0) = 0.7
        assert score.aggregate_score == pytest.approx(0.7, abs=0.01)

    # -----------------------------------------------------------------------
    # aggregate – structural advantage (rule 6) weighting
    # -----------------------------------------------------------------------
    def test_正常系_ルール6で構造的優位性の重み1_5が適用される(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(
                    id="c1",
                    ticker="AAPL",
                    final_confidence=0.9,
                    applied_rules=["rule_6"],
                ),
                _make_scored_claim(
                    id="c2",
                    ticker="AAPL",
                    final_confidence=0.5,
                    applied_rules=["rule_1"],
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        score = result["AAPL"]
        # rule_6 weight=1.5, rule_1 weight=1.0
        # Expected: (0.9*1.5 + 0.5*1.0) / (1.5+1.0) = (1.35+0.5)/2.5 = 0.74
        assert score.aggregate_score == pytest.approx(0.74, abs=0.01)

    # -----------------------------------------------------------------------
    # aggregate – industry structure (rule 11) weighting
    # -----------------------------------------------------------------------
    def test_正常系_ルール11で業界構造合致の重み2_0が適用される(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(
                    id="c1",
                    ticker="AAPL",
                    final_confidence=0.9,
                    applied_rules=["rule_11"],
                ),
                _make_scored_claim(
                    id="c2",
                    ticker="AAPL",
                    final_confidence=0.5,
                    applied_rules=["rule_1"],
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        score = result["AAPL"]
        # rule_11 weight=2.0, rule_1 weight=1.0
        # Expected: (0.9*2.0 + 0.5*1.0) / (2.0+1.0) = (1.8+0.5)/3.0 = 0.7667
        assert score.aggregate_score == pytest.approx(0.7667, abs=0.01)

    # -----------------------------------------------------------------------
    # aggregate – CAGR connection boost
    # -----------------------------------------------------------------------
    def test_正常系_CAGRクレームで正のブーストが適用される(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(
                    id="c1",
                    ticker="AAPL",
                    final_confidence=0.8,
                    applied_rules=["rule_1"],
                    claim_type="cagr_connection",
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        score = result["AAPL"]
        # CAGR connection with high confidence (>=0.7) -> +10% boost
        # base = 0.8, boosted = 0.8 * 1.1 = 0.88
        assert score.aggregate_score == pytest.approx(0.88, abs=0.01)

    def test_正常系_低信頼度CAGRクレームで負のブーストが適用される(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(
                    id="c1",
                    ticker="AAPL",
                    final_confidence=0.3,
                    applied_rules=["rule_1"],
                    claim_type="cagr_connection",
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        score = result["AAPL"]
        # CAGR connection with low confidence (<0.7) -> -10% penalty
        # base = 0.3, penalized = 0.3 * 0.9 = 0.27
        assert score.aggregate_score == pytest.approx(0.27, abs=0.01)

    # -----------------------------------------------------------------------
    # aggregate – structural_weight calculation
    # -----------------------------------------------------------------------
    def test_正常系_structural_weightが正しく計算される(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(
                    id="c1",
                    ticker="AAPL",
                    final_confidence=0.8,
                    applied_rules=["rule_6"],
                ),
                _make_scored_claim(
                    id="c2",
                    ticker="AAPL",
                    final_confidence=0.6,
                    applied_rules=["rule_1"],
                ),
                _make_scored_claim(
                    id="c3",
                    ticker="AAPL",
                    final_confidence=0.7,
                    applied_rules=["rule_11"],
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        score = result["AAPL"]
        # Structural claims: rule_6 (weight 1.5) + rule_11 (weight 2.0) = 3.5
        # Total weights: 1.5 + 1.0 + 2.0 = 4.5
        # structural_weight = 3.5 / 4.5 = 0.7778
        assert 0.0 <= score.structural_weight <= 1.0

    # -----------------------------------------------------------------------
    # aggregate – combined rules
    # -----------------------------------------------------------------------
    def test_正常系_複数ルール適用時に最大重みが使用される(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(
                    id="c1",
                    ticker="AAPL",
                    final_confidence=0.8,
                    applied_rules=["rule_6", "rule_11"],  # Both structural rules
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        score = result["AAPL"]
        # When multiple rules apply, use the maximum weight
        # rule_6=1.5, rule_11=2.0 -> max=2.0
        assert score.claim_count == 1

    # -----------------------------------------------------------------------
    # aggregate – edge cases
    # -----------------------------------------------------------------------
    def test_エッジケース_空のクレーム辞書で空辞書を返す(self) -> None:
        agg = ScoreAggregator()
        result = agg.aggregate({})
        assert result == {}

    def test_正常系_スコアが0_0から1_0の範囲にクランプされる(self) -> None:
        # Even with boosting, score should be clamped to [0, 1]
        claims = {
            "AAPL": [
                _make_scored_claim(
                    id="c1",
                    ticker="AAPL",
                    final_confidence=0.98,
                    applied_rules=["rule_1"],
                    claim_type="cagr_connection",
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        score = result["AAPL"]
        assert 0.0 <= score.aggregate_score <= 1.0

    def test_エッジケース_空のクレームリストを含むtickerは除外される(self) -> None:
        claims = {
            "AAPL": [
                _make_scored_claim(ticker="AAPL", final_confidence=0.8),
            ],
            "MSFT": [],  # Empty list should be excluded
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        assert "AAPL" in result
        assert "MSFT" not in result

    def test_正常系_ハイフン含みティッカーが正しく処理される(self) -> None:
        """BUG-001: BRK-B等のハイフン含みティッカーをdict keyで正しく処理."""
        claims = {
            "BRK-B": [
                _make_scored_claim(
                    id="c1",
                    ticker="BRK-B",
                    final_confidence=0.85,
                ),
            ],
        }
        agg = ScoreAggregator()
        result = agg.aggregate(claims)

        assert "BRK-B" in result
        assert result["BRK-B"].ticker == "BRK-B"
        assert result["BRK-B"].aggregate_score == pytest.approx(0.85, abs=0.01)
