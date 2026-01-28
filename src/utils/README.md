# utils - コアユーティリティパッケージ

プロジェクト全体で使用されるコアユーティリティを提供します。

## 概要

utils パッケージは以下の機能を提供します:

- **構造化ロギング**: structlog ベースの統一ログ出力
- **コンテキスト管理**: リクエスト単位でのコンテキスト変数管理
- **パフォーマンス計測**: 関数実行時間の自動ログ出力

## インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

## クイックスタート

### 基本的なロギング

```python
from utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing started", item_count=100, source="yfinance")
logger.error("Fetch failed", symbol="AAPL", error="Connection timeout")
```

### ロギング設定のカスタマイズ

```python
from utils.logging import setup_logging, get_logger

# 開発環境向け設定（カラー付きコンソール出力）
setup_logging(level="DEBUG", format="console")

# 本番環境向け設定（JSON 出力）
setup_logging(level="INFO", format="json")

# ファイル出力を有効化
setup_logging(level="INFO", log_file="logs/app.log")

logger = get_logger(__name__)
logger.info("Application started")
```

### コンテキスト管理

```python
from utils.logging import get_logger, log_context

logger = get_logger(__name__)

# リクエスト全体でコンテキストを共有
with log_context(user_id=123, request_id="abc-123"):
    logger.info("Processing user request")
    # このブロック内のすべてのログに user_id と request_id が自動追加される
    process_data()
    logger.info("Request completed")
```

### パフォーマンス計測

```python
from utils.logging import get_logger, log_performance

logger = get_logger(__name__)

@log_performance(logger)
def heavy_computation(data: list[int]) -> int:
    """時間のかかる処理"""
    return sum(x ** 2 for x in data)

# 関数の開始・終了・実行時間が自動的にログ出力される
result = heavy_computation([1, 2, 3, 4, 5])
```

### ログレベルの動的変更

```python
from utils.logging import get_logger, set_log_level

logger = get_logger(__name__)

# デバッグ情報を一時的に有効化
set_log_level("DEBUG")
logger.debug("Detailed debug information")

# 元に戻す
set_log_level("INFO")
```

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

## 公開 API

### ロギング (`utils.logging`)

```python
from utils.logging import (
    get_logger,        # ロガーインスタンス取得
    setup_logging,     # ロギング設定
    log_context,       # コンテキスト管理
    log_performance,   # パフォーマンス計測デコレータ
    set_log_level,     # ログレベル動的変更
    LoggerProtocol,    # ロガーの型定義
)
```

#### get_logger

```python
def get_logger(name: str, **context: Any) -> BoundLogger:
    """オプションのコンテキスト付きで構造化ロガーインスタンスを取得する.

    Parameters
    ----------
    name : str
        ロガー名（通常は __name__）
    **context : Any
        ロガーにバインドする初期コンテキスト

    Returns
    -------
    BoundLogger
        設定済みの structlog ロガーインスタンス
    """
```

**使用例:**

```python
# 基本的な使用法
logger = get_logger(__name__)
logger.info("Hello, world!")

# 初期コンテキスト付き
logger = get_logger(__name__, module="data_processor", version="1.0")
logger.info("Processing started")  # module と version が自動追加
```

#### setup_logging

```python
def setup_logging(
    *,
    level: LogLevel | str = "INFO",
    format: LogFormat = "console",
    log_file: str | Path | None = None,
    include_timestamp: bool = True,
    include_caller_info: bool = True,
    force: bool = False,
) -> None:
    """構造化ロギングの設定をセットアップする.

    Parameters
    ----------
    level : LogLevel | str
        ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    format : LogFormat
        出力フォーマット: "json", "console", "plain"
    log_file : str | Path | None
        ログ出力先ファイルパス
    include_timestamp : bool
        ISO タイムスタンプをログに追加するか
    include_caller_info : bool
        呼び出し元情報（ファイル、関数、行番号）を追加するか
    force : bool
        既存の設定があっても強制的に再設定するか
    """
```

**出力フォーマット:**

| フォーマット | 説明 | 用途 |
|-------------|------|------|
| `console` | カラー付き人間可読出力 | 開発環境 |
| `json` | 構造化 JSON 出力 | 本番環境、ログ集約 |
| `plain` | シンプルな key=value 出力 | CI/CD、シンプルな環境 |

#### log_context

```python
@contextmanager
def log_context(**kwargs: Any) -> Iterator[None]:
    """コンテキスト変数を一時的にバインドするコンテキストマネージャ.

    Parameters
    ----------
    **kwargs : Any
        バインドするコンテキスト変数
    """
```

**使用例:**

```python
with log_context(user_id=123, request_id="abc"):
    logger.info("Processing user request")
    # user_id=123, request_id="abc" が自動追加
```

#### log_performance

```python
def log_performance(logger: BoundLogger) -> Callable:
    """関数のパフォーマンスメトリクスをログ出力するデコレータ.

    Parameters
    ----------
    logger : BoundLogger
        使用するロガーインスタンス
    """
```

**使用例:**

```python
@log_performance(logger)
def process_data(items: list) -> list:
    return [item * 2 for item in items]

# 出力例:
# Function process_data started  function=process_data args_count=1
# Function process_data completed  function=process_data duration_ms=1.23 success=True
```

#### set_log_level

```python
def set_log_level(level: LogLevel | str, logger_name: str | None = None) -> None:
    """ログレベルを動的に変更する.

    Parameters
    ----------
    level : LogLevel | str
        新しいログレベル
    logger_name : str | None
        更新対象のロガー名。None の場合はルートロガーを更新
    """
```

### 型定義 (`utils.types`)

```python
from utils.types import (
    LogFormat,   # "json" | "console" | "plain"
    LogLevel,    # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
)
```

## ディレクトリ構成

```
src/utils/
├── __init__.py           # パッケージエクスポート
├── py.typed              # PEP 561 型サポート
├── pyproject.toml        # パッケージ設定
├── types.py              # 型定義
└── logging/
    ├── __init__.py       # 公開 API エクスポート
    └── config.py         # ロギング設定実装
```

## 依存関係

### 外部パッケージ

| パッケージ | 用途 | 必須/オプション |
|-----------|------|----------------|
| `structlog` | 構造化ロギング | 必須 |
| `python-dotenv` | 環境変数読み込み | 必須 |

### 他パッケージとの関係

`utils` パッケージはコアユーティリティとして、以下のパッケージから利用されます:

- `database`: データベース操作のロギング
- `market`: 市場データ取得のロギング
- `analyze`: 分析処理のロギング
- `rss`: RSS フィード監視のロギング
- `factor`: ファクター分析のロギング
- `strategy`: バックテストのロギング

## 開発

### テスト実行

```bash
# 全テスト
uv run pytest tests/utils/

# カバレッジ付き
uv run pytest tests/utils/ --cov=src/utils --cov-report=term-missing
```

### 品質チェック

```bash
# フォーマット
uv run ruff format src/utils/ tests/utils/

# リント
uv run ruff check src/utils/ tests/utils/

# 型チェック
uv run pyright src/utils/ tests/utils/
```

## 関連ドキュメント

- [テンプレート実装](../../template/src/template_package/README.md)
- [開発ガイドライン](../../docs/development-guidelines.md)
- [コーディング規約](../../docs/coding-standards.md)

## ライセンス

MIT License
