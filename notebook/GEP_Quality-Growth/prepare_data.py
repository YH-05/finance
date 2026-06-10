"""
prepare_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd


def invert_high_low_label(df: pd.DataFrame) -> pd.DataFrame:
    """Value と Low Volatility の符号を反転し Low-High に統一する。非破壊的。"""
    df = df.copy()  # 副作用を防ぐ
    value_cols = [c for c in df.columns if "Value" in c]
    vol_cols = [c for c in df.columns if "Low Volatility" in c]

    df[value_cols] = -1 * df[value_cols]
    df.rename(
        columns={
            c: c.replace("Long-Short (High-Low)", "Long-Short (Low-High)")
            for c in value_cols
        },
        inplace=True,
    )
    df[vol_cols] = -1 * df[vol_cols]
    df.rename(
        columns={
            c: c.replace("Long-Short (High-Low)", "Long-Short (Low-High)")
            for c in vol_cols
        },
        inplace=True,
    )
    return df


def get_factor_cum_return(data_path: Path) -> pd.DataFrame:
    """符号反転済みの累積リターン(%)を返す。"""
    df = pd.read_parquet(data_path)
    return invert_high_low_label(df)


def arithmetic_cumret_to_daily(
    data_path: Path,
    drop_all_zero_rows: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    算術累計(日次リターン%の単純累積)から日次リターン(小数)を復元する。
    反転は最後に一度だけ適用する。
    """
    df = pd.read_parquet(data_path).sort_index()
    df = df[~df.index.duplicated(keep="first")]

    daily = df.diff() / 100.0  # 算術累計 → 日次リターン(小数)。反転前の生データで実施
    daily = invert_high_low_label(daily)  # 反転は差分後に一度だけ(線形なので可換)
    daily = daily.iloc[1:]

    if drop_all_zero_rows:
        all_zero = (daily.abs() <= 1e-12).all(axis=1)
        if all_zero.any() and verbose:
            print(f"[情報] 全ゼロ行(非取引日)を {int(all_zero.sum())} 件除去する。")
        daily = daily.loc[~all_zero]

    if verbose:
        print(
            f"[完了] {len(daily)} 行。"
            f" 中央絶対値 {daily.abs().stack().median():.5f}(小数)。"
            f" 期間 {daily.index.min().date()} 〜 {daily.index.max().date()}。"
        )
    return daily
