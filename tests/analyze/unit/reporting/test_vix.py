"""Tests for VIX reporting module.

TDD Green phase complete: All tests pass with the improved implementation.

受け入れ条件:
- [x] TestLoadMultipleSeries クラス作成
- [x] test_正常系_複数シリーズを結合できる テスト
- [x] test_異常系_全シリーズ失敗でエラー テスト
- [x] test_エッジケース_部分欠損で警告つき成功 テスト
- [x] HistoricalCache をモック化
- [x] テストが通ることを確認（Green）
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from analyze.reporting.vix import _load_multiple_series
from market.errors import FREDCacheNotFoundError


class TestLoadMultipleSeries:
    """Tests for _load_multiple_series function.

    _load_multiple_series() は複数のFREDシリーズをHistoricalCacheから
    ロードして結合する関数。改修後は以下の動作が期待される:

    1. 全シリーズが見つかった場合: date, variable, value 列を持つDataFrameを返す
    2. 全シリーズがキャッシュにない場合: FREDCacheNotFoundErrorを発生させる
    3. 一部のシリーズのみ見つかった場合: 警告を出力し、見つかったシリーズのみで結果を返す
    """

    @patch("analyze.reporting.vix.HistoricalCache")
    def test_正常系_複数シリーズを結合できる(self, mock_cache_class: MagicMock) -> None:
        """複数のFREDシリーズを正しく結合できることを確認.

        Docstringに記載された列名 (date, variable, value) を期待する。
        現在の実装ではreset_index()により列名がindexになっているため、
        このテストは失敗する（Red状態）。改修でdate列名を正しく設定する必要がある。
        """
        # Arrange: モックデータの準備
        # HistoricalCache.get_series_df() はDatetimeIndexを持つDataFrameを返す
        dates_vix = pd.date_range("2026-01-01", periods=3, freq="D")
        dates_spread = pd.date_range("2026-01-01", periods=3, freq="D")

        mock_cache = MagicMock()

        def mock_get_series_df(series_id: str) -> pd.DataFrame | None:
            if series_id == "VIXCLS":
                df = pd.DataFrame(
                    {"value": [15.0, 16.0, 17.0]},
                    index=dates_vix,
                )
                df.index.name = None  # HistoricalCacheの実装に合わせる
                return df
            elif series_id == "BAMLH0A0HYM2":
                df = pd.DataFrame(
                    {"value": [3.5, 3.6, 3.7]},
                    index=dates_spread,
                )
                df.index.name = None
                return df
            return None

        mock_cache.get_series_df.side_effect = mock_get_series_df
        mock_cache_class.return_value = mock_cache

        # Act
        result = _load_multiple_series(["VIXCLS", "BAMLH0A0HYM2"])

        # Assert
        assert not result.empty
        # Docstringで定義された列名を確認
        assert "date" in result.columns, "date列が必要（現在はindexになっている）"
        assert "variable" in result.columns
        assert "value" in result.columns
        # 3行 x 2シリーズ = 6行
        assert len(result) == 6
        assert set(result["variable"].unique()) == {"VIXCLS", "BAMLH0A0HYM2"}

    @patch("analyze.reporting.vix.HistoricalCache")
    def test_異常系_全シリーズ失敗でFREDCacheNotFoundError(
        self, mock_cache_class: MagicMock
    ) -> None:
        """全てのシリーズがキャッシュに存在しない場合、FREDCacheNotFoundErrorを発生させる.

        現在の実装では空のDataFrameを返すが、改修後は例外を発生させるべき。
        これによりキャッシュ同期が必要であることを呼び出し元に明確に伝える。

        期待動作（改修後）:
        - FREDCacheNotFoundError を raise
        - エラーオブジェクトに欠落したシリーズIDのリストを含める
        """
        # Arrange: 全シリーズがNoneを返す（キャッシュに存在しない）
        mock_cache = MagicMock()
        mock_cache.get_series_df.return_value = None
        mock_cache_class.return_value = mock_cache

        # Act & Assert
        # 改修後: FREDCacheNotFoundError が発生するべき
        with pytest.raises(FREDCacheNotFoundError) as exc_info:
            _load_multiple_series(["VIXCLS", "BAMLH0A0HYM2"])

        # エラーに欠落したシリーズIDが含まれることを確認
        assert "VIXCLS" in exc_info.value.series_ids
        assert "BAMLH0A0HYM2" in exc_info.value.series_ids

    @patch("analyze.reporting.vix.HistoricalCache")
    def test_エッジケース_部分欠損で警告つき成功(
        self, mock_cache_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """一部のシリーズのみキャッシュに存在する場合、警告を出力して成功したシリーズのみ返す.

        現在の実装では警告なく成功するが、改修後は警告を出力するべき。
        これにより運用者がキャッシュ同期の必要性を認識できる。

        期待動作（改修後）:
        - 成功したシリーズのみでDataFrameを返す
        - 欠落したシリーズについてWARNINGログを出力
        """
        # Arrange: 一部のシリーズのみ成功
        dates = pd.date_range("2026-01-01", periods=3, freq="D")

        mock_cache = MagicMock()

        def mock_get_series_df(series_id: str) -> pd.DataFrame | None:
            if series_id == "VIXCLS":
                df = pd.DataFrame(
                    {"value": [15.0, 16.0, 17.0]},
                    index=dates,
                )
                df.index.name = None
                return df
            # BAMLH0A0HYM2 はキャッシュに存在しない
            return None

        mock_cache.get_series_df.side_effect = mock_get_series_df
        mock_cache_class.return_value = mock_cache

        # Act
        result = _load_multiple_series(["VIXCLS", "BAMLH0A0HYM2"])

        # Assert: 成功したシリーズのみが含まれる
        assert not result.empty
        assert "VIXCLS" in result["variable"].unique()
        assert "BAMLH0A0HYM2" not in result["variable"].unique()
        assert len(result) == 3  # VIXCLSの3行のみ

        # 改修後: 警告ログが出力されるべき
        # caplog を使用して警告ログを確認
        # 現在の実装では警告は出力されないが、改修後は出力されるべき
        warning_messages = [
            record.message for record in caplog.records if record.levelname == "WARNING"
        ]
        assert any("BAMLH0A0HYM2" in msg for msg in warning_messages), (
            "欠落したシリーズについて警告が出力されるべき"
        )

    @patch("analyze.reporting.vix.HistoricalCache")
    def test_正常系_単一シリーズでも動作する(self, mock_cache_class: MagicMock) -> None:
        """単一のシリーズIDでも正しく動作することを確認.

        単一シリーズの場合も複数シリーズと同じ形式のDataFrameを返す。
        """
        # Arrange
        dates = pd.date_range("2026-01-01", periods=5, freq="D")
        mock_cache = MagicMock()
        df = pd.DataFrame(
            {"value": [15.0, 16.0, 17.0, 18.0, 19.0]},
            index=dates,
        )
        df.index.name = None
        mock_cache.get_series_df.return_value = df
        mock_cache_class.return_value = mock_cache

        # Act
        result = _load_multiple_series(["VIXCLS"])

        # Assert
        assert not result.empty
        assert len(result) == 5
        assert list(result["variable"].unique()) == ["VIXCLS"]

    @patch("analyze.reporting.vix.HistoricalCache")
    def test_エッジケース_空のシリーズリストで空のDataFrame(
        self, mock_cache_class: MagicMock
    ) -> None:
        """空のシリーズリストを渡した場合、空のDataFrameを返す.

        空リストは有効な入力であり、空のDataFrame（正しい列名付き）を返す。
        """
        # Arrange
        mock_cache = MagicMock()
        mock_cache_class.return_value = mock_cache

        # Act
        result = _load_multiple_series([])

        # Assert
        assert result.empty
        assert list(result.columns) == ["date", "variable", "value"]
        # get_series_df は呼び出されないはず
        mock_cache.get_series_df.assert_not_called()

    @patch("analyze.reporting.vix.HistoricalCache")
    def test_正常系_データフレームの列順序が正しい(
        self, mock_cache_class: MagicMock
    ) -> None:
        """返されるDataFrameの列順序が [date, variable, value] であることを確認.

        Docstringで定義された列名・順序に従う。現在の実装ではreset_index()により
        列名がindexになっているため、このテストは失敗する（Red状態）。
        """
        # Arrange
        dates = pd.date_range("2026-01-01", periods=2, freq="D")
        mock_cache = MagicMock()
        df = pd.DataFrame(
            {"value": [15.0, 16.0]},
            index=dates,
        )
        df.index.name = None
        mock_cache.get_series_df.return_value = df
        mock_cache_class.return_value = mock_cache

        # Act
        result = _load_multiple_series(["VIXCLS"])

        # Assert
        assert list(result.columns) == ["date", "variable", "value"]
