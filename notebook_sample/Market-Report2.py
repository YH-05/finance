import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Market-Report.ipynb

    weekly などのマーケットコメント用データ収集ノートブック
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo
    import os
    import re
    import sqlite3
    import sys
    import warnings

    import curl_cffi
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns

    pd.options.display.precision = 2
    from pathlib import Path

    import yfinance as yf

    warnings.simplefilter("ignore")
    from dotenv import load_dotenv

    load_dotenv()
    QUANTS_DIR = Path(os.environ.get("QUANTS_DIR"))
    DATA_DIR = Path(os.environ.get("DATA_DIR"))
    FRED_DIR = Path(os.environ.get("FRED_DIR"))
    BLOOMBERG_ROOT_DIR = Path(os.environ.get("BLOOMBERG_ROOT_DIR"))  # type: ignore
    TSA_DIR = Path(os.environ.get("TSA_DIR"))  # type: ignore
    sys.path.insert(0, str(QUANTS_DIR))  # type: ignore
    import src.fred_database_utils as fred_utils  # type: ignore
    import src.market_report_utils as mru  # type: ignore

    from src import us_treasury

    # sys.path.append(str(ROOT_DIR))
    fred_db_path = FRED_DIR / "FRED.db"
    tsa_db_path = TSA_DIR / "TSA.db"
    sp_price_db_path = BLOOMBERG_ROOT_DIR / "SP_Indices_Price.db"
    fred = fred_utils.FredDataProcessor()
    fred.store_fred_database()
    bbg = mru.BloombergDataProcessor()
    bbg.store_sp_indices_price_to_database()
    sp500_tickers = [re.split(" ", s)[0] for s in bbg.get_current_sp_members()]
    tsa_data_collector = mru.TSAPassengerDataCollector()
    _df = tsa_data_collector.scrape_tsa_passenger_data()
    tsa_data_collector.store_to_tsa_database(df=_df, db_path=tsa_db_path)
    # daily data collect
    # bbg.delete_table_from_db(db_path=bbg.sp_price_db, table_name="Members")
    # display(sp500_tickers)
    analyzer = mru.MarketPerformanceAnalyzer()
    return (
        FRED_DIR,
        analyzer,
        curl_cffi,
        fred_db_path,
        mru,
        np,
        pd,
        plt,
        sns,
        sp_price_db_path,
        sqlite3,
        us_treasury,
        yf,
    )


@app.cell
def _(display, pd, sp_price_db_path, sqlite3):
    conn = sqlite3.connect(sp_price_db_path)
    _df = pd.read_sql("SELECT * FROM Members", con=conn)
    display(_df)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## S&P Index, Magnificent 7 & SOX Index, Sector

    -   TODO: 直近 5 日間の分足データをプロットできるようにしておく -> やっぱりいらないかも
    """)


@app.cell
def _(analyzer, display, mru):
    _price = analyzer.price_data
    display(
        _price[[col for col in _price.columns if col.startswith("XL")] + ["^SOX"]].tail(
            6
        )
    )
    performance_dict = analyzer.get_performance_groups()
    display(mru.apply_df_style(performance_dict["US_and_SP500_Indices"]))
    performance_sp_indices = performance_dict["US_and_SP500_Indices"]
    analyzer.plot_sp500_indices()
    display(mru.apply_df_style(performance_dict["Mag7_SOX"]))
    analyzer.plot_mag7_sox()
    # display(performance_sp_indices["last_Tuesday"])
    poerformance_sector = performance_dict["Sector"]
    display(mru.apply_df_style(poerformance_sector))
    analyzer.plot_sector_performance()
    # performance_mag7_sox = performance_dict["Mag7_SOX"]
    # display(performance_mag7_sox[["last_Tuesday"]])
    display(mru.apply_df_style(performance_dict["Metals"]))
    # display(poerformance_sector["last_Tuesday"])
    analyzer.plot_metal()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### SP500 Sector ETF Beta(vs SP500)
    """)


@app.cell
def _(analyzer, mru):
    sp500_etf = [
        col for col in list(analyzer.SECTOR_MAP_EN.keys()) if col.startswith("XL")
    ]
    tickers_to_download = sp500_etf + ["^SPX"]
    df_price = analyzer.yf_download_with_curl(
        tickers_to_download=tickers_to_download, period="max"
    )
    df_price = df_price.loc[df_price["variable"] == "Adj Close"].drop(
        columns=["variable"]
    )
    freq = "W"
    window_years = 3
    _df_beta = mru.rolling_beta(
        df_price=df_price, target_col="^SPX", freq=freq, window_years=window_years
    )
    _fig = mru.plot_rolling_beta(
        df_beta=_df_beta,
        freq=freq,
        window_years=window_years,
        tickers_to_plot=["XLK", "XLU", "XLRE"],
        target_index_name="S&P500",
    )
    _fig.show()
    return df_price, freq, window_years


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### (✏️Test) Kalman Filter Beta
    """)


@app.cell
def _(df_price, display, freq, mru, window_years):
    _df_beta = mru.calculate_kalman_beta(
        df_price=df_price, target_col="^SPX", freq=freq, window_years=window_years
    )
    display(_df_beta)
    _fig = mru.plot_rolling_beta(
        df_beta=_df_beta,
        freq=freq,
        window_years=window_years,
        tickers_to_plot=["XLK", "XLU", "XLRE"],
        target_index_name="S&P500",
        beta_variable_name="beta_3y_w_kalman_3years",
    )
    _fig.show()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## US Interest Rate / Corporate Bond Spread
    """)


@app.cell
def _(FRED_DIR, fred_db_path, us_treasury):
    us_treasury.plot_us_interest_rates_and_spread_3(
        db_path=fred_db_path, start_date="2000-01-01"
    )
    us_treasury.plot_us_corporate_bond_spreads(
        db_path=fred_db_path, json_config_path=FRED_DIR / "fred_series.json"
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## VIX, High Yield Spread, US Economic Uncertainty Index
    """)


@app.cell
def _(mru):
    mru.plot_vix_and_high_yield_spread()
    mru.plot_vix_and_uncertainty_index()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Dollars Index vs Metals
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Price and Rolling Correlation
    """)


@app.cell
def _(mru):
    metal_analyzer = mru.DollarsIndexAndMetalsAnalyzer()
    df_metal_price = metal_analyzer.price
    _fig = metal_analyzer.plot_us_dollar_index_and_metal_price()
    _fig.show()
    df_corr = mru.rolling_correlation(df_price=df_metal_price, target_col="DTWEXAFEGS")
    for _ticker in ["GLD", "SLV", "CPER", "PPLT", "PALL"]:
        _fig = mru.plot_rolling_correlation(
            df_corr=df_corr,
            ticker_to_plot=_ticker,
            target_index_name="Nominal Advanced Foreign Economies US Dolalr Index",
        )
        _fig.show()
    return (df_metal_price,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Beta
    """)


@app.cell
def _(df_metal_price, mru):
    _df_beta = mru.rolling_beta(
        df_price=df_metal_price, target_col="DTWEXAFEGS", freq="W", window_years=5
    )
    _fig = mru.plot_rolling_beta(
        df_beta=_df_beta,
        freq="W",
        window_years=5,
        tickers_to_plot=["GLD", "SLV", "PPLT"],
        target_index_name="Nominal Advanced Foreign Economies US Dolalr Index",
    )
    _fig.show()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SP500 Index weekly return
    """)


@app.cell
def _(display, mru, np, yf):
    analyzer_1 = mru.MarketPerformanceAnalyzer()
    tickers_sp500 = analyzer_1.TICKERS_SP500
    _price = yf.download(tickers=tickers_sp500, auto_adjust=False, period="max")[
        "Close"
    ].dropna(how="any")
    log_return = np.log(_price / _price.shift(5)).dropna(how="any")
    log_return = log_return.loc[log_return.index.year == 2025]
    log_return_long = (
        log_return.stack().reset_index().rename(columns={0: "weekly_log_return"})
    )
    log_return_long["weekly_log_return"] = log_return_long["weekly_log_return"].mul(100)
    display(log_return_long)
    stats = (
        log_return_long.groupby("Ticker")["weekly_log_return"]
        .agg(["mean", "std"])
        .rename(columns={"mean": "log_return_avg(%)", "std": "log_return_std(%)"})
    )
    display(stats)
    return log_return_long, stats


@app.cell
def _(log_return_long, plt, sns, stats):
    # FacetGridを初期化し、ティッカーごとにグラフを分割
    # col_wrap=2 で横に2つ並べるように指定
    g = sns.FacetGrid(log_return_long, col="Ticker", col_wrap=2, height=4, sharex=True)
    g.map(
        sns.histplot,
        "weekly_log_return",
        bins=100,
        kde=True,
        stat="density",
        edgecolor="black",
    )
    # 各グラフにヒストグラムをプロット
    for ax in g.axes.flatten():
        _ticker = ax.get_title().split("=")[1].strip()
        mean_val = stats.loc[_ticker, "log_return_avg(%)"]
        std_val = stats.loc[_ticker, "log_return_std(%)"]
        ax.axvline(
            mean_val,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {mean_val:.4f}",
        )
        ax.axvline(
            mean_val + std_val,
            color="green",
            linestyle=":",
            linewidth=1.5,
            label="+1 Sigma",
        )
        ax.axvline(
            mean_val - std_val,
            color="green",
            linestyle=":",
            linewidth=1.5,
            label="-1 Sigma",
        )
    plt.suptitle("Weekly log return", y=1.02, fontsize=16)
    g.set_axis_labels("return", "density")
    # 各サブプロットに平均値と±1シグマの垂直線を追加
    g.tight_layout()
    # レイアウトの調整
    plt.show()  # 該当ティッカーの統計量を取得  # 平均 (µ) の線  # +1シグマ (µ + σ) の線  # -1シグマ (µ - σ) の線  # 凡例をプロットに追加（スペースがあれば）  # ax.legend()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## S&P セクター別 ETF

    -   SPDR
    """)


@app.cell
def _(curl_cffi, display, yf):
    session = curl_cffi.Session(impersonate="safari15_5")
    ticker_list = " ".join(
        [
            "XLK",
            "XLF",
            "XLV",
            "XLY",
            "XLC",
            "XLI",
            "XLP",
            "XLE",
            "XLU",
            "XLRE",
            "XLB",
            "^SPX",
        ]
    )
    Tickers_obj = yf.Tickers(ticker_list, session=session)
    data = (
        Tickers_obj.history(period="max", interval="1d")
        .stack()
        .reset_index()
        .rename(columns={"Date": "date"})
    )
    display(data)


@app.cell
def _(display, yf):
    stock = yf.Ticker("MSFT")
    earnings_info = stock.calendar
    display(earnings_info)
    historical_earnings = stock.get_earnings_dates()
    display(historical_earnings)


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
