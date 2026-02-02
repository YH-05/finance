# utils_core - コアユーティリティパッケージ

プロジェクト全体で使用されるコアユーティリティを提供します。

## 概要

utils_core パッケージは以下の機能を提供します:

- **構造化ロギング**: structlog ベースの統一ログ出力
- **環境変数管理**: 型安全な環境変数の遅延読み込み
- **コンテキスト管理**: リクエスト単位でのコンテキスト変数管理
- **パフォーマンス計測**: 関数実行時間の自動ログ出力

<!-- AUTO-GENERATED: STRUCTURE -->

## ディレクトリ構成

```
utils_core/
├── __init__.py           # パッケージエクスポート
├── py.typed              # PEP 561 型サポート
├── types.py              # 型定義
├── settings.py           # 環境変数管理
├── logging/
│   ├── __init__.py       # 公開 API エクスポート
│   └── config.py         # ロギング設定実装
└── docs/
    ├── project.md        # プロジェクト管理ドキュメント
    └── logging_config_comparison.md  # ロギング設定比較
```

<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->

## 実装状況

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|-----------|------|
| `types.py` | ✅ 実装済み | 1 | 6 |
| `settings.py` | ✅ 実装済み | 1 | 155 |
| `logging/` | ✅ 実装済み | 2 | 585 |

<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: STATS -->

## モジュール統計

| 項目 | 値 |
|------|-----|
| Python ファイル数 | 5 |
| 総行数（実装コード） | 594 |
| モジュール数 | 2 |
| テストファイル数 | 3 |
| テストカバレッジ | N/A |

<!-- END: STATS -->

## インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

<!-- AUTO-GENERATED: QUICKSTART -->

## クイックスタート

### インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

### 基本的な使い方

```python
from utils_core.logging import get_logger

# 1. ロガーインスタンスを取得
logger = get_logger(__name__)

# 2. 構造化ログを出力
logger.info("Processing started", item_count=100, source="yfinance")
logger.error("Fetch failed", symbol="AAPL", error="Connection timeout")
```

### よくある使い方

#### ユースケース1: ロギング設定のカスタマイズ

```python
from utils_core.logging import setup_logging, get_logger

# 開発環境向け設定（カラー付きコンソール出力）
setup_logging(level="DEBUG", format="console")

# 本番環境向け設定（JSON 出力）
setup_logging(level="INFO", format="json")

# ファイル出力を有効化
setup_logging(level="INFO", log_file="logs/app.log")

logger = get_logger(__name__)
logger.info("Application started")
```

#### ユースケース2: コンテキスト管理

```python
from utils_core.logging import get_logger, log_context

logger = get_logger(__name__)

# リクエスト全体でコンテキストを共有
with log_context(user_id=123, request_id="abc-123"):
    logger.info("Processing user request")
    # このブロック内のすべてのログに user_id と request_id が自動追加される
    process_data()
    logger.info("Request completed")
```

#### ユースケース3: パフォーマンス計測

```python
from utils_core.logging import get_logger, log_performance

logger = get_logger(__name__)

@log_performance(logger)
def heavy_computation(data: list[int]) -> int:
    """時間のかかる処理"""
    return sum(x ** 2 for x in data)

# 関数の開始・終了・実行時間が自動的にログ出力される
result = heavy_computation([1, 2, 3, 4, 5])
```

#### ユースケース4: 環境変数管理

```python
from utils_core.settings import get_log_level, get_fred_api_key

# 環境変数から型安全に取得
log_level = get_log_level()  # デフォルト: INFO
fred_key = get_fred_api_key()  # 必須、未設定時はValueError
```

<!-- END: QUICKSTART -->

## 環境変数

| 変数名 | 説明 | デフォルト | 有効な値 |
|--------|------|-----------|---------|
| `LOG_LEVEL` | ログレベル | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT` | 出力フォーマット | `console` | `json`, `console`, `plain` |
| `LOG_DIR` | ログ出力ディレクトリ | なし | ディレクトリパス |
| `LOG_FILE_ENABLED` | ファイル出力の有効化 | `true` | `true`, `false` |
| `PROJECT_ENV` | 実行環境 | `development` | `development`, `production` |

### .env ファイルの例

```env
# 開発環境
LOG_LEVEL=DEBUG
LOG_FORMAT=console
PROJECT_ENV=development

# 本番環境
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_DIR=/var/log/finance
LOG_FILE_ENABLED=true
PROJECT_ENV=production
```

<!-- AUTO-GENERATED: API -->

## 公開 API

### ロギング (`utils_core.logging`)

プロジェクト全体で使用される構造化ロギング機能を提供します。

```python
from utils_core.logging import (
    get_logger,        # ロガーインスタンス取得
    setup_logging,     # ロギング設定
    log_context,       # コンテキスト管理
    log_performance,   # パフォーマンス計測デコレータ
    set_log_level,     # ログレベル動的変更
    LoggerProtocol,    # ロガーの型定義
)
```

#### `get_logger(name, **context)`

**説明**: オプションのコンテキスト付きで構造化ロガーインスタンスを取得します。

**基本的な使い方**:

```python
from utils_core.logging import get_logger

# ロガーインスタンスを取得
logger = get_logger(__name__)
logger.info("Processing started", items_count=100)
```

**主なパラメータ**:

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `name` | `str` | ロガー名（通常は `__name__`） |
| `**context` | `Any` | ロガーにバインドする初期コンテキスト（オプション） |

**戻り値**: `BoundLogger` - 設定済みの structlog ロガーインスタンス

**使用例（初期コンテキスト付き）**:

```python
# モジュール情報を自動追加
logger = get_logger(__name__, module="data_processor", version="1.0")
logger.info("Processing started")
# 出力: Processing started  module=data_processor version=1.0
```

---

#### `setup_logging(*, level, format, log_file, ...)`

**説明**: 構造化ロギングの設定をセットアップします。開発環境・本番環境で異なるフォーマットを使い分けできます。

**基本的な使い方**:

```python
from utils_core.logging import setup_logging, get_logger

# 開発環境向け設定
setup_logging(level="DEBUG", format="console")

logger = get_logger(__name__)
logger.info("Application started")
```

**主なパラメータ**:

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `level` | `LogLevel \| str` | `"INFO"` | コンソール出力のログレベル |
| `file_level` | `LogLevel \| str \| None` | `None` | ファイル出力のログレベル（デフォルトはlevelと同じ） |
| `format` | `LogFormat` | `"console"` | 出力フォーマット（json/console/plain） |
| `log_file` | `str \| Path \| None` | `None` | ログ出力先ファイルパス |
| `include_timestamp` | `bool` | `True` | ISO タイムスタンプを追加 |
| `include_caller_info` | `bool` | `True` | 呼び出し元情報を追加 |
| `force` | `bool` | `False` | 強制的に再設定 |

**出力フォーマット**:

| フォーマット | 説明 | 用途 |
|-------------|------|------|
| `console` | カラー付き人間可読出力 | 開発環境 |
| `json` | 構造化 JSON 出力 | 本番環境、ログ集約 |
| `plain` | シンプルな key=value 出力 | CI/CD、シンプルな環境 |

**使用例（本番環境）**:

```python
# 本番環境: コンソールはINFO、ファイルはDEBUG
setup_logging(
    level="INFO",
    file_level="DEBUG",
    format="json",
    log_file="logs/app.log"
)
```

---

#### `log_context(**kwargs)`

**説明**: コンテキスト変数を一時的にバインドするコンテキストマネージャ。ブロック内の全ログに自動追加されます。

**基本的な使い方**:

```python
from utils_core.logging import get_logger, log_context

logger = get_logger(__name__)

with log_context(user_id=123, request_id="abc-123"):
    logger.info("Processing user request")
    # 出力: Processing user request  user_id=123 request_id=abc-123
```

**主なパラメータ**:

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `**kwargs` | `Any` | バインドするコンテキスト変数 |

**使用例（ネスト）**:

```python
with log_context(user_id=123):
    logger.info("User session started")

    with log_context(action="purchase"):
        logger.info("Processing payment")
        # 出力: user_id=123 action=purchase
```

---

#### `log_performance(logger)`

**説明**: 関数のパフォーマンスメトリクス（実行時間、成功/失敗）を自動ログ出力するデコレータ。

**基本的な使い方**:

```python
from utils_core.logging import get_logger, log_performance

logger = get_logger(__name__)

@log_performance(logger)
def process_data(items: list) -> list:
    return [item * 2 for item in items]

# 自動ログ出力:
# Function process_data started  function=process_data args_count=1
# Function process_data completed  function=process_data duration_ms=1.23 success=True
```

**主なパラメータ**:

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `logger` | `BoundLogger` | 使用するロガーインスタンス（必須） |

**戻り値**: デコレータ関数

**使用例（エラー時）**:

```python
@log_performance(logger)
def risky_operation():
    raise ValueError("Something went wrong")

# エラー時のログ出力:
# Function risky_operation failed  function=risky_operation duration_ms=0.15 success=False error_type=ValueError
```

---

#### `set_log_level(level, logger_name=None)`

**説明**: ログレベルを実行時に動的に変更します。デバッグ時に一時的に詳細ログを有効化する際に便利です。

**基本的な使い方**:

```python
from utils_core.logging import get_logger, set_log_level

logger = get_logger(__name__)

# デバッグ情報を一時的に有効化
set_log_level("DEBUG")
logger.debug("Detailed debug information")

# 元に戻す
set_log_level("INFO")
```

**主なパラメータ**:

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `level` | `LogLevel \| str` | - | 新しいログレベル（必須） |
| `logger_name` | `str \| None` | `None` | 更新対象のロガー名（Noneならルートロガー） |

---

### 環境変数管理 (`utils_core.settings`)

型安全な環境変数の遅延読み込みを提供します。

```python
from utils_core.settings import (
    get_fred_api_key,  # FRED API Key取得（必須）
    get_log_level,     # ログレベル取得
    get_log_format,    # ログフォーマット取得
    get_log_dir,       # ログディレクトリ取得
    get_project_env,   # プロジェクト環境取得
)
```

#### `get_fred_api_key()`

**説明**: FRED API Key を環境変数 `FRED_API_KEY` から取得します。未設定時はエラー。

**基本的な使い方**:

```python
from utils_core.settings import get_fred_api_key

api_key = get_fred_api_key()  # 必須、未設定時はValueError
```

#### その他の環境変数取得関数

| 関数 | 環境変数 | デフォルト | 説明 |
|------|---------|-----------|------|
| `get_log_level()` | `LOG_LEVEL` | `"INFO"` | ログレベル取得 |
| `get_log_format()` | `LOG_FORMAT` | `"console"` | ログフォーマット取得 |
| `get_log_dir()` | `LOG_DIR` | `"logs/"` | ログディレクトリ取得 |
| `get_project_env()` | `PROJECT_ENV` | `"development"` | プロジェクト環境取得 |

---

### 型定義 (`utils_core.types`)

ロギング関連の型定義を提供します。

```python
from utils_core.types import (
    LogFormat,   # "json" | "console" | "plain"
    LogLevel,    # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
)
```

<!-- END: API -->


## 依存関係

### 外部パッケージ

| パッケージ | 用途 | 必須/オプション |
|-----------|------|----------------|
| `structlog` | 構造化ロギング | 必須 |
| `python-dotenv` | 環境変数読み込み | 必須 |

### 他パッケージとの関係

`utils_core` パッケージはコアユーティリティとして、以下のパッケージから利用されます:

- `database`: データベース操作のロギング
- `market`: 市場データ取得のロギング
- `analyze`: 分析処理のロギング
- `rss`: RSS フィード監視のロギング
- `factor`: ファクター分析のロギング
- `strategy`: バックテストのロギング
- `news`: ニュース処理のロギング

## 開発

### テスト実行

```bash
# 全テスト
uv run pytest tests/utils_core/

# カバレッジ付き
uv run pytest tests/utils_core/ --cov=src/utils_core --cov-report=term-missing

# 特定のテストのみ
uv run pytest tests/utils_core/unit/logging/test_config.py -v
```

### 品質チェック

```bash
# フォーマット
uv run ruff format src/utils_core/ tests/utils_core/

# リント
uv run ruff check src/utils_core/ tests/utils_core/

# 型チェック
uv run pyright src/utils_core/ tests/utils_core/

# 全チェック
make check-all
```

## 関連ドキュメント

- [テンプレート実装](../../template/src/template_package/README.md)
- [開発ガイドライン](../../docs/development-guidelines.md)
- [コーディング規約](../../docs/coding-standards.md)

## ライセンス

MIT License
