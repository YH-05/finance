# analyze パッケージ

金融データ分析のための Python パッケージ。

## インストール

```bash
uv sync
```

## モジュール

### technical - テクニカル分析

テクニカル指標の計算機能を提供します。

#### 使用方法

```python
import pandas as pd
from analyze.technical.indicators import TechnicalIndicators

# サンプル価格データ
prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0])

# 単純移動平均 (SMA)
sma = TechnicalIndicators.calculate_sma(prices, window=3)

# 指数移動平均 (EMA)
ema = TechnicalIndicators.calculate_ema(prices, window=3)

# RSI (Relative Strength Index)
rsi = TechnicalIndicators.calculate_rsi(prices, period=5)

# MACD
macd = TechnicalIndicators.calculate_macd(
    prices,
    fast_period=3,
    slow_period=5,
    signal_period=2
)
print(macd["macd"])
print(macd["signal"])
print(macd["histogram"])

# ボリンジャーバンド
bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=5, num_std=2.0)
print(bands["upper"])
print(bands["middle"])
print(bands["lower"])

# リターン計算
returns = TechnicalIndicators.calculate_returns(prices)

# ボラティリティ
vol = TechnicalIndicators.calculate_volatility(returns, window=3)

# 全指標一括計算
all_indicators = TechnicalIndicators.calculate_all(prices)
```

#### 提供する指標

| メソッド | 説明 |
|----------|------|
| `calculate_sma` | 単純移動平均 (Simple Moving Average) |
| `calculate_ema` | 指数移動平均 (Exponential Moving Average) |
| `calculate_rsi` | 相対力指数 (Relative Strength Index) |
| `calculate_macd` | MACD (Moving Average Convergence Divergence) |
| `calculate_bollinger_bands` | ボリンジャーバンド |
| `calculate_returns` | リターン計算（単純/対数） |
| `calculate_volatility` | ボラティリティ（標準偏差） |
| `calculate_all` | 複数指標の一括計算 |

## ディレクトリ構造

```
src/analyze/
├── __init__.py
├── py.typed
├── README.md
└── technical/
    ├── __init__.py
    ├── indicators.py   # TechnicalIndicators クラス
    └── types.py        # 型定義
```

## テスト

```bash
# analyze パッケージのテスト実行
uv run pytest tests/analyze/ -v

# カバレッジ付き
uv run pytest tests/analyze/ -v --cov=analyze --cov-report=term-missing
```

## 型定義

`analyze.technical.types` モジュールで型定義を提供：

- `PriceSeries`, `ReturnSeries`, `IndicatorSeries` - 型エイリアス
- `SMAParams`, `EMAParams`, `RSIParams`, `MACDParams` - パラメータ型
- `BollingerBandsResult`, `MACDResult` - 結果型

## 関連

- 移植元: `market_analysis.analysis.indicators`
- GitHub Issue: #953
