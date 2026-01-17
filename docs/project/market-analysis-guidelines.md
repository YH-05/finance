# 週次マーケットレポート用 市場分析ガイドライン

## 概要

本ドキュメントは、週次マーケットレポート作成のための標準的な市場分析項目、データソース、分析手法を定義します。`market_analysis`パッケージを活用し、一貫性のある高品質なレポート作成を支援します。

## データソースの方針

| データ種別 | データソース | 理由 |
|-----------|-------------|------|
| 金利データ | FRED | 公式な経済統計として信頼性が高く、長期の時系列データが利用可能 |
| 株価・指数 | yfinance | リアルタイム性が高く、幅広い銘柄・指数をカバー |
| 為替レート | yfinance | 日次の為替レートを取得可能 |
| コモディティ | yfinance | 先物価格をリアルタイムで取得可能 |
| 経済指標 | FRED | GDP、CPI、雇用統計など公式統計を利用 |

### FRED series ID参照先
`data/config/fred_series.json` に主要な経済指標のseries IDとメタデータが定義されています。

### yfinanceティッカー参照先
`data/config/yfinance_tickers.json` に主要な株式、指数、ETF、為替、コモディティのティッカーシンボルとメタデータが定義されています。

## 週次マーケットレポートの標準分析項目

### 1. 主要インデックス動向

#### 対象ティッカー
| ティッカー | 名称 | 説明 |
|-----------|------|------|
| ^GSPC | S&P 500 | 米国大型株500銘柄の時価総額加重平均指数 |
| ^IXIC | NASDAQ総合指数 | NASDAQ上場全銘柄の時価総額加重平均指数 |
| ^DJI | ダウ工業株30種平均 | 米国を代表する30銘柄の株価平均指数 |
| ^N225 | 日経平均株価 | 東京証券取引所プライム市場の代表的な225銘柄の株価平均指数 |

#### 分析項目
1. **移動平均との乖離**
   - 50日移動平均（SMA50）との乖離率
   - 200日移動平均（SMA200）との乖離率
   - 解釈：
     - 価格 > SMA50: 短期的な上昇トレンド
     - 価格 > SMA200: 長期的な上昇トレンド
     - ゴールデンクロス（SMA50 > SMA200）: 強気シグナル
     - デッドクロス（SMA50 < SMA200）: 弱気シグナル

2. **パフォーマンス指標**
   - 1日リターン
   - 1週間リターン（5営業日）
   - 1ヶ月リターン（21営業日）
   - 1年リターン（252営業日）
   - 5年リターン（1260営業日）
   - MTD（Month-to-Date）: 月初来リターン
   - YTD（Year-to-Date）: 年初来リターン

3. **ボラティリティ**
   - 20日ボラティリティ（年率換算）
   - 解釈：
     - 高ボラティリティ（>20%）: 市場の不確実性が高い
     - 低ボラティリティ（<10%）: 市場が安定

#### 実装例
```python
from market_analysis.api import MarketData, Analysis

# データ取得
data = MarketData()
sp500 = data.fetch_stock("^GSPC", start="2024-01-01")

# テクニカル分析
analysis = (
    Analysis(sp500, symbol="S&P 500")
    .add_sma(period=50)
    .add_sma(period=200)
    .add_returns()
    .add_volatility(period=20, annualize=True)
)

result = analysis.result()
latest = result.data.iloc[-1]

# 移動平均乖離率の計算
price = latest['close']
sma50 = latest['sma_50']
sma200 = latest['sma_200']

sma50_divergence = ((price - sma50) / sma50) * 100
sma200_divergence = ((price - sma200) / sma200) * 100

# リターン計算
returns_1d = result.data['close'].pct_change(1).iloc[-1] * 100
returns_1w = result.data['close'].pct_change(5).iloc[-1] * 100
returns_1m = result.data['close'].pct_change(21).iloc[-1] * 100
returns_1y = result.data['close'].pct_change(252).iloc[-1] * 100

# MTD/YTD計算
import pandas as pd
from datetime import datetime

current_date = result.data.index[-1]
month_start = pd.Timestamp(current_date.year, current_date.month, 1)
year_start = pd.Timestamp(current_date.year, 1, 1)

mtd_return = ((price / result.data.loc[month_start:, 'close'].iloc[0]) - 1) * 100
ytd_return = ((price / result.data.loc[year_start:, 'close'].iloc[0]) - 1) * 100
```

### 2. スタイルファクター分析

#### 対象ティッカー
| ティッカー | 名称 | スタイル |
|-----------|------|---------|
| VUG | Vanguard Growth ETF | グロース（成長株） |
| VTV | Vanguard Value ETF | バリュー（割安株） |
| SPY | SPDR S&P 500 ETF Trust | 大型株ベンチマーク |
| IWM | iShares Russell 2000 ETF | 小型株 |
| QUAL | iShares MSCI USA Quality Factor ETF | クオリティ（高品質企業） |

#### 分析項目
1. **相対パフォーマンス**
   - グロース vs バリュー: VUG / VTV 比率
   - 大型 vs 小型: SPY / IWM 比率
   - 解釈：
     - VUG/VTV上昇: グロース優勢（リスクオン）
     - VUG/VTV下降: バリュー優勢（リスクオフ）
     - SPY/IWM上昇: 大型株優勢（安全志向）
     - SPY/IWM下降: 小型株優勢（リスクテイク）

2. **トレンド判定**
   - 各ETFの50日/200日移動平均との位置関係
   - 1週間・1ヶ月・1年リターン及びMTD/YTD

3. **クオリティファクター**
   - QUAL vs SPY の相対パフォーマンス
   - 解釈：QUAL優勢時は、財務健全性を重視する市場環境

#### 実装例
```python
from market_analysis.api import MarketData, Analysis

data = MarketData()

# スタイルファクターETFのデータ取得
vug = data.fetch_stock("VUG", start="2024-01-01")
vtv = data.fetch_stock("VTV", start="2024-01-01")
spy = data.fetch_stock("SPY", start="2024-01-01")
iwm = data.fetch_stock("IWM", start="2024-01-01")
qual = data.fetch_stock("QUAL", start="2024-01-01")

# 相対パフォーマンス計算
import pandas as pd

# VUG/VTV比率（グロース vs バリュー）
growth_value_ratio = vug['close'] / vtv['close']
growth_value_trend = growth_value_ratio.pct_change(21).iloc[-1] * 100  # 1ヶ月変化率

# SPY/IWM比率（大型 vs 小型）
large_small_ratio = spy['close'] / iwm['close']
large_small_trend = large_small_ratio.pct_change(21).iloc[-1] * 100

# QUAL vs SPY相対パフォーマンス
qual_spy_ratio = qual['close'] / spy['close']
quality_trend = qual_spy_ratio.pct_change(21).iloc[-1] * 100

print(f"グロース/バリュー 1ヶ月変化率: {growth_value_trend:.2f}%")
print(f"大型/小型 1ヶ月変化率: {large_small_trend:.2f}%")
print(f"クオリティ/SPY 1ヶ月変化率: {quality_trend:.2f}%")
```

### 3. セクター別パフォーマンス

#### 対象ティッカー（11セクターETF）
| ティッカー | セクター | 日本語名称 |
|-----------|---------|-----------|
| XLK | Technology | テクノロジー |
| XLF | Financials | 金融 |
| XLV | Health Care | ヘルスケア |
| XLE | Energy | エネルギー |
| XLI | Industrials | 資本財 |
| XLY | Consumer Discretionary | 一般消費財 |
| XLP | Consumer Staples | 生活必需品 |
| XLU | Utilities | 公益事業 |
| XLRE | Real Estate | 不動産 |
| XLB | Materials | 素材 |
| XLC | Communication Services | 通信サービス |

#### 分析項目
1. **セクターローテーション分析**
   - 1週間の騰落率ランキング
   - 上位3セクター・下位3セクターの特定
   - セクター別の1日・1週間・1ヶ月・1年・5年リターン及びMTD/YTD

2. **個別銘柄のドライバー分析**
   - 上位・下位セクターそれぞれで主要な値動きの原因となった個別銘柄をピックアップ
   - ニュース、決算、RSSフィードなどから背景情報を収集
   - 解釈：
     - セクターローテーションは景気サイクルと関連
     - 景気拡大初期: 金融、テクノロジー
     - 景気拡大後期: エネルギー、素材
     - 景気後退期: ヘルスケア、生活必需品、公益事業

3. **相対強度**
   - 各セクターのS&P 500に対する相対パフォーマンス

#### 実装例
```python
from market_analysis.api import MarketData
import pandas as pd

data = MarketData()

# 11セクターETFのティッカー
sector_tickers = {
    "XLK": "テクノロジー",
    "XLF": "金融",
    "XLV": "ヘルスケア",
    "XLE": "エネルギー",
    "XLI": "資本財",
    "XLY": "一般消費財",
    "XLP": "生活必需品",
    "XLU": "公益事業",
    "XLRE": "不動産",
    "XLB": "素材",
    "XLC": "通信サービス",
}

# データ取得と1週間リターン計算
sector_performance = {}
for ticker, name in sector_tickers.items():
    df = data.fetch_stock(ticker, start="2024-01-01")
    weekly_return = df['close'].pct_change(5).iloc[-1] * 100
    sector_performance[name] = {
        'ticker': ticker,
        'weekly_return': weekly_return,
        'latest_price': df['close'].iloc[-1]
    }

# ランキング作成
ranking = pd.DataFrame(sector_performance).T.sort_values('weekly_return', ascending=False)
print("セクター別 1週間パフォーマンス:")
print(ranking)

# 上位3・下位3セクター
top3 = ranking.head(3)
bottom3 = ranking.tail(3)

print("\n上位3セクター:")
print(top3[['ticker', 'weekly_return']])

print("\n下位3セクター:")
print(bottom3[['ticker', 'weekly_return']])

# セクターローテーション判定
if "XLF" in top3.index or "XLK" in top3.index:
    print("\n→ 景気拡大初期の兆候（金融・テクノロジー優勢）")
elif "XLE" in top3.index or "XLB" in top3.index:
    print("\n→ 景気拡大後期の兆候（エネルギー・素材優勢）")
elif "XLV" in top3.index or "XLP" in top3.index or "XLU" in top3.index:
    print("\n→ 景気後退・防御的局面（ヘルスケア・生活必需品・公益事業優勢）")
```

### 4. Magnificent 7動向

#### 対象ティッカー
| ティッカー | 企業名 | セクター |
|-----------|--------|---------|
| AAPL | Apple Inc. | テクノロジー |
| MSFT | Microsoft Corporation | テクノロジー |
| GOOGL | Alphabet Inc. (Google) | 通信サービス |
| AMZN | Amazon.com Inc. | 一般消費財 |
| NVDA | NVIDIA Corporation | テクノロジー |
| META | Meta Platforms Inc. (Facebook) | 通信サービス |
| TSLA | Tesla Inc. | 一般消費財 |

#### 分析項目
1. **週間パフォーマンス**
   - 各銘柄の1週間リターン
   - Mag7全体の加重平均パフォーマンス
   - S&P 500との比較

2. **決算発表スケジュール**
   - 直近の決算発表日
   - 次回決算予定日
   - コンセンサス予想（EPSなど）

3. **ニュースハイライト**
   - 重要なニュースやアナウンスメント
   - 製品発表、M&A、規制動向など

4. **バリュエーション**
   - PER（株価収益率）
   - PSR（株価売上高倍率）
   - 時価総額

#### 実装例
```python
from market_analysis.api import MarketData
import pandas as pd

data = MarketData()

# Magnificent 7のティッカー
mag7_tickers = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta",
    "TSLA": "Tesla",
}

# データ取得とパフォーマンス計算
mag7_performance = {}
for ticker, name in mag7_tickers.items():
    df = data.fetch_stock(ticker, start="2024-01-01")

    # 各種リターン計算
    returns = {
        '1d': df['close'].pct_change(1).iloc[-1] * 100,
        '1w': df['close'].pct_change(5).iloc[-1] * 100,
        '1m': df['close'].pct_change(21).iloc[-1] * 100,
        '1y': df['close'].pct_change(252).iloc[-1] * 100,
        'ytd': ((df['close'].iloc[-1] / df['close'].loc[f"{df.index[-1].year}-01-01":].iloc[0]) - 1) * 100
    }

    mag7_performance[name] = {
        'ticker': ticker,
        **returns,
        'latest_price': df['close'].iloc[-1]
    }

# パフォーマンステーブル作成
perf_df = pd.DataFrame(mag7_performance).T
print("Magnificent 7 パフォーマンス:")
print(perf_df.to_string())

# 加重平均計算（簡易版：均等加重）
avg_weekly = perf_df['1w'].mean()
print(f"\nMag7 平均1週間リターン: {avg_weekly:.2f}%")

# S&P 500との比較
sp500 = data.fetch_stock("^GSPC", start="2024-01-01")
sp500_weekly = sp500['close'].pct_change(5).iloc[-1] * 100
print(f"S&P 500 1週間リターン: {sp500_weekly:.2f}%")
print(f"Mag7 vs S&P 500: {avg_weekly - sp500_weekly:+.2f}%")
```

### 5. マクロ経済指標

#### 5.1 金利動向（FREDから取得）

| Series ID | 名称 | 説明 |
|-----------|------|------|
| DGS3MO | 米国債3ヶ月物利回り | 短期金利の代表格 |
| DGS2 | 米国債2年物利回り | 中期金利、近い将来の金融政策期待を反映 |
| DGS10 | 米国債10年物利回り | 長期金利、経済成長期待を反映 |
| T10Y2Y | 10年債-2年債スプレッド | イールドカーブの形状を示す重要指標 |

**解釈ポイント:**
- イールドカーブ（DGS10 - DGS2）
  - 正常（プラス）: 経済成長期待
  - 逆転（マイナス）: 景気後退の前兆シグナル（過去の景気後退前に観測）
- 金利上昇: インフレ懸念、金融引き締め
- 金利低下: 景気減速懸念、金融緩和

#### 実装例（金利）
```python
from market_analysis.api import MarketData
import pandas as pd

data = MarketData(fred_api_key="YOUR_FRED_API_KEY")  # 環境変数FRED_API_KEYからも自動取得

# 金利データ取得
dgs3mo = data.fetch_fred("DGS3MO", start="2024-01-01")
dgs2 = data.fetch_fred("DGS2", start="2024-01-01")
dgs10 = data.fetch_fred("DGS10", start="2024-01-01")

# イールドカーブスプレッド計算
yield_curve = pd.DataFrame({
    '3mo': dgs3mo['close'],
    '2y': dgs2['close'],
    '10y': dgs10['close']
})

# 10年-2年スプレッド
yield_curve['10y-2y'] = yield_curve['10y'] - yield_curve['2y']

latest = yield_curve.iloc[-1]
print(f"3ヶ月物: {latest['3mo']:.2f}%")
print(f"2年物: {latest['2y']:.2f}%")
print(f"10年物: {latest['10y']:.2f}%")
print(f"10-2年スプレッド: {latest['10y-2y']:.2f}%")

if latest['10y-2y'] < 0:
    print("⚠️ イールドカーブ逆転 - 景気後退の警戒シグナル")
elif latest['10y-2y'] > 0.5:
    print("✓ イールドカーブ正常 - 経済成長期待")
else:
    print("→ イールドカーブフラット化 - 移行期")
```

#### 5.2 為替（yfinanceから取得）

| ティッカー | 通貨ペア | 説明 |
|-----------|---------|------|
| USDJPY=X | 米ドル/日本円 | 円相場の基準 |
| EURJPY=X | ユーロ/日本円 | ユーロ円相場 |
| EURUSD=X | ユーロ/米ドル | 世界最大の取引量 |
| DX-Y.NYB | 米ドル指数 | 主要6通貨に対する米ドルの価値 |

**解釈ポイント:**
- ドル円上昇: 円安進行（日本輸出企業にプラス、輸入物価上昇）
- ドル円下降: 円高進行（日本輸出企業にマイナス、輸入物価低下）
- ドル指数上昇: ドル高（米国金利上昇や安全資産需要で発生）
- ドル指数下降: ドル安（リスクオン局面で発生しやすい）

#### 実装例（為替）
```python
from market_analysis.api import MarketData, Analysis

data = MarketData()

# 為替データ取得
usdjpy = data.fetch_forex("USDJPY", start="2024-01-01")
eurjpy = data.fetch_forex("EURJPY", start="2024-01-01")
eurusd = data.fetch_forex("EURUSD", start="2024-01-01")
dxy = data.fetch_stock("DX-Y.NYB", start="2024-01-01")  # 米ドル指数

# 各通貨ペアのパフォーマンス
usdjpy_weekly = usdjpy['close'].pct_change(5).iloc[-1] * 100
eurjpy_weekly = eurjpy['close'].pct_change(5).iloc[-1] * 100
eurusd_weekly = eurusd['close'].pct_change(5).iloc[-1] * 100
dxy_weekly = dxy['close'].pct_change(5).iloc[-1] * 100

print(f"USD/JPY 1週間変化率: {usdjpy_weekly:+.2f}%")
print(f"EUR/JPY 1週間変化率: {eurjpy_weekly:+.2f}%")
print(f"EUR/USD 1週間変化率: {eurusd_weekly:+.2f}%")
print(f"米ドル指数 1週間変化率: {dxy_weekly:+.2f}%")

# 為替トレンド判定
if usdjpy_weekly > 0:
    print("→ 円安進行中")
else:
    print("→ 円高進行中")
```

#### 5.3 コモディティ

| ティッカー | 商品 | 説明 |
|-----------|------|------|
| GC=F | 金先物 | 安全資産、インフレヘッジ |
| SI=F | 銀先物 | 工業用途と投資用途 |
| PL=F | プラチナ先物 | 自動車触媒として需要 |
| HG=F | 銅先物 | 景気の先行指標「ドクター・カッパー」 |
| CL=F | WTI原油先物 | エネルギー価格の指標 |

**解釈ポイント:**
- 金価格上昇: リスクオフ、インフレ懸念、ドル安
- 銅価格上昇: 景気拡大期待（製造業・インフラ需要）
- 原油価格上昇: 需要増加または供給制約、インフレ圧力

#### 実装例（コモディティ）
```python
from market_analysis.api import MarketData

data = MarketData()

# コモディティデータ取得
commodities = {
    "GC=F": "金",
    "SI=F": "銀",
    "PL=F": "プラチナ",
    "HG=F": "銅",
    "CL=F": "WTI原油",
}

commodity_performance = {}
for ticker, name in commodities.items():
    df = data.fetch_commodity(ticker, start="2024-01-01")
    weekly_return = df['close'].pct_change(5).iloc[-1] * 100
    commodity_performance[name] = {
        'ticker': ticker,
        'weekly_return': weekly_return,
        'latest_price': df['close'].iloc[-1]
    }

import pandas as pd
perf_df = pd.DataFrame(commodity_performance).T
print("コモディティ 1週間パフォーマンス:")
print(perf_df.to_string())

# 金と銅の動向から市場センチメント判定
gold_return = commodity_performance['金']['weekly_return']
copper_return = commodity_performance['銅']['weekly_return']

if gold_return > 2 and copper_return < -2:
    print("\n⚠️ リスクオフ局面（金上昇・銅下落）")
elif gold_return < -2 and copper_return > 2:
    print("\n✓ リスクオン局面（金下落・銅上昇）")
else:
    print("\n→ 混在シグナル")
```

## market_analysisパッケージの使用方法

### インストール
```bash
# 依存関係のインストール
uv sync --all-extras

# FRED APIキーの設定（環境変数）
export FRED_API_KEY="your_api_key_here"
```

### 基本的な使用パターン

#### 1. データ取得
```python
from market_analysis.api import MarketData

# MarketDataインスタンス作成
data = MarketData(
    cache_path="data/sqlite/market_cache.db",  # キャッシュ有効化
    fred_api_key="YOUR_KEY"  # または環境変数FRED_API_KEY
)

# 株価データ取得
df_stock = data.fetch_stock("AAPL", start="2024-01-01", end="2024-12-31")

# 為替データ取得
df_forex = data.fetch_forex("USDJPY", start="2024-01-01")

# FRED経済指標取得
df_fred = data.fetch_fred("DGS10", start="2024-01-01")

# コモディティ取得
df_commodity = data.fetch_commodity("GC=F", start="2024-01-01")
```

#### 2. テクニカル分析
```python
from market_analysis.api import Analysis

# Analysisインスタンス作成とメソッドチェーン
analysis = (
    Analysis(df_stock, symbol="AAPL")
    .add_sma(period=50)
    .add_sma(period=200)
    .add_ema(period=20)
    .add_returns()
    .add_volatility(period=20, annualize=True)
)

# 結果取得
result = analysis.result()
print(result.data.tail())
print(f"Indicators: {result.indicators}")
```

#### 3. 相関分析
```python
from market_analysis.api import Analysis

# 複数銘柄の相関行列
dfs = [
    data.fetch_stock("AAPL", start="2024-01-01"),
    data.fetch_stock("GOOGL", start="2024-01-01"),
    data.fetch_stock("MSFT", start="2024-01-01"),
]

correlation_matrix = Analysis.correlation(
    dfs,
    symbols=["AAPL", "GOOGL", "MSFT"],
    method="pearson"
)
print(correlation_matrix)

# ローリング相関
rolling_corr = Analysis.rolling_correlation(
    dfs[0], dfs[1],
    period=20,
    column="close"
)
print(rolling_corr.tail())

# ベータ係数
beta = Analysis.beta(
    stock=data.fetch_stock("AAPL", start="2024-01-01"),
    benchmark=data.fetch_stock("^GSPC", start="2024-01-01")
)
print(f"AAPL Beta: {beta:.2f}")
```

#### 4. データエクスポート
```python
# SQLiteに保存
data.save_to_sqlite(
    db_path="data/sqlite/market_data.db",
    data=df_stock,
    table_name="aapl_daily"
)

# AI Agent用JSON形式
json_output = data.to_agent_json(
    data=df_stock,
    symbol="AAPL",
    include_metadata=True
)
```

### チャート生成（visualization API）
```python
from market_analysis.api import Chart

# 価格チャート（移動平均線付き）
Chart.price_with_ma(
    data=result.data,
    symbol="AAPL",
    ma_periods=[50, 200],
    output_path="output/aapl_price.png"
)

# ボラティリティチャート
Chart.volatility(
    data=result.data,
    symbol="AAPL",
    output_path="output/aapl_volatility.png"
)

# 相関ヒートマップ
Chart.correlation_heatmap(
    correlation_matrix=correlation_matrix,
    output_path="output/correlation.png"
)
```

## 週次レポート作成のワークフロー例

```python
from market_analysis.api import MarketData, Analysis
import pandas as pd
from datetime import datetime, timedelta

# 1. データ取得期間設定
end_date = datetime.now()
start_date = end_date - timedelta(days=365)  # 1年分

data = MarketData(
    cache_path="data/sqlite/market_cache.db",
    fred_api_key="YOUR_KEY"
)

# 2. 主要インデックス分析
indices = ["^GSPC", "^IXIC", "^DJI", "^N225"]
index_results = {}

for ticker in indices:
    df = data.fetch_stock(ticker, start=start_date.strftime("%Y-%m-%d"))
    analysis = (
        Analysis(df, symbol=ticker)
        .add_sma(period=50)
        .add_sma(period=200)
        .add_returns()
        .add_volatility(period=20)
    )
    index_results[ticker] = analysis.result()

# 3. セクター分析
sectors = ["XLK", "XLF", "XLV", "XLE", "XLI", "XLY", "XLP", "XLU", "XLRE", "XLB", "XLC"]
sector_performance = {}

for ticker in sectors:
    df = data.fetch_stock(ticker, start=start_date.strftime("%Y-%m-%d"))
    weekly_return = df['close'].pct_change(5).iloc[-1] * 100
    sector_performance[ticker] = weekly_return

sector_ranking = pd.Series(sector_performance).sort_values(ascending=False)

# 4. Magnificent 7分析
mag7 = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
mag7_results = {}

for ticker in mag7:
    df = data.fetch_stock(ticker, start=start_date.strftime("%Y-%m-%d"))
    weekly_return = df['close'].pct_change(5).iloc[-1] * 100
    mag7_results[ticker] = weekly_return

# 5. マクロ指標
dgs10 = data.fetch_fred("DGS10", start=start_date.strftime("%Y-%m-%d"))
dgs2 = data.fetch_fred("DGS2", start=start_date.strftime("%Y-%m-%d"))
usdjpy = data.fetch_forex("USDJPY", start=start_date.strftime("%Y-%m-%d"))

# 6. レポート生成
print("=" * 60)
print(f"週次マーケットレポート - {end_date.strftime('%Y年%m月%d日')}")
print("=" * 60)

print("\n【主要インデックス】")
for ticker, result in index_results.items():
    latest = result.data.iloc[-1]
    print(f"{ticker}: {latest['close']:.2f} (1週間: {latest['returns']*5*100:+.2f}%)")

print("\n【セクターランキング（1週間）】")
print(sector_ranking.head(3).to_string())
print("...")
print(sector_ranking.tail(3).to_string())

print("\n【Magnificent 7】")
for ticker, ret in mag7_results.items():
    print(f"{ticker}: {ret:+.2f}%")

print("\n【マクロ指標】")
print(f"10年債利回り: {dgs10['close'].iloc[-1]:.2f}%")
print(f"2年債利回り: {dgs2['close'].iloc[-1]:.2f}%")
print(f"イールドスプレッド: {(dgs10['close'].iloc[-1] - dgs2['close'].iloc[-1]):.2f}%")
print(f"USD/JPY: {usdjpy['close'].iloc[-1]:.2f}")
```

## トラブルシューティング

### FRED APIキーエラー
```
ValidationError: FRED API key not found. Set FRED_API_KEY environment variable.
```
**解決策:**
```bash
export FRED_API_KEY="your_api_key_here"
```

### データ取得エラー
```
DataFetchError: No data found for symbol: AAPL
```
**解決策:**
- ティッカーシンボルが正しいか確認
- 日付範囲が適切か確認（週末・祝日はデータなし）
- インターネット接続を確認

### キャッシュ関連
キャッシュをクリアする場合:
```bash
rm data/sqlite/market_cache.db
```

## 参考資料

- `src/market_analysis/docs/` - 詳細なライブラリドキュメント
- `data/config/fred_series.json` - FRED series ID一覧
- `data/config/yfinance_tickers.json` - yfinanceティッカー一覧
- `template/` - テスト・実装テンプレート

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-01-14 | 初版作成 - 週次マーケットレポートの標準分析項目とガイドラインを定義 |
