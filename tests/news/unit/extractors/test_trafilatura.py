"""Unit tests for TrafilaturaExtractor.

This module tests the TrafilaturaExtractor class which wraps the
rss.services.article_extractor.ArticleExtractor to extract article
body text from URLs.

Tests cover:
- Basic instantiation and configuration
- Successful extraction scenarios
- Error handling and status mapping
- min_body_length validation
- Retry functionality with exponential backoff (Issue #2383)
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from news.extractors.base import BaseExtractor
from news.extractors.trafilatura import TrafilaturaExtractor
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
)
from rss.services.article_extractor import (
    ExtractedArticle as RssExtractedArticle,
)
from rss.services.article_extractor import (
    ExtractionStatus as RssExtractionStatus,
)


@pytest.fixture
def sample_collected_article() -> CollectedArticle:
    """Create a sample CollectedArticle for testing."""
    return CollectedArticle(
        url="https://www.cnbc.com/article/test",  # type: ignore[arg-type]
        title="Test Article",
        published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        raw_summary="This is a test summary",
        source=ArticleSource(
            source_type=SourceType.RSS,
            source_name="CNBC Markets",
            category="market",
        ),
        collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def mock_rss_extracted_article_success() -> RssExtractedArticle:
    """Create a mock successful RssExtractedArticle."""
    return RssExtractedArticle(
        url="https://www.cnbc.com/article/test",
        title="Test Article",
        text="This is the extracted article body text. " * 20,  # > 200 chars
        author="Test Author",
        date="2025-01-15",
        source="cnbc.com",
        language="en",
        status=RssExtractionStatus.SUCCESS,
        error=None,
        extraction_method="trafilatura",
    )


@pytest.fixture
def mock_rss_extracted_article_short() -> RssExtractedArticle:
    """Create a mock RssExtractedArticle with short text."""
    return RssExtractedArticle(
        url="https://www.cnbc.com/article/test",
        title="Test Article",
        text="Short",  # < 200 chars
        author=None,
        date=None,
        source="cnbc.com",
        language="en",
        status=RssExtractionStatus.SUCCESS,
        error=None,
        extraction_method="trafilatura",
    )


@pytest.fixture
def mock_rss_extracted_article_timeout() -> RssExtractedArticle:
    """Create a mock RssExtractedArticle with timeout status."""
    return RssExtractedArticle(
        url="https://www.cnbc.com/article/test",
        title=None,
        text=None,
        author=None,
        date=None,
        source=None,
        language=None,
        status=RssExtractionStatus.TIMEOUT,
        error="Request timed out",
        extraction_method="trafilatura",
    )


@pytest.fixture
def mock_rss_extracted_article_failed() -> RssExtractedArticle:
    """Create a mock RssExtractedArticle with failed status."""
    return RssExtractedArticle(
        url="https://www.cnbc.com/article/test",
        title=None,
        text=None,
        author=None,
        date=None,
        source=None,
        language=None,
        status=RssExtractionStatus.FAILED,
        error="Failed to fetch",
        extraction_method="fallback",
    )


class TestTrafilaturaExtractorInstantiation:
    """Tests for TrafilaturaExtractor instantiation."""

    def test_正常系_BaseExtractorを継承している(self) -> None:
        """TrafilaturaExtractor should inherit from BaseExtractor."""
        assert issubclass(TrafilaturaExtractor, BaseExtractor)

    def test_正常系_デフォルト設定でインスタンス化できる(self) -> None:
        """TrafilaturaExtractor can be instantiated with default settings."""
        extractor = TrafilaturaExtractor()
        assert extractor is not None
        assert extractor._min_body_length == 200

    def test_正常系_カスタムmin_body_lengthでインスタンス化できる(self) -> None:
        """TrafilaturaExtractor can be instantiated with custom min_body_length."""
        extractor = TrafilaturaExtractor(min_body_length=100)
        assert extractor._min_body_length == 100

    def test_正常系_extractor_nameはtrafilaturaを返す(self) -> None:
        """extractor_name should return 'trafilatura'."""
        extractor = TrafilaturaExtractor()
        assert extractor.extractor_name == "trafilatura"


class TestTrafilaturaExtractorExtract:
    """Tests for TrafilaturaExtractor.extract() method."""

    @pytest.mark.asyncio
    async def test_正常系_成功時にExtractedArticleを返す(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """extract should return ExtractedArticle on success."""
        extractor = TrafilaturaExtractor()

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_rss_extracted_article_success,
        ):
            result = await extractor.extract(sample_collected_article)

        assert isinstance(result, ExtractedArticle)
        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.body_text is not None
        assert len(result.body_text) >= 200
        assert result.extraction_method == "trafilatura"
        assert result.collected == sample_collected_article
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_正常系_CollectedArticleがそのまま保持される(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """extract should preserve the original CollectedArticle."""
        extractor = TrafilaturaExtractor()

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_rss_extracted_article_success,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.collected == sample_collected_article
        assert result.collected.title == "Test Article"
        assert str(result.collected.url) == "https://www.cnbc.com/article/test"

    @pytest.mark.asyncio
    async def test_異常系_本文が短い場合FAILEDステータスを返す(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_short: RssExtractedArticle,
    ) -> None:
        """extract should return FAILED status when body is too short."""
        extractor = TrafilaturaExtractor(min_body_length=200)

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_rss_extracted_article_short,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.body_text is None
        assert result.error_message == "Body text too short or empty"

    @pytest.mark.asyncio
    async def test_異常系_本文がNoneの場合FAILEDステータスを返す(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """extract should return FAILED status when body is None."""
        extractor = TrafilaturaExtractor()

        mock_result = RssExtractedArticle(
            url="https://www.cnbc.com/article/test",
            title="Test Article",
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.body_text is None
        assert result.error_message == "Body text too short or empty"

    @pytest.mark.asyncio
    async def test_異常系_タイムアウト時にTIMEOUTステータスを返す(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_timeout: RssExtractedArticle,
    ) -> None:
        """extract should return TIMEOUT status on timeout."""
        extractor = TrafilaturaExtractor()

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_rss_extracted_article_timeout,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.TIMEOUT
        assert result.body_text is None
        assert result.error_message == "Request timed out"

    @pytest.mark.asyncio
    async def test_異常系_失敗時にFAILEDステータスを返す(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_failed: RssExtractedArticle,
    ) -> None:
        """extract should return FAILED status on failure."""
        extractor = TrafilaturaExtractor()

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_rss_extracted_article_failed,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.body_text is None
        assert result.error_message == "Failed to fetch"

    @pytest.mark.asyncio
    async def test_異常系_例外発生時にFAILEDステータスを返す(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """extract should return FAILED status when exception occurs."""
        extractor = TrafilaturaExtractor()

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            side_effect=Exception("Unexpected error"),
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.body_text is None
        assert "Unexpected error" in str(result.error_message)


class TestTrafilaturaExtractorMinBodyLength:
    """Tests for min_body_length validation."""

    @pytest.mark.asyncio
    async def test_正常系_min_body_lengthより長いテキストは成功(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """Text longer than min_body_length should succeed."""
        extractor = TrafilaturaExtractor(min_body_length=50)

        mock_result = RssExtractedArticle(
            url="https://www.cnbc.com/article/test",
            title="Test Article",
            text="A" * 100,  # 100 chars > 50
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.body_text == "A" * 100

    @pytest.mark.asyncio
    async def test_正常系_min_body_lengthちょうどのテキストは成功(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """Text exactly at min_body_length should succeed."""
        extractor = TrafilaturaExtractor(min_body_length=50)

        mock_result = RssExtractedArticle(
            url="https://www.cnbc.com/article/test",
            title="Test Article",
            text="A" * 50,  # 50 chars == 50
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.body_text == "A" * 50

    @pytest.mark.asyncio
    async def test_異常系_min_body_lengthより短いテキストは失敗(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """Text shorter than min_body_length should fail."""
        extractor = TrafilaturaExtractor(min_body_length=50)

        mock_result = RssExtractedArticle(
            url="https://www.cnbc.com/article/test",
            title="Test Article",
            text="A" * 49,  # 49 chars < 50
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.body_text is None
        assert result.error_message == "Body text too short or empty"


class TestTrafilaturaExtractorStatusMapping:
    """Tests for extraction status mapping."""

    @pytest.mark.asyncio
    async def test_正常系_SUCCESS_to_SUCCESS(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """RssExtractionStatus.SUCCESS should map to ExtractionStatus.SUCCESS."""
        extractor = TrafilaturaExtractor()

        mock_result = RssExtractedArticle(
            url="https://www.cnbc.com/article/test",
            title="Test Article",
            text="A" * 300,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_正常系_FAILED_to_FAILED(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """RssExtractionStatus.FAILED should map to ExtractionStatus.FAILED."""
        extractor = TrafilaturaExtractor()

        mock_result = RssExtractedArticle(
            url="https://www.cnbc.com/article/test",
            title=None,
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.FAILED,
            error="Connection error",
            extraction_method="trafilatura",
        )

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED

    @pytest.mark.asyncio
    async def test_正常系_TIMEOUT_to_TIMEOUT(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """RssExtractionStatus.TIMEOUT should map to ExtractionStatus.TIMEOUT."""
        extractor = TrafilaturaExtractor()

        mock_result = RssExtractedArticle(
            url="https://www.cnbc.com/article/test",
            title=None,
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.TIMEOUT,
            error="Request timed out",
            extraction_method="trafilatura",
        )

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_正常系_PAYWALL_to_PAYWALL(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """RssExtractionStatus.PAYWALL should map to ExtractionStatus.PAYWALL."""
        extractor = TrafilaturaExtractor()

        mock_result = RssExtractedArticle(
            url="https://www.cnbc.com/article/test",
            title="Test Article",
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.PAYWALL,
            error="Paywall detected",
            extraction_method="trafilatura",
        )

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.PAYWALL


class TestTrafilaturaExtractorRetry:
    """Tests for TrafilaturaExtractor retry functionality.

    Issue #2383: Add retry logic to TrafilaturaExtractor.
    - Maximum 3 retries
    - Exponential backoff (1s, 2s, 4s)
    """

    @pytest.mark.asyncio
    async def test_正常系_リトライパラメータでインスタンス化できる(self) -> None:
        """TrafilaturaExtractor can be instantiated with retry parameters."""
        extractor = TrafilaturaExtractor(max_retries=3, timeout_seconds=30)
        assert extractor._max_retries == 3
        assert extractor._timeout_seconds == 30

    @pytest.mark.asyncio
    async def test_正常系_デフォルトリトライパラメータ(self) -> None:
        """Default retry parameters are set correctly."""
        extractor = TrafilaturaExtractor()
        assert extractor._max_retries == 3
        assert extractor._timeout_seconds == 30

    @pytest.mark.asyncio
    async def test_正常系_1回目で成功時はリトライしない(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """extract should not retry when first attempt succeeds."""
        extractor = TrafilaturaExtractor()
        call_count = 0

        async def mock_extract(url: str) -> RssExtractedArticle:
            nonlocal call_count
            call_count += 1
            return mock_rss_extracted_article_success

        with patch.object(
            extractor._extractor,
            "extract",
            side_effect=mock_extract,
        ):
            result = await extractor.extract(sample_collected_article)

        assert call_count == 1
        assert result.extraction_status == ExtractionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_正常系_2回目で成功時は2回呼び出される(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """extract should succeed on second attempt after first failure."""
        extractor = TrafilaturaExtractor()
        call_count = 0

        async def mock_extract(url: str) -> RssExtractedArticle:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt failed")
            return mock_rss_extracted_article_success

        with (
            patch.object(
                extractor._extractor,
                "extract",
                side_effect=mock_extract,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            result = await extractor.extract(sample_collected_article)

        assert call_count == 2
        assert result.extraction_status == ExtractionStatus.SUCCESS
        # Exponential backoff: 2^0 = 1 second
        mock_sleep.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_正常系_3回目で成功時は3回呼び出される(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """extract should succeed on third attempt after two failures."""
        extractor = TrafilaturaExtractor()
        call_count = 0

        async def mock_extract(url: str) -> RssExtractedArticle:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            return mock_rss_extracted_article_success

        with (
            patch.object(
                extractor._extractor,
                "extract",
                side_effect=mock_extract,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            result = await extractor.extract(sample_collected_article)

        assert call_count == 3
        assert result.extraction_status == ExtractionStatus.SUCCESS
        # Exponential backoff: 2^0=1s, 2^1=2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @pytest.mark.asyncio
    async def test_異常系_3回全て失敗時はFAILEDステータス(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """extract should return FAILED after all retries exhausted."""
        extractor = TrafilaturaExtractor(max_retries=3)
        call_count = 0

        async def mock_extract(url: str) -> RssExtractedArticle:
            nonlocal call_count
            call_count += 1
            raise Exception(f"Attempt {call_count} failed")

        with (
            patch.object(
                extractor._extractor,
                "extract",
                side_effect=mock_extract,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            result = await extractor.extract(sample_collected_article)

        assert call_count == 3
        assert result.extraction_status == ExtractionStatus.FAILED
        assert "Attempt 3 failed" in str(result.error_message)
        # Exponential backoff: 2^0=1s, 2^1=2s (no sleep after last attempt)
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_正常系_指数バックオフが正しく適用される(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """Exponential backoff should be applied correctly (1s, 2s, 4s)."""
        extractor = TrafilaturaExtractor(max_retries=4)
        call_count = 0

        async def mock_extract(url: str) -> RssExtractedArticle:
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise Exception(f"Attempt {call_count} failed")
            return mock_rss_extracted_article_success

        with (
            patch.object(
                extractor._extractor,
                "extract",
                side_effect=mock_extract,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            result = await extractor.extract(sample_collected_article)

        assert call_count == 4
        assert result.extraction_status == ExtractionStatus.SUCCESS
        # Exponential backoff: 2^0=1s, 2^1=2s, 2^2=4s
        assert mock_sleep.call_count == 3
        calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert calls == [1, 2, 4]

    @pytest.mark.asyncio
    async def test_異常系_タイムアウト時もリトライする(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """extract should retry on timeout and succeed on subsequent attempt."""
        extractor = TrafilaturaExtractor(timeout_seconds=5)
        call_count = 0

        async def mock_extract(url: str) -> RssExtractedArticle:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise asyncio.TimeoutError("Timeout")
            return mock_rss_extracted_article_success

        with (
            patch.object(
                extractor._extractor,
                "extract",
                side_effect=mock_extract,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await extractor.extract(sample_collected_article)

        assert call_count == 2
        assert result.extraction_status == ExtractionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_異常系_タイムアウト3回でTIMEOUTステータス(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """extract should return TIMEOUT after all timeout retries."""
        extractor = TrafilaturaExtractor(max_retries=3, timeout_seconds=5)

        async def mock_extract(url: str) -> RssExtractedArticle:
            raise asyncio.TimeoutError("Timeout")

        with (
            patch.object(
                extractor._extractor,
                "extract",
                side_effect=mock_extract,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.TIMEOUT
        assert "Timeout" in str(result.error_message)

    @pytest.mark.asyncio
    async def test_正常系_max_retries_1は即座に失敗を返す(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """extract with max_retries=1 should fail immediately without retry."""
        extractor = TrafilaturaExtractor(max_retries=1)
        call_count = 0

        async def mock_extract(url: str) -> RssExtractedArticle:
            nonlocal call_count
            call_count += 1
            raise Exception("Failed")

        with (
            patch.object(
                extractor._extractor,
                "extract",
                side_effect=mock_extract,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            result = await extractor.extract(sample_collected_article)

        assert call_count == 1
        assert result.extraction_status == ExtractionStatus.FAILED
        mock_sleep.assert_not_called()


class TestTrafilaturaExtractorBatch:
    """Tests for extract_batch inherited from BaseExtractor."""

    @pytest.mark.asyncio
    async def test_正常系_extract_batchは複数記事を抽出できる(self) -> None:
        """extract_batch should extract multiple articles."""
        extractor = TrafilaturaExtractor()

        articles = [
            CollectedArticle(
                url=f"https://www.cnbc.com/article/{i}",  # type: ignore[arg-type]
                title=f"Test Article {i}",
                published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                raw_summary=f"Summary {i}",
                source=ArticleSource(
                    source_type=SourceType.RSS,
                    source_name="CNBC Markets",
                    category="market",
                ),
                collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            )
            for i in range(3)
        ]

        async def mock_extract(url: str) -> RssExtractedArticle:
            return RssExtractedArticle(
                url=url,
                title="Test",
                text="A" * 300,
                author=None,
                date=None,
                source=None,
                language=None,
                status=RssExtractionStatus.SUCCESS,
                error=None,
                extraction_method="trafilatura",
            )

        with patch.object(
            extractor._extractor,
            "extract",
            side_effect=mock_extract,
        ):
            results = await extractor.extract_batch(articles)

        assert len(results) == 3
        assert all(isinstance(r, ExtractedArticle) for r in results)
        assert all(r.extraction_status == ExtractionStatus.SUCCESS for r in results)
