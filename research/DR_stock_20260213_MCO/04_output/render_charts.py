"""MCO 投資分析レポート用チャート生成スクリプト.

リサーチID: DR_stock_20260213_MCO
生成チャート:
  1. 株価チャート（ローソク足 + SMA20/50）
  2. ピア比較（相対パフォーマンス）
  3. 財務トレンド（月次株価推移）
  4. バリュエーション比較（ヒートマップ）
  5. セクターパフォーマンス（リターン比較）

Usage:
    python render_charts.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from analyze.visualization import (  # noqa: E402
    ChartConfig,
    ChartTheme,
    HeatmapChart,
    get_theme_colors,
)
from utils_core.logging import get_logger  # noqa: E402

logger = get_logger(__name__)

# 定数
RESEARCH_DIR = Path(__file__).resolve().parent.parent
MARKET_DATA_PATH = RESEARCH_DIR / "01_data_collection" / "market-data.json"
CHARTS_DIR = RESEARCH_DIR / "04_output" / "charts"
TARGET_TICKER = "MCO"
PEER_TICKERS = ["SPGI", "MSCI", "ICE", "VRSK", "FDS"]
ALL_TICKERS = [TARGET_TICKER, *PEER_TICKERS]


def load_market_data() -> dict:
    """market-data.json を読み込む."""
    logger.info("Loading market data", path=str(MARKET_DATA_PATH))
    with open(MARKET_DATA_PATH) as f:
        return json.load(f)


def create_price_chart(data: dict) -> None:
    """株価チャート: MCO の月次株価推移 + SMA20/50 相当."""
    logger.info("Creating price chart for MCO")
    config = ChartConfig(
        title="MCO 株価推移（5年）",
        theme=ChartTheme.LIGHT,
        width=1200,
        height=600,
    )
    colors = get_theme_colors(config.theme)

    mco_data = data["stocks"]["MCO"]
    monthly_closes = mco_data["price_data"]["monthly_closes"]

    dates = list(monthly_closes.keys())
    prices = list(monthly_closes.values())

    df = pd.DataFrame({"date": pd.to_datetime(dates), "close": prices})
    df = df.sort_values("date").reset_index(drop=True)

    # SMA 計算（月次ベースなので 3ヶ月 / 6ヶ月 移動平均）
    df["sma_3m"] = df["close"].rolling(window=3).mean()
    df["sma_6m"] = df["close"].rolling(window=6).mean()

    fig = go.Figure()

    # 株価ライン
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines+markers",
            name="MCO 月次終値",
            line={"color": colors.accent, "width": 2},
            marker={"size": 3},
        )
    )

    # SMA 3ヶ月
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["sma_3m"],
            mode="lines",
            name="SMA 3ヶ月",
            line={"color": colors.series_colors[1], "width": 1, "dash": "dash"},
        )
    )

    # SMA 6ヶ月
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["sma_6m"],
            mode="lines",
            name="SMA 6ヶ月",
            line={"color": colors.series_colors[2], "width": 1, "dash": "dot"},
        )
    )

    # 52週高値/安値ライン
    stats = mco_data["price_data"]["period_stats"]
    fig.add_hline(
        y=stats["high_52w"],
        line_dash="dash",
        line_color=colors.positive,
        annotation_text=f"52W High: ${stats['high_52w']}",
        annotation_position="top right",
    )
    fig.add_hline(
        y=stats["low_52w"],
        line_dash="dash",
        line_color=colors.negative,
        annotation_text=f"52W Low: ${stats['low_52w']}",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title={"text": "MCO 株価推移（5年）", "x": 0.5, "xanchor": "center"},
        xaxis_title="日付",
        yaxis_title="株価 ($)",
        paper_bgcolor=colors.paper,
        plot_bgcolor=colors.background,
        font={"color": colors.text},
        showlegend=True,
        legend={"orientation": "h", "y": 1.02, "x": 0.5, "xanchor": "center"},
        width=config.width,
        height=config.height,
    )
    fig.update_xaxes(gridcolor=colors.grid)
    fig.update_yaxes(gridcolor=colors.grid)

    output_path = CHARTS_DIR / "price_chart.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(output_path), scale=2)
    logger.info("Price chart saved", path=str(output_path))


def create_peer_comparison(data: dict) -> None:
    """ピア比較: 累積リターン比較チャート."""
    logger.info("Creating peer comparison chart")
    colors = get_theme_colors(ChartTheme.LIGHT)

    fig = go.Figure()

    for i, ticker in enumerate(ALL_TICKERS):
        stock_data = data["stocks"].get(ticker)
        if not stock_data:
            continue

        monthly_closes = stock_data["price_data"]["monthly_closes"]
        dates = sorted(monthly_closes.keys())
        prices = [monthly_closes[d] for d in dates]

        if not prices or prices[0] == 0:
            continue

        # 累積リターン計算
        base_price = prices[0]
        cumulative_returns = [(p / base_price - 1) * 100 for p in prices]

        line_width = 3 if ticker == TARGET_TICKER else 1.5
        color = (
            colors.accent
            if ticker == TARGET_TICKER
            else colors.series_colors[i % len(colors.series_colors)]
        )

        fig.add_trace(
            go.Scatter(
                x=[pd.to_datetime(d) for d in dates],
                y=cumulative_returns,
                mode="lines",
                name=ticker,
                line={"color": color, "width": line_width},
                hovertemplate=f"{ticker}<br>%{{x}}<br>%{{y:.1f}}%<extra></extra>",
            )
        )

    fig.update_layout(
        title={
            "text": "MCO vs ピアグループ 累積リターン（5年）",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="日付",
        yaxis_title="累積リターン (%)",
        paper_bgcolor=colors.paper,
        plot_bgcolor=colors.background,
        font={"color": colors.text},
        showlegend=True,
        legend={"orientation": "h", "y": 1.02, "x": 0.5, "xanchor": "center"},
        width=1200,
        height=600,
        yaxis={"tickformat": "+.0f", "ticksuffix": "%"},
    )
    fig.update_xaxes(gridcolor=colors.grid)
    fig.update_yaxes(gridcolor=colors.grid, zeroline=True, zerolinecolor=colors.axis)

    output_path = CHARTS_DIR / "peer_comparison.png"
    fig.write_image(str(output_path), scale=2)
    logger.info("Peer comparison chart saved", path=str(output_path))


def create_financial_trend(data: dict) -> None:
    """財務トレンド: 主要財務指標のピア間比較バーチャート."""
    logger.info("Creating financial trend chart")
    colors = get_theme_colors(ChartTheme.LIGHT)

    metrics = {
        "営業利益率 (%)": "operating_margin",
        "純利益率 (%)": "profit_margin",
        "ROA (%)": "return_on_assets",
        "売上成長率 (%)": "revenue_growth",
    }

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=list(metrics.keys()),
        vertical_spacing=0.15,
        horizontal_spacing=0.12,
    )

    for idx, (label, key) in enumerate(metrics.items()):
        row = idx // 2 + 1
        col = idx % 2 + 1

        tickers_data = []
        values = []

        for ticker in ALL_TICKERS:
            fi = data["stocks"].get(ticker, {}).get("financial_info", {})
            val = fi.get(key)
            if val is not None:
                tickers_data.append(ticker)
                values.append(val * 100 if val < 1 else val)

        bar_colors = [
            colors.accent if t == TARGET_TICKER else colors.series_colors[2]
            for t in tickers_data
        ]

        fig.add_trace(
            go.Bar(
                x=tickers_data,
                y=values,
                marker_color=bar_colors,
                showlegend=False,
                text=[f"{v:.1f}%" for v in values],
                textposition="outside",
            ),
            row=row,
            col=col,
        )

    fig.update_layout(
        title={
            "text": "MCO vs ピアグループ 財務指標比較",
            "x": 0.5,
            "xanchor": "center",
        },
        paper_bgcolor=colors.paper,
        plot_bgcolor=colors.background,
        font={"color": colors.text},
        width=1200,
        height=800,
    )
    fig.update_xaxes(gridcolor=colors.grid)
    fig.update_yaxes(gridcolor=colors.grid)

    output_path = CHARTS_DIR / "financial_trend.png"
    fig.write_image(str(output_path), scale=2)
    logger.info("Financial trend chart saved", path=str(output_path))


def create_valuation_heatmap(data: dict) -> None:
    """バリュエーション比較: ヒートマップ."""
    logger.info("Creating valuation heatmap")

    valuation_metrics = [
        ("Trailing P/E", "trailing_pe"),
        ("Forward P/E", "forward_pe"),
        ("P/B", "price_to_book"),
        ("EV/EBITDA", "ev_to_ebitda"),
        ("P/S", "price_to_sales"),
    ]

    matrix_data = {}
    for ticker in ALL_TICKERS:
        fi = data["stocks"].get(ticker, {}).get("financial_info", {})
        row = {}
        for label, key in valuation_metrics:
            val = fi.get(key)
            row[label] = val if val is not None else float("nan")
        matrix_data[ticker] = row

    df = pd.DataFrame(matrix_data).T

    colors = get_theme_colors(ChartTheme.LIGHT)

    fig = go.Figure(
        data=go.Heatmap(
            z=df.values,
            x=list(df.columns),
            y=list(df.index),
            colorscale="RdYlGn_r",
            text=[
                [f"{v:.1f}" if not pd.isna(v) else "N/A" for v in row]
                for row in df.values
            ],
            texttemplate="%{text}",
            hoverongaps=False,
        )
    )

    fig.update_layout(
        title={
            "text": "バリュエーション比較ヒートマップ",
            "x": 0.5,
            "xanchor": "center",
        },
        paper_bgcolor=colors.paper,
        plot_bgcolor=colors.background,
        font={"color": colors.text},
        width=1000,
        height=500,
    )

    output_path = CHARTS_DIR / "valuation_heatmap.png"
    fig.write_image(str(output_path), scale=2)
    logger.info("Valuation heatmap saved", path=str(output_path))


def create_sector_performance(data: dict) -> None:
    """セクターパフォーマンス: 期間別リターン比較."""
    logger.info("Creating sector performance chart")
    colors = get_theme_colors(ChartTheme.LIGHT)

    periods = ["1m", "3m", "6m", "1y"]
    period_labels = ["1ヶ月", "3ヶ月", "6ヶ月", "1年"]

    fig = go.Figure()

    for i, ticker in enumerate(ALL_TICKERS):
        stock_data = data["stocks"].get(ticker)
        if not stock_data:
            continue

        returns = stock_data["price_data"].get("returns", {})
        period_returns = [returns.get(p, 0) for p in periods]

        line_width = 3 if ticker == TARGET_TICKER else 1.5
        color = (
            colors.accent
            if ticker == TARGET_TICKER
            else colors.series_colors[i % len(colors.series_colors)]
        )

        fig.add_trace(
            go.Bar(
                x=period_labels,
                y=period_returns,
                name=ticker,
                marker_color=color,
                text=[f"{r:+.1f}%" for r in period_returns],
                textposition="outside",
            )
        )

    fig.update_layout(
        title={
            "text": "MCO vs ピアグループ 期間別リターン",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="期間",
        yaxis_title="リターン (%)",
        barmode="group",
        paper_bgcolor=colors.paper,
        plot_bgcolor=colors.background,
        font={"color": colors.text},
        showlegend=True,
        legend={"orientation": "h", "y": 1.05, "x": 0.5, "xanchor": "center"},
        width=1200,
        height=600,
        yaxis={"tickformat": "+.0f", "ticksuffix": "%"},
    )
    fig.update_xaxes(gridcolor=colors.grid)
    fig.update_yaxes(gridcolor=colors.grid, zeroline=True, zerolinecolor=colors.axis)

    output_path = CHARTS_DIR / "sector_performance.png"
    fig.write_image(str(output_path), scale=2)
    logger.info("Sector performance chart saved", path=str(output_path))


def main() -> None:
    """全チャートを生成."""
    logger.info("Starting chart generation for DR_stock_20260213_MCO")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    data = load_market_data()

    create_price_chart(data)
    create_peer_comparison(data)
    create_financial_trend(data)
    create_valuation_heatmap(data)
    create_sector_performance(data)

    logger.info(
        "All charts generated successfully",
        output_dir=str(CHARTS_DIR),
        charts_count=5,
    )


if __name__ == "__main__":
    main()
