"""Unit tests for Article model and related types."""

from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from news.core.article import (
    Article,
    ArticleSource,
    ContentType,
    Provider,
    Thumbnail,
)


class TestContentTypeEnum:
    """Test ContentType enum."""

    def test_正常系_ARTICLE値が存在する(self) -> None:
        """ContentType.ARTICLEが正しい値を持つことを確認。"""
        assert ContentType.ARTICLE == "article"
        assert ContentType.ARTICLE.value == "article"

    def test_正常系_VIDEO値が存在する(self) -> None:
        """ContentType.VIDEOが正しい値を持つことを確認。"""
        assert ContentType.VIDEO == "video"
        assert ContentType.VIDEO.value == "video"

    def test_正常系_PRESS_RELEASE値が存在する(self) -> None:
        """ContentType.PRESS_RELEASEが正しい値を持つことを確認。"""
        assert ContentType.PRESS_RELEASE == "press_release"
        assert ContentType.PRESS_RELEASE.value == "press_release"

    def test_正常系_UNKNOWN値が存在する(self) -> None:
        """ContentType.UNKNOWNが正しい値を持つことを確認。"""
        assert ContentType.UNKNOWN == "unknown"
        assert ContentType.UNKNOWN.value == "unknown"

    def test_正常系_全ての値をリストできる(self) -> None:
        """ContentTypeの全ての値をリストできることを確認。"""
        expected_values = {"article", "video", "press_release", "unknown"}
        actual_values = {ct.value for ct in ContentType}
        assert actual_values == expected_values


class TestArticleSourceEnum:
    """Test ArticleSource enum."""

    def test_正常系_YFINANCE_TICKER値が存在する(self) -> None:
        """ArticleSource.YFINANCE_TICKERが正しい値を持つことを確認。"""
        assert ArticleSource.YFINANCE_TICKER == "yfinance_ticker"
        assert ArticleSource.YFINANCE_TICKER.value == "yfinance_ticker"

    def test_正常系_YFINANCE_SEARCH値が存在する(self) -> None:
        """ArticleSource.YFINANCE_SEARCHが正しい値を持つことを確認。"""
        assert ArticleSource.YFINANCE_SEARCH == "yfinance_search"
        assert ArticleSource.YFINANCE_SEARCH.value == "yfinance_search"

    def test_正常系_SCRAPER値が存在する(self) -> None:
        """ArticleSource.SCRAPERが正しい値を持つことを確認。"""
        assert ArticleSource.SCRAPER == "scraper"
        assert ArticleSource.SCRAPER.value == "scraper"

    def test_正常系_RSS値が存在する(self) -> None:
        """ArticleSource.RSSが正しい値を持つことを確認。"""
        assert ArticleSource.RSS == "rss"
        assert ArticleSource.RSS.value == "rss"

    def test_正常系_全ての値をリストできる(self) -> None:
        """ArticleSourceの全ての値をリストできることを確認。"""
        expected_values = {"yfinance_ticker", "yfinance_search", "scraper", "rss"}
        actual_values = {src.value for src in ArticleSource}
        assert actual_values == expected_values


class TestProviderModel:
    """Test Provider submodel."""

    def test_正常系_名前のみで作成できる(self) -> None:
        """名前のみでProviderを作成できることを確認。"""
        provider = Provider(name="Yahoo Finance")

        assert provider.name == "Yahoo Finance"
        assert provider.url is None

    def test_正常系_名前とURLで作成できる(self) -> None:
        """名前とURLでProviderを作成できることを確認。"""
        provider = Provider(
            name="Yahoo Finance",
            url="https://finance.yahoo.com/",  # type: ignore[arg-type]
        )

        assert provider.name == "Yahoo Finance"
        assert str(provider.url) == "https://finance.yahoo.com/"

    def test_異常系_名前なしでValidationError(self) -> None:
        """名前なしでProviderを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="name"):
            Provider()

    def test_異常系_不正なURLでValidationError(self) -> None:
        """不正なURLでProviderを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="url"):
            Provider(name="Test", url="not-a-valid-url")  # type: ignore[arg-type]

    def test_正常系_JSONシリアライズできる(self) -> None:
        """ProviderをJSONにシリアライズできることを確認。"""
        provider = Provider(
            name="Reuters",
            url="https://www.reuters.com/",  # type: ignore[arg-type]
        )
        json_str = provider.model_dump_json()

        assert "Reuters" in json_str
        assert "reuters.com" in json_str

    def test_正常系_JSONからデシリアライズできる(self) -> None:
        """JSONからProviderをデシリアライズできることを確認。"""
        json_data = '{"name": "Bloomberg", "url": "https://bloomberg.com/"}'
        provider = Provider.model_validate_json(json_data)

        assert provider.name == "Bloomberg"
        assert str(provider.url) == "https://bloomberg.com/"


class TestThumbnailModel:
    """Test Thumbnail submodel."""

    def test_正常系_URLのみで作成できる(self) -> None:
        """URLのみでThumbnailを作成できることを確認。"""
        thumbnail = Thumbnail(url="https://example.com/image.jpg")

        assert str(thumbnail.url) == "https://example.com/image.jpg"
        assert thumbnail.width is None
        assert thumbnail.height is None

    def test_正常系_全フィールドで作成できる(self) -> None:
        """全フィールドでThumbnailを作成できることを確認。"""
        thumbnail = Thumbnail(
            url="https://example.com/image.jpg",  # type: ignore[arg-type]
            width=1200,
            height=800,
        )

        assert str(thumbnail.url) == "https://example.com/image.jpg"
        assert thumbnail.width == 1200
        assert thumbnail.height == 800

    def test_異常系_URLなしでValidationError(self) -> None:
        """URLなしでThumbnailを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="url"):
            Thumbnail()

    def test_異常系_不正なURLでValidationError(self) -> None:
        """不正なURLでThumbnailを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="url"):
            Thumbnail(url="not-a-valid-url")

    def test_正常系_JSONシリアライズできる(self) -> None:
        """ThumbnailをJSONにシリアライズできることを確認。"""
        thumbnail = Thumbnail(
            url="https://s.yimg.com/image.jpg",  # type: ignore[arg-type]
            width=5971,
            height=3980,
        )
        json_str = thumbnail.model_dump_json()

        assert "s.yimg.com" in json_str
        assert "5971" in json_str
        assert "3980" in json_str

    def test_正常系_JSONからデシリアライズできる(self) -> None:
        """JSONからThumbnailをデシリアライズできることを確認。"""
        json_data = (
            '{"url": "https://example.com/thumb.png", "width": 640, "height": 480}'
        )
        thumbnail = Thumbnail.model_validate_json(json_data)

        assert str(thumbnail.url) == "https://example.com/thumb.png"
        assert thumbnail.width == 640
        assert thumbnail.height == 480


class TestArticleModel:
    """Test Article model."""

    @pytest.fixture
    def valid_article_data(self) -> dict[str, Any]:
        """有効なArticleデータを提供するフィクスチャ。"""
        return {
            "url": "https://finance.yahoo.com/news/test-article",
            "title": "Test Article Title",
            "published_at": datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            "source": ArticleSource.YFINANCE_TICKER,
        }

    @pytest.fixture
    def full_article_data(self) -> dict[str, Any]:
        """全フィールドを持つArticleデータを提供するフィクスチャ。"""
        return {
            "url": "https://finance.yahoo.com/news/full-article",
            "title": "Full Article Title",
            "published_at": datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            "source": ArticleSource.YFINANCE_TICKER,
            "summary": "This is the article summary.",
            "content_type": ContentType.ARTICLE,
            "provider": Provider(
                name="Yahoo Finance",
                url="https://finance.yahoo.com/",  # type: ignore[arg-type]
            ),
            "thumbnail": Thumbnail(
                url="https://s.yimg.com/thumb.jpg",  # type: ignore[arg-type]
                width=1200,
                height=800,
            ),
            "related_tickers": ["AAPL", "GOOGL"],
            "tags": ["technology", "earnings"],
            "metadata": {"editors_pick": True, "is_premium": False},
            "summary_ja": "これは記事の要約です。",
            "category": "technology",
            "sentiment": 0.75,
        }

    def test_正常系_必須フィールドのみで作成できる(
        self,
        valid_article_data: dict[str, Any],
    ) -> None:
        """必須フィールドのみでArticleを作成できることを確認。"""
        article = Article(**valid_article_data)

        assert str(article.url) == "https://finance.yahoo.com/news/test-article"
        assert article.title == "Test Article Title"
        assert article.published_at == datetime(
            2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc
        )
        assert article.source == ArticleSource.YFINANCE_TICKER

    def test_正常系_オプションフィールドのデフォルト値(
        self,
        valid_article_data: dict[str, Any],
    ) -> None:
        """オプションフィールドが正しいデフォルト値を持つことを確認。"""
        article = Article(**valid_article_data)

        assert article.summary is None
        assert article.content_type == ContentType.ARTICLE
        assert article.provider is None
        assert article.thumbnail is None
        assert article.related_tickers == []
        assert article.tags == []
        assert article.metadata == {}
        assert article.summary_ja is None
        assert article.category is None
        assert article.sentiment is None

    def test_正常系_fetched_atが自動設定される(
        self,
        valid_article_data: dict[str, Any],
    ) -> None:
        """fetched_atが自動的に現在時刻に設定されることを確認。"""
        before = datetime.now(timezone.utc)
        article = Article(**valid_article_data)
        after = datetime.now(timezone.utc)

        assert article.fetched_at is not None
        # fetched_at が before と after の間にあることを確認
        # タイムゾーン情報を統一して比較
        fetched_at_utc = (
            article.fetched_at.replace(tzinfo=timezone.utc)
            if article.fetched_at.tzinfo is None
            else article.fetched_at
        )
        assert before <= fetched_at_utc <= after

    def test_正常系_全フィールドで作成できる(
        self,
        full_article_data: dict[str, Any],
    ) -> None:
        """全フィールドでArticleを作成できることを確認。"""
        article = Article(**full_article_data)

        assert article.summary == "This is the article summary."
        assert article.content_type == ContentType.ARTICLE
        assert article.provider is not None
        assert article.provider.name == "Yahoo Finance"
        assert article.thumbnail is not None
        assert article.thumbnail.width == 1200
        assert article.related_tickers == ["AAPL", "GOOGL"]
        assert article.tags == ["technology", "earnings"]
        assert article.metadata == {"editors_pick": True, "is_premium": False}
        assert article.summary_ja == "これは記事の要約です。"
        assert article.category == "technology"
        assert article.sentiment == 0.75

    def test_異常系_URLなしでValidationError(self) -> None:
        """URLなしでArticleを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="url"):
            Article(
                title="Test",
                published_at=datetime.now(timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
            )

    def test_異常系_タイトルなしでValidationError(self) -> None:
        """タイトルなしでArticleを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="title"):
            Article(
                url="https://example.com/article",
                published_at=datetime.now(timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
            )

    def test_異常系_空のタイトルでValidationError(self) -> None:
        """空のタイトルでArticleを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="title"):
            Article(
                url="https://example.com/article",
                title="",
                published_at=datetime.now(timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
            )

    def test_異常系_published_atなしでValidationError(self) -> None:
        """published_atなしでArticleを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="published_at"):
            Article(
                url="https://example.com/article",
                title="Test",
                source=ArticleSource.YFINANCE_TICKER,
            )

    def test_異常系_sourceなしでValidationError(self) -> None:
        """sourceなしでArticleを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="source"):
            Article(
                url="https://example.com/article",
                title="Test",
                published_at=datetime.now(timezone.utc),
            )

    def test_異常系_不正なURLでValidationError(self) -> None:
        """不正なURLでArticleを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="url"):
            Article(
                url="not-a-valid-url",
                title="Test",
                published_at=datetime.now(timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
            )

    def test_異常系_不正なsourceでValidationError(self) -> None:
        """不正なsourceでArticleを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="source"):
            Article(
                url="https://example.com/article",
                title="Test",
                published_at=datetime.now(timezone.utc),
                source="invalid_source",
            )

    def test_異常系_sentimentが範囲外でValidationError(self) -> None:
        """sentimentが範囲外でArticleを作成するとValidationErrorが発生することを確認。"""
        with pytest.raises(ValidationError, match="sentiment"):
            Article(
                url="https://example.com/article",
                title="Test",
                published_at=datetime.now(timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
                sentiment=1.5,  # 範囲外: -1.0 ~ 1.0
            )

        with pytest.raises(ValidationError, match="sentiment"):
            Article(
                url="https://example.com/article",
                title="Test",
                published_at=datetime.now(timezone.utc),
                source=ArticleSource.YFINANCE_TICKER,
                sentiment=-1.5,  # 範囲外: -1.0 ~ 1.0
            )

    def test_正常系_sentimentの境界値(
        self,
        valid_article_data: dict[str, Any],
    ) -> None:
        """sentimentの境界値が有効であることを確認。"""
        # 最小値
        valid_article_data["sentiment"] = -1.0
        article_min = Article(**valid_article_data)
        assert article_min.sentiment == -1.0

        # 最大値
        valid_article_data["sentiment"] = 1.0
        article_max = Article(**valid_article_data)
        assert article_max.sentiment == 1.0

        # 中間値
        valid_article_data["sentiment"] = 0.0
        article_mid = Article(**valid_article_data)
        assert article_mid.sentiment == 0.0


class TestArticleJSONSerialization:
    """Test Article JSON serialization and deserialization."""

    @pytest.fixture
    def article_for_serialization(self) -> Article:
        """シリアライズテスト用のArticleを提供するフィクスチャ。"""
        return Article(
            url="https://finance.yahoo.com/news/test-article",
            title="Test Article Title",
            published_at=datetime(2026, 1, 27, 23, 33, 53, tzinfo=timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
            summary="Test summary",
            content_type=ContentType.ARTICLE,
            provider=Provider(
                name="Yahoo Finance",
                url="https://finance.yahoo.com/",  # type: ignore[arg-type]
            ),
            thumbnail=Thumbnail(
                url="https://s.yimg.com/thumb.jpg",  # type: ignore[arg-type]
                width=1200,
                height=800,
            ),
            related_tickers=["AAPL"],
            tags=["technology"],
            metadata={"editors_pick": True},
            fetched_at=datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
        )

    def test_正常系_JSONにシリアライズできる(
        self,
        article_for_serialization: Article,
    ) -> None:
        """ArticleをJSONにシリアライズできることを確認。"""
        json_str = article_for_serialization.model_dump_json()

        assert "finance.yahoo.com/news/test-article" in json_str
        assert "Test Article Title" in json_str
        assert "yfinance_ticker" in json_str
        assert "Test summary" in json_str
        assert "Yahoo Finance" in json_str
        assert "AAPL" in json_str
        assert "technology" in json_str

    def test_正常系_model_dumpでdictに変換できる(
        self,
        article_for_serialization: Article,
    ) -> None:
        """Articleをdictに変換できることを確認。"""
        data = article_for_serialization.model_dump()

        assert data["title"] == "Test Article Title"
        assert data["source"] == "yfinance_ticker"
        assert data["summary"] == "Test summary"
        assert data["provider"]["name"] == "Yahoo Finance"
        assert data["thumbnail"]["width"] == 1200
        assert data["related_tickers"] == ["AAPL"]
        assert data["tags"] == ["technology"]
        assert data["metadata"]["editors_pick"] is True

    def test_正常系_model_dump_jsonでdatetimeがISO形式に変換される(
        self,
        article_for_serialization: Article,
    ) -> None:
        """datetimeがISO8601形式にシリアライズされることを確認。"""
        json_str = article_for_serialization.model_dump_json()

        # ISO8601形式の日時文字列が含まれることを確認
        assert "2026-01-27T23:33:53" in json_str

    def test_正常系_JSONからデシリアライズできる(self) -> None:
        """JSONからArticleをデシリアライズできることを確認。"""
        json_data = """
        {
            "url": "https://example.com/article",
            "title": "Deserialized Article",
            "published_at": "2026-01-27T23:33:53Z",
            "source": "yfinance_search",
            "summary": "Deserialized summary",
            "content_type": "article",
            "related_tickers": ["GOOGL", "MSFT"],
            "tags": ["ai", "cloud"],
            "metadata": {"is_premium": false},
            "fetched_at": "2026-01-28T12:00:00Z"
        }
        """
        article = Article.model_validate_json(json_data)

        assert str(article.url) == "https://example.com/article"
        assert article.title == "Deserialized Article"
        assert article.source == ArticleSource.YFINANCE_SEARCH
        assert article.summary == "Deserialized summary"
        assert article.content_type == ContentType.ARTICLE
        assert article.related_tickers == ["GOOGL", "MSFT"]
        assert article.tags == ["ai", "cloud"]
        assert article.metadata == {"is_premium": False}

    def test_正常系_ネストされたオブジェクトをJSONからデシリアライズできる(
        self,
    ) -> None:
        """ネストされたオブジェクトを含むJSONからArticleをデシリアライズできることを確認。"""
        json_data = """
        {
            "url": "https://example.com/nested-article",
            "title": "Nested Article",
            "published_at": "2026-01-27T23:33:53Z",
            "source": "yfinance_ticker",
            "provider": {
                "name": "Reuters",
                "url": "https://www.reuters.com/"
            },
            "thumbnail": {
                "url": "https://example.com/image.jpg",
                "width": 640,
                "height": 480
            }
        }
        """
        article = Article.model_validate_json(json_data)

        assert article.provider is not None
        assert article.provider.name == "Reuters"
        assert str(article.provider.url) == "https://www.reuters.com/"
        assert article.thumbnail is not None
        assert article.thumbnail.width == 640
        assert article.thumbnail.height == 480

    def test_正常系_シリアライズとデシリアライズの往復(
        self,
        article_for_serialization: Article,
    ) -> None:
        """シリアライズとデシリアライズを往復しても同じ値になることを確認。"""
        # シリアライズ
        json_str = article_for_serialization.model_dump_json()

        # デシリアライズ
        restored = Article.model_validate_json(json_str)

        # 比較（URLはHttpUrl型なのでstr変換して比較）
        assert str(restored.url) == str(article_for_serialization.url)
        assert restored.title == article_for_serialization.title
        assert restored.source == article_for_serialization.source
        assert restored.summary == article_for_serialization.summary
        assert restored.content_type == article_for_serialization.content_type
        assert restored.related_tickers == article_for_serialization.related_tickers
        assert restored.tags == article_for_serialization.tags
        assert restored.metadata == article_for_serialization.metadata

    def test_正常系_dictからmodel_validateで作成できる(self) -> None:
        """dictからmodel_validateでArticleを作成できることを確認。"""
        data = {
            "url": "https://example.com/dict-article",
            "title": "Dict Article",
            "published_at": "2026-01-27T23:33:53Z",
            "source": "scraper",
        }
        article = Article.model_validate(data)

        assert str(article.url) == "https://example.com/dict-article"
        assert article.title == "Dict Article"
        assert article.source == ArticleSource.SCRAPER


class TestArticleSourceCompatibility:
    """Test Article creation with different source types."""

    @pytest.mark.parametrize(
        "source",
        [
            ArticleSource.YFINANCE_TICKER,
            ArticleSource.YFINANCE_SEARCH,
            ArticleSource.SCRAPER,
            ArticleSource.RSS,
        ],
    )
    def test_パラメトライズ_全てのソースタイプで作成できる(
        self,
        source: ArticleSource,
    ) -> None:
        """全てのArticleSourceでArticleを作成できることを確認。"""
        article = Article(
            url="https://example.com/article",
            title=f"Article from {source.value}",
            published_at=datetime.now(timezone.utc),
            source=source,
        )

        assert article.source == source

    @pytest.mark.parametrize(
        "content_type",
        [
            ContentType.ARTICLE,
            ContentType.VIDEO,
            ContentType.PRESS_RELEASE,
            ContentType.UNKNOWN,
        ],
    )
    def test_パラメトライズ_全てのコンテンツタイプで作成できる(
        self,
        content_type: ContentType,
    ) -> None:
        """全てのContentTypeでArticleを作成できることを確認。"""
        article = Article(
            url="https://example.com/article",
            title=f"Article with {content_type.value}",
            published_at=datetime.now(timezone.utc),
            source=ArticleSource.YFINANCE_TICKER,
            content_type=content_type,
        )

        assert article.content_type == content_type
