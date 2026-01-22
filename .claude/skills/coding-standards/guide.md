# Python コーディング規約 詳細ガイド

このガイドでは、SKILL.md のクイックリファレンスを補完する詳細な規約とパターンを説明します。

## 型ヒント詳細

### dataclass vs TypedDict

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

# TypedDict: 辞書型のスキーマ定義（JSON 互換）
class TaskDict(TypedDict):
    id: str
    title: str
    completed: bool

# 使い分け
# - dataclass: ドメインオブジェクト、ビジネスロジックを持つ
# - TypedDict: API レスポンス、設定ファイル、JSON データ
```

### Protocol（インターフェース）

```python
from typing import Protocol

class TaskRepository(Protocol):
    """タスクリポジトリのインターフェース定義。"""

    def save(self, task: Task) -> None: ...
    def find_by_id(self, id: str) -> Task | None: ...
    def find_all(self) -> list[Task]: ...

# 実装クラスは Protocol を継承しなくても良い（構造的部分型）
class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def save(self, task: Task) -> None:
        self._tasks[task.id] = task

    def find_by_id(self, id: str) -> Task | None:
        return self._tasks.get(id)

    def find_all(self) -> list[Task]:
        return list(self._tasks.values())
```

### 型エイリアス（PEP 695）

```python
# 型エイリアスの定義
type TaskId = str
type UserId = str
type TaskStatus = Literal["todo", "in_progress", "completed"]

# ジェネリック型エイリアス
type Nullable[T] = T | None
type Result[T, E] = tuple[T, None] | tuple[None, E]

# 使用例
def get_task(task_id: TaskId) -> Nullable[Task]:
    return repository.find_by_id(task_id)
```

## 関数設計

### 単一責務の原則

```python
# 良い例: 単一の責務
def calculate_total_price(items: list[CartItem]) -> float:
    """合計金額を計算する。"""
    return sum(item.price * item.quantity for item in items)

def format_price(amount: float) -> str:
    """金額をフォーマットする。"""
    return f"¥{amount:,.0f}"

def apply_discount(amount: float, rate: float) -> float:
    """割引を適用する。"""
    return amount * (1 - rate)

# 悪い例: 複数の責務
def calculate_and_format_price_with_discount(
    items: list[CartItem],
    discount_rate: float,
) -> str:
    # 計算、割引適用、フォーマットを全て行う（分離すべき）
    total = sum(item.price * item.quantity for item in items)
    discounted = total * (1 - discount_rate)
    return f"¥{discounted:,.0f}"
```

### パラメータ数の管理

```python
from dataclasses import dataclass
from typing import Literal

# パラメータが多い場合は dataclass でまとめる
@dataclass
class CreateTaskOptions:
    title: str
    description: str | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    due_date: datetime | None = None
    tags: list[str] | None = None
    assignee_id: str | None = None

def create_task(options: CreateTaskOptions) -> Task:
    """タスクを作成する。"""
    # 実装

# 悪い例: パラメータが多すぎる
def create_task_bad(
    title: str,
    description: str | None,
    priority: str,
    due_date: datetime | None,
    tags: list[str] | None,
    assignee_id: str | None,
) -> Task:
    # パラメータの意味が分かりにくい
    ...
```

### 関数の長さガイドライン

| 長さ | 評価 | アクション |
|------|------|-----------|
| ~20行 | 理想的 | そのまま |
| 20-50行 | 許容 | 可能なら分割検討 |
| 50-100行 | 要注意 | 分割を推奨 |
| 100行~ | 問題あり | 必ず分割 |

## エラーハンドリング

### カスタム例外クラス

```python
class ValidationError(Exception):
    """入力検証エラー。"""

    def __init__(
        self,
        message: str,
        field: str,
        value: object,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.value = value


class NotFoundError(Exception):
    """リソースが見つからないエラー。"""

    def __init__(self, resource: str, id: str) -> None:
        super().__init__(f"{resource} not found: {id}")
        self.resource = resource
        self.id = id


class DatabaseError(Exception):
    """データベースエラー。"""

    def __init__(
        self,
        message: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.__cause__ = cause
```

### エラーハンドリングパターン

```python
async def get_task(id: str) -> Task:
    """タスクを取得する。

    Raises
    ------
    NotFoundError
        タスクが見つからない場合
    DatabaseError
        データベースエラーの場合
    """
    try:
        task = await repository.find_by_id(id)

        if task is None:
            raise NotFoundError("Task", id)

        return task
    except NotFoundError:
        # 予期されるエラー: そのまま再送出
        logger.warning("Task not found", task_id=id)
        raise
    except Exception as e:
        # 予期しないエラー: ラップして送出
        logger.error("Failed to get task", task_id=id, error=str(e))
        raise DatabaseError(f"Failed to get task {id}") from e
```

### エラーメッセージのベストプラクティス

```python
# 1. 具体的な値を含める
raise ValueError(f"Expected positive integer, got {count}")
raise ValueError(f"Email must be valid, got: {email!r}")

# 2. 解決策を示す
raise FileNotFoundError(
    f"Config file not found at {path}. "
    f"Create it by running: python -m {__package__}.init"
)

# 3. 期待値と実際の値を示す
raise TypeError(
    f"Expected str or bytes, got {type(value).__name__}"
)

# 4. 範囲を示す
raise ValueError(
    f"retry_count must be between 1 and 10, got {retry_count}"
)
```

## 非同期処理

### async/await の基本

```python
import asyncio

async def fetch_user_tasks(user_id: str) -> list[Task]:
    """ユーザーのタスク一覧を取得する。"""
    logger.debug("Fetching tasks", user_id=user_id)

    user = await user_repository.find_by_id(user_id)
    if user is None:
        raise NotFoundError("User", user_id)

    tasks = await task_repository.find_by_user_id(user.id)
    logger.info("Tasks fetched", user_id=user_id, count=len(tasks))

    return tasks
```

### 並列処理

```python
import asyncio

# 良い例: asyncio.gather で並列実行
async def fetch_multiple_users(ids: list[str]) -> list[User]:
    """複数ユーザーを並列で取得する。"""
    tasks = [user_repository.find_by_id(id) for id in ids]
    return await asyncio.gather(*tasks)

# 悪い例: 逐次実行（遅い）
async def fetch_multiple_users_slow(ids: list[str]) -> list[User]:
    users: list[User] = []
    for id in ids:
        user = await user_repository.find_by_id(id)  # 一つずつ待機
        users.append(user)
    return users
```

### セマフォによる並列数制限

```python
import asyncio

async def fetch_with_limit(
    ids: list[str],
    max_concurrent: int = 10,
) -> list[Data]:
    """並列数を制限してデータを取得する。"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(id: str) -> Data:
        async with semaphore:
            return await fetch_data(id)

    return await asyncio.gather(*[fetch_one(id) for id in ids])
```

## セキュリティ

### 入力検証

```python
import re

def validate_email(email: str) -> None:
    """メールアドレスを検証する。

    Raises
    ------
    ValidationError
        検証に失敗した場合
    """
    if not email or not isinstance(email, str):
        raise ValidationError(
            "Email is required",
            field="email",
            value=email,
        )

    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    if not re.match(email_regex, email):
        raise ValidationError(
            f"Invalid email format: {email}",
            field="email",
            value=email,
        )

    if len(email) > 254:
        raise ValidationError(
            f"Email too long: {len(email)} chars (max 254)",
            field="email",
            value=email,
        )
```

### 機密情報の管理

```python
import os

# 良い例: 環境変数から読み込み
def get_api_key() -> str:
    """API キーを取得する。"""
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise RuntimeError(
            "API_KEY environment variable is not set. "
            "Set it by: export API_KEY=your-key"
        )
    return api_key

# 悪い例: ハードコード（絶対禁止）
API_KEY = "sk-1234567890abcdef"  # セキュリティリスク
```

## パフォーマンス

### データ構造の選択

```python
# dict: O(1) アクセス
user_map = {u.id: u for u in users}
user = user_map.get(user_id)  # O(1)

# set: O(1) 存在チェック
valid_ids = {u.id for u in users}
is_valid = user_id in valid_ids  # O(1)

# list: O(n) 検索（避ける）
user = next((u for u in users if u.id == user_id), None)  # O(n)
```

### リスト内包表記とジェネレータ

```python
# リスト内包表記: 結果を全てメモリに保持
results = [process(item) for item in items]

# ジェネレータ: 遅延評価（メモリ効率）
results = (process(item) for item in items)

# 条件付きリスト内包表記
valid_items = [item for item in items if item.is_valid]

# 辞書内包表記
item_map = {item.id: item for item in items}
```

### メモ化

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(input_data: str) -> Result:
    """重い計算をキャッシュする。"""
    # 計算処理
    return result

# 注意: 引数は hashable である必要がある
# リストや辞書は使えない → タプルに変換
```

## テストコードの実装

### Given-When-Then パターン

```python
import pytest

class TestTaskService:
    """TaskService のテストクラス。"""

    class TestCreate:
        """create メソッドのテスト。"""

        def test_正常系_有効なデータでタスクを作成できる(
            self,
            mock_repository: Mock,
        ) -> None:
            # Given: 準備
            service = TaskService(mock_repository)
            data = {"title": "テストタスク", "priority": "high"}

            # When: 実行
            result = service.create(data)

            # Then: 検証
            assert result.id is not None
            assert result.title == "テストタスク"
            assert result.priority == "high"
            mock_repository.save.assert_called_once()

        def test_異常系_タイトルが空の場合ValidationError(
            self,
            mock_repository: Mock,
        ) -> None:
            # Given
            service = TaskService(mock_repository)
            invalid_data = {"title": ""}

            # When/Then
            with pytest.raises(ValidationError, match="title"):
                service.create(invalid_data)
```

### Mock の使用

```python
from unittest.mock import Mock, AsyncMock

# 同期モック
mock_repo = Mock(spec=TaskRepository)
mock_repo.find_by_id.return_value = mock_task

# 非同期モック
mock_async_repo = AsyncMock(spec=TaskRepository)
mock_async_repo.find_by_id.return_value = mock_task

# 条件付き戻り値
def find_by_id_side_effect(id: str) -> Task | None:
    if id == "existing-id":
        return mock_task
    return None

mock_repo.find_by_id.side_effect = find_by_id_side_effect
```

## コードチェックリスト

実装完了前に確認：

### コード品質

- [ ] 命名が明確で一貫している
- [ ] 関数が単一の責務を持っている
- [ ] マジックナンバーがない
- [ ] 型ヒントが適切に記載されている

### セキュリティ

- [ ] 入力検証が実装されている
- [ ] 機密情報がハードコードされていない

### パフォーマンス

- [ ] 適切なデータ構造を使用している
- [ ] 不要な計算を避けている

### テスト

- [ ] ユニットテストが書かれている
- [ ] テストがパスする

### ドキュメント

- [ ] NumPy 形式の Docstring がある
- [ ] 複雑なロジックにコメントがある
