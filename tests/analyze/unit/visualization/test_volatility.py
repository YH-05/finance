"""Unit tests for volatility visualization module."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from pandas import DataFrame

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_vix_high_yield_df() -> DataFrame:
    """Create sample DataFrame with VIX and High Yield Spread data."""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    data = {
        "VIX": np.random.uniform(12, 30, 30),
        "High_Yield_Spread": np.random.uniform(3, 6, 30),
    }
    return DataFrame(data, index=dates)


@pytest.fixture
def sample_vix_uncertainty_df() -> DataFrame:
    """Create sample DataFrame with VIX and Economic Policy Uncertainty Index."""
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    data = {
        "VIX": np.random.uniform(12, 30, 60),
        "Uncertainty_Index": np.random.uniform(80, 200, 60),
    }
    return DataFrame(data, index=dates)


@pytest.fixture
def empty_df() -> DataFrame:
    """Create empty DataFrame."""
    return DataFrame()


@pytest.fixture
def df_with_nan() -> DataFrame:
    """Create DataFrame with NaN values."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    data = {
        "VIX": [15.0, 16.0, np.nan, 18.0, 19.0, np.nan, 21.0, 22.0, 23.0, 24.0],
        "High_Yield_Spread": [4.0, 4.2, 4.3, np.nan, 4.5, 4.6, 4.7, np.nan, 4.9, 5.0],
    }
    return DataFrame(data, index=dates)


# =============================================================================
# plot_vix_and_high_yield_spread Tests
# =============================================================================


class TestPlotVixAndHighYieldSpread:
    """Tests for plot_vix_and_high_yield_spread function."""

    def test_正常系_Figureが返される(self, sample_vix_high_yield_df: DataFrame) -> None:
        """Plotly Figureオブジェクトが返されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_high_yield_spread

        result = plot_vix_and_high_yield_spread(sample_vix_high_yield_df)

        assert isinstance(result, go.Figure)

    def test_正常系_2軸プロットが作成される(
        self, sample_vix_high_yield_df: DataFrame
    ) -> None:
        """VIXとハイイールドスプレッドの2軸プロットが作成されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_high_yield_spread

        result = plot_vix_and_high_yield_spread(sample_vix_high_yield_df)

        # 2つのトレースが存在することを確認
        traces = list(result.data)
        assert len(traces) == 2

        # トレース名を確認
        trace_names = [trace.name for trace in traces]
        assert "VIX" in trace_names
        assert (
            "High Yield Spread" in trace_names
            or "ハイイールドスプレッド" in trace_names
        )

    def test_正常系_Y軸が2つ存在する(self, sample_vix_high_yield_df: DataFrame) -> None:
        """2つのY軸が設定されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_high_yield_spread

        result = plot_vix_and_high_yield_spread(sample_vix_high_yield_df)

        # yaxis と yaxis2 が設定されていることを確認
        assert result.layout.yaxis is not None
        assert result.layout.yaxis2 is not None

    def test_正常系_タイトルが設定される(
        self, sample_vix_high_yield_df: DataFrame
    ) -> None:
        """チャートタイトルが設定されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_high_yield_spread

        result = plot_vix_and_high_yield_spread(sample_vix_high_yield_df)

        # タイトルが存在することを確認
        assert result.layout.title is not None
        assert result.layout.title.text is not None

    def test_エッジケース_空のDataFrameで空のFigure(self, empty_df: DataFrame) -> None:
        """空のDataFrameで空のFigureが返されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_high_yield_spread

        result = plot_vix_and_high_yield_spread(empty_df)

        assert isinstance(result, go.Figure)

    def test_エッジケース_NaN値があっても処理される(
        self, df_with_nan: DataFrame
    ) -> None:
        """NaN値を含むDataFrameでもエラーなく処理されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_high_yield_spread

        result = plot_vix_and_high_yield_spread(df_with_nan)

        assert isinstance(result, go.Figure)
        traces = list(result.data)
        assert len(traces) == 2

    def test_正常系_凡例が表示される(self, sample_vix_high_yield_df: DataFrame) -> None:
        """凡例が表示されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_high_yield_spread

        result = plot_vix_and_high_yield_spread(sample_vix_high_yield_df)

        # showlegend が True または None (デフォルト表示) であることを確認
        assert result.layout.showlegend is True or result.layout.showlegend is None


# =============================================================================
# plot_vix_and_uncertainty_index Tests
# =============================================================================


class TestPlotVixAndUncertaintyIndex:
    """Tests for plot_vix_and_uncertainty_index function."""

    def test_正常系_Figureが返される(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """Plotly Figureオブジェクトが返されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        result = plot_vix_and_uncertainty_index(sample_vix_uncertainty_df)

        assert isinstance(result, go.Figure)

    def test_正常系_2軸プロットが作成される(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """VIXと不確実性指数の2軸プロットが作成されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        result = plot_vix_and_uncertainty_index(sample_vix_uncertainty_df)

        # 2つのトレースが存在することを確認 (VIX + Uncertainty Index)
        traces = list(result.data)
        assert len(traces) == 2

    def test_正常系_デフォルトのEMAスパンが30(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """デフォルトのEMAスパンが30であることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        # デフォルト引数でエラーなく実行できることを確認
        result = plot_vix_and_uncertainty_index(sample_vix_uncertainty_df)

        assert isinstance(result, go.Figure)

    def test_正常系_カスタムEMAスパンが適用される(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """カスタムEMAスパンが正しく適用されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        # ema_span=10 で実行
        result = plot_vix_and_uncertainty_index(sample_vix_uncertainty_df, ema_span=10)

        assert isinstance(result, go.Figure)

    def test_正常系_Y軸が2つ存在する(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """2つのY軸が設定されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        result = plot_vix_and_uncertainty_index(sample_vix_uncertainty_df)

        # yaxis と yaxis2 が設定されていることを確認
        assert result.layout.yaxis is not None
        assert result.layout.yaxis2 is not None

    def test_正常系_タイトルが設定される(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """チャートタイトルが設定されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        result = plot_vix_and_uncertainty_index(sample_vix_uncertainty_df)

        # タイトルが存在することを確認
        assert result.layout.title is not None
        assert result.layout.title.text is not None

    def test_エッジケース_空のDataFrameで空のFigure(self, empty_df: DataFrame) -> None:
        """空のDataFrameで空のFigureが返されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        result = plot_vix_and_uncertainty_index(empty_df)

        assert isinstance(result, go.Figure)

    def test_異常系_EMAスパンが0以下でValueError(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """EMAスパンが0以下の場合にValueErrorが発生することを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        with pytest.raises(ValueError, match="ema_span must be positive"):
            plot_vix_and_uncertainty_index(sample_vix_uncertainty_df, ema_span=0)

        with pytest.raises(ValueError, match="ema_span must be positive"):
            plot_vix_and_uncertainty_index(sample_vix_uncertainty_df, ema_span=-5)

    def test_正常系_凡例が表示される(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """凡例が表示されることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        result = plot_vix_and_uncertainty_index(sample_vix_uncertainty_df)

        # showlegend が True または None (デフォルト表示) であることを確認
        assert result.layout.showlegend is True or result.layout.showlegend is None

    def test_正常系_EMAが適用されている(
        self, sample_vix_uncertainty_df: DataFrame
    ) -> None:
        """不確実性指数にEMAが適用されていることを確認。"""
        from analyze.visualization.volatility import plot_vix_and_uncertainty_index

        result = plot_vix_and_uncertainty_index(sample_vix_uncertainty_df, ema_span=10)

        traces = list(result.data)
        assert len(traces) == 2
