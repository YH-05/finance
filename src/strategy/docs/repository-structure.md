# リポジトリ構造定義書 (Repository Structure Document)

## 1. パッケージ構造

```
src/strategy/
├── __init__.py                  # パッケージエクスポート（公開API）
├── py.typed                     # PEP 561 マーカー
├── types.py                     # 共通型定義（Holding, TickerInfo, Period等）
├── errors.py                    # エラー・警告クラス定義
├── portfolio.py                 # Portfolio クラス
│
├── risk/                        # Core Layer - リスク計算
│   ├── __init__.py
│   ├── calculator.py            # RiskCalculator
│   └── metrics.py               # RiskMetricsResult
│
├── rebalance/                   # Rebalance Layer
│   ├── __init__.py
│   ├── rebalancer.py            # Rebalancer クラス
│   ├── drift.py                 # DriftResult, DriftDetector
│   └── cost.py                  # RebalanceCost, CostEstimator
│
├── providers/                   # Provider Layer
│   ├── __init__.py
│   ├── protocol.py              # DataProvider Protocol
│   ├── market_analysis.py       # MarketAnalysisProvider
│   └── mock.py                  # MockProvider（テスト用）
│
├── visualization/               # Visualization Layer
│   ├── __init__.py
│   └── charts.py                # ChartGenerator
│
├── output/                      # Output Layer
│   ├── __init__.py
│   ├── dataframe.py             # DataFrame出力
│   ├── json.py                  # JSON出力
│   └── markdown.py              # Markdown出力
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
tests/strategy/
├── unit/                        # ユニットテスト
│   ├── test_portfolio.py        # Portfolio クラスのテスト
│   ├── test_types.py            # 型定義のテスト
│   ├── risk/
│   │   ├── test_calculator.py   # RiskCalculator のテスト
│   │   └── test_metrics.py      # RiskMetricsResult のテスト
│   ├── rebalance/
│   │   ├── test_rebalancer.py   # Rebalancer のテスト
│   │   ├── test_drift.py        # DriftDetector のテスト
│   │   └── test_cost.py         # CostEstimator のテスト
│   ├── providers/
│   │   ├── test_market_analysis.py  # MarketAnalysisProvider のテスト
│   │   └── test_mock.py         # MockProvider のテスト
│   ├── visualization/
│   │   └── test_charts.py       # ChartGenerator のテスト
│   └── output/
│       ├── test_dataframe.py    # DataFrame出力のテスト
│       ├── test_json.py         # JSON出力のテスト
│       └── test_markdown.py     # Markdown出力のテスト
│
├── property/                    # プロパティベーステスト
│   ├── test_portfolio.py        # 配分正規化の不変条件
│   ├── test_risk_calculator.py  # リスク指標の境界値
│   └── test_rebalancer.py       # ドリフト計算の境界値
│
├── integration/                 # 統合テスト
│   └── test_end_to_end.py       # エンドツーエンドフロー
│
└── conftest.py                  # テストフィクスチャ
```

## 3. ディレクトリ詳細

### 3.1 API Layer（ルートモジュール）

**役割**: 公開インターフェースの提供、入力バリデーション

**配置ファイル**:
- `__init__.py`: パッケージ公開API（Portfolio, Rebalancer等のエクスポート）
- `portfolio.py`: Portfolio クラス（ポートフォリオ定義・分析の起点）
- `types.py`: 共通型定義
- `errors.py`: エラー・警告クラス

**命名規則**:
- ファイル名: snake_case
- クラス名: PascalCase

**依存関係**:
- 依存可能: `risk/`, `rebalance/`, `providers/`, `visualization/`, `output/`, `types.py`, `errors.py`
- 依存禁止: なし（最上位レイヤー）

### 3.2 Core Layer - Risk (`risk/`)

**役割**: リスク指標計算のオーケストレーション、計算ロジック

**配置ファイル**:
- `calculator.py`: RiskCalculator クラス（各種リスク指標の計算）
- `metrics.py`: RiskMetricsResult クラス（計算結果のデータコンテナ）

**命名規則**:
- ファイル名: snake_case
- クラス名: PascalCase
- メソッド名: snake_case

**依存関係**:
- 依存可能: `providers/`, `output/`, `types.py`, `errors.py`
- 依存禁止: `portfolio.py`（下位レイヤーからの逆依存禁止）

**例**:
```python
# risk/calculator.py
import pandas as pd
import numpy as np
from scipy import stats
from strategy.types import RiskMetricsResult

class RiskCalculator:
    """リスク指標計算クラス（内部コンポーネント）."""

    def __init__(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        annualization_factor: int = 252,
    ) -> None:
        self._returns = returns
        self._risk_free_rate = risk_free_rate
        self._annualization_factor = annualization_factor

    def volatility(self) -> float:
        """年率ボラティリティを計算."""
        return self._returns.std() * np.sqrt(self._annualization_factor)

    def sharpe_ratio(self) -> float:
        """シャープレシオを計算."""
        ...
```

### 3.3 Rebalance Layer (`rebalance/`)

**役割**: 配分ドリフト検出、リバランスコスト計算、タイミング分析

**配置ファイル**:
- `rebalancer.py`: Rebalancer クラス（リバランス分析の統合クラス）
- `drift.py`: DriftResult, DriftDetector（配分ドリフト検出）
- `cost.py`: RebalanceCost, CostEstimator（リバランスコスト計算）

**命名規則**:
- ファイル名: snake_case
- クラス名: PascalCase
- 結果型: PascalCase + `Result` サフィックス

**依存関係**:
- 依存可能: `providers/`, `visualization/`, `types.py`, `errors.py`
- 依存禁止: `portfolio.py`, `risk/`（同一レイヤーへの依存は Protocol 経由）

**例**:
```python
# rebalance/drift.py
from dataclasses import dataclass

@dataclass
class DriftResult:
    """配分ドリフトの分析結果."""
    ticker: str
    target_weight: float
    current_weight: float
    drift: float
    drift_percent: float
    requires_rebalance: bool

class DriftDetector:
    """配分ドリフト検出クラス."""

    def detect(
        self,
        current_weights: dict[str, float],
        target_weights: dict[str, float],
        threshold: float = 0.05,
    ) -> list[DriftResult]:
        ...
```

### 3.4 Provider Layer (`providers/`)

**役割**: データソースの抽象化、market_analysis パッケージとの連携

**配置ファイル**:
- `protocol.py`: DataProvider Protocol（抽象インターフェース）
- `market_analysis.py`: MarketAnalysisProvider 実装（デフォルトプロバイダー）
- `mock.py`: MockProvider（テスト用モックプロバイダー）

**命名規則**:
- ファイル名: データソース名（snake_case）
- クラス名: データソース名 + `Provider` サフィックス

**依存関係**:
- 依存可能: `types.py`, `errors.py`, 外部ライブラリ（market_analysis）
- 依存禁止: `portfolio.py`, `risk/`, `rebalance/`, `visualization/`, `output/`（最下位レイヤー）

**例**:
```python
# providers/protocol.py
from typing import Protocol
import pandas as pd
from strategy.types import TickerInfo

class DataProvider(Protocol):
    """データプロバイダーの抽象インターフェース."""

    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """指定期間の価格データ（OHLCV）を取得."""
        ...

    def get_ticker_info(self, ticker: str) -> TickerInfo:
        """ティッカーの情報（セクター、資産クラス等）を取得."""
        ...

    def get_ticker_infos(self, tickers: list[str]) -> dict[str, TickerInfo]:
        """複数ティッカーの情報を一括取得."""
        ...
```

```python
# providers/market_analysis.py
from market_analysis.core import YFinanceFetcher
from strategy.providers.protocol import DataProvider
from strategy.types import TickerInfo

class MarketAnalysisProvider:
    """market_analysis パッケージを使用するデータプロバイダー."""

    def __init__(
        self,
        cache_config: CacheConfig | None = None,
        use_cache: bool = True,
    ) -> None:
        self._use_cache = use_cache
        self._yfinance_fetcher = YFinanceFetcher(
            cache_config=cache_config,
        )

    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        ...
```

### 3.5 Visualization Layer (`visualization/`)

**役割**: チャート生成（Plotly）

**配置ファイル**:
- `charts.py`: ChartGenerator クラス（各種チャート生成）

**命名規則**:
- ファイル名: snake_case
- クラス名: PascalCase
- メソッド名: `create_` + チャート種別

**依存関係**:
- 依存可能: `types.py`, `errors.py`, 外部ライブラリ（plotly）
- 依存禁止: `portfolio.py`, `risk/`, `rebalance/`, `providers/`

**例**:
```python
# visualization/charts.py
import plotly.graph_objects as go
from strategy.types import Holding, TickerInfo, DriftResult

class ChartGenerator:
    """チャート生成クラス."""

    def create_allocation_pie(
        self,
        holdings: list[Holding],
        ticker_infos: dict[str, TickerInfo] | None = None,
    ) -> go.Figure:
        """資産配分の円グラフを生成."""
        ...

    def create_allocation_bar(
        self,
        holdings: list[Holding],
        ticker_infos: dict[str, TickerInfo] | None = None,
    ) -> go.Figure:
        """資産配分の棒グラフを生成."""
        ...

    def create_drift_chart(
        self,
        drift_results: list[DriftResult],
    ) -> go.Figure:
        """配分ドリフトのチャートを生成."""
        ...
```

### 3.6 Output Layer (`output/`)

**役割**: 出力フォーマット変換（DataFrame, JSON, Markdown）

**配置ファイル**:
- `dataframe.py`: DataFrame出力ユーティリティ
- `json.py`: JSON出力ユーティリティ
- `markdown.py`: Markdown出力ユーティリティ

**命名規則**:
- ファイル名: snake_case（出力形式名）
- 関数名: `to_` + 出力形式

**依存関係**:
- 依存可能: `types.py`, 外部ライブラリ（pandas）
- 依存禁止: `portfolio.py`, `risk/`, `rebalance/`, `providers/`, `visualization/`

**例**:
```python
# output/markdown.py
from strategy.types import RiskMetricsResult

def to_markdown(metrics: RiskMetricsResult) -> str:
    """リスク指標をマークダウン形式のレポートに変換."""
    return f"""
## リスク指標サマリー

| 指標 | 値 |
|------|-----|
| 年率ボラティリティ | {metrics.volatility:.2%} |
| シャープレシオ | {metrics.sharpe_ratio:.2f} |
| 最大ドローダウン | {metrics.max_drawdown:.2%} |
| 95% VaR | {metrics.var_95:.2%} |
| 99% VaR | {metrics.var_99:.2%} |
"""
```

### 3.7 Utils (`utils/`)

**役割**: 横断的なユーティリティ機能

**配置ファイル**:
- `logging_config.py`: ログ設定

**命名規則**:
- ファイル名: snake_case
- 関数名: snake_case

**依存関係**:
- 依存可能: 標準ライブラリ、外部ライブラリ（structlog）
- 依存禁止: パッケージ内の他ディレクトリ

### 3.8 Types (`types.py`)

**役割**: 共通型定義

**配置内容**:
- `AssetClass`: 資産クラス Literal 型
- `PresetPeriod`: プリセット期間 Literal 型
- `Holding`: 保有銘柄（dataclass）
- `TickerInfo`: ティッカー情報（dataclass）
- `Period`: 分析期間（dataclass）
- `RiskMetricsResult`: リスク指標結果（dataclass）
- `DriftResult`: 配分ドリフト結果（dataclass）
- `RebalanceCost`: リバランスコスト結果（dataclass）

**依存関係**:
- 依存可能: 標準ライブラリ、pandas, numpy
- 依存禁止: パッケージ内の他モジュール

**例**:
```python
# types.py
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

type AssetClass = Literal["equity", "bond", "commodity", "real_estate", "cash", "other"]
type PresetPeriod = Literal["1y", "3y", "5y", "10y", "ytd", "max"]

@dataclass(frozen=True)
class Holding:
    """ポートフォリオ内の個別保有銘柄."""
    ticker: str
    weight: float

@dataclass(frozen=True)
class TickerInfo:
    """ティッカーの詳細情報."""
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    asset_class: AssetClass = "equity"

@dataclass(frozen=True)
class Period:
    """分析期間の定義."""
    start: date
    end: date
    preset: PresetPeriod | None = None
```

### 3.9 Errors (`errors.py`)

**役割**: エラー・警告クラス定義

**配置内容**:
- `StrategyError`: 基底エラー
- `DataProviderError`: データプロバイダーエラー
- `InvalidTickerError`: 無効なティッカーエラー
- `InsufficientDataError`: データ不足エラー
- `ConfigurationError`: 設定エラー
- `ValidationError`: 入力バリデーションエラー
- `StrategyWarning`: 基底警告
- `DataWarning`: データ関連警告
- `NormalizationWarning`: 正規化関連警告

**依存関係**:
- 依存可能: 標準ライブラリ
- 依存禁止: パッケージ内の他モジュール

**例**:
```python
# errors.py
class StrategyError(Exception):
    """strategy パッケージの基底例外クラス."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.cause = cause

class DataProviderError(StrategyError):
    """データプロバイダー関連のエラー."""

class InvalidTickerError(StrategyError):
    """無効なティッカーシンボルのエラー."""

class InsufficientDataError(StrategyError):
    """データ不足のエラー."""

class ConfigurationError(StrategyError):
    """設定エラー."""

class ValidationError(StrategyError):
    """入力バリデーションエラー."""

# 警告クラス
import warnings

class StrategyWarning(UserWarning):
    """strategy パッケージの基底警告クラス."""

class DataWarning(StrategyWarning):
    """データ関連の警告."""

class NormalizationWarning(StrategyWarning):
    """正規化関連の警告."""
```

## 4. テストディレクトリ詳細

### 4.1 unit/ (ユニットテスト)

**役割**: 個別関数・クラスの単体テスト

**構造**: `src/strategy/` と同じディレクトリ構造を維持

**命名規則**:
- ファイル名: `test_` + 対象ファイル名
- 関数名: `test_` + テスト内容

**例**:
```
tests/strategy/unit/
├── test_portfolio.py            # Portfolio クラスのテスト
├── test_types.py                # 型定義のテスト
├── risk/
│   ├── test_calculator.py       # RiskCalculator のテスト
│   └── test_metrics.py          # RiskMetricsResult のテスト
├── rebalance/
│   ├── test_rebalancer.py       # Rebalancer のテスト
│   ├── test_drift.py            # DriftDetector のテスト
│   └── test_cost.py             # CostEstimator のテスト
└── providers/
    └── test_market_analysis.py  # MarketAnalysisProvider のテスト
```

### 4.2 property/ (プロパティベーステスト)

**役割**: Hypothesis を使用した不変条件・境界値テスト

**命名規則**:
- ファイル名: `test_` + テスト対象
- 関数名: `test_` + プロパティ説明

**例**:
```python
# tests/strategy/property/test_portfolio.py
from hypothesis import given, strategies as st

@given(st.lists(st.floats(min_value=0.01, max_value=1.0), min_size=2, max_size=10))
def test_weights_normalize_to_one(weights):
    """正規化後の比率合計が1.0になることを確認."""
    normalized = normalize_weights(weights)
    assert abs(sum(normalized) - 1.0) < 1e-10

@given(st.lists(st.floats(min_value=-0.1, max_value=0.1), min_size=100))
def test_max_drawdown_bounds(returns):
    """最大ドローダウンが -1.0 から 0.0 の範囲内であることを確認."""
    returns_series = pd.Series(returns)
    mdd = calculate_max_drawdown(returns_series)
    assert -1.0 <= mdd <= 0.0
```

### 4.3 integration/ (統合テスト)

**役割**: 複数コンポーネントの連携テスト

**命名規則**:
- ファイル名: `test_` + シナリオ名

**例**:
```python
# tests/strategy/integration/test_end_to_end.py
import pytest

@pytest.mark.integration
def test_portfolio_analysis_with_mock_provider():
    """モックプロバイダーでのポートフォリオ分析が正常に完了することを確認."""
    provider = MockProvider(sample_prices, sample_ticker_infos)
    portfolio = Portfolio(
        holdings=[("VOO", 0.6), ("BND", 0.4)],
        provider=provider,
    )
    portfolio.set_period("1y")

    metrics = portfolio.risk_metrics()

    assert metrics.volatility > 0
    assert -1.0 <= metrics.max_drawdown <= 0.0
    assert metrics.var_95 < 0
```

## 5. ファイル配置規則

### 5.1 ソースファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|-------------|--------|---------|-----|
| Portfolio クラス | ルート | `portfolio.py` | `portfolio.py` |
| リスク計算 | `risk/` | `[name].py` | `calculator.py`, `metrics.py` |
| リバランス | `rebalance/` | `[name].py` | `rebalancer.py`, `drift.py` |
| データプロバイダー | `providers/` | `[source_name].py` | `market_analysis.py`, `mock.py` |
| チャート生成 | `visualization/` | `charts.py` | `charts.py` |
| 出力フォーマット | `output/` | `[format_name].py` | `dataframe.py`, `json.py` |
| 型定義 | ルート | `types.py` | `types.py` |
| エラー定義 | ルート | `errors.py` | `errors.py` |

### 5.2 テストファイル

| テスト種別 | 配置先 | 命名規則 | 例 |
|-----------|--------|---------|-----|
| ユニットテスト | `tests/strategy/unit/` | `test_[対象].py` | `test_calculator.py` |
| プロパティテスト | `tests/strategy/property/` | `test_[対象].py` | `test_portfolio.py` |
| 統合テスト | `tests/strategy/integration/` | `test_[シナリオ].py` | `test_end_to_end.py` |

## 6. 命名規則

### 6.1 ディレクトリ名

| カテゴリ | 規則 | 例 |
|---------|------|-----|
| レイヤーディレクトリ | 複数形、snake_case | `providers/`, `rebalance/` |
| 機能ディレクトリ | 単数形、snake_case | `risk/`, `output/` |
| テストディレクトリ | 複数形、snake_case | `unit/`, `property/`, `integration/` |

### 6.2 ファイル名

| カテゴリ | 規則 | 例 |
|---------|------|-----|
| モジュール | snake_case | `portfolio.py`, `calculator.py` |
| 初期化 | `__init__.py` | `__init__.py` |
| 型定義 | `types.py` | `types.py` |
| エラー定義 | `errors.py` | `errors.py` |

### 6.3 クラス名

| カテゴリ | 規則 | 例 |
|---------|------|-----|
| メインクラス | PascalCase | `Portfolio`, `Rebalancer` |
| 計算クラス | PascalCase + `Calculator` | `RiskCalculator` |
| 検出クラス | PascalCase + `Detector` | `DriftDetector` |
| 推定クラス | PascalCase + `Estimator` | `CostEstimator` |
| プロバイダー | PascalCase + `Provider` | `MarketAnalysisProvider`, `MockProvider` |
| 生成クラス | PascalCase + `Generator` | `ChartGenerator` |
| 結果型 | PascalCase + `Result` | `RiskMetricsResult`, `DriftResult` |
| エラー | PascalCase + `Error` | `StrategyError`, `DataProviderError` |
| 警告 | PascalCase + `Warning` | `StrategyWarning`, `DataWarning` |

## 7. 依存関係のルール

### 7.1 レイヤー間の依存方向

```
API Layer (portfolio.py, __init__.py)
    ↓ (OK)
Core Layer (risk/)
    ↓ (OK)
Rebalance Layer (rebalance/)
    ↓ (OK)
Provider Layer (providers/)

Visualization Layer (visualization/)
    ↓ (OK)
types.py, errors.py

Output Layer (output/)
    ↓ (OK)
types.py
```

**許可される依存**:
- 上位レイヤー → 下位レイヤー
- 全レイヤー → `types.py`, `errors.py`
- 全レイヤー → `utils/`

**禁止される依存**:
- 下位レイヤー → 上位レイヤー
- Provider Layer → 他のすべてのレイヤー（最下位）
- Visualization Layer と Output Layer 間の相互依存

### 7.2 依存関係マトリクス

| From \ To | portfolio.py | risk/ | rebalance/ | providers/ | visualization/ | output/ | types.py | errors.py | utils/ |
|-----------|--------------|-------|------------|------------|----------------|---------|----------|-----------|--------|
| portfolio.py | - | OK | OK | OK | OK | OK | OK | OK | OK |
| risk/ | NG | - | NG | OK | NG | OK | OK | OK | OK |
| rebalance/ | NG | NG | - | OK | OK | NG | OK | OK | OK |
| providers/ | NG | NG | NG | - | NG | NG | OK | OK | OK |
| visualization/ | NG | NG | NG | NG | - | NG | OK | OK | OK |
| output/ | NG | NG | NG | NG | NG | - | OK | NG | OK |

### 7.3 循環依存の回避

**問題のあるパターン**:
```python
# portfolio.py
from strategy.risk.calculator import RiskCalculator

# risk/calculator.py
from strategy.portfolio import Portfolio  # 循環依存
```

**解決策**: Protocol を使用
```python
# types.py に Protocol を定義
from typing import Protocol

class PortfolioProtocol(Protocol):
    @property
    def holdings(self) -> list[Holding]: ...
    @property
    def tickers(self) -> list[str]: ...
    @property
    def weights(self) -> dict[str, float]: ...

# risk/calculator.py
from strategy.types import PortfolioProtocol

class RiskCalculator:
    def __init__(self, returns: pd.Series, ...) -> None:
        ...  # リターンデータのみを受け取り、Portfolio への依存なし
```

## 8. スケーリング戦略

### 8.1 新規データプロバイダーの追加

新しいデータプロバイダー（例: Factset）を追加する場合:

```
providers/
├── protocol.py
├── market_analysis.py
├── mock.py
└── factset.py                   # 新規追加
```

**手順**:
1. `providers/` 配下に新ファイルを作成
2. `DataProvider` Protocol を実装
3. `providers/__init__.py` でエクスポート
4. `src/strategy/__init__.py` の `__all__` に追加

### 8.2 新規リスク指標の追加

新しいリスク指標（例: Calmar Ratio）を追加する場合:

```python
# risk/calculator.py に追加
class RiskCalculator:
    ...

    def calmar_ratio(self) -> float:
        """カルマーレシオを計算."""
        annualized_return = self._calculate_annualized_return()
        max_dd = self.max_drawdown()
        if max_dd == 0:
            return float('inf') if annualized_return > 0 else 0.0
        return annualized_return / abs(max_dd)
```

### 8.3 リバランス戦略の拡張（P1）

新しいリバランス戦略を追加する場合:

```
rebalance/
├── __init__.py
├── rebalancer.py
├── drift.py
├── cost.py
└── strategies/                   # 新規追加
    ├── __init__.py
    ├── protocol.py               # RebalanceStrategy Protocol
    ├── periodic.py               # PeriodicRebalanceStrategy
    └── threshold.py              # ThresholdRebalanceStrategy
```

### 8.4 ファイルサイズの管理

**分割の目安**:
- 1ファイル: 300行以下を推奨
- 300-500行: リファクタリングを検討
- 500行以上: 分割を強く推奨

**分割例**:
```python
# 分割前: risk/calculator.py (500行)

# 分割後
risk/
├── __init__.py
├── calculator.py            # RiskCalculator (200行)
├── metrics.py               # RiskMetricsResult (150行)
└── algorithms/              # 新規追加
    ├── __init__.py
    ├── volatility.py        # ボラティリティ計算
    ├── drawdown.py          # ドローダウン計算
    └── var.py               # VaR計算
```

## 9. 公開API (`__init__.py`)

### 9.1 パッケージルート

```python
# src/strategy/__init__.py
"""strategy - ポートフォリオ管理・分析ライブラリ"""

# Main Classes
from strategy.portfolio import Portfolio
from strategy.rebalance.rebalancer import Rebalancer

# Risk
from strategy.risk.metrics import RiskMetricsResult

# Providers
from strategy.providers.protocol import DataProvider
from strategy.providers.market_analysis import MarketAnalysisProvider
from strategy.providers.mock import MockProvider

# Types
from strategy.types import (
    Holding,
    TickerInfo,
    Period,
    AssetClass,
    PresetPeriod,
)

# Rebalance Results
from strategy.rebalance.drift import DriftResult
from strategy.rebalance.cost import RebalanceCost

# Errors
from strategy.errors import (
    StrategyError,
    DataProviderError,
    InvalidTickerError,
    InsufficientDataError,
    ConfigurationError,
    ValidationError,
)

# Warnings
from strategy.errors import (
    StrategyWarning,
    DataWarning,
    NormalizationWarning,
)

__all__ = [
    # Main Classes
    "Portfolio",
    "Rebalancer",
    # Risk
    "RiskMetricsResult",
    # Providers
    "DataProvider",
    "MarketAnalysisProvider",
    "MockProvider",
    # Types
    "Holding",
    "TickerInfo",
    "Period",
    "AssetClass",
    "PresetPeriod",
    # Rebalance Results
    "DriftResult",
    "RebalanceCost",
    # Errors
    "StrategyError",
    "DataProviderError",
    "InvalidTickerError",
    "InsufficientDataError",
    "ConfigurationError",
    "ValidationError",
    # Warnings
    "StrategyWarning",
    "DataWarning",
    "NormalizationWarning",
]
```

### 9.2 サブパッケージ

**risk/__init__.py**:
```python
from strategy.risk.calculator import RiskCalculator
from strategy.risk.metrics import RiskMetricsResult

__all__ = ["RiskCalculator", "RiskMetricsResult"]
```

**rebalance/__init__.py**:
```python
from strategy.rebalance.rebalancer import Rebalancer
from strategy.rebalance.drift import DriftResult, DriftDetector
from strategy.rebalance.cost import RebalanceCost, CostEstimator

__all__ = [
    "Rebalancer",
    "DriftResult",
    "DriftDetector",
    "RebalanceCost",
    "CostEstimator",
]
```

**providers/__init__.py**:
```python
from strategy.providers.protocol import DataProvider
from strategy.providers.market_analysis import MarketAnalysisProvider
from strategy.providers.mock import MockProvider

__all__ = ["DataProvider", "MarketAnalysisProvider", "MockProvider"]
```

**visualization/__init__.py**:
```python
from strategy.visualization.charts import ChartGenerator

__all__ = ["ChartGenerator"]
```

**output/__init__.py**:
```python
from strategy.output.dataframe import to_dataframe
from strategy.output.json import to_dict
from strategy.output.markdown import to_markdown

__all__ = ["to_dataframe", "to_dict", "to_markdown"]
```

## 10. アーキテクチャ対応表

| アーキテクチャレイヤー | ディレクトリ | 主要コンポーネント |
|-----------------------|-------------|-------------------|
| API Layer | ルート（`portfolio.py`, `__init__.py`） | Portfolio, 公開API |
| Core Layer | `risk/` | RiskCalculator, RiskMetricsResult |
| Rebalance Layer | `rebalance/` | Rebalancer, DriftDetector, CostEstimator |
| Provider Layer | `providers/` | DataProvider Protocol, MarketAnalysisProvider |
| Visualization Layer | `visualization/` | ChartGenerator |
| Output Layer | `output/` | DataFrame/JSON/Markdown 出力 |

## 11. チェックリスト

- [x] 6層構造（API/Core/Rebalance/Provider/Visualization/Output）がディレクトリに反映されている
- [x] DataProvider プロトコルが `providers/protocol.py` に定義されている
- [x] MarketAnalysisProvider が `providers/market_analysis.py` に配置されている
- [x] MockProvider（テスト用）が `providers/mock.py` に配置されている
- [x] テストディレクトリが `unit/`, `property/`, `integration/` に分割されている
- [x] テストディレクトリがソース構造と対応している
- [x] 依存関係ルールが明確に定義されている
- [x] 命名規則が一貫している
- [x] スケーリング戦略が考慮されている
- [x] 公開APIが明確に定義されている
