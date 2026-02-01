# ロギング設定ファイルの機能差分分析

## 概要

このドキュメントは、`news/utils/logging_config.py` と `utils_core/logging/config.py` の機能差分を分析し、統合方針を明確化します。

## ファイル情報

| 項目 | news/utils/logging_config.py | utils_core/logging/config.py |
|------|------------------------------|------------------------------|
| パス | `src/news/utils/logging_config.py` | `src/utils_core/logging/config.py` |
| 行数 | 369行 | 420+行 |
| 依存関係 | `news.types` | `utils_core.types`, `utils_core.settings` |

## 機能差分マトリックス

| 機能 | news版 | utils_core版 | 備考 |
|------|--------|--------------|------|
| **基本関数** ||||
| `get_logger()` | ✅ | ✅ | ほぼ同一 |
| `setup_logging()` | ✅ | ✅ | パラメータに差異あり |
| `log_context()` | ✅ | ✅ | 同一 |
| `set_log_level()` | ✅ | ✅ | 同一 |
| `log_performance()` | ✅ | ✅ | 実装方法が異なる |
| **プロセッサー** ||||
| `add_timestamp()` | ✅ | ✅ | 同一 |
| `add_caller_info()` | ✅ | ✅ | 実装がほぼ同一 |
| `add_log_level_upper()` | ✅ | ✅ | 同一 |
| `_get_shared_processors()` | ❌ | ✅ | utils_core版のみ |
| **環境変数管理** ||||
| 直接 `os.environ.get()` | ✅ | ❌ | news版は直接取得 |
| `settings.py` 使用 | ❌ | ✅ | utils_core版は設定モジュール使用 |
| **ファイル出力** ||||
| ログファイル出力 | ✅ (simple) | ✅ (advanced) | utils_core版は日付別ファイル対応 |
| `file_level` パラメータ | ✅ | ❌ | news版はコンソールとファイルで異なるレベル設定可能 |
| `LOG_DIR` 環境変数対応 | ❌ | ✅ | utils_core版はディレクトリ指定可能 |
| `LOG_FILE_ENABLED` 対応 | ❌ | ✅ | utils_core版はファイル出力の有効/無効切り替え可能 |
| 日付別ログファイル | ❌ | ✅ | utils_core版は `finance-YYYY-MM-DD.log` 形式 |
| **初期化** ||||
| 遅延初期化 | ❌ | ✅ | utils_core版は `_ensure_basic_config()` |
| 重複ハンドラー防止 | ❌ | ✅ | utils_core版は明示的にクリア |
| **レンダラー** ||||
| JSON | ✅ | ✅ | 同一 |
| Console (colored) | ✅ | ✅ | 同一 |
| Plain (key=value) | ✅ | ✅ | utils_core版は PlainRenderer |
| ProcessorFormatter | ❌ | ✅ | utils_core版は標準ログとの統合 |
| **サードパーティ制御** ||||
| urllib3, asyncio ログレベル調整 | ✅ | ✅ | 両方とも WARNING に設定 |

## 主要な差異

### 1. setup_logging() のパラメータ

#### news版
```python
def setup_logging(
    *,
    level: LogLevel | str = "INFO",
    file_level: LogLevel | str | None = None,  # ← 独自パラメータ
    format: LogFormat = "console",
    log_file: str | Path | None = None,
    include_timestamp: bool = True,
    include_caller_info: bool = True,
    force: bool = False,
) -> None:
```

**特徴**: `file_level` パラメータでコンソールとファイルで異なるログレベルを設定可能。
- 例: `level="INFO"` でコンソールは INFO、`file_level="DEBUG"` でファイルには DEBUG も記録

#### utils_core版
```python
def setup_logging(
    *,
    level: LogLevel | str = "INFO",
    format: LogFormat = "console",
    log_file: str | Path | None = None,  # ← LOG_DIR より優先
    include_timestamp: bool = True,
    include_caller_info: bool = True,
    force: bool = False,
) -> None:
```

**特徴**:
- `file_level` パラメータなし（コンソールとファイルで同一レベル）
- `LOG_DIR` 環境変数で日付別ログファイルを自動作成
- `LOG_FILE_ENABLED` 環境変数でファイル出力の有効/無効を切り替え

### 2. 環境変数管理

#### news版
```python
# 直接 os.environ.get() を使用
env_level = os.environ.get("LOG_LEVEL", "").upper()
env_format = os.environ.get("LOG_FORMAT", "").lower()
```

#### utils_core版
```python
# settings.py の関数を使用（型安全、バリデーション、キャッシュ）
from utils_core.settings import get_log_level, get_log_format, get_log_dir, get_project_env

if os.environ.get("LOG_LEVEL"):
    try:
        level = get_log_level()
    except ValueError:
        pass
```

**利点**:
- 型安全性（LogLevel, LogFormat のバリデーション）
- エラーハンドリング（不正な値の検出）
- 遅延読み込みとキャッシュ（@lru_cache）
- 中央集約（環境変数管理が settings.py に集中）

### 3. ログファイル出力

#### news版
```python
# 単一のログファイル
if log_file:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    effective_file_level = file_level if file_level is not None else level

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(getattr(logging, effective_file_level.upper()))
    logging.root.addHandler(file_handler)
```

**特徴**:
- シンプルなファイル出力
- `file_level` で異なるレベルを設定可能

#### utils_core版
```python
# 日付別ログファイル
def _get_date_based_log_file(log_dir: Path) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"finance-{today}.log"

# LOG_DIR 環境変数対応
env_log_dir = get_log_dir()
log_file_enabled = os.environ.get("LOG_FILE_ENABLED", "true").lower() != "false"

if log_file:
    final_log_file = Path(log_file)
elif log_file_enabled and env_log_dir:
    log_dir = Path(env_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    final_log_file = _get_date_based_log_file(log_dir)
```

**特徴**:
- 日付別ログファイル（ローテーション）
- `LOG_DIR` 環境変数でディレクトリ指定
- `LOG_FILE_ENABLED` で有効/無効切り替え

### 4. 初期化と重複ハンドラー防止

#### news版
- 明示的な初期化制御なし
- 重複ハンドラーの防止なし

#### utils_core版
```python
_initialized = False

def _ensure_basic_config() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True
    # 最小限の設定
```

**特徴**:
- `get_logger()` 呼び出し前に最小限の設定を自動適用
- 重複ハンドラー追加を明示的に防止

### 5. ProcessorFormatter（標準ログ統合）

#### news版
- structlog のみを設定
- 標準ライブラリの logging と分離

#### utils_core版
```python
# structlog と logging の統合
console_formatter = structlog.stdlib.ProcessorFormatter(
    foreign_pre_chain=shared_processors,
    processors=[
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.dev.ConsoleRenderer(colors=True),
    ],
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
logging.root.addHandler(console_handler)
```

**特徴**:
- 標準ライブラリの logging も structlog のフォーマッターを使用
- サードパーティライブラリのログも構造化

## マージ方針

### 推奨: utils_core版をベースに news版の機能を統合

#### 理由

1. **環境変数管理の優位性**
   - `settings.py` による型安全性とバリデーション
   - 中央集約されたコンフィグ管理

2. **日付別ログファイル対応**
   - 本番運用に適したローテーション機能
   - `LOG_DIR` 環境変数対応

3. **標準ログ統合**
   - ProcessorFormatter によるサードパーティライブラリログの構造化
   - より堅牢なロギング基盤

4. **初期化制御**
   - 重複ハンドラー防止
   - 遅延初期化による柔軟性

### 統合時の対応

#### utils_core版に追加すべき機能

1. **file_level パラメータ**（news版の機能）
   ```python
   def setup_logging(
       *,
       level: LogLevel | str = "INFO",
       file_level: LogLevel | str | None = None,  # ← 追加
       format: LogFormat = "console",
       log_file: str | Path | None = None,
       include_timestamp: bool = True,
       include_caller_info: bool = True,
       force: bool = False,
   ) -> None:
   ```

   **実装**:
   ```python
   # ファイルハンドラーに異なるレベルを設定
   effective_file_level = file_level if file_level is not None else level

   if final_log_file:
       file_handler = logging.FileHandler(final_log_file, encoding="utf-8")
       file_handler.setLevel(getattr(logging, effective_file_level.upper()))
       file_handler.setFormatter(file_formatter)
       logging.root.addHandler(file_handler)
   ```

#### news版から削除可能な機能

1. **環境変数の直接取得**
   - `utils_core.settings` に移行

2. **Rich ConsoleRenderer の try-except**
   - utils_core版ですでに対応済み

### マイグレーションパス

#### Phase 1: utils_core版に file_level を追加
- `setup_logging()` に `file_level` パラメータを追加
- ファイルハンドラーでの異なるログレベル設定を実装
- テストを追加

#### Phase 2: news版を utils_core版に置き換え
- `news/utils/logging_config.py` を削除
- news パッケージで `utils_core.logging.config` をインポート
- 既存のテストを更新

#### Phase 3: Deprecation 警告
- news パッケージで `utils_core.logging.config` へのエイリアスを作成
- Deprecation 警告を追加

## 結論

### 統合方針: 完全置換

**utils_core版** を基盤として、**news版の file_level 機能のみを追加**する方針を推奨。

#### 理由
- utils_core版が構造的に優れている（環境変数管理、日付別ログ、標準ログ統合）
- news版の独自機能（file_level）は価値があり、追加実装は容易
- 2つのロギング設定を維持するメンテナンスコストを削減

#### 次のステップ
1. utils_core版に `file_level` パラメータを追加（Phase 1）
2. news版を削除し、utils_core版に置き換え（Phase 2）
3. Deprecation 警告を追加（Phase 3）

## 付録: API 互換性マトリックス

| 関数/パラメータ | news版 | utils_core版 | 互換性 |
|----------------|--------|--------------|--------|
| `get_logger(name, **context)` | ✅ | ✅ | ✅ 完全互換 |
| `setup_logging(level)` | ✅ | ✅ | ✅ 完全互換 |
| `setup_logging(file_level)` | ✅ | ❌ | ⚠️ news版のみ |
| `setup_logging(format)` | ✅ | ✅ | ✅ 完全互換 |
| `setup_logging(log_file)` | ✅ | ✅ | ✅ 完全互換 |
| `log_context(**kwargs)` | ✅ | ✅ | ✅ 完全互換 |
| `set_log_level(level, logger_name)` | ✅ | ✅ | ✅ 完全互換 |
| `log_performance(logger)` | ✅ | ✅ | ✅ 完全互換 |

**互換性リスク**: `file_level` パラメータのみ（news版でのみ使用されている可能性）
