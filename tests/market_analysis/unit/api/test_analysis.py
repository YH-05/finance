"""Unit tests for Analysis API."""

import numpy as np
import pandas as pd
import pytest

from market_analysis import Analysis
from market_analysis.errors import ValidationError


class TestAnalysisInit:
    """Tests for Analysis initialization."""

    def test_init_with_valid_data(self) -> None:
        """有効なDataFrameで初期化できる."""
        df = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
        analysis = Analysis(df)

        assert analysis is not None
        assert len(analysis.data) == 5

    def test_init_with_empty_data_raises_error(self) -> None:
        """空のDataFrameでValidationErrorが発生."""
        df = pd.DataFrame()
        with pytest.raises(ValidationError, match="cannot be empty"):
            Analysis(df)

    def test_init_with_none_raises_error(self) -> None:
        """NoneでValidationErrorが発生."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            Analysis(None)


class TestAnalysisAddSma:
    """Tests for Analysis.add_sma method."""

    def test_add_sma_creates_column(self) -> None:
        """SMAが列として追加される."""
        df = pd.DataFrame({"close": [100, 102, 101, 103, 105, 104, 106]})
        analysis = Analysis(df)

        result = analysis.add_sma(period=3)

        assert "sma_3" in result.data.columns
        assert result is analysis  # Method chaining

    def test_add_sma_with_invalid_period_raises_error(self) -> None:
        """負のperiodでValidationErrorが発生."""
        df = pd.DataFrame({"close": [100, 102, 101]})
        analysis = Analysis(df)

        with pytest.raises(ValidationError, match="must be positive"):
            analysis.add_sma(period=-1)

    def test_add_sma_multiple_periods(self) -> None:
        """複数のSMAをチェーンで追加できる."""
        df = pd.DataFrame({"close": list(range(100, 150))})
        analysis = Analysis(df)

        result = analysis.add_sma(period=5).add_sma(period=10).add_sma(period=20)

        assert "sma_5" in result.data.columns
        assert "sma_10" in result.data.columns
        assert "sma_20" in result.data.columns


class TestAnalysisAddEma:
    """Tests for Analysis.add_ema method."""

    def test_add_ema_creates_column(self) -> None:
        """EMAが列として追加される."""
        df = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
        analysis = Analysis(df)

        result = analysis.add_ema(period=3)

        assert "ema_3" in result.data.columns

    def test_add_ema_with_invalid_period_raises_error(self) -> None:
        """負のperiodでValidationErrorが発生."""
        df = pd.DataFrame({"close": [100, 102, 101]})
        analysis = Analysis(df)

        with pytest.raises(ValidationError, match="must be positive"):
            analysis.add_ema(period=0)


class TestAnalysisAddReturns:
    """Tests for Analysis.add_returns method."""

    def test_add_returns_creates_column(self) -> None:
        """リターンが列として追加される."""
        df = pd.DataFrame({"close": [100, 102, 101, 103]})
        analysis = Analysis(df)

        result = analysis.add_returns()

        assert "returns" in result.data.columns


class TestAnalysisAddVolatility:
    """Tests for Analysis.add_volatility method."""

    def test_add_volatility_creates_column(self) -> None:
        """ボラティリティが列として追加される."""
        df = pd.DataFrame({"close": list(range(100, 130))})
        analysis = Analysis(df)

        result = analysis.add_volatility(period=5)

        assert (
            "volatility" in result.data.columns or "volatility_5" in result.data.columns
        )

    def test_add_volatility_with_invalid_period_raises_error(self) -> None:
        """period<2でValidationErrorが発生."""
        df = pd.DataFrame({"close": [100, 102, 101]})
        analysis = Analysis(df)

        with pytest.raises(ValidationError, match="must be at least 2"):
            analysis.add_volatility(period=1)


class TestAnalysisMethodChaining:
    """Tests for Analysis method chaining."""

    def test_full_chain(self) -> None:
        """メソッドチェーンで全ての指標を追加できる."""
        df = pd.DataFrame({"close": list(range(100, 150))})

        result = (
            Analysis(df)
            .add_sma(period=5)
            .add_ema(period=5)
            .add_returns()
            .add_volatility(period=5)
        )

        assert "sma_5" in result.data.columns
        assert "ema_5" in result.data.columns
        assert "returns" in result.data.columns
        assert (
            "volatility" in result.data.columns or "volatility_5" in result.data.columns
        )

    def test_indicators_property(self) -> None:
        """indicators プロパティが追加された指標を返す."""
        df = pd.DataFrame({"close": list(range(100, 120))})

        analysis = Analysis(df).add_sma(period=5).add_returns()

        indicators = analysis.indicators
        assert "sma_5" in indicators
        assert "returns" in indicators


class TestAnalysisCorrelation:
    """Tests for Analysis.correlation static method."""

    def test_correlation_with_two_dataframes(self) -> None:
        """2つのDataFrameで相関行列が計算できる."""
        df1 = pd.DataFrame({"close": [1, 2, 3, 4, 5]})
        df2 = pd.DataFrame({"close": [2, 4, 6, 8, 10]})

        corr = Analysis.correlation([df1, df2], symbols=["A", "B"])

        assert corr.shape == (2, 2)
        assert corr.loc["A", "B"] == pytest.approx(1.0, abs=0.001)

    def test_correlation_with_three_dataframes(self) -> None:
        """3つのDataFrameで相関行列が計算できる."""
        df1 = pd.DataFrame({"close": [1, 2, 3, 4, 5]})
        df2 = pd.DataFrame({"close": [2, 4, 6, 8, 10]})
        df3 = pd.DataFrame({"close": [5, 4, 3, 2, 1]})

        corr = Analysis.correlation([df1, df2, df3], symbols=["A", "B", "C"])

        assert corr.shape == (3, 3)
        assert corr.loc["A", "C"] == pytest.approx(-1.0, abs=0.001)

    def test_correlation_raises_with_one_dataframe(self) -> None:
        """1つのDataFrameでValidationErrorが発生."""
        df = pd.DataFrame({"close": [1, 2, 3]})

        with pytest.raises(ValidationError, match="At least 2"):
            Analysis.correlation([df], symbols=["A"])

    def test_correlation_raises_with_mismatched_symbols(self) -> None:
        """シンボル数とDataFrame数が一致しない場合エラー."""
        df1 = pd.DataFrame({"close": [1, 2, 3]})
        df2 = pd.DataFrame({"close": [2, 4, 6]})

        with pytest.raises(ValidationError, match="must match"):
            Analysis.correlation([df1, df2], symbols=["A", "B", "C"])

    def test_correlation_with_default_symbols(self) -> None:
        """シンボル未指定でデフォルト名が使われる."""
        df1 = pd.DataFrame({"close": [1, 2, 3]})
        df2 = pd.DataFrame({"close": [2, 4, 6]})

        corr = Analysis.correlation([df1, df2])

        assert "Symbol_0" in corr.columns
        assert "Symbol_1" in corr.columns


class TestAnalysisRollingCorrelation:
    """Tests for Analysis.rolling_correlation static method."""

    def test_rolling_correlation_returns_series(self) -> None:
        """ローリング相関がSeriesとして返される."""
        df1 = pd.DataFrame({"close": list(range(1, 31))})
        df2 = pd.DataFrame({"close": list(range(2, 62, 2))})

        result = Analysis.rolling_correlation(df1, df2, period=5)

        assert isinstance(result, pd.Series)
        assert len(result) == 30

    def test_rolling_correlation_with_invalid_period_raises_error(self) -> None:
        """period<2でValidationErrorが発生."""
        df1 = pd.DataFrame({"close": [1, 2, 3]})
        df2 = pd.DataFrame({"close": [2, 4, 6]})

        with pytest.raises(ValidationError, match="must be at least 2"):
            Analysis.rolling_correlation(df1, df2, period=1)


class TestAnalysisBeta:
    """Tests for Analysis.beta static method."""

    def test_beta_with_perfect_correlation(self) -> None:
        """完全相関でbetaが計算できる."""
        # Stock moves 2x the benchmark
        benchmark = pd.DataFrame({"close": [100, 101, 100, 102, 103]})
        stock = pd.DataFrame({"close": [100, 102, 100, 104, 106]})

        beta = Analysis.beta(stock, benchmark)

        # Beta should be approximately 2.0
        assert beta == pytest.approx(2.0, abs=0.1)

    def test_beta_returns_nan_with_insufficient_data(self) -> None:
        """データ不足でNaNが返される."""
        benchmark = pd.DataFrame({"close": [100]})
        stock = pd.DataFrame({"close": [100]})

        beta = Analysis.beta(stock, benchmark)

        assert np.isnan(beta)

    def test_beta_case_insensitive_column(self) -> None:
        """列名が大文字小文字を区別しない."""
        benchmark = pd.DataFrame({"Close": [100, 101, 102, 103, 104]})
        stock = pd.DataFrame({"CLOSE": [100, 102, 104, 106, 108]})

        beta = Analysis.beta(stock, benchmark, column="close")

        assert not np.isnan(beta)


class TestAnalysisResult:
    """Tests for Analysis.result method."""

    def test_result_returns_analysis_result(self) -> None:
        """result()がAnalysisResultを返す."""
        df = pd.DataFrame({"close": list(range(100, 120))})

        result = Analysis(df, symbol="TEST").add_sma(period=5).add_returns().result()

        assert result.symbol == "TEST"
        assert "sma_5" in result.indicators
        assert "returns" in result.indicators
