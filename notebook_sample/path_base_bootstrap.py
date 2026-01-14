import marimo

__generated_with = "0.19.2"
app = marimo.App()


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
    import yaml
    import yfinance as yf
    import datetime
    from market_report_utils import (
            MarketPerformanceAnalyzer,
            apply_df_style,
            plot_vix_and_high_yield_spread,
            plot_vix_and_uncertainty_index
        )
    from fred_database_utils import (
            store_fred_database,
            get_fred_ids_from_file,
            load_data_from_database,
            delete_table_from_db  # type: ignore
        )
    from us_treasury import (
            plot_us_interest_rates_and_spread_3,
            plot_us_corporate_bond_spreads  # type: ignore
        )
    from path_base_bootstrap import (
            run_portfolio_bootstrap,
            print_bootstrap_stats,
            run_multiple_bootstrap_simulations
        )
    from pathlib import Path
    from fredapi import Fred

    ROOT_DIR = Path().cwd().parent
    DATA_DIR = ROOT_DIR / "data"
    FRED_DIR = DATA_DIR / "FRED"

    db_path = FRED_DIR / "FRED.db"
    id_list = get_fred_ids_from_file(file_path=FRED_DIR / "fred_series.json")

    # store_fred_database(db_path=db_path, series_id_list=id_list)
    return (
        MarketPerformanceAnalyzer,
        ROOT_DIR,
        pd,
        plt,
        print_bootstrap_stats,
        run_multiple_bootstrap_simulations,
        run_portfolio_bootstrap,
    )


@app.cell
def _(MarketPerformanceAnalyzer, display, pd):
    analyzer = MarketPerformanceAnalyzer()
    sector_map_en = {
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLE": "Energy",
        "XLF": "Financials",
        "XLV": "Health Care",
        "XLI": "Industrials",
        "XLK": "Information Technology",
        "XLB": "Materials",
        "XLU": "Utilities",
        "XLC": "Communication Services",
        "XLRE": "Real Estate",
    }
    tickers_to_download = ["^SPX", "GLD"] + list(sector_map_en.keys())

    df_price = analyzer.yf_download_with_curl(
        tickers_to_download=tickers_to_download, period="20y"
    )
    # display(df_price)

    df = df_price.copy()
    df = df.loc[df["variable"] == "Adj Close"].assign(
        value=lambda x: x["value"].astype(float)
    )
    df = (
        pd.pivot(
            df,
            index="Date",
            columns="Ticker",
            values="value",
        )
        .rename(columns=sector_map_en)
        .dropna(axis=1, how="any")
    )
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    display(df)
    return (df,)


@app.cell
def _(ROOT_DIR, df, run_multiple_bootstrap_simulations):
    PRJ_DIR = ROOT_DIR / "SP500_Sector_Weight"
    PRJ_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PRJ_DIR / "bootstrap_results.csv"
    run_multiple_bootstrap_simulations(
        prices_df=df, output_path=output_path, max_workers=20, weight_step=0.2
    )
    return (output_path,)


@app.cell
def _(
    df,
    display,
    output_path,
    pd,
    plt,
    print_bootstrap_stats,
    run_portfolio_bootstrap,
):
    sort_cols = ["sharpe_ratio (mean of paths)"]
    # sort_cols = ["mean_2y_return"]
    df_result = pd.read_csv(output_path).sort_values(sort_cols, ascending=False)
    display(df_result.columns)
    display(df_result.head(5))
    df_result = df_result[df.columns.tolist() + sort_cols]
    display(df_result.head(5))

    optimal_weights = df_result.iloc[0][df.columns.tolist()].to_dict()
    print("Optimal Weights:")
    for k, v in optimal_weights.items():
        print(f"  {k}: {v:.2f}")

    # weights = {
    #     "Information Technology": 0.4,
    #     "GLD": 0.2,
    #     "Utilities": 0.2,
    #     "Consumer Discretionary": 0.2,
    # }
    weights = optimal_weights

    stats, fig = run_portfolio_bootstrap(prices_df=df, weights=weights)

    print_bootstrap_stats(stats)
    plt.tight_layout()
    plt.show()
    return


if __name__ == "__main__":
    app.run()
