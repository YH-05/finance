"""
factset_downloaded_data_utils.py

Factsetからエクセルでダウンロードしたデータを操作するモジュール
"""

import datetime
import sqlite3
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.simplefilter("ignore")


# =====================================================================
def store_to_database(
    df: pd.DataFrame,
    db_path: Path,
    table_name: str,
    unique_cols: list[str] | None = None,
    verbose: bool = False,
):
    """
    Pandas DataFrameをSQLiteデータベースに書き込む。
    既存のテーブルのデータと重複する行（date, P_SYMBOL, value, variable の組み合わせが一致する行）
    は追加しない。

    Args:
        df (pd.DataFrame): 書き込みたいデータフレーム（date, P_SYMBOL, value, variable のカラムを持つ）。
        db_path (str): 接続するSQLiteデータベースのファイルパス。
        table_name (str): 書き込み先のテーブル名。
        unique_cols ([str]): 一意性をチェックするカラム
    """
    if unique_cols is None:
        unique_cols = ["date", "P_SYMBOL", "variable"]

    # 必須カラムのチェック
    if not all(col in df.columns for col in unique_cols):
        raise ValueError(
            f"データフレームには必須のカラム {unique_cols} の全てが含まれている必要があります。"
        )

    # 1. データベースに接続
    # db_path (データベースファイルへのパス) を使用
    conn = sqlite3.connect(db_path)

    # 2. 既存のテーブルから一意性チェックに必要なデータを取得し、重複行を除外
    try:
        # テーブルが存在する場合、既存の複合キーデータを取得
        select_cols = ", ".join(unique_cols)
        existing_df = pd.read_sql(f"SELECT {select_cols} FROM {table_name}", conn)

        # ▼▼▼ 修正箇所 ▼▼▼
        # 既存データの 'date' カラムも datetime 型に変換する
        # (unique_cols に 'date' が含まれている場合のみ)
        if "date" in unique_cols and "date" in existing_df.columns:
            existing_df["date"] = pd.to_datetime(existing_df["date"])
        # ▲▲▲ 修正箇所 ▲▲▲

        # 重複チェック用に新しいデータと既存データをマージ
        merged_df = pd.merge(
            df.drop_duplicates(subset=unique_cols),  # 新しいデータ側も自身の重複を除去
            existing_df,
            on=unique_cols,
            how="left",
            indicator=True,
        )

        # 既存データに含まれていない行 ('left_only') のみを選択
        df_to_add = merged_df[merged_df["_merge"] == "left_only"].drop(
            columns=["_merge"]
        )

        if df_to_add.empty:
            print(
                f"テーブル '{table_name}' に追加すべき新しいデータはありませんでした。スキップします。"
            )
            conn.close()
            return

        if verbose:
            print(
                f"既存の {len(existing_df)} 行との重複をチェックしました。{len(df_to_add)} 行を新たに追加します。"
            )

    except pd.io.sql.DatabaseError:  # type: ignore
        # テーブルがまだ存在しない場合、全ての行を追加
        df_to_add = df.drop_duplicates(subset=unique_cols)  # 自身の重複は除去
        if verbose:
            print(
                f"テーブル '{table_name}' は存在しません。新しいテーブルとして、すべての {len(df_to_add)} 行を追加します。"
            )

    # 3. ユニークな行だけをデータベースに書き込み
    df_to_add.to_sql(table_name, conn, if_exists="append", index=False)

    # 4. 接続を閉じる
    conn.close()
    print(f"  -> {table_name}: データの書き込みが完了しました。")


# =====================================================================
def delete_table_from_database(db_path: Path, table_name: str, verbose: bool = False):
    """
    指定されたSQLiteデータベースから特定のテーブルを削除する。
    テーブルが存在しない場合でもエラーは発生しない。

    Args:
        db_path (Path): 接続するSQLiteデータベースのファイルパス。
        table_name (str): 削除するテーブル名。
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
