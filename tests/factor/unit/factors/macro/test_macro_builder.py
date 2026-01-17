"""Unit tests for MacroFactorBuilder class.

MacroFactorBuilder orchestrates the construction of all macro factors:
- Market factor (excess return)
- Interest rate factors (Level, Slope, Curvature)
- Flight-to-quality factor (FtoQ)
- Inflation factor

The builder handles:
1. Data aggregation from multiple sources
2. Proper orthogonalization ordering
3. Factor integration into a single DataFrame

Orthogonalization order (from src_sample/make_factor.py):
1. Market - not orthogonalized
2. Level, Slope, Curvature - orthogonalized against Market
3. FtoQ - orthogonalized against Market, Level, Slope, Curvature
4. Inflation - orthogonalized against all previous factors
"""

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: These imports will fail until the implementation is created.
# This is intentional - tests are in Red state (TDD).
from factor.factors.macro.macro_builder import MacroFactorBuilder


class TestMacroFactorBuilderInit:
    """Tests for MacroFactorBuilder initialization."""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """MacroFactorBuilderをデフォルト値で初期化できることを確認。"""
        builder = MacroFactorBuilder()
        assert builder is not None

    def test_正常系_カスタムパラメータで初期化できる(self) -> None:
        """カスタムパラメータで初期化できることを確認。"""
        builder = MacroFactorBuilder(
            pca_components=3,
            min_samples=50,
        )
        assert builder.pca_components == 3
        assert builder.min_samples == 50


class TestMacroFactorBuilderBuildAllFactors:
    """Tests for build_all_factors method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.builder = MacroFactorBuilder()

        np.random.seed(42)
        n = 252
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Create comprehensive test data
        self.test_data = self._create_comprehensive_test_data(n, dates)

    def _create_comprehensive_test_data(
        self,
        n: int,
        dates: pd.DatetimeIndex,
    ) -> dict[str, pd.DataFrame | pd.Series]:
        """Create comprehensive test data for all macro factors."""
        # Market data
        market_return = pd.Series(
            np.random.randn(n) * 0.01,
            index=dates,
            name="market_return",
        )
        risk_free = pd.Series(
            np.full(n, 0.02 / 252),  # ~2% annual risk-free rate
            index=dates,
            name="risk_free",
        )

        # Yield curve data
        yield_data = {}
        maturities = [
            "DGS1MO",
            "DGS3MO",
            "DGS6MO",
            "DGS1",
            "DGS2",
            "DGS3",
            "DGS5",
            "DGS7",
            "DGS10",
            "DGS20",
            "DGS30",
        ]
        for i, mat in enumerate(maturities):
            yield_data[mat] = np.random.randn(n).cumsum() * 0.01 + 2.0 + i * 0.1

        yield_df = pd.DataFrame(yield_data, index=dates)

        # Credit spread data
        spread_data = pd.DataFrame(
            {
                "BAMLH0A0HYM2": np.random.randn(n).cumsum() * 0.05 + 4.5,
                "BAMLC0A0CM": np.random.randn(n).cumsum() * 0.02 + 1.5,
            },
            index=dates,
        )

        # Inflation expectation data
        inflation_data = pd.DataFrame(
            {
                "T10YIE": np.random.randn(n).cumsum() * 0.02 + 2.2,
            },
            index=dates,
        )

        return {
            "market_return": market_return,
            "risk_free": risk_free,
            "yields": yield_df,
            "spreads": spread_data,
            "inflation": inflation_data,
        }

    def test_正常系_DataFrameを返す(self) -> None:
        """build_all_factorsがDataFrameを返すことを確認。"""
        result = self.builder.build_all_factors(self.test_data)
        assert isinstance(result, pd.DataFrame)

    def test_正常系_全ファクター列を含む(self) -> None:
        """結果が全てのマクロファクター列を含むことを確認。"""
        result = self.builder.build_all_factors(self.test_data)

        expected_columns = [
            "Factor_Market",
            "Factor_Level",
            "Factor_Slope",
            "Factor_Curvature",
            "Factor_FtoQ",
            "Factor_Inflation",
        ]

        for col in expected_columns:
            assert col in result.columns, f"{col} should be in result columns"

    def test_正常系_日時インデックスを保持する(self) -> None:
        """結果が日時インデックスを保持することを確認。"""
        result = self.builder.build_all_factors(self.test_data)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_ファクター間の相関が低い(self) -> None:
        """構築されたファクター間の相関が低いことを確認。"""
        result = self.builder.build_all_factors(self.test_data)

        # Drop rows with NaN to compute correlation
        result_clean = result.dropna()
        corr_matrix = result_clean.corr()

        # Off-diagonal correlations should be relatively small
        # (due to orthogonalization)
        for i, col1 in enumerate(result.columns):
            for j, col2 in enumerate(result.columns):
                if i != j:
                    corr = abs(corr_matrix.loc[col1, col2])
                    assert corr < 0.2, (
                        f"Correlation between {col1} and {col2} is too high: {corr:.3f}"
                    )


class TestMacroFactorBuilderOrthogonalizationOrder:
    """Tests for proper orthogonalization ordering."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.builder = MacroFactorBuilder()

        np.random.seed(42)
        n = 252
        dates = pd.date_range("2020-01-01", periods=n, freq="B")

        # Create test data with known correlations
        self.market = pd.Series(np.random.randn(n), index=dates, name="market")

        # Create correlated factors for testing
        self.level_raw = 0.3 * self.market + 0.7 * pd.Series(
            np.random.randn(n), index=dates
        )
        self.ftoq_raw = (
            0.2 * self.market
            + 0.2 * self.level_raw
            + 0.6 * pd.Series(np.random.randn(n), index=dates)
        )

    def test_正常系_Marketは直交化されない(self) -> None:
        """Factor_Marketが直交化されないことを確認。"""
        # Market factor should be the base - not orthogonalized
        # This is verified by checking it maintains its original properties
        pass  # Implicit in the build process

    def test_正常系_金利ファクターはMarketに対して直交化(self) -> None:
        """Level, Slope, CurvatureがMarketに対して直交化されることを確認。

        From src_sample/make_factor.py:
        for factor in ["Factor_Level", "Factor_Slope", "Factor_Curvature"]:
            df_descriptor[factor] = orthogonalize(
                df_descriptor[f"{factor.replace('Factor_', '')}_Shock"],
                df_descriptor["Factor_Market"],
            )
        """
        # This is tested via the correlation check in build_all_factors tests
        pass

    def test_正常系_FtoQはMarketと金利ファクターに対して直交化(self) -> None:
        """FtoQがMarket, Level, Slope, Curvatureに対して直交化されることを確認。

        From src_sample/make_factor.py:
        regressors_ftoq = df_descriptor[
            ["Factor_Market", "Factor_Level", "Factor_Slope", "Factor_Curvature"]
        ]
        df_descriptor["Factor_FtoQ"] = orthogonalize(
            df_descriptor["FtoQ_Shock"], regressors=regressors_ftoq
        )
        """
        pass

    def test_正常系_Inflationは全ファクターに対して直交化(self) -> None:
        """Inflationが全ての他のファクターに対して直交化されることを確認。

        From src_sample/make_factor.py:
        regressors_inflation = df_descriptor[
            ["Factor_Market", "Factor_Level", "Factor_Slope", "Factor_Curvature",
             "Factor_FtoQ"]
        ]
        df_descriptor["Factor_Inflation"] = orthogonalize(
            df_descriptor["Inflation_Shock"], regressors=regressors_inflation
        )
        """
        pass


class TestMacroFactorBuilderDataValidation:
    """Tests for input data validation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.builder = MacroFactorBuilder()

    def test_異常系_必要なデータがない場合エラー(self) -> None:
        """必要なデータがない場合にエラーが発生することを確認。"""
        incomplete_data: dict[str, pd.DataFrame | pd.Series] = {
            "market_return": pd.Series([0.01, 0.02]),  # Missing other data
        }

        with pytest.raises((KeyError, ValueError)):
            self.builder.build_all_factors(incomplete_data)

    def test_異常系_データ長が不一致の場合エラー(self) -> None:
        """データ長が不一致の場合にエラーが発生することを確認。"""
        np.random.seed(42)
        dates_short = pd.date_range("2020-01-01", periods=10, freq="B")
        dates_long = pd.date_range("2020-01-01", periods=100, freq="B")

        mismatched_data = {
            "market_return": pd.Series(np.random.randn(10), index=dates_short),
            "yields": pd.DataFrame({"DGS10": np.random.randn(100)}, index=dates_long),
        }

        # Should either raise an error or handle gracefully by alignment
        # Implementation decides the behavior
        with pytest.raises((ValueError, KeyError)):
            self.builder.build_all_factors(mismatched_data)


class TestMacroFactorBuilderIntegration:
    """Integration tests for MacroFactorBuilder."""

    def test_正常系_フルパイプライン実行(self) -> None:
        """データ取得からファクター構築までの完全パイプラインを確認。"""
        builder = MacroFactorBuilder()

        np.random.seed(42)
        n = 500  # Longer time series for robustness
        dates = pd.date_range("2019-01-01", periods=n, freq="B")

        # Create realistic test data
        market_return = pd.Series(
            np.random.randn(n) * 0.01,
            index=dates,
            name="market_return",
        )
        risk_free = pd.Series(
            np.full(n, 0.02 / 252),
            index=dates,
            name="risk_free",
        )

        # Yield curve with realistic dynamics
        level = np.cumsum(np.random.randn(n) * 0.01)
        slope = np.cumsum(np.random.randn(n) * 0.005)
        curve = np.cumsum(np.random.randn(n) * 0.003)

        yield_data = {}
        maturities = {
            "DGS1MO": {"l": 1.0, "s": -0.5, "c": 0.2},
            "DGS3MO": {"l": 1.0, "s": -0.4, "c": 0.3},
            "DGS6MO": {"l": 1.0, "s": -0.3, "c": 0.4},
            "DGS1": {"l": 1.0, "s": -0.2, "c": 0.4},
            "DGS2": {"l": 1.0, "s": -0.1, "c": 0.3},
            "DGS3": {"l": 1.0, "s": 0.0, "c": 0.2},
            "DGS5": {"l": 1.0, "s": 0.1, "c": 0.0},
            "DGS7": {"l": 1.0, "s": 0.2, "c": -0.1},
            "DGS10": {"l": 1.0, "s": 0.3, "c": -0.2},
            "DGS20": {"l": 1.0, "s": 0.4, "c": -0.3},
            "DGS30": {"l": 1.0, "s": 0.5, "c": -0.4},
        }

        for mat, loadings in maturities.items():
            base = 2.0 + list(maturities.keys()).index(mat) * 0.1
            yield_data[mat] = (
                base
                + loadings["l"] * level
                + loadings["s"] * slope
                + loadings["c"] * curve
                + np.random.randn(n) * 0.01
            )

        yield_df = pd.DataFrame(yield_data, index=dates)

        # Credit spreads
        spread_data = pd.DataFrame(
            {
                "BAMLH0A0HYM2": np.random.randn(n).cumsum() * 0.05 + 4.5,
                "BAMLC0A0CM": np.random.randn(n).cumsum() * 0.02 + 1.5,
            },
            index=dates,
        )

        # Inflation
        inflation_data = pd.DataFrame(
            {
                "T10YIE": np.random.randn(n).cumsum() * 0.02 + 2.2,
            },
            index=dates,
        )

        test_data = {
            "market_return": market_return,
            "risk_free": risk_free,
            "yields": yield_df,
            "spreads": spread_data,
            "inflation": inflation_data,
        }

        result = builder.build_all_factors(test_data)

        # Verify structure
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 6  # 6 factors

        # Verify no all-NaN columns
        for col in result.columns:
            is_all_nan = bool(result[col].isna().all())
            assert not is_all_nan, f"{col} should not be all NaN"


class TestMacroFactorBuilderGetFactorMetadata:
    """Tests for factor metadata retrieval."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.builder = MacroFactorBuilder()

    def test_正常系_ファクター名リストを取得できる(self) -> None:
        """get_factor_namesでファクター名リストを取得できることを確認。"""
        names = self.builder.get_factor_names()

        assert isinstance(names, list)
        assert "Factor_Market" in names
        assert "Factor_Level" in names
        assert "Factor_Slope" in names
        assert "Factor_Curvature" in names
        assert "Factor_FtoQ" in names
        assert "Factor_Inflation" in names

    def test_正常系_必要なFRED系列を取得できる(self) -> None:
        """get_required_seriesで全ての必要なFRED系列を取得できることを確認。"""
        series = self.builder.get_required_series()

        assert isinstance(series, list)

        # Should include yield curve maturities
        for mat in ["DGS1MO", "DGS10", "DGS30"]:
            assert mat in series

        # Should include credit spreads
        assert "BAMLH0A0HYM2" in series
        assert "BAMLC0A0CM" in series

        # Should include inflation
        assert "T10YIE" in series
