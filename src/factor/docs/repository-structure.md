# リポジトリ構造定義書 (Repository Structure Document)

## 1. パッケージ構造

```
src/factor/
├── __init__.py                  # パッケージエクスポート（公開API）
├── py.typed                     # PEP 561 マーカー
├── types.py                     # 共通型定義
├── errors.py                    # エラー型定義
│
├── api/                         # API Layer
│   ├── __init__.py
│   └── facade.py                # ファサード（将来用）
│
├── core/                        # Core Layer
│   ├── __init__.py
│   ├── base.py                  # Factor 基底クラス
│   ├── normalizer.py            # Normalizer（正規化処理）
│   └── registry.py              # ファクター登録（将来用）
│
├── factors/                     # Factor Layer
│   ├── __init__.py
│   ├── price/                   # 価格ベースファクター
│   │   ├── __init__.py
│   │   ├── momentum.py          # MomentumFactor
│   │   ├── reversal.py          # ReversalFactor
│   │   └── volatility.py        # VolatilityFactor
│   ├── value/                   # バリューファクター
│   │   ├── __init__.py
│   │   └── value.py             # ValueFactor, CompositeValueFactor
│   ├── quality/                 # クオリティファクター
│   │   ├── __init__.py
│   │   └── quality.py           # QualityFactor, CompositeQualityFactor
│   └── size/                    # サイズファクター
│       ├── __init__.py
│       └── size.py              # SizeFactor
│
├── providers/                   # Provider Layer
│   ├── __init__.py
│   ├── base.py                  # DataProvider Protocol
│   ├── yfinance.py              # YFinanceProvider
│   └── cache.py                 # Cache
│
├── validation/                  # 検証機能
│   ├── __init__.py
│   ├── ic_analyzer.py           # ICAnalyzer（IC/IR分析）
│   └── quantile_analyzer.py     # QuantileAnalyzer（分位分析）
│
├── utils/                       # ユーティリティ
│   ├── __init__.py
│   └── logging_config.py        # ログ設定
│
└── docs/                        # ライブラリドキュメント
    ├── project.md               # プロジェクトファイル
    ├── library-requirements.md  # LRD
    ├── functional-design.md     # 機能設計書
    ├── architecture.md          # アーキテクチャ設計書
    └── repository-structure.md  # リポジトリ構造定義書（本書）
```

## 2. テスト構造

```
tests/factor/
├── unit/                        # ユニットテスト
│   ├── core/
│   │   ├── test_base.py         # Factor基底クラスのテスト
│   │   └── test_normalizer.py   # Normalizerのテスト
│   ├── factors/
│   │   ├── price/
│   │   │   ├── test_momentum.py
│   │   │   ├── test_reversal.py
│   │   │   └── test_volatility.py
│   │   ├── value/
│   │   │   └── test_value.py
│   │   ├── quality/
│   │   │   └── test_quality.py
│   │   └── size/
│   │       └── test_size.py
│   ├── providers/
│   │   └── test_yfinance.py
│   └── validation/
│       ├── test_ic_analyzer.py
│       └── test_quantile_analyzer.py
│
├── property/                    # プロパティベーステスト
│   ├── test_normalizer.py       # 正規化の不変条件
│   ├── test_ic.py               # IC計算の境界値
│   └── test_quantile.py         # 分位分析の境界値
│
├── integration/                 # 統合テスト
│   └── test_end_to_end.py       # エンドツーエンドフロー
│
├── regression/                  # 回帰テスト
│   └── test_known_values.py     # 既知値との比較
│
└── conftest.py                  # テストフィクスチャ
```

## 3. ディレクトリ詳細

### 3.1 API Layer (`api/`)

**役割**: 公開インターフェースの提供、入力バリデーション、結果のラッピング

**配置ファイル**:
- `facade.py`: ファクター計算・検証の統合ファサード（将来用）

**命名規則**:
- ファイル名: snake_case
- クラス名: PascalCase

**依存関係**:
- 依存可能: `core/`, `factors/`, `providers/`, `validation/`, `types.py`, `errors.py`
- 依存禁止: なし（最上位レイヤー）

### 3.2 Core Layer (`core/`)

**役割**: ファクター計算のオーケストレーション、正規化ロジック

**配置ファイル**:
- `base.py`: Factor 抽象基底クラス
- `normalizer.py`: Normalizer クラス（zscore, rank, winsorize）
- `registry.py`: ファクター登録・検索（将来用）

**命名規則**:
- ファイル名: snake_case
- クラス名: PascalCase
- メソッド名: snake_case

**依存関係**:
- 依存可能: `providers/`, `types.py`, `errors.py`
- 依存禁止: `api/`, `factors/`（下位レイヤーからの逆依存禁止）

**例**:
```python
# core/base.py
from abc import ABC, abstractmethod
from factor.providers.base import DataProvider

class Factor(ABC):
    name: str
    description: str

    @abstractmethod
    def compute(self, provider: DataProvider, ...) -> pd.DataFrame:
        ...
```

### 3.3 Factor Layer (`factors/`)

**役割**: 個別ファクターの計算ロジック実装

**サブディレクトリ構成**:

| ディレクトリ | 役割 | 主要クラス |
|-------------|------|-----------|
| `price/` | 価格ベースファクター | MomentumFactor, ReversalFactor, VolatilityFactor |
| `value/` | バリューファクター | ValueFactor, CompositeValueFactor |
| `quality/` | クオリティファクター | QualityFactor, CompositeQualityFactor |
| `size/` | サイズファクター | SizeFactor |

**配置ファイル**:
- 各カテゴリの `__init__.py`: サブパッケージエクスポート
- 個別ファクターファイル: 1ファイル1ファクター（複合ファクターは例外）

**命名規則**:
- ディレクトリ名: 単数形、snake_case（`price/`, `value/`, `quality/`, `size/`）
- ファイル名: snake_case（ファクター名と一致）
- クラス名: PascalCase + `Factor` サフィックス

**依存関係**:
- 依存可能: `core/base.py`（継承）, `providers/`, `types.py`, `errors.py`
- 依存禁止: `api/`, `core/normalizer.py`, `validation/`

**例**:
```
factors/
├── __init__.py              # from factor.factors.price import *
├── price/
│   ├── __init__.py          # __all__ = ["MomentumFactor", ...]
│   ├── momentum.py          # class MomentumFactor(Factor)
│   ├── reversal.py          # class ReversalFactor(Factor)
│   └── volatility.py        # class VolatilityFactor(Factor)
├── value/
│   ├── __init__.py
│   └── value.py             # ValueFactor, CompositeValueFactor
├── quality/
│   ├── __init__.py
│   └── quality.py           # QualityFactor, CompositeQualityFactor
└── size/
    ├── __init__.py
    └── size.py              # SizeFactor
```

### 3.4 Provider Layer (`providers/`)

**役割**: データソースの抽象化、キャッシュ管理

**配置ファイル**:
- `base.py`: DataProvider Protocol（抽象インターフェース）
- `yfinance.py`: YFinanceProvider 実装
- `cache.py`: Cache クラス

**命名規則**:
- ファイル名: データソース名（snake_case）
- クラス名: データソース名 + `Provider` サフィックス

**依存関係**:
- 依存可能: `types.py`, `errors.py`, 外部ライブラリ（yfinance）
- 依存禁止: `api/`, `core/`, `factors/`, `validation/`（最下位レイヤー）

**例**:
```python
# providers/base.py
from typing import Protocol
import pandas as pd

class DataProvider(Protocol):
    def get_prices(self, symbols: list[str], ...) -> pd.DataFrame: ...
    def get_volumes(self, symbols: list[str], ...) -> pd.DataFrame: ...
    def get_fundamentals(self, symbols: list[str], ...) -> pd.DataFrame: ...
    def get_market_cap(self, symbols: list[str], ...) -> pd.DataFrame: ...
```

### 3.5 Validation (`validation/`)

**役割**: ファクターの検証ロジック（IC/IR分析、分位分析）

**配置ファイル**:
- `ic_analyzer.py`: ICAnalyzer クラス（IC/IR計算、統計検定）
- `quantile_analyzer.py`: QuantileAnalyzer クラス（分位分析、可視化）

**命名規則**:
- ファイル名: snake_case + `_analyzer` サフィックス
- クラス名: PascalCase + `Analyzer` サフィックス

**依存関係**:
- 依存可能: `types.py`, `errors.py`, 外部ライブラリ（scipy, plotly）
- 依存禁止: `api/`, `core/`, `factors/`, `providers/`

**例**:
```python
# validation/ic_analyzer.py
class ICAnalyzer:
    def analyze(self, factor_values: pd.DataFrame, forward_returns: pd.DataFrame) -> ICResult: ...
    def compute_ic_series(self, ...) -> pd.Series: ...
```

### 3.6 Utils (`utils/`)

**役割**: 横断的なユーティリティ機能

**配置ファイル**:
- `logging_config.py`: ログ設定

**命名規則**:
- ファイル名: snake_case
- 関数名: snake_case

**依存関係**:
- 依存可能: 標準ライブラリ、外部ライブラリ（structlog）
- 依存禁止: パッケージ内の他ディレクトリ

### 3.7 Types (`types.py`)

**役割**: 共通型定義

**配置内容**:
- `FactorValue`: ファクター値の計算結果
- `ICResult`: IC/IR分析結果
- `QuantileResult`: 分位分析結果
- `FactorMetadata`: ファクターメタデータ
- `FactorCategory`: ファクターカテゴリ Enum
- `NormalizedFactorValue`: 正規化後のファクター値
- オプション型（`FactorComputeOptions`, `NormalizationOptions`, etc.）

**依存関係**:
- 依存可能: 標準ライブラリ、pandas, numpy
- 依存禁止: パッケージ内の他モジュール

### 3.8 Errors (`errors.py`)

**役割**: エラー型定義

**配置内容**:
- `FactorError`: 基底エラー
- `DataFetchError`: データ取得エラー
- `ValidationError`: 入力バリデーションエラー
- `ComputationError`: 計算エラー
- `InsufficientDataError`: データ不足エラー

**依存関係**:
- 依存可能: 標準ライブラリ
- 依存禁止: パッケージ内の他モジュール

## 4. テストディレクトリ詳細

### 4.1 unit/ (ユニットテスト)

**役割**: 個別関数・クラスの単体テスト

**構造**: `src/factor/` と同じディレクトリ構造を維持

**命名規則**:
- ファイル名: `test_` + 対象ファイル名
- 関数名: `test_` + テスト内容

**例**:
```
tests/factor/unit/
├── core/
│   ├── test_base.py           # Factor基底クラスのテスト
│   └── test_normalizer.py     # Normalizerのテスト
├── factors/
│   └── price/
│       └── test_momentum.py   # MomentumFactorのテスト
└── validation/
    └── test_ic_analyzer.py    # ICAnalyzerのテスト
```

### 4.2 property/ (プロパティベーステスト)

**役割**: Hypothesis を使用した不変条件・境界値テスト

**命名規則**:
- ファイル名: `test_` + テスト対象
- 関数名: `test_` + プロパティ説明

**例**:
```python
# tests/factor/property/test_normalizer.py
from hypothesis import given, strategies as st

@given(st.floats(min_value=-1e10, max_value=1e10))
def test_zscore_always_produces_mean_near_zero(values):
    ...
```

### 4.3 integration/ (統合テスト)

**役割**: 複数コンポーネントの連携テスト

**命名規則**:
- ファイル名: `test_` + シナリオ名

### 4.4 regression/ (回帰テスト)

**役割**: 既知値との比較による回帰防止

**命名規則**:
- ファイル名: `test_known_values.py`

## 5. ファイル配置規則

### 5.1 ソースファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|-------------|--------|---------|-----|
| 基底クラス | `core/` | `base.py`, `[name].py` | `base.py`, `normalizer.py` |
| ファクター実装 | `factors/[category]/` | `[factor_name].py` | `momentum.py`, `value.py` |
| データプロバイダー | `providers/` | `[source_name].py` | `yfinance.py` |
| アナライザー | `validation/` | `[name]_analyzer.py` | `ic_analyzer.py` |
| 型定義 | ルート | `types.py` | `types.py` |
| エラー定義 | ルート | `errors.py` | `errors.py` |

### 5.2 テストファイル

| テスト種別 | 配置先 | 命名規則 | 例 |
|-----------|--------|---------|-----|
| ユニットテスト | `tests/factor/unit/` | `test_[対象].py` | `test_momentum.py` |
| プロパティテスト | `tests/factor/property/` | `test_[対象].py` | `test_normalizer.py` |
| 統合テスト | `tests/factor/integration/` | `test_[シナリオ].py` | `test_end_to_end.py` |
| 回帰テスト | `tests/factor/regression/` | `test_known_values.py` | `test_known_values.py` |

## 6. 命名規則

### 6.1 ディレクトリ名

| カテゴリ | 規則 | 例 |
|---------|------|-----|
| レイヤーディレクトリ | 複数形、snake_case | `providers/`, `factors/` |
| ファクターカテゴリ | 単数形、snake_case | `price/`, `value/`, `quality/`, `size/` |
| テストディレクトリ | 複数形、snake_case | `unit/`, `property/`, `integration/` |

### 6.2 ファイル名

| カテゴリ | 規則 | 例 |
|---------|------|-----|
| モジュール | snake_case | `momentum.py`, `ic_analyzer.py` |
| 初期化 | `__init__.py` | `__init__.py` |
| 型定義 | `types.py` | `types.py` |
| エラー定義 | `errors.py` | `errors.py` |

### 6.3 クラス名

| カテゴリ | 規則 | 例 |
|---------|------|-----|
| ファクター | PascalCase + `Factor` | `MomentumFactor`, `ValueFactor` |
| プロバイダー | PascalCase + `Provider` | `YFinanceProvider` |
| アナライザー | PascalCase + `Analyzer` | `ICAnalyzer`, `QuantileAnalyzer` |
| 結果型 | PascalCase + `Result` | `ICResult`, `QuantileResult` |
| エラー | PascalCase + `Error` | `FactorError`, `DataFetchError` |

## 7. 依存関係のルール

### 7.1 レイヤー間の依存方向

```
API Layer
    ↓ (OK)
Core Layer
    ↓ (OK)
Factor Layer
    ↓ (OK)
Provider Layer
```

**許可される依存**:
- 上位レイヤー → 下位レイヤー
- 全レイヤー → `types.py`, `errors.py`
- 全レイヤー → `utils/`

**禁止される依存**:
- 下位レイヤー → 上位レイヤー
- Factor Layer → Validation (検証は独立)
- Provider Layer → 他のすべてのレイヤー

### 7.2 依存関係マトリクス

| From \ To | api/ | core/ | factors/ | providers/ | validation/ | types.py | errors.py | utils/ |
|-----------|------|-------|----------|------------|-------------|----------|-----------|--------|
| api/ | - | OK | OK | OK | OK | OK | OK | OK |
| core/ | NG | - | NG | OK | NG | OK | OK | OK |
| factors/ | NG | OK | - | OK | NG | OK | OK | OK |
| providers/ | NG | NG | NG | - | NG | OK | OK | OK |
| validation/ | NG | NG | NG | NG | - | OK | OK | OK |

### 7.3 循環依存の回避

**問題のあるパターン**:
```python
# factors/price/momentum.py
from factor.validation.ic_analyzer import ICAnalyzer  # NG

# validation/ic_analyzer.py
from factor.factors.price.momentum import MomentumFactor  # 循環依存
```

**解決策**: Protocol を使用
```python
# types.py に Protocol を定義
class FactorProtocol(Protocol):
    def compute(self, ...) -> pd.DataFrame: ...

# validation/ic_analyzer.py
from factor.types import FactorProtocol

class ICAnalyzer:
    def analyze(self, factor_values: pd.DataFrame, ...) -> ICResult:
        ...  # ファクター値のみを受け取り、Factor クラスへの依存なし
```

## 8. スケーリング戦略

### 8.1 新規ファクターカテゴリの追加

新しいファクターカテゴリ（例: `macro/`）を追加する場合:

```
factors/
├── price/
├── value/
├── quality/
├── size/
└── macro/                    # 新規追加
    ├── __init__.py
    ├── interest_rate.py      # 金利感応度ファクター
    └── inflation.py          # インフレ感応度ファクター
```

**手順**:
1. `factors/` 配下に新カテゴリディレクトリを作成
2. `__init__.py` でエクスポート設定
3. `types.py` の `FactorCategory` Enum に追加
4. `src/factor/__init__.py` の `__all__` に追加

### 8.2 新規データプロバイダーの追加

新しいデータプロバイダー（例: FRED）を追加する場合:

```
providers/
├── base.py
├── yfinance.py
├── cache.py
└── fred.py                   # 新規追加
```

**手順**:
1. `providers/` 配下に新ファイルを作成
2. `DataProvider` Protocol を実装
3. `providers/__init__.py` でエクスポート
4. `src/factor/__init__.py` の `__all__` に追加

### 8.3 検証機能の追加

新しい検証機能（例: 回帰分析）を追加する場合:

```
validation/
├── __init__.py
├── ic_analyzer.py
├── quantile_analyzer.py
└── regression_analyzer.py    # 新規追加
```

### 8.4 ファイルサイズの管理

**分割の目安**:
- 1ファイル: 300行以下を推奨
- 300-500行: リファクタリングを検討
- 500行以上: 分割を強く推奨

**複合ファクターの分割例**:
```python
# 分割前: value.py (500行)
# ValueFactor + CompositeValueFactor

# 分割後
value/
├── __init__.py              # エクスポート
├── value.py                 # ValueFactor (200行)
└── composite.py             # CompositeValueFactor (200行)
```

## 9. 公開API (`__init__.py`)

### 9.1 パッケージルート

```python
# src/factor/__init__.py
"""factor - カスタムファクター開発フレームワーク"""

# Core
from factor.core.base import Factor
from factor.core.normalizer import Normalizer

# Price Factors
from factor.factors.price import MomentumFactor, ReversalFactor, VolatilityFactor

# Value Factors
from factor.factors.value import ValueFactor, CompositeValueFactor

# Quality Factors
from factor.factors.quality import QualityFactor, CompositeQualityFactor

# Size Factors
from factor.factors.size import SizeFactor

# Providers
from factor.providers import YFinanceProvider

# Validation
from factor.validation import ICAnalyzer, QuantileAnalyzer

# Types
from factor.types import (
    FactorValue,
    ICResult,
    QuantileResult,
    FactorMetadata,
    FactorCategory,
)

# Errors
from factor.errors import (
    FactorError,
    DataFetchError,
    ValidationError,
    ComputationError,
    InsufficientDataError,
)

__all__ = [
    # Core
    "Factor",
    "Normalizer",
    # Price Factors
    "MomentumFactor",
    "ReversalFactor",
    "VolatilityFactor",
    # Value Factors
    "ValueFactor",
    "CompositeValueFactor",
    # Quality Factors
    "QualityFactor",
    "CompositeQualityFactor",
    # Size Factors
    "SizeFactor",
    # Providers
    "YFinanceProvider",
    # Validation
    "ICAnalyzer",
    "QuantileAnalyzer",
    # Types
    "FactorValue",
    "ICResult",
    "QuantileResult",
    "FactorMetadata",
    "FactorCategory",
    # Errors
    "FactorError",
    "DataFetchError",
    "ValidationError",
    "ComputationError",
    "InsufficientDataError",
]
```

### 9.2 サブパッケージ

**factors/__init__.py**:
```python
from factor.factors.price import MomentumFactor, ReversalFactor, VolatilityFactor
from factor.factors.value import ValueFactor, CompositeValueFactor
from factor.factors.quality import QualityFactor, CompositeQualityFactor
from factor.factors.size import SizeFactor

__all__ = [
    "MomentumFactor",
    "ReversalFactor",
    "VolatilityFactor",
    "ValueFactor",
    "CompositeValueFactor",
    "QualityFactor",
    "CompositeQualityFactor",
    "SizeFactor",
]
```

**providers/__init__.py**:
```python
from factor.providers.yfinance import YFinanceProvider

__all__ = ["YFinanceProvider"]
```

**validation/__init__.py**:
```python
from factor.validation.ic_analyzer import ICAnalyzer
from factor.validation.quantile_analyzer import QuantileAnalyzer

__all__ = ["ICAnalyzer", "QuantileAnalyzer"]
```

## 10. アーキテクチャ対応表

| アーキテクチャレイヤー | ディレクトリ | 主要コンポーネント |
|-----------------------|-------------|-------------------|
| API Layer | `api/` | Facade (将来用) |
| Core Layer | `core/` | Factor, Normalizer |
| Factor Layer | `factors/` | Builtin Factors |
| Provider Layer | `providers/` | DataProvider, YFinanceProvider |
| 検証機能 | `validation/` | ICAnalyzer, QuantileAnalyzer |

## 11. チェックリスト

- [x] 4層構造（API/Core/Factor/Provider）がディレクトリに反映されている
- [x] ビルトインファクターがカテゴリ別サブディレクトリに配置されている
- [x] 検証機能（validation）のモジュール構成が定義されている
- [x] データプロバイダーの実装ディレクトリが定義されている
- [x] テストディレクトリがソース構造と対応している
- [x] 依存関係ルールが明確に定義されている
- [x] 命名規則が一貫している
- [x] スケーリング戦略が考慮されている
- [x] 公開APIが明確に定義されている
