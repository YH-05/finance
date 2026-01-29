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
    ## `yfinance_news.ipynb`
    """)


@app.cell
def _():
    import pandas as pd
    import yfinance as yf

    return (yf,)


@app.cell
def _(display, yf):
    news = yf.Ticker("AAPL").news
    display(news)


if __name__ == "__main__":
    app.run()
