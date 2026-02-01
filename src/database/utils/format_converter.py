"""Format converter utilities for Parquet/JSON conversion.

Issue #951: Parquet/JSON形式間のフォーマット変換ユーティリティ

このモジュールはParquetファイルとJSONファイル間の相互変換機能を提供する。
pyarrowを使用してデータ型を正しく保持しながら変換を行う。
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from utils_core.logging import get_logger

logger = get_logger(__name__)


def parquet_to_json(input_path: Path, output_path: Path) -> bool:
    """Parquetファイルを読み込み、JSON形式で出力する。

    Parameters
    ----------
    input_path : Path
        入力Parquetファイルのパス
    output_path : Path
        出力JSONファイルのパス

    Returns
    -------
    bool
        変換成功時True

    Raises
    ------
    FileNotFoundError
        入力ファイルが存在しない場合
    ValueError
        入力ファイルが有効なParquet形式でない場合

    Examples
    --------
    >>> parquet_to_json(Path("data.parquet"), Path("data.json"))
    True
    """
    logger.debug(
        "Starting Parquet to JSON conversion",
        input_path=str(input_path),
        output_path=str(output_path),
    )

    # ファイル存在チェック
    if not input_path.exists():
        logger.error(
            "Input file not found",
            input_path=str(input_path),
        )
        raise FileNotFoundError(f"File not found: {input_path}")

    # Parquetファイルの読み込み
    try:
        table = pq.read_table(input_path)
        logger.debug(
            "Parquet file loaded",
            rows=len(table),
            columns=table.column_names,
        )
    except Exception as e:
        logger.error(
            "Failed to read Parquet file",
            input_path=str(input_path),
            error=str(e),
        )
        raise ValueError(f"Invalid Parquet file: {input_path}") from e

    # DataFrameに変換
    df = table.to_pandas()

    # JSONに変換可能な形式に変換
    records = _dataframe_to_records(df)

    # 出力ディレクトリを作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # JSONファイルに書き込み
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=_json_serializer)

    logger.info(
        "Parquet to JSON conversion completed",
        input_path=str(input_path),
        output_path=str(output_path),
        rows=len(records),
    )

    return True


def json_to_parquet(input_path: Path, output_path: Path) -> bool:
    """JSONファイルを読み込み、Parquet形式で出力する。

    Parameters
    ----------
    input_path : Path
        入力JSONファイルのパス
    output_path : Path
        出力Parquetファイルのパス

    Returns
    -------
    bool
        変換成功時True

    Raises
    ------
    FileNotFoundError
        入力ファイルが存在しない場合
    ValueError
        入力ファイルが有効なJSON形式でない場合
        データが空の場合

    Examples
    --------
    >>> json_to_parquet(Path("data.json"), Path("data.parquet"))
    True
    """
    logger.debug(
        "Starting JSON to Parquet conversion",
        input_path=str(input_path),
        output_path=str(output_path),
    )

    # ファイル存在チェック
    if not input_path.exists():
        logger.error(
            "Input file not found",
            input_path=str(input_path),
        )
        raise FileNotFoundError(f"File not found: {input_path}")

    # JSONファイルの読み込み
    try:
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(
            "JSON file loaded",
            data_type=type(data).__name__,
        )
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse JSON file",
            input_path=str(input_path),
            error=str(e),
        )
        raise ValueError(f"Invalid JSON: {input_path}") from e

    # データがリスト形式であることを確認
    if not isinstance(data, list):
        logger.error(
            "JSON data must be a list of records",
            input_path=str(input_path),
            actual_type=type(data).__name__,
        )
        raise ValueError(
            f"Invalid JSON: Expected list of records, got {type(data).__name__}"
        )

    # 空データチェック
    if len(data) == 0:
        logger.error(
            "Empty data in JSON file",
            input_path=str(input_path),
        )
        raise ValueError(f"Empty data: {input_path}")

    # レコードをPyArrow Tableに変換
    try:
        table = _records_to_table(data)
        logger.debug(
            "Data converted to PyArrow Table",
            rows=len(table),
            columns=table.column_names,
        )
    except Exception as e:
        logger.error(
            "Failed to convert data to PyArrow Table",
            input_path=str(input_path),
            error=str(e),
        )
        raise ValueError(f"Failed to convert JSON data: {e}") from e

    # 出力ディレクトリを作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parquetファイルに書き込み
    pq.write_table(table, output_path)

    logger.info(
        "JSON to Parquet conversion completed",
        input_path=str(input_path),
        output_path=str(output_path),
        rows=len(table),
    )

    return True


def _dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """DataFrameをレコードのリストに変換する。

    各行を辞書に変換し、pandas/numpy固有の型をPython標準型に変換する。

    Parameters
    ----------
    df : pd.DataFrame
        変換するDataFrame

    Returns
    -------
    list[dict[str, Any]]
        レコードのリスト。各辞書のキーはカラム名、値はPython標準型に変換済み。
    """
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        record: dict[str, Any] = {}
        for col in df.columns:
            value = row[col]
            # pandas/numpy 型をPython標準型に変換
            record[col] = _convert_to_python_type(value)
        records.append(record)
    return records


def _convert_to_python_type(value: Any) -> Any:
    """pandas/numpy型をPython標準型に変換する。

    pandas/numpyのデータ型（numpy.int64, numpy.float64, pd.Timestamp等）を
    JSONシリアライズ可能なPython標準型に変換する。ネスト構造（dict, list）も
    再帰的に処理する。

    Parameters
    ----------
    value : Any
        変換する値。None, pandas/numpy型, dict, list, または標準型。

    Returns
    -------
    Any
        Python標準型に変換された値:
        - np.integer → int
        - np.floating → float
        - np.bool_ → bool
        - pd.Timestamp/np.datetime64 → ISO 8601文字列
        - np.ndarray → list
        - pd.NaT/np.nan → None
        - dict/list → 再帰的に変換
    """
    # None/NaN 処理
    if pd.isna(value):
        return None

    # numpy 整数型
    if isinstance(value, np.integer):
        return int(value)

    # numpy 浮動小数点型
    if isinstance(value, np.floating):
        return float(value)

    # numpy 論理型
    if isinstance(value, np.bool_):
        return bool(value)

    # Timestamp 型
    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    # datetime64 型
    if isinstance(value, np.datetime64):
        return pd.Timestamp(value).isoformat()

    # numpy ndarray (リスト変換)
    if isinstance(value, np.ndarray):
        return value.tolist()

    # dict型（ネスト構造）
    if isinstance(value, dict):
        return {k: _convert_to_python_type(v) for k, v in value.items()}

    # list型（ネスト構造）
    if isinstance(value, list):
        return [_convert_to_python_type(item) for item in value]

    return value


def _records_to_table(records: list[dict[str, Any]]) -> pa.Table:
    """レコードのリストをPyArrow Tableに変換する。

    全レコードからカラム名を収集し、各カラムの値を適切なPyArrow型に
    変換してTableを構築する。異なる型が混在する場合やネスト構造は
    文字列（JSON）として格納する。

    Parameters
    ----------
    records : list[dict[str, Any]]
        レコードのリスト。各レコードは {column_name: value} の辞書。
        異なるレコード間でキーが異なっていてもよい。

    Returns
    -------
    pa.Table
        全レコードを含むPyArrow Table。空のリストの場合は空のTableを返す。
    """
    if not records:
        return pa.table({})

    # 全レコードの列名を収集
    all_columns: set[str] = set()
    for record in records:
        all_columns.update(record.keys())

    # 各列のデータを収集
    columns_data: dict[str, list[Any]] = {col: [] for col in all_columns}

    for record in records:
        for col in all_columns:
            value = record.get(col)
            columns_data[col].append(value)

    # PyArrow 配列に変換
    arrays = {}
    for col, values in columns_data.items():
        # 型を推論して配列を作成
        arrays[col] = _create_pyarrow_array(values)

    return pa.table(arrays)


def _create_pyarrow_array(values: list[Any]) -> pa.Array:
    """値のリストからPyArrow配列を作成する。

    値の型を分析し、適切なPyArrow型で配列を作成する。
    - 全てNoneの場合: null配列
    - ネスト構造(dict/list)が含まれる場合: JSON文字列として格納
    - 混合型の場合: 全て文字列に変換
    - 単一型の場合: PyArrowの自動型推論を使用

    Parameters
    ----------
    values : list[Any]
        配列に変換する値のリスト。None値を含んでもよい。

    Returns
    -------
    pa.Array
        PyArrow配列。型は値の内容に応じて自動決定される。
    """
    # 非None値の型を確認
    non_none_values = [v for v in values if v is not None]

    if not non_none_values:
        # 全てNoneの場合はnull配列
        return pa.nulls(len(values))

    # 全ての型を収集
    types_found = set(type(v).__name__ for v in non_none_values)

    # ネスト構造（dict/list）が含まれる場合
    if any(isinstance(v, (dict, list)) for v in non_none_values):
        # JSON文字列に変換して格納
        json_values = [
            json.dumps(v, ensure_ascii=False, default=_json_serializer)
            if v is not None
            else None
            for v in values
        ]
        return pa.array(json_values, type=pa.string())

    # 混合型の場合（異なる型が混在）
    if len(types_found) > 1:
        # 全てを文字列に変換
        str_values = [str(v) if v is not None else None for v in values]
        return pa.array(str_values, type=pa.string())

    # 単一型の場合はpyarrowの自動推論に任せる
    try:
        return pa.array(values)
    except (pa.ArrowTypeError, pa.ArrowInvalid):
        # 型推論に失敗した場合は文字列に変換
        str_values = [str(v) if v is not None else None for v in values]
        return pa.array(str_values, type=pa.string())


def _json_serializer(obj: Any) -> Any:
    """JSONシリアライズのカスタムハンドラー。

    json.dump()のdefault引数として使用し、標準のJSONエンコーダでは
    処理できないpandas/numpy型を変換する。

    Parameters
    ----------
    obj : Any
        シリアライズする値。pandas/numpy型が想定される。

    Returns
    -------
    Any
        シリアライズ可能なPython標準型:
        - pd.Timestamp → ISO 8601文字列
        - np.datetime64 → ISO 8601文字列
        - np.integer → int
        - np.floating → float
        - np.bool_ → bool
        - np.ndarray → list

    Raises
    ------
    TypeError
        サポートされていない型の場合。
    """
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, np.datetime64):
        return pd.Timestamp(obj).isoformat()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()

    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
