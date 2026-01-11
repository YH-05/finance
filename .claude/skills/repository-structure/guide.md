# リポジトリ構造定義書作成ガイド

## 基本原則

### 1. 役割の明確化

各ディレクトリは単一の明確な役割を持つべきです。

**悪い例**:
```
src/
├── stuff/           # 曖昧
├── misc/            # 雑多
└── utils/           # 汎用的すぎる
```

**良い例**:
```
src/
├── commands/        # CLIコマンド実装
├── services/        # ビジネスロジック
├── repositories/    # データ永続化
└── validators/      # 入力検証
```

### 2. レイヤー分離の徹底

アーキテクチャのレイヤー構造をディレクトリ構造に反映させます:

```
src/
├── ui/              # UIレイヤー
│   └── cli/         # CLI実装
├── services/        # サービスレイヤー
│   └── task/        # タスク管理サービス
└── repositories/    # データレイヤー
    └── task/        # タスクリポジトリ
```

### 3. 技術要素ベースの分割(基本)

関連する技術要素ごとにディレクトリを分割します:

**基本構造**:
```
src/
├── commands/        # CLIコマンド
├── services/        # ビジネスロジック
├── repositories/    # データ永続化
└── types/           # 型定義
```

**レイヤー構造との対応**:
```
CLI/UIレイヤー      → commands/, cli/
サービスレイヤー    → services/
データレイヤー      → repositories/, storage/
```

## ディレクトリ構造の設計

### レイヤー構造の表現

```python
# 悪い例: 平坦な構造
src/
├── task_cli.py
├── task_service.py
├── task_repository.py
├── user_cli.py
├── user_service.py
└── user_repository.py

# 良い例: レイヤーを明確に
src/
├── cli/
│   ├── task_cli.py
│   └── user_cli.py
├── services/
│   ├── task_service.py
│   └── user_service.py
└── repositories/
    ├── task_repository.py
    └── user_repository.py
```

### テストディレクトリの配置

**推奨構造**:
```
project/
├── src/
│   └── services/
│       └── task_service.py
└── tests/
    ├── unit/
    │   └── services/
    │       └── test_task_service.py
    ├── integration/
    └── e2e/
```

**理由**:
- テストコードが本番コードと分離
- ビルド時にテストを除外しやすい
- テストタイプごとに整理可能

## 命名規則のベストプラクティス

### ディレクトリ名の原則

**1. 複数形を使う (レイヤーディレクトリ)**
```
✅ services/
✅ repositories/
✅ controllers/

❌ service/
❌ repository/
❌ controller/
```

理由: 複数のファイルを格納するため

**2. kebab-caseを使う**
```
✅ task-management/
✅ user-authentication/

❌ TaskManagement/
❌ userAuthentication/
```

理由: URL、ファイルシステムとの互換性

**3. 具体的な名前を使う**
```
✅ validators/       # 入力検証
✅ formatters/       # データ整形
✅ parsers/          # データ解析

❌ utils/            # 汎用的すぎる
❌ helpers/          # 曖昧
❌ common/           # 意味不明
```

### ファイル名の原則

**1. モジュールファイル: snake_case**
```python
# サービスモジュール
task_service.py
user_authentication_service.py

# リポジトリモジュール
task_repository.py
user_repository.py

# コントローラーモジュール
task_controller.py
```

**2. ユーティリティ関数ファイル: snake_case + 動詞で始める**
```python
# ユーティリティ関数
format_date.py
validate_email.py
parse_command_arguments.py
```

**3. 型定義ファイル: snake_case**
```python
# 型定義
types.py           # 共通型定義
task_types.py      # タスク関連型
api_types.py       # API関連型
```

**4. 定数ファイル: snake_case**
```python
# 定数定義
constants.py       # 共通定数
api_endpoints.py   # APIエンドポイント
error_messages.py  # エラーメッセージ
```

## 依存関係の管理

### レイヤー間の依存ルール

```python
# ✅ 良い例: 上位レイヤーから下位レイヤーへの依存
# cli/task_cli.py
from services.task_service import TaskService


class TaskCLI:
    def __init__(self, task_service: TaskService) -> None:
        self.task_service = task_service


# ❌ 悪い例: 下位レイヤーから上位レイヤーへの依存
# services/task_service.py
from cli.task_cli import TaskCLI  # 禁止！
```

### 循環依存の回避

**問題のあるコード**:
```python
# services/task_service.py
from services.user_service import UserService


class TaskService:
    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service


# services/user_service.py
from services.task_service import TaskService  # 循環依存！


class UserService:
    def __init__(self, task_service: TaskService) -> None:
        self.task_service = task_service
```

**解決策1: Protocolで型定義を抽出**
```python
# types/protocols.py
from typing import Protocol


class TaskServiceProtocol(Protocol):
    def create_task(self, title: str) -> None: ...


class UserServiceProtocol(Protocol):
    def get_user(self, user_id: str) -> None: ...


# services/task_service.py
from types.protocols import UserServiceProtocol


class TaskService:
    def __init__(self, user_service: UserServiceProtocol) -> None:
        self.user_service = user_service


# services/user_service.py
from types.protocols import TaskServiceProtocol


class UserService:
    def __init__(self, task_service: TaskServiceProtocol) -> None:
        self.task_service = task_service
```

**解決策2: 依存関係を見直す**
```python
# 共通の機能を別サービスに抽出
# services/notification_service.py
class NotificationService:
    def notify_task_assignment(self, task_id: str, user_id: str) -> None:
        # 通知処理
        ...


# services/task_service.py
from services.notification_service import NotificationService


class TaskService:
    def __init__(self, notification_service: NotificationService) -> None:
        self.notification_service = notification_service


# services/user_service.py
from services.notification_service import NotificationService


class UserService:
    def __init__(self, notification_service: NotificationService) -> None:
        self.notification_service = notification_service
```

## スケーリング戦略

### 推奨構造

**標準パターン**:
```
src/
├── commands/
│   └── task_command.py
├── services/
│   ├── task_service.py
│   └── user_service.py
├── repositories/
│   ├── task_repository.py
│   └── user_repository.py
├── types/
│   ├── task.py
│   └── user.py
├── validators/
│   └── task_validator.py
└── __init__.py
```

**理由**:
- レイヤーごとに責務が明確
- 後からのリファクタリングが不要
- チーム開発で統一しやすい

### モジュール分離のタイミング

**分離を検討する兆候**:
1. ディレクトリ内のファイル数が10個以上
2. 関連する機能がまとまっている
3. 独立してテスト可能
4. 他の機能への依存が少ない

**分離の手順**:
```python
# Before: 全てservices/に配置
services/
├── task_service.py
├── task_validation_service.py
├── task_notification_service.py
├── user_service.py
└── user_auth_service.py

# After: 機能ごとにモジュール化
modules/
├── task/
│   ├── task_service.py
│   ├── task_validation_service.py
│   └── task_notification_service.py
└── user/
    ├── user_service.py
    └── user_auth_service.py
```

## 特殊なケースの対応

### 共有コードの配置

**shared/ または common/ ディレクトリ**
```
src/
├── shared/
│   ├── utils/           # 汎用ユーティリティ
│   ├── types/           # 共通型定義
│   └── constants/       # 共通定数
├── commands/
├── services/
└── repositories/
```

**ルール**:
- 本当に複数のレイヤーで使われるもののみ
- 単一レイヤーでしか使わないものは含めない

### 設定ファイルの管理(該当する場合)

```
config/
├── default.py           # デフォルト設定
└── constants.py         # 定数定義
```

### スクリプトの管理(該当する場合)

```
scripts/
├── build.sh             # ビルドスクリプト
└── dev_tools.py         # 開発補助スクリプト
```

## ドキュメント配置

### ドキュメントの種類と配置先

**プロジェクトルート**:
- `README.md`: プロジェクト概要
- `CONTRIBUTING.md`: 貢献ガイド
- `LICENSE`: ライセンス

**docs/ ディレクトリ**:
- `product-requirements.md`: PRD
- `functional-design.md`: 機能設計書
- `architecture.md`: アーキテクチャ設計書
- `repository-structure.md`: 本ドキュメント
- `development-guidelines.md`: 開発ガイドライン
- `glossary.md`: 用語集

**ソースコード内**:
- NumPy形式docstring: 関数・クラスの説明

## チェックリスト

- [ ] 各ディレクトリの役割が明確に定義されている
- [ ] レイヤー構造がディレクトリに反映されている
- [ ] 命名規則が一貫している
- [ ] テストコードの配置方針が決まっている
- [ ] 依存関係のルールが明確である
- [ ] 循環依存がない
- [ ] スケーリング戦略が考慮されている
- [ ] 共有コードの配置ルールが定義されている
- [ ] 設定ファイルの管理方法が決まっている
- [ ] ドキュメントの配置場所が明確である
