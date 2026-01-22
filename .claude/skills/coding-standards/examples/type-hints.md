# 型ヒント詳細例（PEP 695）

Python 3.12+ の新しい型構文を使用した例集です。

## 基本的な型ヒント

```python
# 組み込み型を直接使用（typing からのインポート不要）
def process_items(items: list[str]) -> dict[str, int]:
    return {item: items.count(item) for item in set(items)}

# Union 型（| 演算子）
def get_value(data: dict[str, str]) -> str | None:
    return data.get("key")

# 複数の Union
def parse_input(value: str | int | float) -> str:
    return str(value)
```

## ジェネリック関数

```python
# PEP 695 新構文: 型パラメータを [] で定義
def first[T](items: list[T]) -> T | None:
    """リストの最初の要素を返す。"""
    return items[0] if items else None

# 複数の型パラメータ
def zip_dict[K, V](keys: list[K], values: list[V]) -> dict[K, V]:
    """キーと値のリストから辞書を作成する。"""
    return dict(zip(keys, values, strict=True))

# 戻り値も含むジェネリック
def transform[T, U](items: list[T], func: Callable[[T], U]) -> list[U]:
    """リストの各要素を変換する。"""
    return [func(item) for item in items]
```

## ジェネリッククラス

```python
class Stack[T]:
    """ジェネリックなスタック実装。"""

    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("Stack is empty")
        return self._items.pop()

    def peek(self) -> T | None:
        return self._items[-1] if self._items else None

    def __len__(self) -> int:
        return len(self._items)


# 使用例
int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)
value = int_stack.pop()  # int 型として推論される
```

## 境界付き型パラメータ

```python
from collections.abc import Hashable, Comparable

# Hashable 境界: set や dict のキーに使用可能
def unique[T: Hashable](items: list[T]) -> set[T]:
    """重複を除去する。"""
    return set(items)

# 複数の型を許容（Union 相当）
def stringify[T: (int, float, str)](value: T) -> str:
    """数値または文字列を文字列に変換する。"""
    return str(value)

# プロトコル境界
from typing import Protocol

class Comparable(Protocol):
    def __lt__(self, other: object) -> bool: ...

def min_value[T: Comparable](items: list[T]) -> T:
    """最小値を返す。"""
    return min(items)
```

## ParamSpec（デコレータ用）

```python
from collections.abc import Callable

# **P で ParamSpec を定義
def logged[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """関数呼び出しをログに記録するデコレータ。"""
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Returned {result}")
        return result
    return wrapper

@logged
def add(a: int, b: int) -> int:
    return a + b

# 型が保持される: add(1, 2) は int を返す


# リトライデコレータ
def retry[**P, R](
    max_attempts: int = 3,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """リトライ機能を追加するデコレータ。"""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_attempts - 1:
                        raise
            raise RuntimeError("Unreachable")
        return wrapper
    return decorator
```

## 型エイリアス

```python
# 基本的な型エイリアス
type UserId = str
type TaskId = str
type Timestamp = float

# Literal 型エイリアス
from typing import Literal
type TaskStatus = Literal["todo", "in_progress", "completed"]
type Priority = Literal["high", "medium", "low"]

# ジェネリック型エイリアス
type Nullable[T] = T | None
type Result[T, E] = tuple[T, None] | tuple[None, E]
type AsyncResult[T] = Coroutine[Any, Any, T]

# 複雑な型のエイリアス
type JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
type Callback[T] = Callable[[T], None]
type Handler[T, R] = Callable[[T], Awaitable[R]]

# 使用例
def get_user(user_id: UserId) -> Nullable[User]:
    return repository.find_by_id(user_id)

def process_task(task_id: TaskId, status: TaskStatus) -> None:
    ...
```

## TypedDict

```python
from typing import TypedDict, Required, NotRequired

# 基本的な TypedDict
class UserDict(TypedDict):
    id: str
    name: str
    email: str

# オプショナルフィールド付き
class TaskDict(TypedDict):
    id: Required[str]
    title: Required[str]
    description: NotRequired[str]
    completed: NotRequired[bool]

# 継承
class DetailedTaskDict(TaskDict):
    created_at: str
    updated_at: str
    assignee: NotRequired[UserDict]

# 使用例
task: TaskDict = {
    "id": "1",
    "title": "Sample Task",
    # description と completed はオプション
}
```

## Protocol（構造的部分型）

```python
from typing import Protocol, runtime_checkable

class Readable(Protocol):
    """読み取り可能なオブジェクトのプロトコル。"""

    def read(self, size: int = -1) -> bytes: ...

class Writable(Protocol):
    """書き込み可能なオブジェクトのプロトコル。"""

    def write(self, data: bytes) -> int: ...

# 複数のプロトコルを継承
class ReadWritable(Readable, Writable, Protocol):
    pass

# runtime_checkable で isinstance チェックを可能に
@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...

# 使用例
def copy_data(src: Readable, dst: Writable) -> None:
    data = src.read()
    dst.write(data)

# 任意のクラスが Protocol を満たせば使用可能
# 明示的な継承は不要
```

## Self 型

```python
from typing import Self

class Builder:
    """ビルダーパターンの実装。"""

    def __init__(self) -> None:
        self._name: str = ""
        self._value: int = 0

    def with_name(self, name: str) -> Self:
        self._name = name
        return self

    def with_value(self, value: int) -> Self:
        self._value = value
        return self

    def build(self) -> dict[str, object]:
        return {"name": self._name, "value": self._value}

# メソッドチェーンが可能
result = Builder().with_name("test").with_value(42).build()
```

## Callable の詳細

```python
from collections.abc import Callable, Awaitable

# 基本的な Callable
type SimpleFunc = Callable[[int, str], bool]

# 可変長引数
type VarArgsFunc = Callable[..., int]

# 非同期関数
type AsyncFunc[T, R] = Callable[[T], Awaitable[R]]

# コールバック
type EventHandler = Callable[[Event], None]
type AsyncEventHandler = Callable[[Event], Awaitable[None]]

# 使用例
def process(
    items: list[int],
    transformer: Callable[[int], str],
) -> list[str]:
    return [transformer(item) for item in items]
```

## 高度なパターン

```python
from typing import TypeVar, overload

# オーバーロード
@overload
def get_item(items: list[str], index: int) -> str: ...
@overload
def get_item(items: list[str], index: slice) -> list[str]: ...

def get_item(items: list[str], index: int | slice) -> str | list[str]:
    return items[index]

# Never 型（到達不能コード）
from typing import Never

def raise_error(message: str) -> Never:
    raise RuntimeError(message)

# assert_never でパターンマッチの網羅性チェック
from typing import assert_never

def handle_status(status: TaskStatus) -> str:
    match status:
        case "todo":
            return "Not started"
        case "in_progress":
            return "Working"
        case "completed":
            return "Done"
        case _:
            assert_never(status)  # 型チェッカーが警告
```
