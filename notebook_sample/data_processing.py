import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Data Processing
    """)


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo

    import os
    import sqlite3
    import sys
    import warnings
    from pathlib import Path

    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import polars as pl
    import seaborn as sns
    from data_check_utils import calculate_missing_stats
    from data_prepare import createDB_bpm_and_factset_code
    from database_utils import (
        get_table_names,
        step1_load_file_to_db,
        step2_create_variable_tables,
        step3_create_return_table,
    )
    from fredapi import Fred
    from tqdm import tqdm

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
        plot_loadings_and_explained_variance,
        plot_us_interest_rates_and_spread,
    )

    FRED_API = os.getenv("FRED_API_KEY")
    return (
        BM_DIR,
        DATA_DIR,
        FRED_API,
        FRED_DIR,
        Fred,
        Path,
        calculate_missing_stats,
        createDB_bpm_and_factset_code,
        get_table_names,
        mdates,
        np,
        pd,
        pl,
        plot_loadings_and_explained_variance,
        plot_us_interest_rates_and_spread,
        plt,
        sns,
        sqlite3,
        step1_load_file_to_db,
        step2_create_variable_tables,
        step3_create_return_table,
        store_fred_database,
        tqdm,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 0. Convert csv files into parquet files
    """)


@app.cell
def _(DATA_DIR, pd):
    _csv_files = sorted(list(DATA_DIR.glob("*.csv")))
    for f in _csv_files:
        df = pd.read_csv(f, encoding="utf-8")
        df.to_parquet(DATA_DIR / f"{f.stem}.parquet", index=False)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Create DB: MSCI_KOKUSAI_BPM_and_Factset_Code.db

    -   ファイルは全てあるか
    -   date, GICS sector ごとに銘柄数とウェイトをチェック
    -   BPM からインデックスデータを取得し Factset の企業名とコードを付与した生データファイルを SQLite3 データベースに保存する
    """)


@app.cell
def _(DATA_DIR, createDB_bpm_and_factset_code, display, pd):
    _parquet_files = sorted(list(DATA_DIR.glob("MSCI_KOKUSAI_Constituents*.parquet")))
    _dfs = [pd.read_parquet(f) for f in _parquet_files]
    df_1 = (
        pd.concat(_dfs)
        .assign(date=lambda row: pd.to_datetime(row["date"]))
        .sort_values("date", ignore_index=True)
    )
    g1 = (
        df_1.groupby(["date"])["Weight (%)"]
        .agg(["count", "sum"])
        .rename(columns={"count": "num of secs", "sum": "total weight (%)"})
    )
    display(g1)
    display(g1.describe())
    g2 = (
        df_1.groupby(["date", "GICS Sector"])["Weight (%)"]
        .agg(["count", "sum"])
        .rename(columns={"count": "num of secs", "sum": "total weight (%)"})
    )
    display(g2)
    _db_name = DATA_DIR / "MSCI_KOKUSAI_BPM_and_Factset_Code.db"
    createDB_bpm_and_factset_code(
        db_name=_db_name, raw_data_list=_parquet_files, file_type="parquet"
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Create financial database: MSCI_KOKUSAI_Factset_Financials.db

    全ての元データファイルの csv を読み込んで sqlite に格納する。5 年前から 5 年後までの monthly のシフトデータ用カラムも追加する。
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 案 1
    """)


@app.cell
def _(DATA_DIR, Path, pd, sqlite3, tqdm):
    def read_csv_with_date(file_path: Path):
        return pd.read_csv(file_path, encoding="utf-8", parse_dates=["date"])

    _csv_files = sorted(list(DATA_DIR.glob("Financials_all_data*.csv")))
    _dfs = [read_csv_with_date(f) for f in _csv_files]
    df_2 = pd.concat(_dfs, ignore_index=True).sort_values("date", ignore_index=True)
    df_copy = df_2.copy().assign(date=lambda row: pd.to_datetime(row["date"]))
    df_copy = (
        pd.pivot_table(
            df_copy, index=["date", "P_SYMBOL"], columns="variable", values="value"
        )
        .reset_index()
        .sort_values(["date", "P_SYMBOL"], ignore_index=True)
        .assign(date=lambda row: pd.to_datetime(row["date"].dt.strftime("%Y-%m-%d")))
    )
    shift_cols = [col for col in df_copy.columns if col not in ["P_SYMBOL", "date"]]
    concat_df = df_copy.copy()
    for shift_period in tqdm(range(1, 61)):
        shifted_values_past = (
            df_copy.groupby("P_SYMBOL")[shift_cols]
            .shift(periods=shift_period)
            .add_suffix(f"_{shift_period}M_ago")
        )
        shifted_values_future = (
            df_copy.groupby("P_SYMBOL")[shift_cols]
            .shift(periods=-shift_period)
            .add_suffix(f"_{shift_period}M_forward")
        )
        concat_df = pd.concat([concat_df, shifted_values_past], axis=1)
        concat_df = pd.concat([concat_df, shifted_values_future], axis=1)
    _db_name = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    try:
        _conn = sqlite3.connect(_db_name)
        unique_dates = df_2["date"].unique()
        for _date in unique_dates:
            df_quarterly = df_2[df_2["date"] == _date]
            table_name = f"{_date.strftime('%Y_%m_%d')}"
            df_quarterly["date"] = pd.to_datetime(df_quarterly["date"]).dt.strftime(
                "%Y-%m-%d"
            )
            df_quarterly.to_sql(table_name, _conn, if_exists="replace", index=False)
            print(
                f"日付: {_date.date()} のデータをテーブル '{table_name}' に書き込みました。"
            )
    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if _conn:
            _conn.close()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 案 2
    """)


@app.cell
def _(DATA_DIR, pd, sqlite3, tqdm):
    def _step1_load_csv_to_db(csv_files, db_path):
        """
        全てのCSVファイルを読み込み、一つのテーブルに生のデータを格納する。
        この処理はメモリを最も使用するが、実行は最初の一度だけ。
        """
        print("--- ステップ1: CSVデータをデータベースにロード開始 ---")
        dfs_generator = (pd.read_csv(f, encoding="utf-8") for f in _csv_files)
        df_raw = pd.concat(dfs_generator, ignore_index=True)
        del dfs_generator
        df_raw["date"] = pd.to_datetime(df_raw["date"]).dt.strftime("%Y-%m-%d")
        try:
            _conn = sqlite3.connect(_db_path)
            df_raw.to_sql("raw_data", _conn, if_exists="replace", index=False)
            print(
                f"全CSVデータをデータベース '{_db_path.name}' の 'raw_data' テーブルに保存しました。"
            )
        except Exception as e:
            print(f"ステップ1でエラーが発生しました: {e}")
        finally:
            if _conn:
                _conn.close()

    def step2_process_and_create_features(db_path):
        """
        銘柄ごとにデータを読み出し、シフト特徴量を「ロングフォーマット」で作成し、
        最終的な結果を新しいテーブルに格納する。
        """
        print("\n--- ステップ2: 銘柄ごとに特徴量を作成開始 (ロングフォーマット) ---")
        try:
            _conn = sqlite3.connect(_db_path)
            symbols = pd.read_sql_query(
                "SELECT DISTINCT P_SYMBOL FROM raw_data", _conn
            )["P_SYMBOL"].tolist()
            for _i, symbol in enumerate(tqdm(symbols, desc="Processing Symbols")):
                _query = f"SELECT * FROM raw_data WHERE P_SYMBOL = '{symbol}'"
                df_symbol = pd.read_sql_query(_query, _conn, parse_dates=["date"])
                df_pivot = pd.pivot_table(
                    df_symbol,
                    index=["date", "P_SYMBOL"],
                    columns="variable",
                    values="value",
                ).reset_index()
                shift_cols = [
                    col for col in df_pivot.columns if col not in ["P_SYMBOL", "date"]
                ]
                all_features_long = []
                base_features = df_pivot.melt(
                    id_vars=["date", "P_SYMBOL"],
                    value_vars=shift_cols,
                    var_name="feature_name",
                    value_name="value",
                )
                all_features_long.append(base_features)
                for shift_period in range(1, 61):
                    past_shift = df_pivot[shift_cols].shift(periods=shift_period)
                    past_shift_long = pd.concat(
                        [df_pivot[["date", "P_SYMBOL"]], past_shift], axis=1
                    ).melt(
                        id_vars=["date", "P_SYMBOL"],
                        value_vars=shift_cols,
                        var_name="feature_name",
                        value_name="value",
                    )
                    past_shift_long["feature_name"] = (
                        past_shift_long["feature_name"] + f"_{shift_period}M_ago"
                    )
                    all_features_long.append(past_shift_long)
                    future_shift = df_pivot[shift_cols].shift(periods=-shift_period)
                    future_shift_long = pd.concat(
                        [df_pivot[["date", "P_SYMBOL"]], future_shift], axis=1
                    ).melt(
                        id_vars=["date", "P_SYMBOL"],
                        value_vars=shift_cols,
                        var_name="feature_name",
                        value_name="value",
                    )
                    future_shift_long["feature_name"] = (
                        future_shift_long["feature_name"] + f"_{shift_period}M_forward"
                    )
                    all_features_long.append(future_shift_long)
                final_symbol_df_long = pd.concat(all_features_long, ignore_index=True)
                final_symbol_df_long.dropna(subset=["value"], inplace=True)
                write_mode = "replace" if _i == 0 else "append"
                final_symbol_df_long.to_sql(
                    "final_data_long_format", _conn, if_exists=write_mode, index=False
                )
            print(
                "全銘柄の処理が完了し、'final_data_long_format' テーブルに保存されました。"
            )
        except Exception as e:
            print(f"ステップ2でエラーが発生しました: {e}")
        finally:
            if _conn:
                _conn.close()

    _csv_files = sorted(list(DATA_DIR.glob("Financials_all_data*.csv")))
    _db_name = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    _step1_load_csv_to_db(_csv_files, _db_name)
    step2_process_and_create_features(_db_name)
    return (step2_process_and_create_features,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 案 3: Polars
    """)


@app.cell
def _(DATA_DIR, pl, step2_process_and_create_features):
    # --- ステップ1：生のCSVデータをPolarsで直接DBに格納 ---
    def _step1_load_csv_to_db(csv_glob_path, db_uri):
        """
        Polarsを使い、全CSVを高速に読み込んでDBに格納する。
        """
        print("--- ステップ1: PolarsでCSVデータをロード開始 ---")
        try:
            df_raw = pl.read_csv(csv_glob_path)
            df_raw = df_raw.with_columns(
                pl.col("date").str.to_datetime().dt.strftime("%Y-%m-%d")
            )
            df_raw.write_database(
                "raw_data", db_uri, if_table_exists="replace"
            )  # 日付のフォーマットを統一
            print("全CSVデータを 'raw_data' テーブルに保存しました。")
        except Exception as e:
            print(f"ステップ1でエラーが発生しました: {e}")

    _csv_files = sorted(list(DATA_DIR.glob("Financials_all_data*.csv")))
    csv_glob_path = (
        str(DATA_DIR) + "/Financials_all_data*.csv"
    )  # 'raw_data'テーブルとして保存
    _db_name = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    db_connection_uri = f"sqlite:///{_db_name}"
    _step1_load_csv_to_db(_csv_files, db_connection_uri)
    # # --- ステップ2：Polarsの並列処理で全特徴量を一気に生成 ---
    # def step2_process_and_create_features(db_uri):
    #     """
    #     Polarsの能力を最大限に活用し、全シンボルの特徴量を一度に計算する。
    #     print("\n--- ステップ2: Polarsで全特徴量を一括生成開始 ---")
    #     try:
    #         # PolarsとconnectorxでDBから高速に読み込み
    #         df_raw = pl.read_database("SELECT * FROM raw_data", db_uri)
    #         # 1. ピボット処理
    #         df_pivot = df_raw.pivot(
    #             index=["date", "P_SYMBOL"], columns="variable", values="value"
    #         ).sort(["P_SYMBOL", "date"])
    #         shift_cols = [
    #             col for col in df_pivot.columns if col not in ["P_SYMBOL", "date"]
    #         ]
    #         # 2. シフト処理の「式(Expression)」をリストとして生成
    #         shift_expressions = []
    #         for col in shift_cols:
    #             for p in range(1, 61):
    #                 # 過去へのシフト式
    #                 shift_expressions.append(
    #                     pl.col(col).shift(p).over("P_SYMBOL").alias(f"{col}_{p}M_ago")
    #                 )
    #                 # 未来へのシフト式
    #                     pl.col(col).shift(-p).over("P_SYMBOL").alias(f"{col}_{p}M_forward")
    #         # 3. 全てのシフト式を一度に適用 (この処理が並列で実行される)
    #         df_wide = df_pivot.with_columns(shift_expressions)
    #         # 4. ワイドフォーマットからロングフォーマットへ変換
    #         final_df_long = df_wide.melt(
    #             id_vars=["date", "P_SYMBOL"],
    #             variable_name="feature_name",
    #             value_name="value",
    #         ).drop_nulls()  # drop_nulls()でNaNの行を効率的に削除
    #         # 5. 最終結果をDBに書き込み
    #         final_df_long.write_database(
    #             "final_data_polars", db_uri, if_table_exists="replace"
    #         )
    #         print(f"全銘柄の処理が完了し、'final_data_polars' テーブルに保存されました。")
    #     except Exception as e:
    #         print(f"ステップ2でエラーが発生しました: {e}")
    step2_process_and_create_features(db_connection_uri)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 案 4: Step1 は pandas 処理、Step2 も Pandas 処理
    """)


@app.cell
def _(
    DATA_DIR,
    display,
    step1_load_file_to_db,
    step2_create_variable_tables,
    step3_create_return_table,
):
    # --- ステップ1：生のデータを一度だけデータベースに格納する ---
    _parquet_files = sorted(list(DATA_DIR.glob("Financials_all_data*.parquet")))
    # csv_files = sorted(list(DATA_DIR.glob("Financials_all_data*.csv")))
    display(_parquet_files[:5])
    display(_parquet_files[-6:])
    print(len(_parquet_files))
    _db_path = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    step1_load_file_to_db(
        file_list=_parquet_files, file_type="parquet", db_name=_db_path
    )
    step2_create_variable_tables(db_name=_db_path)
    # --- ステップ2：クエリを使ってvariableごとにテーブルを作成 ---
    # --- ステップ3：リターンデータを格納するテーブルを作成 ---
    step3_create_return_table(db_path=_db_path)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### (ボツ?)
    """)


@app.cell
def _(DATA_DIR, display, get_table_names, pd, sqlite3, tqdm):
    _db_path = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    db_uri = f"sqlite:///{_db_path}"
    _variables = [
        s
        for s in get_table_names(db_uri=db_uri)
        if (s != "all_data") & ~s.endswith("_processed")
    ]
    all_variables = get_table_names(db_uri=db_uri)
    display(all_variables)
    _conn = sqlite3.connect(_db_path)
    for _variable in tqdm(_variables[:3]):
        _query = f"\n        SELECT\n            date,\n            P_SYMBOL,\n            value\n        FROM\n            '{_variable}'\n        WHERE\n            variable NOT LIKE '%Mago%'\n            AND variable NOT LIKE '%Mforward'\n        "
        df_3 = (
            pd.read_sql(sql=_query, con=_conn)
            .sort_values("date")
            .rename(columns={"value": _variable})
        )
        for _i in range(-60, 61):
            if _i == 0:
                continue
            col_name = (
                f"{_variable}_{abs(_i)}Mago"
                if _i > 0
                else f"{_variable}_{abs(_i)}Mforward"
            )
            df_3[col_name] = df_3.groupby("P_SYMBOL")[_variable].shift(_i)
        df_3 = pd.melt(
            df_3, id_vars=["date", "P_SYMBOL"], value_name="value", var_name="variable"
        )
        display(df_3)
        df_3.to_sql(
            name=f"{_variable}_processed",
            con=_conn,
            if_exists="replace",
            index=False,
            method="multi",
        )
    _conn.close()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Check Missing Values
    """)


@app.cell
def _(DATA_DIR, calculate_missing_stats, get_table_names, pd, sqlite3, tqdm):
    db_code = DATA_DIR / "MSCI_KOKUSAI_BPM_and_Factset_Code.db"
    db_uri_code = f"sqlite:///{db_code}"
    db_financials = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    db_uri_financials = f"sqlite:///{db_financials}"
    tables_code = get_table_names(db_uri=db_uri_code)
    tables_financials = get_table_names(db_uri=db_uri_financials)
    _conn = sqlite3.connect(db_code)
    cursor = _conn.cursor()
    cursor.execute("PRAGMA table_info(all_data);")
    all_columns = [row[1] for row in cursor.fetchall()]
    exclude_columns = [
        "Bloomberg Ticker",
        "BloombergID",
        "CODE_JP",
        "P_SYMBOL_SEDOL",
        "P_SYMBOL_CUSIP",
        "P_SYMBOL_ISIN",
        "FG_COMPANY_NAME_SEDOL",
        "FG_COMPANY_NAME_CUSIP",
        "FG_COMPANY_NAME_ISIN",
        "欠損状態",
    ]
    cols_to_select = [f'"{col}"' for col in all_columns if col not in exclude_columns]
    select_clause = ", ".join(cols_to_select)
    print(select_clause)
    _query = f"SELECT {select_clause} FROM 'all_data';"
    _df_code = pd.read_sql(sql=_query, con=_conn)
    _conn.close()
    del cursor
    _conn = sqlite3.connect(db_financials)
    missing_stats_dfs = []
    missing_stats_sector_dfs = []
    for _variable in tqdm([s for s in tables_financials if s != "all_data"]):
        _query = f"\n    SELECT\n        date,\n        P_SYMBOL,\n        value\n    FROM\n        '{_variable}'\n    "
        _df_financials = pd.read_sql(sql=_query, con=_conn).rename(
            columns={"value": _variable}
        )
        _df_financials = (
            _df_financials.sort_values("date", ignore_index=True)
            .assign(year=lambda row: pd.to_datetime(row["date"]).dt.year)
            .assign(month=lambda row: pd.to_datetime(row["date"]).dt.month)
        )  # 除外するカラム
        _df_financials = pd.merge(
            _df_financials,
            _df_code.drop(columns=["date"]),
            on=["year", "month", "P_SYMBOL"],
            how="outer",
        ).dropna(subset=["date", "Weight (%)"], how="any", ignore_index=True)
        missing_stats = calculate_missing_stats(
            group_cols=["date"], df=_df_financials, variable=_variable
        )
        missing_stats_dfs.append(missing_stats)
        missing_stats_sector = calculate_missing_stats(
            group_cols=["date", "GICS Sector"], df=_df_financials, variable=_variable
        )
        missing_stats_sector_dfs.append(missing_stats_sector)
    missing_stats = pd.concat(missing_stats_dfs, ignore_index=True)
    missing_stats_sector = pd.concat(missing_stats_sector_dfs, ignore_index=True)
    missing_stats_report = DATA_DIR / "Factset_Financials_Missing_data_report.xlsx"
    with pd.ExcelWriter(missing_stats_report) as writer:
        missing_stats.to_excel(writer, sheet_name="Index", index=False)
        missing_stats_sector.to_excel(writer, sheet_name="GICS Sector", index=False)
    missing_stats.to_csv(
        DATA_DIR / "Factset_Financials_Missing_data_report.csv", index=False
    )
    # export missing value report
    missing_stats_sector.to_csv(
        DATA_DIR / "Factset_Financials_Missing_data_sector_report.csv", index=False
    )  # インデックス構成銘柄に対して欠損している銘柄数とウェイトを計算したデータフレームを格納  # インデックス構成銘柄に対して欠損している銘柄数とウェイトをセクター別に計算したデータフレームを格納


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Create Benchmark databse: Factset_BM.db
    """)


@app.cell
def _(BM_DIR, display, pd, sqlite3):
    sheet_names = pd.ExcelFile(
        BM_DIR / "Benchmark_Price_and_Valuation.xlsx"
    ).sheet_names
    _dfs = []
    for sheet_name in sheet_names:
        df_4 = pd.read_excel(
            BM_DIR / "Benchmark_Price_and_Valuation.xlsx", sheet_name=sheet_name
        ).dropna(subset=["date"], ignore_index=True)
        df_melt = (
            pd.melt(df_4, id_vars="date", var_name="Benchmark", value_name="value")
            .assign(variable=sheet_name)
            .reindex(columns=["date", "Benchmark", "variable", "value"])
        )
        _dfs.append(df_melt)
    df_4 = pd.concat(_dfs, ignore_index=True)
    df_4["value"] = df_4["value"].astype(float)
    display(df_4)
    _db_path = BM_DIR / "Benchmark_Price_and_Valuation.db"
    _conn = sqlite3.connect(_db_path)
    for _benchmark in df_4["Benchmark"].unique():
        df_benchmark = df_4[df_4["Benchmark"] == _benchmark]
        df_benchmark.to_sql(name=_benchmark, con=_conn, index=False)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Data check(Plot price and valuation)
    """)


@app.cell
def _(BM_DIR, mdates, pd, plt, sns, sqlite3):
    _benchmark = "MSCI Kokusai Index (World ex Japan)"
    _db_path = BM_DIR / "Benchmark_Price_and_Valuation.db"
    _conn = sqlite3.connect(_db_path)
    df_5 = pd.pivot(
        pd.read_sql(sql=f"SELECT * FROM '{_benchmark}'", con=_conn),
        index="date",
        columns="variable",
        values="value",
    ).sort_index()
    df_5.index = pd.to_datetime(df_5.index)
    _variables = df_5.columns.tolist()
    _fig, _axes = plt.subplots(6, 1, figsize=(12, 8), tight_layout=True, sharex=True)
    _fig.suptitle(_benchmark)
    for _i, _variable in enumerate(
        [
            s
            for s in _variables
            if s not in ["FMA_EVAL_EBIT", "FMA_EVAL_EBITDA", "FMA_EVAL_SALES"]
        ]
    ):
        _ax = _axes[_i]
        _ax.set_ylabel(_variable)
        sns.lineplot(df_5, x=df_5.index, y=df_5[_variable], ax=_ax)
        _ax.grid(axis="y")
    for _variable in ["FMA_EVAL_EBIT", "FMA_EVAL_EBITDA", "FMA_EVAL_SALES"]:
        _ax = _axes[5]
        _ax.set_ylabel(_variable)
        sns.lineplot(df_5, x=df_5.index, y=df_5[_variable], ax=_ax, label=_variable)
        _ax.legend(loc="lower left")
        _ax.grid(axis="y")
    _axes[-1].xaxis.set_major_locator(mdates.YearLocator())
    _axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.savefig(BM_DIR / f"{_benchmark}_prce_and_valuation.png", dpi=300)
    plt.close()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Daily Price data(universe securities and benchmarks)
    """)


@app.cell
def _(DATA_DIR, pd, sqlite3):
    file_list = sorted(list(DATA_DIR.glob("MSCI_KOKUSAI_Price*.parquet")))
    _dfs = [pd.read_parquet(file) for file in file_list]
    df_6 = pd.concat(_dfs, ignore_index=True)
    df_6["date"] = pd.to_datetime(df_6["date"])
    df_6.sort_values(["P_SYMBOL", "date"], ignore_index=True)
    _db_path = DATA_DIR / "MSCI_KOKUSAI_Price_Daily.db"
    _conn = sqlite3.connect(_db_path)
    df_6.to_sql(name="FG_PRICE_Daily", con=_conn, if_exists="replace", index=False)
    _conn.close()


@app.cell
def _(BM_DIR, pd, sqlite3):
    file_path = BM_DIR / "Benchmark_Price.parquet"
    df_7 = pd.read_parquet(file_path)
    df_7["date"] = pd.to_datetime(df_7["date"])
    df_7.sort_values(["P_SYMBOL", "date"], ignore_index=True)
    _db_path = BM_DIR / "BM_Price_Daily.db"
    _conn = sqlite3.connect(_db_path)
    df_7.to_sql(name="FG_PRICE_Daily", con=_conn, if_exists="replace", index=False)
    _conn.close()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Check
    """)


@app.cell
def _(DATA_DIR, display, get_table_names, pd, sqlite3):
    # def get_table_names(db_path: Path) -> list[str]:
    #     table_names = []
    #     try:
    #         with sqlite3.connect(db_path) as conn:
    #             cursor = conn.cursor()
    #             query = "select name from sqlite_master where type='table';"
    #             cursor.execute(query)
    #             tables = cursor.fetchall()
    #             table_names = [table[0] for table in tables]
    #     except sqlite3.Error as e:
    #         print(f"データベースエラーが発生: {e}")
    #     except Exception as e:
    #         print(f"予期せぬエラーが発生: {e}")
    code_db = DATA_DIR / "MSCI_KOKUSAI_BPM_and_Factset_Code.db"
    #     return table_names
    code_db_date_list = get_table_names(code_db)
    financials_db = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    financials_db_date_list = get_table_names(financials_db)
    for d in financials_db_date_list[40:41]:
        with sqlite3.connect(code_db) as _conn:
            _df_code = pd.read_sql_query(f"SELECT * FROM '{d}'", _conn)
        # display(financials_db_date_list[0])
        with sqlite3.connect(financials_db) as _conn:
            _df_financials = pd.read_sql_query(f"SELECT * FROM '{d}'", _conn)
        _df_financials = (
            pd.pivot_table(
                _df_financials,
                index=["date", "P_SYMBOL"],
                columns="variable",
                values="value",
            )
            .reset_index()
            .sort_values("date", ignore_index=True)
        )
        display(_df_financials)
        merged_df = pd.merge(
            _df_financials,
            _df_code[
                ["date", "P_SYMBOL", "GICS Sector", "GICS Industry", "Weight (%)"]
            ],
            on=["date", "P_SYMBOL"],
            how="left",
        ).dropna(subset="Weight (%)")
        print(f"df_code: {_df_code.shape} --> merged_df: {merged_df.shape}")
        display(merged_df)
        display(merged_df["Weight (%)"].sum())  # display(df_code)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## FRED Economic data
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Download data and store in FRED database
    """)


@app.cell
def _(FRED_DIR, store_fred_database):
    _db_path = FRED_DIR / "FRED.db"
    yield_data = [
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
    spread = ["T10Y2Y", "T10Y3M"]  # FF金利（実行金利）
    store_fred_database(
        db_path=_db_path, series_id_list=yield_data + spread
    )  # 1 month  # 3 month  # 6 month  # 1 year  # 2 year  # 3 year  # 5 year  # 7 year  # 10 year  # 20 year  # 30 year


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Plot Spread and Interest Rate
    """)


@app.cell
def _(FRED_DIR, plot_us_interest_rates_and_spread):
    _db_path = FRED_DIR / "FRED.db"
    plot_us_interest_rates_and_spread(db_path=_db_path)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Leve, Slope, Curvature(PCA analysis)
    """)


@app.cell
def _(FRED_DIR, pd, plot_loadings_and_explained_variance, sqlite3):
    series_id_list = [
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
    _conn = sqlite3.connect(FRED_DIR / "FRED.db")
    _dfs = []
    for series_id in series_id_list:
        df_8 = (
            pd.read_sql(sql=f"SELECT * FROM '{series_id}'", con=_conn)
            .rename(columns={series_id: "value"})
            .assign(variable=series_id)
        )
        _dfs.append(df_8)
    df_8 = pd.pivot(
        pd.concat(_dfs, ignore_index=True),
        index="date",
        values="value",
        columns="variable",
    ).sort_index()
    df_8.index = pd.to_datetime(df_8.index)
    df_8 = df_8.reindex(columns=series_id_list)
    plot_loadings_and_explained_variance(df_8)


@app.cell
def _(pd_df, plt, sns):
    # plot
    _fig, _axes = plt.subplots(3, 1, figsize=(12, 6), tight_layout=True, sharex=True)
    _fig.suptitle("PCA of US Treasury Yield Changes")
    ax1 = _axes[0]
    sns.lineplot(pd_df, x=pd_df.index, y="PC1 (Level)", ax=ax1, color="blue")
    ax1.grid(linewidth=0.5)
    ax2 = _axes[1]
    sns.lineplot(pd_df, x=pd_df.index, y="PC2 (Slope)", ax=ax2, color="red")
    ax2.grid(linewidth=0.5)
    ax3 = _axes[2]
    sns.lineplot(pd_df, x=pd_df.index, y="PC3 (Curvature)", ax=ax3, color="green")
    ax3.grid(linewidth=0.5)
    plt.show()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Financials -> Rank
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Make Return data
    """)


@app.cell
def _(DATA_DIR, display, pd, sqlite3):
    _db_path = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    _conn = sqlite3.connect(_db_path)
    df_9 = pd.read_sql(sql="SELECT * FROM Return", con=_conn)
    display(df_9)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Make rank data tables
    """)


@app.cell
def _(DATA_DIR, display, np, pd, sqlite3):
    _db_path = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    _conn = sqlite3.connect(_db_path)
    _variable = "FF_ROIC"
    df_10 = (
        pd.read_sql(f"SELECT * FROM '{_variable}'", con=_conn, parse_dates=["date"])
        .assign(
            year=lambda row: row["date"].dt.year, month=lambda row: row["date"].dt.month
        )
        .drop(columns="variable")
    )
    _db_path = DATA_DIR / "MSCI_KOKUSAI_BPM_and_Factset_Code.db"
    _conn = sqlite3.connect(_db_path)
    _df_code = pd.read_sql(sql="SELECT * FROM all_data", con=_conn)
    df_10 = pd.merge(
        df_10,
        _df_code[["year", "month", "P_SYMBOL", "Weight (%)", "GICS Sector"]],
        how="left",
    ).dropna(subset=["Weight (%)"])
    df_10[f"{_variable}_rank_universe"] = (
        df_10.groupby("date")["value"]
        .transform(
            lambda x: pd.qcut(x, q=5, labels=False, duplicates="drop") + 1
            if x.notna().sum() >= 5
            else pd.Series(np.nan, index=x.index)
        )
        .replace({1.0: "rank5", 2.0: "rank4", 3.0: "rank3", 4.0: "rank2", 5.0: "rank1"})
    )
    df_10[f"{_variable}_rank_sector"] = (
        df_10.groupby(["date", "GICS Sector"])["value"]
        .transform(
            lambda x: pd.qcut(x, q=5, labels=False, duplicates="drop") + 1
            if x.notna().sum() >= 5
            else pd.Series(np.nan, index=x.index)
        )
        .replace({1.0: "rank5", 2.0: "rank4", 3.0: "rank3", 4.0: "rank2", 5.0: "rank1"})
    )
    df_10.rename(columns={"value": _variable}, inplace=True)
    display(df_10)
    _db_path = DATA_DIR / "MSCI_KOKUSAI_Factset_Financials.db"
    _conn = sqlite3.connect(_db_path)
    df_return = pd.pivot(
        pd.read_sql(sql="SELECT * FROM Return", con=_conn, parse_dates=["date"]),
        index=["date", "P_SYMBOL"],
        columns="variable",
        values="value",
    ).reset_index()
    df_10 = pd.merge(df_10, df_return, on=["date", "P_SYMBOL"], how="left")
    display(df_10)
    return (df_10,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Visualize total weight by FF_ROIC rank(timeseries)
    """)


@app.cell
def _(df_10, mdates, pd, plt):
    _variable = "FF_ROIC"
    g = pd.DataFrame(
        df_10.groupby(["date", f"{_variable}_rank_universe"])["P_SYMBOL"].agg("count")
    ).reset_index()
    g = pd.pivot(
        g, index="date", columns=f"{_variable}_rank_universe", values="P_SYMBOL"
    )
    g["total_secs"] = g.sum(axis=1)
    g_weight = pd.DataFrame(
        df_10.groupby(["date", f"{_variable}_rank_universe"])["Weight (%)"].agg("sum")
    ).reset_index()
    g_weight = pd.pivot(
        g_weight,
        index="date",
        columns=f"{_variable}_rank_universe",
        values="Weight (%)",
    )
    g_weight["total_weight (%)"] = g_weight.sum(axis=1)
    g_weight.index = pd.to_datetime(g_weight.index)
    cols_to_plot = [f"rank{_i}" for _i in range(1, 6)]
    _ax = g_weight[cols_to_plot].plot(
        kind="area", stacked=True, figsize=(10, 4), alpha=0.7
    )
    _ax.set_title(f"Total Weight (%) by {_variable} Rank")
    _ax.set_ylabel("Total Weight (%)")
    _ax.xaxis.set_major_locator(mdates.YearLocator(2))
    _ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _ax.set_xlabel("Year")
    _ax.legend(title=f"{_variable} Rank", loc="lower right")
    plt.xticks(rotation=0, ha="center")
    plt.tight_layout()
    plt.show()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    -   2019 年から 2020 年にかけて、ROIC ランクが高位の weight が増加。rank1 は大型寄りになった。
    """)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 1. 【最重要・先行指標】実質時給 (Real Average Hourly Earnings)
    """)


@app.cell
def _(FRED_API, FRED_DIR, Fred, store_fred_database):
    fred = Fred(api_key=FRED_API)
    store_fred_database(
        db_path=FRED_DIR / "FRED.db",
        series_id_list=[
            "CES0500000031",  # Real Average Hourly Earnings
            "PCEC",  # Personal Consumption Expenditures
            "PAYEMS",  # All Employees: Total Nonfarm Payrolls
            "UNRATE",  # Unemployment Rate
            "UMCSENT",  # University of Michigan: Consumer Sentiment
            "INDRPO",  # Industrial Production Index - Total Index [INDPRO]
            "TCU",  # Capacity Utilization: Total Industry [TCU]
            "IPNCON",  # Industrial Production: Nondefense Capital Goods [IPNCONGD]
            "USTRADE",  # U.S. International Trade Balance [NETEXP]
        ],
    )


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
