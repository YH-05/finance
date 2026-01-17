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

    return datetime, mo, np, pd, timedelta


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

    # Initialize MarketData instance
    market_data = MarketData()

    def get_date_range(days: int) -> tuple[Any, Any]:
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

    def fetch_stock_data(symbols: list[str], days: int) -> dict[str, Any]:
        """Fetch stock data for given symbols.

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
        start_date, end_date = get_date_range(days)
        result: dict[str, Any] = {}

        for symbol in symbols:
            try:
                df = market_data.fetch_stock(
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
        start_date, end_date = get_date_range(days)
        result: dict[str, Any] = {}

        for symbol in symbols:
            try:
                df = market_data.fetch_stock(
                    symbol, start=start_date, end=end_date
                )
                result[symbol] = df
            except Exception:  # nosec B110 - Intentional: skip unavailable symbols
                pass

        return result

    return (
        fetch_commodity_data,
        fetch_stock_data,
        get_date_range,
        market_data,
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
    fetch_stock_data,
    mo,
    selected_days,
):
    """Fetch and display performance data for Tab 1."""
    # Fetch data for all ticker groups
    # Combine all indices and Mag7 for one fetch
    indices_mag7_symbols = MAJOR_INDICES + MAG7_SOX
    indices_mag7_data = fetch_stock_data(indices_mag7_symbols, selected_days)

    # Fetch sector ETF data
    sector_data = fetch_stock_data(SECTOR_ETFS, selected_days)

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


@app.cell
def _(mo, performance_tab_content):
    """Tab navigation with actual content."""
    dashboard_tabs = mo.ui.tabs(
        {
            "パフォーマンス概要": performance_tab_content,
            "マクロ指標": mo.md(
                "## Tab 2: マクロ指標\n\n"
                "- 米国金利（10Y, 2Y, FF）\n"
                "- イールドスプレッド\n"
                "- VIX & ハイイールドスプレッド\n\n"
                "> *後続の Issue で実装予定*"
            ),
            "相関・ベータ分析": mo.md(
                "## Tab 3: 相関・ベータ分析\n\n"
                "- セクターETFローリングベータ（vs S&P500）\n"
                "- ドルインデックス vs 貴金属相関\n"
                "- 相関ヒートマップ\n\n"
                "> *後続の Issue で実装予定*"
            ),
            "リターン分布": mo.md(
                "## Tab 4: リターン分布\n\n"
                "- 週次リターンヒストグラム\n"
                "- 統計サマリー\n\n"
                "> *後続の Issue で実装予定*"
            ),
        }
    )
    return (dashboard_tabs,)


@app.cell(hide_code=True)
def _(dashboard_tabs, mo, period_dropdown, selected_days):
    """Main dashboard layout."""
    mo.vstack(
        [
            mo.md(
                """
                # Market Dashboard

                株式市場・マクロ経済データ確認用のインタラクティブダッシュボード

                ---
                """
            ),
            mo.hstack([period_dropdown], justify="start"),
            mo.md(f"**選択期間**: {selected_days} 日"),
            dashboard_tabs,
        ]
    )


if __name__ == "__main__":
    app.run()
