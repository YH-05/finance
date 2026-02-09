# market.yfinance

Yahoo Finance から株式・指数・為替・先物の OHLCV データを取得するモジュール。

## 概要

yfinance ライブラリと curl_cffi を使用して Yahoo Finance からマーケットデータを取得します。ブラウザの TLS フィンガープリントを模倣することで、レート制限を回避しています。

**対応データ:**

- **株式**: AAPL, MSFT, GOOGL, BRK.B など
- **指数**: ^GSPC (S&P 500), ^DJI (ダウ), ^IXIC (NASDAQ) など
- **為替**: USDJPY=X, EURUSD=X など
- **先物**: GC=F (金), CL=F (原油) など

## クイックスタート

```python
from market.yfinance import YFinanceFetcher, FetchOptions

# 1. フェッチャーを作成
fetcher = YFinanceFetcher()

# 2. 株価データを取得
options = FetchOptions(
    symbols=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
results = fetcher.fetch(options)

# 3. 結果を確認
for result in results:
    print(f"{result.symbol}: {result.row_count} 件")
    print(result.data.tail())
```

## 使い方

### コンテキストマネージャーでの使用

```python
with YFinanceFetcher() as fetcher:
    options = FetchOptions(symbols=["^GSPC"], start_date="2024-01-01")
    results = fetcher.fetch(options)
    # セッションは自動的にクローズされる
```

### リトライ設定

```python
from market.yfinance import YFinanceFetcher, RetryConfig, FetchOptions

retry_config = RetryConfig(
    max_attempts=5,        # 最大5回試行
    initial_delay=1.0,     # 初回リトライまで1秒待機
    max_delay=30.0,        # 最大待機時間
    exponential_base=2.0,  # 指数バックオフ（1秒→2秒→4秒...）
    jitter=True,           # ランダムジッターを追加
)

fetcher = YFinanceFetcher(retry_config=retry_config)
```

### キャッシュ設定

```python
from market.yfinance import YFinanceFetcher, CacheConfig

cache_config = CacheConfig(
    enabled=True,
    ttl_seconds=3600,     # 1時間
    max_entries=1000,
    db_path="./data/cache/yfinance.db",
)

fetcher = YFinanceFetcher(cache_config=cache_config)
```

### カスタム HTTP セッションの注入

テストや特殊な環境向けにセッションを注入可能:

```python
from market.yfinance import YFinanceFetcher
from market.yfinance.session import StandardRequestsSession

# requests ベースのセッションを使用
session = StandardRequestsSession()
fetcher = YFinanceFetcher(http_session=session)
```

### シンボルのバリデーション

```python
fetcher = YFinanceFetcher()

# 有効なシンボル
fetcher.validate_symbol("AAPL")      # True（株式）
fetcher.validate_symbol("^GSPC")     # True（指数）
fetcher.validate_symbol("USDJPY=X")  # True（為替）
fetcher.validate_symbol("GC=F")      # True（先物）
fetcher.validate_symbol("BRK.B")     # True（ドット付き）

# 無効なシンボル
fetcher.validate_symbol("")           # False
fetcher.validate_symbol("invalid!")   # False
```

### データ間隔の指定

```python
from market.yfinance import FetchOptions, Interval

# 日次データ（デフォルト）
options = FetchOptions(symbols=["AAPL"], interval=Interval.DAILY)

# 週次データ
options = FetchOptions(symbols=["AAPL"], interval=Interval.WEEKLY)

# 月次データ
options = FetchOptions(symbols=["AAPL"], interval=Interval.MONTHLY)

# 時間足データ（過去730日以内のみ）
options = FetchOptions(symbols=["AAPL"], interval=Interval.HOURLY)
```

## API リファレンス

### YFinanceFetcher

Yahoo Finance データフェッチャーのメインクラス。

**コンストラクタ:**

```python
YFinanceFetcher(
    cache_config: CacheConfig | None = None,
    retry_config: RetryConfig | None = None,
    impersonate: BrowserTypeLiteral | None = None,
    http_session: HttpSessionProtocol | None = None,
)
```

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `cache_config` | `CacheConfig \| None` | キャッシュ設定 |
| `retry_config` | `RetryConfig \| None` | リトライ設定 |
| `impersonate` | `BrowserTypeLiteral \| None` | ブラウザ偽装対象。None の場合ランダム選択 |
| `http_session` | `HttpSessionProtocol \| None` | カスタム HTTP セッション（DI 用） |

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `fetch(options)` | 指定シンボルのデータを一括取得 | `list[MarketDataResult]` |
| `validate_symbol(symbol)` | シンボルの形式を検証 | `bool` |
| `close()` | セッションを閉じる | `None` |

**プロパティ:**

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `source` | `DataSource` | 常に `DataSource.YFINANCE` |
| `default_interval` | `Interval` | 常に `Interval.DAILY` |

### FetchOptions

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `symbols` | `list[str]` | 必須 | 取得するシンボルのリスト |
| `start_date` | `datetime \| str \| None` | None | 取得開始日 |
| `end_date` | `datetime \| str \| None` | None | 取得終了日 |
| `interval` | `Interval` | DAILY | データ間隔 |
| `use_cache` | `bool` | True | キャッシュを使用するか |

### MarketDataResult

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `symbol` | `str` | シンボル |
| `data` | `pd.DataFrame` | OHLCV データ（open, high, low, close, volume） |
| `source` | `DataSource` | データソース |
| `fetched_at` | `datetime` | 取得日時 |
| `from_cache` | `bool` | キャッシュからの取得か |
| `metadata` | `dict[str, Any]` | メタデータ |
| `is_empty` | `bool` | データが空か（プロパティ） |
| `row_count` | `int` | 行数（プロパティ） |

### Interval（列挙型）

| 値 | yfinance 文字列 | 説明 |
|----|-----------------|------|
| `DAILY` | `1d` | 日次 |
| `WEEKLY` | `1wk` | 週次 |
| `MONTHLY` | `1mo` | 月次 |
| `HOURLY` | `1h` | 時間足 |
| `MINUTE` | `1m` | 分足 |

### セッションクラス

| クラス | 説明 |
|--------|------|
| `HttpSessionProtocol` | HTTP セッションのプロトコル定義（Protocol） |
| `CurlCffiSession` | curl_cffi ベースのセッション。ブラウザ TLS フィンガープリント偽装 |
| `StandardRequestsSession` | requests ベースの標準セッション |

### 例外クラス

| 例外 | 説明 |
|------|------|
| `DataFetchError` | データ取得エラー（API エラー、ネットワークエラー） |
| `ValidationError` | 入力バリデーションエラー（無効なシンボルなど） |

## 設計

### ブラウザ偽装

Yahoo Finance のレート制限を回避するため、curl_cffi を使用して実際のブラウザの TLS フィンガープリントを模倣します。

対応ブラウザ:
- `chrome`, `chrome110`, `chrome120`
- `edge99`
- `safari15_3`

リトライ時にはブラウザフィンガープリントをローテーションして検出を回避します。

### バルクダウンロード

`yf.download()` を使用して複数シンボルを効率的に一括取得します。マルチスレッド対応。

## モジュール構成

```
market/yfinance/
├── __init__.py    # パッケージエクスポート
├── fetcher.py     # YFinanceFetcher 実装
├── types.py       # 型定義（FetchOptions, MarketDataResult 等）
├── session.py     # HTTP セッション抽象化（Protocol, CurlCffi, Requests）
└── README.md      # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| yfinance | Yahoo Finance API クライアント |
| curl_cffi | ブラウザ TLS フィンガープリント偽装 |
| requests | 標準 HTTP セッション（フォールバック） |
| pandas | データフレーム操作 |

## 関連モジュール

- [market.fred](../fred/README.md) - FRED 経済指標データ取得
- [market.bloomberg](../bloomberg/README.md) - Bloomberg Terminal データ取得
- [market.cache](../cache/README.md) - キャッシュ機能
- [market.export](../export/README.md) - データエクスポート
