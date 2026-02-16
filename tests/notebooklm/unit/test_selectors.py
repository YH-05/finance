"""Unit tests for notebooklm.selectors module."""

from datetime import date

import pytest
from pydantic import ValidationError

from notebooklm.selectors import (
    SelectorCandidate,
    SelectorGroup,
    SelectorManager,
    SelectorMetadata,
    StabilityLevel,
)

# ---------------------------------------------------------------------------
# SelectorCandidate tests
# ---------------------------------------------------------------------------


class TestSelectorCandidate:
    """Tests for SelectorCandidate model."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        candidate = SelectorCandidate(
            selector='button[aria-label="送信"]',
            method="aria-label",
            priority=1,
        )
        assert candidate.selector == 'button[aria-label="送信"]'
        assert candidate.method == "aria-label"
        assert candidate.priority == 1
        assert candidate.description is None

    def test_正常系_全フィールド指定で作成できる(self) -> None:
        candidate = SelectorCandidate(
            selector='button[aria-label="送信"]',
            method="aria-label",
            priority=1,
            description="Chat send button via aria-label",
        )
        assert candidate.description == "Chat send button via aria-label"

    def test_正常系_frozenモデルである(self) -> None:
        candidate = SelectorCandidate(
            selector='button[aria-label="送信"]',
            method="aria-label",
            priority=1,
        )
        with pytest.raises(ValidationError):
            candidate.selector = "changed"  # type: ignore[misc]

    def test_異常系_空のselectorでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            SelectorCandidate(selector="", method="aria-label", priority=1)

    def test_異常系_空のmethodでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            SelectorCandidate(selector="button", method="", priority=1)

    def test_異常系_負のpriorityでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            SelectorCandidate(selector="button", method="aria-label", priority=-1)


# ---------------------------------------------------------------------------
# SelectorMetadata tests
# ---------------------------------------------------------------------------


class TestSelectorMetadata:
    """Tests for SelectorMetadata model."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        metadata = SelectorMetadata(
            stability=StabilityLevel.STABLE,
            last_verified=date(2026, 2, 16),
        )
        assert metadata.stability == StabilityLevel.STABLE
        assert metadata.last_verified == date(2026, 2, 16)
        assert metadata.notes is None

    def test_正常系_全フィールド指定で作成できる(self) -> None:
        metadata = SelectorMetadata(
            stability=StabilityLevel.FRAGILE,
            last_verified=date(2026, 2, 16),
            notes="ref attributes change frequently",
        )
        assert metadata.notes == "ref attributes change frequently"

    def test_正常系_全安定性レベルが使用できる(self) -> None:
        for level in StabilityLevel:
            metadata = SelectorMetadata(
                stability=level,
                last_verified=date(2026, 2, 16),
            )
            assert metadata.stability == level

    def test_正常系_frozenモデルである(self) -> None:
        metadata = SelectorMetadata(
            stability=StabilityLevel.STABLE,
            last_verified=date(2026, 2, 16),
        )
        with pytest.raises(ValidationError):
            metadata.stability = StabilityLevel.FRAGILE  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SelectorGroup tests
# ---------------------------------------------------------------------------


class TestSelectorGroup:
    """Tests for SelectorGroup model."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        group = SelectorGroup(
            name="chat_send_button",
            description="Chat send button",
            group="chat",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="送信"]',
                    method="aria-label",
                    priority=1,
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=date(2026, 2, 16),
            ),
        )
        assert group.name == "chat_send_button"
        assert group.group == "chat"
        assert len(group.candidates) == 1

    def test_正常系_複数のcandidateを持てる(self) -> None:
        group = SelectorGroup(
            name="create_notebook_button",
            description="Create notebook button",
            group="notebook",
            candidates=[
                SelectorCandidate(
                    selector='button[aria-label="新規作成"]',
                    method="aria-label",
                    priority=1,
                ),
                SelectorCandidate(
                    selector='button[ref="e78"]',
                    method="ref",
                    priority=10,
                ),
                SelectorCandidate(
                    selector='button[ref="e135"]',
                    method="ref",
                    priority=11,
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.MODERATE,
                last_verified=date(2026, 2, 16),
            ),
        )
        assert len(group.candidates) == 3

    def test_正常系_candidatesがpriority順でソートされている(self) -> None:
        group = SelectorGroup(
            name="test",
            description="Test group",
            group="notebook",
            candidates=[
                SelectorCandidate(
                    selector='button[ref="e78"]',
                    method="ref",
                    priority=10,
                ),
                SelectorCandidate(
                    selector='button[aria-label="送信"]',
                    method="aria-label",
                    priority=1,
                ),
                SelectorCandidate(
                    selector='button[role="button"]',
                    method="role",
                    priority=5,
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=date(2026, 2, 16),
            ),
        )
        priorities = [c.priority for c in group.sorted_candidates]
        assert priorities == [1, 5, 10]

    def test_異常系_空のcandidatesでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            SelectorGroup(
                name="empty",
                description="Empty group",
                group="notebook",
                candidates=[],
                metadata=SelectorMetadata(
                    stability=StabilityLevel.STABLE,
                    last_verified=date(2026, 2, 16),
                ),
            )

    def test_異常系_空のnameでValidationError(self) -> None:
        with pytest.raises(ValidationError):
            SelectorGroup(
                name="",
                description="Test",
                group="notebook",
                candidates=[
                    SelectorCandidate(
                        selector="button",
                        method="role",
                        priority=1,
                    ),
                ],
                metadata=SelectorMetadata(
                    stability=StabilityLevel.STABLE,
                    last_verified=date(2026, 2, 16),
                ),
            )

    def test_正常系_frozenモデルである(self) -> None:
        group = SelectorGroup(
            name="test",
            description="Test",
            group="notebook",
            candidates=[
                SelectorCandidate(
                    selector="button",
                    method="role",
                    priority=1,
                ),
            ],
            metadata=SelectorMetadata(
                stability=StabilityLevel.STABLE,
                last_verified=date(2026, 2, 16),
            ),
        )
        with pytest.raises(ValidationError):
            group.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SelectorManager tests
# ---------------------------------------------------------------------------


class TestSelectorManager:
    """Tests for SelectorManager class."""

    def test_正常系_グループ名でSelectorGroupを取得できる(self) -> None:
        manager = SelectorManager()
        group = manager.get_group("chat_send_button")
        assert group is not None
        assert group.name == "chat_send_button"

    def test_正常系_存在しないグループ名でNoneを返す(self) -> None:
        manager = SelectorManager()
        group = manager.get_group("nonexistent_group")
        assert group is None

    def test_正常系_機能グループでフィルタできる(self) -> None:
        manager = SelectorManager()
        chat_groups = manager.get_groups_by_category("chat")
        assert len(chat_groups) > 0
        for group in chat_groups:
            assert group.group == "chat"

    def test_正常系_7つの機能グループが存在する(self) -> None:
        manager = SelectorManager()
        categories = manager.get_all_categories()
        expected_categories = {
            "notebook",
            "source",
            "chat",
            "audio",
            "studio",
            "note",
            "search",
        }
        assert expected_categories.issubset(categories)

    def test_正常系_candidatesがpriority順で返される(self) -> None:
        manager = SelectorManager()
        candidates = manager.get_candidates("chat_send_button")
        assert len(candidates) > 0
        priorities = [c.priority for c in candidates]
        assert priorities == sorted(priorities)

    def test_正常系_セレクター文字列のリストを取得できる(self) -> None:
        manager = SelectorManager()
        selectors = manager.get_selector_strings("chat_send_button")
        assert len(selectors) > 0
        assert all(isinstance(s, str) for s in selectors)

    def test_正常系_存在しないグループのcandidatesは空リスト(self) -> None:
        manager = SelectorManager()
        candidates = manager.get_candidates("nonexistent_group")
        assert candidates == []

    def test_正常系_全グループを取得できる(self) -> None:
        manager = SelectorManager()
        all_groups = manager.get_all_groups()
        assert len(all_groups) > 0

    def test_正常系_fragileセレクターには代替が存在する(self) -> None:
        """fragile レベルのセレクターには必ず代替セレクターが定義されていること."""
        manager = SelectorManager()
        for group in manager.get_all_groups():
            if group.metadata.stability == StabilityLevel.FRAGILE:
                assert len(group.candidates) >= 2, (
                    f"Fragile group '{group.name}' must have at least 2 "
                    f"candidate selectors, but has {len(group.candidates)}"
                )

    def test_正常系_notebookグループにセレクターが定義されている(self) -> None:
        manager = SelectorManager()
        groups = manager.get_groups_by_category("notebook")
        assert len(groups) > 0

    def test_正常系_sourceグループにセレクターが定義されている(self) -> None:
        manager = SelectorManager()
        groups = manager.get_groups_by_category("source")
        assert len(groups) > 0

    def test_正常系_chatグループにセレクターが定義されている(self) -> None:
        manager = SelectorManager()
        groups = manager.get_groups_by_category("chat")
        assert len(groups) > 0

    def test_正常系_audioグループにセレクターが定義されている(self) -> None:
        manager = SelectorManager()
        groups = manager.get_groups_by_category("audio")
        assert len(groups) > 0

    def test_正常系_studioグループにセレクターが定義されている(self) -> None:
        manager = SelectorManager()
        groups = manager.get_groups_by_category("studio")
        assert len(groups) > 0

    def test_正常系_noteグループにセレクターが定義されている(self) -> None:
        manager = SelectorManager()
        groups = manager.get_groups_by_category("note")
        assert len(groups) > 0

    def test_正常系_searchグループにセレクターが定義されている(self) -> None:
        manager = SelectorManager()
        groups = manager.get_groups_by_category("search")
        assert len(groups) > 0

    def test_正常系_metadataを取得できる(self) -> None:
        manager = SelectorManager()
        metadata = manager.get_metadata("chat_send_button")
        assert metadata is not None
        assert isinstance(metadata.stability, StabilityLevel)
        assert isinstance(metadata.last_verified, date)

    def test_正常系_存在しないグループのmetadataはNone(self) -> None:
        manager = SelectorManager()
        metadata = manager.get_metadata("nonexistent_group")
        assert metadata is None

    def test_正常系_存在しないグループのselector_stringsは空リスト(self) -> None:
        manager = SelectorManager()
        selectors = manager.get_selector_strings("nonexistent_group")
        assert selectors == []
