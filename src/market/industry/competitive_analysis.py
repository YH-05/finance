"""Competitive advantage analysis based on dogma.md 12-rule framework.

This module programmatically applies the analyst_YK evaluation rules
from ``analyst/Competitive_Advantage/analyst_YK/dogma.md`` to assess
competitive advantage claims, compute moat type/strength scores, and
perform simplified Porter's 5 Forces evaluation.

Classes
-------
CompetitiveAnalyzer
    Orchestrator for competitive advantage assessment.

Functions
---------
evaluate_advantage_claim
    Apply dogma.md 12 rules to a single advantage claim.
score_moat
    Aggregate multiple assessments into a moat score.
evaluate_porter_forces
    Simplified Porter's 5 Forces evaluation from industry data.

See Also
--------
market.industry.types : Type definitions (AdvantageClaim, AdvantageAssessment, etc.).
market.industry.peer_groups : Peer group retrieval for competitive context.
"""

from __future__ import annotations

from market.industry.types import (
    AdvantageAssessment,
    AdvantageClaim,
    ConfidenceLevel,
    DogmaRuleResult,
    MoatScore,
    MoatStrength,
    MoatType,
    PorterForce,
    PorterForcesAssessment,
    PorterForceStrength,
)
from utils_core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Dogma Rule Definitions
# =============================================================================

_DOGMA_RULES: list[tuple[int, str]] = [
    (1, "能力・仕組み vs 結果・実績"),
    (2, "名詞属性 vs 動詞行動"),
    (3, "相対的優位性の要求"),
    (4, "定量的裏付け"),
    (5, "CAGR接続の直接性・検証可能性"),
    (6, "構造的要素 vs 補完的要素"),
    (7, "純粋競合に対する差別化"),
    (8, "戦略 ≠ 優位性"),
    (9, "事実誤認の即却下"),
    (10, "ネガティブケースによる裏付け"),
    (11, "業界構造とポジションの合致"),
    (12, "期初レポート主、四半期レビュー従"),
]
"""Dogma rule number-name pairs from the 12-rule evaluation framework."""


# =============================================================================
# Individual Rule Evaluation Functions
# =============================================================================


def _evaluate_rule_1(claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 1: Advantage is capability/mechanism, not result/achievement.

    Claims about outcomes (market share, revenue growth) are rejected.
    Claims about structural capabilities and mechanisms pass.
    """
    passed = claim.is_structural
    adjustment = 0 if passed else -30
    reasoning = (
        "クレームは構造的能力・仕組みを記述している"
        if passed
        else "クレームは結果・実績を記述しており、優位性の原因ではない"
    )
    return DogmaRuleResult(
        rule_number=1,
        rule_name="能力・仕組み vs 結果・実績",
        passed=passed,
        adjustment=adjustment,
        reasoning=reasoning,
    )


def _evaluate_rule_2(claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 2: Advantage is expressed as noun-attribute, not verb-action.

    Good: brand power, switching cost, ecosystem
    Bad: accelerating growth, shifting portfolio
    """
    passed = claim.is_structural
    adjustment = 0 if passed else -10
    reasoning = (
        "クレームは名詞的属性として表現されている"
        if passed
        else "クレームは動詞的行動（戦略実行）として表現されている"
    )
    return DogmaRuleResult(
        rule_number=2,
        rule_name="名詞属性 vs 動詞行動",
        passed=passed,
        adjustment=adjustment,
        reasoning=reasoning,
    )


def _evaluate_rule_3(claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 3: Relative advantage required (not industry-common).

    Claims about capabilities common across the industry are rejected.
    """
    passed = not claim.is_industry_common
    adjustment = 0 if passed else -30
    reasoning = (
        "クレームは競合に対して相対的に際立つ優位性を記述している"
        if passed
        else "クレームは業界共通の能力であり、差別化要因にならない"
    )
    return DogmaRuleResult(
        rule_number=3,
        rule_name="相対的優位性の要求",
        passed=passed,
        adjustment=adjustment,
        reasoning=reasoning,
    )


def _evaluate_rule_4(claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 4: Quantitative evidence increases conviction.

    Quantitative data (ratios, competitor comparisons) boost the score.
    """
    passed = claim.is_quantitative
    adjustment = 20 if passed else -10
    reasoning = (
        "定量的裏付けがあり、納得度が向上する"
        if passed
        else "定量的裏付けが不足しており、評価が限定的"
    )
    return DogmaRuleResult(
        rule_number=4,
        rule_name="定量的裏付け",
        passed=passed,
        adjustment=adjustment,
        reasoning=reasoning,
    )


def _evaluate_rule_5(_claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 5: CAGR connection requires direct mechanism and verifiability.

    This rule is about CAGR connection quality. Since claims don't
    typically include CAGR data, we return a neutral assessment.
    """
    return DogmaRuleResult(
        rule_number=5,
        rule_name="CAGR接続の直接性・検証可能性",
        passed=True,
        adjustment=0,
        reasoning="CAGR接続の評価は個別の優位性評価とは独立して実施",
    )


def _evaluate_rule_6(claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 6: Distinguish structural vs complementary elements.

    Structural elements (vendor negotiation power) score higher than
    complementary elements (gasoline sales).
    """
    passed = claim.is_structural
    adjustment = 10 if passed else -10
    reasoning = (
        "クレームは構造的要素を記述している"
        if passed
        else "クレームは補完的要素であり、構造的な優位性ではない"
    )
    return DogmaRuleResult(
        rule_number=6,
        rule_name="構造的要素 vs 補完的要素",
        passed=passed,
        adjustment=adjustment,
        reasoning=reasoning,
    )


def _evaluate_rule_7(claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 7: Differentiation against direct competitors required.

    Specific competitor comparisons (ORLY vs AZO) boost the score.
    """
    passed = claim.has_competitor_comparison
    adjustment = 15 if passed else -10
    reasoning = (
        "純粋競合に対する具体的な差別化が示されている"
        if passed
        else "純粋競合に対する差別化の根拠が不十分"
    )
    return DogmaRuleResult(
        rule_number=7,
        rule_name="純粋競合に対する差別化",
        passed=passed,
        adjustment=adjustment,
        reasoning=reasoning,
    )


def _evaluate_rule_8(claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 8: Strategy is not advantage.

    Strategy is a decision; advantage is the structural force that
    enables the strategy to work.
    """
    passed = claim.is_structural
    adjustment = 0 if passed else -20
    reasoning = (
        "クレームは戦略ではなく構造的優位性を記述している"
        if passed
        else "クレームは戦略（意思決定）であり、優位性（構造的力）ではない"
    )
    return DogmaRuleResult(
        rule_number=8,
        rule_name="戦略 ≠ 優位性",
        passed=passed,
        adjustment=adjustment,
        reasoning=reasoning,
    )


def _evaluate_rule_9(_claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 9: Factual errors are immediately rejected.

    This rule requires external verification; flagged via separate
    fact-checking process. Defaults to pass.
    """
    return DogmaRuleResult(
        rule_number=9,
        rule_name="事実誤認の即却下",
        passed=True,
        adjustment=0,
        reasoning="事実誤認は外部検証プロセスで確認",
    )


def _evaluate_rule_10(_claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 10: Negative cases (examples of restraint) boost conviction.

    Examples where the company declined to act (e.g. acquisition
    pass due to valuation) add credibility. Neutral by default.
    """
    return DogmaRuleResult(
        rule_number=10,
        rule_name="ネガティブケースによる裏付け",
        passed=True,
        adjustment=0,
        reasoning="ネガティブケースの有無は追加情報に依存",
    )


def _evaluate_rule_11(claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 11: Industry structure alignment scores highest.

    When market structure (fragmentation, density importance) aligns
    with the company's structural position, award maximum score.
    """
    has_alignment = (
        claim.is_structural
        and claim.has_competitor_comparison
        and claim.is_quantitative
    )
    passed = has_alignment
    adjustment = 30 if passed else 0
    reasoning = (
        "業界構造と企業ポジションが合致し、最高評価"
        if passed
        else "業界構造との合致評価には追加情報が必要"
    )
    return DogmaRuleResult(
        rule_number=11,
        rule_name="業界構造とポジションの合致",
        passed=passed,
        adjustment=adjustment,
        reasoning=reasoning,
    )


def _evaluate_rule_12(_claim: AdvantageClaim) -> DogmaRuleResult:
    """Rule 12: Initial report is primary, quarterly review is secondary.

    Be cautious about "discovering" new advantages from quarterly reviews.
    Neutral assessment as this requires source context.
    """
    return DogmaRuleResult(
        rule_number=12,
        rule_name="期初レポート主、四半期レビュー従",
        passed=True,
        adjustment=0,
        reasoning="情報ソースの優先順位は外部コンテキストに依存",
    )


_RULE_EVALUATORS: list = [
    _evaluate_rule_1,
    _evaluate_rule_2,
    _evaluate_rule_3,
    _evaluate_rule_4,
    _evaluate_rule_5,
    _evaluate_rule_6,
    _evaluate_rule_7,
    _evaluate_rule_8,
    _evaluate_rule_9,
    _evaluate_rule_10,
    _evaluate_rule_11,
    _evaluate_rule_12,
]
"""Ordered list of rule evaluator functions, indexed by rule number - 1."""


# =============================================================================
# Score Calculation Helpers
# =============================================================================


def _calculate_confidence(base_score: int) -> ConfidenceLevel:
    """Map a numeric score to the nearest ConfidenceLevel.

    Parameters
    ----------
    base_score : int
        Raw score before mapping (typically 10-90).

    Returns
    -------
    ConfidenceLevel
        The nearest confidence level.
    """
    if base_score >= 80:
        return ConfidenceLevel.HIGHLY_CONVINCED
    if base_score >= 60:
        return ConfidenceLevel.MOSTLY_CONVINCED
    if base_score >= 40:
        return ConfidenceLevel.SOMEWHAT_CONVINCED
    if base_score >= 20:
        return ConfidenceLevel.NOT_CONVINCED
    return ConfidenceLevel.REJECTED


def _classify_moat_strength(score: int) -> MoatStrength:
    """Classify moat strength from an overall score.

    Parameters
    ----------
    score : int
        Overall moat score (0-100).

    Returns
    -------
    MoatStrength
        Classified strength level.
    """
    if score >= 70:
        return MoatStrength.WIDE
    if score >= 40:
        return MoatStrength.NARROW
    return MoatStrength.NONE


# =============================================================================
# Public Functions
# =============================================================================


def evaluate_advantage_claim(claim: AdvantageClaim) -> AdvantageAssessment:
    """Apply dogma.md 12 rules to evaluate a competitive advantage claim.

    Each rule is evaluated independently against the claim, producing
    a ``DogmaRuleResult``. The overall confidence level is computed
    from a base score of 50 (neutral) adjusted by each rule's outcome.

    Parameters
    ----------
    claim : AdvantageClaim
        The advantage claim to evaluate.

    Returns
    -------
    AdvantageAssessment
        The assessment result with confidence level and rule details.

    Examples
    --------
    >>> claim = AdvantageClaim(
    ...     claim="買収ターゲットの選定能力",
    ...     evidence="買収基準の明確化",
    ...     ticker="CHD",
    ...     is_structural=True,
    ... )
    >>> result = evaluate_advantage_claim(claim)
    >>> result.confidence.value >= 50
    True
    """
    logger.debug(
        "Evaluating advantage claim",
        claim=claim.claim,
        ticker=claim.ticker,
    )

    rule_results: list[DogmaRuleResult] = []
    adjustment_factors: list[str] = []
    base_score = 50  # Neutral starting point

    for evaluator in _RULE_EVALUATORS:
        result = evaluator(claim)
        rule_results.append(result)

        if result.adjustment != 0:
            direction = "+" if result.adjustment > 0 else ""
            adjustment_factors.append(
                f"Rule {result.rule_number} ({result.rule_name}): "
                f"{direction}{result.adjustment}%"
            )
            base_score += result.adjustment

    # Clamp score to valid range
    clamped_score = max(10, min(90, base_score))
    confidence = _calculate_confidence(clamped_score)

    # Infer moat type from claim characteristics
    moat_type = _infer_moat_type(claim)

    assessment = AdvantageAssessment(
        claim=claim.claim,
        confidence=confidence,
        rule_results=rule_results,
        moat_type=moat_type,
        adjustment_factors=adjustment_factors,
    )

    logger.info(
        "Advantage claim evaluated",
        claim=claim.claim,
        ticker=claim.ticker,
        confidence=confidence.value,
        moat_type=moat_type.value,
        adjustment_count=len(adjustment_factors),
    )

    return assessment


def _infer_moat_type(claim: AdvantageClaim) -> MoatType:
    """Infer the moat type from claim text and characteristics.

    Uses keyword matching on the claim text to classify the moat type.
    This is a simplified heuristic; production use should integrate
    NLP-based classification.

    Parameters
    ----------
    claim : AdvantageClaim
        The advantage claim.

    Returns
    -------
    MoatType
        Inferred moat type.
    """
    claim_lower = claim.claim.lower()
    evidence_lower = claim.evidence.lower()
    combined = claim_lower + " " + evidence_lower

    # Brand-related keywords
    brand_keywords = [
        "ブランド",
        "brand",
        "認知",
        "awareness",
        "ロイヤルティ",
        "loyalty",
    ]
    if any(kw in combined for kw in brand_keywords):
        return MoatType.BRAND_POWER

    # Switching cost keywords
    switch_keywords = [
        "スイッチング",
        "switching",
        "移行コスト",
        "ロックイン",
        "lock-in",
        "粘着",
    ]
    if any(kw in combined for kw in switch_keywords):
        return MoatType.SWITCHING_COST

    # Network effect keywords
    network_keywords = [
        "ネットワーク効果",
        "network effect",
        "エコシステム",
        "ecosystem",
        "プラットフォーム",
        "platform",
    ]
    if any(kw in combined for kw in network_keywords):
        return MoatType.NETWORK_EFFECT

    # Cost advantage keywords
    cost_keywords = [
        "コスト優位",
        "cost advantage",
        "規模の経済",
        "economies of scale",
        "ベンダー交渉",
        "密度",
    ]
    if any(kw in combined for kw in cost_keywords):
        return MoatType.COST_ADVANTAGE

    # Intangible asset keywords
    intangible_keywords = [
        "特許",
        "patent",
        "ライセンス",
        "license",
        "技術力",
        "ノウハウ",
        "know-how",
        "買収",
    ]
    if any(kw in combined for kw in intangible_keywords):
        return MoatType.INTANGIBLE_ASSETS

    # Efficient scale keywords
    scale_keywords = [
        "効率的規模",
        "efficient scale",
        "参入障壁",
        "barrier",
    ]
    if any(kw in combined for kw in scale_keywords):
        return MoatType.EFFICIENT_SCALE

    return MoatType.NONE


def score_moat(assessments: list[AdvantageAssessment]) -> MoatScore:
    """Aggregate multiple advantage assessments into a moat score.

    Computes an overall score by weighting each assessment's confidence
    level, groups scores by moat type, and determines the dominant
    moat type and overall strength.

    Parameters
    ----------
    assessments : list[AdvantageAssessment]
        List of advantage assessments to aggregate.

    Returns
    -------
    MoatScore
        Aggregated moat score with type breakdown.

    Examples
    --------
    >>> assessments = [
    ...     AdvantageAssessment(
    ...         claim="ブランド力",
    ...         confidence=ConfidenceLevel.MOSTLY_CONVINCED,
    ...         rule_results=[],
    ...         moat_type=MoatType.BRAND_POWER,
    ...     ),
    ... ]
    >>> result = score_moat(assessments)
    >>> result.strength
    <MoatStrength.NARROW: 'narrow'>
    """
    logger.debug(
        "Scoring moat from assessments",
        assessment_count=len(assessments),
    )

    if not assessments:
        logger.info("No assessments provided, returning zero moat")
        return MoatScore(
            overall_score=0,
            strength=MoatStrength.NONE,
            moat_type_scores={},
            dominant_moat=MoatType.NONE,
            summary="評価対象の優位性クレームなし",
        )

    # Calculate per-moat-type scores
    moat_type_scores: dict[MoatType, list[int]] = {}
    for assessment in assessments:
        mt = assessment.moat_type
        if mt not in moat_type_scores:
            moat_type_scores[mt] = []
        moat_type_scores[mt].append(assessment.confidence.value)

    # Average scores per moat type
    averaged_scores: dict[MoatType, int] = {}
    for mt, scores in moat_type_scores.items():
        averaged_scores[mt] = sum(scores) // len(scores) if scores else 0

    # Overall score: weighted average of all confidence levels
    total_score = sum(a.confidence.value for a in assessments)
    overall_score = total_score // len(assessments)

    # Clamp to 0-100
    overall_score = max(0, min(100, overall_score))

    # Determine dominant moat type
    dominant_moat = MoatType.NONE
    max_type_score = 0
    for mt, avg_score in averaged_scores.items():
        if mt != MoatType.NONE and avg_score > max_type_score:
            max_type_score = avg_score
            dominant_moat = mt

    strength = _classify_moat_strength(overall_score)

    # Build summary
    summary_parts: list[str] = []
    if strength == MoatStrength.WIDE:
        summary_parts.append("強固な経済的モート")
    elif strength == MoatStrength.NARROW:
        summary_parts.append("限定的な経済的モート")
    else:
        summary_parts.append("有意な経済的モートなし")

    if dominant_moat != MoatType.NONE:
        summary_parts.append(f"主要モートタイプ: {dominant_moat.value}")

    summary = "。".join(summary_parts)

    moat_score = MoatScore(
        overall_score=overall_score,
        strength=strength,
        moat_type_scores=averaged_scores,
        dominant_moat=dominant_moat,
        summary=summary,
    )

    logger.info(
        "Moat scored",
        overall_score=overall_score,
        strength=strength.value,
        dominant_moat=dominant_moat.value,
        assessment_count=len(assessments),
    )

    return moat_score


def evaluate_porter_forces(
    industry_data: dict[str, str],
) -> PorterForcesAssessment:
    """Perform simplified Porter's 5 Forces evaluation.

    Maps industry data fields to the five competitive forces and
    computes an overall competitive intensity assessment.

    Parameters
    ----------
    industry_data : dict[str, str]
        Dictionary with keys such as ``"market_concentration"``,
        ``"entry_barriers"``, ``"substitute_availability"``,
        ``"supplier_concentration"``, ``"buyer_concentration"``.
        Values should be ``"low"``, ``"medium"``, or ``"high"``.

    Returns
    -------
    PorterForcesAssessment
        Assessment of all 5 forces with overall intensity.

    Examples
    --------
    >>> data = {
    ...     "market_concentration": "low",
    ...     "entry_barriers": "high",
    ...     "substitute_availability": "low",
    ...     "supplier_concentration": "medium",
    ...     "buyer_concentration": "low",
    ... }
    >>> result = evaluate_porter_forces(data)
    >>> result.overall_intensity
    'low'
    """
    logger.debug("Evaluating Porter's 5 Forces", data_keys=list(industry_data.keys()))

    forces: list[PorterForce] = [
        _evaluate_competitive_rivalry(industry_data),
        _evaluate_threat_of_new_entrants(industry_data),
        _evaluate_threat_of_substitutes(industry_data),
        _evaluate_supplier_power(industry_data),
        _evaluate_buyer_power(industry_data),
    ]

    # Calculate overall intensity
    strength_values = {"low": 1, "medium": 2, "high": 3}
    total = sum(strength_values.get(f.strength.value, 2) for f in forces)
    avg = total / len(forces) if forces else 2

    if avg >= 2.5:
        overall = "high"
    elif avg >= 1.5:
        overall = "medium"
    else:
        overall = "low"

    assessment = PorterForcesAssessment(
        forces=forces,
        overall_intensity=overall,
        summary=f"全体的な競争強度: {overall}",
    )

    logger.info(
        "Porter's 5 Forces evaluated",
        overall_intensity=overall,
        force_count=len(forces),
    )

    return assessment


def _map_strength(value: str | None) -> PorterForceStrength:
    """Map a string value to PorterForceStrength.

    Parameters
    ----------
    value : str | None
        Strength value ("low", "medium", "high").

    Returns
    -------
    PorterForceStrength
        Mapped strength, defaults to MEDIUM for unknown values.
    """
    mapping = {
        "low": PorterForceStrength.LOW,
        "medium": PorterForceStrength.MEDIUM,
        "high": PorterForceStrength.HIGH,
    }
    return mapping.get(value or "", PorterForceStrength.MEDIUM)


def _evaluate_competitive_rivalry(data: dict[str, str]) -> PorterForce:
    """Evaluate competitive rivalry force.

    Low market concentration = high rivalry (many competitors).
    """
    concentration = data.get("market_concentration", "medium")
    # Invert: low concentration = high rivalry
    rivalry_map = {"low": "high", "medium": "medium", "high": "low"}
    strength = _map_strength(rivalry_map.get(concentration, "medium"))
    return PorterForce(
        name="Competitive Rivalry",
        strength=strength,
        reasoning=f"市場集中度: {concentration} → 競争強度: {strength.value}",
    )


def _evaluate_threat_of_new_entrants(data: dict[str, str]) -> PorterForce:
    """Evaluate threat of new entrants.

    High entry barriers = low threat of new entrants.
    """
    barriers = data.get("entry_barriers", "medium")
    # Invert: high barriers = low threat
    threat_map = {"low": "high", "medium": "medium", "high": "low"}
    strength = _map_strength(threat_map.get(barriers, "medium"))
    return PorterForce(
        name="Threat of New Entrants",
        strength=strength,
        reasoning=f"参入障壁: {barriers} → 新規参入脅威: {strength.value}",
    )


def _evaluate_threat_of_substitutes(data: dict[str, str]) -> PorterForce:
    """Evaluate threat of substitute products.

    High substitute availability = high threat.
    """
    substitutes = data.get("substitute_availability", "medium")
    strength = _map_strength(substitutes)
    return PorterForce(
        name="Threat of Substitutes",
        strength=strength,
        reasoning=f"代替品の利用可能性: {substitutes} → 代替品脅威: {strength.value}",
    )


def _evaluate_supplier_power(data: dict[str, str]) -> PorterForce:
    """Evaluate bargaining power of suppliers.

    High supplier concentration = high supplier power.
    """
    supplier_conc = data.get("supplier_concentration", "medium")
    strength = _map_strength(supplier_conc)
    return PorterForce(
        name="Bargaining Power of Suppliers",
        strength=strength,
        reasoning=f"サプライヤー集中度: {supplier_conc} → 交渉力: {strength.value}",
    )


def _evaluate_buyer_power(data: dict[str, str]) -> PorterForce:
    """Evaluate bargaining power of buyers.

    High buyer concentration = high buyer power.
    """
    buyer_conc = data.get("buyer_concentration", "medium")
    strength = _map_strength(buyer_conc)
    return PorterForce(
        name="Bargaining Power of Buyers",
        strength=strength,
        reasoning=f"バイヤー集中度: {buyer_conc} → 交渉力: {strength.value}",
    )


# =============================================================================
# CompetitiveAnalyzer Class
# =============================================================================


class CompetitiveAnalyzer:
    """Orchestrator for competitive advantage assessment.

    Provides a unified interface for evaluating multiple advantage
    claims and computing aggregate moat scores.

    Examples
    --------
    >>> analyzer = CompetitiveAnalyzer()
    >>> claims = [
    ...     AdvantageClaim(
    ...         claim="ブランド力",
    ...         evidence="業界トップの認知度",
    ...         ticker="AAPL",
    ...         is_structural=True,
    ...     ),
    ... ]
    >>> assessments = analyzer.evaluate_claims(claims)
    >>> moat = analyzer.score_moat(assessments)
    >>> moat.strength
    <MoatStrength.NARROW: 'narrow'>
    """

    def evaluate_claims(
        self,
        claims: list[AdvantageClaim],
    ) -> list[AdvantageAssessment]:
        """Evaluate a list of advantage claims.

        Parameters
        ----------
        claims : list[AdvantageClaim]
            List of claims to evaluate.

        Returns
        -------
        list[AdvantageAssessment]
            Assessment results for each claim.
        """
        logger.info(
            "Evaluating multiple advantage claims",
            claim_count=len(claims),
        )
        return [evaluate_advantage_claim(claim) for claim in claims]

    def score_moat(
        self,
        assessments: list[AdvantageAssessment],
    ) -> MoatScore:
        """Compute aggregate moat score from assessments.

        Parameters
        ----------
        assessments : list[AdvantageAssessment]
            List of advantage assessments.

        Returns
        -------
        MoatScore
            Aggregated moat score.
        """
        return score_moat(assessments)

    def evaluate_porter_forces(
        self,
        industry_data: dict[str, str],
    ) -> PorterForcesAssessment:
        """Evaluate Porter's 5 Forces for the given industry data.

        Parameters
        ----------
        industry_data : dict[str, str]
            Industry data with force-level information.

        Returns
        -------
        PorterForcesAssessment
            Complete 5 Forces assessment.
        """
        return evaluate_porter_forces(industry_data)


__all__ = [
    "CompetitiveAnalyzer",
    "evaluate_advantage_claim",
    "evaluate_porter_forces",
    "score_moat",
]
