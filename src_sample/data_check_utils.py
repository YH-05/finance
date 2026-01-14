"""

data_check_utils.py

"""

from datetime import datetime, timedelta
from typing import List

import pandas as pd
from dateutil.relativedelta import relativedelta


# ==========================================================================================
def calculate_missing_stats(group_cols: List[str], df: pd.DataFrame, variable: str):
    """
    特定の変数について、指定されたグループごとの欠損統計量を計算する。

    Parameters
    ----------
    group_cols : List[str]
        グループ化に使用するカラム名のリスト（例: `['date', 'sector']`）。
    df : pd.DataFrame
        分析対象のデータフレーム。
    variable : str
        欠損統計量を計算する対象のカラム名。

    Returns
    -------
    pd.DataFrame
        指定されたグループごとの欠損統計量を含むデータフレーム。
        カラムは以下の通り:
        * `group_cols`で指定されたカラム
        * `variable`: 統計量を計算した変数名
        * `total_securities`: グループ内の証券総数
        * `total_weight`: グループ内の`Weight (%)`の合計
        * `missing_securities`: 指定された変数が欠損している証券の数
        * `missing_Weight (%)`: 指定された変数が欠損している証券の`Weight (%)`の合計
        * `missing_ratio`: 指定された変数が欠損している証券の割合
    """

    missing_condition = df[variable].isnull()
    # 欠損の個数
    result = (
        (
            df.groupby(group_cols)
            .agg(
                total_securities=("P_SYMBOL", "count"),
                total_weight=("Weight (%)", "sum"),
                missing_securities=(
                    "P_SYMBOL",
                    lambda x: missing_condition[x.index].sum(),
                ),
                missing_weight=(
                    "Weight (%)",
                    lambda x: x[missing_condition[x.index]].sum(),
                ),
            )
            .rename(columns={"missing_weight": "missing_Weight (%)"})
        )
        .sort_index()
        .reset_index()
    ).assign(variable=variable)
    # 欠損割合
    result["missing_ratio"] = result["missing_securities"] / result["total_securities"]
    # reindex
    result = result.reindex(
        columns=group_cols
        + [
            "variable",
            "total_securities",
            "total_weight",
            "missing_securities",
            "missing_Weight (%)",
            "missing_ratio",
        ]
    )

    return result


# ==========================================================================================
def extract_dates_in_range(
    date_list: List[str],
    target_date_str: str,
    months_around: int = 60,
    date_format: str = "%Y-%m-%d",
) -> List[str]:
    """
    日付文字列のリストから、指定された日付の前後(months_around)ヶ月の期間内にある日付を抽出する。

    期間の定義:
    - 開始: 指定日の(months_around)ヶ月前の月の初日
    - 終了: 指定日の(months_around)ヶ月後の月の末日

    Parameters
    ----------
    date_list : List[str]
        検索対象の日付文字列のリスト。
    target_date_str : str
        基準となる日付文字列。
    months_around : int, default 60
        基準日の前後何ヶ月を範囲とするか。
    date_format : str, optional
        日付文字列のフォーマット。デフォルトは "%Y-%m-%d"。

    Returns
    -------
    List[str]
        抽出された日付文字列のリスト。
    """
    try:
        target_date = datetime.strptime(target_date_str, date_format).date()
    except ValueError:
        print(
            f"エラー: 基準日 '{target_date_str}' のフォーマットが '{date_format}' と一致しません。"
        )
        return []

    # 期間の開始日を計算 (基準日の(months_around)ヶ月前の月の初日)
    start_date_calc = target_date - relativedelta(months=months_around)
    start_of_period = start_date_calc.replace(day=1)

    # 期間の終了日を計算 (基準日の(months_around)ヶ月後の月の末日)
    end_date_calc = target_date + relativedelta(months=months_around)
    # (months_around+1)ヶ月後の月の初日を求め、1日引くことで正確な月末日を計算
    next_month_after_end = end_date_calc.replace(day=1) + relativedelta(months=1)
    end_of_period = next_month_after_end - timedelta(days=1)

    print(f"抽出期間: {start_of_period} から {end_of_period} まで")

    extracted_dates = []
    for date_str in date_list:
        if "_" in date_str:
            date_str = date_str.replace("_", "-")
        try:
            current_date = datetime.strptime(date_str, date_format).date()
            if start_of_period <= current_date <= end_of_period:
                extracted_dates.append(date_str)
        except ValueError:
            # 不正なフォーマットのデータは警告を表示してスキップ
            print(f"警告: '{date_str}' は不正なフォーマットのためスキップします。")
            continue

    return extracted_dates
