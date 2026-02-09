# analyze.statistics

統計分析モジュール。

## 概要

金融データの統計分析機能を提供します。記述統計、相関分析、ベータ値計算、ローリング分析に対応。`StatisticalAnalyzer` 抽象基底クラスによる拡張可能な設計で、ローリング相関・ローリングベータ・カルマンフィルタベータの具象実装を提供。

**機能一覧:**

| カテゴリ | 機能 | 主要関数/クラス |
|---------|------|----------------|
| 記述統計 | 平均、中央値、標準偏差、分散、歪度、尖度 | `describe()`, `calculate_mean()` 等 |
| 相関分析 | Pearson/Spearman/Kendall 相関、相関行列 | `calculate_correlation()`, `CorrelationAnalyzer` |
| ベータ分析 | ベータ係数（市場感応度） | `calculate_beta()` |
| ローリング | ローリング相関、ローリングベータ | `RollingCorrelationAnalyzer`, `RollingBetaAnalyzer` |
| カルマン | 時変ベータ推定（カルマンフィルタ） | `KalmanBetaAnalyzer` |

## クイックスタート

### 記述統計

```python
import pandas as pd
from analyze.statistics.descriptive import describe, calculate_mean, calculate_skewness

series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])

# 一括取得（Pydantic モデル）
stats = describe(series)
print(f"mean={stats.mean}, std={stats.std}, skewness={stats.skewness}")

# 個別関数
mean = calculate_mean(series)
skew = calculate_skewness(series)
```

### 相関分析

```python
from analyze.statistics.correlation import (
    calculate_correlation,
    calculate_correlation_matrix,
    CorrelationAnalyzer,
)

# ペアワイズ相関
corr = calculate_correlation(series_a, series_b, method="pearson")

# 相関行列
df = pd.DataFrame({"AAPL": [...], "MSFT": [...], "GOOGL": [...]})
matrix = calculate_correlation_matrix(df, method="spearman")

# CorrelationAnalyzer（構造化結果）
analyzer = CorrelationAnalyzer()
result = analyzer.analyze(df, period="1Y")
print(result.symbols)             # ['AAPL', 'MSFT', 'GOOGL']
print(result.correlation_matrix)  # pd.DataFrame
```

### ベータ値計算

```python
from analyze.statistics.correlation import calculate_beta, calculate_rolling_beta

# 静的ベータ
beta = calculate_beta(stock_returns, market_returns)

# ローリングベータ
rolling_beta = calculate_rolling_beta(stock_returns, market_returns, window=60)
```

### カルマンフィルタベータ

```python
from analyze.statistics.beta import KalmanBetaAnalyzer

analyzer = KalmanBetaAnalyzer(transition_covariance=0.001, em_iterations=10)
result = analyzer.analyze(df, target_column="SPY")
```

## API リファレンス

### 記述統計関数（descriptive.py）

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `describe(series)` | 包括的記述統計（Pydantic モデル） | `DescriptiveStats` |
| `calculate_mean(series)` | 算術平均 | `float` |
| `calculate_median(series)` | 中央値 | `float` |
| `calculate_std(series, ddof=1)` | 標準偏差 | `float` |
| `calculate_var(series, ddof=1)` | 分散 | `float` |
| `calculate_skewness(series)` | 歪度 | `float` |
| `calculate_kurtosis(series)` | 超過尖度 | `float` |
| `calculate_quantile(series, q)` | 分位点 | `float` |
| `calculate_percentile_rank(series, value)` | パーセンタイルランク（0-100） | `float` |

### 相関・ベータ関数（correlation.py）

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `calculate_correlation(a, b, method)` | ペアワイズ相関係数 | `float` |
| `calculate_correlation_matrix(data, method)` | 相関行列 | `pd.DataFrame` |
| `calculate_rolling_correlation(a, b, window)` | ローリング相関 | `pd.Series` |
| `calculate_beta(returns, benchmark)` | ベータ係数 | `float` |
| `calculate_rolling_beta(returns, benchmark, window)` | ローリングベータ | `pd.Series` |

### クラス

| クラス | 親クラス | 説明 |
|--------|---------|------|
| `StatisticalAnalyzer` | ABC | 統計分析の抽象基底クラス（`validate_input()` → `calculate()` のテンプレートメソッド） |
| `CorrelationAnalyzer` | — | 相関分析（`analyze()` で `CorrelationResult` を返却） |
| `RollingCorrelationAnalyzer` | `StatisticalAnalyzer` | ローリング相関（window=252, min_periods=30） |
| `RollingBetaAnalyzer` | `StatisticalAnalyzer` | ローリングベータ（window=60, freq="W"/"M"） |
| `KalmanBetaAnalyzer` | `StatisticalAnalyzer` | カルマンフィルタベータ（`pykalman` 依存） |

### 型定義

| 型 | 説明 |
|----|------|
| `DescriptiveStats` | Pydantic モデル（count, mean, median, std, var, min, max, q25, q50, q75, skewness, kurtosis） |
| `CorrelationResult` | Pydantic モデル（symbols, correlation_matrix, period, method） |
| `CorrelationMethod` | `Literal["pearson", "spearman", "kendall"]` |

## モジュール構成

```
analyze/statistics/
├── __init__.py      # パッケージエクスポート（StatisticalAnalyzer）
├── base.py          # StatisticalAnalyzer ABC（validate → calculate テンプレート）
├── types.py         # Pydantic モデル（DescriptiveStats, CorrelationResult）
├── descriptive.py   # 記述統計関数（9関数）
├── correlation.py   # 相関・ベータ関数 + CorrelationAnalyzer + RollingCorrelationAnalyzer
├── beta.py          # RollingBetaAnalyzer, KalmanBetaAnalyzer
└── README.md        # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 | 必須 |
|-----------|------|------|
| pandas | データ操作 | 必須 |
| numpy | 数値計算 | 必須 |
| pydantic | 結果モデルのバリデーション | 必須 |
| scipy | 初期ベータ推定（`linregress`） | KalmanBetaAnalyzer で使用 |
| pykalman | カルマンフィルタ | KalmanBetaAnalyzer のみ（オプション） |

## 関連モジュール

- [analyze.technical](../technical/README.md) - テクニカル指標計算
- [analyze.visualization](../visualization/README.md) - 相関・ベータの可視化
- [analyze.integration](../integration/README.md) - データ取得→統計分析の統合
