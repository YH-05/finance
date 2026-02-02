"""
step2.py

[データ前処理 step2]
Factsetからダウンロードしたデータをまとめる
- FinancialsおよびPriceのデータをデータベースに格納する
"""

from pathlib import Path

import pandas as pd
from pandas import DataFrame
from src.configuration import Config

from src import factset_utils


def load_update_data(file_update: Path) -> DataFrame:
    df_update = pd.read_parquet(file_update).sort_values("date", ignore_index=True)
    df_update = (
        df_update.drop_duplicates()
        .sort_values(["variable", "P_SYMBOL", "date"], ignore_index=True)
        .assign(value=lambda x: x["value"].astype(float))
    )
    return df_update


def update_variable_database_tables(df_update: DataFrame, db_path: Path) -> None:
    """
    最新版（直近1年：1AY）のデータのみ追加
    既存データベースにあるもので、最新版データと重複しているデータは、新しいデータに置き換える(op_duplicate="update")
    【注意】：新規データは新しくデータベースを作成する必要がある
    """
    for variable in df_update["variable"].unique():
        df_update_slice = df_update.loc[df_update["variable"] == variable]
        factset_utils.store_to_database(
            df=df_update_slice,
            db_path=db_path,
            table_name=variable,
            unique_cols=["date", "P_SYMBOL", "variable"],
            verbose=True,
            on_duplicate="update",
        )


def main(universe_code: str) -> None:
    config = Config.from_env()
    factset_financials_dir = config.factset_financials_dir
    index_dir = factset_financials_dir / universe_code
    file_update = (
        index_dir / "Financials_and_Price-compressed-20250131_20251231.parquet"
    )

    df_update = load_update_data(file_update=file_update)

    financials_db_path = index_dir / "Financials_and_Price.db"
    update_variable_database_tables(df_update=df_update, db_path=financials_db_path)


if __name__ == "__main__":
    universe_code = "MSXJPN_AD"
    main(universe_code=universe_code)
