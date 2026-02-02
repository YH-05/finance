"""Tests for VIX reporting module.

TDD Green phase complete: All tests pass with the improved implementation.

受け入れ条件:
- [x] TestLoadMultipleSeries クラス作成
- [x] test_正常系_複数シリーズを結合できる テスト
- [x] test_異常系_全シリーズ失敗でエラー テスト
- [x] test_エッジケース_部分欠損で警告つき成功 テスト
- [x] HistoricalCache をモック化
- [x] テストが通ることを確認（Green）

Issue #2837 追加テスト:
- [ ] TestPlotVixAndHighYieldSpread クラス作成
- [ ] test_正常系_データがある場合にFigureを返す
- [ ] test_異常系_FREDCacheNotFoundErrorが再発生する
- [ ] test_異常系_pivot前にカラムが不足でValueError
- [ ] test_エッジケース_pivot後にシリーズが不足でNoneを返す
- [ ] test_正常系_関数開始時に情報ログが出力される
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import plotly.graph_objects as go
import pytest

from analyze.reporting.vix import _load_multiple_series, plot_vix_and_high_yield_spread
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


class TestPlotVixAndHighYieldSpread:
    """Tests for plot_vix_and_high_yield_spread function.

    Issue #2837: plot_vix_and_high_yield_spread 関数改修

    受け入れ条件:
    1. 関数開始時の情報ログ
    2. FREDCacheNotFoundError の catch & re-raise
    3. pivot 前のカラム検証（date, variable, value）
    4. pivot 後のシリーズ検証
    5. 戻り値の型ヒントを go.Figure | None に変更
    6. Docstring に Raises セクション追加
    """

    @patch("analyze.reporting.vix._load_multiple_series")
    def test_正常系_データがある場合にFigureを返す(self, mock_load: MagicMock) -> None:
        """正常なデータがある場合、go.Figureを返すことを確認.

        改修後の関数は fig.show() を呼ばず、Figureを返すように変更される。
        """
        # Arrange: 正常なモックデータ
        dates = pd.date_range("2026-01-01", periods=5, freq="D")
        mock_data = pd.DataFrame(
            {
                "date": list(dates) * 2,
                "variable": ["VIXCLS"] * 5 + ["BAMLH0A0HYM2"] * 5,
                "value": [15.0, 16.0, 17.0, 18.0, 19.0, 3.5, 3.6, 3.7, 3.8, 3.9],
            }
        )
        mock_load.return_value = mock_data

        # Act
        result = plot_vix_and_high_yield_spread()

        # Assert
        assert isinstance(result, go.Figure), "戻り値はgo.Figureであるべき"
        mock_load.assert_called_once_with(["VIXCLS", "BAMLH0A0HYM2"])

    @patch("analyze.reporting.vix._load_multiple_series")
    def test_異常系_FREDCacheNotFoundErrorが再発生する(
        self, mock_load: MagicMock
    ) -> None:
        """_load_multiple_seriesがFREDCacheNotFoundErrorを発生させた場合、再発生させる.

        改修後の関数はFREDCacheNotFoundErrorをcatchしてre-raiseする。
        """
        # Arrange: FREDCacheNotFoundErrorを発生させる
        mock_load.side_effect = FREDCacheNotFoundError(["VIXCLS", "BAMLH0A0HYM2"])

        # Act & Assert
        with pytest.raises(FREDCacheNotFoundError) as exc_info:
            plot_vix_and_high_yield_spread()

        assert "VIXCLS" in exc_info.value.series_ids
        assert "BAMLH0A0HYM2" in exc_info.value.series_ids

    @patch("analyze.reporting.vix._load_multiple_series")
    def test_異常系_pivot前にカラムが不足でValueError(
        self, mock_load: MagicMock
    ) -> None:
        """_load_multiple_seriesの戻り値に必須カラムが不足している場合、ValueErrorを発生させる.

        改修後の関数はpivot前にカラム検証を行う。
        必須カラム: date, variable, value
        """
        # Arrange: 必須カラムが不足したデータ（variableがない）
        mock_data = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=3, freq="D"),
                "value": [15.0, 16.0, 17.0],
                # "variable" カラムがない
            }
        )
        mock_load.return_value = mock_data

        # Act & Assert
        with pytest.raises(ValueError, match="Missing columns"):
            plot_vix_and_high_yield_spread()

    @patch("analyze.reporting.vix._load_multiple_series")
    def test_エッジケース_pivot後にシリーズが不足でNoneを返す(
        self, mock_load: MagicMock
    ) -> None:
        """pivot後に必要なシリーズ（VIXCLS, BAMLH0A0HYM2）が不足している場合、Noneを返す.

        改修後の関数はpivot後にシリーズ検証を行い、データ不足時はNoneを返す。
        """
        # Arrange: VIXCLSのみのデータ（BAMLH0A0HYM2がない）
        dates = pd.date_range("2026-01-01", periods=3, freq="D")
        mock_data = pd.DataFrame(
            {
                "date": list(dates),
                "variable": ["VIXCLS"] * 3,
                "value": [15.0, 16.0, 17.0],
            }
        )
        mock_load.return_value = mock_data

        # Act
        result = plot_vix_and_high_yield_spread()

        # Assert
        assert result is None, "データ不足時はNoneを返すべき"

    @patch("analyze.reporting.vix._load_multiple_series")
    def test_正常系_関数開始時に情報ログが出力される(
        self, mock_load: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """関数開始時に情報ログが出力されることを確認.

        改修後の関数は logger.info() で開始ログを出力する。
        """
        # Arrange
        dates = pd.date_range("2026-01-01", periods=5, freq="D")
        mock_data = pd.DataFrame(
            {
                "date": list(dates) * 2,
                "variable": ["VIXCLS"] * 5 + ["BAMLH0A0HYM2"] * 5,
                "value": [15.0, 16.0, 17.0, 18.0, 19.0, 3.5, 3.6, 3.7, 3.8, 3.9],
            }
        )
        mock_load.return_value = mock_data

        # Act
        with caplog.at_level("INFO"):
            plot_vix_and_high_yield_spread()

        # Assert
        info_messages = [
            record.message for record in caplog.records if record.levelname == "INFO"
        ]
        assert any("VIX" in msg and "High Yield" in msg for msg in info_messages), (
            "関数開始時の情報ログが出力されるべき"
        )

    @patch("analyze.reporting.vix._load_multiple_series")
    def test_正常系_Figureに正しいトレースが含まれる(
        self, mock_load: MagicMock
    ) -> None:
        """返されるFigureに必要なトレースが含まれることを確認.

        改修後の関数は以下のトレースを含むFigureを返す:
        - VIX
        - VIX mean
        - US High Yield Index Option-Adjusted Spread
        - Spread mean
        """
        # Arrange
        dates = pd.date_range("2026-01-01", periods=5, freq="D")
        mock_data = pd.DataFrame(
            {
                "date": list(dates) * 2,
                "variable": ["VIXCLS"] * 5 + ["BAMLH0A0HYM2"] * 5,
                "value": [15.0, 16.0, 17.0, 18.0, 19.0, 3.5, 3.6, 3.7, 3.8, 3.9],
            }
        )
        mock_load.return_value = mock_data

        # Act
        result = plot_vix_and_high_yield_spread()

        # Assert
        assert result is not None
        trace_names = [trace.name for trace in result.data]
        assert any("VIX" in name for name in trace_names), "VIXトレースが必要"
        assert any("mean" in name.lower() for name in trace_names), (
            "平均線トレースが必要"
        )
