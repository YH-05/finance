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

    from market_analysis import MarketData, Analysis, Chart, MarketPerformanceAnalyzer
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return Chart, MarketData, MarketPerformanceAnalyzer, os


@app.cell
def _(Chart, MarketData):
    data = MarketData()
    df_stock = data.fetch_stock("NVDA", start="2020-01-01")
    # display(df_stock)
    chart = Chart(df_stock, title='NVDA')
    fig = chart.price_chart(overlays=['EMA_20', 'EMA_50', 'EMA_200'])
    fig.show()
    return


@app.cell
def _(MarketData, display, os):
    fred_data = MarketData(fred_api_key=os.environ.get("FRED_API_KEY"))
    df_gdp = fred_data.fetch_fred("GDP")
    display(df_gdp)
    return


@app.cell
def _():
    import yfinance as yf
    aapl = yf.Ticker("AAPL").get_analyst_price_targets()
    print(aapl)
    return


@app.cell
def _(MarketPerformanceAnalyzer):
    analyzer = MarketPerformanceAnalyzer()
    price = analyzer.price_data

    price.tail(7)

    performance_dict = analyzer.get_performance_groups()
    performance_dict['Mag7_SOX']
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
