"""Pydantic v2 data models for the NotebookLM MCP server package.

This module defines all data models used for MCP tool responses
and notebook data representation. All models use ``ConfigDict(frozen=True)``
for immutability and include Field validation.

Model Categories
----------------
- Notebook models: NotebookInfo, NotebookSummary
- Source models: SourceInfo, SourceDetails
- Chat models: ChatResponse, ChatHistory
- Audio models: AudioOverviewResult
- Studio models: StudioContentResult
- Note models: NoteInfo, NoteContent
- Utility models: SearchResult, BatchResult, WorkflowResult

See Also
--------
database.types : Similar Pydantic v2 model patterns.
"""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

type SourceType = Literal[
    "text", "url", "file", "google_drive", "youtube", "web_research"
]
"""Supported source types for NotebookLM notebooks."""

type StudioContentType = Literal[
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
"""Supported Studio content generation types."""

type ReportFormat = Literal["custom", "briefing_doc", "study_guide", "blog_post"]
"""Available report format options for Studio report generation."""

type ResearchMode = Literal["fast", "deep"]
"""Research mode for web source discovery."""


# ---------------------------------------------------------------------------
# Notebook models
# ---------------------------------------------------------------------------


class NotebookInfo(BaseModel):
    """Information about a NotebookLM notebook.

    Represents basic metadata for a notebook as returned by
    the list notebooks operation.

    Parameters
    ----------
    notebook_id : str
        Unique identifier for the notebook (UUID from URL).
    title : str
        Display title of the notebook.
    updated_at : datetime | None
        Last modification timestamp, if available.
    source_count : int
        Number of sources in the notebook.

    Examples
    --------
    >>> info = NotebookInfo(
    ...     notebook_id="c9354f3f-f55b-4f90-a5c4-219e582945cf",
    ...     title="AI Research Notes",
    ...     source_count=5,
    ... )
    >>> info.notebook_id
    'c9354f3f-f55b-4f90-a5c4-219e582945cf'
    """

    model_config = ConfigDict(frozen=True)

    notebook_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the notebook (UUID from URL)",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Display title of the notebook",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Last modification timestamp",
    )
    source_count: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            description="Number of sources in the notebook",
        ),
    ] = 0


class NotebookSummary(BaseModel):
    """AI-generated summary of a notebook's contents.

    Contains the overview text and suggested questions
    that NotebookLM auto-generates from the notebook's sources.

    Parameters
    ----------
    notebook_id : str
        Unique identifier for the notebook.
    summary_text : str
        AI-generated overview of the notebook contents.
    suggested_questions : list[str]
        AI-generated follow-up questions.

    Examples
    --------
    >>> summary = NotebookSummary(
    ...     notebook_id="abc-123",
    ...     summary_text="This notebook covers...",
    ...     suggested_questions=["What are the key findings?"],
    ... )
    """

    model_config = ConfigDict(frozen=True)

    notebook_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the notebook",
    )
    summary_text: str = Field(
        ...,
        description="AI-generated overview of the notebook contents",
    )
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="AI-generated follow-up questions",
    )


# ---------------------------------------------------------------------------
# Source models
# ---------------------------------------------------------------------------


class SourceInfo(BaseModel):
    """Basic information about a source in a notebook.

    Parameters
    ----------
    source_id : str
        Identifier for the source within the notebook.
    title : str
        Display title of the source.
    source_type : SourceType
        Type of the source (text, url, file, etc.).
    added_at : datetime | None
        Timestamp when the source was added.

    Examples
    --------
    >>> source = SourceInfo(
    ...     source_id="src-001",
    ...     title="Research Paper on AI",
    ...     source_type="url",
    ... )
    """

    model_config = ConfigDict(frozen=True)

    source_id: str = Field(
        ...,
        min_length=1,
        description="Identifier for the source within the notebook",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Display title of the source",
    )
    source_type: SourceType = Field(
        ...,
        description="Type of the source",
    )
    added_at: datetime | None = Field(
        default=None,
        description="Timestamp when the source was added",
    )


class SourceDetails(BaseModel):
    """Detailed information about a source, including its content summary.

    Extends SourceInfo with additional metadata and AI-generated summary.

    Parameters
    ----------
    source_id : str
        Identifier for the source within the notebook.
    title : str
        Display title of the source.
    source_type : SourceType
        Type of the source.
    source_url : str | None
        Original URL if the source is a URL or web research result.
    content_summary : str | None
        AI-generated summary of the source content.
    added_at : datetime | None
        Timestamp when the source was added.

    Examples
    --------
    >>> details = SourceDetails(
    ...     source_id="src-001",
    ...     title="AI Ethics Paper",
    ...     source_type="url",
    ...     source_url="https://example.com/paper.pdf",
    ...     content_summary="This paper discusses...",
    ... )
    """

    model_config = ConfigDict(frozen=True)

    source_id: str = Field(
        ...,
        min_length=1,
        description="Identifier for the source within the notebook",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Display title of the source",
    )
    source_type: SourceType = Field(
        ...,
        description="Type of the source",
    )
    source_url: str | None = Field(
        default=None,
        description="Original URL if the source is URL-based",
    )
    content_summary: str | None = Field(
        default=None,
        description="AI-generated summary of the source content",
    )
    added_at: datetime | None = Field(
        default=None,
        description="Timestamp when the source was added",
    )


# ---------------------------------------------------------------------------
# Chat models
# ---------------------------------------------------------------------------


class ChatResponse(BaseModel):
    """Response from an AI chat interaction.

    Contains the AI's answer along with source citations
    and suggested follow-up questions.

    Parameters
    ----------
    notebook_id : str
        Notebook that the chat is associated with.
    question : str
        The original question asked.
    answer : str
        AI-generated answer text.
    citations : list[str]
        Source citations referenced in the answer.
    suggested_followups : list[str]
        AI-suggested follow-up questions.

    Examples
    --------
    >>> response = ChatResponse(
    ...     notebook_id="abc-123",
    ...     question="What are the key findings?",
    ...     answer="The key findings include...",
    ...     citations=["Source 1: AI Research Paper"],
    ...     suggested_followups=["How do these findings compare?"],
    ... )
    """

    model_config = ConfigDict(frozen=True)

    notebook_id: str = Field(
        ...,
        min_length=1,
        description="Notebook that the chat is associated with",
    )
    question: str = Field(
        ...,
        min_length=1,
        description="The original question asked",
    )
    answer: str = Field(
        ...,
        description="AI-generated answer text",
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Source citations referenced in the answer",
    )
    suggested_followups: list[str] = Field(
        default_factory=list,
        description="AI-suggested follow-up questions",
    )


class ChatHistory(BaseModel):
    """Chat conversation history for a notebook.

    Parameters
    ----------
    notebook_id : str
        Notebook that the chat history belongs to.
    messages : list[ChatResponse]
        Ordered list of chat interactions.
    total_messages : int
        Total number of messages in the history.

    Examples
    --------
    >>> history = ChatHistory(
    ...     notebook_id="abc-123",
    ...     messages=[],
    ...     total_messages=0,
    ... )
    """

    model_config = ConfigDict(frozen=True)

    notebook_id: str = Field(
        ...,
        min_length=1,
        description="Notebook that the chat history belongs to",
    )
    messages: list[ChatResponse] = Field(
        default_factory=list,
        description="Ordered list of chat interactions",
    )
    total_messages: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            description="Total number of messages in the history",
        ),
    ] = 0

    @model_validator(mode="after")
    def validate_message_count(self) -> Self:
        """Validate that total_messages is consistent with messages list."""
        if self.total_messages < len(self.messages):
            raise ValueError(
                f"total_messages ({self.total_messages}) cannot be less than "
                f"the number of messages ({len(self.messages)})"
            )
        return self


# ---------------------------------------------------------------------------
# Audio models
# ---------------------------------------------------------------------------


class AudioOverviewResult(BaseModel):
    """Result of an Audio Overview (podcast) generation.

    Parameters
    ----------
    notebook_id : str
        Notebook that the audio was generated from.
    status : str
        Generation status ("completed", "in_progress", "failed").
    audio_url : str | None
        URL to the generated audio, if available.
    duration_seconds : float | None
        Duration of the generated audio in seconds.
    generation_time_seconds : float | None
        Time taken to generate the audio in seconds.

    Examples
    --------
    >>> result = AudioOverviewResult(
    ...     notebook_id="abc-123",
    ...     status="completed",
    ...     duration_seconds=180.0,
    ...     generation_time_seconds=45.0,
    ... )
    """

    model_config = ConfigDict(frozen=True)

    notebook_id: str = Field(
        ...,
        min_length=1,
        description="Notebook that the audio was generated from",
    )
    status: Literal["completed", "in_progress", "failed"] = Field(
        ...,
        description="Generation status",
    )
    audio_url: str | None = Field(
        default=None,
        description="URL to the generated audio",
    )
    duration_seconds: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            description="Duration of the generated audio in seconds",
        ),
    ] = None
    generation_time_seconds: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            description="Time taken to generate the audio in seconds",
        ),
    ] = None


# ---------------------------------------------------------------------------
# Studio models
# ---------------------------------------------------------------------------


class StudioContentResult(BaseModel):
    """Result of a Studio content generation operation.

    Represents the output of generating Studio content such as reports,
    infographics, slides, data tables, flashcards, quizzes, etc.

    Parameters
    ----------
    notebook_id : str
        Notebook that the content was generated from.
    content_type : StudioContentType
        Type of Studio content generated.
    title : str
        Title of the generated content.
    text_content : str | None
        Extracted text for text-based content (reports).
    table_data : list[list[str]] | None
        Structured table data for table-based content (data tables).
    download_path : str | None
        Local file path for downloaded content (infographics, slides).
    generation_time_seconds : float
        Time taken for content generation in seconds.

    Examples
    --------
    >>> result = StudioContentResult(
    ...     notebook_id="abc-123",
    ...     content_type="report",
    ...     title="AI Research Overview",
    ...     text_content="# Report Title\\n\\nContent...",
    ...     generation_time_seconds=15.0,
    ... )
    """

    model_config = ConfigDict(frozen=True)

    notebook_id: str = Field(
        ...,
        min_length=1,
        description="Notebook that the content was generated from",
    )
    content_type: StudioContentType = Field(
        ...,
        description="Type of Studio content generated",
    )
    title: str = Field(
        ...,
        description="Title of the generated content",
    )
    text_content: str | None = Field(
        default=None,
        description="Extracted text for text-based content (reports)",
    )
    table_data: list[list[str]] | None = Field(
        default=None,
        description="Structured table data for table-based content",
    )
    download_path: str | None = Field(
        default=None,
        description="Local file path for downloaded content (images, slides)",
    )
    generation_time_seconds: Annotated[
        float,
        Field(
            ...,
            ge=0.0,
            description="Time taken for content generation in seconds",
        ),
    ]


# ---------------------------------------------------------------------------
# Note models
# ---------------------------------------------------------------------------


class NoteInfo(BaseModel):
    """Basic information about a note in a notebook.

    Parameters
    ----------
    note_id : str
        Identifier for the note.
    title : str
        Display title of the note.
    created_at : datetime | None
        Timestamp when the note was created.

    Examples
    --------
    >>> note = NoteInfo(
    ...     note_id="note-001",
    ...     title="Key Observations",
    ... )
    """

    model_config = ConfigDict(frozen=True)

    note_id: str = Field(
        ...,
        min_length=1,
        description="Identifier for the note",
    )
    title: str = Field(
        ...,
        max_length=1000,
        description="Display title of the note",
    )
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the note was created",
    )


class NoteContent(BaseModel):
    """Full content of a note including its body text.

    Parameters
    ----------
    note_id : str
        Identifier for the note.
    title : str
        Display title of the note.
    content : str
        Full text content of the note.
    created_at : datetime | None
        Timestamp when the note was created.

    Examples
    --------
    >>> note = NoteContent(
    ...     note_id="note-001",
    ...     title="Key Observations",
    ...     content="The main takeaway is...",
    ... )
    """

    model_config = ConfigDict(frozen=True)

    note_id: str = Field(
        ...,
        min_length=1,
        description="Identifier for the note",
    )
    title: str = Field(
        ...,
        max_length=1000,
        description="Display title of the note",
    )
    content: str = Field(
        ...,
        description="Full text content of the note",
    )
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the note was created",
    )


# ---------------------------------------------------------------------------
# Utility models
# ---------------------------------------------------------------------------


class SearchResult(BaseModel):
    """Result of a web research source discovery.

    Parameters
    ----------
    title : str
        Title of the discovered source.
    url : str
        URL of the discovered source.
    summary : str
        AI-generated summary of the source.
    source_type : str
        Type indicator (web, drive, etc.).
    selected : bool
        Whether the source is selected for import.

    Examples
    --------
    >>> result = SearchResult(
    ...     title="AI Research Paper",
    ...     url="https://example.com/paper",
    ...     summary="This paper discusses...",
    ...     source_type="web",
    ... )
    """

    model_config = ConfigDict(frozen=True)

    title: str = Field(
        ...,
        description="Title of the discovered source",
    )
    url: str = Field(
        ...,
        min_length=1,
        description="URL of the discovered source",
    )
    summary: str = Field(
        default="",
        description="AI-generated summary of the source",
    )
    source_type: str = Field(
        default="web",
        description="Type indicator (web, drive, etc.)",
    )
    selected: bool = Field(
        default=True,
        description="Whether the source is selected for import",
    )


class BatchResult(BaseModel):
    """Result of a batch operation across multiple notebooks or sources.

    Parameters
    ----------
    total : int
        Total number of items processed.
    succeeded : int
        Number of items that succeeded.
    failed : int
        Number of items that failed.
    results : list[dict[str, str]]
        Individual results for each item.

    Examples
    --------
    >>> batch = BatchResult(
    ...     total=5,
    ...     succeeded=4,
    ...     failed=1,
    ...     results=[
    ...         {"notebook_id": "abc-123", "status": "success"},
    ...     ],
    ... )
    """

    model_config = ConfigDict(frozen=True)

    total: Annotated[
        int,
        Field(
            ...,
            ge=0,
            description="Total number of items processed",
        ),
    ]
    succeeded: Annotated[
        int,
        Field(
            ...,
            ge=0,
            description="Number of items that succeeded",
        ),
    ]
    failed: Annotated[
        int,
        Field(
            ...,
            ge=0,
            description="Number of items that failed",
        ),
    ]
    results: list[dict[str, str]] = Field(
        default_factory=list,
        description="Individual results for each item",
    )

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        """Validate that succeeded + failed equals total."""
        if self.succeeded + self.failed != self.total:
            raise ValueError(
                f"succeeded ({self.succeeded}) + failed ({self.failed}) "
                f"must equal total ({self.total})"
            )
        return self

    @classmethod
    def create_empty(cls) -> Self:
        """Create an empty batch result with zero counts.

        Returns
        -------
        BatchResult
            A BatchResult with all counts set to zero.

        Examples
        --------
        >>> result = BatchResult.create_empty()
        >>> result.total
        0
        """
        return cls(total=0, succeeded=0, failed=0, results=[])


class WorkflowResult(BaseModel):
    """Result of a multi-step workflow operation.

    Represents the outcome of complex operations that involve
    multiple steps (e.g., create notebook -> add sources -> generate content).

    Parameters
    ----------
    workflow_name : str
        Name identifying the workflow.
    status : str
        Overall workflow status ("completed", "partial", "failed").
    steps_completed : int
        Number of workflow steps completed successfully.
    steps_total : int
        Total number of steps in the workflow.
    outputs : dict[str, str]
        Key-value pairs of workflow outputs (e.g., notebook_id, content_path).
    errors : list[str]
        Error messages from any failed steps.

    Examples
    --------
    >>> result = WorkflowResult(
    ...     workflow_name="create_and_analyze",
    ...     status="completed",
    ...     steps_completed=3,
    ...     steps_total=3,
    ...     outputs={"notebook_id": "abc-123", "summary": "..."},
    ... )
    """

    model_config = ConfigDict(frozen=True)

    workflow_name: str = Field(
        ...,
        min_length=1,
        description="Name identifying the workflow",
    )
    status: Literal["completed", "partial", "failed"] = Field(
        ...,
        description="Overall workflow status",
    )
    steps_completed: Annotated[
        int,
        Field(
            ...,
            ge=0,
            description="Number of workflow steps completed successfully",
        ),
    ]
    steps_total: Annotated[
        int,
        Field(
            ...,
            ge=1,
            description="Total number of steps in the workflow",
        ),
    ]
    outputs: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value pairs of workflow outputs",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Error messages from any failed steps",
    )

    @model_validator(mode="after")
    def validate_steps(self) -> Self:
        """Validate that steps_completed does not exceed steps_total."""
        if self.steps_completed > self.steps_total:
            raise ValueError(
                f"steps_completed ({self.steps_completed}) cannot exceed "
                f"steps_total ({self.steps_total})"
            )
        return self

    @model_validator(mode="after")
    def validate_status_consistency(self) -> Self:
        """Validate that status is consistent with completion state."""
        if self.status == "completed" and self.steps_completed != self.steps_total:
            raise ValueError(
                f"Status is 'completed' but steps_completed ({self.steps_completed}) "
                f"does not equal steps_total ({self.steps_total})"
            )
        if self.status == "failed" and not self.errors:
            raise ValueError("Status is 'failed' but no errors were provided")
        return self


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "AudioOverviewResult",
    "BatchResult",
    "ChatHistory",
    "ChatResponse",
    "NoteContent",
    "NoteInfo",
    "NotebookInfo",
    "NotebookSummary",
    "ReportFormat",
    "ResearchMode",
    "SearchResult",
    "SourceDetails",
    "SourceInfo",
    "SourceType",
    "StudioContentResult",
    "StudioContentType",
    "WorkflowResult",
]
