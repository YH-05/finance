"""Pydantic v2 data models for the CA Strategy package.

Defines all shared types used across the ca_strategy pipeline:
- Transcript models (input to Phase 1)
- Claim / ScoredClaim models (Phase 1 & 2 outputs)
- StockScore / PortfolioHolding models (Phase 3 & 4 outputs)
- Configuration models (UniverseConfig, BenchmarkWeight)

All models are immutable (frozen=True) with field validators.
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 - required at runtime by Pydantic
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
type ClaimType = Literal["competitive_advantage", "cagr_connection", "factual_claim"]


# ===========================================================================
# Transcript models
# ===========================================================================
class TranscriptSection(BaseModel):
    """A single section of an earnings call transcript.

    Parameters
    ----------
    speaker : str
        Name of the speaker (e.g. "Tim Cook").
    role : str | None
        Role of the speaker (e.g. "CEO", "CFO").  None for operator.
    section_type : str
        Type of section (e.g. "prepared_remarks", "q_and_a", "operator").
    content : str
        Text content of this section.
    """

    model_config = ConfigDict(frozen=True)

    speaker: str
    role: str | None
    section_type: str
    content: str

    @field_validator("speaker")
    @classmethod
    def _speaker_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "speaker must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("content")
    @classmethod
    def _content_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "content must be non-empty string"
            raise ValueError(msg)
        return v


class TranscriptMetadata(BaseModel):
    """Metadata for an earnings call transcript.

    Parameters
    ----------
    ticker : str
        Ticker symbol (e.g. "AAPL").
    event_date : date
        Date of the earnings call.
    fiscal_quarter : str
        Fiscal quarter label (e.g. "Q1 2024").
    is_truncated : bool
        Whether the transcript was truncated due to length limits.
    """

    model_config = ConfigDict(frozen=True)

    ticker: str
    event_date: date
    fiscal_quarter: str
    is_truncated: bool = False

    @field_validator("ticker")
    @classmethod
    def _ticker_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "ticker must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("fiscal_quarter")
    @classmethod
    def _fiscal_quarter_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "fiscal_quarter must be non-empty string"
            raise ValueError(msg)
        return v


class Transcript(BaseModel):
    """Complete earnings call transcript.

    Parameters
    ----------
    metadata : TranscriptMetadata
        Metadata about the transcript (ticker, date, quarter).
    sections : list[TranscriptSection]
        Ordered list of transcript sections.  Must not be empty.
    raw_source : str | None
        Original raw transcript text, if available.
    """

    model_config = ConfigDict(frozen=True)

    metadata: TranscriptMetadata
    sections: list[TranscriptSection]
    raw_source: str | None

    @field_validator("sections")
    @classmethod
    def _sections_non_empty(cls, v: list[TranscriptSection]) -> list[TranscriptSection]:
        if not v:
            msg = "sections must contain at least one section"
            raise ValueError(msg)
        return v


# ===========================================================================
# Phase 1 output models
# ===========================================================================
class RuleEvaluation(BaseModel):
    """Result of applying KB1 rules to a claim.

    Parameters
    ----------
    applied_rules : list[str]
        List of rule identifiers that were applied.
    results : dict[str, bool]
        Mapping of rule ID to pass/fail result.
    confidence : float
        Confidence score between 0.0 and 1.0.
    adjustments : list[str]
        List of adjustment descriptions applied.
    """

    model_config = ConfigDict(frozen=True)

    applied_rules: list[str]
    results: dict[str, bool]
    confidence: float
    adjustments: list[str]

    @field_validator("confidence")
    @classmethod
    def _confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"confidence must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v


class Claim(BaseModel):
    """A claim extracted from a transcript with rule evaluation.

    Parameters
    ----------
    id : str
        Unique identifier for the claim.
    claim_type : ClaimType
        Type of claim: competitive_advantage, cagr_connection, or factual_claim.
    claim : str
        The claim text.
    evidence : str
        Supporting evidence for the claim.
    rule_evaluation : RuleEvaluation
        Results of applying KB1 rules.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    claim_type: ClaimType
    claim: str
    evidence: str
    rule_evaluation: RuleEvaluation

    @field_validator("id")
    @classmethod
    def _id_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "id must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("claim")
    @classmethod
    def _claim_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "claim must be non-empty string"
            raise ValueError(msg)
        return v


# ===========================================================================
# Phase 2 output models
# ===========================================================================
class ConfidenceAdjustment(BaseModel):
    """A confidence adjustment applied during Phase 2 scoring.

    Parameters
    ----------
    source : str
        Source of the adjustment (e.g. "pattern_I", "pattern_A").
    adjustment : float
        Adjustment value between -1.0 and 1.0.
    reasoning : str
        Explanation for the adjustment.
    """

    model_config = ConfigDict(frozen=True)

    source: str
    adjustment: float
    reasoning: str

    @field_validator("adjustment")
    @classmethod
    def _adjustment_in_range(cls, v: float) -> float:
        if not -1.0 <= v <= 1.0:
            msg = f"adjustment must be between -1.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v


class ScoredClaim(BaseModel):
    """A claim with final confidence score after Phase 2 adjustments.

    Extends Claim fields with scoring information.

    Parameters
    ----------
    id : str
        Unique identifier for the claim.
    claim_type : ClaimType
        Type of claim.
    claim : str
        The claim text.
    evidence : str
        Supporting evidence.
    rule_evaluation : RuleEvaluation
        Results of applying KB1 rules.
    final_confidence : float
        Final confidence score between 0.0 and 1.0 after adjustments.
    adjustments : list[ConfidenceAdjustment]
        List of adjustments applied.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    claim_type: ClaimType
    claim: str
    evidence: str
    rule_evaluation: RuleEvaluation
    final_confidence: float
    adjustments: list[ConfidenceAdjustment]

    @field_validator("id")
    @classmethod
    def _id_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "id must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("claim")
    @classmethod
    def _claim_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "claim must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("final_confidence")
    @classmethod
    def _final_confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"final_confidence must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v


# ===========================================================================
# Score / Portfolio models
# ===========================================================================
class StockScore(BaseModel):
    """Aggregate score for a single stock.

    Parameters
    ----------
    ticker : str
        Ticker symbol.
    aggregate_score : float
        Aggregate score between 0.0 and 1.0.
    claim_count : int
        Number of claims contributing to the score.  Must be >= 0.
    structural_weight : float
        Weight of structural (competitive advantage) claims, 0.0-1.0.
    """

    model_config = ConfigDict(frozen=True)

    ticker: str
    aggregate_score: float
    claim_count: int
    structural_weight: float

    @field_validator("ticker")
    @classmethod
    def _ticker_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "ticker must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("aggregate_score")
    @classmethod
    def _aggregate_score_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"aggregate_score must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("claim_count")
    @classmethod
    def _claim_count_non_negative(cls, v: int) -> int:
        if v < 0:
            msg = f"claim_count must be >= 0, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("structural_weight")
    @classmethod
    def _structural_weight_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"structural_weight must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v


class PortfolioHolding(BaseModel):
    """A single holding in the constructed portfolio.

    Parameters
    ----------
    ticker : str
        Ticker symbol.
    weight : float
        Portfolio weight, 0.0-1.0.
    sector : str
        GICS sector name.
    score : float
        Stock score, 0.0-1.0.
    rationale_summary : str
        Brief rationale for inclusion.
    """

    model_config = ConfigDict(frozen=True)

    ticker: str
    weight: float
    sector: str
    score: float
    rationale_summary: str

    @field_validator("ticker")
    @classmethod
    def _ticker_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "ticker must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("weight")
    @classmethod
    def _weight_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"weight must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("sector")
    @classmethod
    def _sector_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "sector must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("score")
    @classmethod
    def _score_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"score must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v


class SectorAllocation(BaseModel):
    """Sector-level allocation in the portfolio.

    Parameters
    ----------
    sector : str
        GICS sector name.
    benchmark_weight : float
        Benchmark sector weight, 0.0-1.0.
    actual_weight : float
        Actual portfolio sector weight, 0.0-1.0.
    stock_count : int
        Number of stocks from this sector in the portfolio.  Must be >= 0.
    """

    model_config = ConfigDict(frozen=True)

    sector: str
    benchmark_weight: float
    actual_weight: float
    stock_count: int

    @field_validator("sector")
    @classmethod
    def _sector_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "sector must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("benchmark_weight")
    @classmethod
    def _benchmark_weight_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"benchmark_weight must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("actual_weight")
    @classmethod
    def _actual_weight_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"actual_weight must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("stock_count")
    @classmethod
    def _stock_count_non_negative(cls, v: int) -> int:
        if v < 0:
            msg = f"stock_count must be >= 0, got {v}"
            raise ValueError(msg)
        return v


# ===========================================================================
# Configuration models
# ===========================================================================
class UniverseTicker(BaseModel):
    """A ticker entry in the investment universe.

    Parameters
    ----------
    ticker : str
        Ticker symbol.
    gics_sector : str
        GICS sector classification.
    """

    model_config = ConfigDict(frozen=True)

    ticker: str
    gics_sector: str

    @field_validator("ticker")
    @classmethod
    def _ticker_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "ticker must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("gics_sector")
    @classmethod
    def _gics_sector_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "gics_sector must be non-empty string"
            raise ValueError(msg)
        return v


class UniverseConfig(BaseModel):
    """Investment universe configuration.

    Parameters
    ----------
    tickers : list[UniverseTicker]
        List of tickers in the universe.  Must not be empty.
    """

    model_config = ConfigDict(frozen=True)

    tickers: list[UniverseTicker]

    @field_validator("tickers")
    @classmethod
    def _tickers_non_empty(cls, v: list[UniverseTicker]) -> list[UniverseTicker]:
        if not v:
            msg = "tickers must contain at least one ticker"
            raise ValueError(msg)
        return v


class BenchmarkWeight(BaseModel):
    """Benchmark sector weight.

    Parameters
    ----------
    sector : str
        GICS sector name.
    weight : float
        Sector weight in the benchmark, 0.0-1.0.
    """

    model_config = ConfigDict(frozen=True)

    sector: str
    weight: float

    @field_validator("sector")
    @classmethod
    def _sector_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "sector must be non-empty string"
            raise ValueError(msg)
        return v

    @field_validator("weight")
    @classmethod
    def _weight_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            msg = f"weight must be between 0.0 and 1.0, got {v}"
            raise ValueError(msg)
        return v
