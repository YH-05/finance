# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

```
project-root/
├── src/                   # ソースコード
│   ├── [layer1]/          # [説明]
│   ├── [layer2]/          # [説明]
│   └── [layer3]/          # [説明]
├── tests/                 # テストコード
│   ├── unit/              # ユニットテスト
│   ├── integration/       # 統合テスト
│   └── e2e/               # E2Eテスト
├── docs/                  # プロジェクトドキュメント
├── config/                # 設定ファイル
└── scripts/               # ビルド・デプロイスクリプト
```

## ディレクトリ詳細

### src/ (ソースコードディレクトリ)

#### [ディレクトリ 1]

**役割**: [説明]

**配置ファイル**:

-   [ファイルパターン 1]: [説明]
-   [ファイルパターン 2]: [説明]

**命名規則**:

-   [規則 1]
-   [規則 2]

**依存関係**:

-   依存可能: [ディレクトリ名]
-   依存禁止: [ディレクトリ名]

**例**:

```
[ディレクトリ名]/
├── [example_file1].py
└── [example_file2].py
```

#### [ディレクトリ 2]

**役割**: [説明]

**配置ファイル**:

-   [ファイルパターン 1]: [説明]

**命名規則**:

-   [規則 1]

**依存関係**:

-   依存可能: [ディレクトリ名]
-   依存禁止: [ディレクトリ名]

### tests/ (テストディレクトリ)

#### unit/

**役割**: ユニットテストの配置

**構造**:

```
tests/unit/
└── [layer]/                # srcディレクトリと同じ構造
    └── test_[filename].py
```

**命名規則**:

-   パターン: `test_[テスト対象ファイル名].py`
-   例: `task_service.py` → `test_task_service.py`

#### integration/

**役割**: 統合テストの配置

**構造**:

```
tests/integration/
└── [feature]/              # 機能単位でディレクトリ分割
    └── test_[scenario].py
```

#### e2e/

**役割**: E2E テストの配置

**構造**:

```
tests/e2e/
└── [user_scenario]/        # ユーザーシナリオ単位
    └── test_[flow].py
```

### docs/ (ドキュメントディレクトリ)

**配置ドキュメント**:

-   `product-requirements.md`: プロダクト要求定義書
-   `functional-design.md`: 機能設計書
-   `architecture.md`: アーキテクチャ設計書
-   `repository-structure.md`: リポジトリ構造定義書(本ドキュメント)
-   `development-guidelines.md`: 開発ガイドライン
-   `glossary.md`: 用語集

### config/ (設定ファイルディレクトリ - 該当する場合)

**配置ファイル**:

-   設定ファイル
-   定数定義ファイル

**例**:

```
config/
├── default.py
└── constants.py
```

### scripts/ (スクリプトディレクトリ - 該当する場合)

**配置ファイル**:

-   ビルドスクリプト
-   開発補助スクリプト

## ファイル配置規則

### ソースファイル

| ファイル種別 | 配置先         | 命名規則 | 例   |
| ------------ | -------------- | -------- | ---- |
| [種別 1]     | [ディレクトリ] | [規則]   | [例] |
| [種別 2]     | [ディレクトリ] | [規則]   | [例] |

### テストファイル

| テスト種別     | 配置先             | 命名規則            | 例                    |
| -------------- | ------------------ | ------------------- | --------------------- |
| ユニットテスト | tests/unit/        | test\_[対象].py     | test_task_service.py  |
| 統合テスト     | tests/integration/ | test\_[機能].py     | test_task_crud.py     |
| E2E テスト     | tests/e2e/         | test\_[シナリオ].py | test_user_workflow.py |

### 設定ファイル

| ファイル種別 | 配置先               | 命名規則       |
| ------------ | -------------------- | -------------- |
| 環境設定     | config/environments/ | [環境名].py    |
| ツール設定   | プロジェクトルート   | pyproject.toml |
| 型定義       | src/types/           | [対象].py      |

## 命名規則

### ディレクトリ名

-   **レイヤーディレクトリ**: 複数形、kebab-case
    -   例: `services/`, `repositories/`, `controllers/`
-   **機能ディレクトリ**: 単数形、kebab-case
    -   例: `task-management/`, `user-authentication/`

### ファイル名

-   **モジュールファイル**: snake_case
    -   例: `task_service.py`, `user_repository.py`
-   **ユーティリティファイル**: snake_case
    -   例: `format_date.py`, `validate_email.py`
-   **定数ファイル**: snake_case
    -   例: `constants.py`, `error_messages.py`

### テストファイル名

-   パターン: `test_[テスト対象].py`
-   例: `test_task_service.py`, `test_format_date.py`

## 依存関係のルール

### レイヤー間の依存

```
UIレイヤー
    ↓ (OK)
サービスレイヤー
    ↓ (OK)
データレイヤー
```

**禁止される依存**:

-   データレイヤー → サービスレイヤー (❌)
-   データレイヤー → UI レイヤー (❌)
-   サービスレイヤー → UI レイヤー (❌)

### モジュール間の依存

**循環依存の禁止**:

```python
# ❌ 悪い例: 循環依存
# file_a.py
from file_b import func_b

# file_b.py
from file_a import func_a  # 循環依存
```

**解決策**:

```python
# ✅ 良い例: 共通モジュールの抽出
# shared.py
from typing import Protocol


class SharedProtocol(Protocol):
    ...


# file_a.py
from shared import SharedProtocol

# file_b.py
from shared import SharedProtocol
```

## スケーリング戦略

### 機能の追加

新しい機能を追加する際の配置方針:

1. **小規模機能**: 既存ディレクトリに配置
2. **中規模機能**: レイヤー内にサブディレクトリを作成
3. **大規模機能**: 独立したモジュールとして分離

**例**:

```
src/
├── services/
│   ├── task_service.py           # 既存機能
│   └── task_management/          # 中規模機能の分離
│       ├── task_service.py
│       ├── subtask_service.py
│       └── task_category_service.py
```

### ファイルサイズの管理

**ファイル分割の目安**:

-   1 ファイル: 300 行以下を推奨
-   300-500 行: リファクタリングを検討
-   500 行以上: 分割を強く推奨

**分割方法**:

```python
# 悪い例: 1ファイルに全機能
# task_service.py (800行)

# 良い例: 責務ごとに分割
# task_service.py (200行) - CRUD操作
# task_validation_service.py (150行) - バリデーション
# task_notification_service.py (100行) - 通知処理
```

## 特殊ディレクトリ

### .claude/ (Claude Code 設定)

**役割**: Claude Code 設定とカスタマイズ

**構造**:

```
.claude/
├── commands/                # スラッシュコマンド
├── skills/                  # タスクモード別スキル
└── agents/                  # サブエージェント定義
```

## 除外設定

### .gitignore

プロジェクトで除外すべきファイル:

-   `.venv/`
-   `__pycache__/`
-   `*.pyc`
-   `dist/`
-   `.env`
-   `*.log`
-   `.DS_Store`

### Ruff 除外設定 (pyproject.toml)

ツールで除外すべきファイル:

```toml
[tool.ruff]
exclude = [
    ".venv",
    "__pycache__",
    "dist",
]
```
