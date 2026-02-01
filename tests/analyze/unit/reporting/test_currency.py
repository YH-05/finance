"""CurrencyAnalyzer のテスト.

TDDに基づいてテストを先に作成し、実装を後から行う。
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from analyze.reporting.currency import CurrencyAnalyzer
from pandas import DataFrame


class TestCurrencyAnalyzerInit:
    """CurrencyAnalyzer の初期化テスト."""

    def test_正常系_デフォルト初期化が成功する(self) -> None:
        """CurrencyAnalyzerがデフォルト設定で初期化できることを確認."""
        analyzer = CurrencyAnalyzer()

        assert analyzer is not None

    def test_正常系_対象通貨ペアが正しく設定される(self) -> None:
        """対象の6通貨ペアが正しく設定されることを確認."""
        analyzer = CurrencyAnalyzer()

        expected_pairs = [
            "USDJPY=X",
            "EURJPY=X",
            "GBPJPY=X",
            "AUDJPY=X",
            "CADJPY=X",
            "CHFJPY=X",
        ]
        assert analyzer.target_pairs == expected_pairs


class TestGetCurrencyPairs:
    """symbols.yaml から通貨ペアを取得するテスト."""

    @patch("analyze.reporting.currency.get_symbols")
    def test_正常系_symbols_yamlから通貨ペアを取得できる(
        self,
        mock_get_symbols: MagicMock,
    ) -> None:
        """symbols.yamlのcurrencies.jpy_crossesから通貨ペアを取得できることを確認."""
        mock_get_symbols.return_value = [
            "USDJPY=X",
            "EURJPY=X",
            "GBPJPY=X",
            "AUDJPY=X",
            "CADJPY=X",
            "CHFJPY=X",
        ]

        analyzer = CurrencyAnalyzer()
        pairs = analyzer.get_currency_pairs()

        mock_get_symbols.assert_called_once_with("currencies", "jpy_crosses")
        assert len(pairs) == 6
        assert "USDJPY=X" in pairs


class TestFetchData:
    """データ取得のテスト."""

    @pytest.fixture
    def mock_yfinance_results(self) -> list[MagicMock]:
        """YFinanceFetcher.fetch の戻り値をモック."""
        results = []
        currency_data = {
            "USDJPY=X": [155.50, 155.75, 156.00],
            "EURJPY=X": [168.50, 168.75, 169.00],
            "GBPJPY=X": [198.00, 198.50, 199.00],
            "AUDJPY=X": [102.50, 102.75, 103.00],
            "CADJPY=X": [112.00, 112.25, 112.50],
            "CHFJPY=X": [178.00, 178.25, 178.50],
        }
        dates = pd.date_range("2026-01-25", periods=3, freq="D")

        for symbol, values in currency_data.items():
            mock_result = MagicMock()
            mock_result.symbol = symbol
            mock_result.data = DataFrame(
                {
                    "open": values,
                    "high": [v + 0.5 for v in values],
                    "low": [v - 0.5 for v in values],
                    "close": values,
                    "volume": [0] * 3,
                },
                index=dates,
            )
            mock_result.is_empty = False
            results.append(mock_result)

        return results

    @patch("analyze.reporting.currency.YFinanceFetcher")
    def test_正常系_6通貨ペアのデータを取得できる(
        self,
        mock_fetcher_class: MagicMock,
        mock_yfinance_results: list[MagicMock],
    ) -> None:
        """YFinanceFetcher を使用して6通貨ペアのデータを取得できることを確認."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_yfinance_results
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = CurrencyAnalyzer()
        data = analyzer.fetch_data()

        assert "USDJPY=X" in data
        assert "EURJPY=X" in data
        assert "GBPJPY=X" in data
        assert "AUDJPY=X" in data
        assert "CADJPY=X" in data
        assert "CHFJPY=X" in data
        assert len(data) == 6

    @patch("analyze.reporting.currency.YFinanceFetcher")
    def test_正常系_各通貨ペアがDataFrameとして返される(
        self,
        mock_fetcher_class: MagicMock,
        mock_yfinance_results: list[MagicMock],
    ) -> None:
        """各通貨ペアのデータがDataFrameとして返されることを確認."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_yfinance_results
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = CurrencyAnalyzer()
        data = analyzer.fetch_data()

        for _symbol, df in data.items():
            assert isinstance(df, DataFrame)
            assert "close" in df.columns


class TestCalculateReturns:
    """騰落率計算のテスト."""

    @pytest.fixture
    def sample_currency_data(self) -> dict[str, DataFrame]:
        """テスト用の為替データ."""
        # 30日分のデータを生成
        dates = pd.date_range("2025-12-27", periods=30, freq="D")
        base_rates = {
            "USDJPY=X": 150.0,
            "EURJPY=X": 165.0,
        }
        result = {}
        for symbol, base in base_rates.items():
            result[symbol] = DataFrame(
                {
                    "open": [base + i * 0.1 for i in range(30)],
                    "high": [base + i * 0.1 + 0.5 for i in range(30)],
                    "low": [base + i * 0.1 - 0.5 for i in range(30)],
                    "close": [base + i * 0.1 for i in range(30)],
                    "volume": [0] * 30,
                },
                index=dates,
            )
        return result

    def test_正常系_1日騰落率が正しく計算される(
        self,
        sample_currency_data: dict[str, DataFrame],
    ) -> None:
        """1日の騰落率が正しく計算されることを確認."""
        analyzer = CurrencyAnalyzer()

        returns = analyzer.calculate_returns(sample_currency_data, periods=["1D"])

        # USDJPY=X: 最新値 - 1日前 の騰落率
        # 最新値: 150.0 + 29*0.1 = 152.9
        # 1日前: 150.0 + 28*0.1 = 152.8
        # 騰落率: (152.9 - 152.8) / 152.8 * 100 ≈ 0.065%
        assert "USDJPY=X" in returns
        assert "1D" in returns["USDJPY=X"]
        return_1d = returns["USDJPY=X"]["1D"]
        assert return_1d is not None
        assert abs(return_1d - 0.065) < 0.01

    def test_正常系_1週間騰落率が正しく計算される(
        self,
        sample_currency_data: dict[str, DataFrame],
    ) -> None:
        """1週間の騰落率が正しく計算されることを確認."""
        analyzer = CurrencyAnalyzer()

        returns = analyzer.calculate_returns(sample_currency_data, periods=["1W"])

        # USDJPY=X: 1W = 5営業日分の騰落率
        # 最新値: 152.9
        # 5日前: 150.0 + 24*0.1 = 152.4
        # 騰落率: (152.9 - 152.4) / 152.4 * 100 ≈ 0.328%
        assert "USDJPY=X" in returns
        assert "1W" in returns["USDJPY=X"]
        return_1w = returns["USDJPY=X"]["1W"]
        assert return_1w is not None
        assert abs(return_1w - 0.328) < 0.01

    def test_正常系_複数期間を一度に計算できる(
        self,
        sample_currency_data: dict[str, DataFrame],
    ) -> None:
        """複数期間の騰落率を一度に計算できることを確認."""
        analyzer = CurrencyAnalyzer()

        returns = analyzer.calculate_returns(
            sample_currency_data, periods=["1D", "1W", "1M"]
        )

        assert "USDJPY=X" in returns
        assert all(p in returns["USDJPY=X"] for p in ["1D", "1W", "1M"])

    def test_エッジケース_データ不足時はNoneが返される(self) -> None:
        """データ不足時にNoneが返されることを確認."""
        analyzer = CurrencyAnalyzer()
        short_data = {
            "USDJPY=X": DataFrame(
                {
                    "open": [150.0, 150.1],
                    "high": [150.5, 150.6],
                    "low": [149.5, 149.6],
                    "close": [150.0, 150.1],
                    "volume": [0, 0],
                },
                index=pd.date_range("2026-01-25", periods=2, freq="D"),
            )
        }

        returns = analyzer.calculate_returns(short_data, periods=["1M"])

        assert returns["USDJPY=X"]["1M"] is None


class TestGetSummary:
    """サマリー取得のテスト."""

    @pytest.fixture
    def sample_full_data(self) -> dict[str, DataFrame]:
        """テスト用の完全なデータセット."""
        dates = pd.date_range("2025-12-27", periods=30, freq="D")
        currency_pairs = [
            ("USDJPY=X", 155.0),
            ("EURJPY=X", 168.0),
            ("GBPJPY=X", 198.0),
            ("AUDJPY=X", 102.0),
            ("CADJPY=X", 112.0),
            ("CHFJPY=X", 178.0),
        ]
        result = {}
        for symbol, base in currency_pairs:
            result[symbol] = DataFrame(
                {
                    "open": [base + i * 0.1 for i in range(30)],
                    "high": [base + i * 0.1 + 0.5 for i in range(30)],
                    "low": [base + i * 0.1 - 0.5 for i in range(30)],
                    "close": [base + i * 0.1 for i in range(30)],
                    "volume": [0] * 30,
                },
                index=dates,
            )
        return result

    @patch("analyze.reporting.currency.YFinanceFetcher")
    def test_正常系_サマリーに全情報が含まれる(
        self,
        mock_fetcher_class: MagicMock,
        sample_full_data: dict[str, DataFrame],
    ) -> None:
        """サマリーに全ての必要な情報が含まれることを確認."""
        # YFinanceFetcherをモック
        mock_results = []
        for symbol, df in sample_full_data.items():
            mock_result = MagicMock()
            mock_result.symbol = symbol
            mock_result.data = df
            mock_result.is_empty = False
            mock_results.append(mock_result)

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = CurrencyAnalyzer()
        summary = analyzer.get_summary()

        # 全通貨ペアの最新値
        assert "latest_rates" in summary
        latest_rates = summary["latest_rates"]
        assert isinstance(latest_rates, dict)
        assert all(
            s in latest_rates
            for s in [
                "USDJPY=X",
                "EURJPY=X",
                "GBPJPY=X",
                "AUDJPY=X",
                "CADJPY=X",
                "CHFJPY=X",
            ]
        )

        # 期間別騰落率
        assert "returns" in summary
        returns = summary["returns"]
        assert isinstance(returns, dict)
        usdjpy_returns = returns["USDJPY=X"]
        assert isinstance(usdjpy_returns, dict)
        assert all(p in usdjpy_returns for p in ["1D", "1W", "1M"])

        # データ取得日時
        assert "generated_at" in summary


class TestAPIErrorHandling:
    """APIエラー時の挙動テスト."""

    @patch("analyze.reporting.currency.YFinanceFetcher")
    def test_異常系_APIエラー時にDataFetchErrorがスローされる(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """API エラー発生時に DataFetchError がスローされることを確認."""
        from market.yfinance.errors import DataFetchError

        # モックの設定: fetchが例外をスロー
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = DataFetchError(
            message="API rate limit exceeded",
            symbol="USDJPY=X",
            source="yfinance",
        )
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = CurrencyAnalyzer()

        with pytest.raises(DataFetchError, match="API rate limit exceeded"):
            analyzer.fetch_data()

    @patch("analyze.reporting.currency.YFinanceFetcher")
    def test_異常系_一部通貨ペアの取得失敗時は空データとして処理される(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """一部通貨ペアの取得失敗時、その通貨は空データとして処理されることを確認."""
        # モックの設定: 一部の通貨ペアが空データを返す
        dates = pd.date_range("2026-01-25", periods=3, freq="D")

        def create_mock_result(symbol: str, is_empty: bool = False) -> MagicMock:
            mock_result = MagicMock()
            mock_result.symbol = symbol
            if is_empty:
                mock_result.data = DataFrame()
                mock_result.is_empty = True
            else:
                mock_result.data = DataFrame(
                    {
                        "open": [150.0, 150.1, 150.2],
                        "high": [150.5, 150.6, 150.7],
                        "low": [149.5, 149.6, 149.7],
                        "close": [150.0, 150.1, 150.2],
                        "volume": [0, 0, 0],
                    },
                    index=dates,
                )
                mock_result.is_empty = False
            return mock_result

        mock_results = [
            create_mock_result("USDJPY=X"),
            create_mock_result("EURJPY=X"),
            create_mock_result("GBPJPY=X", is_empty=True),  # この通貨ペアは取得失敗
            create_mock_result("AUDJPY=X"),
            create_mock_result("CADJPY=X"),
            create_mock_result("CHFJPY=X"),
        ]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = CurrencyAnalyzer()
        data = analyzer.fetch_data()

        # 空でない通貨ペアは5つ（GBPJPY=Xは空）
        assert len(data) == 5
        assert "GBPJPY=X" not in data


class TestEdgeCases:
    """エッジケースのテスト."""

    def test_エッジケース_空のデータで空の結果が返される(self) -> None:
        """空のデータで空の結果が返されることを確認."""
        analyzer = CurrencyAnalyzer()
        empty_data: dict[str, DataFrame] = {}

        returns = analyzer.calculate_returns(empty_data, periods=["1D"])

        assert returns == {}

    def test_エッジケース_NaN値を含むデータの処理(self) -> None:
        """NaN値を含むデータが適切に処理されることを確認."""
        analyzer = CurrencyAnalyzer()
        dates = pd.date_range("2026-01-20", periods=10, freq="D")
        close_values = [
            150.0,
            float("nan"),
            150.2,
            150.3,
            150.4,
            150.5,
            float("nan"),
            150.7,
            150.8,
            150.9,
        ]
        data_with_nan = {
            "USDJPY=X": DataFrame(
                {
                    "open": close_values,
                    "high": [
                        v + 0.5 if not pd.isna(v) else float("nan")
                        for v in close_values
                    ],
                    "low": [
                        v - 0.5 if not pd.isna(v) else float("nan")
                        for v in close_values
                    ],
                    "close": close_values,
                    "volume": [0] * 10,
                },
                index=dates,
            )
        }

        returns = analyzer.calculate_returns(data_with_nan, periods=["1D"])

        # NaNを含んでいても最新の有効な値から計算される
        assert "USDJPY=X" in returns
        # 結果がNoneでないことを確認（最新値と前日の有効値から計算）
        assert returns["USDJPY=X"]["1D"] is not None


class TestLogging:
    """ロギングのテスト."""

    @patch("analyze.reporting.currency.YFinanceFetcher")
    def test_正常系_ロギングが実装されている(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """適切なロギングが実装されていることを確認."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        analyzer = CurrencyAnalyzer()

        # loggerが存在することを確認
        assert hasattr(analyzer, "logger")
