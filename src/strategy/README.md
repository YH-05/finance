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

#### ポートフォリオのリスク分析

```python
from strategy import RiskCalculator, ResultFormatter
import pandas as pd

# ポートフォリオの日次リターンデータ
returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])

# リスク指標を計算
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

### 主要クラス

#### `RiskCalculator`

ポートフォリオリターンから各種リスク指標を計算するクラス。

```python
from strategy import RiskCalculator
import pandas as pd

returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
calculator = RiskCalculator(returns=returns, risk_free_rate=0.02)
result = calculator.calculate()
```

**主なメソッド**: `calculate()`, `volatility()`, `sharpe_ratio()`, `sortino_ratio()`, `max_drawdown()`

---

#### `RiskMetricsResult`

リスク指標の計算結果を保持するデータクラス。

**主な属性**: `volatility`, `sharpe_ratio`, `sortino_ratio`, `max_drawdown`, `var_95`, `var_99`, `annualized_return`, `cumulative_return`

---

#### `ResultFormatter`

リスク指標結果を様々な形式に変換するフォーマッタ。

```python
from strategy import ResultFormatter

formatter = ResultFormatter()
df = formatter.to_dataframe(result)        # DataFrame
data = formatter.to_dict(result)           # 辞書
markdown = formatter.to_markdown(result)   # Markdown
```

---

#### `ChartGenerator`

Plotlyを使用したポートフォリオ可視化。

```python
from strategy import ChartGenerator
from strategy.portfolio import Portfolio

portfolio = Portfolio([("VOO", 0.6), ("BND", 0.4)])
generator = ChartGenerator(portfolio=portfolio)
fig = generator.plot_allocation()
fig.show()
```

---

### ユーティリティ関数

#### `get_logger(name, **context)`

構造化ロギング機能を備えたロガーインスタンスを取得。

```python
from strategy import get_logger

logger = get_logger(__name__)
logger.info("リスク計算開始", ticker="VOO", period="1y")
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
