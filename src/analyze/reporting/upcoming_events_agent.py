"""upcoming_events_agent.py

AIエージェント向けの来週注目材料取得クラス。
JSON形式で決算発表日と経済指標発表予定を出力する。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from analyze.reporting.upcoming_events import (
    EarningsDateInfo,
    UpcomingEventsAnalyzer,
    get_upcoming_economic_releases,
)
from utils_core.logging import get_logger


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
        決算発表予定リスト
    economic_releases : list[dict[str, Any]]
        経済指標発表予定リスト
    summary : dict[str, Any]
        サマリー情報（決算数、重要指標数、最忙日等）
    """

    group: str
    generated_at: str
    period: dict[str, str]
    earnings: list[dict[str, Any]]
    economic_releases: list[dict[str, Any]]
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換する."""
        return {
            "group": self.group,
            "generated_at": self.generated_at,
            "period": self.period,
            "earnings": self.earnings,
            "economic_releases": self.economic_releases,
            "summary": self.summary,
        }


class UpcomingEvents4Agent:
    """AIエージェント向けの来週注目材料取得クラス.

    UpcomingEventsAnalyzerの機能をラップし、AIエージェントが解釈しやすい
    JSON形式で結果を出力する。決算発表日と経済指標発表予定を
    統合して提供する。

    Examples
    --------
    >>> agent = UpcomingEvents4Agent()
    >>> result = agent.get_upcoming_events()
    >>> print(result.to_dict())
    {
        "group": "upcoming_events",
        "generated_at": "2026-01-29T12:00:00",
        "period": {"start": "2026-01-30", "end": "2026-02-05"},
        "earnings": [...],
        "economic_releases": [...],
        "summary": {...}
    }
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__, component="UpcomingEvents4Agent")
        self._analyzer = UpcomingEventsAnalyzer()

    def get_upcoming_events(
        self,
        days_ahead: int = 7,
    ) -> UpcomingEventsResult:
        """来週の注目材料をJSON形式で取得する.

        Parameters
        ----------
        days_ahead : int, default=7
            何日先までを対象とするか（デフォルト: 7日間）

        Returns
        -------
        UpcomingEventsResult
            構造化された来週の注目材料
        """
        self.logger.info(
            "Getting upcoming events for agent",
            days_ahead=days_ahead,
        )

        # 期間の計算
        now = datetime.now(tz=timezone.utc)
        start_date = (now + timedelta(days=1)).date()
        end_date = (now + timedelta(days=days_ahead)).date()

        # 決算発表日の取得
        earnings_list = self._analyzer.get_upcoming_earnings(days_ahead=days_ahead)
        earnings_dicts = [self._earnings_to_dict(e) for e in earnings_list]

        # 経済指標発表予定の取得
        economic_result = get_upcoming_economic_releases(days_ahead=days_ahead)
        economic_releases = economic_result.get("upcoming_economic_releases", [])

        # サマリー情報の計算
        summary = self._calculate_summary(earnings_list, economic_releases)

        self.logger.info(
            "Upcoming events retrieved",
            earnings_count=len(earnings_dicts),
            economic_count=len(economic_releases),
        )

        return UpcomingEventsResult(
            group="upcoming_events",
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            period={
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            },
            earnings=earnings_dicts,
            economic_releases=economic_releases,
            summary=summary,
        )

    def _earnings_to_dict(self, info: EarningsDateInfo) -> dict[str, Any]:
        """EarningsDateInfoを辞書に変換する.

        Parameters
        ----------
        info : EarningsDateInfo
            決算発表日情報

        Returns
        -------
        dict[str, Any]
            辞書形式の決算発表日情報
        """
        return info.to_dict()

    def _calculate_summary(
        self,
        earnings_list: list[EarningsDateInfo],
        economic_releases: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """サマリー情報を計算する.

        Parameters
        ----------
        earnings_list : list[EarningsDateInfo]
            決算発表日リスト
        economic_releases : list[dict[str, Any]]
            経済指標発表予定リスト

        Returns
        -------
        dict[str, Any]
            サマリー情報
        """
        earnings_count = len(earnings_list)
        economic_release_count = len(economic_releases)

        # high importance の経済指標数
        high_importance_count = sum(
            1 for r in economic_releases if r.get("importance") == "high"
        )

        # 最も忙しい日を計算
        busiest_date = self._calculate_busiest_date(earnings_list, economic_releases)

        return {
            "earnings_count": earnings_count,
            "economic_release_count": economic_release_count,
            "high_importance_count": high_importance_count,
            "busiest_date": busiest_date,
        }

    def _calculate_busiest_date(
        self,
        earnings_list: list[EarningsDateInfo],
        economic_releases: list[dict[str, Any]],
    ) -> str | None:
        """最も忙しい日（イベント数が最多の日）を計算する.

        Parameters
        ----------
        earnings_list : list[EarningsDateInfo]
            決算発表日リスト
        economic_releases : list[dict[str, Any]]
            経済指標発表予定リスト

        Returns
        -------
        str | None
            最も忙しい日（YYYY-MM-DD形式）。イベントがない場合はNone
        """
        if not earnings_list and not economic_releases:
            return None

        # 日付ごとのイベント数をカウント
        date_counts: dict[str, int] = {}

        for earnings in earnings_list:
            date_str = earnings.earnings_date.strftime("%Y-%m-%d")
            date_counts[date_str] = date_counts.get(date_str, 0) + 1

        for release in economic_releases:
            date_str = release.get("release_date", "")
            if date_str:
                date_counts[date_str] = date_counts.get(date_str, 0) + 1

        if not date_counts:
            return None

        # 最もイベント数が多い日を返す
        busiest_date = max(date_counts, key=lambda d: date_counts[d])
        return busiest_date


def main() -> None:
    """エントリーポイント."""
    import json

    from utils_core.logging import setup_logging

    setup_logging(level="INFO", format="console", force=True)

    agent = UpcomingEvents4Agent()

    # 来週の注目材料を取得
    print("\n=== Upcoming Events (JSON) ===")
    result = agent.get_upcoming_events()
    result_json = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    print(result_json)


if __name__ == "__main__":
    main()
