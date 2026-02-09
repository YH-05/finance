# analyze.visualization

金融チャート生成モジュール。

## 概要

Plotly を使用した金融データの可視化機能を提供します。ローソク足、ラインチャート、ヒートマップの基本チャートに加え、パフォーマンス、相関、ベータ、通貨、ボラティリティの特化チャートを提供。ダーク/ライトテーマ対応、日本語フォントサポート付き。

**チャート一覧:**

| カテゴリ | チャート | クラス/関数 |
|---------|---------|------------|
| 基本 | ローソク足（OHLCV） | `CandlestickChart` |
| 基本 | ラインチャート | `LineChart` |
| 基本 | ヒートマップ | `HeatmapChart` |
| 特化 | 累積リターン | `plot_cumulative_returns()` |
| 特化 | ローリング相関 | `plot_rolling_correlation()` |
| 特化 | ローリングベータ | `plot_rolling_beta()` |
| 特化 | ドルインデックス & 貴金属 | `plot_dollar_index_and_metals()` |
| 特化 | VIX & ハイイールドスプレッド | `plot_vix_and_high_yield_spread()` |
| 特化 | VIX & 不確実性指数 | `plot_vix_and_uncertainty_index()` |

## クイックスタート

### ローソク足チャート

```python
from analyze.visualization import CandlestickChart, PriceChartData

data = PriceChartData(df=ohlcv_df, symbol="AAPL")
chart = CandlestickChart(data)
chart.add_sma(20)
chart.add_ema(50)
chart.add_volume()
fig = chart.build()
fig.write_image("candlestick.png")
```

### ヒートマップ（相関行列）

```python
from analyze.visualization import HeatmapChart

heatmap = HeatmapChart(correlation_matrix)
fig = heatmap.build()
fig.write_image("heatmap.png")
```

### テーマ設定

```python
from analyze.visualization import ChartConfig, ChartTheme, ChartBuilder

config = ChartConfig(
    theme=ChartTheme.DARK,
    title="Price Chart",
    width=1200,
    height=600,
)
builder = ChartBuilder(config)
```

### 特化チャート

```python
from analyze.visualization import (
    plot_cumulative_returns,
    plot_rolling_correlation,
    plot_rolling_beta,
    plot_dollar_index_and_metals,
    plot_vix_and_high_yield_spread,
    apply_df_style,
)

# 累積リターン比較
fig = plot_cumulative_returns(price_df, ["AAPL", "MSFT"], "Performance")

# ローリング相関
fig = plot_rolling_correlation(df_corr, ticker="AAPL", target_index="S&P 500")

# ローリングベータ
fig = plot_rolling_beta(df_beta, tickers=["AAPL", "MSFT"], target_index="S&P 500")

# DataFrame スタイリング
styled = apply_df_style(returns_df)
```

## API リファレンス

### チャートクラス

| クラス | 説明 | 主要メソッド |
|--------|------|-------------|
| `ChartBuilder` | 基本チャートビルダー | `build()` → `go.Figure` |
| `CandlestickChart` | ローソク足チャート（出来高、MA オーバーレイ対応） | `add_sma()`, `add_ema()`, `add_volume()`, `build()` |
| `LineChart` | ラインチャート | `add_line()`, `build()` |
| `HeatmapChart` | ヒートマップ（相関行列等） | `build()` |
| `PriceChartBuilder` | 価格チャートベースクラス | — |

### 設定クラス

| クラス/Enum | フィールド | 説明 |
|------------|-----------|------|
| `ChartConfig` | theme, title, width, height, show_grid | チャート設定（dataclass） |
| `ChartTheme` | LIGHT, DARK | テーマ Enum |
| `ExportFormat` | PNG, JPEG, HTML, SVG | エクスポート形式 Enum |
| `ThemeColors` | background, text, positive, negative, neutral | テーマカラー（dataclass） |
| `PriceChartData` | df, symbol, start_date, end_date | 価格データコンテナ |
| `IndicatorOverlay` | — | インジケーターオーバーレイ設定（TypedDict） |

### 特化チャート関数

| 関数 | ファイル | 説明 |
|------|---------|------|
| `plot_cumulative_returns()` | performance.py | 累積リターン比較チャート |
| `apply_df_style()` | performance.py | DataFrame のスタイリング |
| `plot_rolling_correlation()` | correlation.py | ローリング相関チャート |
| `plot_rolling_beta()` | beta.py | ローリングベータチャート |
| `plot_dollar_index_and_metals()` | currency.py | ドルインデックス & 貴金属チャート |
| `plot_vix_and_high_yield_spread()` | volatility.py | VIX & ハイイールドスプレッドチャート |
| `plot_vix_and_uncertainty_index()` | volatility.py | VIX & 不確実性指数チャート |

### 定数

| 定数 | 説明 |
|------|------|
| `DARK_THEME_COLORS` | ダークテーマカラー定義 |
| `LIGHT_THEME_COLORS` | ライトテーマカラー定義 |
| `DEFAULT_WIDTH` | デフォルト幅（1200px） |
| `DEFAULT_HEIGHT` | デフォルト高さ（600px） |
| `JAPANESE_FONT_STACK` | 日本語フォントスタック |

### ユーティリティ

| 関数 | 説明 |
|------|------|
| `get_theme_colors(theme)` | テーマに対応する `ThemeColors` を取得 |

## モジュール構成

```
analyze/visualization/
├── __init__.py       # パッケージエクスポート（22エクスポート）
├── charts.py         # ChartBuilder, ChartConfig, テーマ定義
├── price_charts.py   # CandlestickChart, LineChart, PriceChartData
├── heatmap.py        # HeatmapChart
├── performance.py    # 累積リターンチャート、DataFrame スタイリング
├── correlation.py    # ローリング相関チャート
├── beta.py           # ローリングベータチャート
├── currency.py       # ドルインデックス & 貴金属チャート
├── volatility.py     # VIX 関連チャート
└── README.md         # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| plotly | チャート生成 |
| pandas | データ操作 |
| kaleido | 画像エクスポート（PNG, JPEG, SVG） |

## 関連モジュール

- [analyze.technical](../technical/README.md) - テクニカル指標（チャートオーバーレイ用）
- [analyze.statistics](../statistics/README.md) - 相関・ベータデータの生成
- [analyze.reporting](../reporting/README.md) - レポート用チャート生成
