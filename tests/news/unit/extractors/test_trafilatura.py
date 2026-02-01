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
- User-Agent rotation (Issue #2605)
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from news.config.workflow import (
    ExtractionConfig,
    PlaywrightFallbackConfig,
    UserAgentRotationConfig,
)
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
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


class TestTrafilaturaExtractorUserAgentRotation:
    """Tests for TrafilaturaExtractor User-Agent rotation functionality.

    Issue #2605: TrafilaturaExtractorにUser-Agent設定
    """

    def test_正常系_user_agent_configなしでインスタンス化できる(self) -> None:
        """user_agent_configなしでインスタンス化できることを確認。"""
        extractor = TrafilaturaExtractor()
        assert extractor._user_agent_config is None

    def test_正常系_user_agent_configありでインスタンス化できる(self) -> None:
        """user_agent_configありでインスタンス化できることを確認。"""
        ua_config = UserAgentRotationConfig(
            enabled=True,
            user_agents=["UA1", "UA2"],
        )
        extractor = TrafilaturaExtractor(user_agent_config=ua_config)
        assert extractor._user_agent_config is ua_config

    @pytest.mark.asyncio
    async def test_正常系_User_Agentが抽出時に使用される(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """User-Agentが抽出時に使用されることを確認。"""
        ua_config = UserAgentRotationConfig(
            enabled=True,
            user_agents=["CustomUA1", "CustomUA2"],
        )
        extractor = TrafilaturaExtractor(user_agent_config=ua_config)

        captured_user_agents: list[str | None] = []

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
            captured_user_agents.append(user_agent)
            return mock_rss_extracted_article_success

        with patch.object(
            extractor._extractor,
            "extract",
            side_effect=mock_extract,
        ):
            await extractor.extract(sample_collected_article)

        # User-Agentがいずれかの設定値であることを確認
        assert len(captured_user_agents) == 1
        assert captured_user_agents[0] in ["CustomUA1", "CustomUA2"]

    @pytest.mark.asyncio
    async def test_正常系_無効時はデフォルトUser_Agentが使用される(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """User-Agent rotation無効時はNoneが渡されることを確認（デフォルト使用）。"""
        ua_config = UserAgentRotationConfig(
            enabled=False,
            user_agents=["CustomUA1", "CustomUA2"],
        )
        extractor = TrafilaturaExtractor(user_agent_config=ua_config)

        captured_user_agents: list[str | None] = []

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
            captured_user_agents.append(user_agent)
            return mock_rss_extracted_article_success

        with patch.object(
            extractor._extractor,
            "extract",
            side_effect=mock_extract,
        ):
            await extractor.extract(sample_collected_article)

        # User-AgentがNone（デフォルト使用）であることを確認
        assert len(captured_user_agents) == 1
        assert captured_user_agents[0] is None

    @pytest.mark.asyncio
    async def test_正常系_User_Agentがリクエスト毎にランダムに選択される(
        self,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """User-Agentがリクエスト毎にランダムに選択されることを確認。"""
        ua_config = UserAgentRotationConfig(
            enabled=True,
            user_agents=["UA1", "UA2", "UA3"],
        )
        extractor = TrafilaturaExtractor(user_agent_config=ua_config)

        captured_user_agents: list[str | None] = []

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
            captured_user_agents.append(user_agent)
            return mock_rss_extracted_article_success

        with patch.object(
            extractor._extractor,
            "extract",
            side_effect=mock_extract,
        ):
            # 複数回抽出を実行
            for i in range(20):
                article = CollectedArticle(
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
                await extractor.extract(article)

        # 複数種類のUser-Agentが使用されることを確認
        unique_user_agents = set(captured_user_agents)
        assert len(unique_user_agents) >= 2  # 20回試行で少なくとも2種類は使用される

    @pytest.mark.asyncio
    async def test_正常系_User_Agentがログに出力される(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """User-Agentがログに出力されることを確認（DEBUGレベル）。"""
        ua_config = UserAgentRotationConfig(
            enabled=True,
            user_agents=["TestUserAgent/1.0"],
        )
        extractor = TrafilaturaExtractor(user_agent_config=ua_config)

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
            return mock_rss_extracted_article_success

        with (
            patch.object(
                extractor._extractor,
                "extract",
                side_effect=mock_extract,
            ),
            patch("news.extractors.trafilatura.logger") as mock_logger,
        ):
            await extractor.extract(sample_collected_article)

        # DEBUGレベルでUser-Agentがログに出力されることを確認
        mock_logger.debug.assert_called()
        debug_calls = mock_logger.debug.call_args_list
        user_agent_logged = any(
            "Using custom User-Agent" in str(call) or "user_agent" in str(call)
            for call in debug_calls
        )
        assert user_agent_logged

    @pytest.mark.asyncio
    async def test_正常系_user_agent_configなしでも正常に動作する(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """user_agent_configなしでも正常に動作することを確認。"""
        extractor = TrafilaturaExtractor()  # user_agent_configなし

        captured_user_agents: list[str | None] = []

        async def mock_extract(
            url: str, user_agent: str | None = None
        ) -> RssExtractedArticle:
            captured_user_agents.append(user_agent)
            return mock_rss_extracted_article_success

        with patch.object(
            extractor._extractor,
            "extract",
            side_effect=mock_extract,
        ):
            result = await extractor.extract(sample_collected_article)

        # 正常に抽出が完了し、User-AgentはNone（デフォルト）
        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert len(captured_user_agents) == 1
        assert captured_user_agents[0] is None


class TestTrafilaturaExtractorPlaywrightFallback:
    """Tests for TrafilaturaExtractor Playwright fallback functionality.

    Issue #2608: trafilatura→Playwrightフォールバック
    - trafilatura失敗時にPlaywrightで再試行
    - フォールバック成功時は extraction_method="trafilatura+playwright"
    - フォールバック無効時は従来通りtrafilaturaのみ
    - 非同期コンテキストマネージャでブラウザ管理
    """

    @pytest.fixture
    def extraction_config(self) -> ExtractionConfig:
        """Create an ExtractionConfig with Playwright fallback enabled."""
        return ExtractionConfig(
            min_body_length=200,
            max_retries=1,  # Reduce retries for faster tests
            timeout_seconds=30,
            playwright_fallback=PlaywrightFallbackConfig(
                enabled=True,
                browser="chromium",
                headless=True,
                timeout_seconds=30,
            ),
        )

    @pytest.fixture
    def extraction_config_disabled(self) -> ExtractionConfig:
        """Create an ExtractionConfig with Playwright fallback disabled."""
        return ExtractionConfig(
            min_body_length=200,
            max_retries=1,
            timeout_seconds=30,
            playwright_fallback=PlaywrightFallbackConfig(
                enabled=False,
            ),
        )

    def test_正常系_ExtractionConfigでインスタンス化できる(
        self,
        extraction_config: ExtractionConfig,
    ) -> None:
        """TrafilaturaExtractor can be instantiated with ExtractionConfig."""
        extractor = TrafilaturaExtractor.from_config(extraction_config)
        assert extractor is not None
        assert extractor._min_body_length == 200
        assert extractor._playwright_config is not None
        assert extractor._playwright_config.enabled is True

    def test_正常系_フォールバック無効時はPlaywrightExtractorがNone(
        self,
        extraction_config_disabled: ExtractionConfig,
    ) -> None:
        """Playwright fallback disabled should result in None playwright extractor."""
        extractor = TrafilaturaExtractor.from_config(extraction_config_disabled)
        assert extractor._playwright_config is not None
        assert extractor._playwright_config.enabled is False
        assert extractor._playwright_extractor is None

    @pytest.mark.asyncio
    async def test_正常系_非同期コンテキストマネージャとして使用できる(
        self,
        extraction_config: ExtractionConfig,
    ) -> None:
        """TrafilaturaExtractor can be used as async context manager."""
        with patch("news.extractors.playwright.PlaywrightExtractor") as MockPlaywright:
            mock_playwright = MagicMock()
            mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_playwright.__aexit__ = AsyncMock(return_value=None)
            MockPlaywright.return_value = mock_playwright

            async with TrafilaturaExtractor.from_config(extraction_config) as extractor:
                assert extractor is not None
                # Playwright extractor should be initialized
                assert extractor._playwright_extractor is not None

            # __aexit__ should have been called
            mock_playwright.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_フォールバック無効時はPlaywrightが初期化されない(
        self,
        extraction_config_disabled: ExtractionConfig,
    ) -> None:
        """Playwright should not be initialized when fallback is disabled."""
        async with TrafilaturaExtractor.from_config(
            extraction_config_disabled
        ) as extractor:
            assert extractor._playwright_extractor is None

    @pytest.mark.asyncio
    async def test_正常系_trafilatura成功時はフォールバックしない(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
        extraction_config: ExtractionConfig,
    ) -> None:
        """No fallback should occur when trafilatura succeeds."""
        with patch("news.extractors.playwright.PlaywrightExtractor") as MockPlaywright:
            mock_playwright = MagicMock()
            mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_playwright.__aexit__ = AsyncMock(return_value=None)
            mock_playwright.extract = AsyncMock()
            MockPlaywright.return_value = mock_playwright

            async with TrafilaturaExtractor.from_config(extraction_config) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=mock_rss_extracted_article_success,
                ):
                    result = await extractor.extract(sample_collected_article)

            assert result.extraction_status == ExtractionStatus.SUCCESS
            assert result.extraction_method == "trafilatura"
            # Playwright extract should not have been called
            mock_playwright.extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_正常系_trafilatura失敗時にPlaywrightでフォールバック(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_failed: RssExtractedArticle,
        extraction_config: ExtractionConfig,
    ) -> None:
        """Fallback to Playwright when trafilatura fails."""
        playwright_result = ExtractedArticle(
            collected=sample_collected_article,
            body_text="Playwright extracted content. " * 20,
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="playwright",
            error_message=None,
        )

        with patch("news.extractors.playwright.PlaywrightExtractor") as MockPlaywright:
            mock_playwright = MagicMock()
            mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_playwright.__aexit__ = AsyncMock(return_value=None)
            mock_playwright.extract = AsyncMock(return_value=playwright_result)
            MockPlaywright.return_value = mock_playwright

            async with TrafilaturaExtractor.from_config(extraction_config) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=mock_rss_extracted_article_failed,
                ):
                    result = await extractor.extract(sample_collected_article)

            assert result.extraction_status == ExtractionStatus.SUCCESS
            assert result.extraction_method == "trafilatura+playwright"
            assert result.body_text is not None
            mock_playwright.extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_本文短すぎ時にPlaywrightでフォールバック(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_short: RssExtractedArticle,
        extraction_config: ExtractionConfig,
    ) -> None:
        """Fallback to Playwright when body text is too short."""
        playwright_result = ExtractedArticle(
            collected=sample_collected_article,
            body_text="Playwright extracted long content. " * 20,
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="playwright",
            error_message=None,
        )

        with patch("news.extractors.playwright.PlaywrightExtractor") as MockPlaywright:
            mock_playwright = MagicMock()
            mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_playwright.__aexit__ = AsyncMock(return_value=None)
            mock_playwright.extract = AsyncMock(return_value=playwright_result)
            MockPlaywright.return_value = mock_playwright

            async with TrafilaturaExtractor.from_config(extraction_config) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=mock_rss_extracted_article_short,
                ):
                    result = await extractor.extract(sample_collected_article)

            assert result.extraction_status == ExtractionStatus.SUCCESS
            assert result.extraction_method == "trafilatura+playwright"
            mock_playwright.extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_異常系_フォールバックも失敗時は元のエラーを返す(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_failed: RssExtractedArticle,
        extraction_config: ExtractionConfig,
    ) -> None:
        """Return original error when both trafilatura and Playwright fail."""
        playwright_result = ExtractedArticle(
            collected=sample_collected_article,
            body_text=None,
            extraction_status=ExtractionStatus.FAILED,
            extraction_method="playwright",
            error_message="Playwright also failed",
        )

        with patch("news.extractors.playwright.PlaywrightExtractor") as MockPlaywright:
            mock_playwright = MagicMock()
            mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_playwright.__aexit__ = AsyncMock(return_value=None)
            mock_playwright.extract = AsyncMock(return_value=playwright_result)
            MockPlaywright.return_value = mock_playwright

            async with TrafilaturaExtractor.from_config(extraction_config) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=mock_rss_extracted_article_failed,
                ):
                    result = await extractor.extract(sample_collected_article)

            # 元のtrafilaturaの結果を返す
            assert result.extraction_status == ExtractionStatus.FAILED
            assert result.extraction_method == "trafilatura"
            assert result.error_message == "Failed to fetch"

    @pytest.mark.asyncio
    async def test_正常系_フォールバック無効時はtrafilaturaのみ(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_failed: RssExtractedArticle,
        extraction_config_disabled: ExtractionConfig,
    ) -> None:
        """Only trafilatura is used when fallback is disabled."""
        async with TrafilaturaExtractor.from_config(
            extraction_config_disabled
        ) as extractor:
            with patch.object(
                extractor._extractor,
                "extract",
                new_callable=AsyncMock,
                return_value=mock_rss_extracted_article_failed,
            ):
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.extraction_method == "trafilatura"
        # Playwright should not have been invoked
        assert extractor._playwright_extractor is None

    @pytest.mark.asyncio
    async def test_正常系_PAYWALL時はフォールバックしない(
        self,
        sample_collected_article: CollectedArticle,
        extraction_config: ExtractionConfig,
    ) -> None:
        """No fallback on PAYWALL status (non-retryable)."""
        paywall_result = RssExtractedArticle(
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

        with patch("news.extractors.playwright.PlaywrightExtractor") as MockPlaywright:
            mock_playwright = MagicMock()
            mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_playwright.__aexit__ = AsyncMock(return_value=None)
            mock_playwright.extract = AsyncMock()
            MockPlaywright.return_value = mock_playwright

            async with TrafilaturaExtractor.from_config(extraction_config) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=paywall_result,
                ):
                    result = await extractor.extract(sample_collected_article)

            assert result.extraction_status == ExtractionStatus.PAYWALL
            # Playwright should not have been called
            mock_playwright.extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_正常系_コンテキストマネージャ外でも使用できる(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
        extraction_config: ExtractionConfig,
    ) -> None:
        """Extractor can be used without context manager (fallback disabled)."""
        # 通常の使用（コンテキストマネージャなし）でも動作
        extractor = TrafilaturaExtractor.from_config(extraction_config)

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_rss_extracted_article_success,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        # フォールバックなしでの成功
        assert result.extraction_method == "trafilatura"

    @pytest.mark.asyncio
    async def test_正常系_コンテキストマネージャ外でフォールバック不要時(
        self,
        sample_collected_article: CollectedArticle,
        mock_rss_extracted_article_success: RssExtractedArticle,
    ) -> None:
        """Extractor works normally without context manager when fallback not needed."""
        extractor = TrafilaturaExtractor()  # レガシーインスタンス化

        with patch.object(
            extractor._extractor,
            "extract",
            new_callable=AsyncMock,
            return_value=mock_rss_extracted_article_success,
        ):
            result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.extraction_method == "trafilatura"
