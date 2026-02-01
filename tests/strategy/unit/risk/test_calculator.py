"""Unit tests for RiskCalculator class.

RiskCalculator はポートフォリオのリターンデータから各種リスク指標を計算する
内部コンポーネントである。このモジュールでは以下の指標の計算をテストする:
- ボラティリティ（年率）
- シャープレシオ
- ソルティノレシオ
- 下方偏差
"""

import math

import numpy as np
import pandas as pd
import pytest
from strategy.risk.calculator import RiskCalculator


class TestRiskCalculatorInit:
    """RiskCalculator の初期化テスト."""

    def test_正常系_デフォルトパラメータで初期化できる(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """デフォルトパラメータで RiskCalculator を初期化できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(sample_returns)

        assert calculator is not None
        assert calculator._risk_free_rate == 0.0
        assert calculator._annualization_factor == 252

    def test_正常系_カスタムパラメータで初期化できる(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """カスタムパラメータで RiskCalculator を初期化できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(
            sample_returns,
            risk_free_rate=0.02,
            annualization_factor=52,  # 週次データ
        )

        assert calculator._risk_free_rate == 0.02
        assert calculator._annualization_factor == 52

    def test_異常系_空のSeriesでValueError(self) -> None:
        """空の Series で初期化するとエラーになることを確認."""
        empty_returns = pd.Series([], dtype=float)

        with pytest.raises(ValueError, match="returns must not be empty"):
            RiskCalculator(empty_returns)

    def test_異常系_負のannualization_factorでValueError(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """負の年率化係数で初期化するとエラーになることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        with pytest.raises(
            ValueError,
            match="annualization_factor must be positive",
        ):
            RiskCalculator(sample_returns, annualization_factor=-1)

    def test_異常系_ゼロのannualization_factorでValueError(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """ゼロの年率化係数で初期化するとエラーになることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        with pytest.raises(
            ValueError,
            match="annualization_factor must be positive",
        ):
            RiskCalculator(sample_returns, annualization_factor=0)


class TestVolatility:
    """ボラティリティ計算のテスト."""

    def test_正常系_正のリターンでボラティリティが正(
        self,
        positive_returns: pd.Series,
    ) -> None:
        """正のリターンでボラティリティが正の値になることを確認.

        Parameters
        ----------
        positive_returns : pd.Series
            全て正のリターンデータ

        Notes
        -----
        Formula: volatility = std(returns) * sqrt(annualization_factor)
        """
        calculator = RiskCalculator(positive_returns)
        volatility = calculator.volatility()

        assert volatility > 0
        assert isinstance(volatility, float)

    def test_正常系_負のリターンでボラティリティが正(
        self,
        negative_returns: pd.Series,
    ) -> None:
        """負のリターンでもボラティリティは正の値になることを確認.

        Parameters
        ----------
        negative_returns : pd.Series
            全て負のリターンデータ

        Notes
        -----
        ボラティリティは標準偏差を基にするため常に非負である。
        """
        calculator = RiskCalculator(negative_returns)
        volatility = calculator.volatility()

        assert volatility > 0
        assert isinstance(volatility, float)

    def test_正常系_混合リターンでボラティリティ計算(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """正負混合のリターンでボラティリティが計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            正負混合のリターンデータ
        """
        calculator = RiskCalculator(sample_returns)
        volatility = calculator.volatility()

        # 期待値の計算: std * sqrt(252)
        expected = sample_returns.std() * np.sqrt(252)

        assert volatility > 0
        assert math.isclose(volatility, expected, rel_tol=1e-10)

    def test_正常系_年率化係数が正しく適用される(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """異なる年率化係数で正しく年率化されることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calc_daily = RiskCalculator(sample_returns, annualization_factor=252)
        calc_weekly = RiskCalculator(sample_returns, annualization_factor=52)

        vol_daily = calc_daily.volatility()
        vol_weekly = calc_weekly.volatility()

        # 日次と週次で係数の比率に基づいた関係
        expected_ratio = np.sqrt(252) / np.sqrt(52)
        actual_ratio = vol_daily / vol_weekly

        assert math.isclose(actual_ratio, expected_ratio, rel_tol=1e-10)

    def test_エッジケース_同一リターンでボラティリティゼロ(self) -> None:
        """全て同じリターンの場合、ボラティリティがゼロになることを確認.

        Notes
        -----
        標準偏差がゼロになるため、ボラティリティもゼロになる。
        """
        constant_returns = pd.Series([0.01] * 100)
        calculator = RiskCalculator(constant_returns)
        volatility = calculator.volatility()

        assert volatility == 0.0


class TestSharpeRatio:
    """シャープレシオ計算のテスト."""

    def test_正常系_正のリターンでシャープレシオが正(
        self,
        positive_returns: pd.Series,
    ) -> None:
        """正のリターンでシャープレシオが正の値になることを確認.

        Parameters
        ----------
        positive_returns : pd.Series
            全て正のリターンデータ

        Notes
        -----
        Formula: sharpe = (mean(excess_returns) / std(excess_returns)) * sqrt(annualization_factor)
        """
        calculator = RiskCalculator(positive_returns, risk_free_rate=0.0)
        sharpe = calculator.sharpe_ratio()

        assert sharpe > 0
        assert isinstance(sharpe, float)

    def test_正常系_負のリターンでシャープレシオが負(
        self,
        negative_returns: pd.Series,
    ) -> None:
        """負のリターンでシャープレシオが負の値になることを確認.

        Parameters
        ----------
        negative_returns : pd.Series
            全て負のリターンデータ
        """
        calculator = RiskCalculator(negative_returns, risk_free_rate=0.0)
        sharpe = calculator.sharpe_ratio()

        assert sharpe < 0
        assert isinstance(sharpe, float)

    def test_正常系_リスクフリーレートが反映される(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """リスクフリーレートが計算に反映されることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        リスクフリーレートが高いほどシャープレシオは低下する。
        """
        calc_rf_zero = RiskCalculator(sample_returns, risk_free_rate=0.0)
        calc_rf_positive = RiskCalculator(sample_returns, risk_free_rate=0.05)

        sharpe_rf_zero = calc_rf_zero.sharpe_ratio()
        sharpe_rf_positive = calc_rf_positive.sharpe_ratio()

        # リスクフリーレートが高いほどシャープレシオは低下
        assert sharpe_rf_positive < sharpe_rf_zero

    def test_正常系_計算式が正しい(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """シャープレシオの計算式が正しいことを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        risk_free_rate = 0.02
        annualization_factor = 252

        calculator = RiskCalculator(
            sample_returns,
            risk_free_rate=risk_free_rate,
            annualization_factor=annualization_factor,
        )
        sharpe = calculator.sharpe_ratio()

        # 期待値の計算
        daily_rf = risk_free_rate / annualization_factor
        excess_returns = sample_returns - daily_rf
        expected = (excess_returns.mean() / excess_returns.std()) * np.sqrt(
            annualization_factor
        )

        assert math.isclose(sharpe, expected, rel_tol=1e-10)

    def test_エッジケース_ゼロ標準偏差で無限大または例外(self) -> None:
        """標準偏差がゼロの場合の動作を確認.

        Notes
        -----
        全て同じリターンの場合、標準偏差がゼロになり、
        シャープレシオは無限大（正の平均）またはNaN（ゼロの平均）になる。
        """
        constant_returns = pd.Series([0.01] * 100)
        calculator = RiskCalculator(constant_returns, risk_free_rate=0.0)

        sharpe = calculator.sharpe_ratio()

        # 標準偏差がゼロで平均が正の場合、無限大
        assert math.isinf(sharpe) or math.isnan(sharpe)


class TestSortinoRatio:
    """ソルティノレシオ計算のテスト."""

    def test_正常系_正のリターンでソルティノレシオが正(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """正負混合のリターンでソルティノレシオが計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            正負混合のリターンデータ

        Notes
        -----
        Formula: sortino = (mean(excess_returns) / downside_std) * sqrt(annualization_factor)
        """
        calculator = RiskCalculator(sample_returns, risk_free_rate=0.0)
        sortino = calculator.sortino_ratio()

        assert isinstance(sortino, float)
        # 平均リターンが正なら正のソルティノレシオ
        if sample_returns.mean() > 0:
            assert sortino > 0

    def test_正常系_下方偏差のみを使用(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """ソルティノレシオが下方偏差のみを使用することを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        ソルティノレシオはシャープレシオと異なり、
        負のリターンのみを使用して標準偏差を計算する。
        """
        calculator = RiskCalculator(sample_returns, risk_free_rate=0.0)

        sortino = calculator.sortino_ratio()
        sharpe = calculator.sharpe_ratio()

        # 下方偏差は通常、全体の標準偏差より小さいため、
        # ソルティノレシオはシャープレシオより大きくなることが多い
        # （ただし、リターン分布によっては異なる）
        assert sortino != sharpe  # 少なくとも異なる値

    def test_正常系_リスクフリーレートが反映される(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """リスクフリーレートが計算に反映されることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calc_rf_zero = RiskCalculator(sample_returns, risk_free_rate=0.0)
        calc_rf_positive = RiskCalculator(sample_returns, risk_free_rate=0.05)

        sortino_rf_zero = calc_rf_zero.sortino_ratio()
        sortino_rf_positive = calc_rf_positive.sortino_ratio()

        # リスクフリーレートが高いほどソルティノレシオは低下
        assert sortino_rf_positive < sortino_rf_zero

    def test_エッジケース_全て正のリターンで無限大(
        self,
        positive_returns: pd.Series,
    ) -> None:
        """全て正のリターンの場合、下方偏差がゼロで無限大になることを確認.

        Parameters
        ----------
        positive_returns : pd.Series
            全て正のリターンデータ

        Notes
        -----
        下方偏差がゼロの場合、平均リターンが正なら無限大を返す。
        """
        calculator = RiskCalculator(positive_returns, risk_free_rate=0.0)
        sortino = calculator.sortino_ratio()

        # 下方偏差がゼロで平均が正の場合、無限大
        assert math.isinf(sortino) and sortino > 0

    def test_エッジケース_全て負のリターンで負のソルティノレシオ(
        self,
        negative_returns: pd.Series,
    ) -> None:
        """全て負のリターンの場合、負のソルティノレシオになることを確認.

        Parameters
        ----------
        negative_returns : pd.Series
            全て負のリターンデータ
        """
        calculator = RiskCalculator(negative_returns, risk_free_rate=0.0)
        sortino = calculator.sortino_ratio()

        assert sortino < 0
        assert isinstance(sortino, float)


class TestDownsideDeviation:
    """下方偏差計算のテスト."""

    def test_正常系_混合リターンで下方偏差が正(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """正負混合のリターンで下方偏差が正の値になることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            正負混合のリターンデータ

        Notes
        -----
        下方偏差は負のリターンの標準偏差であり、常に非負である。
        """
        calculator = RiskCalculator(sample_returns)
        downside_dev = calculator.downside_deviation()

        assert downside_dev > 0
        assert isinstance(downside_dev, float)

    def test_正常系_負のリターンのみを使用(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """下方偏差が負のリターンのみを使用して計算されることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(sample_returns)
        downside_dev = calculator.downside_deviation()

        # 期待値: 負のリターンの標準偏差 * sqrt(annualization_factor)
        negative_returns = sample_returns[sample_returns < 0]
        expected = negative_returns.std() * np.sqrt(252)

        assert math.isclose(downside_dev, expected, rel_tol=1e-10)

    def test_正常系_全て負のリターンで計算(
        self,
        negative_returns: pd.Series,
    ) -> None:
        """全て負のリターンで下方偏差が計算できることを確認.

        Parameters
        ----------
        negative_returns : pd.Series
            全て負のリターンデータ
        """
        calculator = RiskCalculator(negative_returns)
        downside_dev = calculator.downside_deviation()

        # 全て負のリターンの標準偏差
        expected = negative_returns.std() * np.sqrt(252)

        assert downside_dev > 0
        assert math.isclose(downside_dev, expected, rel_tol=1e-10)

    def test_エッジケース_全て正のリターンで下方偏差ゼロ(
        self,
        positive_returns: pd.Series,
    ) -> None:
        """全て正のリターンの場合、下方偏差がゼロになることを確認.

        Parameters
        ----------
        positive_returns : pd.Series
            全て正のリターンデータ
        """
        calculator = RiskCalculator(positive_returns)
        downside_dev = calculator.downside_deviation()

        assert downside_dev == 0.0

    def test_正常系_年率化係数が正しく適用される(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """下方偏差に年率化係数が正しく適用されることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calc_daily = RiskCalculator(sample_returns, annualization_factor=252)
        calc_monthly = RiskCalculator(sample_returns, annualization_factor=12)

        dd_daily = calc_daily.downside_deviation()
        dd_monthly = calc_monthly.downside_deviation()

        # 年率化係数の比率に基づいた関係
        expected_ratio = np.sqrt(252) / np.sqrt(12)
        actual_ratio = dd_daily / dd_monthly

        assert math.isclose(actual_ratio, expected_ratio, rel_tol=1e-10)


class TestRiskCalculatorIntegration:
    """RiskCalculator の統合的なテスト."""

    def test_正常系_全指標が計算できる(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """全てのリスク指標が計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(
            sample_returns,
            risk_free_rate=0.02,
            annualization_factor=252,
        )

        # 全指標を計算
        volatility = calculator.volatility()
        sharpe = calculator.sharpe_ratio()
        sortino = calculator.sortino_ratio()
        downside_dev = calculator.downside_deviation()

        # 全て float であることを確認
        assert isinstance(volatility, float)
        assert isinstance(sharpe, float)
        assert isinstance(sortino, float)
        assert isinstance(downside_dev, float)

        # 基本的な数学的関係を確認
        assert volatility >= 0
        assert downside_dev >= 0

    def test_正常系_実際の市場データ形式で計算(self) -> None:
        """実際の市場データに近い形式で計算できることを確認.

        Notes
        -----
        日次リターン、252営業日、2%のリスクフリーレートを想定。
        """
        # 実際の市場データに近いリターン（平均0.04%, 標準偏差1%程度）
        np.random.seed(42)
        returns = pd.Series(
            np.random.normal(0.0004, 0.01, 252),  # 252営業日分
            index=pd.date_range("2023-01-01", periods=252, freq="B"),
        )

        calculator = RiskCalculator(
            returns,
            risk_free_rate=0.02,
            annualization_factor=252,
        )

        volatility = calculator.volatility()
        sharpe = calculator.sharpe_ratio()
        sortino = calculator.sortino_ratio()
        downside_dev = calculator.downside_deviation()

        # 現実的な範囲内の値であることを確認
        assert 0.1 < volatility < 0.3  # 年率10%-30%のボラティリティ
        assert -2 < sharpe < 2  # 一般的なシャープレシオの範囲
        assert -3 < sortino < 3  # 一般的なソルティノレシオの範囲
        assert downside_dev > 0


class TestMaxDrawdown:
    """最大ドローダウン (MDD) 計算のテスト."""

    def test_正常系_正負混合リターンでMDDが負(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """正負混合のリターンで MDD が負の値になることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            正負混合のリターンデータ

        Notes
        -----
        MDD は最大の累積損失を表すため、常に 0 以下の値となる。
        """
        calculator = RiskCalculator(sample_returns)
        mdd = calculator.max_drawdown()

        assert mdd <= 0
        assert isinstance(mdd, float)

    def test_正常系_MDDの計算式が正しい(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """MDD の計算式が正しいことを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        Formula:
        - cumulative = (1 + returns).cumprod()
        - running_max = cumulative.cummax()
        - drawdown = (cumulative - running_max) / running_max
        - max_drawdown = min(drawdown)
        """
        calculator = RiskCalculator(sample_returns)
        mdd = calculator.max_drawdown()

        # 期待値の計算
        cumulative = (1 + sample_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        expected = float(drawdown.min())

        assert math.isclose(mdd, expected, rel_tol=1e-10)

    def test_正常系_全て正のリターンでMDDがゼロ(
        self,
        positive_returns: pd.Series,
    ) -> None:
        """全て正のリターンで MDD がゼロになることを確認.

        Parameters
        ----------
        positive_returns : pd.Series
            全て正のリターンデータ

        Notes
        -----
        累積リターンが常に増加するため、ドローダウンは発生しない。
        """
        calculator = RiskCalculator(positive_returns)
        mdd = calculator.max_drawdown()

        assert mdd == 0.0

    def test_正常系_全て負のリターンでMDDが負(
        self,
        negative_returns: pd.Series,
    ) -> None:
        """全て負のリターンで MDD が負の値になることを確認.

        Parameters
        ----------
        negative_returns : pd.Series
            全て負のリターンデータ
        """
        calculator = RiskCalculator(negative_returns)
        mdd = calculator.max_drawdown()

        assert mdd < 0
        # MDD は -1.0 以上（完全損失以上にはならない）
        assert mdd >= -1.0

    def test_境界条件_MDDの範囲が0から負1(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """MDD が -1.0 から 0.0 の範囲内であることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        MDD は 0（ドローダウンなし）から -1（完全損失）の範囲となる。
        """
        calculator = RiskCalculator(sample_returns)
        mdd = calculator.max_drawdown()

        assert -1.0 <= mdd <= 0.0


class TestVaR:
    """VaR (Value at Risk) 計算のテスト."""

    def test_正常系_VaR95ヒストリカル(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """95% VaR (ヒストリカル法) が計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        VaR は損失を表すため、通常は負の値となる。
        """
        calculator = RiskCalculator(sample_returns)
        var_95 = calculator.var(confidence=0.95, method="historical")

        assert isinstance(var_95, float)
        # VaR は通常負の値（損失を表す）
        # ただし、リターンが全て正の場合は正の値もありうる
        assert not math.isnan(var_95)

    def test_正常系_VaR99ヒストリカル(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """99% VaR (ヒストリカル法) が計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(sample_returns)
        var_99 = calculator.var(confidence=0.99, method="historical")

        assert isinstance(var_99, float)
        assert not math.isnan(var_99)

    def test_正常系_VaR95パラメトリック(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """95% VaR (パラメトリック法) が計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        パラメトリック法は正規分布を仮定して計算する。
        """
        calculator = RiskCalculator(sample_returns)
        var_95 = calculator.var(confidence=0.95, method="parametric")

        assert isinstance(var_95, float)
        assert not math.isnan(var_95)

    def test_正常系_VaR99パラメトリック(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """99% VaR (パラメトリック法) が計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(sample_returns)
        var_99 = calculator.var(confidence=0.99, method="parametric")

        assert isinstance(var_99, float)
        assert not math.isnan(var_99)

    def test_正常系_VaR99はVaR95より小さいまたは等しい(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """99% VaR は 95% VaR 以下であることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        信頼水準が高いほど、より悪いケースを捉えるため、
        VaR の値（損失）は大きくなる（より負の値になる）。
        """
        calculator = RiskCalculator(sample_returns)
        var_95 = calculator.var(confidence=0.95, method="historical")
        var_99 = calculator.var(confidence=0.99, method="historical")

        # 99% VaR は 95% VaR 以下（より大きな損失を示す）
        assert var_99 <= var_95 + 1e-10  # 浮動小数点誤差を考慮

    def test_正常系_VaRヒストリカルの計算式が正しい(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """ヒストリカル VaR の計算式が正しいことを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        Formula: var = percentile(returns, (1 - confidence) * 100)
        """
        calculator = RiskCalculator(sample_returns)
        var_95 = calculator.var(confidence=0.95, method="historical")

        # 期待値の計算
        expected = float(np.percentile(sample_returns, (1 - 0.95) * 100))

        assert math.isclose(var_95, expected, rel_tol=1e-10)

    def test_正常系_VaRパラメトリックの計算式が正しい(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """パラメトリック VaR の計算式が正しいことを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ

        Notes
        -----
        Formula: var = mean(returns) + z_score * std(returns)
        where z_score = norm.ppf(1 - confidence)
        """
        from scipy import stats

        calculator = RiskCalculator(sample_returns)
        var_95 = calculator.var(confidence=0.95, method="parametric")

        # 期待値の計算
        z_score = stats.norm.ppf(1 - 0.95)
        expected = float(sample_returns.mean() + z_score * sample_returns.std())

        assert math.isclose(var_95, expected, rel_tol=1e-10)

    def test_正常系_デフォルトはヒストリカル法(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """デフォルトの method がヒストリカル法であることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(sample_returns)
        var_default = calculator.var(confidence=0.95)
        var_historical = calculator.var(confidence=0.95, method="historical")

        assert var_default == var_historical

    def test_異常系_無効なmethodでValueError(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """無効な method を指定すると ValueError になることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(sample_returns)

        with pytest.raises(ValueError, match="method must be"):
            calculator.var(confidence=0.95, method="invalid")  # type: ignore

    def test_正常系_異なる信頼水準での計算(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """異なる信頼水準で VaR が計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            テスト用の日次リターンデータ
        """
        calculator = RiskCalculator(sample_returns)

        var_90 = calculator.var(confidence=0.90, method="historical")
        var_95 = calculator.var(confidence=0.95, method="historical")
        var_99 = calculator.var(confidence=0.99, method="historical")

        # 信頼水準が高いほど VaR は小さい（より大きな損失）
        assert var_90 >= var_95 - 1e-10
        assert var_95 >= var_99 - 1e-10


class TestBeta:
    """ベータ値計算のテスト."""

    def test_正常系_ベータ値が計算できる(
        self,
        sample_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> None:
        """ベンチマーク指定時にベータ値が計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            ポートフォリオのリターンデータ
        benchmark_returns : pd.Series
            ベンチマークのリターンデータ

        Notes
        -----
        Formula: beta = cov(returns, benchmark) / var(benchmark)
        """
        calculator = RiskCalculator(sample_returns)
        beta = calculator.beta(benchmark_returns)

        assert isinstance(beta, float)
        assert not math.isnan(beta)

    def test_正常系_ベータ値の計算式が正しい(
        self,
        sample_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> None:
        """ベータ値の計算式が正しいことを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            ポートフォリオのリターンデータ
        benchmark_returns : pd.Series
            ベンチマークのリターンデータ

        Notes
        -----
        Formula: beta = cov(returns, benchmark) / var(benchmark)
        """
        calculator = RiskCalculator(sample_returns)
        beta = calculator.beta(benchmark_returns)

        # 期待値の計算
        aligned = pd.DataFrame(
            {
                "portfolio": sample_returns,
                "benchmark": benchmark_returns,
            }
        ).dropna()

        portfolio_series = pd.Series(aligned["portfolio"])
        benchmark_series = pd.Series(aligned["benchmark"])
        covariance = portfolio_series.cov(benchmark_series)
        benchmark_variance = benchmark_series.var()
        expected = covariance / benchmark_variance

        assert math.isclose(beta, expected, rel_tol=1e-10)

    def test_正常系_同一リターンでベータ1(self) -> None:
        """ポートフォリオとベンチマークが同一の場合、ベータが1になることを確認.

        Notes
        -----
        完全相関の場合、beta = cov(x,x) / var(x) = var(x) / var(x) = 1
        """
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))

        calculator = RiskCalculator(returns)
        beta = calculator.beta(returns)

        assert math.isclose(beta, 1.0, rel_tol=1e-10)

    def test_エッジケース_ベンチマーク分散ゼロでNaN(self) -> None:
        """ベンチマークの分散がゼロの場合、NaN を返すことを確認.

        Notes
        -----
        分散ゼロはゼロ除算になるため、NaN を返す。
        """
        np.random.seed(42)
        portfolio_returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        constant_benchmark = pd.Series([0.001] * 100)  # 分散ゼロ

        calculator = RiskCalculator(portfolio_returns)
        beta = calculator.beta(constant_benchmark)

        assert math.isnan(beta)

    def test_正常系_日付アライメントが正しく動作(self) -> None:
        """異なる日付インデックスでも正しくアライメントされることを確認.

        Notes
        -----
        ポートフォリオとベンチマークの日付が一致しない場合、
        共通の日付のみを使用して計算する。
        """
        np.random.seed(42)
        portfolio_returns = pd.Series(
            np.random.normal(0.001, 0.02, 100),
            index=pd.date_range("2023-01-01", periods=100, freq="B"),
        )
        # 一部異なる日付
        benchmark_returns = pd.Series(
            np.random.normal(0.0005, 0.015, 100),
            index=pd.date_range("2023-01-05", periods=100, freq="B"),
        )

        calculator = RiskCalculator(portfolio_returns)
        beta = calculator.beta(benchmark_returns)

        assert isinstance(beta, float)
        assert not math.isnan(beta)


class TestTreynorRatio:
    """トレイナーレシオ計算のテスト."""

    def test_正常系_トレイナーレシオが計算できる(
        self,
        sample_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> None:
        """ベンチマーク指定時にトレイナーレシオが計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            ポートフォリオのリターンデータ
        benchmark_returns : pd.Series
            ベンチマークのリターンデータ

        Notes
        -----
        Formula: treynor = (annualized_return - risk_free_rate) / beta
        """
        calculator = RiskCalculator(sample_returns, risk_free_rate=0.02)
        treynor = calculator.treynor_ratio(benchmark_returns)

        assert isinstance(treynor, float)
        assert not math.isnan(treynor)

    def test_正常系_トレイナーレシオの計算式が正しい(
        self,
        sample_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> None:
        """トレイナーレシオの計算式が正しいことを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            ポートフォリオのリターンデータ
        benchmark_returns : pd.Series
            ベンチマークのリターンデータ

        Notes
        -----
        Formula: treynor = (annualized_return - risk_free_rate) / beta
        """
        risk_free_rate = 0.02
        annualization_factor = 252

        calculator = RiskCalculator(
            sample_returns,
            risk_free_rate=risk_free_rate,
            annualization_factor=annualization_factor,
        )
        treynor = calculator.treynor_ratio(benchmark_returns)

        # 期待値の計算
        annualized_return = float(sample_returns.mean()) * annualization_factor
        beta = calculator.beta(benchmark_returns)
        expected = (annualized_return - risk_free_rate) / beta

        assert math.isclose(treynor, expected, rel_tol=1e-10)

    def test_正常系_リスクフリーレートが反映される(self) -> None:
        """リスクフリーレートが計算に反映されることを確認.

        Notes
        -----
        ベータが正の場合、リスクフリーレートが高いほどトレイナーレシオは低下。
        ベータが負の場合は逆の関係になる。
        """
        np.random.seed(42)
        # 正のベータを確保するため、同じシードで相関のあるリターンを生成
        base_returns = np.random.normal(0.001, 0.02, 100)
        portfolio_returns = pd.Series(
            base_returns * 1.2 + np.random.normal(0, 0.005, 100)
        )
        benchmark_returns = pd.Series(base_returns)

        calc_rf_zero = RiskCalculator(portfolio_returns, risk_free_rate=0.0)
        calc_rf_positive = RiskCalculator(portfolio_returns, risk_free_rate=0.05)

        # ベータが正であることを確認
        beta = calc_rf_zero.beta(benchmark_returns)
        assert beta > 0, f"Expected positive beta, got {beta}"

        treynor_rf_zero = calc_rf_zero.treynor_ratio(benchmark_returns)
        treynor_rf_positive = calc_rf_positive.treynor_ratio(benchmark_returns)

        # ベータが正の場合、リスクフリーレートが高いほどトレイナーレシオは低下
        assert treynor_rf_positive < treynor_rf_zero

    def test_エッジケース_ベータゼロでInfまたはNaN(self) -> None:
        """ベータがゼロの場合の動作を確認.

        Notes
        -----
        ベータがゼロの場合、ゼロ除算になるため無限大または NaN を返す。
        """
        np.random.seed(42)
        # 完全に無相関にするのは難しいため、ベンチマーク分散ゼロでベータ NaN のケースをテスト
        portfolio_returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        constant_benchmark = pd.Series([0.001] * 100)  # 分散ゼロ

        calculator = RiskCalculator(portfolio_returns)
        treynor = calculator.treynor_ratio(constant_benchmark)

        # ベータが NaN の場合、トレイナーレシオも NaN
        assert math.isnan(treynor) or math.isinf(treynor)


class TestInformationRatio:
    """情報レシオ計算のテスト."""

    def test_正常系_情報レシオが計算できる(
        self,
        sample_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> None:
        """ベンチマーク指定時に情報レシオが計算できることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            ポートフォリオのリターンデータ
        benchmark_returns : pd.Series
            ベンチマークのリターンデータ

        Notes
        -----
        Formula: IR = mean(active_returns) / std(active_returns) * sqrt(annualization_factor)
        where active_returns = portfolio_returns - benchmark_returns
        """
        calculator = RiskCalculator(sample_returns)
        ir = calculator.information_ratio(benchmark_returns)

        assert isinstance(ir, float)
        assert not math.isnan(ir)

    def test_正常系_情報レシオの計算式が正しい(
        self,
        sample_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> None:
        """情報レシオの計算式が正しいことを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            ポートフォリオのリターンデータ
        benchmark_returns : pd.Series
            ベンチマークのリターンデータ

        Notes
        -----
        Formula: IR = mean(active_returns) / std(active_returns) * sqrt(annualization_factor)
        """
        annualization_factor = 252

        calculator = RiskCalculator(
            sample_returns, annualization_factor=annualization_factor
        )
        ir = calculator.information_ratio(benchmark_returns)

        # 期待値の計算
        aligned = pd.DataFrame(
            {
                "portfolio": sample_returns,
                "benchmark": benchmark_returns,
            }
        ).dropna()

        portfolio_series = pd.Series(aligned["portfolio"])
        benchmark_series = pd.Series(aligned["benchmark"])
        active_returns = portfolio_series - benchmark_series
        expected = float(
            (active_returns.mean() / active_returns.std())
            * np.sqrt(annualization_factor)
        )

        assert math.isclose(ir, expected, rel_tol=1e-10)

    def test_正常系_アウトパフォーム時に正の情報レシオ(self) -> None:
        """ポートフォリオがベンチマークをアウトパフォームする場合、正の IR になることを確認.

        Notes
        -----
        アクティブリターンの平均が正の場合、情報レシオは正になる。
        """
        np.random.seed(42)
        # 共通のベースリターンに対して、ポートフォリオが常にアウトパフォーム
        base_returns = np.random.normal(0.001, 0.02, 100)
        portfolio_returns = pd.Series(base_returns + 0.001)  # 常に0.1%上回る
        benchmark_returns = pd.Series(base_returns)

        calculator = RiskCalculator(portfolio_returns)
        ir = calculator.information_ratio(benchmark_returns)

        assert ir > 0

    def test_正常系_アンダーパフォーム時に負の情報レシオ(self) -> None:
        """ポートフォリオがベンチマークをアンダーパフォームする場合、負の IR になることを確認.

        Notes
        -----
        アクティブリターンの平均が負の場合、情報レシオは負になる。
        """
        np.random.seed(42)
        # 共通のベースリターンに対して、ポートフォリオが常にアンダーパフォーム
        base_returns = np.random.normal(0.001, 0.02, 100)
        portfolio_returns = pd.Series(base_returns - 0.001)  # 常に0.1%下回る
        benchmark_returns = pd.Series(base_returns)

        calculator = RiskCalculator(portfolio_returns)
        ir = calculator.information_ratio(benchmark_returns)

        assert ir < 0

    def test_エッジケース_同一リターンでゼロまたはNaN(self) -> None:
        """ポートフォリオとベンチマークが同一の場合、ゼロまたは NaN になることを確認.

        Notes
        -----
        アクティブリターンがゼロの場合、平均もゼロで標準偏差もゼロになり、
        0/0 となるため NaN を返す。
        """
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))

        calculator = RiskCalculator(returns)
        ir = calculator.information_ratio(returns)

        # 同一リターンの場合、アクティブリターン = 0 で NaN
        assert math.isnan(ir) or math.isclose(ir, 0.0, abs_tol=1e-10)

    def test_エッジケース_トラッキングエラーゼロでInfまたはNaN(self) -> None:
        """トラッキングエラー（アクティブリターンの標準偏差）がゼロの場合の動作を確認.

        Notes
        -----
        トラッキングエラーがゼロでアクティブリターン平均が正の場合、無限大を返す。
        """
        # 定数のリターン（トラッキングエラーゼロ、アクティブリターン正）
        portfolio_returns = pd.Series([0.011] * 100)  # 定数リターン
        benchmark_returns = pd.Series(
            [0.010] * 100
        )  # 定数リターン（ポートフォリオより0.1%低い）

        calculator = RiskCalculator(portfolio_returns)
        ir = calculator.information_ratio(benchmark_returns)

        # トラッキングエラーゼロでアクティブリターン正の場合、無限大
        assert math.isinf(ir) and ir > 0


class TestBenchmarkMetricsErrors:
    """ベンチマーク指標のエラーハンドリングテスト."""

    def test_異常系_空のベンチマークでValueError(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """空のベンチマークリターンでエラーになることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            ポートフォリオのリターンデータ
        """
        empty_benchmark = pd.Series([], dtype=float)
        calculator = RiskCalculator(sample_returns)

        with pytest.raises(ValueError, match=r"benchmark.*empty"):
            calculator.beta(empty_benchmark)

        with pytest.raises(ValueError, match=r"benchmark.*empty"):
            calculator.treynor_ratio(empty_benchmark)

        with pytest.raises(ValueError, match=r"benchmark.*empty"):
            calculator.information_ratio(empty_benchmark)

    def test_異常系_共通日付なしでValueError(
        self,
        sample_returns: pd.Series,
    ) -> None:
        """ポートフォリオとベンチマークに共通日付がない場合エラーになることを確認.

        Parameters
        ----------
        sample_returns : pd.Series
            ポートフォリオのリターンデータ（2023年）
        """
        # 完全に異なる期間のベンチマーク
        benchmark_returns = pd.Series(
            np.random.normal(0.001, 0.02, 100),
            index=pd.date_range("2025-01-01", periods=100, freq="B"),
        )

        calculator = RiskCalculator(sample_returns)

        with pytest.raises(ValueError, match=r"common|overlapping"):
            calculator.beta(benchmark_returns)
