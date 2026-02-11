"""Unit tests for StructureValidator (selector hit rate structure change detection).

Tests cover:
- Article list selector hit count checking
- Title/date selector hit rate calculation
- Threshold-based alert logging (ERROR/WARNING/INFO)
- Structure change patterns (complete change, partial change, normal)
"""

import logging

import pytest

from rss.services.company_scrapers.structure_validator import StructureValidator
from rss.services.company_scrapers.types import CompanyConfig, StructureReport

# ---------------------------------------------------------------------------
# Helper: sample HTML builders
# ---------------------------------------------------------------------------


def _build_html(articles: list[dict[str, str | None]]) -> str:
    """Build a sample blog HTML page from article specs.

    Parameters
    ----------
    articles : list[dict[str, str | None]]
        Each dict may contain "title" and "date" keys.
        If a key is None or absent, that element is omitted.
    """
    items: list[str] = []
    for art in articles:
        parts: list[str] = []
        if art.get("title") is not None:
            parts.append(f"<h2>{art['title']}</h2>")
        if art.get("date") is not None:
            parts.append(f"<time>{art['date']}</time>")
        items.append(f"<article>{''.join(parts)}</article>")
    body = "\n".join(items)
    return f"<html><body>{body}</body></html>"


def _make_config(**overrides: object) -> CompanyConfig:
    """Create a CompanyConfig with sensible defaults for testing."""
    defaults: dict[str, object] = {
        "key": "test_company",
        "name": "Test Company",
        "category": "test",
        "blog_url": "https://example.com/blog",
        "article_list_selector": "article",
        "article_title_selector": "h2",
        "article_date_selector": "time",
    }
    defaults.update(overrides)
    return CompanyConfig(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def validator() -> StructureValidator:
    """Create a StructureValidator instance."""
    return StructureValidator()


# ---------------------------------------------------------------------------
# Article list selector hit count
# ---------------------------------------------------------------------------


class TestArticleListSelectorHitCount:
    """Tests for article list selector hit counting."""

    def test_正常系_記事要素が正しくカウントされる(
        self,
        validator: StructureValidator,
    ) -> None:
        html = _build_html(
            [
                {"title": "Article 1", "date": "2026-01-01"},
                {"title": "Article 2", "date": "2026-01-02"},
                {"title": "Article 3", "date": "2026-01-03"},
            ]
        )
        config = _make_config()
        report = validator.validate(html, config)
        assert report.article_list_hits == 3

    def test_正常系_記事が0件の場合ヒット数が0(
        self,
        validator: StructureValidator,
    ) -> None:
        html = "<html><body><div>No articles here</div></body></html>"
        config = _make_config()
        report = validator.validate(html, config)
        assert report.article_list_hits == 0

    def test_正常系_カスタムセレクタで記事をカウントできる(
        self,
        validator: StructureValidator,
    ) -> None:
        html = (
            "<html><body>"
            '<div class="post"><h3>Title</h3><span class="date">2026-01-01</span></div>'
            '<div class="post"><h3>Title 2</h3><span class="date">2026-01-02</span></div>'
            "</body></html>"
        )
        config = _make_config(
            article_list_selector="div.post",
            article_title_selector="h3",
            article_date_selector="span.date",
        )
        report = validator.validate(html, config)
        assert report.article_list_hits == 2


# ---------------------------------------------------------------------------
# Hit rate calculation
# ---------------------------------------------------------------------------


class TestHitRateCalculation:
    """Tests for title/date selector hit rate calculation."""

    def test_正常系_全記事にタイトルと日付がある場合ヒット率1(
        self,
        validator: StructureValidator,
    ) -> None:
        html = _build_html(
            [
                {"title": "A", "date": "2026-01-01"},
                {"title": "B", "date": "2026-01-02"},
                {"title": "C", "date": "2026-01-03"},
                {"title": "D", "date": "2026-01-04"},
                {"title": "E", "date": "2026-01-05"},
            ]
        )
        config = _make_config()
        report = validator.validate(html, config)
        assert report.hit_rate == pytest.approx(1.0)
        assert report.title_found_count == 5
        assert report.date_found_count == 5

    def test_正常系_タイトルのみの記事でヒット率が低下する(
        self,
        validator: StructureValidator,
    ) -> None:
        html = _build_html(
            [
                {"title": "A", "date": "2026-01-01"},
                {"title": "B", "date": None},  # date missing
            ]
        )
        config = _make_config()
        report = validator.validate(html, config)
        assert report.title_found_count == 2
        assert report.date_found_count == 1
        # hit_rate = (title_hits + date_hits) / (2 * article_count)
        # = (2 + 1) / (2 * 2) = 3/4 = 0.75
        assert report.hit_rate == pytest.approx(0.75)

    def test_正常系_日付のみの記事でヒット率が低下する(
        self,
        validator: StructureValidator,
    ) -> None:
        html = _build_html(
            [
                {"title": None, "date": "2026-01-01"},
                {"title": None, "date": "2026-01-02"},
            ]
        )
        config = _make_config()
        report = validator.validate(html, config)
        assert report.title_found_count == 0
        assert report.date_found_count == 2
        # hit_rate = (0 + 2) / (2 * 2) = 2/4 = 0.5
        assert report.hit_rate == pytest.approx(0.5)

    def test_正常系_タイトルも日付もない場合ヒット率0(
        self,
        validator: StructureValidator,
    ) -> None:
        # Articles exist but have no title/date matching selectors
        html = (
            "<html><body>"
            "<article><p>No title or date</p></article>"
            "<article><p>Another one</p></article>"
            "</body></html>"
        )
        config = _make_config()
        report = validator.validate(html, config)
        assert report.article_list_hits == 2
        assert report.title_found_count == 0
        assert report.date_found_count == 0
        assert report.hit_rate == pytest.approx(0.0)

    def test_エッジケース_記事が0件の場合ヒット率0(
        self,
        validator: StructureValidator,
    ) -> None:
        html = "<html><body></body></html>"
        config = _make_config()
        report = validator.validate(html, config)
        assert report.article_list_hits == 0
        assert report.hit_rate == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# StructureReport output
# ---------------------------------------------------------------------------


class TestStructureReportOutput:
    """Tests for StructureReport correctness."""

    def test_正常系_レポートのcompanyフィールドがconfigのkeyに一致する(
        self,
        validator: StructureValidator,
    ) -> None:
        html = _build_html([{"title": "A", "date": "2026-01-01"}])
        config = _make_config(key="nvidia_ai")
        report = validator.validate(html, config)
        assert report.company == "nvidia_ai"

    def test_正常系_レポートがStructureReport型である(
        self,
        validator: StructureValidator,
    ) -> None:
        html = _build_html([{"title": "A", "date": "2026-01-01"}])
        config = _make_config()
        report = validator.validate(html, config)
        assert isinstance(report, StructureReport)


# ---------------------------------------------------------------------------
# Threshold-based logging
# ---------------------------------------------------------------------------


class TestThresholdBasedLogging:
    """Tests for threshold-based alert logging."""

    def test_正常系_ヒット率0でERRORログが出力される(
        self,
        validator: StructureValidator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        html = (
            "<html><body><article><p>No matching selectors</p></article></body></html>"
        )
        config = _make_config(key="broken_company")
        with caplog.at_level(logging.DEBUG):
            validator.validate(html, config)
        error_messages = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(error_messages) > 0
        assert any("broken_company" in r.message for r in error_messages)

    def test_正常系_ヒット率05未満でWARNINGログが出力される(
        self,
        validator: StructureValidator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # 4 articles, only 1 title and 0 dates => hit_rate = 1/8 = 0.125
        html = (
            "<html><body>"
            "<article><h2>Title</h2></article>"
            "<article><p>None</p></article>"
            "<article><p>None</p></article>"
            "<article><p>None</p></article>"
            "</body></html>"
        )
        config = _make_config(key="degraded_company")
        with caplog.at_level(logging.DEBUG):
            validator.validate(html, config)
        warn_messages = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warn_messages) > 0

    def test_正常系_ヒット率08未満でWARNINGログが出力される(
        self,
        validator: StructureValidator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # 2 articles: both have title, 1 has date => hit_rate = 3/4 = 0.75
        html = _build_html(
            [
                {"title": "A", "date": "2026-01-01"},
                {"title": "B", "date": None},
            ]
        )
        config = _make_config(key="partial_company")
        with caplog.at_level(logging.DEBUG):
            validator.validate(html, config)
        warn_messages = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warn_messages) > 0

    def test_正常系_ヒット率08以上でINFOログが出力される(
        self,
        validator: StructureValidator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        html = _build_html(
            [
                {"title": "A", "date": "2026-01-01"},
                {"title": "B", "date": "2026-01-02"},
                {"title": "C", "date": "2026-01-03"},
                {"title": "D", "date": "2026-01-04"},
                {"title": "E", "date": "2026-01-05"},
            ]
        )
        config = _make_config(key="healthy_company")
        with caplog.at_level(logging.DEBUG):
            validator.validate(html, config)
        # Should have INFO log (not WARNING or ERROR)
        info_messages = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_messages) > 0
        error_warn_messages = [
            r for r in caplog.records if r.levelno >= logging.WARNING
        ]
        assert len(error_warn_messages) == 0

    def test_正常系_記事0件でERRORログが出力される(
        self,
        validator: StructureValidator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        html = "<html><body><div>Empty page</div></body></html>"
        config = _make_config(key="empty_company")
        with caplog.at_level(logging.DEBUG):
            validator.validate(html, config)
        error_messages = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(error_messages) > 0


# ---------------------------------------------------------------------------
# Structure change patterns
# ---------------------------------------------------------------------------


class TestStructureChangePatterns:
    """Tests for distinct structure change patterns."""

    def test_正常系_完全構造変更パターン_ヒット率0(
        self,
        validator: StructureValidator,
    ) -> None:
        """Selectors don't match anything - complete structure change."""
        html = (
            "<html><body>"
            "<article><span>Different structure</span></article>"
            "</body></html>"
        )
        config = _make_config()
        report = validator.validate(html, config)
        assert report.hit_rate == pytest.approx(0.0)
        assert report.article_list_hits > 0  # articles exist
        assert report.title_found_count == 0
        assert report.date_found_count == 0

    def test_正常系_部分構造変更パターン_ヒット率05(
        self,
        validator: StructureValidator,
    ) -> None:
        """Some selectors match - partial structure change."""
        # 2 articles, both have title, neither has date
        html = _build_html(
            [
                {"title": "Title 1", "date": None},
                {"title": "Title 2", "date": None},
            ]
        )
        config = _make_config()
        report = validator.validate(html, config)
        # hit_rate = (2 + 0) / (2 * 2) = 0.5
        assert report.hit_rate == pytest.approx(0.5)

    def test_正常系_正常パターン_ヒット率1(
        self,
        validator: StructureValidator,
    ) -> None:
        """All selectors match - structure is healthy."""
        html = _build_html(
            [
                {"title": "A", "date": "2026-01-01"},
                {"title": "B", "date": "2026-01-02"},
                {"title": "C", "date": "2026-01-03"},
            ]
        )
        config = _make_config()
        report = validator.validate(html, config)
        assert report.hit_rate == pytest.approx(1.0)
        assert report.article_list_hits == 3
        assert report.title_found_count == 3
        assert report.date_found_count == 3

    def test_正常系_セレクタ不一致パターン_記事リストもヒットしない(
        self,
        validator: StructureValidator,
    ) -> None:
        """Article list selector doesn't match - entirely wrong page."""
        html = (
            "<html><body><section><p>Completely different</p></section></body></html>"
        )
        config = _make_config()
        report = validator.validate(html, config)
        assert report.article_list_hits == 0
        assert report.hit_rate == pytest.approx(0.0)
