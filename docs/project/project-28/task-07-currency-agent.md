# Task 07: CurrencyAnalyzer4Agent クラス作成

**Phase**: 2 - 為替データ
**依存**: Task 06
**ファイル**: `src/analyze/reporting/currency_agent.py`

## 概要

`CurrencyAnalyzer` をラップし、AIエージェントが解釈しやすいJSON形式で為替データを出力する `CurrencyAnalyzer4Agent` クラスを作成する。

## 実装仕様

### データクラス

```python
@dataclass
class CurrencyResult:
    """為替分析結果を格納するデータクラス.

    Attributes
    ----------
    group : str
        グループ名（"currencies"）
    subgroup : str
        サブグループ名（"jpy_crosses"）
    generated_at : str
        生成日時（ISO形式）
    base_currency : str
        基準通貨（"JPY"）
    periods : list[str]
        分析対象の期間リスト
    symbols : dict[str, dict[str, Any]]
        通貨ペアごとのレートと騰落率
    summary : dict[str, Any]
        サマリー情報
    data_freshness : dict[str, Any]
        データ鮮度情報
    """

    group: str
    subgroup: str
    generated_at: str
    base_currency: str
    periods: list[str]
    symbols: dict[str, dict[str, Any]]
    summary: dict[str, Any]
    data_freshness: dict[str, Any]

    def to_dict(self) -> dict[str, Any]: ...
```

### クラス設計

```python
class CurrencyAnalyzer4Agent:
    """AIエージェント向けの為替分析クラス.

    CurrencyAnalyzer の機能をラップし、
    JSON形式で結果を出力する。
    """

    def __init__(self) -> None: ...

    def get_currency_performance(
        self,
        subgroup: str = "jpy_crosses",
    ) -> CurrencyResult:
        """為替パフォーマンスをJSON形式で取得."""
        ...

    def _calculate_summary(
        self,
        returns_df: DataFrame,
        periods: list[str],
    ) -> dict[str, Any]:
        """サマリー情報を計算（最強/最弱通貨等）."""
        ...
```

### 出力形式

```json
{
  "group": "currencies",
  "subgroup": "jpy_crosses",
  "generated_at": "2026-01-29T10:00:00",
  "base_currency": "JPY",
  "periods": ["1D", "1W", "MTD", "YTD"],
  "symbols": {
    "USDJPY=X": {
      "name": "米ドル/円",
      "latest_rate": 155.50,
      "latest_date": "2026-01-28",
      "changes": {
        "1D": 0.35,
        "1W": -0.82,
        "MTD": 1.25,
        "YTD": 2.50
      }
    },
    "EURJPY=X": { ... },
    "GBPJPY=X": { ... },
    "AUDJPY=X": { ... },
    "CADJPY=X": { ... },
    "CHFJPY=X": { ... }
  },
  "summary": {
    "strongest_currency": {
      "symbol": "USDJPY=X",
      "name": "米ドル/円",
      "return_pct": 2.50
    },
    "weakest_currency": {
      "symbol": "AUDJPY=X",
      "name": "豪ドル/円",
      "return_pct": -1.20
    },
    "yen_trend": "円安傾向"
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

- [ ] CurrencyAnalyzer を使用してデータを取得
- [ ] CurrencyResult データクラスで結果を構造化
- [ ] to_dict() で JSON シリアライズ可能な辞書を返す
- [ ] 最強/最弱通貨のサマリーを含む
- [ ] データ鮮度情報を含む
