"""Unit tests for sync_historical CLI script.

FRED 履歴データ同期用CLIスクリプトのテストスイート。
"""

import json
import subprocess
import sys
import tempfile
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# プロジェクトルートを動的に取得
PROJECT_ROOT = Path(__file__).resolve().parents[4]

# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """一時的な出力ディレクトリを作成。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_cache() -> MagicMock:
    """モックの HistoricalCache を作成。"""
    cache = MagicMock()
    cache.sync_series.return_value = {
        "series_id": "DGS10",
        "success": True,
        "data_points": 100,
        "new_points": 5,
    }
    cache.sync_all_presets.return_value = [
        {"series_id": "DGS10", "success": True, "data_points": 100},
        {"series_id": "GDP", "success": True, "data_points": 50},
    ]
    cache.sync_category.return_value = [
        {"series_id": "DGS10", "success": True, "data_points": 100},
        {"series_id": "DGS2", "success": True, "data_points": 80},
    ]
    cache.get_status.return_value = {
        "DGS10": {
            "cached": True,
            "data_points": 100,
            "last_fetched": "2026-01-29T10:00:00+00:00",
        },
        "GDP": {"cached": False},
    }
    return cache


# =============================================================================
# parse_args のテスト
# =============================================================================


class TestParseArgs:
    """コマンドライン引数のパースのテスト。"""

    def test_正常系_allオプション(self) -> None:
        """--all オプションが正しくパースされることを確認。"""
        from market.fred.scripts.sync_historical import parse_args

        args = parse_args(["--all"])

        assert args.all is True
        assert args.series is None
        assert args.category is None

    def test_正常系_seriesオプション(self) -> None:
        """--series オプションが正しくパースされることを確認。"""
        from market.fred.scripts.sync_historical import parse_args

        args = parse_args(["--series", "DGS10"])

        assert args.series == "DGS10"
        assert args.all is False

    def test_正常系_categoryオプション(self) -> None:
        """--category オプションが正しくパースされることを確認。"""
        from market.fred.scripts.sync_historical import parse_args

        args = parse_args(["--category", "Treasury Yields"])

        assert args.category == "Treasury Yields"
        assert args.all is False

    def test_正常系_statusオプション(self) -> None:
        """--status オプションが正しくパースされることを確認。"""
        from market.fred.scripts.sync_historical import parse_args

        args = parse_args(["--status"])

        assert args.status is True

    def test_正常系_outputdirオプション(self) -> None:
        """--output-dir オプションが正しくパースされることを確認。"""
        from market.fred.scripts.sync_historical import parse_args

        args = parse_args(["--all", "--output-dir", "/custom/path"])

        assert args.output_dir == "/custom/path"

    def test_正常系_autoオプション(self) -> None:
        """--auto オプションが正しくパースされることを確認。"""
        from market.fred.scripts.sync_historical import parse_args

        args = parse_args(["--auto"])

        assert args.auto is True

    def test_正常系_stalehoursオプション(self) -> None:
        """--stale-hours オプションが正しくパースされることを確認。"""
        from market.fred.scripts.sync_historical import parse_args

        args = parse_args(["--auto", "--stale-hours", "48"])

        assert args.stale_hours == 48

    def test_正常系_デフォルト値(self) -> None:
        """デフォルト値が正しく設定されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args

        args = parse_args([])

        assert args.all is False
        assert args.series is None
        assert args.category is None
        assert args.status is False
        assert args.auto is False
        assert args.output_dir is None
        assert args.stale_hours == 24


# =============================================================================
# run_sync のテスト
# =============================================================================


class TestRunSync:
    """run_sync 関数のテスト。"""

    @patch("market.fred.scripts.sync_historical.HistoricalCache")
    def test_正常系_allオプションで全シリーズ同期(
        self, mock_cache_class: MagicMock, mock_cache: MagicMock
    ) -> None:
        """--all オプションで全シリーズが同期されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args, run_sync

        mock_cache_class.return_value = mock_cache

        args = parse_args(["--all"])
        result = run_sync(args)

        assert result == 0
        mock_cache.sync_all_presets.assert_called_once()

    @patch("market.fred.scripts.sync_historical.HistoricalCache")
    def test_正常系_seriesオプションで単一シリーズ同期(
        self, mock_cache_class: MagicMock, mock_cache: MagicMock
    ) -> None:
        """--series オプションで単一シリーズが同期されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args, run_sync

        mock_cache_class.return_value = mock_cache

        args = parse_args(["--series", "DGS10"])
        result = run_sync(args)

        assert result == 0
        mock_cache.sync_series.assert_called_once_with("DGS10")

    @patch("market.fred.scripts.sync_historical.HistoricalCache")
    def test_正常系_categoryオプションでカテゴリ同期(
        self, mock_cache_class: MagicMock, mock_cache: MagicMock
    ) -> None:
        """--category オプションでカテゴリが同期されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args, run_sync

        mock_cache_class.return_value = mock_cache

        args = parse_args(["--category", "Treasury Yields"])
        result = run_sync(args)

        assert result == 0
        mock_cache.sync_category.assert_called_once_with("Treasury Yields")

    @patch("market.fred.scripts.sync_historical.HistoricalCache")
    def test_正常系_statusオプションでステータス表示(
        self,
        mock_cache_class: MagicMock,
        mock_cache: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--status オプションでステータスが表示されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args, run_sync

        mock_cache_class.return_value = mock_cache

        args = parse_args(["--status"])
        result = run_sync(args)

        assert result == 0
        mock_cache.get_status.assert_called_once()

        # 出力にステータス情報が含まれていることを確認
        captured = capsys.readouterr()
        assert "DGS10" in captured.out

    @patch("market.fred.scripts.sync_historical.HistoricalCache")
    def test_正常系_outputdirオプションでカスタムパス(
        self, mock_cache_class: MagicMock, mock_cache: MagicMock, temp_output_dir: Path
    ) -> None:
        """--output-dir オプションでカスタムパスが使用されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args, run_sync

        mock_cache_class.return_value = mock_cache

        args = parse_args(["--all", "--output-dir", str(temp_output_dir)])
        run_sync(args)

        mock_cache_class.assert_called_once_with(base_path=temp_output_dir)

    @patch("market.fred.scripts.sync_historical.HistoricalCache")
    def test_正常系_オプションなしでヘルプメッセージ(
        self, mock_cache_class: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """オプションなしの場合、ヘルプメッセージが表示されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args, run_sync

        args = parse_args([])
        result = run_sync(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "specify" in captured.err.lower() or "option" in captured.err.lower()

    @patch("market.fred.scripts.sync_historical.HistoricalCache")
    def test_異常系_同期失敗時に非ゼロ終了コード(
        self, mock_cache_class: MagicMock
    ) -> None:
        """同期が失敗した場合、非ゼロ終了コードが返されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args, run_sync

        mock_cache = MagicMock()
        mock_cache.sync_series.return_value = {
            "series_id": "INVALID",
            "success": False,
            "error": "Series not found",
        }
        mock_cache_class.return_value = mock_cache

        args = parse_args(["--series", "INVALID"])
        result = run_sync(args)

        assert result == 1


# =============================================================================
# auto モードのテスト
# =============================================================================


class TestAutoMode:
    """--auto モードのテスト。"""

    @patch("market.fred.scripts.sync_historical.HistoricalCache")
    def test_正常系_古いデータのみ更新(self, mock_cache_class: MagicMock) -> None:
        """--auto モードで古いデータのみ更新されることを確認。"""
        from market.fred.scripts.sync_historical import parse_args, run_sync

        now = datetime.now(timezone.utc)
        one_hour_ago = (now - timedelta(hours=1)).isoformat()
        two_days_ago = (now - timedelta(days=2)).isoformat()

        mock_cache = MagicMock()
        # DGS10: 最近更新 (スキップ)
        # GDP: 古いデータ (更新)
        # UNRATE: キャッシュなし (更新)
        mock_cache.get_status.return_value = {
            "DGS10": {
                "cached": True,
                "last_fetched": one_hour_ago,  # 1時間前
                "data_points": 100,
            },
            "GDP": {
                "cached": True,
                "last_fetched": two_days_ago,  # 2日前
                "data_points": 50,
            },
            "UNRATE": {
                "cached": False,
            },
        }
        mock_cache.sync_series.return_value = {
            "series_id": "test",
            "success": True,
            "data_points": 100,
        }
        mock_cache_class.return_value = mock_cache

        args = parse_args(["--auto", "--stale-hours", "24"])
        result = run_sync(args)

        assert result == 0
        # GDP と UNRATE のみ同期されるべき
        assert mock_cache.sync_series.call_count == 2


# =============================================================================
# モジュール実行のテスト
# =============================================================================


class TestModuleExecution:
    """モジュールとしての実行テスト。"""

    def test_正常系_helpオプション(self) -> None:
        """--help オプションでヘルプが表示されることを確認。"""
        result = subprocess.run(
            [sys.executable, "-m", "market.fred.scripts.sync_historical", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            check=False,
        )

        assert result.returncode == 0
        assert "usage" in result.stdout.lower()
        assert "--all" in result.stdout
        assert "--series" in result.stdout
        assert "--category" in result.stdout
        assert "--status" in result.stdout
        assert "--output-dir" in result.stdout
        assert "--auto" in result.stdout
