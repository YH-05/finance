# 実装ガイド (Implementation Guide)

このドキュメントは参照用として保持されています。
**最新のコーディング規約は coding-standards スキルを参照してください。**

## スキル参照

| リソース | パス |
|---------|------|
| クイックリファレンス | `.claude/skills/coding-standards/SKILL.md` |
| 詳細ガイド | `.claude/skills/coding-standards/guide.md` |
| 型ヒント例 | `.claude/skills/coding-standards/examples/type-hints.md` |
| Docstring例 | `.claude/skills/coding-standards/examples/docstrings.md` |
| エラーメッセージ例 | `.claude/skills/coding-standards/examples/error-messages.md` |
| 命名規則例 | `.claude/skills/coding-standards/examples/naming.md` |
| ロギング例 | `.claude/skills/coding-standards/examples/logging.md` |

## 概要

| 項目 | 規約 |
|------|------|
| 型ヒント | Python 3.12+ スタイル（PEP 695） |
| Docstring | NumPy 形式 |
| クラス名 | PascalCase |
| 関数/変数名 | snake_case |
| 定数 | UPPER_SNAKE |
| プライベート | _prefix |

---

**注**: 以下の内容はレガシー参照用です。最新情報はスキルを確認してください。

---

## Python 規約

### 型ヒント

**Python 3.12+ スタイル（PEP 695）**:

```python
# ✅ 良い例: 組み込み型を直接使用
def process_items(items: list[str]) -> dict[str, int]:
    return {item: items.count(item) for item in set(items)}

# ❌ 悪い例: typing モジュールからインポート（Python 3.9以降は不要）
from typing import List, Dict
def process_items(items: List[str]) -> Dict[str, int]: ...
```

**ジェネリック関数・クラス（PEP 695）**:

```python
# ✅ 良い例: PEP 695 の新構文（Python 3.12以上）
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

# ❌ 悪い例: 従来の TypeVar を使用（Python 3.11以前のスタイル）
from typing import TypeVar, Generic
T = TypeVar("T")

def first(items: list[T]) -> T | None: ...

class Stack(Generic[T]):
    ...
```

**ParamSpec（デコレータ用）**:

```python
from collections.abc import Callable

# ✅ 良い例: PEP 695 の **P 構文
def logged[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

# ❌ 悪い例: 従来の ParamSpec を使用
from typing import ParamSpec, TypeVar
P = ParamSpec("P")
R = TypeVar("R")
```

**境界付き型パラメータ**:

```python
from collections.abc import Hashable

# ✅ 良い例: 境界付き型パラメータ
def unique[T: Hashable](items: list[T]) -> set[T]:
    return set(items)

# 複数の境界（Union相当）
def stringify[T: (int, float, str)](value: T) -> str:
    return str(value)
```

**型注釈の原則**:

```python
# ✅ 良い例: 明示的な型注釈
def calculate_total(prices: list[float]) -> float:
    return sum(prices)

# ❌ 悪い例: 型注釈なし
def calculate_total(prices):  # 型が不明
    return sum(prices)
```

**dataclass vs TypedDict**:

```python
from dataclasses import dataclass
from typing import TypedDict

# dataclass: メソッドを持つオブジェクト型
@dataclass
class Task:
    id: str
    title: str
    completed: bool = False

    def mark_complete(self) -> None:
        self.completed = True

# TypedDict: 辞書型のスキーマ定義
class TaskDict(TypedDict):
    id: str
    title: str
    completed: bool

# 型エイリアス: ユニオン型、リテラル型など
type TaskStatus = Literal["todo", "in_progress", "completed"]
type TaskId = str
type Nullable[T] = T | None
```

### 命名規則

**変数・関数**:

```python
# 変数: snake_case、名詞
user_name = "John"
task_list = []
is_completed = True

# 関数: snake_case、動詞で始める
def fetch_user_data() -> User: ...
def validate_email(email: str) -> bool: ...
def calculate_total_price(items: list[Item]) -> float: ...

# Boolean: is_, has_, should_, can_ で始める
is_valid = True
has_permission = False
should_retry = True
can_delete = False
```

**クラス・型**:

```python
# クラス: PascalCase、名詞
class TaskManager: ...
class UserAuthenticationService: ...

# Protocol（インターフェース相当）: PascalCase
from typing import Protocol

class TaskRepository(Protocol):
    def save(self, task: Task) -> None: ...
    def find_by_id(self, id: str) -> Task | None: ...

# 型エイリアス: PascalCase
type TaskStatus = Literal["todo", "in_progress", "completed"]
```

**定数**:

```python
# UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.example.com"
DEFAULT_TIMEOUT = 5000

# 設定オブジェクトの場合（イミュータブル）
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    max_retry_count: int = 3
    api_base_url: str = "https://api.example.com"
    default_timeout: int = 5000

CONFIG = Config()
```

**ファイル名**:

-   全て snake_case.py
    -   task_service.py
    -   user_repository.py
    -   format_date.py
    -   validate_email.py
-   テストファイル
    -   test_task_service.py
    -   test_user_repository.py
-   定数ファイル
    -   constants.py
    -   error_messages.py

### 関数設計

**単一責務の原則**:

```python
# ✅ 良い例: 単一の責務
def calculate_total_price(items: list[CartItem]) -> float:
    return sum(item.price * item.quantity for item in items)

def format_price(amount: float) -> str:
    return f"¥{amount:,.0f}"

# ❌ 悪い例: 複数の責務
def calculate_and_format_price(items: list[CartItem]) -> str:
    total = sum(item.price * item.quantity for item in items)
    return f"¥{total:,.0f}"
```

**関数の長さ**:

-   目標: 20 行以内
-   推奨: 50 行以内
-   100 行以上: リファクタリングを検討

**パラメータの数**:

```python
from dataclasses import dataclass

# ✅ 良い例: dataclassでまとめる
@dataclass
class CreateTaskOptions:
    title: str
    description: str | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    due_date: datetime | None = None

def create_task(options: CreateTaskOptions) -> Task:
    ...

# ❌ 悪い例: パラメータが多すぎる
def create_task(
    title: str,
    description: str,
    priority: str,
    due_date: datetime,
    tags: list[str],
    assignee: str,
) -> Task:
    ...
```

### エラーハンドリング

**カスタム例外クラス**:

```python
class ValidationError(Exception):
    """入力検証エラー"""

    def __init__(self, message: str, field: str, value: object) -> None:
        super().__init__(message)
        self.field = field
        self.value = value


class NotFoundError(Exception):
    """リソースが見つからないエラー"""

    def __init__(self, resource: str, id: str) -> None:
        super().__init__(f"{resource} not found: {id}")
        self.resource = resource
        self.id = id


class DatabaseError(Exception):
    """データベースエラー"""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause
```

**エラーハンドリングパターン**:

```python
# ✅ 良い例: 適切なエラーハンドリング
async def get_task(id: str) -> Task:
    try:
        task = await repository.find_by_id(id)

        if task is None:
            raise NotFoundError("Task", id)

        return task
    except NotFoundError:
        # 予期されるエラー: 適切に処理
        logger.warning(f"タスクが見つかりません: {id}")
        raise
    except Exception as e:
        # 予期しないエラー: ラップして上位に伝播
        raise DatabaseError("タスクの取得に失敗しました", cause=e) from e

# ❌ 悪い例: エラーを無視
async def get_task(id: str) -> Task | None:
    try:
        return await repository.find_by_id(id)
    except Exception:
        return None  # エラー情報が失われる
```

**エラーメッセージ**:

```python
# ✅ 良い例: 具体的で解決策を示す
raise ValidationError(
    f"タイトルは1-200文字で入力してください。現在の文字数: {len(title)}",
    field="title",
    value=title,
)

# ❌ 悪い例: 曖昧で役に立たない
raise ValueError("Invalid input")
```

### 非同期処理

**async/await の使用**:

```python
import asyncio

# ✅ 良い例: async/await
async def fetch_user_tasks(user_id: str) -> list[Task]:
    try:
        user = await user_repository.find_by_id(user_id)
        tasks = await task_repository.find_by_user_id(user.id)
        return tasks
    except Exception as e:
        logger.error("タスクの取得に失敗", exc_info=True)
        raise
```

**並列処理**:

```python
import asyncio

# ✅ 良い例: asyncio.gatherで並列実行
async def fetch_multiple_users(ids: list[str]) -> list[User]:
    tasks = [user_repository.find_by_id(id) for id in ids]
    return await asyncio.gather(*tasks)

# ❌ 悪い例: 逐次実行
async def fetch_multiple_users(ids: list[str]) -> list[User]:
    users: list[User] = []
    for id in ids:
        user = await user_repository.find_by_id(id)  # 遅い
        users.append(user)
    return users
```

## コメント規約

### ドキュメントコメント

**NumPy 形式**:

```python
async def create_task(data: CreateTaskData) -> Task:
    """タスクを作成する。

    Parameters
    ----------
    data : CreateTaskData
        作成するタスクのデータ

    Returns
    -------
    Task
        作成されたタスク

    Raises
    ------
    ValidationError
        データが不正な場合
    DatabaseError
        データベースエラーの場合

    Examples
    --------
    >>> task = await create_task(CreateTaskData(title="新しいタスク", priority="high"))
    >>> print(task.id)
    'abc123'
    """
    ...
```

### インラインコメント

**良いコメント**:

```python
# ✅ 理由を説明
# キャッシュを無効化して最新データを取得
cache.clear()

# ✅ 複雑なロジックを説明
# Kadaneのアルゴリズムで最大部分配列和を計算
# 時間計算量: O(n)
max_so_far = arr[0]
max_ending_here = arr[0]

# ✅ AIDEV-NOTE/TODO/FIXME を活用
# AIDEV-NOTE: パフォーマンス最適化のためキャッシュを導入
# AIDEV-TODO: キャッシュ機能を実装 (Issue #123)
# FIXME: 大量データでパフォーマンス劣化 (Issue #456)
```

**悪いコメント**:

```python
# ❌ コードの内容を繰り返すだけ
# iを1増やす
i += 1

# ❌ 古い情報
# このコードは2020年に追加された (不要な情報)

# ❌ コメントアウトされたコード
# old_implementation = lambda: ...  # 削除すべき
```

## セキュリティ

### 入力検証

```python
import re

# ✅ 良い例: 厳密な検証
def validate_email(email: str) -> None:
    if not email or not isinstance(email, str):
        raise ValidationError("メールアドレスは必須です", "email", email)

    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    if not re.match(email_regex, email):
        raise ValidationError("メールアドレスの形式が不正です", "email", email)

    if len(email) > 254:
        raise ValidationError("メールアドレスが長すぎます", "email", email)

# ❌ 悪い例: 検証なし
def validate_email(email: str) -> None:
    pass  # 検証なし
```

### 機密情報の管理

```python
import os

# ✅ 良い例: 環境変数から読み込み
api_key = os.environ.get("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY環境変数が設定されていません")

# ❌ 悪い例: ハードコード
api_key = "sk-1234567890abcdef"  # 絶対にしない！
```

## パフォーマンス

### データ構造の選択

```python
# ✅ 良い例: dictで O(1) アクセス
user_map = {u.id: u for u in users}
user = user_map.get(user_id)  # O(1)

# ❌ 悪い例: リストで O(n) 検索
user = next((u for u in users if u.id == user_id), None)  # O(n)
```

### ループの最適化

```python
# ✅ 良い例: リスト内包表記
results = [process(item) for item in items]

# ✅ 良い例: ジェネレータ（メモリ効率）
results = (process(item) for item in items)

# ❌ 悪い例: 逐次append
results = []
for item in items:
    results.append(process(item))
```

### メモ化

```python
from functools import lru_cache

# 計算結果のキャッシュ
@lru_cache(maxsize=128)
def expensive_calculation(input: str) -> Result:
    # 重い計算
    return result
```

## ライブラリ別ベストプラクティス

### yfinance

> **詳細ドキュメント**: `docs/yfinance-best-practices.md`

**curl_cffi によるセッション管理**:

```python
import curl_cffi
import yfinance as yf

class YfinanceFetcher:
    def __init__(self):
        # クラスレベルでセッションを共有（リソース効率化）
        self.session = curl_cffi.requests.Session(impersonate="safari15_5")

    def get_data(self, symbol: str):
        ticker = yf.Ticker(symbol, session=self.session)
        return ticker.info
```

**複数銘柄の一括取得**:

```python
# ✅ 良い例: 一括ダウンロード
df = yf.download(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="2y",
    session=session,
    auto_adjust=False,
)

# ❌ 悪い例: ループで個別取得
for ticker in tickers:
    yf.download(ticker, ...)  # 非効率
```

**yfinance クラスの使い分け**:

| クラス | 用途 | session |
|--------|------|---------|
| `yf.Ticker` | 個別銘柄データ | 推奨 |
| `yf.Sector` | セクター情報 | 推奨 |
| `yf.Search` | ニュース検索 | 不要 |
| `yf.download()` | 価格データ一括取得 | 推奨（日次以上） |

**エラーハンドリング**:

```python
for symbol in symbols:
    try:
        data = yf.Ticker(symbol, session=session).info

        if data is None:  # None チェック必須
            logger.warning(f"{symbol}: データがNone")
            continue

    except AttributeError as e:
        logger.error(f"{symbol}: 属性エラー - {e}")
        continue
    except Exception as e:
        logger.error(f"{symbol}: {type(e).__name__}: {e}")
        continue
```

**タイムゾーン処理**:

```python
# 米国市場時間を考慮
now_et = pd.Timestamp.now(tz="America/New_York")
```

---

## テストコード

### テストの構造 (Given-When-Then)

```python
import pytest
from task_service import TaskService, ValidationError


class TestTaskService:
    """TaskServiceのテストクラス"""

    class TestCreate:
        """createメソッドのテスト"""

        def test_正常なデータでタスクを作成できる(self, mock_repository):
            # Given: 準備
            service = TaskService(mock_repository)
            task_data = {"title": "テストタスク", "description": "テスト用の説明"}

            # When: 実行
            result = service.create(task_data)

            # Then: 検証
            assert result is not None
            assert result.id is not None
            assert result.title == "テストタスク"
            assert result.description == "テスト用の説明"
            assert isinstance(result.created_at, datetime)

        def test_タイトルが空の場合ValidationErrorを送出する(self, mock_repository):
            # Given: 準備
            service = TaskService(mock_repository)
            invalid_data = {"title": ""}

            # When/Then: 実行と検証
            with pytest.raises(ValidationError):
                service.create(invalid_data)
```

### モックの作成

```python
from unittest.mock import Mock, AsyncMock

# ✅ 良い例: Mockオブジェクトの使用
mock_repository = Mock(spec=TaskRepository)

# 戻り値の設定
mock_repository.find_by_id.return_value = mock_task

# 条件付き戻り値
def find_by_id_side_effect(id: str) -> Task | None:
    if id == "existing-id":
        return mock_task
    return None

mock_repository.find_by_id.side_effect = find_by_id_side_effect

# 非同期モック
mock_async_repository = AsyncMock(spec=TaskRepository)
mock_async_repository.find_by_id.return_value = mock_task
```

## リファクタリング

### マジックナンバーの排除

```python
# ✅ 良い例: 定数を定義
MAX_RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 1.0

for i in range(MAX_RETRY_COUNT):
    try:
        return await fetch_data()
    except Exception:
        if i < MAX_RETRY_COUNT - 1:
            await asyncio.sleep(RETRY_DELAY_SECONDS)

# ❌ 悪い例: マジックナンバー
for i in range(3):
    try:
        return await fetch_data()
    except Exception:
        if i < 2:
            await asyncio.sleep(1)
```

### 関数の抽出

```python
# ✅ 良い例: 関数を抽出
def process_order(order: Order) -> None:
    validate_order(order)
    calculate_total(order)
    apply_discounts(order)
    save_order(order)

def validate_order(order: Order) -> None:
    if not order.items:
        raise ValidationError("商品が選択されていません", "items", order.items)

def calculate_total(order: Order) -> None:
    order.total = sum(item.price * item.quantity for item in order.items)

# ❌ 悪い例: 長い関数
def process_order(order: Order) -> None:
    if not order.items:
        raise ValidationError("商品が選択されていません", "items", order.items)

    order.total = sum(item.price * item.quantity for item in order.items)

    if order.coupon:
        order.total -= order.total * order.coupon.discount_rate

    repository.save(order)
```

## チェックリスト

実装完了前に確認:

### コード品質

-   [ ] 命名が明確で一貫している（snake_case 統一）
-   [ ] 関数が単一の責務を持っている
-   [ ] マジックナンバーがない
-   [ ] 型ヒントが適切に記載されている
-   [ ] エラーハンドリングが実装されている

### セキュリティ

-   [ ] 入力検証が実装されている
-   [ ] 機密情報がハードコードされていない
-   [ ] SQL インジェクション対策がされている

### パフォーマンス

-   [ ] 適切なデータ構造を使用している（dict, set）
-   [ ] 不要な計算を避けている
-   [ ] ループが最適化されている（内包表記）

### テスト

-   [ ] ユニットテストが書かれている（pytest）
-   [ ] テストがパスする（make test）
-   [ ] エッジケースがカバーされている

### ドキュメント

-   [ ] 関数・クラスに NumPy 形式の docstring がある
-   [ ] 複雑なロジックにコメントがある
-   [ ] AIDEV-TODO/FIXME が記載されている（該当する場合）

### ツール

-   [ ] Ruff エラーがない（make lint）
-   [ ] 型チェックがパスする（make typecheck）
-   [ ] フォーマットが統一されている（make format）
