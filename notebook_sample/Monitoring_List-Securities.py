import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Monitoring_List-Securities.ipynb
    """)
    return


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import pandas as pd
    from pathlib import Path
    import numpy as np
    import datetime
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.graph_objects as go
    import matplotlib.ticker as mtick
    from pprint import pprint
    import yaml
    import sqlite3
    from database_utils import get_table_names, append_diff_to_sqlite
    import factset_downloaded_data_utils as f_db_utils
    import ROIC_make_data_files_ver2 as roic_utils
    import bloomberg_utils as bbg_utils
    import warnings

    warnings.simplefilter("ignore")

    UNIVERSE_CODE = "MSXJPN_AD"

    ROOT_DIR = Path().cwd().parent
    DATA_DIR = ROOT_DIR / "data"
    FACTSET_DIR = DATA_DIR / "Factset"
    BPM_DIR = DATA_DIR / "BPM"
    INDEX_DIR = FACTSET_DIR / f"Financials/{UNIVERSE_CODE}"
    INDEX_CONSTITUENTS_DIR = FACTSET_DIR / "Index_Constituents"
    BBG_DIR = DATA_DIR / "Bloomberg"


    db_path = INDEX_DIR / "Financials_and_Price.db"
    factset_index_db_path = INDEX_CONSTITUENTS_DIR / "Index_Constituents.db"
    bpm_db_path = BPM_DIR / "Index_Constituents.db"
    bloomberg_db_path =BBG_DIR / "Bloomberg.db"
    return (
        UNIVERSE_CODE,
        bbg_utils,
        bloomberg_db_path,
        bpm_db_path,
        datetime,
        pd,
        sqlite3,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## MSCI KOKUSAI 構成銘柄取得
    """)
    return


@app.cell
def _(UNIVERSE_CODE, bpm_db_path, datetime, display, pd, sqlite3):
    conn = sqlite3.connect(bpm_db_path)
    start_date = "2020-01-01"
    end_date = datetime.datetime.today().strftime("%Y-%m-%d")
    df = pd.read_sql(
        f"SELECT * FROM {UNIVERSE_CODE} WHERE date>='{start_date}' AND date<='{end_date}'",
        con=conn,
    )
    display(df)

    sedol_list = df["SEDOL"].dropna().unique().tolist()
    cusip_list = df["CUSIP"].dropna().unique().tolist()

    print(len(sedol_list))
    print(len(cusip_list))
    return df, end_date, sedol_list, start_date


@app.cell
def _(df, display):
    display(df[df["SEDOL"] == "688692"].tail())
    return


@app.cell
def _(
    bbg_utils,
    bloomberg_db_path,
    display,
    end_date,
    pd,
    sedol_list,
    start_date,
):
    bbg = bbg_utils.BlpapiCustom()
    df_test = bbg.get_historical_data(
        securities=[f"{s.zfill(7)} Equity" for s in sedol_list],
        fields=["PX_LAST"],
        start_date=start_date.replace("-", ""),
        # end_date=datetime.date.today().strftime("%Y%m%d"),
        end_date=end_date.replace("-", ""),
        currency="USD",
    ).reset_index()
    df_test = pd.melt(df_test, id_vars="Date", var_name="SEDOL", value_name="Price")

    display(df_test)
    bbg.store_to_database(
        df=df_test,
        db_path=bloomberg_db_path,
        table_name="price_sedol",
        primary_keys=["Date", "SEDOL"],
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
