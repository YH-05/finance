"""

database_utils.py

"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl


# ==========================================================================================
def get_table_names(db_path: Path | str):
    """
    指定されたSQLiteデータベース内の全テーブル名を取得する。

    Parameters
    ----------
    db_path : Path | str
        SQLiteデータベースのパス。

    Returns
    -------
    list[str]
        データベース内で見つかったテーブル名のリスト。
    """
    db_path = str(db_path) if isinstance(db_path, Path) else db_path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


# def get_table_names(db_path: Path | str) -> list[str]:
#     table_names = []
#     try:
#         with sqlite3.connect(str(db_path)) as conn:
#             cursor = conn.cursor()
#             query = "select name from sqlite_master where type='table';"
#             cursor.execute(query)
#             tables = cursor.fetchall()
#             table_names = [table[0] for table in tables]
#     except sqlite3.Error as e:
#         print(f"データベースエラーが発生: {e}")
#     except Exception as e:
#         print(f"予期せぬエラーが発生: {e}")

#     return table_names


# ==========================================================================================


def read_single_table(table: str, db_uri: str) -> pl.DataFrame | None:
    """
    指定されたURIのSQLiteデータベースから単一のテーブルを読み込む。

    `read_tables_parallel`関数から呼び出されることを想定したヘルパー関数である。
    エラーが発生した場合はNoneを返す。

    Parameters
    ----------
    table : str
        読み込むテーブルの名前。
    db_uri : str
        SQLiteデータベースのURI。
        例: "sqlite:///path/to/database.db"

    Returns
    -------
    polars.DataFrame or None
        読み込んだテーブルのデータを格納したPolars DataFrame。
        読み込みに失敗した場合はNoneを返す。
    """
    print(f"Reading table: '{table}'...")
    try:
        query = f"SELECT * FROM `{table}`"
        df = pl.read_database_uri(query, db_uri)
        # df = df.with_columns(pl.lit(table).alias("source_table"))
        return df
    except Exception as e:
        print(f"Error reading table '{table}': {e}")
        return None


# ==========================================================================================
def read_tables_parallel(db_uri: str, table_names: list[str]) -> pl.DataFrame:
    """
    複数のテーブルを並列で読み込み、一つのPolars DataFrameに結合する。

    内部で `read_single_table` を並列に呼び出す。
    読み込みに失敗したテーブルは無視される。

    Parameters
    ----------
    db_uri : str
        SQLiteデータベースのURI。
    table_names : list[str]
        読み込むテーブル名のリスト。

    Returns
    -------
    polars.DataFrame
        結合されたPolars DataFrame。
        全てのテーブルの読み込みに失敗した場合は空のDataFrameを返す。
    """
    num_workers = len(table_names)
    num_workers = min(num_workers, 4)

    # ThreadPoolExecutorを使ってI/Oバウンドなタスクを並列化
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # map()を使って各テーブルの読み込みタスクを並列実行
        # db_uriは全ての呼び出しに同じものが使われます
        dfs = list(
            executor.map(read_single_table, table_names, [db_uri] * len(table_names))
        )

    # None（読み込み失敗）を除外
    valid_dfs = [df for df in dfs if df is not None]

    if not valid_dfs:
        print("No data was successfully read. Returning an empty DataFrame.")
        return pl.DataFrame()

    return pl.concat(valid_dfs, how="vertical_relaxed")


# ==========================================================================================
def step1_load_file_to_db(
    file_list,
    db_name,
    file_type="parquet",
) -> None:
    """
    全てのCSVファイルを読み込み、一つのテーブルに生のデータを格納する。
    この処理はメモリを最も使用するが、実行は最初の一度だけ。

    Parameters
    ----------
    file_list : list
        読み込むファイルのリスト。
    db_name : str
        データベース名。
    file_type : str, default "parquet"
        ファイルタイプ ("parquet" または "csv")。
    """
    print("--- ステップ1: 元データファイルをデータベースにロード開始 ---")

    conn = None
    try:
        # データベースに接続（ファイルがなければ新規作成）
        conn = sqlite3.connect(db_name)

        # データベースのページサイズを増やし、同期をオフにすることで書き込みを高速化
        conn.execute("PRAGMA page_size = 65536;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = OFF;")

        # 最初の一度だけ、既存のテーブルを削除する
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS all_data;")

        # 各ファイルをループ処理でデータベースに直接書き込み
        for i, file_path in enumerate(file_list):
            print(f"({i+1}/{len(file_list)}) {file_path.name} を読み込み中...")

            if file_type == "parquet":
                df = pd.read_parquet(file_path)
            elif file_type == "csv":
                df = pd.read_csv(file_path, encoding="utf-8")
            else:
                raise ValueError("Unsupported file type.")

            # 日付カラムのフォーマットを変換
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

            # データベースにデータを追記
            # 初回はテーブルが作成される
            df.to_sql("all_data", conn, if_exists="append", index=False)

            # メモリを解放
            del df

        print("--- 全てのデータを一つのテーブル 'all_data' に格納完了 ---")

    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if conn:
            conn.close()


# ==========================================================================================
def step2_create_variable_tables(db_name) -> None:
    """
    一つの大きなテーブルから、variableごとにテーブルを分割する。

    Parameters
    ----------
    db_name : str
        データベース名。
    """
    print("--- ステップ2: variableごとのテーブル作成開始 ---")

    conn = None
    try:
        conn = sqlite3.connect(db_name)

        # データベースのページサイズを増やし、同期をオフにすることで書き込みを高速化
        conn.execute("PRAGMA page_size = 65536;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = OFF;")

        # uniqueなvariable名をSQLで取得
        unique_variables_sql = pd.read_sql_query(
            "SELECT DISTINCT variable FROM all_data", conn
        )
        unique_variables = unique_variables_sql["variable"].tolist()

        for i, variable in enumerate(unique_variables):
            print(f"({i+1}/{len(unique_variables)}) {variable} のテーブルを作成中...")

            # SQLクエリでデータをフィルタリングし、新しいテーブルとして作成
            query = f"""
                CREATE TABLE IF NOT EXISTS {variable} AS
                SELECT * FROM all_data WHERE variable = '{variable}';
            """
            conn.execute(query)

        # `variable`カラムにインデックスを作成して検索を高速化
        conn.execute("CREATE INDEX IF NOT EXISTS idx_variable ON all_data(variable);")

        print("--- variableごとのテーブル作成完了 ---")

    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if conn:
            conn.close()


# ==========================================================================================
def step3_create_return_table(db_path) -> None:
    """
    価格データからリターンを計算し、Returnテーブルを作成する。

    Parameters
    ----------
    db_path : str
        データベースパス。
    """
    conn = sqlite3.connect(db_path)
    df = (
        pd.read_sql("SELECT * FROM FG_PRICE", con=conn)
        .sort_values(["P_SYMBOL", "date"], ignore_index=True)
        .drop(columns=["variable"])
    ).assign(log_value=lambda row: np.log(row["value"]))

    for month in [1, 3, 6, 12, 36, 60]:  # 1M, 3M, 6M, 1Y, 3Y, 5Yのリターン
        # 過去リターン
        return_col = ""
        if month < 12:
            return_col = f"Return_{month}M"
        else:
            return_col = f"Return_{month//12}Y"
        df[return_col] = df.groupby(["P_SYMBOL"])["log_value"].diff(periods=month)

        # 将来リターン
        if month < 12:
            return_col = f"Return_{month}MForward"
        else:
            return_col = f"Return_{month//12}YForward"
        df[return_col] = df.groupby(["P_SYMBOL"])["log_value"].diff(periods=-month)

    save_cols = ["date", "P_SYMBOL"] + [s for s in df.columns if s.startswith("Return")]
    df = df[save_cols]
    df = pd.melt(
        df,
        id_vars=["date", "P_SYMBOL"],
        value_vars=df.columns.tolist()[2:],
    )

    # store in a database
    df.to_sql(name="Return", con=conn, if_exists="replace", index=False)
    print("Return tableが作成されました。")


# ==========================================================================================
def append_diff_to_sqlite(db_path: str, table_name: str, df_new: pd.DataFrame):
    """
    SQLite3の既存テーブルと新しいDataFrameを比較し、差分のみをテーブルに追加する。

    Parameters
    ----------
    db_path : str
        SQLite3 データベースファイルへのパス。
    table_name : str
        対象のテーブル名。
    df_new : pd.DataFrame
        新しく保存したいデータを含むDataFrame。
    """
    conn = sqlite3.connect(db_path)

    try:
        # --- 1. 既存のテーブルをDataFrameとして読み込む ---
        # テーブルが存在しない場合は、空のDataFrameを作成する
        if pd.io.sql.has_table(table_name, conn):
            df_existing = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        else:
            print(
                f"テーブル '{table_name}' が存在しないため、全てのデータを新規保存します。"
            )
            df_existing = pd.DataFrame(columns=df_new.columns)

        # データ型が異なると正しく比較できないため、可能な範囲で合わせる
        # (ここでは省略していますが、厳密に行う場合は型変換の考慮が必要です)

        # --- 2. 新しいデータと既存データの差分を特定する ---
        # 外部結合(outer join)を使い、どちらのDFにデータが存在するかを示す列(_merge)を追加
        merged_df = pd.merge(
            df_existing,
            df_new,
            how="outer",
            on=list(df_new.columns),  # 全ての列をキーとして比較
            indicator=True,
        )

        # '_merge'列が'right_only'のものが、新しいDFにのみ存在する行
        df_to_add = merged_df[merged_df["_merge"] == "right_only"].drop(
            columns=["_merge"]
        )

        # --- 3. 差分データをテーブルに追加する ---
        if not df_to_add.empty:
            print(
                f"{len(df_to_add)}件の新規データをテーブル '{table_name}' に追加します。"
            )
            df_to_add.to_sql(
                table_name,
                conn,
                if_exists="append",  # 既存のテーブルに追記
                index=False,  # DataFrameのインデックスは不要
            )
        else:
            print("新規データはありませんでした。")

    finally:
        conn.close()


# ==========================================================================================
def get_rows_by_unique_values(
    source_db_path: Path,
    target_db_path: Path,
    source_table: str,
    target_table: str,
    source_column: str,
    target_column: str,
) -> pd.DataFrame:
    """
    source_tableの指定カラムのユニークな値を持つ行をtarget_tableから抽出

    Parameters
    ----------
    source_db_path : Path
        ユニークな値を取得する元データベースファイルのパス
    target_db_path : Path
        データを抽出する対象データベースファイルのパス
    source_table : str
        ユニークな値を取得する元テーブル名
    target_table : str
        データを抽出する対象テーブル名
    source_column : str
        source_table内でユニークな値を取得するカラム名
    target_column : str
        target_table内でフィルタリングに使用するカラム名

    Returns
    -------
    pd.DataFrame
        target_tableから抽出された行を含むDataFrame

    Examples
    --------
    >>> source_db = Path("data/prices.db")
    >>> target_db = Path("data/company_info.db")
    >>> df = get_rows_by_unique_values(
    ...     source_db_path=source_db,
    ...     target_db_path=target_db,
    ...     source_table="PX_LAST",
    ...     target_table="COMPANY_INFO",
    ...     source_column="Ticker",
    ...     target_column="Bloomberg_Ticker"
    ... )
    >>> print(df.head())
    """
    # source_tableからユニークな値を取得
    with sqlite3.connect(str(source_db_path)) as conn:
        query = f'SELECT DISTINCT "{source_column}" FROM "{source_table}"'
        unique_values = pd.read_sql(query, conn)[source_column].tolist()

    # target_tableから該当する行を抽出
    with sqlite3.connect(str(target_db_path)) as conn:
        placeholders = ",".join(["?" for _ in unique_values])
        query = f"""
            SELECT *
            FROM "{target_table}"
            WHERE "{target_column}" IN ({placeholders})
        """
        df = pd.read_sql(query, conn, params=unique_values)

    return df


# ==========================================================================================
def get_unique_values(db_path: Path, table_name: str, column_name: str) -> list:
    """
    指定したテーブルとカラムのユニークな値を取得する。

    Parameters
    ----------
    db_path : Path
        データベースパス。
    table_name : str
        テーブル名。
    column_name : str
        カラム名。

    Returns
    -------
    list
        ユニークな値のリスト。
    """
    with sqlite3.connect(str(db_path)) as conn:
        query = f'SELECT DISTINCT "{column_name}" FROM "{table_name}" ORDER BY "{column_name}"'
        df = pd.read_sql(query, conn)
    return df[column_name].tolist()


# ============================================================================================
def delete_table_from_database(db_path: Path, table_name: str, verbose: bool = False):
    """
    指定されたSQLiteデータベースから特定のテーブルを削除する。
    テーブルが存在しない場合でもエラーは発生しない。

    Parameters
    ----------
    db_path : Path
        接続するSQLiteデータベースのファイルパス。
    table_name : str
        削除するテーブル名。
    verbose : bool, default False
        詳細なログを出力するかどうか。
    """
    conn = None
    try:
        # 1. データベースに接続
        conn = sqlite3.connect(db_path)

        # 2. カーソルを作成
        cur = conn.cursor()

        # 3. DROP TABLE IF EXISTS クエリを実行
        #    f-stringはSQLインジェクションのリスクがあるが、
        #    この関数の用途（内部的なDB管理）を考慮し、許可する。
        query = f"DROP TABLE IF EXISTS {table_name}"
        cur.execute(query)

        # 4. 変更をコミット
        conn.commit()

        if verbose:
            print(
                f"データベース '{db_path.name}' からテーブル '{table_name}' を削除しました（または存在しませんでした）。"
            )

    except sqlite3.Error as e:
        print(f"データベース '{db_path.name}' の操作中にエラーが発生しました: {e}")
        if conn:
            conn.rollback()  # エラー時はロールバック

    finally:
        # 5. 接続を閉じる
        if conn:
            conn.close()
