# analyze.earnings

決算カレンダー・決算データモジュール。

## 概要

yfinance API を使用して、今後の決算発表日程と決算データ（EPS 予想、売上予想）を取得します。MAG7 およびセクター代表銘柄をデフォルト対象としつつ、任意の銘柄リストにも対応。JSON 形式での出力にも対応し、AI エージェントとの連携に最適化。

## クイックスタート

### 今後の決算取得

```python
from analyze.earnings import get_upcoming_earnings

# リスト形式（デフォルト）
earnings = get_upcoming_earnings(days_ahead=14)
for e in earnings:
    print(f"{e.ticker} ({e.name}): {e.earnings_date}")

# JSON 形式
json_data = get_upcoming_earnings(days_ahead=7, format="json")
```

### EarningsCalendar クラス

```python
from analyze.earnings import EarningsCalendar

calendar = EarningsCalendar()

# 今後14日間の決算
upcoming = calendar.get_upcoming_earnings(days_ahead=14)

# 個別銘柄の決算
nvda = calendar.get_earnings_for_symbol("NVDA")
if nvda:
    print(f"EPS予想: {nvda.eps_estimate}")
    print(f"売上予想: {nvda.revenue_estimate}")
```

### EarningsData の直接使用

```python
from datetime import datetime, timezone
from analyze.earnings import EarningsData

data = EarningsData(
    ticker="NVDA",
    name="NVIDIA Corporation",
    earnings_date=datetime(2026, 2, 26, tzinfo=timezone.utc),
    eps_estimate=0.85,
    revenue_estimate=38_000_000_000,
)
print(data.to_dict())
# → {'ticker': 'NVDA', 'name': 'NVIDIA Corporation',
#     'earnings_date': '2026-02-26', 'eps_estimate': 0.85, ...}
```

## API リファレンス

### 関数

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `get_upcoming_earnings(symbols=None, days_ahead=14, format="list")` | 今後の決算取得（便利関数） | `list[EarningsData] \| dict[str, Any]` |

### クラス

| クラス | 説明 |
|--------|------|
| `EarningsCalendar` | 決算カレンダー管理（デフォルト銘柄: MAG7 + セクター代表銘柄） |
| `EarningsData` | 決算データ（dataclass） |

### EarningsCalendar メソッド

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `get_upcoming_earnings(days_ahead=14)` | 今後の決算リスト | `list[EarningsData]` |
| `get_earnings_for_symbol(symbol, limit=100)` | 個別銘柄の決算データ | `EarningsData \| None` |

### EarningsData フィールド

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `ticker` | `str` | ティッカーシンボル |
| `name` | `str` | 企業名 |
| `earnings_date` | `datetime` | 決算発表日 |
| `eps_estimate` | `float \| None` | EPS 予想 |
| `revenue_estimate` | `float \| None` | 売上予想 |

## モジュール構成

```
analyze/earnings/
├── __init__.py   # パッケージエクスポート（2クラス + 1関数）
├── earnings.py   # EarningsCalendar クラス、get_upcoming_earnings 関数
├── types.py      # EarningsData dataclass
└── README.md     # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| yfinance | 決算データ取得 |

## 関連モジュール

- [analyze.reporting](../reporting/README.md) - 今後のイベントレポート（`UpcomingEvents4Agent`）
- [analyze.config](../config/README.md) - デフォルト銘柄リスト（MAG7、セクター代表銘柄）
