"""Unit tests for article_extractor module.

Tests cover:
- ExtractionStatus enum values
- ExtractedArticle dataclass
- ArticleExtractor.extract() method (trafilatura + fallback)
- ArticleExtractor.extract_batch() method (parallel processing)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rss.services.article_extractor import (
    ArticleExtractor,
    ExtractedArticle,
    ExtractionStatus,
)

# ---------------------------------------------------------------------------
# ExtractionStatus enum tests
# ---------------------------------------------------------------------------


class TestExtractionStatus:
    """Test ExtractionStatus enum."""

    def test_正常系_SUCCESS値が正しい(self) -> None:
        assert ExtractionStatus.SUCCESS.value == "success"

    def test_正常系_FAILED値が正しい(self) -> None:
        assert ExtractionStatus.FAILED.value == "failed"

    def test_正常系_PAYWALL値が正しい(self) -> None:
        assert ExtractionStatus.PAYWALL.value == "paywall"

    def test_正常系_TIMEOUT値が正しい(self) -> None:
        assert ExtractionStatus.TIMEOUT.value == "timeout"

    def test_正常系_全ステータスが4つ存在する(self) -> None:
        assert len(ExtractionStatus) == 4


# ---------------------------------------------------------------------------
# ExtractedArticle dataclass tests
# ---------------------------------------------------------------------------


class TestExtractedArticle:
    """Test ExtractedArticle frozen dataclass."""

    def test_正常系_データクラスが正しく作成される(self) -> None:
        article = ExtractedArticle(
            url="https://example.com/article",
            title="Test Article",
            text="This is the article content.",
            author="John Doe",
            date="2026-01-15",
            source="Example News",
            language="en",
            status=ExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )
        assert article.url == "https://example.com/article"
        assert article.title == "Test Article"
        assert article.text == "This is the article content."
        assert article.author == "John Doe"
        assert article.date == "2026-01-15"
        assert article.source == "Example News"
        assert article.language == "en"
        assert article.status == ExtractionStatus.SUCCESS
        assert article.error is None
        assert article.extraction_method == "trafilatura"

    def test_正常系_frozenでイミュータブル(self) -> None:
        article = ExtractedArticle(
            url="https://example.com",
            title="Title",
            text="Text",
            author=None,
            date=None,
            source=None,
            language=None,
            status=ExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )
        with pytest.raises(AttributeError):
            article.title = "New Title"  # type: ignore[misc]

    def test_正常系_失敗時のエラーメッセージ(self) -> None:
        article = ExtractedArticle(
            url="https://example.com/timeout",
            title=None,
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=ExtractionStatus.TIMEOUT,
            error="Connection timed out after 30s",
            extraction_method="trafilatura",
        )
        assert article.status == ExtractionStatus.TIMEOUT
        assert article.error == "Connection timed out after 30s"
        assert article.text is None

    def test_正常系_フォールバックメソッド(self) -> None:
        article = ExtractedArticle(
            url="https://example.com",
            title="Fallback Title",
            text="Fallback content",
            author=None,
            date=None,
            source=None,
            language=None,
            status=ExtractionStatus.SUCCESS,
            error=None,
            extraction_method="fallback",
        )
        assert article.extraction_method == "fallback"

    def test_エッジケース_全てNoneのオプションフィールド(self) -> None:
        article = ExtractedArticle(
            url="https://example.com",
            title=None,
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=ExtractionStatus.FAILED,
            error="Extraction failed",
            extraction_method="trafilatura",
        )
        assert article.title is None
        assert article.text is None
        assert article.author is None
        assert article.date is None
        assert article.source is None
        assert article.language is None


# ---------------------------------------------------------------------------
# ArticleExtractor.extract() tests (mocked)
# ---------------------------------------------------------------------------


class TestArticleExtractorExtract:
    """Test ArticleExtractor.extract() method."""

    @pytest.mark.asyncio
    async def test_正常系_trafilaturaで記事抽出成功(self) -> None:
        mock_html = "<html><body><article><p>Test content</p></article></body></html>"
        mock_result = {
            "title": "Test Article",
            "text": "Test content for the article.",
            "author": "Author Name",
            "date": "2026-01-15",
            "hostname": "example.com",
            "language": "en",
        }

        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                return_value=mock_html,
            ),
            patch(
                "rss.services.article_extractor.trafilatura.bare_extraction",
                return_value=mock_result,
            ),
        ):
            extractor = ArticleExtractor()
            result = await extractor.extract("https://example.com/article")

        assert result.status == ExtractionStatus.SUCCESS
        assert result.title == "Test Article"
        assert result.text == "Test content for the article."
        assert result.author == "Author Name"
        assert result.extraction_method == "trafilatura"

    @pytest.mark.asyncio
    async def test_正常系_trafilatura失敗時にフォールバック(self) -> None:
        # MIN_CONTENT_LENGTH (100文字) 以上のコンテンツを用意
        long_content = "Fallback article content. " * 10  # 十分な長さ
        mock_html = f"""
        <html><body>
            <article>
                <h1>Fallback Title</h1>
                <p>{long_content}</p>
            </article>
        </body></html>
        """

        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                return_value=None,
            ),
            patch(
                "rss.services.article_extractor.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            extractor = ArticleExtractor()
            result = await extractor.extract("https://example.com/article")

        assert result.status == ExtractionStatus.SUCCESS
        assert result.extraction_method == "fallback"
        assert result.text is not None
        assert "Fallback" in result.text

    @pytest.mark.asyncio
    async def test_異常系_タイムアウトでTIMEOUTステータス(self) -> None:
        import httpx

        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                return_value=None,
            ),
            patch(
                "rss.services.article_extractor.httpx.AsyncClient",
                side_effect=httpx.TimeoutException("Connection timed out"),
            ),
        ):
            extractor = ArticleExtractor()
            result = await extractor.extract("https://example.com/slow")

        assert result.status == ExtractionStatus.TIMEOUT
        assert result.error is not None
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_異常系_HTTP404でFAILEDステータス(self) -> None:
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404

        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                return_value=None,
            ),
            patch(
                "rss.services.article_extractor.httpx.AsyncClient",
                side_effect=httpx.HTTPStatusError(
                    "404 Not Found",
                    request=MagicMock(),
                    response=mock_response,
                ),
            ),
        ):
            extractor = ArticleExtractor()
            result = await extractor.extract("https://example.com/not-found")

        assert result.status == ExtractionStatus.FAILED
        assert result.error is not None
        assert "404" in result.error

    @pytest.mark.asyncio
    async def test_エッジケース_空コンテンツでFAILEDステータス(self) -> None:
        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                return_value="",
            ),
            patch(
                "rss.services.article_extractor.trafilatura.bare_extraction",
                return_value=None,
            ),
        ):
            extractor = ArticleExtractor()
            result = await extractor.extract("https://example.com/empty")

        assert result.status == ExtractionStatus.FAILED
        assert result.text is None

    @pytest.mark.asyncio
    async def test_正常系_カスタムタイムアウト(self) -> None:
        mock_html = "<html><body><p>Content</p></body></html>"
        mock_result = {"title": "Test", "text": "Content"}

        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                return_value=mock_html,
            ) as mock_fetch,
            patch(
                "rss.services.article_extractor.trafilatura.bare_extraction",
                return_value=mock_result,
            ),
        ):
            extractor = ArticleExtractor(timeout=60)
            await extractor.extract("https://example.com")

        # タイムアウト値が設定されていることを確認
        assert extractor.timeout == 60


# ---------------------------------------------------------------------------
# ArticleExtractor.extract_batch() tests (mocked)
# ---------------------------------------------------------------------------


class TestArticleExtractorExtractBatch:
    """Test ArticleExtractor.extract_batch() method."""

    @pytest.mark.asyncio
    async def test_正常系_複数URLを並列処理(self) -> None:
        mock_result = {
            "title": "Test",
            "text": "Content",
            "author": None,
            "date": None,
            "hostname": None,
            "language": None,
        }

        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                return_value="<html></html>",
            ),
            patch(
                "rss.services.article_extractor.trafilatura.bare_extraction",
                return_value=mock_result,
            ),
        ):
            extractor = ArticleExtractor()
            urls = [
                "https://example.com/article1",
                "https://example.com/article2",
                "https://example.com/article3",
            ]
            results = await extractor.extract_batch(urls, rate_limit=0.1)

        assert len(results) == 3
        for result in results:
            assert result.status == ExtractionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_正常系_一部失敗しても他は成功(self) -> None:
        def mock_fetch(url: str) -> str | None:
            if "fail" in url:
                return None
            return "<html><body><p>Content</p></body></html>"

        mock_result = {"title": "Test", "text": "Sufficient content for extraction."}

        # フォールバック用のモックも設定（失敗URLの場合）
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>Short</p></body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                side_effect=mock_fetch,
            ),
            patch(
                "rss.services.article_extractor.trafilatura.bare_extraction",
                side_effect=lambda html, **kwargs: mock_result if html else None,
            ),
            patch(
                "rss.services.article_extractor.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            extractor = ArticleExtractor()
            urls = [
                "https://example.com/success1",
                "https://example.com/fail",
                "https://example.com/success2",
            ]
            results = await extractor.extract_batch(urls, rate_limit=0.01)

        assert len(results) == 3
        success_count = sum(1 for r in results if r.status == ExtractionStatus.SUCCESS)
        # 成功は少なくとも2件（trafilaturaで成功したもの）
        assert success_count >= 2

    @pytest.mark.asyncio
    async def test_エッジケース_空のURLリスト(self) -> None:
        extractor = ArticleExtractor()
        results = await extractor.extract_batch([])

        assert results == []

    @pytest.mark.asyncio
    async def test_エッジケース_単一URL(self) -> None:
        mock_result = {"title": "Single", "text": "Single content"}

        with (
            patch(
                "rss.services.article_extractor.trafilatura.fetch_url",
                return_value="<html></html>",
            ),
            patch(
                "rss.services.article_extractor.trafilatura.bare_extraction",
                return_value=mock_result,
            ),
        ):
            extractor = ArticleExtractor()
            results = await extractor.extract_batch(
                ["https://example.com/single"], rate_limit=0.01
            )

        assert len(results) == 1
        assert results[0].title == "Single"


# ---------------------------------------------------------------------------
# ArticleExtractor initialization tests
# ---------------------------------------------------------------------------


class TestArticleExtractorInit:
    """Test ArticleExtractor initialization."""

    def test_正常系_デフォルト値で初期化(self) -> None:
        extractor = ArticleExtractor()
        assert extractor.timeout == 30
        assert extractor.user_agent is not None

    def test_正常系_カスタム値で初期化(self) -> None:
        extractor = ArticleExtractor(
            timeout=60,
            user_agent="CustomBot/1.0",
        )
        assert extractor.timeout == 60
        assert extractor.user_agent == "CustomBot/1.0"
