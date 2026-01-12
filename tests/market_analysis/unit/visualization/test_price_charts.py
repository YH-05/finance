"""Unit tests for price_charts module."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import plotly.graph_objects as go
import pytest

from market_analysis.visualization.charts import ChartConfig, ChartTheme
from market_analysis.visualization.price_charts import (
    CandlestickChart,
    IndicatorOverlay,
    LineChart,
    PriceChartData,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Create a sample OHLCV DataFrame."""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    return pd.DataFrame(
        {
            "Open": [100 + i * 0.5 for i in range(30)],
            "High": [101 + i * 0.5 for i in range(30)],
            "Low": [99 + i * 0.5 for i in range(30)],
            "Close": [100.5 + i * 0.5 for i in range(30)],
            "Volume": [1000000 + i * 10000 for i in range(30)],
        },
        index=dates,
    )


@pytest.fixture
def price_data(sample_ohlcv_df: pd.DataFrame) -> PriceChartData:
    """Create a PriceChartData instance."""
    return PriceChartData(df=sample_ohlcv_df, symbol="TEST")


@pytest.fixture
def candlestick_chart(price_data: PriceChartData) -> CandlestickChart:
    """Create a CandlestickChart instance."""
    return CandlestickChart(price_data)


@pytest.fixture
def line_chart(price_data: PriceChartData) -> LineChart:
    """Create a LineChart instance."""
    return LineChart(price_data)


# =============================================================================
# PriceChartData Tests
# =============================================================================


class TestPriceChartData:
    """Tests for PriceChartData dataclass."""

    def test_正常系_データ初期化(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """データが正しく初期化されることを確認。"""
        data = PriceChartData(df=sample_ohlcv_df, symbol="AAPL")
        assert data.symbol == "AAPL"
        assert len(data.df) == 30
        assert data.start_date is None
        assert data.end_date is None

    def test_正常系_日付フィルタリング(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """日付範囲でフィルタリングできることを確認。"""
        data = PriceChartData(
            df=sample_ohlcv_df,
            symbol="TEST",
            start_date="2024-01-10",
            end_date="2024-01-20",
        )
        filtered = data.get_filtered_data()
        assert len(filtered) == 11  # 10日から20日まで
        assert filtered.index.min() >= pd.Timestamp("2024-01-10")  # type: ignore[operator]
        assert filtered.index.max() <= pd.Timestamp("2024-01-20")  # type: ignore[operator]

    def test_正常系_開始日のみフィルタリング(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """開始日のみでフィルタリングできることを確認。"""
        data = PriceChartData(
            df=sample_ohlcv_df,
            symbol="TEST",
            start_date="2024-01-20",
        )
        filtered = data.get_filtered_data()
        assert filtered.index.min() >= pd.Timestamp("2024-01-20")  # type: ignore[operator]

    def test_正常系_終了日のみフィルタリング(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """終了日のみでフィルタリングできることを確認。"""
        data = PriceChartData(
            df=sample_ohlcv_df,
            symbol="TEST",
            end_date="2024-01-10",
        )
        filtered = data.get_filtered_data()
        assert filtered.index.max() <= pd.Timestamp("2024-01-10")  # type: ignore[operator]

    def test_正常系_datetimeでフィルタリング(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """datetime型で日付フィルタリングできることを確認。"""
        data = PriceChartData(
            df=sample_ohlcv_df,
            symbol="TEST",
            start_date=datetime(2024, 1, 15),
        )
        filtered = data.get_filtered_data()
        assert filtered.index.min() >= pd.Timestamp("2024-01-15")  # type: ignore[operator]

    def test_異常系_必須カラム欠損でValueError(self) -> None:
        """必須カラム（OHLC）が欠損している場合にValueErrorが発生することを確認。"""
        # Closeカラムが欠損
        df_missing_close = pd.DataFrame(
            {
                "Open": [100, 101],
                "High": [102, 103],
                "Low": [99, 100],
                "Volume": [1000, 2000],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            PriceChartData(df=df_missing_close, symbol="TEST")

    def test_異常系_複数カラム欠損でValueError(self) -> None:
        """複数の必須カラムが欠損している場合にValueErrorが発生することを確認。"""
        df_missing_multiple = pd.DataFrame(
            {
                "Open": [100, 101],
                "Volume": [1000, 2000],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            PriceChartData(df=df_missing_multiple, symbol="TEST")

    def test_異常系_日付範囲不正でValueError(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """start_dateがend_dateより後の場合にValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="start_date.*must be before end_date"):
            PriceChartData(
                df=sample_ohlcv_df,
                symbol="TEST",
                start_date="2024-01-20",
                end_date="2024-01-10",
            )

    def test_正常系_Volumeなしでも初期化可能(self) -> None:
        """Volume列がなくても初期化できることを確認（OHLCのみ必須）。"""
        df_no_volume = pd.DataFrame(
            {
                "Open": [100, 101],
                "High": [102, 103],
                "Low": [99, 100],
                "Close": [101, 102],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )
        data = PriceChartData(df=df_no_volume, symbol="TEST")
        assert len(data.df) == 2


# =============================================================================
# IndicatorOverlay Tests
# =============================================================================


class TestIndicatorOverlay:
    """Tests for IndicatorOverlay dataclass."""

    def test_正常系_デフォルト値で初期化(self) -> None:
        """デフォルト値で初期化されることを確認。"""
        overlay = IndicatorOverlay(indicator_type="sma")
        assert overlay.indicator_type == "sma"
        assert overlay.params == {}
        assert overlay.color is None
        assert overlay.name is None

    def test_正常系_パラメータ付きで初期化(self) -> None:
        """パラメータ付きで初期化されることを確認。"""
        overlay = IndicatorOverlay(
            indicator_type="sma",
            params={"window": 20},
            color="#FF0000",
            name="Custom SMA",
        )
        assert overlay.params["window"] == 20
        assert overlay.color == "#FF0000"
        assert overlay.name == "Custom SMA"


# =============================================================================
# CandlestickChart Tests
# =============================================================================


class TestCandlestickChart:
    """Tests for CandlestickChart class."""

    def test_正常系_初期化(self, candlestick_chart: CandlestickChart) -> None:
        """CandlestickChartが正しく初期化されることを確認。"""
        assert candlestick_chart.figure is None
        assert candlestick_chart.config is not None

    def test_正常系_buildでfigureが作成される(
        self, candlestick_chart: CandlestickChart
    ) -> None:
        """build()でfigureが作成されることを確認。"""
        candlestick_chart.build()
        assert candlestick_chart.figure is not None
        assert isinstance(candlestick_chart.figure, go.Figure)

    def test_正常系_buildはメソッドチェーン可能(
        self, candlestick_chart: CandlestickChart
    ) -> None:
        """build()がselfを返すことを確認。"""
        result = candlestick_chart.build()
        assert result is candlestick_chart

    def test_正常系_ローソク足トレースが含まれる(
        self, candlestick_chart: CandlestickChart
    ) -> None:
        """ローソク足のトレースが含まれることを確認。"""
        candlestick_chart.build()
        traces = candlestick_chart.figure.data  # type: ignore[union-attr]
        candlestick_traces = [t for t in traces if isinstance(t, go.Candlestick)]
        assert len(candlestick_traces) == 1

    def test_正常系_出来高トレースが含まれる(
        self, candlestick_chart: CandlestickChart
    ) -> None:
        """出来高のバートレースが含まれることを確認。"""
        candlestick_chart.build()
        traces = candlestick_chart.figure.data  # type: ignore[union-attr]
        bar_traces = [t for t in traces if isinstance(t, go.Bar)]
        assert len(bar_traces) == 1

    def test_正常系_出来高非表示(self, price_data: PriceChartData) -> None:
        """出来高を非表示にできることを確認。"""
        chart = CandlestickChart(price_data, show_volume=False)
        chart.build()
        traces = chart.figure.data  # type: ignore[union-attr]
        bar_traces = [t for t in traces if isinstance(t, go.Bar)]
        assert len(bar_traces) == 0

    def test_正常系_ダークテーマが適用される(self, price_data: PriceChartData) -> None:
        """ダークテーマが正しく適用されることを確認。"""
        config = ChartConfig(theme=ChartTheme.DARK, title="Dark Theme Chart")
        chart = CandlestickChart(price_data, config).build()
        layout = chart.figure.layout  # type: ignore[union-attr]
        assert layout.paper_bgcolor == "#1E1E1E"


class TestCandlestickChartIndicators:
    """Tests for CandlestickChart indicator methods."""

    def test_正常系_SMAオーバーレイ追加(
        self, candlestick_chart: CandlestickChart
    ) -> None:
        """SMAオーバーレイを追加できることを確認。"""
        candlestick_chart.add_sma(20).build()
        traces = candlestick_chart.figure.data  # type: ignore[union-attr]
        scatter_traces = [t for t in traces if isinstance(t, go.Scatter)]
        assert any("SMA" in (t.name or "") for t in scatter_traces)

    def test_正常系_EMAオーバーレイ追加(
        self, candlestick_chart: CandlestickChart
    ) -> None:
        """EMAオーバーレイを追加できることを確認。"""
        candlestick_chart.add_ema(12).build()
        traces = candlestick_chart.figure.data  # type: ignore[union-attr]
        scatter_traces = [t for t in traces if isinstance(t, go.Scatter)]
        assert any("EMA" in (t.name or "") for t in scatter_traces)

    def test_正常系_ボリンジャーバンドオーバーレイ追加(
        self, candlestick_chart: CandlestickChart
    ) -> None:
        """ボリンジャーバンドオーバーレイを追加できることを確認。"""
        candlestick_chart.add_bollinger_bands(20, 2.0).build()
        traces = candlestick_chart.figure.data  # type: ignore[union-attr]
        scatter_traces = [t for t in traces if isinstance(t, go.Scatter)]
        bb_traces = [t for t in scatter_traces if "BB" in (t.name or "")]
        assert len(bb_traces) == 3  # Upper, Middle, Lower

    def test_正常系_複数指標追加(self, candlestick_chart: CandlestickChart) -> None:
        """複数の指標を追加できることを確認。"""
        candlestick_chart.add_sma(20).add_sma(50).add_ema(12).build()
        traces = candlestick_chart.figure.data  # type: ignore[union-attr]
        scatter_traces = [t for t in traces if isinstance(t, go.Scatter)]
        assert len(scatter_traces) >= 3

    def test_正常系_カスタムカラー指定(
        self, candlestick_chart: CandlestickChart
    ) -> None:
        """カスタムカラーを指定できることを確認。"""
        candlestick_chart.add_sma(20, color="#FF0000", name="Custom SMA").build()
        traces = candlestick_chart.figure.data  # type: ignore[union-attr]
        sma_trace = next(
            (t for t in traces if isinstance(t, go.Scatter) and t.name == "Custom SMA"),
            None,
        )
        assert sma_trace is not None
        assert sma_trace.line is not None
        assert sma_trace.line.color == "#FF0000"

    def test_正常系_メソッドチェーン(self, candlestick_chart: CandlestickChart) -> None:
        """add_*メソッドがメソッドチェーン可能であることを確認。"""
        result = candlestick_chart.add_sma(20).add_ema(12).add_bollinger_bands()
        assert result is candlestick_chart


class TestCandlestickChartExport:
    """Tests for CandlestickChart export functionality."""

    def test_正常系_PNG保存(
        self, candlestick_chart: CandlestickChart, tmp_path: Path
    ) -> None:
        """PNG形式で保存できることを確認。"""
        output_path = tmp_path / "chart.png"
        candlestick_chart.build()

        with patch("plotly.io.write_image") as mock_write:
            candlestick_chart.save(output_path)
            mock_write.assert_called_once()

    def test_正常系_SVG保存(
        self, candlestick_chart: CandlestickChart, tmp_path: Path
    ) -> None:
        """SVG形式で保存できることを確認。"""
        output_path = tmp_path / "chart.svg"
        candlestick_chart.build()

        with patch("plotly.io.write_image") as mock_write:
            candlestick_chart.save(output_path)
            mock_write.assert_called_once()

    def test_正常系_HTML保存(
        self, candlestick_chart: CandlestickChart, tmp_path: Path
    ) -> None:
        """HTML形式で保存できることを確認。"""
        output_path = tmp_path / "chart.html"
        candlestick_chart.build()

        with patch.object(candlestick_chart.figure, "write_html") as mock_write:
            candlestick_chart.save(output_path)
            mock_write.assert_called_once()


# =============================================================================
# LineChart Tests
# =============================================================================


class TestLineChart:
    """Tests for LineChart class."""

    def test_正常系_初期化(self, line_chart: LineChart) -> None:
        """LineChartが正しく初期化されることを確認。"""
        assert line_chart.figure is None
        assert line_chart.config is not None

    def test_正常系_buildでfigureが作成される(self, line_chart: LineChart) -> None:
        """build()でfigureが作成されることを確認。"""
        line_chart.build()
        assert line_chart.figure is not None
        assert isinstance(line_chart.figure, go.Figure)

    def test_正常系_ラインチャートトレースが含まれる(
        self, line_chart: LineChart
    ) -> None:
        """ラインチャートのトレースが含まれることを確認。"""
        line_chart.build()
        traces = line_chart.figure.data  # type: ignore[union-attr]
        scatter_traces = [
            t for t in traces if isinstance(t, go.Scatter) and t.name == "TEST"
        ]
        assert len(scatter_traces) == 1

    def test_正常系_出来高トレースが含まれる(self, line_chart: LineChart) -> None:
        """出来高のバートレースが含まれることを確認。"""
        line_chart.build()
        traces = line_chart.figure.data  # type: ignore[union-attr]
        bar_traces = [t for t in traces if isinstance(t, go.Bar)]
        assert len(bar_traces) == 1

    def test_正常系_出来高非表示(self, price_data: PriceChartData) -> None:
        """出来高を非表示にできることを確認。"""
        chart = LineChart(price_data, show_volume=False)
        chart.build()
        traces = chart.figure.data  # type: ignore[union-attr]
        bar_traces = [t for t in traces if isinstance(t, go.Bar)]
        assert len(bar_traces) == 0

    def test_正常系_価格カラム指定(self, price_data: PriceChartData) -> None:
        """価格カラムを指定できることを確認。"""
        chart = LineChart(price_data, price_column="Open")
        chart.build()
        assert chart.figure is not None


class TestLineChartIndicators:
    """Tests for LineChart indicator methods."""

    def test_正常系_SMAオーバーレイ追加(self, line_chart: LineChart) -> None:
        """SMAオーバーレイを追加できることを確認。"""
        line_chart.add_sma(20).build()
        traces = line_chart.figure.data  # type: ignore[union-attr]
        scatter_traces = [t for t in traces if isinstance(t, go.Scatter)]
        assert any("SMA" in (t.name or "") for t in scatter_traces)

    def test_正常系_EMAオーバーレイ追加(self, line_chart: LineChart) -> None:
        """EMAオーバーレイを追加できることを確認。"""
        line_chart.add_ema(12).build()
        traces = line_chart.figure.data  # type: ignore[union-attr]
        scatter_traces = [t for t in traces if isinstance(t, go.Scatter)]
        assert any("EMA" in (t.name or "") for t in scatter_traces)

    def test_正常系_ボリンジャーバンドオーバーレイ追加(
        self, line_chart: LineChart
    ) -> None:
        """ボリンジャーバンドオーバーレイを追加できることを確認。"""
        line_chart.add_bollinger_bands(20, 2.0).build()
        traces = line_chart.figure.data  # type: ignore[union-attr]
        scatter_traces = [t for t in traces if isinstance(t, go.Scatter)]
        bb_traces = [t for t in scatter_traces if "BB" in (t.name or "")]
        assert len(bb_traces) == 3


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestPriceChartErrorHandling:
    """Tests for price chart error handling."""

    def test_異常系_CandlestickChart_build前にsave呼び出しでRuntimeError(
        self, price_data: PriceChartData, tmp_path: Path
    ) -> None:
        """build()前にsave()を呼ぶとRuntimeErrorが発生することを確認。"""
        chart = CandlestickChart(price_data)
        output_path = tmp_path / "should_not_exist.png"

        with pytest.raises(RuntimeError, match="Chart not built"):
            chart.save(output_path)

    def test_異常系_CandlestickChart_build前にshow呼び出しでRuntimeError(
        self, price_data: PriceChartData
    ) -> None:
        """build()前にshow()を呼ぶとRuntimeErrorが発生することを確認。"""
        chart = CandlestickChart(price_data)

        with pytest.raises(RuntimeError, match="Chart not built"):
            chart.show()

    def test_異常系_CandlestickChart_build前にto_html呼び出しでRuntimeError(
        self, price_data: PriceChartData
    ) -> None:
        """build()前にto_html()を呼ぶとRuntimeErrorが発生することを確認。"""
        chart = CandlestickChart(price_data)

        with pytest.raises(RuntimeError, match="Chart not built"):
            chart.to_html()

    def test_異常系_LineChart_build前にsave呼び出しでRuntimeError(
        self, price_data: PriceChartData, tmp_path: Path
    ) -> None:
        """build()前にsave()を呼ぶとRuntimeErrorが発生することを確認。"""
        chart = LineChart(price_data)
        output_path = tmp_path / "should_not_exist.png"

        with pytest.raises(RuntimeError, match="Chart not built"):
            chart.save(output_path)

    def test_異常系_LineChart_build前にshow呼び出しでRuntimeError(
        self, price_data: PriceChartData
    ) -> None:
        """build()前にshow()を呼ぶとRuntimeErrorが発生することを確認。"""
        chart = LineChart(price_data)

        with pytest.raises(RuntimeError, match="Chart not built"):
            chart.show()


# =============================================================================
# Edge Cases
# =============================================================================


class TestPriceChartEdgeCases:
    """Tests for edge cases in price charts."""

    def test_正常系_空のデータフレーム(self) -> None:
        """空のデータフレームでもエラーにならないことを確認。"""
        empty_df = pd.DataFrame(
            columns=["Open", "High", "Low", "Close", "Volume"],  # type: ignore[arg-type]
            index=pd.DatetimeIndex([]),
        )
        data = PriceChartData(df=empty_df, symbol="EMPTY")
        chart = CandlestickChart(data)
        chart.build()
        assert chart.figure is not None

    def test_正常系_フィルタリング後に空になるデータ(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """フィルタリング後に空になってもエラーにならないことを確認。"""
        data = PriceChartData(
            df=sample_ohlcv_df,
            symbol="TEST",
            start_date="2025-01-01",  # 将来の日付
        )
        chart = CandlestickChart(data)
        chart.build()
        assert chart.figure is not None

    def test_正常系_Volumeカラムなしでも動作(self) -> None:
        """Volumeカラムがなくても動作することを確認。"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame(
            {
                "Open": [100] * 10,
                "High": [101] * 10,
                "Low": [99] * 10,
                "Close": [100.5] * 10,
            },
            index=dates,
        )
        data = PriceChartData(df=df, symbol="NO_VOLUME")
        chart = CandlestickChart(data)
        chart.build()
        assert chart.figure is not None
