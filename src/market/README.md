# market - 金融データ取得パッケージ

金融市場データを取得するための統合パッケージ。Yahoo Finance、FRED、Bloomberg など複数のデータソースに対応。

## インストール

```bash
# uv を使用
uv add market

# または pip
pip install market
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
| `market.yfinance` | Yahoo Finance データ取得 | ✅ 実装済み |
| `market.fred` | FRED 経済指標データ取得 | ✅ 実装済み |
| `market.factset` | FactSet データ取得 | 🚧 計画中 |
| `market.alternative` | オルタナティブデータ | 🚧 計画中 |
| `market.bloomberg` | Bloomberg データ取得 | 🚧 計画中 |
| `market.export` | データエクスポート | ✅ 実装済み |

## yfinance モジュール

### 主要クラス

#### YFinanceFetcher

Yahoo Finance からOHLCVデータを取得するフェッチャー。

```python
from market.yfinance import (
    YFinanceFetcher,
    FetchOptions,
    Interval,
    DataSource,
)

# 基本的な使用法
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

#### FetchOptions

データ取得オプションを指定するデータクラス。

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `symbols` | `list[str]` | 必須 | 取得するシンボルのリスト |
| `start_date` | `datetime \| str \| None` | None | 開始日 |
| `end_date` | `datetime \| str \| None` | None | 終了日 |
| `interval` | `Interval` | `Interval.DAILY` | データ間隔 |
| `use_cache` | `bool` | True | キャッシュを使用するか |

#### Interval

サポートされるデータ間隔。

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

### キャッシュ設定

```python
from market.yfinance import (
    YFinanceFetcher,
    FetchOptions,
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

## ディレクトリ構造

```
src/market/
├── __init__.py
├── README.md
├── types.py             # 共通型定義
├── errors.py            # 共通エラー定義
├── yfinance/            # Yahoo Finance データ取得
│   ├── __init__.py
│   ├── fetcher.py
│   ├── types.py
│   └── errors.py
├── fred/                # FRED 経済指標データ取得
│   ├── __init__.py
│   ├── README.md
│   ├── fetcher.py
│   ├── base_fetcher.py
│   ├── cache.py
│   ├── constants.py
│   ├── types.py
│   └── errors.py
├── factset/             # FactSet 連携（計画中）
│   ├── __init__.py
│   └── README.md
├── alternative/         # オルタナティブデータ（計画中）
│   ├── __init__.py
│   └── README.md
├── export/              # データエクスポート
│   ├── __init__.py
│   └── exporter.py
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
