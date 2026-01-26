# market - 金融データ取得パッケージ

金融市場データを取得するための統合パッケージ。Yahoo Finance、FRED など複数のデータソースに対応。

## インストール

```bash
# uv を使用（このリポジトリ内）
uv sync --all-extras
```

## クイックスタート

```python
from market.yfinance import YFinanceFetcher, FetchOptions

# フェッチャーを初期化
fetcher = YFinanceFetcher()

# オプションを設定
options = FetchOptions(
    symbols=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# データを取得
results = fetcher.fetch(options)

# 結果を処理
for result in results:
    print(f"{result.symbol}: {len(result.data)} rows")
```

## サブモジュール

| モジュール | 説明 | ステータス |
|-----------|------|-----------|
| `market.yfinance` | Yahoo Finance データ取得 | 実装済み |
| `market.fred` | FRED 経済指標データ取得 | 実装済み |
| `market.export` | データエクスポート | 実装済み |
| `market.schema` | JSON スキーマ定義 (Pydantic V2) | 実装済み |
| `market.cache` | キャッシュ機能 | 実装済み |
| `market.factset` | FactSet データ取得 | 計画中 |
| `market.alternative` | オルタナティブデータ | 計画中 |
| `market.bloomberg` | Bloomberg データ取得 | 計画中 |

## 公開 API

### トップレベルインポート

```python
from market import (
    # データ型
    DataSource,           # データソース列挙型
    MarketDataResult,     # データ取得結果
    AnalysisResult,       # 分析結果
    AgentOutput,          # AI エージェント向け出力
    AgentOutputMetadata,  # エージェント出力のメタデータ

    # エクスポート
    DataExporter,         # データエクスポーター

    # 設定 (Pydantic V2 モデル)
    MarketConfig,         # 完全な設定
    CacheConfig,          # キャッシュ設定
    DataSourceConfig,     # データソース設定
    DateRange,            # 日付範囲
    ExportConfig,         # エクスポート設定

    # メタデータ
    StockDataMetadata,    # 株価データのメタデータ
    EconomicDataMetadata, # 経済指標のメタデータ

    # バリデーション
    validate_config,
    validate_stock_metadata,
    validate_economic_metadata,

    # エラー
    MarketError,          # 基底エラー
    ExportError,          # エクスポートエラー
    CacheError,           # キャッシュエラー
    ErrorCode,            # エラーコード列挙型
)
```

### DataSource 列挙型

```python
from market import DataSource

print(DataSource.YFINANCE)   # Yahoo Finance
print(DataSource.FRED)       # Federal Reserve Economic Data
print(DataSource.LOCAL)      # ローカルファイル
print(DataSource.BLOOMBERG)  # Bloomberg (計画中)
print(DataSource.FACTSET)    # FactSet (計画中)
```

## yfinance モジュール

Yahoo Finance から OHLCV データを取得します。

### 基本的な使い方

```python
from market.yfinance import (
    YFinanceFetcher,
    FetchOptions,
    Interval,
    DataSource,
)

fetcher = YFinanceFetcher()

# 日次データを取得
options = FetchOptions(
    symbols=["AAPL"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval=Interval.DAILY,
)
results = fetcher.fetch(options)

# 結果を確認
result = results[0]
print(f"Symbol: {result.symbol}")
print(f"Source: {result.source}")  # DataSource.YFINANCE
print(f"Rows: {len(result.data)}")
print(result.data.head())
```

### FetchOptions パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `symbols` | `list[str]` | 必須 | 取得するシンボルのリスト |
| `start_date` | `datetime \| str \| None` | None | 開始日 |
| `end_date` | `datetime \| str \| None` | None | 終了日 |
| `interval` | `Interval` | `Interval.DAILY` | データ間隔 |
| `use_cache` | `bool` | True | キャッシュを使用するか |

### Interval 列挙型

| 値 | 文字列 | 説明 |
|----|--------|------|
| `Interval.DAILY` | "1d" | 日次 |
| `Interval.WEEKLY` | "1wk" | 週次 |
| `Interval.MONTHLY` | "1mo" | 月次 |
| `Interval.HOURLY` | "1h" | 時間足 |

### エラーハンドリング

```python
from market.yfinance import (
    YFinanceFetcher,
    FetchOptions,
    DataFetchError,
    ValidationError,
)

fetcher = YFinanceFetcher()

try:
    options = FetchOptions(symbols=["INVALID_SYMBOL"])
    results = fetcher.fetch(options)
except ValidationError as e:
    print(f"バリデーションエラー: {e}")
    print(f"フィールド: {e.field}")
    print(f"値: {e.value}")
except DataFetchError as e:
    print(f"データ取得エラー: {e}")
    print(f"シンボル: {e.symbol}")
    print(f"ソース: {e.source}")
    print(f"エラーコード: {e.code}")
```

### キャッシュとリトライ設定

```python
from market.yfinance import (
    YFinanceFetcher,
    CacheConfig,
    RetryConfig,
)

# キャッシュ設定
cache_config = CacheConfig(
    ttl_seconds=3600,  # 1時間
    max_entries=1000,
)

# リトライ設定
retry_config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
)

# 設定を適用
fetcher = YFinanceFetcher(
    cache_config=cache_config,
    retry_config=retry_config,
)
```

## fred モジュール

FRED (Federal Reserve Economic Data) から経済指標データを取得します。

### 基本的な使い方

```python
from market.fred import FREDFetcher, FRED_API_KEY_ENV
from market.fred.types import FetchOptions

# 環境変数 FRED_API_KEY を設定するか、コンストラクタで渡す
fetcher = FREDFetcher()

# 経済指標を取得
options = FetchOptions(symbols=["GDP", "CPIAUCSL", "UNRATE"])
results = fetcher.fetch(options)

for result in results:
    print(f"{result.symbol}: {len(result.data)} data points")
```

### 利用可能な定数

```python
from market.fred import FRED_API_KEY_ENV, FRED_SERIES_PATTERN

print(FRED_API_KEY_ENV)      # "FRED_API_KEY"
print(FRED_SERIES_PATTERN)   # FRED シリーズ ID の正規表現パターン
```

## export モジュール

データを各種フォーマットでエクスポートします。

### DataExporter

```python
from market import DataExporter

exporter = DataExporter()

# JSON エクスポート
exporter.to_json(data, "output.json")

# CSV エクスポート
exporter.to_csv(data, "output.csv")

# SQLite に保存 (UPSERT サポート)
exporter.to_sqlite(data, "database.db", "table_name")

# AI エージェント向け JSON 出力
agent_output = exporter.to_agent_json(data)
```

## ディレクトリ構造

```
src/market/
├── __init__.py          # 公開 API
├── README.md
├── types.py             # 共通型定義
├── errors.py            # 共通エラー定義
├── schema.py            # Pydantic V2 スキーマ
├── yfinance/            # Yahoo Finance データ取得
│   ├── __init__.py
│   ├── fetcher.py       # YFinanceFetcher
│   ├── types.py         # FetchOptions, Interval 等
│   └── errors.py        # DataFetchError, ValidationError
├── fred/                # FRED 経済指標データ取得
│   ├── __init__.py
│   ├── fetcher.py       # FREDFetcher
│   ├── base_fetcher.py
│   ├── cache.py
│   ├── constants.py
│   ├── types.py
│   └── errors.py
├── cache/               # キャッシュ機能
│   ├── __init__.py
│   ├── cache.py
│   └── types.py
├── export/              # データエクスポート
│   ├── __init__.py
│   └── exporter.py      # DataExporter
├── factset/             # FactSet 連携 (計画中)
│   └── __init__.py
├── alternative/         # オルタナティブデータ (計画中)
│   └── __init__.py
├── bloomberg/           # Bloomberg 連携 (計画中)
│   ├── __init__.py
│   ├── constants.py
│   ├── errors.py
│   ├── fetcher.py
│   └── types.py
└── utils/               # ユーティリティ
    ├── __init__.py
    └── logging_config.py
```

## 開発

### テスト実行

```bash
# 全テスト
uv run pytest tests/market/

# カバレッジ付き
uv run pytest tests/market/ --cov=src/market --cov-report=term-missing
```

### 品質チェック

```bash
# フォーマット
uv run ruff format src/market/ tests/market/

# リント
uv run ruff check src/market/ tests/market/

# 型チェック
uv run pyright src/market/ tests/market/
```

## 関連ドキュメント

- [パッケージリファクタリング計画](../../docs/project/package-refactoring.md)
- [コーディング規約](../../docs/coding-standards.md)
- [テスト戦略](../../docs/testing-strategy.md)

## ライセンス

MIT License
