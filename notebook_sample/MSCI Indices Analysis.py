import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import pandas as pd
    import polars as pl
    from pathlib import Path
    import sqlite3
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    import seaborn as sns
    import json
    import os
    import sys
    from dotenv import load_dotenv
    from dateutil.relativedelta import relativedelta
    from datetime import datetime, date, timedelta
    from typing import List
    from fredapi import Fred
    from tqdm import tqdm
    from data_check_utils import calculate_missing_stats, extract_dates_in_range
    from database_utils import get_table_names, step1_load_file_to_db, step2_create_variable_tables, step3_create_return_table
    from data_prepare import createDB_bpm_and_factset_code
    from concurrent.futures import ThreadPoolExecutor
    from fred_database_utils import store_fred_database, get_fred_ids_from_file  # type: ignore
    from us_treasury import (
            plot_us_interest_rates_and_spread,
            analyze_yield_curve_pca,
            plot_loadings_and_explained_variance,
            plot_us_interest_rates_and_spread_2
        )
    import warnings
    warnings.simplefilter("ignore")

    FRED_API = os.getenv("FRED_API_KEY")
    Q_DIR = Path().cwd().parent
    DATA_DIR = Q_DIR / "data" / "MSCI_KOKUSAI"
    PRJ_DIR = Q_DIR / "A_001"
    # Factset Benchmark directory
    BM_DIR = Q_DIR / "data/Factset/Benchmark"
    FRED_DIR = Q_DIR / 'data' / 'FRED'
    INDEX_DIR = Q_DIR / 'data' / 'Factset' / 'Index'
    return INDEX_DIR, np, pd, plt, sns, sqlite3


@app.cell
def _(INDEX_DIR, pd, sqlite3):
    _df = pd.read_parquet(INDEX_DIR / 'Index_Price-and-Valuation.parquet')
    db_path = INDEX_DIR / 'Index-Price-and-Valuation.db'
    _conn = sqlite3.connect(db_path)
    for variable in _df['variable'].unique():
        df_slice = _df[_df['variable'] == variable].reset_index(drop=True)
        df_slice.to_sql(variable, _conn, index=False, if_exists='replace')
    _conn.close()
    return (db_path,)


@app.cell
def _(db_path, np, pd, plt, sns, sqlite3):
    _conn = sqlite3.connect(db_path)
    _df_price = pd.read_sql('SELECT * FROM FG_PRICE', con=_conn).drop(columns=['variable'])
    _df_price = pd.pivot(_df_price, index='date', columns='Index', values='value').sort_index()
    _df_price.index = pd.to_datetime(_df_price.index)
    start_date = pd.to_datetime('2015-01-01')
    df_price_slice = _df_price.loc[start_date:]
    # display(df_price)
    df_return_daily = np.log(df_price_slice) - np.log(df_price_slice.shift())
    df_cum_log_return = df_return_daily.fillna(0).cumsum()
    df_cum_return = np.exp(df_cum_log_return)
    df_price_monthly = _df_price.asfreq('BM').sort_index()
    df_return_monthly = np.log(df_price_monthly) - np.log(df_price_monthly.shift())
    df_return_monthly.dropna(inplace=True)
    # display(df_cum_return.head())
    df_price_annual = _df_price.asfreq('BY').sort_index()
    df_return_annual = np.log(df_price_annual) - np.log(df_price_annual.shift())
    df_return_annual.dropna(inplace=True)
    _fig, _axes = plt.subplots(4, 1, figsize=(10, 8), tight_layout=True, sharex=True)
    _fig.suptitle(f"MSCI Index Cumulative Return (start={start_date.strftime('%Y-%m-%d')})")
    # display(df_return_monthly.head())
    index_kokusai = ['MSCI Kokusai Index (World ex Japan)', 'MSCI Kokusai Index (World ex Japan) Growth', 'MSCI Kokusai Index (World ex Japan) Value', 'MSCI Kokusai Quality']
    index_usa_and_world = ['MSCI USA', 'MSCI AC World', 'MSCI Kokusai Index (World ex Japan)', 'MSCI EM (Emerging Markets)']
    index_europe = ['MSCI Germany', 'MSCI France']
    index_asia = ['MSCI Japan', 'MSCI China', 'MSCI Hong Kong', 'MSCI India']
    # display(df_return_annual.head())
    index_group = [index_kokusai, index_usa_and_world, index_europe, index_asia]
    max_y_lim = 4.0
    for _i, index_list in enumerate(index_group):
    # start_date = df_cum_return.index.min()
        for _col in index_list:
            sns.lineplot(df_cum_return, x=df_cum_return.index, y=df_cum_return[_col], ax=_axes[_i], label=_col, linewidth=0.8)
            _axes[_i].legend(loc='upper left')
            _axes[_i].set_ylabel('')
            _axes[_i].set_ylim(0.5, max_y_lim)
    for _i in range(len(index_group)):
        _axes[_i].grid()
    _axes[-1].set_xlabel('Date')
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### EPS
    """)
    return


@app.cell
def _(INDEX_DIR, display, np, pd, plt, sns, sqlite3):
    db_path_1 = INDEX_DIR / 'Index-Price-and-Valuation.db'
    _conn = sqlite3.connect(db_path_1)
    df_eps = pd.read_sql("\n        SELECT\n            date, value\n        FROM\n            FMA_EPS_LTM\n        WHERE\n            `Index`=='MSCI Kokusai Index (World ex Japan)'\n    ", con=_conn, index_col='date').rename(columns={'value': 'EPS_LTM'})
    display(df_eps.head())
    _df_price = pd.read_sql("\n        SELECT\n            date, value\n        FROM\n            FG_PRICE\n        WHERE\n            `Index`=='MSCI Kokusai Index (World ex Japan)'\n    ", con=_conn, index_col='date').rename(columns={'value': 'price'})
    _df = pd.merge(df_eps, _df_price, left_index=True, right_index=True).fillna(method='ffill')
    _df = _df.assign(PER=lambda row: row['price'].div(row['EPS_LTM']), log_return=lambda row: (np.log(row['price']) - np.log(row['price'].shift())) * 12, EPS_chg=lambda row: row['EPS_LTM'].pct_change() * 12).fillna(0)
    _df.index = pd.to_datetime(_df.index)
    _df['cum_return'] = np.exp(_df['log_return'].div(12).cumsum())
    display(_df)
    _fig, _axes = plt.subplots(4, 1, figsize=(10, 6), sharex=True)
    for _i, _col in enumerate(['price', 'PER', 'EPS_LTM', 'EPS_chg']):
        ax = _axes[_i]
        sns.lineplot(_df, x=_df.index, y=_df[_col], label=_col, ax=_axes[_i])
        ax.legend(loc='upper left')
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Interest rate, ISM-PMI
    """)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
