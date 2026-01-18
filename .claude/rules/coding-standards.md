# コーディング規約

## 概要

| 項目 | 規約 |
|------|------|
| 型ヒント | Python 3.12+ スタイル（PEP 695） |
| Docstring | NumPy 形式 |
| クラス名 | PascalCase |
| 関数/変数名 | snake_case |
| 定数 | UPPER_SNAKE |
| プライベート | _prefix |

## 型ヒント（Python 3.12+ / PEP 695）

```python
# 組み込み型を直接使用
def process_items(items: list[str]) -> dict[str, int]:
    return {item: items.count(item) for item in set(items)}

# ジェネリック関数・クラス（PEP 695 新構文）
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

# ParamSpec（デコレータ用）
def logged[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

# 境界付き型パラメータ
def unique[T: Hashable](items: list[T]) -> set[T]:
    return set(items)
```

## 命名規則

```python
# 変数: snake_case、名詞
user_name = "John"
is_completed = True  # Boolean: is_, has_, should_, can_

# 関数: snake_case、動詞で始める
def fetch_user_data() -> User: ...
def validate_email(email: str) -> bool: ...

# クラス: PascalCase、名詞
class TaskManager: ...
class UserAuthenticationService: ...

# 定数: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.example.com"

# ファイル名: snake_case.py
# task_service.py, user_repository.py
```

## Docstring（NumPy 形式）

```python
def process_items(
    items: list[dict[str, Any]],
    max_count: int = 100,
    validate: bool = True,
) -> list[dict[str, Any]]:
    """Process a list of items with optional validation.

    Parameters
    ----------
    items : list[dict[str, Any]]
        List of items to process
    max_count : int, default=100
        Maximum number of items to process
    validate : bool, default=True
        Whether to validate items before processing

    Returns
    -------
    list[dict[str, Any]]
        Processed items

    Raises
    ------
    ValueError
        If items is empty when validation is enabled

    Examples
    --------
    >>> items = [{"id": 1, "name": "test"}]
    >>> result = process_items(items)
    >>> len(result)
    1
    """
```

## 関数設計

- **単一責務**: 1関数 = 1つの責務
- **関数の長さ**: 目標20行以内、推奨50行以内、100行以上はリファクタ
- **パラメータ数**: 多い場合はdataclassでまとめる

```python
# dataclassでパラメータをまとめる
@dataclass
class CreateTaskOptions:
    title: str
    description: str | None = None
    priority: Literal["high", "medium", "low"] = "medium"

def create_task(options: CreateTaskOptions) -> Task:
    ...
```

## エラーメッセージ

```python
# 具体的で解決策を示す
raise ValueError(f"Expected positive integer, got {count}")
raise ValueError(f"Failed to process {source_file}: {e}")
raise FileNotFoundError(f"Config not found. Create by: python -m {__package__}.init")
```

## アンカーコメント

```python
# AIDEV-NOTE: 実装の意図や背景の説明
# AIDEV-TODO: 未完了タスク
# AIDEV-QUESTION: 確認が必要な疑問点
```

## 詳細参照

完全なコーディング規約: `docs/coding-standards.md`
