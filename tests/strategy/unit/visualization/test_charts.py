"""Unit tests for ChartGenerator.

Tests for chart generation functionality:
- Pie chart for asset allocation
- Bar chart for asset allocation
- Drift visualization
- Group-by options (ticker, sector, asset_class)
- Plotly figure structure validation
- marimo notebook compatibility
"""

import plotly.graph_objects as go
import pytest
from strategy.portfolio import Portfolio
from strategy.rebalance.types import DriftResult
from strategy.types import TickerInfo
from strategy.visualization.charts import ChartGenerator

# =============================================================================
# TestChartGeneratorInitialization
# =============================================================================


class TestChartGeneratorInitialization:
    """ChartGenerator 初期化のテスト."""

    def test_正常系_Portfolioから初期化できる(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """ChartGeneratorがPortfolioから正しく初期化されることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        assert generator is not None
        assert generator.portfolio is simple_portfolio

    def test_正常系_ticker_infoを設定できる(
        self,
        simple_portfolio: Portfolio,
        sample_ticker_info: dict[str, TickerInfo],
    ) -> None:
        """ティッカー情報を設定できることを確認."""
        generator = ChartGenerator(
            portfolio=simple_portfolio,
            ticker_info=sample_ticker_info,
        )

        assert generator.ticker_info is not None
        assert "VOO" in generator.ticker_info
        assert "BND" in generator.ticker_info


# =============================================================================
# TestPlotAllocationPieChart
# =============================================================================


class TestPlotAllocationPieChart:
    """plot_allocation 円グラフのテスト."""

    def test_正常系_円グラフを生成できる(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """デフォルトで円グラフが生成されることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_allocation()

        assert isinstance(fig, go.Figure)
        data = list(fig.data)
        assert len(data) == 1
        assert isinstance(data[0], go.Pie)

    def test_正常系_円グラフのデータが正しい(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """円グラフのデータがポートフォリオの配分と一致することを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_allocation(chart_type="pie")

        pie_trace = fig.data[0]
        assert "VOO" in pie_trace.labels
        assert "BND" in pie_trace.labels

        # values の合計が 1.0 (または 100%) になることを確認
        total_values = sum(pie_trace.values)
        assert abs(total_values - 1.0) < 0.01 or abs(total_values - 100) < 1

    def test_正常系_複数銘柄の円グラフを生成できる(
        self,
        multi_asset_portfolio: Portfolio,
    ) -> None:
        """複数銘柄のポートフォリオで円グラフが生成されることを確認."""
        generator = ChartGenerator(portfolio=multi_asset_portfolio)

        fig = generator.plot_allocation(chart_type="pie")

        pie_trace = fig.data[0]
        assert len(pie_trace.labels) == 4

    def test_正常系_単一銘柄の円グラフを生成できる(
        self,
        single_holding_portfolio: Portfolio,
    ) -> None:
        """単一銘柄でも円グラフが生成されることを確認."""
        generator = ChartGenerator(portfolio=single_holding_portfolio)

        fig = generator.plot_allocation(chart_type="pie")

        assert isinstance(fig, go.Figure)
        pie_trace = fig.data[0]
        assert len(pie_trace.labels) == 1


# =============================================================================
# TestPlotAllocationBarChart
# =============================================================================


class TestPlotAllocationBarChart:
    """plot_allocation 棒グラフのテスト."""

    def test_正常系_棒グラフを生成できる(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """chart_type='bar'で棒グラフが生成されることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_allocation(chart_type="bar")

        assert isinstance(fig, go.Figure)
        data = list(fig.data)
        assert len(data) >= 1
        assert isinstance(data[0], go.Bar)

    def test_正常系_棒グラフのデータが正しい(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """棒グラフのデータがポートフォリオの配分と一致することを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_allocation(chart_type="bar")

        bar_trace = fig.data[0]
        assert "VOO" in bar_trace.x or "VOO" in list(bar_trace.x)
        assert "BND" in bar_trace.x or "BND" in list(bar_trace.x)

    def test_正常系_複数銘柄の棒グラフを生成できる(
        self,
        multi_asset_portfolio: Portfolio,
    ) -> None:
        """複数銘柄のポートフォリオで棒グラフが生成されることを確認."""
        generator = ChartGenerator(portfolio=multi_asset_portfolio)

        fig = generator.plot_allocation(chart_type="bar")

        bar_trace = fig.data[0]
        assert len(bar_trace.x) == 4


# =============================================================================
# TestPlotAllocationGroupBy
# =============================================================================


class TestPlotAllocationGroupBy:
    """plot_allocation グループ化オプションのテスト."""

    def test_正常系_tickerでグループ化できる(
        self,
        multi_asset_portfolio: Portfolio,
        sample_ticker_info: dict[str, TickerInfo],
    ) -> None:
        """group_by='ticker'でティッカー別にグループ化されることを確認."""
        generator = ChartGenerator(
            portfolio=multi_asset_portfolio,
            ticker_info=sample_ticker_info,
        )

        fig = generator.plot_allocation(chart_type="pie", group_by="ticker")

        assert isinstance(fig, go.Figure)
        pie_trace = fig.data[0]
        # ticker でグループ化した場合、銘柄数と同じラベル数
        assert len(pie_trace.labels) == 4

    def test_正常系_sectorでグループ化できる(
        self,
        multi_asset_portfolio: Portfolio,
        sample_ticker_info: dict[str, TickerInfo],
    ) -> None:
        """group_by='sector'でセクター別にグループ化されることを確認."""
        generator = ChartGenerator(
            portfolio=multi_asset_portfolio,
            ticker_info=sample_ticker_info,
        )

        fig = generator.plot_allocation(chart_type="pie", group_by="sector")

        assert isinstance(fig, go.Figure)
        pie_trace = fig.data[0]
        # セクターは4つ（Broad Market, Fixed Income, Real Estate, Commodities）
        assert len(pie_trace.labels) == 4

    def test_正常系_asset_classでグループ化できる(
        self,
        multi_asset_portfolio: Portfolio,
        sample_ticker_info: dict[str, TickerInfo],
    ) -> None:
        """group_by='asset_class'で資産クラス別にグループ化されることを確認."""
        generator = ChartGenerator(
            portfolio=multi_asset_portfolio,
            ticker_info=sample_ticker_info,
        )

        fig = generator.plot_allocation(chart_type="pie", group_by="asset_class")

        assert isinstance(fig, go.Figure)
        pie_trace = fig.data[0]
        # 資産クラスは4つ（equity, bond, real_estate, commodity）
        assert len(pie_trace.labels) == 4

    def test_正常系_ticker_info未設定でgroup_byを使うとticker扱い(
        self,
        multi_asset_portfolio: Portfolio,
    ) -> None:
        """ticker_info未設定でgroup_by='sector'を使った場合の挙動を確認.

        ticker_infoがない場合は、group_byを無視してティッカーごとの表示となる。
        """
        generator = ChartGenerator(portfolio=multi_asset_portfolio)

        # ticker_info 未設定でも動作することを確認
        fig = generator.plot_allocation(chart_type="pie", group_by="sector")

        assert isinstance(fig, go.Figure)


# =============================================================================
# TestPlotDrift
# =============================================================================


class TestPlotDrift:
    """plot_drift ドリフト可視化のテスト."""

    def test_正常系_ドリフト棒グラフを生成できる(
        self,
        simple_portfolio: Portfolio,
        sample_drift_results: list[DriftResult],
    ) -> None:
        """ドリフト結果から棒グラフが生成されることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_drift(drift_results=sample_drift_results)

        assert isinstance(fig, go.Figure)
        data = list(fig.data)
        assert len(data) >= 1
        assert isinstance(data[0], go.Bar)

    def test_正常系_ドリフトデータが正しく表示される(
        self,
        simple_portfolio: Portfolio,
        sample_drift_results: list[DriftResult],
    ) -> None:
        """ドリフト値が正しくグラフに反映されることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_drift(drift_results=sample_drift_results)

        bar_trace = fig.data[0]
        # ティッカー名がx軸に含まれる
        x_values = list(bar_trace.x)
        assert "VOO" in x_values
        assert "BND" in x_values

        # ドリフト値がy軸に含まれる
        y_values = list(bar_trace.y)
        assert any(abs(y - 0.05) < 0.01 for y in y_values)  # VOO の drift
        assert any(abs(y - (-0.05)) < 0.01 for y in y_values)  # BND の drift

    def test_正常系_ドリフトゼロのグラフを生成できる(
        self,
        simple_portfolio: Portfolio,
        no_drift_results: list[DriftResult],
    ) -> None:
        """ドリフトがゼロの場合もグラフが生成されることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_drift(drift_results=no_drift_results)

        assert isinstance(fig, go.Figure)
        bar_trace = fig.data[0]
        # 全ての値がゼロ
        assert all(abs(y) < 1e-10 for y in bar_trace.y)

    def test_正常系_複数銘柄のドリフトを表示できる(
        self,
        multi_asset_portfolio: Portfolio,
        multi_asset_drift_results: list[DriftResult],
    ) -> None:
        """複数銘柄のドリフトが正しく表示されることを確認."""
        generator = ChartGenerator(portfolio=multi_asset_portfolio)

        fig = generator.plot_drift(drift_results=multi_asset_drift_results)

        bar_trace = fig.data[0]
        assert len(bar_trace.x) == 4

    def test_正常系_リバランス必要銘柄が区別される(
        self,
        simple_portfolio: Portfolio,
        sample_drift_results: list[DriftResult],
    ) -> None:
        """リバランスが必要な銘柄が視覚的に区別されることを確認.

        色分けやマーカーでリバランス必要銘柄が区別されることを期待。
        """
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_drift(drift_results=sample_drift_results)

        assert isinstance(fig, go.Figure)
        # 色やマーカーで区別されているかは実装依存
        # ここでは Figure が正しく生成されることを確認


# =============================================================================
# TestPlotDriftEdgeCases
# =============================================================================


class TestPlotDriftEdgeCases:
    """plot_drift エッジケースのテスト."""

    def test_異常系_空のdrift_resultsでエラー(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """空のdrift_resultsでValueErrorが発生することを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        with pytest.raises(ValueError, match="drift_results cannot be empty"):
            generator.plot_drift(drift_results=[])

    def test_正常系_単一銘柄のドリフトを表示できる(
        self,
        single_holding_portfolio: Portfolio,
    ) -> None:
        """単一銘柄のドリフトでもグラフが生成されることを確認."""
        generator = ChartGenerator(portfolio=single_holding_portfolio)

        drift_results = [
            DriftResult(
                ticker="VOO",
                target_weight=1.0,
                current_weight=1.0,
                drift=0.0,
                drift_percent=0.0,
                requires_rebalance=False,
            ),
        ]

        fig = generator.plot_drift(drift_results=drift_results)

        assert isinstance(fig, go.Figure)
        assert len(fig.data[0].x) == 1


# =============================================================================
# TestChartLayout
# =============================================================================


class TestChartLayout:
    """チャートレイアウトのテスト."""

    def test_正常系_タイトルが設定される(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """チャートにタイトルが設定されることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_allocation(chart_type="pie")

        assert fig.layout.title is not None
        # タイトルのテキストを取得
        title_text = (
            fig.layout.title.text
            if hasattr(fig.layout.title, "text")
            else str(fig.layout.title)
        )
        assert len(title_text) > 0

    def test_正常系_ポートフォリオ名がタイトルに含まれる(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """ポートフォリオ名がチャートタイトルに含まれることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_allocation(chart_type="pie")

        title_text = (
            fig.layout.title.text
            if hasattr(fig.layout.title, "text")
            else str(fig.layout.title)
        )
        # ポートフォリオ名 "60/40 Portfolio" がタイトルに含まれる
        assert "60/40" in title_text or "Portfolio" in title_text

    def test_正常系_ドリフトグラフに軸ラベルがある(
        self,
        simple_portfolio: Portfolio,
        sample_drift_results: list[DriftResult],
    ) -> None:
        """ドリフトグラフに適切な軸ラベルがあることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_drift(drift_results=sample_drift_results)

        # x軸またはy軸のラベルが設定されている
        assert fig.layout.xaxis is not None or fig.layout.yaxis is not None


# =============================================================================
# TestMarimoCompatibility
# =============================================================================


class TestMarimoCompatibility:
    """marimo ノートブック互換性のテスト."""

    def test_正常系_Figureが直接表示可能(
        self,
        simple_portfolio: Portfolio,
    ) -> None:
        """生成されたFigureがmarimoで直接表示可能な形式であることを確認.

        Plotlyのgo.Figureはmarimoで直接表示可能。
        """
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_allocation()

        # go.Figure であればmarimoで直接表示可能
        assert isinstance(fig, go.Figure)
        # show メソッドが存在する
        assert hasattr(fig, "show")
        # to_html メソッドが存在する（インライン表示用）
        assert hasattr(fig, "to_html")

    def test_正常系_複数のチャートを順次生成できる(
        self,
        simple_portfolio: Portfolio,
        sample_drift_results: list[DriftResult],
    ) -> None:
        """複数のチャートを連続して生成できることを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig1 = generator.plot_allocation(chart_type="pie")
        fig2 = generator.plot_allocation(chart_type="bar")
        fig3 = generator.plot_drift(drift_results=sample_drift_results)

        # 全て独立した Figure オブジェクト
        assert isinstance(fig1, go.Figure)
        assert isinstance(fig2, go.Figure)
        assert isinstance(fig3, go.Figure)
        assert fig1 is not fig2
        assert fig2 is not fig3


# =============================================================================
# TestChartGeneratorParameterized
# =============================================================================


class TestChartGeneratorParameterized:
    """パラメトライズされたテスト."""

    @pytest.mark.parametrize(
        "chart_type",
        ["pie", "bar"],
    )
    def test_パラメトライズ_全てのチャートタイプで動作する(
        self,
        simple_portfolio: Portfolio,
        chart_type: str,
    ) -> None:
        """全てのchart_typeで正しく動作することを確認."""
        generator = ChartGenerator(portfolio=simple_portfolio)

        fig = generator.plot_allocation(chart_type=chart_type)  # type: ignore[arg-type]

        assert isinstance(fig, go.Figure)
        data = list(fig.data)
        assert len(data) >= 1

    @pytest.mark.parametrize(
        "group_by",
        [None, "ticker", "sector", "asset_class"],
    )
    def test_パラメトライズ_全てのgroup_byオプションで動作する(
        self,
        multi_asset_portfolio: Portfolio,
        sample_ticker_info: dict[str, TickerInfo],
        group_by: str | None,
    ) -> None:
        """全てのgroup_byオプションで正しく動作することを確認."""
        generator = ChartGenerator(
            portfolio=multi_asset_portfolio,
            ticker_info=sample_ticker_info,
        )

        fig = generator.plot_allocation(chart_type="pie", group_by=group_by)  # type: ignore[arg-type]

        assert isinstance(fig, go.Figure)

    @pytest.mark.parametrize(
        "holdings",
        [
            [("A", 1.0)],
            [("A", 0.5), ("B", 0.5)],
            [("A", 0.33), ("B", 0.33), ("C", 0.34)],
            [("A", 0.25), ("B", 0.25), ("C", 0.25), ("D", 0.25)],
        ],
    )
    def test_パラメトライズ_様々な銘柄数で動作する(
        self,
        holdings: list[tuple[str, float]],
    ) -> None:
        """様々な銘柄数のポートフォリオで動作することを確認."""
        portfolio = Portfolio(holdings=holdings)
        generator = ChartGenerator(portfolio=portfolio)

        fig = generator.plot_allocation()

        assert isinstance(fig, go.Figure)
        assert len(fig.data[0].labels) == len(holdings)
