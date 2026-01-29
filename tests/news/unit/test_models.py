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


class TestExtractionStatus:
    """ExtractionStatus StrEnum のテストクラス."""

    def test_正常系_SUCCESS値が定義されている(self) -> None:
        """ExtractionStatus.SUCCESS が "success" 値で定義されていること."""
        from news.models import ExtractionStatus

        assert ExtractionStatus.SUCCESS == "success"
        assert ExtractionStatus.SUCCESS.value == "success"

    def test_正常系_FAILED値が定義されている(self) -> None:
        """ExtractionStatus.FAILED が "failed" 値で定義されていること."""
        from news.models import ExtractionStatus

        assert ExtractionStatus.FAILED == "failed"
        assert ExtractionStatus.FAILED.value == "failed"

    def test_正常系_PAYWALL値が定義されている(self) -> None:
        """ExtractionStatus.PAYWALL が "paywall" 値で定義されていること."""
        from news.models import ExtractionStatus

        assert ExtractionStatus.PAYWALL == "paywall"
        assert ExtractionStatus.PAYWALL.value == "paywall"

    def test_正常系_TIMEOUT値が定義されている(self) -> None:
        """ExtractionStatus.TIMEOUT が "timeout" 値で定義されていること."""
        from news.models import ExtractionStatus

        assert ExtractionStatus.TIMEOUT == "timeout"
        assert ExtractionStatus.TIMEOUT.value == "timeout"

    def test_正常系_全4種類の値が存在する(self) -> None:
        """ExtractionStatus は SUCCESS, FAILED, PAYWALL, TIMEOUT の4種類のみ."""
        from news.models import ExtractionStatus

        members = list(ExtractionStatus)
        assert len(members) == 4
        assert ExtractionStatus.SUCCESS in members
        assert ExtractionStatus.FAILED in members
        assert ExtractionStatus.PAYWALL in members
        assert ExtractionStatus.TIMEOUT in members

    def test_正常系_StrEnumなので文字列として比較可能(self) -> None:
        """ExtractionStatus は StrEnum なので文字列との比較が可能."""
        from news.models import ExtractionStatus

        assert ExtractionStatus.SUCCESS == "success"
        assert ExtractionStatus.FAILED == "failed"
        assert ExtractionStatus.PAYWALL == "paywall"
        assert ExtractionStatus.TIMEOUT == "timeout"


class TestExtractedArticle:
    """ExtractedArticle Pydantic モデルのテストクラス."""

    def test_正常系_必須フィールドで作成できる(self) -> None:
        """collected, body_text, extraction_status, extraction_method で作成できる."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=datetime.now(tz=timezone.utc),
        )

        extracted = ExtractedArticle(
            collected=collected,
            body_text="This is the article body content.",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )

        assert extracted.collected == collected
        assert extracted.body_text == "This is the article body content."
        assert extracted.extraction_status == ExtractionStatus.SUCCESS
        assert extracted.extraction_method == "trafilatura"
        assert extracted.error_message is None

    def test_正常系_error_messageを指定して作成できる(self) -> None:
        """error_message を指定して ExtractedArticle を作成できる."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=datetime.now(tz=timezone.utc),
        )

        extracted = ExtractedArticle(
            collected=collected,
            body_text=None,
            extraction_status=ExtractionStatus.FAILED,
            extraction_method="trafilatura",
            error_message="Failed to extract content",
        )

        assert extracted.error_message == "Failed to extract content"
        assert extracted.body_text is None
        assert extracted.extraction_status == ExtractionStatus.FAILED

    def test_正常系_PAYWALL状態で作成できる(self) -> None:
        """ペイウォール検出時の ExtractedArticle を作成できる."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="WSJ",
            category="finance",
        )
        collected = CollectedArticle(
            url="https://www.wsj.com/article/123",  # type: ignore[arg-type]
            title="Premium Article",
            source=source,
            collected_at=datetime.now(tz=timezone.utc),
        )

        extracted = ExtractedArticle(
            collected=collected,
            body_text=None,
            extraction_status=ExtractionStatus.PAYWALL,
            extraction_method="trafilatura",
            error_message="Paywall detected",
        )

        assert extracted.extraction_status == ExtractionStatus.PAYWALL
        assert extracted.body_text is None

    def test_正常系_TIMEOUT状態で作成できる(self) -> None:
        """タイムアウト時の ExtractedArticle を作成できる."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="Slow Site",
            category="tech",
        )
        collected = CollectedArticle(
            url="https://slow.example.com/article",  # type: ignore[arg-type]
            title="Slow Article",
            source=source,
            collected_at=datetime.now(tz=timezone.utc),
        )

        extracted = ExtractedArticle(
            collected=collected,
            body_text=None,
            extraction_status=ExtractionStatus.TIMEOUT,
            extraction_method="trafilatura",
            error_message="Request timed out after 30s",
        )

        assert extracted.extraction_status == ExtractionStatus.TIMEOUT
        assert extracted.body_text is None

    def test_正常系_fallback抽出方法で作成できる(self) -> None:
        """fallback 抽出方法の ExtractedArticle を作成できる."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=datetime.now(tz=timezone.utc),
        )

        extracted = ExtractedArticle(
            collected=collected,
            body_text="Fallback extracted content.",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="fallback",
        )

        assert extracted.extraction_method == "fallback"

    def test_異常系_collectedが必須(self) -> None:
        """collected がない場合は ValidationError."""
        from news.models import ExtractedArticle, ExtractionStatus

        with pytest.raises(ValidationError) as exc_info:
            ExtractedArticle(
                body_text="Some content",
                extraction_status=ExtractionStatus.SUCCESS,
                extraction_method="trafilatura",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("collected",) for e in errors)

    def test_異常系_extraction_statusが必須(self) -> None:
        """extraction_status がない場合は ValidationError."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=datetime.now(tz=timezone.utc),
        )

        with pytest.raises(ValidationError) as exc_info:
            ExtractedArticle(
                collected=collected,
                body_text="Some content",
                extraction_method="trafilatura",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("extraction_status",) for e in errors)

    def test_異常系_extraction_methodが必須(self) -> None:
        """extraction_method がない場合は ValidationError."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=datetime.now(tz=timezone.utc),
        )

        with pytest.raises(ValidationError) as exc_info:
            ExtractedArticle(
                collected=collected,
                body_text="Some content",
                extraction_status=ExtractionStatus.SUCCESS,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("extraction_method",) for e in errors)

    def test_正常系_モデルをdictに変換できる(self) -> None:
        """ExtractedArticle は model_dump() で dict に変換可能."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected_at = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=collected_at,
        )

        extracted = ExtractedArticle(
            collected=collected,
            body_text="Article body content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )

        data = extracted.model_dump()

        assert data["body_text"] == "Article body content"
        assert data["extraction_status"] == ExtractionStatus.SUCCESS
        assert data["extraction_method"] == "trafilatura"
        assert data["error_message"] is None
        assert data["collected"]["title"] == "Sample Article"

    def test_正常系_dictからモデルを作成できる(self) -> None:
        """dict から ExtractedArticle を作成可能."""
        from news.models import ExtractedArticle, ExtractionStatus, SourceType

        data = {
            "collected": {
                "url": "https://www.cnbc.com/article/123",
                "title": "Sample Article",
                "source": {
                    "source_type": "rss",
                    "source_name": "CNBC Markets",
                    "category": "market",
                },
                "collected_at": "2025-01-15T12:00:00Z",
            },
            "body_text": "Article body content",
            "extraction_status": "success",
            "extraction_method": "trafilatura",
        }

        extracted = ExtractedArticle.model_validate(data)

        assert extracted.body_text == "Article body content"
        assert extracted.extraction_status == ExtractionStatus.SUCCESS
        assert extracted.extraction_method == "trafilatura"
        assert extracted.collected.title == "Sample Article"
        assert extracted.collected.source.source_type == SourceType.RSS

    def test_正常系_JSONシリアライズ可能(self) -> None:
        """ExtractedArticle は JSON シリアライズ可能."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        )
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Sample Article",
            source=source,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        extracted = ExtractedArticle(
            collected=collected,
            body_text="Article body content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )

        json_str = extracted.model_dump_json()

        assert '"body_text":"Article body content"' in json_str
        assert '"extraction_status":"success"' in json_str
        assert '"extraction_method":"trafilatura"' in json_str
        assert "https://www.cnbc.com/article/123" in json_str

    def test_正常系_CollectedArticleと関連が正しい(self) -> None:
        """ExtractedArticle から CollectedArticle の全プロパティにアクセスできる."""
        from news.models import (
            ArticleSource,
            CollectedArticle,
            ExtractedArticle,
            ExtractionStatus,
            SourceType,
        )

        source = ArticleSource(
            source_type=SourceType.YFINANCE,
            source_name="NVDA",
            category="yf_ai_stock",
        )
        published = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        collected_at = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        collected = CollectedArticle(
            url="https://finance.yahoo.com/news/nvda",  # type: ignore[arg-type]
            title="NVDA Earnings Report",
            published=published,
            raw_summary="NVDA reports quarterly earnings",
            source=source,
            collected_at=collected_at,
        )

        extracted = ExtractedArticle(
            collected=collected,
            body_text="Full article body about NVDA earnings...",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )

        # CollectedArticle の全プロパティにアクセス可能
        assert str(extracted.collected.url) == "https://finance.yahoo.com/news/nvda"
        assert extracted.collected.title == "NVDA Earnings Report"
        assert extracted.collected.published == published
        assert extracted.collected.raw_summary == "NVDA reports quarterly earnings"
        assert extracted.collected.source.source_type == SourceType.YFINANCE
        assert extracted.collected.source.source_name == "NVDA"
        assert extracted.collected.collected_at == collected_at
