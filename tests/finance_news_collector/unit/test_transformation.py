"""Unit tests for finance news data transformation."""

import pytest

from rss.types import FeedItem


@pytest.fixture
def sample_feed_item() -> FeedItem:
    """Sample feed item fixture."""
    return FeedItem(
        item_id="test-001",
        title="日経平均株価が3万円台を回復",
        link="https://www.nikkei.com/article/DGXZQOUB150001",
        published="2026-01-15T09:30:00Z",
        summary="東京株式市場で日経平均株価が3万円台を回復した。",
        content="東京株式市場で日経平均株価が大幅に上昇し、3万円台を回復した。米国の金利政策の見通しが好感された。",
        author="日経新聞編集部",
        fetched_at="2026-01-15T10:00:00Z",
    )


@pytest.fixture
def filter_config() -> dict:
    """Filter configuration fixture."""
    return {
        "sources": {
            "tier1": ["nikkei.com", "reuters.com", "bloomberg.com"],
            "tier2": ["asahi.com", "toyokeizai.net"],
            "tier3": [],
        },
    }


class TestConvertToIssueFormat:
    """Test convert_to_issue_format function."""

    def test_basic_conversion(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test basic conversion of FeedItem to Issue format."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert "title" in result
        assert "body" in result
        assert result["title"] == sample_feed_item.title

    def test_issue_title_matches_feed_title(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test issue title matches feed item title."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert result["title"] == "日経平均株価が3万円台を回復"

    def test_issue_body_contains_summary(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test issue body contains summary section."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert "## 概要" in result["body"]
        assert sample_feed_item.summary is not None
        assert sample_feed_item.summary in result["body"]

    def test_issue_body_contains_source_info(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test issue body contains source information."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert "## 情報源" in result["body"]
        assert sample_feed_item.link in result["body"]
        assert sample_feed_item.published is not None
        assert sample_feed_item.published in result["body"]

    def test_issue_body_contains_reliability_score(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test issue body contains reliability score."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert "信頼性スコア" in result["body"]

    def test_issue_body_contains_content(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test issue body contains detailed content."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert "## 詳細" in result["body"]
        assert sample_feed_item.content is not None
        assert sample_feed_item.content in result["body"]

    def test_issue_body_contains_auto_generated_note(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test issue body contains auto-generation note."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert "自動収集" in result["body"]
        assert "finance-news-collector" in result["body"]

    def test_handles_none_summary(self, filter_config: dict) -> None:
        """Test handling of None summary."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="test-002",
            title="テストタイトル",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary=None,
            content="詳細な内容",
            author="著者名",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)

        assert result["title"] == "テストタイトル"
        assert "body" in result

    def test_handles_none_content(self, filter_config: dict) -> None:
        """Test handling of None content."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="test-003",
            title="テストタイトル",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="要約",
            content=None,
            author="著者名",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)

        assert result["title"] == "テストタイトル"
        assert "body" in result

    def test_handles_none_published(self, filter_config: dict) -> None:
        """Test handling of None published date."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="test-004",
            title="テストタイトル",
            link="https://example.com/test",
            published=None,
            summary="要約",
            content="詳細",
            author="著者名",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)

        assert result["title"] == "テストタイトル"
        assert "body" in result

    def test_handles_none_author(self, filter_config: dict) -> None:
        """Test handling of None author."""
        from finance_news_collector.transformation import convert_to_issue_format

        item = FeedItem(
            item_id="test-005",
            title="テストタイトル",
            link="https://example.com/test",
            published="2026-01-15T10:00:00Z",
            summary="要約",
            content="詳細",
            author=None,
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = convert_to_issue_format(item, filter_config)

        assert result["title"] == "テストタイトル"
        assert "body" in result

    def test_markdown_formatting(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test proper markdown formatting in issue body."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        # Check for markdown headers
        assert result["body"].count("##") >= 3

        # Check for horizontal rule
        assert "---" in result["body"]

    def test_category_extraction_from_config(self, sample_feed_item: FeedItem) -> None:
        """Test category extraction from filter config."""
        from finance_news_collector.transformation import convert_to_issue_format

        config_with_category = {
            "sources": {
                "tier1": ["nikkei.com"],
                "tier2": [],
                "tier3": [],
            },
            "category": "finance",
        }

        result = convert_to_issue_format(sample_feed_item, config_with_category)

        assert "カテゴリ" in result["body"]

    def test_url_in_markdown_format(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test URL is formatted properly in markdown."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        # URL should be present
        assert sample_feed_item.link in result["body"]

    def test_timestamp_formatting(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test timestamp is properly formatted."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        # Published timestamp should be present
        assert "2026-01-15" in result["body"]

    def test_returns_dict_with_required_keys(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test return value has required keys."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert isinstance(result, dict)
        assert "title" in result
        assert "body" in result
        assert isinstance(result["title"], str)
        assert isinstance(result["body"], str)

    def test_title_not_empty(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test title is not empty."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert len(result["title"]) > 0

    def test_body_not_empty(
        self, sample_feed_item: FeedItem, filter_config: dict
    ) -> None:
        """Test body is not empty."""
        from finance_news_collector.transformation import convert_to_issue_format

        result = convert_to_issue_format(sample_feed_item, filter_config)

        assert len(result["body"]) > 0
