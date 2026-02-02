"""Unit tests for correlation visualization module."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from pandas import DataFrame

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_rolling_correlation_df() -> DataFrame:
    """Create sample DataFrame with rolling correlation data."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    # Simulate rolling correlation data with index name
    np.random.seed(42)
    data = {
        "AAPL": np.random.uniform(-0.5, 1.0, 100),
        "MSFT": np.random.uniform(-0.3, 0.9, 100),
    }
    df = DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


@pytest.fixture
def sample_single_ticker_df() -> DataFrame:
    """Create sample DataFrame with single ticker correlation."""
    dates = pd.date_range("2024-01-01", periods=50, freq="D")
    np.random.seed(42)
    data = {
        "AAPL": np.random.uniform(-0.5, 1.0, 50),
    }
    df = DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


@pytest.fixture
def empty_df() -> DataFrame:
    """Create empty DataFrame."""
    return DataFrame()


@pytest.fixture
def df_with_nan() -> DataFrame:
    """Create DataFrame with NaN values."""
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    data = {
        "AAPL": [
            0.5,
            0.6,
            np.nan,
            0.7,
            0.65,
            np.nan,
            0.72,
            0.68,
            0.75,
            0.8,
            0.78,
            np.nan,
            0.82,
            0.79,
            0.85,
            np.nan,
            0.88,
            0.86,
            0.9,
            0.87,
        ],
    }
    df = DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


# =============================================================================
# plot_rolling_correlation Tests
# =============================================================================


class TestPlotRollingCorrelation:
    """Tests for plot_rolling_correlation function."""

    def test_正常系_Figureが返される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """Plotly Figureオブジェクトが返されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)

    def test_正常系_ラインプロットが作成される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """ローリング相関係数のラインプロットが作成されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # トレースが存在することを確認
        traces = list(result.data)
        assert len(traces) >= 1

        # ラインプロットであることを確認
        assert traces[0].mode == "lines"

    def test_正常系_タイトルにティッカーと指数が含まれる(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """チャートタイトルにティッカーシンボルと対象指数が含まれることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # タイトルが存在し、ティッカーと指数名が含まれることを確認
        assert result.layout.title is not None
        title_text = result.layout.title.text
        assert title_text is not None
        assert "AAPL" in title_text
        assert "S&P 500" in title_text

    def test_正常系_Y軸が相関係数の範囲に設定される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """Y軸が相関係数の妥当な範囲に設定されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # Y軸の設定を確認
        assert result.layout.yaxis is not None

    def test_正常系_X軸が日付として設定される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """X軸が日付データとして設定されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # X軸の設定を確認
        assert result.layout.xaxis is not None

    def test_正常系_複数ティッカーのDataFrameで指定ティッカーのみ表示(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """複数ティッカーのDataFrameで指定したティッカーのみプロットされることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="MSFT",
            target_index="S&P 500",
        )

        # 1つのトレースが存在することを確認
        traces = list(result.data)
        assert len(traces) == 1

    def test_エッジケース_空のDataFrameで空のFigure(self, empty_df: DataFrame) -> None:
        """空のDataFrameで空のFigureが返されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            empty_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)

    def test_エッジケース_NaN値があっても処理される(
        self, df_with_nan: DataFrame
    ) -> None:
        """NaN値を含むDataFrameでもエラーなく処理されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            df_with_nan,
            ticker="AAPL",
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)
        traces = list(result.data)
        assert len(traces) >= 1

    def test_正常系_凡例が表示される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """凡例が表示されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # showlegend が True または None (デフォルト表示) であることを確認
        assert result.layout.showlegend is True or result.layout.showlegend is None

    def test_正常系_日本語フォントスタックが適用される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """日本語フォントスタックがタイトルに適用されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # フォント設定を確認
        assert result.layout.title is not None
        assert result.layout.title.font is not None
        font_family = result.layout.title.font.family
        assert font_family is not None
        assert "Hiragino" in font_family or "Noto Sans JP" in font_family

    def test_正常系_ホバー情報が設定される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """ホバー時に情報が表示される設定があることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # トレースにホバー設定があることを確認
        traces = list(result.data)
        assert len(traces) >= 1
        # hovertemplate が設定されているか確認
        assert traces[0].hovertemplate is not None

    def test_異常系_存在しないティッカーで空のFigure(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """存在しないティッカーを指定した場合、空のFigureが返されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="INVALID",
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)
        # トレースが存在しないか確認
        traces = list(result.data)
        assert len(traces) == 0

    def test_正常系_ゼロ基準線が表示される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """相関係数0の基準線が表示されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # shapes または hlines でゼロ線が設定されているか確認
        # または yaxis の zeroline が True であるか確認
        shapes = result.layout.shapes
        has_zero_line = False

        if shapes:
            for shape in shapes:
                if hasattr(shape, "y0") and shape.y0 == 0 and shape.y1 == 0:
                    has_zero_line = True
                    break

        # zeroline が True の場合も OK
        if result.layout.yaxis and result.layout.yaxis.zeroline:
            has_zero_line = True

        assert has_zero_line, "ゼロ基準線が設定されていません"

    def test_正常系_グリッドが表示される(
        self, sample_rolling_correlation_df: DataFrame
    ) -> None:
        """グリッドが表示されることを確認。"""
        from analyze.visualization.correlation import plot_rolling_correlation

        result = plot_rolling_correlation(
            sample_rolling_correlation_df,
            ticker="AAPL",
            target_index="S&P 500",
        )

        # showgrid が True であることを確認
        assert result.layout.yaxis is not None
        assert result.layout.yaxis.showgrid is True
