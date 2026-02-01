"""Regression tests for Orthogonalizer.

This module verifies that Orthogonalizer methods produce consistent results
by comparing against known expected values.

Tolerance: 1e-10
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from factor.core.orthogonalization import Orthogonalizer

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestOrthogonalizerRegression:
    """Regression tests for Orthogonalizer class."""

    @pytest.fixture
    def single_expected(self) -> pd.DataFrame:
        """Load expected values for single orthogonalization from fixture."""
        return pd.read_parquet(
            FIXTURES_DIR / "orthogonalization_single_expected.parquet"
        )

    @pytest.fixture
    def cascade_expected(self) -> pd.DataFrame:
        """Load expected values for cascade orthogonalization from fixture."""
        return pd.read_parquet(
            FIXTURES_DIR / "orthogonalization_cascade_expected.parquet"
        )

    @pytest.fixture
    def metadata(self) -> pd.DataFrame:
        """Load metadata from fixture."""
        return pd.read_parquet(FIXTURES_DIR / "orthogonalization_metadata.parquet")

    @pytest.fixture
    def orthogonalizer(self) -> Orthogonalizer:
        """Create Orthogonalizer instance for testing."""
        return Orthogonalizer(min_samples=20)

    def test_回帰_orthogonalize_残差の固定期待値との比較(
        self,
        orthogonalizer: Orthogonalizer,
        single_expected: pd.DataFrame,
    ) -> None:
        """Orthogonalizer.orthogonalize の残差が既知の期待値と一致することを確認。"""
        control = single_expected["control"]
        factor_to_clean = pd.Series(single_expected["factor_to_clean"])
        expected_residuals = single_expected["residuals_expected"]

        result = orthogonalizer.orthogonalize(
            factor_to_clean,
            control,
        )

        # Compare residuals
        actual_residuals = result.orthogonalized_data.iloc[:, 0]

        np.testing.assert_array_almost_equal(
            actual_residuals.to_numpy(),
            expected_residuals.to_numpy(),
            decimal=10,
        )

    def test_回帰_orthogonalize_R2の検証(
        self,
        orthogonalizer: Orthogonalizer,
        single_expected: pd.DataFrame,
        metadata: pd.DataFrame,
    ) -> None:
        """Orthogonalizer.orthogonalize の R-squared が既知の期待値と一致することを確認。"""
        control = single_expected["control"]
        factor_to_clean = pd.Series(single_expected["factor_to_clean"])
        expected_r_squared = metadata["r_squared_single"].iloc[0]

        result = orthogonalizer.orthogonalize(
            factor_to_clean,
            control,
        )

        np.testing.assert_almost_equal(
            result.r_squared,
            expected_r_squared,
            decimal=10,
        )

    def test_回帰_orthogonalize_cascade_結果検証(
        self,
        orthogonalizer: Orthogonalizer,
        cascade_expected: pd.DataFrame,
    ) -> None:
        """Orthogonalizer.orthogonalize_cascade の結果が既知の期待値と一致することを確認。"""
        # Extract input factors
        factors: dict[str, pd.Series] = {
            "f1": pd.Series(cascade_expected["f1"]),
            "f2": pd.Series(cascade_expected["f2"]),
            "f3": pd.Series(cascade_expected["f3"]),
        }

        # Run cascade orthogonalization
        results = orthogonalizer.orthogonalize_cascade(
            factors,
            order=["f1", "f2", "f3"],
        )

        # f1 should be unchanged
        f1_result = results["f1"].orthogonalized_data.iloc[:, 0]
        np.testing.assert_array_almost_equal(
            f1_result.to_numpy(),
            cascade_expected["f1_ortho"].to_numpy(),
            decimal=10,
        )

        # f2 should be orthogonalized against f1
        f2_result = results["f2"].orthogonalized_data.iloc[:, 0]
        np.testing.assert_array_almost_equal(
            f2_result.to_numpy(),
            cascade_expected["f2_ortho"].to_numpy(),
            decimal=10,
        )

        # f3 should be orthogonalized against f1 and f2
        f3_result = results["f3"].orthogonalized_data.iloc[:, 0]
        np.testing.assert_array_almost_equal(
            f3_result.to_numpy(),
            cascade_expected["f3_ortho"].to_numpy(),
            decimal=10,
        )


class TestOrthogonalizerRegressionProperties:
    """Property-based regression tests for Orthogonalizer."""

    @pytest.fixture
    def orthogonalizer(self) -> Orthogonalizer:
        """Create Orthogonalizer instance for testing."""
        return Orthogonalizer(min_samples=20)

    def test_回帰_直交化後の相関がゼロに近い(
        self,
        orthogonalizer: Orthogonalizer,
    ) -> None:
        """直交化後、コントロール変数との相関がゼロに近いことを確認。"""
        np.random.seed(42)
        n = 100

        # Create correlated variables
        control = pd.Series(np.random.randn(n), name="control")
        factor = pd.Series(0.5 * control + np.random.randn(n) * 0.5, name="factor")

        result = orthogonalizer.orthogonalize(factor, control)

        # Residuals should be uncorrelated with control
        residuals = result.orthogonalized_data.iloc[:, 0]
        correlation = residuals.corr(control)

        assert abs(correlation) < 1e-10

    def test_回帰_残差の平均がゼロ(
        self,
        orthogonalizer: Orthogonalizer,
    ) -> None:
        """OLS残差の平均がゼロであることを確認。"""
        np.random.seed(42)
        n = 100

        control = pd.Series(np.random.randn(n), name="control")
        factor = pd.Series(0.5 * control + np.random.randn(n) * 0.5, name="factor")

        result = orthogonalizer.orthogonalize(factor, control)

        # Residuals mean should be approximately zero
        residuals = result.orthogonalized_data.iloc[:, 0]
        assert abs(residuals.mean()) < 1e-10

    def test_回帰_R2の範囲が有効(
        self,
        orthogonalizer: Orthogonalizer,
    ) -> None:
        """R-squared が [0, 1] の範囲内であることを確認。"""
        np.random.seed(42)
        n = 100

        control = pd.Series(np.random.randn(n), name="control")
        factor = pd.Series(0.5 * control + np.random.randn(n) * 0.5, name="factor")

        result = orthogonalizer.orthogonalize(factor, control)

        assert 0 <= result.r_squared <= 1

    def test_回帰_複数コントロール変数での直交化(
        self,
        orthogonalizer: Orthogonalizer,
    ) -> None:
        """複数のコントロール変数に対する直交化が正しく動作することを確認。"""
        np.random.seed(42)
        n = 100

        control1 = pd.Series(np.random.randn(n), name="control1")
        control2 = pd.Series(np.random.randn(n), name="control2")
        controls = pd.DataFrame({"control1": control1, "control2": control2})

        factor = pd.Series(
            0.3 * control1 + 0.4 * control2 + np.random.randn(n) * 0.3,
            name="factor",
        )

        result = orthogonalizer.orthogonalize(factor, controls)

        residuals = result.orthogonalized_data.iloc[:, 0]

        # Residuals should be uncorrelated with both controls
        corr1 = residuals.corr(control1)
        corr2 = residuals.corr(control2)

        assert abs(corr1) < 1e-10
        assert abs(corr2) < 1e-10


class TestOrthogonalizerRegressionCascade:
    """Cascade orthogonalization regression tests."""

    @pytest.fixture
    def orthogonalizer(self) -> Orthogonalizer:
        """Create Orthogonalizer instance for testing."""
        return Orthogonalizer(min_samples=20)

    def test_回帰_cascade_最初のファクターは未変更(
        self,
        orthogonalizer: Orthogonalizer,
    ) -> None:
        """Cascade 直交化で最初のファクターが変更されないことを確認。"""
        np.random.seed(42)
        n = 100

        factors = {
            "f1": pd.Series(np.random.randn(n), name="f1"),
            "f2": pd.Series(np.random.randn(n), name="f2"),
            "f3": pd.Series(np.random.randn(n), name="f3"),
        }

        results = orthogonalizer.orthogonalize_cascade(
            factors, order=["f1", "f2", "f3"]
        )

        # f1 should be exactly unchanged
        f1_result = results["f1"].orthogonalized_data.iloc[:, 0]
        pd.testing.assert_series_equal(
            f1_result,
            factors["f1"],
            check_names=False,
        )

        # f1 R-squared should be 0
        assert results["f1"].r_squared == 0.0

    def test_回帰_cascade_順序依存性(
        self,
        orthogonalizer: Orthogonalizer,
    ) -> None:
        """Cascade 直交化の結果が順序に依存することを確認。"""
        np.random.seed(42)
        n = 100

        # Create correlated factors
        f1 = pd.Series(np.random.randn(n), name="f1")
        f2 = pd.Series(0.5 * f1 + np.random.randn(n) * 0.5, name="f2")
        f3 = pd.Series(0.3 * f1 + 0.3 * f2 + np.random.randn(n) * 0.4, name="f3")

        factors = {"f1": f1, "f2": f2, "f3": f3}

        # Order 1: f1 -> f2 -> f3
        results1 = orthogonalizer.orthogonalize_cascade(
            factors, order=["f1", "f2", "f3"]
        )

        # Order 2: f2 -> f1 -> f3
        results2 = orthogonalizer.orthogonalize_cascade(
            factors, order=["f2", "f1", "f3"]
        )

        # Results should be different due to order
        f1_order1 = results1["f1"].orthogonalized_data.iloc[:, 0]
        f1_order2 = results2["f1"].orthogonalized_data.iloc[:, 0]

        # In order 1, f1 is unchanged; in order 2, f1 is orthogonalized against f2
        assert not np.allclose(f1_order1.values, f1_order2.values)

    def test_回帰_cascade_全ペアの直交性(
        self,
        orthogonalizer: Orthogonalizer,
    ) -> None:
        """Cascade 直交化後、すべてのファクターペアが直交することを確認。"""
        np.random.seed(42)
        n = 100

        # Create correlated factors
        f1 = pd.Series(np.random.randn(n), name="f1")
        f2 = pd.Series(0.5 * f1 + np.random.randn(n) * 0.5, name="f2")
        f3 = pd.Series(0.3 * f1 + 0.3 * f2 + np.random.randn(n) * 0.4, name="f3")

        factors = {"f1": f1, "f2": f2, "f3": f3}

        results = orthogonalizer.orthogonalize_cascade(
            factors, order=["f1", "f2", "f3"]
        )

        # Get orthogonalized factors
        ortho_f1 = results["f1"].orthogonalized_data.iloc[:, 0]
        ortho_f2 = results["f2"].orthogonalized_data.iloc[:, 0]
        ortho_f3 = results["f3"].orthogonalized_data.iloc[:, 0]

        # All pairs should be uncorrelated
        # f2 is orthogonalized against f1
        corr_f1_f2 = ortho_f1.corr(ortho_f2)
        assert abs(corr_f1_f2) < 1e-10

        # f3 is orthogonalized against both f1 and f2
        corr_f1_f3 = ortho_f1.corr(ortho_f3)
        corr_f2_f3 = ortho_f2.corr(ortho_f3)
        assert abs(corr_f1_f3) < 1e-10
        assert abs(corr_f2_f3) < 1e-10


class TestOrthogonalizerRegressionEdgeCases:
    """Edge case regression tests for Orthogonalizer."""

    def test_回帰_min_samples未満でエラー(self) -> None:
        """min_samples 未満のデータでエラーが発生することを確認。"""
        from factor.errors import InsufficientDataError

        orthogonalizer = Orthogonalizer(min_samples=50)

        control = pd.Series(np.random.randn(30), name="control")
        factor = pd.Series(np.random.randn(30), name="factor")

        with pytest.raises(InsufficientDataError):
            orthogonalizer.orthogonalize(factor, control)

    def test_回帰_定数コントロールでの動作(self) -> None:
        """コントロール変数が定数の場合のエラーハンドリングを確認。"""
        orthogonalizer = Orthogonalizer(min_samples=20)

        # Constant control (no variance)
        # Note: statsmodels OLS with constant control may not raise an error
        # because add_constant adds an intercept. The constant column becomes
        # redundant with the intercept, which OLS handles gracefully.
        control = pd.Series([1.0] * 50, name="control")
        factor = pd.Series(np.random.randn(50), name="factor")

        # The result should have R-squared close to 0 since
        # a constant cannot explain variance
        result = orthogonalizer.orthogonalize(factor, control)
        assert result.r_squared < 0.01

    def test_回帰_cascade_存在しないファクターでエラー(self) -> None:
        """存在しないファクター名を order に含む場合のエラーを確認。"""
        orthogonalizer = Orthogonalizer(min_samples=20)

        factors = {
            "f1": pd.Series(np.random.randn(50), name="f1"),
            "f2": pd.Series(np.random.randn(50), name="f2"),
        }

        with pytest.raises(ValueError, match="Factors not found"):
            orthogonalizer.orthogonalize_cascade(factors, order=["f1", "f2", "f3"])
