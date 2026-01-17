import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    """Initialize marimo and imports."""
    import marimo as mo

    return (mo,)


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
def _(mo, return_distribution_content):
    """Tab navigation for dashboard sections."""
    tabs = mo.ui.tabs(
        {
            "パフォーマンス概要": mo.md("## Tab 1: パフォーマンス概要\n\n- S&P500 & 主要指数のパフォーマンス\n- Magnificent 7 & SOX指数\n- セクターETF（XL系）\n- 貴金属"),
            "マクロ指標": mo.md("## Tab 2: マクロ指標\n\n- 米国金利（10Y, 2Y, FF）\n- イールドスプレッド\n- VIX & ハイイールドスプレッド"),
            "相関・ベータ分析": mo.md("## Tab 3: 相関・ベータ分析\n\n- セクターETFローリングベータ（vs S&P500）\n- ドルインデックス vs 貴金属相関\n- 相関ヒートマップ"),
            "リターン分布": return_distribution_content,
        }
    )
    return (tabs,)


@app.cell
def _(PERIOD_OPTIONS, period_dropdown):
    """Get selected period value for data fetching."""
    selected_period = PERIOD_OPTIONS.get(period_dropdown.value, "1y")
    return (selected_period,)


@app.cell
def _():
    """Data fetching function skeleton.

    TODO: Implement actual data fetching using market_analysis API.
    """
    from datetime import datetime, timedelta

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

    def fetch_stock_data(symbols: list[str], period: str) -> dict:
        """Fetch stock data for given symbols.

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols
        period : str
            Period string

        Returns
        -------
        dict
            Dictionary of symbol -> DataFrame
        """
        # Skeleton: To be implemented with MarketData API
        return {}

    def fetch_fred_data(series_ids: list[str], period: str) -> dict:
        """Fetch FRED economic indicator data.

        Parameters
        ----------
        series_ids : list[str]
            List of FRED series IDs
        period : str
            Period string

        Returns
        -------
        dict
            Dictionary of series_id -> DataFrame
        """
        # Skeleton: To be implemented with MarketData API
        return {}

    return fetch_fred_data, fetch_stock_data, get_date_range


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


@app.cell(hide_code=True)
def _(mo, selected_period):
    """Display current selection status."""
    _status = mo.md(
        f"""
        ---
        **現在の選択**: 期間 = {selected_period}

        > このダッシュボードは開発中です。データ取得機能は後続の Issue で実装予定です。
        """
    )
    return (_status,)


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
