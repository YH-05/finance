"""Tests for ca_strategy scorer module (Phase 2 KB1/KB2/KB3 scoring).

Validates ClaimScorer class for scoring competitive advantage claims
using KB1-T/KB2-T/KB3-T rules and dogma.md evaluation criteria.
All LLM calls are mocked for unit testing.
"""

from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from dev.ca_strategy.cost import CostTracker
from dev.ca_strategy.scorer import ClaimScorer
from dev.ca_strategy.types import (
    Claim,
    ConfidenceAdjustment,
    RuleEvaluation,
    ScoredClaim,
)

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def kb1_dir(tmp_path: Path) -> Path:
    """Create a temporary KB1-T rules directory with sample rule files."""
    kb1 = tmp_path / "kb1_rules_transcript"
    kb1.mkdir()
    (kb1 / "rule01_capability_not_result.md").write_text(
        "# Rule 1-T: Capability not result\nTest rule content."
    )
    (kb1 / "rule04_quantitative_evidence.md").write_text(
        "# Rule 4-T: Quantitative evidence\nTest rule content."
    )
    return kb1


@pytest.fixture
def kb2_dir(tmp_path: Path) -> Path:
    """Create a temporary KB2-T patterns directory with rejection and high-rating files."""
    kb2 = tmp_path / "kb2_patterns_transcript"
    kb2.mkdir()
    (kb2 / "pattern_A_result_as_cause.md").write_text(
        "# Rejection Pattern A-T: Result as cause\n"
        "## 種別: 却下パターン\n## 確信度: 却下〜30%\nTest pattern."
    )
    (kb2 / "pattern_B_industry_common.md").write_text(
        "# Rejection Pattern B-T: Industry common\n"
        "## 種別: 却下パターン\n## 確信度: 却下〜30%\nTest pattern."
    )
    (kb2 / "pattern_I_quantitative_differentiation.md").write_text(
        "# High-rating Pattern I-T: Quantitative differentiation\n"
        "## 種別: 高評価パターン\n## 確信度: 70-90%\nTest pattern."
    )
    (kb2 / "pattern_II_direct_cagr_mechanism.md").write_text(
        "# High-rating Pattern II-T: Direct CAGR mechanism\n"
        "## 種別: 高評価パターン\n## 確信度: 70-90%\nTest pattern."
    )
    return kb2


@pytest.fixture
def kb3_dir(tmp_path: Path) -> Path:
    """Create a temporary KB3-T few-shot directory with sample files."""
    kb3 = tmp_path / "kb3_fewshot_transcript"
    kb3.mkdir()
    (kb3 / "fewshot_ORLY.md").write_text(
        "# few-shot: ORLY\nSample few-shot evaluation with 70% confidence."
    )
    (kb3 / "fewshot_COST.md").write_text(
        "# few-shot: COST\nSample few-shot evaluation with 50% confidence."
    )
    return kb3


@pytest.fixture
def dogma_path(tmp_path: Path) -> Path:
    """Create a temporary dogma.md file."""
    dogma_file = tmp_path / "dogma.md"
    dogma_file.write_text(
        "# Dogma\n\n"
        "KY rules for evaluation.\n\n"
        "## ゲートキーパールール\n"
        "- ルール9: 事実誤認は即却下 → confidence: 10\n"
        "- ルール3: 業界共通能力は 30% 以下\n"
    )
    return dogma_file


@pytest.fixture
def cost_tracker() -> CostTracker:
    """Create a CostTracker instance."""
    return CostTracker()


@pytest.fixture
def sample_claims() -> dict[str, list[Claim]]:
    """Create sample claims grouped by ticker for scoring."""
    return {
        "AAPL": [
            Claim(
                id="AAPL-CA-001",
                claim_type="competitive_advantage",
                claim="Proprietary silicon design capability",
                evidence="CEO: Our silicon advantage compounds every year.",
                rule_evaluation=RuleEvaluation(
                    applied_rules=["rule_1_t", "rule_4_t"],
                    results={"rule_1_t": True, "rule_4_t": True},
                    confidence=0.7,
                    adjustments=["Strong structural advantage"],
                ),
            ),
            Claim(
                id="AAPL-CAGR-002",
                claim_type="cagr_connection",
                claim="Silicon -> ASP maintenance -> Revenue CAGR +2pp",
                evidence="CEO: This drives our pricing power.",
                rule_evaluation=RuleEvaluation(
                    applied_rules=["rule_5_t"],
                    results={"rule_5_t": True},
                    confidence=0.6,
                    adjustments=["Direct mechanism"],
                ),
            ),
        ],
        "MSFT": [
            Claim(
                id="MSFT-CA-001",
                claim_type="competitive_advantage",
                claim="Enterprise cloud platform lock-in via Azure",
                evidence="CFO: Azure revenue grew 29% YoY.",
                rule_evaluation=RuleEvaluation(
                    applied_rules=["rule_1_t", "rule_6_t"],
                    results={"rule_1_t": True, "rule_6_t": True},
                    confidence=0.5,
                    adjustments=[],
                ),
            ),
        ],
    }


@pytest.fixture
def sample_gatekeeper_claim_rule9() -> Claim:
    """Create a claim with factual error (Rule 9 -> confidence 10)."""
    return Claim(
        id="TEST-CA-R9",
        claim_type="competitive_advantage",
        claim="Market share is 85% globally",
        evidence="CEO stated 85% market share, but actual data shows 12%.",
        rule_evaluation=RuleEvaluation(
            applied_rules=["rule_9_t"],
            results={"rule_9_t": False},
            confidence=0.1,
            adjustments=["Factual error detected"],
        ),
    )


@pytest.fixture
def sample_gatekeeper_claim_rule3() -> Claim:
    """Create a claim with industry-common capability (Rule 3 -> confidence <= 30)."""
    return Claim(
        id="TEST-CA-R3",
        claim_type="competitive_advantage",
        claim="Strong customer service",
        evidence="CEO: We provide excellent customer service.",
        rule_evaluation=RuleEvaluation(
            applied_rules=["rule_3_t"],
            results={"rule_3_t": False},
            confidence=0.3,
            adjustments=["Industry common capability"],
        ),
    )


@pytest.fixture
def sample_llm_scoring_response() -> str:
    """Create a sample LLM JSON response for scoring."""
    return json.dumps(
        {
            "scored_claims": [
                {
                    "id": "AAPL-CA-001",
                    "claim_type": "competitive_advantage",
                    "claim": "Proprietary silicon design capability",
                    "evidence": "CEO: Our silicon advantage compounds every year.",
                    "gatekeeper": {
                        "rule9_factual_error": False,
                        "rule3_industry_common": False,
                    },
                    "kb2_patterns": [
                        {
                            "pattern": "pattern_I",
                            "match": True,
                            "adjustment": 0.1,
                            "reasoning": "Quantitative differentiation present",
                        }
                    ],
                    "final_confidence": 0.7,
                    "confidence_adjustments": [
                        {
                            "source": "pattern_I",
                            "adjustment": 0.1,
                            "reasoning": "Quantitative differentiation present",
                        }
                    ],
                    "overall_reasoning": "Strong structural advantage with quantitative support",
                }
            ]
        },
        ensure_ascii=False,
    )


@pytest.fixture
def scorer(
    kb1_dir: Path,
    kb2_dir: Path,
    kb3_dir: Path,
    dogma_path: Path,
    cost_tracker: CostTracker,
) -> ClaimScorer:
    """Create a ClaimScorer instance for testing."""
    return ClaimScorer(
        kb1_dir=kb1_dir,
        kb2_dir=kb2_dir,
        kb3_dir=kb3_dir,
        dogma_path=dogma_path,
        cost_tracker=cost_tracker,
    )


# =============================================================================
# ClaimScorer initialization
# =============================================================================
class TestClaimScorerInit:
    """ClaimScorer initialization tests."""

    def test_正常系_初期化でKB1ファイルが読み込まれる(
        self,
        scorer: ClaimScorer,
    ) -> None:
        assert scorer._kb1_rules is not None
        assert len(scorer._kb1_rules) == 2

    def test_正常系_KB2パターンが読み込まれる(
        self,
        scorer: ClaimScorer,
    ) -> None:
        assert scorer._kb2_patterns is not None
        assert len(scorer._kb2_patterns) == 4  # 2 rejection + 2 high-rating

    def test_正常系_KB3_fewshotが読み込まれる(
        self,
        scorer: ClaimScorer,
    ) -> None:
        assert scorer._kb3_examples is not None
        assert len(scorer._kb3_examples) == 2

    def test_正常系_dogmaが読み込まれる(
        self,
        scorer: ClaimScorer,
    ) -> None:
        assert scorer._dogma is not None
        assert "ゲートキーパールール" in scorer._dogma

    def test_正常系_コストトラッカーが設定される(
        self,
        scorer: ClaimScorer,
    ) -> None:
        assert scorer._cost_tracker is not None

    def test_異常系_KB1ディレクトリが存在しない場合(
        self,
        tmp_path: Path,
        kb2_dir: Path,
        kb3_dir: Path,
        dogma_path: Path,
        cost_tracker: CostTracker,
    ) -> None:
        non_existent = tmp_path / "non_existent_kb1"
        s = ClaimScorer(
            kb1_dir=non_existent,
            kb2_dir=kb2_dir,
            kb3_dir=kb3_dir,
            dogma_path=dogma_path,
            cost_tracker=cost_tracker,
        )
        assert len(s._kb1_rules) == 0

    def test_異常系_KB2ディレクトリが存在しない場合(
        self,
        kb1_dir: Path,
        tmp_path: Path,
        kb3_dir: Path,
        dogma_path: Path,
        cost_tracker: CostTracker,
    ) -> None:
        non_existent = tmp_path / "non_existent_kb2"
        s = ClaimScorer(
            kb1_dir=kb1_dir,
            kb2_dir=non_existent,
            kb3_dir=kb3_dir,
            dogma_path=dogma_path,
            cost_tracker=cost_tracker,
        )
        assert len(s._kb2_patterns) == 0

    def test_異常系_KB3ディレクトリが存在しない場合(
        self,
        kb1_dir: Path,
        kb2_dir: Path,
        tmp_path: Path,
        dogma_path: Path,
        cost_tracker: CostTracker,
    ) -> None:
        non_existent = tmp_path / "non_existent_kb3"
        s = ClaimScorer(
            kb1_dir=kb1_dir,
            kb2_dir=kb2_dir,
            kb3_dir=non_existent,
            dogma_path=dogma_path,
            cost_tracker=cost_tracker,
        )
        assert len(s._kb3_examples) == 0

    def test_異常系_dogmaファイルが存在しない場合(
        self,
        kb1_dir: Path,
        kb2_dir: Path,
        kb3_dir: Path,
        tmp_path: Path,
        cost_tracker: CostTracker,
    ) -> None:
        non_existent = tmp_path / "non_existent_dogma.md"
        s = ClaimScorer(
            kb1_dir=kb1_dir,
            kb2_dir=kb2_dir,
            kb3_dir=kb3_dir,
            dogma_path=non_existent,
            cost_tracker=cost_tracker,
        )
        assert s._dogma == ""


# =============================================================================
# ClaimScorer._build_scoring_prompt
# =============================================================================
class TestBuildScoringPrompt:
    """Tests for _build_scoring_prompt method."""

    def test_正常系_プロンプトにクレーム情報が含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        prompt = scorer._build_scoring_prompt(
            claims=sample_claims["AAPL"],
            ticker="AAPL",
        )
        assert "AAPL-CA-001" in prompt
        assert "Proprietary silicon design" in prompt

    def test_正常系_プロンプトにKB1ルールが含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        prompt = scorer._build_scoring_prompt(
            claims=sample_claims["AAPL"],
            ticker="AAPL",
        )
        assert "Rule 1-T" in prompt or "Capability not result" in prompt

    def test_正常系_プロンプトにKB2パターンが含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        prompt = scorer._build_scoring_prompt(
            claims=sample_claims["AAPL"],
            ticker="AAPL",
        )
        assert "pattern_A" in prompt or "Result as cause" in prompt

    def test_正常系_プロンプトにKB3_fewshotが含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        prompt = scorer._build_scoring_prompt(
            claims=sample_claims["AAPL"],
            ticker="AAPL",
        )
        assert "ORLY" in prompt or "few-shot" in prompt

    def test_正常系_プロンプトにdogmaが含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        prompt = scorer._build_scoring_prompt(
            claims=sample_claims["AAPL"],
            ticker="AAPL",
        )
        assert "ゲートキーパールール" in prompt or "dogma" in prompt.lower()

    def test_正常系_プロンプトにゲートキーパー指示が含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        prompt = scorer._build_scoring_prompt(
            claims=sample_claims["AAPL"],
            ticker="AAPL",
        )
        assert (
            "ルール9" in prompt
            or "事実誤認" in prompt
            or "gatekeeper" in prompt.lower()
        )

    def test_正常系_出力形式の指示が含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        prompt = scorer._build_scoring_prompt(
            claims=sample_claims["AAPL"],
            ticker="AAPL",
        )
        assert "scored_claims" in prompt or "final_confidence" in prompt


# =============================================================================
# ClaimScorer._parse_scoring_response
# =============================================================================
class TestParseScoringResponse:
    """Tests for _parse_scoring_response method."""

    def test_正常系_有効なJSONからScoredClaimリストをパースできる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        scored = scorer._parse_scoring_response(
            response_text=sample_llm_scoring_response,
            original_claims=sample_claims["AAPL"],
        )
        assert len(scored) > 0
        assert all(isinstance(s, ScoredClaim) for s in scored)

    def test_正常系_final_confidenceが0_1の範囲で設定される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        scored = scorer._parse_scoring_response(
            response_text=sample_llm_scoring_response,
            original_claims=sample_claims["AAPL"],
        )
        for s in scored:
            assert 0.0 <= s.final_confidence <= 1.0

    def test_正常系_confidence_adjustmentsが含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        scored = scorer._parse_scoring_response(
            response_text=sample_llm_scoring_response,
            original_claims=sample_claims["AAPL"],
        )
        assert len(scored) > 0
        assert isinstance(scored[0].adjustments, list)
        for adj in scored[0].adjustments:
            assert isinstance(adj, ConfidenceAdjustment)

    def test_正常系_元のClaim情報が保持される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        scored = scorer._parse_scoring_response(
            response_text=sample_llm_scoring_response,
            original_claims=sample_claims["AAPL"],
        )
        assert len(scored) > 0
        assert scored[0].id == "AAPL-CA-001"
        assert scored[0].claim_type == "competitive_advantage"
        assert scored[0].claim == "Proprietary silicon design capability"

    def test_異常系_不正なJSONで空リストが返される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        scored = scorer._parse_scoring_response(
            response_text="not valid json {{{",
            original_claims=sample_claims["AAPL"],
        )
        assert scored == []

    def test_異常系_scored_claims_keyが欠落したJSONで空リストが返される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        scored = scorer._parse_scoring_response(
            response_text='{"ticker": "AAPL"}',
            original_claims=sample_claims["AAPL"],
        )
        assert scored == []

    def test_正常系_JSONがコードブロックに包まれている場合も対応(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        wrapped = f"```json\n{sample_llm_scoring_response}\n```"
        scored = scorer._parse_scoring_response(
            response_text=wrapped,
            original_claims=sample_claims["AAPL"],
        )
        assert len(scored) > 0

    def test_正常系_confidenceが100段階の場合0_1に正規化される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        response = json.dumps(
            {
                "scored_claims": [
                    {
                        "id": "AAPL-CA-001",
                        "final_confidence": 70,
                        "confidence_adjustments": [],
                        "gatekeeper": {
                            "rule9_factual_error": False,
                            "rule3_industry_common": False,
                        },
                        "kb2_patterns": [],
                        "overall_reasoning": "Test",
                    }
                ]
            }
        )
        scored = scorer._parse_scoring_response(
            response_text=response,
            original_claims=sample_claims["AAPL"],
        )
        assert len(scored) > 0
        assert scored[0].final_confidence == 0.7


# =============================================================================
# ClaimScorer._score_single_ticker (LLM call)
# =============================================================================
class TestScoreSingleTicker:
    """Tests for _score_single_ticker method."""

    def test_正常系_LLM呼び出しでScoredClaimリストが返される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_scoring_response)]
        mock_message.usage.input_tokens = 2000
        mock_message.usage.output_tokens = 1000

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            scored = scorer._score_single_ticker(
                claims=sample_claims["AAPL"],
                ticker="AAPL",
            )

        assert len(scored) > 0
        assert all(isinstance(s, ScoredClaim) for s in scored)

    def test_正常系_CostTrackerにPhase2トークン数が記録される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_scoring_response)]
        mock_message.usage.input_tokens = 3000
        mock_message.usage.output_tokens = 1500

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            scorer._score_single_ticker(
                claims=sample_claims["AAPL"],
                ticker="AAPL",
            )

        assert scorer._cost_tracker.get_phase_cost("phase2") > 0

    def test_異常系_LLM呼び出しが例外を投げた場合に空リストが返される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        with patch.object(
            scorer._client.messages,
            "create",
            side_effect=Exception("API error"),
        ):
            scored = scorer._score_single_ticker(
                claims=sample_claims["AAPL"],
                ticker="AAPL",
            )

        assert scored == []


# =============================================================================
# ClaimScorer.score_batch
# =============================================================================
class TestScoreBatch:
    """Tests for score_batch method."""

    def test_正常系_複数ティッカーのクレームがスコアリングされる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_scoring_response)]
        mock_message.usage.input_tokens = 2000
        mock_message.usage.output_tokens = 1000

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            result = scorer.score_batch(claims=sample_claims)

        assert "AAPL" in result
        assert "MSFT" in result

    def test_正常系_空のクレームで空の結果が返される(
        self,
        scorer: ClaimScorer,
    ) -> None:
        result = scorer.score_batch(claims={})
        assert result == {}

    def test_正常系_出力ディレクトリにJSONが保存される(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
        tmp_path: Path,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_scoring_response)]
        mock_message.usage.input_tokens = 2000
        mock_message.usage.output_tokens = 1000

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            scorer.score_batch(
                claims=sample_claims,
                output_dir=tmp_path,
            )

        # Check AAPL output directory exists
        aapl_dir = tmp_path / "AAPL"
        assert aapl_dir.exists()

    def test_正常系_結果にScoredClaimが含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
        sample_llm_scoring_response: str,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_scoring_response)]
        mock_message.usage.input_tokens = 2000
        mock_message.usage.output_tokens = 1000

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            result = scorer.score_batch(claims=sample_claims)

        for ticker_claims in result.values():
            for claim in ticker_claims:
                assert isinstance(claim, ScoredClaim)


# =============================================================================
# Gatekeeper rules validation
# =============================================================================
class TestGatekeeperRules:
    """Tests for gatekeeper rule validation in scoring responses."""

    def test_正常系_ルール9_事実誤認はconfidence_10になる(
        self,
        scorer: ClaimScorer,
        sample_gatekeeper_claim_rule9: Claim,
    ) -> None:
        response = json.dumps(
            {
                "scored_claims": [
                    {
                        "id": "TEST-CA-R9",
                        "final_confidence": 10,
                        "gatekeeper": {
                            "rule9_factual_error": True,
                            "rule3_industry_common": False,
                        },
                        "kb2_patterns": [],
                        "confidence_adjustments": [
                            {
                                "source": "gatekeeper_rule9",
                                "adjustment": -0.6,
                                "reasoning": "Factual error detected: "
                                "claimed 85% market share, actual is 12%",
                            }
                        ],
                        "overall_reasoning": "Immediate rejection due to factual error",
                    }
                ]
            }
        )

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=response)]
        mock_message.usage.input_tokens = 1000
        mock_message.usage.output_tokens = 500

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            scored = scorer._score_single_ticker(
                claims=[sample_gatekeeper_claim_rule9],
                ticker="TEST",
            )

        assert len(scored) > 0
        assert scored[0].final_confidence == 0.1

    def test_正常系_ルール3_業界共通はconfidence_30以下になる(
        self,
        scorer: ClaimScorer,
        sample_gatekeeper_claim_rule3: Claim,
    ) -> None:
        response = json.dumps(
            {
                "scored_claims": [
                    {
                        "id": "TEST-CA-R3",
                        "final_confidence": 30,
                        "gatekeeper": {
                            "rule9_factual_error": False,
                            "rule3_industry_common": True,
                        },
                        "kb2_patterns": [],
                        "confidence_adjustments": [
                            {
                                "source": "gatekeeper_rule3",
                                "adjustment": -0.4,
                                "reasoning": "Industry-common capability, "
                                "not a differentiator",
                            }
                        ],
                        "overall_reasoning": "Industry-standard capability",
                    }
                ]
            }
        )

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=response)]
        mock_message.usage.input_tokens = 1000
        mock_message.usage.output_tokens = 500

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            scored = scorer._score_single_ticker(
                claims=[sample_gatekeeper_claim_rule3],
                ticker="TEST",
            )

        assert len(scored) > 0
        assert scored[0].final_confidence <= 0.3


# =============================================================================
# KB2 patterns validation
# =============================================================================
class TestKb2Patterns:
    """Tests for KB2 pattern matching in scoring responses."""

    def test_正常系_却下パターンA_Gで確信度が低下する(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        response = json.dumps(
            {
                "scored_claims": [
                    {
                        "id": "AAPL-CA-001",
                        "final_confidence": 40,
                        "gatekeeper": {
                            "rule9_factual_error": False,
                            "rule3_industry_common": False,
                        },
                        "kb2_patterns": [
                            {
                                "pattern": "pattern_A",
                                "match": True,
                                "adjustment": -0.2,
                                "reasoning": "Result presented as cause",
                            }
                        ],
                        "confidence_adjustments": [
                            {
                                "source": "pattern_A",
                                "adjustment": -0.2,
                                "reasoning": "Result presented as cause",
                            }
                        ],
                        "overall_reasoning": "Rejection pattern A detected",
                    }
                ]
            }
        )

        scored = scorer._parse_scoring_response(
            response_text=response,
            original_claims=sample_claims["AAPL"],
        )

        assert len(scored) > 0
        assert scored[0].final_confidence < 0.7  # Lower than original 0.7
        # Check that adjustment is negative
        has_negative_adj = any(a.adjustment < 0 for a in scored[0].adjustments)
        assert has_negative_adj

    def test_正常系_高評価パターンI_Vで確信度が向上する(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        response = json.dumps(
            {
                "scored_claims": [
                    {
                        "id": "AAPL-CA-001",
                        "final_confidence": 80,
                        "gatekeeper": {
                            "rule9_factual_error": False,
                            "rule3_industry_common": False,
                        },
                        "kb2_patterns": [
                            {
                                "pattern": "pattern_I",
                                "match": True,
                                "adjustment": 0.2,
                                "reasoning": "Quantitative differentiation present",
                            }
                        ],
                        "confidence_adjustments": [
                            {
                                "source": "pattern_I",
                                "adjustment": 0.2,
                                "reasoning": "Quantitative differentiation present",
                            }
                        ],
                        "overall_reasoning": "Strong quantitative support",
                    }
                ]
            }
        )

        scored = scorer._parse_scoring_response(
            response_text=response,
            original_claims=sample_claims["AAPL"],
        )

        assert len(scored) > 0
        assert scored[0].final_confidence >= 0.7
        # Check that adjustment is positive
        has_positive_adj = any(a.adjustment > 0 for a in scored[0].adjustments)
        assert has_positive_adj


# =============================================================================
# KB3 calibration
# =============================================================================
class TestKb3Calibration:
    """Tests for KB3 calibration distribution targets."""

    def test_正常系_プロンプトに分布目標が含まれる(
        self,
        scorer: ClaimScorer,
        sample_claims: dict[str, list[Claim]],
    ) -> None:
        prompt = scorer._build_scoring_prompt(
            claims=sample_claims["AAPL"],
            ticker="AAPL",
        )
        # Distribution targets: 90%:6%, 70%:26%, 50%:35%, 30%:26%, 10%:6%
        assert "90" in prompt or "6%" in prompt
        assert "50" in prompt or "35%" in prompt


# =============================================================================
# Output persistence
# =============================================================================
class TestOutputPersistence:
    """Tests for saving scored claims to JSON files."""

    def test_正常系_スコア結果がJSONファイルに保存される(
        self,
        scorer: ClaimScorer,
        tmp_path: Path,
    ) -> None:
        scored_claims = [
            ScoredClaim(
                id="AAPL-CA-001",
                claim_type="competitive_advantage",
                claim="Proprietary silicon design",
                evidence="CEO: Our silicon advantage compounds.",
                rule_evaluation=RuleEvaluation(
                    applied_rules=["rule_1_t"],
                    results={"rule_1_t": True},
                    confidence=0.7,
                    adjustments=["Strong structural"],
                ),
                final_confidence=0.7,
                adjustments=[
                    ConfidenceAdjustment(
                        source="pattern_I",
                        adjustment=0.1,
                        reasoning="Quantitative support",
                    )
                ],
            )
        ]

        scorer._save_scored_claims(
            scored_claims=scored_claims,
            ticker="AAPL",
            output_dir=tmp_path,
        )

        # Find the output file
        aapl_dir = tmp_path / "AAPL"
        assert aapl_dir.exists()
        output_file = aapl_dir / "scored.json"
        assert output_file.exists()

        data = json.loads(output_file.read_text())
        assert "scored_claims" in data
        assert data["ticker"] == "AAPL"

    def test_正常系_保存されたJSONにconfidence_adjustmentsが含まれる(
        self,
        scorer: ClaimScorer,
        tmp_path: Path,
    ) -> None:
        scored_claims = [
            ScoredClaim(
                id="AAPL-CA-001",
                claim_type="competitive_advantage",
                claim="Proprietary silicon design",
                evidence="CEO: Our silicon advantage compounds.",
                rule_evaluation=RuleEvaluation(
                    applied_rules=["rule_1_t"],
                    results={"rule_1_t": True},
                    confidence=0.7,
                    adjustments=["Strong structural"],
                ),
                final_confidence=0.7,
                adjustments=[
                    ConfidenceAdjustment(
                        source="pattern_I",
                        adjustment=0.1,
                        reasoning="Quantitative support",
                    )
                ],
            )
        ]

        scorer._save_scored_claims(
            scored_claims=scored_claims,
            ticker="AAPL",
            output_dir=tmp_path,
        )

        aapl_dir = tmp_path / "AAPL"
        output_file = aapl_dir / "scored.json"
        data = json.loads(output_file.read_text())

        claim_data = data["scored_claims"][0]
        assert "adjustments" in claim_data
        assert len(claim_data["adjustments"]) > 0
        assert claim_data["adjustments"][0]["source"] == "pattern_I"


# =============================================================================
# Edge cases
# =============================================================================
class TestEdgeCases:
    """Tests for edge cases in scoring."""

    def test_エッジケース_空のクレームリストで空結果が返される(
        self,
        scorer: ClaimScorer,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"scored_claims": []}')]
        mock_message.usage.input_tokens = 100
        mock_message.usage.output_tokens = 50

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            scored = scorer._score_single_ticker(claims=[], ticker="EMPTY")

        assert scored == []

    def test_エッジケース_factual_claimもスコアリング対象になる(
        self,
        scorer: ClaimScorer,
    ) -> None:
        claims = [
            Claim(
                id="TEST-FACT-001",
                claim_type="factual_claim",
                claim="Revenue grew 30% YoY",
                evidence="CFO statement in prepared remarks.",
                rule_evaluation=RuleEvaluation(
                    applied_rules=[],
                    results={},
                    confidence=0.5,
                    adjustments=[],
                ),
            )
        ]

        response = json.dumps(
            {
                "scored_claims": [
                    {
                        "id": "TEST-FACT-001",
                        "final_confidence": 50,
                        "gatekeeper": {
                            "rule9_factual_error": False,
                            "rule3_industry_common": False,
                        },
                        "kb2_patterns": [],
                        "confidence_adjustments": [],
                        "overall_reasoning": "Factual claim, standard confidence",
                    }
                ]
            }
        )

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=response)]
        mock_message.usage.input_tokens = 500
        mock_message.usage.output_tokens = 200

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            scored = scorer._score_single_ticker(claims=claims, ticker="TEST")

        assert len(scored) > 0
        assert scored[0].final_confidence == 0.5

    def test_エッジケース_全クレームがゲートキーパーで却下される(
        self,
        scorer: ClaimScorer,
        sample_gatekeeper_claim_rule9: Claim,
        sample_gatekeeper_claim_rule3: Claim,
    ) -> None:
        claims = [sample_gatekeeper_claim_rule9, sample_gatekeeper_claim_rule3]

        response = json.dumps(
            {
                "scored_claims": [
                    {
                        "id": "TEST-CA-R9",
                        "final_confidence": 10,
                        "gatekeeper": {
                            "rule9_factual_error": True,
                            "rule3_industry_common": False,
                        },
                        "kb2_patterns": [],
                        "confidence_adjustments": [
                            {
                                "source": "gatekeeper_rule9",
                                "adjustment": -0.6,
                                "reasoning": "Factual error",
                            }
                        ],
                        "overall_reasoning": "Rejected by gatekeeper",
                    },
                    {
                        "id": "TEST-CA-R3",
                        "final_confidence": 30,
                        "gatekeeper": {
                            "rule9_factual_error": False,
                            "rule3_industry_common": True,
                        },
                        "kb2_patterns": [],
                        "confidence_adjustments": [
                            {
                                "source": "gatekeeper_rule3",
                                "adjustment": -0.4,
                                "reasoning": "Industry common",
                            }
                        ],
                        "overall_reasoning": "Industry common, low confidence",
                    },
                ]
            }
        )

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=response)]
        mock_message.usage.input_tokens = 1000
        mock_message.usage.output_tokens = 500

        with patch.object(scorer._client.messages, "create", return_value=mock_message):
            scored = scorer._score_single_ticker(claims=claims, ticker="TEST")

        assert len(scored) == 2
        assert scored[0].final_confidence <= 0.1
        assert scored[1].final_confidence <= 0.3
