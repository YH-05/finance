# Task 12: UpcomingEvents4Agent クラス作成

**Phase**: 3 - 来週の注目材料
**依存**: Task 10, Task 11
**ファイル**: `src/analyze/reporting/upcoming_events_agent.py`

## 概要

`UpcomingEventsCollector` をラップし、AIエージェントが解釈しやすいJSON形式で来週の注目材料を出力する `UpcomingEvents4Agent` クラスを作成する。

## 実装仕様

### データクラス

```python
@dataclass
class UpcomingEventsResult:
    """来週の注目材料を格納するデータクラス.

    Attributes
    ----------
    group : str
        グループ名（"upcoming_events"）
    generated_at : str
        生成日時（ISO形式）
    period : dict[str, str]
        対象期間（start, end）
    earnings : list[dict[str, Any]]
        決算発表予定
    economic_releases : list[dict[str, Any]]
        経済指標発表予定
    summary : dict[str, Any]
        サマリー情報
    """

    group: str
    generated_at: str
    period: dict[str, str]
    earnings: list[dict[str, Any]]
    economic_releases: list[dict[str, Any]]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]: ...
```

### クラス設計

```python
class UpcomingEvents4Agent:
    """AIエージェント向けの来週注目材料クラス.

    UpcomingEventsCollector の機能をラップし、
    JSON形式で結果を出力する。
    """

    def __init__(self) -> None: ...

    def get_upcoming_events(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> UpcomingEventsResult:
        """来週の注目材料をJSON形式で取得.

        Parameters
        ----------
        start_date : date | None
            開始日（デフォルト: 明日）
        end_date : date | None
            終了日（デフォルト: 1週間後）

        Returns
        -------
        UpcomingEventsResult
            構造化された結果
        """
        ...

    def _calculate_summary(
        self,
        earnings: list[dict[str, Any]],
        economic_releases: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """サマリー情報を計算."""
        ...
```

### 出力形式

```json
{
  "group": "upcoming_events",
  "generated_at": "2026-01-29T10:00:00",
  "period": {
    "start": "2026-01-30",
    "end": "2026-02-05"
  },
  "earnings": [
    {
      "symbol": "AAPL",
      "name": "Apple",
      "date": "2026-02-01",
      "timing": "After Market Close"
    },
    {
      "symbol": "MSFT",
      "name": "Microsoft",
      "date": "2026-02-03",
      "timing": "After Market Close"
    }
  ],
  "economic_releases": [
    {
      "release_id": "10",
      "name": "Employment Situation",
      "name_ja": "雇用統計",
      "date": "2026-02-07",
      "importance": "high"
    },
    {
      "release_id": "21",
      "name": "Consumer Price Index",
      "name_ja": "消費者物価指数",
      "date": "2026-02-12",
      "importance": "high"
    }
  ],
  "summary": {
    "earnings_count": 5,
    "high_importance_releases": 3,
    "busiest_day": {
      "date": "2026-02-01",
      "events": 4
    },
    "highlight": "今週はApple、Microsoftの決算と雇用統計に注目"
  }
}
```

## 参照パターン

- `src/analyze/reporting/performance_agent.py`: PerformanceAnalyzer4Agent
- `src/analyze/reporting/interest_rate_agent.py`: InterestRateAnalyzer4Agent (Task 02)

## 受け入れ条件

- [ ] UpcomingEventsCollector を使用してデータを取得
- [ ] UpcomingEventsResult データクラスで結果を構造化
- [ ] to_dict() で JSON シリアライズ可能な辞書を返す
- [ ] サマリー情報を含む（決算数、重要指標数等）
- [ ] デフォルトで明日から1週間の期間を対象
