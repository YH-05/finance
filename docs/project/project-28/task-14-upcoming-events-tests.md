# Task 14: 来週の注目材料の単体テスト作成

**Phase**: 3 - 来週の注目材料
**依存**: Task 10, Task 11, Task 12
**ファイル**: `tests/analyze/reporting/unit/test_upcoming_events.py`

## 概要

`UpcomingEventsCollector` と `UpcomingEvents4Agent` の単体テストを作成する。

## テスト対象

### UpcomingEventsCollector

1. **正常系**: 決算発表日取得
2. **正常系**: 経済指標発表予定取得
3. **正常系**: 期間フィルタリング
4. **異常系**: yfinance エラー時の挙動
5. **異常系**: FRED API エラー時の挙動
6. **エッジケース**: 期間内にイベントがない場合

### UpcomingEvents4Agent

1. **正常系**: JSON形式での出力
2. **正常系**: サマリー情報の計算
3. **正常系**: to_dict() の構造検証

## テスト実装

```python
"""来週の注目材料のテスト."""

from datetime import date, timedelta

import pytest

from analyze.reporting.upcoming_events import UpcomingEventsCollector
from analyze.reporting.upcoming_events_agent import (
    UpcomingEvents4Agent,
    UpcomingEventsResult,
)


class TestUpcomingEventsCollector:
    """UpcomingEventsCollector のテスト."""

    def test_正常系_決算発表日を取得できる(self) -> None:
        """yfinance から決算発表日を取得できることを確認."""
        collector = UpcomingEventsCollector()
        today = date.today()
        end_date = today + timedelta(days=30)

        earnings = collector.get_upcoming_earnings(today, end_date)

        assert isinstance(earnings, list)
        # 結果があれば構造を確認
        if earnings:
            assert "symbol" in earnings[0]
            assert "name" in earnings[0]
            assert "date" in earnings[0]

    def test_正常系_経済指標発表予定を取得できる(self) -> None:
        """FRED API から経済指標発表予定を取得できることを確認."""
        collector = UpcomingEventsCollector()
        today = date.today()
        end_date = today + timedelta(days=30)

        releases = collector.get_upcoming_economic_releases(today, end_date)

        assert isinstance(releases, list)
        # 結果があれば構造を確認
        if releases:
            assert "release_id" in releases[0]
            assert "name_ja" in releases[0]
            assert "date" in releases[0]

    def test_正常系_期間フィルタリングができる(self) -> None:
        """指定期間内のイベントのみ取得."""
        collector = UpcomingEventsCollector()
        start_date = date(2026, 2, 1)
        end_date = date(2026, 2, 7)

        earnings = collector.get_upcoming_earnings(start_date, end_date)

        for earning in earnings:
            event_date = date.fromisoformat(earning["date"])
            assert start_date <= event_date <= end_date

    def test_エッジケース_期間内にイベントがない場合(self) -> None:
        """期間内にイベントがない場合は空リストを返す."""
        collector = UpcomingEventsCollector()
        # 遠い過去を指定
        start_date = date(2000, 1, 1)
        end_date = date(2000, 1, 7)

        earnings = collector.get_upcoming_earnings(start_date, end_date)

        assert earnings == []


class TestUpcomingEvents4Agent:
    """UpcomingEvents4Agent のテスト."""

    def test_正常系_JSON形式で出力できる(self) -> None:
        """結果を JSON シリアライズ可能な形式で取得."""
        agent = UpcomingEvents4Agent()
        today = date.today()
        end_date = today + timedelta(days=14)

        result = agent.get_upcoming_events(today, end_date)

        assert isinstance(result, UpcomingEventsResult)
        result_dict = result.to_dict()

        assert result_dict["group"] == "upcoming_events"
        assert "period" in result_dict
        assert "earnings" in result_dict
        assert "economic_releases" in result_dict

    def test_正常系_サマリー情報が含まれる(self) -> None:
        """サマリー情報が正しく計算される."""
        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()
        result_dict = result.to_dict()

        assert "summary" in result_dict
        assert "earnings_count" in result_dict["summary"]
        assert "high_importance_releases" in result_dict["summary"]

    def test_正常系_デフォルト期間が設定される(self) -> None:
        """開始日・終了日を指定しない場合のデフォルト期間."""
        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()
        result_dict = result.to_dict()

        today = date.today()
        start_date = date.fromisoformat(result_dict["period"]["start"])
        end_date = date.fromisoformat(result_dict["period"]["end"])

        # 開始日は明日
        assert start_date == today + timedelta(days=1)
        # 終了日は1週間後
        assert end_date == today + timedelta(days=8)
```

## テスト実行

```bash
# 単体テストのみ
uv run pytest tests/analyze/reporting/unit/test_upcoming_events.py -v

# カバレッジ付き
uv run pytest tests/analyze/reporting/unit/test_upcoming_events.py --cov=analyze.reporting.upcoming_events
```

## 受け入れ条件

- [ ] 全テストケースがパスする
- [ ] カバレッジ 80% 以上
- [ ] 日本語テスト名で意図が明確
- [ ] 決算と経済指標の両方をテスト
- [ ] エッジケース（空結果）をテスト
