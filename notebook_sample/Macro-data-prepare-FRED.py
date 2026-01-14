import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Macro-data-prepare-FRED.ipynb

    FRED の日次データなどを集める
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import sqlite3
    from pathlib import Path

    import pandas as pd
    from fred_database_utils import get_fred_ids_from_file, store_fred_database

    ROOT_DIR = Path().cwd().parent
    FRED_DIR = ROOT_DIR / "data/FRED"
    return (
        FRED_DIR,
        ROOT_DIR,
        get_fred_ids_from_file,
        pd,
        sqlite3,
        store_fred_database,
    )


@app.cell
def _(FRED_DIR, get_fred_ids_from_file, store_fred_database):
    series_id_list = get_fred_ids_from_file(file_path=FRED_DIR / "fred_series.json")
    db_path = FRED_DIR / "FRED.db"
    store_fred_database(db_path=db_path, series_id_list=series_id_list)
    return (db_path,)


@app.cell
def _(db_path, display, pd, sqlite3):
    conn = sqlite3.connect(db_path)
    table_list = ["GDPC1", "CLVMNACSCAB1GQEA19", "JPNRGDPEXP"]
    table_list = {
        "GDPC1": "Real GDP - US",
        "CLVMNACSCAB1GQEA19": "Real GDP - EUR",
        "JPNRGDPEXP": "Real GDP - Japan",
    }
    dfs = []
    for table in table_list.keys():
        df = (
            pd.read_sql(f"SELECT * FROM `{table}`", con=conn, parse_dates="date")
            .drop_duplicates()
            .rename(columns={table: "value"})
            .assign(variable=table_list[table])
        )
        dfs.append(df)
    _gdp = pd.pivot(
        pd.concat(dfs, ignore_index=True),
        index="date",
        columns="variable",
        values="value",
    )
    display(_gdp)
    gdp_growth = _gdp.pct_change(4).dropna()
    gdp_growth.columns = [col + "(YoY)" for col in gdp_growth.columns]
    display(gdp_growth)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Real GDP

    データは[World Bank DataBank](https://databank.worldbank.org/reports.aspx?source=2&series=NY.GDP.MKTP.KD&country=#)より取得。GDP(constant 2015 US$)
    """)


@app.cell
def _(ROOT_DIR, display, pd):
    WORLD_BANK_DIR = ROOT_DIR / "data/World Bank"
    _gdp = pd.read_excel(WORLD_BANK_DIR / "world_bank-RealGDP.xlsx", sheet_name="Data")
    display(_gdp)


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
