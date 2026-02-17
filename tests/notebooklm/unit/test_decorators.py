"""Tests for decorator utilities.

Tests for ``handle_browser_operation`` and ``mcp_tool_handler`` decorators
that standardize error handling and logging across the notebooklm package.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from notebooklm.decorators import handle_browser_operation, mcp_tool_handler
from notebooklm.errors import NotebookLMError, SourceAddError


class TestHandleBrowserOperation:
    """Tests for @handle_browser_operation decorator."""

    @pytest.mark.asyncio
    async def test_正常系_成功時にデコレート関数が正常に実行される(self) -> None:
        """Decorated function executes normally on success."""

        @handle_browser_operation()
        async def sample_operation(value: str) -> str:
            return f"processed: {value}"

        result = await sample_operation("test")
        assert result == "processed: test"

    @pytest.mark.asyncio
    async def test_正常系_ValueErrorはpass_throughされる(self) -> None:
        """ValueError is passed through without wrapping."""

        @handle_browser_operation(error_class=SourceAddError)
        async def failing_operation() -> None:
            raise ValueError("Invalid input")

        with pytest.raises(ValueError, match="Invalid input"):
            await failing_operation()

    @pytest.mark.asyncio
    async def test_正常系_NotebookLMErrorはpass_throughされる(self) -> None:
        """NotebookLMError subclasses are passed through."""

        @handle_browser_operation(error_class=SourceAddError)
        async def failing_operation() -> None:
            raise SourceAddError("Already wrapped")

        with pytest.raises(SourceAddError, match="Already wrapped"):
            await failing_operation()

    @pytest.mark.asyncio
    async def test_正常系_汎用Exceptionは指定のerror_classでラップされる(self) -> None:
        """Generic exceptions are wrapped in specified error_class."""

        @handle_browser_operation(error_class=SourceAddError)
        async def failing_operation() -> None:
            raise RuntimeError("Generic failure")

        with pytest.raises(SourceAddError) as exc_info:
            await failing_operation()

        assert "failed" in str(exc_info.value).lower()
        assert exc_info.value.__cause__.__class__.__name__ == "RuntimeError"

    @pytest.mark.asyncio
    async def test_正常系_デフォルトerror_classはNotebookLMError(self) -> None:
        """Default error_class wraps with NotebookLMError."""

        @handle_browser_operation()
        async def failing_operation() -> None:
            raise RuntimeError("Generic failure")

        with pytest.raises(NotebookLMError) as exc_info:
            await failing_operation()

        assert "failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_正常系_ラップされたエラーにcontextが含まれる(self) -> None:
        """Wrapped error includes context dictionary."""

        @handle_browser_operation(error_class=SourceAddError)
        async def failing_operation() -> None:
            raise RuntimeError("Something broke")

        with pytest.raises(SourceAddError) as exc_info:
            await failing_operation()

        assert "operation" in exc_info.value.context
        assert "error" in exc_info.value.context
        assert "error_type" in exc_info.value.context


class TestMCPToolHandler:
    """Tests for @mcp_tool_handler decorator."""

    @pytest.mark.asyncio
    async def test_正常系_進捗レポートが自動的に呼ばれる(self) -> None:
        """Progress is automatically reported at start and end."""
        ctx = MagicMock()
        ctx.report_progress = AsyncMock()

        @mcp_tool_handler("test_tool")
        async def sample_tool(ctx: MagicMock) -> dict:
            return {"result": "success"}

        result = await sample_tool(ctx=ctx)

        assert result == {"result": "success"}
        assert ctx.report_progress.call_count == 2
        ctx.report_progress.assert_any_call(0.0, 1.0)
        ctx.report_progress.assert_any_call(1.0, 1.0)

    @pytest.mark.asyncio
    async def test_正常系_ctxなしでも動作する(self) -> None:
        """Tool works even without ctx parameter."""

        @mcp_tool_handler("test_tool")
        async def sample_tool() -> dict:
            return {"result": "success"}

        result = await sample_tool()
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_正常系_ValueErrorはエラー辞書として返される(self) -> None:
        """ValueError is returned as error dict."""
        ctx = MagicMock()
        ctx.report_progress = AsyncMock()

        @mcp_tool_handler("test_tool")
        async def failing_tool(ctx: MagicMock) -> dict:
            raise ValueError("Invalid parameter")

        result = await failing_tool(ctx=ctx)

        assert result["error"] == "Invalid parameter"
        assert result["error_type"] == "ValueError"
        assert result["tool"] == "test_tool"

    @pytest.mark.asyncio
    async def test_正常系_NotebookLMErrorはエラー辞書として返される(self) -> None:
        """NotebookLMError is returned as error dict with context."""
        ctx = MagicMock()
        ctx.report_progress = AsyncMock()

        @mcp_tool_handler("test_tool")
        async def failing_tool(ctx: MagicMock) -> dict:
            raise SourceAddError("Operation failed", context={"id": "123"})

        result = await failing_tool(ctx=ctx)

        assert "Operation failed" in result["error"]
        assert result["error_type"] == "SourceAddError"
        assert result["context"]["id"] == "123"

    @pytest.mark.asyncio
    async def test_正常系_汎用Exceptionはエラー辞書として返される(self) -> None:
        """Generic exceptions are returned as error dict."""
        ctx = MagicMock()
        ctx.report_progress = AsyncMock()

        @mcp_tool_handler("test_tool")
        async def failing_tool(ctx: MagicMock) -> dict:
            raise RuntimeError("Unexpected failure")

        result = await failing_tool(ctx=ctx)

        assert "Unexpected error" in result["error"]
        assert result["error_type"] == "RuntimeError"

    @pytest.mark.asyncio
    async def test_正常系_ctxが位置引数でも検出される(self) -> None:
        """ctx is detected even when passed as positional arg."""
        ctx = MagicMock()
        ctx.report_progress = AsyncMock()

        @mcp_tool_handler("test_tool")
        async def sample_tool(context: MagicMock) -> dict:
            return {"result": "ok"}

        result = await sample_tool(ctx)
        assert result == {"result": "ok"}
        assert ctx.report_progress.call_count == 2
