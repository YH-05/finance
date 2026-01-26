# マイグレーションガイド: 2026年1月パッケージリファクタリング

**作成日**: 2026-01-26
**対象バージョン**: v2.0.0
**最終更新**: 2026-01-26

このガイドは、2026年1月に実施されたPythonパッケージリファクタリングに伴うマイグレーション手順を説明します。

---

## 概要

### 変更の要約

| 旧パッケージ | 新パッケージ | 変更内容 |
|-------------|-------------|----------|
| `market_analysis` | `market` + `analyze` | データ取得と分析を分離 |
| `finance` | `database` | 責務を明確化するリネーム |
| `bloomberg` | `market.bloomberg` | market パッケージに統合 |

### 新しいアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                    4. strategy (戦略構築)                        │
├─────────────────────────────────────────────────────────────────┤
│                    3. factor (ファクター分析)                    │
├─────────────────────────────────────────────────────────────────┤
│                    2. analyze (データ分析・可視化)               │  ← NEW
├─────────────────────────────────────────────────────────────────┤
│                    1. market (データ取得)                        │  ← NEW
│   database (永続化・インフラ)    rss (フィード管理)               │  ← RENAMED
└─────────────────────────────────────────────────────────────────┘
```

---

## インポート文の変更一覧

### 1. finance -> database

**ロギング**

```python
# 旧
from finance.utils.logging_config import get_logger

# 新
from database import get_logger
```

**データベースクライアント**

```python
# 旧
from finance.db import SQLiteClient, DuckDBClient
from finance.db.connection import get_db_path

# 新
from database.db import SQLiteClient, DuckDBClient, get_db_path
```

**日付ユーティリティ**

```python
# 旧
from finance.utils.date_utils import (
    calculate_weekly_comment_period,
    format_date_japanese,
    parse_date,
)

# 新
from database.utils.date_utils import (
    calculate_weekly_comment_period,
    format_date_japanese,
    parse_date,
)
```

**型定義**

```python
# 旧
from finance.types import DatabaseType, DataSource, FileFormat

# 新
from database.types import DatabaseType, DataSource, FileFormat
```

---

### 2. market_analysis -> market (データ取得)

**YFinance フェッチャー**

```python
# 旧
from market_analysis.core.yfinance_fetcher import YFinanceFetcher
from market_analysis.core.types import FetchOptions

# 新
from market.yfinance import YFinanceFetcher, FetchOptions, Interval
```

**FRED フェッチャー**

```python
# 旧
from market_analysis.core.fred_fetcher import FREDFetcher

# 新
from market.fred import FREDFetcher, FRED_API_KEY_ENV
from market.fred.types import FetchOptions
```

**データエクスポート**

```python
# 旧
from market_analysis.export import DataExporter

# 新
from market import DataExporter
# または
from market.export import DataExporter
```

**キャッシュ**

```python
# 旧
from market_analysis.utils.cache import CacheConfig

# 新
from market.cache import CacheConfig
# または
from market import CacheConfig
```

**共通型定義**

```python
# 旧
from market_analysis import DataSource, MarketDataResult

# 新
from market import DataSource, MarketDataResult
```

---

### 3. market_analysis -> analyze (データ分析)

**テクニカル分析**

```python
# 旧
from market_analysis.analysis.indicators import TechnicalIndicators

# 新
from analyze.technical.indicators import TechnicalIndicators
```

**テクニカル分析の型定義**

```python
# 旧
from market_analysis.analysis.types import (
    SMAParams,
    EMAParams,
    RSIParams,
    MACDParams,
    MACDResult,
)

# 新
from analyze.technical import (
    SMAParams,
    EMAParams,
    RSIParams,
    MACDParams,
    MACDResult,
    BollingerBandsParams,
    BollingerBandsResult,
)
```

**統計分析**

```python
# 旧（存在しない場合もあり）
from market_analysis.analysis.statistics import describe, calculate_correlation

# 新
from analyze.statistics import (
    describe,
    calculate_mean,
    calculate_std,
    calculate_correlation,
    calculate_correlation_matrix,
    calculate_beta,
    CorrelationAnalyzer,
    CorrelationMethod,
)
```

**セクター分析**

```python
# 旧
from market_analysis.analysis.sector import (
    analyze_sector_performance,
    fetch_sector_etf_returns,
)

# 新
from analyze.sector import (
    analyze_sector_performance,
    fetch_sector_etf_returns,
    get_top_bottom_sectors,
    SECTOR_ETF_MAP,
)
```

**決算カレンダー**

```python
# 旧
from market_analysis.analysis.earnings import EarningsCalendar

# 新
from analyze.earnings import EarningsCalendar, EarningsData, get_upcoming_earnings
```

**リターン計算**

```python
# 旧
from market_analysis.analysis.returns import (
    calculate_return,
    calculate_multi_period_returns,
)

# 新
from analyze.returns import (
    calculate_return,
    calculate_multi_period_returns,
    generate_returns_report,
    RETURN_PERIODS,
    TICKERS_US_INDICES,
    TICKERS_MAG7,
)
```

**可視化**

```python
# 旧
from market_analysis.visualization import ChartBuilder
from market_analysis.visualization.charts import create_candlestick

# 新
from analyze.visualization import (
    ChartBuilder,
    ChartConfig,
    ChartTheme,
    CandlestickChart,
    LineChart,
    HeatmapChart,
)
```

**統合分析（market + analyze 連携）**

```python
# 旧
from market_analysis.api.analysis import analyze_market_data

# 新
from analyze.integration import (
    MarketDataAnalyzer,
    analyze_market_data,
    fetch_and_analyze,
)
```

---

### 4. bloomberg -> market.bloomberg

```python
# 旧
from bloomberg.fetcher import BloombergFetcher
from bloomberg.types import BloombergConfig

# 新
from market.bloomberg import BloombergFetcher
from market.bloomberg.types import BloombergConfig
```

---

## 機能の移行詳細

### market パッケージ (データ取得)

| 旧モジュール | 新モジュール | 説明 |
|-------------|-------------|------|
| `market_analysis.core.yfinance_fetcher` | `market.yfinance` | Yahoo Finance データ取得 |
| `market_analysis.core.fred_fetcher` | `market.fred` | FRED 経済指標データ取得 |
| `market_analysis.export` | `market.export` | JSON/CSV/SQLite エクスポート |
| `market_analysis.utils.cache` | `market.cache` | キャッシュ機能 |
| `bloomberg` | `market.bloomberg` | Bloomberg 連携 (計画中) |
| - | `market.factset` | FactSet 連携 (計画中) |
| - | `market.alternative` | オルタナティブデータ (計画中) |

### analyze パッケージ (データ分析)

| 旧モジュール | 新モジュール | 説明 |
|-------------|-------------|------|
| `market_analysis.analysis.indicators` | `analyze.technical` | テクニカル分析 |
| - | `analyze.statistics` | 統計分析 (新規) |
| `market_analysis.analysis.sector` | `analyze.sector` | セクター分析 |
| `market_analysis.analysis.earnings` | `analyze.earnings` | 決算カレンダー |
| `market_analysis.analysis.returns` | `analyze.returns` | リターン計算 |
| `market_analysis.visualization` | `analyze.visualization` | 可視化 |
| `market_analysis.api.analysis` | `analyze.integration` | market 連携 |

### database パッケージ (インフラ)

| 旧モジュール | 新モジュール | 説明 |
|-------------|-------------|------|
| `finance.db` | `database.db` | SQLite/DuckDB クライアント |
| `finance.utils.logging_config` | `database` (トップレベル) | 構造化ロギング |
| `finance.utils.date_utils` | `database.utils.date_utils` | 日付ユーティリティ |
| `finance.types` | `database.types` | 共通型定義 |
| - | `database.parquet_schema` | Parquet スキーマ定義 (新規) |
| - | `database.utils.format_converter` | Parquet/JSON 変換 (新規) |

---

## 一括置換スクリプト

以下のスクリプトでインポート文を一括置換できます:

```bash
#!/bin/bash

# finance -> database
find src/ tests/ -name "*.py" -exec sed -i '' \
    -e 's/from finance\.utils\.logging_config import get_logger/from database import get_logger/g' \
    -e 's/from finance\.db import/from database.db import/g' \
    -e 's/from finance\.types import/from database.types import/g' \
    -e 's/from finance\.utils\.date_utils import/from database.utils.date_utils import/g' \
    {} \;

# market_analysis.core -> market
find src/ tests/ -name "*.py" -exec sed -i '' \
    -e 's/from market_analysis\.core\.yfinance_fetcher import/from market.yfinance import/g' \
    -e 's/from market_analysis\.core\.fred_fetcher import/from market.fred import/g' \
    -e 's/from market_analysis\.export import/from market.export import/g' \
    {} \;

# market_analysis.analysis -> analyze
find src/ tests/ -name "*.py" -exec sed -i '' \
    -e 's/from market_analysis\.analysis\.indicators import/from analyze.technical.indicators import/g' \
    -e 's/from market_analysis\.analysis\.sector import/from analyze.sector import/g' \
    -e 's/from market_analysis\.analysis\.earnings import/from analyze.earnings import/g' \
    -e 's/from market_analysis\.analysis\.returns import/from analyze.returns import/g' \
    -e 's/from market_analysis\.visualization import/from analyze.visualization import/g' \
    {} \;

# bloomberg -> market.bloomberg
find src/ tests/ -name "*.py" -exec sed -i '' \
    -e 's/from bloomberg\./from market.bloomberg./g' \
    {} \;
```

---

## よくある問題と解決策

### Q1: `ModuleNotFoundError: No module named 'finance'`

**原因**: 旧パッケージ名 `finance` が使用されています。

**解決策**: `database` に置き換えてください。

```python
# 旧
from finance import get_logger

# 新
from database import get_logger
```

### Q2: `ModuleNotFoundError: No module named 'market_analysis'`

**原因**: 旧パッケージ名 `market_analysis` が使用されています。

**解決策**: データ取得は `market`、分析は `analyze` に分けて置き換えてください。

```python
# データ取得の場合
# 旧
from market_analysis.core.yfinance_fetcher import YFinanceFetcher
# 新
from market.yfinance import YFinanceFetcher

# 分析の場合
# 旧
from market_analysis.analysis.indicators import TechnicalIndicators
# 新
from analyze.technical.indicators import TechnicalIndicators
```

### Q3: `ImportError: cannot import name 'xxx' from 'market'`

**原因**: 新しい API エクスポート構造に適合していません。

**解決策**: 各パッケージの `__init__.py` でエクスポートされている API を確認してください。

```python
# トップレベルからインポート可能な型
from market import (
    DataSource,
    MarketDataResult,
    DataExporter,
    MarketConfig,
    CacheConfig,
)

# サブモジュールから直接インポート
from market.yfinance import YFinanceFetcher, FetchOptions
from market.fred import FREDFetcher
```

### Q4: `AttributeError: module 'analyze' has no attribute 'xxx'`

**原因**: サブモジュールを直接インポートせずにトップレベルからアクセスしようとしています。

**解決策**: サブモジュールを明示的にインポートしてください。

```python
# 誤り
import analyze
indicators = analyze.TechnicalIndicators  # AttributeError

# 正しい
from analyze.technical.indicators import TechnicalIndicators
```

### Q5: データフォーマットの互換性

**原因**: Parquet スキーマが更新されている可能性があります。

**解決策**:

1. 新しいスキーマ定義を確認:

```python
from database.parquet_schema import (
    STOCK_PRICE_SCHEMA,
    ECONOMIC_INDICATOR_SCHEMA,
    validate_stock_price_schema,
)
```

2. 既存データの変換が必要な場合は `database.utils.format_converter` を使用:

```python
from database.utils.format_converter import parquet_to_json, json_to_parquet
```

### Q6: テストが失敗する

**原因**: テストファイルのインポートが更新されていません。

**解決策**:

1. テストファイルのインポートを更新
2. フィクスチャの参照パスを確認
3. モックのターゲットパスを新しいモジュールパスに変更

```python
# 旧
@patch("market_analysis.core.yfinance_fetcher.yf.download")
def test_fetch(mock_download):
    ...

# 新
@patch("market.yfinance.fetcher.yf.download")
def test_fetch(mock_download):
    ...
```

---

## 非互換の変更

### 1. 削除された機能

以下の機能は新パッケージに移行されていません:

- `market_analysis.api.batch` - 代替: 各フェッチャーを直接使用
- `market_analysis.utils.deprecated_module` - 削除

### 2. 名前が変更された関数

| 旧名 | 新名 | パッケージ |
|-----|------|-----------|
| `create_chart` | `ChartBuilder.build()` | analyze.visualization |
| `get_sector_returns` | `fetch_sector_etf_returns` | analyze.sector |

### 3. シグネチャが変更された関数

**TechnicalIndicators.calculate_macd**

```python
# 旧
result = TechnicalIndicators.calculate_macd(prices, fast=12, slow=26)

# 新 (パラメータ名の変更)
result = TechnicalIndicators.calculate_macd(
    prices,
    fast_period=12,
    slow_period=26,
    signal_period=9
)
```

---

## チェックリスト

マイグレーション完了を確認するためのチェックリスト:

### インポート更新

- [ ] `finance` -> `database` の全インポートを更新
- [ ] `market_analysis.core` -> `market` の全インポートを更新
- [ ] `market_analysis.analysis` -> `analyze` の全インポートを更新
- [ ] `market_analysis.visualization` -> `analyze.visualization` の全インポートを更新
- [ ] `bloomberg` -> `market.bloomberg` の全インポートを更新

### テスト

- [ ] 全テストファイルのインポートを更新
- [ ] モックのパスを更新
- [ ] `make test` が成功

### 品質チェック

- [ ] `make format` が成功
- [ ] `make lint` が成功
- [ ] `make typecheck` が成功
- [ ] `make check-all` が成功

### 動作確認

- [ ] 主要機能の動作を手動確認
- [ ] データ取得が正常に動作
- [ ] 分析機能が正常に動作
- [ ] 可視化が正常に動作

---

## サポート

問題が発生した場合は、以下のリソースを参照してください:

- [パッケージリファクタリング計画書](../project/package-refactoring.md)
- [4層アーキテクチャ設計書](../architecture/packages.md)
- [各パッケージの README](../../src/)
  - [market README](../../src/market/README.md)
  - [analyze README](../../src/analyze/README.md)
  - [database README](../../src/database/README.md)

GitHub Issues で質問や問題を報告してください:
https://github.com/YH-05/finance/issues

---

## 更新履歴

| 日付 | 更新内容 |
|------|---------|
| 2026-01-26 | 初版作成 |
