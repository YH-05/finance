"""
data_prepare.py
"""

import sqlite3
import warnings
from pathlib import Path
from typing import List

import pandas as pd

warnings.simplefilter("ignore")


# ==================================================================================
def createDB_bpm_and_factset_code(
    db_name: Path, raw_data_list: List[Path], file_type: str = "csv"
) -> None:
    """
    BPMおよびFactSetの生データからSQLite3データベースを作成する。

    Parameters
    ----------
    db_name : Path
        作成するデータベースファイルのパス。
    raw_data_list : List[Path]
        読み込む生データファイルのパスのリスト。
    file_type : str, default "csv"
        読み込むファイルの種類。"csv" または "parquet"。

    Returns
    -------
    None
    """

    dfs = []
    if file_type == "csv":
        dfs = [pd.read_csv(f, encoding="utf-8") for f in raw_data_list]
    elif file_type == "parquet":
        dfs = [pd.read_parquet(f) for f in raw_data_list]

    df = (
        pd.concat(dfs)
        .assign(date=lambda row: pd.to_datetime(row["date"]))
        .sort_values("date", ignore_index=True)
    )

    # SQLite3データベース作成
    conn = None

    try:
        # データベースに接続（ファイルがなければ新規作成）
        conn = sqlite3.connect(db_name)

        # DataFrameからユニークな日付を取得
        unique_dates = df["date"].unique()

        # 各日付ごとにループ処理
        for date in unique_dates:
            # 現在のループの日付でDataFrameをフィルタリング
            df_monthly = df[df["date"] == date]

            # 日付からテーブル名を作成
            table_name = f"{date.strftime('%Y_%m_%d')}"

            # date列のデータ型をstringに変更
            df_monthly["date"] = pd.to_datetime(df_monthly["date"]).dt.strftime(
                "%Y-%m-%d"
            )

            # DataFrameを対応するテーブルに書き込む
            # if_exists='replace': もし同名テーブルがあれば上書きする
            # index=False: DataFrameのインデックスをDBに保存しない
            df_monthly.to_sql(table_name, conn, if_exists="replace", index=False)

            print(
                f"日付: {date.date()} のデータをテーブル '{table_name}' に書き込みました。"
            )

        # 全ての日付のデータを書き込む(上記で日付ごとにループを回していたものを一括でテーブルに書き込む)
        df["year"] = pd.to_datetime(df["date"]).dt.year
        df["month"] = pd.to_datetime(df["date"]).dt.month
        df.to_sql("all_data", conn, if_exists="replace", index=False)
        print("全ての日付のデータをテーブル名: all_data に書き込みました。")

    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        # 接続を閉じる
        if conn:
            conn.close()
