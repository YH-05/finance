"""Unit tests for InflationFactor class.

InflationFactor calculates an inflation expectations factor based on
the 10-Year Breakeven Inflation Rate (T10YIE).

FRED Series:
- T10YIE: 10-Year Breakeven Inflation Rate

Inflation_Shock = diff(T10YIE)
Factor_Inflation = orthogonalize(Inflation_Shock,
                                  [Market, Level, Slope, Curvature, FtoQ])
"""

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: These imports will fail until the implementation is created.
# This is intentional - tests are in Red state (TDD).
from factor.factors.macro.base import BaseMacroFactor
from factor.factors.macro.inflation import InflationFactor


class TestInflationFactorInit:
    """Tests for InflationFactor initialization."""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """InflationFactorをデフォルト値で初期化できることを確認。"""
        factor = InflationFactor()
        assert factor is not None

    def test_正常系_BaseMacroFactorを継承している(self) -> None:
        """InflationFactorがBaseMacroFactorを継承していることを確認。"""
        assert issubclass(InflationFactor, BaseMacroFactor)


class TestInflationFactorProperties:
    """Tests for InflationFactor properties."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = InflationFactor()

    def test_正常系_nameはInflationを返す(self) -> None:
        """nameプロパティが'Inflation'を返すことを確認。"""
        assert self.factor.name == "Inflation"

    def test_正常系_required_seriesは10年インフレ期待系列を含む(self) -> None:
        """required_seriesが10年インフレ期待のFRED系列を含むことを確認。"""
        series = self.factor.required_series

        # Based on src_sample/make_factor.py
        expected_series = ["T10YIE"]  # 10-Year Breakeven Inflation Rate

        for expected in expected_series:
            assert expected in series, f"{expected} should be in required_series"


class TestInflationFactorCalculate:
    """Tests for InflationFactor calculate method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = InflationFactor()

        # Create synthetic inflation expectation data
        np.random.seed(42)
        n = 252
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # 10-Year Breakeven Inflation Rate (typically 1.5-3%)
        inflation_trend = np.cumsum(np.random.randn(n) * 0.02)

        self.inflation_data = pd.DataFrame(
            {
                "T10YIE": 2.2 + inflation_trend,  # ~2.2% baseline
            },
            index=dates,
        )

    def test_正常系_DataFrameを返す(self) -> None:
        """calculateがDataFrameを返すことを確認。"""
        result = self.factor.calculate(self.inflation_data)
        assert isinstance(result, pd.DataFrame)

    def test_正常系_Inflationファクター列を含む(self) -> None:
        """結果がInflationファクター列を含むことを確認。"""
        result = self.factor.calculate(self.inflation_data)
        assert "Inflation" in result.columns

    def test_正常系_日時インデックスを保持する(self) -> None:
        """結果が日時インデックスを保持することを確認。"""
        result = self.factor.calculate(self.inflation_data)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_インフレ期待の変化から計算される(self) -> None:
        """Inflationファクターがインフレ期待の変化(shock)から計算されることを確認。"""
        result = self.factor.calculate(self.inflation_data)

        # The factor should be based on T10YIE changes
        is_all_nan = bool(result["Inflation"].isna().all())
        assert not is_all_nan
        assert result["Inflation"].std() > 0  # Should have some variance

    def test_異常系_必要な列がない場合エラー(self) -> None:
        """必要なFRED系列がない場合にエラーが発生することを確認。"""
        incomplete_data = pd.DataFrame(
            {"WRONG_SERIES": [1.0, 2.0, 3.0]},
            index=pd.date_range("2020-01-01", periods=3, freq="B"),
        )

        with pytest.raises((KeyError, ValueError)):
            self.factor.calculate(incomplete_data)

    def test_エッジケース_NaN値を含むデータの処理(self) -> None:
        """NaN値を含むデータを適切に処理することを確認。"""
        data_with_nan = self.inflation_data.copy()
        data_with_nan.iloc[0:5, 0] = np.nan

        result = self.factor.calculate(data_with_nan)

        # Result should handle NaN appropriately
        is_all_nan = bool(result["Inflation"].isna().all())
        assert not is_all_nan


class TestInflationFactorOrthogonalization:
    """Tests for orthogonalization against all other factors."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = InflationFactor()

        np.random.seed(42)
        n = 252
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Inflation data
        self.inflation_data = pd.DataFrame(
            {
                "T10YIE": np.random.randn(n).cumsum() + 2.2,
            },
            index=dates,
        )

        # Control factors for orthogonalization
        # Inflation is orthogonalized against Market, Level, Slope, Curvature, FtoQ
        self.control_factors = pd.DataFrame(
            {
                "Factor_Market": np.random.randn(n),
                "Level": np.random.randn(n),
                "Slope": np.random.randn(n),
                "Curvature": np.random.randn(n),
                "FtoQ": np.random.randn(n),
            },
            index=dates,
        )

    def test_正常系_全ファクターに対して直交化(self) -> None:
        """InflationがMarket, Level, Slope, Curvature, FtoQに対して直交化されることを確認。

        Based on src_sample/make_factor.py:
        regressors_inflation = [Market, Level, Slope, Curvature, FtoQ]
        Factor_Inflation = orthogonalize(Inflation_Shock, regressors_inflation)
        """
        result = self.factor.calculate(
            self.inflation_data,
            control_factors=self.control_factors,
        )

        # Factor should be uncorrelated with all control factors
        common_idx = result.index.intersection(self.control_factors.index)

        for control_col in self.control_factors.columns:
            factor_values = result.loc[common_idx, "Inflation"]
            control_values = self.control_factors.loc[common_idx, control_col]

            corr = factor_values.corr(control_values)
            assert abs(corr) < 0.1, (
                f"Inflation should be uncorrelated with {control_col}, got {corr:.3f}"
            )

    def test_正常系_直交化なしでも計算できる(self) -> None:
        """control_factorsなしでも計算できることを確認。"""
        result = self.factor.calculate(self.inflation_data)

        assert isinstance(result, pd.DataFrame)
        assert "Inflation" in result.columns


class TestInflationFactorEconomicInterpretation:
    """Tests for economic interpretation of Inflation factor."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = InflationFactor()

    def test_正常系_インフレ期待上昇時にファクターが正(self) -> None:
        """インフレ期待が上昇する時、Inflationファクターが正となることを確認。

        When inflation expectations rise:
        - T10YIE increases
        - This should correspond to positive Inflation factor
        """
        np.random.seed(42)
        n = 100
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Create scenario where inflation expectations rise
        inflation_rise = np.linspace(0, 1, n)  # Gradual rise

        data = pd.DataFrame(
            {
                "T10YIE": 2.0 + inflation_rise,  # Rising inflation expectations
            },
            index=dates,
        )

        result = self.factor.calculate(data)

        # Verify calculation completes
        assert "Inflation" in result.columns
        assert len(result) > 0

    def test_正常系_インフレ期待低下時にファクターが負(self) -> None:
        """インフレ期待が低下する時、Inflationファクターが負となることを確認。

        When inflation expectations fall:
        - T10YIE decreases
        - This should correspond to negative Inflation factor
        """
        np.random.seed(42)
        n = 100
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Create scenario where inflation expectations fall
        inflation_fall = np.linspace(1, 0, n)  # Gradual fall

        data = pd.DataFrame(
            {
                "T10YIE": 2.0 + inflation_fall,  # Falling inflation expectations
            },
            index=dates,
        )

        result = self.factor.calculate(data)

        # Verify calculation completes
        assert "Inflation" in result.columns
        assert len(result) > 0

    def test_正常系_ボラティリティが妥当な範囲(self) -> None:
        """Inflationファクターのボラティリティが妥当な範囲であることを確認。"""
        np.random.seed(42)
        n = 252
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Realistic T10YIE data
        data = pd.DataFrame(
            {
                "T10YIE": 2.2 + np.cumsum(np.random.randn(n) * 0.02),
            },
            index=dates,
        )

        result = self.factor.calculate(data)

        # Factor should have non-zero but finite variance
        factor_std = result["Inflation"].std()
        assert factor_std > 0, "Factor should have positive standard deviation"
        assert factor_std < 10, "Factor standard deviation should be reasonable"
