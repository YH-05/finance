"""Unit tests for the Publisher class.

Tests for the basic Publisher class structure including:
- Constructor initialization with NewsWorkflowConfig
- publish() method signature and behavior with no summary
- publish_batch() method signature

Following TDD approach: Red -> Green -> Refactor
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from news.config.workflow import NewsWorkflowConfig, SummarizationConfig
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
    PublicationStatus,
    SourceType,
    StructuredSummary,
    SummarizationStatus,
    SummarizedArticle,
)

# Fixtures


@pytest.fixture
def sample_config() -> NewsWorkflowConfig:
    """Create a sample NewsWorkflowConfig for testing."""
    return NewsWorkflowConfig(
        version="1.0",
        status_mapping={"market": "index", "tech": "ai"},
        github_status_ids={
            "index": "test-index-id",
            "ai": "test-ai-id",
            "finance": "test-finance-id",
        },
        rss={"presets_file": "test.json"},  # type: ignore[arg-type]
        summarization=SummarizationConfig(
            prompt_template="Summarize this article in Japanese: {body}",
        ),
        github={  # type: ignore[arg-type]
            "project_number": 15,
            "project_id": "PVT_test",
            "status_field_id": "PVTSSF_test",
            "published_date_field_id": "PVTF_test",
            "repository": "YH-05/finance",
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
def sample_extracted_article(
    sample_collected_article: CollectedArticle,
) -> ExtractedArticle:
    """Create a sample ExtractedArticle with body text."""
    return ExtractedArticle(
        collected=sample_collected_article,
        body_text="Full article content about the S&P 500 rally...",
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_method="trafilatura",
    )


@pytest.fixture
def sample_summary() -> StructuredSummary:
    """Create a sample StructuredSummary."""
    return StructuredSummary(
        overview="S&P 500が上昇した。",
        key_points=["ポイント1", "ポイント2"],
        market_impact="市場への影響",
        related_info="関連情報",
    )


@pytest.fixture
def summarized_article_with_summary(
    sample_extracted_article: ExtractedArticle,
    sample_summary: StructuredSummary,
) -> SummarizedArticle:
    """Create a SummarizedArticle with summary."""
    return SummarizedArticle(
        extracted=sample_extracted_article,
        summary=sample_summary,
        summarization_status=SummarizationStatus.SUCCESS,
    )


@pytest.fixture
def summarized_article_no_summary(
    sample_extracted_article: ExtractedArticle,
) -> SummarizedArticle:
    """Create a SummarizedArticle without summary (summarization failed)."""
    return SummarizedArticle(
        extracted=sample_extracted_article,
        summary=None,
        summarization_status=SummarizationStatus.SKIPPED,
        error_message="No body text available",
    )


# Tests


class TestPublisher:
    """Tests for the Publisher class basic structure."""

    def test_正常系_コンストラクタで設定を受け取る(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Publisher should accept NewsWorkflowConfig in constructor."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        assert publisher._config is sample_config
        assert publisher._repo == sample_config.github.repository
        assert publisher._project_id == sample_config.github.project_id
        assert publisher._project_number == sample_config.github.project_number
        assert publisher._status_field_id == sample_config.github.status_field_id
        assert (
            publisher._published_date_field_id
            == sample_config.github.published_date_field_id
        )

    def test_正常系_status_mappingが設定される(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Publisher should store status_mapping from config."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        assert publisher._status_mapping == sample_config.status_mapping
        assert publisher._status_ids == sample_config.github_status_ids

    def test_正常系_publishメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Publisher should have a publish() method."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Check method exists and is callable
        assert hasattr(publisher, "publish")
        assert callable(publisher.publish)

    def test_正常系_publish_batchメソッドが存在する(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """Publisher should have a publish_batch() method."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Check method exists and is callable
        assert hasattr(publisher, "publish_batch")
        assert callable(publisher.publish_batch)


class TestPublishNoSummary:
    """Tests for publish() when article has no summary."""

    @pytest.mark.asyncio
    async def test_正常系_要約なしでSKIPPEDステータスを返す(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_no_summary: SummarizedArticle,
    ) -> None:
        """publish() should return SKIPPED status when summary is None."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        result = await publisher.publish(summarized_article_no_summary)

        assert result.publication_status == PublicationStatus.SKIPPED
        assert result.issue_number is None
        assert result.issue_url is None
        assert result.error_message == "No summary available"
        assert result.summarized is summarized_article_no_summary


class TestPublishBatch:
    """Tests for publish_batch() method."""

    @pytest.mark.asyncio
    async def test_正常系_空リストで空リストを返す(
        self, sample_config: NewsWorkflowConfig
    ) -> None:
        """publish_batch() should return empty list for empty input."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        result = await publisher.publish_batch([])

        assert result == []

    @pytest.mark.asyncio
    async def test_正常系_dry_runパラメータが受け付けられる(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_no_summary: SummarizedArticle,
    ) -> None:
        """publish_batch() should accept dry_run parameter."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Should not raise with dry_run parameter
        result = await publisher.publish_batch(
            [summarized_article_no_summary], dry_run=True
        )

        assert len(result) == 1
        # No summary -> SKIPPED regardless of dry_run
        assert result[0].publication_status == PublicationStatus.SKIPPED


class TestGenerateIssueBody:
    """Tests for _generate_issue_body() method (P5-002)."""

    def test_正常系_4セクション構造でIssue本文を生成(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_generate_issue_body should include 4 sections."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        body = publisher._generate_issue_body(summarized_article_with_summary)

        # Check all 4 sections exist
        assert "## 概要" in body
        assert "## キーポイント" in body
        assert "## 市場への影響" in body
        assert "## 関連情報" in body

    def test_正常系_メタデータが含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_generate_issue_body should include source, published date, and URL."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        body = publisher._generate_issue_body(summarized_article_with_summary)

        # Check metadata section
        assert "**ソース**:" in body
        assert "CNBC Markets" in body
        assert "**公開日**:" in body
        assert "2025-01-15 10:00" in body
        assert "**URL**:" in body
        assert "https://www.cnbc.com/article/123" in body

    def test_正常系_キーポイントがマークダウンリストで出力(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_generate_issue_body should output key_points as markdown list."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        body = publisher._generate_issue_body(summarized_article_with_summary)

        # Check key points are formatted as markdown list
        assert "- ポイント1" in body
        assert "- ポイント2" in body

    def test_正常系_関連情報なしでセクション省略(
        self,
        sample_config: NewsWorkflowConfig,
        sample_extracted_article: ExtractedArticle,
    ) -> None:
        """_generate_issue_body should omit related_info section when None."""
        from news.publisher import Publisher

        # Create summary without related_info
        summary_no_related = StructuredSummary(
            overview="S&P 500が上昇した。",
            key_points=["ポイント1", "ポイント2"],
            market_impact="市場への影響",
            related_info=None,
        )
        article = SummarizedArticle(
            extracted=sample_extracted_article,
            summary=summary_no_related,
            summarization_status=SummarizationStatus.SUCCESS,
        )

        publisher = Publisher(config=sample_config)

        body = publisher._generate_issue_body(article)

        # Related info section should not exist
        assert "## 関連情報" not in body
        # Other sections should still exist
        assert "## 概要" in body
        assert "## キーポイント" in body
        assert "## 市場への影響" in body

    def test_正常系_公開日なしで不明と表示(
        self,
        sample_config: NewsWorkflowConfig,
        sample_source: ArticleSource,
        sample_summary: StructuredSummary,
    ) -> None:
        """_generate_issue_body should show '不明' when published is None."""
        from news.publisher import Publisher

        # Create article without published date
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Market Update",
            published=None,
            source=sample_source,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        article = SummarizedArticle(
            extracted=extracted,
            summary=sample_summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )

        publisher = Publisher(config=sample_config)

        body = publisher._generate_issue_body(article)

        assert "**公開日**: 不明" in body

    def test_正常系_タイトルが本文の先頭に含まれる(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_generate_issue_body should include article title at the start."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        body = publisher._generate_issue_body(summarized_article_with_summary)

        # Title should be at the start as h1
        assert body.startswith("# Market Update: S&P 500 Rallies")


class TestGenerateIssueTitle:
    """Tests for _generate_issue_title() method (P5-002)."""

    def test_正常系_カテゴリプレフィックスが付与される(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_generate_issue_title should add category prefix from status_mapping."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        title = publisher._generate_issue_title(summarized_article_with_summary)

        # category is "market", which maps to "index"
        assert title == "[index] Market Update: S&P 500 Rallies"

    def test_正常系_マッピングにないカテゴリでotherプレフィックス(
        self,
        sample_config: NewsWorkflowConfig,
        sample_extracted_article: ExtractedArticle,
        sample_summary: StructuredSummary,
    ) -> None:
        """_generate_issue_title should use 'other' for unknown categories."""
        from news.publisher import Publisher

        # Create article with unknown category
        unknown_source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="Unknown Source",
            category="unknown_category",
        )
        collected = CollectedArticle(
            url="https://example.com/article",  # type: ignore[arg-type]
            title="Unknown Article",
            source=unknown_source,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        article = SummarizedArticle(
            extracted=extracted,
            summary=sample_summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )

        publisher = Publisher(config=sample_config)

        title = publisher._generate_issue_title(article)

        assert title == "[other] Unknown Article"

    def test_正常系_techカテゴリでaiプレフィックス(
        self,
        sample_config: NewsWorkflowConfig,
        sample_extracted_article: ExtractedArticle,
        sample_summary: StructuredSummary,
    ) -> None:
        """_generate_issue_title should map 'tech' category to 'ai' prefix."""
        from news.publisher import Publisher

        # Create article with tech category
        tech_source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="Tech News",
            category="tech",
        )
        collected = CollectedArticle(
            url="https://example.com/tech-article",  # type: ignore[arg-type]
            title="AI Breakthrough",
            source=tech_source,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        article = SummarizedArticle(
            extracted=extracted,
            summary=sample_summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )

        publisher = Publisher(config=sample_config)

        title = publisher._generate_issue_title(article)

        assert title == "[ai] AI Breakthrough"


class TestResolveStatus:
    """Tests for _resolve_status() method (P5-003)."""

    def test_正常系_カテゴリからStatusを解決(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_resolve_status should resolve category to status name and ID."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # category is "market", which maps to "index"
        status_name, status_id = publisher._resolve_status(
            summarized_article_with_summary
        )

        assert status_name == "index"
        assert status_id == "test-index-id"

    def test_正常系_techカテゴリでaiステータス(
        self,
        sample_config: NewsWorkflowConfig,
        sample_extracted_article: ExtractedArticle,
        sample_summary: StructuredSummary,
    ) -> None:
        """_resolve_status should map 'tech' category to 'ai' status."""
        from news.publisher import Publisher

        # Create article with tech category
        tech_source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="Tech News",
            category="tech",
        )
        collected = CollectedArticle(
            url="https://example.com/tech-article",  # type: ignore[arg-type]
            title="AI Breakthrough",
            source=tech_source,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        article = SummarizedArticle(
            extracted=extracted,
            summary=sample_summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )

        publisher = Publisher(config=sample_config)

        status_name, status_id = publisher._resolve_status(article)

        assert status_name == "ai"
        assert status_id == "test-ai-id"

    def test_正常系_未知のカテゴリでfinanceフォールバック(
        self,
        sample_extracted_article: ExtractedArticle,
        sample_summary: StructuredSummary,
    ) -> None:
        """_resolve_status should fallback to 'finance' for unknown categories."""
        from news.publisher import Publisher

        # Config with finance fallback
        config_with_finance = NewsWorkflowConfig(
            version="1.0",
            status_mapping={"market": "index", "tech": "ai"},
            github_status_ids={
                "index": "test-index-id",
                "ai": "test-ai-id",
                "finance": "test-finance-id",
            },
            rss={"presets_file": "test.json"},  # type: ignore[arg-type]
            summarization=SummarizationConfig(
                prompt_template="Summarize this article in Japanese: {body}",
            ),
            github={  # type: ignore[arg-type]
                "project_number": 15,
                "project_id": "PVT_test",
                "status_field_id": "PVTSSF_test",
                "published_date_field_id": "PVTF_test",
                "repository": "YH-05/finance",
            },
            output={"result_dir": "data/exports"},  # type: ignore[arg-type]
        )

        # Create article with unknown category
        unknown_source = ArticleSource(
            source_type=SourceType.RSS,
            source_name="Unknown Source",
            category="unknown_category",
        )
        collected = CollectedArticle(
            url="https://example.com/article",  # type: ignore[arg-type]
            title="Unknown Article",
            source=unknown_source,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        article = SummarizedArticle(
            extracted=extracted,
            summary=sample_summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )

        publisher = Publisher(config=config_with_finance)

        status_name, status_id = publisher._resolve_status(article)

        # Should fallback to "finance"
        assert status_name == "finance"
        assert status_id == "test-finance-id"

    def test_正常系_戻り値がタプル(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_resolve_status should return a tuple of (status_name, status_id)."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        result = publisher._resolve_status(summarized_article_with_summary)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)


class TestCreateIssue:
    """Tests for _create_issue() method (P5-004)."""

    @pytest.mark.asyncio
    async def test_正常系_Issue作成でIssue番号とURLを返す(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_create_issue should return issue number and URL on success."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Mock subprocess.run for gh issue create
        with patch("news.publisher.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "https://github.com/YH-05/finance/issues/123\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            issue_number, issue_url = await publisher._create_issue(
                summarized_article_with_summary
            )

            assert issue_number == 123
            assert issue_url == "https://github.com/YH-05/finance/issues/123"

    @pytest.mark.asyncio
    async def test_正常系_ghコマンドに正しい引数を渡す(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_create_issue should call gh with correct arguments."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Mock subprocess.run
        with patch("news.publisher.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "https://github.com/YH-05/finance/issues/123\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            await publisher._create_issue(summarized_article_with_summary)

            # Verify the call was made
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]

            assert call_args[0] == "gh"
            assert call_args[1] == "issue"
            assert call_args[2] == "create"
            assert "--repo" in call_args
            assert "YH-05/finance" in call_args
            assert "--title" in call_args
            assert "--body" in call_args


class TestAddToProject:
    """Tests for _add_to_project() method (P5-004)."""

    @pytest.mark.asyncio
    async def test_正常系_Projectに追加してフィールドを設定(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_add_to_project should add issue and set fields."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Mock subprocess.run
        with patch("news.publisher.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "PVTI_test_item_id\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            await publisher._add_to_project(123, summarized_article_with_summary)

            # Should be called 3 times: item-add, item-edit (status), item-edit (date)
            assert mock_run.call_count == 3

    @pytest.mark.asyncio
    async def test_正常系_item_addで正しい引数を渡す(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_add_to_project should call gh project item-add correctly."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        with patch("news.publisher.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "PVTI_test_item_id\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            await publisher._add_to_project(123, summarized_article_with_summary)

            # Check first call (item-add)
            first_call_args = mock_run.call_args_list[0][0][0]
            assert first_call_args[0] == "gh"
            assert first_call_args[1] == "project"
            assert first_call_args[2] == "item-add"
            assert "15" in first_call_args  # project_number
            assert "--owner" in first_call_args
            assert "YH-05" in first_call_args
            assert "--url" in first_call_args
            assert "https://github.com/YH-05/finance/issues/123" in first_call_args

    @pytest.mark.asyncio
    async def test_正常系_Statusフィールドを設定(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_add_to_project should set Status field."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        with patch("news.publisher.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "PVTI_test_item_id\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            await publisher._add_to_project(123, summarized_article_with_summary)

            # Check second call (status field edit)
            second_call_args = mock_run.call_args_list[1][0][0]
            assert second_call_args[0] == "gh"
            assert second_call_args[1] == "project"
            assert second_call_args[2] == "item-edit"
            assert "--project-id" in second_call_args
            assert "PVT_test" in second_call_args
            assert "--id" in second_call_args
            assert "PVTI_test_item_id" in second_call_args
            assert "--field-id" in second_call_args
            assert "PVTSSF_test" in second_call_args
            assert "--single-select-option-id" in second_call_args

    @pytest.mark.asyncio
    async def test_正常系_PublishedDateフィールドを設定(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """_add_to_project should set PublishedDate field."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        with patch("news.publisher.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "PVTI_test_item_id\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            await publisher._add_to_project(123, summarized_article_with_summary)

            # Check third call (date field edit)
            third_call_args = mock_run.call_args_list[2][0][0]
            assert third_call_args[0] == "gh"
            assert third_call_args[1] == "project"
            assert third_call_args[2] == "item-edit"
            assert "--project-id" in third_call_args
            assert "--id" in third_call_args
            assert "--field-id" in third_call_args
            assert "PVTF_test" in third_call_args  # published_date_field_id
            assert "--date" in third_call_args
            assert "2025-01-15" in third_call_args  # ISO format date

    @pytest.mark.asyncio
    async def test_正常系_公開日なしでDateフィールドをスキップ(
        self,
        sample_config: NewsWorkflowConfig,
        sample_source: ArticleSource,
        sample_summary: StructuredSummary,
    ) -> None:
        """_add_to_project should skip date field when published is None."""
        from news.publisher import Publisher

        # Create article without published date
        collected = CollectedArticle(
            url="https://www.cnbc.com/article/123",  # type: ignore[arg-type]
            title="Market Update",
            published=None,
            source=sample_source,
            collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        extracted = ExtractedArticle(
            collected=collected,
            body_text="Content",
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="trafilatura",
        )
        article_no_date = SummarizedArticle(
            extracted=extracted,
            summary=sample_summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )

        publisher = Publisher(config=sample_config)

        with patch("news.publisher.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "PVTI_test_item_id\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            await publisher._add_to_project(123, article_no_date)

            # Should be called only 2 times: item-add, item-edit (status only)
            assert mock_run.call_count == 2


class TestPublishWithIssueCreation:
    """Tests for publish() method with Issue creation (P5-004)."""

    @pytest.mark.asyncio
    async def test_正常系_要約ありでIssue作成成功(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """publish() should create Issue and return SUCCESS status."""
        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Mock subprocess.run for all gh commands
        with patch("news.publisher.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "https://github.com/YH-05/finance/issues/456\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Mock _add_to_project to avoid complex mocking
            with patch.object(publisher, "_add_to_project"):
                result = await publisher.publish(summarized_article_with_summary)

            assert result.publication_status == PublicationStatus.SUCCESS
            assert result.issue_number == 456
            assert result.issue_url == "https://github.com/YH-05/finance/issues/456"
            assert result.summarized is summarized_article_with_summary

    @pytest.mark.asyncio
    async def test_異常系_Issue作成失敗でFAILEDステータス(
        self,
        sample_config: NewsWorkflowConfig,
        summarized_article_with_summary: SummarizedArticle,
    ) -> None:
        """publish() should return FAILED status when Issue creation fails."""
        import subprocess

        from news.publisher import Publisher

        publisher = Publisher(config=sample_config)

        # Mock subprocess.run to raise CalledProcessError
        with patch("news.publisher.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "gh", stderr="Error creating issue"
            )

            result = await publisher.publish(summarized_article_with_summary)

            assert result.publication_status == PublicationStatus.FAILED
            assert result.issue_number is None
            assert result.issue_url is None
            assert result.error_message is not None
