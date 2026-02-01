"""Integration tests for macro factor pipeline.

This module tests the MacroFactorBuilder class and its integration
with all dependent macro factor components.
"""

import numpy as np
import pandas as pd
import pytest
from factor.factors.macro.flight_to_quality import HY_SPREAD_SERIES, IG_SPREAD_SERIES
from factor.factors.macro.inflation import INFLATION_SERIES
from factor.factors.macro.interest_rate import TREASURY_YIELD_SERIES
from factor.factors.macro.macro_builder import FACTOR_NAMES, MacroFactorBuilder


class TestMacroFactorPipeline:
    """Integration tests for MacroFactorBuilder pipeline."""

    @pytest.fixture
    def sample_yields(self) -> pd.DataFrame:
        """Create sample Treasury yield data for testing."""
        np.random.seed(42)
        n_samples = 100
        dates = pd.date_range("2020-01-01", periods=n_samples, freq="D")

        # Create realistic yield curve data (increasing with maturity)
        base_yields = {
            "DGS1MO": 0.5,
            "DGS3MO": 0.7,
            "DGS6MO": 0.9,
            "DGS1": 1.2,
            "DGS2": 1.5,
            "DGS3": 1.8,
            "DGS5": 2.2,
            "DGS7": 2.5,
            "DGS10": 2.8,
            "DGS20": 3.2,
            "DGS30": 3.5,
        }

        data = {}
        for series_id, base_yield in base_yields.items():
            # Random walk around base yield
            changes = np.random.randn(n_samples) * 0.02
            yields = base_yield + np.cumsum(changes)
            data[series_id] = yields

        return pd.DataFrame(data, index=dates)

    @pytest.fixture
    def sample_spreads(self) -> pd.DataFrame:
        """Create sample credit spread data for testing."""
        np.random.seed(42)
        n_samples = 100
        dates = pd.date_range("2020-01-01", periods=n_samples, freq="D")

        # HY spread (typically 3-6%)
        hy_base = 4.5
        hy_changes = np.random.randn(n_samples) * 0.1
        hy_spread = hy_base + np.cumsum(hy_changes)

        # IG spread (typically 0.5-2%)
        ig_base = 1.0
        ig_changes = np.random.randn(n_samples) * 0.03
        ig_spread = ig_base + np.cumsum(ig_changes)

        return pd.DataFrame(
            {
                HY_SPREAD_SERIES: hy_spread,
                IG_SPREAD_SERIES: ig_spread,
            },
            index=dates,
        )

    @pytest.fixture
    def sample_inflation(self) -> pd.DataFrame:
        """Create sample inflation expectation data for testing."""
        np.random.seed(42)
        n_samples = 100
        dates = pd.date_range("2020-01-01", periods=n_samples, freq="D")

        # Inflation expectation (typically 1.5-3%)
        inflation_base = 2.2
        inflation_changes = np.random.randn(n_samples) * 0.02
        inflation = inflation_base + np.cumsum(inflation_changes)

        return pd.DataFrame(
            {
                INFLATION_SERIES: inflation,
            },
            index=dates,
        )

    @pytest.fixture
    def sample_market_data(self) -> tuple[pd.Series, pd.Series]:
        """Create sample market return and risk-free data."""
        np.random.seed(42)
        n_samples = 100
        dates = pd.date_range("2020-01-01", periods=n_samples, freq="D")

        # Market return
        market_return = pd.Series(
            np.random.randn(n_samples) * 0.01,
            index=dates,
            name="market_return",
        )

        # Risk-free rate
        risk_free = pd.Series(
            np.full(n_samples, 0.001),  # 0.1% daily risk-free
            index=dates,
            name="risk_free",
        )

        return market_return, risk_free

    @pytest.fixture
    def complete_input_data(
        self,
        sample_yields: pd.DataFrame,
        sample_spreads: pd.DataFrame,
        sample_inflation: pd.DataFrame,
        sample_market_data: tuple[pd.Series, pd.Series],
    ) -> dict[str, pd.DataFrame | pd.Series]:
        """Create complete input data for MacroFactorBuilder."""
        market_return, risk_free = sample_market_data

        return {
            "market_return": market_return,
            "risk_free": risk_free,
            "yields": sample_yields,
            "spreads": sample_spreads,
            "inflation": sample_inflation,
        }

    def test_正常系_全依存関係が揃っている場合の完全なパイプライン(
        self,
        complete_input_data: dict[str, pd.DataFrame | pd.Series],
    ) -> None:
        """全ての依存データが揃っている場合、完全なパイプラインが正常に動作することを確認。"""
        builder = MacroFactorBuilder(pca_components=3, min_samples=20)

        result = builder.build_all_factors(complete_input_data)

        # Output columns check
        assert list(result.columns) == FACTOR_NAMES

        # Output should have data
        assert len(result) > 0

        # All factors should be numeric
        for col in result.columns:
            assert result[col].dtype in [np.float64, np.float32]

        # Check that factors are not all NaN
        for col in result.columns:
            assert bool(result[col].notna().any()), f"{col} is all NaN"

    def test_正常系_MacroFactorBuilderが全マクロファクターを構築できる(
        self,
        complete_input_data: dict[str, pd.DataFrame | pd.Series],
    ) -> None:
        """MacroFactorBuilderが6つのマクロファクターを正しく構築できることを確認。"""
        builder = MacroFactorBuilder()

        result = builder.build_all_factors(complete_input_data)

        # Should have exactly 6 factors
        assert len(result.columns) == 6

        # Check each factor exists
        expected_factors = [
            "Factor_Market",
            "Factor_Level",
            "Factor_Slope",
            "Factor_Curvature",
            "Factor_FtoQ",
            "Factor_Inflation",
        ]
        for factor in expected_factors:
            assert factor in result.columns

    def test_正常系_ファクター間の直交性を確認(
        self,
        complete_input_data: dict[str, pd.DataFrame | pd.Series],
    ) -> None:
        """直交化されたファクター間の相関が低いことを確認。"""
        builder = MacroFactorBuilder(min_samples=20)

        result = builder.build_all_factors(complete_input_data)

        # Drop NaN for correlation calculation
        result_clean = result.dropna()

        # Calculate correlation matrix
        corr_matrix = result_clean.corr()

        # Orthogonalized factors should have low correlation
        # (not perfectly zero due to finite sample effects)
        orthogonalized_pairs = [
            ("Factor_Level", "Factor_Market"),
            ("Factor_Slope", "Factor_Market"),
            ("Factor_Curvature", "Factor_Market"),
        ]

        for factor1, factor2 in orthogonalized_pairs:
            corr = abs(corr_matrix.loc[factor1, factor2])
            assert corr < 0.3, f"Correlation between {factor1} and {factor2} is {corr}"

    def test_異常系_yieldsデータがない場合KeyError(
        self,
        sample_spreads: pd.DataFrame,
        sample_inflation: pd.DataFrame,
        sample_market_data: tuple[pd.Series, pd.Series],
    ) -> None:
        """yields データが欠落している場合、KeyError が発生することを確認。"""
        market_return, risk_free = sample_market_data

        incomplete_data = {
            "market_return": market_return,
            "risk_free": risk_free,
            # "yields" is missing
            "spreads": sample_spreads,
            "inflation": sample_inflation,
        }

        builder = MacroFactorBuilder()

        with pytest.raises(KeyError, match="Missing required data keys"):
            builder.build_all_factors(incomplete_data)

    def test_異常系_spreadsデータがない場合KeyError(
        self,
        sample_yields: pd.DataFrame,
        sample_inflation: pd.DataFrame,
        sample_market_data: tuple[pd.Series, pd.Series],
    ) -> None:
        """spreads データが欠落している場合、KeyError が発生することを確認。"""
        market_return, risk_free = sample_market_data

        incomplete_data = {
            "market_return": market_return,
            "risk_free": risk_free,
            "yields": sample_yields,
            # "spreads" is missing
            "inflation": sample_inflation,
        }

        builder = MacroFactorBuilder()

        with pytest.raises(KeyError, match="Missing required data keys"):
            builder.build_all_factors(incomplete_data)

    def test_異常系_inflationデータがない場合KeyError(
        self,
        sample_yields: pd.DataFrame,
        sample_spreads: pd.DataFrame,
        sample_market_data: tuple[pd.Series, pd.Series],
    ) -> None:
        """inflation データが欠落している場合、KeyError が発生することを確認。"""
        market_return, risk_free = sample_market_data

        incomplete_data = {
            "market_return": market_return,
            "risk_free": risk_free,
            "yields": sample_yields,
            "spreads": sample_spreads,
            # "inflation" is missing
        }

        builder = MacroFactorBuilder()

        with pytest.raises(KeyError, match="Missing required data keys"):
            builder.build_all_factors(incomplete_data)

    def test_異常系_yieldsがDataFrameでない場合ValueError(
        self,
        sample_spreads: pd.DataFrame,
        sample_inflation: pd.DataFrame,
        sample_market_data: tuple[pd.Series, pd.Series],
    ) -> None:
        """yields が DataFrame でない場合、ValueError が発生することを確認。"""
        market_return, risk_free = sample_market_data

        invalid_data = {
            "market_return": market_return,
            "risk_free": risk_free,
            "yields": market_return,  # Series instead of DataFrame
            "spreads": sample_spreads,
            "inflation": sample_inflation,
        }

        builder = MacroFactorBuilder()

        with pytest.raises(ValueError, match="'yields' must be a DataFrame"):
            builder.build_all_factors(invalid_data)

    def test_異常系_spread列が欠落している場合KeyError(
        self,
        sample_yields: pd.DataFrame,
        sample_inflation: pd.DataFrame,
        sample_market_data: tuple[pd.Series, pd.Series],
    ) -> None:
        """spreads に必要な列がない場合、KeyError が発生することを確認。"""
        market_return, risk_free = sample_market_data
        dates = pd.date_range("2020-01-01", periods=100, freq="D")

        # Missing IG_SPREAD_SERIES column
        invalid_spreads = pd.DataFrame(
            {
                HY_SPREAD_SERIES: np.random.randn(100),
                # IG_SPREAD_SERIES is missing
            },
            index=dates,
        )

        invalid_data = {
            "market_return": market_return,
            "risk_free": risk_free,
            "yields": sample_yields,
            "spreads": invalid_spreads,
            "inflation": sample_inflation,
        }

        builder = MacroFactorBuilder()

        with pytest.raises(KeyError, match="Missing spread series"):
            builder.build_all_factors(invalid_data)

    def test_正常系_ヘルパーメソッドの動作確認(self) -> None:
        """ヘルパーメソッドが正しく動作することを確認。"""
        builder = MacroFactorBuilder(pca_components=3, min_samples=20)

        # get_factor_names
        factor_names = builder.get_factor_names()
        assert factor_names == FACTOR_NAMES
        assert len(factor_names) == 6

        # get_required_series
        required_series = builder.get_required_series()
        assert len(required_series) == len(TREASURY_YIELD_SERIES) + 3
        assert HY_SPREAD_SERIES in required_series
        assert IG_SPREAD_SERIES in required_series
        assert INFLATION_SERIES in required_series

    def test_正常系_min_samplesパラメータの効果(
        self,
        complete_input_data: dict[str, pd.DataFrame | pd.Series],
    ) -> None:
        """min_samples パラメータが正しく機能することを確認。"""
        # Large min_samples should require more data
        builder_strict = MacroFactorBuilder(min_samples=50)
        result = builder_strict.build_all_factors(complete_input_data)

        # Should still work with sufficient data
        assert len(result) > 0

        # Very large min_samples with insufficient data should fail
        from factor.errors import InsufficientDataError

        builder_too_strict = MacroFactorBuilder(min_samples=200)

        with pytest.raises(InsufficientDataError):
            # Should fail due to insufficient data
            builder_too_strict.build_all_factors(complete_input_data)

    def test_正常系_pca_componentsパラメータの効果(
        self,
        complete_input_data: dict[str, pd.DataFrame | pd.Series],
    ) -> None:
        """pca_components パラメータが正しく機能することを確認。"""
        # Note: MacroFactorBuilder currently requires 3 PCA components
        # because it assumes Level, Slope, and Curvature all exist
        # This test verifies the default behavior with 3 components
        builder = MacroFactorBuilder(pca_components=3, min_samples=20)

        result = builder.build_all_factors(complete_input_data)

        # All factors should exist with 3 components
        assert "Factor_Market" in result.columns
        assert "Factor_Level" in result.columns
        assert "Factor_Slope" in result.columns
        assert "Factor_Curvature" in result.columns
