# アーキテクチャ設計ガイド

## 基本原則

### 1. 技術選定には理由を明記

**悪い例**:
```
- Node.js
- TypeScript
```

**良い例**:
```
- Python 3.12+
  - 型ヒントの改善（PEP 695）により、可読性と保守性が向上
  - パターンマッチング、改善されたエラーメッセージなど最新機能を活用可能
  - 3.12以上をサポートし、安定した開発環境を維持

- uv
  - Rustベースで高速なパッケージ管理
  - pip/pipx/virtualenv/pyenvの機能を統合
  - pyproject.tomlによる依存関係の厳密な管理が可能

- Ruff
  - Rustベースで高速なリント・フォーマット
  - Flake8、isort、Blackなどの機能を統合
  - 自動修正機能により開発効率が向上
```

### 2. レイヤー分離の原則

各レイヤーの責務を明確にし、依存関係を一方向に保ちます:

```
UI → Service → Data (OK)
UI ← Service (NG)
UI → Data (NG)
```

### 3. 測定可能な要件

すべてのパフォーマンス要件は測定可能な形で記述します。

## レイヤードアーキテクチャの設計

### 各レイヤーの責務

**UIレイヤー**:
```python
# 責務: ユーザー入力の受付とバリデーション
class CLI:
    # OK: サービスレイヤーを呼び出す
    def add_task(self, title: str) -> None:
        task = self.task_service.create(title=title)
        print(f"Created: {task.id}")

    # NG: データレイヤーを直接呼び出す
    def add_task(self, title: str) -> None:
        task = self.repository.save(title=title)  # ❌
```

**サービスレイヤー**:
```python
# 責務: ビジネスロジックの実装
class TaskService:
    # ビジネスロジック: 優先度の自動推定
    def create(self, data: CreateTaskData) -> Task:
        task = Task(
            **data,
            estimated_priority=self.estimate_priority(data),
        )
        return self.repository.save(task)
```

**データレイヤー**:
```python
# 責務: データの永続化
class TaskRepository:
    def save(self, task: Task) -> None:
        self.storage.write(task)
```

## パフォーマンス要件の設定

### 具体的な数値目標

```
コマンド実行時間: 100ms以内(平均的なPC環境で)
└─ 測定方法: console.timeでCLI起動から結果表示まで計測
└─ 測定環境: CPU Core i5相当、メモリ8GB、SSD

タスク一覧表示: 1000件まで1秒以内
└─ 測定方法: 1000件のダミーデータで計測
└─ 許容範囲: 100件で100ms、1000件で1秒、10000件で10秒
```

## セキュリティ設計

### データ保護の3原則

1. **最小権限の原則**
```bash
# ファイルパーミッション
chmod 600 ~/.devtask/tasks.json  # 所有者のみ読み書き
```

2. **入力検証**
```python
def validate_title(title: str) -> None:
    if not title or len(title) == 0:
        raise ValidationError("タイトルは必須です")
    if len(title) > 200:
        raise ValidationError("タイトルは200文字以内です")
```

3. **機密情報の管理**
```bash
# 環境変数で管理
export DEVTASK_API_KEY="xxxxx"  # コード内にハードコードしない
```

## スケーラビリティ設計

### データ増加への対応

**想定データ量**: [例: 10,000件のタスク]

**対策**:
- データのページネーション
- 古いデータのアーカイブ
- インデックスの最適化

```python
# アーカイブ機能の例: 古いタスクを別ファイルに移動
class ArchiveService:
    def archive_completed_tasks(self, older_than: datetime) -> None:
        old_tasks = self.repository.find_completed(older_than)
        self.archive_storage.save(old_tasks)
        self.repository.delete_many([t.id for t in old_tasks])
```

## 依存関係管理

### バージョン管理方針

```toml
# pyproject.toml
[project]
dependencies = [
    "click>=8.0.0",           # マイナーバージョンアップは自動
    "rich==13.7.0",           # 破壊的変更のリスクがある場合は固定
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",            # 開発ツールは柔軟に
    "pyright>=1.1.0",
    "pytest>=8.0.0",
]
```

**方針**:
- 安定版は`>=`でマイナーバージョンまで許可
- 破壊的変更のリスクがある場合は`==`で完全固定
- 開発ツールは`>=`で柔軟に更新

## チェックリスト

- [ ] すべての技術選定に理由が記載されている
- [ ] レイヤードアーキテクチャが明確に定義されている
- [ ] パフォーマンス要件が測定可能である
- [ ] セキュリティ考慮事項が記載されている
- [ ] スケーラビリティが考慮されている
- [ ] バックアップ戦略が定義されている
- [ ] 依存関係管理のポリシーが明確である
- [ ] テスト戦略が定義されている
