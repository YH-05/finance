# analyze - 金融データ分析パッケージ

金融データの包括的な分析機能を提供する Python パッケージ。

## 概要

analyze パッケージは以下の分析機能を提供します:

- **technical**: テクニカル分析（移動平均、RSI、MACD、ボリンジャーバンド）
- **statistics**: 統計分析（記述統計、相関分析、ベータ計算）
- **sector**: セクター分析（ETF リターン、セクターランキング）
- **earnings**: 決算分析（決算カレンダー、決算データ取得）
- **returns**: リターン計算（複数期間リターン、MTD、YTD）
- **visualization**: 可視化（チャート、ヒートマップ、ローソク足）
- **integration**: market パッケージとの統合

## インストール

```bash
uv sync --all-extras
```

## クイックスタート

```python
import pandas as pd
from analyze.technical.indicators import TechnicalIndicators

# サンプル価格データ
prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0])

# 移動平均を計算
sma = TechnicalIndicators.calculate_sma(prices, window=3)
ema = TechnicalIndicators.calculate_ema(prices, window=3)

# RSI を計算
rsi = TechnicalIndicators.calculate_rsi(prices, period=5)

# 全指標を一括計算
all_indicators = TechnicalIndicators.calculate_all(prices)
```

## サブモジュール

| モジュール | 説明 | ステータス |
|-----------|------|-----------|
| `analyze.technical` | テクニカル分析（移動平均、RSI、MACD） | 実装済み |
| `analyze.statistics` | 統計分析（記述統計、相関分析） | 実装済み |
| `analyze.sector` | セクター分析（ETF パフォーマンス） | 実装済み |
| `analyze.earnings` | 決算カレンダー・決算データ | 実装済み |
| `analyze.returns` | 複数期間リターン計算 | 実装済み |
| `analyze.visualization` | チャート・グラフ生成 | 実装済み |
| `analyze.integration` | market パッケージとの統合 | 実装済み |

---

## technical モジュール

テクニカル指標の計算機能を提供します。

### 使用方法

```python
import pandas as pd
from analyze.technical.indicators import TechnicalIndicators

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

### 提供する指標

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

### 型定義

```python
from analyze.technical import (
    SMAParams,
    EMAParams,
    RSIParams,
    MACDParams,
    MACDResult,
    BollingerBandsParams,
    BollingerBandsResult,
    ReturnParams,
    VolatilityParams,
)
```

---

## statistics モジュール

統計分析機能を提供します。

### 記述統計

```python
import pandas as pd
from analyze.statistics import (
    describe,
    calculate_mean,
    calculate_median,
    calculate_std,
    calculate_var,
    calculate_skewness,
    calculate_kurtosis,
    calculate_quantile,
    calculate_percentile_rank,
)

series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])

# 記述統計を一括取得
stats = describe(series)
print(stats.count)   # 5
print(stats.mean)    # 3.0
print(stats.std)     # 標準偏差

# 個別の統計量
mean = calculate_mean(series)      # 3.0
median = calculate_median(series)  # 3.0
std = calculate_std(series)
skew = calculate_skewness(series)
kurt = calculate_kurtosis(series)
```

### 相関分析

```python
import pandas as pd
from analyze.statistics import (
    CorrelationAnalyzer,
    calculate_correlation,
    calculate_correlation_matrix,
    calculate_beta,
    calculate_rolling_correlation,
    calculate_rolling_beta,
    CorrelationMethod,
)

# 相関係数
corr = calculate_correlation(series_a, series_b)

# 相関行列
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
corr_matrix = calculate_correlation_matrix(df)

# ベータ値（市場感応度）
beta = calculate_beta(stock_returns, market_returns)

# ローリング相関
rolling_corr = calculate_rolling_correlation(series_a, series_b, window=20)

# CorrelationAnalyzer クラス
analyzer = CorrelationAnalyzer(df)
result = analyzer.analyze(method=CorrelationMethod.PEARSON)
```

### 型定義

```python
from analyze.statistics import (
    DescriptiveStats,     # 記述統計の結果
    CorrelationResult,    # 相関分析の結果
    CorrelationMethod,    # 相関計算手法（PEARSON, SPEARMAN, KENDALL）
)
```

---

## sector モジュール

セクター分析機能を提供します。

### セクター ETF パフォーマンス

```python
from analyze.sector import (
    analyze_sector_performance,
    fetch_sector_etf_returns,
    get_top_bottom_sectors,
    SECTOR_ETF_MAP,
    SECTOR_KEYS,
    SECTOR_NAMES,
)

# セクター ETF のリターンを取得
returns = fetch_sector_etf_returns(period="1mo")

# セクターパフォーマンスを分析
result = analyze_sector_performance(period="1mo", top_n=3)

# 上位/下位セクターを取得
top, bottom = get_top_bottom_sectors(returns, n=3)

# セクター ETF マッピング
print(SECTOR_ETF_MAP)  # {"XLK": "Technology", "XLF": "Financial", ...}
```

### 型定義

```python
from analyze.sector import (
    SectorInfo,           # セクター情報
    SectorContributor,    # セクター貢献銘柄
    SectorAnalysisResult, # 分析結果
)
```

---

## earnings モジュール

決算カレンダーと決算データを提供します。

### 決算カレンダー

```python
from datetime import datetime, timezone
from analyze.earnings import (
    EarningsCalendar,
    EarningsData,
    get_upcoming_earnings,
)

# 決算カレンダーを取得
calendar = EarningsCalendar()
results = calendar.get_upcoming_earnings(days_ahead=14)

# 便利関数
json_data = get_upcoming_earnings(days_ahead=7, format="json")

# EarningsData を直接使用
data = EarningsData(
    ticker="NVDA",
    name="NVIDIA Corporation",
    earnings_date=datetime(2026, 1, 28, tzinfo=timezone.utc),
    eps_estimate=0.85,
)
print(data.to_dict())
```

---

## returns モジュール

複数期間のリターン計算を提供します。

### リターン計算

```python
from analyze.returns import (
    calculate_return,
    calculate_multi_period_returns,
    generate_returns_report,
    fetch_topix_data,
    RETURN_PERIODS,
    TICKERS_US_INDICES,
    TICKERS_GLOBAL_INDICES,
    TICKERS_MAG7,
    TICKERS_SECTORS,
)

# 単一期間のリターン
ret = calculate_return(prices, period="1mo")

# 複数期間のリターンを一括計算
returns = calculate_multi_period_returns(
    tickers=["AAPL", "MSFT", "GOOGL"],
    periods=["1d", "1w", "1mo", "mtd", "ytd"],
)

# レポート生成
report = generate_returns_report(
    tickers=TICKERS_MAG7,
    periods=RETURN_PERIODS,
)

# TOPIX データ取得（日本株指数）
topix_data = fetch_topix_data()
```

### 定義済みティッカーリスト

```python
from analyze.returns import (
    TICKERS_US_INDICES,     # S&P 500, NASDAQ, DOW 等
    TICKERS_GLOBAL_INDICES, # 世界の主要指数
    TICKERS_MAG7,           # Magnificent 7 (AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA)
    TICKERS_SECTORS,        # セクター ETF
    RETURN_PERIODS,         # 標準期間リスト
)
```

---

## visualization モジュール

金融チャートの生成機能を提供します。

### チャートビルダー

```python
from analyze.visualization import (
    ChartBuilder,
    ChartConfig,
    ChartTheme,
    ExportFormat,
    get_theme_colors,
)

# チャート設定
config = ChartConfig(
    theme=ChartTheme.DARK,
    title="Price Chart",
    width=1200,
    height=600,
)

# チャートビルダー
builder = ChartBuilder(config)
```

### ローソク足チャート

```python
from analyze.visualization import (
    CandlestickChart,
    LineChart,
    PriceChartData,
    PriceChartBuilder,
    IndicatorOverlay,
)

# 価格データを準備
data = PriceChartData(df=ohlcv_df, symbol="AAPL")

# ローソク足チャートを作成
chart = CandlestickChart(data)
chart.add_sma(20)
chart.add_ema(50)
chart.add_volume()
fig = chart.build()
fig.write_image("candlestick.png")

# ラインチャート
line_chart = LineChart(data)
fig = line_chart.build()
```

### ヒートマップ

```python
from analyze.visualization import HeatmapChart

# 相関行列のヒートマップ
heatmap = HeatmapChart(correlation_matrix)
fig = heatmap.build()
fig.write_image("heatmap.png")
```

### テーマカラー

```python
from analyze.visualization import (
    ChartTheme,
    DARK_THEME_COLORS,
    LIGHT_THEME_COLORS,
    JAPANESE_FONT_STACK,
)

# テーマカラーを取得
colors = get_theme_colors(ChartTheme.DARK)
print(colors.background)
print(colors.text)
print(colors.positive)  # 上昇色
print(colors.negative)  # 下落色
```

---

## integration モジュール

market パッケージとの統合機能を提供します。

### MarketDataAnalyzer

```python
from analyze.integration import (
    MarketDataAnalyzer,
    analyze_market_data,
    fetch_and_analyze,
)

# MarketDataAnalyzer クラス
analyzer = MarketDataAnalyzer()
result = analyzer.fetch_and_analyze(
    symbols=["AAPL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# 便利関数: データ取得と分析を一括実行
result = fetch_and_analyze(
    symbols=["AAPL"],
    indicators=["sma_20", "rsi_14", "macd"],
)

# 既存の DataFrame を分析
df = ...  # 価格データ
analysis = analyze_market_data(df)
```

---

## 公開 API（トップレベル）

```python
from analyze import (
    # technical モジュール
    SMAParams, EMAParams, RSIParams, MACDParams, MACDResult,
    BollingerBandsParams, BollingerBandsResult, ReturnParams, VolatilityParams,

    # statistics モジュール
    DescriptiveStats, CorrelationResult, CorrelationMethod,

    # earnings モジュール
    EarningsCalendar, EarningsData, get_upcoming_earnings,

    # returns モジュール
    calculate_return, calculate_multi_period_returns, generate_returns_report,
    fetch_topix_data,
    RETURN_PERIODS, TICKERS_US_INDICES, TICKERS_GLOBAL_INDICES,
    TICKERS_MAG7, TICKERS_SECTORS,

    # integration モジュール
    MarketDataAnalyzer, analyze_market_data, fetch_and_analyze,

    # sector モジュール
    sector,
)
```

---

## ディレクトリ構造

```
src/analyze/
├── __init__.py           # 公開 API
├── py.typed
├── README.md
├── technical/            # テクニカル分析
│   ├── __init__.py
│   ├── indicators.py     # TechnicalIndicators クラス
│   └── types.py          # パラメータ・結果の型定義
├── statistics/           # 統計分析
│   ├── __init__.py
│   ├── descriptive.py    # 記述統計関数
│   ├── correlation.py    # 相関分析関数
│   └── types.py          # 型定義
├── sector/               # セクター分析
│   ├── __init__.py
│   └── sector.py         # セクター分析関数
├── earnings/             # 決算分析
│   ├── __init__.py
│   ├── earnings.py       # EarningsCalendar クラス
│   └── types.py          # EarningsData 型定義
├── returns/              # リターン計算
│   ├── __init__.py
│   └── returns.py        # リターン計算関数
├── visualization/        # 可視化
│   ├── __init__.py
│   ├── charts.py         # ChartBuilder, ChartConfig
│   ├── heatmap.py        # HeatmapChart
│   └── price_charts.py   # CandlestickChart, LineChart
└── integration/          # market パッケージ統合
    ├── __init__.py
    └── market_integration.py  # MarketDataAnalyzer
```

---

## 開発

### テスト実行

```bash
# analyze パッケージのテスト実行
uv run pytest tests/analyze/ -v

# カバレッジ付き
uv run pytest tests/analyze/ -v --cov=analyze --cov-report=term-missing
```

### 品質チェック

```bash
# フォーマット
uv run ruff format src/analyze/ tests/analyze/

# リント
uv run ruff check src/analyze/ tests/analyze/

# 型チェック
uv run pyright src/analyze/ tests/analyze/
```

---

## 関連

- 移植元: `market_analysis.analysis.indicators`
- GitHub Issue: #953
- [market パッケージ](../market/README.md)
- [database パッケージ](../database/README.md)

## ライセンス

MIT License
