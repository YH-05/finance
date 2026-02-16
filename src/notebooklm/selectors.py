"""CSS selector management for NotebookLM Playwright automation.

This module centralizes all CSS selectors used to interact with the
NotebookLM web UI via Playwright. Selectors are organized into
functional groups (notebook, source, chat, audio, studio, note, search)
with priority-based fallback and stability metadata.

Fallback Priority Order
-----------------------
1. aria-label (most stable, accessibility-based)
2. placeholder (stable for input fields)
3. role+text (stable, semantic HTML)
4. ref attribute (fragile, frequently changes with UI updates)

Architecture
------------
- ``SelectorCandidate``: Individual selector with method and priority.
- ``SelectorMetadata``: Stability level and last verification date.
- ``SelectorGroup``: Named group of candidates for a single UI element.
- ``SelectorManager``: Registry providing priority-ordered fallback lookup.

Examples
--------
>>> from notebooklm.selectors import SelectorManager
>>> manager = SelectorManager()
>>> candidates = manager.get_candidates("chat_send_button")
>>> for c in candidates:
...     print(f"[{c.priority}] {c.selector}")

See Also
--------
news.extractors.playwright : Similar CSS selector fallback pattern.
"""

from datetime import date
from enum import StrEnum
from functools import cached_property
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from utils_core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class StabilityLevel(StrEnum):
    """Stability level for a selector group.

    Indicates how likely a selector is to break due to UI updates.

    Attributes
    ----------
    STABLE : str
        Selector is based on accessibility attributes or semantic HTML.
        Unlikely to break with UI updates.
    MODERATE : str
        Selector uses text content or placeholders.
        May break with localization or UI text changes.
    FRAGILE : str
        Selector relies on implementation-specific attributes (e.g., ref=).
        Likely to break with any UI update. Must have fallback alternatives.
    """

    STABLE = "stable"
    MODERATE = "moderate"
    FRAGILE = "fragile"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SelectorCandidate(BaseModel):
    """Individual CSS/Playwright selector candidate.

    Represents a single selector string with its lookup method
    and priority for fallback ordering.

    Parameters
    ----------
    selector : str
        CSS selector or Playwright locator string.
    method : str
        Selector method used (e.g., "aria-label", "placeholder", "role", "ref").
    priority : int
        Priority for fallback ordering (lower = higher priority, tried first).
    description : str | None
        Human-readable description of what this selector targets.

    Examples
    --------
    >>> candidate = SelectorCandidate(
    ...     selector='button[aria-label="送信"]',
    ...     method="aria-label",
    ...     priority=1,
    ...     description="Chat send button via aria-label",
    ... )
    """

    model_config = ConfigDict(frozen=True)

    selector: str = Field(
        ...,
        min_length=1,
        description="CSS selector or Playwright locator string",
    )
    method: str = Field(
        ...,
        min_length=1,
        description="Selector method (aria-label, placeholder, role, ref)",
    )
    priority: Annotated[
        int,
        Field(
            ...,
            ge=0,
            description="Fallback priority (lower = higher priority)",
        ),
    ]
    description: str | None = Field(
        default=None,
        description="Human-readable description of the selector target",
    )


class SelectorMetadata(BaseModel):
    """Metadata about a selector group's stability and verification status.

    Parameters
    ----------
    stability : StabilityLevel
        How stable the selector group is against UI changes.
    last_verified : date
        Date when the selectors were last verified against live UI.
    notes : str | None
        Additional notes about the selector group.

    Examples
    --------
    >>> metadata = SelectorMetadata(
    ...     stability=StabilityLevel.STABLE,
    ...     last_verified=date(2026, 2, 16),
    ...     notes="Verified on live NotebookLM UI",
    ... )
    """

    model_config = ConfigDict(frozen=True)

    stability: StabilityLevel = Field(
        ...,
        description="Stability level of the selector group",
    )
    last_verified: date = Field(
        ...,
        description="Date when selectors were last verified against live UI",
    )
    notes: str | None = Field(
        default=None,
        description="Additional notes about the selector group",
    )


class SelectorGroup(BaseModel):
    """Named group of selector candidates for a single UI element.

    Groups related selectors for the same UI element with metadata
    about stability and verification status.

    Parameters
    ----------
    name : str
        Unique identifier for this selector group.
    description : str
        Human-readable description of the target UI element.
    group : str
        Functional category (notebook, source, chat, audio, studio, note, search).
    candidates : list[SelectorCandidate]
        List of selector candidates (must have at least one).
    metadata : SelectorMetadata
        Stability and verification metadata.

    Examples
    --------
    >>> group = SelectorGroup(
    ...     name="chat_send_button",
    ...     description="Chat send button",
    ...     group="chat",
    ...     candidates=[
    ...         SelectorCandidate(
    ...             selector='query-box button[aria-label="送信"]',
    ...             method="aria-label",
    ...             priority=1,
    ...         ),
    ...     ],
    ...     metadata=SelectorMetadata(
    ...         stability=StabilityLevel.STABLE,
    ...         last_verified=date(2026, 2, 16),
    ...     ),
    ... )
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for this selector group",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the target UI element",
    )
    group: str = Field(
        ...,
        min_length=1,
        description="Functional category (notebook, source, chat, etc.)",
    )
    candidates: list[SelectorCandidate] = Field(
        ...,
        min_length=1,
        description="Selector candidates (at least one required)",
    )
    metadata: SelectorMetadata = Field(
        ...,
        description="Stability and verification metadata",
    )

    @cached_property
    def sorted_candidates(self) -> list[SelectorCandidate]:
        """Return candidates sorted by priority (ascending).

        Returns
        -------
        list[SelectorCandidate]
            Candidates ordered from highest priority (lowest number)
            to lowest priority (highest number).
        """
        return sorted(self.candidates, key=lambda c: c.priority)


# ---------------------------------------------------------------------------
# Verified date constant
# ---------------------------------------------------------------------------

_VERIFIED_DATE = date(2026, 2, 16)
"""Date when all selectors were verified against the live NotebookLM UI."""


# ---------------------------------------------------------------------------
# Selector definitions by functional group
# ---------------------------------------------------------------------------


def _build_notebook_selectors() -> list[SelectorGroup]:
    """Build selector groups for notebook management operations.

    Returns
    -------
    list[SelectorGroup]
        Selector groups for notebook creation, listing, and deletion.
    """
    return [
        SelectorGroup(
            name="create_notebook_button",
            description="Button to create a new notebook",
            group="notebook",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="新しいノートブック"]',
                    method="aria-label",
                    priority=1,
                    description="Create notebook via aria-label",
                ),
                SelectorCandidate(
                    selector='button[ref="e78"]',
                    method="ref",
                    priority=10,
                    description="Create notebook via ref (primary)",
                ),
                SelectorCandidate(
                    selector='button[ref="e135"]',
                    method="ref",
                    priority=11,
                    description="Create notebook via ref (secondary)",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.FRAGILE,
                last_verified=_VERIFIED_DATE,
                notes="ref values change frequently with UI updates",
            ),
        ),
        SelectorGroup(
            name="notebook_list_item",
            description="Individual notebook entry in the notebook list",
            group="notebook",
            candidates=[
                SelectorCandidate(
                    selector='a[href*="/notebook/"]',
                    method="href",
                    priority=1,
                    description="Notebook link by URL pattern",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
                notes="URL pattern is stable",
            ),
        ),
        SelectorGroup(
            name="notebook_title_input",
            description="Input field for notebook title",
            group="notebook",
            candidates=[
                SelectorCandidate(
                    selector='input[aria-label="ノートブックのタイトル"]',
                    method="aria-label",
                    priority=1,
                    description="Notebook title input via aria-label",
                ),
                SelectorCandidate(
                    selector='input[type="text"]',
                    method="type",
                    priority=5,
                    description="Generic text input fallback",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="notebook_settings_menu",
            description="Notebook settings/options menu button",
            group="notebook",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="もっと見る"]',
                    method="aria-label",
                    priority=1,
                    description="More options button via aria-label",
                ),
                SelectorCandidate(
                    selector='button[aria-label="その他のオプション"]',
                    method="aria-label",
                    priority=2,
                    description="Other options button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="notebook_delete_menuitem",
            description="Delete notebook menu item",
            group="notebook",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("削除")',
                    method="role+text",
                    priority=1,
                    description="Delete menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
    ]


def _build_source_selectors() -> list[SelectorGroup]:
    """Build selector groups for source management operations.

    Returns
    -------
    list[SelectorGroup]
        Selector groups for source addition, listing, and management.
    """
    return [
        SelectorGroup(
            name="source_add_button",
            description="Button to open the source addition dialog",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="ソースを追加"]',
                    method="aria-label",
                    priority=1,
                    description="Add source button via aria-label",
                ),
                SelectorCandidate(
                    selector='[role="button"]:has-text("ソースを追加")',
                    method="role+text",
                    priority=3,
                    description="Add source button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_text_button",
            description="Button to select text source type",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("コピーしたテキスト")',
                    method="role+text",
                    priority=1,
                    description="Copied text source button via role and text",
                ),
                SelectorCandidate(
                    selector='button[ref="e1842"]',
                    method="ref",
                    priority=10,
                    description="Copied text source button via ref",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.FRAGILE,
                last_verified=_VERIFIED_DATE,
                notes="ref value is fragile; role+text is preferred",
            ),
        ),
        SelectorGroup(
            name="source_text_input",
            description="Text input area for pasting text source",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[placeholder="ここにテキストを貼り付けてください"]',
                    method="placeholder",
                    priority=1,
                    description="Text paste area via placeholder",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="Placeholder text may change with localization",
            ),
        ),
        SelectorGroup(
            name="source_url_button",
            description="Button to select URL/website source type",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("ウェブサイト")',
                    method="role+text",
                    priority=1,
                    description="Website source button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_url_input",
            description="URL input field for adding URL source",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[placeholder="リンクを貼り付ける"]',
                    method="placeholder",
                    priority=1,
                    description="URL input via placeholder",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="Placeholder text may change with localization",
            ),
        ),
        SelectorGroup(
            name="source_file_upload_button",
            description="Button to upload file as source",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("ファイルをアップロード")',
                    method="role+text",
                    priority=1,
                    description="File upload button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_drive_button",
            description="Button to add Google Drive source",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("ドライブ")',
                    method="role+text",
                    priority=1,
                    description="Google Drive source button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_insert_button",
            description="Insert/submit button for adding source",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("挿入")',
                    method="role+text",
                    priority=1,
                    description="Insert button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_select_all_checkbox",
            description="Checkbox to select/deselect all sources",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[role="checkbox"][aria-label="すべてのソースを選択"]',
                    method="aria-label",
                    priority=1,
                    description="Select all sources checkbox via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_more_menu_button",
            description="More options button for individual source",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="もっと見る"]',
                    method="aria-label",
                    priority=1,
                    description="More menu button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_delete_menuitem",
            description="Menu item to delete a source",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("ソースを削除")',
                    method="role+text",
                    priority=1,
                    description="Delete source menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_rename_menuitem",
            description="Menu item to rename a source",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("ソース名を変更")',
                    method="role+text",
                    priority=1,
                    description="Rename source menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="source_count_indicator",
            description="Source count indicator (e.g., '5 / 300')",
            group="source",
            candidates=[
                SelectorCandidate(
                    selector="text=/\\d+ \\/ 300/",
                    method="text-pattern",
                    priority=1,
                    description="Source count via regex text pattern",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="Max source count (300) may change",
            ),
        ),
    ]


def _build_chat_selectors() -> list[SelectorGroup]:
    """Build selector groups for chat operations.

    Returns
    -------
    list[SelectorGroup]
        Selector groups for chat input, sending, and response extraction.
    """
    return [
        SelectorGroup(
            name="chat_query_input",
            description="Chat query text input field",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='[role="textbox"][aria-label="クエリボックス"]',
                    method="aria-label",
                    priority=1,
                    description="Chat input via aria-label",
                ),
                SelectorCandidate(
                    selector='[placeholder="入力を開始します..."]',
                    method="placeholder",
                    priority=2,
                    description="Chat input via placeholder",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="chat_send_button",
            description="Button to send a chat query",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='query-box button[aria-label="送信"]',
                    method="aria-label",
                    priority=1,
                    description="Chat send button via aria-label in query-box",
                ),
                SelectorCandidate(
                    selector='query-box [role="button"]:has-text("送信")',
                    method="role+text",
                    priority=3,
                    description="Chat send button via role and text",
                ),
                SelectorCandidate(
                    selector='button[ref="e2001"]',
                    method="ref",
                    priority=10,
                    description="Chat send button via ref",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.FRAGILE,
                last_verified=_VERIFIED_DATE,
                notes="ref value is fragile; aria-label is preferred",
            ),
        ),
        SelectorGroup(
            name="chat_copy_response_button",
            description="Button to copy AI response to clipboard",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="モデルの回答をクリップボードにコピー"]',
                    method="aria-label",
                    priority=1,
                    description="Copy response button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="chat_save_to_note_button",
            description="Button to save chat response to notes",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="メッセージをメモに保存"]',
                    method="aria-label",
                    priority=1,
                    description="Save to note button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="chat_settings_button",
            description="Button to open chat settings dialog",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="ノートブックを設定"]',
                    method="aria-label",
                    priority=1,
                    description="Chat settings button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="chat_options_menu_button",
            description="Chat options menu button (three dots)",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="チャット オプション"]',
                    method="aria-label",
                    priority=1,
                    description="Chat options menu via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="chat_clear_history_menuitem",
            description="Menu item to clear chat history",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("チャットの履歴を削除")',
                    method="role+text",
                    priority=1,
                    description="Clear history menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="chat_settings_save_button",
            description="Save button in chat settings dialog",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("設定を保存")',
                    method="role+text",
                    priority=1,
                    description="Settings save button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="chat_settings_close_button",
            description="Close button in chat settings dialog",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="チャット設定を閉じる"]',
                    method="aria-label",
                    priority=1,
                    description="Settings close button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="chat_summary_copy_button",
            description="Button to copy notebook summary",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="概要をコピー"]',
                    method="aria-label",
                    priority=1,
                    description="Copy summary button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
    ]


def _build_audio_selectors() -> list[SelectorGroup]:
    """Build selector groups for Audio Overview operations.

    Returns
    -------
    list[SelectorGroup]
        Selector groups for Audio Overview generation.
    """
    return [
        SelectorGroup(
            name="audio_overview_button",
            description="Button to start Audio Overview generation",
            group="audio",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("Audio overview")',
                    method="role+text",
                    priority=1,
                    description="Audio Overview button via role and text",
                ),
                SelectorCandidate(
                    selector='button[ref="e1960"]',
                    method="ref",
                    priority=10,
                    description="Audio Overview button via ref",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.FRAGILE,
                last_verified=_VERIFIED_DATE,
                notes="ref value is fragile; role+text is preferred",
            ),
        ),
        SelectorGroup(
            name="audio_customize_input",
            description="Audio Overview customization text input",
            group="audio",
            candidates=[
                SelectorCandidate(
                    selector='[role="textbox"][aria-label="カスタマイズ"]',
                    method="aria-label",
                    priority=1,
                    description="Customize input via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
    ]


def _build_studio_selectors() -> list[SelectorGroup]:
    """Build selector groups for Studio content generation operations.

    Returns
    -------
    list[SelectorGroup]
        Selector groups for Studio features (report, infographic, slides, etc.).
    """
    return [
        SelectorGroup(
            name="studio_report_button",
            description="Button to generate a report in Studio",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("レポート")',
                    method="role+text",
                    priority=1,
                    description="Report button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_infographic_button",
            description="Button to generate an infographic in Studio",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("インフォグラフィック")',
                    method="role+text",
                    priority=1,
                    description="Infographic button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_slides_button",
            description="Button to generate slides in Studio",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("スライド資料")',
                    method="role+text",
                    priority=1,
                    description="Slides button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_data_table_button",
            description="Button to generate a data table in Studio",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("Data Table")',
                    method="role+text",
                    priority=1,
                    description="Data Table button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_more_options_button",
            description="More options menu button in Studio viewer",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="その他のオプション"]',
                    method="aria-label",
                    priority=1,
                    description="More options button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_download_menuitem",
            description="Download menu item in Studio viewer",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("ダウンロード")',
                    method="role+text",
                    priority=1,
                    description="Download menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_report_format_briefing",
            description="Report format: briefing document",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("概要説明資料")',
                    method="role+text",
                    priority=1,
                    description="Briefing doc format button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="Format names may change with localization",
            ),
        ),
        SelectorGroup(
            name="studio_report_format_study_guide",
            description="Report format: study guide",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("学習ガイド")',
                    method="role+text",
                    priority=1,
                    description="Study guide format button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_report_format_blog",
            description="Report format: blog post",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("ブログ投稿")',
                    method="role+text",
                    priority=1,
                    description="Blog post format button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_copy_report_button",
            description="Button to copy report content with formatting",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector=(
                        'button[aria-label="書式設定を保持したままコンテンツをコピー"]'
                    ),
                    method="aria-label",
                    priority=1,
                    description="Copy report button via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_report_viewer",
            description="Report content viewer element",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector="labs-tailwind-doc-viewer",
                    method="tag",
                    priority=1,
                    description="Report viewer custom element",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="Custom element tag name is relatively stable",
            ),
        ),
        SelectorGroup(
            name="studio_close_viewer_report",
            description="Close button for report viewer",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="レポートビューアを閉じる"]',
                    method="aria-label",
                    priority=1,
                    description="Close report viewer via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_close_viewer_slides",
            description="Close button for slides viewer",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="スライド資料を閉じる"]',
                    method="aria-label",
                    priority=1,
                    description="Close slides viewer via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="studio_close_viewer_table",
            description="Close button for table viewer",
            group="studio",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="表を閉じる"]',
                    method="aria-label",
                    priority=1,
                    description="Close table viewer via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
    ]


def _build_note_selectors() -> list[SelectorGroup]:
    """Build selector groups for note management operations.

    Returns
    -------
    list[SelectorGroup]
        Selector groups for note creation, reading, and deletion.
    """
    return [
        SelectorGroup(
            name="note_add_button",
            description="Button to create a new note",
            group="note",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="メモを追加します"]',
                    method="aria-label",
                    priority=1,
                    description="Add note button via aria-label",
                ),
                SelectorCandidate(
                    selector='[role="button"]:has-text("メモを追加します")',
                    method="role+text",
                    priority=3,
                    description="Add note button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="note_title_input",
            description="Input field for note title",
            group="note",
            candidates=[
                SelectorCandidate(
                    selector='[role="textbox"][aria-label="メモのタイトルを編集可能"]',
                    method="aria-label",
                    priority=1,
                    description="Note title input via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="note_editor_manual",
            description="Content editor for manually created notes",
            group="note",
            candidates=[
                SelectorCandidate(
                    selector="rich-text-editor.note-editor [contenteditable=true]",
                    method="contenteditable",
                    priority=1,
                    description="Manual note editor via contenteditable",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="ProseMirror editor, CSS class may change",
            ),
        ),
        SelectorGroup(
            name="note_viewer_readonly",
            description="Readonly viewer for chat-saved notes",
            group="note",
            candidates=[
                SelectorCandidate(
                    selector="labs-tailwind-doc-viewer.note-editor--readonly",
                    method="class",
                    priority=1,
                    description="Readonly note viewer via class",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="Custom element class may change",
            ),
        ),
        SelectorGroup(
            name="note_delete_button",
            description="Button to delete a note",
            group="note",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="メモを削除"]',
                    method="aria-label",
                    priority=1,
                    description="Delete note button via aria-label",
                ),
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("削除")',
                    method="role+text",
                    priority=3,
                    description="Delete menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="note_delete_confirm_button",
            description="Confirmation button for note deletion",
            group="note",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("削除の確認")',
                    method="role+text",
                    priority=1,
                    description="Delete confirm button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
    ]


def _build_search_selectors() -> list[SelectorGroup]:
    """Build selector groups for web search/research operations.

    Returns
    -------
    list[SelectorGroup]
        Selector groups for web search, Fast Research, and Deep Research.
    """
    return [
        SelectorGroup(
            name="search_query_input",
            description="Search query input field for source discovery",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector=(
                        '[role="textbox"]'
                        '[aria-label="入力されたクエリをもとにソースを検出する"]'
                    ),
                    method="aria-label",
                    priority=1,
                    description="Search query input via aria-label",
                ),
                SelectorCandidate(
                    selector='[placeholder="ウェブで新しいソースを検索"]',
                    method="placeholder",
                    priority=2,
                    description="Fast Research placeholder",
                ),
                SelectorCandidate(
                    selector='[placeholder="調べたい内容を入力してください"]',
                    method="placeholder",
                    priority=3,
                    description="Deep Research placeholder",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_source_type_web",
            description="Source type dropdown: Web option",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("ウェブ")',
                    method="role+text",
                    priority=1,
                    description="Web source type menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_source_type_drive",
            description="Source type dropdown: Drive option",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("ドライブ")',
                    method="role+text",
                    priority=1,
                    description="Drive source type menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_mode_fast",
            description="Research mode: Fast Research",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("Fast Research")',
                    method="role+text",
                    priority=1,
                    description="Fast Research menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_mode_deep",
            description="Research mode: Deep Research",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='[role="menuitem"]:has-text("Deep Research")',
                    method="role+text",
                    priority=1,
                    description="Deep Research menu item via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_fast_complete",
            description="Fast Research completion message",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='text="高速リサーチが完了しました！"',
                    method="text",
                    priority=1,
                    description="Fast Research complete message via text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="Completion message text may change",
            ),
        ),
        SelectorGroup(
            name="search_deep_complete",
            description="Deep Research completion message",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='text="ディープリサーチが完了しました！"',
                    method="text",
                    priority=1,
                    description="Deep Research complete message via text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=_VERIFIED_DATE,
                notes="Completion message text is estimated (not fully verified)",
            ),
        ),
        SelectorGroup(
            name="search_stop_button",
            description="Button to stop Deep Research in progress",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="ソース検出を停止"]',
                    method="aria-label",
                    priority=1,
                    description="Stop research button via aria-label",
                ),
                SelectorCandidate(
                    selector='[role="button"]:has-text("ソース検出を停止")',
                    method="role+text",
                    priority=3,
                    description="Stop research button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_view_sources_button",
            description="Button to view all search results",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("ソースを表示")',
                    method="role+text",
                    priority=1,
                    description="View sources button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_import_button",
            description="Button to import selected search results",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("インポート")',
                    method="role+text",
                    priority=1,
                    description="Import button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_cancel_confirm_button",
            description="Confirm button in Deep Research cancel dialog",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='[role="button"]:has-text("確認")',
                    method="role+text",
                    priority=1,
                    description="Cancel confirm button via role and text",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
        SelectorGroup(
            name="search_progress_bar",
            description="Progress bar during source loading",
            group="search",
            candidates=[
                SelectorCandidate(
                    selector='[role="progressbar"][aria-label="ソースを読み込んでいます"]',
                    method="aria-label",
                    priority=1,
                    description="Loading progress bar via aria-label",
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=_VERIFIED_DATE,
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# SelectorManager
# ---------------------------------------------------------------------------


class SelectorManager:
    """Registry of all NotebookLM CSS selectors with fallback support.

    Provides priority-ordered access to selector candidates for each
    UI element, organized by functional group.

    The manager is initialized with all verified selectors from the
    NotebookLM UI and provides methods for retrieving selectors
    by group name or functional category.

    Examples
    --------
    >>> manager = SelectorManager()
    >>> # Get all selectors for chat send button
    >>> candidates = manager.get_candidates("chat_send_button")
    >>> for c in candidates:
    ...     print(f"[{c.priority}] {c.method}: {c.selector}")

    >>> # Get all selector groups for a functional category
    >>> chat_groups = manager.get_groups_by_category("chat")
    >>> for g in chat_groups:
    ...     print(f"{g.name}: {len(g.candidates)} candidates")
    """

    def __init__(self) -> None:
        all_groups: list[SelectorGroup] = [
            *_build_notebook_selectors(),
            *_build_source_selectors(),
            *_build_chat_selectors(),
            *_build_audio_selectors(),
            *_build_studio_selectors(),
            *_build_note_selectors(),
            *_build_search_selectors(),
        ]
        self._groups: dict[str, SelectorGroup] = {g.name: g for g in all_groups}

        logger.debug(
            "SelectorManager initialized",
            total_groups=len(self._groups),
            categories=list(self.get_all_categories()),
        )

    # ---- Group-level access ----

    def get_group(self, name: str) -> SelectorGroup | None:
        """Get a selector group by its unique name.

        Parameters
        ----------
        name : str
            Unique identifier for the selector group.

        Returns
        -------
        SelectorGroup | None
            The matching selector group, or None if not found.
        """
        return self._groups.get(name)

    def get_all_groups(self) -> list[SelectorGroup]:
        """Get all registered selector groups.

        Returns
        -------
        list[SelectorGroup]
            All selector groups in the registry.
        """
        return list(self._groups.values())

    def get_groups_by_category(self, category: str) -> list[SelectorGroup]:
        """Get all selector groups in a functional category.

        Parameters
        ----------
        category : str
            Functional category name (notebook, source, chat, etc.).

        Returns
        -------
        list[SelectorGroup]
            All selector groups in the specified category.
        """
        return [g for g in self._groups.values() if g.group == category]

    def get_all_categories(self) -> set[str]:
        """Get all unique functional category names.

        Returns
        -------
        set[str]
            Set of all category names (e.g., notebook, source, chat, ...).
        """
        return {g.group for g in self._groups.values()}

    # ---- Candidate-level access ----

    def get_candidates(self, group_name: str) -> list[SelectorCandidate]:
        """Get selector candidates for a group, sorted by priority.

        Parameters
        ----------
        group_name : str
            Name of the selector group.

        Returns
        -------
        list[SelectorCandidate]
            Candidates sorted by priority (ascending), or empty list
            if the group does not exist.
        """
        group = self._groups.get(group_name)
        if group is None:
            return []
        return group.sorted_candidates

    def get_selector_strings(self, group_name: str) -> list[str]:
        """Get selector strings for a group, sorted by priority.

        Convenience method that returns only the selector strings
        without the full SelectorCandidate objects.

        Parameters
        ----------
        group_name : str
            Name of the selector group.

        Returns
        -------
        list[str]
            Selector strings sorted by priority (ascending),
            or empty list if the group does not exist.
        """
        return [c.selector for c in self.get_candidates(group_name)]

    # ---- Metadata access ----

    def get_metadata(self, group_name: str) -> SelectorMetadata | None:
        """Get metadata for a selector group.

        Parameters
        ----------
        group_name : str
            Name of the selector group.

        Returns
        -------
        SelectorMetadata | None
            Metadata for the group, or None if the group does not exist.
        """
        group = self._groups.get(group_name)
        if group is None:
            return None
        return group.metadata


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "SelectorCandidate",
    "SelectorGroup",
    "SelectorManager",
    "SelectorMetadata",
    "StabilityLevel",
]
