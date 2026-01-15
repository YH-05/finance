"""Unit tests for finance news filtering logic."""

import pytest

from rss.types import FeedItem


@pytest.fixture
def filter_config() -> dict:
    """Filter configuration fixture."""
    return {
        "keywords": {
            "include": {
                "market": ["株価", "株式", "為替", "stock", "forex"],
                "policy": ["金利", "日銀", "interest rate", "Fed"],
                "corporate": ["決算", "業績", "earnings"],
            },
            "exclude": {
                "sports": ["サッカー", "野球", "soccer", "baseball"],
                "entertainment": ["映画", "音楽", "movie", "music"],
            },
        },
        "sources": {
            "tier1": ["nikkei.com", "reuters.com", "bloomberg.com"],
            "tier2": ["asahi.com", "toyokeizai.net"],
            "tier3": [],
        },
        "filtering": {
            "min_keyword_matches": 1,
            "title_similarity_threshold": 0.85,
        },
    }


@pytest.fixture
def sample_feed_item() -> FeedItem:
    """Sample feed item fixture."""
    return FeedItem(
        item_id="test-001",
        title="日経平均株価が上昇",
        link="https://www.nikkei.com/article/test-001",
        published="2026-01-15T10:00:00Z",
        summary="東京株式市場で日経平均株価が上昇した。",
        content="詳細な記事内容...",
        author="記者A",
        fetched_at="2026-01-15T11:00:00Z",
    )


class TestMatchesFinancialKeywords:
    """Test matches_financial_keywords function."""

    def test_matches_single_keyword_in_title(
        self, filter_config: dict, sample_feed_item: FeedItem
    ) -> None:
        """Test matching a single keyword in title."""
        from finance_news_collector.filtering import matches_financial_keywords

        result = matches_financial_keywords(sample_feed_item, filter_config)
        assert result is True

    def test_matches_multiple_keywords(self, filter_config: dict) -> None:
        """Test matching multiple keywords."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="test-002",
            title="日銀が金利政策を変更",
            link="https://example.com/test-002",
            published="2026-01-15T10:00:00Z",
            summary="日本銀行が政策金利を変更した。",
            content="詳細...",
            author="記者B",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_matches_keyword_in_summary(self, filter_config: dict) -> None:
        """Test matching keyword in summary."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="test-003",
            title="市場動向レポート",
            link="https://example.com/test-003",
            published="2026-01-15T10:00:00Z",
            summary="為替市場で円高が進行している。",
            content="詳細...",
            author="記者C",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_matches_keyword_in_content(self, filter_config: dict) -> None:
        """Test matching keyword in content."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="test-004",
            title="経済ニュース",
            link="https://example.com/test-004",
            published="2026-01-15T10:00:00Z",
            summary="今日の経済動向",
            content="企業決算が発表された。好調な業績が続いている。",
            author="記者D",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_no_match_when_no_keywords(self, filter_config: dict) -> None:
        """Test no match when item contains no financial keywords."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="test-005",
            title="一般的なニュース",
            link="https://example.com/test-005",
            published="2026-01-15T10:00:00Z",
            summary="今日の天気は晴れです。",
            content="明日も晴れるでしょう。",
            author="記者E",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is False

    def test_case_insensitive_matching(self, filter_config: dict) -> None:
        """Test case-insensitive keyword matching."""
        from finance_news_collector.filtering import matches_financial_keywords

        item = FeedItem(
            item_id="test-006",
            title="STOCK market update",
            link="https://example.com/test-006",
            published="2026-01-15T10:00:00Z",
            summary="FOREX trading analysis",
            content="EARNINGS report",
            author="記者F",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = matches_financial_keywords(item, filter_config)
        assert result is True

    def test_min_keyword_matches_threshold(self, filter_config: dict) -> None:
        """Test minimum keyword matches threshold."""
        from finance_news_collector.filtering import matches_financial_keywords

        # Set higher threshold
        filter_config["filtering"]["min_keyword_matches"] = 3

        # Item with only 1 match
        item_one_match = FeedItem(
            item_id="test-007",
            title="株価に関するニュース",
            link="https://example.com/test-007",
            published="2026-01-15T10:00:00Z",
            summary="一般的な内容",
            content="特に金融情報なし",
            author="記者G",
            fetched_at="2026-01-15T11:00:00Z",
        )

        # Item with 3+ matches
        item_three_matches = FeedItem(
            item_id="test-008",
            title="株価と為替と金利の動向",
            link="https://example.com/test-008",
            published="2026-01-15T10:00:00Z",
            summary="決算発表",
            content="業績が好調",
            author="記者H",
            fetched_at="2026-01-15T11:00:00Z",
        )

        assert matches_financial_keywords(item_one_match, filter_config) is False
        assert matches_financial_keywords(item_three_matches, filter_config) is True


class TestIsExcluded:
    """Test is_excluded function."""

    def test_excluded_sports_keyword(self, filter_config: dict) -> None:
        """Test exclusion of sports-related content."""
        from finance_news_collector.filtering import is_excluded

        item = FeedItem(
            item_id="test-101",
            title="サッカーの試合結果",
            link="https://example.com/test-101",
            published="2026-01-15T10:00:00Z",
            summary="昨日のサッカー試合は...",
            content="詳細...",
            author="記者A",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = is_excluded(item, filter_config)
        assert result is True

    def test_excluded_entertainment_keyword(self, filter_config: dict) -> None:
        """Test exclusion of entertainment-related content."""
        from finance_news_collector.filtering import is_excluded

        item = FeedItem(
            item_id="test-102",
            title="新作映画の公開",
            link="https://example.com/test-102",
            published="2026-01-15T10:00:00Z",
            summary="話題の映画が公開される",
            content="詳細...",
            author="記者B",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = is_excluded(item, filter_config)
        assert result is True

    def test_not_excluded_when_has_financial_keywords(
        self, filter_config: dict
    ) -> None:
        """Test not excluded when item has both exclude and financial keywords."""
        from finance_news_collector.filtering import is_excluded

        item = FeedItem(
            item_id="test-103",
            title="サッカークラブの株価が上昇",
            link="https://example.com/test-103",
            published="2026-01-15T10:00:00Z",
            summary="サッカークラブの株式が市場で注目",
            content="詳細...",
            author="記者C",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = is_excluded(item, filter_config)
        assert result is False

    def test_not_excluded_financial_content(
        self, filter_config: dict, sample_feed_item: FeedItem
    ) -> None:
        """Test financial content is not excluded."""
        from finance_news_collector.filtering import is_excluded

        result = is_excluded(sample_feed_item, filter_config)
        assert result is False

    def test_case_insensitive_exclusion(self, filter_config: dict) -> None:
        """Test case-insensitive exclusion matching."""
        from finance_news_collector.filtering import is_excluded

        item = FeedItem(
            item_id="test-104",
            title="BASEBALL game results",
            link="https://example.com/test-104",
            published="2026-01-15T10:00:00Z",
            summary="Today's SOCCER match",
            content="詳細...",
            author="記者D",
            fetched_at="2026-01-15T11:00:00Z",
        )

        result = is_excluded(item, filter_config)
        assert result is True


class TestCalculateReliabilityScore:
    """Test calculate_reliability_score function."""

    def test_tier1_source_high_score(self, filter_config: dict) -> None:
        """Test tier1 source gets high reliability score."""
        from finance_news_collector.filtering import calculate_reliability_score

        item = FeedItem(
            item_id="test-201",
            title="株価と為替の動向",
            link="https://www.nikkei.com/article/test-201",
            published="2026-01-15T10:00:00Z",
            summary="金利政策の影響で株式市場が...",
            content="決算発表の業績...",
            author="記者A",
            fetched_at="2026-01-15T11:00:00Z",
        )

        score = calculate_reliability_score(item, filter_config)
        assert score > 0
        assert isinstance(score, int)

    def test_tier2_source_medium_score(self, filter_config: dict) -> None:
        """Test tier2 source gets medium reliability score."""
        from finance_news_collector.filtering import calculate_reliability_score

        item = FeedItem(
            item_id="test-202",
            title="株価と為替の動向",
            link="https://www.asahi.com/article/test-202",
            published="2026-01-15T10:00:00Z",
            summary="金利政策の影響で株式市場が...",
            content="決算発表の業績...",
            author="記者B",
            fetched_at="2026-01-15T11:00:00Z",
        )

        score_tier2 = calculate_reliability_score(item, filter_config)

        item_tier1 = FeedItem(
            item_id="test-203",
            title="株価と為替の動向",
            link="https://www.nikkei.com/article/test-203",
            published="2026-01-15T10:00:00Z",
            summary="金利政策の影響で株式市場が...",
            content="決算発表の業績...",
            author="記者C",
            fetched_at="2026-01-15T11:00:00Z",
        )

        score_tier1 = calculate_reliability_score(item_tier1, filter_config)

        assert score_tier2 < score_tier1
        assert score_tier2 > 0

    def test_unknown_source_low_score(self, filter_config: dict) -> None:
        """Test unknown source gets low reliability score."""
        from finance_news_collector.filtering import calculate_reliability_score

        item = FeedItem(
            item_id="test-204",
            title="株価動向",
            link="https://unknown-site.com/article/test-204",
            published="2026-01-15T10:00:00Z",
            summary="市場情報",
            content="詳細...",
            author="記者D",
            fetched_at="2026-01-15T11:00:00Z",
        )

        score = calculate_reliability_score(item, filter_config)
        assert score == 0

    def test_more_keywords_higher_score(self, filter_config: dict) -> None:
        """Test more keyword matches result in higher score."""
        from finance_news_collector.filtering import calculate_reliability_score

        item_few_keywords = FeedItem(
            item_id="test-205",
            title="株価動向",
            link="https://www.nikkei.com/article/test-205",
            published="2026-01-15T10:00:00Z",
            summary="一般的な内容",
            content="詳細...",
            author="記者E",
            fetched_at="2026-01-15T11:00:00Z",
        )

        item_many_keywords = FeedItem(
            item_id="test-206",
            title="株価、為替、金利の総合分析",
            link="https://www.nikkei.com/article/test-206",
            published="2026-01-15T10:00:00Z",
            summary="日銀の政策金利と為替市場の動向",
            content="決算発表、業績、株式市場の詳細分析",
            author="記者F",
            fetched_at="2026-01-15T11:00:00Z",
        )

        score_few = calculate_reliability_score(item_few_keywords, filter_config)
        score_many = calculate_reliability_score(item_many_keywords, filter_config)

        assert score_many > score_few

    def test_score_is_integer(
        self, filter_config: dict, sample_feed_item: FeedItem
    ) -> None:
        """Test reliability score is returned as integer."""
        from finance_news_collector.filtering import calculate_reliability_score

        score = calculate_reliability_score(sample_feed_item, filter_config)
        assert isinstance(score, int)

    def test_score_non_negative(
        self, filter_config: dict, sample_feed_item: FeedItem
    ) -> None:
        """Test reliability score is non-negative."""
        from finance_news_collector.filtering import calculate_reliability_score

        score = calculate_reliability_score(sample_feed_item, filter_config)
        assert score >= 0
