import marimo

__generated_with = "0.19.6"
app = marimo.App()


@app.cell
def _():
    import pandas as pd

    from market_analysis import MarketData


if __name__ == "__main__":
    app.run()
