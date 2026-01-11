# リポジトリ構造定義書 (Repository Structure Document)

## 1. プロジェクト構造

### 1.1 全体構成

```
finance/
├── src/
│   └── market_analysis/        # market_analysisパッケージ
│       ├── __init__.py         # 公開APIエクスポート
│       ├── py.typed            # PEP 561マーカー
│       ├── types.py            # 共通型定義
│       ├── errors.py           # エラー型定義
│       ├── api/                # インターフェース層
│       ├── core/               # コアロジック層
│       ├── utils/              # インフラ層ユーティリティ
│       └── docs/               # ライブラリドキュメント
├── tests/
│   └── market_analysis/        # market_analysisテスト
│       ├── unit/               # ユニットテスト
│       ├── property/           # プロパティベーステスト
│       ├── integration/        # 統合テスト
│       └── conftest.py         # 共通フィクスチャ
├── docs/                       # リポジトリ共通ドキュメント
├── template/                   # テンプレートパッケージ（参照専用）
└── pyproject.toml              # プロジェクト設定
```

### 1.2 レイヤー構成図

```
┌─────────────────────────────────────────────────────────────┐
│                    インターフェース層 (api/)                  │
│  market_data.py  │  analysis.py  │  chart.py               │
│  - 入力バリデーション                                        │
│  - 戻り値の型保証                                            │
│  - 公開API定義                                               │
├─────────────────────────────────────────────────────────────┤
│                    コアロジック層 (core/)                     │
│  fetcher.py  │  analyzer.py  │  visualizer.py  │ exporter.py│
│  - ビジネスロジック                                          │
│  - データ変換                                                │
│  - エラーハンドリング                                        │
├─────────────────────────────────────────────────────────────┤
│                    インフラ層 (utils/)                        │
│  cache.py  │  retry.py  │  validators.py  │ logging_config.py│
│  - 技術的関心事                                              │
│  - 外部サービス接続                                          │
│  - 横断的関心事                                              │
└─────────────────────────────────────────────────────────────┘
```

## 2. ソースコードディレクトリ詳細

### 2.1 src/market_analysis/ (パッケージルート)

#### ルートファイル

| ファイル | 役割 | 備考 |
|---------|------|------|
| `__init__.py` | 公開APIエクスポート | MarketData, Analysis, Chart, エラー型 |
| `py.typed` | PEP 561マーカー | 型ヒント対応の宣言 |
| `types.py` | 共通型定義 | dataclass, TypedDict, Literal等 |
| `errors.py` | エラー型定義 | カスタム例外クラス |

#### types.py の定義内容

```python
# 含めるべき型
- DataSource          # データソース情報
- MarketDataResult    # 市場データ取得結果
- AnalysisResult      # 分析結果
- CorrelationResult   # 相関分析結果
- AgentOutput         # AIエージェント向け出力
- FetchOptions        # データ取得オプション
- AnalysisOptions     # 分析オプション
- ChartOptions        # チャートオプション
- ExportOptions       # エクスポートオプション
- RetryConfig         # リトライ設定
```

#### errors.py の定義内容

```python
# 含めるべきエラー型
- MarketAnalysisError     # 基底エラー
- DataFetchError          # データ取得エラー
- ValidationError         # 入力バリデーションエラー
- AnalysisError           # 分析エラー
- ExportError             # エクスポートエラー
```

### 2.2 api/ (インターフェース層)

**役割**: ユーザー向け公開API。入力バリデーションと型保証を担当。

**構造**:
```
api/
├── __init__.py           # APIエクスポート
├── market_data.py        # MarketData クラス
├── analysis.py           # Analysis クラス
└── chart.py              # Chart クラス
```

**配置ファイル**:

| ファイル | 主要クラス | 責務 |
|---------|----------|------|
| `market_data.py` | MarketData | データ取得統一API |
| `analysis.py` | Analysis | テクニカル分析API |
| `chart.py` | Chart | チャート生成API |

**命名規則**:
- ファイル名: `snake_case.py`
- クラス名: `PascalCase`
- メソッド名: `snake_case`

**依存関係**:
- 依存可能: `core/`, `utils/`, `types.py`, `errors.py`
- 依存禁止: 外部API直接呼び出し（yfinance, fredapi）

**market_data.py の実装概要**:

```python
class MarketData:
    """市場データ取得の統一インターフェース"""

    def fetch_stock(symbol: str, start, end) -> pd.DataFrame
    def fetch_forex(pair: str, start, end) -> pd.DataFrame
    def fetch_fred(series_id: str, start, end) -> pd.DataFrame
    def fetch_commodity(symbol: str, start, end) -> pd.DataFrame
    def save_to_sqlite(db_path, data, table_name) -> None
    def to_agent_json(data, include_metadata) -> dict
```

### 2.3 core/ (コアロジック層)

**役割**: ビジネスロジックの実装。外部APIとの通信、データ変換、分析処理を担当。

**構造**:
```
core/
├── __init__.py           # コア層エクスポート
├── fetcher.py            # データ取得実装
├── analyzer.py           # 分析ロジック実装
├── visualizer.py         # 可視化ロジック実装
└── exporter.py           # エクスポート実装
```

**配置ファイル**:

| ファイル | 主要クラス | 責務 |
|---------|----------|------|
| `fetcher.py` | BaseDataFetcher, YFinanceFetcher, FREDFetcher | 外部APIからのデータ取得 |
| `analyzer.py` | Analyzer, CorrelationAnalyzer, IndicatorCalculator | 指標計算・統計分析 |
| `visualizer.py` | PlotlyChart, HeatmapChart | チャート生成 |
| `exporter.py` | Exporter | データ出力・フォーマット変換 |

**命名規則**:
- ファイル名: `snake_case.py`
- クラス名: `PascalCase` + 役割サフィックス（Fetcher, Analyzer等）
- 抽象クラス: `Base` プレフィックス（BaseDataFetcher）

**依存関係**:
- 依存可能: `utils/`, `types.py`, `errors.py`, 外部ライブラリ（yfinance, fredapi, plotly等）
- 依存禁止: `api/`（上位レイヤー）

**fetcher.py の実装概要**:

```python
class BaseDataFetcher(ABC):
    """データ取得基底クラス"""
    @abstractmethod
    def fetch(symbol, start, end) -> pd.DataFrame
    @abstractmethod
    def validate_symbol(symbol) -> bool

class YFinanceFetcher(BaseDataFetcher):
    """yfinanceデータ取得"""
    pass

class FREDFetcher(BaseDataFetcher):
    """FREDデータ取得"""
    pass

class DataFetcherFactory:
    """データ取得インスタンス生成"""
    @staticmethod
    def create(source: Literal["yfinance", "fred"]) -> BaseDataFetcher
```

### 2.4 utils/ (インフラ層ユーティリティ)

**役割**: 横断的関心事の処理。ログ、キャッシュ、リトライ、バリデーション等を担当。

**構造**:
```
utils/
├── __init__.py           # ユーティリティエクスポート
├── logging_config.py     # 構造化ログ設定
├── cache.py              # SQLiteキャッシュ管理
├── validators.py         # 入力バリデーション
├── retry.py              # リトライ処理
└── profiling.py          # プロファイリング
```

**配置ファイル**:

| ファイル | 主要機能 | 責務 |
|---------|---------|------|
| `logging_config.py` | `get_logger()` | structlogベースの構造化ログ |
| `cache.py` | CacheManager | SQLiteキャッシュの読み書き |
| `validators.py` | Validator | シンボル、日付等の入力検証 |
| `retry.py` | RetryHandler, `with_retry()` | 指数バックオフリトライ |
| `profiling.py` | `@profile`, `@timeit` | パフォーマンス計測 |

**命名規則**:
- ファイル名: 機能を表す `snake_case.py`
- 関数: `snake_case`
- クラス: `PascalCase`
- デコレータ: `snake_case`

**依存関係**:
- 依存可能: `types.py`, `errors.py`, 標準ライブラリ、structlog、tenacity
- 依存禁止: `api/`, `core/`（他のレイヤー）

### 2.5 docs/ (ライブラリドキュメント)

**役割**: market_analysisパッケージのドキュメント管理

**構造**:
```
docs/
├── project.md                  # プロジェクトファイル
├── library-requirements.md     # LRD（ライブラリ要求定義書）
├── functional-design.md        # 機能設計書
├── architecture.md             # アーキテクチャ設計書
├── repository-structure.md     # リポジトリ構造定義書（本ドキュメント）
├── development-guidelines.md   # 開発ガイドライン
└── glossary.md                 # 用語集
```

## 3. テストディレクトリ詳細

### 3.1 tests/market_analysis/ (テストルート)

**構造**:
```
tests/market_analysis/
├── __init__.py
├── conftest.py              # 共通フィクスチャ
├── fixtures/                # テストデータ
│   ├── sample_ohlcv.csv
│   └── sample_fred.csv
├── unit/                    # ユニットテスト
│   ├── __init__.py
│   ├── api/
│   │   ├── test_market_data.py
│   │   ├── test_analysis.py
│   │   └── test_chart.py
│   ├── core/
│   │   ├── test_fetcher.py
│   │   ├── test_analyzer.py
│   │   ├── test_visualizer.py
│   │   └── test_exporter.py
│   └── utils/
│       ├── test_cache.py
│       ├── test_validators.py
│       └── test_retry.py
├── property/                # プロパティベーステスト
│   ├── __init__.py
│   ├── test_indicators.py
│   └── test_correlation.py
├── integration/             # 統合テスト
│   ├── __init__.py
│   ├── test_fetch_flow.py
│   ├── test_analysis_flow.py
│   └── test_chart_flow.py
└── e2e/                     # E2Eテスト (CI外)
    ├── __init__.py
    └── test_real_api.py
```

### 3.2 テスト種別ごとの配置規則

| テスト種別 | 配置先 | 命名規則 | 実行頻度 |
|-----------|--------|---------|---------|
| ユニットテスト | `unit/[layer]/` | `test_[対象モジュール].py` | CI毎回 |
| プロパティテスト | `property/` | `test_[機能]_property.py` | CI毎回 |
| 統合テスト | `integration/` | `test_[フロー名]_flow.py` | CI毎回 (モック) |
| E2Eテスト | `e2e/` | `test_[シナリオ].py` | 手動/定期 |

### 3.3 テストファイルの対応関係

```
src/market_analysis/api/market_data.py
  └── tests/market_analysis/unit/api/test_market_data.py

src/market_analysis/core/fetcher.py
  └── tests/market_analysis/unit/core/test_fetcher.py

src/market_analysis/utils/cache.py
  └── tests/market_analysis/unit/utils/test_cache.py
```

### 3.4 conftest.py で定義するフィクスチャ

```python
# 含めるべきフィクスチャ
- sample_ohlcv_data      # OHLCVサンプルデータ
- sample_fred_data       # FREDサンプルデータ
- mock_yfinance          # yfinanceモック
- mock_fred              # FREDモック
- temp_cache_db          # 一時キャッシュDB
- market_data_client     # MarketDataインスタンス
```

## 4. ファイル配置規則

### 4.1 新規ファイル追加の判断基準

| 追加するコード | 配置先 | 条件 |
|---------------|-------|------|
| 公開API（ユーザー向け） | `api/` | ユーザーが直接呼び出す |
| ビジネスロジック | `core/` | データ変換、計算、外部API呼び出し |
| 横断的機能 | `utils/` | ログ、キャッシュ、バリデーション等 |
| 型定義 | `types.py` | dataclass、TypedDict等 |
| エラー定義 | `errors.py` | カスタム例外クラス |

### 4.2 ファイル命名規則

| ファイル種別 | 命名規則 | 例 |
|-------------|---------|-----|
| モジュール | `snake_case.py` | `market_data.py` |
| テスト | `test_[対象].py` | `test_market_data.py` |
| 型定義 | `types.py` または `[domain]_types.py` | `types.py` |
| 定数 | `constants.py` | `constants.py` |

### 4.3 クラス・関数命名規則

| 要素 | 命名規則 | 例 |
|-----|---------|-----|
| クラス | PascalCase | `MarketData`, `DataFetcher` |
| 関数 | snake_case | `fetch_stock`, `calculate_sma` |
| 定数 | UPPER_SNAKE | `DEFAULT_TTL_HOURS`, `MAX_RETRIES` |
| プライベート | _prefix | `_validate_symbol`, `_cache` |

## 5. 依存関係ルール

### 5.1 レイヤー間の依存方向

```
api/ (インターフェース層)
    ↓ (OK)
core/ (コアロジック層)
    ↓ (OK)
utils/ (インフラ層)

types.py, errors.py ← 全レイヤーから参照可能
```

**許可される依存**:
- `api/` → `core/`, `utils/`, `types.py`, `errors.py`
- `core/` → `utils/`, `types.py`, `errors.py`
- `utils/` → `types.py`, `errors.py`

**禁止される依存**:
- `core/` → `api/` (下位から上位への依存)
- `utils/` → `api/`, `core/` (インフラ層から他レイヤーへの依存)

### 5.2 外部ライブラリの依存配置

| 外部ライブラリ | 使用可能なレイヤー | 理由 |
|---------------|------------------|------|
| yfinance | `core/fetcher.py` | データ取得はコア層の責務 |
| fredapi | `core/fetcher.py` | データ取得はコア層の責務 |
| plotly | `core/visualizer.py` | 可視化はコア層の責務 |
| pandas | 全レイヤー | データ構造として全体で使用 |
| structlog | `utils/logging_config.py` | ログはインフラ層の責務 |
| tenacity | `utils/retry.py` | リトライはインフラ層の責務 |
| pydantic | `utils/validators.py` | バリデーションはインフラ層の責務 |

### 5.3 循環依存の回避

```python
# 悪い例: core/analyzer.py と core/fetcher.py の循環依存
# core/analyzer.py
from core.fetcher import DataFetcher  # NG: 循環の可能性

# 良い例: Protocolで依存を切り離す
# types.py
from typing import Protocol

class DataFetcherProtocol(Protocol):
    def fetch(self, symbol: str, ...) -> pd.DataFrame: ...

# core/analyzer.py
from types import DataFetcherProtocol  # OK: 型定義への依存
```

## 6. スケーリング戦略

### 6.1 機能追加時の配置方針

**小規模機能（単一ファイル）**:
```
# 新しいテクニカル指標を追加
core/analyzer.py に新メソッドを追加
```

**中規模機能（サブモジュール化）**:
```
# 機械学習機能を追加（将来）
core/
├── analyzer.py
├── visualizer.py
└── ml/                    # 新サブモジュール
    ├── __init__.py
    ├── predictor.py
    └── trainer.py
```

**大規模機能（新パッケージ）**:
```
# 完全に独立した機能（例: バックテスト）
src/
├── market_analysis/       # 既存パッケージ
└── backtest/              # 新パッケージ
```

### 6.2 ファイルサイズの管理

**分割の目安**:
- 推奨: 300行以下
- 検討: 300-500行
- 必須: 500行以上は分割

**分割例**:
```
# Before: core/analyzer.py (600行)
# 全ての分析機能が1ファイルに

# After: 責務ごとに分割
core/
├── analyzer.py              # Analyzerクラス (200行)
├── correlation_analyzer.py  # CorrelationAnalyzer (150行)
└── indicator_calculator.py  # IndicatorCalculator (200行)
```

### 6.3 データソース追加時のパターン

```python
# 新しいデータソース（例: Alpha Vantage）を追加する場合

# 1. core/fetcher.py に新クラスを追加
class AlphaVantageFetcher(BaseDataFetcher):
    """Alpha Vantageデータ取得"""
    pass

# 2. DataFetcherFactoryを更新
class DataFetcherFactory:
    @staticmethod
    def create(source: Literal["yfinance", "fred", "alphavantage"]) -> BaseDataFetcher:
        if source == "alphavantage":
            return AlphaVantageFetcher()
        ...

# 3. api/market_data.py に新メソッドを追加
class MarketData:
    def fetch_alphavantage(self, symbol: str, ...) -> pd.DataFrame:
        ...
```

## 7. 公開APIの定義

### 7.1 __init__.py でのエクスポート

```python
# src/market_analysis/__init__.py
"""market_analysis - 金融市場データ取得・分析・可視化ライブラリ"""

from market_analysis.api.market_data import MarketData
from market_analysis.api.analysis import Analysis
from market_analysis.api.chart import Chart
from market_analysis.errors import (
    MarketAnalysisError,
    DataFetchError,
    ValidationError,
    AnalysisError,
    ExportError,
)

__all__ = [
    # 主要クラス
    "MarketData",
    "Analysis",
    "Chart",
    # エラー型
    "MarketAnalysisError",
    "DataFetchError",
    "ValidationError",
    "AnalysisError",
    "ExportError",
]
```

### 7.2 サブモジュールのエクスポート

```python
# src/market_analysis/api/__init__.py
from market_analysis.api.market_data import MarketData
from market_analysis.api.analysis import Analysis
from market_analysis.api.chart import Chart

__all__ = ["MarketData", "Analysis", "Chart"]
```

```python
# src/market_analysis/core/__init__.py
from market_analysis.core.fetcher import (
    BaseDataFetcher,
    YFinanceFetcher,
    FREDFetcher,
    DataFetcherFactory,
)
from market_analysis.core.analyzer import Analyzer, IndicatorCalculator
from market_analysis.core.visualizer import PlotlyChart, HeatmapChart
from market_analysis.core.exporter import Exporter

__all__ = [
    "BaseDataFetcher",
    "YFinanceFetcher",
    "FREDFetcher",
    "DataFetcherFactory",
    "Analyzer",
    "IndicatorCalculator",
    "PlotlyChart",
    "HeatmapChart",
    "Exporter",
]
```

## 8. 設定・環境

### 8.1 環境変数

| 変数名 | 説明 | デフォルト | 使用箇所 |
|--------|------|-----------|---------|
| `FRED_API_KEY` | FRED API キー | なし（必須） | `core/fetcher.py` |
| `LOG_LEVEL` | ログレベル | INFO | `utils/logging_config.py` |
| `LOG_FORMAT` | ログフォーマット (json/text) | text | `utils/logging_config.py` |
| `MARKET_ANALYSIS_CACHE_PATH` | キャッシュDBパス | `~/.market_analysis/cache.db` | `utils/cache.py` |

### 8.2 デフォルト設定

```python
# 設定値は types.py またはモジュール内で定数として定義

# キャッシュ設定
DEFAULT_CACHE_TTL_HOURS = 24
DEFAULT_CACHE_PATH = "~/.market_analysis/cache.db"

# リトライ設定
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_RETRY_EXPONENTIAL_BASE = 2.0
DEFAULT_MAX_DELAY = 30.0

# チャート設定
DEFAULT_CHART_WIDTH = 1200
DEFAULT_CHART_HEIGHT = 600
```

## 9. 除外設定

### 9.1 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python
build/
dist/
*.egg-info/
.eggs/

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.hypothesis/

# Logs
*.log

# Cache
.market_analysis/

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
```

### 9.2 pyproject.toml (ruff除外)

```toml
[tool.ruff]
exclude = [
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
]
```

## 10. チェックリスト

### 新規ファイル追加時

- [ ] 適切なレイヤー（api/core/utils）に配置した
- [ ] 命名規則に従っている（snake_case、適切なサフィックス）
- [ ] 依存関係ルールに違反していない
- [ ] `__init__.py` でエクスポートを定義した
- [ ] 対応するテストファイルを作成した
- [ ] NumPy形式のdocstringを記述した

### 新規機能追加時

- [ ] 機能規模に応じた配置方針を選択した
- [ ] types.pyに必要な型定義を追加した
- [ ] errors.pyに必要なエラー型を追加した
- [ ] 公開APIの場合、__init__.pyに追加した
- [ ] テストカバレッジが80%以上である

### 構造変更時

- [ ] レイヤー構造を維持している
- [ ] 循環依存が発生していない
- [ ] 既存のインポートパスへの影響を確認した
- [ ] ドキュメントを更新した

## 11. LRD/アーキテクチャとの対応

| LRD要件 | ディレクトリ/ファイル | 備考 |
|---------|---------------------|------|
| FR-001: 株価データ取得 | `api/market_data.py`, `core/fetcher.py` | MarketData.fetch_stock() |
| FR-002: 為替データ取得 | `api/market_data.py`, `core/fetcher.py` | MarketData.fetch_forex() |
| FR-003: 経済指標取得 | `api/market_data.py`, `core/fetcher.py` | MarketData.fetch_fred() |
| FR-004: コモディティ取得 | `api/market_data.py`, `core/fetcher.py` | MarketData.fetch_commodity() |
| FR-005: テクニカル指標 | `api/analysis.py`, `core/analyzer.py` | Analysis.add_sma/ema等 |
| FR-006: 相関分析 | `api/analysis.py`, `core/analyzer.py` | Analysis.correlation等 |
| FR-007: チャート生成 | `api/chart.py`, `core/visualizer.py` | Chart.price_chart等 |
| FR-008: データエクスポート | `api/market_data.py`, `core/exporter.py` | save_to_sqlite等 |
| FR-009: AI向けJSON出力 | `api/market_data.py`, `core/exporter.py` | to_agent_json() |
