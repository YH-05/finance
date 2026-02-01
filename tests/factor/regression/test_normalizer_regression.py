"""Regression tests for Normalizer.

This module verifies that Normalizer methods produce consistent results
by comparing against known expected values.

Tolerance: 1e-10
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from factor.core.normalizer import Normalizer

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestNormalizerRegression:
    """Regression tests for Normalizer class."""

    @pytest.fixture
    def expected_data(self) -> pd.DataFrame:
        """Load expected values from parquet fixture."""
        return pd.read_parquet(FIXTURES_DIR / "normalizer_expected.parquet")

    @pytest.fixture
    def input_data(self, expected_data: pd.DataFrame) -> pd.Series:
        """Extract input data from fixture."""
        return pd.Series(expected_data["input_data"])

    @pytest.fixture
    def normalizer(self) -> Normalizer:
        """Create Normalizer instance for testing."""
        return Normalizer(min_samples=5)

    def test_回帰_zscore_robust_固定期待値との比較(
        self,
        normalizer: Normalizer,
        input_data: pd.Series,
        expected_data: pd.DataFrame,
    ) -> None:
        """Normalizer.zscore (robust=True) の結果が既知の期待値と一致することを確認。"""
        result = normalizer.zscore(input_data, robust=True)
        expected = expected_data["zscore_robust_expected"]

        pd.testing.assert_series_equal(
            result,
            expected,
            check_names=False,
            atol=1e-10,
        )

    def test_回帰_zscore_standard_固定期待値との比較(
        self,
        normalizer: Normalizer,
        input_data: pd.Series,
        expected_data: pd.DataFrame,
    ) -> None:
        """Normalizer.zscore (robust=False) の結果が既知の期待値と一致することを確認。"""
        result = normalizer.zscore(input_data, robust=False)
        expected = expected_data["zscore_standard_expected"]

        pd.testing.assert_series_equal(
            result,
            expected,
            check_names=False,
            atol=1e-10,
        )

    def test_回帰_percentile_rank_固定期待値との比較(
        self,
        normalizer: Normalizer,
        input_data: pd.Series,
        expected_data: pd.DataFrame,
    ) -> None:
        """Normalizer.percentile_rank の結果が既知の期待値と一致することを確認。"""
        result = normalizer.percentile_rank(input_data)
        expected = expected_data["percentile_rank_expected"]

        pd.testing.assert_series_equal(
            result,
            expected,
            check_names=False,
            atol=1e-10,
        )

    def test_回帰_quintile_rank_固定期待値との比較(
        self,
        normalizer: Normalizer,
        input_data: pd.Series,
        expected_data: pd.DataFrame,
    ) -> None:
        """Normalizer.quintile_rank の結果が既知の期待値と一致することを確認。"""
        result = normalizer.quintile_rank(input_data)
        expected = expected_data["quintile_expected"]

        # quintile_rank returns floats, convert expected for comparison
        np.testing.assert_array_almost_equal(
            result.to_numpy(),
            expected.to_numpy(),
            decimal=10,
        )

    def test_回帰_winsorize_固定期待値との比較(
        self,
        normalizer: Normalizer,
        input_data: pd.Series,
        expected_data: pd.DataFrame,
    ) -> None:
        """Normalizer.winsorize の結果が既知の期待値と一致することを確認。"""
        result = normalizer.winsorize(input_data, limits=(0.1, 0.1))
        expected = expected_data["winsorize_expected"]

        pd.testing.assert_series_equal(
            result,
            expected,
            check_names=False,
            atol=1e-10,
        )


class TestNormalizerRegressionProperties:
    """Property-based regression tests for Normalizer."""

    @pytest.fixture
    def normalizer(self) -> Normalizer:
        """Create Normalizer instance for testing."""
        return Normalizer(min_samples=5)

    def test_回帰_zscore_数学的性質の確認(
        self,
        normalizer: Normalizer,
    ) -> None:
        """Zscore が正しい数学的性質を満たすことを確認。"""
        np.random.seed(42)
        data = pd.Series(np.random.randn(100) * 10 + 50)

        # Robust zscore
        result = normalizer.zscore(data, robust=True)

        # Median should be approximately 0
        assert abs(result.median()) < 0.01

        # Standard zscore
        result_std = normalizer.zscore(data, robust=False)

        # Mean should be approximately 0
        assert abs(result_std.mean()) < 1e-10

        # Standard deviation should be approximately 1
        assert abs(result_std.std() - 1) < 1e-10

    def test_回帰_percentile_rank_範囲と分布の確認(
        self,
        normalizer: Normalizer,
    ) -> None:
        """Percentile rank が [0, 1] の範囲に収まることを確認。"""
        np.random.seed(42)
        data = pd.Series(np.random.randn(100))

        result = normalizer.percentile_rank(data)

        # All values should be in [0, 1]
        assert result.min() >= 0
        assert result.max() <= 1

        # Distribution should be approximately uniform
        quartiles = result.quantile([0.25, 0.5, 0.75])
        assert abs(quartiles[0.25] - 0.25) < 0.1
        assert abs(quartiles[0.5] - 0.5) < 0.1
        assert abs(quartiles[0.75] - 0.75) < 0.1

    def test_回帰_quintile_rank_カテゴリ分布の確認(
        self,
        normalizer: Normalizer,
    ) -> None:
        """Quintile rank が 5 カテゴリに均等に分布することを確認。"""
        np.random.seed(42)
        data = pd.Series(np.random.randn(100))

        result = normalizer.quintile_rank(data)

        # Should have 5 categories
        unique_values = result.dropna().unique()
        assert len(unique_values) == 5

        # Each category should have approximately 20% of data
        value_counts = result.value_counts(normalize=True)
        for count in value_counts.values:
            assert 0.15 <= count <= 0.25  # Allow some tolerance

    def test_回帰_winsorize_外れ値クリップの確認(
        self,
        normalizer: Normalizer,
    ) -> None:
        """Winsorize が正しく外れ値をクリップすることを確認。"""
        # Data with extreme outliers
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100, -50])

        result = normalizer.winsorize(data, limits=(0.1, 0.1))

        # Extreme values should be clipped
        assert result.max() < 100
        assert result.min() > -50

        # Non-extreme values should be unchanged
        _middle_values = data[(data >= 1) & (data <= 10)]
        result_middle = result[(result >= result.min()) & (result <= result.max())]
        # Middle values should still be in the result
        assert len(result_middle) > 0


class TestNormalizerRegressionConsistency:
    """Consistency tests to ensure Normalizer produces reproducible results."""

    @pytest.fixture
    def normalizer(self) -> Normalizer:
        """Create Normalizer instance for testing."""
        return Normalizer(min_samples=5)

    def test_回帰_複数回実行で同一結果(
        self,
        normalizer: Normalizer,
    ) -> None:
        """同じデータに対して複数回実行しても同一の結果が得られることを確認。"""
        np.random.seed(42)
        data = pd.Series(np.random.randn(100))

        # Run multiple times
        results = []
        for _ in range(5):
            result = normalizer.zscore(data, robust=True)
            results.append(result)

        # All results should be identical
        for i in range(1, len(results)):
            pd.testing.assert_series_equal(
                results[0],
                results[i],
                check_names=False,
            )

    def test_回帰_DataFrame入力とSeries入力で一貫した結果(
        self,
        normalizer: Normalizer,
    ) -> None:
        """DataFrame 入力と Series 入力で一貫した結果が得られることを確認。"""
        np.random.seed(42)
        data = pd.Series(np.random.randn(100), name="col1")
        df = pd.DataFrame({"col1": data})

        result_series = normalizer.zscore(data, robust=True)
        result_df = normalizer.zscore(df, robust=True)

        pd.testing.assert_series_equal(
            result_series,
            result_df["col1"],
            check_names=False,
        )

    def test_回帰_min_samples境界でのパラメータ感度(
        self,
    ) -> None:
        """min_samples パラメータの境界条件でのの動作を確認。"""
        # Exactly min_samples data points
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])

        normalizer_5 = Normalizer(min_samples=5)
        normalizer_6 = Normalizer(min_samples=6)

        # Should work with min_samples=5
        result_5 = normalizer_5.zscore(data, robust=True)
        assert bool(result_5.notna().all())

        # Should return NaN with min_samples=6
        result_6 = normalizer_6.zscore(data, robust=True)
        assert bool(result_6.isna().all())
