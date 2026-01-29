# factor

ファクター投資・マルチファクターモデル分析パッケージ

## 概要

このパッケージはファクター投資戦略とマルチファクターモデルの分析機能を提供します。

**現在のバージョン:** 0.1.0

<!-- AUTO-GENERATED: QUICKSTART -->
## クイックスタート

### インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

### 基本的な使い方（5分でわかる）

ファクター投資で最も一般的な流れは「**データ取得 → ファクター計算 → ポートフォリオ構築**」です。

```python
from factor import YFinanceProvider, ValueFactor, Normalizer, NormalizationMethod

# ステップ1: データプロバイダーを準備
provider = YFinanceProvider()

# ステップ2: バリューファクター（割安度）を計算
# PER が低い企業を高スコア（invert=True）
factor = ValueFactor(metric="per", invert=True)
scores = factor.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# ステップ3: スコアを正規化（-1 ~ 1 の範囲）
normalizer = Normalizer(method=NormalizationMethod.ZSCORE)
normalized_scores = normalizer.normalize(scores)

print(normalized_scores)
```

### よくある使い方

#### パターン1: 複数のファクターを組み合わせる

```python
from factor import YFinanceProvider, ValueFactor, MomentumFactor, Normalizer, NormalizationMethod

provider = YFinanceProvider()
universe = ["AAPL", "GOOGL", "MSFT", "AMZN"]

# バリューファクター（割安度）
value = ValueFactor(metric="per", invert=True)
value_scores = value.compute(provider, universe, "2024-01-01", "2024-12-31")

# モメンタムファクター（過去12ヶ月のリターン）
momentum = MomentumFactor(lookback_days=252)
momentum_scores = momentum.compute(provider, universe, "2024-01-01", "2024-12-31")

# 両方のスコアを正規化して平均化
normalizer = Normalizer(method=NormalizationMethod.ZSCORE)
combined = (normalizer.normalize(value_scores) + normalizer.normalize(momentum_scores)) / 2
```

#### パターン2: ファクターのパフォーマンスを検証する

```python
from factor import QuantileAnalyzer, YFinanceProvider, ValueFactor
import pandas as pd

provider = YFinanceProvider()
factor = ValueFactor(metric="per", invert=True)
scores = factor.compute(provider, ["AAPL", "GOOGL"], "2024-01-01", "2024-12-31")

# 分位ポートフォリオ分析
# スコアが高い企業と低い企業のグループを作成し、リターン差を確認
analyzer = QuantileAnalyzer(n_quantiles=5)
# ※ returns_data は実際の日次リターンデータ
# result = analyzer.analyze(factor_data=scores, returns=returns_data)
```

#### パターン3: カスタムファクターを作成する

```python
from factor import Factor, FactorCategory, YFinanceProvider

class PriceToSalesRatio(Factor):
    """Price-to-Sales ファクター（営業利益率ベース）"""
    name = "ps_ratio"
    category = FactorCategory.VALUE
    description = "Price-to-Sales ratio factor"

    def compute(self, provider, universe, start_date, end_date):
        # 実装は省略
        pass

# 使用
provider = YFinanceProvider()
ps_factor = PriceToSalesRatio()
scores = ps_factor.compute(provider, ["AAPL"], "2024-01-01", "2024-12-31")
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
factor/
├── __init__.py
├── py.typed
├── types.py           # 型定義（FactorConfig, FactorResult等）
├── errors.py          # カスタム例外クラス
├── enums.py           # Enum定義（FactorCategory, NormalizationMethod）
├── core/              # コアアルゴリズム
│   ├── __init__.py
│   ├── base.py                # Factor抽象基底クラス
│   ├── registry.py            # ファクターレジストリ
│   ├── normalizer.py          # ファクター正規化
│   ├── return_calculator.py   # リターン計算
│   ├── orthogonalization.py   # ファクター直交化
│   └── pca.py                 # イールドカーブPCA分析
├── factors/           # ファクター実装
│   ├── __init__.py
│   ├── macro/         # マクロ経済ファクター
│   │   ├── __init__.py
│   │   ├── base.py             # マクロファクター基底クラス
│   │   ├── macro_builder.py    # マクロファクタービルダー
│   │   ├── interest_rate.py    # 金利ファクター
│   │   ├── inflation.py        # インフレファクター
│   │   └── flight_to_quality.py # フライト・トゥ・クオリティ
│   ├── price/         # 価格ファクター
│   │   ├── __init__.py
│   │   ├── momentum.py   # モメンタム
│   │   ├── reversal.py   # リバーサル
│   │   └── volatility.py # ボラティリティ
│   ├── quality/       # クオリティファクター
│   │   ├── __init__.py
│   │   ├── quality.py     # 基本クオリティ
│   │   ├── roic.py        # ROIC
│   │   ├── roic_label.py  # ROICラベリング
│   │   └── composite.py   # 複合クオリティ
│   ├── size/          # サイズファクター
│   │   ├── __init__.py
│   │   └── size.py        # 時価総額
│   └── value/         # バリューファクター
│       ├── __init__.py
│       ├── value.py       # 基本バリュー
│       └── composite.py   # 複合バリュー
├── providers/         # データプロバイダー
│   ├── __init__.py
│   ├── base.py        # プロバイダープロトコル
│   ├── cache.py       # キャッシュユーティリティ
│   └── yfinance.py    # Yahoo Financeプロバイダー
├── integration/       # 他パッケージとの統合
│   ├── __init__.py
│   ├── market_integration.py   # market パッケージ連携
│   └── analyze_integration.py  # analyze パッケージ連携
├── validation/        # ファクター検証
│   ├── __init__.py
│   ├── ic_analyzer.py       # IC/IR分析
│   └── quantile_analyzer.py # 分位ポートフォリオ分析
└── utils/             # ユーティリティ
    ├── __init__.py
    └── logging_config.py # 構造化ロギング
```

<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->
## 実装状況

| モジュール        | 状態        | ファイル数 | 行数  | 説明                                           |
| ----------------- | ----------- | ---------- | ----- | ---------------------------------------------- |
| `__init__.py`     | ✅ 実装済み | 1          | 158   | パッケージエントリーポイント                   |
| `types.py`        | ✅ 実装済み | 1          | 352   | 型定義（FactorConfig, FactorResult等）         |
| `errors.py`       | ✅ 実装済み | 1          | 354   | カスタム例外クラス                             |
| `enums.py`        | ✅ 実装済み | 1          | 74    | Enum定義（FactorCategory, NormalizationMethod）|
| `core/`           | ✅ 実装済み | 7          | 2,324 | コアアルゴリズム（Factor基底、正規化、PCA等）  |
| `factors/macro/`  | ✅ 実装済み | 6          | 1,177 | マクロ経済ファクター（金利、インフレ等）       |
| `factors/price/`  | ✅ 実装済み | 4          | 889   | 価格ファクター（モメンタム、リバーサル等）     |
| `factors/quality/`| ✅ 実装済み | 5          | 1,195 | クオリティファクター（ROE、ROIC等）           |
| `factors/size/`   | ✅ 実装済み | 2          | 398   | サイズファクター（時価総額）                  |
| `factors/value/`  | ✅ 実装済み | 3          | 736   | バリューファクター（PER、PBR等）              |
| `providers/`      | ✅ 実装済み | 4          | 1,227 | データプロバイダー（YFinance、キャッシュ）    |
| `integration/`    | ✅ 実装済み | 3          | 835   | 統合モジュール（market、analyze パッケージ連携）|
| `validation/`     | ✅ 実装済み | 3          | 1,276 | ファクター検証（IC分析、分位分析）            |
| `utils/`          | ✅ 実装済み | 1          | 3     | ユーティリティ（構造化ロギング）              |

<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### クイックスタート

パッケージの基本的な使い方を3つのステップで説明します:

```python
from factor import YFinanceProvider, ValueFactor, Normalizer, NormalizationMethod

# ステップ1: データソースを設定（Yahoo Finance）
provider = YFinanceProvider()

# ステップ2: ファクターモデルを定義
# バリューファクター：PER が低い企業を高スコア
factor = ValueFactor(metric="per", invert=True)

# ステップ3: ファクター値を計算
result = factor.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# 結果を正規化（全スコアを -1 ～ 1 の範囲に）
normalizer = Normalizer(method=NormalizationMethod.ZSCORE)
normalized = normalizer.normalize(result)
```

**このコードで何ができるか:**
- 3つの企業の割安度スコアを計算
- スコアを正規化して比較可能に
- 低い PER を持つ企業が高スコアになる

### 主要クラス

#### `Factor`

**説明**: 全ファクター実装の抽象基底クラス。カスタムファクターを作成する際に継承します。

**基本的な使い方**:

```python
from factor import Factor, FactorCategory, YFinanceProvider

class CustomFactor(Factor):
    name = "custom"
    description = "Custom factor implementation"
    category = FactorCategory.VALUE

    def compute(self, provider, universe, start_date, end_date):
        prices = provider.get_prices(universe, start_date, end_date)
        return prices.pct_change()

# 使用例
provider = YFinanceProvider()
custom = CustomFactor()
scores = custom.compute(provider, ["AAPL"], "2024-01-01", "2024-12-31")
```

**主な抽象メソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `compute(provider, universe, start_date, end_date)` | ファクター値を計算 | `pd.DataFrame` |

---

#### `YFinanceProvider`

**説明**: Yahoo Financeから価格・ファンダメンタルデータを取得するプロバイダー。

**基本的な使い方**:

```python
from factor import YFinanceProvider

provider = YFinanceProvider()

# 株価データ取得
prices = provider.get_prices(["AAPL", "GOOGL"], "2024-01-01", "2024-12-31")

# ファンダメンタルデータ取得
fundamentals = provider.get_fundamentals(["AAPL", "GOOGL"])
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `get_prices(symbols, start, end)` | 株価データ取得 | `pd.DataFrame` |
| `get_fundamentals(symbols)` | ファンダメンタルデータ取得 | `dict` |

---

#### `ValueFactor`

**説明**: バリューファクター（PER、PBR、配当利回り、EV/EBITDA）を計算。

**基本的な使い方**:

```python
from factor import ValueFactor, YFinanceProvider

provider = YFinanceProvider()

# PERファクター（低PERほど高スコア）
per_factor = ValueFactor(metric="per", invert=True)
scores = per_factor.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
```

**主なパラメータ**:

- `metric` (必須): "per", "pbr", "dividend_yield", "ev_ebitda"
- `invert` (デフォルト=False): True の場合、低い値ほど高スコア

---

#### `MomentumFactor`

**説明**: 過去リターンに基づくモメンタムファクター。

**基本的な使い方**:

```python
from factor import MomentumFactor, YFinanceProvider

provider = YFinanceProvider()

# 過去12ヶ月（252営業日）のモメンタム
momentum = MomentumFactor(lookback_days=252)
scores = momentum.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
```

**主なパラメータ**:

- `lookback_days` (必須): モメンタム計算期間（営業日数）

---

#### `Normalizer`

**説明**: ファクター値を正規化（z-score、ランク、パーセンタイル）。

**基本的な使い方**:

```python
from factor import Normalizer, NormalizationMethod
import pandas as pd

factor_data = pd.DataFrame({
    "AAPL": [1.2, 1.5, 1.3],
    "GOOGL": [0.8, 0.9, 0.7],
})

# Z-score正規化
normalizer = Normalizer(method=NormalizationMethod.ZSCORE)
normalized = normalizer.normalize(factor_data)
```

**主なパラメータ**:

- `method` (必須): `NormalizationMethod.ZSCORE`, `RANK`, `PERCENTILE`

---

#### `QuantileAnalyzer`

**説明**: ファクター値に基づく分位ポートフォリオ分析。

**基本的な使い方**:

```python
from factor import QuantileAnalyzer

analyzer = QuantileAnalyzer(n_quantiles=5)
result = analyzer.analyze(
    factor_data=normalized_scores,
    returns=returns_data,
)

# 各分位のリターン統計を確認
print(result.quantile_returns)
```

**主なパラメータ**:

- `n_quantiles` (デフォルト=5): 分位数

---

### ファクター実装一覧

#### 価格ファクター

```python
from factor import (
    MomentumFactor,      # モメンタム（過去リターン）
    ReversalFactor,      # リバーサル（短期反転）
    VolatilityFactor,    # ボラティリティ
)
```

#### バリューファクター

```python
from factor import (
    ValueFactor,          # バリューファクター（PER、PBR等）
    CompositeValueFactor, # 複合バリューファクター
)
```

#### クオリティファクター

```python
from factor import (
    QualityFactor,          # クオリティ（ROE、ROA等）
    CompositeQualityFactor, # 複合クオリティ
    ROICFactor,             # ROIC（投下資本利益率）
    ROICTransitionLabeler,  # ROICラベリング
)
```

#### サイズファクター

```python
from factor import (
    SizeFactor,  # サイズ（時価総額）
)
```

---

### コアツール

```python
from factor import (
    Normalizer,         # ファクター正規化
    Orthogonalizer,     # ファクター直交化
    YieldCurvePCA,      # イールドカーブPCA分析
    ReturnCalculator,   # リターン計算
    ICAnalyzer,         # IC/IR分析
    QuantileAnalyzer,   # 分位ポートフォリオ分析
)
```

---

### Enum

```python
from factor import FactorCategory, NormalizationMethod

# ファクターカテゴリ
FactorCategory.VALUE       # バリュー
FactorCategory.MOMENTUM    # モメンタム
FactorCategory.QUALITY     # クオリティ
FactorCategory.SIZE        # サイズ
FactorCategory.MACRO       # マクロ経済

# 正規化手法
NormalizationMethod.ZSCORE      # Z-score正規化
NormalizationMethod.RANK        # ランク正規化
NormalizationMethod.PERCENTILE  # パーセンタイル正規化
```

---

### 型定義

データ構造の定義。型ヒントやバリデーションに使用:

```python
from factor import (
    FactorConfig,              # ファクター設定
    FactorResult,              # ファクター計算結果
    OrthogonalizationResult,   # 直交化結果
    QuantileResult,            # 分位分析結果
    FactorMetadata,            # ファクターメタ情報
    FactorComputeOptions,      # 計算オプション
    ReturnConfig,              # リターン計算設定
    PCAResult,                 # PCA分析結果
    ICResult,                  # IC分析結果
)
```

---

### 例外クラス

```python
from factor import (
    FactorError,              # 基底例外
    FactorNotFoundError,      # ファクター未登録
    InsufficientDataError,    # データ不足
    NormalizationError,       # 正規化エラー
    OrthogonalizationError,   # 直交化エラー
    ValidationError,          # バリデーションエラー
    DataFetchError,           # データ取得エラー
)
```

---

### ユーティリティ

#### `get_registry() -> FactorRegistry`

**説明**: ファクターレジストリのシングルトンインスタンスを取得。

**使用例**:

```python
from factor import get_registry

registry = get_registry()
all_factors = registry.list_factors()
```

---

#### `register_factor(factor_class: type[Factor]) -> type[Factor]`

**説明**: カスタムファクタークラスをレジストリに登録するデコレーター。

**使用例**:

```python
from factor import register_factor, Factor

@register_factor
class CustomFactor(Factor):
    name = "custom"
    # ...
```

---

### 統合モジュール（market + analyze パッケージとの連携）

#### `MarketDataProvider`

**説明**: `market` パッケージの `YFinanceFetcher` をアダプトしたデータプロバイダー。

**基本的な使い方**:

```python
from factor import MarketDataProvider, ValueFactor

# market パッケージのフェッチャーをラップ
provider = MarketDataProvider()

# ValueFactor で使用
value_factor = ValueFactor(metric="per", invert=True)
scores = value_factor.compute(
    provider=provider,
    universe=["AAPL", "GOOGL"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
```

---

#### `EnhancedFactorAnalyzer`

**説明**: `analyze` パッケージのテクニカル指標を組み込んだファクター分析ツール。

**基本的な使い方**:

```python
from factor import EnhancedFactorAnalyzer
import pandas as pd

analyzer = EnhancedFactorAnalyzer(indicators=["SMA", "RSI", "MACD"])
result = analyzer.analyze(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# テクニカル指標を含むファクター分析結果を取得
print(result.indicators)
```

---

#### `create_market_provider() -> MarketDataProvider`

**説明**: MarketDataProvider のファクトリー関数。初期化済みプロバイダーを取得。

**使用例**:

```python
from factor import create_market_provider

provider = create_market_provider()
prices = provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")
```

---

#### `create_enhanced_analyzer(indicators: list[str]) -> EnhancedFactorAnalyzer`

**説明**: EnhancedFactorAnalyzer のファクトリー関数。

**使用例**:

```python
from factor import create_enhanced_analyzer

analyzer = create_enhanced_analyzer(indicators=["SMA", "RSI"])
result = analyzer.analyze("AAPL", "2024-01-01", "2024-12-31")
```

---

#### `calculate_factor_with_indicators(symbol, factor, indicators, start_date, end_date) -> dict`

**説明**: ファクター値とテクニカル指標を同時に計算するユーティリティ関数。

**使用例**:

```python
from factor import calculate_factor_with_indicators, ValueFactor

factor = ValueFactor(metric="per", invert=True)
result = calculate_factor_with_indicators(
    symbol="AAPL",
    factor=factor,
    indicators=["SMA", "RSI", "MACD"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# 結果には factor_values と indicators が含まれる
print(result["factor_values"])
print(result["indicators"])
```

<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値     |
| -------------------- | ------ |
| Python ファイル数    | 43     |
| 総行数（実装コード） | 11,021 |
| モジュール数         | 12     |
| テストファイル数     | 37     |
| テストカバレッジ     | N/A    |

<!-- END: STATS -->

## 依存関係

### 必須パッケージ

| パッケージ | 用途 |
|-----------|------|
| `pandas` | データフレーム操作、時系列データ処理 |
| `numpy` | 数値計算、配列操作 |
| `scipy` | 統計計算（z-score、ランク等） |
| `yfinance` | Yahoo Financeからの株価・ファンダメンタルデータ取得 |
| `structlog` | 構造化ロギング |

### 内部パッケージ

このパッケージは以下の内部パッケージに依存しています:

- `finance` - コアインフラ（ロギング、データベース）
- `market_analysis` - 市場データ取得（YFinance、FRED連携）

### インストール

```bash
# 全依存関係をインストール
uv sync --all-extras

# 本番環境のみ
uv sync
```

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
