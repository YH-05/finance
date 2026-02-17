---
summary: "yfinance開発のベストプラクティス - curl_cffiセッション管理、複数銘柄一括取得、クラス使い分け、エラーハンドリング、並列処理パターン"
created: 2026-01-21
tags: [yfinance, curl_cffi, performance, best-practices]
related: [src/market_analysis/dev/, docs/guidelines/yfinance-best-practices.md]
---

# yfinance 開発ベストプラクティス

> **ソース**: `src/market_analysis/dev/` の開発コードから抽出
> **詳細ドキュメント**: `docs/guidelines/yfinance-best-practices.md`

## 1. curl_cffi によるセッション管理

```python
import curl_cffi
import yfinance as yf

class YfinanceFetcher:
    def __init__(self):
        # クラスレベルでセッションを共有（リソース効率化）
        self.session = curl_cffi.requests.Session(impersonate="safari15_5")

    def get_data(self, symbol: str):
        ticker = yf.Ticker(symbol, session=self.session)
        return ticker.info
```

**ポイント**:
- `impersonate="safari15_5"` でブラウザ偽装
- rate limiting / 403エラー対策
- セッションはメソッドごとに新規作成しない

## 2. 複数銘柄の一括取得

```python
df = yf.download(
    tickers=["AAPL", "MSFT", "GOOGL"],
    period="2y",
    session=session,
    auto_adjust=False,
)

# long形式に変換
df = df.stack(future_stack=True).reset_index()
df = pd.melt(df, id_vars=["Date", "Ticker"], ...)
```

## 3. yfinance クラス使い分け

| クラス | 用途 | session |
|--------|------|---------|
| `yf.Ticker` | 個別銘柄データ | 推奨 |
| `yf.Sector` | セクター情報 | 推奨 |
| `yf.Search` | ニュース検索 | 不要 |
| `yf.download()` | 価格一括取得 | 推奨（日次以上） |

## 4. イントラデイ vs 日次

```python
intra_day_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

if interval in intra_day_intervals:
    # イントラデイ: sessionを渡さない、Datetime列
    df = yf.download(tickers, period, interval, group_by="ticker")
else:
    # 日次以上: session使用、Date列
    df = yf.download(tickers, period, interval, session=session)
```

## 5. エラーハンドリング

```python
for symbol in symbols:
    try:
        data = yf.Ticker(symbol, session=session).info
        if data is None:  # None チェック必須
            logger.warning(f"{symbol}: データがNone")
            continue
    except AttributeError as e:
        logger.error(f"{symbol}: 属性エラー - {e}")
        continue
    except Exception as e:
        logger.error(f"{symbol}: {type(e).__name__}: {e}")
        continue
```

## 6. 並列処理

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=6) as executor:
    futures = {executor.submit(process, s): s for s in sectors}
    for future in as_completed(futures):
        result = future.result()
```

## 7. パフォーマンス計算

```python
# 複数期間のリターン一括計算
periods = {"1d": 1, "5d": 5, "1m": 21, "3m": 63, "6m": 126, "1y": 252}
df_perf = pd.DataFrame({
    name: price.pct_change(periods=p).iloc[-1]
    for name, p in periods.items()
})

# 累積リターン
log_return = np.log(price / price.shift(1))
cum_return = np.exp(log_return.cumsum()).fillna(1)
```

## 8. タイムゾーン

```python
# 米国市場時間を考慮
now_et = pd.Timestamp.now(tz="America/New_York")
```
