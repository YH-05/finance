"""Chart generation module for portfolio visualization.

This module provides the ChartGenerator class for creating Plotly charts
that visualize portfolio allocations and drift analysis.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Literal

import plotly.graph_objects as go
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from ..portfolio import Portfolio
    from ..rebalance.types import DriftResult
    from ..types import TickerInfo

logger = get_logger(__name__, module="visualization")


class ChartGenerator:
    """ポートフォリオ可視化用のチャート生成クラス.

    Plotlyを使用して、ポートフォリオの資産配分や
    ドリフト分析の可視化を行う。

    Parameters
    ----------
    portfolio : Portfolio
        可視化対象のポートフォリオ
    ticker_info : dict[str, TickerInfo] | None
        ティッカー情報の辞書（セクター/資産クラス別グループ化に使用）

    Attributes
    ----------
    portfolio : Portfolio
        可視化対象のポートフォリオ
    ticker_info : dict[str, TickerInfo] | None
        ティッカー情報の辞書

    Examples
    --------
    >>> from strategy.portfolio import Portfolio
    >>> portfolio = Portfolio([("VOO", 0.6), ("BND", 0.4)])
    >>> generator = ChartGenerator(portfolio=portfolio)
    >>> fig = generator.plot_allocation()
    >>> fig.show()  # marimoノートブックで直接表示可能
    """

    def __init__(
        self,
        portfolio: Portfolio,
        ticker_info: dict[str, TickerInfo] | None = None,
    ) -> None:
        """Initialize ChartGenerator with portfolio and optional ticker info.

        Parameters
        ----------
        portfolio : Portfolio
            可視化対象のポートフォリオ
        ticker_info : dict[str, TickerInfo] | None
            ティッカー情報の辞書（セクター/資産クラス別グループ化に使用）
        """
        logger.debug(
            "Creating ChartGenerator",
            portfolio_name=portfolio.name,
            holdings_count=len(portfolio),
            has_ticker_info=ticker_info is not None,
        )

        self._portfolio = portfolio
        self._ticker_info = ticker_info

        logger.info(
            "ChartGenerator created",
            portfolio_name=portfolio.name,
            holdings_count=len(portfolio),
        )

    @property
    def portfolio(self) -> Portfolio:
        """可視化対象のポートフォリオを返す.

        Returns
        -------
        Portfolio
            可視化対象のポートフォリオ
        """
        return self._portfolio

    @property
    def ticker_info(self) -> dict[str, TickerInfo] | None:
        """ティッカー情報の辞書を返す.

        Returns
        -------
        dict[str, TickerInfo] | None
            ティッカー情報の辞書。設定されていない場合はNone
        """
        return self._ticker_info

    def plot_allocation(
        self,
        chart_type: Literal["pie", "bar"] = "pie",
        group_by: Literal["ticker", "sector", "asset_class"] | None = None,
        title: str | None = None,
    ) -> go.Figure:
        """資産配分のチャートを生成.

        Parameters
        ----------
        chart_type : Literal["pie", "bar"], default="pie"
            チャートタイプ（"pie": 円グラフ、"bar": 棒グラフ）
        group_by : Literal["ticker", "sector", "asset_class"] | None, default=None
            グループ化の基準。Noneまたは"ticker"の場合はティッカー別
        title : str | None, default=None
            チャートのタイトル。Noneの場合は自動生成

        Returns
        -------
        go.Figure
            Plotlyのチャートオブジェクト

        Examples
        --------
        >>> generator = ChartGenerator(portfolio=portfolio)
        >>> # デフォルトで円グラフ
        >>> fig = generator.plot_allocation()
        >>> # 棒グラフ
        >>> fig = generator.plot_allocation(chart_type="bar")
        >>> # セクター別グループ化
        >>> fig = generator.plot_allocation(group_by="sector")
        """
        logger.debug(
            "Generating allocation chart",
            chart_type=chart_type,
            group_by=group_by,
            title=title,
        )

        # タイトルの自動生成
        if title is None:
            title = self._generate_allocation_title(chart_type, group_by)

        # データの準備
        labels, values = self._prepare_allocation_data(group_by)

        # チャートの生成
        if chart_type == "pie":
            fig = self._create_pie_chart(labels, values, title)
        else:
            fig = self._create_bar_chart(labels, values, title)

        logger.info(
            "Allocation chart generated",
            chart_type=chart_type,
            group_by=group_by,
            data_points=len(labels),
        )

        return fig

    def plot_drift(
        self,
        drift_results: list[DriftResult],
        title: str | None = None,
    ) -> go.Figure:
        """ドリフト分析の棒グラフを生成.

        Parameters
        ----------
        drift_results : list[DriftResult]
            ドリフト分析結果のリスト
        title : str | None, default=None
            チャートのタイトル。Noneの場合は自動生成

        Returns
        -------
        go.Figure
            Plotlyのチャートオブジェクト

        Raises
        ------
        ValueError
            drift_resultsが空の場合

        Examples
        --------
        >>> from strategy.rebalance.types import DriftResult
        >>> drift_results = [
        ...     DriftResult("VOO", 0.6, 0.65, 0.05, 8.33, True),
        ...     DriftResult("BND", 0.4, 0.35, -0.05, -12.5, True),
        ... ]
        >>> generator = ChartGenerator(portfolio=portfolio)
        >>> fig = generator.plot_drift(drift_results=drift_results)
        """
        logger.debug(
            "Generating drift chart",
            drift_count=len(drift_results),
            title=title,
        )

        if not drift_results:
            logger.error("Drift chart generation failed", reason="empty drift_results")
            msg = "drift_results cannot be empty"
            raise ValueError(msg)

        # タイトルの自動生成
        if title is None:
            portfolio_name = self._portfolio.name or "Portfolio"
            title = f"{portfolio_name} - Drift Analysis"

        # データの準備
        tickers = [result.ticker for result in drift_results]
        drifts = [result.drift for result in drift_results]
        requires_rebalance = [result.requires_rebalance for result in drift_results]

        # 色の設定（リバランス必要な銘柄を強調）
        colors = [
            "rgba(239, 85, 59, 0.8)" if req else "rgba(99, 110, 250, 0.8)"
            for req in requires_rebalance
        ]

        # チャートの生成
        fig = go.Figure(
            data=[
                go.Bar(
                    x=tickers,
                    y=drifts,
                    marker_color=colors,
                    text=[f"{d:.1%}" for d in drifts],
                    textposition="outside",
                )
            ]
        )

        # レイアウトの設定
        fig.update_layout(
            title=title,
            xaxis_title="Ticker",
            yaxis_title="Drift",
            yaxis_tickformat=".1%",
            showlegend=False,
        )

        # ゼロラインを追加
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        logger.info(
            "Drift chart generated",
            ticker_count=len(tickers),
            rebalance_required_count=sum(requires_rebalance),
        )

        return fig

    def _generate_allocation_title(
        self,
        chart_type: Literal["pie", "bar"],
        group_by: Literal["ticker", "sector", "asset_class"] | None,
    ) -> str:
        """配分チャートのタイトルを自動生成.

        Parameters
        ----------
        chart_type : Literal["pie", "bar"]
            チャートタイプ
        group_by : Literal["ticker", "sector", "asset_class"] | None
            グループ化の基準

        Returns
        -------
        str
            生成されたタイトル
        """
        portfolio_name = self._portfolio.name or "Portfolio"

        group_label = ""
        if group_by == "sector":
            group_label = " by Sector"
        elif group_by == "asset_class":
            group_label = " by Asset Class"

        # AIDEV-NOTE: chart_type による分岐を削除（現在は同じ文字列を使用）
        _ = chart_type  # unused, but kept for future extension

        return f"{portfolio_name} - Allocation{group_label}"

    def _prepare_allocation_data(
        self,
        group_by: Literal["ticker", "sector", "asset_class"] | None,
    ) -> tuple[list[str], list[float]]:
        """配分データを準備.

        Parameters
        ----------
        group_by : Literal["ticker", "sector", "asset_class"] | None
            グループ化の基準

        Returns
        -------
        tuple[list[str], list[float]]
            ラベルと値のタプル
        """
        holdings = self._portfolio.holdings

        # ticker_info がない場合、または group_by が None/"ticker" の場合
        if self._ticker_info is None or group_by is None or group_by == "ticker":
            labels = [h.ticker for h in holdings]
            values = [h.weight for h in holdings]
            return labels, values

        # グループ化処理
        grouped: dict[str, float] = defaultdict(float)

        for holding in holdings:
            ticker_info = self._ticker_info.get(holding.ticker)
            if ticker_info is None:
                # ticker_info がない場合はティッカー名を使用
                group_key = holding.ticker
            elif group_by == "sector":
                group_key = ticker_info.sector or "Unknown"
            elif group_by == "asset_class":
                group_key = ticker_info.asset_class
            else:
                group_key = holding.ticker

            grouped[group_key] += holding.weight

        labels = list(grouped.keys())
        values = list(grouped.values())

        return labels, values

    def _create_pie_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str,
    ) -> go.Figure:
        """円グラフを作成.

        Parameters
        ----------
        labels : list[str]
            ラベルのリスト
        values : list[float]
            値のリスト
        title : str
            チャートのタイトル

        Returns
        -------
        go.Figure
            Plotlyの円グラフ
        """
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    textinfo="label+percent",
                    hoverinfo="label+percent+value",
                )
            ]
        )

        fig.update_layout(title=title)

        return fig

    def _create_bar_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str,
    ) -> go.Figure:
        """棒グラフを作成.

        Parameters
        ----------
        labels : list[str]
            ラベルのリスト
        values : list[float]
            値のリスト
        title : str
            チャートのタイトル

        Returns
        -------
        go.Figure
            Plotlyの棒グラフ
        """
        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels,
                    y=values,
                    text=[f"{v:.1%}" for v in values],
                    textposition="outside",
                )
            ]
        )

        fig.update_layout(
            title=title,
            xaxis_title="Asset",
            yaxis_title="Weight",
            yaxis_tickformat=".0%",
        )

        return fig
