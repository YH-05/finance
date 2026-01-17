import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    """Initialize marimo and imports."""
    from datetime import datetime, timedelta

    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    return datetime, go, make_subplots, mo, np, pd, timedelta


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
    # Period options mapping (display label -> yfinance period)
    PERIOD_OPTIONS = {
        "1M": "1mo",
        "3M": "3mo",
        "6M": "6mo",
        "1Y": "1y",
        "2Y": "2y",
        "5Y": "5y",
    }

    # Period options mapping (display label -> days for date calculation)
    PERIOD_DAYS = {
        "1M": 30,
        "3M": 90,
        "6M": 180,
        "1Y": 365,
        "2Y": 730,
        "5Y": 1825,
    }

    period_dropdown = mo.ui.dropdown(
        options=list(PERIOD_OPTIONS.keys()),
        value="1Y",
        label="期間選択",
    )

    mo.hstack([period_dropdown], justify="start")
    return PERIOD_DAYS, PERIOD_OPTIONS, period_dropdown


@app.cell
def _(PERIOD_DAYS, PERIOD_OPTIONS, period_dropdown):
    """Get selected period value for data fetching."""
    selected_period = PERIOD_OPTIONS.get(period_dropdown.value, "1y")
    selected_days = PERIOD_DAYS.get(period_dropdown.value, 365)
    return selected_days, selected_period


@app.cell
def _(datetime, timedelta):
    """Data fetching functions using market_analysis API."""
    from typing import Any

    from market_analysis import MarketData

    # Initialize MarketData instance for bulk fetching
    _market_data_instance = MarketData()

    def get_date_range_from_days(days: int) -> tuple[Any, Any]:
        """Calculate date range from days.

        Parameters
        ----------
        days : int
            Number of days to look back

        Returns
        -------
        tuple[datetime, datetime]
            Start and end dates
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date

    def get_date_range_from_period(period: str) -> tuple[datetime, datetime]:
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

    def fetch_stock_data_bulk(symbols: list[str], days: int) -> dict[str, Any]:
        """Fetch stock data for given symbols (bulk).

        Parameters
        ----------
        symbols : list[str]
            List of ticker symbols
        days : int
            Number of days to look back

        Returns
        -------
        dict[str, pd.DataFrame]
            Dictionary of symbol -> DataFrame
        """
        start_date, end_date = get_date_range_from_days(days)
        result: dict[str, Any] = {}

        for symbol in symbols:
            try:
                df = _market_data_instance.fetch_stock(
                    symbol, start=start_date, end=end_date
                )
                result[symbol] = df
            except Exception:  # nosec B110 - Intentional: skip unavailable symbols
                pass

        return result

    def fetch_commodity_data(symbols: list[str], days: int) -> dict[str, Any]:
        """Fetch commodity data for given symbols.

        Parameters
        ----------
        symbols : list[str]
            List of commodity symbols (e.g., "GLD", "SLV")
        days : int
            Number of days to look back

        Returns
        -------
        dict[str, pd.DataFrame]
            Dictionary of symbol -> DataFrame
        """
        start_date, end_date = get_date_range_from_days(days)
        result: dict[str, Any] = {}

        for symbol in symbols:
            try:
                df = _market_data_instance.fetch_stock(
                    symbol, start=start_date, end=end_date
                )
                result[symbol] = df
            except Exception:  # nosec B110 - Intentional: skip unavailable symbols
                pass

        return result

    def fetch_stock_data_single(symbol: str, period: str) -> dict:
        """Fetch stock data for a single symbol.

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
            start_date, end_date = get_date_range_from_period(period)
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
            start_date, end_date = get_date_range_from_period(period)
            df = market_data.fetch_fred(series_id, start=start_date, end=end_date)
            return {"data": df, "error": None}
        except Exception as e:
            return {"data": None, "error": str(e)}

    return (
        MarketData,
        fetch_commodity_data,
        fetch_fred_data,
        fetch_stock_data_bulk,
        fetch_stock_data_single,
        get_date_range_from_days,
        get_date_range_from_period,
    )


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

    # Metals (ETFs for precious metals)
    METALS = ["GLD", "SLV", "CPER", "PPLT", "PALL"]

    # Display names for tickers
    TICKER_NAMES = {
        # Major indices
        "^GSPC": "S&P 500",
        "^DJI": "ダウ30",
        "^IXIC": "NASDAQ",
        "^RUT": "Russell 2000",
        # Magnificent 7
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Google",
        "AMZN": "Amazon",
        "NVDA": "NVIDIA",
        "META": "Meta",
        "TSLA": "Tesla",
        "^SOX": "半導体指数",
        # Sector ETFs
        "XLK": "テクノロジー",
        "XLV": "ヘルスケア",
        "XLF": "金融",
        "XLY": "一般消費財",
        "XLP": "生活必需品",
        "XLE": "エネルギー",
        "XLI": "資本財",
        "XLB": "素材",
        "XLU": "公益",
        "XLRE": "不動産",
        "XLC": "通信",
        # Metals
        "GLD": "金",
        "SLV": "銀",
        "CPER": "銅",
        "PPLT": "プラチナ",
        "PALL": "パラジウム",
    }

    # FRED series IDs for macro indicators
    FRED_SERIES = {
        "DGS10": "10年国債",
        "DGS2": "2年国債",
        "DFF": "FF金利",
        "BAMLH0A0HYM2": "ハイイールドスプレッド",
        "USEPUINDXD": "経済不確実性指数",
        "DTWEXAFEGS": "ドルインデックス",
    }

    return (
        FRED_SERIES,
        MAG7_SOX,
        MAJOR_INDICES,
        METALS,
        SECTOR_ETFS,
        TICKER_NAMES,
    )


# =============================================================================
# Tab 1: パフォーマンス概要
# =============================================================================


@app.cell
def _(np, pd):
    """Performance calculation functions."""
    from typing import Any

    def calculate_period_return(
        df: Any, days: int, price_col: str = "close"
    ) -> float | None:
        """Calculate return for a specific period.

        Parameters
        ----------
        df : pd.DataFrame
            Price data with datetime index
        days : int
            Number of trading days for the period
        price_col : str
            Column name for price data

        Returns
        -------
        float | None
            Return as percentage, None if insufficient data
        """
        if df.empty or len(df) < 2:
            return None

        try:
            # Get the most recent price
            current_price = df[price_col].iloc[-1]

            # Find price from 'days' trading days ago
            if len(df) >= days:
                past_price = df[price_col].iloc[-days]
            else:
                # Use earliest available price if less data
                past_price = df[price_col].iloc[0]

            if past_price == 0 or np.isnan(past_price):
                return None

            return ((current_price - past_price) / past_price) * 100
        except (IndexError, KeyError):
            return None

    def calculate_ytd_return(df: Any, price_col: str = "close") -> float | None:
        """Calculate Year-to-Date return.

        Parameters
        ----------
        df : pd.DataFrame
            Price data with datetime index
        price_col : str
            Column name for price data

        Returns
        -------
        float | None
            YTD return as percentage, None if insufficient data
        """
        if df.empty or len(df) < 2:
            return None

        try:
            current_price = df[price_col].iloc[-1]

            # Find first trading day of current year
            current_year = df.index[-1].year
            year_start_data = df[df.index.year == current_year]

            if year_start_data.empty:
                return None

            year_start_price = year_start_data[price_col].iloc[0]

            if year_start_price == 0 or np.isnan(year_start_price):
                return None

            return ((current_price - year_start_price) / year_start_price) * 100
        except (IndexError, KeyError, AttributeError):
            return None

    def calculate_performance_metrics(
        data: dict[str, Any],
        ticker_names: dict[str, str],
    ) -> Any:
        """Calculate performance metrics for multiple symbols.

        Parameters
        ----------
        data : dict[str, pd.DataFrame]
            Dictionary of symbol -> price DataFrame
        ticker_names : dict[str, str]
            Dictionary of symbol -> display name

        Returns
        -------
        pd.DataFrame
            Performance table with 1D, 1W, 1M, YTD returns
        """
        records = []

        for symbol, df in data.items():
            if df.empty:
                continue

            name = ticker_names.get(symbol, symbol)
            current_price = df["close"].iloc[-1] if not df.empty else None

            record = {
                "シンボル": symbol,
                "名称": name,
                "現在値": current_price,
                "1D": calculate_period_return(df, 1),
                "1W": calculate_period_return(df, 5),
                "1M": calculate_period_return(df, 21),
                "YTD": calculate_ytd_return(df),
            }
            records.append(record)

        if not records:
            return pd.DataFrame()

        return pd.DataFrame(records)

    return (
        calculate_performance_metrics,
        calculate_period_return,
        calculate_ytd_return,
    )


@app.cell
def _(
    MAG7_SOX,
    MAJOR_INDICES,
    METALS,
    SECTOR_ETFS,
    TICKER_NAMES,
    calculate_performance_metrics,
    fetch_commodity_data,
    fetch_stock_data_bulk,
    mo,
    selected_days,
):
    """Fetch and display performance data for Tab 1."""
    # Fetch data for all ticker groups
    # Combine all indices and Mag7 for one fetch
    indices_mag7_symbols = MAJOR_INDICES + MAG7_SOX
    indices_mag7_data = fetch_stock_data_bulk(indices_mag7_symbols, selected_days)

    # Fetch sector ETF data
    sector_data = fetch_stock_data_bulk(SECTOR_ETFS, selected_days)

    # Fetch metals data
    metals_data = fetch_commodity_data(METALS, selected_days)

    # Calculate performance tables
    indices_mag7_perf = calculate_performance_metrics(
        indices_mag7_data, TICKER_NAMES
    )
    sector_perf = calculate_performance_metrics(sector_data, TICKER_NAMES)
    metals_perf = calculate_performance_metrics(metals_data, TICKER_NAMES)

    # Store data for tabs
    performance_data = {
        "indices_mag7": indices_mag7_perf,
        "sectors": sector_perf,
        "metals": metals_perf,
    }

    mo.output.clear()
    return (
        indices_mag7_data,
        indices_mag7_perf,
        metals_data,
        metals_perf,
        performance_data,
        sector_data,
        sector_perf,
    )


@app.cell
def _(mo, pd):
    """Helper function to style performance tables with heatmap."""
    from typing import Any

    def style_performance_table(
        df: Any, return_cols: list[str] | None = None
    ) -> Any:
        """Apply heatmap styling to performance table.

        Parameters
        ----------
        df : pd.DataFrame
            Performance table
        return_cols : list[str] | None
            Columns to apply heatmap styling (default: 1D, 1W, 1M, YTD)

        Returns
        -------
        mo.Html
            Styled table as marimo HTML
        """
        if df.empty:
            return mo.md("*データがありません*")

        if return_cols is None:
            return_cols = ["1D", "1W", "1M", "YTD"]

        # Create a copy to avoid modifying original
        styled_df = df.copy()

        # Format numeric columns
        for col in return_cols:
            if col in styled_df.columns:
                styled_df[col] = styled_df[col].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"
                )

        if "現在値" in styled_df.columns:
            styled_df["現在値"] = styled_df["現在値"].apply(
                lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A"
            )

        return mo.ui.table(styled_df, selection=None)

    return (style_performance_table,)


@app.cell
def _(mo, performance_data, selected_days, style_performance_table):
    """Tab 1: Performance Overview content."""
    # Create styled tables
    indices_table = style_performance_table(performance_data["indices_mag7"])
    sector_table = style_performance_table(performance_data["sectors"])
    metals_table = style_performance_table(performance_data["metals"])

    # Create the performance overview tab content
    performance_tab_content = mo.vstack(
        [
            mo.md(f"## パフォーマンス概要 (過去 {selected_days} 日)"),
            mo.md("### 主要指数 & Magnificent 7"),
            indices_table,
            mo.md("### セクターETF"),
            sector_table,
            mo.md("### 貴金属"),
            metals_table,
        ]
    )
    return (
        indices_table,
        metals_table,
        performance_tab_content,
        sector_table,
    )


# =============================================================================
# Tab 2: マクロ指標
# =============================================================================


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
def _(fetch_stock_data_single, selected_period):
    """Fetch VIX data from Yahoo Finance."""
    vix_result = fetch_stock_data_single("^VIX", selected_period)
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


# =============================================================================
# Dashboard Main
# =============================================================================


@app.cell
def _(mo, performance_tab_content, return_distribution_content, tab2_content, tab3_content):
    """Tab navigation for dashboard sections with all implemented tabs."""
    tabs_with_all = mo.ui.tabs(
        {
            "パフォーマンス概要": performance_tab_content,
            "マクロ指標": tab2_content,
            "相関・ベータ分析": tab3_content,
            "リターン分布": return_distribution_content,
        }
    )
    return (tabs_with_all,)


@app.cell(hide_code=True)
def _(mo, selected_period, tabs_with_all):
    """Display main dashboard with tabs."""
    _dashboard = mo.vstack(
        [
            mo.md(f"**選択期間**: {selected_period}"),
            tabs_with_all,
        ],
        gap=2,
    )
    return (_dashboard,)


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
    MarketData, METALS, SECTOR_ETFS, contextlib, get_date_range_from_period, pd, selected_period
):
    """Fetch data for Tab 3 analysis."""
    market_data = MarketData()
    start_date, end_date = get_date_range_from_period(selected_period)

    # Fetch sector ETF data + S&P500 benchmark
    sector_data = {}  # dict[str, DataFrame]
    benchmark_symbol = "SPY"  # S&P500 ETF as benchmark
    sector_symbols = [*SECTOR_ETFS, benchmark_symbol]

    for symbol in sector_symbols:
        try:
            df = market_data.fetch_stock(symbol, start=start_date, end=end_date)
            sector_data[symbol] = df
        except Exception:  # nosec B110 - intentional pass for graceful degradation
            pass

    # Fetch metals data
    metals_data = {}  # dict[str, DataFrame]
    for symbol in METALS:
        try:
            df = market_data.fetch_stock(symbol, start=start_date, end=end_date)
            metals_data[symbol] = df
        except Exception:  # nosec B110 - intentional pass for graceful degradation
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
            except Exception:  # nosec B110 - intentional pass for graceful degradation
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
                except Exception:  # nosec B110 - intentional pass for graceful degradation
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
