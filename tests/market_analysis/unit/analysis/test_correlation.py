"""Unit tests for CorrelationAnalyzer class."""

import numpy as np
import pandas as pd
import pytest

from market_analysis.analysis.correlation import CorrelationAnalyzer
from market_analysis.types import CorrelationResult


class TestCalculateCorrelation:
    """Tests for pairwise correlation calculation."""

    def test_perfect_positive_correlation(self) -> None:
        """Test perfect positive correlation (r=1.0)."""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])

        corr = CorrelationAnalyzer.calculate_correlation(a, b)
        assert corr == pytest.approx(1.0)

    def test_perfect_negative_correlation(self) -> None:
        """Test perfect negative correlation (r=-1.0)."""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([10.0, 8.0, 6.0, 4.0, 2.0])

        corr = CorrelationAnalyzer.calculate_correlation(a, b)
        assert corr == pytest.approx(-1.0)

    def test_zero_correlation(self) -> None:
        """Test zero correlation between uncorrelated series."""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([3.0, 3.0, 3.0, 3.0, 3.0])

        corr = CorrelationAnalyzer.calculate_correlation(a, b)
        # Constant series has zero variance, correlation is NaN
        assert np.isnan(corr)

    def test_correlation_in_range(self) -> None:
        """Test that correlation is within [-1, 1] range."""
        a = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0])
        b = pd.Series([2.0, 4.0, 1.0, 6.0, 3.0])

        corr = CorrelationAnalyzer.calculate_correlation(a, b)
        assert -1.0 <= corr <= 1.0

    def test_spearman_correlation(self) -> None:
        """Test Spearman rank correlation."""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([1.0, 4.0, 9.0, 16.0, 25.0])

        corr = CorrelationAnalyzer.calculate_correlation(a, b, method="spearman")
        # Monotonically increasing, so Spearman should be 1.0
        assert corr == pytest.approx(1.0)

    def test_kendall_correlation(self) -> None:
        """Test Kendall tau correlation."""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])

        corr = CorrelationAnalyzer.calculate_correlation(a, b, method="kendall")
        assert corr == pytest.approx(1.0)

    def test_series_length_mismatch(self) -> None:
        """Test that mismatched series lengths raise ValueError."""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0])

        with pytest.raises(ValueError, match="must have equal length"):
            CorrelationAnalyzer.calculate_correlation(a, b)

    def test_invalid_method(self) -> None:
        """Test that invalid correlation method raises ValueError."""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Invalid method"):
            CorrelationAnalyzer.calculate_correlation(a, b, method="invalid")  # type: ignore[arg-type]

    def test_empty_series(self) -> None:
        """Test correlation with empty series returns NaN."""
        a = pd.Series(dtype=np.float64)
        b = pd.Series(dtype=np.float64)

        corr = CorrelationAnalyzer.calculate_correlation(a, b)
        assert np.isnan(corr)

    def test_series_with_nan(self) -> None:
        """Test that NaN values are handled correctly."""
        a = pd.Series([1.0, np.nan, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, np.nan, 10.0])

        # Should calculate correlation using only non-NaN pairs
        corr = CorrelationAnalyzer.calculate_correlation(a, b)
        assert not np.isnan(corr)
        assert -1.0 <= corr <= 1.0


class TestCalculateCorrelationMatrix:
    """Tests for correlation matrix calculation."""

    def test_matrix_is_symmetric(self) -> None:
        """Test that correlation matrix is symmetric."""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0, 5.0],
                "B": [2.0, 4.0, 6.0, 8.0, 10.0],
                "C": [5.0, 4.0, 3.0, 2.0, 1.0],
            }
        )

        matrix = CorrelationAnalyzer.calculate_correlation_matrix(data)

        # Check symmetry
        assert matrix.loc["A", "B"] == pytest.approx(matrix.loc["B", "A"])
        assert matrix.loc["A", "C"] == pytest.approx(matrix.loc["C", "A"])
        assert matrix.loc["B", "C"] == pytest.approx(matrix.loc["C", "B"])

    def test_diagonal_is_one(self) -> None:
        """Test that diagonal elements are 1.0."""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0],
                "B": [2.0, 3.0, 4.0, 5.0],
                "C": [4.0, 3.0, 2.0, 1.0],
            }
        )

        matrix = CorrelationAnalyzer.calculate_correlation_matrix(data)

        assert matrix.loc["A", "A"] == pytest.approx(1.0)
        assert matrix.loc["B", "B"] == pytest.approx(1.0)
        assert matrix.loc["C", "C"] == pytest.approx(1.0)

    def test_values_in_range(self) -> None:
        """Test that all values are in [-1, 1] range."""
        data = pd.DataFrame(
            {
                "A": [1.0, 3.0, 2.0, 5.0],
                "B": [2.0, 4.0, 1.0, 6.0],
                "C": [3.0, 1.0, 4.0, 2.0],
            }
        )

        matrix = CorrelationAnalyzer.calculate_correlation_matrix(data)

        for col in matrix.columns:
            for row in matrix.index:
                assert -1.0 <= matrix.loc[row, col] <= 1.0

    def test_matrix_shape(self) -> None:
        """Test that matrix has correct shape."""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0],
                "B": [2.0, 3.0, 4.0],
                "C": [3.0, 4.0, 5.0],
                "D": [4.0, 5.0, 6.0],
            }
        )

        matrix = CorrelationAnalyzer.calculate_correlation_matrix(data)

        assert matrix.shape == (4, 4)
        assert list(matrix.columns) == ["A", "B", "C", "D"]
        assert list(matrix.index) == ["A", "B", "C", "D"]

    def test_insufficient_columns(self) -> None:
        """Test that single column raises ValueError."""
        data = pd.DataFrame({"A": [1.0, 2.0, 3.0]})

        with pytest.raises(ValueError, match="at least 2 columns"):
            CorrelationAnalyzer.calculate_correlation_matrix(data)

    def test_spearman_matrix(self) -> None:
        """Test Spearman correlation matrix."""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0, 5.0],
                "B": [1.0, 4.0, 9.0, 16.0, 25.0],  # Monotonic with A
            }
        )

        matrix = CorrelationAnalyzer.calculate_correlation_matrix(
            data, method="spearman"
        )

        # Spearman should be 1.0 for monotonically related series
        assert matrix.loc["A", "B"] == pytest.approx(1.0)


class TestCalculateRollingCorrelation:
    """Tests for rolling correlation calculation."""

    def test_rolling_correlation_basic(self) -> None:
        """Test basic rolling correlation calculation."""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0])

        rolling = CorrelationAnalyzer.calculate_rolling_correlation(a, b, window=5)

        # First 4 values should be NaN (window-1)
        assert pd.isna(rolling.iloc[0])
        assert pd.isna(rolling.iloc[1])
        assert pd.isna(rolling.iloc[2])
        assert pd.isna(rolling.iloc[3])

        # From index 4 onwards, should have valid correlation
        for i in range(4, 10):
            assert rolling.iloc[i] == pytest.approx(1.0)

    def test_rolling_correlation_nan_at_start(self) -> None:
        """Test that rolling correlation has NaN at start."""
        a = pd.Series(range(20), dtype=np.float64)
        b = pd.Series(range(20), dtype=np.float64)

        rolling = CorrelationAnalyzer.calculate_rolling_correlation(a, b, window=10)

        # First 9 values should be NaN
        assert rolling.iloc[:9].isna().all()
        # From index 9 onwards should be valid
        assert rolling.iloc[9:].notna().all()

    def test_rolling_correlation_length_mismatch(self) -> None:
        """Test that mismatched lengths raise ValueError."""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0])

        with pytest.raises(ValueError, match="must have equal length"):
            CorrelationAnalyzer.calculate_rolling_correlation(a, b, window=2)

    def test_rolling_correlation_invalid_window(self) -> None:
        """Test that invalid window raises ValueError."""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="Window must be at least 2"):
            CorrelationAnalyzer.calculate_rolling_correlation(a, b, window=1)

    def test_rolling_correlation_custom_min_periods(self) -> None:
        """Test rolling correlation with custom min_periods."""
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])

        rolling = CorrelationAnalyzer.calculate_rolling_correlation(
            a, b, window=5, min_periods=3
        )

        # With min_periods=3, valid from index 2
        assert pd.isna(rolling.iloc[0])
        assert pd.isna(rolling.iloc[1])
        assert pd.notna(rolling.iloc[2])

    def test_rolling_correlation_invalid_min_periods(self) -> None:
        """Test that invalid min_periods raises ValueError."""
        a = pd.Series([1.0, 2.0, 3.0])
        b = pd.Series([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="min_periods must be at least 2"):
            CorrelationAnalyzer.calculate_rolling_correlation(
                a, b, window=3, min_periods=1
            )


class TestCalculateBeta:
    """Tests for beta calculation."""

    def test_beta_perfect_correlation(self) -> None:
        """Test beta with perfect correlation (beta = 2.0)."""
        # Asset moves 2x the benchmark
        asset = pd.Series([0.02, 0.04, -0.02, 0.06, 0.02])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        beta = CorrelationAnalyzer.calculate_beta(asset, benchmark)
        assert beta == pytest.approx(2.0)

    def test_beta_equals_one(self) -> None:
        """Test beta = 1.0 when asset moves same as benchmark."""
        asset = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        beta = CorrelationAnalyzer.calculate_beta(asset, benchmark)
        assert beta == pytest.approx(1.0)

    def test_beta_less_than_one(self) -> None:
        """Test beta < 1 for less volatile asset."""
        # Asset moves 0.5x the benchmark
        asset = pd.Series([0.005, 0.01, -0.005, 0.015, 0.005])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        beta = CorrelationAnalyzer.calculate_beta(asset, benchmark)
        assert beta == pytest.approx(0.5)

    def test_negative_beta(self) -> None:
        """Test negative beta (inverse relationship)."""
        # Asset moves opposite to benchmark
        asset = pd.Series([-0.01, -0.02, 0.01, -0.03, -0.01])
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01])

        beta = CorrelationAnalyzer.calculate_beta(asset, benchmark)
        assert beta == pytest.approx(-1.0)

    def test_beta_series_length_mismatch(self) -> None:
        """Test that mismatched series lengths raise ValueError."""
        asset = pd.Series([0.01, 0.02])
        benchmark = pd.Series([0.01])

        with pytest.raises(ValueError, match="must have equal length"):
            CorrelationAnalyzer.calculate_beta(asset, benchmark)

    def test_beta_with_nan(self) -> None:
        """Test beta calculation with NaN values."""
        asset = pd.Series([0.01, np.nan, 0.03, 0.04, 0.05])
        benchmark = pd.Series([0.005, 0.01, np.nan, 0.02, 0.025])

        # Should calculate using only valid pairs
        beta = CorrelationAnalyzer.calculate_beta(asset, benchmark)
        assert not np.isnan(beta)

    def test_beta_zero_benchmark_variance(self) -> None:
        """Test beta returns NaN when benchmark has zero variance."""
        asset = pd.Series([0.01, 0.02, 0.03])
        benchmark = pd.Series([0.01, 0.01, 0.01])

        beta = CorrelationAnalyzer.calculate_beta(asset, benchmark)
        assert np.isnan(beta)


class TestCalculateRollingBeta:
    """Tests for rolling beta calculation."""

    def test_rolling_beta_basic(self) -> None:
        """Test basic rolling beta calculation."""
        # Asset moves 2x the benchmark
        asset = pd.Series([0.02, 0.04, -0.02, 0.06, 0.02] * 10)
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01] * 10)

        rolling = CorrelationAnalyzer.calculate_rolling_beta(
            asset, benchmark, window=20
        )

        # First 19 values should be NaN
        assert rolling.iloc[:19].isna().all()

        # Beta should be approximately 2.0
        valid_betas = rolling.dropna()
        for beta in valid_betas:
            assert beta == pytest.approx(2.0, rel=0.01)

    def test_rolling_beta_nan_at_start(self) -> None:
        """Test that rolling beta has NaN at start."""
        asset = pd.Series(np.random.randn(30))
        benchmark = pd.Series(np.random.randn(30))

        rolling = CorrelationAnalyzer.calculate_rolling_beta(
            asset, benchmark, window=10
        )

        assert rolling.iloc[:9].isna().all()

    def test_rolling_beta_invalid_window(self) -> None:
        """Test that invalid window raises ValueError."""
        asset = pd.Series([0.01, 0.02, 0.03])
        benchmark = pd.Series([0.01, 0.02, 0.03])

        with pytest.raises(ValueError, match="Window must be at least 2"):
            CorrelationAnalyzer.calculate_rolling_beta(asset, benchmark, window=1)

    def test_rolling_beta_length_mismatch(self) -> None:
        """Test that mismatched lengths raise ValueError."""
        asset = pd.Series([0.01, 0.02, 0.03])
        benchmark = pd.Series([0.01, 0.02])

        with pytest.raises(ValueError, match="must have equal length"):
            CorrelationAnalyzer.calculate_rolling_beta(asset, benchmark, window=2)


class TestAnalyze:
    """Tests for the analyze method."""

    def test_analyze_returns_correlation_result(self) -> None:
        """Test that analyze returns CorrelationResult."""
        data = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03],
                "GOOGL": [0.015, 0.018, -0.008, 0.025],
            }
        )

        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(data, period="1Y")

        assert isinstance(result, CorrelationResult)

    def test_analyze_symbols(self) -> None:
        """Test that analyze captures symbols correctly."""
        data = pd.DataFrame(
            {
                "AAPL": [0.01, 0.02, -0.01, 0.03],
                "GOOGL": [0.015, 0.018, -0.008, 0.025],
                "MSFT": [0.012, 0.019, -0.009, 0.028],
            }
        )

        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(data)

        assert result.symbols == ["AAPL", "GOOGL", "MSFT"]

    def test_analyze_period(self) -> None:
        """Test that period is captured in result."""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0],
                "B": [2.0, 3.0, 4.0],
            }
        )

        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(data, period="2024-01-01 to 2024-12-31")

        assert result.period == "2024-01-01 to 2024-12-31"

    def test_analyze_method(self) -> None:
        """Test that method is captured in result."""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0],
                "B": [2.0, 3.0, 4.0, 5.0],
            }
        )

        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(data, method="spearman")

        assert result.method == "spearman"

    def test_analyze_correlation_matrix(self) -> None:
        """Test that correlation matrix is correctly included."""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0, 5.0],
                "B": [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfect correlation with A
            }
        )

        analyzer = CorrelationAnalyzer()
        result = analyzer.analyze(data)

        # Diagonal should be 1.0
        assert result.correlation_matrix.loc["A", "A"] == pytest.approx(1.0)
        assert result.correlation_matrix.loc["B", "B"] == pytest.approx(1.0)

        # Off-diagonal should be 1.0 (perfect correlation)
        assert result.correlation_matrix.loc["A", "B"] == pytest.approx(1.0)
