"""
price.py

Factsetデータのprice系データ
"""

import sqlite3
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from utils_core.logging import get_logger

logger = get_logger(__name__)


def load_fg_price(
    db_path: Path,
    start_date: str | None = None,
    end_date: str | None = None,
    p_symbol_list: list[str] | None = None,
) -> DataFrame:
    """
    FG_PRICEテーブルからデータを読み込む。

    Parameters
    ----------
    db_path : Path
        データベースパス。
    start_date : str, optional
        開始日（例: '2024-01-01'）。
    end_date : str, optional
        終了日。
    p_symbol_list : List[str], optional
        対象シンボル(Factsetシンボル)のリスト。

    Returns
    -------
    pd.DataFrame
        インデックスがdateのデータフレーム。
    """

    # クエリを構築
    query = """
        SELECT
            date,
            P_SYMBOL,
            CAST(value AS REAL) AS FG_PRICE
        FROM FG_PRICE
        WHERE 1=1
    """

    params = {}

    if start_date:
        query += " AND date >= :start_date"
        params["start_date"] = start_date

    if end_date:
        query += " AND date <= :end_date"
        params["end_date"] = end_date

    if p_symbol_list:
        placeholders = ",".join([f":sym{i}" for i in range(len(p_symbol_list))])
        query += f" AND P_SYMBOL IN ({placeholders})"
        params.update({f"sym{i}": sym for i, sym in enumerate(p_symbol_list)})

    query += " ORDER BY date"

    # データ読み込み
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql(
                query, con=conn, params=params, parse_dates=["date"], index_col="date"
            )
        logger.info("Price data loaded", db_path=str(db_path))
    except Exception as e:
        logger.error("Price data load failed", error=str(e), exc_info=True)
        raise

    return df
