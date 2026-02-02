"""Integration tests for Summarizer with Claude subscription authentication.

This module tests the Summarizer class using actual Claude Agent SDK calls
with Claude Pro/Max subscription authentication.

Prerequisites
-------------
1. Claude Code CLI installed: claude --version
2. Claude subscription authenticated: claude auth login
3. ANTHROPIC_API_KEY NOT set (to use subscription auth)

Notes
-----
These tests make real API calls and consume subscription quota.
They are marked with @pytest.mark.integration to allow selective execution.
"""

import re
from datetime import datetime, timezone

import pytest

from news.config.models import load_config
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
    SummarizationStatus,
)
from news.summarizer import Summarizer


@pytest.fixture
def config():
    """Load the actual workflow configuration."""
    return load_config("data/config/news-collection-config.yaml")


@pytest.fixture
def sample_article() -> ExtractedArticle:
    """Create a sample article for testing.

    Returns an ExtractedArticle with realistic financial news content
    that can be summarized by the AI model.
    """
    source = ArticleSource(
        source_type=SourceType.RSS,
        source_name="Test Source",
        category="market",
    )
    collected = CollectedArticle(
        url="https://example.com/test-article",  # type: ignore[arg-type]
        title="S&P 500 Hits Record High on Strong Earnings",
        published=datetime.now(timezone.utc),
        raw_summary="Markets rally on earnings reports",
        source=source,
        collected_at=datetime.now(timezone.utc),
    )
    return ExtractedArticle(
        collected=collected,
        body_text="""
        The S&P 500 index reached a new all-time high on Tuesday,
        driven by strong earnings reports from technology companies.
        Apple, Microsoft, and Nvidia all reported better-than-expected
        quarterly results, boosting investor confidence.

        The tech-heavy index closed at 5,234.18, up 1.2% for the day.
        This marks the fifth consecutive record close for the benchmark,
        as investors continue to bet on the AI-driven growth story.

        Analysts suggest the rally could continue as the Federal Reserve
        maintains its accommodative monetary policy stance. The central
        bank signaled it could cut interest rates later this year if
        inflation continues to moderate.

        "We're seeing a perfect storm of positive catalysts," said Jane Smith,
        chief market strategist at ABC Capital. "Strong earnings, dovish Fed,
        and continued AI momentum are all supporting equity prices."

        Market breadth has also improved, with 80% of S&P 500 components
        trading above their 50-day moving averages. This broad participation
        suggests the rally has legs beyond just the mega-cap tech stocks.
        """,
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_method="test",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_summarize_success(
    config,
    sample_article: ExtractedArticle,
) -> None:
    """Test that summarization succeeds with subscription authentication.

    This test verifies:
    1. Summarizer can be instantiated with config
    2. Claude Agent SDK is called successfully
    3. SummarizationStatus is SUCCESS
    4. StructuredSummary fields are populated
    5. Summary is in Japanese

    Note
    ----
    This test requires `claude auth login` to be completed with a
    Claude Pro/Max subscription. ANTHROPIC_API_KEY should NOT be set.
    """
    summarizer = Summarizer(config=config)
    result = await summarizer.summarize(sample_article)

    # Verify summarization succeeded
    assert result.summarization_status == SummarizationStatus.SUCCESS, (
        f"Expected SUCCESS, got {result.summarization_status}. "
        f"Error: {result.error_message}"
    )
    assert result.summary is not None, "Summary should not be None on success"

    # Verify StructuredSummary fields
    assert result.summary.overview is not None
    assert len(result.summary.overview) > 0, "Overview should not be empty"

    assert result.summary.key_points is not None
    assert len(result.summary.key_points) > 0, (
        "Key points should have at least one item"
    )

    assert result.summary.market_impact is not None
    assert len(result.summary.market_impact) > 0, "Market impact should not be empty"

    # Verify summary is in Japanese (contains hiragana, katakana, or kanji)
    japanese_pattern = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]")
    assert japanese_pattern.search(result.summary.overview), (
        f"Overview should be in Japanese: {result.summary.overview}"
    )

    # Print results for manual inspection
    print("\n=== Summarization Result ===")
    print(f"Status: {result.summarization_status}")
    print(f"Overview: {result.summary.overview}")
    print(f"Key Points: {result.summary.key_points}")
    print(f"Market Impact: {result.summary.market_impact}")
    if result.summary.related_info:
        print(f"Related Info: {result.summary.related_info}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_summarize_skips_no_body(config) -> None:
    """Test that summarization is skipped when body text is missing.

    This test verifies the SKIPPED status path without making API calls.
    """
    source = ArticleSource(
        source_type=SourceType.RSS,
        source_name="Test Source",
        category="market",
    )
    collected = CollectedArticle(
        url="https://example.com/no-body",  # type: ignore[arg-type]
        title="Article Without Body",
        source=source,
        collected_at=datetime.now(timezone.utc),
    )
    article = ExtractedArticle(
        collected=collected,
        body_text=None,  # No body text
        extraction_status=ExtractionStatus.FAILED,
        extraction_method="test",
        error_message="Extraction failed",
    )

    summarizer = Summarizer(config=config)
    result = await summarizer.summarize(article)

    assert result.summarization_status == SummarizationStatus.SKIPPED
    assert result.summary is None
    assert result.error_message == "No body text available"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_summarize_timeout_config(config) -> None:
    """Test that timeout configuration is respected.

    This test verifies the timeout_seconds configuration is applied.
    We don't actually trigger a timeout, just verify the config is used.
    """
    summarizer = Summarizer(config=config)

    # Verify timeout is configured (default is 60 seconds)
    assert summarizer._timeout_seconds == config.summarization.timeout_seconds
    assert summarizer._timeout_seconds <= 60, (
        "Timeout should be within acceptance criteria (60 seconds)"
    )
