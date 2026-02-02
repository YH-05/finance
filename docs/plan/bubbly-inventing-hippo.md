# 環境変数読み込み問題の修正計画

> **詳細計画**: [docs/project/project-31/project.md](../project/project-31/project.md)

## 問題概要

`utils_core/settings.py`で`__file__`ベースのパス解決を使用しているため、パッケージをsite-packagesにインストールすると`.env`ファイルが見つからない。

## 影響範囲

| ファイル | 問題 |
|----------|------|
| `src/utils_core/settings.py` | PROJECT_ROOT、ENV_FILE_PATHが誤ったパスになる |
| `src/market/fred/historical_cache.py` | `_DEFAULT_CACHE_PATH`が誤ったパスになる |
| `src/market/fred/fetcher.py` | `DEFAULT_PRESETS_PATH`が誤ったパスになる |
| `src/database/db/connection.py` | PROJECT_ROOT、DATA_DIRが誤ったパスになる |

## 修正方針

### 方針1: カレントディレクトリ優先の`.env`探索

`.env`ファイルの探索順序を変更し、site-packages環境でも動作するようにする。

### 方針2: デフォルトパスの環境変数化

データディレクトリのパスを環境変数で設定可能にし、`__file__`ベースのパスはフォールバックとして残す。

---

## 修正内容

### Phase 1: settings.pyの修正

**ファイル**: `src/utils_core/settings.py`

```python
# 変更前
PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
ENV_FILE_PATH: Path = PROJECT_ROOT / ".env"

def load_project_env(*, override: bool = False) -> bool:
    return load_dotenv(dotenv_path=ENV_FILE_PATH, override=override)
```

```python
# 変更後
def _find_env_file() -> Path | None:
    """Find .env file in order of priority.

    Search order:
    1. DOTENV_PATH environment variable
    2. Current working directory
    3. Parent directories (up to 5 levels)
    """
    # 1. 環境変数で明示的に指定されたパス
    env_path = os.environ.get("DOTENV_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    # 2. カレントディレクトリ
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return cwd_env

    # 3. 親ディレクトリを遡って探索（最大5レベル）
    current = Path.cwd()
    for _ in range(5):
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None

def load_project_env(*, override: bool = False) -> bool:
    """Load environment variables from .env file.

    Parameters
    ----------
    override : bool
        If True, override existing environment variables.

    Returns
    -------
    bool
        True if .env file was found and loaded.
    """
    env_file = _find_env_file()
    if env_file:
        logger.debug("Loading .env file", path=str(env_file))
        return load_dotenv(dotenv_path=env_file, override=override)

    logger.debug("No .env file found")
    return False

# PROJECT_ROOT は非推奨化（後方互換性のため残す）
# WARNING: site-packages環境では正しく動作しない
PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
ENV_FILE_PATH: Path = PROJECT_ROOT / ".env"  # 非推奨
```

### Phase 2: データパスの環境変数化

#### 2-1. historical_cache.pyの修正

**ファイル**: `src/market/fred/historical_cache.py`

```python
# 変更前
_DEFAULT_CACHE_PATH = Path(__file__).parents[3] / "data" / "raw" / "fred" / "indicators"

def get_default_cache_path() -> Path:
    load_project_env()
    env_path = os.environ.get(FRED_HISTORICAL_CACHE_DIR_ENV)
    if env_path:
        return Path(env_path)
    return _DEFAULT_CACHE_PATH
```

```python
# 変更後
def get_default_cache_path() -> Path:
    """Get the default cache path for FRED historical data.

    Priority:
    1. FRED_HISTORICAL_CACHE_DIR environment variable
    2. ./data/raw/fred/indicators (relative to cwd)
    3. Fallback: __file__ based path (for backward compatibility)
    """
    load_project_env()

    # 1. 環境変数
    env_path = os.environ.get(FRED_HISTORICAL_CACHE_DIR_ENV)
    if env_path:
        return Path(env_path)

    # 2. カレントディレクトリからの相対パス
    cwd_path = Path.cwd() / "data" / "raw" / "fred" / "indicators"
    if cwd_path.exists() or cwd_path.parent.exists():
        return cwd_path

    # 3. フォールバック（後方互換性）
    return Path(__file__).parents[3] / "data" / "raw" / "fred" / "indicators"
```

#### 2-2. fetcher.pyの修正

**ファイル**: `src/market/fred/fetcher.py`

```python
# 変更前
DEFAULT_PRESETS_PATH = (
    Path(__file__).parents[3] / "data" / "config" / "fred_series.json"
)
```

```python
# 変更後
def _get_default_presets_path() -> Path:
    """Get the default presets path for FRED series.

    Priority:
    1. FRED_SERIES_ID_JSON environment variable
    2. ./data/config/fred_series.json (relative to cwd)
    3. Fallback: __file__ based path (for backward compatibility)
    """
    # 環境変数はload_presets内で処理されるため、ここでは参照しない

    # 1. カレントディレクトリからの相対パス
    cwd_path = Path.cwd() / "data" / "config" / "fred_series.json"
    if cwd_path.exists():
        return cwd_path

    # 2. フォールバック（後方互換性）
    return Path(__file__).parents[3] / "data" / "config" / "fred_series.json"

# モジュールレベル定数は廃止し、関数呼び出しに変更
```

#### 2-3. connection.pyの修正

**ファイル**: `src/database/db/connection.py`

```python
# 変更前
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
```

```python
# 変更後
def get_data_dir() -> Path:
    """Get the data directory path.

    Priority:
    1. DATA_DIR environment variable
    2. ./data (relative to cwd)
    3. Fallback: __file__ based path (for backward compatibility)
    """
    # 1. 環境変数
    env_path = os.environ.get("DATA_DIR")
    if env_path:
        return Path(env_path)

    # 2. カレントディレクトリからの相対パス
    cwd_path = Path.cwd() / "data"
    if cwd_path.exists():
        return cwd_path

    # 3. フォールバック（後方互換性）
    return Path(__file__).parent.parent.parent.parent / "data"

# 後方互換性のため定数も残す（非推奨）
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # 非推奨
DATA_DIR = PROJECT_ROOT / "data"  # 非推奨
```

### Phase 3: ドキュメント追加

#### 3-1. .env.exampleの更新

**ファイル**: `.env.example`

```bash
# Finance Library Configuration
# Copy this file to .env and fill in your values

# =============================================================================
# Path Configuration (Optional)
# =============================================================================
# These are optional. If not set, paths are resolved relative to the current
# working directory.

# Custom .env file path (default: ./.env)
# DOTENV_PATH=/path/to/custom/.env

# Data directory (default: ./data)
# DATA_DIR=/path/to/data

# FRED historical cache directory (default: ./data/raw/fred/indicators)
# FRED_HISTORICAL_CACHE_DIR=/path/to/cache

# =============================================================================
# API Keys (Required for full functionality)
# =============================================================================

# FRED API Key (https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY=

# Tavily API Key (for web search)
TAVILY_API_KEY=
```

#### 3-2. README.mdへの追記

**セクション追加**: 環境設定について

```markdown
## 環境設定

### .envファイルの配置

`.env`ファイルは以下の順序で探索されます：

1. `DOTENV_PATH`環境変数で指定されたパス
2. カレントディレクトリ（`./`）
3. 親ディレクトリを遡って探索（最大5レベル）

**推奨**: プロジェクトルートに`.env`ファイルを配置し、そのディレクトリから実行してください。

### パッケージインストール時の注意

`pip install`（非editable）でインストールした場合、`__file__`ベースのパス解決は機能しません。
以下のいずれかの方法で対応してください：

1. **推奨**: プロジェクトディレクトリから実行する
2. 環境変数でパスを明示的に設定する（`DATA_DIR`, `FRED_HISTORICAL_CACHE_DIR`等）
```

---

## 修正ファイル一覧

| ファイル | 修正内容 |
|----------|----------|
| `src/utils_core/settings.py` | `_find_env_file()`追加、`load_project_env()`修正 |
| `src/market/fred/historical_cache.py` | `get_default_cache_path()`修正 |
| `src/market/fred/fetcher.py` | `_get_default_presets_path()`追加 |
| `src/database/db/connection.py` | `get_data_dir()`追加 |
| `.env.example` | パス設定オプション追加 |

---

## 検証方法

### 1. 単体テスト

```bash
# 既存テストが通ることを確認
make test-unit
```

### 2. 統合テスト

```bash
# カレントディレクトリから実行
cd /Users/yukihata/Desktop/finance
python -c "from utils_core.settings import load_project_env; print(load_project_env())"
# 期待結果: True

# 別ディレクトリから実行（.envなし）
cd /tmp
python -c "from utils_core.settings import load_project_env; print(load_project_env())"
# 期待結果: False

# 環境変数でパス指定
DOTENV_PATH=/Users/yukihata/Desktop/finance/.env python -c "from utils_core.settings import load_project_env; print(load_project_env())"
# 期待結果: True
```

### 3. site-packages環境でのテスト

```bash
# 通常インストール
cd /tmp
uv venv test-env
source test-env/bin/activate
uv pip install /Users/yukihata/Desktop/finance

# プロジェクトディレクトリに移動して実行
cd /Users/yukihata/Desktop/finance
python -c "from utils_core.settings import load_project_env; print(load_project_env())"
# 期待結果: True
```

---

## 後方互換性

- `PROJECT_ROOT`、`ENV_FILE_PATH`、`DATA_DIR`は残すが非推奨とする
- 既存のコードはそのまま動作する（editable install環境）
- 新しい環境変数（`DOTENV_PATH`, `DATA_DIR`）は任意設定
