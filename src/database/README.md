# database - 共通インフラパッケージ

プロジェクト全体で使用される共通インフラストラクチャを提供します。

## 概要

database パッケージは以下の機能を提供します:

- **SQLiteClient**: トランザクション処理 (OLTP)
- **DuckDBClient**: 分析クエリ (OLAP)、Parquet 直接読み込み対応
- **構造化ロギング**: structlog ベースの統一ログ出力
- **日付ユーティリティ**: 取引期間計算、日本語/US 形式フォーマット
- **フォーマット変換**: Parquet/JSON 相互変換

## インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

## クイックスタート

### ロギング

```python
from database import get_logger

logger = get_logger(__name__)
logger.info("Processing started", item_count=100, source="yfinance")
logger.error("Fetch failed", symbol="AAPL", error="Connection timeout")
```

### SQLite (OLTP)

```python
from database.db import SQLiteClient, get_db_path

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

### DuckDB (OLAP)

```python
from database.db import DuckDBClient, get_db_path

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

### 日付ユーティリティ

```python
from datetime import date
from database.utils.date_utils import (
    calculate_weekly_comment_period,
    format_date_japanese,
    format_date_us,
    get_trading_days_in_period,
    parse_date,
)

# 週次コメント期間を計算（火曜日〜火曜日）
period = calculate_weekly_comment_period()
print(period["start"], "〜", period["end"])

# 日付フォーマット
d = date(2026, 1, 22)
print(format_date_japanese(d, "full"))   # "2026年1月22日(水)"
print(format_date_japanese(d, "short"))  # "1/22(水)"
print(format_date_us(d, "full"))         # "January 22, 2026"

# 取引日を取得
trading_days = get_trading_days_in_period(date(2026, 1, 19), date(2026, 1, 23))

# 日付文字列のパース
parsed = parse_date("2026-01-22")  # YYYY-MM-DD, YYYYMMDD, MM/DD/YYYY 対応
```

### フォーマット変換

```python
from pathlib import Path
from database.utils.format_converter import parquet_to_json, json_to_parquet

# Parquet → JSON
parquet_to_json(Path("data.parquet"), Path("data.json"))

# JSON → Parquet
json_to_parquet(Path("data.json"), Path("data.parquet"))
```

## 公開 API

### トップレベル (`database`)

```python
from database import get_logger

logger = get_logger(__name__)
```

### データベース (`database.db`)

```python
from database.db import (
    SQLiteClient,      # SQLite クライアント
    DuckDBClient,      # DuckDB クライアント
    get_db_path,       # DB パス取得
    DATA_DIR,          # データディレクトリ
    PROJECT_ROOT,      # プロジェクトルート
)
```

#### SQLiteClient

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `execute(sql, params)` | SQL 実行してデータ取得 | `list[sqlite3.Row]` |
| `execute_many(sql, params_list)` | 一括 INSERT/UPDATE | `int` (影響行数) |
| `execute_script(script)` | SQL スクリプト実行 | `None` |
| `connection()` | コンテキストマネージャー | `sqlite3.Connection` |

#### DuckDBClient

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `query_df(sql)` | SQL クエリ実行して DataFrame 取得 | `pd.DataFrame` |
| `execute(sql)` | SQL を実行（結果なし） | `None` |
| `read_parquet(pattern)` | Parquet ファイル読み込み | `pd.DataFrame` |
| `write_parquet(df, path)` | DataFrame を Parquet に書き込み | `None` |

#### get_db_path

```python
from database.db import get_db_path

# SQLite データベースのパス
sqlite_path = get_db_path("sqlite", "market")  # data/sqlite/market.db

# DuckDB データベースのパス
duckdb_path = get_db_path("duckdb", "analytics")  # data/duckdb/analytics.duckdb
```

### ユーティリティ (`database.utils`)

#### 日付ユーティリティ (`database.utils.date_utils`)

| 関数 | 説明 |
|------|------|
| `calculate_weekly_comment_period(reference_date)` | 火曜日〜火曜日の週次期間を計算 |
| `get_previous_tuesday(date)` | 直近の火曜日を取得 |
| `get_last_tuesday(date)` | 先週の火曜日を取得 |
| `format_date_japanese(date, style)` | 日本語形式でフォーマット |
| `format_date_us(date, style)` | US 形式でフォーマット |
| `get_trading_days_in_period(start, end)` | 期間内の取引日（平日）を取得 |
| `parse_date(date_str)` | 日付文字列をパース |

#### フォーマット変換 (`database.utils.format_converter`)

| 関数 | 説明 |
|------|------|
| `parquet_to_json(input_path, output_path)` | Parquet を JSON に変換 |
| `json_to_parquet(input_path, output_path)` | JSON を Parquet に変換 |

### 型定義 (`database.types`)

```python
from database.types import (
    DatabaseType,      # "sqlite" | "duckdb"
    DataSource,        # "yfinance" | "fred"
    AssetCategory,     # "stocks" | "forex" | "indices" | "indicators"
    FileFormat,        # "parquet" | "csv" | "json"
    LogFormat,         # "json" | "console" | "plain"
    LogLevel,          # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
    DatabaseConfig,    # データベース設定の TypedDict
    FetchResult,       # データ取得結果の TypedDict
    MigrationInfo,     # マイグレーション情報の TypedDict
    JSONPrimitive,     # str | int | float | bool | None
    JSONValue,         # JSONPrimitive | Mapping[str, JSONValue] | list[JSONValue]
    JSONObject,        # Mapping[str, JSONValue]
)
```

## ディレクトリ構成

```
src/database/
├── __init__.py           # get_logger のエクスポート
├── py.typed
├── types.py              # 型定義
├── parquet_schema.py     # Parquet スキーマ定義
├── db/
│   ├── __init__.py       # SQLiteClient, DuckDBClient エクスポート
│   ├── connection.py     # get_db_path, DATA_DIR, PROJECT_ROOT
│   ├── sqlite_client.py  # SQLiteClient
│   ├── duckdb_client.py  # DuckDBClient
│   └── migrations/
│       ├── __init__.py
│       ├── runner.py
│       └── versions/
└── utils/
    ├── __init__.py
    ├── logging_config.py  # get_logger
    ├── date_utils.py      # 日付ユーティリティ
    └── format_converter.py # Parquet/JSON 変換
```

## 依存関係

### 外部パッケージ

| パッケージ | 用途 | 必須/オプション |
|-----------|------|----------------|
| `structlog` | 構造化ロギング | 必須 |
| `duckdb` | DuckDB 分析エンジン | 必須 |
| `pandas` | DataFrame 操作 | 必須 |
| `pyarrow` | Parquet 読み書き | 必須 |
| `sqlite3` | SQLite データベース | 必須（標準ライブラリ） |

### 他パッケージとの関係

`database` パッケージはコアインフラとして、以下のパッケージから利用されます:

- `market`: 市場データの保存
- `analyze`: 分析結果の保存とクエリ
- `rss`: RSS フィードデータの保存
- `factor`: ファクター分析結果の保存
- `strategy`: バックテスト結果の保存

## 開発

### テスト実行

```bash
# 全テスト
uv run pytest tests/database/

# カバレッジ付き
uv run pytest tests/database/ --cov=src/database --cov-report=term-missing
```

### 品質チェック

```bash
# フォーマット
uv run ruff format src/database/ tests/database/

# リント
uv run ruff check src/database/ tests/database/

# 型チェック
uv run pyright src/database/ tests/database/
```

## 関連ドキュメント

- [テンプレート実装](../../template/src/template_package/README.md)
- [開発ガイドライン](../../docs/development-guidelines.md)
- [コーディング規約](../../docs/coding-standards.md)

## ライセンス

MIT License
