"""Score aggregation for the CA Strategy pipeline.

Aggregates scored claims (Phase 2 output) into per-stock scores using
structural-advantage-weighted averaging.

Weight scheme
-------------
- Default claim weight: 1.0
- Rule 6 (structural advantage): 1.5
- Rule 11 (industry structure match): 2.0
- CAGR connection quality boost: +/-10% on final score

The aggregate score for each stock is:

    score = sum(confidence_i * weight_i) / sum(weight_i)

where weight_i is determined by the highest-weight rule applied to
claim_i.  For CAGR-connection claims, the final score receives a
+10% boost if confidence >= 0.7, or a -10% penalty otherwise.
"""

from __future__ import annotations

from utils_core.logging import get_logger

from .types import ScoredClaim, StockScore

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_WEIGHT: float = 1.0
"""Default weight for claims not matching structural rules."""

_STRUCTURAL_WEIGHT: float = 1.5
"""Weight for rule 6 (structural advantage) claims."""

_INDUSTRY_WEIGHT: float = 2.0
"""Weight for rule 11 (industry structure match) claims."""

_CAGR_BOOST: float = 0.10
"""Boost/penalty magnitude for CAGR connection quality (+/-10%)."""

_CAGR_CONFIDENCE_THRESHOLD: float = 0.7
"""Confidence threshold for positive vs. negative CAGR boost."""

_STRUCTURAL_RULES: frozenset[str] = frozenset({"rule_6", "rule_11"})
"""Rules that indicate structural/competitive advantage."""


class ScoreAggregator:
    """Aggregate scored claims into per-stock scores.

    Parameters
    ----------
    default_weight : float, default=1.0
        Weight for claims with no structural rule applied.
    structural_weight : float, default=1.5
        Weight for rule 6 (structural advantage) claims.
    industry_weight : float, default=2.0
        Weight for rule 11 (industry structure match) claims.
    cagr_boost : float, default=0.10
        Magnitude of the CAGR connection boost/penalty.

    Examples
    --------
    >>> aggregator = ScoreAggregator()
    >>> scores = aggregator.aggregate(scored_claims)
    >>> scores["AAPL"].aggregate_score
    0.82
    """

    def __init__(
        self,
        default_weight: float = _DEFAULT_WEIGHT,
        structural_weight: float = _STRUCTURAL_WEIGHT,
        industry_weight: float = _INDUSTRY_WEIGHT,
        cagr_boost: float = _CAGR_BOOST,
    ) -> None:
        self._default_weight = default_weight
        self._structural_weight = structural_weight
        self._industry_weight = industry_weight
        self._cagr_boost = cagr_boost
        logger.debug(
            "ScoreAggregator initialized",
            default_weight=default_weight,
            structural_weight=structural_weight,
            industry_weight=industry_weight,
            cagr_boost=cagr_boost,
        )

    def aggregate(
        self,
        scored_claims_by_ticker: dict[str, list[ScoredClaim]],
    ) -> dict[str, StockScore]:
        """Aggregate scored claims into per-stock scores.

        Parameters
        ----------
        scored_claims_by_ticker : dict[str, list[ScoredClaim]]
            Mapping of ticker to list of scored claims from Phase 2.
            Using explicit ticker keys avoids incorrect extraction from
            claim IDs containing hyphens (e.g. BRK-B).

        Returns
        -------
        dict[str, StockScore]
            Mapping of ticker to aggregated StockScore.
        """
        if not scored_claims_by_ticker:
            logger.info("No scored claims to aggregate")
            return {}

        total_claims = sum(len(v) for v in scored_claims_by_ticker.values())
        logger.info(
            "Aggregating claims",
            total_claims=total_claims,
            unique_tickers=len(scored_claims_by_ticker),
        )

        results: dict[str, StockScore] = {}
        for ticker, claims in scored_claims_by_ticker.items():
            if claims:
                results[ticker] = self._aggregate_ticker(ticker, claims)

        return results

    def _aggregate_ticker(
        self,
        ticker: str,
        claims: list[ScoredClaim],
    ) -> StockScore:
        """Compute the aggregate score for a single ticker.

        Parameters
        ----------
        ticker : str
            Ticker symbol.
        claims : list[ScoredClaim]
            Claims belonging to this ticker.

        Returns
        -------
        StockScore
            Aggregated score for the ticker.
        """
        total_weighted_score = 0.0
        total_weight = 0.0
        structural_weight_sum = 0.0

        for claim in claims:
            weight = self._compute_claim_weight(claim)
            confidence = claim.final_confidence

            # Apply CAGR connection boost/penalty to the confidence
            if claim.claim_type == "cagr_connection":
                if confidence >= _CAGR_CONFIDENCE_THRESHOLD:
                    confidence = confidence * (1.0 + self._cagr_boost)
                else:
                    confidence = confidence * (1.0 - self._cagr_boost)

            total_weighted_score += confidence * weight
            total_weight += weight

            # Track structural weight contribution
            if self._is_structural(claim):
                structural_weight_sum += weight

        # Weighted average
        raw_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # Clamp to [0, 1]
        aggregate_score = max(0.0, min(1.0, raw_score))

        # Structural weight ratio
        structural_ratio = (
            structural_weight_sum / total_weight if total_weight > 0 else 0.0
        )

        logger.debug(
            "Ticker aggregated",
            ticker=ticker,
            claim_count=len(claims),
            aggregate_score=round(aggregate_score, 4),
            structural_weight=round(structural_ratio, 4),
        )

        return StockScore(
            ticker=ticker,
            aggregate_score=aggregate_score,
            claim_count=len(claims),
            structural_weight=structural_ratio,
        )

    def _compute_claim_weight(self, claim: ScoredClaim) -> float:
        """Determine the weight for a claim based on its applied rules.

        When multiple rules apply, use the maximum weight.

        Parameters
        ----------
        claim : ScoredClaim
            The scored claim.

        Returns
        -------
        float
            The weight to apply.
        """
        applied = claim.rule_evaluation.applied_rules
        max_weight = self._default_weight

        for rule in applied:
            if rule == "rule_11":
                max_weight = max(max_weight, self._industry_weight)
            elif rule == "rule_6":
                max_weight = max(max_weight, self._structural_weight)

        return max_weight

    def _is_structural(self, claim: ScoredClaim) -> bool:
        """Check if a claim has structural advantage rules applied.

        A claim is considered structural if it has rule 6 (structural
        advantage) or rule 11 (industry structure match) in its applied
        rules.

        Parameters
        ----------
        claim : ScoredClaim
            The scored claim to check.

        Returns
        -------
        bool
            True if any structural rule was applied.
        """
        return bool(_STRUCTURAL_RULES.intersection(claim.rule_evaluation.applied_rules))


__all__ = ["ScoreAggregator"]
