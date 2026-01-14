"""
ROIC_make_data_files.py

ROIC関連のデータファイルを作成する関数群を定義するスクリプト。

"""

import sqlite3
import warnings
from pathlib import Path
from typing import List, Optional

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
def load_FG_PRICE(
    db_path: str | Path,
    start_date: str = None,  # type: ignore
    end_date: str = None,  # type: ignore
    p_symbol_list: List[str] = None,  # type:ignore
):
    """
    FG_PRICEテーブルからデータを読み込む。

    Parameters
    ----------
    db_path : str | Path
        データベースパス。
    start_date : str, optional
        開始日（例: '2024-01-01'）。
    end_date : str, optional
        終了日。
    p_symbol_list : List[str], optional
        対象シンボルのリスト。

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
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql(
            query, con=conn, params=params, parse_dates=["date"], index_col="date"
        )

    return df


# =====================================================================
def calculate_Return(
    df_price: pd.DataFrame,
    date_column: str = "date",
    symbol_column: str = "P_SYMBOL",
    price_column: str = "FG_PRICE",
    periods_months: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    価格データから複数期間のリターンを計算する。

    `load_FG_PRICE`から得られるような、日付をインデックスに持つ価格データフレームを
    入力として受け取ります。この関数は、まずデータを「整然化」します。
    これは、データフレーム内のすべての日付とすべての銘柄の組み合わせを持つ
    MultiIndexを作成し、欠損している価格データをNaNで埋める処理です。
    この整然化されたデータに対して、各銘柄ごとに複数期間のリターン、
    フォワードリターン、およびそれらの年率換算値を計算します。

    Parameters
    ----------
    df_price : pd.DataFrame
        価格データを含むデータフレーム。
        インデックスは日付 (datetime型)、カラムには銘柄コードと価格が含まれている必要があります。
    date_column : str, optional, default "date"
        日付カラム名。
    symbol_column : str, optional, default "P_SYMBOL"
        銘柄コードカラム名。
    price_column : str, optional, default "FG_PRICE"
        価格カラム名。
    periods_months : List[int], optional
        リターンを計算する期間（月単位）のリスト。
        デフォルトは [1, 3, 6, 12, 36, 60]。

    Returns
    -------
    pd.DataFrame
        `symbol_column` と `date_column` を MultiIndex に持つデータフレーム。
        元の価格データに加えて、以下のカラムが追加されます。
        - Return_{period_name}: 各期間のリターン。
            (例: `Return_1M`, `Return_3M`, `Return_1Y`)
        - Forward_Return_{period_name}: 各期間のフォワードリターン。
            (例: `Forward_Return_1M`, `Forward_Return_3M`)
        - Return_{period_name}_annlzd: 年率換算されたリターン。
            (例: `Return_1M_annlzd`, `Return_1Y_annlzd`)
        - Forward_Return_{period_name}_annlzd: 年率換算されたフォワードリターン。
            (例: `Forward_Return_1M_annlzd`)

    Notes
    -----
    この関数は、時系列データに欠損（特定の日付の価格データがないなど）が
    ある場合でも、正確なリターン計算を行うために重要です。
    `reindex` を使用してデータフレームを整然化することで、`pct_change` や `shift`
    が各銘柄の時系列に対して正しく適用されることを保証します。

    Examples
    --------
    >>> df_price.head()
                P_SYMBOL  FG_PRICE
    date
    2020-01-31     AAPL      77.37
    2020-01-31     MSFT     170.23
    ...
    >>> df_returns = calculate_Return(df_price)
    >>> df_returns.head()
                                FG_PRICE  Return_1M  Forward_Return_1M ...
    P_SYMBOL date
    AAPL     2020-01-31      77.37        NaN           0.128989 ...

    >>> # カスタムカラム名と期間を使用
    >>> df_returns = calculate_Return(
    ...     df_price,
    ...     date_column="Date",
    ...     symbol_column="Ticker",
    ...     price_column="Close",
    ...     periods_months=[1, 6, 12]
    ... )
    """
    # デフォルトの期間設定
    if periods_months is None:
        periods_months = [1, 3, 6, 12, 36, 60]

    # 1. 元のdfを銘柄と日付を列に戻す
    if date_column not in df_price.columns:
        df_reset = df_price.reset_index()
    else:
        df_reset = df_price.copy()

    # 2. 全銘柄リストと全日付リストを取得
    all_symbols = df_reset[symbol_column].unique().tolist()
    all_dates = df_reset[date_column].unique().tolist()

    # 3. 全銘柄×全日付の組み合わせ(MultiIndex)を作成
    new_index = pd.MultiIndex.from_product(
        [all_symbols, all_dates], names=[symbol_column, date_column]
    )

    # 4. 元のデータをMultiIndexにセットし直し、存在しない組み合わせをNaNで埋める
    #    これが「整然化」されたデータ
    df_regular = df_reset.set_index([symbol_column, date_column]).reindex(new_index)

    # 5. この整然化されたデータに対してリターンを計算する
    #    dateでソートする必要がある
    df_regular = df_regular.sort_index(level=date_column)

    for period_month in periods_months:
        period_name = (
            f"{int(period_month//12)}Y" if period_month >= 36 else f"{period_month}M"
        )

        # 通常のリターンとforwardリターンを計算
        df_regular[f"Return_{period_name}"] = df_regular.groupby(symbol_column)[
            price_column
        ].pct_change(period_month)
        df_regular[f"Forward_Return_{period_name}"] = df_regular.groupby(symbol_column)[
            f"Return_{period_name}"
        ].shift(-period_month)

        # 年率化したカラムを追加
        # すべての期間で統一的に計算: 年率換算リターン = リターン × (12 / 期間（月）)
        annualization_factor = 12 / period_month

        df_regular[f"Return_{period_name}_annlzd"] = (
            df_regular[f"Return_{period_name}"] * annualization_factor
        )
        df_regular[f"Forward_Return_{period_name}_annlzd"] = (
            df_regular[f"Forward_Return_{period_name}"] * annualization_factor
        )

    return df_regular


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

    # 期間 N = years
    N = years

    # CAGRを計算するための過去の値 (開始時点の値)
    V_start = series.shift(periods)

    # 現在の値 (最終時点の値)
    V_end = series

    # CAGR = (V_end / V_start)^(1/N) - 1
    # ゼロやマイナスの値の除算/累乗エラーを避けるため、条件を設定
    cagr = np.where(
        (V_start > 0),  # 開始値が正の場合のみ計算
        (V_end / V_start) ** (1 / N) - 1,
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
def calculate_margin_improvement(
    df: pd.DataFrame, data_name: str, growth_type: str
) -> pd.DataFrame:
    """
    マージン改善率（delta）を計算する関数

    Args:
        df: 元データのDataFrame (columns: date, P_SYMBOL, value, variable)
        data_name: データ項目名
        growth_type: 成長率の種類（CHANGE_QoQ, CHANGE_YoY, CHANGE_3Y, CHANGE_5Y）

    Returns:
        成長率を計算したDataFrame (columns: date, P_SYMBOL, value, variable)
    """
    df_growth = df.copy()
    new_variable = f"{data_name}_{growth_type}"

    # 成長率の計算
    if growth_type == "CHANGE_QoQ":
        # 四半期変化率（3ヶ月前との比較）
        periods = 3
        df_growth[new_variable] = df_growth.groupby("P_SYMBOL")["value"].diff(
            periods=periods
        )

    elif growth_type == "CHANGE_YoY":
        # 前年同期比（12ヶ月前との比較）
        periods = 12
        df_growth[new_variable] = df_growth.groupby("P_SYMBOL")["value"].diff(
            periods=periods
        )

    elif growth_type == "CHANGE_3Y":
        # 3年複合年間成長率
        years = 3
        df_growth[new_variable] = df_growth.groupby("P_SYMBOL")["value"].transform(
            lambda x: calculate_cagr(x, years=years)
        )

    elif growth_type == "CHANGE_5Y":
        # 5年複合年間成長率
        years = 5
        df_growth[new_variable] = df_growth.groupby("P_SYMBOL")["value"].transform(
            lambda x: calculate_cagr(x, years=years)
        )

    else:
        raise ValueError(
            f"未対応の成長率タイプ: {growth_type}\n"
            f"対応タイプ: CHANGE_QoQ, CHANGE_YoY, CHANGE_3Y, CHANGE_5Y"
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
) -> pd.DataFrame:
    """
    各時点の指定したデータ項目のパーセンタイルランクのカラムを追加する
    """

    rank_col_name = f"{factor_name}_{freq_suffix}"
    groupby_cols = ["date"]
    # セクター中立化を行う場合は、セクター内でパーセンタイルランク変換する
    if sector_neutral_mode:
        groupby_cols.append("GICS Sector")
    df[rank_col_name] = df.groupby(groupby_cols)[factor_name].transform(
        lambda x: x.rank(pct=True)
    )

    return df


# =====================================================================
def add_factor_rank_cols(
    df: pd.DataFrame,
    factor_name: str,
    freq_suffix: str = "Rank",
    sector_neutral_mode: bool = True,
) -> pd.DataFrame:
    """
    各時点の指定したデータ項目のランクカラムを追加する
    """

    rank_col_name = f"{factor_name}_{freq_suffix}"
    groupby_cols = ["date"]
    if sector_neutral_mode:
        groupby_cols.append("GICS Sector")

    df[rank_col_name] = (
        df.groupby(groupby_cols)[factor_name]
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
def add_factor_zscore_cols(
    df: pd.DataFrame,
    factor_name: str,
    freq_suffix: str = "ZScore",
    sector_neutral_mode: bool = True,
    use_median: bool = True,
    min_samples: int = 5,
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

    # グループ化する列
    groupby_cols = ["date"]
    if sector_neutral_mode:
        groupby_cols.append("GICS Sector")

    # Zスコアの計算
    if use_median:
        df[zscore_col_name] = df.groupby(groupby_cols)[factor_name].transform(
            calculate_robust_zscore
        )
    else:
        df[zscore_col_name] = df.groupby(groupby_cols)[factor_name].transform(
            calculate_standard_zscore
        )

    return df


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
def test_assign_roic_label(
    row,
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

    """  # 1. Get all ranks for the period, handling missing columns/values safely
    shift_direction_suffix = None
    if shift_direction == "Future":
        shift_direction_suffix = "Forward"
    elif shift_direction == "Past":
        shift_direction_suffix = "Ago"
    else:
        raise ValueError("shift_direction must be 'Future' or 'Past'")

    cols = []
    if freq == "annual":
        cols = [f"ROIC_Rank_1M{shift_direction_suffix}"] + [
            f"ROIC_Rank_{month}M{shift_direction_suffix}"
            for month in range(12, 12 * (year_period + 1), 12)
        ]
    elif freq == "monthly":
        cols = [
            f"ROIC_Rank_{month}M{shift_direction_suffix}"
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
            slope_col = f"ROIC_Slope_{int(year_period*12)}M{shift_direction_suffix}"
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
        test_assign_roic_label, quarter_period=12, judge_by_slope=False, axis=1
    ).reset_index(drop=True)
    df_eoq["ROIC_Label_20QForward"] = df_return_and_roic_filled.apply(
        test_assign_roic_label, quarter_period=20, judge_by_slope=False, axis=1
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
def calculate_cumulative_return(
    df,
    roic_label_col: str,
    return_col: str,
    start_date: str,
    end_date: Optional[str] = None,
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
    fig_title: Optional[str] = None,
    show_benchmark: bool = False,
    savefig: bool = False,
    save_path: Optional[str] | Optional[Path] = None,
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
