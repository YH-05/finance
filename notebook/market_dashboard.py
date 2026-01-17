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
def _(mo, tab3_content):
    """Tab navigation for dashboard sections."""
    tabs = mo.ui.tabs(
        {
            "パフォーマンス概要": mo.md("## Tab 1: パフォーマンス概要\n\n- S&P500 & 主要指数のパフォーマンス\n- Magnificent 7 & SOX指数\n- セクターETF（XL系）\n- 貴金属"),
            "マクロ指標": mo.md("## Tab 2: マクロ指標\n\n- 米国金利（10Y, 2Y, FF）\n- イールドスプレッド\n- VIX & ハイイールドスプレッド"),
            "相関・ベータ分析": tab3_content,
            "リターン分布": mo.md("## Tab 4: リターン分布\n\n- 週次リターンヒストグラム\n- 統計サマリー"),
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
# Tab 3: 相関・ベータ分析
# =============================================================================


@app.cell
def _(mo):
    """Rolling window slider for Tab 3."""
    rolling_window_slider = mo.ui.slider(
        start=20,
        stop=252,
        step=1,
        value=60,
        label="ローリング窓サイズ（日数）",
        show_value=True,
    )
    return (rolling_window_slider,)


@app.cell
def _():
    """Import market_analysis API for Tab 3."""
    import contextlib
    import warnings

    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    from market_analysis import CorrelationAnalyzer, MarketData
    from market_analysis.visualization import HeatmapChart

    warnings.filterwarnings("ignore")
    return (
        CorrelationAnalyzer,
        HeatmapChart,
        MarketData,
        contextlib,
        go,
        make_subplots,
        pd,
    )


@app.cell
def _(
    MarketData, METALS, SECTOR_ETFS, contextlib, get_date_range, pd, selected_period
):
    """Fetch data for Tab 3 analysis."""
    market_data = MarketData()
    start_date, end_date = get_date_range(selected_period)

    # Fetch sector ETF data + S&P500 benchmark
    sector_data = {}  # dict[str, DataFrame]
    benchmark_symbol = "SPY"  # S&P500 ETF as benchmark
    sector_symbols = [*SECTOR_ETFS, benchmark_symbol]

    for symbol in sector_symbols:
        try:
            df = market_data.fetch_stock(symbol, start=start_date, end=end_date)
            sector_data[symbol] = df
        except Exception:
            pass  # Skip if data not available

    # Fetch metals data
    metals_data = {}  # dict[str, DataFrame]
    for symbol in METALS:
        try:
            df = market_data.fetch_stock(symbol, start=start_date, end=end_date)
            metals_data[symbol] = df
        except Exception:
            pass

    # Fetch USD Index from FRED
    usd_data = None  # DataFrame | None
    with contextlib.suppress(Exception):
        usd_data = market_data.fetch_fred("DTWEXAFEGS", start=start_date, end=end_date)

    return benchmark_symbol, market_data, metals_data, sector_data, usd_data


@app.cell
def _(
    CorrelationAnalyzer,
    benchmark_symbol,
    pd,
    rolling_window_slider,
    sector_data,
):
    """Calculate rolling beta for sector ETFs vs S&P500."""
    rolling_window = rolling_window_slider.value

    # Calculate returns for all sectors
    sector_returns = {}  # dict[str, Series]
    for symbol, df in sector_data.items():
        if "close" in df.columns:
            returns = df["close"].pct_change().dropna()
            sector_returns[symbol] = returns

    # Calculate rolling beta for each sector vs benchmark
    rolling_betas = {}  # dict[str, Series]
    if benchmark_symbol in sector_returns:
        benchmark_returns = sector_returns[benchmark_symbol]
        for symbol, returns in sector_returns.items():
            if symbol == benchmark_symbol:
                continue
            try:
                # Align returns
                aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
                if len(aligned) >= rolling_window:
                    beta = CorrelationAnalyzer.calculate_rolling_beta(
                        aligned.iloc[:, 0],
                        aligned.iloc[:, 1],
                        window=rolling_window,
                    )
                    rolling_betas[symbol] = beta
            except Exception:
                pass

    return rolling_betas, rolling_window, sector_returns


@app.cell
def _(go, make_subplots, rolling_betas, rolling_window):
    """Create sector ETF rolling beta chart."""
    # Select key sectors to display
    display_sectors = ["XLK", "XLF", "XLE", "XLU", "XLRE"]
    sector_names = {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLE": "Energy",
        "XLU": "Utilities",
        "XLRE": "Real Estate",
        "XLV": "Healthcare",
        "XLY": "Consumer Disc.",
        "XLP": "Consumer Staples",
        "XLI": "Industrials",
        "XLB": "Materials",
        "XLC": "Communication",
    }

    fig_beta = make_subplots(rows=1, cols=1)

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
    ]

    for i, symbol in enumerate(display_sectors):
        if symbol in rolling_betas:
            beta_series = rolling_betas[symbol].dropna()
            fig_beta.add_trace(
                go.Scatter(
                    x=beta_series.index,
                    y=beta_series.values,
                    mode="lines",
                    name=f"{symbol} ({sector_names.get(symbol, symbol)})",
                    line={"color": colors[i % len(colors)]},
                )
            )

    # Add beta = 1 reference line
    if rolling_betas:
        fig_beta.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="gray",
            annotation_text="β=1",
            annotation_position="right",
        )

    fig_beta.update_layout(
        title=f"セクターETF ローリングベータ (vs SPY, {rolling_window}日窓)",
        xaxis_title="日付",
        yaxis_title="ベータ",
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.3},
        height=450,
        template="plotly_white",
    )
    return colors, display_sectors, fig_beta, sector_names


@app.cell
def _(CorrelationAnalyzer, metals_data, pd, rolling_window, usd_data):
    """Calculate rolling correlation between USD index and metals."""
    usd_metals_correlations = {}  # dict[str, Series]

    if usd_data is not None and "close" in usd_data.columns:
        usd_prices = usd_data["close"]

        for symbol, df in metals_data.items():
            if "close" in df.columns:
                try:
                    metal_prices = df["close"]
                    # Align data
                    aligned = pd.concat([usd_prices, metal_prices], axis=1).dropna()
                    if len(aligned) >= rolling_window:
                        corr = CorrelationAnalyzer.calculate_rolling_correlation(
                            aligned.iloc[:, 0],
                            aligned.iloc[:, 1],
                            window=rolling_window,
                        )
                        usd_metals_correlations[symbol] = corr
                except Exception:
                    pass
    return (usd_metals_correlations,)


@app.cell
def _(go, make_subplots, rolling_window, usd_metals_correlations):
    """Create USD vs metals rolling correlation chart."""
    metal_names = {
        "GLD": "Gold",
        "SLV": "Silver",
        "CPER": "Copper",
        "PPLT": "Platinum",
        "PALL": "Palladium",
    }

    fig_usd_metals = make_subplots(rows=1, cols=1)

    colors_metals = ["#FFD700", "#C0C0C0", "#B87333", "#E5E4E2", "#CED0DD"]

    for i, (symbol, corr_series) in enumerate(usd_metals_correlations.items()):
        corr_clean = corr_series.dropna()
        fig_usd_metals.add_trace(
            go.Scatter(
                x=corr_clean.index,
                y=corr_clean.values,
                mode="lines",
                name=f"{symbol} ({metal_names.get(symbol, symbol)})",
                line={"color": colors_metals[i % len(colors_metals)]},
            )
        )

    # Add reference lines
    fig_usd_metals.add_hline(
        y=0, line_dash="dash", line_color="gray", annotation_text="相関=0"
    )

    fig_usd_metals.update_layout(
        title=f"ドルインデックス vs 貴金属 ローリング相関 ({rolling_window}日窓)",
        xaxis_title="日付",
        yaxis_title="相関係数",
        yaxis={"range": [-1, 1]},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.3},
        height=400,
        template="plotly_white",
    )
    return colors_metals, fig_usd_metals, metal_names


@app.cell
def _(CorrelationAnalyzer, pd, sector_returns):
    """Calculate correlation matrix for sector ETFs."""
    # Create returns DataFrame for correlation matrix
    returns_df = pd.DataFrame(sector_returns)

    # Calculate correlation matrix
    if not returns_df.empty and returns_df.shape[1] >= 2:
        correlation_matrix = CorrelationAnalyzer.calculate_correlation_matrix(
            returns_df, method="pearson"
        )
    else:
        correlation_matrix = pd.DataFrame()
    return correlation_matrix, returns_df


@app.cell
def _(HeatmapChart, correlation_matrix):
    """Create correlation heatmap for sector ETFs."""
    if not correlation_matrix.empty:
        heatmap_chart = HeatmapChart(
            correlation_matrix,
            show_values=True,
            value_format=".2f",
        )
        heatmap_chart.build()
        fig_heatmap = heatmap_chart.figure
        fig_heatmap.update_layout(
            title="セクターETF 相関ヒートマップ",
            height=500,
            width=600,
        )
    else:
        import plotly.graph_objects as go

        fig_heatmap = go.Figure()
        fig_heatmap.add_annotation(
            text="データ不足のためヒートマップを表示できません",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
    return fig_heatmap, heatmap_chart


@app.cell
def _(
    fig_beta,
    fig_heatmap,
    fig_usd_metals,
    mo,
    rolling_window_slider,
):
    """Assemble Tab 3 content."""
    tab3_content = mo.vstack(
        [
            mo.md("## Tab 3: 相関・ベータ分析"),
            mo.hstack([rolling_window_slider], justify="start"),
            mo.md("### セクターETF ローリングベータ (vs S&P500)"),
            fig_beta,
            mo.md("### ドルインデックス vs 貴金属 相関"),
            fig_usd_metals,
            mo.md("### セクターETF 相関ヒートマップ"),
            fig_heatmap,
        ],
        align="stretch",
    )
    return (tab3_content,)


if __name__ == "__main__":
    app.run()
