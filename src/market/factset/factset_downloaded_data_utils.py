"""
factset_downloaded_data_utils.py

Factsetからエクセルでダウンロードしたデータを操作するモジュール
"""

import datetime
import re
import sqlite3
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from utils_core.logging import get_logger

logger = get_logger(__name__)

warnings.simplefilter("ignore")


# =====================================================================
# SQLインジェクション対策用ヘルパー関数
# =====================================================================
def _validate_sql_identifier(name: str) -> str:
    """SQL識別子（テーブル名・カラム名）が安全であることを検証する。

    SQLiteでは識別子をパラメータ化できないため、
    この関数で識別子が安全な形式であることを保証する。

    Parameters
    ----------
    name : str
        検証するSQL識別子

    Returns
    -------
    str
        検証済みの識別子（入力と同じ値）

    Raises
    ------
    ValueError
        識別子が不正な形式の場合
    """
    # 空文字列チェック
    if not name or not name.strip():
        raise ValueError("SQL識別子は空にできません")

    # 許可するパターン: 英数字、アンダースコア、ハイフン、ドット
    # （FactSetのテーブル名・カラム名で使用される文字）
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_\-\.]*$"
    if not re.match(pattern, name):
        raise ValueError(
            f"SQL識別子に不正な文字が含まれています: {name!r}. "
            f"許可される形式: 英字で始まり、英数字・アンダースコア・ハイフン・ドットのみ"
        )

    return name


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

    # SQL識別子バリデーション（CWE-89 対策）
    _validate_sql_identifier(table_name)
    for col in unique_cols:
        _validate_sql_identifier(col)

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
        # nosec B608 - table_name, unique_cols は _validate_sql_identifier() で検証済み
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
            logger.info("No new data to add, skipping", table=table_name)
            conn.close()
            return

        if verbose:
            logger.debug(
                "Deduplication check completed",
                table=table_name,
                existing_rows=len(existing_df),
                new_rows=len(df_to_add),
            )

    except pd.io.sql.DatabaseError:  # type: ignore
        # テーブルがまだ存在しない場合、全ての行を追加
        df_to_add = df.drop_duplicates(subset=unique_cols)  # 自身の重複は除去
        if verbose:
            logger.debug(
                "Table does not exist, creating new",
                table=table_name,
                rows=len(df_to_add),
            )

    # 3. ユニークな行だけをデータベースに書き込み
    df_to_add.to_sql(table_name, conn, if_exists="append", index=False)

    # 4. 接続を閉じる
    conn.close()
    logger.info("Data written to database", table=table_name)


# =====================================================================
def delete_table_from_database(db_path: Path, table_name: str, verbose: bool = False):
    """
    指定されたSQLiteデータベースから特定のテーブルを削除する。
    テーブルが存在しない場合でもエラーは発生しない。

    Args:
        db_path (Path): 接続するSQLiteデータベースのファイルパス。
        table_name (str): 削除するテーブル名。
    """
    # SQL識別子バリデーション（CWE-89 対策）
    _validate_sql_identifier(table_name)

    conn = None
    try:
        # 1. データベースに接続
        conn = sqlite3.connect(db_path)

        # 2. カーソルを作成
        cur = conn.cursor()

        # 3. DROP TABLE IF EXISTS クエリを実行
        # nosec B608 - table_name は _validate_sql_identifier() で検証済み
        query = f"DROP TABLE IF EXISTS {table_name}"
        cur.execute(query)

        # 4. 変更をコミット
        conn.commit()

        if verbose:
            logger.debug(
                "Table dropped",
                database=db_path.name,
                table=table_name,
            )

    except sqlite3.Error as e:
        logger.error(
            "Database operation failed",
            database=db_path.name,
            error=str(e),
            exc_info=True,
        )
        if conn:
            conn.rollback()  # エラー時はロールバック

    finally:
        # 5. 接続を閉じる
        if conn:
            conn.close()
