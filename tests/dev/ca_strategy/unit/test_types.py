"""Tests for ca_strategy types module.

All Pydantic models must be immutable (frozen=True) and properly validated.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from dev.ca_strategy.types import (
    BenchmarkWeight,
    Claim,
    ClaimType,
    ConfidenceAdjustment,
    PortfolioHolding,
    RuleEvaluation,
    ScoredClaim,
    SectorAllocation,
    StockScore,
    Transcript,
    TranscriptMetadata,
    TranscriptSection,
    UniverseConfig,
    UniverseTicker,
)


# =============================================================================
# TranscriptSection
# =============================================================================
class TestTranscriptSection:
    """TranscriptSection model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        section = TranscriptSection(
            speaker="Tim Cook",
            role="CEO",
            section_type="prepared_remarks",
            content="We had a great quarter...",
        )
        assert section.speaker == "Tim Cook"
        assert section.role == "CEO"
        assert section.section_type == "prepared_remarks"
        assert section.content == "We had a great quarter..."

    def test_正常系_frozenモデルである(self) -> None:
        section = TranscriptSection(
            speaker="Tim Cook",
            role="CEO",
            section_type="prepared_remarks",
            content="content",
        )
        with pytest.raises(ValidationError):
            section.speaker = "other"

    def test_異常系_speakerが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="speaker"):
            TranscriptSection(
                speaker="",
                role="CEO",
                section_type="prepared_remarks",
                content="content",
            )

    def test_異常系_contentが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="content"):
            TranscriptSection(
                speaker="Tim Cook",
                role="CEO",
                section_type="prepared_remarks",
                content="",
            )

    def test_正常系_roleがNoneでも作成できる(self) -> None:
        section = TranscriptSection(
            speaker="Operator",
            role=None,
            section_type="operator",
            content="Welcome to the call.",
        )
        assert section.role is None


# =============================================================================
# TranscriptMetadata
# =============================================================================
class TestTranscriptMetadata:
    """TranscriptMetadata model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        meta = TranscriptMetadata(
            ticker="AAPL",
            event_date=date(2024, 1, 25),
            fiscal_quarter="Q1 2024",
            is_truncated=False,
        )
        assert meta.ticker == "AAPL"
        assert meta.event_date == date(2024, 1, 25)
        assert meta.fiscal_quarter == "Q1 2024"
        assert meta.is_truncated is False

    def test_正常系_frozenモデルである(self) -> None:
        meta = TranscriptMetadata(
            ticker="AAPL",
            event_date=date(2024, 1, 25),
            fiscal_quarter="Q1 2024",
            is_truncated=False,
        )
        with pytest.raises(ValidationError):
            meta.ticker = "MSFT"

    def test_異常系_tickerが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="ticker"):
            TranscriptMetadata(
                ticker="",
                event_date=date(2024, 1, 25),
                fiscal_quarter="Q1 2024",
                is_truncated=False,
            )

    def test_異常系_fiscal_quarterが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="fiscal_quarter"):
            TranscriptMetadata(
                ticker="AAPL",
                event_date=date(2024, 1, 25),
                fiscal_quarter="",
                is_truncated=False,
            )

    def test_正常系_is_truncatedのデフォルトはFalse(self) -> None:
        meta = TranscriptMetadata(
            ticker="AAPL",
            event_date=date(2024, 1, 25),
            fiscal_quarter="Q1 2024",
        )
        assert meta.is_truncated is False


# =============================================================================
# Transcript
# =============================================================================
class TestTranscript:
    """Transcript model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        section = TranscriptSection(
            speaker="Tim Cook",
            role="CEO",
            section_type="prepared_remarks",
            content="Great quarter.",
        )
        meta = TranscriptMetadata(
            ticker="AAPL",
            event_date=date(2024, 1, 25),
            fiscal_quarter="Q1 2024",
            is_truncated=False,
        )
        transcript = Transcript(
            metadata=meta,
            sections=[section],
            raw_source="Full transcript text...",
        )
        assert transcript.metadata == meta
        assert len(transcript.sections) == 1
        assert transcript.raw_source == "Full transcript text..."

    def test_正常系_frozenモデルである(self) -> None:
        section = TranscriptSection(
            speaker="Tim Cook",
            role="CEO",
            section_type="prepared_remarks",
            content="content",
        )
        meta = TranscriptMetadata(
            ticker="AAPL",
            event_date=date(2024, 1, 25),
            fiscal_quarter="Q1 2024",
        )
        transcript = Transcript(
            metadata=meta,
            sections=[section],
            raw_source="source",
        )
        with pytest.raises(ValidationError):
            transcript.raw_source = "other"

    def test_異常系_sectionsが空リストでValidationError(self) -> None:
        meta = TranscriptMetadata(
            ticker="AAPL",
            event_date=date(2024, 1, 25),
            fiscal_quarter="Q1 2024",
        )
        with pytest.raises(ValidationError, match="sections"):
            Transcript(
                metadata=meta,
                sections=[],
                raw_source="source",
            )

    def test_正常系_raw_sourceがNoneでも作成できる(self) -> None:
        section = TranscriptSection(
            speaker="Tim Cook",
            role="CEO",
            section_type="prepared_remarks",
            content="content",
        )
        meta = TranscriptMetadata(
            ticker="AAPL",
            event_date=date(2024, 1, 25),
            fiscal_quarter="Q1 2024",
        )
        transcript = Transcript(
            metadata=meta,
            sections=[section],
            raw_source=None,
        )
        assert transcript.raw_source is None


# =============================================================================
# ClaimType
# =============================================================================
class TestClaimType:
    """ClaimType literal type tests."""

    def test_正常系_competitive_advantageが有効(self) -> None:
        claim = Claim(
            id="c1",
            claim_type="competitive_advantage",
            claim="Strong brand",
            evidence="Revenue growth",
            rule_evaluation=RuleEvaluation(
                applied_rules=["rule01"],
                results={"rule01": True},
                confidence=0.8,
                adjustments=[],
            ),
        )
        assert claim.claim_type == "competitive_advantage"

    def test_正常系_cagr_connectionが有効(self) -> None:
        claim = Claim(
            id="c2",
            claim_type="cagr_connection",
            claim="Growth driver",
            evidence="Data shows",
            rule_evaluation=RuleEvaluation(
                applied_rules=["rule01"],
                results={"rule01": True},
                confidence=0.7,
                adjustments=[],
            ),
        )
        assert claim.claim_type == "cagr_connection"

    def test_正常系_factual_claimが有効(self) -> None:
        claim = Claim(
            id="c3",
            claim_type="factual_claim",
            claim="Revenue was $100B",
            evidence="10-K filing",
            rule_evaluation=RuleEvaluation(
                applied_rules=["rule01"],
                results={"rule01": True},
                confidence=0.9,
                adjustments=[],
            ),
        )
        assert claim.claim_type == "factual_claim"


# =============================================================================
# RuleEvaluation
# =============================================================================
class TestRuleEvaluation:
    """RuleEvaluation model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01", "rule02"],
            results={"rule01": True, "rule02": False},
            confidence=0.75,
            adjustments=[],
        )
        assert rule_eval.applied_rules == ["rule01", "rule02"]
        assert rule_eval.results == {"rule01": True, "rule02": False}
        assert rule_eval.confidence == 0.75
        assert rule_eval.adjustments == []

    def test_正常系_frozenモデルである(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01"],
            results={"rule01": True},
            confidence=0.8,
            adjustments=[],
        )
        with pytest.raises(ValidationError):
            rule_eval.confidence = 0.5

    def test_異常系_confidenceが0未満でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="confidence"):
            RuleEvaluation(
                applied_rules=["rule01"],
                results={"rule01": True},
                confidence=-0.1,
                adjustments=[],
            )

    def test_異常系_confidenceが1を超えてValidationError(self) -> None:
        with pytest.raises(ValidationError, match="confidence"):
            RuleEvaluation(
                applied_rules=["rule01"],
                results={"rule01": True},
                confidence=1.1,
                adjustments=[],
            )

    def test_エッジケース_confidence境界値0と1が有効(self) -> None:
        rule_eval_0 = RuleEvaluation(
            applied_rules=[],
            results={},
            confidence=0.0,
            adjustments=[],
        )
        assert rule_eval_0.confidence == 0.0

        rule_eval_1 = RuleEvaluation(
            applied_rules=[],
            results={},
            confidence=1.0,
            adjustments=[],
        )
        assert rule_eval_1.confidence == 1.0


# =============================================================================
# Claim
# =============================================================================
class TestClaim:
    """Claim model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01"],
            results={"rule01": True},
            confidence=0.8,
            adjustments=[],
        )
        claim = Claim(
            id="claim_001",
            claim_type="competitive_advantage",
            claim="Strong brand recognition",
            evidence="Market share data shows 35% dominance",
            rule_evaluation=rule_eval,
        )
        assert claim.id == "claim_001"
        assert claim.claim_type == "competitive_advantage"
        assert claim.claim == "Strong brand recognition"
        assert claim.evidence == "Market share data shows 35% dominance"
        assert claim.rule_evaluation == rule_eval

    def test_正常系_frozenモデルである(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01"],
            results={"rule01": True},
            confidence=0.8,
            adjustments=[],
        )
        claim = Claim(
            id="c1",
            claim_type="competitive_advantage",
            claim="claim",
            evidence="evidence",
            rule_evaluation=rule_eval,
        )
        with pytest.raises(ValidationError):
            claim.claim = "other"

    def test_異常系_idが空文字でValidationError(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01"],
            results={"rule01": True},
            confidence=0.8,
            adjustments=[],
        )
        with pytest.raises(ValidationError, match="id"):
            Claim(
                id="",
                claim_type="competitive_advantage",
                claim="claim",
                evidence="evidence",
                rule_evaluation=rule_eval,
            )

    def test_異常系_claimが空文字でValidationError(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01"],
            results={"rule01": True},
            confidence=0.8,
            adjustments=[],
        )
        with pytest.raises(ValidationError, match="claim"):
            Claim(
                id="c1",
                claim_type="competitive_advantage",
                claim="",
                evidence="evidence",
                rule_evaluation=rule_eval,
            )


# =============================================================================
# ConfidenceAdjustment
# =============================================================================
class TestConfidenceAdjustment:
    """ConfidenceAdjustment model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        adj = ConfidenceAdjustment(
            source="pattern_I",
            adjustment=0.1,
            reasoning="Quantitative evidence supports claim",
        )
        assert adj.source == "pattern_I"
        assert adj.adjustment == 0.1
        assert adj.reasoning == "Quantitative evidence supports claim"

    def test_正常系_frozenモデルである(self) -> None:
        adj = ConfidenceAdjustment(
            source="pattern_I",
            adjustment=0.1,
            reasoning="reasoning",
        )
        with pytest.raises(ValidationError):
            adj.adjustment = 0.2

    def test_正常系_負のadjustmentも有効(self) -> None:
        adj = ConfidenceAdjustment(
            source="pattern_A",
            adjustment=-0.2,
            reasoning="Result as cause detected",
        )
        assert adj.adjustment == -0.2

    def test_異常系_adjustmentが範囲外でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="adjustment"):
            ConfidenceAdjustment(
                source="pattern_A",
                adjustment=-1.1,
                reasoning="too much",
            )

        with pytest.raises(ValidationError, match="adjustment"):
            ConfidenceAdjustment(
                source="pattern_I",
                adjustment=1.1,
                reasoning="too much",
            )


# =============================================================================
# ScoredClaim
# =============================================================================
class TestScoredClaim:
    """ScoredClaim model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01"],
            results={"rule01": True},
            confidence=0.8,
            adjustments=[],
        )
        adj = ConfidenceAdjustment(
            source="pattern_I",
            adjustment=0.1,
            reasoning="Good quantitative evidence",
        )
        scored = ScoredClaim(
            id="c1",
            claim_type="competitive_advantage",
            claim="Strong brand",
            evidence="Market data",
            rule_evaluation=rule_eval,
            final_confidence=0.9,
            adjustments=[adj],
        )
        assert scored.final_confidence == 0.9
        assert len(scored.adjustments) == 1
        assert scored.adjustments[0].source == "pattern_I"

    def test_正常系_frozenモデルである(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01"],
            results={"rule01": True},
            confidence=0.8,
            adjustments=[],
        )
        scored = ScoredClaim(
            id="c1",
            claim_type="competitive_advantage",
            claim="claim",
            evidence="evidence",
            rule_evaluation=rule_eval,
            final_confidence=0.8,
            adjustments=[],
        )
        with pytest.raises(ValidationError):
            scored.final_confidence = 0.5

    def test_異常系_final_confidenceが範囲外でValidationError(self) -> None:
        rule_eval = RuleEvaluation(
            applied_rules=["rule01"],
            results={"rule01": True},
            confidence=0.8,
            adjustments=[],
        )
        with pytest.raises(ValidationError, match="final_confidence"):
            ScoredClaim(
                id="c1",
                claim_type="competitive_advantage",
                claim="claim",
                evidence="evidence",
                rule_evaluation=rule_eval,
                final_confidence=1.5,
                adjustments=[],
            )

        with pytest.raises(ValidationError, match="final_confidence"):
            ScoredClaim(
                id="c1",
                claim_type="competitive_advantage",
                claim="claim",
                evidence="evidence",
                rule_evaluation=rule_eval,
                final_confidence=-0.1,
                adjustments=[],
            )


# =============================================================================
# StockScore
# =============================================================================
class TestStockScore:
    """StockScore model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        score = StockScore(
            ticker="AAPL",
            aggregate_score=0.85,
            claim_count=5,
            structural_weight=0.7,
        )
        assert score.ticker == "AAPL"
        assert score.aggregate_score == 0.85
        assert score.claim_count == 5
        assert score.structural_weight == 0.7

    def test_正常系_frozenモデルである(self) -> None:
        score = StockScore(
            ticker="AAPL",
            aggregate_score=0.85,
            claim_count=5,
            structural_weight=0.7,
        )
        with pytest.raises(ValidationError):
            score.ticker = "MSFT"

    def test_異常系_tickerが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="ticker"):
            StockScore(
                ticker="",
                aggregate_score=0.85,
                claim_count=5,
                structural_weight=0.7,
            )

    def test_異常系_aggregate_scoreが範囲外でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="aggregate_score"):
            StockScore(
                ticker="AAPL",
                aggregate_score=-0.1,
                claim_count=5,
                structural_weight=0.7,
            )

        with pytest.raises(ValidationError, match="aggregate_score"):
            StockScore(
                ticker="AAPL",
                aggregate_score=1.1,
                claim_count=5,
                structural_weight=0.7,
            )

    def test_異常系_claim_countが負でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="claim_count"):
            StockScore(
                ticker="AAPL",
                aggregate_score=0.85,
                claim_count=-1,
                structural_weight=0.7,
            )

    def test_異常系_structural_weightが範囲外でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="structural_weight"):
            StockScore(
                ticker="AAPL",
                aggregate_score=0.85,
                claim_count=5,
                structural_weight=-0.1,
            )

        with pytest.raises(ValidationError, match="structural_weight"):
            StockScore(
                ticker="AAPL",
                aggregate_score=0.85,
                claim_count=5,
                structural_weight=1.1,
            )


# =============================================================================
# PortfolioHolding
# =============================================================================
class TestPortfolioHolding:
    """PortfolioHolding model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        holding = PortfolioHolding(
            ticker="AAPL",
            weight=0.05,
            sector="Information Technology",
            score=0.85,
            rationale_summary="Strong competitive advantages in ecosystem lock-in",
        )
        assert holding.ticker == "AAPL"
        assert holding.weight == 0.05
        assert holding.sector == "Information Technology"
        assert holding.score == 0.85
        assert "ecosystem" in holding.rationale_summary

    def test_正常系_frozenモデルである(self) -> None:
        holding = PortfolioHolding(
            ticker="AAPL",
            weight=0.05,
            sector="Information Technology",
            score=0.85,
            rationale_summary="summary",
        )
        with pytest.raises(ValidationError):
            holding.weight = 0.1

    def test_異常系_tickerが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="ticker"):
            PortfolioHolding(
                ticker="",
                weight=0.05,
                sector="Information Technology",
                score=0.85,
                rationale_summary="summary",
            )

    def test_異常系_weightが範囲外でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="weight"):
            PortfolioHolding(
                ticker="AAPL",
                weight=-0.01,
                sector="Information Technology",
                score=0.85,
                rationale_summary="summary",
            )

        with pytest.raises(ValidationError, match="weight"):
            PortfolioHolding(
                ticker="AAPL",
                weight=1.1,
                sector="Information Technology",
                score=0.85,
                rationale_summary="summary",
            )

    def test_異常系_scoreが範囲外でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="score"):
            PortfolioHolding(
                ticker="AAPL",
                weight=0.05,
                sector="Information Technology",
                score=-0.1,
                rationale_summary="summary",
            )

    def test_異常系_sectorが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="sector"):
            PortfolioHolding(
                ticker="AAPL",
                weight=0.05,
                sector="",
                score=0.85,
                rationale_summary="summary",
            )


# =============================================================================
# SectorAllocation
# =============================================================================
class TestSectorAllocation:
    """SectorAllocation model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        alloc = SectorAllocation(
            sector="Information Technology",
            benchmark_weight=0.19,
            actual_weight=0.22,
            stock_count=10,
        )
        assert alloc.sector == "Information Technology"
        assert alloc.benchmark_weight == 0.19
        assert alloc.actual_weight == 0.22
        assert alloc.stock_count == 10

    def test_正常系_frozenモデルである(self) -> None:
        alloc = SectorAllocation(
            sector="IT",
            benchmark_weight=0.19,
            actual_weight=0.22,
            stock_count=10,
        )
        with pytest.raises(ValidationError):
            alloc.stock_count = 20

    def test_異常系_sectorが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="sector"):
            SectorAllocation(
                sector="",
                benchmark_weight=0.19,
                actual_weight=0.22,
                stock_count=10,
            )

    def test_異常系_stock_countが負でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="stock_count"):
            SectorAllocation(
                sector="IT",
                benchmark_weight=0.19,
                actual_weight=0.22,
                stock_count=-1,
            )

    def test_異常系_weightが範囲外でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="benchmark_weight"):
            SectorAllocation(
                sector="IT",
                benchmark_weight=-0.1,
                actual_weight=0.22,
                stock_count=10,
            )

        with pytest.raises(ValidationError, match="actual_weight"):
            SectorAllocation(
                sector="IT",
                benchmark_weight=0.19,
                actual_weight=1.1,
                stock_count=10,
            )


# =============================================================================
# UniverseTicker
# =============================================================================
class TestUniverseTicker:
    """UniverseTicker model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        ticker = UniverseTicker(
            ticker="AAPL",
            gics_sector="Information Technology",
        )
        assert ticker.ticker == "AAPL"
        assert ticker.gics_sector == "Information Technology"

    def test_異常系_tickerが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="ticker"):
            UniverseTicker(
                ticker="",
                gics_sector="Information Technology",
            )

    def test_異常系_gics_sectorが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="gics_sector"):
            UniverseTicker(
                ticker="AAPL",
                gics_sector="",
            )


# =============================================================================
# UniverseConfig
# =============================================================================
class TestUniverseConfig:
    """UniverseConfig model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        tickers = [
            UniverseTicker(ticker="AAPL", gics_sector="Information Technology"),
            UniverseTicker(ticker="MSFT", gics_sector="Information Technology"),
        ]
        config = UniverseConfig(tickers=tickers)
        assert len(config.tickers) == 2
        assert config.tickers[0].ticker == "AAPL"

    def test_正常系_frozenモデルである(self) -> None:
        tickers = [
            UniverseTicker(ticker="AAPL", gics_sector="Information Technology"),
        ]
        config = UniverseConfig(tickers=tickers)
        with pytest.raises(ValidationError):
            config.tickers = []

    def test_異常系_tickersが空リストでValidationError(self) -> None:
        with pytest.raises(ValidationError, match="tickers"):
            UniverseConfig(tickers=[])


# =============================================================================
# BenchmarkWeight
# =============================================================================
class TestBenchmarkWeight:
    """BenchmarkWeight model tests."""

    def test_正常系_有効なデータで作成できる(self) -> None:
        bw = BenchmarkWeight(
            sector="Information Technology",
            weight=0.19,
        )
        assert bw.sector == "Information Technology"
        assert bw.weight == 0.19

    def test_正常系_frozenモデルである(self) -> None:
        bw = BenchmarkWeight(
            sector="IT",
            weight=0.19,
        )
        with pytest.raises(ValidationError):
            bw.weight = 0.25

    def test_異常系_sectorが空文字でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="sector"):
            BenchmarkWeight(
                sector="",
                weight=0.19,
            )

    def test_異常系_weightが範囲外でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="weight"):
            BenchmarkWeight(
                sector="IT",
                weight=-0.1,
            )

        with pytest.raises(ValidationError, match="weight"):
            BenchmarkWeight(
                sector="IT",
                weight=1.1,
            )

    def test_エッジケース_weight境界値0と1が有効(self) -> None:
        bw0 = BenchmarkWeight(sector="IT", weight=0.0)
        assert bw0.weight == 0.0

        bw1 = BenchmarkWeight(sector="IT", weight=1.0)
        assert bw1.weight == 1.0
