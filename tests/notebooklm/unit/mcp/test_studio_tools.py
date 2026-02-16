"""Unit tests for NotebookLM MCP Studio tools.

Tests cover:
- notebooklm_generate_studio_content: Success for all 4 content types
  (report, infographic, slides, data_table).
- Report with optional report_format parameter.
- Validation error handling (empty notebook_id).
- NotebookLMError (StudioGenerationError) handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.errors import StudioGenerationError
from notebooklm.types import StudioContentResult


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create a mocked FastMCP Context with lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"browser_manager": MagicMock()}
    return ctx


class TestGenerateStudioContentReport:
    """Tests for notebooklm_generate_studio_content with report type."""

    @pytest.mark.asyncio
    async def test_正常系_レポートを生成してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にレポートを生成し、dict形式で結果を返すこと。"""
        expected_result = StudioContentResult(
            notebook_id="abc-123",
            content_type="report",
            title="AI Research Overview",
            text_content="# AI Research Overview\n\nContent here...",
            generation_time_seconds=15.0,
        )

        with patch(
            "notebooklm.mcp.tools.studio_tools.StudioService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_content = AsyncMock(return_value=expected_result)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_studio_content"]
            result = await tool.fn(
                notebook_id="abc-123",
                content_type="report",
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "abc-123"
        assert result["content_type"] == "report"
        assert result["title"] == "AI Research Overview"
        assert result["text_content"] is not None
        assert result["generation_time_seconds"] == 15.0

    @pytest.mark.asyncio
    async def test_正常系_レポートフォーマット指定でdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """レポートフォーマット（briefing_doc）指定で正常に生成すること。"""
        expected_result = StudioContentResult(
            notebook_id="abc-123",
            content_type="report",
            title="Briefing Document",
            text_content="# Briefing Document\n\nSummary...",
            generation_time_seconds=12.5,
        )

        with patch(
            "notebooklm.mcp.tools.studio_tools.StudioService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_content = AsyncMock(return_value=expected_result)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_studio_content"]
            result = await tool.fn(
                notebook_id="abc-123",
                content_type="report",
                ctx=mock_ctx,
                report_format="briefing_doc",
            )

        assert result["content_type"] == "report"
        assert result["title"] == "Briefing Document"

        # Verify the service was called with report_format
        mock_service.generate_content.assert_awaited_once_with(
            "abc-123",
            "report",
            report_format="briefing_doc",
        )


class TestGenerateStudioContentInfographic:
    """Tests for notebooklm_generate_studio_content with infographic type."""

    @pytest.mark.asyncio
    async def test_正常系_インフォグラフィックを生成してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にインフォグラフィックを生成すること。"""
        expected_result = StudioContentResult(
            notebook_id="nb-001",
            content_type="infographic",
            title="Infographic",
            generation_time_seconds=20.0,
        )

        with patch(
            "notebooklm.mcp.tools.studio_tools.StudioService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_content = AsyncMock(return_value=expected_result)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_studio_content"]
            result = await tool.fn(
                notebook_id="nb-001",
                content_type="infographic",
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "nb-001"
        assert result["content_type"] == "infographic"
        assert result["text_content"] is None


class TestGenerateStudioContentSlides:
    """Tests for notebooklm_generate_studio_content with slides type."""

    @pytest.mark.asyncio
    async def test_正常系_スライドを生成してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にスライドを生成すること。"""
        expected_result = StudioContentResult(
            notebook_id="nb-002",
            content_type="slides",
            title="Slides",
            generation_time_seconds=18.0,
        )

        with patch(
            "notebooklm.mcp.tools.studio_tools.StudioService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_content = AsyncMock(return_value=expected_result)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_studio_content"]
            result = await tool.fn(
                notebook_id="nb-002",
                content_type="slides",
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "nb-002"
        assert result["content_type"] == "slides"


class TestGenerateStudioContentDataTable:
    """Tests for notebooklm_generate_studio_content with data_table type."""

    @pytest.mark.asyncio
    async def test_正常系_DataTableを生成してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にDataTableを生成し、table_dataが含まれること。"""
        expected_result = StudioContentResult(
            notebook_id="nb-003",
            content_type="data_table",
            title="Data Table",
            table_data=[["Header1", "Header2"], ["Value1", "Value2"]],
            generation_time_seconds=10.0,
        )

        with patch(
            "notebooklm.mcp.tools.studio_tools.StudioService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_content = AsyncMock(return_value=expected_result)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_studio_content"]
            result = await tool.fn(
                notebook_id="nb-003",
                content_type="data_table",
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "nb-003"
        assert result["content_type"] == "data_table"
        assert result["table_data"] is not None
        assert len(result["table_data"]) == 2
        assert result["table_data"][0] == ["Header1", "Header2"]


class TestGenerateStudioContentErrors:
    """Tests for error handling in notebooklm_generate_studio_content."""

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.studio_tools.StudioService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_content = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_studio_content"]
            result = await tool.fn(
                notebook_id="",
                content_type="report",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_StudioGenerationErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """StudioGenerationError 発生時にエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.studio_tools.StudioService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.generate_content = AsyncMock(
                side_effect=StudioGenerationError(
                    "Generation timed out",
                    context={
                        "content_type": "report",
                        "notebook_id": "abc-123",
                    },
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_generate_studio_content"]
            result = await tool.fn(
                notebook_id="abc-123",
                content_type="report",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "StudioGenerationError"
        assert result["context"]["content_type"] == "report"
