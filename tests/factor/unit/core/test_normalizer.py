"""Unit tests for Normalizer class."""

import pandas as pd
import pytest
from factor.core.normalizer import Normalizer
from factor.errors import ValidationError


class TestNormalizerInit:
    """Tests for Normalizer initialization."""

    def test_default_min_samples(self) -> None:
        """Default min_samples is 5."""
        normalizer = Normalizer()
        assert normalizer.min_samples == 5

    def test_custom_min_samples(self) -> None:
        """Custom min_samples is stored."""
        normalizer = Normalizer(min_samples=10)
        assert normalizer.min_samples == 10

    def test_invalid_min_samples_raises_error(self) -> None:
        """Non-positive min_samples raises ValidationError."""
        with pytest.raises(ValidationError):
            Normalizer(min_samples=0)

        with pytest.raises(ValidationError):
            Normalizer(min_samples=-5)


class TestZscore:
    """Tests for zscore method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.normalizer = Normalizer(min_samples=3)
        self.sample_data = pd.Series(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        )

    def test_standard_zscore_mean_zero(self) -> None:
        """Standard zscore should have approximately zero mean."""
        result = self.normalizer.zscore(self.sample_data, robust=False)
        assert abs(result.mean()) < 1e-10

    def test_standard_zscore_std_one(self) -> None:
        """Standard zscore should have approximately unit std."""
        result = self.normalizer.zscore(self.sample_data, robust=False)
        # Using ddof=0 gives std of 1.0
        assert abs(result.std(ddof=0) - 1.0) < 0.1

    def test_robust_zscore_median_zero(self) -> None:
        """Robust zscore should have zero median."""
        result = self.normalizer.zscore(self.sample_data, robust=True)
        assert abs(result.median()) < 1e-10

    def test_zscore_preserves_index(self) -> None:
        """Zscore should preserve the original index."""
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=["a", "b", "c", "d", "e"])
        result = self.normalizer.zscore(data)
        assert list(result.index) == ["a", "b", "c", "d", "e"]

    def test_zscore_insufficient_data(self) -> None:
        """Zscore returns NaN when data is insufficient."""
        normalizer = Normalizer(min_samples=10)
        data = pd.Series([1.0, 2.0, 3.0])
        result = normalizer.zscore(data)
        assert bool(result.isna().all())

    def test_zscore_dataframe(self) -> None:
        """Zscore works with DataFrame input."""
        df = pd.DataFrame(
            {"A": [1.0, 2.0, 3.0, 4.0, 5.0], "B": [10.0, 20.0, 30.0, 40.0, 50.0]}
        )
        result = self.normalizer.zscore(df)
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["A", "B"]


class TestPercentileRank:
    """Tests for percentile_rank method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.normalizer = Normalizer(min_samples=3)

    def test_percentile_rank_range(self) -> None:
        """Percentile ranks should be in range (0, 1]."""
        data = pd.Series([10.0, 30.0, 20.0, 40.0, 50.0])
        result = self.normalizer.percentile_rank(data)
        assert result.min() > 0
        assert result.max() <= 1.0

    def test_percentile_rank_ordering(self) -> None:
        """Percentile rank should preserve ordering."""
        data = pd.Series([10.0, 30.0, 20.0, 40.0, 50.0])
        result = self.normalizer.percentile_rank(data)
        # Index 0 (value 10) should have lowest rank
        # Index 4 (value 50) should have highest rank
        assert result.iloc[0] < result.iloc[4]

    def test_percentile_rank_highest_is_one(self) -> None:
        """Highest value should have percentile rank 1.0."""
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = self.normalizer.percentile_rank(data)
        assert result.iloc[4] == 1.0


class TestQuintileRank:
    """Tests for quintile_rank method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.normalizer = Normalizer(min_samples=3)

    def test_quintile_rank_values(self) -> None:
        """Quintile ranks should be 1-5."""
        data = pd.Series(range(1, 21))  # 20 values
        result = self.normalizer.quintile_rank(data)
        unique_values = set(result.dropna().unique())
        assert unique_values.issubset({1, 2, 3, 4, 5})

    def test_quintile_rank_custom_labels(self) -> None:
        """Custom labels should be applied correctly."""
        data = pd.Series(range(1, 21))
        labels = ["Very Low", "Low", "Medium", "High", "Very High"]
        result = self.normalizer.quintile_rank(data, labels=labels)
        unique_values = set(result.dropna().unique())
        assert unique_values.issubset(set(labels))

    def test_quintile_rank_invalid_labels_raises_error(self) -> None:
        """Invalid labels count raises ValidationError."""
        data = pd.Series(range(1, 21))
        with pytest.raises(ValidationError):
            self.normalizer.quintile_rank(data, labels=["A", "B", "C"])  # Only 3 labels


class TestWinsorize:
    """Tests for winsorize method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.normalizer = Normalizer()

    def test_winsorize_clips_outliers(self) -> None:
        """Winsorize should clip extreme values."""
        # Data with outliers
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 100.0])
        result = self.normalizer.winsorize(data, limits=(0.1, 0.1))
        # Max should be clipped
        assert result.max() < 100.0

    def test_winsorize_preserves_middle_values(self) -> None:
        """Winsorize should not affect middle values."""
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = self.normalizer.winsorize(data, limits=(0.1, 0.1))
        # Middle value should be unchanged
        assert result.iloc[2] == 3.0

    def test_winsorize_invalid_limits_raises_error(self) -> None:
        """Invalid limits raise ValidationError."""
        data = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValidationError):
            self.normalizer.winsorize(data, limits=(0.6, 0.1))  # > 0.5


class TestNormalizeByGroup:
    """Tests for normalize_by_group method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.normalizer = Normalizer(min_samples=2)
        self.df = pd.DataFrame(
            {
                "date": ["2024-01-01"] * 6,
                "sector": ["Tech", "Tech", "Tech", "Finance", "Finance", "Finance"],
                "value": [1.0, 2.0, 3.0, 10.0, 20.0, 30.0],
            }
        )

    def test_normalize_by_group_zscore(self) -> None:
        """Group normalization with zscore method."""
        result = self.normalizer.normalize_by_group(
            self.df,
            "value",
            ["date", "sector"],
            method="zscore",
        )
        assert "value_zscore" in result.columns

    def test_normalize_by_group_percentile_rank(self) -> None:
        """Group normalization with percentile_rank method."""
        result = self.normalizer.normalize_by_group(
            self.df,
            "value",
            ["date", "sector"],
            method="percentile_rank",
        )
        assert "value_percentile_rank" in result.columns

    def test_normalize_by_group_missing_column_raises_error(self) -> None:
        """Missing column raises ValidationError."""
        with pytest.raises(ValidationError):
            self.normalizer.normalize_by_group(
                self.df,
                "nonexistent",
                ["date", "sector"],
            )

    def test_normalize_by_group_invalid_method_raises_error(self) -> None:
        """Invalid method raises ValidationError."""
        with pytest.raises(ValidationError):
            self.normalizer.normalize_by_group(
                self.df,
                "value",
                ["date"],
                method="invalid_method",
            )
