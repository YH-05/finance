# analyze - 金融データ分析パッケージ

金融データの包括的な分析機能を提供する Python パッケージ。

## 概要

analyze パッケージは以下の分析機能を提供します:

- **reporting**: 包括的なマーケットレポート生成（週次レポート向けAIエージェント対応）
  - パフォーマンス分析（指数・個別銘柄・セクター）
  - 通貨分析（USD/JPY、EUR/USD 等）
  - 金利分析（10年債利回り、FF金利 等）
  - 経済イベント・決算カレンダー
  - 貴金属・米国債・VIX 分析
- **visualization**: 多様な金融チャート（ローソク足、ヒートマップ、相関、ボラティリティ等）
- **statistics**: 統計分析（記述統計、相関分析、ベータ計算、カルマンフィルタ）
- **technical**: テクニカル分析（移動平均、RSI、MACD、ボリンジャーバンド）
- **returns**: リターン計算（複数期間リターン、MTD、YTD）
- **sector**: セクター分析（ETF リターン、セクターランキング）
- **earnings**: 決算分析（決算カレンダー、決算データ取得）
- **integration**: market パッケージとの統合（データ取得→分析の一括実行）
- **config**: 設定管理（シンボルグループ、期間設定の読み込み）

## インストール

```bash
uv sync --all-extras
```

<!-- AUTO-GENERATED: QUICKSTART -->

## クイックスタート

### 基本的な使い方

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

### よくある使い方

#### 複数銘柄のリターン計算

```python
from analyze.returns import calculate_multi_period_returns, TICKERS_MAG7

# 複数期間のリターンを一括計算
returns = calculate_multi_period_returns(
    tickers=TICKERS_MAG7,  # Magnificent 7
    periods=["1d", "1w", "1mo", "ytd"],
)
```

#### セクター分析

```python
from analyze.sector import analyze_sector_performance

# セクターパフォーマンスを分析
result = analyze_sector_performance(period="1mo", top_n=5)
for sector in result.sectors:
    print(f"{sector.name}: {sector.return_1m:.2%}")
```

#### テクニカル指標とMA の組み合わせ

```python
from analyze.technical.indicators import TechnicalIndicators

prices = pd.Series([...])

# MACD とシグナルライン
macd = TechnicalIndicators.calculate_macd(prices)

# ボリンジャーバンド
bands = TechnicalIndicators.calculate_bollinger_bands(prices, window=20)
```

#### 週次マーケットレポート生成（AIエージェント向け）

```python
from analyze.reporting import (
    PerformanceAnalyzer4Agent,
    CurrencyAnalyzer4Agent,
    InterestRateAnalyzer4Agent,
    UpcomingEvents4Agent,
)

# パフォーマンス分析（指数、MAG7、セクター等）
perf_analyzer = PerformanceAnalyzer4Agent()
perf_result = perf_analyzer.analyze_cross_section(
    data=df,
    group="MAG7",
    periods=["1d", "1w", "1mo", "ytd"],
)

# 通貨分析（USD/JPY, EUR/USD等）
currency_analyzer = CurrencyAnalyzer4Agent()
currency_result = currency_analyzer.analyze()

# 金利分析（10年債利回り、FF金利等）
interest_analyzer = InterestRateAnalyzer4Agent()
interest_result = interest_analyzer.analyze()

# 今後の経済イベント・決算
events_analyzer = UpcomingEvents4Agent()
events_result = events_analyzer.analyze(days_ahead=14)
```

#### 可視化

```python
from analyze.visualization import CandlestickChart, HeatmapChart

# ローソク足チャート
chart = CandlestickChart(price_data)
chart.add_sma(20)
chart.add_volume()
fig = chart.build()
fig.write_image("chart.png")

# 相関ヒートマップ
heatmap = HeatmapChart(correlation_matrix)
fig = heatmap.build()
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->

## 実装状況

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|-----------|------|
| `reporting/` | ✅ 実装済み | 13 | 5,703 |
| `visualization/` | ✅ 実装済み | 9 | 3,428 |
| `statistics/` | ✅ 実装済み | 6 | 2,603 |
| `technical/` | ✅ 実装済み | 3 | 1,137 |
| `config/` | ✅ 実装済み | 3 | 1,047 |
| `returns/` | ✅ 実装済み | 3 | 788 |
| `sector/` | ✅ 実装済み | 2 | 731 |
| `earnings/` | ✅ 実装済み | 3 | 553 |
| `integration/` | ✅ 実装済み | 2 | 395 |

<!-- END: IMPLEMENTATION -->

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

### ベータ値計算

```python
from analyze.statistics import beta

# ベータ値を計算（市場感応度）
beta_value = beta.calculate_beta(stock_returns, market_returns)

# ローリングベータ
rolling_beta = beta.calculate_rolling_beta(stock_returns, market_returns, window=60)
```

### 統計分析ベースクラス

```python
from analyze.statistics import StatisticalAnalyzer

# カスタム統計分析クラスを作成
class MyAnalyzer(StatisticalAnalyzer):
    def calculate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        # 分析ロジックを実装
        return df.describe()

    def validate_input(self, df: pd.DataFrame) -> bool:
        # 入力検証
        return not df.empty
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

### 特化チャート

```python
from analyze.visualization import beta, correlation, currency, performance, volatility

# ベータ値チャート
beta_chart = beta.create_chart(beta_data)

# 相関チャート
corr_chart = correlation.create_chart(correlation_data)

# 通貨チャート
currency_chart = currency.create_chart(currency_data)

# パフォーマンスチャート
perf_chart = performance.create_chart(performance_data)

# ボラティリティチャート
vol_chart = volatility.create_chart(volatility_data)
```

---

## config モジュール

設定管理機能を提供します。

### シンボルグループの読み込み

```python
from analyze.config import (
    load_symbols_config,
    get_symbol_group,
    get_symbols,
    get_return_periods,
)

# 設定を読み込み
config = load_symbols_config()

# シンボルグループを取得
mag7_symbols = get_symbol_group("MAG7")

# グループ内の全シンボルを取得
all_symbols = get_symbols(group="indices")

# リターン計算用の期間リストを取得
periods = get_return_periods()
```

---

## reporting モジュール

包括的な市場レポート生成機能を提供します。週次マーケットレポート作成に最適化された AIエージェント向け分析機能を中心に、パフォーマンス・通貨・金利・イベント分析を統合。

### パフォーマンス分析（AIエージェント向け）

```python
from analyze.reporting import (
    PerformanceAnalyzer4Agent,
    PerformanceResult,
)

# AIエージェント向けのパフォーマンス分析
analyzer = PerformanceAnalyzer4Agent()

# クロスセクション分析（複数シンボル、複数期間）
result = analyzer.analyze_cross_section(
    data=df,
    group="MAG7",
    periods=["1d", "1w", "1mo", "ytd"],
)

# 結果はJSON形式で出力可能
performance_json = result.to_dict()
```

### 通貨分析（AIエージェント向け）

```python
from analyze.reporting import (
    CurrencyAnalyzer4Agent,
    CurrencyResult,
)

# 通貨ペア分析（USD/JPY, EUR/USD等）
analyzer = CurrencyAnalyzer4Agent()
result = analyzer.analyze()

# 分析結果
print(result.currencies)  # 通貨ペアごとの情報
print(result.summary)     # サマリー
```

### 金利分析（AIエージェント向け）

```python
from analyze.reporting import (
    InterestRateAnalyzer4Agent,
    InterestRateResult,
)

# 金利データ分析（10年債利回り、FF金利等）
analyzer = InterestRateAnalyzer4Agent()
result = analyzer.analyze()

# 分析結果
print(result.rates)       # 金利データ
print(result.summary)     # サマリー
```

### 今後の経済イベント・決算（AIエージェント向け）

```python
from analyze.reporting import (
    UpcomingEvents4Agent,
    UpcomingEventsResult,
    get_upcoming_earnings,
    get_upcoming_economic_releases,
    MAJOR_RELEASES,
)

# 今後14日間のイベントを取得
analyzer = UpcomingEvents4Agent()
result = analyzer.analyze(days_ahead=14)

# 便利関数
earnings = get_upcoming_earnings(days_ahead=7)
releases = get_upcoming_economic_releases()

# 主要経済指標リスト
print(MAJOR_RELEASES)
```

### その他の分析

```python
from analyze.reporting import metal, us_treasury, vix

# 貴金属分析（金、銀、プラチナ等）
metal_data = metal.analyze()

# 米国債分析
treasury_data = us_treasury.analyze()

# VIX（恐怖指数）分析
vix_data = vix.analyze()
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

<!-- AUTO-GENERATED: API -->

## 公開 API

### 主要クラス

#### `TechnicalIndicators` (technical モジュール)

**説明**: テクニカル指標を計算するための静的メソッドを提供するクラス

**基本的な使い方**:

```python
import pandas as pd
from analyze.technical.indicators import TechnicalIndicators

prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])

# 移動平均
sma = TechnicalIndicators.calculate_sma(prices, window=3)
ema = TechnicalIndicators.calculate_ema(prices, window=3)

# RSI（相対力指数）
rsi = TechnicalIndicators.calculate_rsi(prices, period=14)

# MACD
macd_result = TechnicalIndicators.calculate_macd(prices)
```

**主なメソッド**:

| メソッド | 説明 |
|---------|------|
| `calculate_sma()` | 単純移動平均 |
| `calculate_ema()` | 指数移動平均 |
| `calculate_rsi()` | 相対力指数（オシレーター） |
| `calculate_macd()` | MACD（トレンド追随） |
| `calculate_bollinger_bands()` | ボリンジャーバンド（ボラティリティ） |
| `calculate_returns()` | リターン率 |
| `calculate_volatility()` | ボラティリティ（標準偏差） |

---

#### `EarningsCalendar` (earnings モジュール)

**説明**: 決算日程と決算推定値を管理するカレンダークラス

**基本的な使い方**:

```python
from analyze.earnings import EarningsCalendar, get_upcoming_earnings

# 方法1: クラスを使用
calendar = EarningsCalendar()
upcoming = calendar.get_upcoming_earnings(days_ahead=14)

# 方法2: 便利関数を使用
earnings_json = get_upcoming_earnings(days_ahead=7, format="json")
```

---

#### `PerformanceAnalyzer4Agent` (reporting モジュール)

**説明**: AIエージェント向けパフォーマンス分析。週次マーケットレポート生成に最適化

**基本的な使い方**:

```python
from analyze.reporting import PerformanceAnalyzer4Agent

analyzer = PerformanceAnalyzer4Agent()

# 複数銘柄・複数期間のパフォーマンス分析
result = analyzer.analyze_cross_section(
    data=df,
    group="MAG7",
    periods=["1d", "1w", "1mo", "ytd"],
)

# JSON形式でエクスポート
report_json = result.to_dict()
```

---

#### `CurrencyAnalyzer4Agent` (reporting モジュール)

**説明**: AIエージェント向け通貨分析。主要通貨ペアのレート・変動率を取得

**基本的な使い方**:

```python
from analyze.reporting import CurrencyAnalyzer4Agent

analyzer = CurrencyAnalyzer4Agent()
result = analyzer.analyze()

# 通貨ペア情報
for currency in result.currencies:
    print(f"{currency.pair}: {currency.rate}")
```

---

#### `InterestRateAnalyzer4Agent` (reporting モジュール)

**説明**: AIエージェント向け金利分析。米国債利回り・FF金利等を取得

**基本的な使い方**:

```python
from analyze.reporting import InterestRateAnalyzer4Agent

analyzer = InterestRateAnalyzer4Agent()
result = analyzer.analyze()

# 金利情報
for rate in result.rates:
    print(f"{rate.name}: {rate.value:.2f}%")
```

---

#### `UpcomingEvents4Agent` (reporting モジュール)

**説明**: AIエージェント向けイベント分析。今後の経済指標発表・決算日程を取得

**基本的な使い方**:

```python
from analyze.reporting import UpcomingEvents4Agent

analyzer = UpcomingEvents4Agent()
result = analyzer.analyze(days_ahead=14)

# 今後14日間のイベント
print(result.earnings)   # 決算予定
print(result.economic)   # 経済指標発表
```

---

#### `MarketDataAnalyzer` (integration モジュール)

**説明**: market パッケージとの統合。データ取得と分析を一括実行

**基本的な使い方**:

```python
from analyze.integration import MarketDataAnalyzer, fetch_and_analyze

# 方法1: クラスを使用
analyzer = MarketDataAnalyzer()
result = analyzer.fetch_and_analyze(
    symbols=["AAPL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# 方法2: 便利関数を使用（テクニカル指標付き）
result = fetch_and_analyze(
    symbols=["AAPL"],
    indicators=["sma_20", "rsi_14", "macd"],
)
```

---

### 関数

#### `calculate_multi_period_returns()`

**説明**: 複数の期間にわたるリターンを一括計算

**使用例**:

```python
from analyze.returns import calculate_multi_period_returns, TICKERS_MAG7

returns = calculate_multi_period_returns(
    tickers=TICKERS_MAG7,
    periods=["1d", "1w", "1mo", "ytd"],
)
```

#### `analyze_sector_performance()`

**説明**: セクター別のパフォーマンスを分析

**使用例**:

```python
from analyze.sector import analyze_sector_performance

result = analyze_sector_performance(period="1mo", top_n=5)
for sector in result.sectors:
    print(f"{sector.name}: {sector.return_1m:.2%}")
```

#### `generate_returns_report()`

**説明**: リターン分析レポートを生成

**使用例**:

```python
from analyze.returns import generate_returns_report, TICKERS_MAG7, RETURN_PERIODS

report = generate_returns_report(
    tickers=TICKERS_MAG7,
    periods=RETURN_PERIODS,
)
```

---

### 型定義

```python
# Technical Analysis
from analyze import (
    SMAParams, EMAParams, RSIParams, MACDParams, MACDResult,
    BollingerBandsParams, BollingerBandsResult, ReturnParams, VolatilityParams,
)

# Statistics
from analyze import (
    DescriptiveStats, CorrelationResult, CorrelationMethod,
)

# Earnings
from analyze import (
    EarningsCalendar, EarningsData, get_upcoming_earnings,
)

# Returns & Constants
from analyze import (
    RETURN_PERIODS, TICKERS_US_INDICES, TICKERS_GLOBAL_INDICES,
    TICKERS_MAG7, TICKERS_SECTORS,
)

# Integration & Analysis
from analyze import (
    MarketDataAnalyzer, analyze_market_data, fetch_and_analyze,
)

# Sector
from analyze import sector
```

---

### 設定・レポート

**config モジュール**: シンボルグループと期間設定の管理

```python
from analyze.config import (
    load_symbols_config,
    get_symbol_group,
    get_symbols,
    get_return_periods,
)
```

**reporting モジュール**: 包括的な市場レポート生成（週次マーケットレポート等）

```python
from analyze.reporting import (
    # パフォーマンス分析
    PerformanceAnalyzer,
    PerformanceAnalyzer4Agent,
    PerformanceResult,
    # 通貨分析
    CurrencyAnalyzer,
    CurrencyAnalyzer4Agent,
    CurrencyResult,
    # 金利分析
    InterestRateAnalyzer,
    InterestRateAnalyzer4Agent,
    InterestRateResult,
    # 今後のイベント
    UpcomingEventsAnalyzer,
    UpcomingEvents4Agent,
    UpcomingEventsResult,
    get_upcoming_earnings,
    get_upcoming_economic_releases,
    MAJOR_RELEASES,
    # 追加モジュール
    metal,      # 貴金属分析
    us_treasury,  # 米国債分析
    vix,        # VIX分析
)
```

**visualization モジュール**: 拡張された可視化機能

```python
from analyze.visualization import (
    # 基本チャート
    ChartBuilder,
    CandlestickChart,
    LineChart,
    HeatmapChart,
    # 特化チャート
    beta,        # ベータ値チャート
    correlation, # 相関チャート
    currency,    # 通貨チャート
    performance, # パフォーマンスチャート
    volatility,  # ボラティリティチャート
)
```

**statistics モジュール**: 拡張された統計分析

```python
from analyze.statistics import (
    StatisticalAnalyzer,  # 統計分析ベースクラス
    # 個別モジュール
    beta,        # ベータ値計算
    correlation, # 相関分析
    descriptive, # 記述統計
)
```

<!-- END: API -->

---

<!-- AUTO-GENERATED: STRUCTURE -->

## ディレクトリ構造

```
analyze/
├── __init__.py                    # 公開 API
├── py.typed                       # 型チェック対応マーカー
├── currency.py                    # 通貨関連ユーティリティ
├── reporting/                     # レポート生成（週次マーケットレポート等）
│   ├── __init__.py
│   ├── currency.py                # 通貨分析
│   ├── currency_agent.py          # 通貨分析（AIエージェント向け）
│   ├── interest_rate.py           # 金利分析
│   ├── interest_rate_agent.py     # 金利分析（AIエージェント向け）
│   ├── market_report_utils.py     # レポート生成ユーティリティ
│   ├── metal.py                   # 貴金属分析
│   ├── performance.py             # パフォーマンス分析
│   ├── performance_agent.py       # パフォーマンス分析（AIエージェント向け）
│   ├── upcoming_events.py         # 今後の経済イベント・決算
│   ├── upcoming_events_agent.py   # イベント分析（AIエージェント向け）
│   ├── us_treasury.py             # 米国債分析
│   └── vix.py                     # VIX（恐怖指数）分析
├── visualization/                 # 可視化
│   ├── __init__.py
│   ├── beta.py                    # ベータ値可視化
│   ├── charts.py                  # 汎用チャート
│   ├── correlation.py             # 相関可視化
│   ├── currency.py                # 通貨チャート
│   ├── heatmap.py                 # ヒートマップ
│   ├── performance.py             # パフォーマンスチャート
│   ├── price_charts.py            # 価格チャート（ローソク足等）
│   └── volatility.py              # ボラティリティチャート
├── statistics/                    # 統計分析
│   ├── __init__.py
│   ├── base.py                    # 統計分析ベースクラス
│   ├── beta.py                    # ベータ値計算
│   ├── correlation.py             # 相関分析
│   ├── descriptive.py             # 記述統計
│   └── types.py                   # 統計型定義
├── technical/                     # テクニカル分析
│   ├── __init__.py
│   ├── indicators.py              # テクニカル指標（SMA, EMA, RSI, MACD等）
│   └── types.py                   # テクニカル型定義
├── config/                        # 設定管理
│   ├── __init__.py
│   ├── loader.py                  # 設定ローダー
│   └── models.py                  # 設定モデル
├── returns/                       # リターン計算
│   ├── __init__.py
│   ├── returns.py                 # リターン計算関数
│   └── returns_proto.py           # リターンプロトタイプ
├── sector/                        # セクター分析
│   ├── __init__.py
│   └── sector.py                  # セクターパフォーマンス分析
├── earnings/                      # 決算分析
│   ├── __init__.py
│   ├── earnings.py                # 決算カレンダー・決算データ
│   └── types.py                   # 決算型定義
└── integration/                   # market パッケージ統合
    ├── __init__.py
    └── market_integration.py      # 市場データ取得と分析の統合
```

<!-- END: STRUCTURE -->

---

<!-- AUTO-GENERATED: STATS -->

## 統計情報

| 項目 | 値 |
|------|-----|
| Python ファイル数 | 46 |
| 総行数（実装コード） | 16,970 |
| モジュール数 | 9 |
| テストファイル数 | 32 |

<!-- END: STATS -->

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
