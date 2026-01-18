"""Unit tests for Chart API module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from market_analysis.api.chart import Chart

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Create sample OHLCV DataFrame for testing."""
    dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
    np.random.seed(42)
    base_price = 100
    prices = base_price + np.cumsum(np.random.randn(50))

    return pd.DataFrame(
        {
            "Open": prices + np.random.rand(50),
            "High": prices + np.random.rand(50) + 1,
            "Low": prices - np.random.rand(50) - 1,
            "Close": prices,
            "Volume": np.random.randint(1000, 10000, 50),
        },
        index=dates,
    )


@pytest.fixture
def sample_close_only_df() -> pd.DataFrame:
    """Create sample DataFrame with only Close column."""
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    np.random.seed(42)
    return pd.DataFrame(
        {"Close": np.random.rand(30) * 100 + 100},
        index=dates,
    )


@pytest.fixture
def sample_correlation_matrix() -> pd.DataFrame:
    """Create sample correlation matrix for testing."""
    np.random.seed(42)
    symbols = pd.Index(["AAPL", "GOOGL", "MSFT"])
    data = np.random.rand(3, 3)
    # Make it symmetric
    data = (data + data.T) / 2
    # Set diagonal to 1
    np.fill_diagonal(data, 1)
    return pd.DataFrame(data, index=symbols, columns=symbols)


@pytest.fixture
def chart(sample_ohlcv_df: pd.DataFrame) -> Chart:
    """Create a Chart instance with sample data."""
    return Chart(sample_ohlcv_df, title="Test Chart")


@pytest.fixture
def chart_with_figure(sample_ohlcv_df: pd.DataFrame) -> Chart:
    """Create a Chart instance with a generated figure."""
    chart = Chart(sample_ohlcv_df, title="Test Chart")
    chart.price_chart()
    return chart


# =============================================================================
# Chart Initialization Tests
# =============================================================================


class TestChartInit:
    """Tests for Chart.__init__ method."""

    def test_正常系_デフォルト初期化(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Chartがデフォルト値で初期化されることを確認。"""
        chart = Chart(sample_ohlcv_df)
        assert chart.title is None
        assert chart.data is sample_ohlcv_df

    def test_正常系_タイトル付きで初期化(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """タイトル付きでChartを初期化できることを確認。"""
        chart = Chart(sample_ohlcv_df, title="AAPL Price Chart")
        assert chart.title == "AAPL Price Chart"

    def test_正常系_OHLCカラムなしでも警告のみ(
        self, sample_close_only_df: pd.DataFrame
    ) -> None:
        """OHLCカラムがなくても初期化でき、警告のみ出ることを確認。"""
        # Should not raise, just log warning
        chart = Chart(sample_close_only_df, title="Test")
        assert chart.data is sample_close_only_df


class TestChartProperties:
    """Tests for Chart properties."""

    def test_正常系_dataプロパティ(
        self, chart: Chart, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """dataプロパティがデータを返すことを確認。"""
        assert chart.data is sample_ohlcv_df

    def test_正常系_titleプロパティ(self, chart: Chart) -> None:
        """titleプロパティがタイトルを返すことを確認。"""
        assert chart.title == "Test Chart"


# =============================================================================
# Price Chart Tests
# =============================================================================


class TestPriceChart:
    """Tests for Chart.price_chart method."""

    def test_正常系_基本的なプライスチャート作成(self, chart: Chart) -> None:
        """基本的なプライスチャートを作成できることを確認。"""
        fig = chart.price_chart()
        assert isinstance(fig, go.Figure)

    def test_正常系_カスタムカラム指定(self, chart: Chart) -> None:
        """カスタムカラムでプライスチャートを作成できることを確認。"""
        fig = chart.price_chart(column="Open")
        assert isinstance(fig, go.Figure)

    def test_正常系_サイズ指定(self, chart: Chart) -> None:
        """カスタムサイズでプライスチャートを作成できることを確認。"""
        fig = chart.price_chart(width=800, height=400)
        assert isinstance(fig, go.Figure)
        assert fig.layout.width == 800
        assert fig.layout.height == 400

    def test_正常系_SMAオーバーレイ付き(self, chart: Chart) -> None:
        """SMAオーバーレイ付きでプライスチャートを作成できることを確認。"""
        fig = chart.price_chart(overlays=["SMA_20"])
        assert isinstance(fig, go.Figure)
        # Should have price trace + SMA trace (+ optional volume)
        trace_count = len(list(fig.data))
        assert trace_count >= 2

    def test_正常系_複数オーバーレイ付き(self, chart: Chart) -> None:
        """複数のオーバーレイ付きでプライスチャートを作成できることを確認。"""
        fig = chart.price_chart(overlays=["SMA_20", "EMA_50"])
        assert isinstance(fig, go.Figure)
        # Should have price trace + 2 indicator traces (+ optional volume)
        trace_count = len(list(fig.data))
        assert trace_count >= 3

    def test_正常系_ボリンジャーバンドオーバーレイ(self, chart: Chart) -> None:
        """ボリンジャーバンドオーバーレイ付きでプライスチャートを作成できることを確認。"""
        fig = chart.price_chart(overlays=["BB_20"])
        assert isinstance(fig, go.Figure)
        # BB adds 3 traces (upper, middle, lower)
        trace_count = len(list(fig.data))
        assert trace_count >= 4

    def test_異常系_存在しないカラム指定(self, chart: Chart) -> None:
        """存在しないカラムを指定するとValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="Column 'NonExistent' not found"):
            chart.price_chart(column="NonExistent")

    def test_正常系_小文字カラム名でプライスチャート作成(self) -> None:
        """小文字カラム名（YFinanceフォーマット）でプライスチャートを作成できることを確認。

        Issue #316: YFinanceから取得したデータは小文字カラム名（close）を使用するため、
        デフォルトの'Close'だとValueErrorが発生する問題への対応。
        """
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        np.random.seed(42)
        # YFinance形式：小文字カラム名
        df_lowercase = pd.DataFrame(
            {
                "open": np.random.rand(30) * 10 + 100,
                "high": np.random.rand(30) * 10 + 110,
                "low": np.random.rand(30) * 10 + 90,
                "close": np.random.rand(30) * 10 + 100,
                "volume": np.random.randint(1000, 10000, 30),
            },
            index=dates,
        )
        chart = Chart(df_lowercase, title="NVDA")
        # デフォルト引数（column='Close'）で呼び出しても動作すること
        fig = chart.price_chart()
        assert isinstance(fig, go.Figure)

    def test_正常系_小文字カラム名でオーバーレイ付きチャート作成(self) -> None:
        """小文字カラム名でオーバーレイ付きプライスチャートを作成できることを確認。

        Issue #316 リグレッションテスト：再現手順と同じ条件でエラーが発生しないことを確認。
        """
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        np.random.seed(42)
        df_lowercase = pd.DataFrame(
            {
                "open": np.random.rand(50) * 10 + 100,
                "high": np.random.rand(50) * 10 + 110,
                "low": np.random.rand(50) * 10 + 90,
                "close": np.random.rand(50) * 10 + 100,
                "volume": np.random.randint(1000, 10000, 50),
            },
            index=dates,
        )
        chart = Chart(df_lowercase, title="NVDA")
        # Issue #316 の再現手順と同じ
        fig = chart.price_chart(overlays=["EMA_20", "EMA_50"])
        assert isinstance(fig, go.Figure)

    def test_正常系_無効なオーバーレイは無視される(self, chart: Chart) -> None:
        """無効なオーバーレイフォーマットは無視されることを確認。"""
        # Should not raise, just log warning
        fig = chart.price_chart(overlays=["INVALID_OVERLAY", "SMA"])
        assert isinstance(fig, go.Figure)

    def test_正常系_未対応の指標タイプは無視される(self, chart: Chart) -> None:
        """未対応の指標タイプは無視されることを確認。"""
        # Should not raise, just log warning
        fig = chart.price_chart(overlays=["RSI_14"])
        assert isinstance(fig, go.Figure)


# =============================================================================
# Correlation Heatmap Tests
# =============================================================================


class TestCorrelationHeatmap:
    """Tests for Chart.correlation_heatmap static method."""

    def test_正常系_基本的なヒートマップ作成(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """基本的な相関ヒートマップを作成できることを確認。"""
        fig = Chart.correlation_heatmap(sample_correlation_matrix)
        assert isinstance(fig, go.Figure)

    def test_正常系_カスタムタイトル(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """カスタムタイトルでヒートマップを作成できることを確認。"""
        fig = Chart.correlation_heatmap(
            sample_correlation_matrix, title="Asset Correlations"
        )
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == "Asset Correlations"

    def test_正常系_カスタムサイズ(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """カスタムサイズでヒートマップを作成できることを確認。"""
        fig = Chart.correlation_heatmap(
            sample_correlation_matrix, width=600, height=600
        )
        assert isinstance(fig, go.Figure)
        assert fig.layout.width == 600
        assert fig.layout.height == 600

    def test_異常系_空の相関行列でValueError(self) -> None:
        """空の相関行列でValueErrorが発生することを確認。"""
        empty_matrix = pd.DataFrame()
        with pytest.raises(ValueError, match="Correlation matrix is empty"):
            Chart.correlation_heatmap(empty_matrix)

    def test_正常系_静的メソッドとして呼び出し(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """静的メソッドとして呼び出せることを確認。"""
        # Can be called without Chart instance
        fig = Chart.correlation_heatmap(sample_correlation_matrix)
        assert isinstance(fig, go.Figure)


# =============================================================================
# Save Tests
# =============================================================================


class TestSave:
    """Tests for Chart.save method."""

    def test_正常系_PNG保存(self, chart_with_figure: Chart, tmp_path: Path) -> None:
        """PNG形式で保存できることを確認。"""
        output_path = tmp_path / "test_chart.png"

        with patch("plotly.io.write_image") as mock_write:
            chart_with_figure.save(output_path)
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert call_args.kwargs["format"] == "png"

    def test_正常系_SVG保存(self, chart_with_figure: Chart, tmp_path: Path) -> None:
        """SVG形式で保存できることを確認。"""
        output_path = tmp_path / "test_chart.svg"

        with patch("plotly.io.write_image") as mock_write:
            chart_with_figure.save(output_path)
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert call_args.kwargs["format"] == "svg"

    def test_正常系_HTML保存(self, chart_with_figure: Chart, tmp_path: Path) -> None:
        """HTML形式で保存できることを確認。"""
        output_path = tmp_path / "test_chart.html"

        # _figureにwrite_htmlメソッドをモック
        chart_with_figure._figure = MagicMock()
        chart_with_figure.save(output_path)
        chart_with_figure._figure.write_html.assert_called_once()

    def test_正常系_フォーマット明示指定(
        self, chart_with_figure: Chart, tmp_path: Path
    ) -> None:
        """フォーマットを明示的に指定できることを確認。"""
        output_path = tmp_path / "test_chart.xyz"

        with patch("plotly.io.write_image") as mock_write:
            chart_with_figure.save(output_path, format="png")
            mock_write.assert_called_once()

    def test_正常系_スケール指定(
        self, chart_with_figure: Chart, tmp_path: Path
    ) -> None:
        """スケールを指定できることを確認。"""
        output_path = tmp_path / "test_chart.png"

        with patch("plotly.io.write_image") as mock_write:
            chart_with_figure.save(output_path, scale=3)
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert call_args.kwargs["scale"] == 3

    def test_異常系_チャート未生成でRuntimeError(
        self, chart: Chart, tmp_path: Path
    ) -> None:
        """チャート未生成でsave()を呼ぶとRuntimeErrorが発生することを確認。"""
        with pytest.raises(RuntimeError, match="No chart to save"):
            chart.save(tmp_path / "test.png")

    def test_異常系_未知の拡張子でValueError(
        self, chart_with_figure: Chart, tmp_path: Path
    ) -> None:
        """未知の拡張子でValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="Cannot infer format"):
            chart_with_figure.save(tmp_path / "test.unknown")

    def test_異常系_未対応フォーマットでValueError(
        self, chart_with_figure: Chart, tmp_path: Path
    ) -> None:
        """未対応フォーマット指定でValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="Unsupported format"):
            chart_with_figure.save(tmp_path / "test.xyz", format="xyz")  # type: ignore[arg-type]

    def test_正常系_親ディレクトリ自動作成(
        self, chart_with_figure: Chart, tmp_path: Path
    ) -> None:
        """親ディレクトリが自動作成されることを確認。"""
        output_path = tmp_path / "nested" / "dir" / "test_chart.html"

        chart_with_figure._figure = MagicMock()
        chart_with_figure.save(output_path)

        assert output_path.parent.exists()


# =============================================================================
# Show Tests
# =============================================================================


class TestShow:
    """Tests for Chart.show method."""

    def test_正常系_showが呼び出せる(self, chart_with_figure: Chart) -> None:
        """show()が呼び出せることを確認。"""
        chart_with_figure._figure = MagicMock()
        chart_with_figure.show()
        chart_with_figure._figure.show.assert_called_once()

    def test_異常系_チャート未生成でRuntimeError(self, chart: Chart) -> None:
        """チャート未生成でshow()を呼ぶとRuntimeErrorが発生することを確認。"""
        with pytest.raises(RuntimeError, match="No chart to show"):
            chart.show()


# =============================================================================
# Integration Tests
# =============================================================================


class TestChartIntegration:
    """Integration tests for Chart class."""

    def test_正常系_チャート作成からファイル保存までのフロー(
        self, sample_ohlcv_df: pd.DataFrame, tmp_path: Path
    ) -> None:
        """チャート作成からファイル保存までの一連のフローを確認。"""
        chart = Chart(sample_ohlcv_df, title="AAPL")
        fig = chart.price_chart(overlays=["SMA_20", "EMA_50"])

        assert isinstance(fig, go.Figure)

        output_path = tmp_path / "output.html"
        chart.save(output_path)
        # Note: HTML write is mocked in individual tests,
        # but here we verify the method doesn't crash
        # (actual file write depends on plotly availability)

    def test_正常系_相関ヒートマップのスタンドアロン使用(
        self, sample_correlation_matrix: pd.DataFrame
    ) -> None:
        """相関ヒートマップをスタンドアロンで使用できることを確認。"""
        # No need for Chart instance with data
        fig = Chart.correlation_heatmap(
            sample_correlation_matrix, title="Correlation Matrix", width=800, height=800
        )
        assert isinstance(fig, go.Figure)


class TestChartImport:
    """Tests for Chart class import."""

    def test_正常系_パッケージからインポート可能(self) -> None:
        """パッケージからChartクラスをインポートできることを確認。"""
        from market_analysis import Chart as ImportedChart

        assert ImportedChart is Chart

    def test_正常系_apiモジュールからインポート可能(self) -> None:
        """apiモジュールからChartクラスをインポートできることを確認。"""
        from market_analysis.api import Chart as ApiChart

        assert ApiChart is Chart
