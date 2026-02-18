"""Pydantic v2 data models for the CA Strategy package.

Defines all shared types used across the ca_strategy pipeline:
- Transcript models (input to Phase 1)
- Claim / ScoredClaim models (Phase 1 & 2 outputs)
- StockScore / PortfolioHolding models (Phase 3 & 4 outputs)
- Configuration models (UniverseConfig, BenchmarkWeight)

All models are immutable (frozen=True) with field validators.
"""

from __future__ import annotations

import re
from datetime import date  # noqa: TC003 - required at runtime by Pydantic
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, field_validator


# ---------------------------------------------------------------------------
# Reusable non-empty string validator (DRY-002)
# ---------------------------------------------------------------------------
def _validate_non_empty_str(v: str) -> str:
    """Validate that a string is non-empty after stripping whitespace."""
    if not v or not v.strip():
        msg = "value must be non-empty string"
        raise ValueError(msg)
    return v


NonEmptyStr = Annotated[str, AfterValidator(_validate_non_empty_str)]


def _validate_unit_range(v: float) -> float:
    """Validate that a float is in [0.0, 1.0]."""
    if not 0.0 <= v <= 1.0:
        msg = f"value must be between 0.0 and 1.0, got {v}"
        raise ValueError(msg)
    return v


UnitFloat = Annotated[float, AfterValidator(_validate_unit_range)]
"""Float constrained to [0.0, 1.0]. Used for scores, weights, and confidences."""


def _validate_non_negative_int(v: int) -> int:
    """Validate that an int is >= 0."""
    if v < 0:
        msg = f"value must be >= 0, got {v}"
        raise ValueError(msg)
    return v


NonNegativeInt = Annotated[int, AfterValidator(_validate_non_negative_int)]
"""Int constrained to >= 0. Used for counts."""


def _validate_adjustment_range(v: float) -> float:
    """Validate that a float is in [-1.0, 1.0]."""
    if not -1.0 <= v <= 1.0:
        msg = f"adjustment must be between -1.0 and 1.0, got {v}"
        raise ValueError(msg)
    return v


AdjustmentFloat = Annotated[float, AfterValidator(_validate_adjustment_range)]
"""Float constrained to [-1.0, 1.0]. Used for confidence adjustments."""


_SAFE_TICKER_RE: re.Pattern[str] = re.compile(r"^[A-Z0-9./]{1,10}$")


def _validate_ticker(v: str) -> str:
    """Validate ticker symbol format: uppercase alphanumeric with . or / allowed."""
    if not _SAFE_TICKER_RE.match(v):
        msg = f"Invalid ticker format: {v!r}. Must match ^[A-Z0-9./]{{1,10}}$"
        raise ValueError(msg)
    return v


TickerStr = Annotated[str, AfterValidator(_validate_ticker)]
"""Ticker symbol constrained to uppercase alphanumeric with . or / (1-10 chars)."""

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

    speaker: NonEmptyStr
    role: str | None
    section_type: str
    content: NonEmptyStr


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

    ticker: TickerStr
    event_date: date
    fiscal_quarter: NonEmptyStr
    is_truncated: bool = False


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
    confidence: UnitFloat
    adjustments: list[str]


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

    id: NonEmptyStr
    claim_type: ClaimType
    claim: NonEmptyStr
    evidence: str
    rule_evaluation: RuleEvaluation


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
    adjustment: AdjustmentFloat
    reasoning: str


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

    id: NonEmptyStr
    claim_type: ClaimType
    claim: NonEmptyStr
    evidence: str
    rule_evaluation: RuleEvaluation
    final_confidence: UnitFloat
    adjustments: list[ConfidenceAdjustment]


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

    ticker: NonEmptyStr
    aggregate_score: UnitFloat
    claim_count: NonNegativeInt
    structural_weight: UnitFloat


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

    ticker: NonEmptyStr
    weight: UnitFloat
    sector: NonEmptyStr
    score: UnitFloat
    rationale_summary: str


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

    sector: NonEmptyStr
    benchmark_weight: UnitFloat
    actual_weight: UnitFloat
    stock_count: NonNegativeInt


class PortfolioResult(BaseModel):
    """Complete portfolio construction result.

    Parameters
    ----------
    holdings : list[PortfolioHolding]
        List of portfolio holdings with weights.
    sector_allocations : list[SectorAllocation]
        Sector-level allocations.
    as_of_date : date
        As-of date for the portfolio.
    """

    model_config = ConfigDict(frozen=True)

    holdings: list[PortfolioHolding]
    sector_allocations: list[SectorAllocation]
    as_of_date: date


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

    ticker: NonEmptyStr
    gics_sector: NonEmptyStr


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

    sector: NonEmptyStr
    weight: UnitFloat
