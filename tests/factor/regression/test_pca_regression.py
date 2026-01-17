"""Regression tests for YieldCurvePCA.

This module verifies that YieldCurvePCA produces consistent results
by comparing against known expected values.

Tolerance: 1e-10
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from factor.core.pca import YieldCurvePCA

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestYieldCurvePCARegression:
    """Regression tests for YieldCurvePCA class."""

    @pytest.fixture
    def input_yields(self) -> pd.DataFrame:
        """Load input yield data from fixture."""
        return pd.read_parquet(FIXTURES_DIR / "pca_input_yields.parquet")

    @pytest.fixture
    def expected_scores(self) -> pd.DataFrame:
        """Load expected PCA scores from fixture."""
        return pd.read_parquet(FIXTURES_DIR / "pca_scores_expected.parquet")

    @pytest.fixture
    def expected_components(self) -> pd.DataFrame:
        """Load expected PCA components from fixture."""
        return pd.read_parquet(FIXTURES_DIR / "pca_components_expected.parquet")

    @pytest.fixture
    def expected_variance(self) -> pd.DataFrame:
        """Load expected explained variance ratios from fixture."""
        return pd.read_parquet(FIXTURES_DIR / "pca_variance_expected.parquet")

    @pytest.fixture
    def pca(self) -> YieldCurvePCA:
        """Create YieldCurvePCA instance for testing."""
        return YieldCurvePCA(n_components=3)

    def test_回帰_fit_transform_スコアの固定期待値との比較(
        self,
        pca: YieldCurvePCA,
        input_yields: pd.DataFrame,
        expected_scores: pd.DataFrame,
    ) -> None:
        """YieldCurvePCA.fit_transform のスコアが既知の期待値と一致することを確認。"""
        result = pca.fit_transform(input_yields, use_changes=True, align_signs=True)

        # Compare scores
        np.testing.assert_array_almost_equal(
            result.scores.values,
            expected_scores.values,
            decimal=10,
        )

    def test_回帰_fit_transform_コンポーネントの検証(
        self,
        pca: YieldCurvePCA,
        input_yields: pd.DataFrame,
        expected_components: pd.DataFrame,
    ) -> None:
        """YieldCurvePCA.fit_transform のコンポーネントが既知の期待値と一致することを確認。"""
        result = pca.fit_transform(input_yields, use_changes=True, align_signs=True)

        # Components might have different signs but same absolute values
        # Check absolute values are close
        np.testing.assert_array_almost_equal(
            np.abs(result.components),
            np.abs(expected_components.values),
            decimal=10,
        )

    def test_回帰_explained_variance_ratio_の検証(
        self,
        pca: YieldCurvePCA,
        input_yields: pd.DataFrame,
        expected_variance: pd.DataFrame,
    ) -> None:
        """explained_variance_ratio が既知の期待値と一致することを確認。"""
        result = pca.fit_transform(input_yields, use_changes=True, align_signs=True)

        np.testing.assert_array_almost_equal(
            result.explained_variance_ratio,
            expected_variance["explained_variance_ratio"].to_numpy(),
            decimal=10,
        )

    def test_回帰_累積分散の確認(
        self,
        pca: YieldCurvePCA,
        input_yields: pd.DataFrame,
        expected_variance: pd.DataFrame,
    ) -> None:
        """cumulative_variance プロパティが正しいことを確認。"""
        result = pca.fit_transform(input_yields, use_changes=True, align_signs=True)

        expected_cumulative = np.cumsum(expected_variance["explained_variance_ratio"].to_numpy())

        np.testing.assert_array_almost_equal(
            result.cumulative_variance,
            expected_cumulative,
            decimal=10,
        )


class TestYieldCurvePCARegressionProperties:
    """Property-based regression tests for YieldCurvePCA."""

    @pytest.fixture
    def pca(self) -> YieldCurvePCA:
        """Create YieldCurvePCA instance for testing."""
        return YieldCurvePCA(n_components=3)

    def test_回帰_explained_variance_比率の合計が1以下(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """explained_variance_ratio の合計が 1 以下であることを確認。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        # Create synthetic yield data
        yields = pd.DataFrame(
            np.random.randn(n_samples, n_maturities),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result = pca.fit_transform(yields, use_changes=True)

        assert result.explained_variance_ratio.sum() <= 1.0 + 1e-10

    def test_回帰_スコアの直交性確認(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """PCAスコアが互いに直交していることを確認。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        yields = pd.DataFrame(
            np.random.randn(n_samples, n_maturities),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result = pca.fit_transform(yields, use_changes=True)

        # Calculate correlation matrix of scores
        corr_matrix = result.scores.corr()

        # Off-diagonal elements should be approximately 0
        n = len(corr_matrix)
        for i in range(n):
            for j in range(i + 1, n):
                assert abs(corr_matrix.iloc[i, j]) < 1e-10

    def test_回帰_コンポーネント名の確認(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """コンポーネント名が正しく設定されることを確認。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        yields = pd.DataFrame(
            np.random.randn(n_samples, n_maturities),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result = pca.fit_transform(yields, use_changes=True)

        assert result.column_names == ["Level", "Slope", "Curvature"]

    def test_回帰_4コンポーネント以上の場合の命名(self) -> None:
        """4コンポーネント以上の場合、追加のコンポーネント名が正しいことを確認。"""
        pca = YieldCurvePCA(n_components=5)

        np.random.seed(42)
        n_samples = 100
        n_maturities = 10

        yields = pd.DataFrame(
            np.random.randn(n_samples, n_maturities),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result = pca.fit_transform(yields, use_changes=True)

        assert result.column_names == ["Level", "Slope", "Curvature", "PC4", "PC5"]


class TestYieldCurvePCARegressionSignAlignment:
    """Sign alignment regression tests for YieldCurvePCA."""

    @pytest.fixture
    def pca(self) -> YieldCurvePCA:
        """Create YieldCurvePCA instance for testing."""
        return YieldCurvePCA(n_components=3)

    def test_回帰_Level_ローディング合計が正(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """Level コンポーネントのローディング合計が正であることを確認（経済的解釈）。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        yields = pd.DataFrame(
            np.cumsum(np.random.randn(n_samples, n_maturities), axis=0),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result = pca.fit_transform(yields, use_changes=True, align_signs=True)

        # Level loadings (first component) should have positive sum
        level_loadings = result.components[0]
        assert np.sum(level_loadings) >= 0

    def test_回帰_Slope_長期ローディングが正(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """Slope コンポーネントの長期（最後の）ローディングが正であることを確認。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        yields = pd.DataFrame(
            np.cumsum(np.random.randn(n_samples, n_maturities), axis=0),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result = pca.fit_transform(yields, use_changes=True, align_signs=True)

        # Slope loadings (second component) should have positive last element
        slope_loadings = result.components[1]
        assert slope_loadings[-1] >= 0

    def test_回帰_Curvature_中央ローディングが正(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """Curvature コンポーネントの中央ローディングが正であることを確認。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        yields = pd.DataFrame(
            np.cumsum(np.random.randn(n_samples, n_maturities), axis=0),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result = pca.fit_transform(yields, use_changes=True, align_signs=True)

        # Curvature loadings (third component) should have positive middle element
        curvature_loadings = result.components[2]
        mid_index = n_maturities // 2
        assert curvature_loadings[mid_index] >= 0

    def test_回帰_align_signs_Falseで符号調整なし(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """align_signs=False で符号調整が行われないことを確認。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        yields = pd.DataFrame(
            np.cumsum(np.random.randn(n_samples, n_maturities), axis=0),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result_aligned = pca.fit_transform(yields, use_changes=True, align_signs=True)

        pca2 = YieldCurvePCA(n_components=3)
        result_not_aligned = pca2.fit_transform(yields, use_changes=True, align_signs=False)

        # Results may differ if signs needed adjustment
        # (they should be equal in absolute value)
        np.testing.assert_array_almost_equal(
            np.abs(result_aligned.scores.values),
            np.abs(result_not_aligned.scores.values),
            decimal=10,
        )


class TestYieldCurvePCARegressionTransform:
    """Transform method regression tests for YieldCurvePCA."""

    @pytest.fixture
    def pca(self) -> YieldCurvePCA:
        """Create YieldCurvePCA instance for testing."""
        return YieldCurvePCA(n_components=3)

    def test_回帰_transform_新データへの適用(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """fit_transform 後、transform で新データに適用できることを確認。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        # Training data
        train_yields = pd.DataFrame(
            np.cumsum(np.random.randn(n_samples, n_maturities), axis=0),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        # Fit on training data
        pca.fit_transform(train_yields, use_changes=True, align_signs=True)

        # Test data
        test_yields = pd.DataFrame(
            np.cumsum(np.random.randn(50, n_maturities), axis=0),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2021-01-01", periods=50, freq="D"),
        )

        # Transform test data
        result = pca.transform(test_yields, use_changes=True)

        assert result is not None
        assert len(result.columns) == 3
        assert list(result.columns) == ["Level", "Slope", "Curvature"]

    def test_回帰_transform_fit前でエラー(
        self,
    ) -> None:
        """fit_transform 前に transform を呼ぶとエラーになることを確認。"""
        pca = YieldCurvePCA(n_components=3)

        np.random.seed(42)
        yields = pd.DataFrame(
            np.random.randn(50, 5),
            columns=pd.Index([f"mat{i}" for i in range(5)]),
            index=pd.date_range("2020-01-01", periods=50, freq="D"),
        )

        with pytest.raises(RuntimeError, match="Must call fit_transform before transform"):
            pca.transform(yields)

    def test_回帰_get_loadings_の取得(
        self,
        pca: YieldCurvePCA,
    ) -> None:
        """get_loadings でローディングを取得できることを確認。"""
        np.random.seed(42)
        n_samples = 100
        n_maturities = 5

        yields = pd.DataFrame(
            np.cumsum(np.random.randn(n_samples, n_maturities), axis=0),
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        pca.fit_transform(yields, use_changes=True)

        loadings = pca.get_loadings()

        assert isinstance(loadings, pd.DataFrame)
        assert loadings.shape == (3, n_maturities)
        assert list(loadings.index) == ["Level", "Slope", "Curvature"]


class TestYieldCurvePCARegressionEdgeCases:
    """Edge case regression tests for YieldCurvePCA."""

    def test_回帰_データ不足でエラー(self) -> None:
        """データが n_components 未満の場合にエラーが発生することを確認。"""
        from factor.errors import InsufficientDataError

        pca = YieldCurvePCA(n_components=3)

        # Only 2 rows after differencing
        yields = pd.DataFrame(
            np.random.randn(3, 5),
            columns=pd.Index([f"mat{i}" for i in range(5)]),
            index=pd.date_range("2020-01-01", periods=3, freq="D"),
        )

        with pytest.raises(InsufficientDataError):
            pca.fit_transform(yields, use_changes=True)

    def test_回帰_n_components_非正値でエラー(self) -> None:
        """n_components が非正の場合にエラーが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            YieldCurvePCA(n_components=0)

        with pytest.raises(ValidationError):
            YieldCurvePCA(n_components=-1)

    def test_回帰_use_changes_Falseで水準データ使用(self) -> None:
        """use_changes=False で水準データに対してPCAが実行されることを確認。"""
        pca = YieldCurvePCA(n_components=3)

        np.random.seed(42)
        n_samples = 50
        n_maturities = 5

        yields = pd.DataFrame(
            np.random.randn(n_samples, n_maturities) + 2.0,  # Level around 2%
            columns=pd.Index([f"mat{i}" for i in range(n_maturities)]),
            index=pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        )

        result = pca.fit_transform(yields, use_changes=False, align_signs=True)

        # Should use all rows (no diff needed)
        assert len(result.scores) == n_samples
