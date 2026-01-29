import marimo

__generated_with = "0.19.6"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `market_report_notebook.ipynb`
    """)


@app.cell
def _():
    from database.utils.logging_config import setup_logging

    setup_logging(level="ERROR", force=True)


@app.cell
def _(display):
    from datetime import datetime, timedelta

    from market.yfinance import FetchOptions, Interval, YFinanceFetcher

    fetcher = YFinanceFetcher()

    symbols = ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "META", "AMZN"]
    start_date = (datetime.today() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
    end_date = datetime.today().strftime("%Y-%m-%d")

    # 複数銘柄を一括取得
    mag7_data = fetcher.fetch_multiple(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=Interval.DAILY,
    )

    # データフレームへの変換
    for result in mag7_data:
        df_data = (
            result.data[["Close"]]
            .reset_index()
            .rename(columns={"Close": "value"})
            .assign(symbol=result.symbol, variable="close")
            .reindex(columns=["Date", "symbol", "variable", "value"])
        )
        display(df_data)


if __name__ == "__main__":
    app.run()
