"""metal.py の DollarsIndexAndMetalsAnalyzer テスト.

analyze.reporting.metal モジュールの DollarsIndexAndMetalsAnalyzer クラスのテスト。
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


class TestLoadDollarsIndex:
    """_load_dollars_index メソッドのテスト."""

    @patch("analyze.reporting.metal.HistoricalCache")
    @patch("analyze.reporting.metal.MarketPerformanceAnalyzer")
    @patch("analyze.reporting.metal.load_project_env")
    def test_正常系_キャッシュからドル指数データを取得できる(
        self,
        mock_load_env: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """キャッシュにデータがある場合、DataFrameが返されることを確認."""
        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        # モックの設定
        mock_cache = MagicMock()
        mock_cache.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0, 111.0, 112.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        mock_cache_class.return_value = mock_cache

        mock_analyzer = MagicMock()
        mock_analyzer.yf_download_with_curl.return_value = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "Ticker": ["GLD", "GLD"],
                "variable": ["Adj Close", "Adj Close"],
                "value": [180.0, 181.0],
            }
        ).set_index("Date")
        mock_analyzer.TICKERS_METAL = ["GLD"]
        mock_analyzer_class.return_value = mock_analyzer

        # _load_dollars_index を直接呼び出すため、__init__をパッチ
        with patch.object(DollarsIndexAndMetalsAnalyzer, "__init__", lambda self: None):
            analyzer = DollarsIndexAndMetalsAnalyzer()
            analyzer.fred_cache = mock_cache

            result = analyzer._load_dollars_index()

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.index.name == "Date"
        mock_cache.get_series_df.assert_called_once_with("DTWEXAFEGS")

    @patch("analyze.reporting.metal.HistoricalCache")
    @patch("analyze.reporting.metal.MarketPerformanceAnalyzer")
    @patch("analyze.reporting.metal.load_project_env")
    def test_異常系_キャッシュにデータがない場合ValueError(
        self,
        mock_load_env: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """キャッシュにデータがない場合、ValueErrorが発生することを確認."""
        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        # モックの設定 - キャッシュはNoneを返す
        mock_cache = MagicMock()
        mock_cache.get_series_df.return_value = None
        mock_cache_class.return_value = mock_cache

        # _load_dollars_index を直接呼び出すため、__init__をパッチ
        with patch.object(DollarsIndexAndMetalsAnalyzer, "__init__", lambda self: None):
            analyzer = DollarsIndexAndMetalsAnalyzer()
            analyzer.fred_cache = mock_cache

            with pytest.raises(ValueError, match="DTWEXAFEGS not found in cache"):
                analyzer._load_dollars_index()

    @patch("analyze.reporting.metal.HistoricalCache")
    @patch("analyze.reporting.metal.MarketPerformanceAnalyzer")
    @patch("analyze.reporting.metal.load_project_env")
    def test_正常系_戻り値のインデックス名がDateである(
        self,
        mock_load_env: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """戻り値のインデックス名が 'Date' であることを確認."""
        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        # モックの設定
        mock_cache = MagicMock()
        # インデックス名がない状態のDataFrame
        df = pd.DataFrame(
            {"value": [110.0, 111.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
        )
        df.index.name = None  # 明示的にインデックス名をNoneに
        mock_cache.get_series_df.return_value = df
        mock_cache_class.return_value = mock_cache

        # _load_dollars_index を直接呼び出すため、__init__をパッチ
        with patch.object(DollarsIndexAndMetalsAnalyzer, "__init__", lambda self: None):
            analyzer = DollarsIndexAndMetalsAnalyzer()
            analyzer.fred_cache = mock_cache

            result = analyzer._load_dollars_index()

        assert result.index.name == "Date"


class TestLoadDollarsIndexDocstring:
    """_load_dollars_index メソッドの Docstring テスト."""

    def test_正常系_NumPy形式のDocstringが存在する(self) -> None:
        """NumPy形式のDocstringが記述されていることを確認."""
        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        docstring = DollarsIndexAndMetalsAnalyzer._load_dollars_index.__doc__
        assert docstring is not None
        # NumPy形式の要素が含まれていることを確認
        assert "Returns" in docstring
        assert "Raises" in docstring
        assert "ValueError" in docstring
