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

### よくある使い方

#### ユースケース1: ログ設定

```python
from factor import get_logger

# 構造化ログの取得
logger = get_logger(__name__)
logger.info("calculation_started", factor="momentum", symbols=100)
logger.error("validation_failed", error="insufficient_data")
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
factor/
├── __init__.py
├── py.typed
├── types.py              # 共通型定義
├── errors.py             # カスタム例外クラス
├── enums.py              # Enum定義（FactorCategory等）
├── core/                 # コアアルゴリズム
│   ├── __init__.py
│   ├── base.py           # Factor基底クラス
│   ├── registry.py       # ファクター登録・管理
│   ├── normalizer.py     # ファクター正規化
│   ├── return_calculator.py  # リターン計算
│   ├── orthogonalization.py  # 直交化
│   └── pca.py            # PCA分析
├── factors/              # ファクター実装
│   ├── __init__.py
│   ├── macro/            # マクロ経済ファクター
│   │   ├── base.py
│   │   ├── macro_builder.py
│   │   ├── interest_rate.py
│   │   ├── inflation.py
│   │   └── flight_to_quality.py
│   ├── price/            # 価格ベースファクター
│   │   ├── momentum.py
│   │   ├── reversal.py
│   │   └── volatility.py
│   ├── quality/          # クオリティファクター
│   │   ├── quality.py
│   │   ├── roic.py
│   │   ├── roic_label.py
│   │   └── composite.py
│   ├── size/             # サイズファクター
│   │   └── size.py
│   └── value/            # バリューファクター
│       ├── value.py
│       └── composite.py
├── providers/            # データプロバイダー
│   ├── base.py           # プロバイダー基底クラス
│   ├── cache.py          # キャッシュ機構
│   └── yfinance.py       # Yahoo Finance連携
├── validation/           # ファクター検証
│   ├── ic_analyzer.py    # IC/IR分析
│   └── quantile_analyzer.py  # 分位分析
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

| モジュール | 状態        | ファイル数 | 行数  |
| ---------- | ----------- | ---------- | ----- |
| `types.py` | ✅ 実装済み | 1          | 352   |
| `errors.py` | ✅ 実装済み | 1         | 354   |
| `enums.py` | ✅ 実装済み | 1          | 74    |
| `core/`    | ✅ 実装済み | 6          | 2,320 |
| `factors/` | ✅ 実装済み | 18         | 4,361 |
| `providers/` | ✅ 実装済み | 4        | 1,227 |
| `validation/` | ✅ 実装済み | 3       | 996   |
| `utils/`   | ✅ 実装済み | 2          | 367   |

<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### 主要クラス

#### `Factor` (基底クラス)

**説明**: ファクター実装の抽象基底クラス

**使用例**:

```python
from factor import Factor, FactorCategory

class CustomFactor(Factor):
    name = "custom"
    category = FactorCategory.VALUE

    def compute(self, provider, universe, start_date, end_date):
        # ファクター計算ロジック
        pass
```

#### `FactorRegistry`

**説明**: ファクターの登録・管理システム

**使用例**:

```python
from factor import get_registry, register_factor

# レジストリ取得
registry = get_registry()

# ファクター登録
@register_factor
class MyFactor(Factor):
    name = "my_factor"
```

---

### ファクター実装

#### `ValueFactor`

**説明**: バリューファクター（PBR, PER, 配当利回り等）

#### `CompositeValueFactor`

**説明**: 複合バリューファクター

---

### Enum

#### `FactorCategory`

```python
from factor import FactorCategory

FactorCategory.MACRO
FactorCategory.QUALITY
FactorCategory.VALUE
FactorCategory.MOMENTUM
FactorCategory.SIZE
```

#### `NormalizationMethod`

```python
from factor import NormalizationMethod

NormalizationMethod.ZSCORE
NormalizationMethod.RANK
NormalizationMethod.PERCENTILE
```

---

### 型定義

#### `FactorConfig`

ファクター設定用データクラス

#### `FactorResult`

ファクター計算結果

#### `OrthogonalizationResult`

直交化結果

#### `QuantileResult`

分位分析結果

---

### 検証ツール

#### `ICAnalyzer`

**説明**: IC/IR分析によるファクター予測力評価

#### `QuantileAnalyzer`

**説明**: 分位ポートフォリオ分析

---

### メタデータ

#### `FactorMetadata`

ファクターのメタ情報

#### `FactorComputeOptions`

ファクター計算オプション

---

### 例外クラス

```python
from factor import (
    FactorError,
    FactorNotFoundError,
    InsufficientDataError,
    NormalizationError,
    OrthogonalizationError,
    ValidationError,
)
```

---

### ユーティリティ

#### `get_logger(name: str) -> BoundLogger`

構造化ログ用ロガー取得

```python
from factor import get_logger

logger = get_logger(__name__)
logger.info("factor_initialized")
```

<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値     |
| -------------------- | ------ |
| Python ファイル数    | 41     |
| 総行数（実装コード） | 10,154 |
| モジュール数         | 7      |
| テストファイル数     | 32     |
| テストカバレッジ     | N/A    |

**詳細内訳**:
- 型定義: 780行（types.py 352行、errors.py 354行、enums.py 74行）
- コア: 2,320行（base.py 451行、registry.py 347行、normalizer.py 452行、return_calculator.py 437行、orthogonalization.py 277行、pca.py 321行）
- ファクター実装: 4,361行（macro/ 1,173行、price/ 889行、quality/ 1,175行、size/ 398行、value/ 736行）
- プロバイダー: 1,227行（base.py 288行、cache.py 204行、yfinance.py 724行）
- 検証: 996行（ic_analyzer.py 451行、quantile_analyzer.py 533行）
- ユーティリティ: 367行（logging_config.py 360行）

<!-- END: STATS -->

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
