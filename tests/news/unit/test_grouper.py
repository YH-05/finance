"""Unit tests for ArticleGrouper.

Tests for Issue #3400: ArticleGrouper・Markdown生成の実装

Tests follow t-wada TDD naming conventions with Japanese test names.
"""

from datetime import datetime, timezone

import pytest

from news.config.models import CategoryLabelsConfig
from news.models import (
    ArticleSource,
    CategoryGroup,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
    StructuredSummary,
    SummarizationStatus,
    SummarizedArticle,
)


def _make_summarized_article(
    *,
    category: str = "market",
    source_name: str = "CNBC Markets",
    title: str = "Test Article",
    url: str = "https://example.com/article/1",
    published: datetime | None = None,
) -> SummarizedArticle:
    """テスト用の SummarizedArticle を作成するヘルパー."""
    source = ArticleSource(
        source_type=SourceType.RSS,
        source_name=source_name,
        category=category,
    )
    collected = CollectedArticle(
        url=url,  # type: ignore[arg-type]
        title=title,
        source=source,
        published=published or datetime(2026, 2, 9, 12, 0, 0, tzinfo=timezone.utc),
        collected_at=datetime.now(tz=timezone.utc),
    )
    extracted = ExtractedArticle(
        collected=collected,
        body_text="Full article content here...",
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_method="trafilatura",
    )
    summary = StructuredSummary(
        overview="Overview of the article",
        key_points=["Point 1", "Point 2"],
        market_impact="Positive impact on markets",
    )
    return SummarizedArticle(
        extracted=extracted,
        summary=summary,
        summarization_status=SummarizationStatus.SUCCESS,
    )


# =============================================================================
# Default status_mapping and category_labels for tests
# =============================================================================

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

DEFAULT_CATEGORY_LABELS = CategoryLabelsConfig()


class TestArticleGrouperGroup:
    """ArticleGrouper.group() のテストクラス."""

    def test_正常系_空リストで空結果を返す(self) -> None:
        """空の記事リストを渡すと空リストが返る."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )

        result = grouper.group([])

        assert result == []

    def test_正常系_単一記事を正しくグループ化する(self) -> None:
        """1件の記事が正しいカテゴリでグループ化される."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        article = _make_summarized_article(category="market")

        result = grouper.group([article])

        assert len(result) == 1
        assert result[0].category == "index"
        assert result[0].category_label == "株価指数"
        assert result[0].date == "2026-02-09"
        assert len(result[0].articles) == 1

    def test_正常系_status_mappingでtechがaiに変換される(self) -> None:
        """tech カテゴリが ai にマッピングされる."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        article = _make_summarized_article(category="tech")

        result = grouper.group([article])

        assert len(result) == 1
        assert result[0].category == "ai"
        assert result[0].category_label == "AI関連"

    def test_正常系_status_mappingでmarketがindexに変換される(self) -> None:
        """market カテゴリが index にマッピングされる."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        article = _make_summarized_article(category="market")

        result = grouper.group([article])

        assert len(result) == 1
        assert result[0].category == "index"

    def test_正常系_status_mappingでeconomyがmacroに変換される(self) -> None:
        """economy カテゴリが macro にマッピングされる."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        article = _make_summarized_article(category="economy")

        result = grouper.group([article])

        assert len(result) == 1
        assert result[0].category == "macro"
        assert result[0].category_label == "マクロ経済"

    def test_正常系_未知のカテゴリはfinanceにフォールバックする(self) -> None:
        """未知のカテゴリは finance にフォールバックする."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        article = _make_summarized_article(category="unknown_category")

        result = grouper.group([article])

        assert len(result) == 1
        assert result[0].category == "finance"
        assert result[0].category_label == "金融"

    def test_正常系_複数カテゴリの記事を別グループに分類する(self) -> None:
        """異なるカテゴリの記事が別々のグループに分類される."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        articles = [
            _make_summarized_article(category="market", url="https://example.com/1"),
            _make_summarized_article(category="tech", url="https://example.com/2"),
            _make_summarized_article(category="stock", url="https://example.com/3"),
        ]

        result = grouper.group(articles)

        categories = {g.category for g in result}
        assert categories == {"index", "ai", "stock"}

    def test_正常系_同じカテゴリの記事は同じグループにまとめられる(self) -> None:
        """同じカテゴリの複数記事が1つのグループにまとめられる."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        articles = [
            _make_summarized_article(
                category="market",
                url="https://example.com/1",
                title="Article 1",
            ),
            _make_summarized_article(
                category="market",
                url="https://example.com/2",
                title="Article 2",
            ),
        ]

        result = grouper.group(articles)

        assert len(result) == 1
        assert result[0].category == "index"
        assert len(result[0].articles) == 2

    def test_正常系_日付でグループ化される(self) -> None:
        """異なる日付の記事は別グループに分類される."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        articles = [
            _make_summarized_article(
                category="market",
                url="https://example.com/1",
                published=datetime(2026, 2, 9, 10, 0, 0, tzinfo=timezone.utc),
            ),
            _make_summarized_article(
                category="market",
                url="https://example.com/2",
                published=datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        result = grouper.group(articles)

        assert len(result) == 2
        dates = {g.date for g in result}
        assert dates == {"2026-02-09", "2026-02-10"}

    def test_正常系_publishedがNoneの場合collected_atの日付を使用する(self) -> None:
        """published が None の場合、collected_at から日付を抽出する."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        article = _make_summarized_article(category="market")
        # published を None に設定
        article.extracted.collected.published = None

        result = grouper.group([article])

        assert len(result) == 1
        # collected_at の日付が使用されるはず（今日の日付）
        assert result[0].date is not None
        assert len(result[0].date) == 10  # YYYY-MM-DD format

    def test_正常系_6カテゴリ全てに正しくグループ化する(self) -> None:
        """6カテゴリ全てにそれぞれ正しくグループ化される."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        articles = [
            _make_summarized_article(category="market", url="https://example.com/1"),
            _make_summarized_article(category="stock", url="https://example.com/2"),
            _make_summarized_article(category="sector", url="https://example.com/3"),
            _make_summarized_article(category="macro", url="https://example.com/4"),
            _make_summarized_article(category="tech", url="https://example.com/5"),
            _make_summarized_article(category="finance", url="https://example.com/6"),
        ]

        result = grouper.group(articles)

        categories = {g.category for g in result}
        assert categories == {"index", "stock", "sector", "macro", "ai", "finance"}

    def test_正常系_yfinanceカテゴリが正しくマッピングされる(self) -> None:
        """yfinance カテゴリ（yf_index, yf_stock 等）が正しくマッピングされる."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        articles = [
            _make_summarized_article(category="yf_index", url="https://example.com/1"),
            _make_summarized_article(
                category="yf_ai_stock", url="https://example.com/2"
            ),
            _make_summarized_article(
                category="yf_sector_etf", url="https://example.com/3"
            ),
        ]

        result = grouper.group(articles)

        categories = {g.category for g in result}
        assert categories == {"index", "ai", "sector"}

    def test_正常系_結果はcategoryでソートされる(self) -> None:
        """結果がカテゴリ名で安定的にソートされている."""
        from news.grouper import ArticleGrouper

        grouper = ArticleGrouper(
            status_mapping=DEFAULT_STATUS_MAPPING,
            category_labels=DEFAULT_CATEGORY_LABELS,
        )
        articles = [
            _make_summarized_article(category="tech", url="https://example.com/1"),
            _make_summarized_article(category="market", url="https://example.com/2"),
            _make_summarized_article(category="stock", url="https://example.com/3"),
        ]

        result = grouper.group(articles)

        result_categories = [g.category for g in result]
        assert result_categories == sorted(result_categories)
