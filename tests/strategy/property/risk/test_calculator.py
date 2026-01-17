"""Property-based tests for RiskCalculator using Hypothesis.

このモジュールではプロパティベーステストを使用して、
RiskCalculator の数学的不変条件と境界値を検証する。
"""

import math

import numpy as np
import pandas as pd
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from strategy.risk.calculator import RiskCalculator

# Threshold for considering standard deviation as effectively zero
_EPSILON = 1e-15


class TestVolatilityProperty:
    """ボラティリティ計算のプロパティテスト."""

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False
            ),
            min_size=10,
            max_size=500,
        ),
        annualization_factor=st.integers(min_value=1, max_value=365),
    )
    @settings(max_examples=100)
    def test_プロパティ_ボラティリティは常に非負(
        self,
        returns: list[float],
        annualization_factor: int,
    ) -> None:
        """ボラティリティは常に非負であることを検証.

        Parameters
        ----------
        returns : list[float]
            ランダムに生成されたリターンデータ
        annualization_factor : int
            年率化係数

        Notes
        -----
        ボラティリティは標準偏差を基にするため、常に非負である必要がある。
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(
            returns_series,
            annualization_factor=annualization_factor,
        )

        volatility = calculator.volatility()

        assert volatility >= 0
        assert not math.isnan(volatility)

    @given(
        base_returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=100,
        ),
        scale_factor=st.floats(min_value=0.1, max_value=10.0),
    )
    @settings(max_examples=50)
    def test_プロパティ_リターンスケールとボラティリティの関係(
        self,
        base_returns: list[float],
        scale_factor: float,
    ) -> None:
        """リターンを定数倍するとボラティリティも同じ倍率で変化することを検証.

        Parameters
        ----------
        base_returns : list[float]
            基準となるリターンデータ
        scale_factor : float
            スケール係数

        Notes
        -----
        σ(kX) = |k| * σ(X) の関係が成り立つ。
        """
        base_series = pd.Series(base_returns)
        scaled_series = base_series * scale_factor

        # 標準偏差が実質的にゼロでない場合のみテスト
        # (浮動小数点精度問題を考慮してEPSILONと比較)
        assume(float(base_series.std()) > _EPSILON)

        calc_base = RiskCalculator(base_series)
        calc_scaled = RiskCalculator(scaled_series)

        vol_base = calc_base.volatility()
        vol_scaled = calc_scaled.volatility()

        # ボラティリティがゼロの場合はスキップ
        assume(vol_base > 0)

        expected_ratio = abs(scale_factor)
        actual_ratio = vol_scaled / vol_base

        assert math.isclose(actual_ratio, expected_ratio, rel_tol=1e-5)

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=100,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_定数加算でボラティリティ不変(
        self,
        returns: list[float],
    ) -> None:
        """リターンに定数を加算してもボラティリティは変化しないことを検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ

        Notes
        -----
        σ(X + c) = σ(X) の関係が成り立つ。
        """
        original_series = pd.Series(returns)
        shifted_series = original_series + 0.05  # 5%のシフト

        calc_original = RiskCalculator(original_series)
        calc_shifted = RiskCalculator(shifted_series)

        vol_original = calc_original.volatility()
        vol_shifted = calc_shifted.volatility()

        assert math.isclose(vol_original, vol_shifted, rel_tol=1e-10)


class TestSharpeRatioProperty:
    """シャープレシオ計算のプロパティテスト."""

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=200,
        ),
        risk_free_rate=st.floats(min_value=0.0, max_value=0.1, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_プロパティ_シャープレシオは有限または無限大(
        self,
        returns: list[float],
        risk_free_rate: float,
    ) -> None:
        """シャープレシオは有限値または無限大であることを検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ
        risk_free_rate : float
            リスクフリーレート

        Notes
        -----
        標準偏差がゼロの場合は無限大、それ以外は有限値となる。
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series, risk_free_rate=risk_free_rate)

        sharpe = calculator.sharpe_ratio()

        # NaN でないことを確認（無限大は許容）
        # 標準偏差が実質的にゼロの場合はNaNも許容
        std = float(returns_series.std())
        assert not math.isnan(sharpe) or std < _EPSILON

    @given(
        returns=st.lists(
            st.floats(
                min_value=0.001, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=100,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_正のリターンで正のシャープレシオ(
        self,
        returns: list[float],
    ) -> None:
        """全て正のリターンでシャープレシオが正になることを検証.

        Parameters
        ----------
        returns : list[float]
            全て正のリターンデータ
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series, risk_free_rate=0.0)

        sharpe = calculator.sharpe_ratio()

        # 無限大でない場合は正である
        if not math.isinf(sharpe):
            assert sharpe > 0

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=-0.001, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=100,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_負のリターンで負のシャープレシオ(
        self,
        returns: list[float],
    ) -> None:
        """全て負のリターンでシャープレシオが負になることを検証.

        Parameters
        ----------
        returns : list[float]
            全て負のリターンデータ
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series, risk_free_rate=0.0)

        sharpe = calculator.sharpe_ratio()

        # 無限大でない場合は負である
        if not math.isinf(sharpe):
            assert sharpe < 0


class TestSortinoRatioProperty:
    """ソルティノレシオ計算のプロパティテスト."""

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=200,
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_ソルティノレシオは計算可能(
        self,
        returns: list[float],
    ) -> None:
        """ソルティノレシオが計算可能であることを検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series)

        sortino = calculator.sortino_ratio()

        # float であることを確認
        assert isinstance(sortino, float)

    @given(
        returns=st.lists(
            st.floats(
                min_value=0.001, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=100,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_全て正のリターンで無限大(
        self,
        returns: list[float],
    ) -> None:
        """全て正のリターンでソルティノレシオが無限大になることを検証.

        Parameters
        ----------
        returns : list[float]
            全て正のリターンデータ

        Notes
        -----
        下方偏差がゼロで平均リターンが正の場合、無限大となる。
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series, risk_free_rate=0.0)

        sortino = calculator.sortino_ratio()

        # 下方偏差がゼロなので無限大
        assert math.isinf(sortino) and sortino > 0


class TestDownsideDeviationProperty:
    """下方偏差計算のプロパティテスト."""

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False
            ),
            min_size=10,
            max_size=500,
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_下方偏差は常に非負(
        self,
        returns: list[float],
    ) -> None:
        """下方偏差は常に非負であることを検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ
        """
        returns_series = pd.Series(returns)

        # 全てゼロに近い値の場合はスキップ
        assume(float(returns_series.std()) > _EPSILON or any(r < 0 for r in returns))

        calculator = RiskCalculator(returns_series)

        downside_dev = calculator.downside_deviation()

        assert downside_dev >= 0
        assert not math.isnan(downside_dev)

    @given(
        returns=st.lists(
            st.floats(
                min_value=0.001, max_value=0.5, allow_nan=False, allow_infinity=False
            ),
            min_size=10,
            max_size=100,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_全て正のリターンで下方偏差ゼロ(
        self,
        returns: list[float],
    ) -> None:
        """全て正のリターンで下方偏差がゼロになることを検証.

        Parameters
        ----------
        returns : list[float]
            全て正のリターンデータ
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series)

        downside_dev = calculator.downside_deviation()

        assert downside_dev == 0.0

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=30,
            max_size=200,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_下方偏差はボラティリティ以下(
        self,
        returns: list[float],
    ) -> None:
        """下方偏差はボラティリティ以下であることを検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ

        Notes
        -----
        下方偏差は負のリターンのみを使用するため、
        通常はボラティリティ（全リターンの標準偏差）以下となる。
        ただし、全て負のリターンの場合は等しくなる可能性がある。
        """
        returns_series = pd.Series(returns)

        # 全てゼロに近い値の場合はスキップ
        assume(float(returns_series.std()) > _EPSILON)

        calculator = RiskCalculator(returns_series)

        downside_dev = calculator.downside_deviation()
        volatility = calculator.volatility()

        # ボラティリティがゼロの場合はスキップ（両方ゼロ）
        assume(volatility > 0)

        # 下方偏差はボラティリティ以下
        # 浮動小数点の誤差を考慮して少し余裕を持たせる
        assert downside_dev <= volatility + 1e-10


class TestMathematicalRelationships:
    """数学的関係性のプロパティテスト."""

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=50,
            max_size=200,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_ソルティノレシオとシャープレシオの関係(
        self,
        returns: list[float],
    ) -> None:
        """ソルティノレシオとシャープレシオの関係を検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ

        Notes
        -----
        下方偏差 <= ボラティリティ なので、同じ超過リターンの場合
        ソルティノレシオ >= シャープレシオ となる（符号が同じ場合）。
        """
        returns_series = pd.Series(returns)

        # 負のリターンが含まれていない場合はスキップ
        assume(any(r < 0 for r in returns))

        # 標準偏差がゼロに近い場合はスキップ
        assume(float(returns_series.std()) > _EPSILON)

        calculator = RiskCalculator(returns_series, risk_free_rate=0.0)

        sortino = calculator.sortino_ratio()
        sharpe = calculator.sharpe_ratio()

        # 無限大の場合はスキップ
        assume(not math.isinf(sortino) and not math.isinf(sharpe))

        # 平均リターンの符号が同じ場合
        mean_return = returns_series.mean()
        if mean_return > 0:
            # 正のリターンの場合、ソルティノ >= シャープ
            assert sortino >= sharpe - 1e-10
        elif mean_return < 0:
            # 負のリターンの場合、ソルティノ <= シャープ（両方負なので絶対値で比較）
            assert abs(sortino) >= abs(sharpe) - 1e-10


class TestBoundaryConditions:
    """境界条件のプロパティテスト."""

    @given(
        constant_value=st.floats(
            min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
        ),
        size=st.integers(min_value=10, max_value=100),
    )
    @settings(max_examples=50)
    def test_プロパティ_定数リターンでボラティリティゼロ(
        self,
        constant_value: float,
        size: int,
    ) -> None:
        """全て同じ値のリターンでボラティリティがゼロになることを検証.

        Parameters
        ----------
        constant_value : float
            定数リターン値
        size : int
            リターン数
        """
        constant_returns = pd.Series([constant_value] * size)
        calculator = RiskCalculator(constant_returns)

        volatility = calculator.volatility()

        assert volatility == 0.0

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=100,
        ),
        factor1=st.integers(min_value=12, max_value=52),
        factor2=st.integers(min_value=52, max_value=365),
    )
    @settings(max_examples=30)
    def test_プロパティ_年率化係数の比率関係(
        self,
        returns: list[float],
        factor1: int,
        factor2: int,
    ) -> None:
        """異なる年率化係数間の比率関係を検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ
        factor1 : int
            年率化係数1（小さい方）
        factor2 : int
            年率化係数2（大きい方）

        Notes
        -----
        年率化係数 N で計算したボラティリティは sqrt(N) に比例する。
        """
        returns_series = pd.Series(returns)

        calc1 = RiskCalculator(returns_series, annualization_factor=factor1)
        calc2 = RiskCalculator(returns_series, annualization_factor=factor2)

        vol1 = calc1.volatility()
        vol2 = calc2.volatility()

        # 標準偏差がゼロの場合はスキップ
        if vol1 == 0 or vol2 == 0:
            return

        expected_ratio = np.sqrt(factor2) / np.sqrt(factor1)
        actual_ratio = vol2 / vol1

        assert math.isclose(actual_ratio, expected_ratio, rel_tol=1e-5)


class TestMaxDrawdownProperty:
    """最大ドローダウン計算のプロパティテスト."""

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False
            ),
            min_size=10,
            max_size=500,
        ),
    )
    @settings(max_examples=100)
    def test_プロパティ_MDDは常に0から負1の範囲(
        self,
        returns: list[float],
    ) -> None:
        """MDD は -1.0 から 0.0 の範囲内であることを検証.

        Parameters
        ----------
        returns : list[float]
            ランダムに生成されたリターンデータ

        Notes
        -----
        MDD は 0（ドローダウンなし）から -1（完全損失）の範囲となる。
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series)

        mdd = calculator.max_drawdown()

        assert -1.0 <= mdd <= 0.0
        assert not math.isnan(mdd)

    @given(
        returns=st.lists(
            st.floats(
                min_value=0.001, max_value=0.5, allow_nan=False, allow_infinity=False
            ),
            min_size=10,
            max_size=100,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_全て正のリターンでMDDはゼロ(
        self,
        returns: list[float],
    ) -> None:
        """全て正のリターンで MDD がゼロになることを検証.

        Parameters
        ----------
        returns : list[float]
            全て正のリターンデータ
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series)

        mdd = calculator.max_drawdown()

        assert mdd == 0.0

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.5, max_value=-0.001, allow_nan=False, allow_infinity=False
            ),
            min_size=10,
            max_size=100,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_全て負のリターンでMDDは負(
        self,
        returns: list[float],
    ) -> None:
        """全て負のリターンで MDD が負になることを検証.

        Parameters
        ----------
        returns : list[float]
            全て負のリターンデータ
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series)

        mdd = calculator.max_drawdown()

        assert mdd < 0.0
        assert mdd >= -1.0


class TestVaRProperty:
    """VaR 計算のプロパティテスト."""

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.3, max_value=0.3, allow_nan=False, allow_infinity=False
            ),
            min_size=20,
            max_size=500,
        ),
        confidence=st.floats(min_value=0.5, max_value=0.99),
    )
    @settings(max_examples=100)
    def test_プロパティ_VaRは有限値(
        self,
        returns: list[float],
        confidence: float,
    ) -> None:
        """VaR が有限値であることを検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ
        confidence : float
            信頼水準
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series)

        var_historical = calculator.var(confidence=confidence, method="historical")
        var_parametric = calculator.var(confidence=confidence, method="parametric")

        assert not math.isnan(var_historical)
        assert not math.isinf(var_historical)
        assert not math.isnan(var_parametric)
        assert not math.isinf(var_parametric)

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=50,
            max_size=200,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_VaR99はVaR95以下(
        self,
        returns: list[float],
    ) -> None:
        """99% VaR は 95% VaR 以下であることを検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ

        Notes
        -----
        信頼水準が高いほど、より悪いケースを捉えるため、
        VaR の値（損失）は大きくなる（より負の値になる）。
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series)

        var_95 = calculator.var(confidence=0.95, method="historical")
        var_99 = calculator.var(confidence=0.99, method="historical")

        # 99% VaR は 95% VaR 以下（より大きな損失を示す）
        assert var_99 <= var_95 + 1e-10

    @given(
        returns=st.lists(
            st.floats(
                min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            min_size=50,
            max_size=200,
        ),
    )
    @settings(max_examples=50)
    def test_プロパティ_VaRはリターン範囲内(
        self,
        returns: list[float],
    ) -> None:
        """VaR がリターンの範囲内にあることを検証.

        Parameters
        ----------
        returns : list[float]
            リターンデータ

        Notes
        -----
        ヒストリカル VaR は過去のリターンから計算するため、
        必ずリターンの最小値から最大値の範囲内に収まる。
        """
        returns_series = pd.Series(returns)
        calculator = RiskCalculator(returns_series)

        var_95 = calculator.var(confidence=0.95, method="historical")

        assert min(returns) <= var_95 <= max(returns)
