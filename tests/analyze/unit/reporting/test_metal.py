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


class TestLoadPrice:
    """load_price メソッドのテスト."""

    @patch("analyze.reporting.metal.HistoricalCache")
    @patch("analyze.reporting.metal.MarketPerformanceAnalyzer")
    @patch("analyze.reporting.metal.load_project_env")
    def test_正常系_ドル指数と金属価格を結合できる(
        self,
        mock_load_env: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """ドル指数と金属価格を結合したロング形式のDataFrameが返されることを確認."""
        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        # モックの設定 - ドル指数データ
        mock_cache = MagicMock()
        df_dollars = pd.DataFrame(
            {"value": [110.0, 111.0, 112.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        df_dollars.index.name = "Date"
        mock_cache.get_series_df.return_value = df_dollars
        mock_cache_class.return_value = mock_cache

        # モックの設定 - 金属価格データ
        mock_analyzer = MagicMock()
        mock_analyzer.yf_download_with_curl.return_value = pd.DataFrame(
            {
                "Date": pd.to_datetime(
                    ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02"]
                ),
                "Ticker": ["GLD", "SLV", "GLD", "SLV"],
                "variable": ["Adj Close", "Adj Close", "Adj Close", "Adj Close"],
                "value": [180.0, 22.0, 181.0, 22.5],
            }
        )
        mock_analyzer.TICKERS_METAL = ["GLD", "SLV"]
        mock_analyzer_class.return_value = mock_analyzer

        # __init__をパッチして内部メソッドを呼び出す
        with patch.object(DollarsIndexAndMetalsAnalyzer, "__init__", lambda self: None):
            analyzer = DollarsIndexAndMetalsAnalyzer()
            analyzer.fred_cache = mock_cache
            # price_metal をセットアップ（_load_metal_priceの出力を模倣）
            analyzer.price_metal = pd.DataFrame(
                {"GLD": [180.0, 181.0], "SLV": [22.0, 22.5]},
                index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
            )
            analyzer.price_metal.index.name = "Date"

            result = analyzer.load_price()

        # 結果の検証
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert "Date" in result.columns
        assert "Ticker" in result.columns
        assert "value" in result.columns
        assert "variable" in result.columns
        # ロング形式であることを確認
        assert set(result["variable"].unique()) == {"Price"}
        # _load_dollars_index が呼ばれたことを確認
        mock_cache.get_series_df.assert_called_with("DTWEXAFEGS")

    @patch("analyze.reporting.metal.HistoricalCache")
    @patch("analyze.reporting.metal.MarketPerformanceAnalyzer")
    @patch("analyze.reporting.metal.load_project_env")
    def test_正常系_sqlite3を使用していない(
        self,
        mock_load_env: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """load_priceがsqlite3.connectを使用していないことを確認."""
        import inspect

        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        # メソッドのソースコードを取得
        source = inspect.getsource(DollarsIndexAndMetalsAnalyzer.load_price)

        # sqlite3.connect が含まれていないことを確認
        assert "sqlite3.connect" not in source
        # pd.read_sql が含まれていないことを確認
        assert "read_sql" not in source
        # _load_dollars_index を使用していることを確認
        assert "_load_dollars_index" in source


class TestCalcReturn:
    """calc_return メソッドのテスト."""

    @patch("analyze.reporting.metal.HistoricalCache")
    @patch("analyze.reporting.metal.MarketPerformanceAnalyzer")
    @patch("analyze.reporting.metal.load_project_env")
    def test_正常系_sqlite3を使用していない(
        self,
        mock_load_env: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """calc_returnがsqlite3.connectを使用していないことを確認."""
        import inspect

        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        # メソッドのソースコードを取得
        source = inspect.getsource(DollarsIndexAndMetalsAnalyzer.calc_return)

        # sqlite3.connect が含まれていないことを確認
        assert "sqlite3.connect" not in source
        # pd.read_sql が含まれていないことを確認
        assert "read_sql" not in source
        # _load_dollars_index を使用していることを確認
        assert "_load_dollars_index" in source

    @patch("analyze.reporting.metal.HistoricalCache")
    @patch("analyze.reporting.metal.MarketPerformanceAnalyzer")
    @patch("analyze.reporting.metal.load_project_env")
    def test_正常系_累積リターンを計算できる(
        self,
        mock_load_env: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """calc_returnが累積リターンを計算することを確認."""
        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        # モックの設定 - ドル指数データ
        mock_cache = MagicMock()
        df_dollars = pd.DataFrame(
            {"value": [100.0, 101.0, 102.0, 103.0]},
            index=pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
            ),
        )
        df_dollars.index.name = "Date"
        mock_cache.get_series_df.return_value = df_dollars
        mock_cache_class.return_value = mock_cache

        # __init__をパッチして内部メソッドを呼び出す
        with patch.object(DollarsIndexAndMetalsAnalyzer, "__init__", lambda self: None):
            analyzer = DollarsIndexAndMetalsAnalyzer()
            analyzer.fred_cache = mock_cache
            # price_metal をセットアップ
            analyzer.price_metal = pd.DataFrame(
                {"GLD": [180.0, 182.0, 184.0, 186.0], "SLV": [20.0, 20.5, 21.0, 21.5]},
                index=pd.to_datetime(
                    ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
                ),
            )
            analyzer.price_metal.index.name = "Date"

            result = analyzer.calc_return(start_date="2020-01-01")

        # 結果の検証
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        # ドル指数の列が含まれていることを確認
        assert "value" in result.columns
        # 金属価格の列が含まれていることを確認
        assert "GLD" in result.columns
        assert "SLV" in result.columns
        # 最初の値が1.0（基準点）になっていることを確認
        assert result["GLD"].iloc[0] == pytest.approx(1.0)
        assert result["SLV"].iloc[0] == pytest.approx(1.0)
        # _load_dollars_index が呼ばれたことを確認
        mock_cache.get_series_df.assert_called_with("DTWEXAFEGS")

    @patch("analyze.reporting.metal.HistoricalCache")
    @patch("analyze.reporting.metal.MarketPerformanceAnalyzer")
    @patch("analyze.reporting.metal.load_project_env")
    def test_正常系_戻り値のDataFrame構造が正しい(
        self,
        mock_load_env: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """calc_returnの戻り値が期待される構造を持つことを確認."""
        from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

        # モックの設定 - ドル指数データ
        mock_cache = MagicMock()
        df_dollars = pd.DataFrame(
            {"value": [100.0, 101.0, 102.0]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        )
        df_dollars.index.name = "Date"
        mock_cache.get_series_df.return_value = df_dollars
        mock_cache_class.return_value = mock_cache

        # __init__をパッチして内部メソッドを呼び出す
        with patch.object(DollarsIndexAndMetalsAnalyzer, "__init__", lambda self: None):
            analyzer = DollarsIndexAndMetalsAnalyzer()
            analyzer.fred_cache = mock_cache
            # price_metal をセットアップ
            analyzer.price_metal = pd.DataFrame(
                {"GLD": [180.0, 181.0, 182.0]},
                index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            )
            analyzer.price_metal.index.name = "Date"

            result = analyzer.calc_return(start_date="2020-01-01")

        # インデックスがDateTimeIndexであることを確認
        assert isinstance(result.index, pd.DatetimeIndex)
        # DataFrameであることを確認
        assert isinstance(result, pd.DataFrame)
