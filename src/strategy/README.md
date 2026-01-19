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
df = formatter.to_dataframe(result)
print(df)
```

### よくある使い方

#### ユースケース1: ポートフォリオのリスク分析

```python
from strategy import RiskCalculator, ResultFormatter
import pandas as pd

# ポートフォリオの日次リターンデータを用意
returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])

# リスク指標を計算
calculator = RiskCalculator(
    returns=returns,
    risk_free_rate=0.02,         # 年率2%（無リスク金利）
    annualization_factor=252     # 日次データの年率換算係数
)
metrics = calculator.calculate()

# Markdown形式で表示
formatter = ResultFormatter()
print(formatter.to_markdown(metrics))
```

#### ユースケース2: ポートフォリオの可視化

```python
from strategy import ChartGenerator
from strategy.portfolio import Portfolio

# ポートフォリオを作成（ティッカーと比率のペア）
portfolio = Portfolio([("VOO", 0.6), ("BND", 0.4)])

# 資産配分チャートを生成
generator = ChartGenerator(portfolio=portfolio)
fig = generator.plot_allocation()
fig.show()  # または fig.write_html("allocation.html")
```

#### ユースケース3: リバランスの判定

```python
from strategy.portfolio import Portfolio
from strategy.rebalance import Rebalancer

# 目標配分
target = Portfolio([("VOO", 0.6), ("BND", 0.4)])

# 現在の配分
current = Portfolio([("VOO", 0.65), ("BND", 0.35)])

# ドリフトを検出
rebalancer = Rebalancer(target_portfolio=target, threshold=0.05)
drift = rebalancer.detect_drift(current)

if drift.needs_rebalance:
    print("リバランスが必要です")
    print(drift.drift_percentage)
```
<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
strategy/
├── __init__.py                       # パッケージ初期化・公開API定義
├── py.typed                          # 型ヒント対応マーカー
├── README.md                         # パッケージドキュメント
├── types.py                          # 型定義（TickerInfo等）
├── errors.py                         # カスタム例外定義
├── portfolio.py                      # Portfolioクラス
├── docs/                             # ドキュメント
├── core/                             # コアモジュール
│   └── __init__.py
├── risk/                             # リスク計算モジュール
│   ├── __init__.py
│   ├── calculator.py                 # RiskCalculator（リスク指標計算）
│   └── metrics.py                    # RiskMetricsResult（計算結果）
├── output/                           # 出力フォーマッタ
│   ├── __init__.py
│   └── formatter.py                  # ResultFormatter（DataFrame/JSON/Markdown変換）
├── visualization/                    # チャート生成
│   ├── __init__.py
│   └── charts.py                     # ChartGenerator（Plotly可視化）
├── rebalance/                        # リバランス分析
│   ├── __init__.py
│   ├── rebalancer.py                 # Rebalancer（ドリフト検出・リバランス提案）
│   └── types.py                      # DriftResult（ドリフト分析結果）
├── providers/                        # データプロバイダ
│   ├── __init__.py
│   ├── protocol.py                   # DataProvider（プロトコル定義）
│   └── market_analysis.py            # MarketAnalysisProvider（market_analysis統合）
└── utils/                            # ユーティリティ
    ├── __init__.py
    └── logging_config.py             # 構造化ロギング設定
```
<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->
## 実装状況

| モジュール         | 状態        | ファイル数 | 行数  |
| ------------------ | ----------- | ---------- | ----- |
| `types.py`         | ✅ 実装済み | 1          | 199   |
| `errors.py`        | ✅ 実装済み | 1          | 240   |
| `portfolio.py`     | ✅ 実装済み | 1          | 320   |
| `risk/`            | ✅ 実装済み | 3          | 806   |
| `output/`          | ✅ 実装済み | 2          | 381   |
| `visualization/`   | ✅ 実装済み | 2          | 339   |
| `rebalance/`       | ✅ 実装済み | 3          | 241   |
| `providers/`       | ✅ 実装済み | 3          | 391   |
| `utils/`           | ✅ 実装済み | 2          | 275   |
| `core/`            | ⏳ 未実装   | 1          | 2     |

**ステータス説明:**

- **✅ 実装済み**: コア機能が実装され、テストが整備されている
- **⏳ 未実装**: 初期化のみで実装が進行していない
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

**説明**: ポートフォリオリターンから各種リスク指標を計算するクラス

**基本的な使い方**:

```python
from strategy import RiskCalculator
import pandas as pd

# 日次リターンデータを用意
returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])

# リスク計算器を初期化
calculator = RiskCalculator(
    returns=returns,
    risk_free_rate=0.02,         # 年率2%（無リスク金利）
    annualization_factor=252     # 日次→年率換算係数
)

# 全指標を一括計算
result = calculator.calculate()
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `calculate()` | 全リスク指標を一括計算 | `RiskMetricsResult` |
| `volatility()` | 年率ボラティリティを計算 | `float` |
| `sharpe_ratio()` | シャープレシオを計算 | `float` |
| `sortino_ratio()` | ソルティノレシオを計算 | `float` |
| `max_drawdown()` | 最大ドローダウンを計算 | `float` |

---

#### `RiskMetricsResult`

**説明**: リスク指標の計算結果を保持するデータクラス

**使用例**:

```python
from strategy import RiskCalculator

# RiskCalculator.calculate() の戻り値として取得
calculator = RiskCalculator(returns=returns)
result = calculator.calculate()

# 各指標にアクセス
print(f"ボラティリティ: {result.volatility:.2%}")
print(f"シャープレシオ: {result.sharpe_ratio:.2f}")
print(f"最大ドローダウン: {result.max_drawdown:.2%}")
```

**主な属性**:

- `volatility`: 年率ボラティリティ（リスクの大きさ）
- `sharpe_ratio`: シャープレシオ（リスク調整後リターン）
- `sortino_ratio`: ソルティノレシオ（下方リスク調整後リターン）
- `max_drawdown`: 最大ドローダウン（最大下落率）
- `var_95`: 95% VaR（5%確率で発生する損失）
- `var_99`: 99% VaR（1%確率で発生する損失）
- `annualized_return`: 年率リターン
- `cumulative_return`: 累積リターン
- `beta`: ベータ値（ベンチマーク対比の感応度、オプション）
- `treynor_ratio`: トレイナーレシオ（オプション）
- `information_ratio`: インフォメーションレシオ（オプション）

---

#### `ResultFormatter`

**説明**: リスク指標結果を様々な形式（DataFrame/JSON/Markdown）に変換するフォーマッタ

**基本的な使い方**:

```python
from strategy import ResultFormatter

formatter = ResultFormatter()

# 様々な形式に変換
df = formatter.to_dataframe(result)        # DataFrame（表形式）
data = formatter.to_dict(result)           # 辞書（JSON互換）
markdown = formatter.to_markdown(result)   # Markdown（ドキュメント）
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `to_dataframe(result)` | DataFrame形式に変換 | `pd.DataFrame` |
| `to_dict(result)` | 辞書形式（JSON互換）に変換 | `dict[str, Any]` |
| `to_markdown(result)` | Markdown形式に変換 | `str` |

---

#### `ChartGenerator`

**説明**: Plotlyを使用してポートフォリオの可視化を行うチャート生成クラス

**基本的な使い方**:

```python
from strategy import ChartGenerator
from strategy.portfolio import Portfolio

# ポートフォリオを作成
portfolio = Portfolio([("VOO", 0.6), ("BND", 0.4)])

# チャート生成器を初期化
generator = ChartGenerator(portfolio=portfolio)

# 資産配分チャートを生成
fig = generator.plot_allocation()
fig.show()  # または fig.write_html("allocation.html")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `plot_allocation()` | 資産配分の円グラフを生成 | `plotly.graph_objects.Figure` |
| `plot_drift()` | ドリフト分析のバーチャートを生成 | `plotly.graph_objects.Figure` |

---

### ユーティリティ関数

#### `get_logger(name, **context)`

**説明**: 構造化ロギング機能を備えたロガーインスタンスを取得

**使用例**:

```python
from strategy import get_logger

# ロガーを取得
logger = get_logger(__name__)

# 構造化ログを出力
logger.info("リスク計算開始", ticker="VOO", period="1y")
logger.debug("中間結果", volatility=0.15)
logger.error("計算エラー", error="データ不足")
```

**パラメータ**:

- `name` (str): ロガー名（通常は `__name__`）
- `**context`: 追加のコンテキスト情報（全ログに付与）
<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値     |
| -------------------- | ------ |
| Python ファイル数    | 20     |
| 総行数（実装コード） | 3,213  |
| モジュール数         | 7      |
| テストファイル数     | 13     |
| テストカバレッジ     | N/A    |

**注**: テストカバレッジは実装完了後に計測予定です。
<!-- END: STATS -->

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
