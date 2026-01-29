# market.fred

FRED（Federal Reserve Economic Data）API を使用して経済指標データを取得するモジュール。

## 概要

このモジュールは、米国連邦準備銀行が提供する FRED サービスから経済指標データを取得する機能を提供します。

**取得可能なデータ:**

- **経済成長**: GDP、実質GDP、GDPデフレーター
- **物価指標**: CPI（消費者物価指数）、PCE（個人消費支出）、PPI（生産者物価指数）
- **雇用統計**: 失業率、非農業部門雇用者数、労働参加率
- **金利**: FF金利、国債利回り（2年/10年/30年）、イールドカーブ
- **マネーサプライ**: M1、M2、マネタリーベース
- **住宅市場**: 住宅着工件数、中古住宅販売、住宅価格指数

## インストール

このモジュールは `market` パッケージの一部です。

```bash
# リポジトリ全体の依存関係をインストール
uv sync --all-extras
```

## 設定

### API キーの取得

FRED API を使用するには API キーが必要です。

1. [FRED API キー取得ページ](https://fred.stlouisfed.org/docs/api/api_key.html) にアクセス
2. アカウントを作成（無料）
3. API キーを発行

### API キーの設定

**方法1: 環境変数（推奨）**

```bash
export FRED_API_KEY="your_api_key_here"
```

**方法2: .env ファイル**

```bash
# .env ファイルに追加
FRED_API_KEY=your_api_key_here
```

**方法3: 直接指定**

```python
fetcher = FREDFetcher(api_key="your_api_key_here")
```

## クイックスタート

### 5分で試せる基本的な使い方

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions

# 1. フェッチャーを作成（環境変数から API キーを読み込み）
fetcher = FREDFetcher()

# 2. GDP データを取得
options = FetchOptions(
    symbols=["GDP"],
    start_date="2020-01-01",
    end_date="2024-12-31",
)
results = fetcher.fetch(options)

# 3. 結果を確認
result = results[0]
print(f"シリーズ: {result.symbol}")
print(f"データ件数: {len(result.data)} 件")
print(result.data.head())
```

**出力例:**

```
シリーズ: GDP
データ件数: 20 件
            value
date
2020-01-01  21481.367
2020-04-01  19477.444
2020-07-01  21138.574
...
```

## 履歴データのローカルキャッシュ

プリセット定義（`data/config/fred_series.json`）のシリーズについて、データ提供開始時点からの全履歴データをローカルにキャッシュできます。

### 設定

**方法1: 環境変数（推奨）**

```bash
export FRED_HISTORICAL_CACHE_DIR="/path/to/cache/dir"
```

**方法2: .env ファイル**

```bash
# .env ファイルに追加
FRED_HISTORICAL_CACHE_DIR=/path/to/cache/dir
```

**方法3: 直接指定**

```python
from market.fred.historical_cache import HistoricalCache

cache = HistoricalCache(base_path="/custom/path")
```

環境変数未設定の場合、デフォルトは `data/raw/fred/indicators/` です。

### CLI での使用

```bash
# 全プリセットを同期
uv run python -m market.fred.scripts.sync_historical --all

# カテゴリ指定
uv run python -m market.fred.scripts.sync_historical --category "Treasury Yields"

# 単一シリーズ
uv run python -m market.fred.scripts.sync_historical --series DGS10

# 同期状況確認
uv run python -m market.fred.scripts.sync_historical --status

# 保存先ディレクトリ指定（環境変数より優先）
uv run python -m market.fred.scripts.sync_historical --all --output-dir /custom/path

# cron用（24時間以上古いデータのみ更新）
uv run python -m market.fred.scripts.sync_historical --auto
uv run python -m market.fred.scripts.sync_historical --auto --stale-hours 48
```

### Python からの使用

```python
from market.fred.historical_cache import HistoricalCache

# 環境変数またはデフォルトパスを使用
cache = HistoricalCache()

# カスタムパス指定
cache = HistoricalCache(base_path="/custom/path")

# 全プリセットを同期
results = cache.sync_all_presets()

# カテゴリ単位で同期
results = cache.sync_category("Treasury Yields")

# 単一シリーズを同期
result = cache.sync_series("DGS10")

# キャッシュからデータ取得（DataFrame形式）
df = cache.get_series_df("DGS10")
print(df.head())

# キャッシュからデータ取得（dict形式）
data = cache.get_series("DGS10")

# 同期状況確認
status = cache.get_status()
for series_id, info in status.items():
    if info["cached"]:
        print(f"{series_id}: {info['data_points']} points")
    else:
        print(f"{series_id}: not cached")

# キャッシュ無効化（次回同期時に全件再取得）
cache.invalidate("DGS10")
```

### cron 設定例

```bash
# 毎日 AM 6:00 に増分更新（24時間以上古いデータのみ）
0 6 * * * cd /path/to/finance && uv run python -m market.fred.scripts.sync_historical --auto
```

### キャッシュファイル構造

```
data/raw/fred/indicators/
├── _index.json      # 全シリーズの管理メタデータ
├── DGS10.json       # 10年国債利回り
├── GDP.json         # 名目GDP
└── ...
```

各シリーズの JSON 構造:

```json
{
  "series_id": "DGS10",
  "preset_info": {
    "name_ja": "10年国債利回り",
    "name_en": "10-Year Treasury Constant Maturity Rate",
    "category": "interest_rate",
    "frequency": "daily",
    "units": "percent"
  },
  "fred_metadata": {
    "observation_start": "1962-01-02",
    "observation_end": "2026-01-28",
    "title": "10-Year Treasury Constant Maturity Rate",
    "last_updated_api": "2026-01-28T15:16:00+00:00"
  },
  "cache_metadata": {
    "last_fetched": "2026-01-29T10:00:00+00:00",
    "data_points": 15847,
    "version": 1
  },
  "data": [
    {"date": "1962-01-02", "value": 4.06},
    {"date": "1962-01-03", "value": 4.03}
  ]
}
```

## 詳細な使い方

### 複数の経済指標を一括取得

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions

fetcher = FREDFetcher()

# 主要な経済指標を一括取得
options = FetchOptions(
    symbols=[
        "GDP",       # 名目GDP
        "CPIAUCSL",  # 消費者物価指数
        "UNRATE",    # 失業率
        "FEDFUNDS",  # FF金利
        "DGS10",     # 10年国債利回り
    ],
    start_date="2020-01-01",
)
results = fetcher.fetch(options)

# 各指標のデータを確認
for result in results:
    print(f"\n{result.symbol}:")
    print(f"  データ件数: {result.row_count}")
    print(f"  期間: {result.data.index.min()} 〜 {result.data.index.max()}")
    print(f"  最新値: {result.data['value'].iloc[-1]:.2f}")
```

### キャッシュを使用した効率的なデータ取得

FRED API には利用制限があるため、キャッシュの使用を推奨します。

```python
from market.fred import FREDFetcher
from market.fred.cache import SQLiteCache
from market.fred.types import CacheConfig, FetchOptions

# キャッシュ設定（24時間有効）
cache_config = CacheConfig(
    ttl_seconds=86400,  # 24時間
    db_path="./data/fred_cache.db",
)

# キャッシュインスタンスを作成
cache = SQLiteCache(cache_config)

# キャッシュ付きフェッチャーを作成
fetcher = FREDFetcher(cache=cache, cache_config=cache_config)

# データ取得（初回は API から取得、2回目以降はキャッシュから取得）
options = FetchOptions(symbols=["GDP", "CPIAUCSL"], start_date="2020-01-01")
results = fetcher.fetch(options)

# キャッシュを無効にして最新データを強制取得
options_no_cache = FetchOptions(
    symbols=["GDP"],
    start_date="2020-01-01",
    use_cache=False,  # キャッシュを使用しない
)
fresh_results = fetcher.fetch(options_no_cache)
```

### リトライ設定によるエラーハンドリング

ネットワークエラーや一時的な API エラーに対応するリトライ機能:

```python
from market.fred import FREDFetcher
from market.fred.types import RetryConfig, FetchOptions

# リトライ設定
retry_config = RetryConfig(
    max_attempts=5,        # 最大5回試行
    initial_delay=1.0,     # 初回リトライまで1秒待機
    exponential_base=2.0,  # 指数バックオフ（1秒→2秒→4秒→8秒）
)

fetcher = FREDFetcher(retry_config=retry_config)

# エラー時も自動リトライ
options = FetchOptions(symbols=["GDP"], start_date="2020-01-01")
results = fetcher.fetch(options)
```

### シリーズ情報の取得

データ取得前にシリーズのメタデータを確認:

```python
fetcher = FREDFetcher()

# GDP のメタデータを取得
info = fetcher.get_series_info("GDP")

print(f"タイトル: {info['title']}")
print(f"単位: {info['units']}")
print(f"頻度: {info['frequency']}")
print(f"季節調整: {info['seasonal_adjustment']}")
print(f"最終更新: {info['last_updated']}")
```

**出力例:**

```
タイトル: Gross Domestic Product
単位: Billions of Dollars
頻度: Quarterly
季節調整: Seasonally Adjusted Annual Rate
最終更新: 2024-12-20
```

### シンボルのバリデーション

FRED シリーズ ID は大文字英字・数字・アンダースコアで構成されます:

```python
fetcher = FREDFetcher()

# 有効なシリーズ ID
print(fetcher.validate_symbol("GDP"))       # True
print(fetcher.validate_symbol("CPIAUCSL"))  # True
print(fetcher.validate_symbol("DGS10"))     # True
print(fetcher.validate_symbol("T10Y2Y"))    # True

# 無効なシリーズ ID
print(fetcher.validate_symbol("gdp"))       # False（小文字は不可）
print(fetcher.validate_symbol("123ABC"))    # False（数字始まりは不可）
print(fetcher.validate_symbol("GDP-CPI"))   # False（ハイフンは不可）
```

### pandas DataFrame との連携

取得したデータは pandas DataFrame として利用可能:

```python
import pandas as pd
from market.fred import FREDFetcher
from market.fred.types import FetchOptions

fetcher = FREDFetcher()

# 複数指標を取得
options = FetchOptions(
    symbols=["GDP", "CPIAUCSL", "UNRATE"],
    start_date="2015-01-01",
)
results = fetcher.fetch(options)

# 各指標を DataFrame に統合
dfs = {}
for result in results:
    dfs[result.symbol] = result.data["value"]

# 1つの DataFrame に結合
combined = pd.DataFrame(dfs)
print(combined.tail())

# 相関分析
print("\n相関行列:")
print(combined.corr())

# 前年同期比の計算（四半期データの場合）
combined["GDP_YoY"] = combined["GDP"].pct_change(4) * 100
print("\nGDP 前年同期比:")
print(combined[["GDP", "GDP_YoY"]].tail())
```

### 金利・イールドカーブ分析

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
    start_date="2023-01-01",
)
results = fetcher.fetch(options)

# イールドカーブを構築
yields = {r.symbol: r.data["value"].iloc[-1] for r in results}
print("最新のイールドカーブ:")
for symbol, rate in yields.items():
    print(f"  {symbol}: {rate:.2f}%")

# 2年-10年スプレッド（逆イールドの判定）
spread = yields["DGS10"] - yields["DGS2"]
print(f"\n2年-10年スプレッド: {spread:.2f}%")
if spread < 0:
    print("⚠️ 逆イールド発生中（景気後退のシグナル）")
```

## よく使う FRED シリーズ ID 一覧

### 経済成長

| シリーズ ID | 説明 | 頻度 |
|------------|------|------|
| GDP | 名目GDP | 四半期 |
| GDPC1 | 実質GDP | 四半期 |
| A191RL1Q225SBEA | 実質GDP成長率（前期比年率） | 四半期 |

### 物価指標

| シリーズ ID | 説明 | 頻度 |
|------------|------|------|
| CPIAUCSL | 消費者物価指数（都市部全品目） | 月次 |
| CPILFESL | コアCPI（食品・エネルギー除く） | 月次 |
| PCEPI | PCE物価指数 | 月次 |
| PCEPILFE | コアPCE物価指数 | 月次 |

### 雇用統計

| シリーズ ID | 説明 | 頻度 |
|------------|------|------|
| UNRATE | 失業率 | 月次 |
| PAYEMS | 非農業部門雇用者数 | 月次 |
| CIVPART | 労働参加率 | 月次 |
| ICSA | 新規失業保険申請件数 | 週次 |

### 金利・国債

| シリーズ ID | 説明 | 頻度 |
|------------|------|------|
| FEDFUNDS | FF金利（実効） | 日次 |
| DFEDTARU | FF金利誘導目標（上限） | 日次 |
| DGS2 | 2年国債利回り | 日次 |
| DGS10 | 10年国債利回り | 日次 |
| DGS30 | 30年国債利回り | 日次 |
| T10Y2Y | 10年-2年スプレッド | 日次 |
| T10Y3M | 10年-3ヶ月スプレッド | 日次 |

### マネーサプライ

| シリーズ ID | 説明 | 頻度 |
|------------|------|------|
| M1SL | M1（狭義マネーサプライ） | 月次 |
| M2SL | M2（広義マネーサプライ） | 月次 |
| BOGMBASE | マネタリーベース | 月次 |

### 住宅市場

| シリーズ ID | 説明 | 頻度 |
|------------|------|------|
| HOUST | 住宅着工件数 | 月次 |
| EXHOSLUSM495S | 中古住宅販売件数 | 月次 |
| CSUSHPINSA | S&P/ケース・シラー住宅価格指数 | 月次 |
| MORTGAGE30US | 30年固定住宅ローン金利 | 週次 |

### 株式・金融市場

| シリーズ ID | 説明 | 頻度 |
|------------|------|------|
| SP500 | S&P 500 指数 | 日次 |
| VIXCLS | VIX（恐怖指数） | 日次 |
| BAMLH0A0HYM2 | ハイイールド債スプレッド | 日次 |

## API リファレンス

### FREDFetcher

FRED データを取得するメインクラス。

**コンストラクタ:**

```python
FREDFetcher(
    api_key: str | None = None,
    cache: SQLiteCache | None = None,
    cache_config: CacheConfig | None = None,
    retry_config: RetryConfig | None = None,
)
```

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `api_key` | `str \| None` | FRED API キー。None の場合は環境変数 `FRED_API_KEY` を使用 |
| `cache` | `SQLiteCache \| None` | キャッシュインスタンス |
| `cache_config` | `CacheConfig \| None` | キャッシュ設定 |
| `retry_config` | `RetryConfig \| None` | リトライ設定 |

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `fetch(options)` | 指定したシリーズのデータを取得 | `list[MarketDataResult]` |
| `validate_symbol(symbol)` | シリーズ ID の形式を検証 | `bool` |
| `get_series_info(series_id)` | シリーズのメタデータを取得 | `dict` |

### FetchOptions

データ取得オプションを指定するクラス。

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `symbols` | `list[str]` | 必須 | 取得するシリーズ ID のリスト |
| `start_date` | `datetime \| str \| None` | None | 取得開始日 |
| `end_date` | `datetime \| str \| None` | None | 取得終了日 |
| `interval` | `Interval` | DAILY | データ間隔 |
| `use_cache` | `bool` | True | キャッシュを使用するか |

### CacheConfig

キャッシュ設定クラス。

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `ttl_seconds` | `int` | 3600 | キャッシュ有効期間（秒） |
| `db_path` | `str` | `:memory:` | SQLite データベースパス |

### RetryConfig

リトライ設定クラス。

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `max_attempts` | `int` | 3 | 最大試行回数 |
| `initial_delay` | `float` | 1.0 | 初回リトライまでの待機時間（秒） |
| `exponential_base` | `float` | 2.0 | 指数バックオフの基数 |

### 例外クラス

| 例外 | 説明 |
|------|------|
| `FREDValidationError` | 入力バリデーションエラー（無効なシリーズ ID など） |
| `FREDFetchError` | データ取得エラー（API エラー、ネットワークエラーなど） |

## モジュール構成

```
market/fred/
├── __init__.py          # パッケージエクスポート
├── constants.py         # 定数（FRED_API_KEY_ENV, FRED_SERIES_PATTERN）
├── errors.py            # 例外クラス
├── types.py             # 型定義（FetchOptions, MarketDataResult 等）
├── cache.py             # SQLiteCache（リクエストキャッシュ）
├── historical_cache.py  # HistoricalCache（履歴データキャッシュ）
├── base_fetcher.py      # 抽象基底クラス
├── fetcher.py           # FREDFetcher 実装
├── scripts/
│   └── sync_historical.py  # 履歴データ同期 CLI スクリプト
└── README.md            # このファイル
```

## 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `FRED_API_KEY` | FRED API キー | なし（必須） |
| `FRED_HISTORICAL_CACHE_DIR` | 履歴データキャッシュの保存先 | `data/raw/fred/indicators/` |

## トラブルシューティング

### API キーエラー

```
FREDFetchError: API key not found
```

**解決方法:** 環境変数 `FRED_API_KEY` を設定するか、`FREDFetcher(api_key="...")` で直接指定してください。

### レート制限エラー

```
FREDFetchError: Rate limit exceeded
```

**解決方法:**
- キャッシュを有効にして API 呼び出し回数を削減
- `RetryConfig` で適切なリトライ間隔を設定
- FRED API の制限は 1秒あたり 120 リクエスト

### 無効なシリーズ ID

```
FREDValidationError: Invalid series ID: xxx
```

**解決方法:**
- シリーズ ID は大文字英字で始まる必要があります
- [FRED ウェブサイト](https://fred.stlouisfed.org/) でシリーズ ID を確認

## 関連リンク

- [FRED 公式サイト](https://fred.stlouisfed.org/)
- [FRED API ドキュメント](https://fred.stlouisfed.org/docs/api/fred/)
- [シリーズ検索](https://fred.stlouisfed.org/tags/series)
