"""UpcomingEvents4Agent のテスト.

UpcomingEventsCollector をラップし、AIエージェントが解釈しやすい
JSON形式で来週の注目材料を出力する機能のテスト。

Issue: #2421
参照: src/analyze/reporting/performance_agent.py
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from analyze.reporting.upcoming_events import (
    EarningsDateInfo,
    EconomicReleaseInfo,
)

# =============================================================================
# TestUpcomingEventsResult
# =============================================================================


class TestUpcomingEventsResult:
    """UpcomingEventsResult データクラスのテスト."""

    def test_正常系_to_dictで全フィールドが辞書に変換される(self) -> None:
        """UpcomingEventsResultがto_dictで全フィールドを辞書に変換できることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEventsResult

        result = UpcomingEventsResult(
            group="upcoming_events",
            generated_at="2026-01-29T12:00:00",
            period={"start": "2026-01-30", "end": "2026-02-05"},
            earnings=[
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "earnings_date": "2026-02-05",
                    "source": "calendar",
                }
            ],
            economic_releases=[
                {
                    "release_id": 10,
                    "name": "Employment Situation",
                    "name_ja": "雇用統計",
                    "release_date": "2026-02-07",
                    "importance": "high",
                }
            ],
            summary={
                "earnings_count": 1,
                "high_importance_count": 1,
                "busiest_date": "2026-02-05",
            },
        )

        dict_result = result.to_dict()

        assert dict_result["group"] == "upcoming_events"
        assert dict_result["generated_at"] == "2026-01-29T12:00:00"
        assert dict_result["period"]["start"] == "2026-01-30"
        assert dict_result["period"]["end"] == "2026-02-05"
        assert len(dict_result["earnings"]) == 1
        assert dict_result["earnings"][0]["symbol"] == "AAPL"
        assert len(dict_result["economic_releases"]) == 1
        assert dict_result["economic_releases"][0]["name_ja"] == "雇用統計"
        assert dict_result["summary"]["earnings_count"] == 1

    def test_正常系_空のリストでも辞書に変換できる(self) -> None:
        """空のリストでもto_dictで辞書に変換できることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEventsResult

        result = UpcomingEventsResult(
            group="upcoming_events",
            generated_at="2026-01-29T12:00:00",
            period={"start": "2026-01-30", "end": "2026-02-05"},
            earnings=[],
            economic_releases=[],
            summary={
                "earnings_count": 0,
                "high_importance_count": 0,
                "busiest_date": None,
            },
        )

        dict_result = result.to_dict()

        assert dict_result["earnings"] == []
        assert dict_result["economic_releases"] == []
        assert dict_result["summary"]["earnings_count"] == 0


# =============================================================================
# TestUpcomingEvents4AgentInit
# =============================================================================


class TestUpcomingEvents4AgentInit:
    """UpcomingEvents4Agent の初期化テスト."""

    def test_正常系_デフォルト初期化が成功する(self) -> None:
        """UpcomingEvents4Agentがデフォルト設定で初期化できることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        agent = UpcomingEvents4Agent()

        assert agent is not None

    def test_正常系_UpcomingEventsAnalyzerを内部に持つ(self) -> None:
        """UpcomingEvents4Agentが内部にUpcomingEventsAnalyzerを持つことを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        agent = UpcomingEvents4Agent()

        assert hasattr(agent, "_analyzer")


# =============================================================================
# TestGetUpcomingEvents
# =============================================================================


class TestGetUpcomingEvents:
    """来週の注目材料取得のテスト."""

    @pytest.fixture
    def mock_earnings_list(self) -> list[EarningsDateInfo]:
        """モック用の決算発表日リスト."""
        now = datetime.now(tz=timezone.utc)
        return [
            EarningsDateInfo(
                symbol="AAPL",
                name="Apple Inc.",
                earnings_date=now + timedelta(days=3),
                source="calendar",
            ),
            EarningsDateInfo(
                symbol="MSFT",
                name="Microsoft Corporation",
                earnings_date=now + timedelta(days=5),
                source="earnings_dates",
            ),
        ]

    @pytest.fixture
    def mock_economic_releases(self) -> dict[str, Any]:
        """モック用の経済指標発表予定."""
        now = datetime.now(tz=timezone.utc)
        return {
            "upcoming_economic_releases": [
                {
                    "release_id": 10,
                    "name": "Employment Situation",
                    "name_ja": "雇用統計",
                    "release_date": (now + timedelta(days=4)).strftime("%Y-%m-%d"),
                    "importance": "high",
                },
                {
                    "release_id": 21,
                    "name": "Consumer Price Index",
                    "name_ja": "消費者物価指数",
                    "release_date": (now + timedelta(days=6)).strftime("%Y-%m-%d"),
                    "importance": "high",
                },
            ]
        }

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_UpcomingEventsResultが返される(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """get_upcoming_eventsがUpcomingEventsResultを返すことを確認."""
        from analyze.reporting.upcoming_events_agent import (
            UpcomingEvents4Agent,
            UpcomingEventsResult,
        )

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        assert isinstance(result, UpcomingEventsResult)
        assert result.group == "upcoming_events"

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_デフォルトで7日間の期間を対象(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """デフォルトで明日から7日間の期間を対象とすることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        # 期間の確認
        assert "start" in result.period
        assert "end" in result.period

        # 7日間の期間を確認
        start_date = datetime.strptime(result.period["start"], "%Y-%m-%d")
        end_date = datetime.strptime(result.period["end"], "%Y-%m-%d")
        assert (end_date - start_date).days == 6  # 7日間なので差は6

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_days_ahead引数で期間を変更できる(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """days_ahead引数で対象期間を変更できることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events(days_ahead=14)

        # 14日間の期間を確認
        start_date = datetime.strptime(result.period["start"], "%Y-%m-%d")
        end_date = datetime.strptime(result.period["end"], "%Y-%m-%d")
        assert (end_date - start_date).days == 13  # 14日間なので差は13

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_決算情報がearningsに含まれる(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """決算情報がearningsフィールドに含まれることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        assert len(result.earnings) == 2
        assert result.earnings[0]["symbol"] == "AAPL"
        assert result.earnings[1]["symbol"] == "MSFT"

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_経済指標がeconomic_releasesに含まれる(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """経済指標がeconomic_releasesフィールドに含まれることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        assert len(result.economic_releases) == 2
        assert result.economic_releases[0]["name_ja"] == "雇用統計"
        assert result.economic_releases[1]["name_ja"] == "消費者物価指数"


# =============================================================================
# TestSummary
# =============================================================================


class TestSummary:
    """サマリー情報のテスト."""

    @pytest.fixture
    def mock_earnings_list(self) -> list[EarningsDateInfo]:
        """モック用の決算発表日リスト."""
        now = datetime.now(tz=timezone.utc)
        return [
            EarningsDateInfo(
                symbol="AAPL",
                name="Apple Inc.",
                earnings_date=now + timedelta(days=3),
                source="calendar",
            ),
            EarningsDateInfo(
                symbol="MSFT",
                name="Microsoft Corporation",
                earnings_date=now + timedelta(days=3),  # 同じ日
                source="earnings_dates",
            ),
            EarningsDateInfo(
                symbol="GOOGL",
                name="Alphabet Inc.",
                earnings_date=now + timedelta(days=5),
                source="calendar",
            ),
        ]

    @pytest.fixture
    def mock_economic_releases(self) -> dict[str, Any]:
        """モック用の経済指標発表予定."""
        now = datetime.now(tz=timezone.utc)
        return {
            "upcoming_economic_releases": [
                {
                    "release_id": 10,
                    "name": "Employment Situation",
                    "name_ja": "雇用統計",
                    "release_date": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "importance": "high",
                },
                {
                    "release_id": 21,
                    "name": "Consumer Price Index",
                    "name_ja": "消費者物価指数",
                    "release_date": (now + timedelta(days=6)).strftime("%Y-%m-%d"),
                    "importance": "high",
                },
                {
                    "release_id": 46,
                    "name": "Producer Price Index",
                    "name_ja": "生産者物価指数",
                    "release_date": (now + timedelta(days=4)).strftime("%Y-%m-%d"),
                    "importance": "medium",
                },
            ]
        }

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_earnings_countが正しく計算される(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """サマリーのearnings_countが正しく計算されることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        assert result.summary["earnings_count"] == 3

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_high_importance_countが正しく計算される(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """サマリーのhigh_importance_countが正しく計算されることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        # high importance: 雇用統計、消費者物価指数の2つ
        assert result.summary["high_importance_count"] == 2

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_busiest_dateが正しく計算される(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """サマリーのbusiest_dateが正しく計算されることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        # 3日後: AAPL、MSFT決算 + 雇用統計 = 3イベント（最多）
        assert result.summary["busiest_date"] is not None

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_正常系_economic_release_countが含まれる(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
        mock_earnings_list: list[EarningsDateInfo],
        mock_economic_releases: dict[str, Any],
    ) -> None:
        """サマリーにeconomic_release_countが含まれることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings_list
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = mock_economic_releases

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        assert result.summary["economic_release_count"] == 3


# =============================================================================
# TestEdgeCases
# =============================================================================


class TestEdgeCases:
    """エッジケースのテスト."""

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_エッジケース_決算がない場合も正常に動作(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
    ) -> None:
        """決算発表がない場合も正常に動作することを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = []
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = {"upcoming_economic_releases": []}

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        assert result.earnings == []
        assert result.summary["earnings_count"] == 0

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_エッジケース_経済指標がない場合も正常に動作(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
    ) -> None:
        """経済指標発表がない場合も正常に動作することを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        now = datetime.now(tz=timezone.utc)
        mock_earnings = [
            EarningsDateInfo(
                symbol="AAPL",
                name="Apple Inc.",
                earnings_date=now + timedelta(days=3),
                source="calendar",
            ),
        ]

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = mock_earnings
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = {"upcoming_economic_releases": []}

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        assert result.economic_releases == []
        assert result.summary["economic_release_count"] == 0
        assert result.summary["high_importance_count"] == 0

    @patch("analyze.reporting.upcoming_events_agent.get_upcoming_economic_releases")
    @patch("analyze.reporting.upcoming_events_agent.UpcomingEventsAnalyzer")
    def test_エッジケース_両方空の場合もbusiest_dateがNone(
        self,
        mock_analyzer_class: MagicMock,
        mock_get_economic: MagicMock,
    ) -> None:
        """両方空の場合もbusiest_dateがNoneになることを確認."""
        from analyze.reporting.upcoming_events_agent import UpcomingEvents4Agent

        mock_analyzer = MagicMock()
        mock_analyzer.get_upcoming_earnings.return_value = []
        mock_analyzer_class.return_value = mock_analyzer
        mock_get_economic.return_value = {"upcoming_economic_releases": []}

        agent = UpcomingEvents4Agent()
        result = agent.get_upcoming_events()

        assert result.summary["busiest_date"] is None
