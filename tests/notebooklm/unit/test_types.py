"""Unit tests for notebooklm.types module."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from notebooklm.types import (
    AudioOverviewResult,
    BatchResult,
    ChatHistory,
    ChatResponse,
    NotebookInfo,
    NotebookSummary,
    NoteContent,
    NoteInfo,
    SearchResult,
    SourceDetails,
    SourceInfo,
    StudioContentResult,
    WorkflowResult,
)


class TestNotebookInfo:
    """Tests for NotebookInfo model."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        info = NotebookInfo(
            notebook_id="c9354f3f-f55b-4f90-a5c4-219e582945cf",
            title="AI Research Notes",
        )
        assert info.notebook_id == "c9354f3f-f55b-4f90-a5c4-219e582945cf"
        assert info.title == "AI Research Notes"
        assert info.updated_at is None
        assert info.source_count == 0

    def test_正常系_全フィールド指定で作成できる(self) -> None:
        now = datetime.now(tz=timezone.utc)
        info = NotebookInfo(
            notebook_id="abc-123",
            title="My Notebook",
            updated_at=now,
            source_count=5,
        )
        assert info.updated_at == now
        assert info.source_count == 5

    def test_正常系_frozenモデルである(self) -> None:
        info = NotebookInfo(notebook_id="abc-123", title="Test")
        with pytest.raises(ValidationError):
            info.title = "Changed"

    def test_異常系_空のnotebook_idでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            NotebookInfo(notebook_id="", title="Test")

    def test_異常系_空のtitleでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            NotebookInfo(notebook_id="abc-123", title="")

    def test_異常系_負のsource_countでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            NotebookInfo(notebook_id="abc-123", title="Test", source_count=-1)


class TestNotebookSummary:
    """Tests for NotebookSummary model."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        summary = NotebookSummary(
            notebook_id="abc-123",
            summary_text="This notebook covers AI topics.",
        )
        assert summary.notebook_id == "abc-123"
        assert summary.summary_text == "This notebook covers AI topics."
        assert summary.suggested_questions == []

    def test_正常系_提案質問付きで作成できる(self) -> None:
        summary = NotebookSummary(
            notebook_id="abc-123",
            summary_text="Summary...",
            suggested_questions=[
                "What are the key findings?",
                "How does this compare?",
            ],
        )
        assert len(summary.suggested_questions) == 2

    def test_異常系_空のnotebook_idでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            NotebookSummary(notebook_id="", summary_text="Test")


class TestSourceInfo:
    """Tests for SourceInfo model."""

    def test_正常系_必須フィールドで作成できる(self) -> None:
        source = SourceInfo(
            source_id="src-001",
            title="Research Paper",
            source_type="url",
        )
        assert source.source_id == "src-001"
        assert source.source_type == "url"
        assert source.added_at is None

    def test_正常系_全ソースタイプが有効(self) -> None:
        valid_types = ["text", "url", "file", "google_drive", "youtube", "web_research"]
        for source_type in valid_types:
            source = SourceInfo(
                source_id="src-001",
                title="Test",
                source_type=source_type,  # type: ignore[arg-type]
            )
            assert source.source_type == source_type

    def test_異常系_無効なソースタイプでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            SourceInfo(
                source_id="src-001",
                title="Test",
                source_type="invalid",  # type: ignore[arg-type]
            )

    def test_異常系_空のsource_idでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            SourceInfo(source_id="", title="Test", source_type="text")


class TestSourceDetails:
    """Tests for SourceDetails model."""

    def test_正常系_全フィールド指定で作成できる(self) -> None:
        details = SourceDetails(
            source_id="src-001",
            title="AI Ethics Paper",
            source_type="url",
            source_url="https://example.com/paper.pdf",
            content_summary="This paper discusses...",
        )
        assert details.source_url == "https://example.com/paper.pdf"
        assert details.content_summary == "This paper discusses..."

    def test_正常系_オプションフィールドなしで作成できる(self) -> None:
        details = SourceDetails(
            source_id="src-001",
            title="Test",
            source_type="text",
        )
        assert details.source_url is None
        assert details.content_summary is None


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_正常系_必須フィールドで作成できる(self) -> None:
        response = ChatResponse(
            notebook_id="abc-123",
            question="What are the key findings?",
            answer="The key findings include...",
        )
        assert response.question == "What are the key findings?"
        assert response.citations == []
        assert response.suggested_followups == []

    def test_正常系_全フィールド指定で作成できる(self) -> None:
        response = ChatResponse(
            notebook_id="abc-123",
            question="Question?",
            answer="Answer.",
            citations=["Source 1", "Source 2"],
            suggested_followups=["Follow up?"],
        )
        assert len(response.citations) == 2
        assert len(response.suggested_followups) == 1

    def test_異常系_空の質問でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            ChatResponse(
                notebook_id="abc-123",
                question="",
                answer="Answer",
            )


class TestChatHistory:
    """Tests for ChatHistory model."""

    def test_正常系_空の履歴を作成できる(self) -> None:
        history = ChatHistory(notebook_id="abc-123")
        assert history.messages == []
        assert history.total_messages == 0

    def test_正常系_メッセージ付き履歴を作成できる(self) -> None:
        msg = ChatResponse(
            notebook_id="abc-123",
            question="Q?",
            answer="A.",
        )
        history = ChatHistory(
            notebook_id="abc-123",
            messages=[msg],
            total_messages=1,
        )
        assert len(history.messages) == 1

    def test_正常系_total_messagesがmessagesより大きくても有効(self) -> None:
        # total can be larger (e.g., pagination - only some messages loaded)
        msg = ChatResponse(
            notebook_id="abc-123",
            question="Q?",
            answer="A.",
        )
        history = ChatHistory(
            notebook_id="abc-123",
            messages=[msg],
            total_messages=10,
        )
        assert history.total_messages == 10

    def test_異常系_total_messagesがmessages数未満でValidationError(self) -> None:
        msg = ChatResponse(
            notebook_id="abc-123",
            question="Q?",
            answer="A.",
        )
        with pytest.raises(ValidationError, match="total_messages"):
            ChatHistory(
                notebook_id="abc-123",
                messages=[msg, msg],
                total_messages=1,
            )


class TestAudioOverviewResult:
    """Tests for AudioOverviewResult model."""

    def test_正常系_完了状態で作成できる(self) -> None:
        result = AudioOverviewResult(
            notebook_id="abc-123",
            status="completed",
            duration_seconds=180.0,
            generation_time_seconds=45.0,
        )
        assert result.status == "completed"
        assert result.duration_seconds == 180.0

    def test_正常系_進行中状態で作成できる(self) -> None:
        result = AudioOverviewResult(
            notebook_id="abc-123",
            status="in_progress",
        )
        assert result.status == "in_progress"
        assert result.audio_url is None

    def test_正常系_失敗状態で作成できる(self) -> None:
        result = AudioOverviewResult(
            notebook_id="abc-123",
            status="failed",
        )
        assert result.status == "failed"

    def test_異常系_無効なステータスでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            AudioOverviewResult(
                notebook_id="abc-123",
                status="unknown",  # type: ignore[arg-type]
            )

    def test_異常系_負のduration_secondsでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            AudioOverviewResult(
                notebook_id="abc-123",
                status="completed",
                duration_seconds=-1.0,
            )


class TestStudioContentResult:
    """Tests for StudioContentResult model."""

    def test_正常系_レポートタイプで作成できる(self) -> None:
        result = StudioContentResult(
            notebook_id="abc-123",
            content_type="report",
            title="AI Research Overview",
            text_content="# Report\n\nContent...",
            generation_time_seconds=15.0,
        )
        assert result.content_type == "report"
        assert result.text_content is not None
        assert result.table_data is None
        assert result.download_path is None

    def test_正常系_データテーブルタイプで作成できる(self) -> None:
        result = StudioContentResult(
            notebook_id="abc-123",
            content_type="data_table",
            title="Data Table",
            table_data=[
                ["Column A", "Column B"],
                ["Value 1", "Value 2"],
            ],
            generation_time_seconds=30.0,
        )
        assert result.content_type == "data_table"
        assert result.table_data is not None
        assert len(result.table_data) == 2

    def test_正常系_画像タイプでダウンロードパス付きで作成できる(self) -> None:
        result = StudioContentResult(
            notebook_id="abc-123",
            content_type="infographic",
            title="Infographic",
            download_path="/tmp/infographic.png",
            generation_time_seconds=50.0,
        )
        assert result.download_path == "/tmp/infographic.png"

    def test_正常系_全コンテンツタイプが有効(self) -> None:
        valid_types = [
            "report",
            "infographic",
            "slides",
            "data_table",
            "flashcards",
            "quiz",
            "mind_map",
            "video_explainer",
            "memo",
        ]
        for content_type in valid_types:
            result = StudioContentResult(
                notebook_id="abc-123",
                content_type=content_type,  # type: ignore[arg-type]
                title="Test",
                generation_time_seconds=1.0,
            )
            assert result.content_type == content_type

    def test_異常系_無効なコンテンツタイプでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            StudioContentResult(
                notebook_id="abc-123",
                content_type="invalid",  # type: ignore[arg-type]
                title="Test",
                generation_time_seconds=1.0,
            )

    def test_異常系_負の生成時間でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            StudioContentResult(
                notebook_id="abc-123",
                content_type="report",
                title="Test",
                generation_time_seconds=-1.0,
            )


class TestNoteInfo:
    """Tests for NoteInfo model."""

    def test_正常系_必須フィールドで作成できる(self) -> None:
        note = NoteInfo(note_id="note-001", title="Key Observations")
        assert note.note_id == "note-001"
        assert note.title == "Key Observations"
        assert note.created_at is None

    def test_正常系_日時付きで作成できる(self) -> None:
        now = datetime.now(tz=timezone.utc)
        note = NoteInfo(note_id="note-001", title="Test", created_at=now)
        assert note.created_at == now

    def test_異常系_空のnote_idでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            NoteInfo(note_id="", title="Test")


class TestNoteContent:
    """Tests for NoteContent model."""

    def test_正常系_全フィールドで作成できる(self) -> None:
        note = NoteContent(
            note_id="note-001",
            title="Key Observations",
            content="The main takeaway is...",
        )
        assert note.content == "The main takeaway is..."

    def test_正常系_空のコンテンツで作成できる(self) -> None:
        note = NoteContent(
            note_id="note-001",
            title="Empty Note",
            content="",
        )
        assert note.content == ""


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_正常系_必須フィールドで作成できる(self) -> None:
        result = SearchResult(
            title="AI Paper",
            url="https://example.com/paper",
        )
        assert result.title == "AI Paper"
        assert result.summary == ""
        assert result.source_type == "web"
        assert result.selected is True

    def test_正常系_全フィールド指定で作成できる(self) -> None:
        result = SearchResult(
            title="AI Paper",
            url="https://example.com/paper",
            summary="This paper discusses...",
            source_type="drive",
            selected=False,
        )
        assert result.selected is False

    def test_異常系_空のURLでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            SearchResult(title="Test", url="")


class TestBatchResult:
    """Tests for BatchResult model."""

    def test_正常系_有効なカウントで作成できる(self) -> None:
        result = BatchResult(
            total=5,
            succeeded=4,
            failed=1,
            results=[{"id": "abc", "status": "success"}],
        )
        assert result.total == 5
        assert result.succeeded == 4
        assert result.failed == 1

    def test_正常系_空のバッチ結果をファクトリメソッドで作成できる(self) -> None:
        result = BatchResult.create_empty()
        assert result.total == 0
        assert result.succeeded == 0
        assert result.failed == 0
        assert result.results == []

    def test_異常系_カウント不整合でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="must equal total"):
            BatchResult(total=5, succeeded=3, failed=1)

    def test_異常系_負のtotalでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            BatchResult(total=-1, succeeded=0, failed=0)

    def test_正常系_全成功のバッチ結果(self) -> None:
        result = BatchResult(total=3, succeeded=3, failed=0)
        assert result.succeeded == result.total

    def test_正常系_全失敗のバッチ結果(self) -> None:
        result = BatchResult(total=3, succeeded=0, failed=3)
        assert result.failed == result.total


class TestWorkflowResult:
    """Tests for WorkflowResult model."""

    def test_正常系_完了ワークフローを作成できる(self) -> None:
        result = WorkflowResult(
            workflow_name="create_and_analyze",
            status="completed",
            steps_completed=3,
            steps_total=3,
            outputs={"notebook_id": "abc-123"},
        )
        assert result.status == "completed"
        assert result.steps_completed == result.steps_total

    def test_正常系_部分完了ワークフローを作成できる(self) -> None:
        result = WorkflowResult(
            workflow_name="multi_step",
            status="partial",
            steps_completed=2,
            steps_total=5,
        )
        assert result.status == "partial"

    def test_正常系_失敗ワークフローをエラー付きで作成できる(self) -> None:
        result = WorkflowResult(
            workflow_name="failed_workflow",
            status="failed",
            steps_completed=1,
            steps_total=3,
            errors=["Step 2 failed: timeout"],
        )
        assert result.status == "failed"
        assert len(result.errors) == 1

    def test_異常系_完了状態でステップ不一致でValidationError(self) -> None:
        with pytest.raises(ValidationError, match="steps_completed"):
            WorkflowResult(
                workflow_name="test",
                status="completed",
                steps_completed=2,
                steps_total=3,
            )

    def test_異常系_失敗状態でエラーなしでValidationError(self) -> None:
        with pytest.raises(ValidationError, match="no errors"):
            WorkflowResult(
                workflow_name="test",
                status="failed",
                steps_completed=1,
                steps_total=3,
                errors=[],
            )

    def test_異常系_steps_completedがsteps_totalを超えるとValidationError(self) -> None:
        with pytest.raises(ValidationError, match="cannot exceed"):
            WorkflowResult(
                workflow_name="test",
                status="partial",
                steps_completed=5,
                steps_total=3,
            )

    def test_異常系_steps_totalが0でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            WorkflowResult(
                workflow_name="test",
                status="partial",
                steps_completed=0,
                steps_total=0,
            )

    def test_異常系_空のworkflow_nameでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            WorkflowResult(
                workflow_name="",
                status="completed",
                steps_completed=1,
                steps_total=1,
            )


class TestModelImmutability:
    """Tests for frozen model behavior across all models."""

    def test_正常系_NotebookInfoがfrozenである(self) -> None:
        info = NotebookInfo(notebook_id="abc", title="Test")
        with pytest.raises(ValidationError):
            info.title = "Changed"

    def test_正常系_ChatResponseがfrozenである(self) -> None:
        response = ChatResponse(
            notebook_id="abc",
            question="Q?",
            answer="A.",
        )
        with pytest.raises(ValidationError):
            response.answer = "Changed"

    def test_正常系_BatchResultがfrozenである(self) -> None:
        result = BatchResult.create_empty()
        with pytest.raises(ValidationError):
            result.total = 10

    def test_正常系_WorkflowResultがfrozenである(self) -> None:
        result = WorkflowResult(
            workflow_name="test",
            status="completed",
            steps_completed=1,
            steps_total=1,
        )
        with pytest.raises(ValidationError):
            result.status = "failed"
