"""Unit tests for BatchService.

Tests cover:
- batch_add_sources: Adds multiple sources sequentially to a notebook.
- batch_chat: Sends multiple questions sequentially to a notebook.
- DI: Service receives dependent services via constructor injection.
- Error paths: empty notebook_id, empty sources/questions lists,
  partial failures.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from notebooklm.errors import ChatError, SourceAddError
from notebooklm.services.batch import BatchService
from notebooklm.services.chat import ChatService
from notebooklm.services.source import SourceService
from notebooklm.types import BatchResult, ChatResponse, SourceInfo

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
def batch_service(
    mock_source_service: MagicMock,
    mock_chat_service: MagicMock,
) -> BatchService:
    """Create a BatchService with mocked dependencies."""
    return BatchService(
        source_service=mock_source_service,
        chat_service=mock_chat_service,
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
