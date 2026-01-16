# strategy

投資戦略の構築・バックテスト・評価パッケージ

## 概要

このパッケージは投資戦略の設計、バックテスト、パフォーマンス評価機能を提供します。

**現在のバージョン:** 0.1.0

<!-- AUTO-GENERATED: QUICKSTART -->
## クイックスタート

### インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

### 基本的な使い方

```python
# ログ設定
from strategy.utils.logging_config import get_logger, setup_logging

# ロギングを初期化
setup_logging(level="INFO", format="console")
logger = get_logger(__name__)

# ログを出力
logger.info("投資戦略パッケージを初期化しました")
```

### よくある使い方

#### ロギング設定とコンテキスト管理

```python
from strategy.utils.logging_config import get_logger, log_context, set_log_level
from strategy.types import LogLevel

# ロガーを取得
logger = get_logger(__name__, module="strategy")

# コンテキスト情報を付与してログ
with log_context(user_id=123, request_id="req_001"):
    logger.info("戦略実行を開始", strategy="momentum")

# ログレベルを動的に変更
set_log_level("DEBUG")
logger.debug("詳細なデバッグ情報")
```

#### パフォーマンス計測

```python
from strategy.utils.logging_config import get_logger, log_performance

logger = get_logger(__name__)

@log_performance(logger)
def backtest_strategy(data, parameters):
    """戦略のバックテストを実行"""
    # バックテスト処理
    return results

# 実行時に自動的に処理時間がログされます
results = backtest_strategy(market_data, {"window": 20})
```
<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
strategy/
├── __init__.py
├── py.typed
├── README.md
├── types.py                          # 型定義
├── core/
│   └── __init__.py
├── utils/
│   ├── __init__.py
│   └── logging_config.py            # 構造化ロギング設定
└── docs/
    ├── architecture.md
    ├── development-guidelines.md
    ├── functional-design.md
    ├── glossary.md
    ├── library-requirements.md
    ├── project.md
    ├── repository-structure.md
    └── tasks.md
```
<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->
## 実装状況

| モジュール      | 状態      | ファイル数 | 行数 |
| --------------- | --------- | ---------- | ---- |
| `types.py`      | ✅ 実装済み | 1          | 106  |
| `utils/`        | ✅ 実装済み | 2          | 367  |
| `core/`         | ⏳ 未実装  | 1          | 3    |

**ステータス説明:**

- **✅ 実装済み**: コア機能が実装され、テスト構造が整備されている
- **⏳ 未実装**: 初期化のみで実装が進行していない
<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### ユーティリティ関数

#### `get_logger(name, **context)`

**説明**: 構造化ロギング機能を備えたロガーインスタンスを取得します。

**基本的な使い方**:

```python
from strategy.utils.logging_config import get_logger

logger = get_logger(__name__)
logger.info("処理開始", user_id=123)
logger.error("エラーが発生しました", error_type="ValidationError")
```

**パラメータ**:

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `name` | str | ロガー名（通常は `__name__`） |
| `**context` | Any | ロガーに事前バインドするコンテキスト変数 |

**戻り値**: `BoundLogger` - 構造化ロギング機能を持つロガーインスタンス

---

### 型定義

パッケージが使用する共通の型定義を提供します。

**主要な型**:

```python
from strategy.types import (
    ProcessorStatus,      # "success" | "error" | "pending"
    ValidationStatus,     # "valid" | "invalid" | "skipped"
    ItemDict,            # アイテムデータの型定義
    ConfigDict,          # 設定データの型定義
    ProcessingResult,    # 処理結果の型定義
    ValidationResult,    # バリデーション結果の型定義
    LogLevel,           # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
)
```

#### `setup_logging(*, level, format, log_file, ...)`

**説明**: 構造化ロギングの設定を初期化します。

**使用例**:

```python
from strategy.utils.logging_config import setup_logging

# 開発環境用の設定
setup_logging(level="INFO", format="console")

# 本番環境用の設定
setup_logging(level="WARNING", format="json", log_file="logs/app.log")
```

**パラメータ**:

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `level` | LogLevel | "INFO" | ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `format` | LogFormat | "console" | 出力形式 (json, console, plain) |
| `log_file` | Path \| None | None | ログファイル出力先 |
| `include_timestamp` | bool | True | タイムスタンプの追加 |
| `include_caller_info` | bool | True | 呼び出し元情報の追加 |
| `force` | bool | False | 既存設定を上書き |

---

#### `log_context(**kwargs)` - コンテキストマネージャー

**説明**: ログに一時的にコンテキスト情報を付与します。

**使用例**:

```python
from strategy.utils.logging_config import log_context

with log_context(user_id=123, request_id="req_001"):
    logger.info("リクエスト処理中")  # user_id と request_id が自動付与される
```

---

#### `set_log_level(level, logger_name)`

**説明**: ログレベルを動的に変更します。

**使用例**:

```python
from strategy.utils.logging_config import set_log_level

# ルートロガーのレベルを変更
set_log_level("DEBUG")

# 特定のロガーのレベルを変更
set_log_level("ERROR", logger_name="strategy.core")
```

---

#### `log_performance(logger)` - デコレータ

**説明**: 関数の実行時間とパフォーマンスを自動的にログに記録します。

**使用例**:

```python
from strategy.utils.logging_config import get_logger, log_performance

logger = get_logger(__name__)

@log_performance(logger)
def process_strategy_data(data, config):
    # 処理実行
    return result

# 実行時に自動的に処理時間がログされます
result = process_strategy_data(market_data, {})
```
<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値   |
| -------------------- | ---- |
| Python ファイル数    | 5    |
| 総行数（実装コード） | 485  |
| モジュール数         | 2    |
| テストファイル数     | 4    |
| テストカバレッジ     | N/A  |

**注**: テストカバレッジはまだ構造段階のため、実装完了後に計測予定です。
<!-- END: STATS -->

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
