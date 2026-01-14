import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # `ROIC-Preprocessing_ver1.ipynb`

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
            _query = f"\n            SELECT\n                *\n            FROM\n                {_table}\n            WHERE\n                date >= '{_start_date.strftime('%Y-%m-%d')}' AND date <= '{_end_date.strftime('%Y-%m-%d')}'\n        "
            _df_existing = (
                pd.read_sql(_query, con=_conn, parse_dates=["date"])
                .rename(columns={"value": "value_existing"})
                .reindex(columns=["date", "P_SYMBOL", "variable", "value_existing"])
            )
            _df_update_slice = (
                _df_update.loc[_df_update["variable"] == _table]
                .copy()
                .rename(columns={"value": "value_new"})
                .reindex(columns=["date", "P_SYMBOL", "variable", "value_new"])
            )
            _df_merged = pd.merge(
                _df_update_slice,
                _df_existing,
                on=["date", "P_SYMBOL", "variable"],
                how="outer",
            )
            _df_merged["value"] = _df_merged.apply(update_value, axis=1)
            _changed_mask = _df_merged["value_existing"].isna() & ~_df_merged[
                "value_new"
            ].isna() | ~_df_merged["value_existing"].isna() & ~_df_merged[
                "value_new"
            ].isna() & ~np.isclose(
                _df_merged["value_existing"],
                _df_merged["value_new"],
                rtol=1e-05,
                atol=0.001,
            )
            _df_to_update = _df_merged[_changed_mask].reset_index(drop=True)[
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
            _query = f"\n            SELECT\n                *\n            FROM\n                {_table}\n            WHERE\n                date >= '{_start_date.strftime('%Y-%m-%d')}' AND date <= '{_end_date.strftime('%Y-%m-%d')}'\n        "
            _df_existing = (
                pd.read_sql(_query, con=_conn, parse_dates=["date"])
                .rename(columns={"value": "value_existing"})
                .reindex(columns=["date", "P_SYMBOL", "variable", "value_existing"])
            )
            _df_update_slice = (
                _df_update.loc[_df_update["variable"] == _table]
                .copy()
                .rename(columns={"value": "value_new"})
                .reindex(columns=["date", "P_SYMBOL", "variable", "value_new"])
            )
            _df_merged = pd.merge(
                _df_update_slice,
                _df_existing,
                on=["date", "P_SYMBOL", "variable"],
                how="outer",
            )
            _df_merged["value"] = _df_merged.apply(update_value, axis=1)
            _changed_mask = _df_merged["value_existing"].isna() & ~_df_merged[
                "value_new"
            ].isna() | ~_df_merged["value_existing"].isna() & ~_df_merged[
                "value_new"
            ].isna() & ~np.isclose(
                _df_merged["value_existing"],
                _df_merged["value_new"],
                rtol=1e-05,
                atol=0.001,
            )
            _df_to_update = _df_merged[_changed_mask].reset_index(drop=True)[
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
    df_price = roic_utils.load_FG_PRICE(db_path=financials_db_path)
    df_return = roic_utils.calculate_Return(
        df_price=df_price,
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
    print(f"\n{'=' * 60}")
    print(f"処理完了: {rows_updated:,}行を処理しました")
    print(f"{'=' * 60}")
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
    display(df_index_return.head(3))
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
        display(df_index_return.head(5))
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
    _return_cols = [
        "Return_12M",
        "Return_12M_annlzd",
        "Forward_Return_12M",
        "Forward_Return_12M_annlzd",
    ]
    union_queries_index = []  # "Return_1M",
    for _table in _return_cols:  # "Return_1M_annlzd",
        union_queries_index.append(
            f"SELECT Date, Ticker, value, variable FROM '{_table}' WHERE Ticker = '{BLOOMBERG_UNIVERSE_TICKER}'"
        )  # "Forward_Return_1M",
    union_query_index = " UNION ALL ".join(
        union_queries_index
    )  # "Forward_Return_1M_annlzd",
    with sqlite3.connect(bloomberg_index_db_path) as _conn:  # "Return_3M",
        df_return_index = pd.read_sql(
            union_query_index, con=_conn, parse_dates=["Date"]
        ).rename(columns={"Date": "date", "Ticker": "symbol"})  # "Return_3M_annlzd",
    df_return_index = df_return_index.drop_duplicates(
        ignore_index=True
    )  # "Forward_Return_3M",
    print(
        f"✅ インデックスデータ: {len(df_return_index):,}件"
    )  # "Forward_Return_3M_annlzd",
    union_queries_security = []  # "Return_6M",
    for _table in _return_cols:  # "Return_6M_annlzd",
        union_queries_security.append(
            f"SELECT date, P_SYMBOL, value, variable FROM '{_table}'"
        )  # "Forward_Return_6M",
    union_query_security = " UNION ALL ".join(
        union_queries_security
    )  # "Forward_Return_6M_annlzd",
    with sqlite3.connect(financials_db_path) as _conn:
        df_return_security = pd.read_sql(
            union_query_security, con=_conn, parse_dates=["date"]
        ).rename(columns={"P_SYMBOL": "symbol"})
    df_return_security = df_return_security.drop_duplicates(ignore_index=True)
    print(f"✅ 個別銘柄データ: {len(df_return_security):,}件")
    df_returns = pd.concat(
        [df_return_index, df_return_security], ignore_index=True
    )  # "Return_3Y",
    display(df_returns.tail(3))  # "Return_3Y_annlzd",
    df_active_returns = performance_metrics_utils.calculate_active_returns_parallel(
        df_returns=df_returns,
        return_cols=_return_cols,
        benchmark_ticker=BLOOMBERG_UNIVERSE_TICKER,
        max_workers=10,
        verbose=False,
    )  # "Forward_Return_3Y",
    display(df_active_returns.tail(3))  # "Forward_Return_3Y_annlzd",
    # ------------------------------------
    # インデックスのリターン
    # データ取得
    # 個別銘柄のリターン
    # concatenate returns
    # アクティブリターン計算
    # Active return: データベース保存
    # 推奨方法：直列書き込み版
    results = factset_utils.store_active_returns_batch_serial_write(
        df_active_returns=df_active_returns,
        return_cols=_return_cols,
        db_path=financials_db_path,
        benchmark_ticker=BLOOMBERG_UNIVERSE_TICKER,
        batch_size=1000000,
        verbose=True,
    )  # "Return_5Y",  # "Return_5Y_annlzd",  # "Forward_Return_5Y",  # "Forward_Return_5Y_annlzd",


@app.cell
def _(db_utils, display, financials_db_path):
    table_names_2 = sorted(db_utils.get_table_names(db_path=financials_db_path))
    display(table_names_2)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### PE 取得テスト from Bloomberg

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
    ## 4. Factor 計算
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-1. Growth Factor（Factset）

    まず、QoQ, YoY, 3Yr CAGR, 5Yr CAGR の値を計算し、データベースに保存する。
    """)


@app.cell
def _(factset_utils, financials_db_path, pd, roic_utils, sqlite3, tqdm):
    _data_list = [
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
    ]
    with sqlite3.connect(financials_db_path) as _conn:
        for _data in tqdm(_data_list):
            df_8 = pd.read_sql(
                f"SELECT * FROM `{_data}`", con=_conn, parse_dates=["date"]
            ).sort_values("date", ignore_index=True)
            for _growth in ["QoQ", "YoY", "CAGR_3Y", "CAGR_5Y"]:
                _df_growth = df_8.copy()
                _new_variable = f"{_data}_{_growth}"
                _df_growth = roic_utils.calculate_growth(
                    df=_df_growth, data_name=_data, growth_type=_growth
                )
                factset_utils.store_to_database(
                    df=_df_growth,
                    db_path=financials_db_path,
                    table_name=_new_variable,
                    verbose=False,
                )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    次に、ファクターのランクを計算し、データベースに保存する。
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    db_utils,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    itertools,
    pd,
    roic_utils,
    sqlite3,
    tqdm,
):
    _query = f"\n    SELECT\n        `date`, `P_SYMBOL`, `FG_COMPANY_NAME`, `Asset ID`, `GICS Sector`, `Weight (%)`\n    FROM\n        {UNIVERSE_CODE}\n"
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_weight = pd.read_sql(_query, parse_dates=["date"], con=_conn)
    _factor_list = [
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
    ]
    _period_list = ["QoQ", "YoY", "CAGR_3Y", "CAGR_5Y"]
    _total_iterations = len(_factor_list) * len(_period_list)
    print(f"処理総数: {_total_iterations} 回")
    with sqlite3.connect(financials_db_path) as _conn:
        for _factor, _periods in tqdm(
            itertools.product(_factor_list, _period_list),
            total=_total_iterations,
            desc="ファクター処理進捗",
        ):
            _factor_growth = f"{_factor}_{_periods}"
            df_9 = (
                pd.read_sql(
                    f"SELECT `date`, `P_SYMBOL`, `value` FROM `{_factor_growth}`",
                    con=_conn,
                    parse_dates=["date"],
                )
                .assign(
                    date=lambda row: pd.to_datetime(row["date"])
                    + pd.tseries.offsets.MonthEnd(0)
                )
                .sort_values("date", ignore_index=True)
                .rename(columns={"value": _factor_growth})
            )
            df_9 = (
                pd.merge(df_weight, df_9, on=["date", "P_SYMBOL"], how="outer")
                .drop_duplicates(subset=["date", "P_SYMBOL"])
                .dropna(
                    subset=["Weight (%)", _factor_growth],
                    how="any",
                    axis=0,
                    ignore_index=True,
                )
            )
            _df_rank = roic_utils.add_factor_rank_cols(
                df=df_9, factor_name=_factor_growth
            )
            _df_rank = (
                _df_rank[["date", "P_SYMBOL", f"{_factor_growth}_Rank"]]
                .rename(columns={f"{_factor_growth}_Rank": "value"})
                .assign(variable=f"{_factor_growth}_Rank")
            )
            _df_pct_rank = roic_utils.add_factor_pct_rank_cols(
                df=df_9, factor_name=_factor_growth
            )
            _df_pct_rank = (
                _df_pct_rank[["date", "P_SYMBOL", f"{_factor_growth}_PctRank"]]
                .rename(columns={f"{_factor_growth}_PctRank": "value"})
                .assign(variable=f"{_factor_growth}_PctRank")
            )
            _df_zscore = roic_utils.add_factor_zscore_cols(
                df=df_9, factor_name=_factor_growth
            )
            _df_zscore = (
                _df_zscore[["date", "P_SYMBOL", f"{_factor_growth}_ZScore"]]
                .rename(columns={f"{_factor_growth}_ZScore": "value"})
                .assign(variable=f"{_factor_growth}_ZScore")
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=f"{_factor_growth}_Rank"
            )
            factset_utils.store_to_database(
                df=_df_rank,
                db_path=financials_db_path,
                table_name=f"{_factor_growth}_Rank",
                verbose=False,
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=f"{_factor_growth}_PctRank"
            )
            factset_utils.store_to_database(
                df=_df_pct_rank,
                db_path=financials_db_path,
                table_name=f"{_factor_growth}_PctRank",
                verbose=False,
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=f"{_factor_growth}_ZScore"
            )
            factset_utils.store_to_database(
                df=_df_zscore,
                db_path=financials_db_path,
                table_name=f"{_factor_growth}_ZScore",
                verbose=False,
            )


@app.cell
def _(db_utils, display, financials_db_path, pd, sqlite3):
    table_names_3 = db_utils.get_table_names(financials_db_path)
    display([s for s in table_names_3 if "QoQ" in s or "YoY" in s or "CAGR" in s])
    with sqlite3.connect(financials_db_path) as _conn:
        df_10 = pd.read_sql(
            "SELECT * FROM FF_SALES_QoQ_PctRank ORDER BY 'date'",
            con=_conn,
            parse_dates=["date"],
        )
        display(df_10)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-2. Valuation（Bloomberg） -> データ不足のためスキップ

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
    _data_list = ["BEST_PE_RATIO", "BEST_EPS", "PE_RATIO", "TRAIL_12M_EPS_BEF_XO_ITEM"]
    blp_2 = bloomberg_utils.BlpapiCustom()
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        for _data in tqdm(_data_list):
            df_11 = (
                pd.read_sql(f"SELECT * FROM `{_data}`", con=_conn, parse_dates=["Date"])
                .sort_values("Date", ignore_index=True)
                .rename(columns={"Date": "date", "SEDOL": "P_SYMBOL"})
            )
            for _growth in ["QoQ", "YoY", "CAGR_3Y", "CAGR_5Y"]:
                _df_growth = df_11.copy()
                _new_variable = f"{_data}_{_growth}"
                _df_growth = roic_utils.calculate_growth(
                    df=_df_growth, data_name=_data, growth_type=_growth
                ).rename(columns={"date": "Date", "P_SYMBOL": "SEDOL"})
                db_utils.delete_table_from_database(
                    db_path=bloomberg_valuation_db_path, table_name=_new_variable
                )
                blp_2.store_to_database(
                    df=_df_growth,
                    db_path=bloomberg_valuation_db_path,
                    table_name=_new_variable,
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
    _query = f"\n    SELECT\n        `date`, `P_SYMBOL`, `SEDOL`, `FG_COMPANY_NAME`, `Asset ID`, `GICS Sector`, `Weight (%)`\n    FROM\n        {UNIVERSE_CODE}\n"
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_weight_1 = pd.read_sql(_query, parse_dates=["date"], con=_conn)
    _factor_list = ["BEST_EPS", "BEST_PE_RATIO"]
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        for _factor in tqdm(_factor_list):
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
                pd.merge(df_weight_1, df_13, on=["date", "SEDOL"], how="outer")
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
    _query = f"\n    SELECT\n        `date`, `P_SYMBOL`, `SEDOL`, `FG_COMPANY_NAME`, `Asset ID`, `GICS Sector`, `Weight (%)`\n    FROM\n        {UNIVERSE_CODE}\n"
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_weight_2 = pd.read_sql(_query, parse_dates=["date"], con=_conn)
    _factor_list = ["BEST_EPS", "BEST_PE_RATIO"]
    _period_list = ["QoQ", "YoY", "CAGR_3Y", "CAGR_5Y"]
    _total_iterations = len(_factor_list) * len(_period_list)
    print(f"処理総数: {_total_iterations} 回")
    with sqlite3.connect(bloomberg_valuation_db_path) as _conn:
        for _factor, _periods in tqdm(
            itertools.product(_factor_list, _period_list),
            total=_total_iterations,
            desc="ファクター処理進捗",
        ):
            _factor_growth = f"{_factor}_{_periods}"
            df_14 = (
                pd.read_sql(
                    f"SELECT `Date`, `SEDOL`, `value` FROM `{_factor_growth}`",
                    con=_conn,
                    parse_dates=["Date"],
                )
                .rename(columns={"Date": "date"})
                .assign(
                    date=lambda row: pd.to_datetime(row["date"])
                    + pd.tseries.offsets.MonthEnd(0)
                )
                .sort_values("date", ignore_index=True)
                .rename(columns={"value": _factor_growth})
            )
            df_14 = (
                pd.merge(df_weight_2, df_14, on=["date", "SEDOL"], how="outer")
                .drop_duplicates(subset=["date", "SEDOL"])
                .dropna(
                    subset=["Weight (%)", _factor_growth],
                    how="any",
                    axis=0,
                    ignore_index=True,
                )
            )
            display(df_14)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-3. ROIC Label Factor（Factset）

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
    sqlite3,
):
    with sqlite3.connect(financials_db_path) as _conn:
        df_roic = (
            pd.read_sql(sql="SELECT * FROM FF_ROIC", con=_conn)
            .assign(date=lambda row: pd.to_datetime(row["date"]))
            .drop(columns=["variable"])
            .rename(columns={"P_SYMBOL": "Symbol", "value": "FF_ROIC"})
        )
        df_roe = (
            pd.read_sql("SELECT * FROM FF_ROE", con=_conn)
            .assign(date=lambda row: pd.to_datetime(row["date"]))
            .drop(columns=["variable"])
            .rename(columns={"P_SYMBOL": "Symbol", "value": "FF_ROE"})
        )
        df_roic = pd.merge(df_roic, df_roe, on=["date", "Symbol"], how="left").assign(
            date=lambda row: pd.to_datetime(row["date"])
            + pd.tseries.offsets.MonthEnd(0)
        )
        del df_roe
    with sqlite3.connect(factset_index_db_path) as _conn:
        _query = f"\n        SELECT\n            `date`, `P_SYMBOL`, `FG_COMPANY_NAME`, `GICS Sector`, `GICS Industry`, `Weight (%)`, `Mkt Value`\n        FROM\n            {UNIVERSE_CODE}\n    "
        security_info = (
            pd.read_sql(_query, con=_conn)
            .rename(columns={"P_SYMBOL": "Symbol"})
            .assign(date=lambda row: pd.to_datetime(row["date"]))
        )
    df_roic_merged = (
        pd.merge(df_roic, security_info, on=["date", "Symbol"], how="left")
        .assign(
            ROIC=lambda x: np.where(
                x["GICS Sector"] == "Financials", x["FF_ROE"], x["FF_ROIC"]
            )
        )
        .dropna(subset=["Weight (%)", "ROIC"], how="any")
        .drop(columns=["FF_ROIC", "FF_ROE"])
    )
    df_roic_merged = roic_utils.add_factor_rank_cols(df_roic_merged, factor_name="ROIC")
    df_roic_merged = roic_utils.add_shifted_factor_cols_month(
        df_roic_merged,
        factor_name="ROIC_Rank",
        shift_month=list(range(1, 61)),
        shift_direction="Past",
    )
    year_period = 5
    df_roic_merged[f"ROIC_label_Past{year_period}Y"] = df_roic_merged.apply(
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
    df_15 = (
        df_15[["date", "Symbol", "ROIC_label_Past5Y"]]
        .rename(columns={"ROIC_label_Past5Y": "value", "Symbol": "P_SYMBOL"})
        .dropna(subset=["value"], ignore_index=True)
        .assign(
            variable="ROIC_label_Past5Y", date=lambda row: pd.to_datetime(row["date"])
        )
    )
    display(df_15)
    factset_utils.store_to_database(
        df=df_15, db_path=financials_db_path, table_name="ROIC_label_Past5Y"
    )
    return (df_roic_merged,)


@app.cell
def _(df_roic_merged, display, pd):
    df_16 = df_roic_merged.copy()
    roic_count = pd.pivot(
        pd.DataFrame(
            df_16.groupby(["date", "GICS Sector", "ROIC_label_Past5Y"])[
                "Symbol"
            ].count()
        ).reset_index(),
        index=["date", "GICS Sector"],
        columns="ROIC_label_Past5Y",
    ).reset_index()
    # --- label count ---
    display(roic_count.loc[roic_count["GICS Sector"] == "Information Technology"])
    roic_count = pd.pivot(
        pd.DataFrame(
            df_16.groupby(["date", "GICS Sector", "ROIC_Rank"])["Symbol"].count()
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
        df_16.groupby(["date", "ROIC_label_Past5Y"])["Weight (%)"]
        .agg(["count", "sum"])
        .rename(columns={"count": "Num of Securities", "sum": "Total Weight (%)"})
        .sort_index()
    )
    # --- weight check ---
    display(roic_label_count)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4-4. その他の財務項目

    時点でのランク、パーセントランク、ZScore のみ計算
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    db_utils,
    factset_index_db_path,
    factset_utils,
    financials_db_path,
    pd,
    roic_utils,
    sqlite3,
    tqdm,
):
    _query = f"\n    SELECT\n        `date`, `P_SYMBOL`, `FG_COMPANY_NAME`, `Asset ID`, `GICS Sector`, `Weight (%)`\n    FROM\n        {UNIVERSE_CODE}\n"
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_weight_3 = pd.read_sql(_query, parse_dates=["date"], con=_conn)
    _factor_list = [
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
    with sqlite3.connect(financials_db_path) as _conn:
        for _factor in tqdm(_factor_list):
            df_17 = (
                pd.read_sql(
                    f"SELECT `date`, `P_SYMBOL`, `value` FROM `{_factor}`",
                    con=_conn,
                    parse_dates=["date"],
                )
                .assign(
                    date=lambda row: pd.to_datetime(row["date"])
                    + pd.tseries.offsets.MonthEnd(0)
                )
                .sort_values("date", ignore_index=True)
                .rename(columns={"value": _factor})
            )
            df_17 = (
                pd.merge(df_weight_3, df_17, on=["date", "P_SYMBOL"], how="outer")
                .drop_duplicates(subset=["date", "P_SYMBOL"])
                .dropna(
                    subset=["Weight (%)", _factor], how="any", axis=0, ignore_index=True
                )
            )
            _df_rank = roic_utils.add_factor_rank_cols(df=df_17, factor_name=_factor)
            _df_rank = (
                _df_rank[["date", "P_SYMBOL", f"{_factor}_Rank"]]
                .rename(columns={f"{_factor}_Rank": "value"})
                .assign(variable=f"{_factor}_Rank")
            )
            _df_pct_rank = roic_utils.add_factor_pct_rank_cols(
                df=df_17, factor_name=_factor
            )
            _df_pct_rank = (
                _df_pct_rank[["date", "P_SYMBOL", f"{_factor}_PctRank"]]
                .rename(columns={f"{_factor}_PctRank": "value"})
                .assign(variable=f"{_factor}_PctRank")
            )
            _df_zscore = roic_utils.add_factor_zscore_cols(
                df=df_17, factor_name=_factor
            )
            _df_zscore = (
                _df_zscore[["date", "P_SYMBOL", f"{_factor}_ZScore"]]
                .rename(columns={f"{_factor}_ZScore": "value"})
                .assign(variable=f"{_factor}_ZScore")
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=f"{_factor}_Rank"
            )
            factset_utils.store_to_database(
                df=_df_rank,
                db_path=financials_db_path,
                table_name=f"{_factor}_Rank",
                verbose=False,
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=f"{_factor}_PctRank"
            )
            factset_utils.store_to_database(
                df=_df_pct_rank,
                db_path=financials_db_path,
                table_name=f"{_factor}_PctRank",
                verbose=False,
            )
            db_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=f"{_factor}_ZScore"
            )
            factset_utils.store_to_database(
                df=_df_zscore,
                db_path=financials_db_path,
                table_name=f"{_factor}_ZScore",
                verbose=False,
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
    table_names_4 = sorted(db_utils.get_table_names(db_path=financials_db_path))
    print(f"全{len(table_names_4)}テーブル")
    display(table_names_4)
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_18 = pd.read_sql(
            f"SELECT * FROM {UNIVERSE_CODE} LIMIT 5", parse_dates=["date"], con=_conn
        )
        display(df_18)
        display(df_18.columns)


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
    table_names_5 = sorted(db_utils.get_table_names(db_path=financials_db_path))
    print(f"全{len(table_names_5)}テーブル")
    display(table_names_5)
    with sqlite3.connect(factset_index_db_path) as _conn:
        df_weight_4 = pd.read_sql(
            f"SELECT * FROM {UNIVERSE_CODE}", parse_dates=["date"], con=_conn
        )
        display(df_weight_4.columns)
        display(df_weight_4.tail(5))
    return df_weight_4, table_names_5


@app.cell
def _(np, pd, sqlite3):
    # 各変数を処理する関数
    def process_variable(variable, financials_db_path, df_weight):
        with sqlite3.connect(financials_db_path) as _conn:
            df_factor = pd.read_sql(
                f"SELECT `date`, `P_SYMBOL`, `value` FROM `{_variable}`",
                con=_conn,
                parse_dates=["date"],
            )
        merged_df = (
            pd.merge(df_weight, df_factor, on=["date", "P_SYMBOL"], how="outer")
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
    df_weight_4,
    financials_db_path,
    process_variable,
    table_names_5,
):
    dfs_weight_sum = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_var = {
            executor.submit(process_variable, var, financials_db_path, df_weight_4): var
            for var in table_names_5
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
    df_weight_4,
    display,
    financials_db_path,
    np,
    pd,
    sqlite3,
    table_names_5,
):
    dfs_weight_sum_1 = []
    with sqlite3.connect(financials_db_path) as _conn:
        for _variable in table_names_5:
            df_factor = pd.read_sql(
                f"SELECT `date`, `P_SYMBOL`, `value` FROM `{_variable}`",
                con=_conn,
                parse_dates=["date"],
            )
            merged_df = (
                pd.merge(df_weight_4, df_factor, on=["date", "P_SYMBOL"], how="outer")
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Growth factor
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### performance
    """)


@app.cell
def _(
    UNIVERSE_CODE,
    db_utils,
    display,
    factset_index_db_path,
    financials_db_path,
    np,
    pd,
    roic_utils,
    sqlite3,
):
    _conn = sqlite3.connect(factset_index_db_path)
    _query = f"\n    SELECT\n        `date`, `Universe`, `Universe_code_BPM`, `P_SYMBOL`, `Name`, `FG_COMPANY_NAME`, `Asset ID`, `Asset ID Type`, `Country`,\n        `GICS Sector`, `GICS Industry`, `GICS Industry Group`, `GICS Sub-Industry`, `Holdings`, `Weight (%)`, `Mkt Value`\n    FROM\n        {UNIVERSE_CODE}\n"
    df_weight_5 = pd.read_sql(_query, con=_conn)
    _conn = sqlite3.connect(financials_db_path)
    union_queries = (
        ["SELECT * FROM ROIC_label_Past5Y"]
        + ["SELECT * FROM FF_SALES_QoQ_Rank"]
        + ["SELECT * FROM FF_SALES_YoY_Rank"]
        + ["SELECT * FROM FF_SALES_CAGR_3Y_Rank"]
        + ["SELECT * FROM FF_EBITDA_OPER_QoQ_Rank"]
        + ["SELECT * FROM FF_EBITDA_OPER_YoY_Rank"]
        + ["SELECT * FROM FF_EBITDA_OPER_CAGR_3Y_Rank"]
        + [
            f"SELECT * FROM '{_table}'"
            for _table in db_utils.get_table_names(db_path=financials_db_path)
            if "annlzd" in _table
        ]
    )
    _query = " UNION ALL ".join(union_queries)
    _data = pd.pivot(
        pd.read_sql(_query, con=_conn),
        index=["date", "P_SYMBOL"],
        columns="variable",
        values="value",
    ).reset_index()
    df_19 = (
        pd.merge(df_weight_5, _data, on=["date", "P_SYMBOL"], how="outer")
        .dropna(subset=["Weight (%)"])
        .fillna(np.nan)
    )
    display(df_19)
    _df_slice = df_19.loc[df_19["date"] >= "2015-01-01"]
    _return_cols = [
        "Return_1M_annlzd",
        "Return_3M_annlzd",
        "Return_6M_annlzd",
        "Return_12M_annlzd",
        "Return_3Y_annlzd",
        "Return_5Y_annlzd",
        "Forward_Return_1M_annlzd",
        "Forward_Return_3M_annlzd",
        "Forward_Return_6M_annlzd",
        "Forward_Return_12M_annlzd",
        "Forward_Return_3Y_annlzd",
        "Forward_Return_5Y_annlzd",
    ]
    pd.options.display.precision = 2
    for _factor in [
        "ROIC_label_Past5Y",
        "FF_SALES_QoQ_Rank",
        "FF_SALES_YoY_Rank",
        "FF_SALES_CAGR_3Y_Rank",
        "FF_EBITDA_OPER_QoQ_Rank",
        "FF_EBITDA_OPER_YoY_Rank",
        "FF_EBITDA_OPER_CAGR_3Y_Rank",
    ]:
        print(_factor)
        g_mean = _df_slice.groupby([_factor])[_return_cols].apply(
            roic_utils.clipped_mean, 1.0
        )
        g_std = _df_slice.groupby([_factor])[_return_cols].apply(
            roic_utils.clipped_std, 1.0
        )
        g_eff = g_mean.div(g_std)
        display(g_eff)
    return (df_19,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Check constituents
    """)


@app.cell
def _(df_19, display):
    _g = df_19.groupby(["date"])["Weight (%)"].agg(["count", "sum"])
    display(_g.tail(10))
    display(
        df_19.loc[
            df_19["FG_COMPANY_NAME"].str.contains("NVIDIA")
            & (df_19["GICS Sector"] == "Information Technology")
        ]
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Performance
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### ROIC label Performance
    """)


@app.cell
def _(df_19, display, pd, roic_utils):
    avg_return = (
        pd.DataFrame(
            df_19.groupby(["date", "ROIC_label_Past5Y"]).apply(
                lambda row: roic_utils.clipped_mean(row["Return_Ann_5Y"], percentile=5)
            )
        )
        .reset_index()
        .rename(columns={0: "avg"})
    )
    std = pd.DataFrame(
        df_19.groupby(["date", "ROIC_label_Past5Y"])
        .apply(lambda row: roic_utils.clipped_std(row["Return_Ann_5Y"], percentile=5))
        .reset_index()
        .rename(columns={0: "std"})
    )
    df_performance = pd.merge(
        avg_return, std, on=["date", "ROIC_label_Past5Y"], how="left"
    ).assign(efficiency=lambda row: row["avg"].div(row["std"]))
    df_performance = pd.pivot(
        df_performance, index="date", columns="ROIC_label_Past5Y"
    ).sort_index()
    display(df_performance)


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
