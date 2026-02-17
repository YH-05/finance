# utils プロジェクト

## 概要

共通ユーティリティパッケージ。ロギング設定を集約し、全パッケージは `utils` からインポートする。

## 主要機能

- [ ] 共通ロギング設定（`logs/finance-YYYY-MM-DD.log` 形式で日付別出力）
- [ ] 開発・本番ともにコンソール + ファイル両方に出力
- [ ] 全パッケージで共通の `get_logger()` を提供
- [ ] 環境変数による設定（LOG_DIR, LOG_FILE_ENABLED, LOG_LEVEL, LOG_FORMAT）

## 技術的考慮事項

- structlog ベースの構造化ロギング
- 既存パッケージ（database, market, rss, factor, strategy）との後方互換性維持
- ローテーション不要（手動管理）

## 成功基準

- 全パッケージが utils.logging からインポート可能
- 既存の import パス（例: `from database.utils.logging_config import get_logger`）が動作継続
- `logs/` ディレクトリにログファイルが自動作成される

## アーキテクチャ

```
src/utils/                    # 新規パッケージ（共通基盤）
├── __init__.py
├── logging/                 # ロギングモジュール
│   ├── __init__.py
│   └── config.py           # ログ設定本体
└── types.py                # 型定義（LogLevel, LogFormat）

依存関係:
  utils (新規) ← database, market, analyze, rss, factor, strategy
```

## 実装計画

### Phase 1: utils パッケージ作成

#### 1.1 パッケージ構造

```
src/utils/
├── __init__.py
├── py.typed
├── logging/
│   ├── __init__.py
│   └── config.py
└── types.py
```

#### 1.2 `src/utils/types.py`

```python
"""Type definitions for the utils package."""

from typing import Literal

type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
```

#### 1.3 `src/utils/logging/config.py`

database の `logging_config.py` をベースに以下を追加:

```python
# 新規追加: 定数
_DEFAULT_LOG_DIR = Path("logs")

def _get_default_log_file() -> Path:
    """日付ベースのログファイルパスを取得"""
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    log_dir = Path(os.environ.get("LOG_DIR", _DEFAULT_LOG_DIR))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"finance-{today}.log"

def _add_file_handler(log_file: Path, level: str) -> None:
    """ファイルハンドラーを追加（重複防止付き）"""
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            if Path(handler.baseFilename).resolve() == log_file.resolve():
                return
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(getattr(logging, level.upper()))
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.root.addHandler(file_handler)

def _ensure_basic_config() -> None:
    # 既存のstructlog設定...

    # 追加: デフォルトファイル出力
    if os.environ.get("LOG_FILE_ENABLED", "true").lower() == "true":
        log_file = _get_default_log_file()
        _add_file_handler(log_file, default_level)
```

#### 1.4 `src/utils/logging/__init__.py`

```python
"""Logging utilities for the finance project."""

from utils.logging.config import (
    LoggerProtocol,
    get_logger,
    log_context,
    log_performance,
    set_log_level,
    setup_logging,
)

__all__ = [
    "LoggerProtocol",
    "get_logger",
    "log_context",
    "log_performance",
    "set_log_level",
    "setup_logging",
]
```

#### 1.5 `src/utils/__init__.py`

```python
"""Core utilities for the finance project."""

from utils.logging import get_logger, setup_logging

__all__ = ["get_logger", "setup_logging"]
```

#### 1.6 環境変数

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `LOG_DIR` | `logs` | ログディレクトリ |
| `LOG_FILE_ENABLED` | `true` | ファイル出力の有効/無効 |
| `LOG_LEVEL` | `INFO` | ログレベル |
| `LOG_FORMAT` | `console` | 出力フォーマット |

### Phase 2: 各パッケージの更新

#### 2.1 database パッケージ

**`src/database/utils/logging_config.py`** → utils からの再エクスポート:

```python
"""Logging configuration (re-exported from utils package)."""

from utils.logging import (
    LoggerProtocol,
    get_logger,
    log_context,
    log_performance,
    set_log_level,
    setup_logging,
)

__all__ = [
    "LoggerProtocol",
    "get_logger",
    "log_context",
    "log_performance",
    "set_log_level",
    "setup_logging",
]
```

**`src/database/types.py`** の `LogFormat`, `LogLevel` → utils から再エクスポート

#### 2.2 他パッケージ（market, rss, factor, strategy）

同様に utils からの再エクスポートに変更。

### Phase 3: pyproject.toml 更新

```toml
[project]
dependencies = [
    "structlog>=24.0.0",
    "python-dotenv>=1.0.0",
]

[tool.uv.sources]
utils = { workspace = true }
```

各パッケージの依存関係に `utils` を追加。

## 変更ファイル一覧

### 新規作成

| ファイル | 説明 |
|----------|------|
| `src/utils/__init__.py` | パッケージ初期化 |
| `src/utils/py.typed` | 型ヒントマーカー |
| `src/utils/types.py` | 型定義 |
| `src/utils/logging/__init__.py` | ロギングモジュール |
| `src/utils/logging/config.py` | ログ設定本体 |
| `src/utils/pyproject.toml` | パッケージ設定 |
| `src/utils/README.md` | ドキュメント |

### 変更

| ファイル | 変更内容 |
|----------|---------|
| `src/database/utils/logging_config.py` | utils から再エクスポート |
| `src/database/types.py` | LogFormat/LogLevel を utils から再エクスポート |
| `src/market/utils/logging_config.py` | utils から再エクスポート |
| `src/rss/utils/logging_config.py` | utils から再エクスポート |
| `src/factor/utils/logging_config.py` | utils から再エクスポート |
| `src/strategy/utils/logging_config.py` | utils から再エクスポート |
| `pyproject.toml` | workspace に utils 追加 |

## 後方互換性

- 既存の `from database.utils.logging_config import get_logger` は動作継続
- 既存の `from market.utils.logging_config import get_logger` も動作継続
- 新規推奨: `from utils.logging import get_logger`

## 検証方法

```bash
# 1. テスト実行
make check-all

# 2. utils パッケージから直接インポート
python -c "from utils.logging import get_logger; get_logger('test').info('test')"
ls -la logs/  # finance-YYYY-MM-DD.log が作成されていることを確認

# 3. 各パッケージからのインポート（後方互換性）
python -c "from database.utils.logging_config import get_logger; get_logger('test').info('db test')"
python -c "from rss.utils.logging_config import get_logger; get_logger('test').info('rss test')"
```
