# strategy

投資戦略の構築・バックテスト・評価パッケージ

## 概要

このパッケージは投資戦略の設計、バックテスト、パフォーマンス評価機能を提供します。

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
from strategy import RiskCalculator, ResultFormatter, get_logger
import pandas as pd

# 1. ログ設定
logger = get_logger(__name__)

# 2. リターンデータを準備（日次リターン）
returns = pd.Series([0.01, -0.02, 0.03, 0.01, -0.01])

# 3. リスク指標を計算
calculator = RiskCalculator(returns=returns, risk_free_rate=0.02)
result = calculator.calculate()

# 4. 結果をフォーマット
formatter = ResultFormatter()
print(formatter.to_markdown(result))
```

### よくある使い方

#### ユースケース1: ポートフォリオのリスク分析

```python
from strategy import RiskCalculator, ResultFormatter
import pandas as pd

# ポートフォリオの日次リターンデータ
returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])

# リスク指標を計算（Sharpe比、Sortino比、最大ドローダウンなど）
calculator = RiskCalculator(
    returns=returns,
    risk_free_rate=0.02,         # 年率2%（無リスク金利）
    annualization_factor=252     # 日次→年率換算係数
)
metrics = calculator.calculate()

# Markdown形式で出力
formatter = ResultFormatter()
print(formatter.to_markdown(metrics))
```

#### ユースケース2: ポートフォリオの可視化

```python
from strategy import ChartGenerator
from strategy.portfolio import Portfolio

# ポートフォリオを定義（60%株式、40%債券）
portfolio = Portfolio([("VOO", 0.6), ("BND", 0.4)])

# チャートジェネレータを作成
generator = ChartGenerator(portfolio=portfolio)

# 資産配分の円グラフを生成
fig = generator.plot_allocation()
fig.show()
```
<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
strategy/
├── __init__.py
├── py.typed
├── types.py
├── errors.py
├── portfolio.py
├── docs/
├── core/
│   └── __init__.py
├── risk/
│   ├── __init__.py
│   ├── calculator.py
│   └── metrics.py
├── output/
│   ├── __init__.py
│   └── formatter.py
├── visualization/
│   ├── __init__.py
│   └── charts.py
├── rebalance/
│   ├── __init__.py
│   ├── rebalancer.py
│   └── types.py
├── providers/
│   ├── __init__.py
│   ├── protocol.py
│   └── market_analysis.py
└── utils/
    ├── __init__.py
    └── logging_config.py
```
<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->
## 実装状況

| モジュール       | 状態        | ファイル数 | 行数 |
| ---------------- | ----------- | ---------- | ---- |
| `types.py`       | ✅ 実装済み | 1          | 277  |
| `errors.py`      | ✅ 実装済み | 1          | 303  |
| `portfolio.py`   | ✅ 実装済み | 1          | 394  |
| `risk/`          | ✅ 実装済み | 3          | 990  |
| `output/`        | ✅ 実装済み | 2          | 447  |
| `visualization/` | ✅ 実装済み | 2          | 424  |
| `rebalance/`     | ✅ 実装済み | 3          | 308  |
| `providers/`     | ✅ 実装済み | 3          | 484  |
| `utils/`         | 🚧 開発中   | 2          | 367  |
| `core/`          | ⏳ 未実装   | 1          | 3    |
<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### クイックスタート

パッケージの基本的な使い方:

```python
from strategy import RiskCalculator, ResultFormatter, get_logger
import pandas as pd

# ログ設定
logger = get_logger(__name__)

# リスク指標の計算
returns = pd.Series([0.01, -0.02, 0.03, 0.01, -0.01])
calculator = RiskCalculator(returns=returns, risk_free_rate=0.02)
result = calculator.calculate()

# 結果のフォーマット
formatter = ResultFormatter()
print(formatter.to_markdown(result))
```

---

### 主要クラス

#### `RiskCalculator`

**説明**: ポートフォリオリターンから各種リスク指標（ボラティリティ、Sharpe比、Sortino比、最大ドローダウンなど）を計算

**基本的な使い方**:

```python
from strategy import RiskCalculator
import pandas as pd

# 日次リターンデータを準備
returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])

# 初期化とリスク指標の計算
calculator = RiskCalculator(
    returns=returns,
    risk_free_rate=0.02,         # 年率無リスク金利
    annualization_factor=252     # 日次データの年率換算係数
)
result = calculator.calculate()
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `calculate()` | 全リスク指標を一括計算 | `RiskMetricsResult` |
| `volatility()` | ボラティリティ（標準偏差）を計算 | `float` |
| `sharpe_ratio()` | Sharpe比を計算 | `float` |
| `sortino_ratio()` | Sortino比を計算 | `float` |
| `max_drawdown()` | 最大ドローダウンを計算 | `float` |

---

#### `RiskMetricsResult`

**説明**: リスク指標の計算結果を保持するデータクラス

**主な属性**:

| 属性 | 型 | 説明 |
|------|-----|------|
| `volatility` | `float` | 年率ボラティリティ |
| `sharpe_ratio` | `float` | Sharpe比（リスク調整後リターン） |
| `sortino_ratio` | `float` | Sortino比（下方リスク調整後リターン） |
| `max_drawdown` | `float` | 最大ドローダウン（最大下落率） |
| `var_95` | `float` | 95%信頼区間のVaR（バリュー・アット・リスク） |
| `var_99` | `float` | 99%信頼区間のVaR |
| `annualized_return` | `float` | 年率リターン |
| `cumulative_return` | `float` | 累積リターン |

---

#### `ResultFormatter`

**説明**: リスク指標結果を様々な形式（DataFrame、辞書、Markdown、HTML）に変換するフォーマッタ

**基本的な使い方**:

```python
from strategy import ResultFormatter

formatter = ResultFormatter()

# 様々な形式に変換
df = formatter.to_dataframe(result)        # DataFrame形式
data = formatter.to_dict(result)           # 辞書（JSON互換）
markdown = formatter.to_markdown(result)   # Markdown形式
html = formatter.to_html(result)           # HTML形式
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `to_dataframe(result)` | DataFrame形式に変換 | `pd.DataFrame` |
| `to_dict(result)` | 辞書形式に変換（JSON互換） | `dict[str, Any]` |
| `to_markdown(result)` | Markdown形式に変換 | `str` |
| `to_html(result)` | HTML形式に変換 | `str` |

---

#### `ChartGenerator`

**説明**: Plotlyを使用したポートフォリオの可視化（資産配分、ドリフト分析など）

**基本的な使い方**:

```python
from strategy import ChartGenerator
from strategy.portfolio import Portfolio

# ポートフォリオを定義
portfolio = Portfolio([("VOO", 0.6), ("BND", 0.4)])

# チャートジェネレータを作成
generator = ChartGenerator(portfolio=portfolio)

# 資産配分の円グラフを生成・表示
fig = generator.plot_allocation()
fig.show()
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `plot_allocation()` | 資産配分の円グラフを生成 | `go.Figure` |
| `plot_drift()` | ドリフト分析（目標比率との乖離）を可視化 | `go.Figure` |

---

### ユーティリティ関数

#### `get_logger(name, **context)`

**説明**: 構造化ロギング機能を備えたロガーインスタンスを取得

**使用例**:

```python
from strategy import get_logger

logger = get_logger(__name__)
logger.info("リスク計算開始", ticker="VOO", period="1y")
```

**パラメータ**: `name` (必須) - ロガー名、`**context` - ログに含めるコンテキスト情報

---

### 型定義

データ構造の定義。型ヒントやバリデーションに使用:

```python
from strategy.types import (
    Holding,        # ポートフォリオ保有銘柄
    Period,         # 分析期間の定義
    PresetPeriod,   # プリセット期間（"1y", "3y" など）
    TickerInfo,     # ティッカー情報（セクター、資産クラスなど）
)
```
<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値     |
| -------------------- | ------ |
| Python ファイル数    | 20     |
| 総行数（実装コード） | 4,020  |
| モジュール数         | 8      |
| テストファイル数     | 13     |
| テストカバレッジ     | N/A    |
<!-- END: STATS -->

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
