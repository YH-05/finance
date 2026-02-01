"""Parquet schema definitions and validation functions.

このモジュールは Parquet ファイルのスキーマ定義と DataFrame 検証機能を提供します。

Schemas
-------
StockPriceSchema
    株価データスキーマ（symbol, date, OHLCV, adjusted_close）
EconomicIndicatorSchema
    経済指標データスキーマ（series_id, date, value, unit）

Functions
---------
validate_stock_price_dataframe
    株価データフレームの検証
validate_economic_indicator_dataframe
    経済指標データフレームの検証

Examples
--------
>>> import pandas as pd
>>> import datetime
>>> df = pd.DataFrame({
...     "symbol": ["AAPL"],
...     "date": [datetime.date(2024, 1, 1)],
...     "open": [150.0],
...     "high": [155.0],
...     "low": [149.0],
...     "close": [154.0],
...     "volume": [1000000],
...     "adjusted_close": [154.0],
... })
>>> validate_stock_price_dataframe(df)
True
"""

import datetime
from typing import Any

import numpy as np
import pandas as pd
from utils_core.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """DataFrame 検証エラー。

    DataFrame のスキーマ検証で問題が発見された場合に発生する例外。
    欠落カラムや型不一致の詳細情報を属性として保持します。

    Parameters
    ----------
    message : str
        エラーメッセージ
    missing_columns : list[str] | None, default=None
        欠落しているカラム名のリスト
    type_mismatches : dict[str, tuple[type, type]] | None, default=None
        型不一致のカラム名と (期待される型, 実際の型) のマッピング

    Attributes
    ----------
    missing_columns : list[str]
        欠落しているカラム名のリスト
    type_mismatches : dict[str, tuple[type, type]]
        型不一致のカラム名と (期待される型, 実際の型) のマッピング

    Examples
    --------
    >>> error = ValidationError(
    ...     "Missing required columns",
    ...     missing_columns=["volume", "adjusted_close"],
    ... )
    >>> error.missing_columns
    ['volume', 'adjusted_close']
    """

    def __init__(
        self,
        message: str,
        missing_columns: list[str] | None = None,
        type_mismatches: dict[str, tuple[type, type]] | None = None,
    ) -> None:
        super().__init__(message)
        self.missing_columns = missing_columns or []
        self.type_mismatches = type_mismatches or {}


class StockPriceSchema:
    """株価データスキーマ定義。

    Parquet ファイルに保存する株価データの構造を定義します。
    `fields` クラス属性でカラム名と期待される Python 型のマッピングを提供します。

    Attributes
    ----------
    fields : dict[str, type]
        カラム名と期待される型のマッピング

        - symbol: str - 銘柄シンボル（例: "AAPL", "GOOGL"）
        - date: datetime.date - 取引日
        - open: float - 始値（0以上）
        - high: float - 高値（0以上）
        - low: float - 安値（0以上）
        - close: float - 終値（0以上）
        - volume: int - 出来高（0以上）
        - adjusted_close: float - 調整後終値（0以上）

    Examples
    --------
    >>> StockPriceSchema.fields["symbol"]
    <class 'str'>
    >>> list(StockPriceSchema.fields.keys())
    ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close']
    """

    fields: dict[str, type] = {
        "symbol": str,
        "date": datetime.date,
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "volume": int,
        "adjusted_close": float,
    }


class EconomicIndicatorSchema:
    """経済指標データスキーマ定義。

    Parquet ファイルに保存する経済指標データの構造を定義します。
    `fields` クラス属性でカラム名と期待される Python 型のマッピングを提供します。

    Attributes
    ----------
    fields : dict[str, type]
        カラム名と期待される型のマッピング

        - series_id: str - 系列ID（例: "GDP", "CPI", "UNEMPLOYMENT"）
        - date: datetime.date - 日付
        - value: float - 値
        - unit: str - 単位（例: "percent", "billions_usd"）

    Examples
    --------
    >>> EconomicIndicatorSchema.fields["series_id"]
    <class 'str'>
    >>> list(EconomicIndicatorSchema.fields.keys())
    ['series_id', 'date', 'value', 'unit']
    """

    fields: dict[str, type] = {
        "series_id": str,
        "date": datetime.date,
        "value": float,
        "unit": str,
    }


def _check_empty_dataframe(df: pd.DataFrame) -> None:
    """DataFrame が空かどうかチェックする。

    Parameters
    ----------
    df : pd.DataFrame
        検証する DataFrame

    Raises
    ------
    ValidationError
        DataFrame が空の場合（行数が0またはカラムが0）
    """
    if df.empty or len(df.columns) == 0:
        raise ValidationError("DataFrame is empty")


def _check_missing_columns(
    df: pd.DataFrame,
    required_columns: set[str],
) -> list[str]:
    """必須カラムの欠落をチェックする。

    Parameters
    ----------
    df : pd.DataFrame
        検証する DataFrame
    required_columns : set[str]
        必須カラム名のセット

    Returns
    -------
    list[str]
        欠落しているカラム名のリスト
    """
    existing_columns = set(df.columns)
    return sorted(required_columns - existing_columns)


def _is_numeric_compatible(value: Any, expected_type: type) -> bool:
    """値が期待される数値型と互換性があるかチェックする。

    Parameters
    ----------
    value : Any
        検証する値
    expected_type : type
        期待される型（int または float）

    Returns
    -------
    bool
        互換性がある場合は True
    """
    if pd.isna(value):
        return True

    if expected_type is float:
        return isinstance(value, (int, float, np.integer, np.floating))

    if expected_type is int:
        return isinstance(value, (int, np.integer)) and not isinstance(value, bool)

    return False


def _is_date_compatible(value: Any) -> bool:
    """値が日付型と互換性があるかチェックする。

    Parameters
    ----------
    value : Any
        検証する値

    Returns
    -------
    bool
        互換性がある場合は True
    """
    if pd.isna(value):
        return True

    return isinstance(value, (datetime.date, pd.Timestamp, np.datetime64))


def _is_string_compatible(value: Any) -> bool:
    """値が文字列型と互換性があるかチェックする。

    Parameters
    ----------
    value : Any
        検証する値

    Returns
    -------
    bool
        互換性がある場合は True
    """
    if pd.isna(value):
        return True

    return isinstance(value, str)


def _check_type_mismatches(
    df: pd.DataFrame,
    schema_fields: dict[str, type],
) -> dict[str, tuple[type, type]]:
    """カラムの型不一致をチェックする。

    Parameters
    ----------
    df : pd.DataFrame
        検証する DataFrame
    schema_fields : dict[str, type]
        スキーマのフィールド定義

    Returns
    -------
    dict[str, tuple[type, type]]
        型不一致のカラム名と (期待される型, 実際の型) のマッピング
    """
    type_mismatches: dict[str, tuple[type, type]] = {}

    for column, expected_type in schema_fields.items():
        if column not in df.columns:
            continue

        # 最初の非 null 値で型チェック
        non_null_values = df[column].dropna()
        if len(non_null_values) == 0:
            continue

        sample_value = non_null_values.iloc[0]

        # 型互換性チェック
        is_compatible = False

        if expected_type is datetime.date:
            is_compatible = _is_date_compatible(sample_value)
        elif expected_type is str:
            is_compatible = _is_string_compatible(sample_value)
        elif expected_type in (int, float):
            is_compatible = _is_numeric_compatible(sample_value, expected_type)
        else:
            is_compatible = isinstance(sample_value, expected_type)

        if not is_compatible:
            type_mismatches[column] = (expected_type, type(sample_value))

    return type_mismatches


def _check_null_values(
    df: pd.DataFrame,
    columns: list[str],
) -> list[str]:
    """指定カラムの null 値をチェックする。

    Parameters
    ----------
    df : pd.DataFrame
        検証する DataFrame
    columns : list[str]
        チェックするカラム名のリスト

    Returns
    -------
    list[str]
        null 値を含むカラム名のリスト
    """
    null_columns = []
    for column in columns:
        if column in df.columns and bool(df[column].isna().any()):
            null_columns.append(column)
    return null_columns


def validate_stock_price_dataframe(df: pd.DataFrame) -> bool:
    """株価データフレームを検証する。

    DataFrame が StockPriceSchema に準拠しているかを検証します。
    検証項目:
    - DataFrame が空でないこと
    - 必須カラムが全て存在すること
    - 各カラムの型が正しいこと

    Parameters
    ----------
    df : pd.DataFrame
        検証する DataFrame

    Returns
    -------
    bool
        検証成功時は True

    Raises
    ------
    ValidationError
        検証失敗時。以下の場合に発生:

        - DataFrame が空の場合
        - 必須カラムが欠落している場合
        - カラムの型が不一致の場合

    Examples
    --------
    >>> import pandas as pd
    >>> import datetime
    >>> df = pd.DataFrame({
    ...     "symbol": ["AAPL"],
    ...     "date": [datetime.date(2024, 1, 1)],
    ...     "open": [150.0],
    ...     "high": [155.0],
    ...     "low": [149.0],
    ...     "close": [154.0],
    ...     "volume": [1000000],
    ...     "adjusted_close": [154.0],
    ... })
    >>> validate_stock_price_dataframe(df)
    True
    """
    logger.debug("Validating stock price DataFrame", row_count=len(df))

    try:
        # 空チェック
        _check_empty_dataframe(df)

        # 必須カラムチェック
        required_columns = set(StockPriceSchema.fields.keys())
        missing_columns = _check_missing_columns(df, required_columns)

        if missing_columns:
            logger.warning(
                "Stock price validation failed: missing columns",
                missing_columns=missing_columns,
            )
            raise ValidationError(
                f"Missing required columns: {', '.join(missing_columns)}. "
                f"Expected: {sorted(required_columns)}",
                missing_columns=missing_columns,
            )

        # 型チェック
        type_mismatches = _check_type_mismatches(df, StockPriceSchema.fields)

        if type_mismatches:
            mismatch_details = [
                f"{col}: expected {exp.__name__}, got {act.__name__}"
                for col, (exp, act) in type_mismatches.items()
            ]
            logger.warning(
                "Stock price validation failed: type mismatch",
                type_mismatches={
                    col: f"{exp.__name__} -> {act.__name__}"
                    for col, (exp, act) in type_mismatches.items()
                },
            )
            raise ValidationError(
                f"Type mismatch in columns: {', '.join(mismatch_details)}",
                type_mismatches=type_mismatches,
            )

        logger.debug("Stock price DataFrame validation successful", row_count=len(df))
        return True

    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during stock price validation",
            error=str(e),
            exc_info=True,
        )
        raise


def validate_economic_indicator_dataframe(df: pd.DataFrame) -> bool:
    """経済指標データフレームを検証する。

    DataFrame が EconomicIndicatorSchema に準拠しているかを検証します。
    検証項目:
    - DataFrame が空でないこと
    - 必須カラムが全て存在すること
    - 各カラムの型が正しいこと
    - 必須フィールド（series_id, date）に null 値がないこと

    Parameters
    ----------
    df : pd.DataFrame
        検証する DataFrame

    Returns
    -------
    bool
        検証成功時は True

    Raises
    ------
    ValidationError
        検証失敗時。以下の場合に発生:

        - DataFrame が空の場合
        - 必須カラムが欠落している場合
        - カラムの型が不一致の場合
        - 必須フィールドに null 値がある場合

    Examples
    --------
    >>> import pandas as pd
    >>> import datetime
    >>> df = pd.DataFrame({
    ...     "series_id": ["GDP"],
    ...     "date": [datetime.date(2024, 1, 1)],
    ...     "value": [25000.5],
    ...     "unit": ["billions_usd"],
    ... })
    >>> validate_economic_indicator_dataframe(df)
    True
    """
    logger.debug("Validating economic indicator DataFrame", row_count=len(df))

    try:
        # 空チェック
        _check_empty_dataframe(df)

        # 必須カラムチェック
        required_columns = set(EconomicIndicatorSchema.fields.keys())
        missing_columns = _check_missing_columns(df, required_columns)

        if missing_columns:
            logger.warning(
                "Economic indicator validation failed: missing columns",
                missing_columns=missing_columns,
            )
            raise ValidationError(
                f"Missing required columns: {', '.join(missing_columns)}. "
                f"Expected: {sorted(required_columns)}",
                missing_columns=missing_columns,
            )

        # null 値チェック（series_id と date は必須）
        null_check_columns = ["series_id", "date"]
        null_columns = _check_null_values(df, null_check_columns)

        if null_columns:
            logger.warning(
                "Economic indicator validation failed: null values in required columns",
                null_columns=null_columns,
            )
            raise ValidationError(
                f"Null values found in required columns: {', '.join(null_columns)}",
            )

        # 型チェック
        type_mismatches = _check_type_mismatches(df, EconomicIndicatorSchema.fields)

        if type_mismatches:
            mismatch_details = [
                f"{col}: expected {exp.__name__}, got {act.__name__}"
                for col, (exp, act) in type_mismatches.items()
            ]
            logger.warning(
                "Economic indicator validation failed: type mismatch",
                type_mismatches={
                    col: f"{exp.__name__} -> {act.__name__}"
                    for col, (exp, act) in type_mismatches.items()
                },
            )
            raise ValidationError(
                f"Type mismatch in columns: {', '.join(mismatch_details)}",
                type_mismatches=type_mismatches,
            )

        logger.debug(
            "Economic indicator DataFrame validation successful", row_count=len(df)
        )
        return True

    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during economic indicator validation",
            error=str(e),
            exc_info=True,
        )
        raise
