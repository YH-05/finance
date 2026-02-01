"""
ROIC_make_data_files_ver2.py

ROIC関連のデータファイルを作成する関数群を定義するスクリプト。

"""

import sqlite3
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from dotenv import load_dotenv

warnings.simplefilter("ignore")
load_dotenv()


# =====================================================================
def clipped_mean(series: pd.Series, percentile: float = 5.0):
    """
    pandasをグルーピングし, 指定したpd.seriesのパーセンタイル点以上・以下を
    クリッピング(winsorize)する関数。

    Parameters
    ----------
    series : pd.Series
        計算対象のデータシリーズ。
    percentile : float, default 5.0
        クリッピングするパーセンタイル。

    Returns
    -------
    float
        クリッピング後の平均値。
    """
    lower_bound = np.percentile(series, percentile)
    upper_bound = np.percentile(series, 100 - percentile)
    return np.clip(series, lower_bound, upper_bound).mean()


# =====================================================================
def clipped_std(series: pd.Series, percentile: float = 5.0):
    """
    pandas Seriesを受け取り、指定したパーセンタイル点以上・以下を
    クリッピング(winsorize)した後の標準偏差を計算する関数。
    NaN値は計算前に除外される。

    Parameters
    ----------
    series : pd.Series
        計算対象のデータシリーズ。
    percentile : float
        クリッピングするパーセンタイル。

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
def get_constituents_weight_from_factset(file_list: list[Path | str]):
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
    shift_direction: str = "Both",
    month_period: int = 60,
) -> pd.DataFrame:
    """
    過去 or 将来のROICの値を入れるカラムを追加する。

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム。
    shift_direction : str, default "Both"
        シフトの方向。
        - "Both" : 過去と将来のROICを追加
        - "Future" : 将来のROICを追加
        - "Past" : 過去のROICを追加
    month_period : int, default 60
        期間（月数）。

    Returns
    -------
    pd.DataFrame
        ROICカラムが追加されたデータフレーム。
    """
    df.sort_values(["date", "Symbol"], inplace=True, ignore_index=True)
    for n in range(1, month_period + 1):
        if shift_direction == "Both":
            df[f"ROIC_{n}MAgo"] = df.groupby(["Symbol"])["ROIC"].shift(n)
            df[f"ROIC_{n}MForward"] = df.groupby(["Symbol"])["ROIC"].shift(-n)
        elif shift_direction == "Future":
            df[f"ROIC_{n}MForward"] = df.groupby(["Symbol"])["ROIC"].shift(-n)
        elif shift_direction == "Past":
            df[f"ROIC_{n}MAgo"] = df.groupby(["Symbol"])["ROIC"].shift(n)

    return df


# =====================================================================
def calculate_cagr(series: pd.Series, years: int) -> pd.Series:
    """
    指定された年数分のCAGRを計算するカスタム関数。
    データは月次（12ヶ月）のため、years * 12 のラグを使用する。

    Parameters
    ----------
    series : pd.Series
        計算対象のSeries。
    years : int
        CAGR計算期間（年）。

    Returns
    -------
    pd.Series
        CAGRを計算したSeries。
    """
    if series.empty:
        return pd.Series(dtype=float)

    # 期間 T = 年数 * 12ヶ月
    periods = years * 12

    # CAGRを計算するための過去の値 (開始時点の値)
    v_start = series.shift(periods)

    # 現在の値 (最終時点の値)
    v_end = series

    # CAGR = (v_end / v_start)^(1/N) - 1
    # ゼロやマイナスの値の除算/累乗エラーを避けるため、条件を設定
    cagr = np.where(
        (v_start > 0),  # 開始値が正の場合のみ計算
        (v_end / v_start) ** (1 / years) - 1,
        np.nan,  # それ以外は NaN
    )

    return pd.Series(cagr, index=series.index)


# =====================================================================
def calculate_growth(
    df: pd.DataFrame, data_name: str, growth_type: str
) -> pd.DataFrame:
    """
    成長率を計算する関数

    Args:
        df: 元データのDataFrame (columns: date, P_SYMBOL, value, variable)
        data_name: データ項目名
        growth_type: 成長率の種類（QoQ, YoY, CAGR_3Y, CAGR_5Y）

    Returns:
        成長率を計算したDataFrame (columns: date, P_SYMBOL, value, variable)
    """
    df_growth = df.copy()
    new_variable = f"{data_name}_{growth_type}"

    # 成長率の計算
    if growth_type == "QoQ":
        # 四半期変化率（3ヶ月前との比較）
        periods = 3
        df_growth[new_variable] = df_growth.groupby("P_SYMBOL")["value"].pct_change(
            periods=periods
        )

    elif growth_type == "YoY":
        # 前年同期比（12ヶ月前との比較）
        periods = 12
        df_growth[new_variable] = df_growth.groupby("P_SYMBOL")["value"].pct_change(
            periods=periods
        )

    elif growth_type == "CAGR_3Y":
        # 3年複合年間成長率
        years = 3
        df_growth[new_variable] = df_growth.groupby("P_SYMBOL")["value"].transform(
            lambda x: calculate_cagr(x, years=years)
        )

    elif growth_type == "CAGR_5Y":
        # 5年複合年間成長率
        years = 5
        df_growth[new_variable] = df_growth.groupby("P_SYMBOL")["value"].transform(
            lambda x: calculate_cagr(x, years=years)
        )

    else:
        raise ValueError(
            f"未対応の成長率タイプ: {growth_type}\n"
            f"対応タイプ: QoQ, YoY, CAGR_3Y, CAGR_5Y"
        )

    # データ整形
    df_growth = (
        df_growth.drop(columns=["value", "variable"])
        .dropna(subset=[new_variable], ignore_index=True)
        .rename(columns={new_variable: "value"})
        .assign(variable=new_variable)
    )

    return df_growth


# =====================================================================
def calculate_margin_delta_annualized(series: pd.Series, years: int) -> pd.Series:
    """
    マージン改善率の年率換算デルタを計算

    :param series: マージン値のシリーズ（時系列順）
    :param years: 計算期間（年数）
    :return: 年率換算のマージン改善率（デルタ）
    """
    periods = years * 12  # 月次データを想定

    # 期間の最初と最後の値の差分を年数で割る
    delta = series.diff(periods=periods)
    annualized_delta = delta / years

    return annualized_delta


# =====================================================================
def calculate_margin_delta(
    df: pd.DataFrame, data_name: str, growth_type: str
) -> pd.DataFrame:
    """
    マージン変化幅（delta）を計算する関数

    Args:
        df: 元データのDataFrame (columns: date, P_SYMBOL, value, variable)
        data_name: データ項目名
        growth_type: 成長率の種類（CHANGE_QoQ, CHANGE_YoY, CHANGE_3Y, CHANGE_5Y）

    Returns:
        成長率を計算したDataFrame (columns: date, P_SYMBOL, value, variable)
    """
    growth_type_config = {
        "CHANGE_QoQ": {"periods": 3, "years": 0.25},  # 3ヶ月 = 0.25年
        "CHANGE_YoY": {"periods": 12, "years": 1.0},  # 12ヶ月 = 1年
        "CHANGE_3Y": {"periods": 36, "years": 3.0},  # 36ヶ月 = 3年
        "CHANGE_5Y": {"periods": 60, "years": 5.0},  # 60ヶ月 = 5年
    }
    if growth_type not in growth_type_config:
        raise ValueError(
            f"未対応の変化タイプ: {growth_type}\n"
            f"対応タイプ: {', '.join(growth_type_config.keys())}"
        )

    df_growth = df.copy()
    df_growth = df_growth.sort_values(["P_SYMBOL", "date"], ignore_index=True)
    new_variable = f"{data_name}_{growth_type}_Ann"

    config = growth_type_config[growth_type]
    periods = config["periods"]
    years = config["years"]
    new_variable = f"{data_name}_{growth_type}"

    # 年率換算されたdeltaの計算
    # (Margin_t - Margin_t-n) / n_years
    df_growth[new_variable] = (
        df_growth.groupby("P_SYMBOL")["value"].diff(periods=periods).div(years)
    )
    # データ整形
    df_growth = (
        df_growth.drop(columns=["value", "variable"])
        .dropna(subset=[new_variable], ignore_index=True)
        .rename(columns={new_variable: "value"})
        .assign(variable=new_variable)
    )

    return df_growth


# =====================================================================
def calculate_margin_improvement_rate_relative(
    df: pd.DataFrame, data_name: str, growth_type: str
) -> pd.DataFrame:
    """
    マージン改善率（相対）を計算する関数

    改善の「余地」を考慮した相対的な改善率を計算する。
    既に高マージンの企業がさらに改善するのは困難であることを反映。

    計算式:
        Relative_Improvement_Rate = (Margin_t - Margin_t-n) / (100% - Margin_t-n)

    例:
        Case 1: 10% → 15% への改善
            通常: 15% - 10% = +5%ポイント
            相対: (15% - 10%) / (100% - 10%) = 5% / 90% = 5.56%

        Case 2: 80% → 85% への改善
            通常: 85% - 80% = +5%ポイント（同じ）
            相対: (85% - 80%) / (100% - 80%) = 5% / 20% = 25.0%（より評価）

    Args:
        df: 元データのDataFrame (columns: date, P_SYMBOL, value, variable)
        data_name: データ項目名（例: "FF_OPER_MGN"）
        growth_type: 変化タイプ（REL_PctCHANGE_QoQ, REL_PctCHANGE_YoY, REL_PctCHANGE_3Y, REL_PctCHANGE_5Y）

    Returns:
        相対改善率を計算したDataFrame (columns: date, P_SYMBOL, value, variable)

    Notes:
        - マージンが100%に近い場合、分母が小さくなり極端な値が出る
        - 負のマージン（赤字）の場合は計算対象外（NaN）
    """
    growth_type_config = {
        "REL_PctCHANGE_QoQ": {"periods": 3, "display": "Rel_QoQ"},
        "REL_PctCHANGE_YoY": {"periods": 12, "display": "Rel_YoY"},
        "REL_PctCHANGE_3Y": {"periods": 36, "display": "Rel_3Y"},
        "REL_PctCHANGE_5Y": {"periods": 60, "display": "Rel_5Y"},
    }

    if growth_type not in growth_type_config:
        raise ValueError(
            f"未対応の変化タイプ: {growth_type}\n"
            f"対応タイプ: {', '.join(growth_type_config.keys())}"
        )

    df_growth = df.copy()
    df_growth = df_growth.sort_values(["P_SYMBOL", "date"], ignore_index=True)

    config = growth_type_config[growth_type]
    periods = config["periods"]
    new_variable = f"{data_name}_{growth_type}"

    # 過去のマージンを取得
    df_growth["margin_past"] = df_growth.groupby("P_SYMBOL")["value"].shift(periods)

    # 現在のマージン
    df_growth["margin_current"] = df_growth["value"]

    # 相対改善率の計算
    # (Margin_t - Margin_t-n) / (100 - Margin_t-n)
    # 注: マージンはパーセント表記（例: 15% -> 15）を前提
    numerator = df_growth["margin_current"] - df_growth["margin_past"]
    denominator = 100 - df_growth["margin_past"]

    # 分母がゼロまたは負の場合（マージン>=100%）はNaNにする
    # 過去マージンが負の場合もNaNにする
    df_growth[new_variable] = np.where(
        (denominator > 0) & (df_growth["margin_past"] >= 0),
        numerator / denominator,
        np.nan,
    )

    # データ整形
    df_growth = (
        df_growth.drop(columns=["value", "variable", "margin_past", "margin_current"])
        .dropna(subset=[new_variable], ignore_index=True)
        .rename(columns={new_variable: "value"})
        .assign(variable=new_variable)
    )

    return df_growth


# =====================================================================
def add_shifted_factor_cols_month(
    df: pd.DataFrame,
    factor_name: str,
    shift_month: list[int],
    shift_direction: str = "Both",
) -> pd.DataFrame:
    """指定されたファクターの過去または将来の月次シフト値カラムを追加する。

    この関数は、DataFrameを 'Symbol' ごとにグループ化し、指定された月数だけ
    ファクター値を時間的にシフトさせた新しいカラムを作成する。
    処理の前に、データフレームは 'date' と 'Symbol' でソートされる。

    Parameters
    ----------
    df : pd.DataFrame
        'date' および 'Symbol' カラムを持つ時系列データフレーム。
        (例: 日付、銘柄、ファクター値を含むパネルデータ)
    factor_name : str
        シフト処理を適用するファクター（特徴量）のカラム名。
    shift_month : list[int]
        ファクター値をシフトさせる月数（期間）。リストに含まれる各整数（n）に対し、
        新しいカラム (例: Factor_nMAgo, Factor_nMForward) が作成される。
    shift_direction : str, optional
        シフト処理の方向を指定する。
        'Both', 'Future', 'Past' のいずれかを指定。デフォルトは "Both"。

        - "Both" : 過去 (Positive shift, nMAgo) と将来 (Negative shift, nMForward) の両方を追加。
        - "Future" : 将来 (Negative shift, nMForward) のみを追加。
        - "Past" : 過去 (Positive shift, nMAgo) のみを追加。

    Returns
    -------
    pd.DataFrame
        シフトされたファクター値のカラムが追加されたデータフレーム。
        追加されるカラム名: ``{factor_name}_{n}MAgo`` および/または ``{factor_name}_{n}MForward``。

    Notes
    -----
    - **過去へのシフト (Past shift, nMAgo)**:
    現在の行に **nヶ月前** のファクター値を格納するために、``shift(n)`` を使用する。
    - **将来へのシフト (Future shift, nMForward)**:
    現在の行に **nヶ月後** のファクター値を格納するために、``shift(-n)`` を使用する。
    これは、現在のファクター値が将来のnヶ月間のリターンを予測する目的などで使用される。
    - 処理は `Symbol` ごとに行われるため、銘柄間でデータが混ざることはない（セクター中立なランキング処理ではない）。
    """

    df.sort_values(["date", "Symbol"], inplace=True, ignore_index=True)
    for n in shift_month:
        if shift_direction == "Both":
            df[f"{factor_name}_{n}MAgo"] = df.groupby(["Symbol"])[factor_name].shift(n)
            df[f"{factor_name}_{n}MForward"] = df.groupby(["Symbol"])[
                factor_name
            ].shift(-n)
        elif shift_direction == "Future":
            df[f"{factor_name}_{n}MForward"] = df.groupby(["Symbol"])[
                factor_name
            ].shift(-n)
        elif shift_direction == "Past":
            df[f"{factor_name}_{n}MAgo"] = df.groupby(["Symbol"])[factor_name].shift(n)

    return df


# =====================================================================
def add_factor_pct_rank_cols(
    df: pd.DataFrame,
    factor_name: str,
    freq_suffix: str = "PctRank",
    sector_neutral_mode: bool = True,
    inversed: bool = False,
    winsorize: bool = False,
    winsorize_limits: tuple = (0.01, 0.01),
) -> pd.DataFrame:
    """
    各時点の指定したデータ項目のパーセンタイルランクのカラムを追加する

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム
    factor_name : str
        ファクター名
    freq_suffix : str, default "PctRank"
        カラム名のサフィックス
    sector_neutral_mode : bool, default True
        セクター中立化を行うか
    inversed : bool, default False
        ランクを反転するか
    winsorize : bool, default False
        ランク変換前にwinsorizeを行うか
    winsorize_limits : tuple, default (0.01, 0.01)
        winsorizeの下限・上限パーセンタイル
        例: (0.01, 0.01) = 上下1%をクリップ
        例: (0.025, 0.025) = 上下2.5%をクリップ

    Returns
    -------
    pd.DataFrame
        パーセンタイルランクが追加されたデータフレーム
    """
    pctrank_col_name = f"{factor_name}_{freq_suffix}"
    if inversed:
        pctrank_col_name = f"{factor_name}_Inv_{freq_suffix}"

    groupby_cols = ["date"]
    # セクター中立化を行う場合は、セクター内でパーセンタイルランク変換する
    if sector_neutral_mode:
        groupby_cols.append("GICS Sector")
        pctrank_col_name = f"{pctrank_col_name}_Sector_Neutral"

    # Winsorize処理を行う場合
    if winsorize:
        # 一時的なカラム名
        temp_factor_col = f"{factor_name}_winsorized_temp"

        # グループごとにwinsorize
        df[temp_factor_col] = df.groupby(groupby_cols)[factor_name].transform(
            lambda x: _winsorize_series_for_rank(x, winsorize_limits)
        )

        # winsorize済みデータでランク変換
        df[pctrank_col_name] = df.groupby(groupby_cols)[temp_factor_col].transform(
            lambda x: x.rank(pct=True)
        )

        # 一時カラムを削除
        df.drop(columns=[temp_factor_col], inplace=True)
    else:
        # 元のデータでランク変換
        df[pctrank_col_name] = df.groupby(groupby_cols)[factor_name].transform(
            lambda x: x.rank(pct=True)
        )

    if inversed:
        df[pctrank_col_name] = 1 - df[pctrank_col_name]

    return df


# =====================================================================
def add_factor_rank_cols(
    df: pd.DataFrame,
    factor_name: str,
    freq_suffix: str = "Rank",
    sector_neutral_mode: bool = True,
    inversed: bool = False,
    winsorize: bool = True,
    winsorize_limits: tuple = (0.01, 0.01),
) -> pd.DataFrame:
    """
    各時点の指定したデータ項目の5分位ランクカラムを追加する

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム
    factor_name : str
        ファクター名
    freq_suffix : str, default "Rank"
        カラム名のサフィックス
    sector_neutral_mode : bool, default True
        セクター中立化を行うか
    inversed : bool, default False
        ランクを反転するか
    winsorize : bool, default False
        ランク変換前にwinsorizeを行うか
    winsorize_limits : tuple, default (0.01, 0.01)
        winsorizeの下限・上限パーセンタイル
        例: (0.01, 0.01) = 上下1%をクリップ
        例: (0.025, 0.025) = 上下2.5%をクリップ

    Returns
    -------
    pd.DataFrame
        5分位ランクが追加されたデータフレーム
    """

    rank_col_name = f"{factor_name}_{freq_suffix}"
    rank_dict = {
        1.0: "rank5",
        2.0: "rank4",
        3.0: "rank3",
        4.0: "rank2",
        5.0: "rank1",
    }
    if inversed:
        rank_col_name = f"{factor_name}_Inv_{freq_suffix}"
        rank_dict = {
            1.0: "rank1",
            2.0: "rank2",
            3.0: "rank3",
            4.0: "rank4",
            5.0: "rank5",
        }

    groupby_cols = ["date"]
    if sector_neutral_mode:
        groupby_cols.append("GICS Sector")
        rank_col_name = f"{rank_col_name}_Sector_Neutral"

    # Winsorize処理を行う場合
    if winsorize:
        # 一時的なカラム名
        temp_factor_col = f"{factor_name}_winsorized_temp"

        # グループごとにwinsorize
        df[temp_factor_col] = df.groupby(groupby_cols)[factor_name].transform(
            lambda x: _winsorize_series_for_rank(x, winsorize_limits)
        )

        # winsorize済みデータで5分位ランク変換
        df[rank_col_name] = (
            df.groupby(groupby_cols)[temp_factor_col]
            .transform(
                lambda x: (
                    (pd.qcut(x, q=5, labels=False, duplicates="drop") + 1)
                    if x.notna().sum() >= 5
                    else pd.Series(np.nan, index=x.index)
                )
            )
            .replace(rank_dict)
        )

        # 一時カラムを削除
        df.drop(columns=[temp_factor_col], inplace=True)
    else:
        # 元のデータで5分位ランク変換
        df[rank_col_name] = (
            df.groupby(groupby_cols)[factor_name]
            .transform(
                lambda x: (
                    (pd.qcut(x, q=5, labels=False, duplicates="drop") + 1)
                    if x.notna().sum() >= 5
                    else pd.Series(np.nan, index=x.index)
                )
            )
            .replace(rank_dict)
        )

    return df


# =====================================================================
def add_factor_zscore_cols(
    df: pd.DataFrame,
    factor_name: str,
    freq_suffix: str = "ZScore",
    sector_neutral_mode: bool = True,
    use_median: bool = True,
    min_samples: int = 5,
    inversed: bool = False,
) -> pd.DataFrame:
    """
    各時点の指定したデータ項目のZスコアカラムを追加する（セクター中立対応）

    Zスコアは以下の式で計算:
    - use_median=True:  Z = (X - median) / MAD * 1.4826
    - use_median=False: Z = (X - mean) / std

    Args:
        df: 入力DataFrame
            必須列: date, factor_name
            sector_neutral_mode=True の場合: GICS Sector も必要
        factor_name: Zスコアを計算する列名
        freq_suffix: 追加する列名のサフィックス（デフォルト: "ZScore"）
        sector_neutral_mode: セクター中立でZスコアを計算するか
            True: 各セクター内でZスコアを計算
            False: 市場全体でZスコアを計算
        use_median: 中央値ベースのZスコアを使用するか
            True: 中央値とMAD（中央絶対偏差）を使用（ロバスト）
            False: 平均値と標準偏差を使用（通常のZスコア）
        min_samples: Zスコア計算に必要な最小サンプル数

    Returns:
        Zスコア列が追加されたDataFrame

    Examples:
        >>> # セクター中立、中央値ベース
        >>> df = add_factor_zscore_cols(df, "ROE")

        >>> # 市場全体
        >>> df = add_factor_zscore_cols(df, "ROE", sector_neutral_mode=False)

        >>> # 平均値ベース
        >>> df = add_factor_zscore_cols(df, "ROE", use_median=False)

    Notes:
        - 中央値ベースのZスコアは外れ値に強い
        - MAD（Median Absolute Deviation）は中央絶対偏差
        - 1.4826 は正規分布の場合にMADを標準偏差と同等にするための係数
    """

    # -------------------------------------------------------------------
    def calculate_robust_zscore(series: pd.Series) -> pd.Series:
        """中央値とMADを使用したロバストなZスコアを計算"""
        valid_count = series.notna().sum()

        if valid_count < min_samples:
            return pd.Series(np.nan, index=series.index)

        median = series.median()
        mad = (series - median).abs().median()

        if mad == 0 or pd.isna(mad):
            return pd.Series(np.nan, index=series.index)

        zscore = (series - median) / (mad * 1.4826)
        return zscore

    # -------------------------------------------------------------------
    def calculate_standard_zscore(series: pd.Series) -> pd.Series:
        """平均値と標準偏差を使用した通常のZスコアを計算"""
        valid_count = series.notna().sum()

        if valid_count < min_samples:
            return pd.Series(np.nan, index=series.index)

        mean = series.mean()
        std = series.std()

        if std == 0 or pd.isna(std):
            return pd.Series(np.nan, index=series.index)

        zscore = (series - mean) / std
        return zscore

    # -------------------------------------------------------------------

    # 入力検証
    if factor_name not in df.columns:
        raise ValueError(f"列 '{factor_name}' がDataFrameに存在しません")

    if "date" not in df.columns:
        raise ValueError("'date' 列が必要です")

    if sector_neutral_mode and "GICS Sector" not in df.columns:
        raise ValueError("sector_neutral_mode=True の場合、'GICS Sector' 列が必要です")

    # Zスコア列名
    zscore_col_name = f"{factor_name}_{freq_suffix}"
    if inversed:
        zscore_col_name = f"{factor_name}_Inv_{freq_suffix}"

    # グループ化する列
    groupby_cols = ["date"]
    if sector_neutral_mode:
        groupby_cols.append("GICS Sector")
        zscore_col_name = f"{zscore_col_name}_Sector_Neutral"

    # Zスコアの計算
    if use_median:
        df[zscore_col_name] = df.groupby(groupby_cols)[factor_name].transform(
            calculate_robust_zscore
        )
    else:
        df[zscore_col_name] = df.groupby(groupby_cols)[factor_name].transform(
            calculate_standard_zscore
        )

    # 符号を逆転する場合
    if inversed:
        df[zscore_col_name] = -df[zscore_col_name]

    return df


# =====================================================================
def _winsorize_series_for_rank(
    series: pd.Series, limits: tuple = (0.01, 0.01)
) -> pd.Series:
    """
    ランク変換前のwinsorize用ヘルパー関数

    Parameters
    ----------
    series : pd.Series
        対象データ
    limits : tuple
        (下限パーセンタイル, 上限パーセンタイル)
        例: (0.01, 0.01) = 上下1%をクリップ

    Returns
    -------
    pd.Series
        winsorize済みのSeries
    """
    # 有効なデータのみ処理
    valid_data = series.dropna()

    # データが少なすぎる場合はそのまま返す
    if len(valid_data) < 10:
        return series

    # パーセンタイル計算
    lower = valid_data.quantile(limits[0])
    upper = valid_data.quantile(1 - limits[1])

    # クリップ
    return series.clip(lower=lower, upper=upper)


# =====================================================================
def add_roic_rank_cols(df: pd.DataFrame, freq_suffix: str) -> pd.DataFrame:
    """
    各時点のROICのランクカラムを追加する
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
# make ROIC_Label column
def make_roic_transition_label(
    row,
    roic_rank_col: str,
    freq: str,
    shift_direction: str,
    year_period: int = 5,
    judge_by_slope: bool = False,
):
    """ROICの5分位ランクの推移に基づきラベルを割り当てる。

    この関数はDataFrameの各行に適用されることを想定している。指定された
    期間におけるROICランクの過去または将来のトレンドを分析し、観測された
    パターンに基づいて説明的なラベルを割り当てる。

    引数
    ----------
    row : pd.Series
        pandas DataFrameの単一行。必要なROICランクと傾きの列を含んでいる
        必要がある。
    freq : {'annual', 'monthly'}
        データの頻度。チェックするランク列を決定するために使用される。
    shift_direction : {'Future', 'Past'}
        ROICランクを調査する時間軸の方向。
        - "Future": 将来のROICランクを分析する (例: `ROIC_Rank_12MForward`)。
        - "Past": 過去のROICランクを分析する (例: `ROIC_Rank_12MAgo`)。
    year_period : int, optional
        観測期間の年数。デフォルトは5年である。
    judge_by_slope : bool, optional
        Trueの場合、"move to high"と"drop to low"の分類に事前に計算された
        ROICの傾きを使用する。Falseの場合は、始点と終点のランクのみを
        使用する。デフォルトはTrueである。

    戻り値
    -------
    str or np.nan
        割り当てられたラベル。取りうる値は以下の通りである。
        - "remain high": 期間中の全てのランクが'rank1'または'rank2'。
        - "remain low": 期間中の全てのランクが'rank4'または'rank5'。
        - "move to high": 低ランク('rank3'-'rank5')で始まり、高ランク('rank1'-'rank2')で終わる。
        - "drop to low": 高ランク('rank1'-'rank3')で始まり、低ランク('rank4'-'rank5')で終わる。
        - "others": 上記のどのパターンにも一致しないが、期間中の全てのランクデータが存在する場合。
        - np.nan: 指定された期間内にランクデータが1つでも欠損している場合。

    注釈
    -----
    この関数は、調査対象の列を動的に決定する。例えば、`freq='annual'`,
    `shift_direction='Future'`, `year_period=5`の場合、`ROIC_Rank_1MForward`から
    `ROIC_Rank_60MForward`までの列をチェックする。

    `judge_by_slope`がTrueの場合、分類をより精緻化するために、対応する傾きの列
    （例: 5年間の場合は`ROIC_Slope_60MForward`）が`row`に含まれている必要が
    ある。

    """

    # 1. Get all ranks for the period, handling missing columns/values safely
    shift_direction_suffix = None
    if shift_direction == "Future":
        shift_direction_suffix = "Forward"
    elif shift_direction == "Past":
        shift_direction_suffix = "Ago"
    else:
        raise ValueError("shift_direction must be 'Future' or 'Past'")

    cols = []
    if freq == "annual":
        cols = [f"{roic_rank_col}_1M{shift_direction_suffix}"] + [
            f"{roic_rank_col}_{month}M{shift_direction_suffix}"
            for month in range(12, 12 * (year_period + 1), 12)
        ]
    elif freq == "monthly":
        cols = [
            f"{roic_rank_col}_{month}M{shift_direction_suffix}"
            for month in range(1, 12 * (year_period) + 1)
        ]
    else:
        raise ValueError("freq must be 'annual' or 'monthly'")

    ranks = []
    for col_name in cols:
        ranks.append(row.get(col_name, np.nan))

    # 2. Check if *any* rank in the period is missing (NaN)
    any_rank_missing = any(pd.isna(r) for r in ranks)

    # 3. Check "move/drop" conditions - requires start and end ranks (and maybe slope)
    current_rank = ranks[0]  # Rank at the start of the period (time 0)
    final_rank = ranks[-1]  # Rank at the end of the period
    move_to_high_condition = False
    drop_to_low_condition = False

    # Only evaluate move/drop if start and end ranks are available
    if not pd.isna(current_rank) and not pd.isna(final_rank):
        if judge_by_slope:
            slope_col = f"ROIC_Slope_{int(year_period * 12)}M{shift_direction_suffix}"
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

    # 4. Check "remain" conditions - requires *all* ranks to be present and match
    result = None
    if not any_rank_missing:  # Only check if all ranks are available
        if all(rank in ["rank1", "rank2"] for rank in ranks):
            result = "remain high"
        elif all(rank in ["rank4", "rank5"] for rank in ranks):
            result = "remain low"
        # Apply move/drop conditions if met
        elif move_to_high_condition:
            result = "move to high"
        elif drop_to_low_condition:
            result = "drop to low"
        # We reach here if none of the specific "remain", "move", or "drop" conditions were met.
        else:
            result = "others"
    # If *any* rank was missing during the period, return NaN.
    else:
        result = np.nan

    return result


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
        ["Quarter", "Symbol", *roic_cols],
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
            (("ROIC" in col) and ("QForward" in col) and ("Slope" not in col))
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
        make_roic_label, quarter_period=12, judge_by_slope=False, axis=1
    ).reset_index(drop=True)
    df_eoq["ROIC_Label_20QForward"] = df_return_and_roic_filled.apply(
        make_roic_label, quarter_period=20, judge_by_slope=False, axis=1
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
            *sorted(
                [col for col in df_return_and_roic_filled.columns if "ROIC" in col]
            ),
        ]
    )

    df_return_and_roic_filled.to_parquet(DATA_DIR / "MSCI KOKUSAI_all data.parquet")


# =====================================================================
def calculate_cumulative_return(
    df,
    roic_label_col: str,
    return_col: str,
    start_date: str,
    end_date: str | None = None,
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
    fig_title: str | None = None,
    show_benchmark: bool = False,
    savefig: bool = False,
    save_path: str | None | Path | None = None,
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
        g.reset_index(),
        id_vars=["date"],
        value_vars=g.columns.tolist(),
        var_name="ROIC_Label",
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


# =====================================================================
def check_all_months_exist(df: pd.DataFrame, date_col: str = "date") -> bool:
    """
    データフレームの日付カラムに、開始日から終了日までの
    全ての年月が欠けなく存在するかを判定します。

    Args:
        df: 判定対象のデータフレーム
        date_col: 日付が格納されたカラム名

    Returns:
        bool: 全ての年月が存在する場合はTrue、そうでない場合はFalse
    """
    # 1. カラムを日付型に変換し、存在する年月のリストを作成
    #    .dt.to_period('M')で 'YYYY-MM' の形式に変換し、重複を除外
    actual_months = pd.to_datetime(df[date_col]).dt.to_period("M").unique()

    # 2. 本来あるべき全ての年月のリストを生成
    #    データ内の最小年月から最大年月までの連続したPeriodIndexを作成
    expected_months = pd.period_range(
        start=actual_months.min(),
        end=actual_months.max(),
        freq="M",  # 'M' はMonthEnd（月末）を表す
    )

    # 3. 2つのリストを比較して欠落をチェック
    if len(actual_months) == len(expected_months):
        print("✅ すべての年月が欠けなく存在します。")
        return True
    else:
        # 集合の差分を取ることで、欠落している年月を特定
        missing_months = sorted(list(set(expected_months) - set(actual_months)))
        print(f"❌ 以下の年月が欠落しています: {missing_months}")
        return False


# =====================================================================
def calculate_interval_returns(df: pd.DataFrame) -> pd.DataFrame:
    """株価データから複数の過去区間におけるリターン（ディスクリプター）を計算する。

    Long形式（縦持ち）の価格データを入力とし、Pivotテーブルを用いて
    日付のアライメントを整えた上でラグ計算を行う。
    計算後、元のDataFrameに結合して返す。

    Args:
        df (pd.DataFrame): 以下のカラムを持つ月次価格データ。
            - 'date': 日付（datetime型、または変換可能な文字列）
            - 'P_SYMBOL': 銘柄コード
            - 'FG_PRICE': 株価（調整済み終値などを推奨）

    Returns:
        pd.DataFrame: 入力dfに以下のカラムを追加したDataFrame。
            - 'Return_1YAgo_to_Current': 直近1年間のリターン (T-12 -> T)
            - 'Return_1YAgo_to_1MAgo': 1年前から1カ月前までのリターン (T-12 -> T-1)
            - 'Return_2YAgo_to_1YAgo': 2年前の1年間のリターン (T-24 -> T-12)
            - 'Return_3YAgo_to_2YAgo': 3年前の1年間のリターン (T-36 -> T-24)
            - 'Return_3YAgo_to_1YAgo': 3年前から1年前までの累積リターン (T-36 -> T-12)
            - 'Return_1MAgo_to_Current': 直近1カ月のリターン (T-1 -> T)

    Note:
        - データの期間が36ヶ月未満の銘柄・日付についてはNaNが格納される。
        - 入力データの頻度は月次を想定している。
    """

    # 1. データの整理（日付型変換とソート）
    work_df = df.copy()
    work_df["date"] = pd.to_datetime(work_df["date"])
    work_df = work_df.sort_values(["date", "P_SYMBOL"])

    # 2. Pivotテーブルの作成（横持ちに変換）
    price_pivot = work_df.pivot(index="date", columns="P_SYMBOL", values="FG_PRICE")

    # 月末日付などに揃えるためリサンプリング（データの抜け漏れ防止）
    try:
        price_pivot = price_pivot.resample("ME").last()
    except ValueError:
        # 古いpandasバージョンへの対応
        price_pivot = price_pivot.resample("M").last()

    # 3. 過去時点の価格を取得（Shift）
    p_lag1 = price_pivot.shift(1)
    p_lag12 = price_pivot.shift(12)
    p_lag24 = price_pivot.shift(24)
    p_lag36 = price_pivot.shift(36)

    # 4. 区間別リターンの計算
    # Standard Momentum用 (T-12 -> T-1)
    ret_yr1_1mago = (p_lag1 / p_lag12) - 1
    # Simple Momentum用 (T-12 -> T)
    ret_yr1 = (price_pivot / p_lag12) - 1
    # 過去の推移確認用
    ret_yr2 = (p_lag12 / p_lag24) - 1
    ret_yr3 = (p_lag24 / p_lag36) - 1

    # 5. リバーサル検証用 (実態は区間リターン)
    # Long-Term (T-36 -> T-12)
    ret_3y_to_1y = (p_lag12 / p_lag36) - 1
    # Short-Term (T-1 -> T)
    ret_1m_to_curr = (price_pivot / p_lag1) - 1

    # 6. Long形式（縦持ち）に戻す
    stats_df = pd.DataFrame(
        {
            "Return_1YAgo_to_Current": ret_yr1.stack(),
            "Return_1YAgo_to_1MAgo": ret_yr1_1mago.stack(),
            "Return_2YAgo_to_1YAgo": ret_yr2.stack(),
            "Return_3YAgo_to_2YAgo": ret_yr3.stack(),
            "Return_3YAgo_to_1YAgo": ret_3y_to_1y.stack(),
            "Return_1MAgo_to_Current": ret_1m_to_curr.stack(),
        }
    )

    # 7. 元データと結合
    merged_df = pd.merge(
        work_df, stats_df, left_on=["date", "P_SYMBOL"], right_index=True, how="left"
    )

    return merged_df


# =====================================================================
def calc_relative_absolute_acceleration(
    df,
    descriptor_list: list[str],
    winsorize_pct=0.01,
    winsorize_groupby="date",
    epsilon=0.5,
    clip_range=(-3, 3),
    add_absolute=True,
    auto_clean=True,
):
    """
    頑健な加速度計算（自動クリーニング + epsilon最適化対応）

    Parameters:
    -----------
    df : pd.DataFrame
        ロングフォーマットデータ
    descriptor_list : List[str]
        加速度計算対象のディスクリプター名リスト
        例: ['FF_SALES', 'FF_OPER_INC']
    winsorize_pct : float
        ウィンソライゼーション比率（デフォルト1%）
    winsorize_groupby : str
        'date', 'sector_date', 'none' から選択
    epsilon : float or 'auto'
        'auto': データから自動決定（推奨）
        float: 固定値
    clip_range : tuple
        加速度のクリップ範囲
    add_absolute : bool
        True: 絶対加速度も追加
    auto_clean : bool
        True: 自動的にデータクリーニング実行

    Returns:
    --------
    pd.DataFrame (ロングフォーマット)
    dict (統計情報)
    """
    # Step 1: データクリーニング（オプション）
    if auto_clean:
        print(f"🧹 自動クリーニング実行中（groupby={winsorize_groupby}）...")
        growth_vars = []
        for desc in descriptor_list:
            growth_vars.extend([f"{desc}_YoY", f"{desc}_CAGR_3Y"])

        df, clean_stats = _clean_growth_data_grouped(
            df,
            winsorize_pct=winsorize_pct,
            growth_variables=growth_vars,
            groupby_method=winsorize_groupby,
        )
    else:
        clean_stats = {}

    # Step 2: ワイドフォーマットに変換
    df_wide = df.pivot_table(
        index=["date", "P_SYMBOL"], columns="variable", values="value"
    ).reset_index()

    # Step 3: epsilon決定
    stats = {"clean_stats": clean_stats}

    if epsilon == "auto":
        print("\n📊 epsilon自動決定中...")
        cagr_vars = [f"{desc}_CAGR_3Y" for desc in descriptor_list]
        epsilon_dict = _determine_optimal_epsilon(
            df, growth_variables=cagr_vars, percentile=0.05
        )
        stats["epsilon_dict"] = epsilon_dict
    else:
        epsilon_dict = dict.fromkeys(descriptor_list, epsilon)
        stats["epsilon_dict"] = epsilon_dict
        print(f"📊 固定epsilon使用: {epsilon:.6f}")

    # Step 4: 加速度計算
    print("\n🚀 加速度計算中...")

    for descriptor in descriptor_list:
        yoy_col = f"{descriptor}_YoY"
        cagr_col = f"{descriptor}_CAGR_3Y"

        if yoy_col not in df_wide.columns or cagr_col not in df_wide.columns:
            print(f"⚠️  {descriptor}: 必要なカラムが見つかりません。スキップ。")
            continue

        # epsilonの取得
        desc_epsilon = epsilon_dict.get(
            cagr_col, epsilon_dict.get("_overall_conservative", 0.02)
        )

        # 相対加速度
        rel_acc_col = f"{descriptor}_Rel_Acc"
        df_wide[rel_acc_col] = (
            (df_wide[yoy_col] - df_wide[cagr_col])
            / np.maximum(np.abs(df_wide[cagr_col]), desc_epsilon)
        ).clip(clip_range[0], clip_range[1])

        # 絶対加速度（オプション）
        if add_absolute:
            abs_acc_col = f"{descriptor}_Abs_Acc"
            df_wide[abs_acc_col] = df_wide[yoy_col] - df_wide[cagr_col]

        # 統計
        stats[f"{descriptor}_rel_acc_mean"] = df_wide[rel_acc_col].mean()
        stats[f"{descriptor}_rel_acc_std"] = df_wide[rel_acc_col].std()
        stats[f"{descriptor}_epsilon_used"] = desc_epsilon

        print(
            f"  ✓ {descriptor}: epsilon={desc_epsilon:.6f}, "
            f"平均={stats[f'{descriptor}_rel_acc_mean']:.4f}, "
            f"標準偏差={stats[f'{descriptor}_rel_acc_std']:.4f}"
        )

    # Step 5: ロングフォーマットに戻す
    df_result = df_wide.melt(
        id_vars=["date", "P_SYMBOL"], var_name="variable", value_name="value"
    )

    print("\n✅ 完了！")

    return df_result, stats


# =====================================================================
def _calculate_relative_acceleration(cagr_1y, cagr_3y, epsilon=0.5, clip_range=(-3, 3)):
    """
    相対加速度計算（クリップ範囲調整可能）
    """
    denominator = np.maximum(np.abs(cagr_3y), epsilon)
    acceleration = (cagr_1y - cagr_3y) / denominator
    acceleration = np.clip(acceleration, clip_range[0], clip_range[1])

    return acceleration


# =====================================================================
def _clean_growth_data_grouped(
    df: pd.DataFrame,
    winsorize_pct: float = 0.01,
    growth_variables: list[str] | None = None,
    groupby_method: str = "date",  # 'date', 'sector_date', 'none'
):
    """
    成長率データのクリーニング（グループ別ウィンソライゼーション対応）

    Parameters:
    -----------
    df : pd.DataFrame
        ロングフォーマットデータ (columns: date, P_SYMBOL, variable, value)
        セクター中立の場合は 'GICS Sector' カラムも必要
    winsorize_pct : float
        ウィンソライゼーション比率（上下1%をクリップ）
    growth_variables : List[str], optional
        クリーニング対象の変数名リスト。Noneの場合は自動検出。
    groupby_method : str
        'date': 各日付ごとにwinsorize（時系列の変化に対応）
        'sector_date': 各日付×セクターごとにwinsorize（セクター中立）
        'none': 全データで一括winsorize（現行方式）

    Returns:
    --------
    pd.DataFrame
        クリーニング済みロングフォーマットデータ
    dict
        クリーニング統計情報
    """
    # 必要なカラムの確認
    required_cols = ["date", "P_SYMBOL", "variable", "value"]
    if groupby_method == "sector_date" and "GICS Sector" not in df.columns:
        raise ValueError(
            "groupby_method='sector_date' の場合、'GICS Sector' カラムが必要です"
        )

    # ワイドフォーマットに変換
    if groupby_method == "sector_date":
        df_wide = df.pivot_table(
            index=["date", "P_SYMBOL", "GICS Sector"],
            columns="variable",
            values="value",
        ).reset_index()
    else:
        df_wide = df.pivot_table(
            index=["date", "P_SYMBOL"], columns="variable", values="value"
        ).reset_index()

    # クリーニング対象変数の決定
    if growth_variables is None:
        growth_variables = [
            col
            for col in df_wide.columns
            if any(keyword in col for keyword in ["CAGR", "YoY", "QoQ", "CHANGE"])
        ]

    print("=" * 70)
    print(f"データクリーニング統計（グルーピング: {groupby_method}）")
    print("=" * 70)

    stats = {}

    for var in growth_variables:
        if var not in df_wide.columns:
            continue

        data = df_wide[var]

        # 基本統計
        var_stats = {
            "total_count": len(data),
            "inf_count": np.isinf(data).sum(),
            "neginf_count": np.isneginf(data).sum(),
            "nan_count_before": data.isna().sum(),
        }

        # Step 1: 無限大をNaNに変換（全データ一括）
        df_wide[var] = df_wide[var].replace([np.inf, -np.inf], np.nan)

        # Step 2: グループ別ウィンソライゼーション
        if winsorize_pct > 0:
            if groupby_method == "date":
                # 日付ごとにwinsorize
                df_wide[var] = df_wide.groupby("date")[var].transform(
                    lambda x: _winsorize_series(x, winsorize_pct)
                )
                var_stats["groupby"] = "date"

            elif groupby_method == "sector_date":
                # 日付×セクターごとにwinsorize
                df_wide[var] = df_wide.groupby(["date", "GICS Sector"])[var].transform(
                    lambda x: _winsorize_series(x, winsorize_pct)
                )
                var_stats["groupby"] = "date × sector"

            elif groupby_method == "none":
                # 全データで一括winsorize
                lower = df_wide[var].quantile(winsorize_pct)
                upper = df_wide[var].quantile(1 - winsorize_pct)
                df_wide[var] = df_wide[var].clip(lower=lower, upper=upper)
                var_stats["groupby"] = "none (全データ一括)"
                var_stats["clip_lower"] = lower
                var_stats["clip_upper"] = upper

        # 最終統計
        var_stats["nan_count_after"] = df_wide[var].isna().sum()

        # 有限値の統計
        finite_data = df_wide[var][np.isfinite(df_wide[var])]
        if len(finite_data) > 0:
            var_stats.update(
                {
                    "min_finite": finite_data.min(),
                    "q01": finite_data.quantile(0.01),
                    "q05": finite_data.quantile(0.05),
                    "median": finite_data.median(),
                    "q95": finite_data.quantile(0.95),
                    "q99": finite_data.quantile(0.99),
                    "max_finite": finite_data.max(),
                }
            )

        stats[var] = var_stats

        # 結果表示
        print(f"\n{var}:")
        print(f"  Total: {var_stats['total_count']:,}")
        print(f"  Inf処理: {var_stats['inf_count']:,} → NaN")
        print(f"  Grouping: {var_stats.get('groupby', 'N/A')}")
        if "median" in var_stats:
            print(
                f"  Range: [{var_stats['min_finite']:.6f}, {var_stats['max_finite']:.6f}]"
            )
            print(f"  1-99%ile: [{var_stats['q01']:.6f}, {var_stats['q99']:.6f}]")
            print(f"  5-95%ile: [{var_stats['q05']:.6f}, {var_stats['q95']:.6f}]")

    # ロングフォーマットに戻す
    if groupby_method == "sector_date":
        df_clean = df_wide.melt(
            id_vars=["date", "P_SYMBOL", "GICS Sector"],
            var_name="variable",
            value_name="value",
        )
    else:
        df_clean = df_wide.melt(
            id_vars=["date", "P_SYMBOL"], var_name="variable", value_name="value"
        )

    print("\n" + "=" * 70)
    print("✅ クリーニング完了")
    print("=" * 70)

    return df_clean, stats


# =====================================================================
def _winsorize_series(series, percentile):
    """
    単一Seriesに対してウィンソライゼーションを実行

    Parameters:
    -----------
    series : pd.Series
        対象データ
    percentile : float
        クリップするパーセンタイル（例: 0.01 = 1%）

    Returns:
    --------
    pd.Series
        ウィンソライズされたSeries
    """
    # 有効なデータのみ処理
    valid_data = series.dropna()

    # データが少なすぎる場合はそのまま返す
    if len(valid_data) < 10:  # 最低10サンプル必要
        return series

    # パーセンタイル計算
    lower = valid_data.quantile(percentile)
    upper = valid_data.quantile(1 - percentile)

    # クリップ
    return series.clip(lower=lower, upper=upper)


# =====================================================================
def _determine_optimal_epsilon(df, growth_variables=None, percentile=0.05):
    """
    クリーニング済みデータから最適epsilonを決定

    Parameters:
    -----------
    df : pd.DataFrame
        ロングフォーマットデータ（クリーニング済みを推奨）
    growth_variables : List[str], optional
        3Y CAGR変数のリスト。Noneの場合は自動検出。
    percentile : float
        epsilon決定に使用するパーセンタイル（デフォルト5%）

    Returns:
    --------
    dict
        変数ごとの推奨epsilon
    """

    # ワイドフォーマットに変換
    df_wide = df.pivot_table(
        index=["date", "P_SYMBOL"], columns="variable", values="value"
    ).reset_index()

    # 3Y CAGR変数の自動検出
    if growth_variables is None:
        growth_variables = [col for col in df_wide.columns if "CAGR_3Y" in col]

    print("=" * 70)
    print(f"Epsilon決定分析（{percentile * 100:.0f}パーセンタイル基準）")
    print("=" * 70)

    epsilon_dict = {}

    for var in growth_variables:
        if var not in df_wide.columns:
            continue

        # 絶対値の分布分析
        abs_values = df_wide[var].abs().dropna()

        if len(abs_values) == 0:
            print(f"\n{var}: データなし")
            continue

        # パーセンタイル計算
        p01 = abs_values.quantile(0.01)
        p05 = abs_values.quantile(0.05)
        p10 = abs_values.quantile(0.10)
        p25 = abs_values.quantile(0.25)
        median = abs_values.median()

        # epsilon推奨値（最小0.5%保証）
        epsilon_recommended = max(abs_values.quantile(percentile), 0.005)

        epsilon_dict[var] = epsilon_recommended

        print(f"\n{var} (絶対値の分布):")
        print(f"  1%ile:  {p01:.6f} ({p01 * 100:.2f}%)")
        print(f"  5%ile:  {p05:.6f} ({p05 * 100:.2f}%)")
        print(f"  10%ile: {p10:.6f} ({p10 * 100:.2f}%)")
        print(f"  25%ile: {p25:.6f} ({p25 * 100:.2f}%)")
        print(f"  Median: {median:.6f} ({median * 100:.2f}%)")
        print(
            f"  → 推奨epsilon: {epsilon_recommended:.6f} ({epsilon_recommended * 100:.2f}%)"
        )

    # 全体の推奨値（保守的に最大値）
    if epsilon_dict:
        overall_epsilon = max(epsilon_dict.values())
        print("\n" + "=" * 70)
        print(
            f"全体推奨epsilon（保守的）: {overall_epsilon:.6f} ({overall_epsilon * 100:.2f}%)"
        )
        print("=" * 70)
        epsilon_dict["_overall_conservative"] = overall_epsilon

    return epsilon_dict
