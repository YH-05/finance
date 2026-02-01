"""Unit tests for the Summarizer class.

Tests for the basic Summarizer class structure including:
- Constructor initialization with NewsWorkflowConfig
- summarize() method signature and behavior with no body text
- summarize_batch() method signature
- Claude SDK integration (P4-002)
- Claude Agent SDK integration (P9-002)

Following TDD approach: Red -> Green -> Refactor
"""

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

import pytest
from news.config.workflow import NewsWorkflowConfig, SummarizationConfig
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    SourceType,
    StructuredSummary,
    SummarizationStatus,
)

# Fixtures


@pytest.fixture
def sample_config() -> NewsWorkflowConfig:
    """Create a sample NewsWorkflowConfig for testing."""
    return NewsWorkflowConfig(
        version="1.0",
        status_mapping={"market": "index"},
        github_status_ids={"index": "test-id"},
        rss={"presets_file": "test.json"},  # type: ignore[arg-type]
        summarization=SummarizationConfig(
            prompt_template="Summarize this article in Japanese: {body}",
        ),
        github={  # type: ignore[arg-type]
            "project_number": 15,
            "project_id": "PVT_test",
            "status_field_id": "PVTSSF_test",
            "published_date_field_id": "PVTF_test",
            "repository": "owner/repo",
        },
        output={"result_dir": "data/exports"},  # type: ignore[arg-type]
    )


@pytest.fixture
def sample_source() -> ArticleSource:
    """Create a sample ArticleSource."""
    return ArticleSource(
        source_type=SourceType.RSS,
        source_name="CNBC Markets",
        category="market",
    )


@pytest.fixture
def sample_collected_article(sample_source: ArticleSource) -> CollectedArticle:
    """Create a sample CollectedArticle."""
    return CollectedArticle(
        url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
        title="Market Update: S&P 500 Rallies",
        published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        raw_summary="Stocks rose on positive earnings reports.",
        source=sample_source,
        collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def extracted_article_with_body(
    sample_collected_article: CollectedArticle,
) -> ExtractedArticle:
    """Create an ExtractedArticle with body text."""
    return ExtractedArticle(
        collected=sample_collected_article,
        body_text="Full article content about the S&P 500 rally...",
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_method="trafilatura",
    )


@pytest.fixture
def extracted_article_no_body(
    sample_collected_article: CollectedArticle,
) -> ExtractedArticle:
    """Create an ExtractedArticle without body text (extraction failed)."""
    return ExtractedArticle(
        collected=sample_collected_article,
        body_text=None,
        extraction_status=ExtractionStatus.FAILED,
        extraction_method="trafilatura",
        error_message="Failed to extract body text",
    )


# Tests


class TestSummarizer:
    """Tests for the Summarizer class."""

    def test_正常系_コンストラクタで設定を受け取る(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Summarizer should accept NewsWorkflowConfig in constructor."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        assert summarizer._config is sample_config
        assert (
            summarizer._prompt_template == sample_config.summarization.prompt_template
        )

    def test_正常系_summarizeメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Summarizer should have a summarize() method."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Check method exists and is callable
        assert hasattr(summarizer, "summarize")
        assert callable(summarizer.summarize)

    def test_正常系_summarize_batchメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Summarizer should have a summarize_batch() method."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Check method exists and is callable
        assert hasattr(summarizer, "summarize_batch")
        assert callable(summarizer.summarize_batch)


class TestSummarizeNoBodyText:
    """Tests for summarize() when article has no body text."""

    @pytest.mark.asyncio
    async def test_正常系_本文なしでSKIPPEDステータスを返す(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_no_body: ExtractedArticle,
    ) -> None:
        """summarize() should return SKIPPED status when body_text is None."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        result = await summarizer.summarize(extracted_article_no_body)

        assert result.summarization_status == SummarizationStatus.SKIPPED
        assert result.summary is None
        assert result.error_message == "No body text available"
        assert result.extracted is extracted_article_no_body

    @pytest.mark.asyncio
    async def test_正常系_本文ありで処理継続(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """summarize() should not immediately return SKIPPED when body_text exists.

        Note: This test only verifies the basic flow. Actual Claude SDK integration
        is handled in P4-002.
        """
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # For P4-001, we just verify the method doesn't return SKIPPED for valid body
        # The actual implementation will be completed in P4-002
        result = await summarizer.summarize(extracted_article_with_body)

        # Should not be SKIPPED since body_text is present
        assert result.summarization_status != SummarizationStatus.SKIPPED


class TestSummarizeBatch:
    """Tests for summarize_batch() method."""

    @pytest.mark.asyncio
    async def test_正常系_空リストで空リストを返す(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """summarize_batch() should return empty list for empty input."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        result = await summarizer.summarize_batch([])

        assert result == []

    @pytest.mark.asyncio
    async def test_正常系_複数記事を処理できる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_no_body: ExtractedArticle,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """summarize_batch() should process multiple articles."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)
        articles = [extracted_article_no_body, extracted_article_with_body]

        result = await summarizer.summarize_batch(articles, concurrency=2)

        assert len(result) == 2
        # First article (no body) should be SKIPPED
        assert result[0].summarization_status == SummarizationStatus.SKIPPED


class TestSummarizerClaudeIntegration:
    """Tests for Claude Agent SDK integration (P9-003)."""

    def test_正常系_プロンプトテンプレートが設定から読み込まれる(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """Prompt template should be loaded from config."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Verify prompt template is loaded from config
        assert (
            summarizer._prompt_template == sample_config.summarization.prompt_template
        )

    @pytest.mark.asyncio
    async def test_正常系_記事情報がプロンプトに含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Article info (title, source, published, body) should be included in prompt."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Test _build_prompt directly
        prompt = summarizer._build_prompt(extracted_article_with_body)

        # Verify article info is in the prompt
        article = extracted_article_with_body.collected
        assert article.title in prompt
        assert article.source.source_name in prompt
        assert extracted_article_with_body.body_text is not None
        assert extracted_article_with_body.body_text in prompt

    @pytest.mark.asyncio
    async def test_正常系_Claudeのレスポンスが取得できる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Claude response should be parsed into StructuredSummary."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Mock _call_claude_sdk to return valid JSON
        async def mock_call_claude_sdk(prompt: str) -> str:
            return """{
                "overview": "S&P 500が上昇した。",
                "key_points": ["ポイント1", "ポイント2"],
                "market_impact": "市場への影響",
                "related_info": "関連情報"
            }"""

        with patch.object(
            summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        # Verify result
        assert result.summarization_status == SummarizationStatus.SUCCESS
        assert result.summary is not None
        assert isinstance(result.summary, StructuredSummary)
        assert result.summary.overview == "S&P 500が上昇した。"
        assert result.summary.key_points == ["ポイント1", "ポイント2"]
        assert result.summary.market_impact == "市場への影響"
        assert result.summary.related_info == "関連情報"

    @pytest.mark.asyncio
    async def test_異常系_APIエラーでFAILEDステータスを返す(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """API error should result in FAILED status."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Mock _call_claude_sdk to raise exception
        async def mock_call_claude_sdk_error(prompt: str) -> str:
            raise Exception("API Error")

        with (
            patch.object(
                summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk_error
            ),
            patch("asyncio.sleep", return_value=None),
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.FAILED
        assert result.summary is None
        assert result.error_message is not None
        assert "API Error" in result.error_message

    @pytest.mark.asyncio
    async def test_異常系_JSONパースエラーでFAILEDステータスを返す(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """JSON parse error should result in FAILED status."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Mock _call_claude_sdk to return invalid JSON
        async def mock_call_claude_sdk_invalid(prompt: str) -> str:
            return "This is not valid JSON"

        with patch.object(
            summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk_invalid
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.FAILED
        assert result.summary is None
        assert result.error_message is not None


class TestSummarizerJsonParsing:
    """Tests for _parse_response JSON parsing (P4-003).

    Tests for:
    - ```json ... ``` markdown block extraction
    - Direct JSON parsing
    - Pydantic model_validate() validation
    - Appropriate error messages
    """

    def test_正常系_直接JSONをパースできる(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """Direct JSON (without markdown block) should be parsed correctly."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        json_response = """{
            "overview": "概要テスト",
            "key_points": ["ポイント1", "ポイント2"],
            "market_impact": "市場影響テスト",
            "related_info": null
        }"""

        result = summarizer._parse_response(json_response)

        assert result.overview == "概要テスト"
        assert result.key_points == ["ポイント1", "ポイント2"]
        assert result.market_impact == "市場影響テスト"
        assert result.related_info is None

    def test_正常系_マークダウンJSON形式をパースできる(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """JSON wrapped in ```json ... ``` markdown block should be parsed."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        markdown_response = """```json
{
    "overview": "マークダウン概要",
    "key_points": ["MDポイント1"],
    "market_impact": "MD市場影響",
    "related_info": "MD関連情報"
}
```"""

        result = summarizer._parse_response(markdown_response)

        assert result.overview == "マークダウン概要"
        assert result.key_points == ["MDポイント1"]
        assert result.market_impact == "MD市場影響"
        assert result.related_info == "MD関連情報"

    def test_正常系_マークダウンJSON形式の前後に空白がある場合(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """JSON block with whitespace before/after should be parsed."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        markdown_response = """Here is the summary:

```json
{
    "overview": "空白付き概要",
    "key_points": ["空白ポイント"],
    "market_impact": "空白市場影響",
    "related_info": null
}
```

Thank you!"""

        result = summarizer._parse_response(markdown_response)

        assert result.overview == "空白付き概要"
        assert result.key_points == ["空白ポイント"]

    def test_正常系_Pydanticモデルバリデーションが適用される(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """Response should be validated using Pydantic model_validate."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Valid JSON that passes Pydantic validation
        valid_response = """{
            "overview": "バリデーション概要",
            "key_points": ["バリデーションポイント"],
            "market_impact": "バリデーション影響",
            "related_info": "関連情報あり"
        }"""

        result = summarizer._parse_response(valid_response)

        # Should return StructuredSummary instance
        assert isinstance(result, StructuredSummary)
        assert result.related_info == "関連情報あり"

    def test_異常系_JSONパースエラーで適切なエラーメッセージ(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """Invalid JSON should raise ValueError with descriptive message."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        invalid_json = "{ invalid json }"

        with pytest.raises(ValueError) as exc_info:
            summarizer._parse_response(invalid_json)

        error_message = str(exc_info.value)
        assert "JSON parse error" in error_message

    def test_異常系_バリデーションエラーで適切なエラーメッセージ(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """Pydantic validation error should raise ValueError with descriptive message."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Valid JSON but invalid structure (missing required field)
        invalid_structure = """{
            "overview": "概要のみ"
        }"""

        with pytest.raises(ValueError) as exc_info:
            summarizer._parse_response(invalid_structure)

        error_message = str(exc_info.value)
        assert "Validation error" in error_message

    def test_異常系_key_pointsが文字列でバリデーションエラー(
        self,
        sample_config: NewsWorkflowConfig,
    ) -> None:
        """key_points should be a list, not a string."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # key_points is a string instead of list
        invalid_type = """{
            "overview": "概要",
            "key_points": "これはリストではない",
            "market_impact": "市場影響"
        }"""

        with pytest.raises(ValueError) as exc_info:
            summarizer._parse_response(invalid_type)

        error_message = str(exc_info.value)
        assert "Validation error" in error_message

    @pytest.mark.asyncio
    async def test_正常系_summarizeでマークダウンJSONが処理される(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """summarize() should correctly process markdown-wrapped JSON response."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Mock _call_claude_sdk to return markdown-wrapped JSON
        async def mock_call_claude_sdk(prompt: str) -> str:
            return """```json
{
    "overview": "統合テスト概要",
    "key_points": ["統合ポイント1", "統合ポイント2"],
    "market_impact": "統合市場影響",
    "related_info": null
}
```"""

        with patch.object(
            summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.SUCCESS
        assert result.summary is not None
        assert result.summary.overview == "統合テスト概要"
        assert result.summary.key_points == ["統合ポイント1", "統合ポイント2"]

    @pytest.mark.asyncio
    async def test_異常系_summarizeでバリデーションエラー時FAILEDを返す(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """summarize() should return FAILED status on validation error."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)

        # Mock _call_claude_sdk to return invalid JSON (missing required fields)
        async def mock_call_claude_sdk(prompt: str) -> str:
            return '{"overview": "概要のみ"}'

        with patch.object(
            summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.FAILED
        assert result.summary is None
        assert result.error_message is not None
        assert "Validation error" in result.error_message


class TestSummarizerRetry:
    """Tests for retry logic in Summarizer (P4-005).

    Tests for:
    - Maximum 3 retries on failure
    - Exponential backoff (1s, 2s, 4s)
    - Timeout handling (default 60 seconds)
    - Appropriate status after all retries fail
    - Retry logging
    """

    @pytest.fixture
    def retry_config(self) -> NewsWorkflowConfig:
        """Create a config with explicit retry settings."""
        return NewsWorkflowConfig(
            version="1.0",
            status_mapping={"market": "index"},
            github_status_ids={"index": "test-id"},
            rss={"presets_file": "test.json"},  # type: ignore[arg-type]
            summarization=SummarizationConfig(
                prompt_template="Summarize: {body}",
                max_retries=3,
                timeout_seconds=60,
            ),
            github={  # type: ignore[arg-type]
                "project_number": 15,
                "project_id": "PVT_test",
                "status_field_id": "PVTSSF_test",
                "published_date_field_id": "PVTF_test",
                "repository": "owner/repo",
            },
            output={"result_dir": "data/exports"},  # type: ignore[arg-type]
        )

    @pytest.mark.asyncio
    async def test_正常系_1回目の試行で成功(
        self,
        retry_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """First attempt succeeds, no retries needed."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)
        call_count = 0

        async def mock_call_claude_sdk(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            return '{"overview": "成功", "key_points": ["p1"], "market_impact": "影響", "related_info": null}'

        with patch.object(
            summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.SUCCESS
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_正常系_2回目の試行で成功(
        self,
        retry_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """First attempt fails, second succeeds."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)
        call_count = 0

        async def mock_call_claude_sdk(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("API Error")
            return '{"overview": "成功", "key_points": ["p1"], "market_impact": "影響", "related_info": null}'

        with (
            patch.object(
                summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
            ),
            patch("asyncio.sleep", return_value=None) as mock_sleep,
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.SUCCESS
        assert call_count == 2
        # Verify backoff was applied (1 second)
        mock_sleep.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_正常系_3回目の試行で成功(
        self,
        retry_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """First two attempts fail, third succeeds."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)
        call_count = 0

        async def mock_call_claude_sdk(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"API Error {call_count}")
            return '{"overview": "成功", "key_points": ["p1"], "market_impact": "影響", "related_info": null}'

        with (
            patch.object(
                summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
            ),
            patch("asyncio.sleep", return_value=None) as mock_sleep,
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.SUCCESS
        assert call_count == 3
        # Verify backoff was applied (1s, 2s)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @pytest.mark.asyncio
    async def test_異常系_3回リトライ後も失敗(
        self,
        retry_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """All 3 retries fail, returns FAILED status."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)
        call_count = 0

        async def mock_call_claude_sdk(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent API Error")

        with (
            patch.object(
                summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
            ),
            patch("asyncio.sleep", return_value=None) as mock_sleep,
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.FAILED
        assert result.summary is None
        assert result.error_message is not None
        assert "Persistent API Error" in result.error_message
        assert call_count == 3
        # Verify backoff was applied (1s, 2s)
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_異常系_タイムアウトでTIMEOUTステータスを返す(
        self,
        retry_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Timeout should return TIMEOUT status after retries."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)
        call_count = 0

        async def mock_call_claude_sdk(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            raise asyncio.TimeoutError("Timeout")

        with (
            patch.object(
                summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
            ),
            patch("asyncio.sleep", return_value=None),
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.TIMEOUT
        assert result.summary is None
        assert result.error_message is not None
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_正常系_指数バックオフの待ち時間(
        self,
        retry_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Backoff should follow 1s, 2s, 4s pattern."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)

        async def mock_call_claude_sdk(prompt: str) -> str:
            raise Exception("Error")

        with (
            patch.object(
                summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
            ),
            patch("asyncio.sleep", return_value=None) as mock_sleep,
        ):
            await summarizer.summarize(extracted_article_with_body)

        # 3 attempts = 2 sleeps (between attempts)
        # Backoff: 2^0=1, 2^1=2 (no sleep after last attempt)
        assert mock_sleep.call_count == 2
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert calls == [1, 2]

    @pytest.mark.asyncio
    async def test_正常系_リトライ中のログ出力(
        self,
        retry_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Retry attempts should be logged with warning level."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)

        async def mock_call_claude_sdk(prompt: str) -> str:
            raise Exception("API Error")

        with (
            patch.object(
                summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
            ),
            patch("asyncio.sleep", return_value=None),
            patch("news.summarizer.logger") as mock_logger,
        ):
            await summarizer.summarize(extracted_article_with_body)

        # Verify warning logs were called for each retry
        warning_calls = mock_logger.warning.call_args_list
        assert len(warning_calls) == 3
        # Check that attempt numbers are logged
        for i, call in enumerate(warning_calls, start=1):
            kwargs = call[1]
            assert kwargs.get("attempt") == i
            assert kwargs.get("max_retries") == 3

    @pytest.mark.asyncio
    async def test_正常系_configからmax_retriesを取得(
        self,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """max_retries should be read from config."""
        from news.summarizer import Summarizer

        # Config with max_retries=2
        config_2_retries = NewsWorkflowConfig(
            version="1.0",
            status_mapping={"market": "index"},
            github_status_ids={"index": "test-id"},
            rss={"presets_file": "test.json"},  # type: ignore[arg-type]
            summarization=SummarizationConfig(
                prompt_template="Summarize: {body}",
                max_retries=2,
                timeout_seconds=60,
            ),
            github={  # type: ignore[arg-type]
                "project_number": 15,
                "project_id": "PVT_test",
                "status_field_id": "PVTSSF_test",
                "published_date_field_id": "PVTF_test",
                "repository": "owner/repo",
            },
            output={"result_dir": "data/exports"},  # type: ignore[arg-type]
        )

        summarizer = Summarizer(config=config_2_retries)
        call_count = 0

        async def mock_call_claude_sdk(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            raise Exception("Error")

        with (
            patch.object(
                summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
            ),
            patch("asyncio.sleep", return_value=None),
        ):
            await summarizer.summarize(extracted_article_with_body)

        # Should only retry 2 times (as per config)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_正常系_configからtimeout_secondsを取得(
        self,
        retry_config: NewsWorkflowConfig,
    ) -> None:
        """timeout_seconds should be read from config and used in __init__."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)

        # Verify timeout is stored from config
        assert summarizer._timeout_seconds == 60

    @pytest.mark.asyncio
    async def test_正常系_本文なしの場合はリトライなしでSKIPPED(
        self,
        retry_config: NewsWorkflowConfig,
        extracted_article_no_body: ExtractedArticle,
    ) -> None:
        """No body text should return SKIPPED without any retry attempts."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=retry_config)
        call_count = 0

        async def mock_call_claude_sdk(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            return '{"overview": "成功", "key_points": ["p1"], "market_impact": "影響", "related_info": null}'

        with patch.object(
            summarizer, "_call_claude_sdk", side_effect=mock_call_claude_sdk
        ):
            result = await summarizer.summarize(extracted_article_no_body)

        assert result.summarization_status == SummarizationStatus.SKIPPED
        # Should not call Claude API at all
        assert call_count == 0


class TestBuildPrompt:
    """Tests for _build_prompt method (P9-003)."""

    def test_正常系_プロンプトにタイトルが含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """_build_prompt should include article title in prompt."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)
        prompt = summarizer._build_prompt(extracted_article_with_body)

        assert extracted_article_with_body.collected.title in prompt

    def test_正常系_プロンプトにソース名が含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """_build_prompt should include source name in prompt."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)
        prompt = summarizer._build_prompt(extracted_article_with_body)

        assert extracted_article_with_body.collected.source.source_name in prompt

    def test_正常系_プロンプトに公開日が含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """_build_prompt should include published date in ISO format."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)
        prompt = summarizer._build_prompt(extracted_article_with_body)

        # Published date should be in ISO format
        expected_date = extracted_article_with_body.collected.published
        assert expected_date is not None
        assert expected_date.isoformat() in prompt

    def test_正常系_プロンプトに本文が含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """_build_prompt should include body text in prompt."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)
        prompt = summarizer._build_prompt(extracted_article_with_body)

        assert extracted_article_with_body.body_text is not None
        assert extracted_article_with_body.body_text in prompt

    def test_正常系_プロンプトにJSON出力形式が含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """_build_prompt should include JSON output format specification."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=sample_config)
        prompt = summarizer._build_prompt(extracted_article_with_body)

        assert "overview" in prompt
        assert "key_points" in prompt
        assert "market_impact" in prompt
        assert "related_info" in prompt

    def test_エッジケース_公開日がNoneの場合は不明と表示(
        self,
        sample_config: NewsWorkflowConfig,
        sample_source: ArticleSource,
    ) -> None:
        """_build_prompt should show '不明' when published date is None."""
        from news.summarizer import Summarizer

        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Test Article",
            published=None,  # No published date
            raw_summary="Summary",
            source=sample_source,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        article = ExtractedArticle(
            collected=collected,
            body_text="Test body text",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )

        summarizer = Summarizer(config=sample_config)
        prompt = summarizer._build_prompt(article)

        assert "不明" in prompt


class TestAsyncioTimeout:
    """Tests for asyncio.timeout integration (P9-003)."""

    @pytest.fixture
    def timeout_config(self) -> NewsWorkflowConfig:
        """Create a config with short timeout for testing."""
        return NewsWorkflowConfig(
            version="1.0",
            status_mapping={"market": "index"},
            github_status_ids={"index": "test-id"},
            rss={"presets_file": "test.json"},  # type: ignore[arg-type]
            summarization=SummarizationConfig(
                prompt_template="Summarize: {body}",
                max_retries=1,
                timeout_seconds=1,  # 1 second timeout
            ),
            github={  # type: ignore[arg-type]
                "project_number": 15,
                "project_id": "PVT_test",
                "status_field_id": "PVTSSF_test",
                "published_date_field_id": "PVTF_test",
                "repository": "owner/repo",
            },
            output={"result_dir": "data/exports"},  # type: ignore[arg-type]
        )

    @pytest.mark.asyncio
    async def test_正常系_asyncio_timeoutでタイムアウト処理(
        self,
        timeout_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """asyncio.timeout should handle slow SDK calls."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=timeout_config)

        async def slow_call_claude_sdk(prompt: str) -> str:
            await asyncio.sleep(10)  # Simulate slow response
            return '{"overview": "遅い", "key_points": [], "market_impact": "なし", "related_info": null}'

        with patch.object(
            summarizer, "_call_claude_sdk", side_effect=slow_call_claude_sdk
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.TIMEOUT
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_正常系_タイムアウト設定が設定から読み込まれる(
        self,
        timeout_config: NewsWorkflowConfig,
    ) -> None:
        """timeout_seconds should be read from config."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=timeout_config)

        assert summarizer._timeout_seconds == 1


class TestCallClaudeSdk:
    """Tests for _call_claude_sdk method (P9-002).

    Tests for claude-agent-sdk integration:
    - query() function usage
    - ClaudeAgentOptions configuration
    - AssistantMessage and TextBlock text extraction
    - ImportError handling for SDK not installed
    - Exception propagation from query()
    """

    @pytest.fixture
    def summarizer_config(self) -> NewsWorkflowConfig:
        """Create a config for _call_claude_sdk tests."""
        return NewsWorkflowConfig(
            version="1.0",
            status_mapping={"market": "index"},
            github_status_ids={"index": "test-id"},
            rss={"presets_file": "test.json"},  # type: ignore[arg-type]
            summarization=SummarizationConfig(
                prompt_template="Summarize: {body}",
                max_retries=3,
                timeout_seconds=60,
            ),
            github={  # type: ignore[arg-type]
                "project_number": 15,
                "project_id": "PVT_test",
                "status_field_id": "PVTSSF_test",
                "published_date_field_id": "PVTF_test",
                "repository": "owner/repo",
            },
            output={"result_dir": "data/exports"},  # type: ignore[arg-type]
        )

    @pytest.mark.asyncio
    async def test_正常系_call_claude_sdkが文字列を返す(
        self,
        summarizer_config: NewsWorkflowConfig,
    ) -> None:
        """_call_claude_sdk should return string from query()."""
        from news.summarizer import Summarizer

        # Create mock AssistantMessage and TextBlock
        mock_text_block = MagicMock()
        mock_text_block.text = "テスト要約"

        mock_message = MagicMock()
        mock_message.__class__.__name__ = "AssistantMessage"
        mock_message.content = [mock_text_block]

        # Create async generator for query()
        async def mock_query_generator(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            yield mock_message

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_generator
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = type(mock_message)
            mock_sdk.TextBlock = type(mock_text_block)

            summarizer = Summarizer(config=summarizer_config)
            result = await summarizer._call_claude_sdk("テストプロンプト")

            assert result == "テスト要約"

    @pytest.mark.asyncio
    async def test_正常系_call_claude_sdkでClaudeAgentOptionsが正しく設定される(
        self,
        summarizer_config: NewsWorkflowConfig,
    ) -> None:
        """_call_claude_sdk should configure ClaudeAgentOptions with allowed_tools=[] and max_turns=1."""
        from news.summarizer import Summarizer

        mock_text_block = MagicMock()
        mock_text_block.text = "要約"

        mock_message = MagicMock()
        mock_message.__class__.__name__ = "AssistantMessage"
        mock_message.content = [mock_text_block]

        captured_options: list[Any] = []

        async def mock_query_generator(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            if "options" in kwargs:
                captured_options.append(kwargs["options"])
            yield mock_message

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_generator
            mock_sdk.ClaudeAgentOptions = MagicMock(return_value=MagicMock())
            mock_sdk.AssistantMessage = type(mock_message)
            mock_sdk.TextBlock = type(mock_text_block)

            summarizer = Summarizer(config=summarizer_config)
            await summarizer._call_claude_sdk("テスト")

            # Verify ClaudeAgentOptions was called with correct arguments
            mock_sdk.ClaudeAgentOptions.assert_called_once_with(
                allowed_tools=[],
                max_turns=1,
            )

    @pytest.mark.asyncio
    async def test_正常系_call_claude_sdkで複数TextBlockを結合(
        self,
        summarizer_config: NewsWorkflowConfig,
    ) -> None:
        """_call_claude_sdk should concatenate text from multiple TextBlocks."""
        from news.summarizer import Summarizer

        # Create a common base class for TextBlock
        class MockTextBlock:
            def __init__(self, text: str) -> None:
                self.text = text

        class MockAssistantMessage:
            def __init__(self, content: list[MockTextBlock]) -> None:
                self.content = content

        mock_text_block1 = MockTextBlock("最初の")
        mock_text_block2 = MockTextBlock("テキスト")
        mock_message = MockAssistantMessage([mock_text_block1, mock_text_block2])

        async def mock_query_generator(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            yield mock_message

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_generator
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = MockAssistantMessage
            mock_sdk.TextBlock = MockTextBlock

            summarizer = Summarizer(config=summarizer_config)
            result = await summarizer._call_claude_sdk("テスト")

            assert result == "最初のテキスト"

    @pytest.mark.asyncio
    async def test_正常系_call_claude_sdkで複数メッセージを結合(
        self,
        summarizer_config: NewsWorkflowConfig,
    ) -> None:
        """_call_claude_sdk should concatenate text from multiple AssistantMessages."""
        from news.summarizer import Summarizer

        # Create common base classes
        class MockTextBlock:
            def __init__(self, text: str) -> None:
                self.text = text

        class MockAssistantMessage:
            def __init__(self, content: list[MockTextBlock]) -> None:
                self.content = content

        mock_text_block1 = MockTextBlock("メッセージ1")
        mock_text_block2 = MockTextBlock("メッセージ2")
        mock_message1 = MockAssistantMessage([mock_text_block1])
        mock_message2 = MockAssistantMessage([mock_text_block2])

        async def mock_query_generator(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            yield mock_message1
            yield mock_message2

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_generator
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = MockAssistantMessage
            mock_sdk.TextBlock = MockTextBlock

            summarizer = Summarizer(config=summarizer_config)
            result = await summarizer._call_claude_sdk("テスト")

            assert result == "メッセージ1メッセージ2"

    @pytest.mark.asyncio
    async def test_異常系_call_claude_sdkでSDK未インストール時RuntimeError(
        self,
        summarizer_config: NewsWorkflowConfig,
    ) -> None:
        """_call_claude_sdk should raise RuntimeError when SDK is not installed."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=summarizer_config)

        # Mock ImportError by removing claude_agent_sdk from sys.modules
        with (
            patch.dict("sys.modules", {"claude_agent_sdk": None}),
            pytest.raises(RuntimeError, match="claude-agent-sdk is not installed"),
        ):
            await summarizer._call_claude_sdk("テスト")

    @pytest.mark.asyncio
    async def test_異常系_call_claude_sdkでquery失敗時例外を伝播(
        self,
        summarizer_config: NewsWorkflowConfig,
    ) -> None:
        """_call_claude_sdk should propagate exceptions from query()."""
        from news.summarizer import Summarizer

        # Create a custom exception that is not an SDK error
        class CustomError(Exception):
            pass

        async def mock_query_with_error(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            raise CustomError("SDK Error")
            yield  # Make this an async generator

        # Create mock exception hierarchy
        class MockClaudeSDKError(Exception):
            pass

        class MockCLIConnectionError(MockClaudeSDKError):
            pass

        class MockCLINotFoundError(MockCLIConnectionError):
            pass

        class MockProcessError(MockClaudeSDKError):
            pass

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_with_error
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = MagicMock
            mock_sdk.TextBlock = MagicMock
            mock_sdk.CLINotFoundError = MockCLINotFoundError
            mock_sdk.ProcessError = MockProcessError
            mock_sdk.CLIConnectionError = MockCLIConnectionError
            mock_sdk.ClaudeSDKError = MockClaudeSDKError

            summarizer = Summarizer(config=summarizer_config)

            with pytest.raises(CustomError, match="SDK Error"):
                await summarizer._call_claude_sdk("テスト")

    @pytest.mark.asyncio
    async def test_正常系_call_claude_sdkで非AssistantMessageは無視(
        self,
        summarizer_config: NewsWorkflowConfig,
    ) -> None:
        """_call_claude_sdk should ignore non-AssistantMessage types."""
        from news.summarizer import Summarizer

        # Create different message types
        mock_text_block = MagicMock()
        mock_text_block.text = "テキスト"

        mock_assistant_message = MagicMock()
        mock_assistant_message.__class__.__name__ = "AssistantMessage"
        mock_assistant_message.content = [mock_text_block]

        mock_result_message = MagicMock()
        mock_result_message.__class__.__name__ = "ResultMessage"

        async def mock_query_generator(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            yield mock_result_message  # Should be ignored
            yield mock_assistant_message  # Should be processed

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_generator
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = type(mock_assistant_message)
            mock_sdk.TextBlock = type(mock_text_block)

            summarizer = Summarizer(config=summarizer_config)
            result = await summarizer._call_claude_sdk("テスト")

            assert result == "テキスト"

    @pytest.mark.asyncio
    async def test_正常系_call_claude_sdkで非TextBlockは無視(
        self,
        summarizer_config: NewsWorkflowConfig,
    ) -> None:
        """_call_claude_sdk should ignore non-TextBlock content."""
        from news.summarizer import Summarizer

        mock_text_block = MagicMock()
        mock_text_block.text = "テキスト"

        mock_tool_use_block = MagicMock()
        mock_tool_use_block.__class__.__name__ = "ToolUseBlock"

        mock_message = MagicMock()
        mock_message.__class__.__name__ = "AssistantMessage"
        mock_message.content = [mock_tool_use_block, mock_text_block]

        async def mock_query_generator(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            yield mock_message

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_generator
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = type(mock_message)
            mock_sdk.TextBlock = type(mock_text_block)

            summarizer = Summarizer(config=summarizer_config)
            result = await summarizer._call_claude_sdk("テスト")

            # Only TextBlock should be processed
            assert result == "テキスト"


class TestSDKErrorHandling:
    """Tests for SDK error handling (P9-004).

    Tests for:
    - CLINotFoundError handling (non-retryable)
    - ProcessError handling (retryable) with exit_code and stderr logging
    - CLIConnectionError handling (retryable)
    - ClaudeSDKError handling (retryable)
    - RuntimeError handling for SDK not installed (non-retryable)
    """

    @pytest.fixture
    def error_config(self) -> NewsWorkflowConfig:
        """Create a config for error handling tests."""
        return NewsWorkflowConfig(
            version="1.0",
            status_mapping={"market": "index"},
            github_status_ids={"index": "test-id"},
            rss={"presets_file": "test.json"},  # type: ignore[arg-type]
            summarization=SummarizationConfig(
                prompt_template="Summarize: {body}",
                max_retries=3,
                timeout_seconds=60,
            ),
            github={  # type: ignore[arg-type]
                "project_number": 15,
                "project_id": "PVT_test",
                "status_field_id": "PVTSSF_test",
                "published_date_field_id": "PVTF_test",
                "repository": "owner/repo",
            },
            output={"result_dir": "data/exports"},  # type: ignore[arg-type]
        )

    @pytest.mark.asyncio
    async def test_異常系_CLINotFoundErrorで適切なログが出力される(
        self,
        error_config: NewsWorkflowConfig,
    ) -> None:
        """CLINotFoundError should be logged with installation hint."""
        from news.summarizer import Summarizer

        # Create mock exception hierarchy that matches the real SDK
        class MockClaudeSDKError(Exception):
            pass

        class MockCLIConnectionError(MockClaudeSDKError):
            pass

        class MockCLINotFoundError(MockCLIConnectionError):
            pass

        class MockProcessError(MockClaudeSDKError):
            pass

        async def mock_query_with_cli_not_found(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            raise MockCLINotFoundError("CLI not found")
            yield  # Make this an async generator

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_with_cli_not_found
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = MagicMock
            mock_sdk.TextBlock = MagicMock
            mock_sdk.CLINotFoundError = MockCLINotFoundError
            mock_sdk.ProcessError = MockProcessError
            mock_sdk.CLIConnectionError = MockCLIConnectionError
            mock_sdk.ClaudeSDKError = MockClaudeSDKError

            summarizer = Summarizer(config=error_config)

            with (
                patch("news.summarizer.logger") as mock_logger,
                pytest.raises(MockCLINotFoundError),
            ):
                await summarizer._call_claude_sdk("テスト")

            # Verify error log was called
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "CLI not found" in call_args[0][0]
            assert "hint" in call_args[1]

    @pytest.mark.asyncio
    async def test_異常系_ProcessErrorでexit_codeとstderrがログ出力される(
        self,
        error_config: NewsWorkflowConfig,
    ) -> None:
        """ProcessError should be logged with exit_code and stderr."""
        from news.summarizer import Summarizer

        # Create mock exception hierarchy that matches the real SDK
        # ClaudeSDKError is the base
        class MockClaudeSDKError(Exception):
            pass

        class MockCLIConnectionError(MockClaudeSDKError):
            pass

        class MockCLINotFoundError(MockCLIConnectionError):
            pass

        class MockProcessError(MockClaudeSDKError):
            def __init__(self, exit_code: int, stderr: str | None) -> None:
                super().__init__(f"Process exited with code {exit_code}")
                self.exit_code = exit_code
                self.stderr = stderr

        async def mock_query_with_process_error(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            raise MockProcessError(exit_code=1, stderr="Error: API rate limit exceeded")
            yield  # Make this an async generator

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_with_process_error
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = MagicMock
            mock_sdk.TextBlock = MagicMock
            mock_sdk.CLINotFoundError = MockCLINotFoundError
            mock_sdk.ProcessError = MockProcessError
            mock_sdk.CLIConnectionError = MockCLIConnectionError
            mock_sdk.ClaudeSDKError = MockClaudeSDKError

            summarizer = Summarizer(config=error_config)

            with (
                patch("news.summarizer.logger") as mock_logger,
                pytest.raises(MockProcessError),
            ):
                await summarizer._call_claude_sdk("テスト")

            # Verify error log was called with exit_code and stderr
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "process error" in call_args[0][0].lower()
            assert call_args[1]["exit_code"] == 1
            assert "API rate limit" in call_args[1]["stderr"]

    @pytest.mark.asyncio
    async def test_異常系_CLIConnectionErrorで適切なログが出力される(
        self,
        error_config: NewsWorkflowConfig,
    ) -> None:
        """CLIConnectionError should be logged."""
        from news.summarizer import Summarizer

        # Create mock exception hierarchy that matches the real SDK
        class MockClaudeSDKError(Exception):
            pass

        class MockCLIConnectionError(MockClaudeSDKError):
            pass

        class MockCLINotFoundError(MockCLIConnectionError):
            pass

        class MockProcessError(MockClaudeSDKError):
            pass

        async def mock_query_with_connection_error(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            raise MockCLIConnectionError("Connection refused")
            yield  # Make this an async generator

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_with_connection_error
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = MagicMock
            mock_sdk.TextBlock = MagicMock
            mock_sdk.CLINotFoundError = MockCLINotFoundError
            mock_sdk.ProcessError = MockProcessError
            mock_sdk.CLIConnectionError = MockCLIConnectionError
            mock_sdk.ClaudeSDKError = MockClaudeSDKError

            summarizer = Summarizer(config=error_config)

            with (
                patch("news.summarizer.logger") as mock_logger,
                pytest.raises(MockCLIConnectionError),
            ):
                await summarizer._call_claude_sdk("テスト")

            # Verify error log was called
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "connection error" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_異常系_ClaudeSDKErrorで適切なログが出力される(
        self,
        error_config: NewsWorkflowConfig,
    ) -> None:
        """ClaudeSDKError should be logged."""
        from news.summarizer import Summarizer

        # Create mock exception hierarchy that matches the real SDK
        # ClaudeSDKError is the base, but we need a concrete subclass to test
        # the generic ClaudeSDKError handler (which catches errors not caught by specific handlers)
        class MockClaudeSDKError(Exception):
            pass

        # These need to be different classes so they don't match MockClaudeSDKError
        class MockCLIConnectionError(MockClaudeSDKError):
            pass

        class MockCLINotFoundError(MockCLIConnectionError):
            pass

        class MockProcessError(MockClaudeSDKError):
            pass

        # Create a different error that is only ClaudeSDKError (not a subclass)
        # This simulates an unknown SDK error that should be caught by the base handler
        class UnknownSDKError(MockClaudeSDKError):
            """An unknown SDK error that should be caught by ClaudeSDKError handler."""

            pass

        async def mock_query_with_sdk_error(
            *args: Any, **kwargs: Any
        ) -> "AsyncIterator[Any]":
            raise UnknownSDKError("Unknown SDK error")
            yield  # Make this an async generator

        with patch.dict("sys.modules", {"claude_agent_sdk": MagicMock()}):
            import sys

            mock_sdk = sys.modules["claude_agent_sdk"]
            mock_sdk.query = mock_query_with_sdk_error
            mock_sdk.ClaudeAgentOptions = MagicMock()
            mock_sdk.AssistantMessage = MagicMock
            mock_sdk.TextBlock = MagicMock
            mock_sdk.CLINotFoundError = MockCLINotFoundError
            mock_sdk.ProcessError = MockProcessError
            mock_sdk.CLIConnectionError = MockCLIConnectionError
            mock_sdk.ClaudeSDKError = MockClaudeSDKError

            summarizer = Summarizer(config=error_config)

            with (
                patch("news.summarizer.logger") as mock_logger,
                pytest.raises(UnknownSDKError),
            ):
                await summarizer._call_claude_sdk("テスト")

            # Verify error log was called
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "SDK error" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_異常系_RuntimeErrorでリトライせずFAILED(
        self,
        error_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """RuntimeError (SDK not installed) should return FAILED without retry."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=error_config)
        call_count = 0

        async def mock_call_claude_sdk_runtime_error(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("claude-agent-sdk is not installed")

        with patch.object(
            summarizer,
            "_call_claude_sdk",
            side_effect=mock_call_claude_sdk_runtime_error,
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.FAILED
        assert result.summary is None
        assert "not installed" in str(result.error_message)
        # Should NOT retry for RuntimeError
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_異常系_SDKエラーでリトライ後FAILED(
        self,
        error_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """SDK errors (ProcessError, CLIConnectionError) should be retried."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=error_config)
        call_count = 0

        # Create a mock exception that will be retried
        class MockProcessError(Exception):
            def __init__(self) -> None:
                super().__init__("Process error")
                self.exit_code = 1
                self.stderr = "Error"

        async def mock_call_claude_sdk_process_error(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            raise MockProcessError()

        with (
            patch.object(
                summarizer,
                "_call_claude_sdk",
                side_effect=mock_call_claude_sdk_process_error,
            ),
            patch("asyncio.sleep", return_value=None),
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.FAILED
        assert result.summary is None
        # Should retry 3 times (max_retries)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_正常系_SDKエラー後リトライで成功(
        self,
        error_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """SDK error followed by success should return SUCCESS."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=error_config)
        call_count = 0

        class MockCLIConnectionError(Exception):
            pass

        async def mock_call_claude_sdk_then_success(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise MockCLIConnectionError("Connection error")
            return '{"overview": "成功", "key_points": ["p1"], "market_impact": "影響", "related_info": null}'

        with (
            patch.object(
                summarizer,
                "_call_claude_sdk",
                side_effect=mock_call_claude_sdk_then_success,
            ),
            patch("asyncio.sleep", return_value=None),
        ):
            result = await summarizer.summarize(extracted_article_with_body)

        assert result.summarization_status == SummarizationStatus.SUCCESS
        assert result.summary is not None
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_正常系_error_typeがログに含まれる(
        self,
        error_config: NewsWorkflowConfig,
        extracted_article_with_body: ExtractedArticle,
    ) -> None:
        """Error type should be included in retry warning logs."""
        from news.summarizer import Summarizer

        summarizer = Summarizer(config=error_config)

        class MockProcessError(Exception):
            pass

        async def mock_call_claude_sdk_error(prompt: str) -> str:
            raise MockProcessError("Process error")

        with (
            patch.object(
                summarizer,
                "_call_claude_sdk",
                side_effect=mock_call_claude_sdk_error,
            ),
            patch("asyncio.sleep", return_value=None),
            patch("news.summarizer.logger") as mock_logger,
        ):
            await summarizer.summarize(extracted_article_with_body)

        # Verify warning logs include error_type
        warning_calls = mock_logger.warning.call_args_list
        assert len(warning_calls) == 3  # max_retries=3
        for call in warning_calls:
            kwargs = call[1]
            assert "error_type" in kwargs
            assert kwargs["error_type"] == "MockProcessError"
