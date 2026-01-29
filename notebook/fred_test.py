import marimo

__generated_with = "0.19.6"
app = marimo.App()


@app.cell
def _():
    from market.fred import fetcher
    import pandas as pd
    from pathlib import Path
    return (fetcher,)


@app.cell
def _(display, fetcher):
    fred = fetcher.FREDFetcher()
    fred.load_presets()
    categories = fred.get_preset_categories()
    series_treasury = fred.get_preset_symbols('Treasury Yields')
    display(series_treasury)
    return (fred,)


@app.cell
def _(display, fred):
    data = fred.fetch_preset('Treasury Yields')
    display(data)
    return (data,)


@app.cell
def _(data, display):
    display(data[0].data.assign(symbol=data[0].symbol))
    return


if __name__ == "__main__":
    app.run()
