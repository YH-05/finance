"""Performance tests for BatchService parallelization.

Tests verify that:
- batch_add_sources uses asyncio.gather for parallel execution.
- batch_chat uses asyncio.gather for parallel execution.
- Semaphore limits concurrent execution to max_concurrent.
- max_concurrent parameter is accepted by BatchService.__init__.
- File source type is handled in parallel batch operations.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from notebooklm.services.batch import BatchService
from notebooklm.types import SourceInfo

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_source_service() -> MagicMock:
    """Create a mocked SourceService."""
    return MagicMock()


@pytest.fixture
def mock_chat_service() -> MagicMock:
    """Create a mocked ChatService."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Parallel execution tests
# ---------------------------------------------------------------------------


class TestBatchServiceParallelization:
    """Tests for BatchService parallel execution."""

    @pytest.mark.asyncio
    async def test_正常系_batch_add_sourcesが全ソースを並列処理する(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        """Verify batch_add_sources processes all sources via asyncio.gather."""
        mock_source_service.add_text_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-001", title="Test", source_type="text"
            ),
        )

        batch_service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
            max_concurrent=5,
        )

        sources = [{"type": "text", "text": f"Text {i}"} for i in range(10)]

        result = await batch_service.batch_add_sources(
            notebook_id="test-notebook",
            sources=sources,
        )

        assert result.total == 10
        assert result.succeeded == 10
        assert result.failed == 0
        assert mock_source_service.add_text_source.call_count == 10

    @pytest.mark.asyncio
    async def test_正常系_batch_chatが全質問を並列処理する(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        """Verify batch_chat processes all questions via asyncio.gather."""
        from notebooklm.types import ChatResponse

        mock_chat_service.chat = AsyncMock(
            return_value=ChatResponse(
                notebook_id="test-notebook",
                question="Q",
                answer="A",
                citations=[],
                suggested_followups=[],
            ),
        )

        batch_service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
            max_concurrent=5,
        )

        questions = [f"Question {i}" for i in range(10)]

        result = await batch_service.batch_chat(
            notebook_id="test-notebook",
            questions=questions,
        )

        assert result.total == 10
        assert result.succeeded == 10
        assert result.failed == 0
        assert mock_chat_service.chat.call_count == 10

    @pytest.mark.asyncio
    async def test_正常系_semaphoreが並行数を制限する(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        """Verify semaphore limits concurrent execution to max_concurrent."""
        concurrent_count = 0
        max_concurrent_observed = 0

        async def mock_add_source(**kwargs: object) -> SourceInfo:
            nonlocal concurrent_count, max_concurrent_observed
            concurrent_count += 1
            max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return SourceInfo(source_id="src-001", title="Test", source_type="text")

        mock_source_service.add_text_source = mock_add_source

        batch_service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
            max_concurrent=3,
        )

        sources = [{"type": "text", "text": f"Text {i}"} for i in range(10)]

        result = await batch_service.batch_add_sources(
            notebook_id="test-notebook",
            sources=sources,
        )

        assert result.total == 10
        assert result.succeeded == 10
        assert max_concurrent_observed <= 3

    @pytest.mark.asyncio
    async def test_正常系_max_concurrent_デフォルト値が設定される(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        """Verify max_concurrent defaults to 5 when not specified."""
        batch_service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
        )

        assert batch_service._semaphore._value == 5

    @pytest.mark.asyncio
    async def test_正常系_fileタイプが並列バッチで処理される(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        """Verify file source type is handled in parallel batch."""
        mock_source_service.add_file_source = AsyncMock(
            return_value=SourceInfo(
                source_id="src-001", title="doc.pdf", source_type="file"
            ),
        )

        batch_service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
            max_concurrent=5,
        )

        sources = [
            {"type": "file", "file_path": "/path/to/doc1.pdf"},
            {"type": "file", "file_path": "/path/to/doc2.pdf"},
        ]

        result = await batch_service.batch_add_sources(
            notebook_id="test-notebook",
            sources=sources,
        )

        assert result.total == 2
        assert result.succeeded == 2
        assert mock_source_service.add_file_source.call_count == 2

    @pytest.mark.asyncio
    async def test_正常系_並列実行で部分失敗を正しく記録する(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        """Verify partial failures are correctly recorded in parallel execution."""
        call_count = 0

        async def mock_add_source(**kwargs: object) -> SourceInfo:
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise RuntimeError("Simulated failure")
            return SourceInfo(
                source_id=f"src-{call_count:03d}", title="Test", source_type="text"
            )

        mock_source_service.add_text_source = mock_add_source

        batch_service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
            max_concurrent=5,
        )

        sources = [{"type": "text", "text": f"Text {i}"} for i in range(5)]

        result = await batch_service.batch_add_sources(
            notebook_id="test-notebook",
            sources=sources,
        )

        assert result.total == 5
        assert result.succeeded == 4
        assert result.failed == 1

    @pytest.mark.asyncio
    async def test_正常系_batch_chatのsemaphoreが並行数を制限する(
        self,
        mock_source_service: MagicMock,
        mock_chat_service: MagicMock,
    ) -> None:
        """Verify semaphore limits concurrent chat execution."""
        from notebooklm.types import ChatResponse

        concurrent_count = 0
        max_concurrent_observed = 0

        async def mock_chat(**kwargs: object) -> ChatResponse:
            nonlocal concurrent_count, max_concurrent_observed
            concurrent_count += 1
            max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return ChatResponse(
                notebook_id="test-notebook",
                question=str(kwargs.get("question", "")),
                answer="Answer",
                citations=[],
                suggested_followups=[],
            )

        mock_chat_service.chat = mock_chat

        batch_service = BatchService(
            source_service=mock_source_service,
            chat_service=mock_chat_service,
            max_concurrent=2,
        )

        questions = [f"Question {i}" for i in range(8)]

        result = await batch_service.batch_chat(
            notebook_id="test-notebook",
            questions=questions,
        )

        assert result.total == 8
        assert result.succeeded == 8
        assert max_concurrent_observed <= 2
