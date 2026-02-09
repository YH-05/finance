# analyze.technical

テクニカル分析モジュール。

## 概要

金融データのテクニカル指標を計算する静的メソッド群を提供します。移動平均（SMA, EMA）、モメンタム指標（RSI, MACD）、ボラティリティ指標（ボリンジャーバンド）、リターン計算に対応。全メソッドは `TechnicalIndicators` クラスの静的メソッドとして提供されます。

**提供する指標:**

| カテゴリ | 指標 | メソッド |
|---------|------|---------|
| トレンド | 単純移動平均（SMA） | `calculate_sma()` |
| トレンド | 指数移動平均（EMA） | `calculate_ema()` |
| モメンタム | 相対力指数（RSI） | `calculate_rsi()` |
| モメンタム | MACD | `calculate_macd()` |
| ボラティリティ | ボリンジャーバンド | `calculate_bollinger_bands()` |
| ボラティリティ | ボラティリティ（標準偏差） | `calculate_volatility()` |
| リターン | 単純/対数リターン | `calculate_returns()` |
| 一括 | 全指標一括計算 | `calculate_all()` |

## クイックスタート

### 個別指標の計算

```python
import pandas as pd
from analyze.technical.indicators import TechnicalIndicators

prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0])

# 移動平均
sma = TechnicalIndicators.calculate_sma(prices, window=3)
ema = TechnicalIndicators.calculate_ema(prices, window=3)

# RSI
rsi = TechnicalIndicators.calculate_rsi(prices, period=5)

# MACD（デフォルト: 12/26/9）
macd = TechnicalIndicators.calculate_macd(prices)
print(macd["macd"], macd["signal"], macd["histogram"])

# ボリンジャーバンド（デフォルト: 20期間, 2σ）
bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=5, num_std=2.0)
print(bands["upper"], bands["middle"], bands["lower"])
```

### 全指標の一括計算

```python
all_indicators = TechnicalIndicators.calculate_all(prices)
# → {'sma_20': ..., 'ema_20': ..., 'rsi_14': ..., 'macd': ..., 'bollinger': ..., ...}
```

## API リファレンス

### TechnicalIndicators クラス

全メソッドは `@staticmethod` として提供。

| メソッド | パラメータ | 戻り値 |
|---------|-----------|--------|
| `calculate_sma(prices, window)` | window: int | `pd.Series` |
| `calculate_ema(prices, window, adjust=True)` | window: int, adjust: bool | `pd.Series` |
| `calculate_returns(prices, periods=1, log_returns=False)` | periods: int, log_returns: bool | `pd.Series` |
| `calculate_volatility(returns, window, annualize=True, annualization_factor=252)` | window: int 等 | `pd.Series` |
| `calculate_bollinger_bands(prices, window=20, num_std=2.0)` | window: int, num_std: float | `BollingerBandsResult` |
| `calculate_rsi(prices, period=14)` | period: int | `pd.Series` |
| `calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9)` | 各 int | `MACDResult` |
| `calculate_all(prices, ...)` | 各指標パラメータ | `dict[str, ...]` |

### 型定義（TypedDict）

**パラメータ型:**

| 型 | フィールド | 説明 |
|----|-----------|------|
| `SMAParams` | window: int | SMA パラメータ |
| `EMAParams` | window: int, adjust?: bool | EMA パラメータ |
| `RSIParams` | period: int | RSI パラメータ |
| `MACDParams` | fast_period?: int, slow_period?: int, signal_period?: int | MACD パラメータ |
| `BollingerBandsParams` | window?: int, num_std?: float | ボリンジャーバンドパラメータ |
| `VolatilityParams` | window?: int, annualize?: bool, annualization_factor?: int | ボラティリティパラメータ |
| `ReturnParams` | periods?: int, log_return?: bool | リターンパラメータ |

**結果型:**

| 型 | フィールド | 説明 |
|----|-----------|------|
| `BollingerBandsResult` | middle, upper, lower: pd.Series | ボリンジャーバンド結果 |
| `MACDResult` | macd, signal, histogram: pd.Series | MACD 結果 |

**型エイリアス（PEP 695）:**

| エイリアス | 元の型 | 説明 |
|-----------|--------|------|
| `PriceSeries` | `pd.Series` | 価格データ |
| `ReturnSeries` | `pd.Series` | リターンデータ |
| `IndicatorSeries` | `pd.Series` | 指標値データ |

## モジュール構成

```
analyze/technical/
├── __init__.py      # パッケージエクスポート（1クラス + 9型定義）
├── indicators.py    # TechnicalIndicators クラス（全静的メソッド）
├── types.py         # TypedDict パラメータ型・結果型・型エイリアス
└── README.md        # このファイル
```

## 関連モジュール

- [analyze.integration](../integration/README.md) - データ取得→テクニカル分析の統合
- [analyze.visualization](../visualization/README.md) - テクニカル指標のチャート描画
- [analyze.statistics](../statistics/README.md) - 統計分析（相関、ベータ）
