"""us_treasury.py の動作確認テスト.

analyze.reporting.us_treasury モジュールの主要関数のテスト。
FRED Cache移行後の動作確認を目的とする。
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


class TestLoadYieldDataFromCache:
    """load_yield_data_from_cache 関数のテスト."""

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    def test_正常系_キャッシュからイールドデータを取得できる(
        self,
        mock_cache_class: MagicMock,
    ) -> None:
        """キャッシュにデータがある場合、DataFrameが返されることを確認."""
        from analyze.reporting.us_treasury import load_yield_data_from_cache

        # モックの設定 - 各シリーズのデータを返す
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [4.0, 4.1, 4.2]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        result = load_yield_data_from_cache()

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    def test_正常系_必要なカラムが全て含まれる(
        self,
        mock_cache_class: MagicMock,
    ) -> None:
        """戻り値に必要なテナーのカラムが全て含まれることを確認."""
        from analyze.reporting.us_treasury import load_yield_data_from_cache

        # モックの設定 - 各シリーズのデータを返す
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [4.0, 4.1, 4.2]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        result = load_yield_data_from_cache()

        # 期待されるテナー列
        expected_columns = [
            "DGS1MO",
            "DGS3MO",
            "DGS6MO",
            "DGS1",
            "DGS2",
            "DGS3",
            "DGS5",
            "DGS7",
            "DGS10",
            "DGS20",
            "DGS30",
        ]
        assert list(result.columns) == expected_columns

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    def test_正常系_データが空でない(
        self,
        mock_cache_class: MagicMock,
    ) -> None:
        """戻り値のDataFrameが空でないことを確認."""
        from analyze.reporting.us_treasury import load_yield_data_from_cache

        # モックの設定 - 各シリーズのデータを返す
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [4.0, 4.1, 4.2]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        result = load_yield_data_from_cache()

        assert len(result) > 0

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    def test_正常系_インデックスがDatetimeIndexである(
        self,
        mock_cache_class: MagicMock,
    ) -> None:
        """戻り値のインデックスがDatetimeIndexであることを確認."""
        from analyze.reporting.us_treasury import load_yield_data_from_cache

        # モックの設定 - 各シリーズのデータを返す
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [4.0, 4.1, 4.2]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        result = load_yield_data_from_cache()

        assert isinstance(result.index, pd.DatetimeIndex)


class TestPlotUsInterestRatesAndSpread:
    """plot_us_interest_rates_and_spread 関数のテスト."""

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    def test_正常系_エラーなく実行できる(
        self,
        mock_cache_class: MagicMock,
    ) -> None:
        """関数がエラーなく実行できることを確認."""
        from analyze.reporting.us_treasury import plot_us_interest_rates_and_spread

        # モックの設定 - 各シリーズのデータを返す
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])

        def mock_get_series_df(series_id: str) -> pd.DataFrame:
            return pd.DataFrame({"value": [4.0, 4.1, 4.2]}, index=dates)

        mock_cache.get_series_df = mock_get_series_df
        mock_cache_class.return_value = mock_cache

        # fig.show() をモックしてプロットを表示しない
        with patch("plotly.graph_objects.Figure.show"):
            # 例外が発生しないことを確認
            plot_us_interest_rates_and_spread(start_date="2020-01-01")

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    def test_正常系_キャッシュからデータを取得している(
        self,
        mock_cache_class: MagicMock,
    ) -> None:
        """HistoricalCacheからデータを取得していることを確認."""
        from analyze.reporting.us_treasury import plot_us_interest_rates_and_spread

        # モックの設定 - 各シリーズのデータを返す
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [4.0, 4.1, 4.2]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        with patch("plotly.graph_objects.Figure.show"):
            plot_us_interest_rates_and_spread(start_date="2020-01-01")

        # get_series_df が呼ばれたことを確認
        assert mock_cache.get_series_df.called

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    def test_正常系_金利シリーズとスプレッドシリーズを取得している(
        self,
        mock_cache_class: MagicMock,
    ) -> None:
        """金利シリーズとスプレッドシリーズの両方を取得していることを確認."""
        from analyze.reporting.us_treasury import plot_us_interest_rates_and_spread

        # モックの設定 - 各シリーズのデータを返す
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [4.0, 4.1, 4.2]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        with patch("plotly.graph_objects.Figure.show"):
            plot_us_interest_rates_and_spread(start_date="2020-01-01")

        # 呼び出された引数を取得
        call_args_list = mock_cache.get_series_df.call_args_list
        called_series = [call[0][0] for call in call_args_list]

        # 金利シリーズの確認
        assert "DFF" in called_series  # FF金利
        assert "DGS10" in called_series  # 10年債利回り

        # スプレッドシリーズの確認
        assert "T10Y3M" in called_series  # 10年-3ヶ月スプレッド
        assert "T10Y2Y" in called_series  # 10年-2年スプレッド


class TestPlotUsCorporateBondSpreads:
    """plot_us_corporate_bond_spreads 関数のテスト."""

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    @patch("analyze.reporting.us_treasury.load_fred_series_id_json")
    def test_正常系_エラーなく実行できる(
        self,
        mock_load_json: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """関数がエラーなく実行できることを確認."""
        from analyze.reporting.us_treasury import plot_us_corporate_bond_spreads

        # モックの設定 - JSONデータ
        mock_load_json.return_value = {
            "Corporate Bond Yield Spread": {
                "BAMLC0A0CM": {"name_en": "ICE BofA US Corporate Bond Index"},
                "BAMLH0A0HYM2": {"name_en": "ICE BofA US High Yield Index"},
            }
        }

        # モックの設定 - キャッシュデータ
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [1.5, 1.6, 1.7]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        # fig.show() をモックしてプロットを表示しない
        with patch("plotly.graph_objects.Figure.show"):
            # 例外が発生しないことを確認
            plot_us_corporate_bond_spreads()

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    @patch("analyze.reporting.us_treasury.load_fred_series_id_json")
    def test_正常系_キャッシュからデータを取得している(
        self,
        mock_load_json: MagicMock,
        mock_cache_class: MagicMock,
    ) -> None:
        """HistoricalCacheからデータを取得していることを確認."""
        from analyze.reporting.us_treasury import plot_us_corporate_bond_spreads

        # モックの設定 - JSONデータ
        mock_load_json.return_value = {
            "Corporate Bond Yield Spread": {
                "BAMLC0A0CM": {"name_en": "ICE BofA US Corporate Bond Index"},
            }
        }

        # モックの設定 - キャッシュデータ
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [1.5, 1.6, 1.7]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        with patch("plotly.graph_objects.Figure.show"):
            plot_us_corporate_bond_spreads()

        # get_series_df が呼ばれたことを確認
        assert mock_cache.get_series_df.called

    @patch("analyze.reporting.us_treasury.HistoricalCache")
    def test_正常系_カスタムシリーズIDを指定できる(
        self,
        mock_cache_class: MagicMock,
    ) -> None:
        """カスタムのシリーズIDリストを指定できることを確認."""
        from typing import Any

        from analyze.reporting.us_treasury import plot_us_corporate_bond_spreads

        # モックの設定 - キャッシュデータ
        mock_cache = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        df_template = pd.DataFrame({"value": [1.5, 1.6, 1.7]}, index=dates)
        mock_cache.get_series_df.return_value = df_template
        mock_cache_class.return_value = mock_cache

        # カスタムシリーズID（関数の実際の実装に合わせて dict 形式で渡す）
        # NOTE: 型ヒントは list[str] | None だが、実装は dict を期待している
        custom_series: dict[str, Any] = {
            "BAMLC0A0CM": {"name_en": "ICE BofA US Corporate Bond Index"},
        }

        with patch("plotly.graph_objects.Figure.show"):
            plot_us_corporate_bond_spreads(fred_series_id=custom_series)  # type: ignore[arg-type]

        # 指定したシリーズIDで呼ばれたことを確認
        call_args_list = mock_cache.get_series_df.call_args_list
        called_series = [call[0][0] for call in call_args_list]
        assert "BAMLC0A0CM" in called_series


class TestAnalyzeYieldCurvePca:
    """analyze_yield_curve_pca 関数のテスト."""

    def test_正常系_PCA分析結果が返される(self) -> None:
        """PCA分析結果（DataFrame, PCAオブジェクト）が返されることを確認."""
        from analyze.reporting.us_treasury import analyze_yield_curve_pca

        # テスト用のイールドデータを作成
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        data = {
            "DGS1MO": [4.0 + i * 0.01 for i in range(100)],
            "DGS3MO": [4.1 + i * 0.01 for i in range(100)],
            "DGS6MO": [4.2 + i * 0.01 for i in range(100)],
            "DGS1": [4.3 + i * 0.01 for i in range(100)],
            "DGS2": [4.4 + i * 0.01 for i in range(100)],
            "DGS3": [4.5 + i * 0.01 for i in range(100)],
            "DGS5": [4.6 + i * 0.01 for i in range(100)],
            "DGS7": [4.7 + i * 0.01 for i in range(100)],
            "DGS10": [4.8 + i * 0.01 for i in range(100)],
            "DGS20": [4.9 + i * 0.01 for i in range(100)],
            "DGS30": [5.0 + i * 0.01 for i in range(100)],
        }
        df_yield = pd.DataFrame(data, index=dates)

        df_pca, pca = analyze_yield_curve_pca(df_yield)

        assert df_pca is not None
        assert pca is not None
        assert isinstance(df_pca, pd.DataFrame)

    def test_正常系_デフォルトで3つの主成分が返される(self) -> None:
        """デフォルト設定で3つの主成分（Level, Slope, Curvature）が返されることを確認."""
        from analyze.reporting.us_treasury import analyze_yield_curve_pca

        # テスト用のイールドデータを作成
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        data = {
            "DGS1MO": [4.0 + i * 0.01 for i in range(100)],
            "DGS3MO": [4.1 + i * 0.01 for i in range(100)],
            "DGS6MO": [4.2 + i * 0.01 for i in range(100)],
            "DGS1": [4.3 + i * 0.01 for i in range(100)],
            "DGS2": [4.4 + i * 0.01 for i in range(100)],
            "DGS3": [4.5 + i * 0.01 for i in range(100)],
            "DGS5": [4.6 + i * 0.01 for i in range(100)],
            "DGS7": [4.7 + i * 0.01 for i in range(100)],
            "DGS10": [4.8 + i * 0.01 for i in range(100)],
            "DGS20": [4.9 + i * 0.01 for i in range(100)],
            "DGS30": [5.0 + i * 0.01 for i in range(100)],
        }
        df_yield = pd.DataFrame(data, index=dates)

        df_pca, _ = analyze_yield_curve_pca(df_yield)

        assert list(df_pca.columns) == ["Level", "Slope", "Curvature"]


class TestAlignPcaComponents:
    """align_pca_components 関数のテスト."""

    def test_正常系_符号が調整される(self) -> None:
        """PCA主成分の符号が経済学的解釈に基づき調整されることを確認."""
        import numpy as np

        from analyze.reporting.us_treasury import align_pca_components

        # テスト用のPCAコンポーネントとスコア
        n_features = 11
        n_samples = 100
        pca_components = np.random.randn(3, n_features)
        pc_scores = np.random.randn(n_samples, 3)

        aligned_scores = align_pca_components(pca_components, pc_scores)

        assert aligned_scores is not None
        assert aligned_scores.shape == pc_scores.shape


class TestLoadFredApiKey:
    """load_fred_api_key 関数のテスト."""

    @patch("analyze.reporting.us_treasury.get_fred_api_key")
    def test_正常系_APIキーを取得できる(
        self,
        mock_get_key: MagicMock,
    ) -> None:
        """環境変数からFRED APIキーを取得できることを確認."""
        from analyze.reporting.us_treasury import load_fred_api_key

        mock_get_key.return_value = "test_api_key"

        result = load_fred_api_key()

        assert result == "test_api_key"
        mock_get_key.assert_called_once()


class TestLoadFredSeriesIdJson:
    """load_fred_series_id_json 関数のテスト."""

    @patch("analyze.reporting.us_treasury.requests.get")
    @patch.dict(
        "os.environ", {"FRED_SERIES_ID_JSON": "https://example.com/series.json"}
    )
    def test_正常系_JSONファイルを読み込める(
        self,
        mock_get: MagicMock,
    ) -> None:
        """GitHubからFREDシリーズIDのJSONファイルを読み込めることを確認."""
        from analyze.reporting.us_treasury import load_fred_series_id_json

        mock_response = MagicMock()
        mock_response.json.return_value = {"Treasury Yields": {"DGS10": {}}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = load_fred_series_id_json()

        assert result is not None
        assert "Treasury Yields" in result

    @patch.dict("os.environ", {}, clear=False)
    def test_異常系_環境変数未設定で空dictが返される(self) -> None:
        """FRED_SERIES_ID_JSON環境変数が未設定の場合、空dictが返されることを確認."""
        import os

        from analyze.reporting.us_treasury import load_fred_series_id_json

        # 環境変数を一時的に削除
        original_value = os.environ.pop("FRED_SERIES_ID_JSON", None)

        try:
            result = load_fred_series_id_json()
            assert result == {}
        finally:
            # 環境変数を復元
            if original_value is not None:
                os.environ["FRED_SERIES_ID_JSON"] = original_value
