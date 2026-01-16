"""Unit tests for YieldCurvePCA class."""

import numpy as np
import pandas as pd
import pytest

from factor.core.pca import PCAResult, YieldCurvePCA
from factor.errors import InsufficientDataError, ValidationError


class TestYieldCurvePCAInit:
    """Tests for YieldCurvePCA initialization."""

    def test_default_n_components(self) -> None:
        """Default n_components is 3."""
        pca = YieldCurvePCA()
        assert pca.n_components == 3

    def test_custom_n_components(self) -> None:
        """Custom n_components is stored."""
        pca = YieldCurvePCA(n_components=5)
        assert pca.n_components == 5

    def test_invalid_n_components_raises_error(self) -> None:
        """Non-positive n_components raises ValidationError."""
        with pytest.raises(ValidationError):
            YieldCurvePCA(n_components=0)

        with pytest.raises(ValidationError):
            YieldCurvePCA(n_components=-1)


class TestFitTransform:
    """Tests for fit_transform method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.pca = YieldCurvePCA(n_components=3)

        # Create synthetic yield curve data
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", periods=500, freq="B")

        # Level, slope, and curvature factors
        level = np.cumsum(np.random.randn(500) * 0.05)
        slope = np.cumsum(np.random.randn(500) * 0.03)
        curvature = np.cumsum(np.random.randn(500) * 0.02)

        # Create yield curves with typical loadings
        maturities = ["3M", "6M", "1Y", "2Y", "5Y", "10Y", "30Y"]
        loadings_level = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        loadings_slope = [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7]
        loadings_curve = [0.2, 0.3, 0.4, 0.3, 0.0, -0.2, -0.3]

        yields = {}
        for i, mat in enumerate(maturities):
            yields[mat] = (
                2.0  # Base rate
                + loadings_level[i] * level
                + loadings_slope[i] * slope
                + loadings_curve[i] * curvature
                + np.random.randn(500) * 0.01  # Noise
            )

        self.yield_data = pd.DataFrame(yields, index=dates)

    def test_fit_transform_returns_pca_result(self) -> None:
        """fit_transform returns PCAResult."""
        result = self.pca.fit_transform(self.yield_data)
        assert isinstance(result, PCAResult)

    def test_scores_shape(self) -> None:
        """Scores have correct shape."""
        result = self.pca.fit_transform(self.yield_data)
        # Using changes, so one less row than original
        assert result.scores.shape[1] == 3

    def test_scores_column_names(self) -> None:
        """Scores have economic names."""
        result = self.pca.fit_transform(self.yield_data)
        assert list(result.scores.columns) == ["Level", "Slope", "Curvature"]

    def test_explained_variance(self) -> None:
        """Explained variance ratios sum to reasonable amount."""
        result = self.pca.fit_transform(self.yield_data)
        # First 3 PCs should explain most variance
        assert result.total_variance_explained > 0.9

    def test_cumulative_variance(self) -> None:
        """Cumulative variance is correctly computed."""
        result = self.pca.fit_transform(self.yield_data)
        expected = np.cumsum(result.explained_variance_ratio)
        np.testing.assert_array_almost_equal(result.cumulative_variance, expected)

    def test_fit_transform_on_levels(self) -> None:
        """fit_transform works on levels (not changes)."""
        result = self.pca.fit_transform(self.yield_data, use_changes=False)
        # No diff, so same number of rows (minus NaN handling)
        assert len(result.scores) == len(self.yield_data.dropna())

    def test_fit_transform_without_sign_alignment(self) -> None:
        """fit_transform works without sign alignment."""
        result = self.pca.fit_transform(self.yield_data, align_signs=False)
        assert result.scores is not None

    def test_insufficient_data_raises_error(self) -> None:
        """Insufficient data raises InsufficientDataError."""
        small_data = self.yield_data.iloc[:2]  # Only 2 rows
        with pytest.raises(InsufficientDataError):
            self.pca.fit_transform(small_data)


class TestAlignSigns:
    """Tests for align_signs method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.pca = YieldCurvePCA(n_components=3)

    def test_level_sign_all_positive_sum(self) -> None:
        """PC1 (Level) loadings should sum to positive."""
        # Create components where level sums to negative
        components = np.array(
            [
                [-0.3, -0.3, -0.4],  # Level (all negative)
                [-0.5, 0.0, 0.5],  # Slope
                [0.3, -0.5, 0.3],  # Curvature
            ]
        )
        scores = np.random.randn(100, 3)

        _ = self.pca.align_signs(components, scores)

        # After alignment, level loadings should sum positive
        assert np.sum(components[0]) > 0

    def test_slope_sign_long_end_positive(self) -> None:
        """PC2 (Slope) should have positive loading at long end."""
        # Create components where slope has negative at long end
        components = np.array(
            [
                [0.3, 0.3, 0.4],  # Level (positive)
                [0.5, 0.0, -0.5],  # Slope (negative at long end)
                [0.3, -0.5, 0.3],  # Curvature
            ]
        )
        scores = np.random.randn(100, 3)

        _ = self.pca.align_signs(components, scores)

        # After alignment, slope should have positive at long end
        assert components[1, -1] > 0

    def test_curvature_sign_middle_positive(self) -> None:
        """PC3 (Curvature) should have positive loading in middle."""
        # Create components where curvature has negative in middle
        components = np.array(
            [
                [0.3, 0.3, 0.4],  # Level
                [-0.5, 0.0, 0.5],  # Slope
                [-0.3, -0.5, -0.3],  # Curvature (negative in middle)
            ]
        )
        scores = np.random.randn(100, 3)

        _ = self.pca.align_signs(components, scores)

        # After alignment, curvature should have positive in middle
        mid_idx = len(components[2]) // 2
        assert components[2, mid_idx] > 0


class TestTransform:
    """Tests for transform method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.pca = YieldCurvePCA(n_components=3)
        np.random.seed(42)

        dates = pd.date_range("2020-01-01", periods=100, freq="B")
        self.yield_data = pd.DataFrame(
            {
                "3M": np.random.randn(100).cumsum() + 2,
                "1Y": np.random.randn(100).cumsum() + 2.5,
                "10Y": np.random.randn(100).cumsum() + 3,
            },
            index=dates,
        )

    def test_transform_before_fit_raises_error(self) -> None:
        """transform before fit_transform raises RuntimeError."""
        with pytest.raises(RuntimeError):
            self.pca.transform(self.yield_data)

    def test_transform_after_fit(self) -> None:
        """transform works after fit_transform."""
        self.pca.fit_transform(self.yield_data)
        new_data = self.yield_data.copy()
        result = self.pca.transform(new_data)
        assert isinstance(result, pd.DataFrame)


class TestGetLoadings:
    """Tests for get_loadings method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.pca = YieldCurvePCA(n_components=3)
        np.random.seed(42)

        dates = pd.date_range("2020-01-01", periods=100, freq="B")
        self.yield_data = pd.DataFrame(
            {
                "3M": np.random.randn(100).cumsum() + 2,
                "1Y": np.random.randn(100).cumsum() + 2.5,
                "10Y": np.random.randn(100).cumsum() + 3,
            },
            index=dates,
        )

    def test_get_loadings_before_fit_raises_error(self) -> None:
        """get_loadings before fit_transform raises RuntimeError."""
        with pytest.raises(RuntimeError):
            self.pca.get_loadings()

    def test_get_loadings_shape(self) -> None:
        """Loadings have correct shape (components x features)."""
        self.pca.fit_transform(self.yield_data)
        loadings = self.pca.get_loadings()

        assert loadings.shape == (3, 3)  # 3 components, 3 features

    def test_get_loadings_index(self) -> None:
        """Loadings have economic component names as index."""
        self.pca.fit_transform(self.yield_data)
        loadings = self.pca.get_loadings()

        assert list(loadings.index) == ["Level", "Slope", "Curvature"]


class TestComponentNames:
    """Tests for component naming."""

    def test_3_components_economic_names(self) -> None:
        """3 components use Level, Slope, Curvature."""
        pca = YieldCurvePCA(n_components=3)
        names = pca._get_component_names()
        assert names == ["Level", "Slope", "Curvature"]

    def test_2_components(self) -> None:
        """2 components use Level, Slope."""
        pca = YieldCurvePCA(n_components=2)
        names = pca._get_component_names()
        assert names == ["Level", "Slope"]

    def test_5_components(self) -> None:
        """5 components use economic names + PC4, PC5."""
        pca = YieldCurvePCA(n_components=5)
        names = pca._get_component_names()
        assert names == ["Level", "Slope", "Curvature", "PC4", "PC5"]
