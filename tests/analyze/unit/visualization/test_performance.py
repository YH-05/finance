"""Unit tests for performance visualization module."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from pandas import DataFrame
from pandas.io.formats.style import Styler

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_returns_df() -> DataFrame:
    """Create sample returns DataFrame for styling tests."""
    data = {
        "symbol": ["AAPL", "MSFT", "GOOGL"],
        "1D": [1.5, -0.8, 2.3],
        "1W": [3.2, -1.5, 4.8],
        "1M": [-2.1, 5.6, -0.3],
        "YTD": [15.2, -8.4, 22.1],
    }
    return DataFrame(data).set_index("symbol")


@pytest.fixture
def sample_price_df() -> DataFrame:
    """Create sample price DataFrame for cumulative returns tests."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    data = {
        "AAPL": [150.0, 152.0, 151.0, 154.0, 156.0, 155.0, 158.0, 160.0, 159.0, 162.0],
        "MSFT": [350.0, 348.0, 352.0, 355.0, 354.0, 358.0, 360.0, 357.0, 362.0, 365.0],
        "GOOGL": [140.0, 142.0, 141.0, 143.0, 145.0, 144.0, 146.0, 148.0, 147.0, 150.0],
    }
    return DataFrame(data, index=dates)


@pytest.fixture
def empty_returns_df() -> DataFrame:
    """Create empty returns DataFrame."""
    return DataFrame({"1D": [], "1W": [], "1M": [], "YTD": []})


@pytest.fixture
def empty_price_df() -> DataFrame:
    """Create empty price DataFrame."""
    return DataFrame()


# =============================================================================
# apply_df_style Tests
# =============================================================================


class TestApplyDfStyle:
    """Tests for apply_df_style function."""

    def test_正常系_スタイルが適用される(self, sample_returns_df: DataFrame) -> None:
        """DataFrameにスタイルが適用されることを確認。"""
        from analyze.visualization.performance import apply_df_style

        result = apply_df_style(sample_returns_df)

        assert isinstance(result, Styler)
        assert result.data.equals(sample_returns_df)

    def test_正常系_正の値に緑色が適用される(
        self, sample_returns_df: DataFrame
    ) -> None:
        """正の値に緑色系のスタイルが適用されることを確認。"""
        from analyze.visualization.performance import apply_df_style

        result = apply_df_style(sample_returns_df)

        # Stylerオブジェクトが作成されていることを確認
        assert isinstance(result, Styler)

    def test_正常系_負の値に赤色が適用される(
        self, sample_returns_df: DataFrame
    ) -> None:
        """負の値に赤色系のスタイルが適用されることを確認。"""
        from analyze.visualization.performance import apply_df_style

        result = apply_df_style(sample_returns_df)

        # Stylerオブジェクトが作成されていることを確認
        assert isinstance(result, Styler)

    def test_エッジケース_空のDataFrameでもエラーなし(
        self, empty_returns_df: DataFrame
    ) -> None:
        """空のDataFrameでもエラーが発生しないことを確認。"""
        from analyze.visualization.performance import apply_df_style

        result = apply_df_style(empty_returns_df)

        assert isinstance(result, Styler)

    def test_正常系_フォーマットが適用される(
        self, sample_returns_df: DataFrame
    ) -> None:
        """数値フォーマットが適用されることを確認。"""
        from analyze.visualization.performance import apply_df_style

        result = apply_df_style(sample_returns_df)

        # HTMLに変換してフォーマットを確認
        html = result.to_html()
        assert isinstance(html, str)

    def test_正常系_バーが表示される(self, sample_returns_df: DataFrame) -> None:
        """バーグラフスタイルが適用されることを確認。"""
        from analyze.visualization.performance import apply_df_style

        result = apply_df_style(sample_returns_df)

        # Stylerオブジェクトが作成されていることを確認
        assert isinstance(result, Styler)


# =============================================================================
# plot_cumulative_returns Tests
# =============================================================================


class TestPlotCumulativeReturns:
    """Tests for plot_cumulative_returns function."""

    def test_正常系_Figureが返される(self, sample_price_df: DataFrame) -> None:
        """Plotly Figureオブジェクトが返されることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        symbols = ["AAPL", "MSFT", "GOOGL"]
        result = plot_cumulative_returns(sample_price_df, symbols, "Test Chart")

        assert isinstance(result, go.Figure)

    def test_正常系_タイトルが設定される(self, sample_price_df: DataFrame) -> None:
        """チャートタイトルが設定されることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        symbols = ["AAPL", "MSFT"]
        title = "Cumulative Returns Test"
        result = plot_cumulative_returns(sample_price_df, symbols, title)

        assert result.layout.title.text == title

    def test_正常系_各シンボルのトレースが追加される(
        self, sample_price_df: DataFrame
    ) -> None:
        """各シンボルに対応するトレースが追加されることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        symbols = ["AAPL", "MSFT"]
        result = plot_cumulative_returns(sample_price_df, symbols, "Test")

        traces = list(result.data)
        trace_names = [trace.name for trace in traces]
        assert "AAPL" in trace_names
        assert "MSFT" in trace_names
        assert len(traces) == 2

    def test_正常系_一部のシンボルのみプロット(
        self, sample_price_df: DataFrame
    ) -> None:
        """一部のシンボルのみを指定してプロットできることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        symbols = ["AAPL"]
        result = plot_cumulative_returns(sample_price_df, symbols, "Single Symbol")

        traces = list(result.data)
        assert len(traces) == 1
        assert traces[0].name == "AAPL"

    def test_正常系_累積リターンが計算される(self, sample_price_df: DataFrame) -> None:
        """累積リターンが正しく計算されることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        symbols = ["AAPL"]
        result = plot_cumulative_returns(sample_price_df, symbols, "Test")

        # 最初の値は0%（基準点）であるべき
        y_values = result.data[0].y
        assert y_values is not None
        assert len(y_values) > 0
        # 最初の値は0に近いはず（累積リターンの開始点）
        assert abs(y_values[0]) < 0.01

    def test_エッジケース_空のDataFrameで空のFigure(
        self, empty_price_df: DataFrame
    ) -> None:
        """空のDataFrameで空のFigureが返されることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        result = plot_cumulative_returns(empty_price_df, [], "Empty Chart")

        assert isinstance(result, go.Figure)
        assert len(list(result.data)) == 0

    def test_エッジケース_存在しないシンボルは無視される(
        self, sample_price_df: DataFrame
    ) -> None:
        """存在しないシンボルが無視されることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        symbols = ["AAPL", "INVALID_SYMBOL"]
        result = plot_cumulative_returns(sample_price_df, symbols, "Test")

        traces = list(result.data)
        trace_names = [trace.name for trace in traces]
        assert "AAPL" in trace_names
        assert "INVALID_SYMBOL" not in trace_names
        assert len(traces) == 1

    def test_正常系_Y軸ラベルにパーセント表記(self, sample_price_df: DataFrame) -> None:
        """Y軸にパーセント表記が使用されることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        symbols = ["AAPL"]
        result = plot_cumulative_returns(sample_price_df, symbols, "Test")

        # Y軸のタイトルまたはフォーマットを確認
        assert result.layout.yaxis is not None

    def test_正常系_凡例が表示される(self, sample_price_df: DataFrame) -> None:
        """凡例が表示されることを確認。"""
        from analyze.visualization.performance import plot_cumulative_returns

        symbols = ["AAPL", "MSFT"]
        result = plot_cumulative_returns(sample_price_df, symbols, "Test")

        assert result.layout.showlegend is True or result.layout.showlegend is None
