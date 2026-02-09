# analyze.integration

market パッケージとの統合モジュール。

## 概要

`market` パッケージ（データ取得）と `analyze` パッケージ（分析）を接続し、データ取得→テクニカル分析→統計分析を一括実行する統合モジュールです。`MarketDataAnalyzer` クラスと便利関数を提供。

**統合フロー:**

```
market.yfinance.YFinanceFetcher（データ取得）
    ↓
analyze.technical.TechnicalIndicators（テクニカル分析）
    ↓
analyze.statistics.descriptive（統計分析）
    ↓
統合結果（dict[str, dict[str, Any]]）
```

## クイックスタート

### MarketDataAnalyzer クラス

```python
from analyze.integration import MarketDataAnalyzer

analyzer = MarketDataAnalyzer()

# 複数銘柄のデータ取得→分析を一括実行
result = analyzer.fetch_and_analyze(
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

for symbol, data in result.items():
    print(f"{symbol}:")
    print(f"  テクニカル指標: {list(data['technical_indicators'].keys())}")
    print(f"  統計情報: {list(data['statistics'].keys())}")
```

### 便利関数

```python
from analyze.integration import analyze_market_data, fetch_and_analyze

# 既存の DataFrame を分析
analysis = analyze_market_data(price_df, symbol="AAPL")

# テクニカル指標を指定してデータ取得→分析
result = fetch_and_analyze(
    symbols=["AAPL"],
    indicators=["sma_20", "rsi_14", "macd"],
)
```

## API リファレンス

### MarketDataAnalyzer クラス

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `fetch_and_analyze(symbols, start_date, end_date, interval)` | データ取得→分析の一括実行 | `dict[str, dict[str, Any]]` |

**コンストラクタ:**

```python
MarketDataAnalyzer(fetcher: YFinanceFetcher | None = None)
```

**戻り値の構造:**

```python
{
    "AAPL": {
        "raw_data": pd.DataFrame,          # 生の価格データ
        "technical_indicators": dict,       # テクニカル指標
        "statistics": dict,                 # 記述統計
        "data_empty": bool,                 # データ有無フラグ
    },
    ...
}
```

### 関数

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `analyze_market_data(df, symbol)` | DataFrame の分析 | `dict[str, Any]` |
| `fetch_and_analyze(symbols, indicators, ...)` | データ取得→分析（便利関数） | `dict[str, dict[str, Any]]` |

## モジュール構成

```
analyze/integration/
├── __init__.py              # パッケージエクスポート（1クラス + 2関数）
├── market_integration.py    # MarketDataAnalyzer, analyze_market_data, fetch_and_analyze
└── README.md                # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| pandas | データ操作 |

## 依存パッケージ

| パッケージ | 用途 |
|-----------|------|
| `market.yfinance` | `YFinanceFetcher`（価格データ取得） |
| `analyze.technical` | `TechnicalIndicators`（テクニカル分析） |
| `analyze.statistics` | 記述統計・相関分析 |

## 関連モジュール

- [market パッケージ](../../market/README.md) - データ取得元
- [analyze.technical](../technical/README.md) - テクニカル指標計算
- [analyze.statistics](../statistics/README.md) - 統計分析
