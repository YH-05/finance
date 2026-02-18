"""Tests for ca_strategy batch module.

Tests for CheckpointManager and BatchProcessor covering:
- Checkpoint save/load
- Batch processing with partial failure tolerance
- Retry with exponential backoff
- Checkpoint-based resume (skip already-processed items)
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import pytest

from dev.ca_strategy.batch import BatchProcessor, CheckpointManager

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# CheckpointManager
# =============================================================================
class TestCheckpointManager:
    """CheckpointManager save/load tests."""

    def test_正常系_初期状態は空のcompleted_keysを返す(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path / "cp.json")
        assert mgr.completed_keys == set()

    def test_正常系_saveで進捗をJSONに保存できる(self, tmp_path: Path) -> None:
        cp_path = tmp_path / "cp.json"
        mgr = CheckpointManager(cp_path)
        mgr.mark_completed("AAPL")
        mgr.mark_completed("MSFT")
        mgr.save()

        assert cp_path.exists()
        data = json.loads(cp_path.read_text())
        assert set(data["completed"]) == {"AAPL", "MSFT"}

    def test_正常系_loadで保存済み進捗を復元できる(self, tmp_path: Path) -> None:
        cp_path = tmp_path / "cp.json"
        # Pre-populate checkpoint file
        cp_path.write_text(json.dumps({"completed": ["AAPL", "MSFT", "GOOG"]}))

        mgr = CheckpointManager(cp_path)
        mgr.load()
        assert mgr.completed_keys == {"AAPL", "MSFT", "GOOG"}

    def test_正常系_ファイルが存在しない場合loadは空のままで例外を出さない(
        self, tmp_path: Path
    ) -> None:
        cp_path = tmp_path / "nonexistent.json"
        mgr = CheckpointManager(cp_path)
        mgr.load()  # Should not raise
        assert mgr.completed_keys == set()

    def test_正常系_mark_completedで個別キーを追加できる(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path / "cp.json")
        mgr.mark_completed("AAPL")
        assert "AAPL" in mgr.completed_keys

    def test_正常系_is_completedで完了済みかどうかを判定できる(
        self, tmp_path: Path
    ) -> None:
        mgr = CheckpointManager(tmp_path / "cp.json")
        mgr.mark_completed("AAPL")
        assert mgr.is_completed("AAPL") is True
        assert mgr.is_completed("MSFT") is False

    def test_正常系_clearで進捗をリセットできる(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path / "cp.json")
        mgr.mark_completed("AAPL")
        mgr.mark_completed("MSFT")
        mgr.clear()
        assert mgr.completed_keys == set()

    def test_正常系_save_and_loadのラウンドトリップ(self, tmp_path: Path) -> None:
        cp_path = tmp_path / "cp.json"
        mgr1 = CheckpointManager(cp_path)
        mgr1.mark_completed("AAPL")
        mgr1.mark_completed("GOOG")
        mgr1.save()

        mgr2 = CheckpointManager(cp_path)
        mgr2.load()
        assert mgr2.completed_keys == {"AAPL", "GOOG"}


# =============================================================================
# BatchProcessor
# =============================================================================
class TestBatchProcessor:
    """BatchProcessor tests."""

    def test_正常系_全アイテムを正常に処理できる(self) -> None:
        processor = BatchProcessor[str, int](
            process_fn=lambda x: len(x),
            max_workers=2,
        )
        results = processor.process(["abc", "de", "f"])
        assert results == {"abc": 3, "de": 2, "f": 1}

    def test_正常系_部分失敗時も継続しExceptionを結果に格納する(self) -> None:
        def _process(item: str) -> int:
            if item == "fail":
                msg = "intentional failure"
                raise ValueError(msg)
            return len(item)

        processor = BatchProcessor[str, int](
            process_fn=_process,
            max_workers=2,
        )
        results = processor.process(["ok", "fail", "abc"])
        assert results["ok"] == 2
        assert results["abc"] == 3
        assert isinstance(results["fail"], Exception)
        assert "intentional failure" in str(results["fail"])

    def test_正常系_チェックポイント付きバッチ処理で全件処理する(
        self, tmp_path: Path
    ) -> None:
        cp_path = tmp_path / "cp.json"
        processor = BatchProcessor[str, int](
            process_fn=lambda x: len(x),
            max_workers=2,
        )
        results = processor.process_with_checkpoint(
            items=["abc", "de", "f"],
            key_fn=lambda x: x,
            checkpoint_path=cp_path,
        )
        assert results == {"abc": 3, "de": 2, "f": 1}

    def test_正常系_チェックポイントからの再開で既処理アイテムをスキップする(
        self, tmp_path: Path
    ) -> None:
        cp_path = tmp_path / "cp.json"
        # Pre-populate checkpoint: "abc" is already done
        cp_path.write_text(json.dumps({"completed": ["abc"]}))

        call_count: dict[str, int] = {}

        def _track_process(item: str) -> int:
            call_count[item] = call_count.get(item, 0) + 1
            return len(item)

        processor = BatchProcessor[str, int](
            process_fn=_track_process,
            max_workers=1,
        )
        results = processor.process_with_checkpoint(
            items=["abc", "de", "f"],
            key_fn=lambda x: x,
            checkpoint_path=cp_path,
        )
        # "abc" was skipped (not in call_count)
        assert "abc" not in call_count
        # Others were processed
        assert call_count["de"] == 1
        assert call_count["f"] == 1
        # Result includes only newly processed items
        assert results == {"de": 2, "f": 1}

    def test_正常系_チェックポイント処理後にsaveが呼ばれる(
        self, tmp_path: Path
    ) -> None:
        cp_path = tmp_path / "cp.json"
        processor = BatchProcessor[str, int](
            process_fn=lambda x: len(x),
            max_workers=1,
        )
        processor.process_with_checkpoint(
            items=["abc", "de"],
            key_fn=lambda x: x,
            checkpoint_path=cp_path,
        )
        # Checkpoint file should exist with completed keys
        assert cp_path.exists()
        data = json.loads(cp_path.read_text())
        assert set(data["completed"]) >= {"abc", "de"}

    def test_正常系_空リストを渡すと空の結果を返す(self) -> None:
        processor = BatchProcessor[str, int](
            process_fn=lambda x: len(x),
            max_workers=2,
        )
        results = processor.process([])
        assert results == {}

    def test_正常系_max_workersのデフォルト値は5(self) -> None:
        processor = BatchProcessor[str, int](
            process_fn=lambda x: len(x),
        )
        assert processor._max_workers == 5

    def test_正常系_key_fnでカスタムキーを指定できる(self, tmp_path: Path) -> None:
        items = [("AAPL", "Apple Inc"), ("MSFT", "Microsoft Corp")]
        processor = BatchProcessor[tuple[str, str], str](
            process_fn=lambda x: x[1].upper(),
            max_workers=1,
        )
        results = processor.process_with_checkpoint(
            items=items,
            key_fn=lambda x: x[0],
            checkpoint_path=tmp_path / "cp.json",
        )
        assert results == {"AAPL": "APPLE INC", "MSFT": "MICROSOFT CORP"}


# =============================================================================
# Retry logic
# =============================================================================
class TestBatchProcessorRetry:
    """Retry with exponential backoff tests."""

    def test_正常系_リトライ成功で最終的に結果を返す(self) -> None:
        call_count = {"n": 0}

        def _flaky(item: str) -> int:
            call_count["n"] += 1
            if call_count["n"] < 3:
                msg = "transient error"
                raise RuntimeError(msg)
            return len(item)

        processor = BatchProcessor[str, int](
            process_fn=_flaky,
            max_workers=1,
            max_retries=3,
        )
        results = processor.process(["abc"])
        assert results["abc"] == 3
        assert call_count["n"] == 3

    def test_異常系_最大リトライ回数を超えるとExceptionが結果に格納される(
        self,
    ) -> None:
        def _always_fail(item: str) -> int:
            msg = "permanent error"
            raise RuntimeError(msg)

        processor = BatchProcessor[str, int](
            process_fn=_always_fail,
            max_workers=1,
            max_retries=3,
        )
        results = processor.process(["abc"])
        assert isinstance(results["abc"], Exception)
        assert "permanent error" in str(results["abc"])

    def test_正常系_指数バックオフで待機時間が増加する(self) -> None:
        call_times: list[float] = []

        def _fail_twice(item: str) -> int:
            call_times.append(time.monotonic())
            if len(call_times) < 3:
                msg = "transient"
                raise RuntimeError(msg)
            return len(item)

        processor = BatchProcessor[str, int](
            process_fn=_fail_twice,
            max_workers=1,
            max_retries=3,
            base_delay=0.05,  # Small delay for fast tests
        )
        results = processor.process(["abc"])
        assert results["abc"] == 3
        assert len(call_times) == 3
        # Second delay should be >= first delay (exponential backoff)
        delay_1 = call_times[1] - call_times[0]
        delay_2 = call_times[2] - call_times[1]
        assert delay_1 >= 0.04  # ~0.05s base
        assert delay_2 >= delay_1 * 0.8  # Allow some tolerance

    def test_正常系_デフォルトのmax_retriesは3(self) -> None:
        processor = BatchProcessor[str, int](
            process_fn=lambda x: len(x),
        )
        assert processor._max_retries == 3

    def test_正常系_リトライなしでもmax_retries_0で即時失敗(self) -> None:
        def _fail(item: str) -> int:
            msg = "fail"
            raise RuntimeError(msg)

        processor = BatchProcessor[str, int](
            process_fn=_fail,
            max_workers=1,
            max_retries=0,
        )
        results = processor.process(["abc"])
        assert isinstance(results["abc"], Exception)


# =============================================================================
# Edge cases
# =============================================================================
class TestBatchProcessorEdgeCases:
    """Edge case tests for BatchProcessor."""

    def test_エッジケース_1アイテムのバッチ処理(self) -> None:
        processor = BatchProcessor[str, int](
            process_fn=lambda x: len(x),
            max_workers=1,
        )
        results = processor.process(["hello"])
        assert results == {"hello": 5}

    def test_エッジケース_全アイテム失敗のバッチ処理(self) -> None:
        def _fail(item: str) -> int:
            msg = f"error for {item}"
            raise RuntimeError(msg)

        processor = BatchProcessor[str, int](
            process_fn=_fail,
            max_workers=2,
            max_retries=0,
        )
        results = processor.process(["a", "b", "c"])
        assert all(isinstance(v, Exception) for v in results.values())

    def test_エッジケース_processのデフォルトkey_fnはstr変換(self) -> None:
        processor = BatchProcessor[int, int](
            process_fn=lambda x: x * 2,
            max_workers=1,
        )
        results = processor.process([1, 2, 3])
        assert results == {"1": 2, "2": 4, "3": 6}
