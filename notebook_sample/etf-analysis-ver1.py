import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # etf-analysis-ver1.ipynb

    SBI 証券で購入可能な ETF を対象に分析
    """)
    return


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np
    import io
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    import datetime
    from dateutil import relativedelta
    import time
    from concurrent.futures import ProcessPoolExecutor, as_completed
    import sqlite3
    from pathlib import Path
    from etf_dot_com import get_etf_fundamentals, get_tickers_from_db, save_data_to_db
    from tqdm import tqdm
    import yfinance as yf
    # from curl_cffi import requests
    # from curl_cffi.requests import Session
    import curl_cffi

    ROOT_DIR = Path().cwd().parent
    ETF_DIR = ROOT_DIR / "data/ETF"
    return ETF_DIR, curl_cffi, datetime, go, np, pd, tqdm, yf


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 日次データ download
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 国内 ETF
    """)
    return


@app.cell
def _(ETF_DIR, curl_cffi, display, pd, yf):
    etf_list_JP = [s + '.T' for s in pd.read_csv(ETF_DIR / 'SBI証券_購入可能ETF_国内.csv')['ティッカー'].tolist()]
    _session = curl_cffi.Session(impersonate='safari15_5')
    data = yf.download(etf_list_JP, session=_session, period='max', interval='1d')
    display(data)
    return (data,)


@app.cell
def _(data, display, pd):
    df = data.stack(future_stack=True).reset_index()
    df = pd.melt(df, id_vars=["Date", "Ticker"], value_vars=df.columns[2:])
    display(df)
    return


@app.cell
def _(display, yf):
    des = yf.Ticker("1306.T").holdings
    display(des)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 海外 ETF
    """)
    return


@app.cell
def _(ETF_DIR, curl_cffi, display, np, pd, yf):
    df_etf_list = pd.read_csv(ETF_DIR / 'SBI証券_購入可能ETF.csv')[['Category', 'Asset Type', 'ティッカー']].rename(columns={'ティッカー': 'Ticker'})
    ticker_list = ','.join(df_etf_list['Ticker'].unique().tolist() + ['^SPX'])
    _session = curl_cffi.Session(impersonate='safari15_5')
    Tickers_obj = yf.Tickers(ticker_list, session=_session)
    data_1 = Tickers_obj.history(period='max', interval='1d').stack(future_stack=True).reset_index().rename(columns={'Date': 'date'})
    display(data_1)
    df_1 = pd.melt(data_1, id_vars=['date', 'Ticker'], value_vars=data_1.columns.tolist()[2:], var_name='variable', value_name='value').assign(date=lambda row: pd.to_datetime(row['date'], unit='s', utc=True))
    display(df_1)
    df_1 = pd.merge(df_1[df_1['variable'] == 'Close'].drop(columns=['variable']).rename(columns={'value': 'Close'}), df_etf_list, on=['Ticker'], how='left').sort_values('date').assign(year=lambda row: pd.to_datetime(row['date']).dt.year, month=lambda row: pd.to_datetime(row['date']).dt.month, date=lambda row: pd.to_datetime(row['date']).dt.strftime('%Y-%m-%d'))
    df_1['log_price'] = np.log(df_1['Close'])
    df_1['log_return'] = df_1.groupby(['Ticker'])['log_price'].diff()
    display(df_1)
    _start_date = '2022-01-01'
    log_return_wide = df_1[df_1['date'] >= _start_date].pivot(index='date', columns='Ticker', values='log_return')
    _corr_matrix = log_return_wide.corr().reset_index().rename(columns={'Ticker': 'Ticker1'})
    df_corr = pd.melt(_corr_matrix, id_vars='Ticker1', value_vars=_corr_matrix.columns.tolist()[1:], var_name='Ticker2', value_name='correlation')
    df_corr = df_corr[df_corr['Ticker1'] < df_corr['Ticker2']].copy()
    df_corr = df_corr.sort_values('correlation', ignore_index=True)
    display(df_corr)
    return (df_1,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Calculate Rolling Correlation
    """)
    return


@app.cell
def _(datetime, df_1, display, pd, tqdm):
    _start_date = '2022-01-01'
    rolling_period = 365
    df_1['date'] = pd.to_datetime(df_1['date'])
    all_date = sorted(df_1['date'].unique().tolist(), reverse=True)
    date_range = [d for d in all_date if pd.to_datetime(d) <= datetime.datetime.today() and pd.to_datetime(d) > datetime.datetime.today() - datetime.timedelta(days=365 * 10)]
    dfs_corr = []
    for end_date in tqdm(date_range):
        _start_date = end_date - datetime.timedelta(days=365)
        log_return_wide_1 = df_1.loc[(df_1['date'] >= _start_date) & (df_1['date'] < end_date)].pivot(index='date', columns='Ticker', values='log_return')
        _corr_matrix = log_return_wide_1.corr().reset_index().rename(columns={'Ticker': 'Ticker1'})
        df_corr_1 = pd.melt(_corr_matrix, id_vars='Ticker1', value_vars=_corr_matrix.columns.tolist()[1:], var_name='Ticker2', value_name='correlation')
        df_corr_1 = df_corr_1[df_corr_1['Ticker1'] < df_corr_1['Ticker2']].copy()
        df_corr_1 = df_corr_1.sort_values('correlation', ignore_index=True).assign(date=end_date)
        dfs_corr.append(df_corr_1)
    df_corr_1 = pd.concat(dfs_corr, ignore_index=True)
    display(df_corr_1)
    return df_corr_1, log_return_wide_1


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### vs SPX で correlation の時系列が安定している ETF を抽出
    """)
    return


@app.cell
def _(df_corr_1, display):
    df_corr_spx = df_corr_1[df_corr_1['Ticker2'] == '^SPX']
    # display(df_corr_spx)
    g = df_corr_spx.groupby('Ticker1')['correlation'].agg(['mean', 'std']).sort_values('mean', key=lambda x: x.abs())
    display(g.head(20))
    return (df_corr_spx,)


@app.cell
def _(df_corr_spx, display, go, pd):
    df_plot = df_corr_spx.copy()
    display(df_plot)
    df_plot = pd.pivot(df_plot, index='date', columns='Ticker1', values='correlation')
    display(df_plot)
    # df_plot = df_plot.set_index("date")
    # df_plot.index = pd.to_datetime(df_plot.index)
    _fig = go.Figure()
    for _ticker in ['IAU', 'GLD', 'GLDM', 'DUST', 'NUGT', 'GDX', 'IGLD', 'COM', 'SLV', 'GDXJ']:
        _fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot[_ticker], mode='lines', name=_ticker, line=dict(width=0.8)))
    _fig.update_layout(title='Rolling Correlation: Window=365 days', xaxis_title='Date', yaxis_title='Correlation', yaxis=dict(range=[-1, 1]), legend=dict(yanchor='top', y=0.99, xanchor='left', x=0.01), margin=dict(l=20, r=20, t=30, b=20), template='plotly_dark')
    return


@app.cell
def _(go, log_return_wide_1, np, pd):
    df_cum_return = np.exp(log_return_wide_1.cumsum())
    first_value = df_cum_return.iloc[0]
    df_cum_return = df_cum_return.div(first_value)
    df_cum_return.index = pd.to_datetime(df_cum_return.index)
    cum_return_latest = pd.melt(df_cum_return.reset_index(), id_vars='date', value_vars=df_cum_return.columns, var_name='Ticker').set_index('date')
    cum_return_latest = cum_return_latest.loc[df_cum_return.index[-1]].sort_values('value').dropna().reset_index(drop=True)
    benchmark_beat_performers = cum_return_latest.loc[cum_return_latest[cum_return_latest['Ticker'] == '^SPX'].index[0] + 1:, 'Ticker'].tolist()
    _fig = go.Figure()
    for _ticker in benchmark_beat_performers + ['^SPX']:
        if _ticker == '^SPX':
            _fig.add_trace(go.Scatter(x=df_cum_return.index, y=df_cum_return[_ticker], name=_ticker, line=dict(color='white', width=0.8)))
        else:
            _fig.add_trace(go.Scatter(x=df_cum_return.index, y=df_cum_return[_ticker], name=_ticker, line=dict(width=0.8)))
    _fig.update_layout(width=1200, height=600, yaxis_title='Cumulative Return', margin=dict(l=20, r=20, t=30, b=20), template='plotly_dark')
    _fig.show()
    return


@app.cell
def _(ETF_DIR, display, pd):
    df_etf = pd.read_csv(ETF_DIR / "SBI証券_購入可能ETF.csv").rename(
        columns={"ティッカー": "Ticker"}
    )
    display(
        df_etf[
            df_etf["Ticker"].isin(
                ["GDXJ", "GDX", "XLK", "SUSA", "TECS", "VDE", "NUGT", "FAS", "DUST"]
            )
        ].sort_values("Ticker")
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
