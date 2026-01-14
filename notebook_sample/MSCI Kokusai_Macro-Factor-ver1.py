import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # MSCI Kokusai Constituents Macro Factor Model Ver1

    金利ファクター

    $$
    R = \alpha + \beta_{\mathrm{mkt}}r_{\mathrm{mkt}} + \beta_{\mathrm{level}}r_{\mathrm{level}}+ \beta_{\mathrm{slope}}r_{\mathrm{slope}}+ \beta_{\mathrm{curvature}}r_{\mathrm{curvature}} + \epsilon
    $$

    -   $\beta_{\mathrm{mkt}}$: マーケット(MSCI Kokusai)ベータ
    -   $\beta_{\mathrm{level}}$: US 金利データを主成分分析したのちの第 1 主成分(level)によるベータ
    -   $\beta_{\mathrm{slope}}$: 第 2 主成分(slope)によるベータ
    -   $\beta_{\mathrm{curvature}}$: 第 3 主成分(curvature)によるベータ
    """)
    return


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
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.gridspec as gridspec
    from matplotlib.ticker import PercentFormatter
    from matplotlib.ticker import MultipleLocator
    import statsmodels.api as sm
    import seaborn as sns
    import json
    import os
    import sys
    from sklearn.decomposition import PCA
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

    import warnings

    warnings.simplefilter("ignore")


    Q_DIR = Path().cwd().parent.parent
    DATA_DIR = Q_DIR / "data" / "MSCI_KOKUSAI"
    PRJ_DIR = Q_DIR / "A_001"
    # Factset Benchmark directory
    BM_DIR = Q_DIR / "data/Factset/Benchmark"
    FRED_DIR = Path().cwd().parents[2] / "FRED"
    print(f"FRED directory: {FRED_DIR}")


    fred_module = str((FRED_DIR / "src").resolve())
    if fred_module not in sys.path:
        sys.path.append(fred_module)
        print(f"{fred_module}をsys.pathに追加しました。")

    from fred_database_utils import store_fred_database  # type: ignore
    from us_treasury import (
        plot_us_interest_rates_and_spread,
        analyze_yield_curve_pca,
        plot_loadings_and_explained_variance,
        )

    FRED_API = os.getenv("FRED_API_KEY")
    return (
        DATA_DIR,
        FRED_DIR,
        analyze_yield_curve_pca,
        gridspec,
        np,
        pd,
        plot_loadings_and_explained_variance,
        plt,
        sm,
        sns,
        sqlite3,
        tqdm,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load Data
    """)
    return


@app.cell
def _(DATA_DIR, FRED_DIR, display, np, pd, sqlite3):
    db_daily_price = DATA_DIR / "MSCI_KOKUSAI_and_BM_Daily_Price.db"
    db_fred = FRED_DIR / "FRED.db"

    df_price = pd.read_sql(
        "SELECT * FROM FG_PRICE_Daily ORDER BY P_SYMBOL, date",
        sqlite3.connect(db_daily_price),
        parse_dates=["date"],
    ).assign(log_value=lambda x: np.log(x["value"]))

    # return data
    df_return = (
        pd.pivot(df_price, index="date", columns="P_SYMBOL", values="log_value")
        .diff()
        .sort_index()
    )
    df_return = df_return.diff().dropna(how="all")

    print("return data")
    display(df_return)


    # interest rates
    table_list = [
        "DFF",
        "DGS1MO",
        "DGS3MO",
        "DGS6MO",
        "DGS1",
        "DGS2",
        "DGS3",
        "DGS5",
        "DGS7",
        "DGS10",
        "DGS20",
        "DGS30",
    ]
    dfs_yield = []
    for table in table_list:
        df = (
            pd.read_sql(
                f"SELECT * FROM {table}", sqlite3.connect(db_fred), parse_dates=["date"]
            )
            .assign(tenor=table)
            .rename(columns={table: "value"})
        )
        dfs_yield.append(df)

    df_yield = (
        pd.pivot(
            pd.concat(dfs_yield, ignore_index=True),
            index="date",
            columns="tenor",
            values="value",
        )
        .sort_index()
        .reindex(columns=table_list)
    )

    print("yield data")
    display(df_yield)
    return df_return, df_yield


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 金利変動幅に対して PCA
    """)
    return


@app.cell
def _(df_yield, plot_loadings_and_explained_variance):
    df_yield_copy = df_yield.copy()
    df_yield_copy.drop(columns=["DFF"], inplace=True)
    df_yield_diff = df_yield_copy.diff().dropna(how="any")
    # display(df_yield_diff)
    plot_loadings_and_explained_variance(df_original=df_yield_diff)
    return (df_yield_copy,)


@app.cell
def _(df_yield, df_yield_copy, gridspec, pd, plt, sns):
    df_yield_ann = df_yield_copy.groupby(df_yield_copy.index.year).tail(1).dropna(how='any')
    fig = plt.figure(figsize=(8, 14), tight_layout=True)
    # === plot ===
    fig.suptitle('US Treasury Yield Curve')
    num_maturity = len(df_yield.columns.tolist())
    # --- GridSpec ---
    gs_master = gridspec.GridSpec(num_maturity + 1, 1, figure=fig, height_ratios=[8] + [1] * num_maturity)
    gs_yield_curve = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=gs_master[0, 0])
    ax_yield_curve = fig.add_subplot(gs_yield_curve[0, 0])
    gs_time_series = gridspec.GridSpecFromSubplotSpec(num_maturity, 1, subplot_spec=gs_master[1:, 0], hspace=0.1)
    # yield curve
    xticks = [1, 3, 6, 1 * 12, 2 * 12, 3 * 12, 5 * 12, 7 * 12, 10 * 12, 15 * 12, 18 * 12]
    xlabels = ['1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y']
    # yield curve time series(line chart)
    date_list = df_yield_ann.index[::3]
    palette = sns.color_palette('Blues', n_colors=len(date_list))
    for i, _date in enumerate(date_list):
        df_slice = pd.DataFrame(df_yield_ann.loc[_date].T)
        sns.lineplot(df_slice, x=xticks, y=df_slice.values.flatten(), ax=ax_yield_curve, marker='o', label=_date.strftime('%Y/%m/%d'), color=palette[i])
    # --- x axis ticks ---
    ax_yield_curve.set_xscale('log')
    ax_yield_curve.set_xticks(xticks)
    ax_yield_curve.set_xticklabels(xlabels)
    ax_yield_curve.set_xlabel('Maturity')
    ax_yield_curve.set_ylabel('Yield (%)')
    ax_yield_curve.legend(bbox_to_anchor=(1, 1), title='date', frameon=True, edgecolor='grey')
    ax_ref = None
    df_to_plot = df_yield.loc['2000-01-01':]
    for i, maturity in enumerate(df_to_plot.columns.tolist()):
        if i == 0:
            ax = fig.add_subplot(gs_time_series[i, 0])
            ax_ref = ax
        else:
            ax = fig.add_subplot(gs_time_series[i, 0], sharex=ax_ref)
        color = 'red' if maturity == 'DFF' else 'blue'
        sns.lineplot(data=df_to_plot, x=df_to_plot.index, y=df_to_plot.iloc[:, i], ax=ax, alpha=0.7, color=color)
        ax.set_ylabel('')
        ax.text(1.01, 0.5, maturity, transform=ax.transAxes, va='center', ha='center', fontsize=9)
        if i < num_maturity - 1:
            ax.set_xlabel('')
            ax.tick_params(labelbottom=False)
        else:
            ax.set_xlabel('date')
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 金利ファクター
    """)
    return


@app.cell
def _(analyze_yield_curve_pca, df_return, df_yield, display, pd, sm):
    # index return
    _kokusai_return = df_return[['MSCI Kokusai Index (World ex Japan)']]
    display(_kokusai_return.head())
    _df_return_ex_benchmark = df_return.drop(columns=['MSCI Kokusai Index (World ex Japan)', 'S&P 500'])
    # 個別銘柄 return
    display(_df_return_ex_benchmark.head())
    _df_pca, _ = analyze_yield_curve_pca(df_yield)
    display(_df_pca.head())
    _symbol = 'MSCI-US'
    _df_merged = pd.merge(_kokusai_return, _df_return_ex_benchmark[[_symbol]], left_index=True, right_index=True)
    _df_merged = pd.merge(_df_merged, _df_pca, left_index=True, right_index=True).dropna(how='any', ignore_index=True)
    # yield diff pca
    display(_df_merged.head())
    _X = _df_merged[['MSCI Kokusai Index (World ex Japan)', 'PC1', 'PC2', 'PC3']]
    _Y = _df_merged[_symbol]
    # merge
    _X = sm.add_constant(_X)
    _model = sm.OLS(_Y, _X).fit()
    # OLS
    print(_model.summary())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 決定係数が閾値を超える銘柄を特定する。
    """)
    return


@app.cell
def _(analyze_yield_curve_pca, df_return, df_yield, pd, sm, tqdm):
    # index return
    _kokusai_return = df_return[['MSCI Kokusai Index (World ex Japan)']]
    # 個別銘柄 return
    _df_return_ex_benchmark = df_return.drop(columns=['MSCI Kokusai Index (World ex Japan)', 'S&P 500'])
    _df_pca, _ = analyze_yield_curve_pca(df_yield)
    symbol_list = []
    # yield diff pca
    model_list = []
    threshold_r_squared = 0.3
    # merge
    for _symbol in tqdm(_df_return_ex_benchmark.columns.tolist()):
        _df_merged = pd.merge(_kokusai_return, _df_return_ex_benchmark[[_symbol]], left_index=True, right_index=True)
        _df_merged = pd.merge(_df_merged, _df_pca, left_index=True, right_index=True).dropna(how='any', ignore_index=True)
        if not len(_df_merged) == 0:
            _X = _df_merged[['MSCI Kokusai Index (World ex Japan)', 'PC1', 'PC2', 'PC3']]
            _Y = _df_merged[_symbol]
            _X = sm.add_constant(_X)
            _model = sm.OLS(_Y, _X).fit()
            r_squared = _model.rsquared
            if r_squared >= threshold_r_squared:
                symbol_list.append(_symbol)
                model_list.append(_model)
    print(f'決定係数が{int(threshold_r_squared * 10)}割を超える銘柄が{len(symbol_list)}銘柄ありました。')  # OLS
    return model_list, symbol_list


@app.cell
def _(symbol_list):
    print(symbol_list)
    return


@app.cell
def _(display, model_list):
    display(model_list[0].resid)
    print(model_list[0].summary())
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
