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
def _(mo):
    """Tab navigation for dashboard sections."""
    tabs = mo.ui.tabs(
        {
            "パフォーマンス概要": mo.md("## Tab 1: パフォーマンス概要\n\n- S&P500 & 主要指数のパフォーマンス\n- Magnificent 7 & SOX指数\n- セクターETF（XL系）\n- 貴金属"),
            "マクロ指標": mo.md("## Tab 2: マクロ指標\n\n- 米国金利（10Y, 2Y, FF）\n- イールドスプレッド\n- VIX & ハイイールドスプレッド"),
            "相関・ベータ分析": mo.md("## Tab 3: 相関・ベータ分析\n\n- セクターETFローリングベータ（vs S&P500）\n- ドルインデックス vs 貴金属相関\n- 相関ヒートマップ"),
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


if __name__ == "__main__":
    app.run()
