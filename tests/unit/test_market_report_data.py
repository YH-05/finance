"""Unit tests for market_report_data.py script.

scripts/market_report_data.py の単体テストを提供します。

このテストモジュールは以下のコンポーネントをテストします:

- collect_returns_data: 騰落率データ収集
- collect_sector_data: セクター分析データ収集
- collect_earnings_data: 決算カレンダーデータ収集
- save_all_reports: 全レポートのJSON出力
- create_parser: コマンドライン引数パーサー
- main: エントリーポイント
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from pytest import LogCaptureFixture


class TestCollectReturnsData:
    """collect_returns_data 関数のテスト。"""

    def test_正常系_returnsモジュールを呼び出して結果を取得できる(self) -> None:
        """generate_returns_report を呼び出してデータを返すことを確認。"""
        # Arrange
        mock_returns_data = {
            "as_of": "2026-01-19T12:00:00",
            "indices": [{"ticker": "^GSPC", "1D": 0.01}],
            "mag7": [],
            "sectors": [],
            "global_indices": [],
        }

        with patch(
            "scripts.market_report_data.generate_returns_report",
            return_value=mock_returns_data,
        ) as mock_generate:
            # Act
            from scripts.market_report_data import collect_returns_data

            result = collect_returns_data()

            # Assert
            mock_generate.assert_called_once()
            assert result == mock_returns_data


class TestCollectSectorData:
    """collect_sector_data 関数のテスト。"""

    def test_正常系_sectorモジュールを呼び出して結果を取得できる(self) -> None:
        """analyze_sector_performance を呼び出してデータを返すことを確認。"""
        # Arrange
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "top_sectors": [{"name": "Technology", "return_1w": 0.05}],
            "bottom_sectors": [{"name": "Energy", "return_1w": -0.02}],
        }

        with patch(
            "scripts.market_report_data.analyze_sector_performance",
            return_value=mock_result,
        ) as mock_analyze:
            # Act
            from scripts.market_report_data import collect_sector_data

            result = collect_sector_data()

            # Assert
            mock_analyze.assert_called_once()
            assert "top_sectors" in result
            assert "bottom_sectors" in result


class TestCollectEarningsData:
    """collect_earnings_data 関数のテスト。"""

    def test_正常系_earningsモジュールを呼び出して結果を取得できる(self) -> None:
        """get_upcoming_earnings を呼び出してデータを返すことを確認。"""
        # Arrange
        mock_earnings_data = {
            "upcoming_earnings": [
                {
                    "ticker": "NVDA",
                    "name": "NVIDIA",
                    "earnings_date": "2026-01-28",
                }
            ]
        }

        with patch(
            "scripts.market_report_data.get_upcoming_earnings",
            return_value=mock_earnings_data,
        ) as mock_get:
            # Act
            from scripts.market_report_data import collect_earnings_data

            result = collect_earnings_data()

            # Assert
            mock_get.assert_called_once()
            assert result == mock_earnings_data


class TestOutputJsonFiles:
    """save_all_reports 関数のJSON出力テスト。"""

    def test_正常系_指定ディレクトリにJSONファイルを出力できる(
        self,
        tmp_path: Path,
    ) -> None:
        """3つのJSONファイル(returns, sectors, earnings)が作成されることを確認。"""
        # Arrange
        mock_returns = {"as_of": "2026-01-19T12:00:00", "indices": []}
        mock_sectors = {"top_sectors": [], "bottom_sectors": []}
        mock_earnings = {"upcoming_earnings": []}

        with (
            patch(
                "scripts.market_report_data.collect_returns_data",
                return_value=mock_returns,
            ),
            patch(
                "scripts.market_report_data.collect_sector_data",
                return_value=mock_sectors,
            ),
            patch(
                "scripts.market_report_data.collect_earnings_data",
                return_value=mock_earnings,
            ),
        ):
            # Act
            from scripts.market_report_data import save_all_reports

            save_all_reports(output_dir=tmp_path)

            # Assert
            returns_file = tmp_path / "returns.json"
            sectors_file = tmp_path / "sectors.json"
            earnings_file = tmp_path / "earnings.json"

            assert returns_file.exists(), "returns.json should be created"
            assert sectors_file.exists(), "sectors.json should be created"
            assert earnings_file.exists(), "earnings.json should be created"

            # Verify content
            with returns_file.open() as f:
                returns_content = json.load(f)
            assert returns_content == mock_returns

            with sectors_file.open() as f:
                sectors_content = json.load(f)
            assert sectors_content == mock_sectors

            with earnings_file.open() as f:
                earnings_content = json.load(f)
            assert earnings_content == mock_earnings


class TestArgumentParser:
    """create_parser 関数のテスト。"""

    def test_正常系_outputオプションでディレクトリを指定できる(self) -> None:
        """--output オプションで出力ディレクトリを指定できることを確認。"""
        # Act
        from scripts.market_report_data import create_parser

        parser = create_parser()
        args = parser.parse_args(["--output", "/path/to/output"])

        # Assert
        assert args.output == "/path/to/output"

    def test_正常系_outputオプションのデフォルト値が設定される(self) -> None:
        """--output 未指定時にタイムスタンプ付きデフォルトパスが設定されることを確認。"""
        # Act
        from scripts.market_report_data import create_parser

        parser = create_parser()
        args = parser.parse_args([])

        # Assert
        # デフォルトはカレントディレクトリまたは指定のディレクトリ
        assert args.output is not None


class TestErrorHandling:
    """save_all_reports のエラーハンドリングテスト。"""

    def test_異常系_モジュールエラー時にログを出力して続行する(
        self,
        tmp_path: Path,
        caplog: LogCaptureFixture,
    ) -> None:
        """一つのモジュールがエラーでも他のモジュールは実行され、エラーログが出力される。"""
        # Arrange
        mock_sectors = {"top_sectors": [], "bottom_sectors": []}
        mock_earnings = {"upcoming_earnings": []}

        with (
            patch(
                "scripts.market_report_data.collect_returns_data",
                side_effect=Exception("Returns API error"),
            ),
            patch(
                "scripts.market_report_data.collect_sector_data",
                return_value=mock_sectors,
            ),
            patch(
                "scripts.market_report_data.collect_earnings_data",
                return_value=mock_earnings,
            ),
        ):
            # Act
            from scripts.market_report_data import save_all_reports

            # エラーが発生しても例外を投げず続行することを確認
            save_all_reports(output_dir=tmp_path)

            # Assert
            # returns.json は作成されない（または空）
            # sectors.json と earnings.json は作成される
            sectors_file = tmp_path / "sectors.json"
            earnings_file = tmp_path / "earnings.json"

            assert sectors_file.exists(), "sectors.json should be created despite error"
            assert earnings_file.exists(), (
                "earnings.json should be created despite error"
            )

            # エラーログが出力されていることを確認
            assert any(
                "Returns API error" in record.message
                or "error" in record.message.lower()
                for record in caplog.records
            )

    def test_異常系_出力ディレクトリが作成できない場合はエラー(
        self,
        tmp_path: Path,
    ) -> None:
        """PermissionError が発生した場合、例外が再スローされることを確認。"""
        # Arrange
        # 存在しない親ディレクトリを持つパスを指定
        invalid_path = tmp_path / "nonexistent" / "deep" / "path"

        with (
            patch(
                "scripts.market_report_data.collect_returns_data",
                return_value={},
            ),
            patch(
                "scripts.market_report_data.collect_sector_data",
                return_value={},
            ),
            patch(
                "scripts.market_report_data.collect_earnings_data",
                return_value={},
            ),
            patch(
                "pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")
            ),
        ):
            # Act & Assert
            from scripts.market_report_data import save_all_reports

            with pytest.raises(PermissionError, match="Permission denied"):
                save_all_reports(output_dir=invalid_path)


class TestMainFunction:
    """main 関数のエントリーポイントテスト。"""

    def test_正常系_main関数が全モジュールを実行して終了する(
        self,
        tmp_path: Path,
    ) -> None:
        """main 関数が全レポートを生成し、終了コード0を返すことを確認。"""
        # Arrange
        mock_returns = {"as_of": "2026-01-19T12:00:00", "indices": []}
        mock_sectors = {"top_sectors": [], "bottom_sectors": []}
        mock_earnings = {"upcoming_earnings": []}

        with (
            patch(
                "scripts.market_report_data.collect_returns_data",
                return_value=mock_returns,
            ),
            patch(
                "scripts.market_report_data.collect_sector_data",
                return_value=mock_sectors,
            ),
            patch(
                "scripts.market_report_data.collect_earnings_data",
                return_value=mock_earnings,
            ),
            patch("sys.argv", ["market_report_data.py", "--output", str(tmp_path)]),
        ):
            # Act
            from scripts.market_report_data import main

            exit_code = main()

            # Assert
            assert exit_code == 0

            # ファイルが作成されていることを確認
            assert (tmp_path / "returns.json").exists()
            assert (tmp_path / "sectors.json").exists()
            assert (tmp_path / "earnings.json").exists()

    def test_異常系_main関数でエラー発生時は終了コード1を返す(
        self,
        tmp_path: Path,
    ) -> None:
        """全モジュールが失敗した場合、終了コード1を返すことを確認。"""
        # Arrange
        with (
            patch(
                "scripts.market_report_data.collect_returns_data",
                side_effect=Exception("Returns error"),
            ),
            patch(
                "scripts.market_report_data.collect_sector_data",
                side_effect=Exception("Sector error"),
            ),
            patch(
                "scripts.market_report_data.collect_earnings_data",
                side_effect=Exception("Earnings error"),
            ),
            patch("sys.argv", ["market_report_data.py", "--output", str(tmp_path)]),
        ):
            # Act
            from scripts.market_report_data import main

            exit_code = main()

            # Assert
            # 全モジュールがエラーの場合は終了コード 1
            assert exit_code == 1
