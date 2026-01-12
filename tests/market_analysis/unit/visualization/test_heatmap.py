"""Unit tests for heatmap module."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from market_analysis.types import CorrelationResult
from market_analysis.visualization.charts import ChartConfig, ChartTheme
from market_analysis.visualization.heatmap import HeatmapChart

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_correlation_matrix() -> pd.DataFrame:
    """Create a sample correlation matrix."""
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
    data = np.array(
        [
            [1.0, 0.8, 0.7, 0.6],
            [0.8, 1.0, 0.9, 0.5],
            [0.7, 0.9, 1.0, 0.4],
            [0.6, 0.5, 0.4, 1.0],
        ]
    )
    return pd.DataFrame(data, index=symbols, columns=symbols)  # type: ignore[arg-type]


@pytest.fixture
def sample_correlation_result(
    sample_correlation_matrix: pd.DataFrame,
) -> CorrelationResult:
    """Create a sample CorrelationResult."""
    return CorrelationResult(
        symbols=["AAPL", "GOOGL", "MSFT", "AMZN"],
        correlation_matrix=sample_correlation_matrix,
        period="1Y",
        method="pearson",
    )


@pytest.fixture
def heatmap_chart(sample_correlation_matrix: pd.DataFrame) -> HeatmapChart:
    """Create a HeatmapChart instance."""
    return HeatmapChart(sample_correlation_matrix)


# =============================================================================
# HeatmapChart Initialization Tests
# =============================================================================


class TestHeatmapChartInit:
    """Tests for HeatmapChart initialization."""

    def test_正常系_DataFrameで初期化(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """DataFrameで初期化できることを確認。"""
        chart = HeatmapChart(sample_correlation_matrix)
        assert chart.figure is None
        assert chart.config is not None

    def test_正常系_CorrelationResultで初期化(
        self, sample_correlation_result: CorrelationResult
    ) -> None:
        """CorrelationResultで初期化できることを確認。"""
        chart = HeatmapChart(sample_correlation_result)
        assert chart.figure is None
        assert chart._symbols == ["AAPL", "GOOGL", "MSFT", "AMZN"]
        assert chart._method == "pearson"

    def test_正常系_カスタム設定で初期化(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """カスタム設定で初期化できることを確認。"""
        config = ChartConfig(title="Correlation Heatmap", theme=ChartTheme.DARK)
        chart = HeatmapChart(
            sample_correlation_matrix,
            config,
            show_values=False,
            value_format=".3f",
        )
        assert chart.config.title == "Correlation Heatmap"
        assert chart.config.theme == ChartTheme.DARK

    def test_正常系_カスタムカラースケール(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """カスタムカラースケールで初期化できることを確認。"""
        colorscale = [[0, "blue"], [0.5, "white"], [1, "red"]]
        chart = HeatmapChart(sample_correlation_matrix, colorscale=colorscale)
        chart.build()
        assert chart.figure is not None


# =============================================================================
# HeatmapChart Build Tests
# =============================================================================


class TestHeatmapChartBuild:
    """Tests for HeatmapChart.build method."""

    def test_正常系_buildでfigureが作成される(
        self, heatmap_chart: HeatmapChart
    ) -> None:
        """build()でfigureが作成されることを確認。"""
        heatmap_chart.build()
        assert heatmap_chart.figure is not None
        assert isinstance(heatmap_chart.figure, go.Figure)

    def test_正常系_buildはメソッドチェーン可能(
        self, heatmap_chart: HeatmapChart
    ) -> None:
        """build()がselfを返すことを確認。"""
        result = heatmap_chart.build()
        assert result is heatmap_chart

    def test_正常系_ヒートマップトレースが含まれる(
        self, heatmap_chart: HeatmapChart
    ) -> None:
        """ヒートマップのトレースが含まれることを確認。"""
        heatmap_chart.build()
        traces = heatmap_chart.figure.data  # type: ignore[union-attr]
        heatmap_traces = [t for t in traces if isinstance(t, go.Heatmap)]
        assert len(heatmap_traces) == 1

    def test_正常系_カラースケールがマイナス1から1(
        self, heatmap_chart: HeatmapChart
    ) -> None:
        """カラースケールが-1から1の範囲であることを確認。"""
        heatmap_chart.build()
        heatmap_trace = heatmap_chart.figure.data[0]  # type: ignore[union-attr]
        assert heatmap_trace.zmin == -1
        assert heatmap_trace.zmax == 1


class TestHeatmapChartAnnotations:
    """Tests for HeatmapChart annotations."""

    def test_正常系_値が表示される(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """相関係数値が表示されることを確認。"""
        chart = HeatmapChart(sample_correlation_matrix, show_values=True)
        chart.build()
        layout = chart.figure.layout  # type: ignore[union-attr]
        assert layout.annotations is not None
        assert len(layout.annotations) == 16  # 4x4 matrix

    def test_正常系_値のフォーマット(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """相関係数値のフォーマットが適用されることを確認。"""
        chart = HeatmapChart(
            sample_correlation_matrix, show_values=True, value_format=".1f"
        )
        chart.build()
        layout = chart.figure.layout  # type: ignore[union-attr]
        # Check that at least one annotation text matches format
        annotation_texts = [ann.text for ann in layout.annotations]
        assert any(
            text in ["1.0", "0.8", "0.7", "0.6", "0.9", "0.5", "0.4"]
            for text in annotation_texts
        )

    def test_正常系_値非表示(self, sample_correlation_matrix: pd.DataFrame) -> None:
        """相関係数値を非表示にできることを確認。"""
        chart = HeatmapChart(sample_correlation_matrix, show_values=False)
        chart.build()
        layout = chart.figure.layout  # type: ignore[union-attr]
        # Annotations should be None or empty when show_values=False
        assert layout.annotations is None or len(layout.annotations) == 0


class TestHeatmapChartTheme:
    """Tests for HeatmapChart theme application."""

    def test_正常系_ライトテーマが適用される(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """ライトテーマが正しく適用されることを確認。"""
        config = ChartConfig(theme=ChartTheme.LIGHT)
        chart = HeatmapChart(sample_correlation_matrix, config)
        chart.build()
        layout = chart.figure.layout  # type: ignore[union-attr]
        assert layout.paper_bgcolor == "#FFFFFF"

    def test_正常系_ダークテーマが適用される(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """ダークテーマが正しく適用されることを確認。"""
        config = ChartConfig(theme=ChartTheme.DARK)
        chart = HeatmapChart(sample_correlation_matrix, config)
        chart.build()
        layout = chart.figure.layout  # type: ignore[union-attr]
        assert layout.paper_bgcolor == "#1E1E1E"


# =============================================================================
# HeatmapChart Export Tests
# =============================================================================


class TestHeatmapChartExport:
    """Tests for HeatmapChart export functionality."""

    def test_正常系_PNG保存(self, heatmap_chart: HeatmapChart, tmp_path: Path) -> None:
        """PNG形式で保存できることを確認。"""
        output_path = tmp_path / "heatmap.png"
        heatmap_chart.build()

        with patch("plotly.io.write_image") as mock_write:
            heatmap_chart.save(output_path)
            mock_write.assert_called_once()

    def test_正常系_SVG保存(self, heatmap_chart: HeatmapChart, tmp_path: Path) -> None:
        """SVG形式で保存できることを確認。"""
        output_path = tmp_path / "heatmap.svg"
        heatmap_chart.build()

        with patch("plotly.io.write_image") as mock_write:
            heatmap_chart.save(output_path)
            mock_write.assert_called_once()

    def test_正常系_HTML保存(self, heatmap_chart: HeatmapChart, tmp_path: Path) -> None:
        """HTML形式で保存できることを確認。"""
        output_path = tmp_path / "heatmap.html"
        heatmap_chart.build()

        with patch.object(heatmap_chart.figure, "write_html") as mock_write:
            heatmap_chart.save(output_path)
            mock_write.assert_called_once()


# =============================================================================
# Edge Cases
# =============================================================================


class TestHeatmapChartEdgeCases:
    """Tests for edge cases in HeatmapChart."""

    def test_正常系_空のDataFrame(self) -> None:
        """空のDataFrameでもエラーにならないことを確認。"""
        empty_df = pd.DataFrame()
        chart = HeatmapChart(empty_df)
        chart.build()
        assert chart.figure is not None

    def test_正常系_NaN値を含む行列(self) -> None:
        """NaN値を含む相関行列でも動作することを確認。"""
        data = np.array(
            [
                [1.0, 0.5, np.nan],
                [0.5, 1.0, 0.3],
                [np.nan, 0.3, 1.0],
            ]
        )
        df = pd.DataFrame(
            data,
            index=["A", "B", "C"],  # type: ignore[arg-type]
            columns=["A", "B", "C"],  # type: ignore[arg-type]
        )
        chart = HeatmapChart(df, show_values=True)
        chart.build()
        assert chart.figure is not None

    def test_正常系_負の相関値を含む行列(self) -> None:
        """負の相関値を含む相関行列が正しく表示されることを確認。"""
        data = np.array(
            [
                [1.0, -0.8, 0.5],
                [-0.8, 1.0, -0.3],
                [0.5, -0.3, 1.0],
            ]
        )
        df = pd.DataFrame(
            data,
            index=["A", "B", "C"],  # type: ignore[arg-type]
            columns=["A", "B", "C"],  # type: ignore[arg-type]
        )
        chart = HeatmapChart(df)
        chart.build()
        heatmap_trace = chart.figure.data[0]  # type: ignore[union-attr]
        # Check that negative values are preserved
        assert np.min(heatmap_trace.z) < 0

    def test_正常系_2x2の最小行列(self) -> None:
        """2x2の最小相関行列でも動作することを確認。"""
        data = np.array([[1.0, 0.5], [0.5, 1.0]])
        df = pd.DataFrame(
            data,
            index=["A", "B"],  # type: ignore[arg-type]
            columns=["A", "B"],  # type: ignore[arg-type]
        )
        chart = HeatmapChart(df)
        chart.build()
        assert chart.figure is not None

    def test_正常系_大きな行列(self) -> None:
        """大きな相関行列でも動作することを確認。"""
        n = 20
        np.random.seed(42)
        data = np.random.rand(n, n)
        # Make it symmetric
        data = (data + data.T) / 2
        # Set diagonal to 1
        np.fill_diagonal(data, 1.0)
        symbols = [f"SYM{i}" for i in range(n)]
        df = pd.DataFrame(
            data,
            index=symbols,  # type: ignore[arg-type]
            columns=symbols,  # type: ignore[arg-type]
        )
        chart = HeatmapChart(df)
        chart.build()
        assert chart.figure is not None
