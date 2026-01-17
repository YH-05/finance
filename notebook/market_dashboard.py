import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    """Initialize marimo and imports."""
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    return go, make_subplots, mo, pd


@app.cell(hide_code=True)
def _(mo):
    """Dashboard header and description."""
    _header = mo.md(
        r"""
        # Market Dashboard

        株式市場・マクロ経済データ確認用のインタラクティブダッシュボード

        ---
        """
    )
    return (_header,)


@app.cell
def _(mo):
    """Period selection dropdown."""
    # Period options mapping
    PERIOD_OPTIONS = {
        "1M": "1mo",
        "3M": "3mo",
        "6M": "6mo",
        "1Y": "1y",
        "2Y": "2y",
        "5Y": "5y",
    }

    period_dropdown = mo.ui.dropdown(
        options=list(PERIOD_OPTIONS.keys()),
        value="1Y",
        label="期間選択",
    )

    mo.hstack([period_dropdown], justify="start")
    return PERIOD_OPTIONS, period_dropdown


@app.cell
def _(PERIOD_OPTIONS, period_dropdown):
    """Get selected period value for data fetching."""
    selected_period = PERIOD_OPTIONS.get(period_dropdown.value, "1y")
    return (selected_period,)


@app.cell
def _():
    """Data fetching functions using MarketData API."""
    from datetime import datetime, timedelta

    from market_analysis import MarketData

    def get_date_range(period: str) -> tuple[datetime, datetime]:
        """Calculate date range from period string.

        Parameters
        ----------
        period : str
            Period string (e.g., "1mo", "3mo", "1y")

        Returns
        -------
        tuple[datetime, datetime]
            Start and end dates
        """
        end_date = datetime.now()

        period_days = {
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
        }

        days = period_days.get(period, 365)
        start_date = end_date - timedelta(days=days)

        return start_date, end_date

    def fetch_stock_data(symbol: str, period: str) -> dict:
        """Fetch stock data for a symbol.

        Parameters
        ----------
        symbol : str
            Ticker symbol
        period : str
            Period string

        Returns
        -------
        dict
            Dictionary with 'data' key containing DataFrame or 'error' key
        """
        try:
            market_data = MarketData()
            start_date, end_date = get_date_range(period)
            df = market_data.fetch_stock(symbol, start=start_date, end=end_date)
            return {"data": df, "error": None}
        except Exception as e:
            return {"data": None, "error": str(e)}

    def fetch_fred_data(series_id: str, period: str) -> dict:
        """Fetch FRED economic indicator data.

        Parameters
        ----------
        series_id : str
            FRED series ID
        period : str
            Period string

        Returns
        -------
        dict
            Dictionary with 'data' key containing DataFrame or 'error' key
        """
        try:
            market_data = MarketData()
            start_date, end_date = get_date_range(period)
            df = market_data.fetch_fred(series_id, start=start_date, end=end_date)
            return {"data": df, "error": None}
        except Exception as e:
            return {"data": None, "error": str(e)}

    return MarketData, fetch_fred_data, fetch_stock_data, get_date_range


@app.cell
def _():
    """Ticker groups for different sections."""
    # Major indices
    MAJOR_INDICES = ["^GSPC", "^DJI", "^IXIC", "^RUT"]

    # Magnificent 7 + SOX
    MAG7_SOX = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "^SOX"]

    # Sector ETFs
    SECTOR_ETFS = [
        "XLK",
        "XLV",
        "XLF",
        "XLY",
        "XLP",
        "XLE",
        "XLI",
        "XLB",
        "XLU",
        "XLRE",
        "XLC",
    ]

    # Metals
    METALS = ["GLD", "SLV", "CPER", "PPLT", "PALL"]

    # FRED series IDs for macro indicators
    FRED_SERIES = {
        "DGS10": "10年国債",
        "DGS2": "2年国債",
        "DFF": "FF金利",
        "BAMLH0A0HYM2": "ハイイールドスプレッド",
        "USEPUINDXD": "経済不確実性指数",
        "DTWEXAFEGS": "ドルインデックス",
    }

    return FRED_SERIES, MAG7_SOX, MAJOR_INDICES, METALS, SECTOR_ETFS


@app.cell
def _(fetch_fred_data, mo, pd, selected_period):
    """Fetch macro indicator data from FRED."""
    # FRED series IDs for interest rates
    interest_rate_series = ["DGS10", "DGS2", "DFF"]

    # Fetch interest rate data
    macro_data = {}
    macro_errors = []

    for series_id in interest_rate_series:
        result = fetch_fred_data(series_id, selected_period)
        if result["error"]:
            macro_errors.append(f"{series_id}: {result['error']}")
        else:
            macro_data[series_id] = result["data"]

    # Fetch high yield spread
    hy_result = fetch_fred_data("BAMLH0A0HYM2", selected_period)
    if hy_result["error"]:
        macro_errors.append(f"BAMLH0A0HYM2: {hy_result['error']}")
    else:
        macro_data["BAMLH0A0HYM2"] = hy_result["data"]

    # Calculate yield spread (10Y - 2Y)
    yield_spread_df = None
    if "DGS10" in macro_data and "DGS2" in macro_data:
        dgs10 = macro_data["DGS10"]["close"].dropna()
        dgs2 = macro_data["DGS2"]["close"].dropna()
        common_idx = dgs10.index.intersection(dgs2.index)
        if len(common_idx) > 0:
            spread = dgs10.loc[common_idx] - dgs2.loc[common_idx]
            yield_spread_df = pd.DataFrame({"spread": spread}, index=common_idx)

    # Show loading status
    if macro_errors:
        _macro_status = mo.callout(
            mo.md("データ取得エラー:\n" + "\n".join(macro_errors)),
            kind="warn",
        )
    else:
        _macro_status = mo.callout(
            mo.md(f"✓ マクロ指標データ取得完了 ({len(macro_data)} シリーズ)"),
            kind="success",
        )

    return _macro_status, macro_data, macro_errors, yield_spread_df


@app.cell
def _(fetch_stock_data, selected_period):
    """Fetch VIX data from Yahoo Finance."""
    vix_result = fetch_stock_data("^VIX", selected_period)
    vix_data = vix_result["data"]
    vix_error = vix_result["error"]

    return vix_data, vix_error


@app.cell
def _(go, macro_data, mo):
    """Create US interest rates chart (10Y, 2Y, FF)."""
    # Create interest rates chart
    interest_rates_chart = None

    if all(key in macro_data for key in ["DGS10", "DGS2", "DFF"]):
        fig = go.Figure()

        # Add 10Y Treasury
        dgs10 = macro_data["DGS10"]
        fig.add_trace(
            go.Scatter(
                x=dgs10.index,
                y=dgs10["close"],
                name="10年国債",
                line={"color": "#1f77b4", "width": 2},
            )
        )

        # Add 2Y Treasury
        dgs2 = macro_data["DGS2"]
        fig.add_trace(
            go.Scatter(
                x=dgs2.index,
                y=dgs2["close"],
                name="2年国債",
                line={"color": "#ff7f0e", "width": 2},
            )
        )

        # Add Fed Funds Rate
        dff = macro_data["DFF"]
        fig.add_trace(
            go.Scatter(
                x=dff.index,
                y=dff["close"],
                name="FF金利",
                line={"color": "#2ca02c", "width": 2},
            )
        )

        fig.update_layout(
            title="米国金利推移",
            xaxis_title="日付",
            yaxis_title="金利 (%)",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
            hovermode="x unified",
            template="plotly_white",
            height=400,
        )

        interest_rates_chart = mo.ui.plotly(fig)
    else:
        interest_rates_chart = mo.callout(
            mo.md("金利データの取得に失敗しました"),
            kind="danger",
        )

    return (interest_rates_chart,)


@app.cell
def _(go, mo, yield_spread_df):
    """Create yield spread chart (10Y - 2Y)."""
    yield_spread_chart = None

    if yield_spread_df is not None and len(yield_spread_df) > 0:
        fig = go.Figure()

        # Add yield spread line
        fig.add_trace(
            go.Scatter(
                x=yield_spread_df.index,
                y=yield_spread_df["spread"],
                name="イールドスプレッド (10Y-2Y)",
                line={"color": "#9467bd", "width": 2},
                fill="tozeroy",
                fillcolor="rgba(148, 103, 189, 0.2)",
            )
        )

        # Add zero line
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="red",
            annotation_text="逆イールド基準",
            annotation_position="right",
        )

        fig.update_layout(
            title="イールドスプレッド (10年 - 2年国債)",
            xaxis_title="日付",
            yaxis_title="スプレッド (%)",
            hovermode="x unified",
            template="plotly_white",
            height=350,
        )

        yield_spread_chart = mo.ui.plotly(fig)
    else:
        yield_spread_chart = mo.callout(
            mo.md("イールドスプレッドの計算に失敗しました"),
            kind="danger",
        )

    return (yield_spread_chart,)


@app.cell
def _(go, macro_data, make_subplots, mo, vix_data, vix_error):
    """Create VIX and High Yield Spread chart."""
    vix_hy_chart = None

    has_vix = vix_data is not None and not vix_error
    has_hy = "BAMLH0A0HYM2" in macro_data

    if has_vix or has_hy:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("VIX 恐怖指数", "ハイイールドスプレッド"),
        )

        if has_vix:
            fig.add_trace(
                go.Scatter(
                    x=vix_data.index,
                    y=vix_data["close"],
                    name="VIX",
                    line={"color": "#d62728", "width": 2},
                ),
                row=1,
                col=1,
            )
            # Add VIX threshold lines
            fig.add_hline(
                y=20,
                line_dash="dash",
                line_color="orange",
                annotation_text="警戒水準",
                row=1,
                col=1,
            )
            fig.add_hline(
                y=30,
                line_dash="dash",
                line_color="red",
                annotation_text="高リスク",
                row=1,
                col=1,
            )

        if has_hy:
            hy_data = macro_data["BAMLH0A0HYM2"]
            fig.add_trace(
                go.Scatter(
                    x=hy_data.index,
                    y=hy_data["close"],
                    name="ハイイールドスプレッド",
                    line={"color": "#8c564b", "width": 2},
                ),
                row=2,
                col=1,
            )

        fig.update_layout(
            title="リスク指標",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            showlegend=True,
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        )

        fig.update_yaxes(title_text="VIX", row=1, col=1)
        fig.update_yaxes(title_text="スプレッド (%)", row=2, col=1)

        vix_hy_chart = mo.ui.plotly(fig)
    else:
        errors = []
        if vix_error:
            errors.append(f"VIX: {vix_error}")
        if not has_hy:
            errors.append("ハイイールドスプレッド: データなし")
        vix_hy_chart = mo.callout(
            mo.md("リスク指標データの取得に失敗しました:\n" + "\n".join(errors)),
            kind="danger",
        )

    return (vix_hy_chart,)


@app.cell
def _(interest_rates_chart, mo, vix_hy_chart, yield_spread_chart):
    """Tab 2: Macro indicators content."""
    tab2_content = mo.vstack(
        [
            mo.md("## マクロ指標"),
            mo.md("### 米国金利"),
            interest_rates_chart,
            mo.md("### イールドスプレッド"),
            yield_spread_chart,
            mo.md("### リスク指標"),
            vix_hy_chart,
        ],
        gap=2,
    )
    return (tab2_content,)


@app.cell
def _(mo, return_distribution_content, tab2_content):
    """Tab navigation for dashboard sections with implemented Tab 2 and Tab 4."""
    tabs_with_macro = mo.ui.tabs(
        {
            "パフォーマンス概要": mo.md("## Tab 1: パフォーマンス概要\n\n- S&P500 & 主要指数のパフォーマンス\n- Magnificent 7 & SOX指数\n- セクターETF（XL系）\n- 貴金属\n\n> 未実装"),
            "マクロ指標": tab2_content,
            "相関・ベータ分析": mo.md("## Tab 3: 相関・ベータ分析\n\n- セクターETFローリングベータ（vs S&P500）\n- ドルインデックス vs 貴金属相関\n- 相関ヒートマップ\n\n> 未実装"),
            "リターン分布": return_distribution_content,
        }
    )
    return (tabs_with_macro,)


@app.cell(hide_code=True)
def _(mo, selected_period, tabs_with_macro):
    """Display main dashboard with tabs."""
    _dashboard = mo.vstack(
        [
            mo.md(f"**選択期間**: {selected_period}"),
            tabs_with_macro,
        ],
        gap=2,
    )
    return (_dashboard,)


# =============================================================================
# Tab 4: リターン分布
# =============================================================================


@app.cell
def _(mo):
    """Return distribution symbol selector."""
    return_dist_symbols = mo.ui.dropdown(
        options=["^GSPC", "^DJI", "^IXIC", "AAPL", "MSFT", "GOOGL", "NVDA", "SPY"],
        value="^GSPC",
        label="銘柄選択",
    )
    return (return_dist_symbols,)


@app.cell
def _():
    """Import dependencies for return distribution analysis."""
    import numpy as np
    import plotly.graph_objects as go

    from market_analysis import MarketData

    return MarketData, go, np


@app.cell
def _(MarketData, np, selected_period):
    """Calculate weekly returns with statistics."""

    def calculate_weekly_returns(symbol: str, period: str) -> dict | None:
        """Calculate weekly log returns and statistics.

        Parameters
        ----------
        symbol : str
            Ticker symbol
        period : str
            Period string (e.g., "1y", "2y")

        Returns
        -------
        dict | None
            Dictionary containing returns and statistics, or None if error
        """
        try:
            # Fetch stock data
            data_client = MarketData()

            # Map period to days
            period_days = {
                "1mo": 30,
                "3mo": 90,
                "6mo": 180,
                "1y": 365,
                "2y": 730,
                "5y": 1825,
            }
            days = period_days.get(period, 365)

            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            df = data_client.fetch_stock(
                symbol, start=start_date.strftime("%Y-%m-%d")
            )

            if df.empty:
                return None

            # Resample to weekly (Friday close)
            weekly_df = df["close"].resample("W-FRI").last().dropna()

            if len(weekly_df) < 2:
                return None

            # Calculate log returns
            log_returns = np.log(weekly_df / weekly_df.shift(1)).dropna()

            # Calculate statistics
            mean_return = float(log_returns.mean())
            std_return = float(log_returns.std())
            annualized_return = mean_return * 52  # Annualize
            annualized_vol = std_return * np.sqrt(52)

            return {
                "returns": log_returns.values,
                "dates": log_returns.index,
                "mean": mean_return,
                "std": std_return,
                "min": float(log_returns.min()),
                "max": float(log_returns.max()),
                "count": len(log_returns),
                "annualized_return": annualized_return,
                "annualized_vol": annualized_vol,
                "skewness": float(log_returns.skew()),
                "kurtosis": float(log_returns.kurtosis()),
            }
        except Exception:
            return None

    return (calculate_weekly_returns,)


@app.cell
def _(calculate_weekly_returns, return_dist_symbols, selected_period):
    """Fetch and calculate return distribution data."""
    return_data = calculate_weekly_returns(return_dist_symbols.value, selected_period)
    return (return_data,)


@app.cell
def _(go, return_data, return_dist_symbols):
    """Create return distribution histogram with vertical lines."""

    def create_return_histogram(data: dict | None, symbol: str):
        """Create histogram with mean and ±1 sigma lines.

        Parameters
        ----------
        data : dict | None
            Return data dictionary
        symbol : str
            Symbol name for title

        Returns
        -------
        go.Figure
            Plotly figure object
        """
        if data is None:
            fig = go.Figure()
            fig.add_annotation(
                text="データを取得できませんでした",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font={"size": 16},
            )
            fig.update_layout(title=f"{symbol} 週次リターン分布")
            return fig

        returns = data["returns"]
        mean = data["mean"]
        std = data["std"]

        # Create histogram
        fig = go.Figure()

        # Add histogram trace
        fig.add_trace(
            go.Histogram(
                x=returns,
                nbinsx=30,
                name="週次リターン",
                marker_color="rgba(55, 128, 191, 0.7)",
                marker_line_color="rgba(55, 128, 191, 1)",
                marker_line_width=1,
            )
        )

        # Add vertical line for mean
        fig.add_vline(
            x=mean,
            line_dash="solid",
            line_color="red",
            line_width=2,
            annotation_text=f"平均: {mean:.4f}",
            annotation_position="top",
        )

        # Add vertical lines for ±1 sigma
        fig.add_vline(
            x=mean + std,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            annotation_text=f"+1σ: {mean + std:.4f}",
            annotation_position="top",
        )

        fig.add_vline(
            x=mean - std,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            annotation_text=f"-1σ: {mean - std:.4f}",
            annotation_position="top",
        )

        # Update layout
        fig.update_layout(
            title=f"{symbol} 週次リターン分布（対数リターン）",
            xaxis_title="週次リターン",
            yaxis_title="頻度",
            showlegend=False,
            height=450,
            template="plotly_white",
        )

        return fig

    return_histogram_fig = create_return_histogram(
        return_data, return_dist_symbols.value
    )
    return (return_histogram_fig,)


@app.cell
def _(mo, return_data, return_dist_symbols):
    """Create statistics summary table."""

    def create_stats_table(data: dict | None, symbol: str) -> str:
        """Create markdown statistics table.

        Parameters
        ----------
        data : dict | None
            Return data dictionary
        symbol : str
            Symbol name

        Returns
        -------
        str
            Markdown table string
        """
        if data is None:
            return "データを取得できませんでした"

        table = f"""
### {symbol} 週次リターン統計サマリー

| 指標 | 値 |
|------|-----|
| サンプル数 | {data['count']} |
| 平均（週次） | {data['mean']:.4%} |
| 標準偏差（週次） | {data['std']:.4%} |
| 最小値 | {data['min']:.4%} |
| 最大値 | {data['max']:.4%} |
| 年率リターン | {data['annualized_return']:.2%} |
| 年率ボラティリティ | {data['annualized_vol']:.2%} |
| 歪度 | {data['skewness']:.3f} |
| 尖度 | {data['kurtosis']:.3f} |
"""
        return table

    stats_table_md = create_stats_table(return_data, return_dist_symbols.value)
    return (stats_table_md,)


@app.cell
def _(mo, return_dist_symbols, return_histogram_fig, stats_table_md):
    """Compose return distribution tab content."""
    return_distribution_content = mo.vstack(
        [
            mo.md("## Tab 4: リターン分布"),
            mo.hstack([return_dist_symbols], justify="start"),
            return_histogram_fig,
            mo.md(stats_table_md),
        ]
    )
    return (return_distribution_content,)


if __name__ == "__main__":
    app.run()
