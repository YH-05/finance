# yfinance 開発ベストプラクティス

> **ソース**: `src/market_analysis/dev/` の開発コードから抽出

## 概要

yfinance を使用した金融データ取得の工夫ポイントをまとめたドキュメント。
rate limiting 回避、効率的なデータ取得、適切なエラーハンドリングのベストプラクティスを記載。

---

## 1. curl_cffi によるセッション管理

### 目的

- yfinance の rate limiting 回避
- 403 エラー対策
- ブラウザ偽装によるアクセス安定化

### 実装パターン

```python
import curl_cffi
import yfinance as yf

class YfinanceFetcher:
    def __init__(self):
        # クラスレベルでセッションを共有（リソース効率化）
        self.session = curl_cffi.requests.Session(impersonate="safari15_5")

    def get_ticker_data(self, symbol: str):
        # sessionをyfinanceに渡す
        ticker = yf.Ticker(symbol, session=self.session)
        return ticker.info
```

### 注意点

- **セッションはクラスレベルで共有**: メソッドごとに新規作成しない
- **impersonate オプション**: `"safari15_5"` が推奨（安定性が高い）
- **イントラデイデータ**: session を渡すとエラーになる場合がある

---

## 2. 複数銘柄の一括データ取得

### 基本パターン

```python
import yfinance as yf
import pandas as pd
import curl_cffi

def download_multiple_tickers(
    tickers: list[str],
    period: str = "2y",
    interval: str = "1d",
) -> pd.DataFrame:
    session = curl_cffi.Session(impersonate="safari15_5")

    df = yf.download(
        tickers=tickers,        # リストで複数銘柄を指定
        period=period,
        interval=interval,
        session=session,        # curl_cffi セッションを使用
        auto_adjust=False,      # Adj Close と Close を分離
    )

    # long形式に変換
    df = (
        df.stack(future_stack=True)
        .reset_index()
    )

    # さらに整形（melt）
    df = pd.melt(
        df,
        id_vars=["Date", "Ticker"],
        value_vars=["Open", "High", "Low", "Close", "Adj Close", "Volume"],
        var_name="variable",
        value_name="value",
    )

    return df
```

### イントラデイ vs 日次の処理分岐

```python
def yf_download(
    tickers: list[str],
    period: str = "2y",
    interval: str = "1d",
) -> pd.DataFrame:
    intra_day_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

    if interval in intra_day_intervals:
        # イントラデイ: sessionを渡さない、Datetime列を使用
        df = yf.download(
            tickers=tickers,
            period=period,
            interval=interval,
            prepost=False,
            group_by="ticker",
        )
        datetime_col = "Datetime"
    else:
        # 日次以上: sessionを使用、Date列を使用
        session = curl_cffi.Session(impersonate="safari15_5")
        df = yf.download(
            tickers=tickers,
            period=period,
            interval=interval,
            session=session,
            auto_adjust=False,
        )
        datetime_col = "Date"

    return df
```

---

## 3. yfinance クラスの使い分け

| クラス | 用途 | session | 主要属性/メソッド |
|--------|------|---------|-------------------|
| `yf.Ticker` | 個別銘柄データ | 推奨 | `.info`, `.history()`, `.get_news()`, `.earnings_history`, `.get_earnings_dates()` |
| `yf.Sector` | セクター情報 | 推奨 | `.top_companies` |
| `yf.Search` | ニュース検索 | 不要 | `.news` |
| `yf.download()` | 価格データ一括取得 | 推奨（日次以上） | - |

### 使用例

```python
# 個別銘柄のデータ取得
ticker = yf.Ticker("AAPL", session=session)
info = ticker.info
news = ticker.get_news(count=15)
earnings = ticker.earnings_history

# セクター情報
sector = yf.Sector("technology", session=session)
top_companies = sector.top_companies

# ニュース検索
search = yf.Search("US Market", news_count=15)
news_list = search.news
```

---

## 4. パフォーマンス計算パターン

### 複数期間のリターン一括計算

```python
def get_performance(tickers: list[str]) -> pd.DataFrame:
    # 価格データ取得
    price = download_and_pivot(tickers)  # Date x Ticker のピボットテーブル

    # 複数期間のリターンを一度に計算
    periods = {
        "1d": 1,
        "5d": 5,
        "1m": 21,
        "3m": 63,
        "6m": 126,
        "1y": 252,
    }

    df_performance = pd.DataFrame({
        name: price.pct_change(periods=p).iloc[-1]
        for name, p in periods.items()
    })

    return df_performance.sort_values("5d", ascending=False)
```

### 累積リターン計算

```python
import numpy as np

# 対数リターン → 累積リターン
log_return = np.log(price / price.shift(1))
cum_return = np.exp(log_return.cumsum()).fillna(1)
```

---

## 5. 並列処理パターン

### ThreadPoolExecutor による並列化

[注意!]レートリミット制限に注意

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

def process_all_sectors(sectors: list[str]) -> pd.DataFrame:
    results = []

    def process_sector(sector: str) -> pd.DataFrame:
        """セクターごとの処理"""
        logger.info(f"Sector: {sector} - 処理開始")
        data = fetch_sector_data(sector)
        logger.info(f"Sector: {sector} - 完了 ({len(data)}件)")
        return data

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(process_sector, sector): sector
            for sector in sectors
        }

        for future in as_completed(futures):
            sector = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Sector: {sector} - エラー: {e}")

    return pd.concat(results, ignore_index=True)
```

---

## 6. エラーハンドリング

### 推奨パターン

```python
import logging

logger = logging.getLogger(__name__)

def get_multiple_data(symbol_list: list[str]) -> pd.DataFrame:
    results = []
    session = curl_cffi.requests.Session(impersonate="safari15_5")

    for symbol in symbol_list:
        try:
            ticker = yf.Ticker(symbol, session=session)
            data = ticker.earnings_history

            # None チェック
            if data is None:
                logger.warning(f"{symbol}: データがNoneです")
                continue

            # 空チェック
            if data.empty:
                logger.info(f"{symbol}: データが空です")
                continue

            results.append(data.assign(symbol=symbol))

        except AttributeError as e:
            # メソッドが存在しない、属性エラー
            logger.error(f"{symbol}: 属性エラー - {e}")
            continue

        except KeyError as e:
            # カラムが存在しない
            logger.debug(f"{symbol}: カラムエラー - {e}")
            continue

        except Exception as e:
            # その他の予期しないエラー
            logger.error(f"{symbol}: 予期しないエラー - {type(e).__name__}: {e}")
            continue

    if not results:
        logger.warning("全銘柄でデータ取得に失敗しました")
        return pd.DataFrame()

    return pd.concat(results, ignore_index=True)
```

---

## 7. タイムゾーン処理

### 米国市場時間の考慮

```python
import pandas as pd

# 米国東部時間での現在時刻
now_et = pd.Timestamp.now(tz="America/New_York")

# 日付範囲のフィルタリング
future_date = now_et + pd.Timedelta(days=7)

df_filtered = df.loc[
    (df["Earnings Date"] >= now_et) &
    (df["Earnings Date"] <= future_date)
]
```

---

## 8. ニュース取得パターン

### Search クラス vs Ticker クラス

```python
class NewsFetcher:
    def __init__(self):
        self.session = curl_cffi.requests.Session(impersonate="safari15_5")

    def get_news_by_search(self, query: str, count: int = 15) -> list[dict]:
        """検索ベースのニュース取得（幅広いトピック向け）"""
        search = yf.Search(query, news_count=count)
        return [
            {
                "title": n.get("title"),
                "publisher": n.get("publisher"),
                "providerPublishTime": n.get("providerPublishTime"),
                "link": n.get("link"),
            }
            for n in search.news
        ]

    def get_news_by_ticker(self, ticker: str, count: int = 15) -> list[dict]:
        """個別銘柄のニュース取得（銘柄固有のニュース向け）"""
        t = yf.Ticker(ticker, session=self.session)
        news_list = t.get_news(count=count)
        return [
            {
                "title": n["content"].get("title"),
                "summary": n["content"].get("summary"),
                "pubDate": n["content"].get("pubDate"),
                "link": n["content"].get("canonicalUrl", {}).get("url"),
            }
            for n in news_list
        ]
```

---

## チェックリスト

yfinance 実装時に確認:

- [ ] `curl_cffi.requests.Session(impersonate="safari15_5")` を使用しているか
- [ ] セッションをクラスレベルで共有しているか
- [ ] イントラデイ/日次の処理を分岐しているか
- [ ] None/空チェックを実装しているか
- [ ] 例外種類別のログ出力をしているか
- [ ] 米国市場時間（America/New_York）を考慮しているか
- [ ] 複数銘柄は `yf.download()` で一括取得しているか
- [ ] 並列処理が必要な場合は `ThreadPoolExecutor` を使用しているか

---

## 関連ファイル

- `src/market_analysis/dev/data_fetch.py`: 基本的なデータ取得クラス
- `src/market_analysis/dev/analysis.py`: 分析クラス（Sector, MAG7）
- `src/market_analysis/dev/earnings.py`: 決算情報取得（並列処理あり）
- `src/market_analysis/dev/news.py`: ニュース取得クラス
- `src/market_analysis/dev/market_report_utils.py`: 総合的なユーティリティ
