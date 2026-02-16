"""Unit tests for BatchService.

Tests cover:
- batch_add_sources: Adds multiple sources sequentially to a notebook.
- batch_chat: Sends multiple questions sequentially to a notebook.
- workflow_research: Orchestrates add sources -> chat -> studio content.
- DI: Service receives dependent services via constructor injection.
- Error paths: empty notebook_id, empty sources/questions lists,
  partial failures.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from notebooklm.errors import ChatError, SourceAddError, StudioGenerationError
from notebooklm.services.batch import BatchService
from notebooklm.services.chat import ChatService
from notebooklm.services.source import SourceService
from notebooklm.services.studio import StudioService
from notebooklm.types import (
    BatchResult,
    ChatResponse,
    SourceInfo,
    StudioContentResult,
    WorkflowResult,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_source_service() -> MagicMock:
    """Create a mocked SourceService."""
    service = MagicMock(spec=SourceService)
    return service


@pytest.fixture
def mock_chat_service() -> MagicMock:
    """Create a mocked ChatService."""
    service = MagicMock(spec=ChatService)
    return service


@pytest.fixture
def mock_studio_service() -> MagicMock:
    """Create a mocked StudioService."""
    service = MagicMock(spec=StudioService)
    return service


@pytest.fixture
def batch_service(
    mock_source_service: MagicMock,
    mock_chat_service: MagicMock,
) -> BatchService:
    """Create a BatchService with mocked dependencies (without StudioService)."""
    return BatchService(
        source_service=mock_source_service,
        chat_service=mock_chat_service,
    )


@pytest.fixture
def batch_service_with_studio(
    mock_source_service: MagicMock,
    mock_chat_service: MagicMock,
    mock_studio_service: MagicMock,
) -> BatchService:
    """Create a BatchService with mocked dependencies (with StudioService)."""
    return BatchService(
        source_service=mock_source_service,
        chat_service=mock_chat_service,
        studio_service=mock_studio_service,
    )


# ---------------------------------------------------------------------------
# DI tests
# ---------------------------------------------------------------------------


class TestBatchServiceInit:
    """Test BatchService initialization and DI."""

    def test_正常系_SourceServiceをDIで受け取る(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
        )
        assert service._source_service is mock_source_service

    def test_正常系_ChatServiceをDIで受け取る(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
        )
        assert service._chat_service is mock_chat_service

    def test_正常系_StudioServiceをDIで受け取る(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
        mock_studio_service: MagicMock,
    ) -> None:
        service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
            studio_service=mock_studio_service,
        )
        assert service._studio_service is mock_studio_service

    def test_正常系_StudioService省略時はNone(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
        )
        assert service._studio_service is None


# ---------------------------------------------------------------------------
# batch_add_sources tests
# ---------------------------------------------------------------------------


class TestBatchAddSources:
    """Test BatchService.batch_add_sources()."""

    @pytest.mark.asyncio
    async def test_正常系_複数テキストソースを順次追加(
        self,
        batch_service: BatchService,
        mock_source_service: MagicMock,
    ) -> None:
        """Multiple text sources are added sequentially."""
        sources = [
            {"type": "text", "text": "Source 1 content", "title": "Source 1"},
            {"type": "text", "text": "Source 2 content", "title": "Source 2"},
        ]

        mock_source_service.add_text_source = AsyncMock(
            side_effect=[
                SourceInfo(source_id="src-001", title="Source 1", source_type="text"),
                SourceInfo(source_id="src-002", title="Source 2", source_type="text"),
            ]
        )

        result = await batch_service.batch_add_sources("nb-001", sources)

        assert isinstance(result, BatchResult)
        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0
        assert len(result.results) == 2

    @pytest.mark.asyncio
    async def test_正常系_URLソースを順次追加(
        self,
        batch_service: BatchService,
        mock_source_service: MagicMock,
    ) -> None:
        """URL sources are added sequentially."""
        sources = [
            {"type": "url", "url": "https://example.com/article1"},
            {"type": "url", "url": "https://example.com/article2"},
        ]

        mock_source_service.add_url_source = AsyncMock(
            side_effect=[
                SourceInfo(
                    source_id="src-001",
                    title="https://example.com/article1",
                    source_type="url",
                ),
                SourceInfo(
                    source_id="src-002",
                    title="https://example.com/article2",
                    source_type="url",
                ),
            ]
        )

        result = await batch_service.batch_add_sources("nb-001", sources)

        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_正常系_混合ソースタイプを追加(
        self,
        batch_service: BatchService,
        mock_source_service: MagicMock,
    ) -> None:
        """Mixed source types (text + url) are handled correctly."""
        sources = [
            {"type": "text", "text": "Content", "title": "Text Source"},
            {"type": "url", "url": "https://example.com/article"},
        ]

        mock_source_service.add_text_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-001", title="Text Source", source_type="text"
            ),
        )
        mock_source_service.add_url_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-002",
                title="https://example.com/article",
                source_type="url",
            ),
        )

        result = await batch_service.batch_add_sources("nb-001", sources)

        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_正常系_部分的な失敗を記録(
        self,
        batch_service: BatchService,
        mock_source_service: MagicMock,
    ) -> None:
        """Partial failures are recorded without stopping the batch."""
        sources = [
            {"type": "text", "text": "Good content", "title": "Good"},
            {"type": "text", "text": "Bad content", "title": "Bad"},
            {"type": "text", "text": "Also good", "title": "Also Good"},
        ]

        mock_source_service.add_text_source = AsyncMock(
            side_effect=[
                SourceInfo(source_id="src-001", title="Good", source_type="text"),
                SourceAddError(
                    "Failed to add text source",
                    context={"notebook_id": "nb-001"},
                ),
                SourceInfo(source_id="src-003", title="Also Good", source_type="text"),
            ]
        )

        result = await batch_service.batch_add_sources("nb-001", sources)

        assert result.total == 3
        assert result.succeeded == 2
        assert result.failed == 1

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        batch_service: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await batch_service.batch_add_sources(
                "", [{"type": "text", "text": "content"}]
            )

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        batch_service: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await batch_service.batch_add_sources(
                "   ", [{"type": "text", "text": "content"}]
            )

    @pytest.mark.asyncio
    async def test_異常系_空のソースリストでValueError(
        self,
        batch_service: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="sources must not be empty"):
            await batch_service.batch_add_sources("nb-001", [])

    @pytest.mark.asyncio
    async def test_正常系_不明なソースタイプを失敗として記録(
        self,
        batch_service: BatchService,
    ) -> None:
        """Unknown source types are recorded as failures."""
        sources = [
            {"type": "unknown", "data": "something"},
        ]

        result = await batch_service.batch_add_sources("nb-001", sources)

        assert result.total == 1
        assert result.succeeded == 0
        assert result.failed == 1
        assert "unsupported" in result.results[0]["status"].lower()

    @pytest.mark.asyncio
    async def test_正常系_結果にソース情報が含まれる(
        self,
        batch_service: BatchService,
        mock_source_service: MagicMock,
    ) -> None:
        """Each result entry contains source_id and title."""
        sources = [
            {"type": "text", "text": "Content", "title": "My Source"},
        ]

        mock_source_service.add_text_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-001", title="My Source", source_type="text"
            ),
        )

        result = await batch_service.batch_add_sources("nb-001", sources)

        assert result.results[0]["source_id"] == "src-001"
        assert result.results[0]["status"] == "success"


# ---------------------------------------------------------------------------
# batch_chat tests
# ---------------------------------------------------------------------------


class TestBatchChat:
    """Test BatchService.batch_chat()."""

    @pytest.mark.asyncio
    async def test_正常系_複数質問を順次送信(
        self,
        batch_service: BatchService,
        mock_chat_service: MagicMock,
    ) -> None:
        """Multiple questions are sent sequentially."""
        questions = ["What is AI?", "How does ML work?"]

        mock_chat_service.chat = AsyncMock(
            side_effect=[
                ChatResponse(
                    notebook_id="nb-001",
                    question="What is AI?",
                    answer="AI is...",
                    citations=[],
                    suggested_followups=[],
                ),
                ChatResponse(
                    notebook_id="nb-001",
                    question="How does ML work?",
                    answer="ML works by...",
                    citations=[],
                    suggested_followups=[],
                ),
            ]
        )

        result = await batch_service.batch_chat("nb-001", questions)

        assert isinstance(result, BatchResult)
        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0
        assert len(result.results) == 2

    @pytest.mark.asyncio
    async def test_正常系_回答テキストが結果に含まれる(
        self,
        batch_service: BatchService,
        mock_chat_service: MagicMock,
    ) -> None:
        """Answer text is included in each result entry."""
        questions = ["What is AI?"]

        mock_chat_service.chat = AsyncMock(
            return_value=ChatResponse(
                notebook_id="nb-001",
                question="What is AI?",
                answer="AI is artificial intelligence.",
                citations=[],
                suggested_followups=[],
            ),
        )

        result = await batch_service.batch_chat("nb-001", questions)

        assert result.results[0]["question"] == "What is AI?"
        assert result.results[0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_正常系_部分的な失敗を記録(
        self,
        batch_service: BatchService,
        mock_chat_service: MagicMock,
    ) -> None:
        """Partial chat failures are recorded without stopping the batch."""
        questions = ["Good question", "Bad question", "Another good question"]

        mock_chat_service.chat = AsyncMock(
            side_effect=[
                ChatResponse(
                    notebook_id="nb-001",
                    question="Good question",
                    answer="Good answer",
                    citations=[],
                    suggested_followups=[],
                ),
                ChatError(
                    "Chat interaction failed",
                    context={"notebook_id": "nb-001"},
                ),
                ChatResponse(
                    notebook_id="nb-001",
                    question="Another good question",
                    answer="Another good answer",
                    citations=[],
                    suggested_followups=[],
                ),
            ]
        )

        result = await batch_service.batch_chat("nb-001", questions)

        assert result.total == 3
        assert result.succeeded == 2
        assert result.failed == 1

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        batch_service: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await batch_service.batch_chat("", ["question"])

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        batch_service: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await batch_service.batch_chat("   ", ["question"])

    @pytest.mark.asyncio
    async def test_異常系_空の質問リストでValueError(
        self,
        batch_service: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="questions must not be empty"):
            await batch_service.batch_chat("nb-001", [])

    @pytest.mark.asyncio
    async def test_正常系_全失敗でもBatchResultを返す(
        self,
        batch_service: BatchService,
        mock_chat_service: MagicMock,
    ) -> None:
        """All failures still return a valid BatchResult."""
        questions = ["Bad Q1", "Bad Q2"]

        mock_chat_service.chat = AsyncMock(
            side_effect=[
                ChatError(
                    "Chat interaction failed",
                    context={"notebook_id": "nb-001"},
                ),
                ChatError(
                    "Chat interaction failed",
                    context={"notebook_id": "nb-001"},
                ),
            ]
        )

        result = await batch_service.batch_chat("nb-001", questions)

        assert result.total == 2
        assert result.succeeded == 0
        assert result.failed == 2


# ---------------------------------------------------------------------------
# workflow_research tests
# ---------------------------------------------------------------------------


class TestWorkflowResearch:
    """Test BatchService.workflow_research()."""

    @pytest.mark.asyncio
    async def test_正常系_全ステップ成功でcompletedを返す(
        self,
        batch_service_with_studio: BatchService,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
        mock_studio_service: MagicMock,
    ) -> None:
        """All steps succeed and status is 'completed'."""
        sources = [
            {"type": "text", "text": "Research content", "title": "Source 1"},
        ]
        questions = ["What are the key findings?"]

        mock_source_service.add_text_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-001", title="Source 1", source_type="text"
            ),
        )
        mock_chat_service.chat = AsyncMock(
            return_value=ChatResponse(
                notebook_id="nb-001",
                question="What are the key findings?",
                answer="The key findings are...",
                citations=[],
                suggested_followups=[],
            ),
        )
        mock_studio_service.generate_content = AsyncMock(
            return_value=StudioContentResult(
                notebook_id="nb-001",
                content_type="report",
                title="Research Report",
                text_content="# Research Report\n\nContent...",
                generation_time_seconds=10.0,
            ),
        )

        result = await batch_service_with_studio.workflow_research(
            notebook_id="nb-001",
            sources=sources,
            questions=questions,
        )

        assert isinstance(result, WorkflowResult)
        assert result.workflow_name == "research"
        assert result.status == "completed"
        assert result.steps_completed == 3
        assert result.steps_total == 3
        assert "notebook_id" in result.outputs
        assert result.outputs["notebook_id"] == "nb-001"
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_正常系_ソース追加失敗で部分成功(
        self,
        batch_service_with_studio: BatchService,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
        mock_studio_service: MagicMock,
    ) -> None:
        """Source addition failure results in 'partial' status."""
        sources = [
            {"type": "text", "text": "Content", "title": "Source 1"},
        ]
        questions = ["What are the key findings?"]

        mock_source_service.add_text_source = AsyncMock(
            side_effect=SourceAddError(
                "Failed to add text source",
                context={"notebook_id": "nb-001"},
            ),
        )
        mock_chat_service.chat = AsyncMock(
            return_value=ChatResponse(
                notebook_id="nb-001",
                question="What are the key findings?",
                answer="Answer...",
                citations=[],
                suggested_followups=[],
            ),
        )
        mock_studio_service.generate_content = AsyncMock(
            return_value=StudioContentResult(
                notebook_id="nb-001",
                content_type="report",
                title="Report",
                text_content="# Report",
                generation_time_seconds=5.0,
            ),
        )

        result = await batch_service_with_studio.workflow_research(
            notebook_id="nb-001",
            sources=sources,
            questions=questions,
        )

        assert result.status == "partial"
        assert result.steps_completed == 2
        assert result.steps_total == 3
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_正常系_チャット失敗で部分成功(
        self,
        batch_service_with_studio: BatchService,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
        mock_studio_service: MagicMock,
    ) -> None:
        """Chat failure results in 'partial' status."""
        sources = [
            {"type": "text", "text": "Content", "title": "Source 1"},
        ]
        questions = ["What are the key findings?"]

        mock_source_service.add_text_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-001", title="Source 1", source_type="text"
            ),
        )
        mock_chat_service.chat = AsyncMock(
            side_effect=ChatError(
                "Chat interaction failed",
                context={"notebook_id": "nb-001"},
            ),
        )
        mock_studio_service.generate_content = AsyncMock(
            return_value=StudioContentResult(
                notebook_id="nb-001",
                content_type="report",
                title="Report",
                text_content="# Report",
                generation_time_seconds=5.0,
            ),
        )

        result = await batch_service_with_studio.workflow_research(
            notebook_id="nb-001",
            sources=sources,
            questions=questions,
        )

        assert result.status == "partial"
        assert result.steps_completed == 2
        assert result.steps_total == 3
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_正常系_Studio生成失敗で部分成功(
        self,
        batch_service_with_studio: BatchService,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
        mock_studio_service: MagicMock,
    ) -> None:
        """Studio generation failure results in 'partial' status."""
        sources = [
            {"type": "text", "text": "Content", "title": "Source 1"},
        ]
        questions = ["What are the key findings?"]

        mock_source_service.add_text_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-001", title="Source 1", source_type="text"
            ),
        )
        mock_chat_service.chat = AsyncMock(
            return_value=ChatResponse(
                notebook_id="nb-001",
                question="What are the key findings?",
                answer="Answer...",
                citations=[],
                suggested_followups=[],
            ),
        )
        mock_studio_service.generate_content = AsyncMock(
            side_effect=StudioGenerationError(
                "Studio generation failed",
                context={"notebook_id": "nb-001"},
            ),
        )

        result = await batch_service_with_studio.workflow_research(
            notebook_id="nb-001",
            sources=sources,
            questions=questions,
        )

        assert result.status == "partial"
        assert result.steps_completed == 2
        assert result.steps_total == 3
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_正常系_全ステップ失敗でfailedを返す(
        self,
        batch_service_with_studio: BatchService,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
        mock_studio_service: MagicMock,
    ) -> None:
        """All steps fail and status is 'failed'."""
        sources = [
            {"type": "text", "text": "Content", "title": "Source 1"},
        ]
        questions = ["What are the key findings?"]

        mock_source_service.add_text_source = AsyncMock(
            side_effect=SourceAddError(
                "Failed",
                context={"notebook_id": "nb-001"},
            ),
        )
        mock_chat_service.chat = AsyncMock(
            side_effect=ChatError(
                "Failed",
                context={"notebook_id": "nb-001"},
            ),
        )
        mock_studio_service.generate_content = AsyncMock(
            side_effect=StudioGenerationError(
                "Failed",
                context={"notebook_id": "nb-001"},
            ),
        )

        result = await batch_service_with_studio.workflow_research(
            notebook_id="nb-001",
            sources=sources,
            questions=questions,
        )

        assert result.status == "failed"
        assert result.steps_completed == 0
        assert result.steps_total == 3
        assert len(result.errors) == 3

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        batch_service_with_studio: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await batch_service_with_studio.workflow_research(
                notebook_id="",
                sources=[{"type": "text", "text": "content"}],
                questions=["question"],
            )

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        batch_service_with_studio: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await batch_service_with_studio.workflow_research(
                notebook_id="   ",
                sources=[{"type": "text", "text": "content"}],
                questions=["question"],
            )

    @pytest.mark.asyncio
    async def test_異常系_空のソースリストでValueError(
        self,
        batch_service_with_studio: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="sources must not be empty"):
            await batch_service_with_studio.workflow_research(
                notebook_id="nb-001",
                sources=[],
                questions=["question"],
            )

    @pytest.mark.asyncio
    async def test_異常系_空の質問リストでValueError(
        self,
        batch_service_with_studio: BatchService,
    ) -> None:
        with pytest.raises(ValueError, match="questions must not be empty"):
            await batch_service_with_studio.workflow_research(
                notebook_id="nb-001",
                sources=[{"type": "text", "text": "content"}],
                questions=[],
            )

    @pytest.mark.asyncio
    async def test_異常系_StudioService未設定でValueError(
        self,
        batch_service: BatchService,
    ) -> None:
        """workflow_research requires studio_service to be set."""
        with pytest.raises(ValueError, match="studio_service is required"):
            await batch_service.workflow_research(
                notebook_id="nb-001",
                sources=[{"type": "text", "text": "content"}],
                questions=["question"],
            )

    @pytest.mark.asyncio
    async def test_正常系_content_typeを指定可能(
        self,
        batch_service_with_studio: BatchService,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
        mock_studio_service: MagicMock,
    ) -> None:
        """content_type can be specified for studio generation."""
        sources = [{"type": "text", "text": "Content", "title": "S1"}]
        questions = ["Q1"]

        mock_source_service.add_text_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-001", title="S1", source_type="text"
            ),
        )
        mock_chat_service.chat = AsyncMock(
            return_value=ChatResponse(
                notebook_id="nb-001",
                question="Q1",
                answer="A1",
                citations=[],
                suggested_followups=[],
            ),
        )
        mock_studio_service.generate_content = AsyncMock(
            return_value=StudioContentResult(
                notebook_id="nb-001",
                content_type="data_table",
                title="Data Table",
                table_data=[["A", "B"], ["1", "2"]],
                generation_time_seconds=5.0,
            ),
        )

        result = await batch_service_with_studio.workflow_research(
            notebook_id="nb-001",
            sources=sources,
            questions=questions,
            content_type="data_table",
        )

        assert result.status == "completed"
        mock_studio_service.generate_content.assert_called_once_with(
            notebook_id="nb-001",
            content_type="data_table",
        )

    @pytest.mark.asyncio
    async def test_正常系_出力にソース数とチャット数が含まれる(
        self,
        batch_service_with_studio: BatchService,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
        mock_studio_service: MagicMock,
    ) -> None:
        """Outputs contain source and chat counts."""
        sources = [
            {"type": "text", "text": "C1", "title": "S1"},
            {"type": "text", "text": "C2", "title": "S2"},
        ]
        questions = ["Q1", "Q2", "Q3"]

        mock_source_service.add_text_source = AsyncMock(
            side_effect=[
                SourceInfo(source_id="src-001", title="S1", source_type="text"),
                SourceInfo(source_id="src-002", title="S2", source_type="text"),
            ]
        )
        mock_chat_service.chat = AsyncMock(
            side_effect=[
                ChatResponse(
                    notebook_id="nb-001",
                    question=q,
                    answer=f"Answer to {q}",
                    citations=[],
                    suggested_followups=[],
                )
                for q in questions
            ]
        )
        mock_studio_service.generate_content = AsyncMock(
            return_value=StudioContentResult(
                notebook_id="nb-001",
                content_type="report",
                title="Report",
                text_content="# Report",
                generation_time_seconds=5.0,
            ),
        )

        result = await batch_service_with_studio.workflow_research(
            notebook_id="nb-001",
            sources=sources,
            questions=questions,
        )

        assert result.outputs["sources_succeeded"] == "2"
        assert result.outputs["sources_failed"] == "0"
        assert result.outputs["chat_succeeded"] == "3"
        assert result.outputs["chat_failed"] == "0"
