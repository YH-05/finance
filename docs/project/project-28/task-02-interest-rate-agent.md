# Task 02: InterestRateAnalyzer4Agent クラス作成

**Phase**: 1 - 金利データ
**依存**: Task 01
**ファイル**: `src/analyze/reporting/interest_rate_agent.py`

## 概要

`InterestRateAnalyzer` をラップし、AIエージェントが解釈しやすいJSON形式で金利データを出力する `InterestRateAnalyzer4Agent` クラスを作成する。

## 実装仕様

### データクラス

```python
@dataclass
class InterestRateResult:
    """金利分析結果を格納するデータクラス.

    Attributes
    ----------
    group : str
        グループ名（"interest_rates"）
    generated_at : str
        生成日時（ISO形式）
    periods : list[str]
        分析対象の期間リスト
    data : dict[str, dict[str, Any]]
        シリーズごとの金利データと変化量
    yield_curve : dict[str, Any]
        イールドカーブ分析結果
    data_freshness : dict[str, Any]
        データ鮮度情報
    """

    group: str
    generated_at: str
    periods: list[str]
    data: dict[str, dict[str, Any]]
    yield_curve: dict[str, Any]
    data_freshness: dict[str, Any]

    def to_dict(self) -> dict[str, Any]: ...
```

### クラス設計

```python
class InterestRateAnalyzer4Agent:
    """AIエージェント向けの金利分析クラス.

    InterestRateAnalyzer の機能をラップし、
    JSON形式で結果を出力する。
    """

    def __init__(self) -> None: ...

    def get_interest_rate_performance(self) -> InterestRateResult:
        """金利パフォーマンスをJSON形式で取得."""
        ...
```

### 出力形式

```json
{
  "group": "interest_rates",
  "generated_at": "2026-01-29T10:00:00",
  "periods": ["1D", "1W", "MTD", "YTD"],
  "data": {
    "DGS2": {
      "name_ja": "2年国債利回り",
      "category": "treasury",
      "latest_value": 4.25,
      "latest_date": "2026-01-28",
      "changes": {
        "1D": -0.02,
        "1W": 0.08,
        "MTD": 0.15,
        "YTD": 0.25
      }
    },
    "DGS10": { ... },
    "DGS30": { ... },
    "FEDFUNDS": { ... },
    "T10Y2Y": { ... }
  },
  "yield_curve": {
    "2y_10y_spread": 0.45,
    "is_inverted": false,
    "interpretation": "順イールド（正常）"
  },
  "data_freshness": {
    "newest_date": "2026-01-28",
    "oldest_date": "2026-01-28",
    "has_date_gap": false
  }
}
```

## 参照パターン

- `src/analyze/reporting/performance_agent.py`: PerformanceAnalyzer4Agent

## 受け入れ条件

- [ ] InterestRateAnalyzer を使用してデータを取得
- [ ] InterestRateResult データクラスで結果を構造化
- [ ] to_dict() で JSON シリアライズ可能な辞書を返す
- [ ] データ鮮度情報を含む
- [ ] ロギングが実装されている
