import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Reference

    -   [FRED](https://fred.stlouisfed.org/searchresults/?st=ICE%20BofA)
    -   [Gemini](https://gemini.google.com/app/a0cd28b75b80675e?utm_source=app_launcher&utm_medium=owned&utm_campaign=base_all)
    -   [Gemini](https://gemini.google.com/app/0da10f614b7e7434?utm_source=app_launcher&utm_medium=owned&utm_campaign=base_all)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # MSCI Kokusai Constituents Macro Factor Model Ver2

    ## 回帰モデル

    $$
    R_i - R_f = \alpha
    + \beta_{\mathrm{mkt}}(R_{\mathrm{mkt}} - R_f)
    + \left[\beta_{\mathrm{level}}F_{\mathrm{level}}
    + \beta_{\mathrm{slope}}F_{\mathrm{slope}}
    + \beta_{\mathrm{curvature}}F_{\mathrm{curvature}}\right]
    + \beta_{X}F_{X}
    + \beta_{\mathrm{Inflation}}F_{\mathrm{Inflation}}
    + \epsilon_{i}
    $$

    -   $R_i$: 個別銘柄リターン
    -   $R_f$: リスクフリーレート（米国 3 ヶ月物財務省短期証券 TBill）、日次リターン計測用。FRED シリーズは`DTB3`。長期の場合は 10 年物財務省長期証券を使用。
        -   年率ベースであるため、日次に変換。
    -   $\beta_{\mathrm{mkt}}$: マーケット(MSCI Kokusai)ベータ。リスクフリーレートからの指数の超過収益を使う。

    ### 金利ベータ

    -   $\beta_{\mathrm{level}}$: US 金利データを主成分分析したのちの第 1 主成分(level)によるベータ
    -   $\beta_{\mathrm{slope}}$: 第 2 主成分(slope)によるベータ
    -   $\beta_{\mathrm{curvature}}$: 第 3 主成分(curvature)によるベータ

    ### クレジット orVIX ベータ: $\beta_{X}$

    次の 1 または 2 を使用。

    1.  $\beta_{\mathrm{FtoQ}}$: Flight to Quality ファクターによるベータ。

        定義は米国ハイイールド債スプレッド（FRED シリーズ:`BAMLH0A0HYM2` ）と米国投資適格級スプレッド（FRED シリーズ`BAMLC0A0CM`）の差分。"質への逃避"をモデル化したもの。このファクターが拡大する時、安全な投資適格債に比べて、リスクの高いハイイールド債を極端に避けている（+より高いリスクプレミアムを要求している）ことを意味する。これは市場の恐怖感を抽出したファクターとなりうる。

        企業の倒産リスクをどれだけ深刻に捉えているかを直接反映する。実際の売買の**行動の結果**が FtoQ ファクターに現れる。また、リスクの識別・選別という情報を含み、単にリスクオフになっているだけでなく、**質の低い社債が質の高い社債に比べてどれだけ余計に売られているか**を定量化している。

    2.  $\beta_{\mathrm{VIX}}$: VIX 指数によるベータ。FRED シリーズは`VIXCLS`。

        S&P 500 の株価が将来どれだけ大きく変動するかという市場予想を反映する。これは企業の信用リスクだけでなく、地政学リスクや政治不安といった不確実性にも反応する。VIX は将来の変動を予想してプットオプションなどを買う行動の結果である。よって VIX が FtoQ に先行して急騰することもある。

    ### インフレベータ

    -   $\beta_{\mathrm{Inflation}}$: インフレファクターベータ。5 年または 10 年ブレークイーブン・インフレ率を使う。
        -   FRED シリーズは`T5YIE`（5 年） or `T10YIE`（10 年）。

    ### 直行化

    [Google Document を参照](https://docs.google.com/document/d/1OJ1hipUb0jYnwNXVZmq4FhBTmOqx0nSz0VpI-uF8PRQ/edit?tab=t.0)
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
    from make_factor import orthogonalize
    from data_prepare import createDB_bpm_and_factset_code
    from concurrent.futures import ThreadPoolExecutor
    import warnings
    warnings.simplefilter('ignore')
    Q_DIR = Path().cwd().parent.parent
    DATA_DIR = Q_DIR / 'data' / 'MSCI_KOKUSAI'
    PRJ_DIR = Q_DIR / 'A_001'
    BM_DIR = Q_DIR / 'data/Factset/Benchmark'
    FRED_DIR = Path().cwd().parents[2] / 'FRED'
    print(f'FRED directory: {FRED_DIR}')
    fred_module = str((FRED_DIR / 'src').resolve())
    if fred_module not in sys.path:
        sys.path.append(fred_module)
        print(f'{fred_module}をsys.pathに追加しました。')
    from fred_database_utils import store_fred_database, get_fred_ids_from_file, load_data_from_database
    from us_treasury import plot_us_interest_rates_and_spread, analyze_yield_curve_pca, plot_loadings_and_explained_variance, load_yield_data_from_database
    FRED_API = os.getenv('FRED_API_KEY')
    # Factset Benchmark directory
    series_id_list = get_fred_ids_from_file(FRED_DIR / 'fred_series.json')
    _db_path = FRED_DIR / 'FRED.db'
    # Prepare FRED Data
    store_fred_database(db_path=_db_path, series_id_list=series_id_list, FRED_API=FRED_API)
    return (
        BM_DIR,
        DATA_DIR,
        FRED_DIR,
        analyze_yield_curve_pca,
        load_data_from_database,
        load_yield_data_from_database,
        np,
        orthogonalize,
        pd,
        plot_loadings_and_explained_variance,
        sqlite3,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Prepare Data
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Return data
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### MSCI Kokusai Constituents
    """)
    return


@app.cell
def _(DATA_DIR, display, np, pd, sqlite3):
    _db_path = DATA_DIR / 'MSCI_KOKUSAI_Price_Daily.db'
    _conn = sqlite3.connect(_db_path)
    return_secs = pd.read_sql('SELECT * FROM FG_PRICE_Daily ORDER BY date', con=_conn, parse_dates=['date']).assign(log_value=lambda row: np.log(row['value']))
    return_secs['Return'] = return_secs.groupby('P_SYMBOL')['log_value'].diff()
    return_secs = return_secs[['date', 'P_SYMBOL', 'Return']].dropna(how='any', ignore_index=True)
    display(return_secs)
    return (return_secs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### MSCI Kokusai Index
    """)
    return


@app.cell
def _(BM_DIR, display, np, pd, sqlite3):
    _db_path = BM_DIR / 'BM_Price_Daily.db'
    _conn = sqlite3.connect(_db_path)
    return_index = pd.read_sql("SELECT * FROM FG_PRICE_Daily WHERE P_SYMBOL='MSCI Kokusai Index (World ex Japan)' ORDER BY date", con=_conn, parse_dates=['date']).assign(log_value=lambda row: np.log(row['value'])).assign(Return=lambda row: row['log_value'].diff()).dropna(ignore_index=True)[['date', 'P_SYMBOL', 'Return']]
    _conn.close()
    display(return_index)
    return (return_index,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Calculate Excess Return
    """)
    return


@app.cell
def _(FRED_DIR, display, pd, return_index, return_secs, sqlite3):
    _db_path = FRED_DIR / 'FRED.db'
    _conn = sqlite3.connect(_db_path)
    risk_free_rate = pd.read_sql('SELECT * FROM DTB3', con=_conn, parse_dates=['date']).assign(DTB3=lambda row: row['DTB3'].div(252 * 100))
    _conn.close()
    print('Risk free rate(DTB3)')
    display(risk_free_rate)
    excess_return_secs = pd.merge(return_secs, risk_free_rate, on=['date'], how='left').dropna(how='any', ignore_index=True).assign(Excess_Return=lambda row: row['Return'].sub(row['DTB3']))  # convert to daily data
    print('Excess return of securities')
    display(excess_return_secs)
    excess_return_index = pd.merge(return_index, risk_free_rate, on=['date'], how='left').dropna(how='any', ignore_index=True).assign(Factor_Market=lambda row: row['Return'].sub(row['DTB3']))
    print('Excess return of MSCI Kokusai Index')
    display(excess_return_index)
    return excess_return_index, excess_return_secs


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Interest Rate Factor

    #### 金利変動幅に対して PCA(Leve, Slope, Curvature)
    """)
    return


@app.cell
def _(
    FRED_DIR,
    analyze_yield_curve_pca,
    display,
    load_yield_data_from_database,
    plot_loadings_and_explained_variance,
):
    _db_path = FRED_DIR / 'FRED.db'
    df_yield = load_yield_data_from_database(db_path=_db_path)
    display(df_yield.head())
    display(df_yield.tail())
    plot_loadings_and_explained_variance(df_yield=df_yield)
    # Check: loading and contribution
    df_pca, pca = analyze_yield_curve_pca(df_yield=df_yield)
    df_pca = df_pca.assign(Level_Shock=lambda row: row['PC1'].diff(), Slope_Shock=lambda row: row['PC2'].diff(), Curvature_Shock=lambda row: row['PC3'].diff()).dropna()
    # PCA and PCA Shock
    display(df_pca)
    return (df_pca,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Flight to Quality Factor and Inflation Factor
    """)
    return


@app.cell
def _(FRED_DIR, display, load_data_from_database, pd):
    # Flight to Quality Factor
    _db_path = FRED_DIR / 'FRED.db'
    df_FtoQ = load_data_from_database(db_path=_db_path, series_id_list=['BAMLH0A0HYM2', 'BAMLC0A0CM'])
    df_FtoQ = pd.pivot(df_FtoQ, index='date', columns='variable', values='value').sort_index().assign(FtoQ=lambda row: row['BAMLH0A0HYM2'].sub(row['BAMLC0A0CM'])).assign(FtoQ_Shock=lambda row: row['FtoQ'].diff()).dropna(how='any')[['FtoQ_Shock']]
    display(df_FtoQ)
    df_Inflation = load_data_from_database(db_path=_db_path, series_id_list=['T10YIE']).set_index('date').assign(Inflation_Shock=lambda row: row['value'].diff()).dropna()[['Inflation_Shock']]
    # Inflation Factor
    display(df_Inflation)
    return df_FtoQ, df_Inflation


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 直行化
    """)
    return


@app.cell
def _(
    df_FtoQ,
    df_Inflation,
    df_pca,
    display,
    excess_return_index,
    orthogonalize,
    pd,
):
    df_factor = excess_return_index.copy().set_index("date")[["Factor_Market"]]
    df_factor = pd.merge(
        df_factor,
        df_pca[["Level_Shock", "Slope_Shock", "Curvature_Shock"]],
        left_index=True,
        right_index=True,
    )
    df_factor = pd.merge(df_factor, df_FtoQ, left_index=True, right_index=True)
    df_factor = pd.merge(
        df_factor, df_Inflation, left_index=True, right_index=True
    ).dropna()
    # display(df_factor)

    # 金利ファクター直行化
    df_factor["Factor_Level"] = orthogonalize(
        df_factor["Level_Shock"], df_factor["Factor_Market"]
    )
    df_factor["Factor_Slope"] = orthogonalize(
        df_factor["Slope_Shock"], df_factor["Factor_Market"]
    )
    df_factor["Factor_Curvature"] = orthogonalize(
        df_factor["Curvature_Shock"], df_factor["Factor_Market"]
    )

    # FtoQファクター直行化: マーケットと金利ファクターに対して直行化
    regressors_ftoq = df_factor[
        ["Factor_Market", "Factor_Level", "Factor_Slope", "Factor_Curvature"]
    ]
    df_factor["Factor_FtoQ"] = orthogonalize(
        df_factor["FtoQ_Shock"], regressors=regressors_ftoq
    )

    # インフレファクター直行化: マーケット、金利ファクター、FtoQファクターに対して直行化
    regressors_inflation = df_factor[
        ["Factor_Market", "Factor_Level", "Factor_Slope", "Factor_Curvature", "Factor_FtoQ"]
    ]
    df_factor["Factor_Inflation"] = orthogonalize(
        df_factor["Inflation_Shock"], regressors=regressors_inflation
    )

    df_factor = df_factor[
        [
            "Factor_Market",
            "Factor_Level",
            "Factor_Slope",
            "Factor_Curvature",
            "Factor_FtoQ",
            "Factor_Inflation",
        ]
    ].dropna(how="any")
    display(df_factor)

    # ファクター間の相関行列
    print("=== Correlation Matrix ===")
    display(df_factor.corr().round(4))
    return (df_factor,)


@app.cell
def _(df_factor, display, excess_return_secs, pd):
    security = "AAPL-US"
    excess_return_security = excess_return_secs.loc[
        excess_return_secs["P_SYMBOL"] == security, ["date", "Excess_Return"]
    ].set_index("date")

    display(excess_return_security)
    df_data = pd.merge(
        excess_return_security,
        df_factor,
        left_index=True,
        right_index=True,
    )
    display(df_data)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
