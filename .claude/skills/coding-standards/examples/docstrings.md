# NumPy 形式 Docstring 詳細例

NumPy 形式の Docstring の書き方と各セクションの詳細例です。

## 基本構造

```python
def function_name(param1: type1, param2: type2) -> return_type:
    """一行の短い説明。

    より詳細な説明（オプション）。
    複数行にわたって書くことができる。

    Parameters
    ----------
    param1 : type1
        param1 の説明
    param2 : type2
        param2 の説明

    Returns
    -------
    return_type
        戻り値の説明

    Raises
    ------
    ExceptionType
        例外が発生する条件

    See Also
    --------
    related_function : 関連する関数
    another_function : もう一つの関連関数

    Notes
    -----
    実装に関する補足情報。

    Examples
    --------
    >>> result = function_name(value1, value2)
    >>> print(result)
    expected_output
    """
```

## 関数の Docstring

### シンプルな関数

```python
def add(a: int, b: int) -> int:
    """2つの整数を加算する。

    Parameters
    ----------
    a : int
        最初の整数
    b : int
        2番目の整数

    Returns
    -------
    int
        a と b の合計

    Examples
    --------
    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    """
    return a + b
```

### 複雑な関数

```python
def fetch_market_data(
    symbols: list[str],
    start_date: datetime,
    end_date: datetime | None = None,
    interval: Literal["1d", "1wk", "1mo"] = "1d",
    include_dividends: bool = False,
) -> dict[str, DataFrame]:
    """指定銘柄の市場データを取得する。

    Yahoo Finance API を使用して、指定された銘柄の
    OHLCV データを取得する。

    Parameters
    ----------
    symbols : list[str]
        取得する銘柄のティッカーシンボル。
        例: ["AAPL", "MSFT", "GOOGL"]
    start_date : datetime
        データ取得開始日
    end_date : datetime | None, default=None
        データ取得終了日。
        None の場合は現在日時を使用。
    interval : {"1d", "1wk", "1mo"}, default="1d"
        データの時間間隔。
        - "1d": 日次
        - "1wk": 週次
        - "1mo": 月次
    include_dividends : bool, default=False
        配当情報を含めるかどうか

    Returns
    -------
    dict[str, DataFrame]
        銘柄シンボルをキーとし、OHLCV データを含む
        DataFrame を値とする辞書。
        各 DataFrame は以下のカラムを持つ:
        - Open: 始値
        - High: 高値
        - Low: 安値
        - Close: 終値
        - Volume: 出来高
        - Dividends: 配当（include_dividends=True の場合）

    Raises
    ------
    ValueError
        symbols が空リストの場合
    InvalidSymbolError
        無効なシンボルが含まれている場合
    NetworkError
        API への接続に失敗した場合

    See Also
    --------
    fetch_single_symbol : 単一銘柄のデータ取得
    download_historical : 履歴データの一括ダウンロード

    Notes
    -----
    - API レート制限により、大量のリクエストは
      自動的にスロットリングされる
    - キャッシュは 15 分間有効

    Examples
    --------
    基本的な使用方法:

    >>> from datetime import datetime
    >>> data = fetch_market_data(
    ...     ["AAPL", "MSFT"],
    ...     start_date=datetime(2024, 1, 1),
    ... )
    >>> data["AAPL"].head()
                  Open    High     Low   Close    Volume
    Date
    2024-01-02  185.5  186.25  184.75  185.80  50000000

    配当情報を含める:

    >>> data = fetch_market_data(
    ...     ["AAPL"],
    ...     start_date=datetime(2024, 1, 1),
    ...     include_dividends=True,
    ... )
    >>> data["AAPL"]["Dividends"].sum()
    0.96
    """
```

## クラスの Docstring

```python
class TaskRepository:
    """タスクの永続化を管理するリポジトリ。

    タスクの CRUD 操作を提供し、データベースとの
    やり取りを抽象化する。

    Parameters
    ----------
    connection : DatabaseConnection
        データベース接続オブジェクト
    cache_ttl : int, default=300
        キャッシュの有効期限（秒）

    Attributes
    ----------
    connection : DatabaseConnection
        データベース接続
    cache : Cache
        内部キャッシュ

    Examples
    --------
    >>> conn = DatabaseConnection("sqlite:///tasks.db")
    >>> repo = TaskRepository(conn)
    >>> task = repo.find_by_id("task-123")
    >>> print(task.title)
    'Sample Task'

    See Also
    --------
    UserRepository : ユーザーリポジトリ
    BaseRepository : 基底リポジトリクラス
    """

    def __init__(
        self,
        connection: DatabaseConnection,
        cache_ttl: int = 300,
    ) -> None:
        """リポジトリを初期化する。

        Parameters
        ----------
        connection : DatabaseConnection
            データベース接続オブジェクト
        cache_ttl : int, default=300
            キャッシュの有効期限（秒）
        """
        self.connection = connection
        self.cache = Cache(ttl=cache_ttl)

    def find_by_id(self, task_id: str) -> Task | None:
        """ID でタスクを検索する。

        Parameters
        ----------
        task_id : str
            検索するタスクの ID

        Returns
        -------
        Task | None
            見つかったタスク、または None
        """
```

## 特殊なセクション

### Yields（ジェネレータ）

```python
def generate_chunks[T](
    items: list[T],
    chunk_size: int,
) -> Iterator[list[T]]:
    """リストをチャンクに分割してイテレートする。

    Parameters
    ----------
    items : list[T]
        分割するリスト
    chunk_size : int
        各チャンクのサイズ

    Yields
    ------
    list[T]
        chunk_size 以下のサイズのリスト

    Examples
    --------
    >>> list(generate_chunks([1, 2, 3, 4, 5], 2))
    [[1, 2], [3, 4], [5]]
    """
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]
```

### Warns

```python
def deprecated_function(value: int) -> int:
    """非推奨: 代わりに new_function を使用してください。

    Parameters
    ----------
    value : int
        処理する値

    Returns
    -------
    int
        処理結果

    Warns
    -----
    DeprecationWarning
        この関数は非推奨であり、将来のバージョンで
        削除される予定

    See Also
    --------
    new_function : 推奨される代替関数
    """
    warnings.warn(
        "deprecated_function is deprecated, use new_function",
        DeprecationWarning,
        stacklevel=2,
    )
    return value * 2
```

### References

```python
def calculate_sharpe_ratio(
    returns: ndarray,
    risk_free_rate: float = 0.0,
) -> float:
    """シャープレシオを計算する。

    Parameters
    ----------
    returns : ndarray
        リターンの配列
    risk_free_rate : float, default=0.0
        無リスク金利

    Returns
    -------
    float
        シャープレシオ

    References
    ----------
    .. [1] Sharpe, W.F. (1966). "Mutual Fund Performance".
           Journal of Business. 39 (S1): 119-138.
    .. [2] https://en.wikipedia.org/wiki/Sharpe_ratio
    """
```

## 複雑な型の記述

### ネストした型

```python
def process_nested_data(
    data: dict[str, list[dict[str, Any]]],
) -> list[tuple[str, int]]:
    """ネストしたデータ構造を処理する。

    Parameters
    ----------
    data : dict[str, list[dict[str, Any]]]
        以下の構造を持つネストした辞書:
        {
            "category": [
                {"id": str, "value": int, ...},
                ...
            ],
            ...
        }

    Returns
    -------
    list[tuple[str, int]]
        (category, total_value) のタプルのリスト
    """
```

### Callable 型

```python
def apply_transform(
    data: list[int],
    transform: Callable[[int], int],
    predicate: Callable[[int], bool] | None = None,
) -> list[int]:
    """データに変換関数を適用する。

    Parameters
    ----------
    data : list[int]
        変換するデータ
    transform : Callable[[int], int]
        各要素に適用する変換関数。
        int を受け取り int を返す。
    predicate : Callable[[int], bool] | None, default=None
        フィルタ条件。
        None の場合は全要素を処理。

    Returns
    -------
    list[int]
        変換後のデータ

    Examples
    --------
    >>> apply_transform([1, 2, 3], lambda x: x * 2)
    [2, 4, 6]
    >>> apply_transform([1, 2, 3], lambda x: x * 2, lambda x: x > 1)
    [4, 6]
    """
```

## Examples セクションのベストプラクティス

```python
def parse_config(path: str) -> dict[str, Any]:
    """設定ファイルを読み込んでパースする。

    Parameters
    ----------
    path : str
        設定ファイルのパス

    Returns
    -------
    dict[str, Any]
        パースされた設定

    Examples
    --------
    基本的な使用方法:

    >>> config = parse_config("config.yaml")
    >>> config["database"]["host"]
    'localhost'

    環境変数の展開:

    >>> # config.yaml: host: ${DB_HOST}
    >>> import os
    >>> os.environ["DB_HOST"] = "production.db.example.com"
    >>> config = parse_config("config.yaml")
    >>> config["database"]["host"]
    'production.db.example.com'

    存在しないファイル:

    >>> parse_config("nonexistent.yaml")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    FileNotFoundError: Config file not found: nonexistent.yaml

    Notes
    -----
    Examples セクションのベストプラクティス:

    1. 基本的な使用例を最初に
    2. 特殊なケースやオプションの使用例
    3. エラーケースの例
    4. doctest で実行可能にする
    """
```
