"""Integration tests for the NotebookLM notebook workflow.

Tests verify the end-to-end workflow of creating a notebook, adding sources,
listing sources, and retrieving summaries through the MCP tool layer.

All tests are marked with ``@pytest.mark.playwright`` since the underlying
services use Playwright browser automation. In these integration tests,
the services are mocked to validate the coordination between MCP tools
and services without requiring a real browser.

Notes
-----
These tests are marked with ``@pytest.mark.playwright`` and require:

- Playwright to be installed: ``uv add playwright && playwright install chromium``
- CI runs should install Playwright before running these tests

Tests will be skipped automatically if:

- Playwright is not installed
- Chromium browser is not installed
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.errors import (
    ElementNotFoundError,
    SessionExpiredError,
    SourceAddError,
)
from notebooklm.types import NotebookInfo, NotebookSummary, SourceInfo


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create a mocked FastMCP Context with lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"browser_manager": MagicMock()}
    ctx.report_progress = AsyncMock()
    return ctx


@pytest.mark.integration
@pytest.mark.playwright
class TestNotebookWorkflow:
    """Integration tests for the full notebook lifecycle workflow.

    Tests the sequence: create notebook -> add source -> list sources
    -> get notebook summary, verifying that all MCP tools work together
    correctly through the service layer.
    """

    @pytest.mark.asyncio
    async def test_正常系_ノートブック作成からソース追加までの完全ワークフロー(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """ノートブック作成 -> ソース追加 -> ソース一覧の完全ワークフロー。"""
        notebook = NotebookInfo(
            notebook_id="wf-nb-001",
            title="Workflow Test Notebook",
            source_count=0,
        )
        source = SourceInfo(
            source_id="src-wf-001",
            title="Workflow Test Source",
            source_type="text",
        )
        sources_after_add = [source]

        with (
            patch(
                "notebooklm.mcp.tools.notebook_tools.NotebookService"
            ) as mock_nb_svc_cls,
            patch(
                "notebooklm.mcp.tools.source_tools.SourceService"
            ) as mock_src_svc_cls,
        ):
            mock_nb_svc = mock_nb_svc_cls.return_value
            mock_nb_svc.create_notebook = AsyncMock(return_value=notebook)

            mock_src_svc = mock_src_svc_cls.return_value
            mock_src_svc.add_text_source = AsyncMock(return_value=source)
            mock_src_svc.list_sources = AsyncMock(return_value=sources_after_add)

            from notebooklm.mcp.server import mcp

            # Step 1: Create notebook
            create_tool = mcp._tool_manager._tools["notebooklm_create_notebook"]
            create_result = await create_tool.fn(
                title="Workflow Test Notebook",
                ctx=mock_ctx,
            )

            assert create_result["notebook_id"] == "wf-nb-001"
            assert create_result["title"] == "Workflow Test Notebook"
            assert create_result["source_count"] == 0

            created_notebook_id = create_result["notebook_id"]

            # Step 2: Add text source
            add_source_tool = mcp._tool_manager._tools["notebooklm_add_text_source"]
            add_result = await add_source_tool.fn(
                notebook_id=created_notebook_id,
                text="This is research content for workflow testing.",
                ctx=mock_ctx,
                title="Workflow Test Source",
            )

            assert add_result["source_id"] == "src-wf-001"
            assert add_result["source_type"] == "text"

            # Step 3: List sources to verify the source was added
            list_sources_tool = mcp._tool_manager._tools["notebooklm_list_sources"]
            list_result = await list_sources_tool.fn(
                notebook_id=created_notebook_id,
                ctx=mock_ctx,
            )

            assert list_result["total"] == 1
            assert list_result["notebook_id"] == created_notebook_id
            assert list_result["sources"][0]["title"] == "Workflow Test Source"

    @pytest.mark.asyncio
    async def test_正常系_ノートブック一覧と概要取得ワークフロー(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """ノートブック一覧取得 -> 概要取得のワークフロー。"""
        notebooks = [
            NotebookInfo(
                notebook_id="wf-nb-010",
                title="Research Notebook",
                source_count=5,
            ),
            NotebookInfo(
                notebook_id="wf-nb-020",
                title="Analysis Notebook",
                source_count=3,
            ),
        ]
        summary = NotebookSummary(
            notebook_id="wf-nb-010",
            summary_text="This notebook covers AI research findings...",
            suggested_questions=[
                "What are the key findings?",
                "How does this compare to prior research?",
            ],
        )

        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_nb_svc_cls:
            mock_nb_svc = mock_nb_svc_cls.return_value
            mock_nb_svc.list_notebooks = AsyncMock(return_value=notebooks)
            mock_nb_svc.get_notebook_summary = AsyncMock(return_value=summary)

            from notebooklm.mcp.server import mcp

            # Step 1: List notebooks
            list_tool = mcp._tool_manager._tools["notebooklm_list_notebooks"]
            list_result = await list_tool.fn(ctx=mock_ctx)

            assert list_result["total"] == 2
            first_notebook_id = list_result["notebooks"][0]["notebook_id"]
            assert first_notebook_id == "wf-nb-010"

            # Step 2: Get summary for the first notebook
            summary_tool = mcp._tool_manager._tools["notebooklm_get_notebook_summary"]
            summary_result = await summary_tool.fn(
                notebook_id=first_notebook_id,
                ctx=mock_ctx,
            )

            assert summary_result["notebook_id"] == first_notebook_id
            assert "AI research" in summary_result["summary_text"]
            assert len(summary_result["suggested_questions"]) == 2

    @pytest.mark.asyncio
    async def test_異常系_セッション期限切れ時にワークフロー全体がエラー返却(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """セッション期限切れ時、各ステップでエラーが返却されること。"""
        session_error = SessionExpiredError(
            "Session expired, re-authentication required",
            context={
                "session_file": ".notebooklm-session.json",
                "last_used": "2026-02-15T10:00:00Z",
            },
        )

        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_nb_svc_cls:
            mock_nb_svc = mock_nb_svc_cls.return_value
            mock_nb_svc.create_notebook = AsyncMock(side_effect=session_error)
            mock_nb_svc.list_notebooks = AsyncMock(side_effect=session_error)

            from notebooklm.mcp.server import mcp

            # Create should fail
            create_tool = mcp._tool_manager._tools["notebooklm_create_notebook"]
            create_result = await create_tool.fn(
                title="Test Notebook",
                ctx=mock_ctx,
            )

            assert "error" in create_result
            assert create_result["error_type"] == "SessionExpiredError"

            # List should also fail
            list_tool = mcp._tool_manager._tools["notebooklm_list_notebooks"]
            list_result = await list_tool.fn(ctx=mock_ctx)

            assert "error" in list_result
            assert list_result["error_type"] == "SessionExpiredError"

    @pytest.mark.asyncio
    async def test_異常系_ソース追加失敗時にノートブック作成は成功済み(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """ノートブック作成成功後、ソース追加で失敗するケース。"""
        notebook = NotebookInfo(
            notebook_id="wf-nb-fail",
            title="Partial Success Notebook",
            source_count=0,
        )
        source_error = SourceAddError(
            "Failed to add text source: dialog not found",
            context={
                "notebook_id": "wf-nb-fail",
                "source_type": "text",
                "text_length": 50,
            },
        )

        with (
            patch(
                "notebooklm.mcp.tools.notebook_tools.NotebookService"
            ) as mock_nb_svc_cls,
            patch(
                "notebooklm.mcp.tools.source_tools.SourceService"
            ) as mock_src_svc_cls,
        ):
            mock_nb_svc = mock_nb_svc_cls.return_value
            mock_nb_svc.create_notebook = AsyncMock(return_value=notebook)

            mock_src_svc = mock_src_svc_cls.return_value
            mock_src_svc.add_text_source = AsyncMock(side_effect=source_error)

            from notebooklm.mcp.server import mcp

            # Step 1: Create notebook succeeds
            create_tool = mcp._tool_manager._tools["notebooklm_create_notebook"]
            create_result = await create_tool.fn(
                title="Partial Success Notebook",
                ctx=mock_ctx,
            )

            assert create_result["notebook_id"] == "wf-nb-fail"
            assert "error" not in create_result

            # Step 2: Add source fails
            add_tool = mcp._tool_manager._tools["notebooklm_add_text_source"]
            add_result = await add_tool.fn(
                notebook_id="wf-nb-fail",
                text="Some text content to add as source.",
                ctx=mock_ctx,
            )

            assert "error" in add_result
            assert add_result["error_type"] == "SourceAddError"
            assert add_result["context"]["notebook_id"] == "wf-nb-fail"

    @pytest.mark.asyncio
    async def test_正常系_複数ソース追加ワークフロー(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """複数のソースを順番に追加するワークフロー。"""
        source_1 = SourceInfo(
            source_id="src-multi-001",
            title="First Source",
            source_type="text",
        )
        source_2 = SourceInfo(
            source_id="src-multi-002",
            title="Second Source",
            source_type="text",
        )
        all_sources = [source_1, source_2]

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_src_svc_cls:
            mock_src_svc = mock_src_svc_cls.return_value
            mock_src_svc.add_text_source = AsyncMock(
                side_effect=[source_1, source_2],
            )
            mock_src_svc.list_sources = AsyncMock(return_value=all_sources)

            from notebooklm.mcp.server import mcp

            add_tool = mcp._tool_manager._tools["notebooklm_add_text_source"]

            # Add first source
            result_1 = await add_tool.fn(
                notebook_id="nb-multi",
                text="First research note...",
                ctx=mock_ctx,
                title="First Source",
            )
            assert result_1["source_id"] == "src-multi-001"

            # Add second source
            result_2 = await add_tool.fn(
                notebook_id="nb-multi",
                text="Second research note...",
                ctx=mock_ctx,
                title="Second Source",
            )
            assert result_2["source_id"] == "src-multi-002"

            # Verify both sources exist
            list_tool = mcp._tool_manager._tools["notebooklm_list_sources"]
            list_result = await list_tool.fn(
                notebook_id="nb-multi",
                ctx=mock_ctx,
            )

            assert list_result["total"] == 2
            source_ids = [s["source_id"] for s in list_result["sources"]]
            assert "src-multi-001" in source_ids
            assert "src-multi-002" in source_ids


@pytest.mark.integration
@pytest.mark.playwright
class TestLifespanIntegration:
    """Integration tests for server lifespan and browser manager coordination."""

    @pytest.mark.asyncio
    async def test_正常系_lifespanコンテキストからサービス初期化まで(
        self,
    ) -> None:
        """lifespan から browser_manager 取得 -> サービス初期化の連携を検証。"""
        from notebooklm.mcp.server import notebooklm_lifespan
        from notebooklm.services.notebook import NotebookService
        from notebooklm.services.source import SourceService

        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.close = AsyncMock()
        mock_manager.headless = True
        mock_manager.has_session = MagicMock(return_value=True)

        with patch(
            "notebooklm.browser.manager.NotebookLMBrowserManager",
            return_value=mock_manager,
        ):
            async with notebooklm_lifespan(None) as context:
                browser_manager = context["browser_manager"]

                # Verify services can be instantiated with the browser manager
                notebook_service = NotebookService(browser_manager)
                source_service = SourceService(browser_manager)

                assert notebook_service._browser_manager is browser_manager
                assert source_service._browser_manager is browser_manager

        # Verify cleanup
        mock_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_異常系_lifespan中のエラーでもクリーンアップ実行(
        self,
    ) -> None:
        """lifespan 中にエラーが発生してもブラウザマネージャーがクリーンアップされること。"""
        from notebooklm.mcp.server import notebooklm_lifespan

        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.close = AsyncMock()
        mock_manager.headless = True
        mock_manager.has_session = MagicMock(return_value=False)

        with (
            patch(
                "notebooklm.browser.manager.NotebookLMBrowserManager",
                return_value=mock_manager,
            ),
            pytest.raises(RuntimeError, match="workflow error"),
        ):
            async with notebooklm_lifespan(None):
                raise RuntimeError("workflow error")

        mock_manager.close.assert_called_once()


@pytest.mark.integration
@pytest.mark.playwright
class TestToolErrorPropagation:
    """Integration tests for error propagation across tool boundaries."""

    @pytest.mark.asyncio
    async def test_正常系_各ツールのエラー型が正しくdict化される(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """異なるエラー型が各ツールで正しく dict に変換されること。"""
        from notebooklm.mcp.server import mcp

        error_cases = [
            (
                "notebooklm_create_notebook",
                {"title": "Test", "ctx": mock_ctx},
                "notebooklm.mcp.tools.notebook_tools.NotebookService",
                "create_notebook",
                ElementNotFoundError(
                    "Create button not found",
                    context={"selector": "button.create"},
                ),
                "ElementNotFoundError",
            ),
            (
                "notebooklm_list_notebooks",
                {"ctx": mock_ctx},
                "notebooklm.mcp.tools.notebook_tools.NotebookService",
                "list_notebooks",
                SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".session.json"},
                ),
                "SessionExpiredError",
            ),
            (
                "notebooklm_get_notebook_summary",
                {"notebook_id": "nb-1", "ctx": mock_ctx},
                "notebooklm.mcp.tools.notebook_tools.NotebookService",
                "get_notebook_summary",
                SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".session.json"},
                ),
                "SessionExpiredError",
            ),
            (
                "notebooklm_add_text_source",
                {
                    "notebook_id": "nb-1",
                    "text": "content",
                    "ctx": mock_ctx,
                },
                "notebooklm.mcp.tools.source_tools.SourceService",
                "add_text_source",
                SourceAddError(
                    "Failed to add source",
                    context={"notebook_id": "nb-1"},
                ),
                "SourceAddError",
            ),
            (
                "notebooklm_list_sources",
                {"notebook_id": "nb-1", "ctx": mock_ctx},
                "notebooklm.mcp.tools.source_tools.SourceService",
                "list_sources",
                SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".session.json"},
                ),
                "SessionExpiredError",
            ),
        ]

        for (
            tool_name,
            tool_kwargs,
            service_path,
            method_name,
            error,
            expected_error_type,
        ) in error_cases:
            with patch(service_path) as mock_svc_cls:
                mock_svc = mock_svc_cls.return_value
                setattr(
                    mock_svc,
                    method_name,
                    AsyncMock(side_effect=error),
                )

                tool = mcp._tool_manager._tools[tool_name]
                result = await tool.fn(**tool_kwargs)

                assert "error" in result, f"Tool {tool_name} did not return error dict"
                assert result["error_type"] == expected_error_type, (
                    f"Tool {tool_name}: expected {expected_error_type}, "
                    f"got {result['error_type']}"
                )
