"""Unit tests for market.industry.competitive_analysis module.

Tests cover the dogma.md 12 rules evaluation framework,
moat type and strength scoring, confidence level assessment,
and Porter's 5 Forces simplified evaluation.
"""

import pytest

from market.industry.competitive_analysis import (
    CompetitiveAnalyzer,
    evaluate_advantage_claim,
    evaluate_porter_forces,
    score_moat,
)
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

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def strong_capability_claim() -> AdvantageClaim:
    """A claim about a structural capability (should score high)."""
    return AdvantageClaim(
        claim="買収ターゲットの選定能力",
        evidence="買収基準の明確化、人員投入プロセス、精査過程が確立",
        ticker="CHD",
        is_quantitative=True,
        has_competitor_comparison=False,
        is_structural=True,
    )


@pytest.fixture()
def weak_result_claim() -> AdvantageClaim:
    """A claim about results, not capability (should score low)."""
    return AdvantageClaim(
        claim="買収ブランドが国際事業成長を加速",
        evidence="国際売上が成長",
        ticker="CHD",
        is_quantitative=False,
        has_competitor_comparison=False,
        is_structural=False,
    )


@pytest.fixture()
def industry_structure_claim() -> AdvantageClaim:
    """A claim with industry structure alignment (should score highest)."""
    return AdvantageClaim(
        claim="フラグメント市場におけるローカルな規模の経済",
        evidence=(
            "自動車アフターマーケットはフラグメント化された市場。"
            "ORLY は地域密度の高い店舗ネットワークで配送効率の"
            "構造的優位性を確立。AZO対比でDIFM補充頻度で優位。"
        ),
        ticker="ORLY",
        is_quantitative=True,
        has_competitor_comparison=True,
        is_structural=True,
    )


@pytest.fixture()
def industry_common_claim() -> AdvantageClaim:
    """A claim about an industry-common capability (should be rejected)."""
    return AdvantageClaim(
        claim="グローバル医療機関ネットワーク",
        evidence="世界各地の医療機関との関係",
        ticker="LLY",
        is_quantitative=False,
        has_competitor_comparison=False,
        is_structural=False,
        is_industry_common=True,
    )


# =============================================================================
# Tests for AdvantageClaim model
# =============================================================================


class TestAdvantageClaim:
    """Tests for AdvantageClaim Pydantic model."""

    def test_正常系_クレームを作成できる(self) -> None:
        claim = AdvantageClaim(
            claim="Test advantage",
            evidence="Test evidence",
            ticker="AAPL",
        )
        assert claim.claim == "Test advantage"
        assert claim.evidence == "Test evidence"
        assert claim.ticker == "AAPL"
        assert claim.is_quantitative is False
        assert claim.is_structural is False

    def test_正常系_全フィールドを指定して作成できる(self) -> None:
        claim = AdvantageClaim(
            claim="定量的優位性",
            evidence="退職率9% vs 業界20%+",
            ticker="COST",
            is_quantitative=True,
            has_competitor_comparison=True,
            is_structural=True,
            is_industry_common=False,
        )
        assert claim.is_quantitative is True
        assert claim.has_competitor_comparison is True
        assert claim.is_structural is True


# =============================================================================
# Tests for ConfidenceLevel
# =============================================================================


class TestConfidenceLevel:
    """Tests for ConfidenceLevel enum."""

    def test_正常系_全確信度レベルが定義されている(self) -> None:
        assert ConfidenceLevel.HIGHLY_CONVINCED.value == 90
        assert ConfidenceLevel.MOSTLY_CONVINCED.value == 70
        assert ConfidenceLevel.SOMEWHAT_CONVINCED.value == 50
        assert ConfidenceLevel.NOT_CONVINCED.value == 30
        assert ConfidenceLevel.REJECTED.value == 10


# =============================================================================
# Tests for MoatType
# =============================================================================


class TestMoatType:
    """Tests for MoatType enum."""

    def test_正常系_モート種別が定義されている(self) -> None:
        assert MoatType.BRAND_POWER is not None
        assert MoatType.SWITCHING_COST is not None
        assert MoatType.NETWORK_EFFECT is not None
        assert MoatType.COST_ADVANTAGE is not None
        assert MoatType.INTANGIBLE_ASSETS is not None
        assert MoatType.EFFICIENT_SCALE is not None
        assert MoatType.NONE is not None


# =============================================================================
# Tests for evaluate_advantage_claim
# =============================================================================


class TestEvaluateAdvantageClaim:
    """Tests for evaluate_advantage_claim function."""

    def test_正常系_構造的能力クレームは高評価(
        self, strong_capability_claim: AdvantageClaim
    ) -> None:
        result = evaluate_advantage_claim(strong_capability_claim)
        assert isinstance(result, AdvantageAssessment)
        assert result.confidence.value >= ConfidenceLevel.SOMEWHAT_CONVINCED.value
        assert len(result.rule_results) > 0

    def test_正常系_結果ベースのクレームは低評価(
        self, weak_result_claim: AdvantageClaim
    ) -> None:
        result = evaluate_advantage_claim(weak_result_claim)
        assert isinstance(result, AdvantageAssessment)
        assert result.confidence.value <= ConfidenceLevel.SOMEWHAT_CONVINCED.value

    def test_正常系_業界構造合致のクレームは最高評価(
        self, industry_structure_claim: AdvantageClaim
    ) -> None:
        result = evaluate_advantage_claim(industry_structure_claim)
        assert isinstance(result, AdvantageAssessment)
        assert result.confidence.value >= ConfidenceLevel.MOSTLY_CONVINCED.value

    def test_正常系_業界共通能力は低評価(
        self, industry_common_claim: AdvantageClaim
    ) -> None:
        result = evaluate_advantage_claim(industry_common_claim)
        assert isinstance(result, AdvantageAssessment)
        assert result.confidence.value <= ConfidenceLevel.NOT_CONVINCED.value

    def test_正常系_ルール結果が12個含まれる(
        self, strong_capability_claim: AdvantageClaim
    ) -> None:
        result = evaluate_advantage_claim(strong_capability_claim)
        assert len(result.rule_results) == 12

    def test_正常系_各ルール結果にルール番号と名前がある(
        self, strong_capability_claim: AdvantageClaim
    ) -> None:
        result = evaluate_advantage_claim(strong_capability_claim)
        for rule_result in result.rule_results:
            assert isinstance(rule_result, DogmaRuleResult)
            assert rule_result.rule_number >= 1
            assert rule_result.rule_number <= 12
            assert len(rule_result.rule_name) > 0


# =============================================================================
# Tests for score_moat
# =============================================================================


class TestScoreMoat:
    """Tests for score_moat function."""

    def test_正常系_評価結果からモートスコアを算出できる(self) -> None:
        assessments = [
            AdvantageAssessment(
                claim="ブランド力",
                confidence=ConfidenceLevel.MOSTLY_CONVINCED,
                rule_results=[],
                moat_type=MoatType.BRAND_POWER,
                adjustment_factors=[],
            ),
            AdvantageAssessment(
                claim="スイッチングコスト",
                confidence=ConfidenceLevel.HIGHLY_CONVINCED,
                rule_results=[],
                moat_type=MoatType.SWITCHING_COST,
                adjustment_factors=[],
            ),
        ]
        result = score_moat(assessments)
        assert isinstance(result, MoatScore)
        assert result.overall_score > 0
        assert result.strength != MoatStrength.NONE

    def test_正常系_空の評価リストでモートなし(self) -> None:
        result = score_moat([])
        assert isinstance(result, MoatScore)
        assert result.overall_score == 0
        assert result.strength == MoatStrength.NONE

    def test_正常系_全却下でモートなし(self) -> None:
        assessments = [
            AdvantageAssessment(
                claim="事実誤認",
                confidence=ConfidenceLevel.REJECTED,
                rule_results=[],
                moat_type=MoatType.NONE,
                adjustment_factors=[],
            ),
        ]
        result = score_moat(assessments)
        assert result.strength == MoatStrength.NONE

    def test_正常系_高評価複数でワイドモート(self) -> None:
        assessments = [
            AdvantageAssessment(
                claim="構造的優位性1",
                confidence=ConfidenceLevel.HIGHLY_CONVINCED,
                rule_results=[],
                moat_type=MoatType.COST_ADVANTAGE,
                adjustment_factors=[],
            ),
            AdvantageAssessment(
                claim="構造的優位性2",
                confidence=ConfidenceLevel.HIGHLY_CONVINCED,
                rule_results=[],
                moat_type=MoatType.SWITCHING_COST,
                adjustment_factors=[],
            ),
            AdvantageAssessment(
                claim="構造的優位性3",
                confidence=ConfidenceLevel.MOSTLY_CONVINCED,
                rule_results=[],
                moat_type=MoatType.BRAND_POWER,
                adjustment_factors=[],
            ),
        ]
        result = score_moat(assessments)
        assert result.strength == MoatStrength.WIDE

    def test_正常系_モートタイプ別スコアが含まれる(self) -> None:
        assessments = [
            AdvantageAssessment(
                claim="ブランド力",
                confidence=ConfidenceLevel.MOSTLY_CONVINCED,
                rule_results=[],
                moat_type=MoatType.BRAND_POWER,
                adjustment_factors=[],
            ),
        ]
        result = score_moat(assessments)
        assert MoatType.BRAND_POWER in result.moat_type_scores


# =============================================================================
# Tests for evaluate_porter_forces
# =============================================================================


class TestEvaluatePorterForces:
    """Tests for evaluate_porter_forces function."""

    def test_正常系_5フォース評価を実行できる(self) -> None:
        industry_data = {
            "market_concentration": "low",
            "entry_barriers": "high",
            "substitute_availability": "low",
            "supplier_concentration": "medium",
            "buyer_concentration": "low",
        }
        result = evaluate_porter_forces(industry_data)
        assert isinstance(result, PorterForcesAssessment)
        assert len(result.forces) == 5

    def test_正常系_各フォースにStrengthが設定される(self) -> None:
        industry_data = {
            "market_concentration": "high",
            "entry_barriers": "low",
            "substitute_availability": "high",
            "supplier_concentration": "high",
            "buyer_concentration": "high",
        }
        result = evaluate_porter_forces(industry_data)
        for force in result.forces:
            assert isinstance(force, PorterForce)
            assert isinstance(force.strength, PorterForceStrength)
            assert len(force.name) > 0

    def test_正常系_全体的な競争強度が算出される(self) -> None:
        industry_data = {
            "market_concentration": "low",
            "entry_barriers": "high",
            "substitute_availability": "low",
            "supplier_concentration": "low",
            "buyer_concentration": "low",
        }
        result = evaluate_porter_forces(industry_data)
        assert result.overall_intensity in ("low", "medium", "high")

    def test_エッジケース_空のデータでデフォルト評価(self) -> None:
        result = evaluate_porter_forces({})
        assert isinstance(result, PorterForcesAssessment)
        assert len(result.forces) == 5


# =============================================================================
# Tests for CompetitiveAnalyzer
# =============================================================================


class TestCompetitiveAnalyzer:
    """Tests for CompetitiveAnalyzer class."""

    def test_正常系_アナライザーを作成できる(self) -> None:
        analyzer = CompetitiveAnalyzer()
        assert analyzer is not None

    def test_正常系_クレームリストを一括評価できる(self) -> None:
        analyzer = CompetitiveAnalyzer()
        claims = [
            AdvantageClaim(
                claim="ブランド力",
                evidence="業界トップの認知度",
                ticker="AAPL",
                is_structural=True,
            ),
            AdvantageClaim(
                claim="エコシステム",
                evidence="ハードウェア・ソフトウェア・サービスの統合",
                ticker="AAPL",
                is_structural=True,
            ),
        ]
        results = analyzer.evaluate_claims(claims)
        assert len(results) == 2
        for result in results:
            assert isinstance(result, AdvantageAssessment)

    def test_正常系_全体スコアを算出できる(self) -> None:
        analyzer = CompetitiveAnalyzer()
        claims = [
            AdvantageClaim(
                claim="構造的優位性",
                evidence="フラグメント市場における規模の経済",
                ticker="ORLY",
                is_structural=True,
                is_quantitative=True,
                has_competitor_comparison=True,
            ),
        ]
        assessments = analyzer.evaluate_claims(claims)
        moat = analyzer.score_moat(assessments)
        assert isinstance(moat, MoatScore)
