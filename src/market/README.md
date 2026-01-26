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

Yahoo Finance から OHLCV データを取得します。curl_cffi によるブラウザ偽装でレート制限を回避します。

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

### 複数シンボルの一括取得

yf.download() を使用した効率的な一括取得をサポートしています。

```python
from market.yfinance import YFinanceFetcher, FetchOptions, Interval

fetcher = YFinanceFetcher()

# MAG7 銘柄を一括取得
options = FetchOptions(
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval=Interval.DAILY,
)

results = fetcher.fetch(options)

# 各銘柄の結果を処理
for result in results:
    if not result.is_empty:
        df = result.data
        print(f"{result.symbol}: {result.row_count} rows")
        print(f"  期間: {df.index.min()} 〜 {df.index.max()}")
        print(f"  終値範囲: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
```

### 株価指数・為替レートの取得

```python
from market.yfinance import YFinanceFetcher, FetchOptions

fetcher = YFinanceFetcher()

# 株価指数を取得
index_options = FetchOptions(
    symbols=["^GSPC", "^DJI", "^IXIC", "^N225"],  # S&P500, ダウ, ナスダック, 日経225
    start_date="2024-01-01",
)
index_results = fetcher.fetch(index_options)

for result in index_results:
    print(f"{result.symbol}: {result.row_count} data points")

# 為替レートを取得
forex_options = FetchOptions(
    symbols=["USDJPY=X", "EURUSD=X", "GBPUSD=X"],
    start_date="2024-01-01",
)
forex_results = fetcher.fetch(forex_options)

for result in forex_results:
    if not result.is_empty:
        latest = result.data['close'].iloc[-1]
        print(f"{result.symbol}: {latest:.4f}")
```

### 時間足データの取得

```python
from market.yfinance import YFinanceFetcher, FetchOptions, Interval

fetcher = YFinanceFetcher()

# 週次データ
weekly_options = FetchOptions(
    symbols=["AAPL"],
    start_date="2020-01-01",
    interval=Interval.WEEKLY,
)

# 月次データ
monthly_options = FetchOptions(
    symbols=["AAPL"],
    start_date="2015-01-01",
    interval=Interval.MONTHLY,
)

# 時間足（直近60日間のみ取得可能）
hourly_options = FetchOptions(
    symbols=["AAPL"],
    interval=Interval.HOURLY,  # 過去60日間の制限あり
)
```

### コンテキストマネージャーの使用

```python
from market.yfinance import YFinanceFetcher, FetchOptions

# with 文でリソースを自動解放
with YFinanceFetcher() as fetcher:
    options = FetchOptions(
        symbols=["AAPL", "GOOGL"],
        start_date="2024-01-01",
    )
    results = fetcher.fetch(options)

    for result in results:
        print(f"{result.symbol}: {result.row_count} rows")
# セッションが自動的にクローズされる
```

### データの操作例

```python
from market.yfinance import YFinanceFetcher, FetchOptions
import pandas as pd

fetcher = YFinanceFetcher()

options = FetchOptions(
    symbols=["AAPL"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
results = fetcher.fetch(options)
result = results[0]

# DataFrame の構造
# columns: ['open', 'high', 'low', 'close', 'volume']
# index: DatetimeIndex
df = result.data

# 日次リターンの計算
df['daily_return'] = df['close'].pct_change()

# 移動平均の追加
df['sma_20'] = df['close'].rolling(window=20).mean()
df['sma_50'] = df['close'].rolling(window=50).mean()

# 統計情報
print(f"平均終値: ${df['close'].mean():.2f}")
print(f"最高値: ${df['high'].max():.2f}")
print(f"最安値: ${df['low'].min():.2f}")
print(f"平均出来高: {df['volume'].mean():,.0f}")
print(f"日次リターン標準偏差: {df['daily_return'].std():.4f}")
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

### 前提条件

FRED API キーが必要です。[FRED](https://fred.stlouisfed.org/) でアカウントを作成し、API キーを取得してください。

```bash
# 環境変数に設定
export FRED_API_KEY="your_api_key_here"
```

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

### 代表的な経済指標の取得

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions

fetcher = FREDFetcher()

# 主要経済指標
options = FetchOptions(
    symbols=[
        "GDP",       # 国内総生産（四半期）
        "CPIAUCSL",  # 消費者物価指数（月次）
        "UNRATE",    # 失業率（月次）
        "FEDFUNDS",  # フェデラルファンド金利（日次）
        "DGS10",     # 10年国債利回り（日次）
        "DGS2",      # 2年国債利回り（日次）
    ],
    start_date="2020-01-01",
    end_date="2024-12-31",
)

results = fetcher.fetch(options)

for result in results:
    if not result.is_empty:
        df = result.data
        # FRED データは close カラムに値が格納される
        print(f"{result.symbol}:")
        print(f"  期間: {df.index.min()} 〜 {df.index.max()}")
        print(f"  最新値: {df['close'].iloc[-1]:.2f}")
        print(f"  データ点数: {result.row_count}")
```

### FRED シリーズ ID 一覧（よく使う指標）

| シリーズ ID | 説明 | 頻度 |
|-------------|------|------|
| `GDP` | 国内総生産 | 四半期 |
| `GDPC1` | 実質 GDP | 四半期 |
| `CPIAUCSL` | 消費者物価指数（全項目） | 月次 |
| `CPILFESL` | コア CPI（食料・エネルギー除く） | 月次 |
| `UNRATE` | 失業率 | 月次 |
| `PAYEMS` | 非農業部門雇用者数 | 月次 |
| `FEDFUNDS` | フェデラルファンド金利 | 日次/月次 |
| `DGS10` | 10年国債利回り | 日次 |
| `DGS2` | 2年国債利回り | 日次 |
| `DGS30` | 30年国債利回り | 日次 |
| `T10Y2Y` | 10年-2年スプレッド（イールドカーブ） | 日次 |
| `VIXCLS` | VIX 恐怖指数 | 日次 |
| `DEXJPUS` | ドル円為替レート | 日次 |
| `M2SL` | M2 マネーサプライ | 月次 |
| `UMCSENT` | ミシガン大学消費者信頼感指数 | 月次 |

### シリーズ情報の取得

```python
from market.fred import FREDFetcher

fetcher = FREDFetcher()

# シリーズのメタデータを取得
info = fetcher.get_series_info("GDP")
print(f"タイトル: {info.get('title')}")
print(f"単位: {info.get('units')}")
print(f"頻度: {info.get('frequency')}")
print(f"季節調整: {info.get('seasonal_adjustment')}")
```

### イールドカーブ分析の例

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions
import pandas as pd

fetcher = FREDFetcher()

# 各年限の国債利回りを取得
options = FetchOptions(
    symbols=[
        "DGS1MO",  # 1ヶ月
        "DGS3MO",  # 3ヶ月
        "DGS6MO",  # 6ヶ月
        "DGS1",    # 1年
        "DGS2",    # 2年
        "DGS5",    # 5年
        "DGS10",   # 10年
        "DGS30",   # 30年
    ],
    start_date="2024-01-01",
)

results = fetcher.fetch(options)

# 最新のイールドカーブを構築
yield_curve = {}
for result in results:
    if not result.is_empty:
        yield_curve[result.symbol] = result.data['close'].iloc[-1]

print("最新イールドカーブ:")
for series_id, value in yield_curve.items():
    print(f"  {series_id}: {value:.2f}%")

# 10年-2年スプレッド（景気後退の先行指標）
if "DGS10" in yield_curve and "DGS2" in yield_curve:
    spread = yield_curve["DGS10"] - yield_curve["DGS2"]
    print(f"\n10年-2年スプレッド: {spread:.2f}%")
    if spread < 0:
        print("⚠️ 逆イールド発生中（景気後退の可能性）")
```

### キャッシュとリトライの設定

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions, CacheConfig, RetryConfig
from market.fred.cache import SQLiteCache

# キャッシュ設定
cache_config = CacheConfig(
    enabled=True,
    ttl_seconds=86400,  # 24時間
    db_path="./cache/fred_cache.db",
)

# リトライ設定
retry_config = RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
)

# キャッシュを初期化
cache = SQLiteCache(db_path="./cache/fred_cache.db")

# フェッチャーを初期化
fetcher = FREDFetcher(
    cache=cache,
    cache_config=cache_config,
    retry_config=retry_config,
)

options = FetchOptions(
    symbols=["GDP", "CPIAUCSL"],
    start_date="2020-01-01",
    use_cache=True,  # キャッシュを使用
)

results = fetcher.fetch(options)

for result in results:
    cache_status = "キャッシュから取得" if result.from_cache else "API から取得"
    print(f"{result.symbol}: {cache_status}")
```

### エラーハンドリング

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions
from market.fred.errors import FREDFetchError, FREDValidationError

try:
    fetcher = FREDFetcher()
    options = FetchOptions(symbols=["INVALID_SERIES_ID"])
    results = fetcher.fetch(options)
except FREDValidationError as e:
    print(f"バリデーションエラー: {e}")
    # API キーが設定されていない場合など
except FREDFetchError as e:
    print(f"データ取得エラー: {e}")
    # 存在しないシリーズ ID、ネットワークエラーなど
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
