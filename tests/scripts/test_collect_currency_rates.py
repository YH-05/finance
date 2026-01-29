"""Tests for collect_currency_rates.py script.

This module tests the currency rates collection CLI script that uses
CurrencyAnalyzer4Agent to collect and output currency rate data.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_currency_result() -> dict[str, Any]:
    """Provide sample CurrencyResult data for testing."""
    return {
        "group": "currencies",
        "subgroup": "jpy_crosses",
        "base_currency": "JPY",
        "generated_at": "2026-01-29T12:00:00",
        "periods": ["1D", "1W", "1M"],
        "symbols": {
            "USDJPY=X": {"1D": 0.16, "1W": 0.5, "1M": 1.2},
            "EURJPY=X": {"1D": -0.08, "1W": 0.3, "1M": 1.5},
            "GBPJPY=X": {"1D": 0.22, "1W": 0.8, "1M": 2.1},
        },
        "summary": {
            "strongest_currency": {
                "symbol": "GBPJPY=X",
                "period": "1M",
                "return_pct": 2.1,
            },
            "weakest_currency": {
                "symbol": "EURJPY=X",
                "period": "1D",
                "return_pct": -0.08,
            },
            "period_averages": {"1D": 0.1, "1W": 0.53, "1M": 1.6},
            "period_best": {
                "1D": {"symbol": "GBPJPY=X", "return_pct": 0.22},
                "1W": {"symbol": "GBPJPY=X", "return_pct": 0.8},
                "1M": {"symbol": "GBPJPY=X", "return_pct": 2.1},
            },
            "period_worst": {
                "1D": {"symbol": "EURJPY=X", "return_pct": -0.08},
                "1W": {"symbol": "EURJPY=X", "return_pct": 0.3},
                "1M": {"symbol": "USDJPY=X", "return_pct": 1.2},
            },
        },
        "latest_dates": {
            "USDJPY=X": "2026-01-29",
            "EURJPY=X": "2026-01-29",
            "GBPJPY=X": "2026-01-29",
        },
        "data_freshness": {
            "newest_date": "2026-01-29",
            "oldest_date": "2026-01-29",
            "has_date_gap": False,
            "symbols_by_date": {
                "2026-01-29": ["USDJPY=X", "EURJPY=X", "GBPJPY=X"],
            },
        },
    }


@pytest.fixture
def mock_currency_result(sample_currency_result: dict[str, Any]) -> MagicMock:
    """Create a mock CurrencyResult object."""
    mock_result = MagicMock()
    mock_result.to_dict.return_value = sample_currency_result
    mock_result.data_freshness = sample_currency_result["data_freshness"]
    return mock_result


# ---------------------------------------------------------------------------
# Test: CLI Argument Parsing
# ---------------------------------------------------------------------------


class TestCLIArgumentParsing:
    """Test CLI argument parsing functionality."""

    def test_正常系_デフォルト引数で実行できる(self) -> None:
        """Test running with default arguments."""
        from scripts.collect_currency_rates import create_parser

        parser = create_parser()
        args = parser.parse_args([])

        assert args.output == "data/market"
        assert args.subgroup == "jpy_crosses"

    def test_正常系_output引数を指定できる(self) -> None:
        """Test specifying output directory."""
        from scripts.collect_currency_rates import create_parser

        parser = create_parser()
        args = parser.parse_args(["--output", "custom/path"])

        assert args.output == "custom/path"

    def test_正常系_subgroup引数を指定できる(self) -> None:
        """Test specifying subgroup."""
        from scripts.collect_currency_rates import create_parser

        parser = create_parser()
        args = parser.parse_args(["--subgroup", "usd_crosses"])

        assert args.subgroup == "usd_crosses"

    def test_正常系_複数引数を同時に指定できる(self) -> None:
        """Test specifying multiple arguments."""
        from scripts.collect_currency_rates import create_parser

        parser = create_parser()
        args = parser.parse_args(["--output", "/tmp/data", "--subgroup", "eur_crosses"])

        assert args.output == "/tmp/data"
        assert args.subgroup == "eur_crosses"


# ---------------------------------------------------------------------------
# Test: Timestamp Generation
# ---------------------------------------------------------------------------


class TestTimestampGeneration:
    """Test timestamp generation functionality."""

    def test_正常系_タイムスタンプが正しい形式で生成される(self) -> None:
        """Test timestamp format is YYYYMMDD-HHMM."""
        from scripts.collect_currency_rates import generate_timestamp

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
        self, tmp_path: Path, sample_currency_result: dict[str, Any]
    ) -> None:
        """Test saving data to JSON file."""
        from scripts.collect_currency_rates import save_json

        file_path = tmp_path / "test.json"
        save_json(sample_currency_result, file_path)

        assert file_path.exists()

        with open(file_path, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == sample_currency_result

    def test_正常系_日本語を含むデータを保存できる(self, tmp_path: Path) -> None:
        """Test saving data with Japanese characters."""
        from scripts.collect_currency_rates import save_json

        data = {"message": "テストメッセージ", "value": 123}
        file_path = tmp_path / "japanese.json"
        save_json(data, file_path)

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        assert "テストメッセージ" in content


# ---------------------------------------------------------------------------
# Test: Currency Data Collection
# ---------------------------------------------------------------------------


class TestCurrencyDataCollection:
    """Test currency data collection functionality."""

    def test_正常系_為替データを収集できる(
        self, tmp_path: Path, mock_currency_result: MagicMock
    ) -> None:
        """Test collecting currency data successfully."""
        from scripts.collect_currency_rates import collect_currency_rates

        with patch(
            "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.return_value = mock_currency_result
            mock_analyzer_class.return_value = mock_analyzer

            result = collect_currency_rates(
                output_dir=tmp_path, timestamp="20260129-1200", subgroup="jpy_crosses"
            )

            assert result is not None
            mock_analyzer.get_currency_performance.assert_called_once()

    def test_正常系_出力ファイルが正しい名前で作成される(
        self, tmp_path: Path, mock_currency_result: MagicMock
    ) -> None:
        """Test output file is created with correct name."""
        from scripts.collect_currency_rates import collect_currency_rates

        with patch(
            "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.return_value = mock_currency_result
            mock_analyzer_class.return_value = mock_analyzer

            collect_currency_rates(
                output_dir=tmp_path, timestamp="20260129-1200", subgroup="jpy_crosses"
            )

            expected_file = tmp_path / "currency_jpy_crosses_20260129-1200.json"
            assert expected_file.exists()

    def test_正常系_出力ディレクトリが存在しない場合は作成される(
        self, tmp_path: Path, mock_currency_result: MagicMock
    ) -> None:
        """Test output directory is created if it doesn't exist."""
        from scripts.collect_currency_rates import collect_currency_rates

        output_dir = tmp_path / "nested" / "dir"

        with patch(
            "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.return_value = mock_currency_result
            mock_analyzer_class.return_value = mock_analyzer

            collect_currency_rates(
                output_dir=output_dir, timestamp="20260129-1200", subgroup="jpy_crosses"
            )

            assert output_dir.exists()

    def test_異常系_データ収集失敗時はNoneを返す(self, tmp_path: Path) -> None:
        """Test returning None when data collection fails."""
        from scripts.collect_currency_rates import collect_currency_rates

        with patch(
            "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.side_effect = Exception("API Error")
            mock_analyzer_class.return_value = mock_analyzer

            result = collect_currency_rates(
                output_dir=tmp_path, timestamp="20260129-1200", subgroup="jpy_crosses"
            )

            assert result is None


# ---------------------------------------------------------------------------
# Test: Data Freshness Warning
# ---------------------------------------------------------------------------


class TestDataFreshnessWarning:
    """Test data freshness warning functionality."""

    def test_正常系_日付ズレがある場合に警告ログを出力する(
        self, tmp_path: Path, sample_currency_result: dict[str, Any]
    ) -> None:
        """Test warning log is output when date gap is detected."""
        from scripts.collect_currency_rates import collect_currency_rates

        # Create result with date gap
        result_with_gap = sample_currency_result.copy()
        result_with_gap["data_freshness"] = {
            "newest_date": "2026-01-29",
            "oldest_date": "2026-01-28",
            "has_date_gap": True,
        }

        mock_result = MagicMock()
        mock_result.to_dict.return_value = result_with_gap
        mock_result.data_freshness = result_with_gap["data_freshness"]

        with (
            patch(
                "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
            ) as mock_analyzer_class,
            patch("scripts.collect_currency_rates.logger") as mock_logger,
        ):
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.return_value = mock_result
            mock_analyzer_class.return_value = mock_analyzer

            collect_currency_rates(
                output_dir=tmp_path, timestamp="20260129-1200", subgroup="jpy_crosses"
            )

            # Check that warning was called
            mock_logger.warning.assert_called()


# ---------------------------------------------------------------------------
# Test: Main Function
# ---------------------------------------------------------------------------


class TestMainFunction:
    """Test main function."""

    def test_正常系_メイン関数が正常終了する(
        self,
        tmp_path: Path,
        mock_currency_result: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test main function exits with code 0 on success."""
        from scripts.collect_currency_rates import main

        with (
            patch(
                "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
            ) as mock_analyzer_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.return_value = mock_currency_result
            mock_analyzer_class.return_value = mock_analyzer

            exit_code = main()

            assert exit_code == 0

    def test_正常系_サマリーが標準出力に表示される(
        self,
        tmp_path: Path,
        mock_currency_result: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test summary is printed to stdout."""
        from scripts.collect_currency_rates import main

        with (
            patch(
                "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
            ) as mock_analyzer_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.return_value = mock_currency_result
            mock_analyzer_class.return_value = mock_analyzer

            main()

            captured = capsys.readouterr()
            assert "Currency Rates Data Collection Complete" in captured.out
            assert "jpy_crosses" in captured.out

    def test_異常系_データ収集失敗時は終了コード1を返す(self, tmp_path: Path) -> None:
        """Test main function exits with code 1 on failure."""
        from scripts.collect_currency_rates import main

        with (
            patch(
                "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
            ) as mock_analyzer_class,
            patch("sys.argv", ["script", "--output", str(tmp_path)]),
        ):
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.side_effect = Exception("API Error")
            mock_analyzer_class.return_value = mock_analyzer

            exit_code = main()

            assert exit_code == 1

    def test_正常系_subgroup引数が反映される(
        self,
        tmp_path: Path,
        mock_currency_result: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test subgroup argument is reflected in output."""
        from scripts.collect_currency_rates import main

        with (
            patch(
                "scripts.collect_currency_rates.CurrencyAnalyzer4Agent"
            ) as mock_analyzer_class,
            patch(
                "sys.argv",
                ["script", "--output", str(tmp_path), "--subgroup", "usd_crosses"],
            ),
        ):
            mock_analyzer = MagicMock()
            mock_analyzer.get_currency_performance.return_value = mock_currency_result
            mock_analyzer_class.return_value = mock_analyzer

            main()

            # Check file was created with correct subgroup name
            files = list(tmp_path.glob("currency_usd_crosses_*.json"))
            assert len(files) == 1
