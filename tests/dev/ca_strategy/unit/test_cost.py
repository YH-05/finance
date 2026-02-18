"""Tests for ca_strategy cost module (LLM cost tracking).

Validates CostTracker class for tracking LLM API costs across
pipeline phases with Sonnet 4 pricing.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from dev.ca_strategy.cost import CostTracker


# =============================================================================
# CostTracker initialization
# =============================================================================
class TestCostTrackerInit:
    """CostTracker initialization tests."""

    def test_正常系_初期化で空のトラッカーが作成される(self) -> None:
        tracker = CostTracker()

        assert tracker.get_total_cost() == 0.0

    def test_正常系_カスタム上限でwarningが設定される(self) -> None:
        tracker = CostTracker(warning_threshold=100.0)

        assert tracker.warning_threshold == 100.0

    def test_正常系_デフォルトwarning閾値は50ドル(self) -> None:
        tracker = CostTracker()

        assert tracker.warning_threshold == 50.0


# =============================================================================
# CostTracker.record
# =============================================================================
class TestCostTrackerRecord:
    """CostTracker.record method tests."""

    def test_正常系_コスト記録ができる(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=1000, tokens_output=500)

        assert tracker.get_total_cost() > 0.0

    def test_正常系_同じフェーズに複数回記録できる(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=1000, tokens_output=500)
        cost_after_first = tracker.get_total_cost()

        tracker.record("phase1", tokens_input=1000, tokens_output=500)
        cost_after_second = tracker.get_total_cost()

        assert cost_after_second > cost_after_first

    def test_正常系_異なるフェーズに記録できる(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=1000, tokens_output=500)
        tracker.record("phase2", tokens_input=2000, tokens_output=1000)

        phase1_cost = tracker.get_phase_cost("phase1")
        phase2_cost = tracker.get_phase_cost("phase2")

        assert phase1_cost > 0.0
        assert phase2_cost > 0.0
        assert phase2_cost > phase1_cost

    def test_異常系_tokens_inputが負でValueError(self) -> None:
        tracker = CostTracker()

        with pytest.raises(ValueError, match="tokens_input"):
            tracker.record("phase1", tokens_input=-1, tokens_output=500)

    def test_異常系_tokens_outputが負でValueError(self) -> None:
        tracker = CostTracker()

        with pytest.raises(ValueError, match="tokens_output"):
            tracker.record("phase1", tokens_input=1000, tokens_output=-1)

    def test_異常系_phaseが空文字でValueError(self) -> None:
        tracker = CostTracker()

        with pytest.raises(ValueError, match="phase"):
            tracker.record("", tokens_input=1000, tokens_output=500)

    def test_エッジケース_tokens_input_0でも記録できる(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=0, tokens_output=500)

        assert tracker.get_total_cost() > 0.0

    def test_エッジケース_tokens_output_0でも記録できる(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=1000, tokens_output=0)

        assert tracker.get_total_cost() > 0.0


# =============================================================================
# CostTracker pricing
# =============================================================================
class TestCostTrackerPricing:
    """CostTracker Sonnet 4 pricing tests."""

    def test_正常系_Sonnet4価格_inputは3ドル_per_1Mtokens(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=1_000_000, tokens_output=0)

        assert tracker.get_total_cost() == pytest.approx(3.0)

    def test_正常系_Sonnet4価格_outputは15ドル_per_1Mtokens(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=0, tokens_output=1_000_000)

        assert tracker.get_total_cost() == pytest.approx(15.0)

    def test_正常系_複合コスト計算(self) -> None:
        tracker = CostTracker()

        # 1M input ($3) + 1M output ($15) = $18
        tracker.record("phase1", tokens_input=1_000_000, tokens_output=1_000_000)

        assert tracker.get_total_cost() == pytest.approx(18.0)

    def test_正常系_小さいトークン数のコスト(self) -> None:
        tracker = CostTracker()

        # 1000 input tokens = $0.003, 500 output tokens = $0.0075
        tracker.record("phase1", tokens_input=1000, tokens_output=500)

        expected = (1000 * 3.0 / 1_000_000) + (500 * 15.0 / 1_000_000)
        assert tracker.get_total_cost() == pytest.approx(expected)


# =============================================================================
# CostTracker.get_total_cost
# =============================================================================
class TestCostTrackerGetTotalCost:
    """CostTracker.get_total_cost method tests."""

    def test_正常系_全フェーズの合計を返す(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=1_000_000, tokens_output=0)
        tracker.record("phase2", tokens_input=0, tokens_output=1_000_000)

        # phase1: $3, phase2: $15 -> total: $18
        assert tracker.get_total_cost() == pytest.approx(18.0)

    def test_正常系_記録なしで0を返す(self) -> None:
        tracker = CostTracker()

        assert tracker.get_total_cost() == 0.0


# =============================================================================
# CostTracker.get_phase_cost
# =============================================================================
class TestCostTrackerGetPhaseCost:
    """CostTracker.get_phase_cost method tests."""

    def test_正常系_特定フェーズのコストを返す(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=1_000_000, tokens_output=0)
        tracker.record("phase2", tokens_input=0, tokens_output=1_000_000)

        assert tracker.get_phase_cost("phase1") == pytest.approx(3.0)
        assert tracker.get_phase_cost("phase2") == pytest.approx(15.0)

    def test_正常系_存在しないフェーズで0を返す(self) -> None:
        tracker = CostTracker()

        assert tracker.get_phase_cost("nonexistent") == 0.0

    def test_正常系_同一フェーズの累積コスト(self) -> None:
        tracker = CostTracker()

        tracker.record("phase1", tokens_input=500_000, tokens_output=0)
        tracker.record("phase1", tokens_input=500_000, tokens_output=0)

        # 500K + 500K = 1M input tokens = $3
        assert tracker.get_phase_cost("phase1") == pytest.approx(3.0)


# =============================================================================
# CostTracker warning
# =============================================================================
class TestCostTrackerWarning:
    """CostTracker warning threshold tests."""

    def test_正常系_閾値超過でwarningログが出力される(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        tracker = CostTracker(warning_threshold=10.0)

        # Record enough to exceed $10 threshold
        # 1M output = $15 > $10
        tracker.record("phase1", tokens_input=0, tokens_output=1_000_000)

        assert any("warning" in r.levelname.lower() for r in caplog.records) or any(
            "cost" in r.message.lower() and "exceed" in r.message.lower()
            for r in caplog.records
        )

    def test_正常系_閾値以下ではwarningログなし(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        tracker = CostTracker(warning_threshold=50.0)

        # Record small amount: $0.003
        tracker.record("phase1", tokens_input=1000, tokens_output=0)

        warning_records = [
            r
            for r in caplog.records
            if r.levelname == "WARNING" and "cost" in r.message.lower()
        ]
        assert len(warning_records) == 0


# =============================================================================
# CostTracker.save / load
# =============================================================================
class TestCostTrackerPersistence:
    """CostTracker save/load tests."""

    def test_正常系_JSONファイルに保存できる(self, tmp_path: Path) -> None:
        tracker = CostTracker()
        tracker.record("phase1", tokens_input=1000, tokens_output=500)

        save_path = tmp_path / "cost_tracking.json"
        tracker.save(save_path)

        assert save_path.exists()
        data = json.loads(save_path.read_text())
        assert "phases" in data

    def test_正常系_保存したデータを復元できる(self, tmp_path: Path) -> None:
        tracker = CostTracker()
        tracker.record("phase1", tokens_input=1_000_000, tokens_output=500_000)
        tracker.record("phase2", tokens_input=2_000_000, tokens_output=1_000_000)

        save_path = tmp_path / "cost_tracking.json"
        tracker.save(save_path)

        loaded = CostTracker.load(save_path)

        assert loaded.get_total_cost() == pytest.approx(tracker.get_total_cost())
        assert loaded.get_phase_cost("phase1") == pytest.approx(
            tracker.get_phase_cost("phase1")
        )
        assert loaded.get_phase_cost("phase2") == pytest.approx(
            tracker.get_phase_cost("phase2")
        )

    def test_正常系_存在しないファイルからloadで空トラッカー(
        self, tmp_path: Path
    ) -> None:
        save_path = tmp_path / "nonexistent.json"

        loaded = CostTracker.load(save_path)

        assert loaded.get_total_cost() == 0.0

    def test_正常系_保存ファイルのディレクトリが自動作成される(
        self, tmp_path: Path
    ) -> None:
        tracker = CostTracker()
        tracker.record("phase1", tokens_input=1000, tokens_output=500)

        save_path = tmp_path / "subdir" / "cost_tracking.json"
        tracker.save(save_path)

        assert save_path.exists()

    def test_正常系_warning_thresholdも保存復元される(self, tmp_path: Path) -> None:
        tracker = CostTracker(warning_threshold=100.0)
        tracker.record("phase1", tokens_input=1000, tokens_output=500)

        save_path = tmp_path / "cost_tracking.json"
        tracker.save(save_path)

        loaded = CostTracker.load(save_path)

        assert loaded.warning_threshold == 100.0

    def test_正常系_保存データが正しいJSON構造(self, tmp_path: Path) -> None:
        tracker = CostTracker()
        tracker.record("phase1", tokens_input=1000, tokens_output=500)

        save_path = tmp_path / "cost_tracking.json"
        tracker.save(save_path)

        data = json.loads(save_path.read_text())
        assert "phases" in data
        assert "phase1" in data["phases"]
        phase_data = data["phases"]["phase1"]
        assert "tokens_input" in phase_data
        assert "tokens_output" in phase_data
        assert "cost" in phase_data
