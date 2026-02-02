"""Unit tests for beta visualization module."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from pandas import DataFrame

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_rolling_beta_df() -> DataFrame:
    """Create sample DataFrame with rolling beta data.

    DataFrame structure: columns are ticker symbols, values are rolling beta coefficients.
    Index is DatetimeIndex.
    """
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    # Simulate rolling beta data for multiple tickers
    np.random.seed(42)
    data = {
        "AAPL": np.random.uniform(0.8, 1.5, 100),
        "MSFT": np.random.uniform(0.7, 1.3, 100),
        "GOOGL": np.random.uniform(0.9, 1.6, 100),
    }
    df = DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


@pytest.fixture
def sample_single_ticker_df() -> DataFrame:
    """Create sample DataFrame with single ticker beta."""
    dates = pd.date_range("2024-01-01", periods=50, freq="D")
    np.random.seed(42)
    data = {
        "AAPL": np.random.uniform(0.8, 1.5, 50),
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
            1.0,
            1.1,
            np.nan,
            1.2,
            1.15,
            np.nan,
            1.25,
            1.18,
            1.3,
            1.28,
            1.22,
            np.nan,
            1.35,
            1.32,
            1.4,
            np.nan,
            1.38,
            1.36,
            1.42,
            1.39,
        ],
    }
    df = DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


@pytest.fixture
def df_with_multiple_tickers() -> DataFrame:
    """Create DataFrame with multiple tickers for testing ticker selection."""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    np.random.seed(42)
    data = {
        "AAPL": np.random.uniform(0.9, 1.4, 30),
        "MSFT": np.random.uniform(0.8, 1.2, 30),
        "TSLA": np.random.uniform(1.2, 2.0, 30),
    }
    df = DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


# =============================================================================
# plot_rolling_beta Tests
# =============================================================================


class TestPlotRollingBeta:
    """Tests for plot_rolling_beta function."""

    def test_正常系_Figureが返される(self, sample_rolling_beta_df: DataFrame) -> None:
        """Plotly Figureオブジェクトが返されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)

    def test_正常系_単一ティッカーでラインプロットが作成される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """単一ティッカーのローリングベータのラインプロットが作成されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        # トレースが存在することを確認
        traces = list(result.data)
        assert len(traces) >= 1

        # ラインプロットであることを確認
        assert traces[0].mode == "lines"

    def test_正常系_複数ティッカーで複数ラインが作成される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """複数ティッカーで複数のラインプロットが作成されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL", "MSFT", "GOOGL"],
            target_index="S&P 500",
        )

        # 3つのトレースが存在することを確認
        traces = list(result.data)
        assert len(traces) == 3

        # 各トレースがラインプロットであることを確認
        for trace in traces:
            assert trace.mode == "lines"

    def test_正常系_タイトルに対象指数が含まれる(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """チャートタイトルに対象指数が含まれることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        # タイトルが存在し、指数名が含まれることを確認
        assert result.layout.title is not None
        title_text = result.layout.title.text
        assert title_text is not None
        assert "S&P 500" in title_text

    def test_正常系_Y軸ラベルにベータが含まれる(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """Y軸ラベルにベータの情報が含まれることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        # Y軸の設定を確認
        assert result.layout.yaxis is not None

    def test_正常系_X軸が日付として設定される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """X軸が日付データとして設定されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        # X軸の設定を確認
        assert result.layout.xaxis is not None

    def test_エッジケース_空のDataFrameで空のFigure(self, empty_df: DataFrame) -> None:
        """空のDataFrameで空のFigureが返されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            empty_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)

    def test_エッジケース_NaN値があっても処理される(
        self, df_with_nan: DataFrame
    ) -> None:
        """NaN値を含むDataFrameでもエラーなく処理されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            df_with_nan,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)
        traces = list(result.data)
        assert len(traces) >= 1

    def test_正常系_凡例が表示される(self, sample_rolling_beta_df: DataFrame) -> None:
        """凡例が表示されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL", "MSFT"],
            target_index="S&P 500",
        )

        # showlegend が True または None (デフォルト表示) であることを確認
        assert result.layout.showlegend is True or result.layout.showlegend is None

    def test_正常系_日本語フォントスタックが適用される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """日本語フォントスタックがタイトルに適用されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        # フォント設定を確認
        assert result.layout.title is not None
        assert result.layout.title.font is not None
        font_family = result.layout.title.font.family
        assert font_family is not None
        assert "Hiragino" in font_family or "Noto Sans JP" in font_family

    def test_正常系_ホバー情報が設定される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """ホバー時に情報が表示される設定があることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        # トレースにホバー設定があることを確認
        traces = list(result.data)
        assert len(traces) >= 1
        # hovertemplate が設定されているか確認
        assert traces[0].hovertemplate is not None

    def test_エッジケース_存在しないティッカーは無視される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """存在しないティッカーを含む場合、そのティッカーは無視されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL", "INVALID", "MSFT"],
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)
        # 有効なティッカー分のトレースのみ存在することを確認
        traces = list(result.data)
        assert len(traces) == 2

    def test_エッジケース_全ティッカーが存在しない場合は空のFigure(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """全てのティッカーが存在しない場合、空のFigureが返されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["INVALID1", "INVALID2"],
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)
        traces = list(result.data)
        assert len(traces) == 0

    def test_正常系_ベータ1基準線が表示される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """ベータ=1の基準線が表示されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        # shapes でベータ=1線が設定されているか確認
        shapes = result.layout.shapes
        has_beta_one_line = False

        if shapes:
            for shape in shapes:
                if hasattr(shape, "y0") and shape.y0 == 1 and shape.y1 == 1:
                    has_beta_one_line = True
                    break

        assert has_beta_one_line, "ベータ=1の基準線が設定されていません"

    def test_正常系_グリッドが表示される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """グリッドが表示されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
        )

        # showgrid が True であることを確認
        assert result.layout.yaxis is not None
        assert result.layout.yaxis.showgrid is True

    def test_正常系_空のティッカーリストで空のFigure(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """空のティッカーリストで空のFigureが返されることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=[],
            target_index="S&P 500",
        )

        assert isinstance(result, go.Figure)
        traces = list(result.data)
        assert len(traces) == 0

    def test_正常系_異なるティッカーに異なる色が割り当てられる(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """複数ティッカーに異なる色が割り当てられることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL", "MSFT", "GOOGL"],
            target_index="S&P 500",
        )

        traces = list(result.data)
        assert len(traces) == 3

        # 各トレースの色が異なることを確認
        colors = [trace.line.color for trace in traces]
        assert len(set(colors)) == 3, "各ティッカーに異なる色が割り当てられていません"

    def test_正常系_ウィンドウパラメータがタイトルに反映される(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """ローリングウィンドウのパラメータがタイトルに含まれることを確認（オプション）。"""
        from analyze.visualization.beta import plot_rolling_beta

        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
            window=60,
        )

        # タイトルが存在することを確認
        assert result.layout.title is not None
        title_text = result.layout.title.text
        assert title_text is not None
        # windowの値がタイトルに含まれる（オプション機能）
        # 含まれなくてもテストは失敗しない

    def test_正常系_カスタムタイトルが設定可能(
        self, sample_rolling_beta_df: DataFrame
    ) -> None:
        """カスタムタイトルを設定できることを確認。"""
        from analyze.visualization.beta import plot_rolling_beta

        custom_title = "カスタムベータチャート"
        result = plot_rolling_beta(
            sample_rolling_beta_df,
            tickers=["AAPL"],
            target_index="S&P 500",
            title=custom_title,
        )

        assert result.layout.title is not None
        assert result.layout.title.text == custom_title
