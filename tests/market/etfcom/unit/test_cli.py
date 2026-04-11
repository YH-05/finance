"""Unit tests for the ETF.com CLI entry point.

Tests cover:
- ``_build_parser()`` — argument parser construction
- ``_resolve_tickers()`` — ticker resolution (inline / file / default)
- ``main()`` — end-to-end CLI invocation with mocked collector
- Partial failure propagation (exit code 1)
- ``--dry-run`` mode
- ``--tickers`` comma-separated and space-separated inputs

See Also
--------
market.etfcom.cli : Implementation under test.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from market.etfcom.cli import _build_parser, _resolve_tickers, main
from market.etfcom.models import CollectionResult, CollectionSummary

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Helpers
# =============================================================================


def _make_summary(
    *,
    successful: int = 1,
    failed: int = 0,
    total_rows: int = 10,
) -> CollectionSummary:
    """Build a minimal CollectionSummary for testing."""
    results = tuple(
        CollectionResult(
            ticker="SPY",
            table="etfcom_fund_flows",
            rows_upserted=total_rows,
            success=True,
        )
        for _ in range(successful)
    ) + tuple(
        CollectionResult(
            ticker="QQQ",
            table="etfcom_fund_flows",
            rows_upserted=0,
            success=False,
            error_message="network error",
        )
        for _ in range(failed)
    )
    return CollectionSummary(
        results=results,
        total_tickers=successful + failed,
        successful=successful,
        failed=failed,
        total_rows=total_rows * successful,
    )


# =============================================================================
# _build_parser
# =============================================================================


class TestBuildParser:
    def test_正常系_デフォルト引数でパース成功(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.frequency == "all"
        assert args.tickers is None
        assert args.tickers_file is None
        assert args.dry_run is False

    def test_正常系_frequency_daily指定(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--frequency", "daily"])
        assert args.frequency == "daily"

    def test_正常系_frequency_weekly指定(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--frequency", "weekly"])
        assert args.frequency == "weekly"

    def test_正常系_frequency_monthly指定(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--frequency", "monthly"])
        assert args.frequency == "monthly"

    def test_正常系_frequency_all指定(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--frequency", "all"])
        assert args.frequency == "all"

    def test_正常系_tickers_スペース区切り(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--tickers", "SPY", "QQQ"])
        assert args.tickers == ["SPY", "QQQ"]

    def test_正常系_tickers_file指定(self, tmp_path: Path) -> None:
        f = tmp_path / "tickers.json"
        f.write_text('["SPY"]')
        parser = _build_parser()
        args = parser.parse_args(["--tickers-file", str(f)])
        assert args.tickers_file == f

    def test_正常系_dry_run_フラグ(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_異常系_tickers_と_tickers_file_は排他(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY"]')
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--tickers", "SPY", "--tickers-file", str(f)])

    def test_異常系_不正なfrequency値でエラー(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--frequency", "yearly"])


# =============================================================================
# _resolve_tickers
# =============================================================================


class TestResolveTickers:
    def test_正常系_tickersarg_スペース区切り(self) -> None:
        result = _resolve_tickers(["SPY", "QQQ"], None)
        assert result == ["SPY", "QQQ"]

    def test_正常系_tickersarg_カンマ区切り(self) -> None:
        result = _resolve_tickers(["SPY,QQQ,IWM"], None)
        assert result == ["SPY", "QQQ", "IWM"]

    def test_正常系_tickersarg_混合区切り(self) -> None:
        result = _resolve_tickers(["SPY,QQQ", "IWM"], None)
        assert result == ["SPY", "QQQ", "IWM"]

    def test_正常系_tickersarg_小文字は大文字変換(self) -> None:
        result = _resolve_tickers(["spy", "qqq"], None)
        assert result == ["SPY", "QQQ"]

    def test_正常系_tickersarg_重複除去(self) -> None:
        result = _resolve_tickers(["SPY", "SPY", "QQQ"], None)
        assert result == ["SPY", "QQQ"]

    def test_正常系_tickers_fileからリスト読込(self, tmp_path: Path) -> None:
        f = tmp_path / "tickers.json"
        f.write_text('["SPY", "QQQ"]')
        result = _resolve_tickers(None, f)
        assert result == ["SPY", "QQQ"]

    def test_正常系_tickers_fileからオブジェクト読込_tickers_key(
        self, tmp_path: Path
    ) -> None:
        f = tmp_path / "tickers.json"
        f.write_text('{"tickers": ["SPY", "QQQ"]}')
        result = _resolve_tickers(None, f)
        assert result == ["SPY", "QQQ"]

    def test_正常系_tickers_fileからオブジェクト読込_key_as_ticker(
        self, tmp_path: Path
    ) -> None:
        f = tmp_path / "tickers.json"
        f.write_text('{"SPY": {}, "QQQ": {}}')
        result = _resolve_tickers(None, f)
        assert "SPY" in result
        assert "QQQ" in result

    def test_異常系_tickersarg_空リストでSystemExit(self) -> None:
        with pytest.raises(SystemExit):
            _resolve_tickers(["  ", ""], None)

    def test_異常系_tickers_fileが存在しない場合SystemExit(
        self, tmp_path: Path
    ) -> None:
        f = tmp_path / "nonexistent.json"
        with pytest.raises(SystemExit):
            _resolve_tickers(None, f)

    def test_異常系_tickers_fileが不正JSONでSystemExit(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.json"
        f.write_text("not json at all")
        with pytest.raises(SystemExit):
            _resolve_tickers(None, f)

    def test_異常系_tickers_fileが空配列でSystemExit(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.json"
        f.write_text("[]")
        with pytest.raises(SystemExit):
            _resolve_tickers(None, f)

    def test_異常系_デフォルトファイルなしでSystemExit(self, tmp_path: Path) -> None:
        # default file does not exist in tmp context; patch _DEFAULT_TICKERS_FILE
        with (
            patch("market.etfcom.cli._DEFAULT_TICKERS_FILE", tmp_path / "nope.json"),
            pytest.raises(SystemExit),
        ):
            _resolve_tickers(None, None)

    def test_正常系_デフォルトファイルが存在する場合読込む(
        self, tmp_path: Path
    ) -> None:
        default_file = tmp_path / "etfcom_tickers.json"
        default_file.write_text('["SPY", "QQQ"]')
        with patch("market.etfcom.cli._DEFAULT_TICKERS_FILE", default_file):
            result = _resolve_tickers(None, None)
        assert result == ["SPY", "QQQ"]


# =============================================================================
# main() — integration with mocked ETFComCollector
# =============================================================================


class TestMain:
    """Test ``main()`` with a mocked ``ETFComCollector``."""

    def _patch_collector(self, summary: CollectionSummary) -> MagicMock:
        """Create a mock collector with all collect methods returning ``summary``."""
        mock_collector = MagicMock()
        mock_collector.collect_daily.return_value = summary
        mock_collector.collect_weekly.return_value = summary
        mock_collector.collect_monthly.return_value = summary
        mock_collector.collect_all.return_value = summary
        return mock_collector

    def test_正常系_daily収集が成功で終了コード0(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY", "QQQ"]')
        summary = _make_summary(successful=1)
        mock_collector = self._patch_collector(summary)

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--frequency", "daily", "--tickers-file", str(f)])

        assert code == 0
        mock_collector.collect_daily.assert_called_once_with(["SPY", "QQQ"])

    def test_正常系_weekly収集が成功で終了コード0(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY"]')
        summary = _make_summary(successful=1)
        mock_collector = self._patch_collector(summary)

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--frequency", "weekly", "--tickers-file", str(f)])

        assert code == 0
        mock_collector.collect_weekly.assert_called_once()

    def test_正常系_monthly収集が成功で終了コード0(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY"]')
        summary = _make_summary(successful=1)
        mock_collector = self._patch_collector(summary)

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--frequency", "monthly", "--tickers-file", str(f)])

        assert code == 0
        mock_collector.collect_monthly.assert_called_once()

    def test_正常系_all収集が成功で終了コード0(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY"]')
        summary = _make_summary(successful=1)
        mock_collector = self._patch_collector(summary)

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--frequency", "all", "--tickers-file", str(f)])

        assert code == 0
        mock_collector.collect_all.assert_called_once()

    def test_正常系_tickers_インライン指定でcollect_daily呼び出し(self) -> None:
        summary = _make_summary(successful=1)
        mock_collector = self._patch_collector(summary)

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--frequency", "daily", "--tickers", "SPY,QQQ"])

        assert code == 0
        mock_collector.collect_daily.assert_called_once_with(["SPY", "QQQ"])

    def test_異常系_部分失敗で終了コード1(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY", "QQQ"]')
        summary = _make_summary(successful=1, failed=1)
        mock_collector = self._patch_collector(summary)

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--frequency", "daily", "--tickers-file", str(f)])

        assert code == 1

    def test_異常系_全失敗で終了コード1(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY"]')
        summary = _make_summary(successful=0, failed=1)
        mock_collector = self._patch_collector(summary)

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--frequency", "daily", "--tickers-file", str(f)])

        assert code == 1

    def test_異常系_コレクター例外発生で終了コード1(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY"]')
        mock_collector = MagicMock()
        mock_collector.collect_daily.side_effect = RuntimeError("storage init failed")

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--frequency", "daily", "--tickers-file", str(f)])

        assert code == 1

    def test_正常系_dry_runモードで収集しない(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY"]')
        mock_collector = MagicMock()

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--dry-run", "--frequency", "daily", "--tickers-file", str(f)])

        assert code == 0
        mock_collector.collect_daily.assert_not_called()
        mock_collector.collect_weekly.assert_not_called()
        mock_collector.collect_monthly.assert_not_called()
        mock_collector.collect_all.assert_not_called()

    def test_正常系_dry_runはtickerリストを出力する(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY", "QQQ"]')

        main(["--dry-run", "--frequency", "weekly", "--tickers-file", str(f)])

        captured = capsys.readouterr()
        assert "weekly" in captured.out
        assert "SPY" in captured.out
        assert "QQQ" in captured.out

    def test_異常系_tickerファイルが存在しない場合SystemExit(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(SystemExit):
            main(
                ["--frequency", "daily", "--tickers-file", str(tmp_path / "nope.json")]
            )

    def test_正常系_デフォルトfrequencyはall(self, tmp_path: Path) -> None:
        f = tmp_path / "t.json"
        f.write_text('["SPY"]')
        summary = _make_summary(successful=1)
        mock_collector = self._patch_collector(summary)

        with patch(
            "market.etfcom.collector.ETFComCollector", return_value=mock_collector
        ):
            code = main(["--tickers-file", str(f)])

        assert code == 0
        mock_collector.collect_all.assert_called_once()
