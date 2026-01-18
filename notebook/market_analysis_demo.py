import marimo

__generated_with = "0.19.4"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `market_analysis.ipynb`
    """)
    return


@app.cell
def _():
    from market_analysis.utils.logging_config import setup_logging
    setup_logging(level="WARNING", force=True)
    return


@app.cell
def _():
    from market_analysis import MarketData, Analysis, Chart
    return Chart, MarketData


@app.cell
def _(Chart, MarketData):
    data = MarketData()
    df_stock = data.fetch_stock("NVDA", start="2020-01-01")
    # display(df_stock)
    chart = Chart(df_stock, title='NVDA')
    fig = chart.price_chart(overlays=['EMA_20', 'EMA_50'])
    fig.show()
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
