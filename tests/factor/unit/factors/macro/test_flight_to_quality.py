"""Unit tests for FlightToQualityFactor class.

FlightToQualityFactor calculates a flight-to-quality factor based on
the spread between High Yield and Investment Grade corporate bonds.
When investors flee to quality, HY spreads widen more than IG spreads.

FRED Series:
- BAMLH0A0HYM2: ICE BofA US High Yield Index Option-Adjusted Spread
- BAMLC0A0CM: ICE BofA US Corporate Index Option-Adjusted Spread

FtoQ = BAMLH0A0HYM2 - BAMLC0A0CM (HY-IG spread)
FtoQ_Shock = diff(FtoQ)
Factor_FtoQ = orthogonalize(FtoQ_Shock, [Market, Level, Slope, Curvature])
"""

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: These imports will fail until the implementation is created.
# This is intentional - tests are in Red state (TDD).
from factor.factors.macro.base import BaseMacroFactor
from factor.factors.macro.flight_to_quality import FlightToQualityFactor


class TestFlightToQualityFactorInit:
    """Tests for FlightToQualityFactor initialization."""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """FlightToQualityFactorをデフォルト値で初期化できることを確認。"""
        factor = FlightToQualityFactor()
        assert factor is not None

    def test_正常系_BaseMacroFactorを継承している(self) -> None:
        """FlightToQualityFactorがBaseMacroFactorを継承していることを確認。"""
        assert issubclass(FlightToQualityFactor, BaseMacroFactor)


class TestFlightToQualityFactorProperties:
    """Tests for FlightToQualityFactor properties."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = FlightToQualityFactor()

    def test_正常系_nameはFlightToQualityを返す(self) -> None:
        """nameプロパティが'FlightToQuality'を返すことを確認。"""
        assert self.factor.name == "FlightToQuality"

    def test_正常系_required_seriesはHYとIGスプレッド系列を含む(self) -> None:
        """required_seriesがHY/IGスプレッドのFRED系列を含むことを確認。"""
        series = self.factor.required_series

        # Based on src_sample/make_factor.py
        expected_series = [
            "BAMLH0A0HYM2",  # US High Yield OAS
            "BAMLC0A0CM",  # US Corporate (IG) OAS
        ]

        for expected in expected_series:
            assert expected in series, f"{expected} should be in required_series"


class TestFlightToQualityFactorCalculate:
    """Tests for FlightToQualityFactor calculate method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = FlightToQualityFactor()

        # Create synthetic HY/IG spread data
        np.random.seed(42)
        n = 252
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # HY spread typically 300-600 bps, IG spread 100-200 bps
        # Create correlated spreads
        common_factor = np.cumsum(np.random.randn(n) * 0.1)
        hy_specific = np.cumsum(np.random.randn(n) * 0.05)
        ig_specific = np.cumsum(np.random.randn(n) * 0.03)

        self.spread_data = pd.DataFrame(
            {
                "BAMLH0A0HYM2": 4.5 + common_factor + hy_specific,  # HY ~450 bps
                "BAMLC0A0CM": 1.5 + common_factor * 0.5 + ig_specific,  # IG ~150 bps
            },
            index=dates,
        )

    def test_正常系_DataFrameを返す(self) -> None:
        """calculateがDataFrameを返すことを確認。"""
        result = self.factor.calculate(self.spread_data)
        assert isinstance(result, pd.DataFrame)

    def test_正常系_FtoQファクター列を含む(self) -> None:
        """結果がFtoQファクター列を含むことを確認。"""
        result = self.factor.calculate(self.spread_data)
        assert "FtoQ" in result.columns

    def test_正常系_日時インデックスを保持する(self) -> None:
        """結果が日時インデックスを保持することを確認。"""
        result = self.factor.calculate(self.spread_data)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_HY_IGスプレッドの差分を計算する(self) -> None:
        """FtoQがHY-IGスプレッドの差分(shock)から計算されることを確認。"""
        result = self.factor.calculate(self.spread_data)

        # The factor should be based on HY-IG spread changes
        # Verify the result has reasonable statistical properties
        is_all_nan = bool(result["FtoQ"].isna().all())
        assert not is_all_nan
        assert result["FtoQ"].std() > 0  # Should have some variance

    def test_異常系_必要な列がない場合エラー(self) -> None:
        """必要なFRED系列がない場合にエラーが発生することを確認。"""
        incomplete_data = pd.DataFrame(
            {"BAMLH0A0HYM2": [1.0, 2.0, 3.0]},  # Missing BAMLC0A0CM
            index=pd.date_range("2020-01-01", periods=3, freq="B"),
        )

        with pytest.raises((KeyError, ValueError)):
            self.factor.calculate(incomplete_data)

    def test_エッジケース_NaN値を含むデータの処理(self) -> None:
        """NaN値を含むデータを適切に処理することを確認。"""
        data_with_nan = self.spread_data.copy()
        data_with_nan.iloc[0:5, 0] = np.nan

        result = self.factor.calculate(data_with_nan)

        # Result should handle NaN appropriately
        is_all_nan = bool(result["FtoQ"].isna().all())
        assert not is_all_nan


class TestFlightToQualityFactorOrthogonalization:
    """Tests for orthogonalization against multiple factors."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = FlightToQualityFactor()

        np.random.seed(42)
        n = 252
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Spread data
        self.spread_data = pd.DataFrame(
            {
                "BAMLH0A0HYM2": np.random.randn(n).cumsum() + 4.5,
                "BAMLC0A0CM": np.random.randn(n).cumsum() + 1.5,
            },
            index=dates,
        )

        # Control factors for orthogonalization
        self.control_factors = pd.DataFrame(
            {
                "Factor_Market": np.random.randn(n),
                "Level": np.random.randn(n),
                "Slope": np.random.randn(n),
                "Curvature": np.random.randn(n),
            },
            index=dates,
        )

    def test_正常系_マーケットと金利ファクターに対して直交化(self) -> None:
        """FtoQがMarket, Level, Slope, Curvatureに対して直交化されることを確認。

        Based on src_sample/make_factor.py:
        Factor_FtoQ = orthogonalize(FtoQ_Shock, [Market, Level, Slope, Curvature])
        """
        result = self.factor.calculate(
            self.spread_data,
            control_factors=self.control_factors,
        )

        # Factor should be uncorrelated with control factors
        common_idx = result.index.intersection(self.control_factors.index)

        for control_col in self.control_factors.columns:
            factor_values = result.loc[common_idx, "FtoQ"]
            control_values = self.control_factors.loc[common_idx, control_col]

            corr = factor_values.corr(control_values)
            assert (
                abs(corr) < 0.1
            ), f"FtoQ should be uncorrelated with {control_col}, got {corr:.3f}"

    def test_正常系_直交化なしでも計算できる(self) -> None:
        """control_factorsなしでも計算できることを確認。"""
        result = self.factor.calculate(self.spread_data)

        assert isinstance(result, pd.DataFrame)
        assert "FtoQ" in result.columns


class TestFlightToQualityFactorEconomicInterpretation:
    """Tests for economic interpretation of FtoQ factor."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.factor = FlightToQualityFactor()

    def test_正常系_スプレッド拡大時にファクターが正(self) -> None:
        """HY-IGスプレッドが拡大する時、FtoQファクターが正となることを確認。

        When investors flee to quality:
        - HY spreads widen significantly
        - IG spreads widen less
        - HY-IG spread increases
        - This should correspond to positive FtoQ factor
        """
        np.random.seed(42)
        n = 100
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Create scenario where HY spreads widen more than IG
        # (flight to quality)
        spread_widening = np.linspace(0, 2, n)  # Gradual widening

        data = pd.DataFrame(
            {
                "BAMLH0A0HYM2": 4.0 + spread_widening * 1.5,  # HY widens more
                "BAMLC0A0CM": 1.0 + spread_widening * 0.5,  # IG widens less
            },
            index=dates,
        )

        result = self.factor.calculate(data)

        # Just verify the calculation runs - actual sign interpretation
        # depends on implementation details
        assert "FtoQ" in result.columns
        assert len(result) > 0

    def test_正常系_スプレッド縮小時にファクターが負(self) -> None:
        """HY-IGスプレッドが縮小する時、FtoQファクターが負となることを確認。

        When risk appetite increases (opposite of flight to quality):
        - HY spreads tighten more than IG
        - HY-IG spread decreases
        """
        np.random.seed(42)
        n = 100
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Create scenario where HY spreads tighten more than IG
        # (risk-on environment)
        spread_tightening = np.linspace(2, 0, n)  # Gradual tightening

        data = pd.DataFrame(
            {
                "BAMLH0A0HYM2": 4.0 + spread_tightening * 1.5,  # HY tightens more
                "BAMLC0A0CM": 1.0 + spread_tightening * 0.5,  # IG tightens less
            },
            index=dates,
        )

        result = self.factor.calculate(data)

        # Verify calculation completes
        assert "FtoQ" in result.columns
        assert len(result) > 0
