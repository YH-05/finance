# 用語集 (Glossary)

## 概要

このドキュメントは、factor パッケージで使用される用語の定義を管理します。
ファクター投資の専門用語、ライブラリ固有の概念、技術用語を体系的に整理しています。

**更新日**: 2026-01-14

---

## 1. ファクター投資関連用語

ファクター投資における専門用語と統計指標の定義。

### ファクター (Factor)

**定義**: 株式リターンを説明・予測する特性や指標

**説明**:
ファクターは、銘柄間のリターン差異を説明する変数です。
学術研究で有効性が確認されたファクター（モメンタム、バリュー、クオリティ等）を
投資戦略に活用することで、市場平均を上回るリターンの獲得を目指します。

**関連用語**: [ファクター値](#ファクター値-factor-value), [ファクターエクスポージャー](#ファクターエクスポージャー-factor-exposure), [ファクタープレミアム](#ファクタープレミアム-factor-premium)

**使用例**:
- 「モメンタムファクターで銘柄をスクリーニングする」
- 「複数ファクターを組み合わせたマルチファクター戦略」

**英語表記**: Factor

---

### ファクター値 (Factor Value)

**定義**: 特定の日付における各銘柄のファクター指標の数値

**説明**:
ファクター値は DataFrame 形式で表現され、行が日付、列が銘柄シンボルとなります。
正規化前の生の値と、正規化後の値の両方を扱います。

**データ構造**:
```
           AAPL    GOOGL    MSFT
2024-01-01  0.15    0.08    0.12
2024-01-02  0.14    0.09    0.11
```

**関連用語**: [正規化](#正規化-normalization), [クロスセクショナル](#クロスセクショナル-cross-sectional)

**実装箇所**: `src/factor/types.py` - `FactorValue` データクラス

**英語表記**: Factor Value

---

### IC (Information Coefficient / 情報係数)

**定義**: ファクター値とフォワードリターンの相関係数

**説明**:
IC はファクターの予測力を測定する指標です。
ファクター値が高い銘柄が実際に高いリターンを達成しているかを評価します。
一般的に Spearman（ランク相関）が使用されます。

**計算式**:
```
IC_t = corr(Factor_t, Return_{t+1})
```

**解釈**:
- IC > 0: ファクター値が高い銘柄は高いリターンを達成
- IC < 0: ファクター値が高い銘柄は低いリターンを達成
- |IC| が大きいほど予測力が高い

**目安**:
| IC値 | 評価 |
|------|------|
| > 0.10 | 非常に強い |
| 0.05 - 0.10 | 強い |
| 0.03 - 0.05 | 中程度 |
| < 0.03 | 弱い |

**関連用語**: [IR](#ir-information-ratio--情報比率), [Spearman相関](#spearman相関-spearman-correlation), [Pearson相関](#pearson相関-pearson-correlation)

**実装箇所**: `src/factor/validation/ic_analyzer.py`

**英語表記**: Information Coefficient

---

### IR (Information Ratio / 情報比率)

**定義**: IC の平均値を IC の標準偏差で割った比率

**説明**:
IR はファクターの予測力の安定性を測定します。
IC が高くても不安定であれば実用性が低いため、
IC の平均だけでなく IR も重要な評価指標となります。

**計算式**:
```
IR = Mean(IC) / Std(IC)
```

**解釈**:
- IR > 0.5: 非常に安定した予測力
- IR 0.3 - 0.5: 安定した予測力
- IR < 0.3: 不安定

**関連用語**: [IC](#ic-information-coefficient--情報係数), [t値](#t値-t-statistic)

**実装箇所**: `src/factor/validation/ic_analyzer.py` - `ICResult.ir`

**英語表記**: Information Ratio

---

### 分位分析 (Quantile Analysis)

**定義**: ファクター値に基づいて銘柄を分位（グループ）に分け、各分位のリターンを比較する分析手法

**説明**:
ファクター値で銘柄をN分位（通常5分位）に分け、
各分位のリターンを比較することで、ファクターの単調性を評価します。
理想的なファクターは、第1分位から第N分位まで
リターンが単調に増加（または減少）します。

**分析項目**:
1. 分位別平均リターン
2. Long-Short リターン（Top - Bottom）
3. 単調性スコア

**図解**:
```
         分位別リターン
  Q1     Q2     Q3     Q4     Q5
 -2%    -1%     0%    +1%    +3%   <- 単調増加（良いファクター）
```

**関連用語**: [Long-Shortリターン](#long-shortリターン-long-short-return), [単調性](#単調性-monotonicity)

**実装箇所**: `src/factor/validation/quantile_analyzer.py`

**英語表記**: Quantile Analysis

---

### Long-Shortリターン (Long-Short Return)

**定義**: 最上位分位（Long）と最下位分位（Short）のリターン差

**説明**:
Long-Short リターンは、ファクターの有効性を示す最も直感的な指標です。
最上位分位の銘柄をロング（買い）、最下位分位の銘柄をショート（売り）
したポートフォリオの期待リターンを表します。

**計算式**:
```
Long-Short Return = Return(Q_n) - Return(Q_1)
```

**関連用語**: [分位分析](#分位分析-quantile-analysis), [ファクタープレミアム](#ファクタープレミアム-factor-premium)

**英語表記**: Long-Short Return

---

### 単調性 (Monotonicity)

**定義**: 分位間でリターンが一貫して増加または減少する性質

**説明**:
単調性スコアは 0 から 1 の値を取り、1 に近いほど
分位間のリターンが単調に変化していることを示します。
単調性が高いファクターは、実運用での信頼性が高いとされます。

**関連用語**: [分位分析](#分位分析-quantile-analysis)

**英語表記**: Monotonicity

---

### フォワードリターン (Forward Return)

**定義**: 現時点から将来の一定期間後のリターン

**説明**:
ファクター値の予測力を評価するために、
ファクター計算時点から将来のリターンを計算します。
一般的に 1 日、5 日、21 日（1 ヶ月）後のリターンが使用されます。

**計算式**:
```
Forward Return_t = P_{t+n} / P_t - 1
```

**注意点**:
- ルックアヘッドバイアスを避けるため、ファクター計算時点より後のデータを使用
- バックテストでは将来データへのアクセスがないことを前提に設計

**関連用語**: [IC](#ic-information-coefficient--情報係数), [ルックアヘッドバイアス](#ルックアヘッドバイアス-look-ahead-bias)

**英語表記**: Forward Return

---

### ルックバック期間 (Lookback Period)

**定義**: ファクター計算に使用する過去データの期間

**説明**:
モメンタムファクターの場合、252 日（約 1 年）のルックバック期間が一般的です。
ルックバック期間が長いほど安定した値が得られますが、
市場環境の変化への反応が遅くなります。

**使用例**:
- モメンタム: 252 日（12 ヶ月）
- 短期リバーサル: 5 日（1 週間）
- ボラティリティ: 20 日（1 ヶ月）

**関連用語**: [モメンタム](#モメンタム-momentum), [ボラティリティ](#ボラティリティ-volatility)

**英語表記**: Lookback Period

---

### モメンタム (Momentum)

**定義**: 過去のリターンが将来のリターンを予測するという現象、またはそれに基づくファクター

**説明**:
過去に上昇した銘柄は引き続き上昇する傾向があり、
過去に下落した銘柄は引き続き下落する傾向があるという
市場のアノマリー（異常現象）に基づいたファクターです。

**計算式**:
```
Momentum = P_{t-skip} / P_{t-lookback} - 1
```

**パラメータ**:
- `lookback`: ルックバック期間（デフォルト: 252 日）
- `skip_recent`: 直近除外期間（デフォルト: 21 日）- リバーサル効果を除去

**関連用語**: [リバーサル](#リバーサル-reversal), [ルックバック期間](#ルックバック期間-lookback-period)

**実装箇所**: `src/factor/factors/price/momentum.py`

**英語表記**: Momentum

---

### リバーサル (Reversal)

**定義**: 短期的に下落した銘柄が反発する現象、またはそれに基づくファクター

**説明**:
短期リバーサルは、数日間で大きく下落した銘柄が
短期的に反発する傾向を利用したファクターです。
モメンタムとは逆の概念です。

**計算式**:
```
Reversal = -(P_t / P_{t-lookback} - 1)
```
※符号を反転して、下落した銘柄が高スコアになる

**関連用語**: [モメンタム](#モメンタム-momentum)

**実装箇所**: `src/factor/factors/price/reversal.py`

**英語表記**: Reversal

---

### ボラティリティ (Volatility)

**定義**: リターンの変動の大きさを示す指標

**説明**:
一般的にリターンの標準偏差で計測します。
低ボラティリティ銘柄がリスク調整後で高いリターンを示す
「低ボラティリティアノマリー」が知られています。

**計算式**:
```
Volatility = std(Returns) * sqrt(252)  # 年率換算
```

**関連用語**: [標準偏差](#標準偏差-standard-deviation)

**実装箇所**: `src/factor/factors/price/volatility.py`

**英語表記**: Volatility

---

### バリュー (Value)

**定義**: 株価に対して割安な銘柄を選好するファクター

**説明**:
PER（株価収益率）、PBR（株価純資産倍率）、配当利回り等の
バリュエーション指標を使用して、
本質的価値に対して株価が割安な銘柄を特定します。

**指標**:
- PER (Price Earnings Ratio): 株価 / EPS
- PBR (Price Book Ratio): 株価 / BPS
- 配当利回り (Dividend Yield): 配当 / 株価
- EV/EBITDA: 企業価値 / EBITDA

**関連用語**: [PER](#per-price-earnings-ratio--株価収益率), [PBR](#pbr-price-book-ratio--株価純資産倍率)

**実装箇所**: `src/factor/factors/value/value.py`

**英語表記**: Value

---

### クオリティ (Quality)

**定義**: 財務的に健全で高品質な企業を選好するファクター

**説明**:
収益性、安定性、財務健全性などの指標を使用して、
経営の質が高い企業を特定します。

**指標**:
- ROE (Return on Equity): 自己資本利益率
- ROA (Return on Assets): 総資産利益率
- 利益の安定性: 収益のボラティリティ
- 負債比率: 負債 / 資本

**関連用語**: [ROE](#roe-return-on-equity--自己資本利益率), [ROA](#roa-return-on-assets--総資産利益率)

**実装箇所**: `src/factor/factors/quality/quality.py`

**英語表記**: Quality

---

### サイズ (Size)

**定義**: 企業規模に基づくファクター

**説明**:
小型株が大型株よりも高いリターンを示す傾向（小型株効果）に
基づいたファクターです。時価総額を対数変換して使用することが一般的です。

**指標**:
- 時価総額 (Market Cap): 株価 * 発行済株式数
- 売上高 (Revenue)
- 総資産 (Total Assets)

**注意点**:
- `invert=True` で小型株プレミアムを狙う（符号反転）
- 対数変換で右に歪んだ分布を正規化

**実装箇所**: `src/factor/factors/size/size.py`

**英語表記**: Size

---

### PER (Price Earnings Ratio / 株価収益率)

**定義**: 株価を 1 株当たり利益（EPS）で割った比率

**計算式**:
```
PER = 株価 / EPS
```

**解釈**:
- 低 PER: 利益に対して株価が割安
- 高 PER: 利益に対して株価が割高、または成長期待

**関連用語**: [バリュー](#バリュー-value), [PBR](#pbr-price-book-ratio--株価純資産倍率)

**英語表記**: Price Earnings Ratio, P/E Ratio

---

### PBR (Price Book Ratio / 株価純資産倍率)

**定義**: 株価を 1 株当たり純資産（BPS）で割った比率

**計算式**:
```
PBR = 株価 / BPS
```

**解釈**:
- PBR < 1: 解散価値より株価が安い
- PBR > 1: 無形資産や将来の成長を織り込んでいる

**関連用語**: [バリュー](#バリュー-value), [PER](#per-price-earnings-ratio--株価収益率)

**英語表記**: Price Book Ratio, P/B Ratio

---

### ROE (Return on Equity / 自己資本利益率)

**定義**: 自己資本に対する純利益の比率

**計算式**:
```
ROE = 純利益 / 自己資本
```

**解釈**:
- 高 ROE: 株主資本を効率的に活用して利益を上げている
- 一般的に 10% 以上が優良とされる

**関連用語**: [クオリティ](#クオリティ-quality), [ROA](#roa-return-on-assets--総資産利益率)

**英語表記**: Return on Equity

---

### ROA (Return on Assets / 総資産利益率)

**定義**: 総資産に対する純利益の比率

**計算式**:
```
ROA = 純利益 / 総資産
```

**解釈**:
- 高 ROA: 資産を効率的に活用して利益を上げている
- 業種により適切な水準が異なる

**関連用語**: [クオリティ](#クオリティ-quality), [ROE](#roe-return-on-equity--自己資本利益率)

**英語表記**: Return on Assets

---

### ファクターエクスポージャー (Factor Exposure)

**定義**: ポートフォリオや銘柄が特定のファクターにどの程度さらされているか

**説明**:
例えば、小型株に集中したポートフォリオはサイズファクターへの
エクスポージャーが高いと言えます。
ファクターエクスポージャーを管理することで、
意図したリスク・リターン特性を実現できます。

**関連用語**: [ファクター](#ファクター-factor)

**英語表記**: Factor Exposure

---

### ファクタープレミアム (Factor Premium)

**定義**: 特定のファクターへのエクスポージャーから得られる期待超過リターン

**説明**:
学術研究で確認されたファクター（バリュー、モメンタム等）は、
長期的に市場平均を上回るリターン（プレミアム）を
提供する傾向があります。

**関連用語**: [ファクター](#ファクター-factor), [Long-Shortリターン](#long-shortリターン-long-short-return)

**英語表記**: Factor Premium

---

### クロスセクショナル (Cross-Sectional)

**定義**: 特定の時点における複数銘柄間の比較

**説明**:
クロスセクショナル分析では、同一時点での銘柄間の
ファクター値やリターンを比較します。
これに対し、時系列分析は同一銘柄の時間的変化を分析します。

**使用例**:
- クロスセクショナル正規化: 各日付で銘柄間の相対的な位置を計算
- クロスセクショナル回帰: 同一時点でのファクターとリターンの関係を分析

**関連用語**: [正規化](#正規化-normalization)

**英語表記**: Cross-Sectional

---

### 正規化 (Normalization)

**定義**: ファクター値を比較可能な形式に変換する処理

**説明**:
異なるファクター間、または異なる時点間で値を比較するために、
ファクター値を標準化します。

**手法**:
1. **Z-score**: 平均 0、標準偏差 1 に変換
2. **ランク**: パーセンタイル（0-1）に変換
3. **Winsorization**: 外れ値をクリップ

**関連用語**: [Z-score正規化](#z-score正規化-z-score-normalization), [Winsorization](#winsorization-ウィンソライゼーション)

**実装箇所**: `src/factor/core/normalizer.py`

**英語表記**: Normalization

---

### Z-score正規化 (Z-score Normalization)

**定義**: 値を平均 0、標準偏差 1 に変換する正規化手法

**計算式**:
```
Z = (X - mean(X)) / std(X)
```

**使用例**:
```python
from factor import Normalizer

normalized = Normalizer.zscore(factor_values, axis="cross_sectional")
# 各日付で銘柄間の平均0、標準偏差1に正規化
```

**関連用語**: [正規化](#正規化-normalization), [ランク正規化](#ランク正規化-rank-normalization)

**実装箇所**: `src/factor/core/normalizer.py` - `Normalizer.zscore()`

**英語表記**: Z-score Normalization

---

### ランク正規化 (Rank Normalization)

**定義**: 値を順位に基づいてパーセンタイルに変換する正規化手法

**説明**:
外れ値の影響を受けにくく、非線形な関係も捉えられます。
0 から 1 の範囲の値に変換されます。

**関連用語**: [正規化](#正規化-normalization), [Z-score正規化](#z-score正規化-z-score-normalization)

**実装箇所**: `src/factor/core/normalizer.py` - `Normalizer.rank()`

**英語表記**: Rank Normalization

---

### Winsorization (ウィンソライゼーション)

**定義**: 外れ値を特定のパーセンタイルでクリップする処理

**説明**:
極端な外れ値が分析結果に与える影響を軽減します。
一般的に 1% と 99% パーセンタイルでクリップします。

**計算式**:
```
X_winsorized = clip(X, percentile_1%, percentile_99%)
```

**関連用語**: [正規化](#正規化-normalization)

**実装箇所**: `src/factor/core/normalizer.py` - `Normalizer.winsorize()`

**英語表記**: Winsorization

---

### Spearman相関 (Spearman Correlation)

**定義**: 順位に基づく相関係数

**説明**:
Spearman 相関は値の順位を使って相関を計算するため、
外れ値の影響を受けにくく、非線形な関係も捉えられます。
IC 計算ではデフォルトで Spearman 相関を使用します。

**関連用語**: [IC](#ic-information-coefficient--情報係数), [Pearson相関](#pearson相関-pearson-correlation)

**英語表記**: Spearman Correlation, Rank Correlation

---

### Pearson相関 (Pearson Correlation)

**定義**: 線形相関係数

**説明**:
Pearson 相関は値の線形関係を測定します。
外れ値の影響を受けやすいため、正規化後のデータに対して使用することが推奨されます。

**関連用語**: [IC](#ic-information-coefficient--情報係数), [Spearman相関](#spearman相関-spearman-correlation)

**英語表記**: Pearson Correlation

---

### t値 (t-statistic)

**定義**: IC の統計的有意性を示す検定統計量

**説明**:
IC が偶然ではなく、統計的に有意であるかを判断するために使用します。
|t| > 2 であれば、95% 信頼水準で有意と判断できます。

**計算式**:
```
t = mean(IC) / (std(IC) / sqrt(n))
```

**関連用語**: [IC](#ic-information-coefficient--情報係数), [p値](#p値-p-value)

**英語表記**: t-statistic

---

### p値 (p-value)

**定義**: IC がゼロであるという帰無仮説が正しい確率

**説明**:
p < 0.05 であれば、95% 信頼水準でファクターの予測力が
統計的に有意であると判断できます。

**関連用語**: [t値](#t値-t-statistic), [IC](#ic-information-coefficient--情報係数)

**英語表記**: p-value

---

### ルックアヘッドバイアス (Look-Ahead Bias)

**定義**: バックテストにおいて、その時点では利用できなかった将来の情報を使用してしまう誤り

**説明**:
ルックアヘッドバイアスを含むバックテストは、
実運用では再現できない過大なパフォーマンスを示します。
ファクター計算では、計算時点で利用可能なデータのみを使用することが重要です。

**回避方法**:
- フォワードリターンは t+1 以降のデータを使用
- 財務データは公表日以降のみ使用

**関連用語**: [フォワードリターン](#フォワードリターン-forward-return)

**英語表記**: Look-Ahead Bias

---

### ユニバース (Universe)

**定義**: 分析・投資の対象となる銘柄の集合

**説明**:
ファクター分析はユニバース内の銘柄に対して行われます。
ユニバースの選定は分析結果に大きく影響するため、
投資戦略に適したユニバースを定義することが重要です。

**使用例**:
```python
universe = ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA"]
factor_values = momentum.compute(provider, universe, start_date, end_date)
```

**英語表記**: Universe

---

## 2. ライブラリ固有用語

factor パッケージで定義されたクラス、インターフェース、概念の用語。

### Factor 基底クラス

**定義**: 全てのファクターが継承する抽象基底クラス

**説明**:
`Factor` クラスはファクター計算の共通インターフェースを定義します。
カスタムファクターを作成する場合は、このクラスを継承して
`compute()` メソッドを実装します。

**主要属性**:
- `name`: ファクター名
- `description`: ファクターの説明
- `category`: ファクターカテゴリ（PRICE, VALUE, QUALITY, SIZE）

**主要メソッド**:
- `compute()`: ファクター値を計算
- `validate_inputs()`: 入力パラメータを検証

**使用例**:
```python
from factor import Factor
from factor.types import FactorCategory

class MyFactor(Factor):
    name = "my_factor"
    description = "カスタムファクター"
    category = FactorCategory.PRICE

    def compute(self, provider, universe, start_date, end_date):
        prices = provider.get_prices(universe, start_date, end_date)
        return prices.pct_change(20)
```

**実装箇所**: `src/factor/core/base.py`

**関連用語**: [FactorCategory](#factorcategory), [DataProvider](#dataprovider)

---

### DataProvider

**定義**: データ取得を抽象化する Protocol（インターフェース）

**説明**:
`DataProvider` Protocol は、任意のデータソースから
価格データ、財務データ等を取得するための
統一されたインターフェースを定義します。
これにより、データソースを切り替えても
ファクター計算コードを変更する必要がありません。

**必須メソッド**:
- `get_prices()`: 終値データを取得
- `get_volumes()`: 出来高データを取得
- `get_fundamentals()`: 財務データを取得
- `get_market_cap()`: 時価総額データを取得

**実装クラス**:
- `YFinanceProvider`: yfinance を使用した実装

**実装箇所**: `src/factor/providers/base.py`

**関連用語**: [YFinanceProvider](#yfinanceprovider), [Protocol](#protocol-プロトコル)

---

### YFinanceProvider

**定義**: yfinance ライブラリを使用した DataProvider の実装

**説明**:
Yahoo Finance からデータを取得する DataProvider の具体的な実装です。
キャッシュ機能とリトライ機能を備えています。

**パラメータ**:
- `cache_path`: キャッシュファイルの保存先
- `cache_ttl_hours`: キャッシュの有効期間（時間）

**使用例**:
```python
from factor.providers import YFinanceProvider

provider = YFinanceProvider(cache_ttl_hours=24)
prices = provider.get_prices(
    symbols=["AAPL", "GOOGL"],
    start_date="2020-01-01",
    end_date="2024-01-01",
)
```

**実装箇所**: `src/factor/providers/yfinance.py`

**関連用語**: [DataProvider](#dataprovider)

---

### Normalizer

**定義**: ファクター値の正規化処理を提供するクラス

**説明**:
ファクター値をクロスセクショナルに正規化するための
静的メソッドを提供します。

**メソッド**:
- `zscore()`: Z-score 正規化
- `rank()`: ランク正規化
- `winsorize()`: 外れ値処理

**使用例**:
```python
from factor import Normalizer

normalized = Normalizer.zscore(factor_values, axis="cross_sectional")
ranked = Normalizer.rank(factor_values, pct=True)
clipped = Normalizer.winsorize(factor_values, limits=(0.01, 0.99))
```

**実装箇所**: `src/factor/core/normalizer.py`

**関連用語**: [正規化](#正規化-normalization)

---

### ICAnalyzer

**定義**: IC/IR 分析を実行するクラス

**説明**:
ファクター値とフォワードリターンの相関（IC）を計算し、
統計的有意性を検定します。

**パラメータ**:
- `method`: 相関計算方法（"spearman" or "pearson"）

**メソッド**:
- `analyze()`: IC/IR 分析を実行し、`ICResult` を返す
- `compute_ic_series()`: 時系列 IC を計算
- `compute_forward_returns()`: フォワードリターンを計算

**使用例**:
```python
from factor.validation import ICAnalyzer

analyzer = ICAnalyzer(method="spearman")
result = analyzer.analyze(factor_values, forward_returns)
print(f"Mean IC: {result.mean_ic:.4f}, IR: {result.ir:.4f}")
```

**実装箇所**: `src/factor/validation/ic_analyzer.py`

**関連用語**: [IC](#ic-information-coefficient--情報係数), [IR](#ir-information-ratio--情報比率), [ICResult](#icresult)

---

### QuantileAnalyzer

**定義**: 分位分析を実行するクラス

**説明**:
ファクター値に基づいて銘柄を分位に分け、
各分位のリターンを分析します。

**パラメータ**:
- `n_quantiles`: 分位数（デフォルト: 5）

**メソッド**:
- `analyze()`: 分位分析を実行し、`QuantileResult` を返す
- `assign_quantiles()`: ファクター値を分位に割り当て
- `compute_quantile_returns()`: 分位別リターンを計算
- `plot()`: 分析結果を可視化

**使用例**:
```python
from factor.validation import QuantileAnalyzer

analyzer = QuantileAnalyzer(n_quantiles=5)
result = analyzer.analyze(factor_values, forward_returns)
print(f"Long-Short Return: {result.long_short_return:.4f}")
analyzer.plot(result)
```

**実装箇所**: `src/factor/validation/quantile_analyzer.py`

**関連用語**: [分位分析](#分位分析-quantile-analysis), [QuantileResult](#quantileresult)

---

### FactorCategory

**定義**: ファクターの分類を表す列挙型

**説明**:
ファクターを種類別に分類するための Enum です。
将来的なファクターカテゴリの拡張にも対応しています。

**値**:
| 値 | 説明 | 主要ファクター |
|----|------|---------------|
| `PRICE` | 価格ベース | モメンタム、リバーサル、ボラティリティ |
| `VALUE` | バリュー | PER、PBR、配当利回り |
| `QUALITY` | クオリティ | ROE、ROA、利益安定性 |
| `SIZE` | サイズ | 時価総額 |
| `MACRO` | マクロ経済（将来対応） | 金利感応度、インフレ感応度 |
| `ALTERNATIVE` | オルタナティブ（将来対応） | センチメント |

**実装箇所**: `src/factor/types.py`

---

### FactorMetadata

**定義**: ファクターのメタデータを格納するデータクラス

**説明**:
ファクターの名前、説明、必要なデータ種別、計算頻度などの
メタ情報を管理します。

**属性**:
- `name`: ファクター名
- `description`: 説明
- `category`: ファクターカテゴリ
- `required_data`: 必要なデータ種別（例: ["price", "volume"]）
- `frequency`: 計算頻度（daily, weekly, monthly, quarterly）
- `lookback_period`: ルックバック期間
- `higher_is_better`: 高い値が良いか
- `default_parameters`: デフォルトパラメータ

**実装箇所**: `src/factor/types.py`

---

### FactorValue

**定義**: ファクター計算結果を格納するデータクラス

**説明**:
ファクター値の DataFrame と、計算に関するメタ情報を
まとめて管理します。

**属性**:
- `data`: ファクター値（DataFrame）
- `factor_name`: ファクター名
- `computed_at`: 計算日時
- `universe`: 対象銘柄リスト
- `start_date`: 開始日
- `end_date`: 終了日
- `parameters`: ファクターパラメータ

**実装箇所**: `src/factor/types.py`

---

### ICResult

**定義**: IC/IR 分析の結果を格納するデータクラス

**説明**:
`ICAnalyzer.analyze()` の戻り値として使用されます。

**属性**:
| 属性 | 型 | 説明 |
|------|-----|------|
| `ic_series` | pd.Series | 時系列 IC |
| `mean_ic` | float | 平均 IC |
| `std_ic` | float | IC 標準偏差 |
| `ir` | float | 情報比率 |
| `t_stat` | float | t 値 |
| `p_value` | float | p 値 |
| `method` | str | 計算方法 |
| `n_periods` | int | 分析期間数 |

**実装箇所**: `src/factor/types.py`

---

### QuantileResult

**定義**: 分位分析の結果を格納するデータクラス

**説明**:
`QuantileAnalyzer.analyze()` の戻り値として使用されます。

**属性**:
| 属性 | 型 | 説明 |
|------|-----|------|
| `quantile_returns` | pd.DataFrame | 分位別リターン |
| `mean_returns` | pd.Series | 分位別平均リターン |
| `long_short_return` | float | Long-Short リターン |
| `monotonicity_score` | float | 単調性スコア（0-1） |
| `n_quantiles` | int | 分位数 |
| `turnover` | pd.Series | 回転率（オプション） |

**実装箇所**: `src/factor/types.py`

---

### FactorError

**定義**: factor パッケージの基底エラークラス

**説明**:
全ての factor パッケージ固有のエラーが継承する基底クラスです。
エラーの種類に応じて派生クラスを使用します。

**派生クラス**:
| クラス | 発生条件 |
|--------|---------|
| `DataFetchError` | データ取得失敗 |
| `ValidationError` | 入力バリデーション失敗 |
| `ComputationError` | ファクター計算失敗 |
| `InsufficientDataError` | データ不足 |

**実装箇所**: `src/factor/errors.py`

---

### DataFetchError

**定義**: データ取得に失敗した場合のエラー

**説明**:
データプロバイダーからのデータ取得が失敗した場合にスローされます。
ネットワークエラー、API エラー、無効なシンボル等が原因となります。

**属性**:
- `symbols`: 取得に失敗した銘柄リスト
- `message`: エラーメッセージ

**使用例**:
```python
raise DataFetchError(
    symbols=["INVALID"],
    message="Failed to fetch data for ['INVALID']: Symbol not found",
)
```

**実装箇所**: `src/factor/errors.py`

---

### ValidationError

**定義**: 入力バリデーションに失敗した場合のエラー

**説明**:
ユーザー入力がビジネスルールに違反した場合にスローされます。

**属性**:
- `field`: エラーが発生したフィールド名
- `value`: 不正な値
- `message`: エラーメッセージ

**使用例**:
```python
raise ValidationError(
    field="lookback",
    value=-1,
    message="lookback must be positive, got -1",
)
```

**実装箇所**: `src/factor/errors.py`

---

### ComputationError

**定義**: ファクター計算に失敗した場合のエラー

**説明**:
数値計算の失敗、ゼロ除算等、計算処理中に発生するエラーです。

**属性**:
- `factor_name`: 失敗したファクターの名前
- `message`: エラーメッセージ

**実装箇所**: `src/factor/errors.py`

---

### InsufficientDataError

**定義**: データ不足の場合のエラー

**説明**:
ファクター計算に必要なデータ量が不足している場合にスローされます。
例えば、252 日のルックバック期間に対して 100 日分のデータしかない場合です。

**属性**:
- `required`: 必要なデータ点数
- `available`: 利用可能なデータ点数
- `message`: エラーメッセージ

**使用例**:
```python
raise InsufficientDataError(
    required=252,
    available=100,
    message="Momentum calculation requires 252 data points, but only 100 available",
)
```

**実装箇所**: `src/factor/errors.py`

---

## 3. 技術用語

プログラミング、Python、使用ライブラリに関する技術用語。

### Protocol (プロトコル)

**定義**: Python の構造的部分型を定義するための仕組み

**説明**:
Protocol を使用すると、明示的な継承なしに
「このメソッドを持っていればこの型として扱える」という
インターフェースを定義できます（ダックタイピングの型安全な実現）。

**本プロジェクトでの用途**:
`DataProvider` Protocol により、任意のデータソースを
統一的なインターフェースで扱えるようにしています。

**使用例**:
```python
from typing import Protocol

class DataProvider(Protocol):
    def get_prices(self, symbols: list[str], ...) -> pd.DataFrame: ...
```

**関連用語**: [DataProvider](#dataprovider), [ABC](#abc-abstract-base-class)

---

### ABC (Abstract Base Class)

**定義**: 抽象基底クラス。インスタンス化できず、継承して使用することを前提としたクラス

**説明**:
`@abstractmethod` デコレータを使用して、
サブクラスで必ず実装すべきメソッドを定義できます。

**本プロジェクトでの用途**:
`Factor` 基底クラスが ABC を継承しており、
全てのファクターが `compute()` メソッドを実装することを強制しています。

**使用例**:
```python
from abc import ABC, abstractmethod

class Factor(ABC):
    @abstractmethod
    def compute(self, ...) -> pd.DataFrame:
        ...
```

**関連用語**: [Factor 基底クラス](#factor-基底クラス)

---

### ベクトル化 (Vectorization)

**定義**: ループを使わず、配列全体に対して一括で演算を行う手法

**説明**:
pandas/numpy のベクトル化演算は、Python のループよりも
10-100 倍高速に動作します。factor パッケージでは、
パフォーマンス要件を満たすために全てのファクター計算で
ベクトル化を使用しています。

**悪い例（ループ）**:
```python
for i in range(len(prices)):
    for col in prices.columns:
        result.iloc[i, col] = prices.iloc[i, col] / prices.iloc[i - lookback, col] - 1
```

**良い例（ベクトル化）**:
```python
result = prices / prices.shift(lookback) - 1
```

**関連用語**: [pandas](#pandas), [numpy](#numpy)

---

### pandas

**定義**: Python のデータ分析ライブラリ

**公式サイト**: https://pandas.pydata.org/

**本プロジェクトでの用途**:
- ファクター値の格納（DataFrame）
- 時系列データの操作
- 正規化計算

**バージョン**: >=2.0

**関連用語**: [DataFrame](#dataframe), [ベクトル化](#ベクトル化-vectorization)

---

### numpy

**定義**: Python の数値計算ライブラリ

**公式サイト**: https://numpy.org/

**本プロジェクトでの用途**:
- 数値計算
- 統計関数
- pandas との連携

**バージョン**: >=1.26

**関連用語**: [ベクトル化](#ベクトル化-vectorization)

---

### scipy

**定義**: Python の科学技術計算ライブラリ

**公式サイト**: https://scipy.org/

**本プロジェクトでの用途**:
- IC 計算（相関係数: `scipy.stats.spearmanr`, `scipy.stats.pearsonr`）
- 統計検定（`scipy.stats.ttest_1samp`）

**バージョン**: >=1.11

**関連用語**: [IC](#ic-information-coefficient--情報係数), [t値](#t値-t-statistic)

---

### yfinance

**定義**: Yahoo Finance からデータを取得する Python ライブラリ

**公式サイト**: https://github.com/ranaroussi/yfinance

**本プロジェクトでの用途**:
- 株価データの取得
- 財務データの取得
- 時価総額データの取得

**バージョン**: >=0.2.36

**関連用語**: [YFinanceProvider](#yfinanceprovider)

---

### plotly

**定義**: インタラクティブなグラフを作成する Python ライブラリ

**公式サイト**: https://plotly.com/python/

**本プロジェクトでの用途**:
- 分位分析チャートの作成
- IC 推移グラフの作成

**バージョン**: >=5.18

---

### DataFrame

**定義**: pandas の 2 次元データ構造

**説明**:
行と列にラベルを持つテーブル形式のデータ構造です。
factor パッケージでは、ファクター値を格納するために使用します。

**ファクター値の DataFrame スキーマ**:
```
           AAPL    GOOGL    MSFT    <- columns: 銘柄シンボル
2024-01-01  0.15    0.08    0.12   <- index: 日付
2024-01-02  0.14    0.09    0.11      values: float64 (ファクター値)
```

**関連用語**: [pandas](#pandas)

---

### dataclass

**定義**: Python 3.7+ で導入されたデータ格納用クラスを簡潔に定義するデコレータ

**説明**:
`@dataclass` デコレータを使用すると、
`__init__`, `__repr__`, `__eq__` 等のボイラープレートコードを
自動生成できます。

**本プロジェクトでの用途**:
`FactorValue`, `ICResult`, `QuantileResult` 等の
結果データクラスに使用しています。

**使用例**:
```python
from dataclasses import dataclass

@dataclass
class ICResult:
    mean_ic: float
    std_ic: float
    ir: float
```

---

### 型ヒント (Type Hints)

**定義**: Python の変数、引数、戻り値の型を明示的に示す注釈

**説明**:
型ヒントにより、コードの可読性が向上し、
pyright 等の静的型チェッカーによるエラー検出が可能になります。

**本プロジェクトでの使用**:
Python 3.12+ スタイル（PEP 695）を採用しています。

**使用例**:
```python
def compute_ic(
    factor_values: pd.DataFrame,
    forward_returns: pd.DataFrame,
    method: str = "spearman",
) -> pd.Series:
    ...
```

---

### 標準偏差 (Standard Deviation)

**定義**: データの散らばりの度合いを示す統計量

**計算式**:
```
std = sqrt(sum((x - mean)^2) / n)
```

**本プロジェクトでの用途**:
- ボラティリティの計算
- Z-score 正規化
- IR の計算（IC の標準偏差）

**関連用語**: [ボラティリティ](#ボラティリティ-volatility), [Z-score正規化](#z-score正規化-z-score-normalization)

**英語表記**: Standard Deviation

---

## 4. 略語・頭字語一覧

| 略語 | 正式名称 | 説明 | 参照 |
|------|---------|------|------|
| ABC | Abstract Base Class | 抽象基底クラス | [ABC](#abc-abstract-base-class) |
| API | Application Programming Interface | プログラム間の通信インターフェース | - |
| BPS | Book-value Per Share | 1株当たり純資産 | [PBR](#pbr-price-book-ratio--株価純資産倍率) |
| EPS | Earnings Per Share | 1株当たり利益 | [PER](#per-price-earnings-ratio--株価収益率) |
| EV | Enterprise Value | 企業価値 | [バリュー](#バリュー-value) |
| EBITDA | Earnings Before Interest, Taxes, Depreciation and Amortization | 利払い・税引き・償却前利益 | [バリュー](#バリュー-value) |
| IC | Information Coefficient | 情報係数 | [IC](#ic-information-coefficient--情報係数) |
| IR | Information Ratio | 情報比率 | [IR](#ir-information-ratio--情報比率) |
| MVI | Minimum Viable Implementation | 最小実装 | - |
| OHLCV | Open, High, Low, Close, Volume | 始値・高値・安値・終値・出来高 | - |
| PBR | Price Book Ratio | 株価純資産倍率 | [PBR](#pbr-price-book-ratio--株価純資産倍率) |
| PER | Price Earnings Ratio | 株価収益率 | [PER](#per-price-earnings-ratio--株価収益率) |
| ROA | Return on Assets | 総資産利益率 | [ROA](#roa-return-on-assets--総資産利益率) |
| ROE | Return on Equity | 自己資本利益率 | [ROE](#roe-return-on-equity--自己資本利益率) |
| TDD | Test-Driven Development | テスト駆動開発 | - |
| TTL | Time To Live | キャッシュの有効期間 | - |

---

## 5. 索引

### あ行
- [アルファベット順索引](#a-z)

### か行
- [クオリティ](#クオリティ-quality)
- [クロスセクショナル](#クロスセクショナル-cross-sectional)
- [計算エラー (ComputationError)](#computationerror)

### さ行
- [サイズ](#サイズ-size)
- [正規化](#正規化-normalization)
- [Spearman相関](#spearman相関-spearman-correlation)
- [Z-score正規化](#z-score正規化-z-score-normalization)
- [標準偏差](#標準偏差-standard-deviation)

### た行
- [単調性](#単調性-monotonicity)
- [t値](#t値-t-statistic)
- [データ取得エラー (DataFetchError)](#datafetcherror)
- [データ不足エラー (InsufficientDataError)](#insufficientdataerror)

### は行
- [バリュー](#バリュー-value)
- [バリデーションエラー (ValidationError)](#validationerror)
- [p値](#p値-p-value)
- [Pearson相関](#pearson相関-pearson-correlation)
- [ファクター](#ファクター-factor)
- [ファクターエクスポージャー](#ファクターエクスポージャー-factor-exposure)
- [ファクター値](#ファクター値-factor-value)
- [ファクタープレミアム](#ファクタープレミアム-factor-premium)
- [フォワードリターン](#フォワードリターン-forward-return)
- [分位分析](#分位分析-quantile-analysis)
- [ベクトル化](#ベクトル化-vectorization)
- [ボラティリティ](#ボラティリティ-volatility)

### ま行
- [モメンタム](#モメンタム-momentum)

### や行
- [ユニバース](#ユニバース-universe)

### ら行
- [ランク正規化](#ランク正規化-rank-normalization)
- [リバーサル](#リバーサル-reversal)
- [ルックアヘッドバイアス](#ルックアヘッドバイアス-look-ahead-bias)
- [ルックバック期間](#ルックバック期間-lookback-period)
- [Long-Shortリターン](#long-shortリターン-long-short-return)

### わ行
- [Winsorization](#winsorization-ウィンソライゼーション)

### A-Z
- [ABC](#abc-abstract-base-class)
- [ComputationError](#computationerror)
- [DataFrame](#dataframe)
- [dataclass](#dataclass)
- [DataFetchError](#datafetcherror)
- [DataProvider](#dataprovider)
- [Factor 基底クラス](#factor-基底クラス)
- [FactorCategory](#factorcategory)
- [FactorError](#factorerror)
- [FactorMetadata](#factormetadata)
- [FactorValue](#factorvalue)
- [IC](#ic-information-coefficient--情報係数)
- [ICAnalyzer](#icanalyzer)
- [ICResult](#icresult)
- [InsufficientDataError](#insufficientdataerror)
- [IR](#ir-information-ratio--情報比率)
- [Normalizer](#normalizer)
- [numpy](#numpy)
- [pandas](#pandas)
- [PBR](#pbr-price-book-ratio--株価純資産倍率)
- [Pearson相関](#pearson相関-pearson-correlation)
- [PER](#per-price-earnings-ratio--株価収益率)
- [plotly](#plotly)
- [Protocol](#protocol-プロトコル)
- [QuantileAnalyzer](#quantileanalyzer)
- [QuantileResult](#quantileresult)
- [ROA](#roa-return-on-assets--総資産利益率)
- [ROE](#roe-return-on-equity--自己資本利益率)
- [scipy](#scipy)
- [Spearman相関](#spearman相関-spearman-correlation)
- [ValidationError](#validationerror)
- [Winsorization](#winsorization-ウィンソライゼーション)
- [yfinance](#yfinance)
- [YFinanceProvider](#yfinanceprovider)
- [Z-score正規化](#z-score正規化-z-score-normalization)

---

## 変更履歴

| 日付 | 変更内容 | 変更者 |
|------|---------|--------|
| 2026-01-14 | 初版作成 | Claude |
