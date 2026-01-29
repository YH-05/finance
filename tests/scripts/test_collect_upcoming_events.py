"""Tests for collect_upcoming_events.py script.

This module tests the upcoming events collection CLI script that uses
UpcomingEvents4Agent to collect and output upcoming events data.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_upcoming_events_result() -> dict[str, Any]:
    """Provide sample UpcomingEventsResult data for testing."""
    now = datetime.now(tz=timezone.utc)
    start_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    earnings_date = (now + timedelta(days=3)).strftime("%Y-%m-%d")
    economic_date = (now + timedelta(days=4)).strftime("%Y-%m-%d")

    return {
        "group": "upcoming_events",
        "generated_at": now.isoformat(),
        "period": {"start": start_date, "end": end_date},
        "earnings": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "earnings_date": earnings_date,
                "source": "calendar",
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "earnings_date": earnings_date,
                "source": "earnings_dates",
            },
        ],
        "economic_releases": [
            {
                "release_id": 10,
                "name": "Employment Situation",
                "name_ja": "雇用統計",
                "release_date": economic_date,
                "importance": "high",
            },
            {
                "release_id": 21,
                "name": "Consumer Price Index",
                "name_ja": "消費者物価指数",
                "release_date": economic_date,
                "importance": "high",
            },
            {
                "release_id": 46,
                "name": "Retail Sales",
                "name_ja": "小売売上高",
                "release_date": economic_date,
                "importance": "medium",
            },
        ],
        "summary": {
            "earnings_count": 2,
            "economic_release_count": 3,
            "high_importance_count": 2,
            "busiest_date": economic_date,
        },
    }


@pytest.fixture
def mock_upcoming_events_result(
    sample_upcoming_events_result: dict[str, Any],
) -> MagicMock:
    """Create a mock UpcomingEventsResult object."""
    mock_result = MagicMock()
    mock_result.to_dict.return_value = sample_upcoming_events_result
    mock_result.period = sample_upcoming_events_result["period"]
    mock_result.earnings = sample_upcoming_events_result["earnings"]
    mock_result.economic_releases = sample_upcoming_events_result["economic_releases"]
    mock_result.summary = sample_upcoming_events_result["summary"]
    return mock_result


# ---------------------------------------------------------------------------
# Test: CLI Argument Parsing
# ---------------------------------------------------------------------------


class TestCLIArgumentParsing:
    """Test CLI argument parsing functionality."""

    def test_正常系_デフォルト引数で実行できる(self) -> None:
        """Test running with default arguments."""
        from scripts.collect_upcoming_events import create_parser

        parser = create_parser()
        args = parser.parse_args([])

        assert args.output == "data/market"
        assert args.start_date is None
        assert args.end_date is None

    def test_正常系_output引数を指定できる(self) -> None:
        """Test specifying output directory."""
        from scripts.collect_upcoming_events import create_parser

        parser = create_parser()
        args = parser.parse_args(["--output", "custom/path"])

        assert args.output == "custom/path"

    def test_正常系_start_date引数を指定できる(self) -> None:
        """Test specifying start date."""
        from scripts.collect_upcoming_events import create_parser

        parser = create_parser()
        args = parser.parse_args(["--start-date", "2026-02-01"])

        assert args.start_date == "2026-02-01"

    def test_正常系_end_date引数を指定できる(self) -> None:
        """Test specifying end date."""
        from scripts.collect_upcoming_events import create_parser

        parser = create_parser()
        args = parser.parse_args(["--end-date", "2026-02-07"])

        assert args.end_date == "2026-02-07"

    def test_正常系_複数引数を同時に指定できる(self) -> None:
        """Test specifying multiple arguments."""
        from scripts.collect_upcoming_events import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "--output",
                "/tmp/data",
                "--start-date",
                "2026-02-01",
                "--end-date",
                "2026-02-07",
            ]
        )

        assert args.output == "/tmp/data"
        assert args.start_date == "2026-02-01"
        assert args.end_date == "2026-02-07"


# ---------------------------------------------------------------------------
# Test: Date Parsing
# ---------------------------------------------------------------------------


class TestDateParsing:
    """Test date parsing functionality."""

    def test_正常系_正しい形式の日付を解析できる(self) -> None:
        """Test parsing date in correct format."""
        from scripts.collect_upcoming_events import parse_date

        result = parse_date("2026-02-01")

        assert result == date(2026, 2, 1)

    def test_異常系_不正な形式の日付でValueError(self) -> None:
        """Test raising ValueError for invalid date format."""
        from scripts.collect_upcoming_events import parse_date

        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("02/01/2026")

    def test_異常系_存在しない日付でValueError(self) -> None:
        """Test raising ValueError for non-existent date."""
        from scripts.collect_upcoming_events import parse_date

        with pytest.raises(ValueError):
            parse_date("2026-02-30")


# ---------------------------------------------------------------------------
# Test: Timestamp Generation
# ---------------------------------------------------------------------------


class TestTimestampGeneration:
    """Test timestamp generation functionality."""

    def test_正常系_タイムスタンプが正しい形式で生成される(self) -> None:
        """Test timestamp format is YYYYMMDD-HHMM."""
        from scripts.collect_upcoming_events import generate_timestamp

        timestamp = generate_timestamp()

        # Format: YYYYMMDD-HHMM
        assert len(timestamp) == 13
        assert timestamp[8] == "-"
        assert timestamp[:8].isdigit()
        assert timestamp[9:].isdigit()


# ---------------------------------------------------------------------------
# Test: JSON File Saving
# ---------------------------------------------------------------------------


class TestJSONFileSaving:
    """Test JSON file saving functionality."""

    def test_正常系_JSONファイルを保存できる(
        self, tmp_path: Path, sample_upcoming_events_result: dict[str, Any]
    ) -> None:
        """Test saving data to JSON file."""
        from scripts.collect_upcoming_events import save_json

        file_path = tmp_path / "test.json"
        save_json(sample_upcoming_events_result, file_path)

        assert file_path.exists()

        with open(file_path, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == sample_upcoming_events_result

    def test_正常系_日本語を含むデータを保存できる(self, tmp_path: Path) -> None:
        """Test saving data with Japanese characters."""
        from scripts.collect_upcoming_events import save_json

        data = {"message": "雇用統計発表予定", "value": 123}
        file_path = tmp_path / "japanese.json"
        save_json(data, file_path)

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        assert "雇用統計発表予定" in content


# ---------------------------------------------------------------------------
# Test: Upcoming Events Collection
# ---------------------------------------------------------------------------


class TestUpcomingEventsCollection:
    """Test upcoming events collection functionality."""

    def test_正常系_来週注目材料を収集できる(
        self, tmp_path: Path, mock_upcoming_events_result: MagicMock
    ) -> None:
        """Test collecting upcoming events successfully."""
        from scripts.collect_upcoming_events import collect_upcoming_events

        with patch(
            "scripts.collect_upcoming_events.UpcomingEvents4Agent"
        ) as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            result = collect_upcoming_events(
                output_dir=tmp_path, timestamp="20260129-1200"
            )

            assert result is not None
            mock_agent.get_upcoming_events.assert_called_once()

    def test_正常系_出力ファイルが正しい名前で作成される(
        self, tmp_path: Path, mock_upcoming_events_result: MagicMock
    ) -> None:
        """Test output file is created with correct name."""
        from scripts.collect_upcoming_events import collect_upcoming_events

        with patch(
            "scripts.collect_upcoming_events.UpcomingEvents4Agent"
        ) as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            collect_upcoming_events(output_dir=tmp_path, timestamp="20260129-1200")

            expected_file = tmp_path / "upcoming_events_20260129-1200.json"
            assert expected_file.exists()

    def test_正常系_出力ディレクトリが存在しない場合は作成される(
        self, tmp_path: Path, mock_upcoming_events_result: MagicMock
    ) -> None:
        """Test output directory is created if it doesn't exist."""
        from scripts.collect_upcoming_events import collect_upcoming_events

        output_dir = tmp_path / "nested" / "dir"

        with patch(
            "scripts.collect_upcoming_events.UpcomingEvents4Agent"
        ) as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            collect_upcoming_events(output_dir=output_dir, timestamp="20260129-1200")

            assert output_dir.exists()

    def test_正常系_カスタム日付範囲で収集できる(
        self, tmp_path: Path, mock_upcoming_events_result: MagicMock
    ) -> None:
        """Test collecting with custom date range."""
        from scripts.collect_upcoming_events import collect_upcoming_events

        start_date = date(2026, 2, 1)
        end_date = date(2026, 2, 7)

        with patch(
            "scripts.collect_upcoming_events.UpcomingEvents4Agent"
        ) as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            result = collect_upcoming_events(
                output_dir=tmp_path,
                timestamp="20260129-1200",
                start_date=start_date,
                end_date=end_date,
            )

            assert result is not None

    def test_異常系_データ収集失敗時はNoneを返す(self, tmp_path: Path) -> None:
        """Test returning None when data collection fails."""
        from scripts.collect_upcoming_events import collect_upcoming_events

        with patch(
            "scripts.collect_upcoming_events.UpcomingEvents4Agent"
        ) as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.side_effect = Exception("API Error")
            mock_agent_class.return_value = mock_agent

            result = collect_upcoming_events(
                output_dir=tmp_path, timestamp="20260129-1200"
            )

            assert result is None


# ---------------------------------------------------------------------------
# Test: Main Function
# ---------------------------------------------------------------------------


class TestMainFunction:
    """Test main function."""

    def test_正常系_メイン関数が正常終了する(
        self,
        tmp_path: Path,
        mock_upcoming_events_result: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test main function exits with code 0 on success."""
        from scripts.collect_upcoming_events import main

        with (
            patch(
                "scripts.collect_upcoming_events.UpcomingEvents4Agent"
            ) as mock_agent_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            exit_code = main()

            assert exit_code == 0

    def test_正常系_サマリーが標準出力に表示される(
        self,
        tmp_path: Path,
        mock_upcoming_events_result: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test summary is printed to stdout."""
        from scripts.collect_upcoming_events import main

        with (
            patch(
                "scripts.collect_upcoming_events.UpcomingEvents4Agent"
            ) as mock_agent_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            main()

            captured = capsys.readouterr()
            assert "Upcoming Events Data Collection Complete" in captured.out
            assert "Earnings:" in captured.out
            assert "Economic Releases:" in captured.out

    def test_異常系_データ収集失敗時は終了コード1を返す(self, tmp_path: Path) -> None:
        """Test main function exits with code 1 on failure."""
        from scripts.collect_upcoming_events import main

        with (
            patch(
                "scripts.collect_upcoming_events.UpcomingEvents4Agent"
            ) as mock_agent_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.side_effect = Exception("API Error")
            mock_agent_class.return_value = mock_agent

            exit_code = main()

            assert exit_code == 1

    def test_正常系_日付引数が反映される(
        self,
        tmp_path: Path,
        mock_upcoming_events_result: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test date arguments are reflected in output."""
        from scripts.collect_upcoming_events import main

        with (
            patch(
                "scripts.collect_upcoming_events.UpcomingEvents4Agent"
            ) as mock_agent_class,
            patch(
                "sys.argv",
                [
                    "script",
                    "--output",
                    str(tmp_path),
                    "--start-date",
                    "2026-02-01",
                    "--end-date",
                    "2026-02-07",
                ],
            ),
        ):
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            exit_code = main()

            assert exit_code == 0

    def test_異常系_不正な日付フォーマットで終了コード1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test invalid date format returns exit code 1."""
        from scripts.collect_upcoming_events import main

        with patch(
            "sys.argv",
            ["script", "--output", str(tmp_path), "--start-date", "02/01/2026"],
        ):
            exit_code = main()

            assert exit_code == 1
            captured = capsys.readouterr()
            assert "Error:" in captured.out

    def test_異常系_終了日が開始日より前で終了コード1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test end date before start date returns exit code 1."""
        from scripts.collect_upcoming_events import main

        with patch(
            "sys.argv",
            [
                "script",
                "--output",
                str(tmp_path),
                "--start-date",
                "2026-02-07",
                "--end-date",
                "2026-02-01",
            ],
        ):
            exit_code = main()

            assert exit_code == 1
            captured = capsys.readouterr()
            assert "Error:" in captured.out


# ---------------------------------------------------------------------------
# Test: Output Summary
# ---------------------------------------------------------------------------


class TestOutputSummary:
    """Test output summary display functionality."""

    def test_正常系_決算情報がサマリーに表示される(
        self,
        tmp_path: Path,
        mock_upcoming_events_result: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test earnings information is displayed in summary."""
        from scripts.collect_upcoming_events import main

        with (
            patch(
                "scripts.collect_upcoming_events.UpcomingEvents4Agent"
            ) as mock_agent_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            main()

            captured = capsys.readouterr()
            assert "AAPL" in captured.out
            assert "MSFT" in captured.out

    def test_正常系_重要度の高い経済指標がサマリーに表示される(
        self,
        tmp_path: Path,
        mock_upcoming_events_result: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test high importance economic releases are displayed in summary."""
        from scripts.collect_upcoming_events import main

        with (
            patch(
                "scripts.collect_upcoming_events.UpcomingEvents4Agent"
            ) as mock_agent_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_upcoming_events_result
            mock_agent_class.return_value = mock_agent

            main()

            captured = capsys.readouterr()
            assert "雇用統計" in captured.out
            assert "消費者物価指数" in captured.out
            # medium importance should not be in high importance section
            assert "小売売上高" not in captured.out or "High Importance" in captured.out


# ---------------------------------------------------------------------------
# Test: Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases."""

    def test_エッジケース_決算がない場合もサマリーが表示される(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test summary is displayed even when no earnings are present."""
        from scripts.collect_upcoming_events import main

        now = datetime.now(tz=timezone.utc)
        empty_earnings_result = {
            "group": "upcoming_events",
            "generated_at": now.isoformat(),
            "period": {
                "start": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                "end": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
            },
            "earnings": [],
            "economic_releases": [],
            "summary": {
                "earnings_count": 0,
                "economic_release_count": 0,
                "high_importance_count": 0,
                "busiest_date": None,
            },
        }

        mock_result = MagicMock()
        mock_result.to_dict.return_value = empty_earnings_result
        mock_result.period = empty_earnings_result["period"]
        mock_result.earnings = empty_earnings_result["earnings"]
        mock_result.economic_releases = empty_earnings_result["economic_releases"]
        mock_result.summary = empty_earnings_result["summary"]

        with (
            patch(
                "scripts.collect_upcoming_events.UpcomingEvents4Agent"
            ) as mock_agent_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_agent = MagicMock()
            mock_agent.get_upcoming_events.return_value = mock_result
            mock_agent_class.return_value = mock_agent

            exit_code = main()

            assert exit_code == 0
            captured = capsys.readouterr()
            assert "Earnings: 0 companies" in captured.out
            assert "Economic Releases: 0 events" in captured.out
