import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Macro-data-prepare.ipynb

    各種経済指標を取得する
    """)
    return


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    from pathlib import Path
    import pandas as pd
    import sqlite3
    from google_drive_utils import upload_file_to_drive
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdate
    import seaborn as sns
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    ROOT_DIR = Path().cwd().parent
    DATA_DIR = ROOT_DIR / "data"
    ECO_DIR = DATA_DIR / "Economic Indicators"
    BBG_DIR = DATA_DIR / 'Bloomberg'
    FRED_DIR = DATA_DIR / 'FRED'
    INDEX_DIR = DATA_DIR / 'Factset' / 'Index'
    return (
        BBG_DIR,
        ECO_DIR,
        FRED_DIR,
        INDEX_DIR,
        np,
        pd,
        plt,
        sns,
        sqlite3,
        upload_file_to_drive,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Baltic Dry Index
    """)
    return


@app.cell
def _(ECO_DIR, upload_file_to_drive):
    # データはInvesting.comとかから手動で収集
    file_list = list(ECO_DIR.glob("Baltic Dry Index/*.csv"))
    upload_file_to_drive(file_list, "13_Quants/data/Baltic Dry Index")
    return (file_list,)


@app.cell
def _(ECO_DIR, file_list, pd, sqlite3, upload_file_to_drive):
    dfs = []
    for f in file_list[:1]:
        df = pd.read_csv(f).drop(columns=['変化率 %']).rename(columns={'日付け': 'date', '終値': 'close', '始値': 'open', '高値': 'high', '安値': 'low', '出来高': 'volume'}).assign(date=lambda row: pd.to_datetime(row['date']))
        dfs.append(df)
    df = pd.melt(pd.concat(dfs, ignore_index=True), id_vars='date', value_name='value').assign(Index='Baltic Dry Index').reindex(columns=['date', 'Index', 'variable', 'value'])
    _db_path = ECO_DIR / 'Economic-Indicators.db'
    _conn = sqlite3.connect(_db_path)
    df.to_sql('Baltic Dry Index', con=_conn, index=False, if_exists='replace')
    _conn.close()
    upload_file_to_drive([_db_path], '13_Quants/data/Economic Indicators')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Bloomberg

    -   ISM-PMI
    """)
    return


@app.cell
def _(BBG_DIR, display, pd, sqlite3):
    df_1 = pd.read_parquet(BBG_DIR / 'Bloomberg_ISM-PMI.parquet')
    df_1['date'] = pd.to_datetime(df_1['date'])
    _db_path = BBG_DIR / 'Bloomberg.db'
    _conn = sqlite3.connect(_db_path)
    df_ticker = pd.read_json(BBG_DIR / 'ticker-description.json')[['bloomberg_ticker', 'name']].rename(columns={'bloomberg_ticker': 'Index'})
    df_1 = pd.merge(df_1, df_ticker, on=['Index'], how='left').drop(columns=['Index']).rename(columns={'name': 'Index'}).reindex(columns=['date', 'Index', 'value'])
    df_1.to_sql('ISM_PMI_Survey', con=_conn, index=False, if_exists='replace')
    _conn.close()
    display(df_1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    -   MSCI Kokusai Index
    """)
    return


@app.cell
def _(INDEX_DIR, display, np, pd, sqlite3):
    _db_path = INDEX_DIR / 'Index-Price-and-Valuation.db'
    _conn = sqlite3.connect(_db_path)
    query = "\n    select\n        date, value, `Index`\n    from\n        FG_PRICE\n    where\n        `Index` in ('MSCI Kokusai Index (World ex Japan)', 'MSCI Kokusai Index (World ex Japan) Growth', 'MSCI Kokusai Index (World ex Japan) Value', 'MSCI Kokusai Quality')\n"
    df_price = pd.read_sql(query, con=_conn).pivot(index='date', columns='Index', values='value').sort_index()
    df_price.columns = [s.replace(' Index (World ex Japan)', '') for s in df_price.columns.tolist()]
    df_price.index = pd.to_datetime(df_price.index)
    start_date = pd.to_datetime('2006-01-01')
    df_price = df_price.loc[start_date:, :]
    df_log_return = np.log(df_price) - np.log(df_price.shift())
    df_log_return = df_log_return.fillna(0)
    df_cum_return = np.exp(df_log_return.cumsum())
    df_cum_return['Growth - Kokusai'] = df_cum_return['MSCI Kokusai Growth'].sub(df_cum_return['MSCI Kokusai'])
    df_cum_return['Quality - Kokusai'] = df_cum_return['MSCI Kokusai Quality'].sub(df_cum_return['MSCI Kokusai'])
    df_cum_return['Quality - Growth'] = df_cum_return['MSCI Kokusai Quality'].sub(df_cum_return['MSCI Kokusai Growth'])
    display(df_log_return)
    display(df_cum_return)
    return df_cum_return, start_date


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    -   US Bond Interest Rate
    """)
    return


@app.cell
def _(BBG_DIR, FRED_DIR, display, pd, sqlite3):
    _db_path = BBG_DIR / 'Bloomberg.db'
    _conn = sqlite3.connect(_db_path)
    df_2 = pd.read_sql('SELECT * FROM ISM_PMI_Survey', con=_conn)
    _conn.close()
    _db_path = FRED_DIR / 'FRED.db'
    _conn = sqlite3.connect(_db_path)
    df_yield = pd.read_sql('SELECT * FROM T10Y2Y', con=_conn, index_col='date').assign(T10Y2Y_EMA=lambda row: row['T10Y2Y'].ewm(span=126, adjust=False).mean())
    df_yield.index = pd.to_datetime(df_yield.index)
    df_yield.sort_index(inplace=True)
    _conn.close()
    display(df_yield)
    df_2['date'] = pd.to_datetime(df_2['date'])
    df_2 = df_2[df_2['Index'].isin(['ISM Manufacturing PMI SA', 'ISM Services PMI', 'ISM PMI Surveys'])]
    df_2 = pd.pivot(df_2, index='date', columns='Index', values='value').assign(ISM_PMI_EMA=lambda row: row['ISM PMI Surveys'].ewm(span=6, adjust=False).mean(), Manufacturing_EMA=lambda row: row['ISM Manufacturing PMI SA'].ewm(span=6, adjust=False).mean(), Service_EMA=lambda row: row['ISM Services PMI'].ewm(span=6, adjust=False).mean())
    display(df_2)
    return df_2, df_yield


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Plot
    """)
    return


@app.cell
def _(df_2, df_cum_return, df_yield, pd, plt, sns, start_date):
    fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True, tight_layout=True)
    # sns.lineplot(
    #     df, x=df.index, y=df["ISM PMI Surveys"], ax=ax, label="ISM PMI", color="orange"
    # )
    ax0 = axes[0]
    #     df,
    #     x=df.index,
    #     y=df["ISM_PMI_EMA"],
    #     ax=ax,
    #     label="ISM PMI EMA(6 Months)",
    #     color="orange",
    sns.lineplot(data=df_cum_return, x=df_cum_return.index, y=df_cum_return['Growth - Kokusai'], label='Growth - Kokusai', color='red', linewidth=0.8, ax=ax0)
    sns.lineplot(data=df_cum_return, x=df_cum_return.index, y=df_cum_return['Quality - Kokusai'], label='Quality - Kokusai', color='green', linewidth=0.8, ax=ax0)
    sns.lineplot(data=df_cum_return, x=df_cum_return.index, y=df_cum_return['Quality - Growth'], label='Quality - Growth', color='purple', linewidth=0.8, ax=ax0)
    # for col in df_cum_return.columns:
    #     linecolor = "black"
    #     if "Growth" in col:
    #         linecolor = "red"
    #     elif "Value" in col:
    #         linecolor = "blue"
    #     elif "Quality" in col:
    #         linecolor = "green"
    #     sns.lineplot(
    #         df_cum_return,
    #         x=df_cum_return.index,
    #         y=df_cum_return[col],
    #         label=col,
    #         ax=ax0,
    #         linewidth=0.8,
    #         color=linecolor,
    #     )
    ax0.grid()
    ax0.set_ylabel('Diff Between Cumulative Returns')
    ax0.axhline(y=0, color='black')
    ax0.legend(loc='upper left')
    ax1 = axes[1]
    sns.lineplot(df_2, x=df_2.index, y=df_2['Manufacturing_EMA'], ax=ax1, label='Manufacturing EMA(6 Months)', color='brown')
    sns.lineplot(df_2, x=df_2.index, y=df_2['Service_EMA'], ax=ax1, label='Service_EMA(6 Months)', color='red')
    ax1.set_ylim(30, 70)
    ax1.axhline(50, color='black')
    ax1.set_ylabel('ISM PMI')
    ax1.legend(loc='lower left')
    ax1.grid(axis='x')
    ax2 = ax1.twinx()
    ax2.fill_between(x=df_yield.index, y1=df_yield['T10Y2Y'], y2=0, color='slateblue', alpha=0.5)
    sns.lineplot(data=df_yield, x=df_yield.index, y=df_yield['T10Y2Y_EMA'], alpha=0.8, label='10Y-2Y Spread EMA(6 Months)', color='darkblue')
    ax2.set_ylim(-3, 3)
    ax2.set_ylabel('US Treasury 10Y-2Y Spread (%pt)')
    ax2.set_xlim(start_date, pd.to_datetime('2026-01-01'))
    ax2.legend(loc='lower right')
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 考察

    -   金利スプレッドが広がってスティープニング**し始めた**2020~2021 年頃と 2024 年後半~2025 年まででは、クオリティ指数がグロース指数に劣後している（Quality - Growth のライン）。

    ### 次の分析

    #### イールドカーブ PCA

    -   スプレッドだけだと分かりにくい。PCA で level 主成分と slope 主成分の推移を重ね合わせることにする。
    -   ![image.png](attachment:image.png)

    #### GEP port、LIST port VS Kokusai Index

    -   個別銘柄の銘柄選択寄与度を時系列で可視化する。
    """)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
