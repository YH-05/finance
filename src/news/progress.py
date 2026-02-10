"""Progress callback for news workflow CLI output.

Provides a protocol for progress notifications and two implementations:
- ConsoleProgressCallback: Reproduces the original print() output (default)
- SilentCallback: No-op implementation for tests and batch jobs
"""

from __future__ import annotations

from typing import Any, Protocol


class ProgressCallback(Protocol):
    """News workflow progress notification protocol."""

    def on_stage_start(self, stage: str, description: str) -> None:
        """Notify that a workflow stage has started.

        Parameters
        ----------
        stage : str
            Stage identifier (e.g. "1/6", "2/6").
        description : str
            Human-readable stage description.
        """
        ...

    def on_progress(
        self,
        current: int,
        total: int,
        message: str,
        *,
        is_error: bool = False,
    ) -> None:
        """Notify item-level progress within a stage.

        Parameters
        ----------
        current : int
            Current item number (1-indexed).
        total : int
            Total number of items.
        message : str
            Progress message.
        is_error : bool
            Whether this progress item represents an error.
        """
        ...

    def on_stage_complete(
        self,
        stage: str,
        success: int,
        total: int,
        *,
        extra: str = "",
    ) -> None:
        """Notify that a workflow stage has completed.

        Parameters
        ----------
        stage : str
            Stage name in Japanese (e.g. "抽出", "要約").
        success : int
            Number of successfully processed items.
        total : int
            Total number of items.
        extra : str
            Additional info to append (e.g. elapsed time).
        """
        ...

    def on_info(self, message: str) -> None:
        """Notify a general informational message.

        Parameters
        ----------
        message : str
            Informational message to display.
        """
        ...

    def on_workflow_complete(self, result: Any) -> None:
        """Notify that the entire workflow has completed.

        Parameters
        ----------
        result : Any
            The WorkflowResult object.
        """
        ...


class ConsoleProgressCallback:
    """Default callback that reproduces original print() output."""

    def on_stage_start(self, stage: str, description: str) -> None:
        """Print stage header with visual separator."""
        print(f"\n{'=' * 60}")
        print(f"[{stage}] {description}")
        print(f"{'=' * 60}")

    def on_progress(
        self,
        current: int,
        total: int,
        message: str,
        *,
        is_error: bool = False,
    ) -> None:
        """Print progress line with count indicator."""
        prefix = "  ERROR" if is_error else "  "
        print(f"{prefix}[{current}/{total}] {message}")

    def on_stage_complete(
        self,
        stage: str,
        success: int,
        total: int,
        *,
        extra: str = "",
    ) -> None:
        """Print stage completion with success rate."""
        rate = (success / total * 100) if total > 0 else 0
        extra_str = f" {extra}" if extra else ""
        print(f"  -> {stage}\u5b8c\u4e86: {success}/{total} ({rate:.0f}%){extra_str}")

    def on_info(self, message: str) -> None:
        """Print informational message."""
        print(message)

    def on_workflow_complete(self, result: Any) -> None:
        """Print final workflow summary with stage timing and domain rates."""
        from news.models import PublicationStatus

        print(f"\n{'=' * 60}")
        print("ワークフロー完了")
        print(f"{'=' * 60}")
        print(f"  収集: {result.total_collected}件")
        if result.feed_errors:
            print(f"  フィードエラー: {len(result.feed_errors)}件")
        print(f"  抽出: {result.total_extracted}件")
        print(f"  要約: {result.total_summarized}件")
        if result.category_results:
            cat_published = sum(
                1
                for r in result.category_results
                if r.status == PublicationStatus.SUCCESS
            )
            print(f"  カテゴリ別公開: {cat_published}/{len(result.category_results)}件")
        else:
            print(f"  公開: {result.total_published}件")
        if result.total_early_duplicates > 0:
            print(f"  重複除外（早期）: {result.total_early_duplicates}件")
        if result.total_duplicates > 0:
            print(f"  重複（公開時）: {result.total_duplicates}件")
        print(f"  処理時間: {result.elapsed_seconds:.1f}秒")

        if result.stage_metrics:
            print("\n  ステージ別処理時間:")
            for sm in result.stage_metrics:
                print(f"    {sm.stage}: {sm.elapsed_seconds:.1f}秒 ({sm.item_count}件)")

        if result.domain_extraction_rates:
            print("\n  ドメイン別抽出成功率:")
            for dr in sorted(
                result.domain_extraction_rates, key=lambda x: x.success_rate
            ):
                print(
                    f"    {dr.domain}: {dr.success}/{dr.total} ({dr.success_rate:.0f}%)"
                )


class SilentCallback:
    """No-op callback for tests and batch jobs."""

    def on_stage_start(self, stage: str, description: str) -> None:
        """No-op."""

    def on_progress(
        self,
        current: int,
        total: int,
        message: str,
        *,
        is_error: bool = False,
    ) -> None:
        """No-op."""

    def on_stage_complete(
        self,
        stage: str,
        success: int,
        total: int,
        *,
        extra: str = "",
    ) -> None:
        """No-op."""

    def on_info(self, message: str) -> None:
        """No-op."""

    def on_workflow_complete(self, result: Any) -> None:
        """No-op."""


__all__ = [
    "ConsoleProgressCallback",
    "ProgressCallback",
    "SilentCallback",
]
