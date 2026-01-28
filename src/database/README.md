# database - 共通インフラパッケージ

プロジェクト全体で使用される共通インフラストラクチャを提供します。

## 概要

`database` パッケージはすべてのファイナンスパッケージ（`market`、`analyze`、`rss` など）の基盤となるコアインフラストラクチャを提供します。

### 主な機能

- **SQLiteClient**: トランザクション処理 (OLTP) - 株価データの永続化
- **DuckDBClient**: 分析クエリ (OLAP) - Parquet ファイルの高速分析
- **構造化ロギング**: structlog ベースの統一ログ出力 - すべてのパッケージから利用
- **日付ユーティリティ**: 取引期間計算、日本語/US 形式フォーマット
- **フォーマット変換**: Parquet/JSON 相互変換

## インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

<!-- AUTO-GENERATED: QUICKSTART -->

## クイックスタート

初めて `database` パッケージを使う場合は、以下の3つのシナリオから始めてください。

### ロギングの基本

すべてのパッケージから使用する基本的なロギング：

```python
from database import get_logger

logger = get_logger(__name__)

# 構造化ログ出力（JSON形式で自動保存）
logger.info("Processing started", item_count=100, source="yfinance")
logger.error("Fetch failed", symbol="AAPL", error="Connection timeout")
```

### データベースの基本（SQLite）

株価データなどのトランザクションデータを保存：

```python
from database.db import SQLiteClient, get_db_path

# クライアント作成
client = SQLiteClient(get_db_path("sqlite", "market"))

# データ挿入
client.execute(
    "INSERT INTO stocks (symbol, price) VALUES (?, ?)",
    ("AAPL", 150.0)
)

# データ取得
results = client.execute("SELECT * FROM stocks WHERE symbol = ?", ("AAPL",))
for row in results:
    print(row["symbol"], row["price"])
```

### データ分析（DuckDB）

複数の Parquet ファイルを高速に分析：

```python
from database.db import DuckDBClient, get_db_path

# クライアント作成
client = DuckDBClient(get_db_path("duckdb", "analytics"))

# 複数の Parquet ファイルから集計
df = client.query_df("""
    SELECT symbol,
           COUNT(*) as record_count,
           AVG(close) as avg_price
    FROM read_parquet('data/raw/yfinance/stocks/*.parquet')
    GROUP BY symbol
    ORDER BY avg_price DESC
""")

print(df)
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: API -->

## 公開 API

### トップレベル (`database`)

`database` パッケージから直接インポートできる主要なAPI：

```python
from database import get_logger, __version__

# 構造化ロギング（すべてのモジュールで推奨）
logger = get_logger(__name__)

# バージョン確認
print(__version__)  # "0.1.0"
```

---

### クラス: `SQLiteClient`

**説明**: SQLite データベースのクライアント。トランザクション処理（OLTP）向け。

**基本的な使い方**:

```python
from database.db import SQLiteClient, get_db_path

# クライアント作成
client = SQLiteClient(get_db_path("sqlite", "market"))

# クエリ実行
rows = client.execute("SELECT * FROM stocks WHERE symbol = ?", ("AAPL",))

# 複数行の一括挿入
client.execute_many(
    "INSERT INTO stocks (symbol, price) VALUES (?, ?)",
    [("AAPL", 150.0), ("GOOGL", 140.0)]
)
```

**主要メソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `execute(sql, params)` | SQL を実行してデータを取得 | `list[sqlite3.Row]` |
| `execute_many(sql, params_list)` | 複数の INSERT/UPDATE を一括実行 | `int` (影響行数) |
| `execute_script(script)` | SQL スクリプトを実行 | `None` |
| `connection()` | データベース接続をコンテキストマネージャーで取得 | `Iterator[sqlite3.Connection]` |
| `path` | データベースファイルのパスを取得 | `Path` |

---

### クラス: `DuckDBClient`

**説明**: DuckDB データベースのクライアント。分析クエリ（OLAP）向け。Parquet ファイルの高速処理に最適。

**基本的な使い方**:

```python
from database.db import DuckDBClient, get_db_path

# クライアント作成
client = DuckDBClient(get_db_path("duckdb", "analytics"))

# 複数の Parquet ファイルから集計
df = client.query_df("""
    SELECT symbol, COUNT(*) as count, AVG(close) as avg
    FROM read_parquet('data/raw/yfinance/stocks/*.parquet')
    GROUP BY symbol
""")

# Parquet から直接読み込み
df = client.read_parquet("data/raw/yfinance/stocks/*.parquet")

# DataFrame を Parquet に保存
client.write_parquet(df, "data/processed/aggregated.parquet")
```

**主要メソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `query_df(sql)` | SQL を実行して pandas DataFrame で取得 | `pd.DataFrame` |
| `execute(sql)` | SQL を実行（結果は取得しない） | `None` |
| `read_parquet(pattern)` | Parquet ファイルを glob パターンで読み込み | `pd.DataFrame` |
| `write_parquet(df, path)` | DataFrame を Parquet ファイルに保存 | `None` |
| `path` | データベースファイルのパスを取得 | `Path` |

---

### 関数: `get_db_path`

**説明**: データベースファイルのパスを生成します。

**使用例**:

```python
from database.db import get_db_path

# SQLite DB パス: data/sqlite/{name}.db
sqlite_path = get_db_path("sqlite", "market")

# DuckDB パス: data/duckdb/{name}.duckdb
duckdb_path = get_db_path("duckdb", "analytics")
```

---

### ユーティリティ関数

#### ロギング

```python
from utils_core.logging import get_logger, setup_logging, log_context

# ロガー取得
logger = get_logger(__name__)

# 構造化ログ出力
logger.info("Processing", count=100, source="yfinance")

# 詳細なログ設定
setup_logging(level="DEBUG", format="console", include_timestamp=True)

# 一時的にコンテキストを追加
with log_context(user_id=123, request_id="abc123"):
    logger.info("User request started")
```

#### 日付ユーティリティ

```python
from datetime import date
from database.utils.date_utils import (
    calculate_weekly_comment_period,
    get_previous_tuesday,
    format_date_japanese,
    format_date_us,
    get_trading_days_in_period,
    parse_date,
)

# 週次コメント期間（火曜日〜火曜日）
period = calculate_weekly_comment_period()
print(period["start"], "〜", period["end"])

# 直近の火曜日を取得
tuesday = get_previous_tuesday(date.today())

# 日付フォーマット
d = date(2026, 1, 22)
print(format_date_japanese(d, "full"))   # "2026年1月22日(水)"
print(format_date_us(d, "full"))         # "January 22, 2026"

# 取引日を計算
trading_days = get_trading_days_in_period(date(2026, 1, 19), date(2026, 1, 23))

# 日付文字列をパース
d = parse_date("2026-01-22")  # YYYY-MM-DD, YYYYMMDD, MM/DD/YYYY に対応
```

#### フォーマット変換

```python
from pathlib import Path
from database.utils.format_converter import parquet_to_json, json_to_parquet

# Parquet → JSON
parquet_to_json(Path("data.parquet"), Path("data.json"))

# JSON → Parquet
json_to_parquet(Path("data.json"), Path("data.parquet"))
```

---

### 型定義 (`database.types`)

```python
from database.types import (
    # データベース型定義
    DatabaseType,           # Literal["sqlite", "duckdb"]
    DataSource,             # Literal["yfinance", "fred"]
    AssetCategory,          # Literal["stocks", "forex", "indices", "indicators"]

    # ファイル形式
    FileFormat,             # Literal["parquet", "csv", "json"]
    ParquetCompression,     # 圧縮形式

    # ロギング設定
    LogFormat,              # Literal["json", "console", "plain"]
    LogLevel,               # Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    # データ構造（TypedDict）
    DatabaseConfig,         # 接続設定
    FetchResult,            # データ取得結果
    MigrationInfo,          # マイグレーション情報

    # JSON 型
    JSONPrimitive,          # str | int | float | bool | None
    JSONValue,              # JSON 値（ネスト対応）
    JSONObject,             # JSON オブジェクト

    # フォーマット変換（Pydantic）
    ConversionOptions,      # 変換オプション
    ConversionResult,       # 変換結果
    TypeMapping,            # 型マッピング情報
)
```

<!-- END: API -->

<!-- AUTO-GENERATED: STRUCTURE -->

## ディレクトリ構成

```
database/
├── __init__.py              # get_logger をエクスポート
├── py.typed                 # PEP 561 型情報マーカー
├── types.py                 # 型定義（TypedDict、Literal）
├── parquet_schema.py        # Parquet スキーマ定義
│
├── db/                      # データベース接続・クライアント
│   ├── __init__.py          # SQLiteClient, DuckDBClient をエクスポート
│   ├── connection.py        # get_db_path(), DATA_DIR, PROJECT_ROOT
│   ├── sqlite_client.py     # SQLiteClient (OLTP)
│   ├── duckdb_client.py     # DuckDBClient (OLAP)
│   └── migrations/          # スキーママイグレーション
│       ├── __init__.py
│       ├── runner.py
│       └── versions/
│
└── utils/                   # ユーティリティ関数
    ├── __init__.py
    ├── logging_config.py    # get_logger() 他、structlog 設定
    ├── date_utils.py        # 日付計算、フォーマット関数
    └── format_converter.py  # Parquet ⇄ JSON 変換
```

<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->

## 実装状況

各モジュールの実装進捗状況：

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|----------|------|
| `types.py` | ✅ 実装済み | 1 | 326 |
| `db/` | ✅ 実装済み | 4 | 328 |
| `utils/` | ✅ 実装済み | 3 | 885 |
| **合計** | **✅** | **13** | **2,019** |

**テスト**:
- テストファイル数: 7
- テストカバレッジ: 対応

<!-- END: IMPLEMENTATION -->

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

<!-- AUTO-GENERATED: STATS -->

## 統計情報

| 項目 | 値 |
|------|-----|
| Python ファイル数 | 13 |
| 総行数（実装コード） | 2,019 |
| モジュール数 | 3 |
| テストファイル数 | 7 |
| 実装状態 | ✅ 完全実装 |

<!-- END: STATS -->

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
