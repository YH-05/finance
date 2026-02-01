"""
step3.py

[データ前処理 step3]
- リターンのテーブルを作成
-
"""

import datetime
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame

from src.analysis.returns import calculate_return_multi_periods
from src.bloomberg import data_blpapi, data_local
from src.configuration import Config
from src.database import sqlite_utils
from src.factset.price import load_fg_price
import src.factset_utils as factset_utils


def get_financials_db_path(universe_code: str) -> Path:
    config = Config.from_env()
    index_dir = config.factset_index_constituents_dir / universe_code
    financials_db_path: Path = index_dir / "Financials_and_Price.db"

    return financials_db_path


def create_return_dataframe(universe_code: str) -> DataFrame:
    """
    FactsetデータのFG_PRICEからリターンを計算（バックとフォワードで他期間）
    """
    financials_db_path = get_financials_db_path(universe_code=universe_code)
    df_price: DataFrame = load_fg_price(financials_db_path)
    df_return = calculate_return_multi_periods(
        df_price=df_price,
        date_column="date",
        symbol_column="P_SYMBOL",
        price_column="FG_PRICE",
    )

    return df_return


def get_missing_data_return_dataframe(df_return: DataFrame) -> DataFrame:
    missing_by_date: DataFrame = df_return.groupby("date").apply(
        lambda x: x.select_dtypes(include=[np.number]).isna().mean() * 100
    )

    return missing_by_date


def validate_return_data(df_return: DataFrame) -> list[str]:
    """
    データチェック
    銘柄によってはdateが1カ月ずつ連続でデータがあるとは限らない
    FG_PRICEがない場合にpct_changeを素直に実行するとリターンの期間が他の銘柄とずれる
    そのため、全dateの長さと銘柄ごとのdateの長さを比較する
    """
    df_check = df_return.reset_index()

    symbol_date_counts = df_check.groupby("P_SYMBOL")["date"].nunique()
    all_date_len = len(df_check["date"].unique())
    not_enough_len_symbols = symbol_date_counts[
        symbol_date_counts != all_date_len
    ].index

    return not_enough_len_symbols


def _preprocess_before_store_to_db(
    df_return: DataFrame, return_col_name: str
) -> DataFrame:
    """
    dbファイルに保存する直前の前処理

    [Args]
        df_return(DataFrame): create_return_dataframe関数で作成した、リターン系のカラムを持つデータフレーム
        return_col_name(str): データベースに保存するリターン系カラム. ReturnまたはForward_Returnで始まる.
    """
    df_slice: DataFrame = (
        df_return[["date", "P_SYMBOL", return_col_name]]
        .rename(columns={return_col_name: "value"})
        .assign(variable=return_col_name)
    )
    df_slice["value"] = df_slice["value"].astype(float)
    df_slice["date"] = pd.to_datetime(df_slice["date"])

    return df_slice


def store_index_price() -> None:
    """
    BlpAPIを使ってインデックスの価格データを取得
    【注意！ Bloomberg Terminalを起動している必要がある】
    """
    bbg_ticker = data_local.BloombergTickers()
    EQUITY_TYPES = {"equity_index", "equity_sector_index", "equity_industry_index"}
    tickers_to_download = [
        ticker["bloomberg_ticker"]
        for ticker in bbg_ticker.get_all_tickers_description()
        if (ticker.get("type") in EQUITY_TYPES)
        & (not ticker.get("bloomberg_ticker").startswith("MXWDJ"))
    ]

    # --- データベースに保存 ---
    blp = data_blpapi.BlpapiFetcher()

    # 新規ティッカーがある場合
    # TODO: 今後機能を分離して実装する

    # data = blp.get_historical_data(
    #     securities=tickers_to_download,
    #     id_type="ticker",
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

    # 既存データの更新
    config = Config.from_env()
    bloomberg_index_db_path = config.bloomberg_root_dir / "Index_Price_and_Returns.db"
    rows_updated = blp.update_historical_data(
        db_path=bloomberg_index_db_path,
        table_name="PX_LAST",
        tickers=tickers_to_download,
        id_type="ticker",
        field="PX_LAST",
        default_start_date=datetime.datetime(2000, 1, 1),
        verbose=True,
    )
    logging.info(f"\n{'=' * 60}")
    logging.info(f"処理完了: {rows_updated:,}行を処理しました")
    logging.info(f"{'=' * 60}")


def main(universe_code: str):
    df_return = create_return_dataframe(universe_code=universe_code)
    not_enough_len_symbols = validate_return_data(df_return)
    financials_db_path = get_financials_db_path(universe_code=universe_code)

    if len(not_enough_len_symbols) > 0:
        logging.error(f"問題あり. not_enough_len_symbols={not_enough_len_symbols}")
    else:  # 問題なければデータベースに保存
        logging.info("問題なし")
        df_return.reset_index(inplace=True)

        for col in [
            s
            for s in df_return.columns
            if s.startswith("Return") or s.startswith("Forward_Return")
        ]:
            df_slice = _preprocess_before_store_to_db(
                df_return=df_return, return_col_name=col
            )
            sqlite_utils.delete_table_from_database(
                db_path=financials_db_path, table_name=col
            )
            factset_utils.store_to_database(
                df=df_slice, db_path=financials_db_path, table_name=col
            )


if __name__ == "__main__":
    UNIVERSE_CODE = "MSXJPN_AD"
    main(universe_code=UNIVERSE_CODE)
