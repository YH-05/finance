"""Unit tests for MarketData API."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market_analysis import MarketData
from market_analysis.errors import DataFetchError, ValidationError
from market_analysis.types import DataSource, MarketDataResult


class TestMarketDataInit:
    """Tests for MarketData initialization."""

    def test_init_default(self) -> None:
        """デフォルト初期化が成功する."""
        market_data = MarketData()
        assert market_data is not None

    def test_init_with_cache_path(self, tmp_path: Path) -> None:
        """キャッシュパス指定で初期化できる."""
        cache_path = str(tmp_path / "cache.db")
        market_data = MarketData(cache_path=cache_path)
        assert market_data is not None


class TestMarketDataFetchStock:
    """Tests for MarketData.fetch_stock method."""

    def test_fetch_stock_validates_empty_symbol(self) -> None:
        """空のシンボルでValidationErrorが発生."""
        market_data = MarketData()
        with pytest.raises(ValidationError, match="cannot be empty"):
            market_data.fetch_stock("")

    def test_fetch_stock_validates_whitespace_symbol(self) -> None:
        """空白のみのシンボルでValidationErrorが発生."""
        market_data = MarketData()
        with pytest.raises(ValidationError, match="cannot be empty"):
            market_data.fetch_stock("   ")

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_fetch_stock_returns_dataframe(self, mock_factory: MagicMock) -> None:
        """正常なシンボルでDataFrameが返される."""
        # Setup mock
        mock_df = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [105.0, 106.0],
                "low": [99.0, 100.0],
                "close": [104.0, 105.0],
                "volume": [1000000, 1100000],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )
        mock_result = MarketDataResult(
            symbol="AAPL",
            data=mock_df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=False,
        )
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [mock_result]
        mock_factory.create.return_value = mock_fetcher

        market_data = MarketData()
        result = market_data.fetch_stock("AAPL", start="2024-01-01", end="2024-01-31")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "close" in result.columns

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_fetch_stock_raises_on_empty_result(self, mock_factory: MagicMock) -> None:
        """空の結果でDataFetchErrorが発生."""
        mock_result = MarketDataResult(
            symbol="INVALID",
            data=pd.DataFrame(),
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=False,
        )
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [mock_result]
        mock_factory.create.return_value = mock_fetcher

        market_data = MarketData()
        with pytest.raises(DataFetchError, match="No data found"):
            market_data.fetch_stock("INVALID")


class TestMarketDataFetchForex:
    """Tests for MarketData.fetch_forex method."""

    def test_fetch_forex_validates_empty_pair(self) -> None:
        """空のペアでValidationErrorが発生."""
        market_data = MarketData()
        with pytest.raises(ValidationError, match="cannot be empty"):
            market_data.fetch_forex("")

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_fetch_forex_converts_pair_to_yfinance_format(
        self, mock_factory: MagicMock
    ) -> None:
        """通貨ペアがyfinance形式に変換される."""
        mock_df = pd.DataFrame(
            {"close": [150.0]}, index=pd.date_range("2024-01-01", periods=1)
        )
        mock_result = MarketDataResult(
            symbol="USDJPY=X",
            data=mock_df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=False,
        )
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [mock_result]
        mock_factory.create.return_value = mock_fetcher

        market_data = MarketData()
        market_data.fetch_forex("USDJPY")

        # Verify the factory was called with correct symbol
        call_args = mock_fetcher.fetch.call_args
        options = call_args[0][0]
        assert options.symbols == ["USDJPY=X"]


class TestMarketDataFetchFred:
    """Tests for MarketData.fetch_fred method."""

    def test_fetch_fred_validates_empty_series_id(self) -> None:
        """空のシリーズIDでValidationErrorが発生."""
        market_data = MarketData()
        with pytest.raises(ValidationError, match="cannot be empty"):
            market_data.fetch_fred("")

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_fetch_fred_returns_dataframe(self, mock_factory: MagicMock) -> None:
        """正常なシリーズIDでDataFrameが返される."""
        mock_df = pd.DataFrame(
            {"close": [4.5, 4.6]}, index=pd.date_range("2024-01-01", periods=2)
        )
        mock_result = MarketDataResult(
            symbol="DGS10",
            data=mock_df,
            source=DataSource.FRED,
            fetched_at=datetime.now(),
            from_cache=False,
        )
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [mock_result]
        mock_factory.create.return_value = mock_fetcher

        market_data = MarketData()
        result = market_data.fetch_fred("DGS10")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2


class TestMarketDataFetchCommodity:
    """Tests for MarketData.fetch_commodity method."""

    def test_fetch_commodity_validates_empty_symbol(self) -> None:
        """空のシンボルでValidationErrorが発生."""
        market_data = MarketData()
        with pytest.raises(ValidationError, match="cannot be empty"):
            market_data.fetch_commodity("")

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_fetch_commodity_preserves_futures_suffix(
        self, mock_factory: MagicMock
    ) -> None:
        """先物サフィックスが保持される."""
        mock_df = pd.DataFrame(
            {"close": [2000.0]}, index=pd.date_range("2024-01-01", periods=1)
        )
        mock_result = MarketDataResult(
            symbol="GC=F",
            data=mock_df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=False,
        )
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [mock_result]
        mock_factory.create.return_value = mock_fetcher

        market_data = MarketData()
        market_data.fetch_commodity("GC=F")

        call_args = mock_fetcher.fetch.call_args
        options = call_args[0][0]
        assert options.symbols == ["GC=F"]


class TestMarketDataToAgentJson:
    """Tests for MarketData.to_agent_json method."""

    def test_to_agent_json_returns_success(self) -> None:
        """正常なDataFrameでsuccessがTrueになる."""
        market_data = MarketData()
        df = pd.DataFrame(
            {"close": [100.0, 101.0, 102.0]},
            index=pd.date_range("2024-01-01", periods=3),
        )

        result = market_data.to_agent_json(df, symbol="AAPL")

        assert result["success"] is True
        assert result["data"] is not None
        assert len(result["data"]) == 3

    def test_to_agent_json_includes_metadata(self) -> None:
        """include_metadata=Trueでメタデータが含まれる."""
        market_data = MarketData()
        df = pd.DataFrame({"close": [100.0]})

        result = market_data.to_agent_json(df, symbol="AAPL", include_metadata=True)

        assert "metadata" in result
        assert result["metadata"]["record_count"] == 1
        assert "AAPL" in result["metadata"]["symbols"]

    def test_to_agent_json_excludes_metadata(self) -> None:
        """include_metadata=Falseでメタデータが除外される."""
        market_data = MarketData()
        df = pd.DataFrame({"close": [100.0]})

        result = market_data.to_agent_json(df, symbol="AAPL", include_metadata=False)

        assert "metadata" not in result


class TestMarketDataDateParsing:
    """Tests for date parsing functionality."""

    def test_parse_iso_date_string(self) -> None:
        """ISO形式の日付文字列がパースできる."""
        market_data = MarketData()
        result = market_data._parse_date("2024-01-15")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime_object(self) -> None:
        """datetimeオブジェクトがそのまま返される."""
        market_data = MarketData()
        dt = datetime(2024, 6, 15)
        result = market_data._parse_date(dt)

        assert result == dt

    def test_parse_none_with_default(self) -> None:
        """Noneでデフォルトオフセットが適用される."""
        market_data = MarketData()
        result = market_data._parse_date(None, default_offset_days=30)

        assert result is not None
        expected = datetime.now().date()
        assert (expected - result.date()).days <= 31

    def test_parse_invalid_date_raises_error(self) -> None:
        """不正な日付でValidationErrorが発生."""
        market_data = MarketData()
        with pytest.raises(ValidationError, match="Invalid date format"):
            market_data._parse_date("invalid-date")
