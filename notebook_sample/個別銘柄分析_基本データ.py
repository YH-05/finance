import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 個別銘柄分析\_基本データ.ipynb
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
    from plotly.subplots import make_subplots
    import numpy as np
    import curl_cffi
    import pandas as pd
    pd.options.display.precision = 2
    import sqlite3
    import json
    import yfinance as yf
    import datetime
    from market_report_utils import MarketPerformanceAnalyzer
    from fred_database_utils import store_fred_database, get_fred_ids_from_file  # type: ignore
    from pathlib import Path
    from typing import List

    TICKER = "BKNG"

    ROOT_DIR = Path().cwd().parent.parent
    # FRED_DIR = ROOT_DIR / "15_Quant/data/FRED"
    FRED_DIR = ROOT_DIR / "Quants/data/FRED"

    # SECURITY_DIR = ROOT_DIR / f"19_Equity_Research/{TICKER}"
    SECURITY_DIR = ROOT_DIR / f"Equity_Research/{TICKER}"
    SECURITY_DATA_DIR = SECURITY_DIR / "data"
    print(ROOT_DIR)
    print(FRED_DIR)
    print(SECURITY_DIR)
    print(SECURITY_DATA_DIR)

    db_path = FRED_DIR / "FRED.db"
    id_list = get_fred_ids_from_file(file_path=FRED_DIR / "fred_series.json")

    store_fred_database(db_path=db_path, series_id_list=id_list)
    return List, Path, SECURITY_DATA_DIR, TICKER, go, make_subplots, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Price, PE and other valuation
    """)
    return


@app.cell
def _(List, Path, SECURITY_DATA_DIR, TICKER, display, pd):
    def read_excel_data(excel_file: Path, sheet_name: str, variable: str) -> pd.DataFrame:
        df = pd.melt(
            pd.read_excel(excel_file, sheet_name=sheet_name)
            .rename(columns={"Unnamed: 0": "date"})
            .dropna(subset=["date"]),
            id_vars="date",
            var_name="Ticker",
            value_name="value",
        ).assign(variable=variable)

        return df


    def read_excel_data_serial(
        excel_file: Path, sheet_name_list: List[str], variable_list: List[str]
    ) -> pd.DataFrame:
        dfs = []
        for sheet_name, variable in zip(sheet_name_list, variable_list):
            df = read_excel_data(
                excel_file=excel_file, sheet_name=sheet_name, variable=variable
            )
            dfs.append(df)

        df = pd.concat(dfs, ignore_index=True)

        return df


    excel_file = SECURITY_DATA_DIR / f"{TICKER}_Price_Valuation.xlsx"
    sheet_name_and_variable_name = {
        "Price": "Price",
        "Forward PE NTM": "Forward_PE_NTM",
        "Forward PE NTM - Index": "Forward_PE_NTM",
        "Actual PE LTM": "Actual_PE_LTM",
        "Actual PE LTM - Index": "Actual_PE_LTM",
    }

    df = read_excel_data_serial(
        excel_file=excel_file,
        sheet_name_list=sheet_name_and_variable_name.keys(),
        variable_list=sheet_name_and_variable_name.values(),
    ).drop_duplicates(ignore_index=True)
    df = df.loc[df["Ticker"] != "GOOGL US Equity"].sort_values("date", ignore_index=True)
    display(
        df.loc[(df["variable"] == "Price") & (df["Ticker"] == "ABNB US Equity")].dropna()
    )
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### cumulative return
    """)
    return


@app.cell
def _(TICKER, df, go, pd):
    start_date = '2021-1-1'
    end_date = '2025-9-30'
    df_price = df[(df['date'] >= start_date) & (df['date'] <= end_date) & (df['variable'] == 'Price')]
    df_price = pd.pivot(df_price, index='date', columns='Ticker', values='value').reset_index().sort_values('date', ignore_index=True).set_index('date')
    df_cum_return = df_price.div(df_price.iloc[0])
    _fig = go.Figure()
    for _ticker in df_cum_return.columns:
        _line_color = 'white' if _ticker.startswith(TICKER) else None
        _line_width = 1.5 if _ticker.startswith(TICKER) else 0.8
        _name = _ticker
        if _ticker == 'S5COND Index':
    # df_price = (
    #     pd.pivot(
    #         df[df["variable"] == "Price"], index="date", columns="Ticker", values="value"
    #     )
    #     .reset_index()
    #     .sort_values("date", ignore_index=True)
    # ).set_index("date")
    # df_price = df_price.iloc[-252 * 3 :, :].set_index("date")
    # 累積リターン
            _name = 'S&P500 Consumer Discretionary Index'
        elif _ticker == 'S5HOTL Index':
            _name = 'S&P500 Hotels, Restaurants & Leisure Index'
        _fig.add_trace(go.Scatter(x=df_cum_return.index, y=df_cum_return[_ticker], name=_name, line=dict(width=_line_width, color=_line_color)))
    _fig.update_layout(width=1000, height=500, template='plotly_dark', hovermode='x', legend=dict(yanchor='top', y=-0.05, xanchor='center', x=0.5, orientation='h'), margin=dict(l=40, r=40, t=50, b=60), title=f"Cumulative Return ({df_cum_return.index.min().strftime('%Y/%m/%d')}~{df_cum_return.index.max().strftime('%Y/%m/%d')})")
    _fig.show()  # Noneはテンプレートのデフォルト色を意味する
    return (start_date,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## PE
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Forward PE
    """)
    return


@app.cell
def _(TICKER, df, go, pd):
    df_forward_pe = pd.pivot(df[df['variable'] == 'Forward_PE_NTM'], index='date', columns='Ticker', values='value').reset_index()
    df_forward_pe = df_forward_pe.iloc[-252 * 5:-1, :].set_index('date')
    _fig = go.Figure()
    for _ticker in df_forward_pe.columns:
        _line_color = 'white' if _ticker.startswith(TICKER) else None
        _line_width = 1.5 if _ticker.startswith(TICKER) else 0.8
        _name = _ticker
        if _ticker == 'S5COND Index':
            _name = 'S&P500 Consumer Discretionary Index'
        elif _ticker == 'S5HOTL Index':
            _name = 'S&P500 Hotels, Restaurants & Leisure Index'
        _fig.add_trace(go.Scatter(x=df_forward_pe.index, y=df_forward_pe[_ticker], name=_name, line=dict(width=_line_width, color=_line_color)))
    _fig.update_yaxes(range=(0, 60))
    _fig.update_layout(width=1000, height=500, template='plotly_dark', hovermode='x', title='Forward PE', legend=dict(yanchor='top', y=-0.05, xanchor='center', x=0.5, orientation='h'), margin=dict(l=40, r=40, t=50, b=60))  # Noneはテンプレートのデフォルト色を意味する
    _fig.show()
    return


@app.cell
def _(TICKER, df, go, make_subplots, pd, start_date):
    df_actual_pe = df[(df['date'] >= start_date) & (df['variable'] == 'Actual_PE_LTM')]
    df_actual_pe = pd.pivot(df_actual_pe, index='date', columns='Ticker', values='value').sort_index()
    _fig = go.Figure()
    for _ticker in df_actual_pe.columns:
        _line_color = 'white' if _ticker.startswith(TICKER) else None
        _fig.add_trace(go.Scatter(x=df_actual_pe.index, y=df_actual_pe[_ticker], name=_ticker, line=dict(width=0.8, color=_line_color)))
    _fig.update_yaxes(range=(0, 60))
    _fig.update_layout(width=1000, height=500, template='plotly_dark', hovermode='x', title='Actual PE LTM', legend=dict(yanchor='top', y=-0.05, xanchor='center', x=0.5, orientation='h'), margin=dict(l=40, r=40, t=50, b=60))
    _fig.show()
    for _ticker in ['BKNG US Equity', 'SPX Index', 'S5HOTL Index']:  # Noneはテンプレートのデフォルト色を意味する
        df_forward_and_actual_pe = df[(df['date'] >= start_date) & df['variable'].isin(['Forward_PE_NTM', 'Actual_PE_LTM']) & df['Ticker'].str.startswith(_ticker)]
        df_forward_and_actual_pe = pd.pivot(df_forward_and_actual_pe, index='date', columns='variable', values='value').sort_index()
        df_forward_and_actual_pe['Actual minus Forward'] = df_forward_and_actual_pe['Actual_PE_LTM'].sub(df_forward_and_actual_pe['Forward_PE_NTM'])
        _fig = make_subplots(specs=[[{'secondary_y': True}]])
        for variable in [v for v in df_forward_and_actual_pe.columns if v != 'Actual minus Forward']:
            _fig.add_trace(go.Scatter(x=df_forward_and_actual_pe.index, y=df_forward_and_actual_pe[variable], name=variable, line=dict(width=0.8), yaxis='y1'), secondary_y=False)
        _fig.add_trace(go.Scatter(x=df_forward_and_actual_pe.index, y=df_forward_and_actual_pe['Actual minus Forward'], name='Actual minus Forward', fill='tozeroy', mode='none', yaxis='y2'), secondary_y=True)
        _fig.update_yaxes(range=(0, 60), title_text='PE(LTM / NTM)', secondary_y=False)
        _fig.update_yaxes(range=(0, 20), title_text='Actual minus Forward', secondary_y=True, showgrid=False)
        _fig.update_layout(width=1000, height=500, template='plotly_dark', hovermode='x unified', legend=dict(yanchor='top', y=-0.05, xanchor='center', x=0.5, orientation='h'), margin=dict(l=40, r=40, t=50, b=60), title=f'{_ticker} : Actual PE LTM and Forward PE NTM')
        _fig.show()
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
