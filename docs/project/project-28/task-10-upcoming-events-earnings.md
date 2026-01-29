# Task 10: 決算発表日取得機能の実装

**Phase**: 3 - 来週の注目材料
**依存**: なし
**ファイル**: `src/analyze/reporting/upcoming_events.py`（部分）

## 概要

yfinance を使用してS&P500時価総額上位20社の次回決算発表日を取得する機能を実装する。

## 対象銘柄

```python
TOP20_SYMBOLS = [
    # MAG7
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    # Top 8-15
    "BRK-B", "LLY", "V", "UNH", "JPM", "XOM", "JNJ", "MA",
    # Top 16-20
    "PG", "HD", "AVGO", "CVX", "MRK",
]
```

## 実装仕様

### クラス設計（部分）

```python
class UpcomingEventsCollector:
    """来週の注目材料（決算・経済指標）を取得するクラス."""

    TOP20_SYMBOLS: ClassVar[list[str]] = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
        "BRK-B", "LLY", "V", "UNH", "JPM", "XOM", "JNJ", "MA",
        "PG", "HD", "AVGO", "CVX", "MRK",
    ]

    # シンボル名マッピング
    SYMBOL_NAMES: ClassVar[dict[str, str]] = {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Alphabet",
        # ...
    }

    def __init__(self) -> None: ...

    def get_upcoming_earnings(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """指定期間内の決算発表予定を取得.

        Parameters
        ----------
        start_date : date
            検索開始日
        end_date : date
            検索終了日

        Returns
        -------
        list[dict[str, Any]]
            決算発表予定のリスト
        """
        ...

    def _get_earnings_date(self, symbol: str) -> dict[str, Any] | None:
        """個別銘柄の次回決算日を取得.

        yfinance.Ticker.calendar を使用して取得。
        KeyError 等のエラー時は None を返す。
        """
        ...
```

### yfinance API 使用方法

```python
import yfinance as yf

ticker = yf.Ticker("AAPL")

# calendar プロパティから次回決算日を取得
calendar = ticker.calendar
# {
#     'Earnings Date': [Timestamp('2026-02-01'), Timestamp('2026-02-03')],
#     'Earnings Average': 2.35,
#     'Earnings Low': 2.20,
#     'Earnings High': 2.50,
#     'Revenue Average': 124500000000,
#     ...
# }

# または get_earnings_dates() を使用
earnings_dates = ticker.get_earnings_dates(limit=4)
```

### 出力形式

```python
[
    {
        "symbol": "AAPL",
        "name": "Apple",
        "date": "2026-02-01",
        "timing": "After Market Close",  # または "Before Market Open", "Unknown"
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft",
        "date": "2026-02-03",
        "timing": "After Market Close",
    },
]
```

## エラーハンドリング

- yfinance の KeyError バグ対策: try-except で個別処理
- 決算日が取得できない銘柄はスキップ
- ログに警告を出力

## 技術的注意点

[yfinance GitHub Issue #2143](https://github.com/ranaroussi/yfinance/issues/2143) によると、`earnings_dates` に KeyError が発生することがある。`ticker.calendar` を優先的に使用し、フォールバックとして `get_earnings_dates()` を試みる。

## 受け入れ条件

- [ ] 20銘柄の決算日を取得できる
- [ ] 指定期間でフィルタリングできる
- [ ] エラー時もクラッシュせず処理を継続
- [ ] 決算日がソートされている
- [ ] ロギングが実装されている
