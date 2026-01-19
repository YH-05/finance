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

### 基本的な使い方

```python
from factor import YFinanceProvider, ValueFactor
from factor import get_logger

# 1. ログ設定
logger = get_logger(__name__)

# 2. データプロバイダーを作成
provider = YFinanceProvider()

# 3. ファクターを計算
factor = ValueFactor(metric="per", invert=True)
result = factor.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

# 4. 結果を確認
print(result)
```

### よくある使い方

#### ユースケース1: ファクター計算

```python
from factor import YFinanceProvider, MomentumFactor, ValueFactor

# データプロバイダー
provider = YFinanceProvider()

# モメンタムファクター
momentum = MomentumFactor(lookback_days=252)
momentum_scores = momentum.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2023-01-01",
    end_date="2024-01-01",
)

# バリューファクター
value = ValueFactor(metric="pbr", invert=True)
value_scores = value.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2023-01-01",
    end_date="2024-01-01",
)
```

#### ユースケース2: ファクター正規化

```python
from factor import Normalizer, NormalizationMethod
import pandas as pd

# ファクターデータ
factor_data = pd.DataFrame({
    "AAPL": [1.2, 1.5, 1.3],
    "GOOGL": [0.8, 0.9, 0.7],
    "MSFT": [1.0, 1.1, 1.2],
})

# Z-score正規化
normalizer = Normalizer(method=NormalizationMethod.ZSCORE)
normalized = normalizer.normalize(factor_data)
```

#### ユースケース3: ファクター登録と取得

```python
from factor import get_registry, register_factor, Factor, FactorCategory

# カスタムファクターを登録
@register_factor
class CustomFactor(Factor):
    name = "custom"
    description = "Custom factor implementation"
    category = FactorCategory.VALUE

    def compute(self, provider, universe, start_date, end_date):
        # カスタム計算ロジック
        return provider.get_prices(universe, start_date, end_date)

# レジストリから取得
registry = get_registry()
factor_class = registry.get("custom")
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
factor/
├── __init__.py
├── py.typed
├── types.py
├── errors.py
├── enums.py
├── core/
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── normalizer.py
│   ├── return_calculator.py
│   ├── orthogonalization.py
│   └── pca.py
├── factors/
│   ├── __init__.py
│   ├── macro/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── macro_builder.py
│   │   ├── interest_rate.py
│   │   ├── inflation.py
│   │   └── flight_to_quality.py
│   ├── price/
│   │   ├── __init__.py
│   │   ├── momentum.py
│   │   ├── reversal.py
│   │   └── volatility.py
│   ├── quality/
│   │   ├── __init__.py
│   │   ├── quality.py
│   │   ├── roic.py
│   │   ├── roic_label.py
│   │   └── composite.py
│   ├── size/
│   │   ├── __init__.py
│   │   └── size.py
│   └── value/
│       ├── __init__.py
│       ├── value.py
│       └── composite.py
├── providers/
│   ├── __init__.py
│   ├── base.py
│   ├── cache.py
│   └── yfinance.py
├── validation/
│   ├── __init__.py
│   ├── ic_analyzer.py
│   └── quantile_analyzer.py
└── utils/
    ├── __init__.py
    └── logging_config.py
```

<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->
## 実装状況

| モジュール      | 状態        | ファイル数 | 説明                             |
| --------------- | ----------- | ---------- | -------------------------------- |
| `types.py`      | ✅ 実装済み | 1          | 型定義（FactorConfig, FactorResult等） |
| `errors.py`     | ✅ 実装済み | 1          | カスタム例外クラス               |
| `enums.py`      | ✅ 実装済み | 1          | Enum定義（FactorCategory等）     |
| `core/`         | ✅ 実装済み | 7          | コアアルゴリズム（Factor基底、正規化、PCA等） |
| `factors/`      | ✅ 実装済み | 19         | ファクター実装（価格・バリュー・クオリティ等） |
| `providers/`    | ✅ 実装済み | 4          | データプロバイダー（YFinance、キャッシュ） |
| `validation/`   | ✅ 実装済み | 3          | ファクター検証（IC分析、分位分析） |
| `utils/`        | ✅ 実装済み | 2          | ユーティリティ（ロギング）       |

<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### コア

#### `Factor` (基底クラス)

**説明**: 全ファクター実装の抽象基底クラス

**基本的な使い方**:

```python
from factor import Factor, FactorCategory

class CustomFactor(Factor):
    name = "custom"
    description = "Custom factor"
    category = FactorCategory.VALUE

    def compute(self, provider, universe, start_date, end_date):
        # ファクター計算ロジックを実装
        prices = provider.get_prices(universe, start_date, end_date)
        return prices.pct_change()
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `compute(provider, universe, start_date, end_date)` | ファクター値を計算 | `pd.DataFrame` |

---

#### `FactorRegistry`

**説明**: ファクターの一元管理・検索システム

**基本的な使い方**:

```python
from factor import get_registry, register_factor

# ファクター登録
@register_factor
class MyFactor(Factor):
    name = "my_factor"
    # ...

# レジストリから取得
registry = get_registry()
factor_class = registry.get("my_factor")
all_factors = registry.list_all()
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `get(name)` | ファクタークラスを取得 | `type[Factor]` |
| `list_all()` | 全ファクター一覧 | `list[str]` |
| `list_by_category(category)` | カテゴリ別一覧 | `list[str]` |

---

#### `Normalizer`

**説明**: ファクター値の正規化（z-score、ランク、パーセンタイル）

**基本的な使い方**:

```python
from factor import Normalizer, NormalizationMethod
import pandas as pd

# Z-score正規化
normalizer = Normalizer(method=NormalizationMethod.ZSCORE)
normalized = normalizer.normalize(factor_data)

# ランク正規化
rank_normalizer = Normalizer(method=NormalizationMethod.RANK)
ranked = rank_normalizer.normalize(factor_data)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `normalize(data)` | データを正規化 | `pd.DataFrame` |

---

#### `Orthogonalizer`

**説明**: ファクター間の直交化（OLS残差法）

**基本的な使い方**:

```python
from factor import Orthogonalizer

orthogonalizer = Orthogonalizer()
orthogonal_factor = orthogonalizer.orthogonalize(
    target=target_factor,
    reference=reference_factor,
)
```

---

#### `YieldCurvePCA`

**説明**: イールドカーブのPCA分析（符号統一付き）

**基本的な使い方**:

```python
from factor import YieldCurvePCA

pca = YieldCurvePCA(n_components=3)
result = pca.fit_transform(yield_curve_data)
```

---

### ファクター実装

#### `ValueFactor`

**説明**: バリューファクター（PER、PBR、配当利回り、EV/EBITDA）

**基本的な使い方**:

```python
from factor import ValueFactor, YFinanceProvider

provider = YFinanceProvider()
factor = ValueFactor(metric="per", invert=True)
scores = factor.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
```

**主なパラメータ**:

- `metric` (必須): "per", "pbr", "dividend_yield", "ev_ebitda"
- `invert` (デフォルト=True): 低い値を高スコアにするか

---

#### `MomentumFactor`

**説明**: モメンタムファクター（過去リターン）

**基本的な使い方**:

```python
from factor import MomentumFactor, YFinanceProvider

provider = YFinanceProvider()
factor = MomentumFactor(lookback_days=252)
scores = factor.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)
```

**主なパラメータ**:

- `lookback_days` (デフォルト=252): ルックバック期間（営業日）

---

#### `QualityFactor`

**説明**: クオリティファクター（ROE、ROA等）

#### `CompositeQualityFactor`

**説明**: 複合クオリティファクター

#### `CompositeValueFactor`

**説明**: 複合バリューファクター

#### `ROICFactor`

**説明**: ROIC（投下資本利益率）ファクター

#### `SizeFactor`

**説明**: サイズファクター（時価総額）

#### `ReversalFactor`

**説明**: リバーサルファクター（短期反転）

#### `VolatilityFactor`

**説明**: ボラティリティファクター

---

### データプロバイダー

#### `YFinanceProvider`

**説明**: Yahoo Financeからデータを取得

**基本的な使い方**:

```python
from factor import YFinanceProvider

# キャッシュなし
provider = YFinanceProvider()

# キャッシュあり
provider = YFinanceProvider(cache_path="./cache", cache_ttl_hours=24)

# 価格データ取得
prices = provider.get_prices(
    symbols=["AAPL", "GOOGL"],
    start_date="2024-01-01",
    end_date="2024-01-31",
)

# メトリクス取得
metrics = provider.get_metrics(
    symbols=["AAPL", "GOOGL"],
    metric="per",
)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `get_prices(symbols, start_date, end_date)` | 株価データ取得 | `pd.DataFrame` |
| `get_metrics(symbols, metric)` | メトリクス取得 | `pd.Series` |

---

### 検証ツール

#### `ICAnalyzer`

**説明**: IC（情報係数）とIR（情報比率）によるファクター予測力評価

**基本的な使い方**:

```python
from factor import ICAnalyzer

analyzer = ICAnalyzer()
result = analyzer.analyze(
    factor_values=factor_data,
    forward_returns=returns_data,
    method="spearman",
)
print(f"Mean IC: {result.mean_ic}")
print(f"IR: {result.ir}")
```

---

#### `QuantileAnalyzer`

**説明**: 分位ポートフォリオ分析（クインタイル分析等）

**基本的な使い方**:

```python
from factor import QuantileAnalyzer

analyzer = QuantileAnalyzer(n_quantiles=5)
result = analyzer.analyze(
    factor_values=factor_data,
    returns=returns_data,
)
```

---

### Enum

#### `FactorCategory`

ファクターのカテゴリ分類

```python
from factor import FactorCategory

FactorCategory.MACRO       # マクロ経済
FactorCategory.QUALITY     # クオリティ
FactorCategory.VALUE       # バリュー
FactorCategory.MOMENTUM    # モメンタム
FactorCategory.SIZE        # サイズ
FactorCategory.ALTERNATIVE # オルタナティブ
```

---

#### `NormalizationMethod`

正規化手法

```python
from factor import NormalizationMethod

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

#### `get_logger(name: str) -> BoundLogger`

構造化ログ用ロガー取得

```python
from factor import get_logger

logger = get_logger(__name__)
logger.info("factor_initialized", symbols=100)
logger.error("computation_failed", factor="momentum", error=str(e))
```

---

### 関数

#### `get_registry() -> FactorRegistry`

ファクターレジストリのシングルトンインスタンスを取得

#### `register_factor(factor_class: type[Factor]) -> type[Factor]`

ファクタークラスをレジストリに登録するデコレーター

<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値     |
| -------------------- | ------ |
| Python ファイル数    | 41     |
| 総行数（実装コード） | 10,523 |
| モジュール数         | 8      |
| テストファイル数     | 33     |
| テストカバレッジ     | N/A    |

<!-- END: STATS -->

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
