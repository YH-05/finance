# analyze.returns

複数期間リターン計算モジュール。

## 概要

金融データの複数期間リターンを一括計算する機能を提供します。固定期間（1D, 1W, 1M 等）に加え、動的期間（MTD: 月初来、YTD: 年初来）にも対応。定義済みティッカーリスト（米国指数、海外指数、MAG7、セクター ETF）を使用して即座にリターンレポートを生成できます。

**対応期間:**

| 期間 | 説明 | 値 |
|------|------|-----|
| 1D | 1 営業日 | 1 |
| WoW | 前週火曜終値比 | `"prev_tue"` |
| 1W | 1 週間（5 営業日） | 5 |
| MTD | 月初来 | `"mtd"` |
| 1M | 1 ヶ月（21 営業日） | 21 |
| 3M | 3 ヶ月（63 営業日） | 63 |
| 6M | 6 ヶ月（126 営業日） | 126 |
| YTD | 年初来 | `"ytd"` |
| 1Y | 1 年（252 営業日） | 252 |
| 3Y | 3 年（756 営業日） | 756 |
| 5Y | 5 年（1260 営業日） | 1260 |

## クイックスタート

### 単一期間のリターン

```python
from analyze.returns import calculate_return

# 固定期間（営業日数）
ret = calculate_return(prices, period=21)  # 1ヶ月

# 動的期間
mtd_ret = calculate_return(prices, period="mtd")
ytd_ret = calculate_return(prices, period="ytd")
```

### 複数期間の一括計算

```python
from analyze.returns import calculate_multi_period_returns, TICKERS_MAG7

returns = calculate_multi_period_returns(
    tickers=TICKERS_MAG7,
    periods=["1d", "1w", "1mo", "mtd", "ytd"],
)
# → pd.DataFrame（行: ティッカー、列: 期間）
```

### レポート生成

```python
from analyze.returns import generate_returns_report, TICKERS_US_INDICES, RETURN_PERIODS

report = generate_returns_report(
    tickers=TICKERS_US_INDICES,
    periods=RETURN_PERIODS,
)
# → dict[str, Any]（リターンデータ + メタ情報）
```

### TOPIX データ取得

```python
from analyze.returns import fetch_topix_data

topix = fetch_topix_data()
# → pd.DataFrame（日経 TOPIX の時系列データ）
```

## API リファレンス

### 関数

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `calculate_return(prices, period)` | 単一期間のリターン計算 | `float \| None` |
| `calculate_multi_period_returns(tickers, periods)` | 複数銘柄×複数期間の一括計算 | `pd.DataFrame` |
| `generate_returns_report(tickers, periods)` | リターンレポート生成 | `dict[str, Any]` |
| `fetch_topix_data()` | TOPIX データ取得 | `pd.DataFrame` |

### 定義済み定数

| 定数 | 説明 |
|------|------|
| `RETURN_PERIODS` | 標準リターン期間定義（`dict[str, int \| str]`） |
| `TICKERS_US_INDICES` | 米国主要指数（S&P 500, NASDAQ, DOW 等） |
| `TICKERS_GLOBAL_INDICES` | 海外主要指数 |
| `TICKERS_MAG7` | Magnificent 7（AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA） |
| `TICKERS_SECTORS` | セクター ETF |

## モジュール構成

```
analyze/returns/
├── __init__.py       # パッケージエクスポート（4関数 + 5定数）
├── returns.py        # リターン計算関数（MTD/YTD の内部ヘルパー含む）
├── returns_proto.py  # リターン計算プロトタイプ
└── README.md         # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| pandas | データ操作、時系列処理 |
| yfinance | 価格データ取得 |

## 関連モジュール

- [analyze.config](../config/README.md) - シンボルグループ定義（`RETURN_PERIODS` 等の元データ）
- [analyze.sector](../sector/README.md) - セクターリターン分析
- [analyze.reporting](../reporting/README.md) - レポート生成（パフォーマンス分析）
