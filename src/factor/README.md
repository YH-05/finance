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
import pandas as pd
from factor import Normalizer, FactorConfig, FactorCategory, NormalizationMethod

# 1. ファクターデータの正規化
normalizer = Normalizer(min_samples=10)
factor_data = pd.Series([1.2, 2.5, 1.8, 3.1, 2.0])

# Z-score正規化
zscore_data = normalizer.zscore(factor_data, robust=True)

# パーセンタイルランク変換
rank_data = normalizer.percentile_rank(factor_data)
```

### よくある使い方

#### ユースケース1: ファクターの正規化と外れ値処理

```python
from factor import Normalizer

normalizer = Normalizer()

# 外れ値をクリッピング（1%と99%でウィンソライズ）
clean_data = normalizer.winsorize(factor_data, limits=(0.01, 0.01))

# その後Z-score正規化
normalized = normalizer.zscore(clean_data)
```

#### ユースケース2: リターン計算

```python
from factor import ReturnCalculator

calculator = ReturnCalculator()

# 価格データから複数期間のリターンを計算
prices_df = pd.DataFrame({
    "date": pd.date_range("2020-01-01", periods=60, freq="ME"),
    "symbol": ["AAPL"] * 60,
    "price": [100 + i * 2 for i in range(60)]
})

returns = calculator.calculate_returns(prices_df)
# Return_1M, Return_3M, Return_6M, Return_1Y 等が含まれる
```

#### ユースケース3: ファクターの直交化

```python
from factor import Orthogonalizer

orthogonalizer = Orthogonalizer(min_samples=20)

# モメンタムファクターから市場ファクターの影響を除去
result = orthogonalizer.orthogonalize(
    factor_to_clean=momentum_factor,
    control_factors=market_factor
)

orthogonal_momentum = result.orthogonalized_data
print(f"R-squared: {result.r_squared:.2%}")
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
factor/
├── __init__.py
├── py.typed
├── types.py              # 共通型定義（FactorConfig, FactorResult等）
├── errors.py             # カスタム例外クラス
├── enums.py              # Enum定義（FactorCategory, NormalizationMethod）
├── core/                 # コアアルゴリズム
│   ├── __init__.py
│   ├── normalizer.py     # ファクター正規化
│   ├── return_calculator.py  # リターン計算
│   ├── orthogonalization.py  # 直交化
│   └── pca.py            # PCA分析
├── utils/                # ユーティリティ
│   ├── __init__.py
│   └── logging_config.py # 構造化ログ設定
└── docs/                 # ドキュメント（8ファイル）
    ├── architecture.md
    ├── development-guidelines.md
    ├── functional-design.md
    ├── glossary.md
    ├── library-requirements.md
    ├── project.md
    ├── repository-structure.md
    └── tasks.md
```

<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->
## 実装状況

| モジュール | 状態        | ファイル数 | 行数  | 説明 |
| ---------- | ----------- | ---------- | ----- | ---- |
| `types.py` | ✅ 実装済み | 1          | 280   | Wave 0: 型定義完了 |
| `errors.py` | ✅ 実装済み | 1         | 314   | Wave 0: 例外クラス完了 |
| `enums.py` | ✅ 実装済み | 1          | 72    | Wave 0: Enum定義完了 |
| `core/`    | ✅ 実装済み | 5          | 1,509 | Wave 1-3: コアアルゴリズム完了 |
| `utils/`   | ✅ 実装済み | 2          | 367   | ログ設定完了 |

**コア実装詳細**:
- `normalizer.py`: Z-score/Percentile/Quintile/Winsorize正規化（453行）
- `return_calculator.py`: マルチピリオドリターン計算（438行）
- `orthogonalization.py`: OLS直交化・カスケード直交化（278行）
- `pca.py`: PCA分析・符号調整（322行）

<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### クイックスタート

基本的な使い方を簡単に説明します:

```python
import pandas as pd
from factor import Normalizer, ReturnCalculator, Orthogonalizer

# ファクター正規化
normalizer = Normalizer()
normalized = normalizer.zscore(factor_data)

# リターン計算
calculator = ReturnCalculator()
returns = calculator.calculate_returns(price_df)

# 直交化
orthogonalizer = Orthogonalizer()
result = orthogonalizer.orthogonalize(momentum, market)
```

---

### 主要クラス

#### `Normalizer`

**説明**: ファクターデータを正規化するクラス。Z-score、パーセンタイル、クインタイル、ウィンソライゼーションをサポート。

**基本的な使い方**:

```python
from factor import Normalizer

normalizer = Normalizer(min_samples=10)

# Z-score正規化（ロバスト版）
zscore = normalizer.zscore(data, robust=True)

# パーセンタイルランク（0-1）
percentile = normalizer.percentile_rank(data)

# クインタイル分割（1-5）
quintile = normalizer.quintile_rank(data)

# ウィンソライゼーション（外れ値クリッピング）
winsorized = normalizer.winsorize(data, limits=(0.01, 0.01))
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `zscore(data, robust=True)` | Z-score正規化（robust=Trueで中央値・MAD使用） | `pd.Series/DataFrame` |
| `percentile_rank(data)` | パーセンタイルランク変換（0-1） | `pd.Series/DataFrame` |
| `quintile_rank(data, labels=None)` | クインタイル変換（1-5） | `pd.Series/DataFrame` |
| `winsorize(data, limits=(0.01, 0.01))` | 外れ値をクリッピング | `pd.Series/DataFrame` |
| `normalize_by_group(data, value_col, group_cols, method="zscore")` | グループ別正規化（セクターニュートラル等） | `pd.DataFrame` |

---

#### `ReturnCalculator`

**説明**: 株価や資産価格データから複数期間のリターンを計算するクラス。

**基本的な使い方**:

```python
from factor import ReturnCalculator

calculator = ReturnCalculator()

# 価格データから1M/3M/6M/1Y/3Y/5Yのリターンを計算
returns = calculator.calculate_returns(
    prices=price_df,
    date_column="date",
    symbol_column="symbol",
    price_column="price"
)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `calculate_returns(prices, ...)` | マルチピリオドリターン計算 | `pd.DataFrame` |
| `calculate_forward_returns(data, periods, ...)` | フォワードリターン計算 | `pd.Series/DataFrame` |
| `annualize_return(returns, period_months, method="simple")` | リターンの年率換算 | `pd.Series/DataFrame` |
| `calculate_active_return(returns, benchmark_col, ...)` | ベンチマーク対比のアクティブリターン | `pd.DataFrame` |
| `calculate_cagr(prices, years)` | 複利年率成長率（CAGR）計算 | `pd.Series` |

---

#### `Orthogonalizer`

**説明**: ファクター間の相関を除去し、直交化するクラス。OLS回帰の残差を使用。

**基本的な使い方**:

```python
from factor import Orthogonalizer

orthogonalizer = Orthogonalizer(min_samples=20)

# モメンタムから市場ファクターを除去
result = orthogonalizer.orthogonalize(
    factor_to_clean=momentum_factor,
    control_factors=market_factor,
    add_constant=True
)

orthogonal_momentum = result.orthogonalized_data
print(f"除去された分散: {result.r_squared:.2%}")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `orthogonalize(factor_to_clean, control_factors, add_constant=True)` | OLS回帰による直交化 | `OrthogonalizationResult` |
| `orthogonalize_cascade(factors, order)` | 複数ファクターの順次直交化 | `dict[str, OrthogonalizationResult]` |

---

#### `YieldCurvePCA`

**説明**: イールドカーブ（金利曲線）に対してPCA分析を実行し、レベル・スロープ・カーブ成分を抽出。

**基本的な使い方**:

```python
from factor import YieldCurvePCA

pca = YieldCurvePCA(n_components=3)

# イールドカーブデータのPCA分析
result = pca.fit_transform(yield_curve_df, use_changes=True)

level_factor = result.scores["Level"]
slope_factor = result.scores["Slope"]
curvature_factor = result.scores["Curvature"]
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `fit_transform(data, use_changes=True, align_signs=True)` | PCA実行とスコア計算 | `PCAResult` |
| `transform(data, use_changes=True)` | 学習済みモデルで新データを変換 | `pd.DataFrame` |
| `get_loadings()` | 主成分負荷量を取得 | `pd.DataFrame` |

---

### Enum定義

#### `FactorCategory`

ファクターのカテゴリ分類:

```python
from factor import FactorCategory

FactorCategory.MACRO       # マクロ経済ファクター
FactorCategory.QUALITY     # 品質ファクター
FactorCategory.VALUE       # バリューファクター
FactorCategory.MOMENTUM    # モメンタムファクター
FactorCategory.SIZE        # サイズファクター
```

#### `NormalizationMethod`

正規化手法:

```python
from factor import NormalizationMethod

NormalizationMethod.ZSCORE      # Z-score正規化
NormalizationMethod.RANK        # ランク変換
NormalizationMethod.PERCENTILE  # パーセンタイル変換
NormalizationMethod.QUINTILE    # クインタイル変換
```

---

### 型定義（Dataclass）

#### `FactorConfig`

ファクター設定用データクラス:

```python
from factor import FactorConfig, FactorCategory, NormalizationMethod

config = FactorConfig(
    name="momentum_12m",
    category=FactorCategory.MOMENTUM,
    normalization=NormalizationMethod.ZSCORE,
    window=252,              # ローリングウィンドウサイズ
    min_periods=20,          # 最小期間数
    winsorize_limits=None,   # ウィンソライゼーション閾値
    lag=0                    # ラグ期間
)
```

#### `FactorResult`

ファクター計算結果:

```python
from factor import FactorResult

# result: FactorResult
result.name                    # ファクター名
result.data                    # DataFrame（日付×銘柄）
result.config                  # 使用した設定
result.coverage                # データカバレッジ率
result.statistics              # 統計サマリー
result.is_empty                # データが空かチェック
result.symbols                 # 対象銘柄リスト
result.date_range              # 日付範囲
```

#### `OrthogonalizationResult`

直交化結果:

```python
from factor import OrthogonalizationResult

# result: OrthogonalizationResult
result.original_factor         # 元のファクター名
result.orthogonalized_data     # 直交化後のデータ
result.control_factors         # 使用したコントロールファクター
result.method                  # 使用した手法（"ols"等）
result.r_squared               # R²（除去された分散割合）
result.residual_std            # 残差の標準偏差
result.variance_removed        # 除去された分散（=r_squared）
```

---

### 例外クラス

全て `FactorError` を継承:

```python
from factor import (
    FactorError,              # ベース例外
    InsufficientDataError,    # データ不足エラー
    NormalizationError,       # 正規化エラー
    OrthogonalizationError,   # 直交化エラー
    ValidationError,          # バリデーションエラー
)
```

---

### ユーティリティ関数

#### `get_logger(name: str) -> BoundLogger`

構造化ログ用ロガー取得:

```python
from factor import get_logger

logger = get_logger(__name__)
logger.info("factor_calculated", factor="momentum", count=100)
logger.error("calculation_failed", error=str(e))
```

<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値     |
| -------------------- | ------ |
| Python ファイル数    | 11     |
| 総行数（実装コード） | 2,598  |
| モジュール数         | 2      |
| テストファイル数     | 4      |
| テストカバレッジ     | N/A    |

**詳細内訳**:
- 型定義: 666行（types.py 280行、errors.py 314行、enums.py 72行）
- コアアルゴリズム: 1,509行（normalizer 453行、return_calculator 438行、orthogonalization 278行、pca 322行、\_\_init\_\_ 18行）
- ユーティリティ: 367行（logging_config 367行）
- テスト: 4ファイル（tests/factor/unit/core/）

<!-- END: STATS -->

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
