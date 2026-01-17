"""Edge case tests for finance news collector."""

import pytest

from rss.types import FeedItem


@pytest.fixture
def filter_config() -> dict:
    """Filter configuration fixture."""
    return {
        "keywords": {
            "include": {
                "market": ["株価", "株式", "為替"],
                "policy": ["金利", "日銀"],
            },
            "exclude": {
                "sports": ["サッカー", "野球"],
            },
        },
        "sources": {
            "tier1": ["nikkei.com"],
            "tier2": ["asahi.com"],
            "tier3": [],
        },
        "filtering": {
            "min_keyword_matches": 1,
            "title_similarity_threshold": 0.85,
        },
    }


class TestEmptyStrings:
    """Test handling of empty strings."""

    def test_empty_title(self, filter_config: dict) -> None:
        """Test handling of empty title."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-001",
            title="",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="株価が上昇",
            content="詳細...",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        # Should still match due to summary
        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_empty_summary(self, filter_config: dict) -> None:
        """Test handling of empty summary."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-002",
            title="株価動向",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="",
            content="詳細...",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        # Should match due to title
        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_empty_content(self, filter_config: dict) -> None:
        """Test handling of empty content."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-003",
            title="株価動向",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="為替市場",
            content="",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        # Should match due to title and summary
        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_all_empty_strings(self, filter_config: dict) -> None:
        """Test handling when all text fields are empty."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-004",
            title="",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="",
            content="",
            author="",
            fetched_at="2026-01-15T11:00:00Z",
        )

        # Should not match
        result = matches_financial_keywords(item, filter_config)
        assert result is False


class TestWhitespaceHandling:
    """Test handling of whitespace."""

    def test_whitespace_only_title(self, filter_config: dict) -> None:
        """Test handling of whitespace-only title."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-005",
            title="   ",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="株価",
            content="詳細",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_keyword_with_extra_whitespace(self, filter_config: dict) -> None:
        """Test keyword matching with extra whitespace."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-006",
            title="  株価  動向  ",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="  為替  市場  ",
            content="詳細",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True


class TestSpecialCharacters:
    """Test handling of special characters."""

    def test_keywords_with_special_chars(self, filter_config: dict) -> None:
        """Test keyword matching with special characters."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-007",
            title="【速報】株価が急上昇！",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="※為替市場の動向",
            content="詳細...",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_url_with_special_chars(self, filter_config: dict) -> None:
        """Test handling of URLs with special characters."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="edge-008",
            title="株価動向",
            link="https://example.com/article?id=123&category=finance&lang=ja",
            published="2026-01-15T10:00:00Z",
            summary="要約",
            content="詳細",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)
        assert item.link in result["body"]

    def test_markdown_special_chars_in_content(self, filter_config: dict) -> None:
        """Test handling of markdown special characters in content."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="edge-009",
            title="株価動向",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="要約に**太字**や_斜体_を含む",
            content="詳細に`コード`や[リンク](url)を含む",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)
        assert "body" in result


class TestUnicodeHandling:
    """Test handling of Unicode characters."""

    def test_japanese_keywords(self, filter_config: dict) -> None:
        """Test matching Japanese keywords."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-010",
            title="株価が上昇",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="日銀の金利政策",
            content="詳細...",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_mixed_japanese_english(self, filter_config: dict) -> None:
        """Test matching mixed Japanese and English."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="edge-011",
            title="株価と為替の動向",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="日銀と金利政策",
            content="詳細...",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_emoji_in_content(self, filter_config: dict) -> None:
        """Test handling of emoji in content."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="edge-012",
            title="株価動向 📈",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="市場が好調 🎉",
            content="詳細 💰",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)
        assert result["title"] == "株価動向 📈"


class TestVeryLongStrings:
    """Test handling of very long strings."""

    def test_very_long_title(self, filter_config: dict) -> None:
        """Test handling of very long title."""
        from finance_news_collector.filtering import matches_financial_keywords

        long_title = "株価動向の分析：" + "非常に長いタイトル" * 100
        item = FeedItem(
            item_id="edge-013",
            title=long_title,
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="要約",
            content="詳細",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_very_long_content(self, filter_config: dict) -> None:
        """Test handling of very long content."""
        from finance_news_collector.transformation import convert_to_issue_format

        long_content = "詳細な分析：" + "非常に長い内容" * 1000
        item = FeedItem(
            item_id="edge-014",
            title="株価動向",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="要約",
            content=long_content,
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)
        assert long_content in result["body"]


class TestReliabilityScoreEdgeCases:
    """Test edge cases for reliability score calculation."""

    def test_score_with_no_matching_source(self, filter_config: dict) -> None:
        """Test reliability score with unrecognized source."""
        from finance_news_collector.filtering import calculate_reliability_score

        item = FeedItem(
            item_id="edge-015",
            title="株価動向",
            link="https://unknown-domain.xyz/article/123",
            published="2026-01-15T10:00:00Z",
            summary="為替市場",
            content="詳細",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        score = calculate_reliability_score(item, filter_config)
        assert score == 0

    def test_score_with_no_keywords(self, filter_config: dict) -> None:
        """Test reliability score with no keyword matches."""
        from finance_news_collector.filtering import calculate_reliability_score

        item = FeedItem(
            item_id="edge-016",
            title="一般的なニュース",
            link="https://www.nikkei.com/article/test",
            published="2026-01-15T10:00:00Z",
            summary="天気予報",
            content="明日は晴れ",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        score = calculate_reliability_score(item, filter_config)
        assert score >= 0


class TestFilterConfigEdgeCases:
    """Test edge cases for filter configuration."""

    def test_empty_include_keywords(self, filter_config: dict) -> None:
        """Test with empty include keywords."""
        from finance_news_collector.filtering import matches_financial_keywords

        config_empty_include = {
            "keywords": {
                "include": {},
                "exclude": {"sports": ["サッカー"]},
            },
            "filtering": {"min_keyword_matches": 1},
        }

        item = FeedItem(
            item_id="edge-017",
            title="株価動向",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="要約",
            content="詳細",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, config_empty_include)
        assert result is False

    def test_empty_exclude_keywords(self, filter_config: dict) -> None:
        """Test with empty exclude keywords."""
        from finance_news_collector.filtering import is_excluded

        config_empty_exclude = {
            "keywords": {
                "include": {"market": ["株価"]},
                "exclude": {},
            },
        }

        item = FeedItem(
            item_id="edge-018",
            title="サッカーの試合",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="スポーツ",
            content="詳細",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = is_excluded(item, config_empty_exclude)
        assert result is False

    def test_min_keyword_matches_zero(self) -> None:
        """Test with min_keyword_matches set to 0."""
        from finance_news_collector.filtering import matches_financial_keywords

        config_zero_min = {
            "keywords": {
                "include": {"market": ["株価"]},
                "exclude": {},
            },
            "filtering": {"min_keyword_matches": 0},
        }

        item = FeedItem(
            item_id="edge-019",
            title="一般ニュース",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="天気",
            content="詳細",
            author="著者",
            fetched_at="2026-01-15T11:00:00Z",
        )

        # With min=0, should match even without keywords
        result = matches_financial_keywords(item, config_zero_min)
        assert result is True


class TestConversionEdgeCases:
    """Test edge cases for data conversion."""

    def test_all_none_optional_fields(self, filter_config: dict) -> None:
        """Test conversion with all optional fields as None."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="edge-020",
            title="タイトル",
            link="https://example.com/test",
            published=None,
            summary=None,
            content=None,
            author=None,
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)

        assert "title" in result
        assert "body" in result
        assert result["title"] == "タイトル"
        assert len(result["body"]) > 0

    def test_minimal_feed_item(self, filter_config: dict) -> None:
        """Test conversion with minimal FeedItem."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="edge-021",
            title="最小限のアイテム",
            link="https://example.com/minimal",
            published=None,
            summary=None,
            content=None,
            author=None,
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)

        assert result["title"] == "最小限のアイテム"
        assert isinstance(result["body"], str)
        assert len(result["body"]) > 0
