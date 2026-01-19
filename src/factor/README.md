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
from factor import get_logger

# ログ設定
logger = get_logger(__name__)
logger.info("factor_package_initialized")
```

### 主要な使用例

#### ファクター計算

```python
from factor import YFinanceProvider, ValueFactor
from factor import get_logger

logger = get_logger(__name__)

# データプロバイダー
provider = YFinanceProvider()

# バリューファクター（PER）
factor = ValueFactor(metric="per", invert=True)
result = factor.compute(
    provider=provider,
    universe=["AAPL", "GOOGL", "MSFT"],
    start_date="2024-01-01",
    end_date="2024-12-31",
)

logger.info("factor_computed", rows=len(result))
```

#### ファクター正規化

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

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
factor/
├── __init__.py
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
├── utils/
│   ├── __init__.py
│   └── logging_config.py
└── docs/
```

<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->
## 実装状況

| モジュール        | 状態        | ファイル数 | 説明                                           |
| ----------------- | ----------- | ---------- | ---------------------------------------------- |
| `types.py`        | ✅ 実装済み | 1          | 型定義（FactorConfig, FactorResult等）         |
| `errors.py`       | ✅ 実装済み | 1          | カスタム例外クラス                             |
| `enums.py`        | ✅ 実装済み | 1          | Enum定義（FactorCategory, NormalizationMethod）|
| `core/`           | ✅ 実装済み | 7          | コアアルゴリズム（Factor基底、正規化、PCA等）  |
| `factors/macro/`  | ✅ 実装済み | 6          | マクロファクター（金利、インフレ、質への逃避）|
| `factors/price/`  | ✅ 実装済み | 4          | 価格ファクター（モメンタム、リバーサル等）    |
| `factors/quality/`| ✅ 実装済み | 5          | クオリティファクター（ROIC、複合等）          |
| `factors/size/`   | ✅ 実装済み | 2          | サイズファクター（時価総額）                  |
| `factors/value/`  | ✅ 実装済み | 3          | バリューファクター（PER、PBR、複合等）        |
| `providers/`      | ✅ 実装済み | 4          | データプロバイダー（YFinance、キャッシュ）    |
| `validation/`     | ✅ 実装済み | 3          | ファクター検証（IC分析、分位分析）            |
| `utils/`          | ✅ 実装済み | 2          | ユーティリティ（構造化ロギング）              |

<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### 主要クラス

#### `Factor` (基底クラス)

全ファクター実装の抽象基底クラス。カスタムファクターを作成する際に継承します。

```python
from factor import Factor, FactorCategory

class CustomFactor(Factor):
    name = "custom"
    description = "Custom factor"
    category = FactorCategory.VALUE

    def compute(self, provider, universe, start_date, end_date):
        prices = provider.get_prices(universe, start_date, end_date)
        return prices.pct_change()
```

---

#### `YFinanceProvider`

Yahoo Financeからデータを取得するプロバイダー。

```python
from factor import YFinanceProvider

provider = YFinanceProvider()
prices = provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")
```

---

#### `ValueFactor`

バリューファクター（PER、PBR、配当利回り、EV/EBITDA）。

```python
from factor import ValueFactor, YFinanceProvider

provider = YFinanceProvider()
factor = ValueFactor(metric="per", invert=True)
scores = factor.compute(provider, ["AAPL"], "2024-01-01", "2024-12-31")
```

---

#### `MomentumFactor`

モメンタムファクター（過去リターン）。

```python
from factor import MomentumFactor, YFinanceProvider

provider = YFinanceProvider()
factor = MomentumFactor(lookback_days=252)
scores = factor.compute(provider, ["AAPL"], "2024-01-01", "2024-12-31")
```

---

#### `Normalizer`

ファクター値の正規化（z-score、ランク、パーセンタイル）。

```python
from factor import Normalizer, NormalizationMethod

normalizer = Normalizer(method=NormalizationMethod.ZSCORE)
normalized = normalizer.normalize(factor_data)
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

構造化ログ用ロガー取得。

```python
from factor import get_logger

logger = get_logger(__name__)
logger.info("factor_initialized", symbols=100)
```

---

### 関数

#### `get_registry() -> FactorRegistry`

ファクターレジストリのシングルトンインスタンスを取得。

#### `register_factor(factor_class: type[Factor]) -> type[Factor]`

ファクタークラスをレジストリに登録するデコレーター。

---

### その他の実装ファクター

- `QualityFactor` - クオリティファクター（ROE、ROA等）
- `CompositeQualityFactor` - 複合クオリティファクター
- `CompositeValueFactor` - 複合バリューファクター
- `ROICFactor` - ROIC（投下資本利益率）ファクター
- `ROICTransitionLabeler` - ROICラベリング
- `SizeFactor` - サイズファクター（時価総額）
- `ReversalFactor` - リバーサルファクター（短期反転）
- `VolatilityFactor` - ボラティリティファクター

### その他のツール

- `Orthogonalizer` - ファクター直交化
- `YieldCurvePCA` - イールドカーブPCA分析
- `ReturnCalculator` - リターン計算
- `ICAnalyzer` - IC/IR分析
- `QuantileAnalyzer` - 分位ポートフォリオ分析
- `Cache` - データキャッシュ

<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値     |
| -------------------- | ------ |
| Python ファイル数    | 41     |
| 総行数（実装コード） | 10,523 |
| モジュール数         | 11     |
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
