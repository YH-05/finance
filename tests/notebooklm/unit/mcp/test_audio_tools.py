"""Unit tests for NotebookLM MCP audio tools.

Tests cover:
- notebooklm_generate_audio_overview: Success, validation error, NotebookLMError.
- Progress reporting via ctx.report_progress().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.errors import BrowserTimeoutError, SessionExpiredError
from notebooklm.types import AudioOverviewResult


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create a mocked FastMCP Context with lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"browser_manager": MagicMock()}
    ctx.report_progress = AsyncMock(return_value=None)
    return ctx


# ---------------------------------------------------------------------------
# notebooklm_generate_audio_overview tests
# ---------------------------------------------------------------------------


class TestGenerateAudioOverview:
    """Tests for notebooklm_generate_audio_overview tool."""

    @pytest.mark.asyncio
    async def test_正常系_AudioOverviewResultをdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にAudioOverviewResultをdict形式で返すこと。"""
        expected_result = AudioOverviewResult(
            notebook_id="abc-123",
            status="completed",
            generation_time_seconds=45.0,
        )

        with patch("notebooklm.mcp.tools.audio_tools.AudioService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_audio_overview = AsyncMock(
                return_value=expected_result,
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_audio_overview"]
            result = await tool.fn(
                notebook_id="abc-123",
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "abc-123"
        assert result["status"] == "completed"
        assert result["generation_time_seconds"] == 45.0

    @pytest.mark.asyncio
    async def test_正常系_カスタマイズプロンプト付きで生成(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """カスタマイズプロンプト付きで生成成功すること。"""
        expected_result = AudioOverviewResult(
            notebook_id="abc-123",
            status="completed",
            generation_time_seconds=50.0,
        )

        with patch("notebooklm.mcp.tools.audio_tools.AudioService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_audio_overview = AsyncMock(
                return_value=expected_result,
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_audio_overview"]
            result = await tool.fn(
                notebook_id="abc-123",
                ctx=mock_ctx,
                customize_prompt="Focus on technical details",
            )

        assert result["status"] == "completed"
        mock_service.generate_audio_overview.assert_awaited_once_with(
            "abc-123",
            customize_prompt="Focus on technical details",
        )

    @pytest.mark.asyncio
    async def test_正常系_進捗報告が呼ばれる(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """ctx.report_progress()が呼ばれること。"""
        expected_result = AudioOverviewResult(
            notebook_id="abc-123",
            status="completed",
            generation_time_seconds=30.0,
        )

        with patch("notebooklm.mcp.tools.audio_tools.AudioService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_audio_overview = AsyncMock(
                return_value=expected_result,
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_audio_overview"]
            await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        # report_progress should be called at least once
        assert mock_ctx.report_progress.await_count >= 1

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空のnotebook_idでValueErrorのエラーdictを返すこと。"""
        with patch("notebooklm.mcp.tools.audio_tools.AudioService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_audio_overview = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_audio_overview"]
            result = await tool.fn(notebook_id="", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_BrowserTimeoutErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """BrowserTimeoutError発生時にエラーdictを返すこと。"""
        with patch("notebooklm.mcp.tools.audio_tools.AudioService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_audio_overview = AsyncMock(
                side_effect=BrowserTimeoutError(
                    "Audio generation timed out",
                    context={"notebook_id": "abc-123", "timeout_ms": 600000},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_audio_overview"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "BrowserTimeoutError"
        assert result["context"]["notebook_id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_異常系_SessionExpiredErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """SessionExpiredError発生時にエラーdictを返すこと。"""
        with patch("notebooklm.mcp.tools.audio_tools.AudioService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_audio_overview = AsyncMock(
                side_effect=SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".notebooklm-session.json"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_audio_overview"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "SessionExpiredError"
