"""Unit tests for DriftResult dataclass.

Tests for DriftResult:
- Basic initialization and field access
- Drift calculation (current - target)
- Drift percent calculation
- Rebalance flag setting
"""

import pytest
from strategy.rebalance.types import DriftResult

# =============================================================================
# TestDriftResultInitialization
# =============================================================================


class TestDriftResultInitialization:
    """DriftResult 初期化のテスト."""

    def test_正常系_DriftResultが正しく初期化される(self) -> None:
        """DriftResultの全フィールドが正しく初期化されることを確認."""
        result = DriftResult(
            ticker="VOO",
            target_weight=0.6,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.33,
            requires_rebalance=True,
        )

        assert result.ticker == "VOO"
        assert result.target_weight == 0.6
        assert result.current_weight == 0.65
        assert result.drift == 0.05
        assert result.drift_percent == 8.33
        assert result.requires_rebalance is True

    def test_正常系_リバランス不要の場合のDriftResult(self) -> None:
        """リバランス不要の場合のDriftResultが正しく初期化されることを確認."""
        result = DriftResult(
            ticker="BND",
            target_weight=0.4,
            current_weight=0.41,
            drift=0.01,
            drift_percent=2.5,
            requires_rebalance=False,
        )

        assert result.ticker == "BND"
        assert result.requires_rebalance is False


# =============================================================================
# TestDriftResultDriftCalculation
# =============================================================================


class TestDriftResultDriftCalculation:
    """DriftResult の乖離幅計算のテスト."""

    def test_正常系_乖離幅が正しく計算される_現在が目標より大きい(self) -> None:
        """現在の配分が目標より大きい場合、正の乖離幅を確認."""
        # current(0.65) - target(0.60) = 0.05
        result = DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.33,
            requires_rebalance=True,
        )

        # drift = current - target
        expected_drift = result.current_weight - result.target_weight
        assert abs(result.drift - expected_drift) < 1e-10
        assert result.drift > 0

    def test_正常系_乖離幅が正しく計算される_現在が目標より小さい(self) -> None:
        """現在の配分が目標より小さい場合、負の乖離幅を確認."""
        # current(0.35) - target(0.40) = -0.05
        result = DriftResult(
            ticker="BND",
            target_weight=0.40,
            current_weight=0.35,
            drift=-0.05,
            drift_percent=-12.5,
            requires_rebalance=True,
        )

        # drift = current - target
        expected_drift = result.current_weight - result.target_weight
        assert abs(result.drift - expected_drift) < 1e-10
        assert result.drift < 0

    def test_正常系_配分が目標と完全一致の場合はドリフトゼロ(self) -> None:
        """配分が目標と完全に一致する場合、ドリフトがゼロであることを確認."""
        result = DriftResult(
            ticker="VTI",
            target_weight=0.50,
            current_weight=0.50,
            drift=0.0,
            drift_percent=0.0,
            requires_rebalance=False,
        )

        assert result.drift == 0.0
        assert result.drift_percent == 0.0


# =============================================================================
# TestDriftResultDriftPercent
# =============================================================================


class TestDriftResultDriftPercent:
    """DriftResult の乖離率計算のテスト."""

    def test_正常系_乖離率が正しく計算される(self) -> None:
        """乖離率が正しく計算されることを確認 (drift / target * 100)."""
        # drift(0.05) / target(0.60) * 100 = 8.333...%
        result = DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.333333333,
            requires_rebalance=True,
        )

        # drift_percent = drift / target * 100
        expected_percent = (result.drift / result.target_weight) * 100
        assert abs(result.drift_percent - expected_percent) < 0.001

    def test_正常系_負の乖離率が正しく計算される(self) -> None:
        """負の乖離率が正しく計算されることを確認."""
        # drift(-0.05) / target(0.40) * 100 = -12.5%
        result = DriftResult(
            ticker="BND",
            target_weight=0.40,
            current_weight=0.35,
            drift=-0.05,
            drift_percent=-12.5,
            requires_rebalance=True,
        )

        expected_percent = (result.drift / result.target_weight) * 100
        assert abs(result.drift_percent - expected_percent) < 0.001

    @pytest.mark.parametrize(
        "target,current,expected_percent",
        [
            (0.50, 0.55, 10.0),  # +10%
            (0.50, 0.45, -10.0),  # -10%
            (0.25, 0.30, 20.0),  # +20%
            (0.25, 0.20, -20.0),  # -20%
            (0.10, 0.11, 10.0),  # +10%
        ],
    )
    def test_パラメトライズ_様々な乖離率のケース(
        self,
        target: float,
        current: float,
        expected_percent: float,
    ) -> None:
        """様々なケースで乖離率が正しく計算されることを確認."""
        drift = current - target
        drift_percent = (drift / target) * 100

        result = DriftResult(
            ticker="TEST",
            target_weight=target,
            current_weight=current,
            drift=drift,
            drift_percent=drift_percent,
            requires_rebalance=False,
        )

        assert abs(result.drift_percent - expected_percent) < 0.001


# =============================================================================
# TestDriftResultRebalanceFlag
# =============================================================================


class TestDriftResultRebalanceFlag:
    """DriftResult のリバランス推奨フラグのテスト."""

    def test_正常系_リバランス推奨フラグがTrueの場合(self) -> None:
        """requires_rebalanceがTrueの場合のDriftResultを確認."""
        result = DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.70,
            drift=0.10,
            drift_percent=16.67,
            requires_rebalance=True,
        )

        assert result.requires_rebalance is True

    def test_正常系_リバランス推奨フラグがFalseの場合(self) -> None:
        """requires_rebalanceがFalseの場合のDriftResultを確認."""
        result = DriftResult(
            ticker="BND",
            target_weight=0.40,
            current_weight=0.41,
            drift=0.01,
            drift_percent=2.5,
            requires_rebalance=False,
        )

        assert result.requires_rebalance is False


# =============================================================================
# TestDriftResultDataclass
# =============================================================================


class TestDriftResultDataclass:
    """DriftResult dataclass の特性テスト."""

    def test_正常系_DriftResultはイミュータブル(self) -> None:
        """DriftResultがfrozen dataclassとして不変であることを確認."""
        result = DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.33,
            requires_rebalance=True,
        )

        # frozen=True の場合、属性変更で FrozenInstanceError が発生
        with pytest.raises(AttributeError):
            result.ticker = "BND"  # type: ignore[misc]

    def test_正常系_DriftResultの等価性比較(self) -> None:
        """同じ値を持つDriftResultが等価であることを確認."""
        result1 = DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.33,
            requires_rebalance=True,
        )
        result2 = DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.33,
            requires_rebalance=True,
        )

        assert result1 == result2

    def test_正常系_DriftResultの非等価性比較(self) -> None:
        """異なる値を持つDriftResultが非等価であることを確認."""
        result1 = DriftResult(
            ticker="VOO",
            target_weight=0.60,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.33,
            requires_rebalance=True,
        )
        result2 = DriftResult(
            ticker="BND",  # 異なるティッカー
            target_weight=0.60,
            current_weight=0.65,
            drift=0.05,
            drift_percent=8.33,
            requires_rebalance=True,
        )

        assert result1 != result2
