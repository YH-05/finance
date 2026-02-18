"""Integration tests for ca_strategy extractor module.

These tests make actual Claude API calls and require:
- ANTHROPIC_API_KEY environment variable to be set
- Network access to the Anthropic API

Run manually with:
    uv run pytest tests/dev/ca_strategy/integration/test_extractor.py -v -s

These tests are marked with @pytest.mark.integration and are excluded
from the default test suite.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pytest

from dev.ca_strategy.cost import CostTracker
from dev.ca_strategy.extractor import ClaimExtractor
from dev.ca_strategy.types import (
    Transcript,
    TranscriptMetadata,
    TranscriptSection,
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
_KB3_DIR = _PROJECT_ROOT / "analyst" / "transcript_eval" / "kb3_fewshot_transcript"
_SYSTEM_PROMPT_PATH = (
    _PROJECT_ROOT / "analyst" / "transcript_eval" / "system_prompt_transcript.md"
)
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
def extractor(cost_tracker: CostTracker) -> ClaimExtractor:
    """Create a ClaimExtractor with real KB files."""
    return ClaimExtractor(
        kb1_dir=_KB1_DIR,
        kb3_dir=_KB3_DIR,
        system_prompt_path=_SYSTEM_PROMPT_PATH,
        dogma_path=_DOGMA_PATH,
        cost_tracker=cost_tracker,
    )


@pytest.fixture
def sample_transcript() -> Transcript:
    """Create a minimal but realistic transcript for integration testing."""
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
                content=(
                    "Our ecosystem continues to grow with over 1 billion "
                    "active devices. The integration of hardware, software, "
                    "and services creates a customer experience that is "
                    "unmatched in the industry. Our proprietary silicon "
                    "design gives us a fundamental performance advantage "
                    "that competitors cannot easily replicate."
                ),
            ),
            TranscriptSection(
                speaker="Luca Maestri",
                role="Executives",
                section_type="prepared_remarks",
                content=(
                    "Revenue grew 30% year-over-year to $74.6 billion. "
                    "iPhone ASPs increased by $50 to $687, driven by "
                    "iPhone 6 Plus popularity. Gross margin was 39.9%."
                ),
            ),
        ],
        raw_source=None,
    )


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------
class TestExtractorIntegration:
    """Integration tests that call the real Claude API."""

    @pytest.mark.integration
    def test_正常系_実APIでクレーム抽出ができる(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
    ) -> None:
        """Verify that the extractor can call Claude API and parse the response."""
        claims = extractor._extract_single(
            transcript=sample_transcript,
            sec_data=None,
        )

        # Should return at least some claims
        assert len(claims) > 0, "Expected at least 1 claim from the LLM"

        # Each claim should have required fields
        for claim in claims:
            assert claim.id
            assert claim.claim_type in (
                "competitive_advantage",
                "cagr_connection",
                "factual_claim",
            )
            assert claim.claim

    @pytest.mark.integration
    def test_正常系_コストが記録される(
        self,
        extractor: ClaimExtractor,
        sample_transcript: Transcript,
        cost_tracker: CostTracker,
    ) -> None:
        """Verify that token costs are recorded after an API call."""
        extractor._extract_single(
            transcript=sample_transcript,
            sec_data=None,
        )

        total_cost = cost_tracker.get_total_cost()
        assert total_cost > 0, "Expected cost to be recorded after API call"
