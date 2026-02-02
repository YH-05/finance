"""Unit tests for currency visualization module."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from pandas import DataFrame

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_dollar_metals_df() -> DataFrame:
    """Create sample DataFrame with Dollar Index and metals cumulative returns data."""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    data = {
        "DX-Y.NYB": np.random.uniform(-5, 5, 30),  # Dollar Index cumulative return
        "GC=F": np.random.uniform(-10, 10, 30),  # Gold cumulative return
        "SI=F": np.random.uniform(-15, 15, 30),  # Silver cumulative return
    }
    return DataFrame(data, index=dates)


@pytest.fixture
def sample_dollar_only_df() -> DataFrame:
    """Create sample DataFrame with only Dollar Index data."""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    data = {
        "DX-Y.NYB": np.random.uniform(-5, 5, 30),
    }
    return DataFrame(data, index=dates)


@pytest.fixture
def sample_metals_only_df() -> DataFrame:
    """Create sample DataFrame with only metals data."""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    data = {
        "GC=F": np.random.uniform(-10, 10, 30),
        "SI=F": np.random.uniform(-15, 15, 30),
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
        "DX-Y.NYB": [1.0, 2.0, np.nan, 4.0, 5.0, np.nan, 7.0, 8.0, 9.0, 10.0],
        "GC=F": [3.0, 4.0, 5.0, np.nan, 7.0, 8.0, 9.0, np.nan, 11.0, 12.0],
        "SI=F": [5.0, np.nan, 7.0, 8.0, 9.0, 10.0, np.nan, 12.0, 13.0, 14.0],
    }
    return DataFrame(data, index=dates)


# =============================================================================
# plot_dollar_index_and_metals Tests
# =============================================================================


class TestPlotDollarIndexAndMetals:
    """Tests for plot_dollar_index_and_metals function."""

    def test_正常系_Figureが返される(self, sample_dollar_metals_df: DataFrame) -> None:
        """Plotly Figureオブジェクトが返されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_dollar_metals_df)

        assert isinstance(result, go.Figure)

    def test_正常系_2軸プロットが作成される(
        self, sample_dollar_metals_df: DataFrame
    ) -> None:
        """ドル指数と金属価格の2軸プロットが作成されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_dollar_metals_df)

        # 3つのトレースが存在することを確認 (DX-Y.NYB, GC=F, SI=F)
        traces = list(result.data)
        assert len(traces) == 3

        # トレース名を確認
        trace_names = [trace.name for trace in traces]
        assert "ドル指数" in trace_names
        assert "金" in trace_names
        assert "銀" in trace_names

    def test_正常系_Y軸が2つ存在する(self, sample_dollar_metals_df: DataFrame) -> None:
        """2つのY軸が設定されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_dollar_metals_df)

        # yaxis と yaxis2 が設定されていることを確認
        assert result.layout.yaxis is not None
        assert result.layout.yaxis2 is not None

    def test_正常系_タイトルが設定される(
        self, sample_dollar_metals_df: DataFrame
    ) -> None:
        """チャートタイトルが設定されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_dollar_metals_df)

        # タイトルが存在することを確認
        assert result.layout.title is not None
        assert result.layout.title.text is not None

    def test_正常系_凡例が表示される(self, sample_dollar_metals_df: DataFrame) -> None:
        """凡例が表示されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_dollar_metals_df)

        # showlegend が True または None (デフォルト表示) であることを確認
        assert result.layout.showlegend is True or result.layout.showlegend is None

    def test_正常系_ドル指数のみの場合(self, sample_dollar_only_df: DataFrame) -> None:
        """ドル指数のみのDataFrameでも動作することを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_dollar_only_df)

        assert isinstance(result, go.Figure)
        traces = list(result.data)
        assert len(traces) == 1

    def test_正常系_金属のみの場合(self, sample_metals_only_df: DataFrame) -> None:
        """金属価格のみのDataFrameでも動作することを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_metals_only_df)

        assert isinstance(result, go.Figure)
        traces = list(result.data)
        assert len(traces) == 2

    def test_エッジケース_空のDataFrameで空のFigure(self, empty_df: DataFrame) -> None:
        """空のDataFrameで空のFigureが返されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(empty_df)

        assert isinstance(result, go.Figure)

    def test_エッジケース_NaN値があっても処理される(
        self, df_with_nan: DataFrame
    ) -> None:
        """NaN値を含むDataFrameでもエラーなく処理されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(df_with_nan)

        assert isinstance(result, go.Figure)
        traces = list(result.data)
        assert len(traces) == 3

    def test_正常系_ドル指数が左軸に配置される(
        self, sample_dollar_metals_df: DataFrame
    ) -> None:
        """ドル指数が左Y軸に配置されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_dollar_metals_df)

        # ドル指数のトレースを探す
        dollar_trace = None
        for trace in result.data:
            if trace.name == "ドル指数":
                dollar_trace = trace
                break

        assert dollar_trace is not None
        # 左軸 (y または y1) に配置されていることを確認
        assert dollar_trace.yaxis == "y" or dollar_trace.yaxis is None

    def test_正常系_金属が右軸に配置される(
        self, sample_dollar_metals_df: DataFrame
    ) -> None:
        """金属価格が右Y軸に配置されることを確認。"""
        from analyze.visualization.currency import plot_dollar_index_and_metals

        result = plot_dollar_index_and_metals(sample_dollar_metals_df)

        # 金のトレースを探す
        gold_trace = None
        for trace in result.data:
            if trace.name == "金":
                gold_trace = trace
                break

        assert gold_trace is not None
        # 右軸 (y2) に配置されていることを確認
        assert gold_trace.yaxis == "y2"
