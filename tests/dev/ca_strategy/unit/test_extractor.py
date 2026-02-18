"""Tests for ca_strategy extractor module (Phase 1 LLM claim extraction).

Validates ClaimExtractor class for extracting competitive advantage claims
from earnings call transcripts using Claude API with KB1-T/KB3-T rules.
All LLM calls are mocked for unit testing.
"""

from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from dev.ca_strategy.cost import CostTracker
from dev.ca_strategy.extractor import ClaimExtractor
from dev.ca_strategy.types import (
    Claim,
    RuleEvaluation,
    Transcript,
    TranscriptMetadata,
    TranscriptSection,
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
def kb3_dir(tmp_path: Path) -> Path:
    """Create a temporary KB3-T few-shot directory with sample files."""
    kb3 = tmp_path / "kb3_fewshot_transcript"
    kb3.mkdir()
    (kb3 / "fewshot_ORLY.md").write_text(
        "# few-shot: ORLY\nSample few-shot evaluation."
    )
    (kb3 / "fewshot_COST.md").write_text(
        "# few-shot: COST\nSample few-shot evaluation."
    )
    return kb3


@pytest.fixture
def system_prompt_path(tmp_path: Path) -> Path:
    """Create a temporary system prompt file."""
    prompt_file = tmp_path / "system_prompt_transcript.md"
    prompt_file.write_text(
        "# System Prompt\n\nYou are an analyst. cutoff_date: {{cutoff_date}}"
    )
    return prompt_file


@pytest.fixture
def dogma_path(tmp_path: Path) -> Path:
    """Create a temporary dogma.md file."""
    dogma_file = tmp_path / "dogma.md"
    dogma_file.write_text("# Dogma\nKY rules for evaluation.")
    return dogma_file


@pytest.fixture
def cost_tracker() -> CostTracker:
    """Create a CostTracker instance."""
    return CostTracker()


@pytest.fixture
def sample_transcript() -> Transcript:
    """Create a sample transcript for testing."""
    return Transcript(
        metadata=TranscriptMetadata(
            ticker="AAPL",
            event_date=date(2015, 1, 27),
            fiscal_quarter="Q1 2015",
            is_truncated=False,
        ),
        sections=[
            TranscriptSection(
                speaker="Tim Cook",
                role="Executives",
                section_type="prepared_remarks",
                content="Our silicon advantage compounds every year.",
            ),
            TranscriptSection(
                speaker="Luca Maestri",
                role="Executives",
                section_type="prepared_remarks",
                content="Revenue grew 30% year-over-year.",
            ),
        ],
        raw_source=None,
    )


@pytest.fixture
def sample_sec_data() -> dict:
    """Create sample SEC filing data for testing."""
    return {
        "ticker": "AAPL",
        "filing_type": "10-K",
        "filing_date": "2014-10-27",
        "sections": {
            "item_1": "Apple designs and manufactures consumer electronics...",
            "item_7": "Revenue increased 7% year-over-year...",
        },
    }


@pytest.fixture
def sample_llm_response_json() -> str:
    """Create a sample LLM JSON response with extracted claims."""
    return json.dumps(
        {
            "ticker": "AAPL",
            "transcript_source": "Q1 FY2015 Earnings Call",
            "extraction_metadata": {
                "cutoff_date": "2015-09-30",
                "kb1_t_rules_loaded": 9,
                "kb2_t_patterns_loaded": 12,
                "dogma_loaded": True,
                "sec_data_available": True,
                "q4_transcript_available": True,
                "quarterly_transcripts_available": ["Q1"],
            },
            "claims": [
                {
                    "id": "AAPL-CA-001",
                    "claim_type": "competitive_advantage",
                    "claim": "Proprietary silicon design capability",
                    "descriptive_label": "Vertical silicon design",
                    "evidence_from_transcript": "CEO: Our silicon advantage compounds",
                    "transcript_call_type": "Q1_quarterly",
                    "speaker": "CEO",
                    "section": "prepared_remarks",
                    "supported_by_facts": [3],
                    "cagr_connections": [2],
                    "rule_evaluation": {
                        "applied_rules": ["rule_1_t", "rule_4_t"],
                        "results": [
                            {
                                "rule": "rule_1_t",
                                "verdict": "pass",
                                "reasoning": "Capability, not result",
                            }
                        ],
                        "kb2_t_pattern_match": "pattern_I_t",
                        "confidence": 70,
                        "confidence_adjustments": [],
                        "overall_reasoning": "Strong structural advantage",
                    },
                },
                {
                    "id": "AAPL-CAGR-002",
                    "claim_type": "cagr_connection",
                    "claim": "Silicon -> ASP maintenance -> Revenue CAGR +2pp",
                    "descriptive_label": "Silicon to revenue path",
                    "source_advantage": 1,
                    "transcript_call_type": "Q1_quarterly",
                    "rule_evaluation": {
                        "applied_rules": ["rule_5_t"],
                        "results": [
                            {
                                "rule": "rule_5_t",
                                "verdict": "direct",
                                "reasoning": "2-step causal chain",
                            }
                        ],
                        "confidence": 60,
                        "confidence_adjustments": [],
                        "overall_reasoning": "Direct mechanism",
                    },
                },
                {
                    "id": "AAPL-FACT-003",
                    "claim_type": "factual_claim",
                    "claim": "Revenue grew 30% year-over-year",
                    "transcript_call_type": "Q1_quarterly",
                    "affected_claims": [1],
                },
            ],
        },
        ensure_ascii=False,
    )


@pytest.fixture
def extractor(
    kb1_dir: Path,
    kb3_dir: Path,
    system_prompt_path: Path,
    dogma_path: Path,
    cost_tracker: CostTracker,
) -> ClaimExtractor:
    """Create a ClaimExtractor instance for testing."""
    return ClaimExtractor(
        kb1_dir=kb1_dir,
        kb3_dir=kb3_dir,
        system_prompt_path=system_prompt_path,
        dogma_path=dogma_path,
        cost_tracker=cost_tracker,
    )


# =============================================================================
# ClaimExtractor initialization
# =============================================================================
class TestClaimExtractorInit:
    """ClaimExtractor initialization tests."""

    def test_正常系_初期化でKBファイルが読み込まれる(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        assert extractor._kb1_rules is not None
        assert len(extractor._kb1_rules) == 2  # 2 rule files created in fixture

    def test_正常系_KB3_fewshotが読み込まれる(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        assert extractor._kb3_examples is not None
        assert len(extractor._kb3_examples) == 2  # 2 fewshot files

    def test_正常系_システムプロンプトが読み込まれる(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        assert extractor._system_prompt is not None
        assert "cutoff_date" in extractor._system_prompt

    def test_正常系_dogmaが読み込まれる(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        assert extractor._dogma is not None
        assert "KY rules" in extractor._dogma

    def test_正常系_コストトラッカーが設定される(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        assert extractor._cost_tracker is not None

    def test_異常系_KB1ディレクトリが存在しない場合(
        self,
        tmp_path: Path,
        kb3_dir: Path,
        system_prompt_path: Path,
        dogma_path: Path,
        cost_tracker: CostTracker,
    ) -> None:
        non_existent = tmp_path / "non_existent_kb1"
        ext = ClaimExtractor(
            kb1_dir=non_existent,
            kb3_dir=kb3_dir,
            system_prompt_path=system_prompt_path,
            dogma_path=dogma_path,
            cost_tracker=cost_tracker,
        )
        assert len(ext._kb1_rules) == 0

    def test_異常系_KB3ディレクトリが存在しない場合(
        self,
        kb1_dir: Path,
        tmp_path: Path,
        system_prompt_path: Path,
        dogma_path: Path,
        cost_tracker: CostTracker,
    ) -> None:
        non_existent = tmp_path / "non_existent_kb3"
        ext = ClaimExtractor(
            kb1_dir=kb1_dir,
            kb3_dir=non_existent,
            system_prompt_path=system_prompt_path,
            dogma_path=dogma_path,
            cost_tracker=cost_tracker,
        )
        assert len(ext._kb3_examples) == 0


# =============================================================================
# ClaimExtractor._build_extraction_prompt
# =============================================================================
class TestBuildExtractionPrompt:
    """Tests for _build_extraction_prompt method."""

    def test_正常系_プロンプトにトランスクリプト内容が含まれる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
    ) -> None:
        prompt = extractor._build_extraction_prompt(
            transcript=sample_transcript,
            sec_data=sample_sec_data,
        )
        assert "Tim Cook" in prompt
        assert "silicon advantage" in prompt

    def test_正常系_プロンプトにKB1ルールが含まれる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
    ) -> None:
        prompt = extractor._build_extraction_prompt(
            transcript=sample_transcript,
            sec_data=sample_sec_data,
        )
        assert "Rule 1-T" in prompt or "Capability not result" in prompt

    def test_正常系_プロンプトにKB3_fewshotが含まれる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
    ) -> None:
        prompt = extractor._build_extraction_prompt(
            transcript=sample_transcript,
            sec_data=sample_sec_data,
        )
        assert "ORLY" in prompt or "few-shot" in prompt

    def test_正常系_プロンプトにSECデータが含まれる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
    ) -> None:
        prompt = extractor._build_extraction_prompt(
            transcript=sample_transcript,
            sec_data=sample_sec_data,
        )
        assert "10-K" in prompt or "consumer electronics" in prompt

    def test_正常系_プロンプトにPoiT制約が含まれる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
    ) -> None:
        prompt = extractor._build_extraction_prompt(
            transcript=sample_transcript,
            sec_data=sample_sec_data,
        )
        assert "2015-09-30" in prompt

    def test_正常系_SECデータがNoneでもプロンプトが構築できる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
    ) -> None:
        prompt = extractor._build_extraction_prompt(
            transcript=sample_transcript,
            sec_data=None,
        )
        assert "Tim Cook" in prompt
        assert len(prompt) > 0

    def test_正常系_ティッカー情報がプロンプトに含まれる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
    ) -> None:
        prompt = extractor._build_extraction_prompt(
            transcript=sample_transcript,
            sec_data=sample_sec_data,
        )
        assert "AAPL" in prompt

    def test_正常系_fiscal_quarter情報がプロンプトに含まれる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
    ) -> None:
        prompt = extractor._build_extraction_prompt(
            transcript=sample_transcript,
            sec_data=sample_sec_data,
        )
        assert "Q1 2015" in prompt


# =============================================================================
# ClaimExtractor._parse_llm_response
# =============================================================================
class TestParseLlmResponse:
    """Tests for _parse_llm_response method."""

    def test_正常系_有効なJSONからClaimリストをパースできる(
        self,
        extractor: ClaimExtractor,
        sample_llm_response_json: str,
    ) -> None:
        claims = extractor._parse_llm_response(sample_llm_response_json)
        assert len(claims) > 0
        assert all(isinstance(c, Claim) for c in claims)

    def test_正常系_competitive_advantageクレームが正しくパースされる(
        self,
        extractor: ClaimExtractor,
        sample_llm_response_json: str,
    ) -> None:
        claims = extractor._parse_llm_response(sample_llm_response_json)
        ca_claims = [c for c in claims if c.claim_type == "competitive_advantage"]
        assert len(ca_claims) >= 1
        assert ca_claims[0].claim == "Proprietary silicon design capability"

    def test_正常系_cagr_connectionクレームが正しくパースされる(
        self,
        extractor: ClaimExtractor,
        sample_llm_response_json: str,
    ) -> None:
        claims = extractor._parse_llm_response(sample_llm_response_json)
        cagr_claims = [c for c in claims if c.claim_type == "cagr_connection"]
        assert len(cagr_claims) >= 1

    def test_正常系_factual_claimクレームが正しくパースされる(
        self,
        extractor: ClaimExtractor,
        sample_llm_response_json: str,
    ) -> None:
        claims = extractor._parse_llm_response(sample_llm_response_json)
        fact_claims = [c for c in claims if c.claim_type == "factual_claim"]
        assert len(fact_claims) >= 1

    def test_正常系_rule_evaluationが正しくパースされる(
        self,
        extractor: ClaimExtractor,
        sample_llm_response_json: str,
    ) -> None:
        claims = extractor._parse_llm_response(sample_llm_response_json)
        ca_claims = [c for c in claims if c.claim_type == "competitive_advantage"]
        assert len(ca_claims) >= 1
        rule_eval = ca_claims[0].rule_evaluation
        assert isinstance(rule_eval, RuleEvaluation)
        assert len(rule_eval.applied_rules) > 0
        assert 0.0 <= rule_eval.confidence <= 1.0

    def test_異常系_不正なJSONで空リストが返される(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        claims = extractor._parse_llm_response("not valid json {{{")
        assert claims == []

    def test_異常系_claims_keyが欠落したJSONで空リストが返される(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        claims = extractor._parse_llm_response('{"ticker": "AAPL"}')
        assert claims == []

    def test_異常系_空のclaimsリストで空リストが返される(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        claims = extractor._parse_llm_response('{"ticker": "AAPL", "claims": []}')
        assert claims == []

    def test_正常系_JSONがコードブロックに包まれている場合も対応(
        self,
        extractor: ClaimExtractor,
        sample_llm_response_json: str,
    ) -> None:
        wrapped = f"```json\n{sample_llm_response_json}\n```"
        claims = extractor._parse_llm_response(wrapped)
        assert len(claims) > 0


# =============================================================================
# ClaimExtractor._extract_single
# =============================================================================
class TestExtractSingle:
    """Tests for _extract_single method."""

    def test_正常系_LLM呼び出しでClaimリストが返される(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
        sample_llm_response_json: str,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_response_json)]
        mock_message.usage.input_tokens = 1000
        mock_message.usage.output_tokens = 500

        with patch.object(
            extractor._client.messages, "create", return_value=mock_message
        ):
            claims = extractor._extract_single(
                transcript=sample_transcript,
                sec_data=sample_sec_data,
            )

        assert len(claims) > 0
        assert all(isinstance(c, Claim) for c in claims)

    def test_正常系_CostTrackerにトークン数が記録される(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
        sample_llm_response_json: str,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_response_json)]
        mock_message.usage.input_tokens = 5000
        mock_message.usage.output_tokens = 2000

        with patch.object(
            extractor._client.messages, "create", return_value=mock_message
        ):
            extractor._extract_single(
                transcript=sample_transcript,
                sec_data=sample_sec_data,
            )

        assert extractor._cost_tracker.get_phase_cost("phase1") > 0

    def test_正常系_temperature_0で呼び出される(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
        sample_llm_response_json: str,
    ) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_response_json)]
        mock_message.usage.input_tokens = 1000
        mock_message.usage.output_tokens = 500

        with patch.object(
            extractor._client.messages, "create", return_value=mock_message
        ) as mock_create:
            extractor._extract_single(
                transcript=sample_transcript,
                sec_data=sample_sec_data,
            )

        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs.get("temperature") == 0

    def test_異常系_LLM呼び出しが例外を投げた場合に空リストが返される(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
    ) -> None:
        with patch.object(
            extractor._client.messages,
            "create",
            side_effect=Exception("API error"),
        ):
            claims = extractor._extract_single(
                transcript=sample_transcript,
                sec_data=sample_sec_data,
            )

        assert claims == []


# =============================================================================
# ClaimExtractor.extract_batch
# =============================================================================
class TestExtractBatch:
    """Tests for extract_batch method."""

    def test_正常系_複数ティッカーのクレームが抽出される(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_llm_response_json: str,
    ) -> None:
        transcripts = {"AAPL": [sample_transcript]}

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_response_json)]
        mock_message.usage.input_tokens = 1000
        mock_message.usage.output_tokens = 500

        with patch.object(
            extractor._client.messages, "create", return_value=mock_message
        ):
            result = extractor.extract_batch(
                transcripts=transcripts,
                sec_data_map={},
            )

        assert "AAPL" in result
        assert len(result["AAPL"]) > 0

    def test_正常系_空のトランスクリプトで空の結果が返される(
        self,
        extractor: ClaimExtractor,
    ) -> None:
        result = extractor.extract_batch(
            transcripts={},
            sec_data_map={},
        )
        assert result == {}

    def test_正常系_出力ディレクトリにJSONが保存される(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_llm_response_json: str,
        tmp_path: Path,
    ) -> None:
        transcripts = {"AAPL": [sample_transcript]}

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_response_json)]
        mock_message.usage.input_tokens = 1000
        mock_message.usage.output_tokens = 500

        with patch.object(
            extractor._client.messages, "create", return_value=mock_message
        ):
            extractor.extract_batch(
                transcripts=transcripts,
                sec_data_map={},
                output_dir=tmp_path,
            )

        output_file = tmp_path / "AAPL" / "Q1_2015_claims.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "claims" in data

    def test_正常系_SECデータが銘柄ごとに渡される(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        sample_sec_data: dict,
        sample_llm_response_json: str,
    ) -> None:
        transcripts = {"AAPL": [sample_transcript]}
        sec_data_map = {"AAPL": sample_sec_data}

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=sample_llm_response_json)]
        mock_message.usage.input_tokens = 1000
        mock_message.usage.output_tokens = 500

        with patch.object(
            extractor._client.messages, "create", return_value=mock_message
        ):
            result = extractor.extract_batch(
                transcripts=transcripts,
                sec_data_map=sec_data_map,
            )

        assert "AAPL" in result
