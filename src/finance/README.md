# finance

共通インフラパッケージ（データベース・ユーティリティ）

## 概要

financeパッケージは、プロジェクト全体で使用される共通インフラストラクチャを提供します。

**主な機能:**
- SQLiteクライアント（OLTP: トランザクション処理）
- DuckDBクライアント（OLAP: 分析クエリ）
- 構造化ロギング

**現在のバージョン:** 0.1.0

## クイックスタート

<!-- AUTO-GENERATED: QUICKSTART -->

### インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

### 基本的な使い方

```python
from finance import get_logger

# ロガーの取得と使用
logger = get_logger(__name__)
logger.info("Processing started", item_count=100)
```

### よくある使い方

#### ユースケース1: SQLiteでトランザクション操作

```python
from finance.db import SQLiteClient, get_db_path

# データベースクライアントの作成
client = SQLiteClient(get_db_path("sqlite", "market"))

# データの挿入
client.execute(
    "INSERT INTO stocks (symbol, price) VALUES (?, ?)",
    ("AAPL", 150.0)
)

# データの取得
results = client.execute("SELECT * FROM stocks WHERE symbol = ?", ("AAPL",))
```

#### ユースケース2: DuckDBで分析クエリ

```python
from finance.db import DuckDBClient, get_db_path

# DuckDBクライアントの作成
client = DuckDBClient(get_db_path("duckdb", "analytics"))

# Parquetファイルから直接クエリ
df = client.read_parquet("data/raw/yfinance/stocks/*.parquet")

# 集計クエリの実行
result = client.query_df("""
    SELECT symbol, AVG(close) as avg_price
    FROM df
    GROUP BY symbol
""")
```

#### ユースケース3: 構造化ロギング

```python
from finance import get_logger

logger = get_logger(__name__)

# 構造化データ付きログ出力
logger.info("Processing started", item_count=100, source="yfinance")
logger.error("Fetch failed", symbol="AAPL", error="Connection timeout")
```

<!-- END: QUICKSTART -->

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->
```
finance/
├── __init__.py
├── py.typed
├── types.py
├── db/
│   ├── __init__.py
│   ├── connection.py
│   ├── sqlite_client.py
│   ├── duckdb_client.py
│   └── migrations/
│       ├── __init__.py
│       ├── runner.py
│       └── versions/
└── utils/
    ├── __init__.py
    └── logging_config.py
```
<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|-----------|-----|
| `types.py` | 🚧 開発中 | 1 | 30 |
| `db/` | ✅ 実装済み | 6 | 342 |
| `utils/` | 🚧 開発中 | 2 | 273 |

<!-- END: IMPLEMENTATION -->

## 公開API

<!-- AUTO-GENERATED: API -->

### クイックスタート

financeパッケージは共通インフラ（データベース・ロギング）を提供します。

```python
from finance import get_logger
from finance.db import SQLiteClient, get_db_path

# ロギングの基本
logger = get_logger(__name__)
logger.info("Processing started", item_count=100)

# データベース操作の基本
client = SQLiteClient(get_db_path("sqlite", "market"))
results = client.execute("SELECT * FROM stocks WHERE symbol = ?", ("AAPL",))
```

---

### 主要クラス

#### `SQLiteClient`

**説明**: SQLiteデータベースへのトランザクション処理（OLTP）用クライアント

**基本的な使い方**:

```python
from finance.db import SQLiteClient, get_db_path

# クライアントの初期化
client = SQLiteClient(get_db_path("sqlite", "market"))

# データの挿入
client.execute(
    "INSERT INTO stocks (symbol, price) VALUES (?, ?)",
    ("AAPL", 150.0)
)

# データの取得
results = client.execute("SELECT * FROM stocks WHERE symbol = ?", ("AAPL",))
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `execute(sql, params)` | SQL実行してデータ取得 | `list[sqlite3.Row]` |
| `execute_many(sql, params_list)` | 一括INSERT/UPDATE | `int` (影響行数) |
| `execute_script(script)` | SQLスクリプト実行 | `None` |
| `connection()` | コンテキストマネージャー | `sqlite3.Connection` |

---

#### `DuckDBClient`

**説明**: DuckDBデータベースへの分析クエリ（OLAP）用クライアント。Parquetファイルの直接読み込みに対応。

**基本的な使い方**:

```python
from finance.db import DuckDBClient, get_db_path

# クライアントの初期化
client = DuckDBClient(get_db_path("duckdb", "analytics"))

# Parquetファイルから直接クエリ
df = client.read_parquet("data/raw/yfinance/stocks/*.parquet")

# 集計クエリの実行
result = client.query_df("SELECT symbol, AVG(close) FROM df GROUP BY symbol")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `query_df(sql)` | SQLクエリ実行してDataFrame取得 | `pd.DataFrame` |
| `execute(sql)` | SQLを実行（結果なし） | `None` |
| `read_parquet(pattern)` | Parquetファイル読み込み | `pd.DataFrame` |
| `write_parquet(df, path)` | DataFrameをParquetに書き込み | `None` |

---

### 関数

#### `get_logger(name, **context)`

**説明**: 構造化ログを出力するロガーインスタンスを取得

**使用例**:

```python
from finance import get_logger

# 基本的な使い方
logger = get_logger(__name__)
logger.info("Processing started", item_count=100)
logger.error("Processing failed", error="Invalid input")
```

**パラメータ**:

- `name` (必須): ロガー名（通常は `__name__`）
- `**context`: ロガーに紐付けるコンテキスト情報

---

#### `get_db_path(db_type, name)`

**説明**: データベースファイルのパスを取得

**使用例**:

```python
from finance.db import get_db_path

# SQLiteデータベースのパス
sqlite_path = get_db_path("sqlite", "market")  # data/sqlite/market.db

# DuckDBデータベースのパス
duckdb_path = get_db_path("duckdb", "analytics")  # data/duckdb/analytics.duckdb
```

---

### 型定義

データ構造の定義。型ヒントに使用:

```python
from finance.types import (
    DatabaseType,      # "sqlite" | "duckdb"
    DataSource,        # "yfinance" | "fred"
    AssetCategory,     # "stocks" | "forex" | "indices" | "indicators"
    FileFormat,        # "parquet" | "csv" | "json"
    LogFormat,         # "json" | "console" | "plain"
    LogLevel,          # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
    DatabaseConfig,    # データベース設定のTypeDict
    FetchResult,       # データ取得結果のTypeDict
)
```

<!-- END: API -->

## 統計

<!-- AUTO-GENERATED: STATS -->

| 項目 | 値 |
|-----|---|
| Pythonファイル数 | 10 |
| 総行数（実装コード） | 649 |
| モジュール数 | 2 |
| テストファイル数 | 3 |
| テストカバレッジ | N/A |

<!-- END: STATS -->

## 使用例

```python
from finance import get_logger

logger = get_logger(__name__)
logger.info("Processing started", item_count=100)
```

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
