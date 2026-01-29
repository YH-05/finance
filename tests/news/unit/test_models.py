"""Unit tests for news/models.py - SourceType, ArticleSource, CollectedArticle models.

Tests follow t-wada TDD naming conventions with Japanese test names.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


class TestSourceType:
    """SourceType StrEnum のテストクラス."""

    def test_正常系_RSS値が定義されている(self) -> None:
        """SourceType.RSS が "rss" 値で定義されていること."""
        from news.models import SourceType

        assert SourceType.RSS == "rss"
        assert SourceType.RSS.value == "rss"

    def test_正常系_YFINANCE値が定義されている(self) -> None:
        """SourceType.YFINANCE が "yfinance" 値で定義されていること."""
        from news.models import SourceType

        assert SourceType.YFINANCE == "yfinance"
        assert SourceType.YFINANCE.value == "yfinance"

    def test_正常系_SCRAPE値が定義されている(self) -> None:
        """SourceType.SCRAPE が "scrape" 値で定義されていること."""
        from news.models import SourceType

        assert SourceType.SCRAPE == "scrape"
        assert SourceType.SCRAPE.value == "scrape"

    def test_正常系_全3種類の値が存在する(self) -> None:
        """SourceType は RSS, YFINANCE, SCRAPE の3種類のみ."""
        from news.models import SourceType

        members = list(SourceType)
        assert len(members) == 3
        assert SourceType.RSS in members
        assert SourceType.YFINANCE in members
        assert SourceType.SCRAPE in members

    def test_正常系_StrEnumなので文字列として比較可能(self) -> None:
        """SourceType は StrEnum なので文字列との比較が可能."""
        from news.models import SourceType

        assert SourceType.RSS == "rss"
        assert SourceType.YFINANCE == "yfinance"
        assert SourceType.SCRAPE == "scrape"


class TestArticleSource:
    """ArticleSource Pydantic モデルのテストクラス."""

    def test_正常系_必須フィールドで作成できる(self) -> None:
        """source_type, source_name, category で ArticleSource を作成できる."""
        from news.models import ArticleSource, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )

        assert source.source_type == SourceType.RSS
        assert source.source_name == "CNBC Markets"
        assert source.category == "market"
        assert source.feed_id is None

    def test_正常系_feed_idを指定して作成できる(self) -> None:
        """feed_id を指定して ArticleSource を作成できる."""
        from news.models import ArticleSource, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
            feed_id="cnbc-markets-001",
        )

        assert source.feed_id == "cnbc-markets-001"

    def test_正常系_YFINANCEソースで作成できる(self) -> None:
        """SourceType.YFINANCE で ArticleSource を作成できる."""
        from news.models import ArticleSource, SourceType

        source = ArticleSource(
            source_type=SourceType.YFINANCE,
            source_name="NVDA",
            category="yf_ai_stock",
        )

        assert source.source_type == SourceType.YFINANCE
        assert source.source_name == "NVDA"
        assert source.category == "yf_ai_stock"

    def test_正常系_SCRAPEソースで作成できる(self) -> None:
        """SourceType.SCRAPE で ArticleSource を作成できる."""
        from news.models import ArticleSource, SourceType

        source = ArticleSource(
            source_type=SourceType.SCRAPE,
            source_name="Custom Scraper",
            category="tech",
        )

        assert source.source_type == SourceType.SCRAPE
        assert source.source_name == "Custom Scraper"
        assert source.category == "tech"

    def test_異常系_source_typeが必須(self) -> None:
        """source_type がない場合は ValidationError."""
        from news.models import ArticleSource

        with pytest.raises(ValidationError) as exc_info:
            ArticleSource(
                source_name="CNBC Markets",
                category="market",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("source_type",) for e in errors)

    def test_異常系_source_nameが必須(self) -> None:
        """source_name がない場合は ValidationError."""
        from news.models import ArticleSource, SourceType

        with pytest.raises(ValidationError) as exc_info:
            ArticleSource(
                source_type=SourceType.RSS,
                category="market",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("source_name",) for e in errors)

    def test_異常系_categoryが必須(self) -> None:
        """category がない場合は ValidationError."""
        from news.models import ArticleSource, SourceType

        with pytest.raises(ValidationError) as exc_info:
            ArticleSource(
                source_type=SourceType.RSS,
                source_name="CNBC Markets",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("category",) for e in errors)

    def test_正常系_モデルをdictに変換できる(self) -> None:
        """ArticleSource は model_dump() で dict に変換可能."""
        from news.models import ArticleSource, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
            feed_id="cnbc-001",
        )

        data = source.model_dump()

        assert data["source_type"] == SourceType.RSS
        assert data["source_name"] == "CNBC Markets"
        assert data["category"] == "market"
        assert data["feed_id"] == "cnbc-001"

    def test_正常系_dictからモデルを作成できる(self) -> None:
        """dict から ArticleSource を作成可能."""
        from news.models import ArticleSource, SourceType

        data = {
            "source_type": "rss",
            "source_name": "CNBC Markets",
            "category": "market",
        }

        source = ArticleSource.model_validate(data)

        assert source.source_type == SourceType.RSS
        assert source.source_name == "CNBC Markets"
        assert source.category == "market"

    def test_正常系_JSONシリアライズ可能(self) -> None:
        """ArticleSource は JSON シリアライズ可能."""
        from news.models import ArticleSource, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )

        json_str = source.model_dump_json()

        assert '"source_type":"rss"' in json_str
        assert '"source_name":"CNBC Markets"' in json_str
        assert '"category":"market"' in json_str


class TestCollectedArticle:
    """CollectedArticle Pydantic モデルのテストクラス."""

    def test_正常系_必須フィールドで作成できる(self) -> None:
        """url, title, source, collected_at で CollectedArticle を作成できる."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected_at = datetime.now(tz=timezone.utc)

        article = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=collected_at,
        )

        assert str(article.url) == "https://www.cnbc.com/article/123"
        assert article.title == "Sample Article"
        assert article.source == source
        assert article.collected_at == collected_at
        assert article.published is None
        assert article.raw_summary is None

    def test_正常系_オプションフィールドを指定して作成できる(self) -> None:
        """published, raw_summary を指定して CollectedArticle を作成できる."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        published = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        collected_at = datetime.now(tz=timezone.utc)

        article = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            published=published,
            raw_summary="This is the RSS summary of the article.",
            source=source,
            collected_at=collected_at,
        )

        assert article.published == published
        assert article.raw_summary == "This is the RSS summary of the article."

    def test_正常系_YFINANCEソースで作成できる(self) -> None:
        """yfinance ソースの記事を作成できる."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.YFINANCE,
            source_name="NVDA",
            category="yf_ai_stock",
        )
        collected_at = datetime.now(tz=timezone.utc)

        article = CollectedArticle(
            url="https://finance.yahoo.com/news/nvda-article",  # type: ignore[arg-type]
            title="NVDA Q4 Earnings",
            source=source,
            collected_at=collected_at,
        )

        assert article.source.source_type == SourceType.YFINANCE
        assert article.source.source_name == "NVDA"

    def test_異常系_urlが必須(self) -> None:
        """url がない場合は ValidationError."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected_at = datetime.now(tz=timezone.utc)

        with pytest.raises(ValidationError) as exc_info:
            CollectedArticle(
                title="Sample Article",
                source=source,
                collected_at=collected_at,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("url",) for e in errors)

    def test_異常系_titleが必須(self) -> None:
        """title がない場合は ValidationError."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected_at = datetime.now(tz=timezone.utc)

        with pytest.raises(ValidationError) as exc_info:
            CollectedArticle(
                url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
                source=source,
                collected_at=collected_at,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_異常系_sourceが必須(self) -> None:
        """source がない場合は ValidationError."""
        from news.models import CollectedArticle

        collected_at = datetime.now(tz=timezone.utc)

        with pytest.raises(ValidationError) as exc_info:
            CollectedArticle(
                url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
                title="Sample Article",
                collected_at=collected_at,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("source",) for e in errors)

    def test_異常系_collected_atが必須(self) -> None:
        """collected_at がない場合は ValidationError."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )

        with pytest.raises(ValidationError) as exc_info:
            CollectedArticle(
                url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
                title="Sample Article",
                source=source,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("collected_at",) for e in errors)

    def test_異常系_不正なURLでValidationError(self) -> None:
        """不正なURL形式では ValidationError."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected_at = datetime.now(tz=timezone.utc)

        with pytest.raises(ValidationError) as exc_info:
            CollectedArticle(
                url="not-a-valid-url",  # type: ignore[arg-type]
                title="Sample Article",
                source=source,
                collected_at=collected_at,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("url",) for e in errors)

    def test_正常系_モデルをdictに変換できる(self) -> None:
        """CollectedArticle は model_dump() で dict に変換可能."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected_at = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        article = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            raw_summary="Summary text",
            source=source,
            collected_at=collected_at,
        )

        data = article.model_dump()

        assert str(data["url"]) == "https://www.cnbc.com/article/123"
        assert data["title"] == "Sample Article"
        assert data["raw_summary"] == "Summary text"
        assert data["published"] is None
        assert data["source"]["source_type"] == SourceType.RSS
        assert data["collected_at"] == collected_at

    def test_正常系_dictからモデルを作成できる(self) -> None:
        """dict から CollectedArticle を作成可能."""
        from news.models import CollectedArticle, SourceType

        data = {
            "url": "https://www.cnbc.com/article/123",
            "title": "Sample Article",
            "published": "2025-01-15T10:30:00Z",
            "raw_summary": "Summary text",
            "source": {
                "source_type": "rss",
                "source_name": "CNBC Markets",
                "category": "market",
            },
            "collected_at": "2025-01-15T12:00:00Z",
        }

        article = CollectedArticle.model_validate(data)

        assert str(article.url) == "https://www.cnbc.com/article/123"
        assert article.title == "Sample Article"
        assert article.source.source_type == SourceType.RSS
        assert article.published is not None
        assert article.raw_summary == "Summary text"

    def test_正常系_JSONシリアライズ可能(self) -> None:
        """CollectedArticle は JSON シリアライズ可能."""
        from news.models import ArticleSource, CollectedArticle, SourceType

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected_at = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        article = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=collected_at,
        )

        json_str = article.model_dump_json()

        assert "https://www.cnbc.com/article/123" in json_str
        assert '"title":"Sample Article"' in json_str
        assert '"source_type":"rss"' in json_str
