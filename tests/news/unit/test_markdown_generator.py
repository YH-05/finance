"""Unit tests for CategoryMarkdownGenerator and MarkdownExporter.

Tests for Issue #3400: ArticleGrouper・Markdown生成の実装

Tests follow t-wada TDD naming conventions with Japanese test names.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

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
    overview: str = "Overview of the article",
    key_points: list[str] | None = None,
    market_impact: str = "Positive impact on markets",
    related_info: str | None = None,
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
        overview=overview,
        key_points=key_points or ["Point 1", "Point 2"],
        market_impact=market_impact,
        related_info=related_info,
    )
    return SummarizedArticle(
        extracted=extracted,
        summary=summary,
        summarization_status=SummarizationStatus.SUCCESS,
    )


def _make_category_group(
    *,
    category: str = "index",
    category_label: str = "株価指数",
    date: str = "2026-02-09",
    articles: list[SummarizedArticle] | None = None,
) -> CategoryGroup:
    """テスト用の CategoryGroup を作成するヘルパー."""
    if articles is None:
        articles = [_make_summarized_article()]
    return CategoryGroup(
        category=category,
        category_label=category_label,
        date=date,
        articles=articles,
    )


# =============================================================================
# CategoryMarkdownGenerator Tests
# =============================================================================


class TestCategoryMarkdownGeneratorGenerateIssueTitle:
    """CategoryMarkdownGenerator.generate_issue_title() のテストクラス."""

    def test_正常系_正しいタイトル形式を生成する(self) -> None:
        """'[株価指数] ニュースまとめ - 2026-02-09' 形式のタイトルを生成する."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        group = _make_category_group()

        title = generator.generate_issue_title(group)

        assert title == "[株価指数] ニュースまとめ - 2026-02-09"

    def test_正常系_異なるカテゴリラベルで正しいタイトルを生成する(self) -> None:
        """異なるカテゴリラベルで正しい形式のタイトルを生成する."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        group = _make_category_group(
            category="ai",
            category_label="AI関連",
            date="2026-02-10",
        )

        title = generator.generate_issue_title(group)

        assert title == "[AI関連] ニュースまとめ - 2026-02-10"


class TestCategoryMarkdownGeneratorGenerateIssueBody:
    """CategoryMarkdownGenerator.generate_issue_body() のテストクラス."""

    def test_正常系_ヘッダーセクションが含まれる(self) -> None:
        """生成されたMarkdownにヘッダーセクションが含まれる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        group = _make_category_group()

        body = generator.generate_issue_body(group)

        assert "# [株価指数] ニュースまとめ - 2026-02-09" in body
        assert "1件の記事を収集" in body

    def test_正常系_記事一覧セクションが含まれる(self) -> None:
        """生成されたMarkdownに記事一覧セクションが含まれる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        group = _make_category_group()

        body = generator.generate_issue_body(group)

        assert "## 記事一覧" in body

    def test_正常系_記事タイトルが含まれる(self) -> None:
        """生成されたMarkdownに記事タイトルが含まれる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        article = _make_summarized_article(title="S&P500が過去最高値を更新")
        group = _make_category_group(articles=[article])

        body = generator.generate_issue_body(group)

        assert "S&P500が過去最高値を更新" in body

    def test_正常系_ソース名と公開日が含まれる(self) -> None:
        """生成されたMarkdownにソース名と公開日が含まれる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        article = _make_summarized_article(
            source_name="CNBC Markets",
            published=datetime(2026, 2, 9, 12, 0, 0, tzinfo=timezone.utc),
        )
        group = _make_category_group(articles=[article])

        body = generator.generate_issue_body(group)

        assert "CNBC Markets" in body
        assert "2026-02-09" in body

    def test_正常系_URLが含まれる(self) -> None:
        """生成されたMarkdownに記事URLが含まれる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        article = _make_summarized_article(url="https://www.cnbc.com/article/123")
        group = _make_category_group(articles=[article])

        body = generator.generate_issue_body(group)

        assert "https://www.cnbc.com/article/123" in body

    def test_正常系_概要セクションが含まれる(self) -> None:
        """生成されたMarkdownに概要セクションが含まれる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        article = _make_summarized_article(overview="Markets rallied strongly today")
        group = _make_category_group(articles=[article])

        body = generator.generate_issue_body(group)

        assert "概要" in body
        assert "Markets rallied strongly today" in body

    def test_正常系_キーポイントセクションが含まれる(self) -> None:
        """生成されたMarkdownにキーポイントセクションが含まれる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        article = _make_summarized_article(
            key_points=["S&P 500 up 1%", "Tech leads gains"]
        )
        group = _make_category_group(articles=[article])

        body = generator.generate_issue_body(group)

        assert "キーポイント" in body
        assert "- S&P 500 up 1%" in body
        assert "- Tech leads gains" in body

    def test_正常系_市場への影響セクションが含まれる(self) -> None:
        """生成されたMarkdownに市場への影響セクションが含まれる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        article = _make_summarized_article(market_impact="Bullish sentiment continues")
        group = _make_category_group(articles=[article])

        body = generator.generate_issue_body(group)

        assert "市場への影響" in body
        assert "Bullish sentiment continues" in body

    def test_正常系_複数記事のMarkdownが正しく生成される(self) -> None:
        """複数記事を含むグループのMarkdownが正しく番号付けされる."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        articles = [
            _make_summarized_article(title="Article 1", url="https://example.com/1"),
            _make_summarized_article(title="Article 2", url="https://example.com/2"),
            _make_summarized_article(title="Article 3", url="https://example.com/3"),
        ]
        group = _make_category_group(articles=articles)

        body = generator.generate_issue_body(group)

        assert "### 1. Article 1" in body
        assert "### 2. Article 2" in body
        assert "### 3. Article 3" in body
        assert "3件の記事を収集" in body

    def test_正常系_記事間にセパレータがある(self) -> None:
        """複数記事の間にセパレータ(---)がある."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        articles = [
            _make_summarized_article(title="Article 1", url="https://example.com/1"),
            _make_summarized_article(title="Article 2", url="https://example.com/2"),
        ]
        group = _make_category_group(articles=articles)

        body = generator.generate_issue_body(group)

        assert "---" in body

    def test_エッジケース_publishedがNoneの場合不明と表示する(self) -> None:
        """published が None の場合、公開日に '不明' と表示する."""
        from news.markdown_generator import CategoryMarkdownGenerator

        generator = CategoryMarkdownGenerator()
        article = _make_summarized_article()
        article.extracted.collected.published = None
        group = _make_category_group(articles=[article])

        body = generator.generate_issue_body(group)

        assert "不明" in body


# =============================================================================
# MarkdownExporter Tests
# =============================================================================


class TestMarkdownExporter:
    """MarkdownExporter のテストクラス."""

    def test_正常系_ファイルが正しいパスに出力される(self, tmp_path: Path) -> None:
        """MarkdownExporter が正しいパスにファイルを出力する."""
        from news.markdown_generator import MarkdownExporter

        exporter = MarkdownExporter()
        group = _make_category_group(
            category="index",
            date="2026-02-09",
        )

        result_path = exporter.export(group, export_dir=tmp_path)

        expected_path = tmp_path / "2026-02-09" / "index.md"
        assert result_path == expected_path
        assert result_path.exists()

    def test_正常系_出力ファイルにMarkdownが含まれる(self, tmp_path: Path) -> None:
        """出力ファイルに正しいMarkdownが含まれる."""
        from news.markdown_generator import MarkdownExporter

        exporter = MarkdownExporter()
        group = _make_category_group()

        result_path = exporter.export(group, export_dir=tmp_path)

        content = result_path.read_text(encoding="utf-8")
        assert "# [株価指数] ニュースまとめ - 2026-02-09" in content

    def test_正常系_ディレクトリが自動作成される(self, tmp_path: Path) -> None:
        """エクスポート先ディレクトリが存在しない場合自動で作成される."""
        from news.markdown_generator import MarkdownExporter

        exporter = MarkdownExporter()
        group = _make_category_group(date="2026-02-09")
        export_dir = tmp_path / "nested" / "dir"

        result_path = exporter.export(group, export_dir=export_dir)

        assert result_path.exists()
        assert result_path.parent == export_dir / "2026-02-09"

    def test_正常系_異なるカテゴリで異なるファイル名になる(
        self, tmp_path: Path
    ) -> None:
        """異なるカテゴリのグループは異なるファイル名で出力される."""
        from news.markdown_generator import MarkdownExporter

        exporter = MarkdownExporter()
        group_index = _make_category_group(category="index")
        group_stock = _make_category_group(category="stock", category_label="個別銘柄")

        path_index = exporter.export(group_index, export_dir=tmp_path)
        path_stock = exporter.export(group_stock, export_dir=tmp_path)

        assert path_index.name == "index.md"
        assert path_stock.name == "stock.md"

    def test_正常系_複数グループを同じ日付ディレクトリに出力できる(
        self, tmp_path: Path
    ) -> None:
        """複数カテゴリのグループを同じ日付ディレクトリに出力できる."""
        from news.markdown_generator import MarkdownExporter

        exporter = MarkdownExporter()
        groups = [
            _make_category_group(category="index"),
            _make_category_group(category="stock", category_label="個別銘柄"),
            _make_category_group(category="ai", category_label="AI関連"),
        ]

        paths = [exporter.export(g, export_dir=tmp_path) for g in groups]

        date_dir = tmp_path / "2026-02-09"
        assert date_dir.exists()
        assert len(list(date_dir.iterdir())) == 3
        assert all(p.exists() for p in paths)

    def test_正常系_戻り値がPathオブジェクトである(self, tmp_path: Path) -> None:
        """export() の戻り値が Path オブジェクトである."""
        from news.markdown_generator import MarkdownExporter

        exporter = MarkdownExporter()
        group = _make_category_group()

        result = exporter.export(group, export_dir=tmp_path)

        assert isinstance(result, Path)
