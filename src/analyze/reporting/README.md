# analyze.reporting

包括的マーケットレポート生成モジュール。

## 概要

週次マーケットレポート作成に最適化されたレポート生成モジュールです。パフォーマンス・通貨・金利・経済イベントの 4 領域を分析し、AI エージェントが解釈しやすい JSON 形式（`to_dict()`）で結果を出力します。各領域に通常版と AI エージェント向け（`*4Agent`）の 2 種類のアナライザーを提供。

**分析領域:**

| 領域 | 通常版 | エージェント版 | 結果クラス |
|------|--------|--------------|-----------|
| パフォーマンス | `PerformanceAnalyzer` | `PerformanceAnalyzer4Agent` | `PerformanceResult` |
| 通貨 | `CurrencyAnalyzer` | `CurrencyAnalyzer4Agent` | `CurrencyResult` |
| 金利 | `InterestRateAnalyzer` | `InterestRateAnalyzer4Agent` | `InterestRateResult` |
| 経済イベント | `UpcomingEventsAnalyzer` | `UpcomingEvents4Agent` | `UpcomingEventsResult` |

**追加分析モジュール:**

| モジュール | 説明 |
|-----------|------|
| `metal` | 貴金属分析（金、銀、プラチナ等） |
| `us_treasury` | 米国債分析 |
| `vix` | VIX（恐怖指数）分析 |

## クイックスタート

### パフォーマンス分析（AI エージェント向け）

```python
from analyze.reporting import PerformanceAnalyzer4Agent

analyzer = PerformanceAnalyzer4Agent()

# グループ別パフォーマンス取得
result = analyzer.get_group_performance("mag7")

# クロスセクション分析
result = analyzer.analyze_cross_section(
    data=df,
    group="MAG7",
    periods=["1d", "1w", "1mo", "ytd"],
)

# JSON 形式でエクスポート
data = result.to_dict()
# → {'group': 'MAG7', 'symbols': {...}, 'summary': {...}, ...}
```

### 通貨分析

```python
from analyze.reporting import CurrencyAnalyzer4Agent

analyzer = CurrencyAnalyzer4Agent()
result = analyzer.analyze()
print(result.to_dict())
# → {'group': 'currencies', 'base_currency': 'JPY', 'symbols': {...}, ...}
```

### 金利分析

```python
from analyze.reporting import InterestRateAnalyzer4Agent

analyzer = InterestRateAnalyzer4Agent()
result = analyzer.analyze()
print(result.to_dict())
# → {'group': 'interest_rates', 'data': {'DGS10': {'latest': 4.25, ...}},
#     'yield_curve': {'is_inverted': True, ...}, ...}
```

### 今後のイベント

```python
from analyze.reporting import UpcomingEvents4Agent

analyzer = UpcomingEvents4Agent()
result = analyzer.analyze(days_ahead=14)
print(result.to_dict())
# → {'earnings': [...], 'economic_releases': [...], 'summary': {...}}
```

### 追加分析

```python
from analyze.reporting import metal, us_treasury, vix

metal_data = metal.analyze()       # 貴金属
treasury_data = us_treasury.analyze()  # 米国債
vix_data = vix.analyze()           # VIX
```

## API リファレンス

### エージェント向けアナライザー

| クラス | 主要メソッド | 結果クラス |
|--------|------------|-----------|
| `PerformanceAnalyzer4Agent` | `get_group_performance(group)`, `analyze_cross_section(data, group, periods)` | `PerformanceResult` |
| `CurrencyAnalyzer4Agent` | `analyze()` | `CurrencyResult` |
| `InterestRateAnalyzer4Agent` | `analyze()` | `InterestRateResult` |
| `UpcomingEvents4Agent` | `analyze(days_ahead=14)` | `UpcomingEventsResult` |

### 結果クラス（dataclass）

**PerformanceResult:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `group` | `str` | シンボルグループ名 |
| `subgroup` | `str \| None` | サブグループ名 |
| `generated_at` | `str` | 生成日時（ISO 形式） |
| `periods` | `list[str]` | 分析対象期間 |
| `symbols` | `dict[str, dict[str, float]]` | シンボル → 期間 → 騰落率 |
| `summary` | `dict[str, Any]` | サマリー（最良/最悪パフォーマー） |
| `latest_dates` | `dict[str, str]` | 最新取引日 |
| `data_freshness` | `dict[str, Any]` | データ鮮度情報 |

**CurrencyResult:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `base_currency` | `str` | 基準通貨（JPY） |
| `symbols` | `dict[str, dict[str, float]]` | 通貨ペア → 期間 → 騰落率 |

**InterestRateResult:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `data` | `dict[str, dict[str, Any]]` | シリーズ → 最新値 + 変化量 |
| `yield_curve` | `dict[str, Any]` | イールドカーブ分析 |

**UpcomingEventsResult:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `period` | `dict[str, str]` | 対象期間（start, end） |
| `earnings` | `list[dict[str, Any]]` | 決算発表予定 |
| `economic_releases` | `list[dict[str, Any]]` | 経済指標発表予定 |

### 便利関数・定数

| 関数/定数 | 説明 |
|----------|------|
| `get_upcoming_earnings(days_ahead=7)` | 決算予定取得 |
| `get_upcoming_economic_releases()` | 経済指標発表予定取得 |
| `MAJOR_RELEASES` | 主要経済指標リスト（`list[str]`） |

### 型定義

| 型 | 説明 |
|----|------|
| `EarningsDateInfo` | 決算日程情報 |
| `EconomicReleaseInfo` | 経済指標発表情報 |

## モジュール構成

```
analyze/reporting/
├── __init__.py                  # パッケージエクスポート（17エクスポート）
├── performance.py               # PerformanceAnalyzer（通常版）
├── performance_agent.py         # PerformanceAnalyzer4Agent + PerformanceResult
├── currency.py                  # CurrencyAnalyzer（通常版）
├── currency_agent.py            # CurrencyAnalyzer4Agent + CurrencyResult
├── interest_rate.py             # InterestRateAnalyzer（通常版）
├── interest_rate_agent.py       # InterestRateAnalyzer4Agent + InterestRateResult
├── upcoming_events.py           # UpcomingEventsAnalyzer + 便利関数
├── upcoming_events_agent.py     # UpcomingEvents4Agent + UpcomingEventsResult
├── metal.py                     # 貴金属分析
├── us_treasury.py               # 米国債分析
├── vix.py                       # VIX 分析
├── market_report_utils.py       # レポート生成ユーティリティ
└── README.md                    # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| pandas | データ操作 |
| yfinance | 市場データ取得 |

## 関連モジュール

- [analyze.config](../config/README.md) - シンボルグループ定義
- [analyze.returns](../returns/README.md) - リターン計算
- [analyze.earnings](../earnings/README.md) - 決算データ（`UpcomingEvents4Agent` で使用）
- [analyze.visualization](../visualization/README.md) - レポート用チャート生成
