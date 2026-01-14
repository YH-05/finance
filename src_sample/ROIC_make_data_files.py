"""
ROIC_make_data_files.py

2025/4/14
"""

import warnings
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns

warnings.simplefilter("ignore")
# =====================================================================
ROOT_DIR = Path().cwd().parent
DATA_DIR = ROOT_DIR / "data_analysis#02"


# =====================================================================
def clipped_mean(series: pd.Series, percentile: float):
    """
    pandasをグルーピングし, 指定したpd.seriesのパーセンタイル点以上・以下を
    クリッピング(winsorize)する関数。

    Parameters
    ----------
    series : pd.Series
        計算対象のデータシリーズ。
    percentile : float
        クリッピングするパーセンタイル（例: 5.0）。

    Returns
    -------
    float
        クリッピング後の平均値。
    """
    lower_bound = np.percentile(series, percentile)
    upper_bound = np.percentile(series, 100 - percentile)
    return np.clip(series, lower_bound, upper_bound).mean()


# =====================================================================
def clipped_std(series: pd.Series, percentile: float):
    """
    pandas Seriesを受け取り、指定したパーセンタイル点以上・以下を
    クリッピング(winsorize)した後の標準偏差を計算する関数。
    NaN値は計算前に除外される。

    Parameters
    ----------
    series : pd.Series
        計算対象のデータシリーズ。
    percentile : float
        クリッピングするパーセンタイル（例: 5.0）。

    Returns
    -------
    float
        クリッピング後の標準偏差。データが2つ未満の場合はNaN。
    """
    # NaNでない値のみを対象とする
    valid_series = series.dropna()

    # 有効なデータが2つ未満の場合、標準偏差は計算できないためNaNを返す
    if len(valid_series) < 2:
        return np.nan

    lower_bound = np.percentile(valid_series, percentile)
    upper_bound = np.percentile(valid_series, 100 - percentile)
    # np.clipを使用してクリッピング
    clipped_series = np.clip(valid_series, lower_bound, upper_bound)
    # クリッピングされたデータの標準偏差を計算して返す
    return clipped_series.std()


# =====================================================================
def get_constituents_weight_from_factset(file_list: List[Path | str]):
    """
    ExcelでダウンロードしたFactset元データを加工する関数。
    parquetファイルに出力する。

    Parameters
    ----------
    file_list : List[Path | str]
        FactsetデータのExcelファイルパスのリスト。
    """

    # ----- Index constituents -----
    loaded_data = []
    for f in file_list:
        df = (
            pd.read_excel(f, header=5)
            .replace(
                {
                    100: np.nan,
                    "-": np.nan,
                    "MSCI Kokusai Index (World ex Japan)": np.nan,
                }
            )
            .dropna(subset=["Symbol", "Name"])
            .set_index(keys=["Name", "Symbol"])
        )
        loaded_data.append(df)

    dfs = []
    for df in loaded_data:
        df.columns = [pd.to_datetime(s.replace(" Weight", "")) for s in df.columns]
        df = df.reset_index()
        df = pd.melt(
            df,
            id_vars=["Name", "Symbol"],
            value_vars=df.columns.tolist()[2:],
            value_name="weight",
        )
        dfs.append(df)
    del loaded_data

    df = (
        pd.concat(dfs, axis=0, ignore_index=True)
        .assign(weight=lambda df: df["weight"] / 100)
        .rename(columns={"variable": "date"})
        .drop_duplicates(ignore_index=True)
    )
    # export
    output_path = DATA_DIR / "MSCI KOKUSAI_weight and full id.parquet"
    df.to_parquet(output_path)
    print(f"{output_path} has been exported.")


# =====================================================================
def get_id_and_return_from_factset(excel_file: str | Path):
    """
    ExcelでダウンロードしたFactset元データを加工する関数。
    security_id, ROICとPriceのタブがあることが前提。

    Parameters
    ----------
    excel_file : str | Path
        FactsetデータのExcelファイルパス。
    """
    # ----- Security ID -----
    df_id = (
        pd.read_excel(excel_file, sheet_name="security_id", header=8)
        .drop(columns=["Unnamed: 0", "Unnamed: 1"], axis=1)
        .rename(columns={"発表頻度フラグ": "freq"})
    )
    # export
    df_id.to_parquet(DATA_DIR / "MSCI KOKUSAI_ID.parquet")
    print(f"{DATA_DIR / 'MSCI KOKUSAI_ID.parquet'} has been exported.")

    # ----- ROIC data -----
    df_roic = (
        pd.read_excel(excel_file, sheet_name="ROIC", header=8)
        .drop(columns=["Unnamed: 0", "Unnamed: 1", "発表頻度フラグ"], axis=1)
        .set_index("Identifier")
        .rename(columns=lambda col: pd.to_datetime(col))
        .T.reset_index()
        .rename(columns={"index": "date"})
        .melt(id_vars=["date"], var_name="Identifier", value_name="ROIC")
    )

    # ----- price -> return -----
    df_price = (
        pd.read_excel(excel_file, sheet_name="Price", header=8)
        .drop(columns=["Unnamed: 0", "Unnamed: 1", "発表頻度フラグ"], axis=1)
        .set_index(keys=["Identifier"])
    )
    df_price.columns = [pd.to_datetime(s) for s in df_price.columns]
    df_price = df_price.T
    df_price.index.name = "date"
    df_price.reset_index(inplace=True)
    # export
    df_price.to_parquet(DATA_DIR / "MSCI KOKUSAI_Price.parquet")
    print(f"{DATA_DIR / 'MSCI KOKUSAI_Price.parquet'} has been exported.")

    df_price.set_index("date", inplace=True)

    # ----- calculate monthly return -----
    df_monthly_return = (
        pd.DataFrame(df_price.pct_change()).dropna(how="all").reset_index()
    )
    df_monthly_return = pd.melt(
        df_monthly_return,
        id_vars=["date"],
        value_vars=df_monthly_return.columns[1:],
        var_name="Identifier",
        value_name="Rtn_M",
    ).assign(Rtn_Ann_M=lambda df: df["Rtn_M"] * 12)  # 月次リターンの年率換算を追加

    # ----- calculate 3M return -----
    df_3m_return = pd.DataFrame(df_price.pct_change(3)).dropna(how="all").reset_index()
    df_3m_return = pd.melt(
        df_3m_return,
        id_vars=["date"],
        value_vars=df_3m_return.columns[1:],
        var_name="Identifier",
        value_name="Rtn_3M",
    ).assign(Rtn_Ann_3M=lambda df: df["Rtn_3M"] * 4)  # 年率換算を追加

    # ----- calculate 6M return -----
    df_6m_return = pd.DataFrame(df_price.pct_change(6)).dropna(how="all").reset_index()
    df_6m_return = pd.melt(
        df_6m_return,
        id_vars=["date"],
        value_vars=df_6m_return.columns[1:],
        var_name="Identifier",
        value_name="Rtn_6M",
    ).assign(Rtn_Ann_6M=lambda df: df["Rtn_6M"] * 2)  # 年率換算を追加

    # ----- calculate 1Y return -----
    df_1y_return = pd.DataFrame(df_price.pct_change(12)).dropna(how="all").reset_index()
    df_1y_return = pd.melt(
        df_1y_return,
        id_vars=["date"],
        value_vars=df_1y_return.columns[1:],
        var_name="Identifier",
        value_name="Rtn_1Y",
    ).assign(Rtn_Ann_1Y=lambda df: df["Rtn_1Y"])  # 年率換算を追加

    # ----- calculate 3Y return -----
    df_3y_return = (
        pd.DataFrame(df_price.pct_change(12 * 3)).dropna(how="all").reset_index()
    )
    df_3y_return = pd.melt(
        df_3y_return,
        id_vars=["date"],
        value_vars=df_3y_return.columns[1:],
        var_name="Identifier",
        value_name="Rtn_3Y",
    ).assign(Rtn_Ann_3Y=lambda df: df["Rtn_3Y"] / 3)  # 年率換算を追加

    # ----- calculate 5Y return -----
    df_5y_return = (
        pd.DataFrame(df_price.pct_change(12 * 5)).dropna(how="all").reset_index()
    )
    df_5y_return = pd.melt(
        df_5y_return,
        id_vars=["date"],
        value_vars=df_5y_return.columns[1:],
        var_name="Identifier",
        value_name="Rtn_5Y",
    ).assign(Rtn_Ann_5Y=lambda df: df["Rtn_5Y"] / 5)  # 年率換算を追加

    # ----- merge -----
    dfs_to_merge = [
        df_monthly_return,
        df_3m_return,
        df_6m_return,
        df_1y_return,
        df_3y_return,
        df_5y_return,
    ]
    for i, _df in enumerate(dfs_to_merge):
        if i == 0:
            df_return = df_monthly_return
        else:
            df_return = pd.merge(df_return, _df, on=["date", "Identifier"], how="left")
    df_return_and_roic = pd.merge(
        df_return, df_roic, on=["date", "Identifier"], how="left"
    )

    df_return_and_roic.to_parquet(DATA_DIR / "MSCI KOKUSAI_ROIC.parquet")
    print(f"{DATA_DIR / 'MSCI KOKUSAI_ROIC.parquet'} has been exported.")


# =====================================================================
def merge_weight_and_roic() -> pd.DataFrame:
    """
    インデックス構成銘柄をID別にsedolとcusipに分け, ROICデータとマージする。
    構成銘柄データとROICデータとのマージのためにこの処理が必要。
    ROICデータは銘柄IDをIdentifer, SEDOL, CUSIP, ISINで取得しているが,
    構成銘柄データはSymbolというカラムで, SEDOL OR CUSIPとなっている(区別用のフラグはない)。

    Returns
    -------
    pd.DataFrame
        マージされたデータフレーム。
    """

    df_return_and_roic = pd.merge(
        pd.read_parquet(DATA_DIR / "MSCI KOKUSAI_ROIC.parquet"),
        pd.read_parquet(DATA_DIR / "MSCI KOKUSAI_ID.parquet"),
        how="left",
        on=["Identifier"],
    ).sort_values("date")

    df_return_and_roic_filled = (
        df_return_and_roic[["date", "Identifier", "ROIC"]]
        .sort_values(["Identifier", "date"])
        .groupby("Identifier")
        .apply(lambda group: group.ffill())
        .reset_index(drop=True)
    )

    df_return_and_roic_filled = (
        pd.merge(
            df_return_and_roic,
            df_return_and_roic_filled,
            on=["date", "Identifier"],
            suffixes=("", "_filled"),
        )
        .drop(columns=["ROIC"], axis=1)
        .rename(columns={"ROIC_filled": "ROIC"})
        .assign(
            SEDOL=lambda row: row["SEDOL"].str[:6],
            CUSIP=lambda row: row["CUSIP"].str[:8],
            ym=lambda row: row["date"].dt.year.astype(str)
            + row["date"].dt.month.astype(str).str.zfill(2),
        )
    )

    df_weight = (
        pd.read_parquet(DATA_DIR / "MSCI KOKUSAI_weight and full id.parquet")
        .assign(
            ym=lambda row: row["date"].dt.year.astype(str)
            + row["date"].dt.month.astype(str).str.zfill(2)
        )
        .drop(columns=["date"])
    )
    df_weight_sedol = (
        pd.merge(
            df_weight.loc[df_weight["Symbol"].str.len() == 6].rename(
                columns={"Symbol": "SEDOL"}
            ),
            df_return_and_roic_filled.drop(columns=["CUSIP", "ISIN"]),
            on=["ym", "SEDOL"],
            how="left",
        )
        .dropna(subset=["weight"])
        .rename(columns={"SEDOL": "Symbol"})
        .reset_index(drop=True)
    )
    df_weight_cusip = (
        pd.merge(
            df_weight.loc[df_weight["Symbol"].str.len() == 8].rename(
                columns={"Symbol": "CUSIP"}
            ),
            df_return_and_roic_filled.drop(columns=["SEDOL", "ISIN"]),
            on=["ym", "CUSIP"],
            how="left",
        )
        .dropna(subset=["weight"])
        .rename(columns={"CUSIP": "Symbol"})
        .reset_index(drop=True)
    )

    df = (
        (
            pd.concat([df_weight_sedol, df_weight_cusip], axis=0, ignore_index=True)
            .dropna(subset=["date"])
            .assign(
                Quarter=lambda row: row["date"].dt.year.astype(int).astype(str)
                + "Q"
                + row["date"].dt.quarter.astype(int).astype(str)
            )
            .rename(
                columns={
                    "SECTOR": "GICS_SECTOR",
                    "INDUSTRY": "GICS_INDUSTRY",
                    "INDGRP": "GICS_INDGRP",
                    "SUBIND": "GICS_SUBIND",
                }
            )
            .reindex(
                columns=[
                    "date",
                    "ym",
                    "Quarter",
                    "Name",
                    "Symbol",
                    "Identifier",
                    "freq",
                    "GICS_SECTOR",
                    "GICS_INDUSTRY",
                    "GICS_INDGRP",
                    "GICS_SUBIND",
                    "weight",
                    "Rtn_M",
                    "Rtn_Ann_M",
                    "Rtn_3M",
                    "Rtn_Ann_3M",
                    "Rtn_6M",
                    "Rtn_Ann_6M",
                    "Rtn_1Y",
                    "Rtn_Ann_1Y",
                    "Rtn_3Y",
                    "Rtn_Ann_3Y",
                    "Rtn_5Y",
                    "Rtn_Ann_5Y",
                    "ROIC",
                ]
            )
        )
        .dropna(subset=["date"])
        .sort_values(["date", "Symbol"], ignore_index=True)
    )

    return df


# =====================================================================
def add_forward_return_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    ヒストリカルリターンからForwardリターンのカラムを追加する。

    Parameters
    ----------
    df : pd.DataFrame
        リターンデータを含むデータフレーム。

    Returns
    -------
    pd.DataFrame
        Forwardリターンが追加されたデータフレーム。
    """

    # --- mothly return ---
    if "Rtn_M" in df.columns:
        df["Rtn_1MForward"] = df.groupby("Symbol")["Rtn_M"].shift(-1)
    if "Rtn_Ann_M" in df.columns:
        df["Rtn_Ann_1MForward"] = df.groupby("Symbol")["Rtn_Ann_M"].shift(-1)

    # --- 3M return ---
    if "Rtn_3M" in df.columns:
        df["Rtn_3MForward"] = df.groupby("Symbol")["Rtn_3M"].shift(-3)
    if "Rtn_Ann_3M" in df.columns:
        df["Rtn_Ann_3MForward"] = df.groupby("Symbol")["Rtn_Ann_3M"].shift(-3)

    # --- 6M return ---
    if "Rtn_6M" in df.columns:
        df["Rtn_6MForward"] = df.groupby("Symbol")["Rtn_6M"].shift(-6)
    if "Rtn_Ann_6M" in df.columns:
        df["Rtn_Ann_6MForward"] = df.groupby("Symbol")["Rtn_Ann_6M"].shift(-6)

    # --- 1Y return ---
    if "Rtn_1Y" in df.columns:
        df["Rtn_1YForward"] = df.groupby("Symbol")["Rtn_1Y"].shift(-12)
    if "Rtn_Ann_1Y" in df.columns:
        df["Rtn_Ann_1YForward"] = df.groupby("Symbol")["Rtn_Ann_1Y"].shift(-12)

    # --- 3Y return ---
    if "Rtn_3Y" in df.columns:
        df["Rtn_3YForward"] = df.groupby("Symbol")["Rtn_3Y"].shift(-12 * 3)
    if "Rtn_Ann_3Y" in df.columns:
        df["Rtn_Ann_3YForward"] = df.groupby("Symbol")["Rtn_Ann_3Y"].shift(-12 * 3)

    # --- 5Y return ---
    if "Rtn_5Y" in df.columns:
        df["Rtn_5YForward"] = df.groupby("Symbol")["Rtn_5Y"].shift(-12 * 5)
    if "Rtn_Ann_5Y" in df.columns:
        df["Rtn_Ann_5YForward"] = df.groupby("Symbol")["Rtn_Ann_5Y"].shift(-12 * 5)

    return df


# =====================================================================
def add_past_and_forward_roic_cols_quarter(
    df: pd.DataFrame,
    quarter_period: int = 20,
) -> pd.DataFrame:
    """
    過去 or 将来のROICの値を入れるカラムを追加する。

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム。
    quarter_period : int, default 20
        期間（四半期数）。

    Returns
    -------
    pd.DataFrame
        ROICカラムが追加されたデータフレーム。
    """
    df.sort_values(["date", "Symbol"], inplace=True, ignore_index=True)
    for n in range(1, quarter_period + 1):
        df[f"ROIC_{n}QAgo"] = df.groupby(["Symbol"])["ROIC"].shift(n * 3)
        df[f"ROIC_{n}QForward"] = df.groupby(["Symbol"])["ROIC"].shift(-n * 3)

    return df


# =====================================================================
def add_shifted_roic_cols_month(
    df: pd.DataFrame,
    shift_direction: str = "both",
    month_period: int = 60,
) -> pd.DataFrame:
    """
    過去 or 将来のROICの値を入れるカラムを追加する。

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム。
    shift_direction : str, default "both"
        シフトの方向。
        - "both" : 過去と将来のROICを追加
        - "forward" : 将来のROICを追加
        - "past" : 過去のROICを追加
    month_period : int, default 60
        期間（月数）。

    Returns
    -------
    pd.DataFrame
        ROICカラムが追加されたデータフレーム。
    """
    df.sort_values(["date", "Symbol"], inplace=True, ignore_index=True)
    for n in range(1, month_period + 1):
        if shift_direction == "both":
            df[f"ROIC_{n}MAgo"] = df.groupby(["Symbol"])["ROIC"].shift(n)
            df[f"ROIC_{n}MForward"] = df.groupby(["Symbol"])["ROIC"].shift(-n)
        elif shift_direction == "forward":
            df[f"ROIC_{n}MForward"] = df.groupby(["Symbol"])["ROIC"].shift(-n)
        elif shift_direction == "past":
            df[f"ROIC_{n}MAgo"] = df.groupby(["Symbol"])["ROIC"].shift(n)

    return df


# =====================================================================
def add_roic_rank_cols(df: pd.DataFrame, freq_suffix: str) -> pd.DataFrame:
    """
    各時点のROICのランクカラムを追加する。

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム。
    freq_suffix : str
        頻度のサフィックス（例: "Q", "M"）。

    Returns
    -------
    pd.DataFrame
        ランクカラムが追加されたデータフレーム。
    """
    roic_cols = [
        col
        for col in df.columns
        if (col == "ROIC")
        or (
            ("ROIC" in col)
            and ((f"{freq_suffix}Ago" in col) or (f"{freq_suffix}Forward" in col))
        )
    ]
    for col in roic_cols:
        if col == "ROIC":
            target_col = "ROIC_Rank"
        else:
            target_col = f"{col.replace('_', '_Rank_')}"
        df[target_col] = (
            df.groupby("date")[col]
            .transform(
                lambda x: (
                    (pd.qcut(x, q=5, labels=False, duplicates="drop") + 1)
                    if x.notna().sum() >= 5
                    else pd.Series(np.nan, index=x.index)
                )
            )
            .replace(
                {
                    1.0: "rank5",
                    2.0: "rank4",
                    3.0: "rank3",
                    4.0: "rank2",
                    5.0: "rank1",
                }
            )
        )

    return df


# =====================================================================
def calculate_roic_slope_quarter(row, quarter_period: int = 20):
    """
    将来一定期間内におけるROICの傾きを計算する関数. 欠損値は無視.

    Parameters
    ----------
    row : pd.Series
        データ行。
    quarter_period : int, default 20
        期間（四半期数）。

    Returns
    -------
    float
        ROICの傾き。計算できない場合はNaN。
    """
    roic_cols = ["ROIC"] + [f"ROIC_{s}QForward" for s in range(1, quarter_period)]

    try:
        y_values = row[roic_cols].values.astype(float)
    except KeyError:
        # rowにroic_cols_existのいずれかのカラムが存在しない場合のエラーハンドリング
        print(f"警告: 必要なROICカラムの一部が見つかりません。行: \n{row}")
        return np.nan
    except ValueError:
        # floatに変換できない値が含まれている場合
        print(f"警告: ROICデータに数値変換できない値が含まれています。行: \n{row}")
        # 問題のある値をNaNに置き換えて続行を試みる
        y_values = pd.to_numeric(row[roic_cols], errors="coerce").values

    # 対応する時間 (x軸の値: 0, 1, 2, ..., quarter_period-1) を生成
    # roic_cols の順序に従ってxの値を決定
    x_values_map = {
        col: (
            int(col.split("_")[1].replace("QForward", "")) if "QForward" in col else 0
        )
        for col in roic_cols
    }
    x_values = np.array([x_values_map[col] for col in roic_cols])

    # 欠損値 (NaN) を持つデータ点を除外
    valid_indices = ~np.isnan(y_values)
    y_valid = y_values[valid_indices]
    x_valid = x_values[valid_indices]

    # 線形回帰を実行するには、少なくとも2つの有効なデータ点が必要
    if len(y_valid) >= 2:
        # numpy.polyfit を使用して線形回帰 (deg=1 は線形)
        # 戻り値: [傾き, 切片]
        slope, intercept = np.polyfit(x_valid, y_valid, 1)
        return slope
    else:
        # 有効なデータ点が2つ未満の場合は、傾きを計算できないため NaN を返す
        return np.nan


# =====================================================================
def calculate_roic_slope_month(row, month_period: int = 60):
    """
    将来一定期間内におけるROICの傾きを計算する関数. 欠損値は無視.

    Parameters
    ----------
    row : pd.Series
        データ行。
    month_period : int, default 60
        期間（月数）。

    Returns
    -------
    float
        ROICの傾き。計算できない場合はNaN。
    """
    roic_cols = ["ROIC"] + [f"ROIC_{s}MForward" for s in range(1, month_period + 1)]

    try:
        y_values = row[roic_cols].values.astype(float)
    except KeyError:
        # rowにroic_cols_existのいずれかのカラムが存在しない場合のエラーハンドリング
        print(f"警告: 必要なROICカラムの一部が見つかりません。行: \n{row}")
        return np.nan
    except ValueError:
        # floatに変換できない値が含まれている場合
        print(f"警告: ROICデータに数値変換できない値が含まれています。行: \n{row}")
        # 問題のある値をNaNに置き換えて続行を試みる
        y_values = pd.to_numeric(row[roic_cols], errors="coerce").values

    # 対応する時間 (x軸の値: 0, 1, 2, ..., month_period-1) を生成
    # roic_cols の順序に従ってxの値を決定
    x_values_map = {
        col: (
            int(col.split("_")[1].replace("MForward", "")) if "MForward" in col else 0
        )
        for col in roic_cols
    }
    x_values = np.array([x_values_map[col] for col in roic_cols])

    # 欠損値 (NaN) を持つデータ点を除外
    valid_indices = ~np.isnan(y_values)
    y_valid = y_values[valid_indices]
    x_valid = x_values[valid_indices]

    # 線形回帰を実行するには、少なくとも2つの有効なデータ点が必要
    if len(y_valid) >= 2:
        # numpy.polyfit を使用して線形回帰 (deg=1 は線形)
        # 戻り値: [傾き, 切片]
        slope, intercept = np.polyfit(x_valid, y_valid, 1)
        return slope
    else:
        # 有効なデータ点が2つ未満の場合は、傾きを計算できないため NaN を返す
        return np.nan


# =====================================================================
# [old version]
# make ROIC_Label column
# def assign_roic_label(row, quarter_period: int = 20, judge_by_slope: bool = True):
#     ranks = [
#         row[f"ROIC_Rank{'_' + str(i) + 'QForward' if i > 0 else ''}"] for i in range(20)
#     ]
#     if judge_by_slope:
#         move_to_high_condition = (row[f"ROIC_Slope_{quarter_period}QForward"] > 0) and (
#             row["ROIC_Rank"] in ["rank1", "rank2"]
#             and row[f"ROIC_Rank_{quarter_period-1}QForward"]
#             in [
#                 "rank4",
#                 "rank5",
#             ]
#         )
#         drop_to_low_condition = (row[f"ROIC_Slope_{quarter_period}QForward"] < 0) and (
#             row["ROIC_Rank"] in ["rank4", "rank5"]
#             and row[f"ROIC_Rank_{quarter_period-1}QForward"]
#             in [
#                 "rank1",
#                 "rank2",
#             ]
#         )
#     else:
#         move_to_high_condition = (row["ROIC_Rank"] in ["rank1", "rank2"]) and (
#             row[f"ROIC_Rank_{quarter_period-1}QForward"]
#             in [
#                 "rank4",
#                 "rank5",
#             ]
#         )
#         drop_to_low_condition = row["ROIC_Rank"] in ["rank4", "rank5"] and row[
#             f"ROIC_Rank_{quarter_period-1}QForward"
#         ] in [
#             "rank1",
#             "rank2",
#         ]

#     if all(rank in ["rank1", "rank2"] for rank in ranks):
#         return "remain high"
#     elif all(rank in ["rank4", "rank5"] for rank in ranks):
#         return "remain low"
#     elif move_to_high_condition:
#         return "move to high"
#     elif drop_to_low_condition:
#         return "drop to low"
#     else:
#         return "others"


# =====================================================================
"""
# make ROIC_Label column
def assign_roic_label(row, quarter_period: int = 20, judge_by_slope: bool = True):
    '''
    Assigns a label based on ROIC rank trajectory over a future period.

    Labels:
    - "remain high": All ranks in the period are rank1 or rank2.
    - "remain low": All ranks in the period are rank4 or rank5.
    - "move to high": Starts high (rank1/2), ends low (rank4/5), optional slope check.
    - "drop to low": Starts low (rank4/5), ends high (rank1/2), optional slope check.
    - "others": None of the above patterns match, AND all ranks in the period are present.
    - np.nan: If any rank within the period is missing (NaN).
    '''
    # 1. Get all ranks for the period, handling missing columns/values safely
    ranks = []
    for i in range(quarter_period):  # 0, 1, ..., quarter_period - 1
        # Construct the column name for the i-th quarter forward rank
        col_name = "ROIC_Rank" if i == 0 else f"ROIC_Rank_{i}QForward"
        # Use .get() to safely retrieve the value, defaulting to np.nan if column missing
        ranks.append(row.get(col_name, np.nan))

    # 2. Check if *any* rank in the period is missing (NaN)
    any_rank_missing = any(pd.isna(r) for r in ranks)

    # 3. Check "remain" conditions - requires *all* ranks to be present and match
    if not any_rank_missing:  # Only check if all ranks are available
        if all(rank in ["rank1", "rank2"] for rank in ranks):
            return "remain high"
        if all(rank in ["rank4", "rank5"] for rank in ranks):
            return "remain low"
    # If any rank was missing, "remain" conditions cannot be met

    # 4. Check "move/drop" conditions - requires start and end ranks (and maybe slope)
    current_rank = ranks[0]  # Rank at the start of the period (time 0)
    final_rank = ranks[quarter_period - 1]  # Rank at the end of the period
    move_to_high_condition = False
    drop_to_low_condition = False

    # Only evaluate move/drop if start and end ranks are available
    if not pd.isna(current_rank) and not pd.isna(final_rank):
        if judge_by_slope:
            slope_col = f"ROIC_Slope_{quarter_period}QForward"
            slope = row.get(slope_col, np.nan)  # Safely get the pre-calculated slope
            # Only evaluate if slope is also available and valid
            if not pd.isna(slope):
                # Condition: Positive slope, starts high, ends low
                move_to_high_condition = (
                    (slope > 0)
                    and (current_rank in ["rank1", "rank2"])
                    and (final_rank in ["rank4", "rank5"])
                )
                # Condition: Negative slope, starts low, ends high
                drop_to_low_condition = (
                    (slope < 0)
                    and (current_rank in ["rank4", "rank5"])
                    and (final_rank in ["rank1", "rank2"])
                )
        else:  # Logic without using slope
            # Condition: Starts high, ends low
            move_to_high_condition = (current_rank in ["rank1", "rank2"]) and (
                final_rank in ["rank4", "rank5"]
            )
            # Condition: Starts low, ends high
            drop_to_low_condition = (current_rank in ["rank4", "rank5"]) and (
                final_rank in ["rank1", "rank2"]
            )

    # Apply move/drop conditions if met
    if move_to_high_condition:
        return "move to high"
    if drop_to_low_condition:
        return "drop to low"

    # 5. Final classification: "others" or NaN
    # We reach here if none of the specific "remain", "move", or "drop" conditions were met.
    if not any_rank_missing:
        # If all ranks were present but no specific pattern matched, classify as "others".
        return "others"
    else:
        # If *any* rank was missing during the period, return NaN.
        return np.nan

"""


# =====================================================================
# make ROIC_Label column
def test_assign_roic_label(
    row, freq: str, year_period: int = 5, judge_by_slope: bool = True
):
    """
    ROICのランク推移に基づいてラベルを割り当てる。

    Parameters
    ----------
    row : pd.Series
        データ行。
    freq : str
        データの頻度 ("annual" または "monthly")。
    year_period : int, default 5
        期間（年数）。
    judge_by_slope : bool, default True
        傾きによる判定を行うかどうか。

    Returns
    -------
    str or np.nan
        割り当てられたラベル。

    Notes
    -----
    Labels:
    - "remain high": All ranks in the period are rank1 or rank2.
    - "remain low": All ranks in the period are rank4 or rank5.
    - "move to high": Starts low (rank4/5), ends high (rank1/2), optional slope check.
    - "drop to low": Starts high (rank1/2), ends low (rank4/5), optional slope check.
    - "others": None of the above patterns match, AND all ranks in the period are present.
    - np.nan: If any rank within the period is missing (NaN).

    Which ROIC rank to use?
        - ROIC_Rank_1MForward       + 1month
        - ROIC_Rank_12MForward      + 1year
        - ROIC_Rank_24MForward      + 2years
        - ROIC_Rank_36MForward      + 3years    (year_period=3)
        - ROIC_Rank_48MForward      + 4years
        - ROIC_Rank_60MForward      + 5years    (year_period=5)
    """
    # 1. Get all ranks for the period, handling missing columns/values safely
    if freq == "annual":
        cols = ["ROIC_Rank_1MForward"] + [
            f"ROIC_Rank_{month}MForward"
            for month in range(12, 12 * (year_period + 1), 12)
        ]
    elif freq == "monthly":
        cols = [
            f"ROIC_Rank_{month}MForward" for month in range(1, 12 * (year_period) + 1)
        ]
    ranks = []
    for col_name in cols:
        ranks.append(row.get(col_name, np.nan))

    # 2. Check if *any* rank in the period is missing (NaN)
    any_rank_missing = any(pd.isna(r) for r in ranks)

    # 3. Check "remain" conditions - requires *all* ranks to be present and match
    if not any_rank_missing:  # Only check if all ranks are available
        if all(rank in ["rank1", "rank2"] for rank in ranks):
            return "remain high"
        if all(rank in ["rank4", "rank5"] for rank in ranks):
            return "remain low"
    # If any rank was missing, "remain" conditions cannot be met

    # 4. Check "move/drop" conditions - requires start and end ranks (and maybe slope)
    current_rank = ranks[0]  # Rank at the start of the period (time 0)
    final_rank = ranks[-1]  # Rank at the end of the period
    move_to_high_condition = False
    drop_to_low_condition = False

    # Only evaluate move/drop if start and end ranks are available
    if not pd.isna(current_rank) and not pd.isna(final_rank):
        if judge_by_slope:
            slope_col = f"ROIC_Slope_{int(year_period*12)}MForward"
            slope = row.get(slope_col, np.nan)  # Safely get the pre-calculated slope
            # Only evaluate if slope is also available and valid
            if not pd.isna(slope):
                # Condition: Positive slope, starts high, ends low
                drop_to_low_condition = (
                    (slope < 0)
                    and (current_rank in ["rank1", "rank2", "rank3"])
                    and (final_rank in ["rank4", "rank5"])
                )
                # Condition: Negative slope, starts low, ends high
                move_to_high_condition = (
                    (slope > 0)
                    and (current_rank in ["rank3", "rank4", "rank5"])
                    and (final_rank in ["rank1", "rank2"])
                )
        else:  # Logic without using slope
            # Condition: Starts high, ends low
            drop_to_low_condition = (current_rank in ["rank1", "rank2", "rank3"]) and (
                final_rank in ["rank4", "rank5"]
            )
            # Condition: Starts low, ends high
            move_to_high_condition = (current_rank in ["rank3", "rank4", "rank5"]) and (
                final_rank in ["rank1", "rank2"]
            )

    # Apply move/drop conditions if met
    if move_to_high_condition:
        return "move to high"
    if drop_to_low_condition:
        return "drop to low"

    # 5. Final classification: "others" or NaN
    # We reach here if none of the specific "remain", "move", or "drop" conditions were met.
    if not any_rank_missing:
        # If all ranks were present but no specific pattern matched, classify as "others".
        return "others"
    else:
        # If *any* rank was missing during the period, return NaN.
        return np.nan


# =====================================================================
def make_roic_label_and_performance_table():
    df_return_and_roic = pd.merge(
        pd.read_parquet(DATA_DIR / "MSCI KOKUSAI_ROIC.parquet"),
        pd.read_parquet(DATA_DIR / "MSCI KOKUSAI_ID.parquet"),
        how="left",
        on=["Identifier"],
    )

    # ----- ROICの欠損値を埋める(1時点前の値) -----
    df_return_and_roic_filled = (
        df_return_and_roic[["date", "Identifier", "ROIC"]]
        .sort_values(["Identifier", "date"])
        .groupby("Identifier")
        .apply(lambda group: group.ffill())
        .reset_index(drop=True)
    )
    df_return_and_roic_filled = (
        pd.merge(
            df_return_and_roic,
            df_return_and_roic_filled,
            on=["date", "Identifier"],
            suffixes=("", "_filled"),
        )
        .drop(columns=["ROIC"], axis=1)
        .rename(columns={"ROIC_filled": "ROIC"})
        .assign(
            SEDOL=lambda row: row["SEDOL"].str[:6],
            CUSIP=lambda row: row["CUSIP"].str[:8],
        )
    )

    # weight of index constituents
    df_weight = pd.read_parquet(DATA_DIR / "MSCI KOKUSAI_weight and full id.parquet")
    col_first = [
        "date",
        "Name",
        "Symbol",
        "SEDOL",
        "CUSIP",
        "ISIN",
        "GICS_SECTOR",
        "GICS_INDUSTRY",
    ]
    remain_cols = [col for col in df_weight.columns if col not in col_first]
    df_weight = df_weight[col_first + remain_cols]

    # merge
    df_weight_sedol = pd.merge(
        df_weight.loc[df_weight["Symbol"].str.len() == 6]
        .drop(columns=["SEDOL", "CUSIP", "ISIN"])
        .rename(columns={"Symbol": "SEDOL"}),
        df_return_and_roic_filled.drop(
            columns=[
                "Identifier",
                "CUSIP",
                "ISIN",
                "SECTOR",
                "INDUSTRY",
                "INDGRP",
                "SUBIND",
            ],
            axis=1,
        ),
        how="left",
        on=["date", "SEDOL"],
    ).rename(columns={"SEDOL": "Symbol"})
    df_weight_cusip = pd.merge(
        df_weight.loc[df_weight["Symbol"].str.len() == 8]
        .drop(columns=["SEDOL", "CUSIP", "ISIN"])
        .rename(columns={"Symbol": "CUSIP"}),
        df_return_and_roic_filled.drop(
            columns=[
                "Identifier",
                "SEDOL",
                "ISIN",
                "SECTOR",
                "INDUSTRY",
                "INDGRP",
                "SUBIND",
            ],
            axis=1,
        ),
        how="left",
        on=["date", "CUSIP"],
    ).rename(columns={"CUSIP": "Symbol"})
    df_return_and_roic_filled = (
        pd.concat([df_weight_sedol, df_weight_cusip], axis=0)
        .dropna(subset=["weight", "Rtn_M"], axis=0, how="any")
        .sort_values(["date", "Symbol"], ignore_index=True)
        .assign(
            Quarter=lambda row: row["date"].dt.year.astype(str)
            + "Q"
            + row["date"].dt.quarter.astype(str),
        )
    )

    g_constituents_count = (
        df_weight.groupby("date")["weight"]
        .count()
        .reset_index()
        .rename(columns={"weight": "num_constituents"})
    )

    g = (
        df_return_and_roic_filled.groupby("date")["weight"]
        .agg(["count", "sum"])
        .reset_index()
        .rename(columns={"count": "num_avail_stocks", "sum": "total_weight"})
    )
    missing_roic = (
        df_return_and_roic_filled.groupby("date")["ROIC"]
        .apply(lambda x: x.isna().sum())
        .reset_index()
        .rename(columns={"ROIC": "num_ROIC_missing"})
    )
    g = pd.merge(g_constituents_count, g, on=["date"]).assign(
        cover_ratio=lambda row: row["num_avail_stocks"] / row["num_constituents"]
    )
    g = pd.merge(g, missing_roic, on=["date"]).reindex(
        [
            "date",
            "num_constituents",
            "num_avail_stocks",
            "cover_ratio",
            "total_weight",
            "num_ROIC_missing",
        ],
        axis=1,
    )

    df_return_and_roic_filled.sort_values(["date", "Symbol"], inplace=True)
    # 1month forward return
    df_return_and_roic_filled["Rtn_M_1MForward"] = df_return_and_roic_filled.groupby(
        "Symbol"
    )["Rtn_M"].shift(-1)
    for n in range(1, 21):
        df_return_and_roic_filled[f"ROIC_{n}QAgo"] = df_return_and_roic_filled.groupby(
            "Symbol"
        )["ROIC"].shift(n * 3)
        df_return_and_roic_filled[f"ROIC_{n}QForward"] = (
            df_return_and_roic_filled.groupby("Symbol")["ROIC"].shift(-n * 3)
        )

    # forward ROIC: linear regression
    roic_cols = [
        col
        for col in df_return_and_roic_filled.columns
        if ("ROIC" in col) and "QAgo" not in col and "20QForward" not in col
    ]
    df_roic_lr = df_return_and_roic_filled.loc[
        df_return_and_roic_filled["date"].dt.month.isin([3, 6, 9, 12]),
        ["Quarter", "Symbol"] + roic_cols,
    ].drop_duplicates(ignore_index=True)

    df_roic_lr["ROIC_Slope_20QForward"] = df_roic_lr.apply(
        calculate_roic_slope_quarter, quarter_period=20, axis=1
    )
    df_roic_lr["ROIC_Slope_12QForward"] = df_roic_lr.apply(
        calculate_roic_slope_quarter, quarter_period=12, axis=1
    )

    df_return_and_roic_filled = pd.merge(
        df_return_and_roic_filled,
        df_roic_lr[
            ["Quarter", "Symbol", "ROIC_Slope_12QForward", "ROIC_Slope_20QForward"]
        ],
        on=["Quarter", "Symbol"],
        how="left",
    )

    roic_cols_to_rank = [
        col
        for col in df_return_and_roic_filled.columns
        if (
            ("ROIC" in col)
            and ("QForward" in col)
            and ("Slope" not in col)
            or (col == "ROIC")
        )
    ]

    for col in roic_cols_to_rank:
        target_col = ""
        if col == "ROIC":
            target_col = "ROIC_Rank"
        else:
            target_col = f"{col.replace('_', '_Rank_')}"
        df_return_and_roic_filled[target_col] = (
            df_return_and_roic_filled.groupby("Quarter")[col]
            .transform(
                lambda x: (
                    pd.qcut(x, q=5, labels=False) + 1
                    if x.notna().sum() >= 5
                    else pd.Series(np.nan, index=x.index)
                )
            )
            .replace(
                {1.0: "rank5", 2.0: "rank4", 3.0: "rank3", 4.0: "rank2", 5.0: "rank1"}
            )
        )

    df_eoq = df_return_and_roic_filled.loc[
        df_return_and_roic_filled["date"].dt.month.isin([3, 6, 9, 12])
    ]
    df_eoq["ROIC_Label_12QForward"] = df_return_and_roic_filled.apply(
        assign_roic_label, quarter_period=12, judge_by_slope=False, axis=1
    ).reset_index(drop=True)
    df_eoq["ROIC_Label_20QForward"] = df_return_and_roic_filled.apply(
        assign_roic_label, quarter_period=20, judge_by_slope=False, axis=1
    ).reset_index(drop=True)

    df_return_and_roic_filled = pd.merge(
        df_return_and_roic_filled,
        df_eoq[["Quarter", "Symbol", "ROIC_Label_12QForward", "ROIC_Label_20QForward"]],
        on=["Quarter", "Symbol"],
        how="left",
    )

    df_return_and_roic_filled = df_return_and_roic_filled.reindex(
        columns=[
            "date",
            "Quarter",
            "Name",
            "Symbol",
            "GICS_SECTOR",
            "GICS_INDUSTRY",
            "freq",
            "weight",
            "Rtn_M",
            "Rtn_M_1MForward",
        ]
        + sorted([col for col in df_return_and_roic_filled.columns if "ROIC" in col])
    )

    df_return_and_roic_filled.to_parquet(DATA_DIR / "MSCI KOKUSAI_all data.parquet")


# =====================================================================
# def calculate_clipped_cumulative_return(df, roic_label_col: str, clipping_percent=5):
#     """
#     date, Symbol, Rtn_M_1MForward, roic_label_colカラムを持つデータフレームに対して、
#     date, roic_label_colごとにグループ化し、Rtn_M_1MForwardの平均値を計算する際に、
#     上位と下位をそれぞれ指定されたパーセンテージでクリッピングし、その平均月次リターンを累積する関数。

#     Args:
#         df (pd.DataFrame): 入力データフレーム
#         clipping_percent (int, optional): クリッピングするパーセンテージ。デフォルトは5。
#     """

#     def clipped_mean(series):
#         lower_bound = np.percentile(series, clipping_percent)
#         upper_bound = np.percentile(series, 100 - clipping_percent)
#         clipped_series = np.clip(series, lower_bound, upper_bound)
#         return clipped_series.mean()

#     # dateとROIC_Label_12QForwardでグループ化し、クリッピングした平均値を計算
#     grouped = pd.DataFrame(
#         df.groupby(["date", roic_label_col])["Rtn_M_1MForward"].apply(clipped_mean)
#     ).reset_index()
#     # df_mean_return = pd.pivot(
#     #     grouped, index="date", columns=roic_label_col, values="Rtn_M_1MForward"
#     # )

#     # グループ化された平均月次リターンを累積
#     def calculate_cumulative(series):
#         cumulative_returns = (1 + series).cumprod() - 1
#         cumulative_returns = cumulative_returns / cumulative_returns.iloc[0]
#         return cumulative_returns

#     # グループ化された平均月次リターンを累積
#     cumulative_returns = df_mean_return.groupby(roic_label_col).apply(
#         calculate_cumulative
#     )
#     # cumulative_returns = pd.DataFrame()

#     return df_mean_return, cumulative_returns


# =====================================================================
def calculate_cumulative_return(
    df,
    roic_label_col: str,
    return_col: str,
    start_date: str,
    end_date: str = None,
    percentile=5,
):
    """
    グループ化してクリッピングした平均値を計算し、累積リターンを求める関数。

    Parameters:
        df (pd.DataFrame): 入力データフレーム
        roic_label_col (str): グループ化に使用するROICラベルのカラム名
        return_col (str): 累積リターンを計算するためのカラム名
        percentile (int): クリッピングに使用するパーセンタイル値（デフォルトは5）

    Returns:
        pd.DataFrame: 累積リターンのデータフレーム
    """

    grouped = (
        df.groupby(["date", roic_label_col])[return_col]
        .apply(clipped_mean, percentile=percentile)
        .reset_index()
    )

    df_mean_return = pd.pivot(
        grouped, index="date", columns=roic_label_col, values=return_col
    )
    if end_date is None:
        df_mean_return = df_mean_return.loc[start_date:].dropna(how="any")
    else:
        df_mean_return = df_mean_return.loc[start_date:end_date].dropna(how="any")
    df_cum_return = (1 + df_mean_return).cumprod() - 1
    return df_cum_return - df_cum_return.iloc[0]


# =====================================================================
def plot_roic_label_cum_return(
    df: pd.DataFrame,
    fig_title: str = None,
    show_benchmark: bool = False,
    savefig: bool = False,
    save_path: str | Path = None,
):
    color_setting1 = {
        "drop to low": "tomato",
        "move to high": "deepskyblue",
        "others": "grey",
        "remain high": "blue",
        "remain low": "red",
    }

    plt.figure(figsize=(8, 4), tight_layout=True)
    if fig_title:
        plt.title(fig_title)
    sns.lineplot(
        df,
        x=df.index,
        y="drop to low",
        label="drop to low",
        color=color_setting1["drop to low"],
    )
    sns.lineplot(
        df,
        x=df.index,
        y="move to high",
        label="move to high",
        color=color_setting1["move to high"],
    )
    sns.lineplot(
        df,
        x=df.index,
        y="others",
        label="others",
        color=color_setting1["others"],
    )
    sns.lineplot(
        df,
        x=df.index,
        y="remain low",
        label="remain low",
        color=color_setting1["remain low"],
    )
    sns.lineplot(
        df,
        x=df.index,
        y="remain high",
        label="remain high",
        color=color_setting1["remain high"],
    )
    if show_benchmark and "Index_cum_return" in df.columns:
        sns.lineplot(
            df,
            x=df.index,
            y="Index_cum_return",
            label="MSCI Kokusai",
            color="black",
            marker="o",
            markersize=4,
        )
    plt.ylabel("Cumulative Return")
    plt.legend()
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.grid()

    if savefig and save_path:
        plt.savefig(save_path, dpi=300)
    else:
        plt.show()


# =====================================================================
def performance_color_cells(df: pd.DataFrame, val):
    """
    値に応じて背景色を返す関数。
    0より大きければ緑色の濃淡、0より小さければ赤色の濃淡。
    """
    if val > 0:
        # 緑色のスケール（値が大きいほど濃く）
        intensity = min(1, val / df.abs().max().max())  # 最大値で正規化
        color = f"rgba(0, {255 * (1 - intensity)}, 0, {0.8})"
    elif val < 0:
        # 赤色のスケール（絶対値が大きいほど濃く）
        intensity = min(1, abs(val) / df.abs().max().max())  # 絶対値の最大値で正規化
        color = f"rgba({255 * (1 - intensity)}, 0, 0, {0.8})"
    else:
        color = ""  # 0の場合は色なし
    return f"background-color: {color}"


# =====================================================================
def calculate_winsorized_mean(series):
    """
    Pandas Seriesを受け取り、5パーセンタイルと95パーセンタイルで
    クリッピング（Winsorize）した後の平均値を計算する関数。
    NaN値は計算前に除外される。
    """
    # NaNでない値のみを対象とする
    valid_series = series.dropna()

    # 有効なデータがない、または少なすぎる場合はNaNを返す
    if valid_series.empty or len(valid_series) < 2:  # パーセンタイル計算には最低2点必要
        return np.nan

    # 5パーセンタイルと95パーセンタイルを計算
    q05 = valid_series.quantile(0.05)
    q95 = valid_series.quantile(0.95)

    # clipメソッドを使用して値をクリッピング
    # lower=q05 より小さい値は q05 に、upper=q95 より大きい値は q95 に置き換えられる
    winsorized_series = valid_series.clip(lower=q05, upper=q95)

    # クリッピングされた値の平均値を計算して返す
    return winsorized_series.mean()


# =====================================================================
def plot_period_return(df: pd.DataFrame, period: int, roic_col: str, return_col: str):
    g = pd.pivot(
        df.groupby(["date", roic_col])[return_col]
        .apply(clipped_mean, percentile=5)
        .reset_index(),
        index="date",
        columns=roic_col,
        values=return_col,
    )

    g_long = pd.melt(
        g.reset_index(), id_vars="date", value_vars=g.columns, var_name="ROIC_Label"
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_title("5 years performance(Annualized, %)")
    sns.boxplot(data=g_long, x="value", y="ROIC_Label", ax=ax)
    ax.xaxis.set_major_formatter(
        mtick.PercentFormatter(1.0)
    )  # Set x-axis to percentage format
    ax.set_xlabel("Annualized Return")
    plt.show()


# =====================================================================
"""

def plot_multi_period_return(df: pd.DataFrame, period: int, roic_col: str, return_cols: List[str]):

    fig, axes = plt.subplots(figsize=(12,4), tight_layout=True)
    for i, return_col in enumerate(return_cols):
        g = pd.pivot(
            df.groupby(["date", roic_col])[return_col]
            .apply(clipped_mean, percentile=5)
            .reset_index(),
            index="date",
            columns=roic_col,
            values=return_col,
        )

        g_long = pd.melt(
            g.reset_index(), id_vars="date", value_vars=g.columns, var_name="ROIC_Label"
        )
        ax = axes[i]
        ax.
"""


# =====================================================================
def plot_sankey_diagram(df: pd.DataFrame, roic_label1: str, roic_label2: str):
    df_plot = df[["Symbol", roic_label1, roic_label2]].dropna(how="any").copy()
    sankey_data = (
        df_plot.groupby([roic_label1, roic_label2]).size().reset_index(name="count")
    )
    labels_1m = sorted(df_plot[roic_label1].unique().tolist())
    labels_60m = sorted(df_plot[roic_label2].unique().tolist())
    all_labels = [f"{label}_1M" for label in labels_1m] + [
        f"{label}_60M" for label in labels_60m
    ]

    unique_labels = []
    for label in all_labels:
        if label not in unique_labels:
            unique_labels.append(label)

    label_to_id = {label: i for i, label in enumerate(unique_labels)}
    # リンクのリスト作成
    source_ids = []
    target_ids = []
    values = []
    link_labels = []

    for _, row in sankey_data.iterrows():
        source_label = f"{row[roic_label1]}_1M"
        target_label = f"{row[roic_label2]}_60M"
        count = row["count"]
        # ラベルがマッピングに含まれているか確認
        if source_label in label_to_id and target_label in label_to_id:
            source_ids.append(label_to_id[source_label])
            target_ids.append(label_to_id[target_label])
            values.append(count)
            link_labels.append(f"{count} Symbols")  # 例: "50 Symbols"

    # --- 3. ノードの色分け (オプション) ---
    # 例えば、ランクごとに色を変える
    rank_colors = {
        "rank1": "rgba(31, 119, 180, 0.8)",  # Blue
        "rank2": "rgba(255, 127, 14, 0.8)",  # Orange
        "rank3": "rgba(44, 160, 44, 0.8)",  # Green
        "rank4": "rgba(214, 39, 40, 0.8)",  # Red
        "rank5": "rgba(148, 103, 189, 0.8)",  # Purple
        "NaN": "rgba(127, 127, 127, 0.8)",  # Grey
    }

    node_colors = []
    node_labels_display = []  # 表示用の短いラベル
    for label in unique_labels:
        rank = label.split("_")[0]  # 'rank1_1M' -> 'rank1'
        node_colors.append(
            rank_colors.get(rank, "rgba(127, 127, 127, 0.8)")
        )  # マップにない場合はグレー
        # 表示用ラベル（例: 'rank1 (1M)'）
        period = label.split("_")[1]
        node_labels_display.append(f"{rank} ({period})")

    # --- 4. Plotlyサンキーダイアグラムの描画 ---
    fig = go.Figure(
        data=[
            go.Sankey(
                # ノード定義
                node=dict(
                    pad=20,  # ノード間の垂直方向のギャップ
                    thickness=15,  # ノードの太さ
                    line=dict(color="black", width=0.5),  # ノードの境界線
                    label=node_labels_display,  # ノードに表示されるラベル (例: 'rank1 (1M)')
                    color=node_colors,  # ノードの色
                    # hoverinfo='skip' # ノードのホバー情報を非表示にする場合
                ),
                # リンク (フロー) 定義
                link=dict(
                    source=source_ids,  # SourceノードのIDリスト
                    target=target_ids,  # TargetノードのIDリスト
                    value=values,  # フローの太さ (Symbol数)
                    label=link_labels,  # フローのラベル (マウスオーバーで表示)
                    color="rgba(200, 200, 200, 0.5)",  # フローの色と透明度
                    hovertemplate="From %{source.label} to %{target.label}: %{value} symbols<extra></extra>",  # ホバーテキストのカスタマイズ
                ),
            )
        ]
    )

    # レイアウト設定
    fig.update_layout(
        width=800,
        height=1000,
        title_text="ROIC Rank Transition: 1M Forward vs 60M Forward",
        font=dict(size=12, color="black"),
        paper_bgcolor="white",  # 背景色
        plot_bgcolor="white",
    )

    fig.show()
