"""
step1.py

[データ前処理 step1]
BPMとFactsetからダウンロードしたデータをsqlite3に保存
- インデックス別にテーブルを作成
- 元データは`Index_Constituents_with_Factset_code-compressed-*.parquet`
- BPMから取得した構成比や銘柄IDなどのデータと、
  Factsetでダウンロードしたsedol, cusip, isin, code_jpにそれぞれ対応する
  P_SYMBOLおよびFG_COMPANY_NAMEを格納したデータ
"""

import logging
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from debugpy.common.log import log_dir
from pandas import DataFrame

from src.configuration import Config, log
from src.database import sqlite_utils


def load_compressed_files() -> list[Path]:
    """paruqetファイルのリストを取得"""
    config = Config.from_env()
    factset_index_constituents_dir = config.factset_index_constituents_dir
    parquet_list = list(
        factset_index_constituents_dir.glob(
            "Index_Constituents_with_Factset_code-compressed-*.parquet"
        )
    )

    return parquet_list


def concatenate_dataframe(parquet_list: list[str]) -> DataFrame:
    """parquetファイルからデータフレームを作成"""
    dfs: list[DataFrame] = [pd.read_parquet(f) for f in parquet_list]
    df = pd.concat(dfs, ignore_index=True)

    return df


def preprocess_dataframe(df: DataFrame) -> DataFrame:
    """paruqetファイルからデータフレーム作成。データ前処理も行う"""

    df: DataFrame = df.assign(
        date=lambda x: pd.to_datetime(x["date"]),
        SEDOL=lambda x: x["SEDOL"].astype(str),
    ).replace("N/A", np.nan)
    df[["Holdings", "Weight (%)", "Mkt Value"]] = df[
        ["Holdings", "Weight (%)", "Mkt Value"]
    ].astype(float)

    head_cols = ["Universe", "Universe_code_BPM", "date"]
    other_cols = [col for col in df.columns if col not in head_cols]
    df = df.reindex(columns=head_cols + other_cols).sort_values(
        ["Universe", "date", "Name"], ignore_index=True
    )

    return df


def store_dataframe_to_sqlite_by_universe(df: DataFrame) -> None:
    """データ前処理を済ませたデータフレームをユニバースごとのテーブルに保存"""
    # sqlite3データベースパス
    config = Config.from_env()
    factset_index_constituents_dir = config.factset_index_constituents_dir
    db_path = factset_index_constituents_dir / "Index_Constituents.db"

    for universe_code in df["Universe_code_BPM"].unique():
        df_slice = df.loc[df["Universe_code_BPM"] == universe_code].reset_index(
            drop=True
        )
        sqlite_utils.store_to_database(
            df=df_slice,
            db_path=db_path,
            table_name=universe_code,
            unique_cols=["date", "Name", "Asset ID"],
        )


def main():
    config = Config.from_env()

    log.setup_logging(log_file="step1.log", level=logging.DEBUG)
    parquet_file = (
        config.factset_index_constituents_dir
        / "Index_Constituents_with_Factset_code.parquet"
    )

    df = pd.read_parquet(parquet_file)
    df = preprocess_dataframe(df)
    store_dataframe_to_sqlite_by_universe(df=df)


if __name__ == "__main__":
    main()
