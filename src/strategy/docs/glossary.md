# strategy パッケージ用語集 (Glossary)

## 概要

このドキュメントは、strategy パッケージ内で使用される用語の定義を管理します。
ポートフォリオ管理・分析ライブラリとして、金融用語、技術用語、ライブラリ固有の用語を体系的に整理しています。

**更新日**: 2026-01-14

---

## 1. ドメイン用語（金融・投資）

プロジェクト固有のビジネス概念や金融機能に関する用語。

### ポートフォリオ (Portfolio)

**定義**: 投資家が保有する金融資産の組み合わせ。

**説明**:
strategy パッケージでは、Portfolio クラスが保有銘柄（Holding）のリストとして表現される。
各銘柄にはティッカーシンボルと配分比率（weight）が設定され、全体で資産配分を構成する。

**関連用語**: [Holding](#holding-保有銘柄), [配分比率](#配分比率-weight), [リバランス](#リバランス-rebalancing)

**使用例**:
- 「ポートフォリオを定義する」: 保有銘柄と比率のリストから Portfolio オブジェクトを作成
- 「ポートフォリオを分析する」: リスク指標の計算や資産配分の可視化を実行

**英語表記**: Portfolio

---

### Holding (保有銘柄)

**定義**: ポートフォリオ内の個別保有銘柄を表すデータ構造。

**説明**:
ティッカーシンボル（ticker）と配分比率（weight）のペアで構成される。
dataclass として定義され、不変（frozen）オブジェクトとして扱われる。

**関連用語**: [ポートフォリオ](#ポートフォリオ-portfolio), [ティッカー](#ティッカー-ticker)

**データモデル**: `src/strategy/types.py`

```python
@dataclass(frozen=True)
class Holding:
    ticker: str   # ティッカーシンボル
    weight: float # 配分比率（0.0-1.0）
```

**英語表記**: Holding

---

### 配分比率 (Weight)

**定義**: ポートフォリオ内での各銘柄の比率。0.0 から 1.0 の範囲で表現。

**説明**:
全銘柄の配分比率の合計は 1.0（100%）となるべき。
合計が 1.0 でない場合、normalize オプションで自動正規化が可能。

**関連用語**: [正規化](#正規化-normalization), [配分ドリフト](#配分ドリフト-drift)

**使用例**:
```python
# VOO: 40%, BND: 30%, GLD: 30%
holdings = [("VOO", 0.4), ("BND", 0.3), ("GLD", 0.3)]
```

**英語表記**: Weight / Allocation Weight

---

### ティッカー (Ticker)

**定義**: 証券取引所で金融商品を識別するためのシンボル。

**説明**:
株式、ETF、投資信託などを一意に識別するための短い文字列。
例: VOO（Vanguard S&P 500 ETF）、AAPL（Apple Inc.）、^GSPC（S&P 500 Index）

**関連用語**: [TickerInfo](#tickerinfo-銘柄情報)

**使用例**:
- 「VOO」: Vanguard S&P 500 ETF
- 「BND」: Vanguard Total Bond Market ETF
- 「^GSPC」: S&P 500 Index（ベンチマーク）

**英語表記**: Ticker Symbol

---

### TickerInfo (銘柄情報)

**定義**: ティッカーの詳細情報を格納するデータ構造。

**説明**:
銘柄名、セクター、業種、資産クラスなどの情報を含む。
DataProvider から取得され、資産配分分析やセクター別集計に使用される。

**関連用語**: [資産クラス](#資産クラス-asset-class), [セクター](#セクター-sector)

**データモデル**: `src/strategy/types.py`

```python
@dataclass(frozen=True)
class TickerInfo:
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    asset_class: AssetClass = "equity"
```

**英語表記**: Ticker Information

---

### 資産クラス (Asset Class)

**定義**: 投資対象の大分類。

**説明**:
strategy パッケージでは以下の資産クラスを定義:
- `equity`: 株式
- `bond`: 債券
- `commodity`: コモディティ（商品）
- `real_estate`: 不動産
- `cash`: 現金・短期金融資産
- `other`: その他

**関連用語**: [TickerInfo](#tickerinfo-銘柄情報), [セクター](#セクター-sector)

**データモデル**: `src/strategy/types.py`

```python
type AssetClass = Literal["equity", "bond", "commodity", "real_estate", "cash", "other"]
```

**英語表記**: Asset Class

---

### セクター (Sector)

**定義**: 経済活動の分野による分類。

**説明**:
株式を業種別にグループ化するための分類。
例: Technology、Financial Services、Healthcare など。
資産配分をセクター別に集計・可視化する際に使用。

**関連用語**: [資産クラス](#資産クラス-asset-class), [TickerInfo](#tickerinfo-銘柄情報)

**英語表記**: Sector

---

### 分析期間 (Period)

**定義**: リスク指標計算やパフォーマンス分析の対象期間。

**説明**:
プリセット期間（1y, 3y, 5y, 10y, ytd, max）またはカスタム期間（開始日・終了日）で指定。
データが不足している場合、警告を出しつつ利用可能な最大期間で計算。

**関連用語**: [PresetPeriod](#presetperiod-プリセット期間)

**データモデル**: `src/strategy/types.py`

```python
@dataclass(frozen=True)
class Period:
    start: date
    end: date
    preset: PresetPeriod | None = None
```

**英語表記**: Analysis Period

---

### PresetPeriod (プリセット期間)

**定義**: あらかじめ定義された分析期間の選択肢。

**説明**:
strategy パッケージで使用可能なプリセット期間:
- `1y`: 1年
- `3y`: 3年
- `5y`: 5年
- `10y`: 10年
- `ytd`: 年初来（Year To Date）
- `max`: 利用可能な最大期間

**関連用語**: [分析期間](#分析期間-period)

**データモデル**: `src/strategy/types.py`

```python
type PresetPeriod = Literal["1y", "3y", "5y", "10y", "ytd", "max"]
```

**英語表記**: Preset Period

---

## 2. リスク指標用語

ポートフォリオのリスク評価に使用される指標。

### ボラティリティ (Volatility)

**定義**: リターンの変動性を表す指標。年率標準偏差で表現。

**説明**:
日次リターンの標準偏差を年率換算（252営業日）したもの。
高いボラティリティは価格変動が大きいことを示す。

**計算式**:
```
volatility = std(returns) * sqrt(252)
```

**関連用語**: [シャープレシオ](#シャープレシオ-sharpe-ratio), [下方偏差](#下方偏差-downside-deviation)

**英語表記**: Volatility / Annualized Volatility

---

### シャープレシオ (Sharpe Ratio)

**定義**: リスク調整後リターンを評価する指標。超過リターンをボラティリティで除算。

**説明**:
リスクフリーレートを上回るリターン（超過リターン）を、
そのリターンを得るために取ったリスク（ボラティリティ）で評価する。
値が高いほど、リスクに対するリターンが効率的。

**計算式**:
```
sharpe = (mean(returns) - risk_free_rate) / std(returns) * sqrt(252)
```

**関連用語**: [ソルティノレシオ](#ソルティノレシオ-sortino-ratio), [トレイナーレシオ](#トレイナーレシオ-treynor-ratio)

**英語表記**: Sharpe Ratio

---

### ソルティノレシオ (Sortino Ratio)

**定義**: 下方リスクに対するリターンを評価する指標。

**説明**:
シャープレシオと異なり、下方偏差（下落時の変動性）のみを
リスクとして考慮する。上昇はリスクとみなさない。

**計算式**:
```
sortino = (mean(returns) - risk_free_rate) / downside_std * sqrt(252)
```

**関連用語**: [シャープレシオ](#シャープレシオ-sharpe-ratio), [下方偏差](#下方偏差-downside-deviation)

**英語表記**: Sortino Ratio

---

### 下方偏差 (Downside Deviation)

**定義**: 負のリターンのみを対象とした標準偏差。

**説明**:
ソルティノレシオの計算に使用される。
上昇リターンはリスクとみなさず、下落リターンのみをリスクとして評価。

**関連用語**: [ソルティノレシオ](#ソルティノレシオ-sortino-ratio)

**英語表記**: Downside Deviation

---

### 最大ドローダウン (Maximum Drawdown / MDD)

**定義**: ある期間内で経験した最大の資産減少幅。

**説明**:
ピーク（最高値）からトラフ（最安値）までの最大の下落率。
負の値で表現される（例: -0.15 = -15%）。
投資における最悪のシナリオを示す。

**計算式**:
```
cumulative = (1 + returns).cumprod()
running_max = cumulative.cummax()
drawdown = (cumulative - running_max) / running_max
max_drawdown = min(drawdown)
```

**関連用語**: [ドローダウン](#ドローダウン-drawdown)

**英語表記**: Maximum Drawdown (MDD)

---

### ドローダウン (Drawdown)

**定義**: ピーク（最高値）からの下落幅。

**説明**:
任意の時点での資産価値がそれまでの最高値からどれだけ下落しているかを示す。
最大ドローダウンはこれらの最大値。

**関連用語**: [最大ドローダウン](#最大ドローダウン-maximum-drawdown--mdd)

**英語表記**: Drawdown

---

### VaR (Value at Risk)

**定義**: 指定信頼水準での最大予想損失額。

**説明**:
一定の信頼水準（95%、99%など）で、一定期間に発生しうる最大損失を推定。
例: 95% VaR が -2% の場合、95%の確率で損失は 2% 以内に収まると予想。

**計算方法**:
- ヒストリカル法: 過去のリターン分布のパーセンタイルを使用
- パラメトリック法: 正規分布を仮定した計算

**関連用語**: [CVaR](#cvar-conditional-var)（将来拡張）

**英語表記**: Value at Risk (VaR)

---

### ベータ (Beta)

**定義**: ベンチマークに対するポートフォリオの感応度。

**説明**:
市場全体（ベンチマーク）が 1% 動いたとき、ポートフォリオがどれだけ動くかを示す。
- Beta = 1.0: 市場と同程度の変動
- Beta > 1.0: 市場より大きく変動
- Beta < 1.0: 市場より小さく変動

**計算式**:
```
beta = cov(portfolio_returns, benchmark_returns) / var(benchmark_returns)
```

**関連用語**: [トレイナーレシオ](#トレイナーレシオ-treynor-ratio), [情報レシオ](#情報レシオ-information-ratio)

**英語表記**: Beta

---

### トレイナーレシオ (Treynor Ratio)

**定義**: 体系的リスク（ベータ）に対するリターンを評価する指標。

**説明**:
シャープレシオがボラティリティ（総リスク）を使用するのに対し、
トレイナーレシオはベータ（市場リスク）を使用する。
分散投資されたポートフォリオの評価に適している。

**計算式**:
```
treynor = (portfolio_return - risk_free_rate) / beta
```

**関連用語**: [ベータ](#ベータ-beta), [シャープレシオ](#シャープレシオ-sharpe-ratio)

**英語表記**: Treynor Ratio

---

### 情報レシオ (Information Ratio)

**定義**: アクティブリターンをトラッキングエラーで除算した指標。

**説明**:
ベンチマークを上回るリターン（アクティブリターン）を、
ベンチマークからの乖離度（トラッキングエラー）で評価。
アクティブ運用の効率性を測定する。

**計算式**:
```
active_return = portfolio_return - benchmark_return
tracking_error = std(active_return)
information_ratio = mean(active_return) / tracking_error
```

**関連用語**: [ベータ](#ベータ-beta), [ベンチマーク](#ベンチマーク-benchmark)

**英語表記**: Information Ratio

---

### ベンチマーク (Benchmark)

**定義**: ポートフォリオのパフォーマンスを比較するための基準指標。

**説明**:
一般的に市場インデックスが使用される。
例: ^GSPC（S&P 500）、^N225（日経平均）
ベータ、トレイナーレシオ、情報レシオの計算に必要。

**関連用語**: [ベータ](#ベータ-beta), [情報レシオ](#情報レシオ-information-ratio)

**英語表記**: Benchmark

---

### リスクフリーレート (Risk-Free Rate)

**定義**: 無リスク資産のリターン率。

**説明**:
一般的に短期国債の利回りが使用される。
シャープレシオ、ソルティノレシオ、トレイナーレシオの計算に使用。
デフォルト値は 0.0（年率）。

**関連用語**: [シャープレシオ](#シャープレシオ-sharpe-ratio), [超過リターン](#超過リターン-excess-return)

**英語表記**: Risk-Free Rate

---

### 超過リターン (Excess Return)

**定義**: リスクフリーレートを上回るリターン。

**説明**:
リスクを取ることで得られる追加のリターン。
シャープレシオの分子として使用される。

**計算式**:
```
excess_return = portfolio_return - risk_free_rate
```

**関連用語**: [リスクフリーレート](#リスクフリーレート-risk-free-rate)

**英語表記**: Excess Return

---

### 年率化 (Annualization)

**定義**: 日次・週次・月次のデータを年率に換算すること。

**説明**:
strategy パッケージでは、日次データを前提に年率化係数 252（営業日）を使用。
週次は 52、月次は 12 を使用。

**計算例**:
```
# 日次リターンの年率化
annualized_return = daily_return * 252
annualized_volatility = daily_std * sqrt(252)
```

**英語表記**: Annualization

---

### 年率化係数 (Annualization Factor)

**定義**: 年率換算に使用する係数。

**説明**:
データの頻度に応じた係数:
- 日次: 252（営業日）
- 週次: 52
- 月次: 12

**関連用語**: [年率化](#年率化-annualization)

**英語表記**: Annualization Factor

---

## 3. リバランス用語

ポートフォリオの配分調整に関する用語。

### リバランス (Rebalancing)

**定義**: ポートフォリオの配分を目標配分に戻す調整。

**説明**:
価格変動により配分が目標からずれた場合、
売買を行って元の配分に戻すこと。
コスト（手数料・税金）と効果のバランスを考慮して実施する。

**関連用語**: [配分ドリフト](#配分ドリフト-drift), [リバランスコスト](#リバランスコスト-rebalance-cost)

**英語表記**: Rebalancing / Portfolio Rebalancing

---

### 配分ドリフト (Drift)

**定義**: 現在の配分と目標配分の乖離。

**説明**:
価格変動により、ポートフォリオの配分が目標から
ずれていく現象。DriftResult として検出結果を表現。

**関連用語**: [リバランス](#リバランス-rebalancing), [閾値](#閾値-threshold)

**データモデル**: `src/strategy/rebalance/drift.py`

```python
@dataclass
class DriftResult:
    ticker: str
    target_weight: float
    current_weight: float
    drift: float            # current - target
    drift_percent: float    # drift / target * 100
    requires_rebalance: bool
```

**英語表記**: Allocation Drift

---

### 閾値 (Threshold)

**定義**: リバランスを実行するかどうかを判断する基準値。

**説明**:
配分ドリフトがこの閾値を超えた場合、リバランスを推奨。
デフォルト値は 0.05（5%）。

**使用例**:
```python
drift = rebalancer.detect_drift(target_weights, threshold=0.05)
# 5%以上乖離した銘柄は requires_rebalance=True となる
```

**関連用語**: [配分ドリフト](#配分ドリフト-drift)

**英語表記**: Threshold

---

### リバランスコスト (Rebalance Cost)

**定義**: リバランスに伴うコストの概算。

**説明**:
取引手数料と売却時の税金を含む総コスト。
RebalanceCost として概算結果を表現。

**関連用語**: [リバランス](#リバランス-rebalancing), [手数料率](#手数料率-commission-rate)

**データモデル**: `src/strategy/rebalance/cost.py`

```python
@dataclass
class RebalanceCost:
    total_trade_value: float   # 総取引金額
    commission_cost: float     # 手数料コスト
    estimated_tax: float       # 推定税金
    total_cost: float          # 総コスト
    cost_ratio: float          # コスト率
```

**英語表記**: Rebalance Cost

---

### 手数料率 (Commission Rate)

**定義**: 取引金額に対する手数料の割合。

**説明**:
証券会社に支払う取引手数料の率。
デフォルト値は 0.001（0.1%）。

**関連用語**: [リバランスコスト](#リバランスコスト-rebalance-cost)

**英語表記**: Commission Rate

---

### 税率 (Tax Rate)

**定義**: 売却益に対する課税率。

**説明**:
日本の場合、申告分離課税で 20.315%（所得税15.315% + 住民税5%）。
デフォルト値は 0.20315。

**関連用語**: [リバランスコスト](#リバランスコスト-rebalance-cost)

**英語表記**: Tax Rate

---

### 定期リバランス (Periodic Rebalancing)

**定義**: 一定期間ごとに実施するリバランス戦略。

**説明**:
月次、四半期、年次など、カレンダーベースでリバランスを実施。
P1 機能として実装予定。

**関連用語**: [閾値リバランス](#閾値リバランス-threshold-rebalancing)

**英語表記**: Periodic Rebalancing

---

### 閾値リバランス (Threshold Rebalancing)

**定義**: 配分ドリフトが閾値を超えた時に実施するリバランス戦略。

**説明**:
乖離が一定以上になった場合のみリバランスを実施。
取引頻度を抑えつつ、大きな乖離を是正。
P1 機能として実装予定。

**関連用語**: [定期リバランス](#定期リバランス-periodic-rebalancing), [閾値](#閾値-threshold)

**英語表記**: Threshold Rebalancing

---

## 4. 技術用語

strategy パッケージで使用している技術・フレームワーク・ツール。

### Protocol

**定義**: Python の構造的部分型（Structural Subtyping）を実現するための仕組み。

**説明**:
`typing.Protocol` を使用して、インターフェースを定義。
strategy パッケージでは DataProvider プロトコルを定義し、
異なるデータソースを統一的に扱うために使用。

**本プロジェクトでの用途**:
- `DataProvider`: データ取得の抽象インターフェース
- 将来の商用データプロバイダー対応を容易にする

**公式ドキュメント**: [PEP 544 - Protocols: Structural subtyping](https://peps.python.org/pep-0544/)

**関連用語**: [DataProvider](#dataprovider)

**英語表記**: Protocol

---

### DataProvider

**定義**: データ取得の抽象インターフェース（Protocol）。

**説明**:
価格データ（OHLCV）とティッカー情報を取得するためのインターフェース。
market_analysis パッケージ、テスト用モック、将来の商用プロバイダーなど、
異なるデータソースを統一的に扱う。

**本プロジェクトでの用途**:
- MarketAnalysisProvider: デフォルト実装（yfinance/FRED）
- MockProvider: テスト用

**インターフェース定義**: `src/strategy/providers/protocol.py`

```python
class DataProvider(Protocol):
    def get_prices(self, tickers: list[str], start: str, end: str) -> pd.DataFrame: ...
    def get_ticker_info(self, ticker: str) -> TickerInfo: ...
    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]: ...
```

**関連用語**: [MarketAnalysisProvider](#marketanalysisprovider), [MockProvider](#mockprovider)

**英語表記**: Data Provider

---

### MarketAnalysisProvider

**定義**: market_analysis パッケージを使用するデータプロバイダー実装。

**説明**:
DataProvider プロトコルの標準実装。
内部で YFinanceFetcher と FREDFetcher を使用し、
キャッシュ機構を活用したデータ取得を提供。

**本プロジェクトでの用途**:
- デフォルトのデータソース
- キャッシュによる効率的なデータアクセス

**関連用語**: [DataProvider](#dataprovider), [market_analysis](#market_analysis)

**実装箇所**: `src/strategy/providers/market_analysis.py`

**英語表記**: Market Analysis Provider

---

### MockProvider

**定義**: テスト用のモックデータプロバイダー。

**説明**:
DataProvider プロトコルを実装したテスト用のモック。
事前定義されたデータを返すことで、外部依存なしのテストを可能にする。

**本プロジェクトでの用途**:
- ユニットテストでの外部API依存の排除
- 決定論的なテストデータの提供

**関連用語**: [DataProvider](#dataprovider)

**実装箇所**: `src/strategy/providers/mock.py`

**英語表記**: Mock Provider

---

### market_analysis

**定義**: 本リポジトリ内の市場データ取得・分析パッケージ。

**説明**:
yfinance および FRED からデータを取得するパッケージ。
SQLite キャッシュ、リトライ機構、データ変換機能を提供。
strategy パッケージは MarketAnalysisProvider 経由でこのパッケージを使用。

**本プロジェクトでの用途**:
- 価格データ取得（YFinanceFetcher）
- 経済指標取得（FREDFetcher）
- キャッシュ管理（SQLiteCache）

**関連ドキュメント**: `src/market_analysis/docs/`

**英語表記**: Market Analysis Package

---

### pandas

**定義**: Python のデータ分析ライブラリ。

**説明**:
DataFrame と Series を中心としたデータ構造を提供。
金融データの処理・分析に広く使用される。

**本プロジェクトでの用途**:
- 価格データの格納（DataFrame）
- リターン計算、統計処理
- MultiIndex による複数銘柄データの管理

**公式サイト**: https://pandas.pydata.org/

**バージョン**: >=2.0

**英語表記**: pandas

---

### numpy

**定義**: Python の数値計算ライブラリ。

**説明**:
多次元配列とベクトル化演算を提供。
高速な数値計算を可能にする。

**本プロジェクトでの用途**:
- リスク指標の計算
- ベクトル化演算によるパフォーマンス最適化

**公式サイト**: https://numpy.org/

**バージョン**: >=1.26

**英語表記**: NumPy

---

### scipy

**定義**: Python の科学計算ライブラリ。

**説明**:
統計、最適化、信号処理などの機能を提供。

**本プロジェクトでの用途**:
- VaR 計算（正規分布のパーセンタイル）
- 統計検定

**公式サイト**: https://scipy.org/

**バージョン**: >=1.11

**英語表記**: SciPy

---

### Plotly

**定義**: インタラクティブなチャート生成ライブラリ。

**説明**:
Webベースのインタラクティブな可視化を提供。
marimo ノートブックとの連携が容易。

**本プロジェクトでの用途**:
- 資産配分の円グラフ・棒グラフ
- 配分ドリフトの可視化
- リスク指標のチャート

**公式サイト**: https://plotly.com/python/

**バージョン**: >=5.18

**英語表記**: Plotly

---

### Hypothesis

**定義**: Python のプロパティベーステストライブラリ。

**説明**:
ランダムなテストデータを生成し、プロパティ（不変条件）をテストする。
エッジケースの自動検出に優れている。

**本プロジェクトでの用途**:
- リスク指標の境界値テスト
- 配分正規化の不変条件テスト

**公式サイト**: https://hypothesis.readthedocs.io/

**バージョン**: >=6.100

**英語表記**: Hypothesis

---

### dataclass

**定義**: Python のデータクラスデコレータ。

**説明**:
クラス定義を簡潔にし、自動的に `__init__`、`__repr__`、`__eq__` などを生成。
`frozen=True` で不変オブジェクトを作成可能。

**本プロジェクトでの用途**:
- Holding、TickerInfo、Period などのデータ構造
- RiskMetricsResult、DriftResult などの結果型

**公式ドキュメント**: [dataclasses](https://docs.python.org/3/library/dataclasses.html)

**英語表記**: dataclass

---

### PEP 695

**定義**: Python 3.12 で導入された型パラメータ構文。

**説明**:
型エイリアスとジェネリクスの新しい構文を定義。
`type X = ...` 形式の型エイリアスを導入。

**本プロジェクトでの用途**:
- 型エイリアスの定義（AssetClass、PresetPeriod）
- ジェネリック関数の定義

**例**:
```python
type AssetClass = Literal["equity", "bond", "commodity", ...]
type PresetPeriod = Literal["1y", "3y", "5y", ...]
```

**公式ドキュメント**: [PEP 695](https://peps.python.org/pep-0695/)

**英語表記**: PEP 695 - Type Parameter Syntax

---

## 5. アーキテクチャ用語

システム設計に関する用語。

### レイヤードアーキテクチャ (Layered Architecture)

**定義**: システムを責務ごとに複数の層に分割する設計パターン。

**説明**:
上位レイヤーから下位レイヤーへの一方向の依存関係を持つ。
各レイヤーは特定の責務を担当し、関心の分離を実現。

**本プロジェクトでの適用**:

```
API Layer (Portfolio, __init__.py)
    ↓
Core Layer (risk/)
    ↓
Rebalance Layer (rebalance/)
    ↓
Provider Layer (providers/)

Visualization Layer (visualization/)
Output Layer (output/)
```

**各レイヤーの責務**:
- API Layer: 公開インターフェース、入力バリデーション
- Core Layer: リスク指標計算のビジネスロジック
- Rebalance Layer: リバランス分析ロジック
- Provider Layer: データソースの抽象化
- Visualization Layer: チャート生成
- Output Layer: 出力フォーマット変換

**関連用語**: [依存性逆転](#依存性逆転-dependency-inversion)

**英語表記**: Layered Architecture

---

### 依存性逆転 (Dependency Inversion)

**定義**: 高レベルモジュールが低レベルモジュールに依存せず、両者が抽象に依存する設計原則。

**説明**:
strategy パッケージでは DataProvider プロトコルを介して
データソースを抽象化し、依存性逆転を実現。

**本プロジェクトでの適用**:
- Portfolio は DataProvider プロトコルに依存
- MarketAnalysisProvider、MockProvider は DataProvider を実装
- 具体的なデータソースへの依存を排除

**関連用語**: [Protocol](#protocol), [DataProvider](#dataprovider)

**英語表記**: Dependency Inversion Principle (DIP)

---

### 疎結合 (Loose Coupling)

**定義**: コンポーネント間の依存関係を最小限に抑える設計方針。

**説明**:
strategy パッケージは market_analysis パッケージと
インターフェース（Protocol）経由で疎結合を維持。
データソースの変更が strategy パッケージに影響しない。

**本プロジェクトでの適用**:
- DataProvider プロトコルによるデータソース抽象化
- market_analysis への直接依存を MarketAnalysisProvider に限定

**関連用語**: [DataProvider](#dataprovider)

**英語表記**: Loose Coupling

---

## 6. 略語・頭字語

### API

**正式名称**: Application Programming Interface

**意味**: ソフトウェアコンポーネント間のインターフェース仕様。

**本プロジェクトでの使用**:
- 公開 API: Portfolio、Rebalancer などの公開クラス
- 外部 API: yfinance、FRED などのデータソース

---

### ETF

**正式名称**: Exchange Traded Fund

**意味**: 上場投資信託。証券取引所で株式のように取引できる投資信託。

**本プロジェクトでの使用**:
- VOO（Vanguard S&P 500 ETF）などのサンプル銘柄

---

### MDD

**正式名称**: Maximum Drawdown

**意味**: 最大ドローダウン。期間内の最大下落幅。

**関連用語**: [最大ドローダウン](#最大ドローダウン-maximum-drawdown--mdd)

---

### MVI

**正式名称**: Minimum Viable Implementation

**意味**: 最小限の実行可能な実装。機能の最初のリリース範囲。

**本プロジェクトでの使用**:
- P0（MVI）: 初期リリースに含める機能
- P1: MVI 後の重要機能
- P2（Post-MVI）: 将来的な拡張機能

---

### OHLCV

**正式名称**: Open, High, Low, Close, Volume

**意味**: 株価データの5つの基本要素（始値、高値、安値、終値、出来高）。

**本プロジェクトでの使用**:
- DataProvider の get_prices が返す DataFrame の構造

---

### TDD

**正式名称**: Test-Driven Development

**意味**: テスト駆動開発。テストを先に書いてから実装を行う開発手法。

**本プロジェクトでの適用**:
strategy パッケージの開発は TDD 必須。Red-Green-Refactor サイクルに従う。

**手順**:
1. Red: 失敗するテストを書く
2. Green: テストが通る最小限の実装
3. Refactor: コードの品質を改善

---

### VaR

**正式名称**: Value at Risk

**意味**: 特定の信頼水準での最大予想損失額。

**関連用語**: [VaR (Value at Risk)](#var-value-at-risk)

---

### YTD

**正式名称**: Year To Date

**意味**: 年初来。年の初めから現在までの期間。

**本プロジェクトでの使用**:
- PresetPeriod の一つとして `"ytd"` を提供

---

## 7. エラー・例外

### StrategyError

**クラス名**: `StrategyError`

**継承元**: `Exception`

**発生条件**: strategy パッケージ内で発生する全エラーの基底クラス。

**対処方法**:
- ユーザー: 派生エラーの種類を確認し、具体的な対処を行う
- 開発者: 適切な派生エラーを使用する

**実装箇所**: `src/strategy/errors.py`

---

### DataProviderError

**クラス名**: `DataProviderError`

**継承元**: `StrategyError`

**発生条件**: データプロバイダーからのデータ取得に失敗した場合。

**エラーメッセージフォーマット**:
```
Failed to fetch data: {cause}. Please check your network connection or try again later.
```

**対処方法**:
- ユーザー: ネットワーク接続を確認、時間をおいて再試行
- 開発者: リトライロジックの確認

**実装箇所**: `src/strategy/errors.py`

---

### InvalidTickerError

**クラス名**: `InvalidTickerError`

**継承元**: `StrategyError`

**発生条件**: 無効なティッカーシンボルが指定された場合。

**エラーメッセージフォーマット**:
```
Invalid ticker symbol: '{ticker}'. Please check the symbol format.
```

**対処方法**:
- ユーザー: ティッカーシンボルのスペルを確認
- 開発者: 入力バリデーションを確認

**実装箇所**: `src/strategy/errors.py`

---

### InsufficientDataError

**クラス名**: `InsufficientDataError`

**継承元**: `StrategyError`

**発生条件**: 指定期間に十分なデータがない場合。

**エラーメッセージフォーマット**:
```
Warning: Only {available_days} days of data available for {ticker}. Using maximum available period.
```

**対処方法**:
- ユーザー: より短い期間を指定、または警告を許容
- 開発者: 利用可能なデータ範囲を事前確認

**実装箇所**: `src/strategy/errors.py`

---

### ConfigurationError

**クラス名**: `ConfigurationError`

**継承元**: `StrategyError`

**発生条件**: 必要な設定が不足している場合（例: Provider 未設定）。

**エラーメッセージフォーマット**:
```
Provider not set. Call set_provider() before analysis.
```

**対処方法**:
- ユーザー: エラーメッセージに従って設定を行う
- 開発者: 設定チェックロジックを確認

**実装箇所**: `src/strategy/errors.py`

---

### ValidationError

**クラス名**: `ValidationError`

**継承元**: `StrategyError`

**発生条件**: 入力パラメータがバリデーションに失敗した場合。

**エラーメッセージフォーマット**:
```
{field}: {message}
例: Weight for 'VOO' must be between 0.0 and 1.0, got 1.5
```

**対処方法**:
- ユーザー: エラーメッセージに従って入力を修正
- 開発者: バリデーションルールを確認

**実装箇所**: `src/strategy/errors.py`

---

## 8. 索引

### あ行

- [アーキテクチャ用語](#5-アーキテクチャ用語) - システム設計
- [閾値](#閾値-threshold) - リバランス用語
- [閾値リバランス](#閾値リバランス-threshold-rebalancing) - リバランス用語

### か行

- [下方偏差](#下方偏差-downside-deviation) - リスク指標
- [配分ドリフト](#配分ドリフト-drift) - リバランス用語

### さ行

- [シャープレシオ](#シャープレシオ-sharpe-ratio) - リスク指標
- [情報レシオ](#情報レシオ-information-ratio) - リスク指標
- [資産クラス](#資産クラス-asset-class) - ドメイン用語
- [正規化](#正規化-normalization) - ドメイン用語（配分比率参照）
- [セクター](#セクター-sector) - ドメイン用語
- [ソルティノレシオ](#ソルティノレシオ-sortino-ratio) - リスク指標
- [疎結合](#疎結合-loose-coupling) - アーキテクチャ用語

### た行

- [定期リバランス](#定期リバランス-periodic-rebalancing) - リバランス用語
- [ティッカー](#ティッカー-ticker) - ドメイン用語
- [トレイナーレシオ](#トレイナーレシオ-treynor-ratio) - リスク指標
- [ドローダウン](#ドローダウン-drawdown) - リスク指標

### な行

- [年率化](#年率化-annualization) - リスク指標
- [年率化係数](#年率化係数-annualization-factor) - リスク指標

### は行

- [配分比率](#配分比率-weight) - ドメイン用語
- [ベータ](#ベータ-beta) - リスク指標
- [ベンチマーク](#ベンチマーク-benchmark) - リスク指標
- [ボラティリティ](#ボラティリティ-volatility) - リスク指標
- [ポートフォリオ](#ポートフォリオ-portfolio) - ドメイン用語

### ま行

- [最大ドローダウン](#最大ドローダウン-maximum-drawdown--mdd) - リスク指標

### ら行

- [リスクフリーレート](#リスクフリーレート-risk-free-rate) - リスク指標
- [リバランス](#リバランス-rebalancing) - リバランス用語
- [リバランスコスト](#リバランスコスト-rebalance-cost) - リバランス用語
- [レイヤードアーキテクチャ](#レイヤードアーキテクチャ-layered-architecture) - アーキテクチャ用語

### A-Z

- [API](#api) - 略語
- [dataclass](#dataclass) - 技術用語
- [DataProvider](#dataprovider) - 技術用語
- [ETF](#etf) - 略語
- [Holding](#holding-保有銘柄) - ドメイン用語
- [Hypothesis](#hypothesis) - 技術用語
- [MarketAnalysisProvider](#marketanalysisprovider) - 技術用語
- [market_analysis](#market_analysis) - 技術用語
- [MDD](#mdd) - 略語
- [MockProvider](#mockprovider) - 技術用語
- [MVI](#mvi) - 略語
- [numpy](#numpy) - 技術用語
- [OHLCV](#ohlcv) - 略語
- [pandas](#pandas) - 技術用語
- [PEP 695](#pep-695) - 技術用語
- [Period](#分析期間-period) - ドメイン用語
- [Plotly](#plotly) - 技術用語
- [PresetPeriod](#presetperiod-プリセット期間) - ドメイン用語
- [Protocol](#protocol) - 技術用語
- [scipy](#scipy) - 技術用語
- [TDD](#tdd) - 略語
- [TickerInfo](#tickerinfo-銘柄情報) - ドメイン用語
- [VaR](#var) - 略語
- [VaR (Value at Risk)](#var-value-at-risk) - リスク指標
- [YTD](#ytd) - 略語

---

## 変更履歴

| 日付 | 変更内容 | 変更者 |
|------|----------|--------|
| 2026-01-14 | 初版作成 | Claude Code |
