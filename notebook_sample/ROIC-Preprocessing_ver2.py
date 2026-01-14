import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # `ROIC-Preprocessing_ver2.ipynb`

    -   ROIC 分析の前処理用 notebook
    -   行うこと
        1. 取得したデータをデータベースに落とし込む
        2. ベンチマークのプライスとリターンデータ用意
        3. ファクター計算
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import datetime
    import gc
    import itertools
    import os
    import sqlite3
    import sys
    import warnings
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import yaml
    from dotenv import load_dotenv
    from tqdm import tqdm

    warnings.simplefilter("ignore")
    load_dotenv()

    UNIVERSE_CODE = "MSXJPN_AD"
    BLOOMBERG_UNIVERSE_TICKER = "MXKO Index"

    QUANTS_DIR = Path(os.environ.get("QUANTS_DIR"))  # type: ignore
    FACTSET_ROOT_DIR = Path(os.environ.get("FACTSET_ROOT_DIR"))  # type: ignore
    FACTSET_FINANCIALS_DIR = Path(os.environ.get("FACTSET_FINANCIALS_DIR"))  # type: ignore
    FACTSET_INDEX_CONSTITUENTS_DIR = Path(
        os.environ.get("FACTSET_INDEX_CONSTITUENTS_DIR")
    )  # type: ignore
    INDEX_DIR = FACTSET_FINANCIALS_DIR / UNIVERSE_CODE
    BPM_ROOT_DIR = Path(os.environ.get("BPM_ROOT_DIR"))  # type: ignore
    BLOOMBERG_ROOT_DIR = Path(os.environ.get("BLOOMBERG_ROOT_DIR"))  # type: ignore
    BLOOMBERG_DATA_DIR = Path(os.environ.get("BLOOMBERG_DATA_DIR"))  # type: ignore

    sys.path.insert(0, str(QUANTS_DIR))
    import src.calculate_performance_metrics as performance_metrics_utils
    import src.database_utils as db_utils
    import src.ROIC_make_data_files_ver2 as roic_utils
    from src import bloomberg_utils, factset_utils

    financials_db_path = INDEX_DIR / "Financials_and_Price.db"
    factset_index_db_path = FACTSET_INDEX_CONSTITUENTS_DIR / "Index_Constituents.db"
    bloomberg_index_db_path = BLOOMBERG_ROOT_DIR / "Index_Price_and_Returns.db"
    bloomberg_valuation_db_path = BLOOMBERG_ROOT_DIR / "Valuation.db"
    bpm_db_path = BPM_ROOT_DIR / "Index_Constituents.db"
    return (
        BLOOMBERG_DATA_DIR,
        BLOOMBERG_ROOT_DIR,
        BLOOMBERG_UNIVERSE_TICKER,
        FACTSET_INDEX_CONSTITUENTS_DIR,
        INDEX_DIR,
        ThreadPoolExecutor,
        UNIVERSE_CODE,
        as_completed,
        bloomberg_index_db_path,
        bloomberg_utils,
        bloomberg_valuation_db_path,
        datetime,
        db_utils,
        factset_index_db_path,
        factset_utils,
        financials_db_path,
        gc,
        itertools,
        np,
        pd,
        performance_metrics_utils,
        roic_utils,
        sqlite3,
        tqdm,
        yaml,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 0. 現在のデータベースチェック
    """)


@app.cell
def _(db_utils, display, financials_db_path, pd, sqlite3):
    _tables = sorted(db_utils.get_table_names(financials_db_path))
    display(_tables)
    with sqlite3.connect(financials_db_path) as _conn:
        df_tables = pd.read_sql(
            "SELECT * FROM FF_ASSETS", con=_conn, parse_dates=["date"]
        )
        display(df_tables)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. BPM と Factset からダウンロードしたデータを sqlite3 に保存

    -   インデックス別にテーブルを作成する
    -   元データは"Index_Constituents_with_Factset_code-compressed-\*.paruqet" -> 圧縮して送信した
    -   BPM から取得した構成比や銘柄 ID などのデータと、Factset でダウンロードした seol, cusip, isin, code_jp にそれぞれ対応する P_SYMBOL および FG_COMPANY_NAME を格納したデータ。
    """)


@app.cell
def _(
    FACTSET_INDEX_CONSTITUENTS_DIR,
    db_utils,
    display,
    factset_index_db_path,
    factset_utils,
    np,
    pd,
):
    compressed_files = list(
        FACTSET_INDEX_CONSTITUENTS_DIR.glob(
            "Index_Constituents_with_Factset_code-compressed-*.parquet"
        )
    )
    _dfs = [pd.read_parquet(f) for f in compressed_files]
    df = (
        pd.concat(_dfs)
        .assign(
            date=lambda x: pd.to_datetime(x["date"]),
            SEDOL=lambda x: x["SEDOL"].astype(str),
        )
        .replace("N/A", np.nan)
    )
    df[["Holdings", "Weight (%)", "Mkt Value"]] = df[
        ["Holdings", "Weight (%)", "Mkt Value"]
    ].astype(float)
    head_cols = ["Universe", "Universe_code_BPM", "date"]
    other_cols = [_col for _col in df.columns if _col not in head_cols]
    df = df.reindex(columns=head_cols + other_cols).sort_values(
        ["Universe", "date", "Name"], ignore_index=True
    )
    for universe_code in df["Universe_code_BPM"].unique():
        _df_slice = df.loc[df["Universe_code_BPM"] == universe_code].reset_index(
            drop=True
        )
        factset_utils.store_to_database(
            df=_df_slice,
            db_path=factset_index_db_path,
            table_name=universe_code,
            unique_cols=["date", "Name", "Asset ID"],
        )
    table_names = db_utils.get_table_names(db_path=factset_index_db_path)
    display(table_names)


@app.cell
def _(UNIVERSE_CODE, display, factset_index_db_path, pd, sqlite3):
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_1 = pd.read_sql(
            f"SELECT * FROM `{UNIVERSE_CODE}`", parse_dates=["date"], con=_conn
        ).drop_duplicates()
        df_1["P_SYMBOL_missing"] = df_1["P_SYMBOL"].isna()
        display(df_1)
        _g = df_1.groupby(["date", "P_SYMBOL_missing"])["Weight (%)"].agg(
            ["count", "sum"]
        )
        display(_g)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Factset からダウンロードしたデータをまとめる

    Financials および Price のデータをデータベースに格納する。
    """)


@app.cell
def _(
    INDEX_DIR,
    db_utils,
    display,
    factset_utils,
    financials_db_path,
    pd,
    tqdm,
):
    file_list = list(INDEX_DIR.glob("Financials_and_Price-compressed-*.parquet"))
    _dfs = [pd.read_parquet(f) for f in tqdm(file_list, desc="loading parquet files")]
    df_2 = (
        pd.concat(_dfs)
        .drop_duplicates()
        .sort_values(["variable", "P_SYMBOL", "date"], ignore_index=True)
        .assign(value=lambda x: x["value"].astype(float))
    )
    for _variable in df_2["variable"].unique():
        _df_slice = df_2.loc[df_2["variable"] == _variable]
        factset_utils.store_to_database(
            df=_df_slice,
            db_path=financials_db_path,
            table_name=_variable,
            unique_cols=["date", "P_SYMBOL", "variable"],
            verbose=True,
        )
    table_names_1 = db_utils.get_table_names(db_path=financials_db_path)
    display(table_names_1)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### ⚠️1AY/新規データ項目の差分更新がある場合
    """)


@app.cell
def _(INDEX_DIR, db_utils, factset_utils, financials_db_path, np, pd, sqlite3):
    def update_value(row, rtol=1e-05, atol=0.001):
        """既存値をアップデートする関数"""
        existing = row["value_existing"]
        new = row["value_new"]
        if pd.isna(existing) and pd.isna(new):
            return np.nan
        if pd.isna(existing):
            return new
        if pd.isna(new):
            return existing
        if np.isclose(existing, new, rtol=rtol, atol=atol):
            return existing
        else:
            return new

    _update_file = (
        INDEX_DIR / "Financials_and_Price-compressed-20241129_20251031.parquet"
    )
    _df_update = pd.read_parquet(_update_file)
    _variable_list = _df_update["variable"].sort_values().unique().tolist()
    _date_list = _df_update["date"].sort_values().unique().tolist()
    _start_date = min(_date_list)
    _end_date = max(_date_list)
    _existing_tables = db_utils.get_table_names(financials_db_path)
    _added_variables = list(set(_variable_list) - set(_existing_tables))
    if len(_added_variables) > 0:
        pass
    _update_tables = sorted(list(set(_existing_tables) & set(_variable_list)))
    _total_updated = 0
    with sqlite3.connect(financials_db_path) as _conn:
        for _idx, _table in enumerate(_update_tables, 1):
            print(f"\n[{_idx}/{len(_update_tables)}] 処理中: {_table}")
            query = f"\n            SELECT\n                *\n            FROM\n                {_table}\n            WHERE\n                date >= '{_start_date.strftime('%Y-%m-%d')}' AND date <= '{_end_date.strftime('%Y-%m-%d')}'\n        "
            _df_existing = (
                pd.read_sql(query, con=_conn, parse_dates=["date"])
                .rename(columns={"value": "value_existing"})
                .reindex(columns=["date", "P_SYMBOL", "variable", "value_existing"])
            )
            _df_update_slice = (
                _df_update.loc[_df_update["variable"] == _table]
                .copy()
                .rename(columns={"value": "value_new"})
                .reindex(columns=["date", "P_SYMBOL", "variable", "value_new"])
            )
            df_merged = pd.merge(
                _df_update_slice,
                _df_existing,
                on=["date", "P_SYMBOL", "variable"],
                how="outer",
            )
            df_merged["value"] = df_merged.apply(update_value, axis=1)
            _changed_mask = df_merged["value_existing"].isna() & ~df_merged[
                "value_new"
            ].isna() | ~df_merged["value_existing"].isna() & ~df_merged[
                "value_new"
            ].isna() & ~np.isclose(
                df_merged["value_existing"],
                df_merged["value_new"],
                rtol=1e-05,
                atol=0.001,
            )
            _df_to_update = df_merged[_changed_mask].reset_index(drop=True)[
                ["date", "P_SYMBOL", "variable", "value"]
            ]
            if len(_df_to_update) > 0:
                print(f"  更新対象: {len(_df_to_update):,}行")
                _rows_affected = factset_utils.upsert_financial_data(
                    _df_to_update, _conn, _table, method="auto"
                )
                _total_updated = _total_updated + _rows_affected
            else:
                print("  変更なし")
    print(f"\n{'=' * 50}")
    print("📊 更新完了")
    print(f"{'=' * 50}")
    print(f"総更新行数: {_total_updated:,}行")
    return (update_value,)


@app.cell
def _(
    INDEX_DIR,
    db_utils,
    factset_utils,
    financials_db_path,
    np,
    pd,
    sqlite3,
    update_value,
):
    _update_file = (
        INDEX_DIR / "Financials_and_Price-compressed-20241129_20251031.parquet"
    )
    _df_update = pd.read_parquet(_update_file)
    _variable_list = _df_update["variable"].sort_values().unique().tolist()
    _date_list = _df_update["date"].sort_values().unique().tolist()
    _start_date = min(_date_list)
    _end_date = max(_date_list)
    _existing_tables = db_utils.get_table_names(financials_db_path)
    _added_variables = list(set(_variable_list) - set(_existing_tables))
    if len(_added_variables) > 0:
        pass
    _update_tables = list(set(_existing_tables) & set(_variable_list))
    _total_updated = 0
    with sqlite3.connect(financials_db_path) as _conn:
        for _idx, _table in enumerate(_update_tables, 1):
            print(f"\n[{_idx}/{len(_update_tables)}] 処理中: {_table}")
            query_1 = f"\n            SELECT\n                *\n            FROM\n                {_table}\n            WHERE\n                date >= '{_start_date.strftime('%Y-%m-%d')}' AND date <= '{_end_date.strftime('%Y-%m-%d')}'\n        "
            _df_existing = (
                pd.read_sql(query_1, con=_conn, parse_dates=["date"])
                .rename(columns={"value": "value_existing"})
                .reindex(columns=["date", "P_SYMBOL", "variable", "value_existing"])
            )
            _df_update_slice = (
                _df_update.loc[_df_update["variable"] == _table]
                .copy()
                .rename(columns={"value": "value_new"})
                .reindex(columns=["date", "P_SYMBOL", "variable", "value_new"])
            )
            df_merged_1 = pd.merge(
                _df_update_slice,
                _df_existing,
                on=["date", "P_SYMBOL", "variable"],
                how="outer",
            )
            df_merged_1["value"] = df_merged_1.apply(update_value, axis=1)
            _changed_mask = df_merged_1["value_existing"].isna() & ~df_merged_1[
                "value_new"
            ].isna() | ~df_merged_1["value_existing"].isna() & ~df_merged_1[
                "value_new"
            ].isna() & ~np.isclose(
                df_merged_1["value_existing"],
                df_merged_1["value_new"],
                rtol=1e-05,
                atol=0.001,
            )
            _df_to_update = df_merged_1[_changed_mask].reset_index(drop=True)[
                ["date", "P_SYMBOL", "variable", "value"]
            ]
            if len(_df_to_update) > 0:
                print(f"  更新対象: {len(_df_to_update):,}行")
                _rows_affected = factset_utils.upsert_financial_data(
                    _df_to_update, _conn, _table, method="upsert"
                )
                _total_updated = _total_updated + _rows_affected
            else:
                print("  変更なし")
    print(f"\n{'=' * 50}")
    print("📊 更新完了")
    print(f"{'=' * 50}")
    print(f"総更新行数: {_total_updated:,}行")


@app.cell
def _(display, financials_db_path, pd, sqlite3):
    with sqlite3.connect(financials_db_path) as _conn:
        df_3 = pd.read_sql("SELECT * FROM FF_SALES", con=_conn, parse_dates=["date"])
        display(df_3.dropna(subset=["date"]))


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### データベースチェック
    """)


@app.cell
def _(display, financials_db_path, pd, sqlite3):
    with sqlite3.connect(financials_db_path) as _conn:
        df_4 = pd.read_sql(
            "SELECT * FROM FF_ASSETS ORDER BY date", parse_dates=["date"], con=_conn
        )
    display(df_4)
    display(df_4.drop_duplicates(subset=["date", "P_SYMBOL"]))
    display(df_4["date"].unique().tolist())


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. リターン&ファクター用テーブル作成
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3-1. リターンのテーブルを作成
    """)


@app.cell
def _(db_utils, display, factset_utils, financials_db_path, pd, roic_utils):
    _df_price = roic_utils.load_FG_PRICE(db_path=financials_db_path)
    df_return = roic_utils.calculate_Return(
        df_price=_df_price,
        date_column="date",
        symbol_column="P_SYMBOL",
        price_column="FG_PRICE",
    )
    print("--- return data ---")
    display(df_return.head(3))
    print("-" * 20)
    _df_check = df_return.reset_index()
    _symbol_date_counts = _df_check.groupby("P_SYMBOL")["date"].nunique()
    _all_date_len = len(_df_check["date"].unique())
    _not_enough_len_symbols = _symbol_date_counts[
        _symbol_date_counts != _all_date_len
    ].index
    if len(_not_enough_len_symbols) > 0:
        print("問題あり")
        # ------------------------------------------------------------------------------------
        # データチェック
        # 銘柄によってはdateが1カ月ずつ連続でデータがあるとは限らない
        # FG_PRICEがない場合にpct_changeを素直に実行するとリターンの期間が他の銘柄とずれる
        # そのため、全dateの長さと銘柄ごとのdateの長さを比較する
        display(_not_enough_len_symbols)
    else:
        print("問題なし")
        df_return.reset_index(inplace=True)
        display(df_return.head(5))
        for _col in [
            s
            for s in df_return.columns
            if s.startswith("Return") or s.startswith("Forward_Return")
        ]:
            _df_slice = (
                df_return[["date", "P_SYMBOL", _col]]
                .rename(columns={_col: "value"})
                .assign(variable=_col)
            )
            _df_slice["value"] = _df_slice["value"].astype(float)
            _df_slice["date"] = pd.to_datetime(_df_slice["date"])
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=_col
            )  # 問題なければデータベースに保存
            factset_utils.store_to_database(
                df=_df_slice, db_path=financials_db_path, table_name=_col
            )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3-2. インデックスの価格とリターンデータを取得 via Blpapi

    ⚠️ 注意 ⚠️ Bloomberg Terminal を起動している必要あり。
    """)


@app.cell
def _(bloomberg_index_db_path, display, pd, sqlite3):
    with sqlite3.connect(bloomberg_index_db_path) as _conn:
        df_5 = pd.read_sql("SELECT * FROM PX_LAST", con=_conn, parse_dates=["Date"])
    display(df_5)
    print(
        f"Date: {df_5['Date'].min().strftime('%Y-%m-%d')} 〜 {df_5['Date'].max().strftime('%Y-%m-%d')} ({len(df_5['Date'].unique()):,}日)"
    )
    print(
        f"Ticker: {df_5['Ticker'].nunique():,}銘柄\n\t{df_5['Ticker'].unique().tolist()}"
    )


@app.cell
def _(
    BLOOMBERG_ROOT_DIR,
    bloomberg_index_db_path,
    bloomberg_utils,
    datetime,
    yaml,
):
    # yamlで設定した銘柄リストの読み込み（Bloomberg Ticker）
    BLOOMBERG_TICKER_YAML = BLOOMBERG_ROOT_DIR / "ticker-description.yaml"
    EQUITY_TYPES = {"equity_index", "equity_sector_index", "equity_industry_index"}

    with open(BLOOMBERG_TICKER_YAML, "r", encoding="utf-8") as f:
        ticker_descriptions = yaml.safe_load(f)

    tickers_to_download = [
        ticker["bloomberg_ticker"]
        for ticker in ticker_descriptions
        if ticker.get("type") in EQUITY_TYPES
    ]

    # -----------------------------------------------------
    # Bloombergから価格データをダウンロードしてデータベースを更新
    # -----------------------------------------------------

    blp = bloomberg_utils.BlpapiCustom()
    # 新規ティッカーがある場合

    # df = blp.get_historical_data(
    #     securities=tickers_to_download,
    #     fields=["PX_LAST"],
    #     start_date="20000101",
    #     end_date=datetime.datetime.today().strftime("%Y%m%d"),
    # )
    # df = pd.melt(
    #     df.reset_index(), id_vars=["Date"], var_name="Ticker", value_name="value"
    # ).assign(variable="PX_LAST")
    # display(df)
    # blp.store_to_database(
    #     df=df,
    #     db_path=bloomberg_index_db_path,
    #     table_name="PX_LAST",
    #     primary_keys=["Date", "Ticker", "variable"],
    #     verbose=True,
    # )

    # 　既存データの更新

    rows_updated = blp.update_historical_data(
        db_path=bloomberg_index_db_path,
        table_name="PX_LAST",
        tickers=tickers_to_download,
        id_type="ticker",
        field="PX_LAST",
        default_start_date=datetime.datetime(2000, 1, 1),
        verbose=True,
    )
    print(f"\n{'='*60}")
    print(f"処理完了: {rows_updated:,}行を処理しました")
    print(f"{'='*60}")
    return (blp,)


@app.cell
def _(
    BLOOMBERG_UNIVERSE_TICKER,
    bloomberg_index_db_path,
    blp,
    db_utils,
    display,
    financials_db_path,
    pd,
    roic_utils,
):
    # 既存のFG_PRICEのテーブルからリターン計算すべき日付を取得
    df_index_price_filtered = (
        db_utils.get_rows_by_unique_values(
            source_db_path=financials_db_path,
            target_db_path=bloomberg_index_db_path,
            source_table="FG_PRICE",
            target_table="PX_LAST",
            source_column="date",
            target_column="Date",
        )
        .query(f"Ticker == '{BLOOMBERG_UNIVERSE_TICKER}'")
        .reset_index(drop=True)
        .assign(Date=lambda x: pd.to_datetime(x["Date"]))
    )
    df_index_return = roic_utils.calculate_Return(
        df_price=df_index_price_filtered,
        date_column="Date",
        symbol_column="Ticker",
        price_column="value",
    )
    print("--- return data ---")
    display(df_index_return.tail(3))
    print("-" * 20)
    _df_check = df_index_return.reset_index()
    _symbol_date_counts = _df_check.groupby("Ticker")["Date"].nunique()
    _all_date_len = len(_df_check["Date"].unique())
    _not_enough_len_symbols = _symbol_date_counts[
        _symbol_date_counts != _all_date_len
    ].index
    if len(_not_enough_len_symbols) > 0:
        print("問題あり")
        display(_not_enough_len_symbols)
    else:
        print("問題なし")
        df_index_return.reset_index(inplace=True)
        # インデックスについて同様にリターンを計算してデータベースに保存
        display(df_index_return.tail(5))
        for _col in [
            s
            for s in df_index_return.columns
            if s.startswith("Return") or s.startswith("Forward_Return")
        ]:
            _df_slice = (
                df_index_return[["Date", "Ticker", _col]]
                .rename(columns={_col: "value"})
                .assign(variable=_col)
            )
            _df_slice["value"] = _df_slice["value"].astype(float)
            _df_slice["Date"] = pd.to_datetime(_df_slice["Date"])
            db_utils.delete_table_from_database(
                db_path=bloomberg_index_db_path, table_name=_col
            )
            # ------------------------------------------------------------------------------------
            # データチェック
            # 銘柄によってはdateが1カ月ずつ連続でデータがあるとは限らない
            # 価格データがない場合にpct_changeを素直に実行するとリターンの期間が他の銘柄とずれる
            # そのため、全dateの長さと銘柄ごとのdateの長さを比較する
            blp.store_to_database(
                df=_df_slice,
                db_path=bloomberg_index_db_path,
                table_name=_col,
                primary_keys=["Date", "Ticker", "variable"],
            )  # 問題なければデータベースに保存


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3-3. Active Return 計算

    テーブル作成し、データベースに保存
    """)


@app.cell
def _(
    BLOOMBERG_UNIVERSE_TICKER,
    bloomberg_index_db_path,
    display,
    factset_utils,
    financials_db_path,
    pd,
    performance_metrics_utils,
    sqlite3,
):
    return_cols = [
        "Return_1M",
        "Return_1M_annlzd",
        "Forward_Return_1M",
        "Forward_Return_1M_annlzd",
        "Return_3M",
        "Return_3M_annlzd",
        "Forward_Return_3M",
        "Forward_Return_3M_annlzd",
        "Return_6M",
        "Return_6M_annlzd",
        "Forward_Return_6M",
        "Forward_Return_6M_annlzd",
        "Return_12M",
        "Return_12M_annlzd",
        "Forward_Return_12M",
        "Forward_Return_12M_annlzd",
        "Return_3Y",
        "Return_3Y_annlzd",
        "Forward_Return_3Y",
        "Forward_Return_3Y_annlzd",
        "Return_5Y",
        "Return_5Y_annlzd",
        "Forward_Return_5Y",
        "Forward_Return_5Y_annlzd",
    ]
    union_queries_index = []
    for _table in return_cols:
        union_queries_index.append(
            f"SELECT Date, Ticker, value, variable FROM '{_table}' WHERE Ticker = '{BLOOMBERG_UNIVERSE_TICKER}'"
        )
    union_query_index = " UNION ALL ".join(union_queries_index)
    with sqlite3.connect(bloomberg_index_db_path) as _conn:
        df_return_index = pd.read_sql(
            union_query_index, con=_conn, parse_dates=["Date"]
        ).rename(columns={"Date": "date", "Ticker": "symbol"})
    df_return_index = df_return_index.drop_duplicates(ignore_index=True)
    print(f"✅ インデックスデータ: {len(df_return_index):,}件")
    union_queries_security = []
    for _table in return_cols:
        union_queries_security.append(
            f"SELECT date, P_SYMBOL, value, variable FROM '{_table}'"
        )
    union_query_security = " UNION ALL ".join(union_queries_security)
    with sqlite3.connect(financials_db_path) as _conn:
        df_return_security = pd.read_sql(
            union_query_security, con=_conn, parse_dates=["date"]
        ).rename(columns={"P_SYMBOL": "symbol"})
    df_return_security = df_return_security.drop_duplicates(ignore_index=True)
    print(f"✅ 個別銘柄データ: {len(df_return_security):,}件")
    df_returns = pd.concat([df_return_index, df_return_security], ignore_index=True)
    display(df_returns.tail(3))
    df_active_returns = performance_metrics_utils.calculate_active_returns_vectorized(
        df_returns=df_returns,
        return_cols=return_cols,
        benchmark_ticker=BLOOMBERG_UNIVERSE_TICKER,
        verbose=False,
    )
    display(df_active_returns.tail(3))
    # ------------------------------------
    # インデックスのリターン
    # データ取得
    # 個別銘柄のリターン
    # concatenate returns
    # アクティブリターン計算
    # Active return: データベース保存
    # 推奨方法：直列書き込み版
    results = factset_utils.insert_active_returns_optimized_sqlite(
        df_active_returns=df_active_returns,
        return_cols=return_cols,
        db_path=financials_db_path,
        benchmark_ticker=BLOOMBERG_UNIVERSE_TICKER,
        batch_size=10000,
        verbose=True,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 🧪PE 取得テスト from Bloomberg（⚠️ データ取得は難しそう）

    -   Forward PE(BEST_PE_RATIO), Trailing PE(PE_RATIO), と Forward EPS(BEST_EPS), Trailing EPS(TRAIL_12M_EPS_BEF_XO_ITEM)を取得

    -   (- Forward PE と Trailing PE の差分のカラムを追加
    -   PEG ratio = BEST_EPS / BEST_PE_RATIO のカラムを追加
        )
    """)


@app.cell
def _(UNIVERSE_CODE, bloomberg_utils, factset_index_db_path, pd, sqlite3):
    fields = ["BEST_PE_RATIO", "BEST_EPS", "PE_RATIO", "TRAIL_12M_EPS_BEF_XO_ITEM"]
    with sqlite3.connect(factset_index_db_path) as _conn:
        sedol_list = pd.read_sql(
            f"SELECT DISTINCT `SEDOL` FROM {UNIVERSE_CODE}", con=_conn
        )["SEDOL"].tolist()
        sedol_list = [s + " Equity" for s in sedol_list]
        _date_list = pd.read_sql(
            f"SELECT DISTINCT `date` FROM {UNIVERSE_CODE} ORDER BY `date`",
            con=_conn,
            parse_dates=["date"],
        )["date"].tolist()
    print("SEDOLと日付のリスト取得完了")
    blp_1 = bloomberg_utils.BlpapiCustom()
    for field in fields:
        df_6 = (
            blp_1.get_historical_data_with_overrides(
                securities=sedol_list,
                id_type="sedol",
                fields=[field],
                start_date=min(_date_list).strftime("%Y%m%d"),
                end_date=max(_date_list).strftime("%Y%m%d"),
                periodicity="MONTHLY",
                verbose=True,
            )
            .sort_values(["Date", "Identifier"], ignore_index=True)
            .drop(columns=["ID_Type"])
            .assign(Date=lambda x: pd.to_datetime(x["Date"]))
        )
        df_6 = (
            pd.melt(
                df_6,
                id_vars=["Date", "Identifier"],
                value_vars=[field],
                var_name="variable",
            )
            .rename(columns={"Identifier": "SEDOL"})
            .assign(SEDOL=lambda x: x["SEDOL"].str.replace(" Equity", ""))
        )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ✅ データベースチェック
    """)


@app.cell
def _(bloomberg_valuation_db_path, display, pd, sqlite3):
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        df_7 = pd.read_sql(
            "SELECT * FROM BEST_PE_RATIO", con=_conn, parse_dates=["Date"]
        )
        display(df_7["Date"].sort_values().unique())
        display(df_7.sort_values("Date", ignore_index=True).drop_duplicates())


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ✅ 欠損割合チェック
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    bloomberg_valuation_db_path,
    display,
    factset_index_db_path,
    factset_utils,
    pd,
    sqlite3,
):
    df_weight = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    )
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        df_forward_pe = pd.read_sql(
            "SELECT * FROM BEST_PE_RATIO", parse_dates=["Date"], con=_conn
        ).rename(columns={"value": "BEST_PE_RATIO", "Date": "date"})
        df_actual_pe = pd.read_sql(
            "SELECT * FROM PE_RATIO", parse_dates=["Date"], con=_conn
        ).rename(columns={"value": "PE_RATIO", "Date": "date"})
        df_actual_pe.drop(columns=["variable"], inplace=True)
        df_pe = pd.merge(
            df_forward_pe, df_actual_pe, on=["date", "SEDOL"], how="outer"
        ).assign(date=lambda x: x["date"] + pd.offsets.MonthEnd(0))
    df_merged_2 = pd.merge(df_weight, df_pe, on=["date", "SEDOL"], how="outer").dropna(
        subset=["Weight (%)", "BEST_PE_RATIO", "PE_RATIO"], how="any", ignore_index=True
    )
    display(df_merged_2.tail(5))
    return (df_merged_2,)


@app.cell
def _(df_merged_2, display, pd):
    _g = pd.DataFrame(
        df_merged_2.groupby(["date"])["Weight (%)"].agg("sum")
    ).reset_index()
    display(_g.query("date>='2023-01-01'"))


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Bloomberg valuation データについてメモ

    -   直近 1,2 年分程度しか forward+actual pe は取れない
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Factor 計算
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-1. 成長率計算（Factset）
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 1. QoQ, YoY, 3Yr CAGR, 5Yr CAGR の値を計算し、データベースに保存する。
    """)


@app.cell
def _():
    factor_list = [
        "FF_SALES",
        "FF_EBITDA_OPER",
        "FF_EBIT_OPER",
        "FF_EPS",
        "FF_OPER_CF",
        "FF_ASSETS",
        "FF_COM_EQ",
        "FF_DEBT",
        "FF_DEBT_LT",
        "FF_DEBT_ST",
        "FF_OPER_INC",
        "FF_CAPEX",
        "FF_FREE_CF",
        "FF_EPS_DIL",
    ]
    period_list = ["QoQ", "YoY", "CAGR_3Y", "CAGR_5Y"]
    return factor_list, period_list


@app.cell
def _(
    db_utils,
    display,
    factor_list,
    factset_utils,
    financials_db_path,
    gc,
    pd,
    period_list,
    roic_utils,
    sqlite3,
    tqdm,
):
    query_2 = [f"SELECT * FROM `{_table}`" for _table in factor_list]
    query_2 = " UNION ALL ".join(query_2)
    with sqlite3.connect(financials_db_path) as _conn:
        _df_all = (
            pd.read_sql(query_2, con=_conn, parse_dates=["date"])
            .sort_values("date", ignore_index=True)
            .assign(
                variable=lambda x: x["variable"].astype("category"),
                P_SYMBOL=lambda x: x["P_SYMBOL"].astype("category"),
            )
            .sort_values(["variable", "P_SYMBOL", "date"], ignore_index=True)
        )
    display(_df_all)
    _grouped = _df_all.groupby("variable", observed=True)
    _total_steps = len(factor_list)
    for _factor_name, _df_factor in tqdm(_grouped, total=_total_steps, desc="Factors"):
        _df_base = _df_factor.copy()
        for _growth in period_list:
            _new_variable_name = f"{_factor_name}_{_growth}"
            _df_result = roic_utils.calculate_growth(
                df=_df_base, data_name=str(_factor_name), growth_type=_growth
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=_new_variable_name
            )
            factset_utils.store_to_database(
                df=_df_result,
                db_path=financials_db_path,
                table_name=_new_variable_name,
                verbose=False,
            )
        del _df_base
        gc.collect()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 2. ファクターのランクを計算し、データベースに保存する。
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    factor_list,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    pd,
    period_list,
):
    # -----------------------------------
    # load data
    df_weight_1 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    ).assign(date=lambda x: pd.to_datetime(x["date"]))
    # 構成銘柄情報
    factset_utils.process_rank_calculation_store_to_db(
        df_weight=df_weight_1,
        factor_list=factor_list,
        financials_db_path=financials_db_path,
        period_list=period_list,
    )


@app.cell
def _(db_utils, display, financials_db_path, pd, sqlite3):
    table_names_2 = db_utils.get_table_names(financials_db_path)
    display([s for s in table_names_2 if "QoQ" in s or "YoY" in s or "CAGR" in s])
    with sqlite3.connect(financials_db_path) as _conn:
        df_8 = pd.read_sql(
            "SELECT * FROM FF_OPER_INC_QoQ_PctRank ORDER BY 'date'",
            con=_conn,
            parse_dates=["date"],
        )
        display(df_8.head())


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-2. マージン改善率
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 1. QoQ, YoY, 3Yr, 5Yr の変化値（delta）を計算し、データベースに保存する。
    """)


@app.cell
def _():
    factor_list_1 = [
        "FF_EBITDA_OPER_MGN",
        "FF_EBIT_OPER_MGN",
        "FF_NET_MGN",
        "FF_OPER_MGN",
        "FF_PTX_MGN",
        "FF_GROSS_MGN",
        "FF_ROA",
        "FF_ROE",
        "FF_ROIC",
        "FF_ROTC",
    ]
    period_list_1 = ["CHANGE_QoQ", "CHANGE_YoY", "CHANGE_3Y", "CHANGE_5Y"]
    query_3 = [
        f"SELECT `date`, `P_SYMBOL`, `variable`, `value` FROM `{_table}`"
        for _table in factor_list_1
    ]
    query_3 = " UNION ALL ".join(query_3)
    return factor_list_1, period_list_1, query_3


@app.cell
def _(
    db_utils,
    display,
    factor_list_1,
    factset_utils,
    financials_db_path,
    gc,
    pd,
    period_list_1,
    query_3,
    roic_utils,
    sqlite3,
    tqdm,
):
    with sqlite3.connect(financials_db_path) as _conn:
        _df_all = (
            pd.read_sql(query_3, con=_conn, parse_dates=["date"])
            .sort_values("date", ignore_index=True)
            .assign(
                variable=lambda x: x["variable"].astype("category"),
                P_SYMBOL=lambda x: x["P_SYMBOL"].astype("category"),
            )
            .sort_values(["variable", "P_SYMBOL", "date"], ignore_index=True)
        )
    display(_df_all)
    _grouped = _df_all.groupby("variable", observed=True)
    _total_steps = len(factor_list_1)
    for _factor_name, _df_factor in tqdm(_grouped, total=_total_steps, desc="Factors"):
        _df_base = _df_factor.copy()
        for _growth in period_list_1:
            _new_variable_name = f"{_factor_name}_{_growth}"
            _df_result = roic_utils.calculate_margin_improvement(
                df=_df_base, data_name=str(_factor_name), growth_type=_growth
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=_new_variable_name
            )
            factset_utils.store_to_database(
                df=_df_result,
                db_path=financials_db_path,
                table_name=_new_variable_name,
                verbose=False,
            )
        del _df_base
        gc.collect()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 2. ファクターのランクを計算し、データベースに保存する
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    factor_list_1,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    pd,
    period_list_1,
):
    # -----------------------------------
    # load data
    df_weight_2 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    ).assign(date=lambda x: pd.to_datetime(x["date"]))
    # 構成銘柄情報
    factset_utils.process_rank_calculation_store_to_db(
        df_weight=df_weight_2,
        factor_list=factor_list_1,
        financials_db_path=financials_db_path,
        period_list=period_list_1,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-3. Composite Growth Factor
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 1. データロード&欠損値確認 -> 欠損値はセクター中央値で補完
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    np,
    pd,
):
    factor_list_2 = [
        "FF_SALES_CAGR_3Y_PctRank",
        "FF_OPER_INC_CAGR_3Y_PctRank",
        "FF_OPER_MGN_CHANGE_3Y_PctRank",
        "FF_GROSS_MGN_CHANGE_3Y_PctRank",
        "FF_NET_MGN_CHANGE_3Y_PctRank",
    ]
    _df_factor = factset_utils.load_financial_data(
        financials_db_path=financials_db_path, factor_list=factor_list_2
    )
    df_weight_3 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    )
    df_9 = (
        factset_utils.merge_idx_constituents_and_financials(
            df_weight=df_weight_3, df_factor=_df_factor
        )
        .fillna(np.nan)
        .dropna(subset=factor_list_2, how="all")
        .dropna(subset=["Weight (%)"], ignore_index=True)
    )
    display(df_9.head())
    factset_utils.check_missing_value_and_fill_by_sector_median(
        df=df_9, factor_list=factor_list_2
    )
    display(df_9)
    _g = pd.DataFrame(df_9.groupby(["date"])["Weight (%)"].agg("sum"))
    _g_count = pd.DataFrame(df_9.groupby(["date"])["SEDOL"].count())
    g_merged = pd.merge(_g, _g_count, left_index=True, right_index=True)
    display(g_merged)
    return (df_9,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 2. Composite Growth Factor 計算
    """)


@app.cell
def _(db_utils, df_9, factset_utils, financials_db_path, pd):
    _blend_weight = {
        "FF_SALES_CAGR_3Y_PctRank": 0.2,
        "FF_OPER_INC_CAGR_3Y_PctRank": 0.2,
        "FF_OPER_MGN_CHANGE_3Y_PctRank": 0.2,
        "FF_GROSS_MGN_CHANGE_3Y_PctRank": 0.2,
        "FF_NET_MGN_CHANGE_3Y_PctRank": 0.2,
    }
    _factor_name = "Factor_Composite_Growth"
    df_10 = factset_utils.create_factor(
        df=df_9, factor_name=_factor_name, blend_weight=_blend_weight
    )
    for _variable in [
        "Factor_Composite_Growth_Score",
        "Factor_Composite_Growth_Score_Rank",
    ]:
        _df_slice = (
            df_10[["date", "P_SYMBOL", _variable]]
            .assign(variable=_variable, date=lambda x: pd.to_datetime(x["date"]))
            .rename(columns={_variable: "value"})
        )
        db_utils.delete_table_from_database(
            db_path=financials_db_path, table_name=_variable
        )
        factset_utils.store_to_database(
            df=_df_slice, db_path=financials_db_path, table_name=_variable, verbose=True
        )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-4. Valuation（Bloomberg） -> ⚠️ データ不足のためスキップ

    `BEST_EPS`と`TRAIL_12M_EPS_BEF_XO_ITEM`の QoQ, YoY, 3Yr CAGR, 5Yr CAGR の値を計算し、データベースに保存する。
    """)


@app.cell
def _(
    bloomberg_utils,
    bloomberg_valuation_db_path,
    db_utils,
    pd,
    roic_utils,
    sqlite3,
    tqdm,
):
    data_list = ["BEST_PE_RATIO", "BEST_EPS", "PE_RATIO", "TRAIL_12M_EPS_BEF_XO_ITEM"]
    blp_2 = bloomberg_utils.BlpapiCustom()
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        for data in tqdm(data_list):
            df_11 = (
                pd.read_sql(f"SELECT * FROM `{data}`", con=_conn, parse_dates=["Date"])
                .sort_values("Date", ignore_index=True)
                .rename(columns={"Date": "date", "SEDOL": "P_SYMBOL"})
            )
            for _growth in ["QoQ", "YoY", "CAGR_3Y", "CAGR_5Y"]:
                df_growth = df_11.copy()
                new_variable = f"{data}_{_growth}"
                df_growth = roic_utils.calculate_growth(
                    df=df_growth, data_name=data, growth_type=_growth
                ).rename(columns={"date": "Date", "P_SYMBOL": "SEDOL"})
                db_utils.delete_table_from_database(
                    db_path=bloomberg_valuation_db_path, table_name=new_variable
                )
                blp_2.store_to_database(
                    df=df_growth,
                    db_path=bloomberg_valuation_db_path,
                    table_name=new_variable,
                    primary_keys=["date", "SEDOL", "variable"],
                )


@app.cell
def _(bloomberg_valuation_db_path, display, pd, sqlite3):
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        df_12 = pd.read_sql("SELECT * FROM BEST_EPS", con=_conn, parse_dates=["Date"])
        display(df_12)


@app.cell
def _(bloomberg_valuation_db_path, db_utils, display):
    _tables = db_utils.get_table_names(bloomberg_valuation_db_path)
    display(_tables)


@app.cell
def _(
    UNIVERSE_CODE,
    bloomberg_valuation_db_path,
    display,
    factset_index_db_path,
    pd,
    sqlite3,
    tqdm,
):
    query_4 = f"\n    SELECT\n        `date`, `P_SYMBOL`, `SEDOL`, `FG_COMPANY_NAME`, `Asset ID`, `GICS Sector`, `Weight (%)`\n    FROM\n        {UNIVERSE_CODE}\n"
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_weight_4 = pd.read_sql(query_4, parse_dates=["date"], con=_conn)
    factor_list_3 = ["BEST_EPS", "BEST_PE_RATIO"]
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        for _factor in tqdm(factor_list_3):
            df_13 = (
                pd.read_sql(
                    f"SELECT `Date`, `SEDOL`, `value` FROM `{_factor}`",
                    con=_conn,
                    parse_dates=["Date"],
                )
                .rename(columns={"Date": "date"})
                .assign(
                    date=lambda row: pd.to_datetime(row["date"])
                    + pd.tseries.offsets.MonthEnd(0)
                )
                .sort_values("date", ignore_index=True)
                .rename(columns={"value": _factor})
            )
            df_13 = (
                pd.merge(df_weight_4, df_13, on=["date", "SEDOL"], how="outer")
                .drop_duplicates(subset=["date", "SEDOL"])
                .dropna(
                    subset=["Weight (%)", _factor], how="any", axis=0, ignore_index=True
                )
            )
            _g = df_13.groupby(["date"])["Weight (%)"].agg("sum").to_frame()
            display(_g.tail(50))


@app.cell
def _(
    UNIVERSE_CODE,
    bloomberg_valuation_db_path,
    display,
    factset_index_db_path,
    itertools,
    pd,
    sqlite3,
    tqdm,
):
    query_5 = f"\n    SELECT\n        `date`, `P_SYMBOL`, `SEDOL`, `FG_COMPANY_NAME`, `Asset ID`, `GICS Sector`, `Weight (%)`\n    FROM\n        {UNIVERSE_CODE}\n"
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_weight_5 = pd.read_sql(query_5, parse_dates=["date"], con=_conn)
    factor_list_4 = ["BEST_EPS", "BEST_PE_RATIO"]
    period_list_2 = ["QoQ", "YoY", "CAGR_3Y", "CAGR_5Y"]
    total_iterations = len(factor_list_4) * len(period_list_2)
    print(f"処理総数: {total_iterations} 回")
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        for _factor, periods in tqdm(
            itertools.product(factor_list_4, period_list_2),
            total=total_iterations,
            desc="ファクター処理進捗",
        ):
            factor_growth = f"{_factor}_{periods}"
            df_14 = (
                pd.read_sql(
                    f"SELECT `Date`, `SEDOL`, `value` FROM `{factor_growth}`",
                    con=_conn,
                    parse_dates=["Date"],
                )
                .rename(columns={"Date": "date"})
                .assign(
                    date=lambda row: pd.to_datetime(row["date"])
                    + pd.tseries.offsets.MonthEnd(0)
                )
                .sort_values("date", ignore_index=True)
                .rename(columns={"value": factor_growth})
            )
            df_14 = (
                pd.merge(df_weight_5, df_14, on=["date", "SEDOL"], how="outer")
                .drop_duplicates(subset=["date", "SEDOL"])
                .dropna(
                    subset=["Weight (%)", factor_growth],
                    how="any",
                    axis=0,
                    ignore_index=True,
                )
            )
            display(df_14)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-5. ROIC Label Factor（Factset）

    -   ROIC(ROE) + Security Code
        -   セクター中立
        -   金融セクターのみ ROIC の代わりに ROE を使用（ただしデータフレームのカラム名は ROIC で表記）
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    np,
    pd,
    roic_utils,
):
    # ----------------------------------------
    # 1. get ROIC and ROE data
    # 2. get security info(Index constituents)
    df_roic_and_roe = factset_utils.load_financial_data(
        financials_db_path=financials_db_path, factor_list=["FF_ROIC", "FF_ROE"]
    )
    security_info = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    )
    df_roic_merged = (
        factset_utils.merge_idx_constituensts_and_financials(
            df_weight=security_info, df_factor=df_roic_and_roe
        )
        .assign(
            ROIC=lambda x: np.where(
                x["GICS Sector"] == "Financials", x["FF_ROE"], x["FF_ROIC"]
            )
        )
        .dropna(subset=["Weight (%)", "ROIC"], how="any", ignore_index=True)
        .drop(columns=["FF_ROIC", "FF_ROE"])
    )
    year_period = 3
    df_roic_merged = roic_utils.add_factor_rank_cols(
        df_roic_merged, factor_name="ROIC"
    ).rename(columns={"P_SYMBOL": "Symbol"})
    df_roic_merged = roic_utils.add_shifted_factor_cols_month(
        df_roic_merged,
        factor_name="ROIC_Rank",
        shift_month=list(range(1, int(year_period * 12) + 1)),
        shift_direction="Past",
    ).rename(columns={"Symbol": "P_SYMBOL"})
    roic_label_name = f"ROIC_label_Past{year_period}Y"
    df_roic_merged[roic_label_name] = df_roic_merged.apply(
        lambda row: roic_utils.test_assign_roic_label(
            row=row,
            freq="annual",
            shift_direction="Past",
            year_period=year_period,
            judge_by_slope=False,
        ),
        axis=1,
    )
    df_15 = df_roic_merged.copy()
    # merge
    df_15 = (
        df_15[["date", "P_SYMBOL", roic_label_name]]
        .rename(columns={roic_label_name: "value"})
        .dropna(subset=["value"], ignore_index=True)
        .assign(variable=roic_label_name, date=lambda row: pd.to_datetime(row["date"]))
    )
    display(df_15.tail(10))
    # sector中立でROICをランキング
    # ROICラベルを付与
    # データベース保存
    factset_utils.store_to_database(
        df=df_15, db_path=financials_db_path, table_name=roic_label_name
    )  # year_periodまでさかのぼってROICの移行を見る
    return df_roic_merged, roic_label_name


@app.cell
def _(df_roic_merged, display, pd, roic_label_name):
    df_16 = df_roic_merged.copy()
    roic_count = pd.pivot(
        pd.DataFrame(
            df_16.groupby(["date", "GICS Sector", roic_label_name])["P_SYMBOL"].count()
        ).reset_index(),
        index=["date", "GICS Sector"],
        columns=roic_label_name,
    ).reset_index()
    # --- label count ---
    display(roic_count.loc[roic_count["GICS Sector"] == "Information Technology"])
    roic_count = pd.pivot(
        pd.DataFrame(
            df_16.groupby(["date", "GICS Sector", "ROIC_Rank"])["P_SYMBOL"].count()
        ).reset_index(),
        index=["date", "GICS Sector"],
        columns="ROIC_Rank",
    ).reset_index()
    display(roic_count.loc[roic_count["GICS Sector"] == "Information Technology"])
    weight_total_count = (
        df_16.groupby(["date"])["Weight (%)"]
        .agg(["count", "sum"])
        .rename(columns={"count": "Num of Securities", "sum": "Total Weight (%)"})
        .sort_index()
    )
    weight_sector_count = (
        df_16.groupby(["date", "GICS Sector"])["Weight (%)"]
        .agg(["count", "sum"])
        .rename(columns={"count": "Num of Securities", "sum": "Total Weight (%)"})
        .sort_index()
    )
    display(weight_total_count)
    display(weight_sector_count)
    roic_label_count = (
        df_16.groupby(["date", roic_label_name])["Weight (%)"]
        .agg(["count", "sum"])
        .rename(columns={"count": "Num of Securities", "sum": "Total Weight (%)"})
        .sort_index()
    )
    # --- weight check ---
    display(roic_label_count)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-6. ROIC 分位移動(⚠️not completed)

    -   3 年前の ROIC5 分位 -> 現在の ROIC5 分位への移動をラベリング
    -   Financials セクターは ROIC の代わりに ROE 使用
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    np,
    roic_utils,
):
    df_weight_6 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    )
    _df_factor = factset_utils.load_financial_data(
        financials_db_path=financials_db_path,
        factor_list=["FF_ROIC_Rank", "FF_ROE_Rank"],
    )
    df_roic_rank = (
        factset_utils.merge_idx_constituensts_and_financials(
            df_weight=df_weight_6, df_factor=_df_factor
        )
        .assign(
            ROIC_Rank=lambda x: np.where(
                x["GICS Sector"] == "Financials", x["FF_ROE_Rank"], x["FF_ROIC_Rank"]
            )
        )
        .drop(columns=["FF_ROIC_Rank", "FF_ROE_Rank"])
        .rename(columns={"SEDOL": "Symbol"})
    )
    df_roic_rank = (
        roic_utils.add_shifted_factor_cols_month(
            df_roic_rank,
            factor_name="ROIC_Rank",
            shift_month=[36],
            shift_direction="Past",
        )
        .rename(columns={"Symbol": "SEDOL"})
        .dropna(subset=["ROIC_Rank", "ROIC_Rank_36MAgo"], how="any")
        .sort_values(["SEDOL", "date"], ignore_index=True)
    )
    display(df_roic_rank)
    return (df_roic_rank,)


@app.cell
def _(df_roic_rank, display, pd):
    _g = pd.DataFrame(df_roic_rank.groupby("date")["Weight (%)"].agg("sum"))
    display(_g)
    _g_count = (
        pd.DataFrame(df_roic_rank.groupby(["date", "GICS Sector"])["SEDOL"].count())
        .reset_index()
        .pivot(index=["date"], columns="GICS Sector", values="SEDOL")
    )
    display(_g_count)


@app.cell
def _(df_roic_rank, display, pd):
    g_roic_rank_shift = (
        pd.DataFrame(
            df_roic_rank.groupby(["date", "ROIC_Rank", "ROIC_Rank_36MAgo"])[
                "SEDOL"
            ].count()
        )
        .reset_index()
        .rename(columns={"SEDOL": "n_SEDOL"})
    )
    g_sedol_count_present_rank = (
        pd.DataFrame(g_roic_rank_shift.groupby(["date", "ROIC_Rank"])["n_SEDOL"].sum())
        .reset_index()
        .rename(columns={"n_SEDOL": "n_SEDOL_ROIC_Rank"})
    )

    g_sedol_count_past_rank = (
        pd.DataFrame(
            g_roic_rank_shift.groupby(["date", "ROIC_Rank_36MAgo"])["n_SEDOL"].sum()
        )
        .reset_index()
        .rename(columns={"n_SEDOL": "n_SEDOL_ROIC_Rank_36MAgo"})
    )

    g_roic_rank_shift = pd.merge(
        g_roic_rank_shift,
        g_sedol_count_present_rank,
        on=["date", "ROIC_Rank"],
        how="left",
    )
    g_roic_rank_shift = pd.merge(
        g_roic_rank_shift,
        g_sedol_count_past_rank,
        on=["date", "ROIC_Rank_36MAgo"],
        how="left",
    )

    g_roic_rank_shift = g_roic_rank_shift.assign(
        n_SEDOL_ROIC_Rank_pct=lambda x: x["n_SEDOL"].div(x["n_SEDOL_ROIC_Rank"]),
        n_SEDOL_ROIC_Rank_36MAgo_pct=lambda x: x["n_SEDOL"].div(
            x["n_SEDOL_ROIC_Rank_36MAgo"]
        ),
    )
    pd.options.display.precision = 2
    display(g_roic_rank_shift[g_roic_rank_shift["ROIC_Rank"] == "rank1"].tail(50))


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-7. Size Factor
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 1. QoQ、YoY、3Yr CAGR, 5Y CAGR を計算してデータベースに保存する。
    """)


@app.cell
def _(itertools):
    factor_list_5 = ["FF_SALES", "FF_ASSETS", "FF_COM_EQ", "FF_SHLDRS_EQ"]
    period_list_3 = ["QoQ", "YoY", "CAGR_3Y", "CAGR_5Y"]
    factor_growth_list = [
        f"{_factor}_{periods}"
        for _factor, periods in itertools.product(factor_list_5, period_list_3)
    ]
    return factor_list_5, period_list_3


@app.cell
def _(
    db_utils,
    display,
    factor_list_5,
    factset_utils,
    financials_db_path,
    gc,
    pd,
    period_list_3,
    roic_utils,
    sqlite3,
    tqdm,
):
    query_6 = [f"SELECT * FROM `{_table}`" for _table in factor_list_5]
    query_6 = " UNION ALL ".join(query_6)
    with sqlite3.connect(financials_db_path) as _conn:
        _df_all = (
            pd.read_sql(query_6, con=_conn, parse_dates=["date"])
            .sort_values("date", ignore_index=True)
            .assign(
                variable=lambda x: x["variable"].astype("category"),
                P_SYMBOL=lambda x: x["P_SYMBOL"].astype("category"),
            )
            .sort_values(["variable", "P_SYMBOL", "date"], ignore_index=True)
        )
    display(_df_all)
    _grouped = _df_all.groupby("variable", observed=True)
    _total_steps = len(factor_list_5)
    for _factor_name, _df_factor in tqdm(_grouped, total=_total_steps, desc="Factors"):
        _df_base = _df_factor.copy()
        for _growth in period_list_3:
            _new_variable_name = f"{_factor_name}_{_growth}"
            _df_result = roic_utils.calculate_growth(
                df=_df_base, data_name=str(_factor_name), growth_type=_growth
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=_new_variable_name
            )
            factset_utils.store_to_database(
                df=_df_result,
                db_path=financials_db_path,
                table_name=_new_variable_name,
                verbose=False,
            )
        del _df_base
        gc.collect()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 2. ファクターのランクを計算し、データベースに保存する。
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    factor_list_5,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    pd,
):
    # -----------------------------------
    # load data
    df_weight_7 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    ).assign(date=lambda x: pd.to_datetime(x["date"]))
    # 構成銘柄情報
    factset_utils.process_rank_calculation_store_to_db(
        df_weight=df_weight_7,
        factor_list=factor_list_5,
        financials_db_path=financials_db_path,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 3. データロード&欠損値確認：欠損値はセクター中央値で補完
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    np,
):
    factor_list_6 = [
        "FF_SALES_CAGR_3Y_PctRank",
        "FF_ASSETS_PctRank",
        "FF_COM_EQ_PctRank",
        "FF_SHLDRS_EQ_PctRank",
    ]
    _df_factor = factset_utils.load_financial_data(
        financials_db_path=financials_db_path, factor_list=factor_list_6
    )
    df_weight_8 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    )
    df_17 = (
        factset_utils.merge_idx_constituents_and_financials(
            df_weight=df_weight_8, df_factor=_df_factor
        )
        .fillna(np.nan)
        .dropna(subset=factor_list_6, how="all")
        .dropna(subset=["Weight (%)"], ignore_index=True)
    )
    display(df_17.head())
    df_17 = factset_utils.check_missing_value_and_fill_by_sector_median(
        df=df_17, factor_list=factor_list_6
    )
    return (df_17,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 4. ファクター計算
    """)


@app.cell
def _(db_utils, df_17, display, factset_utils, financials_db_path, pd):
    _blend_weight = {
        "FF_SALES_CAGR_3Y_PctRank": 0.25,
        "FF_ASSETS_PctRank": 0.25,
        "FF_COM_EQ_PctRank": 0.25,
        "FF_SHLDRS_EQ_PctRank": 0.25,
    }
    _factor_name = "Factor_Size"
    df_18 = factset_utils.create_factor(
        df=df_17, factor_name=_factor_name, blend_weight=_blend_weight
    )
    display(df_18.tail(5))
    for _variable in [f"{_factor_name}_Score", f"{_factor_name}_Score_Rank"]:
        _df_slice = (
            df_18[["date", "P_SYMBOL", _variable]]
            .assign(variable=_variable, date=lambda x: pd.to_datetime(x["date"]))
            .rename(columns={_variable: "value"})
        )
        db_utils.delete_table_from_database(
            db_path=financials_db_path, table_name=_variable
        )
        factset_utils.store_to_database(
            df=_df_slice, db_path=financials_db_path, table_name=_variable, verbose=True
        )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-8. Leverage Factor

    -   FF_DEBT_EQ(Debt to Equity ratio)
    -   FF_LIABS_SHLDRS_EQ(Total Liabilities to Shareholders' Equity ratio)
    -   FF_NET_DEBT(Net Debt)
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### (🚧 実装予定)📝 ディスクリプター追加：NET_DEBT_TO_EBITDA_OPER

    -> FF_NET_DEBT / FF_EBITDA_OPER
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    pd,
):
    descriptor_list = ["FF_NET_DEBT", "FF_EBITDA_OPER"]
    df_weight_9 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    ).assign(date=lambda x: pd.to_datetime(x["date"]))
    _df_factor = factset_utils.load_financial_data(
        financials_db_path=financials_db_path, factor_list=descriptor_list
    ).assign(date=lambda x: pd.to_datetime(x["date"]))
    df_merged_3 = factset_utils.merge_idx_constituents_and_financials(
        df_weight=df_weight_9, df_factor=_df_factor
    )
    df_merged_3["NET_DEBT_TO_EBITDA_OPER"] = df_merged_3["FF_NET_DEBT"].div(
        df_merged_3["FF_EBITDA_OPER"]
    )
    display(df_merged_3.loc[df_merged_3["NET_DEBT_TO_EBITDA_OPER"] < 0])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 1. ファクター値を計算してデータベースに保存する
    """)


@app.cell
def _():
    factor_list_7 = ["FF_DEBT_EQ", "FF_LIABS_SHLDRS_EQ", "FF_NET_DEBT"]
    return (factor_list_7,)


@app.cell
def _(
    UNIVERSE_CODE,
    factor_list_7,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    pd,
):
    # -----------------------------------
    # load data
    df_weight_10 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    ).assign(date=lambda x: pd.to_datetime(x["date"]))
    # 構成銘柄情報
    factset_utils.process_rank_calculation_store_to_db(
        df_weight=df_weight_10,
        factor_list=factor_list_7,
        financials_db_path=financials_db_path,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    データロード&欠損値確認: 欠損値はセクター中央値で補完
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    np,
):
    factor_list_8 = [
        "FF_DEBT_EQ_Inv_PctRank",
        "FF_LIABS_SHLDRS_EQ_Inv_PctRank",
        "FF_NET_DEBT_Inv_PctRank",
    ]
    _df_factor = factset_utils.load_financial_data(
        financials_db_path=financials_db_path, factor_list=factor_list_8
    )
    df_weight_11 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    )
    df_19 = (
        factset_utils.merge_idx_constituents_and_financials(
            df_weight=df_weight_11, df_factor=_df_factor
        )
        .fillna(np.nan)
        .dropna(subset=factor_list_8, how="all")
        .dropna(subset=["Weight (%)"], ignore_index=True)
    )
    display(df_19.head())
    df_19 = factset_utils.check_missing_value_and_fill_by_sector_median(
        df=df_19, factor_list=factor_list_8
    )
    return (df_19,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ファクター計算
    """)


@app.cell
def _(db_utils, df_19, display, factset_utils, financials_db_path, pd):
    _blend_weight = {
        "FF_DEBT_EQ_Inv_PctRank": 1 / 3,
        "FF_LIABS_SHLDRS_EQ_Inv_PctRank": 1 / 3,
        "FF_NET_DEBT_Inv_PctRank": 1 / 3,
    }
    _factor_name = "Factor_Leverage"
    df_20 = factset_utils.create_factor(
        df=df_19, factor_name=_factor_name, blend_weight=_blend_weight
    )
    display(df_20.tail(5))
    for _variable in [f"{_factor_name}_Score", f"{_factor_name}_Score_Rank"]:
        _df_slice = (
            df_20[["date", "P_SYMBOL", _variable]]
            .assign(variable=_variable, date=lambda x: pd.to_datetime(x["date"]))
            .rename(columns={_variable: "value"})
        )
        db_utils.delete_table_from_database(
            db_path=financials_db_path, table_name=_variable
        )
        factset_utils.store_to_database(
            df=_df_slice, db_path=financials_db_path, table_name=_variable, verbose=True
        )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-9. Momentum/Reversal Factor
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 1. 区間リターンを計算
    """)


@app.cell
def _(factset_utils, financials_db_path, pd, roic_utils):
    # ----------------------------------------
    # load price data
    _df_price = (
        roic_utils.load_FG_PRICE(db_path=financials_db_path)
        .reset_index()
        .astype({"P_SYMBOL": "category"})
        .assign(date=lambda x: pd.to_datetime(x["date"]))
        .sort_values(["date", "P_SYMBOL"], ignore_index=True)
    )
    df_calculated = roic_utils.calculate_interval_returns(df=_df_price).drop(
        columns=["FG_PRICE"]
    )
    target_columns = [c for c in df_calculated.columns if c not in ["date", "P_SYMBOL"]]
    for col_name in target_columns:
        _df_slice = df_calculated[["date", "P_SYMBOL", col_name]].copy()
        _df_slice = (
            _df_slice.rename(columns={col_name: "value"})
            .assign(variable=col_name)
            .reindex(columns=["date", "P_SYMBOL", "variable", "value"])
        )
        _df_slice = _df_slice.dropna(subset=["value"])
        # 区間リターンを計算
        # store to database
        factset_utils.store_to_database(
            df=_df_slice, db_path=financials_db_path, table_name=col_name
        )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 2. ファクター値を計算して DB 保存
    """)


@app.cell
def _():
    # inverse = False
    momentum_descriptor_list = [
        "Return_1YAgo_to_Current",
        "Return_1YAgo_to_1MAgo",
        "Return_2YAgo_to_1YAgo",
        "Return_3YAgo_to_2YAgo",
    ]

    # inverse = True
    reversal_descriptor_list = [
        "Return_3YAgo_to_1YAgo",
        "Return_1MAgo_to_Current",
    ]
    return momentum_descriptor_list, reversal_descriptor_list


@app.cell
def _(
    UNIVERSE_CODE,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    pd,
    reversal_descriptor_list,
):
    # -----------------------------------
    # load data
    df_weight_12 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    ).assign(date=lambda x: pd.to_datetime(x["date"]))
    # 構成銘柄情報
    factset_utils.process_rank_calculation_store_to_db(
        df_weight=df_weight_12,
        factor_list=reversal_descriptor_list,
        financials_db_path=financials_db_path,
        sector_neutral_mode=False,
        inversed=True,
    )
    # Momentum -> inversed=False
    # セクター中立なし
    # process_rank_calculation_store_to_db(
    #     df_weight=df_weight,
    #     factor_list=momentum_descriptor_list,
    #     financials_db_path=financials_db_path,
    #     sector_neutral_mode=False,
    #     inversed=False,
    # )
    # # セクター中立あり
    #     sector_neutral_mode=True,
    # Reversal -> inversed=True
    # セクター中立あり
    factset_utils.process_rank_calculation_store_to_db(
        df_weight=df_weight_12,
        factor_list=reversal_descriptor_list,
        financials_db_path=financials_db_path,
        sector_neutral_mode=True,
        inversed=True,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 3. データロード&欠損値確認: 欠損値はセクター中央値で補完
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    display,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    momentum_descriptor_list,
    np,
):
    factor_list_9 = [s + "_PctRank" for s in momentum_descriptor_list]
    _df_factor = factset_utils.load_financial_data(
        financials_db_path=financials_db_path, factor_list=factor_list_9
    )
    df_weight_13 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    )
    df_21 = (
        factset_utils.merge_idx_constituents_and_financials(
            df_weight=df_weight_13, df_factor=_df_factor
        )
        .fillna(np.nan)
        .dropna(subset=factor_list_9, how="all")
        .dropna(subset=["Weight (%)"], ignore_index=True)
    )
    df_21 = df_21.loc[df_21["date"].dt.year >= 2009]
    display(df_21.head())
    df_21 = factset_utils.check_missing_value_and_fill_by_sector_median(
        df=df_21, factor_list=factor_list_9
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### （🚧 工事中）4. ファクター計算
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-10. その他の財務項目

    時点でのランク、パーセントランク、ZScore のみ計算
    """)


@app.cell
def _():
    # ファクター値
    factor_list_10 = [
        "FF_ASSETS",
        "FF_BPS",
        "FF_BPS_TANG",
        "FF_CAPEX",
        "FF_CASH_ST",
        "FF_COGS",
        "FF_COM_EQ",
        "FF_CURR_RATIO",
        "FF_DEBT",
        "FF_DEBT_ENTRPR_VAL",
        "FF_DEBT_EQ",
        "FF_DEBT_LT",
        "FF_DEBT_ST",
        "FF_DEP_AMORT_EXP",
        "FF_DIV_YLD",
        "FF_DPS",
        "FF_EBITDA_OPER",
        "FF_EBITDA_OPER_MGN",
        "FF_EBIT_OPER",
        "FF_EBIT_OPER_MGN",
        "FF_ENTRPR_VAL_EBITDA_OPER",
        "FF_ENTRPR_VAL_EBIT_OPER",
        "FF_ENTRPR_VAL_SALES",
        "FF_EPS",
        "FF_EPS_DIL",
        "FF_FREE_CF",
        "FF_FREE_PS_CF",
        "FF_GROSS_INC",
        "FF_GROSS_MGN",
        "FF_INC_TAX",
        "FF_INT_EXP_NET",
        "FF_LIABS",
        "FF_LIABS_SHLDRS_EQ",
        "FF_MIN_INT_ACCUM",
        "FF_NET_DEBT",
        "FF_NET_INC",
        "FF_NET_MGN",
        "FF_OPER_CF",
        "FF_OPER_INC",
        "FF_OPER_MGN",
        "FF_OPER_PS_NET_CF",
        "FF_PAY_OUT_RATIO",
        "FF_PBK",
        "FF_PE",
        "FF_PFD_STK",
        "FF_PPE_NET",
        "FF_PSALES",
        "FF_PTX_INC",
        "FF_PTX_MGN",
        "FF_QUICK_RATIO",
        "FF_ROA",
        "FF_ROE",
        "FF_ROIC",
        "FF_ROTC",
        "FF_SALES",
        "FF_SALES_PS",
        "FF_SGA",
        "FF_SHLDRS_EQ",
        "FF_STK_OPT_EXP",
        "FF_STK_PURCH_CF",
        "FF_TAX_RATE",
        "FF_WKCAP",
    ]
    return (factor_list_10,)


@app.cell
def _(
    UNIVERSE_CODE,
    factor_list_10,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    pd,
):
    # -----------------------------------
    # load data
    df_weight_14 = factset_utils.load_index_constituents(
        factset_index_db_path=factset_index_db_path, UNIVERSE_CODE=UNIVERSE_CODE
    ).assign(date=lambda x: pd.to_datetime(x["date"]))
    # 構成銘柄情報
    factset_utils.process_rank_calculation_store_to_db(
        df_weight=df_weight_14,
        factor_list=factor_list_10,
        financials_db_path=financials_db_path,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### ✅ データベース内容確認
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    db_utils,
    display,
    factset_index_db_path,
    financials_db_path,
    pd,
    sqlite3,
):
    table_names_3 = sorted(db_utils.get_table_names(db_path=financials_db_path))
    print(f"全{len(table_names_3)}テーブル")
    display(table_names_3)
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_22 = pd.read_sql(
            f"SELECT * FROM {UNIVERSE_CODE} LIMIT 5", parse_dates=["date"], con=_conn
        )
        display(df_22)
        display(df_22.columns)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. 欠損確認
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### ✅ データベース確認
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    db_utils,
    display,
    factset_index_db_path,
    financials_db_path,
    pd,
    sqlite3,
):
    table_names_4 = sorted(db_utils.get_table_names(db_path=financials_db_path))
    print(f"全{len(table_names_4)}テーブル")
    display(table_names_4)
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_weight_15 = pd.read_sql(
            f"SELECT * FROM {UNIVERSE_CODE}", parse_dates=["date"], con=_conn
        )
        display(df_weight_15.columns)
        display(df_weight_15.tail(5))
    return df_weight_15, table_names_4


@app.cell
def _(np, pd, sqlite3):
    # 各変数を処理する関数
    def process_variable(variable, financials_db_path, df_weight):
        with sqlite3.connect(financials_db_path) as _conn:
            _df_factor = pd.read_sql(
                f"SELECT `date`, `P_SYMBOL`, `value` FROM `{_variable}`",
                con=_conn,
                parse_dates=["date"],
            )
        merged_df = (
            pd.merge(df_weight, _df_factor, on=["date", "P_SYMBOL"], how="outer")
            .rename(columns={"value": _variable})
            .dropna(subset=["Weight (%)", _variable], how="any", axis=0)
            .fillna(np.nan)
        )
        _g = (
            pd.DataFrame(merged_df.groupby(["date"])["Weight (%)"].agg("sum"))
            .reset_index()
            .assign(variable=_variable)
        )
        return _g

    return (process_variable,)


@app.cell
def _(
    ThreadPoolExecutor,
    as_completed,
    df_weight_15,
    financials_db_path,
    process_variable,
    table_names_4,
):
    dfs_weight_sum = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_var = {
            executor.submit(
                process_variable, var, financials_db_path, df_weight_15
            ): var
            for var in table_names_4
        }
        for future in as_completed(future_to_var):
            _variable = future_to_var[future]
            try:
                result = future.result()
                if result is not None:
                    dfs_weight_sum.append(result)
                    print(f"✓ Completed: {_variable}")
            except Exception as e:
                print(f"✗ Failed {_variable}: {e}")
    return (dfs_weight_sum,)


@app.cell
def _(BLOOMBERG_DATA_DIR, UNIVERSE_CODE, dfs_weight_sum, display, pd):
    _df_weight_sum = pd.concat(dfs_weight_sum).sort_values(
        ["date", "Weight (%)"], ignore_index=True
    )
    _df_weight_sum = (
        pd.pivot(
            _df_weight_sum, index=["date"], columns="variable", values="Weight (%)"
        )
        .reset_index()
        .filter(regex="date|_Rank|_PctRank|_ZScore")
    )
    display(_df_weight_sum)
    output_path = BLOOMBERG_DATA_DIR / f"{UNIVERSE_CODE}_not_missing_weight.xlsx"
    _df_weight_sum.to_excel(output_path, index=False)


@app.cell
def _(
    df_weight_15,
    display,
    financials_db_path,
    np,
    pd,
    sqlite3,
    table_names_4,
):
    dfs_weight_sum_1 = []
    with sqlite3.connect(financials_db_path) as _conn:
        for _variable in table_names_4:
            _df_factor = pd.read_sql(
                f"SELECT `date`, `P_SYMBOL`, `value` FROM `{_variable}`",
                con=_conn,
                parse_dates=["date"],
            )
            merged_df = (
                pd.merge(df_weight_15, _df_factor, on=["date", "P_SYMBOL"], how="outer")
                .rename(columns={"value": _variable})
                .dropna(subset=["Weight (%)", _variable], how="any", axis=0)
                .fillna(np.nan)
            )
            _g = (
                pd.DataFrame(merged_df.groupby(["date"])["Weight (%)"].agg("sum"))
                .reset_index()
                .assign(variable=_variable)
            )
            dfs_weight_sum_1.append(_g)
    _df_weight_sum = pd.concat(dfs_weight_sum_1, ignore_index=True)
    _df_weight_sum = pd.pivot(
        _df_weight_sum, index=["date"], columns="variable", values="Weight (%)"
    ).reset_index()
    display(_df_weight_sum)


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
