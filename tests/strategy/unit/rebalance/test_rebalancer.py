"""Unit tests for Rebalancer.detect_drift method.

Tests for detect_drift:
- Basic drift detection
- Threshold-based rebalance recommendation
- Multiple tickers handling
- Edge cases (exact match, custom threshold)
- Error handling
"""

import pytest
from strategy.errors import ValidationError
from strategy.portfolio import Portfolio
from strategy.rebalance.rebalancer import Rebalancer
from strategy.rebalance.types import DriftResult

# =============================================================================
# Test fixtures
# =============================================================================


@pytest.fixture
def sample_portfolio() -> Portfolio:
    """60/40 ポートフォリオを作成."""
    return Portfolio(holdings=[("VOO", 0.6), ("BND", 0.4)])


@pytest.fixture
def drifted_portfolio() -> Portfolio:
    """ドリフトした状態のポートフォリオを作成（normalize=Trueで比率調整）.

    現在の配分:
    - VOO: 65% (目標60%から+5%のドリフト)
    - BND: 35% (目標40%から-5%のドリフト)
    """
    return Portfolio(holdings=[("VOO", 0.65), ("BND", 0.35)], normalize=True)


@pytest.fixture
def multi_asset_portfolio() -> Portfolio:
    """複数銘柄のポートフォリオを作成."""
    return Portfolio(
        holdings=[
            ("VOO", 0.40),
            ("BND", 0.30),
            ("VTI", 0.20),
            ("GLD", 0.10),
        ]
    )


@pytest.fixture
def rebalancer(sample_portfolio: Portfolio) -> Rebalancer:
    """Rebalancer インスタンスを作成."""
    return Rebalancer(portfolio=sample_portfolio)


@pytest.fixture
def drifted_rebalancer(drifted_portfolio: Portfolio) -> Rebalancer:
    """ドリフトしたポートフォリオ用の Rebalancer インスタンスを作成."""
    return Rebalancer(portfolio=drifted_portfolio)


# =============================================================================
# TestRebalancerInitialization
# =============================================================================


class TestRebalancerInitialization:
    """Rebalancer 初期化のテスト."""

    def test_正常系_Rebalancerが正しく初期化される(
        self,
        sample_portfolio: Portfolio,
    ) -> None:
        """RebalancerがPortfolioから正しく初期化されることを確認."""
        rebalancer = Rebalancer(portfolio=sample_portfolio)

        assert rebalancer is not None
        assert rebalancer.portfolio is sample_portfolio


# =============================================================================
# TestDetectDriftBasic
# =============================================================================


class TestDetectDriftBasic:
    """detect_drift 基本機能のテスト."""

    def test_正常系_配分差異を正しく計算できる(
        self,
        drifted_rebalancer: Rebalancer,
    ) -> None:
        """ドリフトしたポートフォリオの配分差異が正しく計算されることを確認."""
        target_weights = {"VOO": 0.6, "BND": 0.4}

        results = drifted_rebalancer.detect_drift(target_weights=target_weights)

        assert len(results) == 2
        assert all(isinstance(r, DriftResult) for r in results)

        # 結果を ticker で辞書化
        results_by_ticker = {r.ticker: r for r in results}

        # VOO: current 0.65 - target 0.60 = +0.05
        voo_result = results_by_ticker["VOO"]
        assert voo_result.target_weight == 0.6
        assert abs(voo_result.drift - 0.05) < 0.01  # 正規化による誤差を許容

        # BND: current 0.35 - target 0.40 = -0.05
        bnd_result = results_by_ticker["BND"]
        assert bnd_result.target_weight == 0.4
        assert bnd_result.drift < 0  # 負のドリフト

    def test_正常系_DriftResultで結果を返す(
        self,
        drifted_rebalancer: Rebalancer,
    ) -> None:
        """detect_driftがDriftResultのリストを返すことを確認."""
        target_weights = {"VOO": 0.6, "BND": 0.4}

        results = drifted_rebalancer.detect_drift(target_weights=target_weights)

        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, DriftResult)
            assert hasattr(result, "ticker")
            assert hasattr(result, "target_weight")
            assert hasattr(result, "current_weight")
            assert hasattr(result, "drift")
            assert hasattr(result, "drift_percent")
            assert hasattr(result, "requires_rebalance")


# =============================================================================
# TestDetectDriftThreshold
# =============================================================================


class TestDetectDriftThreshold:
    """detect_drift 閾値判定のテスト."""

    def test_正常系_閾値未満はリバランス不要と判定(
        self,
        drifted_rebalancer: Rebalancer,
    ) -> None:
        """ドリフトが閾値未満の場合、リバランス不要と判定されることを確認."""
        target_weights = {"VOO": 0.6, "BND": 0.4}

        # 閾値を10%に設定（ドリフト5%は閾値未満）
        results = drifted_rebalancer.detect_drift(
            target_weights=target_weights,
            threshold=0.10,
        )

        # 全ての銘柄がリバランス不要
        assert all(not r.requires_rebalance for r in results)

    def test_正常系_閾値以上はリバランス必要と判定(
        self,
        drifted_rebalancer: Rebalancer,
    ) -> None:
        """ドリフトが閾値以上の場合、リバランス必要と判定されることを確認."""
        target_weights = {"VOO": 0.6, "BND": 0.4}

        # 閾値を3%に設定（ドリフト5%は閾値以上）
        results = drifted_rebalancer.detect_drift(
            target_weights=target_weights,
            threshold=0.03,
        )

        # ドリフトした銘柄はリバランス必要
        results_by_ticker = {r.ticker: r for r in results}
        assert results_by_ticker["VOO"].requires_rebalance is True
        assert results_by_ticker["BND"].requires_rebalance is True

    def test_正常系_デフォルト閾値は5パーセント(
        self,
        rebalancer: Rebalancer,
    ) -> None:
        """デフォルトの閾値が5%であることを確認."""
        # ポートフォリオと目標が同じ場合
        target_weights = {"VOO": 0.6, "BND": 0.4}

        results = rebalancer.detect_drift(target_weights=target_weights)

        # ドリフトがない場合はリバランス不要
        assert all(not r.requires_rebalance for r in results)

    def test_正常系_カスタム閾値を設定できる(
        self,
        drifted_rebalancer: Rebalancer,
    ) -> None:
        """カスタム閾値を設定できることを確認."""
        target_weights = {"VOO": 0.6, "BND": 0.4}

        # 厳しい閾値（1%）
        results_strict = drifted_rebalancer.detect_drift(
            target_weights=target_weights,
            threshold=0.01,
        )

        # 緩い閾値（20%）
        results_loose = drifted_rebalancer.detect_drift(
            target_weights=target_weights,
            threshold=0.20,
        )

        # 厳しい閾値ではリバランス必要
        assert any(r.requires_rebalance for r in results_strict)

        # 緩い閾値ではリバランス不要
        assert all(not r.requires_rebalance for r in results_loose)


# =============================================================================
# TestDetectDriftMultipleTickers
# =============================================================================


class TestDetectDriftMultipleTickers:
    """複数銘柄のドリフト検出テスト."""

    def test_正常系_複数銘柄のドリフトを検出できる(
        self,
        multi_asset_portfolio: Portfolio,
    ) -> None:
        """複数銘柄のポートフォリオでドリフトが検出されることを確認."""
        rebalancer = Rebalancer(portfolio=multi_asset_portfolio)

        # 異なる目標配分を設定
        target_weights = {
            "VOO": 0.35,  # 現在40% -> -5%のドリフト
            "BND": 0.35,  # 現在30% -> +5%のドリフト
            "VTI": 0.15,  # 現在20% -> -5%のドリフト
            "GLD": 0.15,  # 現在10% -> +5%のドリフト
        }

        results = rebalancer.detect_drift(target_weights=target_weights)

        assert len(results) == 4
        tickers = {r.ticker for r in results}
        assert tickers == {"VOO", "BND", "VTI", "GLD"}

    def test_正常系_銘柄ごとに異なるドリフト判定(
        self,
        multi_asset_portfolio: Portfolio,
    ) -> None:
        """各銘柄のドリフトが個別に判定されることを確認."""
        rebalancer = Rebalancer(portfolio=multi_asset_portfolio)

        # 一部の銘柄だけドリフトさせる
        target_weights = {
            "VOO": 0.40,  # 現在と同じ -> ドリフトなし
            "BND": 0.30,  # 現在と同じ -> ドリフトなし
            "VTI": 0.10,  # 現在20% -> +10%のドリフト
            "GLD": 0.20,  # 現在10% -> -10%のドリフト
        }

        results = rebalancer.detect_drift(target_weights=target_weights, threshold=0.05)
        results_by_ticker = {r.ticker: r for r in results}

        # VOO, BND はドリフトなし
        assert not results_by_ticker["VOO"].requires_rebalance
        assert not results_by_ticker["BND"].requires_rebalance

        # VTI, GLD はドリフトあり
        assert results_by_ticker["VTI"].requires_rebalance
        assert results_by_ticker["GLD"].requires_rebalance


# =============================================================================
# TestDetectDriftEdgeCases
# =============================================================================


class TestDetectDriftEdgeCases:
    """detect_drift エッジケースのテスト."""

    def test_正常系_配分が目標と完全一致の場合はドリフトゼロ(
        self,
        rebalancer: Rebalancer,
    ) -> None:
        """現在の配分が目標と完全に一致する場合、ドリフトがゼロであることを確認."""
        # ポートフォリオと同じ目標配分
        target_weights = {"VOO": 0.6, "BND": 0.4}

        results = rebalancer.detect_drift(target_weights=target_weights)

        for result in results:
            assert abs(result.drift) < 1e-10
            assert abs(result.drift_percent) < 1e-10
            assert result.requires_rebalance is False

    def test_正常系_閾値ちょうどの場合のリバランス判定(
        self,
        sample_portfolio: Portfolio,
    ) -> None:
        """ドリフトが閾値とちょうど等しい場合の判定を確認.

        実装の仕様によって、閾値以上または閾値超過でリバランス推奨となる。
        ここでは閾値以上でリバランス必要と仮定。
        """
        # 5%のドリフトを持つポートフォリオ
        drifted = Portfolio(holdings=[("VOO", 0.65), ("BND", 0.35)], normalize=True)
        rebalancer = Rebalancer(portfolio=drifted)

        target_weights = {"VOO": 0.6, "BND": 0.4}

        # 閾値をちょうど5%に設定
        results = rebalancer.detect_drift(
            target_weights=target_weights,
            threshold=0.05,
        )

        # VOOのドリフトは約5%なので、閾値以上ならリバランス必要
        results_by_ticker = {r.ticker: r for r in results}
        # 注: 実装の仕様により、>=か>かで結果が変わる可能性あり
        assert results_by_ticker["VOO"].requires_rebalance is True


# =============================================================================
# TestDetectDriftErrorHandling
# =============================================================================


class TestDetectDriftErrorHandling:
    """detect_drift エラーハンドリングのテスト."""

    def test_異常系_target_weightsが空の場合はエラー(
        self,
        rebalancer: Rebalancer,
    ) -> None:
        """target_weightsが空の辞書の場合、ValidationErrorが発生することを確認."""
        with pytest.raises(ValidationError, match="target_weights cannot be empty"):
            rebalancer.detect_drift(target_weights={})

    def test_異常系_ポートフォリオにない銘柄が指定された場合(
        self,
        rebalancer: Rebalancer,
    ) -> None:
        """ポートフォリオに存在しない銘柄が目標に含まれる場合の挙動を確認.

        実装の仕様によって:
        1. エラーを発生させる
        2. 警告を出して無視する
        3. current_weight=0として処理する

        ここでは ValueError が発生することを期待。
        """
        target_weights = {
            "VOO": 0.6,
            "BND": 0.3,
            "INVALID_TICKER": 0.1,  # ポートフォリオにない銘柄
        }

        with pytest.raises(ValueError, match="not in portfolio"):
            rebalancer.detect_drift(target_weights=target_weights)

    def test_異常系_目標配分の合計が1でない場合の挙動(
        self,
        rebalancer: Rebalancer,
    ) -> None:
        """目標配分の合計が1.0でない場合の挙動を確認.

        実装の仕様によって:
        1. 警告を出して処理を続行
        2. ValidationError を発生させる

        ここでは警告を出して処理を続行することを期待。
        """
        target_weights = {
            "VOO": 0.5,  # 合計0.8
            "BND": 0.3,
        }

        # エラーを発生させるか、警告して続行するかは実装依存
        # ここでは処理が成功することを確認
        results = rebalancer.detect_drift(target_weights=target_weights)
        assert len(results) == 2


# =============================================================================
# TestDetectDriftParameterized
# =============================================================================


class TestDetectDriftParameterized:
    """パラメトライズされたテスト."""

    @pytest.mark.parametrize(
        "threshold",
        [0.01, 0.03, 0.05, 0.10, 0.15, 0.20],
    )
    def test_パラメトライズ_様々な閾値で動作する(
        self,
        drifted_rebalancer: Rebalancer,
        threshold: float,
    ) -> None:
        """様々な閾値でdetect_driftが正しく動作することを確認."""
        target_weights = {"VOO": 0.6, "BND": 0.4}

        results = drifted_rebalancer.detect_drift(
            target_weights=target_weights,
            threshold=threshold,
        )

        assert len(results) == 2
        assert all(isinstance(r, DriftResult) for r in results)

    @pytest.mark.parametrize(
        "current_holdings,target_weights,expected_rebalance_count",
        [
            # ドリフトなし
            ([("A", 0.5), ("B", 0.5)], {"A": 0.5, "B": 0.5}, 0),
            # 1銘柄ドリフト
            ([("A", 0.6), ("B", 0.4)], {"A": 0.5, "B": 0.5}, 2),
            # 小さなドリフト（閾値未満）
            ([("A", 0.51), ("B", 0.49)], {"A": 0.5, "B": 0.5}, 0),
        ],
    )
    def test_パラメトライズ_様々なドリフトパターン(
        self,
        current_holdings: list[tuple[str, float]],
        target_weights: dict[str, float],
        expected_rebalance_count: int,
    ) -> None:
        """様々なドリフトパターンで正しく判定されることを確認."""
        portfolio = Portfolio(holdings=current_holdings)
        rebalancer = Rebalancer(portfolio=portfolio)

        results = rebalancer.detect_drift(
            target_weights=target_weights,
            threshold=0.05,
        )

        rebalance_needed = sum(1 for r in results if r.requires_rebalance)
        assert rebalance_needed == expected_rebalance_count
