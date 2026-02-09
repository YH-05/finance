"""Property-based tests for ArticleGrouper using Hypothesis.

Tests for Issue #3400: ArticleGrouper・Markdown生成の実装

Property tests verify invariants that must hold for any valid input.
"""

from datetime import datetime, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from news.config.models import CategoryLabelsConfig
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
    StructuredSummary,
    SummarizationStatus,
    SummarizedArticle,
)

# =============================================================================
# Strategies
# =============================================================================

VALID_CATEGORIES = [
    "tech",
    "market",
    "finance",
    "stock",
    "sector",
    "macro",
    "economy",
    "earnings",
    "etfs",
    "yf_index",
    "yf_stock",
    "yf_ai_stock",
    "yf_sector_etf",
    "yf_macro",
    "unknown",
    "other",
]

EXPECTED_MAPPED_CATEGORIES = {"index", "stock", "sector", "macro", "ai", "finance"}

DEFAULT_STATUS_MAPPING: dict[str, str] = {
    "tech": "ai",
    "market": "index",
    "finance": "finance",
    "stock": "stock",
    "sector": "sector",
    "macro": "macro",
    "economy": "macro",
    "earnings": "stock",
    "etfs": "sector",
    "yf_index": "index",
    "yf_stock": "stock",
    "yf_ai_stock": "ai",
    "yf_sector_etf": "sector",
    "yf_macro": "macro",
}


def _make_article(category: str, url_suffix: int, date: datetime) -> SummarizedArticle:
    """テスト用の SummarizedArticle を作成する."""
    source = ArticleSource(
        source_type=SourceType.RSS,
        source_name="Test Source",
        category=category,
    )
    collected = CollectedArticle(
        url=f"https://example.com/article/{url_suffix}",  # type: ignore[arg-type]
        title=f"Test Article {url_suffix}",
        source=source,
        published=date,
        collected_at=datetime.now(tz=timezone.utc),
    )
    extracted = ExtractedArticle(
        collected=collected,
        body_text="Article content",
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_method="trafilatura",
    )
    summary = StructuredSummary(
        overview="Overview",
        key_points=["Point 1"],
        market_impact="Impact",
    )
    return SummarizedArticle(
        extracted=extracted,
        summary=summary,
        summarization_status=SummarizationStatus.SUCCESS,
    )


# Strategy for generating lists of articles
article_lists = st.lists(
    st.tuples(
        st.sampled_from(VALID_CATEGORIES),
        st.integers(min_value=1, max_value=10000),
        st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31),
            timezones=st.just(timezone.utc),
        ),
    ),
    min_size=0,
    max_size=20,
)


# =============================================================================
# Property Tests
# =============================================================================


class TestArticleGrouperProperties:
    """ArticleGrouper のプロパティベーステスト."""

    @given(data=article_lists)
    @settings(max_examples=50)
    def test_プロパティ_グループ化しても全記事が保持される(
        self, data: list[tuple[str, int, datetime]]
    ) -> None:
        """グループ化後の記事総数が入力と一致する."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=CategoryLabelsConfig(),
        )
        articles = [_make_article(cat, idx, dt) for cat, idx, dt in data]

        result = grouper.group(articles)

        total_articles = sum(len(g.articles) for g in result)
        assert total_articles == len(articles)

    @given(data=article_lists)
    @settings(max_examples=50)
    def test_プロパティ_全グループのカテゴリが有効な6カテゴリに含まれる(
        self, data: list[tuple[str, int, datetime]]
    ) -> None:
        """全グループのカテゴリが6つの有効カテゴリのいずれかである."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=CategoryLabelsConfig(),
        )
        articles = [_make_article(cat, idx, dt) for cat, idx, dt in data]

        result = grouper.group(articles)

        for group in result:
            assert group.category in EXPECTED_MAPPED_CATEGORIES, (
                f"Unexpected category: {group.category}"
            )

    @given(data=article_lists)
    @settings(max_examples=50)
    def test_プロパティ_同じカテゴリと日付の組は重複しない(
        self, data: list[tuple[str, int, datetime]]
    ) -> None:
        """(category, date) の組み合わせがグループ間で重複しない."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=CategoryLabelsConfig(),
        )
        articles = [_make_article(cat, idx, dt) for cat, idx, dt in data]

        result = grouper.group(articles)

        keys = [(g.category, g.date) for g in result]
        assert len(keys) == len(set(keys)), "Duplicate (category, date) groups found"

    @given(data=article_lists)
    @settings(max_examples=50)
    def test_プロパティ_各グループの記事数が1以上である(
        self, data: list[tuple[str, int, datetime]]
    ) -> None:
        """空のグループが作成されない（全グループの記事数 >= 1）."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=CategoryLabelsConfig(),
        )
        articles = [_make_article(cat, idx, dt) for cat, idx, dt in data]

        result = grouper.group(articles)

        for group in result:
            assert len(group.articles) >= 1, (
                f"Empty group found: {group.category}/{group.date}"
            )

    @given(data=article_lists)
    @settings(max_examples=50)
    def test_プロパティ_各グループのdateがYYYY_MM_DD形式である(
        self, data: list[tuple[str, int, datetime]]
    ) -> None:
        """各グループの date フィールドが YYYY-MM-DD 形式である."""
        import re

        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=CategoryLabelsConfig(),
        )
        articles = [_make_article(cat, idx, dt) for cat, idx, dt in data]

        result = grouper.group(articles)

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for group in result:
            assert date_pattern.match(group.date), f"Invalid date format: {group.date}"

    @given(data=article_lists)
    @settings(max_examples=50)
    def test_プロパティ_結果はcategoryとdateでソートされている(
        self, data: list[tuple[str, int, datetime]]
    ) -> None:
        """結果が (category, date) でソートされている."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=CategoryLabelsConfig(),
        )
        articles = [_make_article(cat, idx, dt) for cat, idx, dt in data]

        result = grouper.group(articles)

        keys = [(g.category, g.date) for g in result]
        assert keys == sorted(keys), "Result is not sorted by (category, date)"
