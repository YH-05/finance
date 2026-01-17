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
from strategy import RiskCalculator, ResultFormatter
import pandas as pd

# 1. リターンデータを準備
returns = pd.Series([0.01, -0.02, 0.03, 0.01, -0.01])

# 2. リスク指標を計算
calculator = RiskCalculator(returns, risk_free_rate=0.02)
result = calculator.calculate()

# 3. 結果をフォーマット
formatter = ResultFormatter()
df = formatter.to_dataframe(result)
print(df)
```

### よくある使い方

#### ユースケース1: ポートフォリオのリスク分析

```python
from strategy import RiskCalculator, ResultFormatter
import pandas as pd

# ポートフォリオのリターンデータ
returns = pd.Series([...])  # 日次リターン

# リスク指標を計算
calculator = RiskCalculator(
    returns=returns,
    risk_free_rate=0.02,  # 年率2%
    annualization_factor=252  # 日次データ
)
metrics = calculator.calculate()

# Markdown形式で出力
formatter = ResultFormatter()
markdown = formatter.to_markdown(metrics)
print(markdown)
```

#### ユースケース2: 結果のエクスポート

```python
from strategy import RiskCalculator, ResultFormatter

# リスク指標を計算
calculator = RiskCalculator(returns)
result = calculator.calculate()

# 様々な形式で出力
formatter = ResultFormatter()

# DataFrame形式
df = formatter.to_dataframe(result)

# 辞書形式（JSON互換）
data_dict = formatter.to_dict(result)

# Markdown形式（レポート用）
markdown = formatter.to_markdown(result)
```
<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->
## ディレクトリ構成

```
strategy/
├── __init__.py
├── py.typed
├── README.md
├── types.py                          # 型定義
├── errors.py                         # エラー定義
├── portfolio.py                      # ポートフォリオ定義
├── core/                             # コアモジュール
│   └── __init__.py
├── risk/                             # リスク計算モジュール
│   ├── __init__.py
│   ├── calculator.py                 # RiskCalculator
│   └── metrics.py                    # RiskMetricsResult
├── output/                           # 出力フォーマッタ
│   ├── __init__.py
│   └── formatter.py                  # ResultFormatter
├── rebalance/                        # リバランス分析
│   ├── __init__.py
│   ├── rebalancer.py                 # Rebalancer
│   └── types.py                      # DriftResult
├── providers/                        # データプロバイダ
│   ├── __init__.py
│   ├── protocol.py                   # DataProvider
│   └── market_analysis.py            # MarketAnalysisProvider
├── utils/                            # ユーティリティ
│   ├── __init__.py
│   └── logging_config.py             # 構造化ロギング設定
└── docs/                             # ドキュメント
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

| モジュール      | 状態      | ファイル数 | 行数 | テスト |
| --------------- | --------- | ---------- | ---- | ------ |
| `types.py`      | ✅ 実装済み | 1          | 278  | 1      |
| `errors.py`     | ✅ 実装済み | 1          | 29   | 1      |
| `portfolio.py`  | ✅ 実装済み | 1          | 142  | 1      |
| `risk/`         | ✅ 実装済み | 3          | 746  | 3      |
| `output/`       | ✅ 実装済み | 2          | 447  | 1      |
| `rebalance/`    | ✅ 実装済み | 3          | 308  | 2      |
| `providers/`    | ✅ 実装済み | 3          | 484  | 3      |
| `utils/`        | ✅ 実装済み | 2          | 367  | 0      |
| `core/`         | ⏳ 未実装  | 1          | 3    | 0      |

**ステータス説明:**

- **✅ 実装済み**: コア機能が実装され、テスト構造が整備されている
- **⏳ 未実装**: 初期化のみで実装が進行していない
<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->
## 公開 API

### クイックスタート

パッケージの基本的な使い方:

```python
from strategy import RiskCalculator, ResultFormatter
import pandas as pd

# リスク指標の計算
calculator = RiskCalculator(returns=pd.Series([0.01, -0.02, 0.03]))
result = calculator.calculate()

# 結果のフォーマット
formatter = ResultFormatter()
print(formatter.to_markdown(result))
```

### 主要クラス

#### `RiskCalculator`

**説明**: ポートフォリオリターンからリスク指標を計算するクラス

**基本的な使い方**:

```python
from strategy import RiskCalculator
import pandas as pd

# 初期化
calculator = RiskCalculator(
    returns=pd.Series([...]),  # 日次リターン
    risk_free_rate=0.02,       # 年率2%
    annualization_factor=252   # 日次データ
)

# リスク指標を計算
result = calculator.calculate()
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `calculate()` | 全リスク指標を計算 | `RiskMetricsResult` |
| `volatility()` | 年率ボラティリティ | `float` |
| `sharpe_ratio()` | シャープレシオ | `float` |
| `sortino_ratio()` | ソルティノレシオ | `float` |
| `max_drawdown()` | 最大ドローダウン | `float` |

---

#### `ResultFormatter`

**説明**: リスク指標結果を様々な形式に変換するフォーマッタ

**基本的な使い方**:

```python
from strategy import ResultFormatter

# 初期化
formatter = ResultFormatter()

# 様々な形式に変換
df = formatter.to_dataframe(result)        # DataFrame
data = formatter.to_dict(result)           # 辞書（JSON互換）
markdown = formatter.to_markdown(result)   # Markdown
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `to_dataframe(result)` | DataFrame形式に変換 | `pd.DataFrame` |
| `to_dict(result)` | 辞書形式に変換 | `dict[str, Any]` |
| `to_markdown(result)` | Markdown形式に変換 | `str` |

---

### データクラス

#### `RiskMetricsResult`

**説明**: リスク指標の計算結果を保持するデータクラス

**使用例**:

```python
from strategy import RiskMetricsResult

# RiskCalculator.calculate() の戻り値として取得
result = calculator.calculate()

# 各指標にアクセス
print(result.volatility)         # ボラティリティ
print(result.sharpe_ratio)       # シャープレシオ
print(result.max_drawdown)       # 最大ドローダウン
```

**主な属性**:

- `volatility`: 年率ボラティリティ
- `sharpe_ratio`: シャープレシオ
- `sortino_ratio`: ソルティノレシオ
- `max_drawdown`: 最大ドローダウン
- `var_95`: 95% VaR
- `var_99`: 99% VaR
- `annualized_return`: 年率リターン
- `cumulative_return`: 累積リターン

---

### ユーティリティ関数

#### `get_logger(name, **context)`

**説明**: 構造化ロギング機能を備えたロガーインスタンスを取得

**使用例**:

```python
from strategy import get_logger

logger = get_logger(__name__)
logger.info("処理開始", user_id=123)
```

---

### 型定義

データ構造の定義。型ヒントやバリデーションに使用:

```python
from strategy.types import (
    AssetClass,      # 資産クラス定義
    Holding,         # 保有銘柄
    TickerInfo,      # ティッカー情報
    Period,          # 分析期間
    PresetPeriod,    # プリセット期間
)
```
<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->
## 統計

| 項目                 | 値     |
| -------------------- | ------ |
| Python ファイル数    | 18     |
| 総行数（実装コード） | 3,349  |
| モジュール数         | 6      |
| テストファイル数     | 12     |
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
