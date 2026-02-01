"""
returns.py
"""

from pathlib import Path

import pandas as pd
from pandas import DataFrame


def _get_period_name(period_month: int) -> str:
    """
    月数を期間名に変換する。

    Parameters
    ----------
    period_month : int
        期間（月単位）

    Returns
    -------
    str
        期間名（例: "1M", "3M", "3Y"）
    """
    return f"{int(period_month // 12)}Y" if period_month >= 36 else f"{period_month}M"


def _prepare_dataframe(
    df_price: DataFrame,
    date_column: str,
    symbol_column: str,
) -> DataFrame:
    """
    価格データフレームを準備する（日付列をインデックスから列に戻す）。

    Parameters
    ----------
    df_price : DataFrame
        価格データフレーム
    date_column : str
        日付カラム名
    symbol_column : str
        銘柄コードカラム名

    Returns
    -------
    DataFrame
        準備されたデータフレーム
    """
    if date_column not in df_price.columns:
        return df_price.reset_index()
    return df_price.copy()


def _create_regular_dataframe(
    df: pd.DataFrame,
    date_column: str,
    symbol_column: str,
) -> pd.DataFrame:
    """
    全銘柄×全日付の組み合わせを持つ「整然化」されたデータフレームを作成する。

    欠損している価格データはNaNで埋められる。

    Parameters
    ----------
    df : pd.DataFrame
        元の価格データフレーム
    date_column : str
        日付カラム名
    symbol_column : str
        銘柄コードカラム名

    Returns
    -------
    pd.DataFrame
        整然化されたデータフレーム（MultiIndex: symbol, date）
    """
    # 全銘柄リストと全日付リストを取得
    all_symbols = df[symbol_column].unique().tolist()
    all_dates = df[date_column].unique().tolist()

    # 全銘柄×全日付の組み合わせ(MultiIndex)を作成
    new_index = pd.MultiIndex.from_product(
        [all_symbols, all_dates], names=[symbol_column, date_column]
    )

    # 元のデータをMultiIndexにセットし直し、存在しない組み合わせをNaNで埋める
    df_regular = df.set_index([symbol_column, date_column]).reindex(new_index)

    # dateでソートする
    df_regular = df_regular.sort_index(level=date_column)

    return df_regular


def _calculate_period_returns(
    df: pd.DataFrame,
    symbol_column: str,
    price_column: str,
    period_month: int,
) -> pd.DataFrame:
    """
    特定期間のリターンとフォワードリターンを計算する。

    Parameters
    ----------
    df : pd.DataFrame
        価格データフレーム（MultiIndexed）
    symbol_column : str
        銘柄コードカラム名
    price_column : str
        価格カラム名
    period_month : int
        期間（月単位）

    Returns
    -------
    pd.DataFrame
        リターンカラムが追加されたデータフレーム
    """
    period_name = _get_period_name(period_month)
    df_result = df.copy()

    # 通常のリターンとforwardリターンを計算
    df_result[f"Return_{period_name}"] = df_result.groupby(symbol_column)[
        price_column
    ].pct_change(period_month)

    df_result[f"Forward_Return_{period_name}"] = df_result.groupby(symbol_column)[
        f"Return_{period_name}"
    ].shift(-period_month)

    return df_result


def _annualize_returns(
    df: pd.DataFrame,
    period_month: int,
) -> pd.DataFrame:
    """
    リターンを年率換算する。

    Parameters
    ----------
    df : pd.DataFrame
        リターンカラムを含むデータフレーム
    period_month : int
        期間（月単位）

    Returns
    -------
    pd.DataFrame
        年率換算リターンカラムが追加されたデータフレーム
    """
    period_name = _get_period_name(period_month)
    df_result = df.copy()

    # 年率化したカラムを追加
    annualization_factor = 12 / period_month

    df_result[f"Return_{period_name}_annlzd"] = (
        df_result[f"Return_{period_name}"] * annualization_factor
    )
    df_result[f"Forward_Return_{period_name}_annlzd"] = (
        df_result[f"Forward_Return_{period_name}"] * annualization_factor
    )

    return df_result


def calculate_return_multi_periods(
    df_price: pd.DataFrame,
    date_column: str = "date",
    symbol_column: str = "P_SYMBOL",
    price_column: str = "FG_PRICE",
    periods_months: list[int] | None = None,
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
    >>> df_returns = calculate_return(df_price)
    >>> df_returns.head()
                                FG_PRICE  Return_1M  Forward_Return_1M ...
    P_SYMBOL date
    AAPL     2020-01-31      77.37        NaN           0.128989 ...

    >>> # カスタムカラム名と期間を使用
    >>> df_returns = calculate_return(
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

    # 1. データフレームを準備
    df_prepared = _prepare_dataframe(df_price, date_column, symbol_column)

    # 2. 整然化されたデータフレームを作成
    df_regular = _create_regular_dataframe(df_prepared, date_column, symbol_column)

    # 3. 各期間のリターンを計算
    for period_month in periods_months:
        df_regular = _calculate_period_returns(
            df_regular, symbol_column, price_column, period_month
        )
        df_regular = _annualize_returns(df_regular, period_month)

    return df_regular
