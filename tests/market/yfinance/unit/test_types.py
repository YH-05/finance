"""Unit tests for market.yfinance.types module."""

from datetime import datetime

import pandas as pd
import pytest


class TestDataSource:
    """Tests for DataSource enum."""

    def test_正常系_YFINANCEの値がyfinance(self) -> None:
        """DataSource.YFINANCE の値が 'yfinance' であることを確認。"""
        from market.yfinance.types import DataSource

        assert DataSource.YFINANCE.value == "yfinance"

    def test_正常系_str型を継承(self) -> None:
        """DataSource が str を継承していることを確認。"""
        from market.yfinance.types import DataSource

        assert isinstance(DataSource.YFINANCE, str)


class TestInterval:
    """Tests for Interval enum."""

    @pytest.mark.parametrize(
        "interval_name,expected_value",
        [
            ("DAILY", "1d"),
            ("WEEKLY", "1wk"),
            ("MONTHLY", "1mo"),
            ("HOURLY", "1h"),
        ],
    )
    def test_正常系_インターバル値が正しい(
        self, interval_name: str, expected_value: str
    ) -> None:
        """各 Interval の値が yfinance 形式であることを確認。"""
        from market.yfinance.types import Interval

        interval = getattr(Interval, interval_name)
        assert interval.value == expected_value


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_正常系_デフォルト値で初期化(self) -> None:
        """RetryConfig がデフォルト値で初期化されることを確認。"""
        from market.yfinance.types import RetryConfig

        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_正常系_カスタム値で初期化(self) -> None:
        """RetryConfig がカスタム値で初期化されることを確認。"""
        from market.yfinance.types import RetryConfig

        config = RetryConfig(max_attempts=5, initial_delay=0.5)
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5


class TestCacheConfig:
    """Tests for CacheConfig dataclass."""

    def test_正常系_デフォルト値で初期化(self) -> None:
        """CacheConfig がデフォルト値で初期化されることを確認。"""
        from market.yfinance.types import CacheConfig

        config = CacheConfig()
        assert config.enabled is True
        assert config.ttl_seconds == 3600
        assert config.max_entries == 1000
        assert config.db_path is None


class TestFetchOptions:
    """Tests for FetchOptions dataclass."""

    def test_正常系_必須パラメータのみで初期化(self) -> None:
        """FetchOptions が必須パラメータのみで初期化されることを確認。"""
        from market.yfinance.types import DataSource, FetchOptions, Interval

        options = FetchOptions(symbols=["AAPL"])
        assert options.symbols == ["AAPL"]
        assert options.start_date is None
        assert options.end_date is None
        assert options.interval == Interval.DAILY
        assert options.source == DataSource.YFINANCE
        assert options.use_cache is True

    def test_正常系_全パラメータで初期化(self) -> None:
        """FetchOptions が全パラメータで初期化されることを確認。"""
        from market.yfinance.types import FetchOptions, Interval

        options = FetchOptions(
            symbols=["AAPL", "GOOGL"],
            start_date="2024-01-01",
            end_date="2024-12-31",
            interval=Interval.WEEKLY,
            use_cache=False,
        )
        assert options.symbols == ["AAPL", "GOOGL"]
        assert options.start_date == "2024-01-01"
        assert options.end_date == "2024-12-31"
        assert options.interval == Interval.WEEKLY
        assert options.use_cache is False


class TestMarketDataResult:
    """Tests for MarketDataResult dataclass."""

    def test_正常系_初期化と基本プロパティ(self) -> None:
        """MarketDataResult が正しく初期化されることを確認。"""
        from market.yfinance.types import DataSource, MarketDataResult

        df = pd.DataFrame(
            {
                "open": [150.0],
                "high": [155.0],
                "low": [149.0],
                "close": [154.0],
                "volume": [1000000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )

        result = MarketDataResult(
            symbol="AAPL",
            data=df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=False,
        )

        assert result.symbol == "AAPL"
        assert result.source == DataSource.YFINANCE
        assert result.from_cache is False
        assert result.row_count == 1

    def test_正常系_is_emptyプロパティ_空データ(self) -> None:
        """空の DataFrame の場合 is_empty が True を返すことを確認。"""
        from market.yfinance.types import DataSource, MarketDataResult

        result = MarketDataResult(
            symbol="AAPL",
            data=pd.DataFrame(),
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
        )

        assert result.is_empty is True

    def test_正常系_is_emptyプロパティ_データあり(self) -> None:
        """データがある場合 is_empty が False を返すことを確認。"""
        from market.yfinance.types import DataSource, MarketDataResult

        df = pd.DataFrame({"close": [100.0]})

        result = MarketDataResult(
            symbol="AAPL",
            data=df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
        )

        assert result.is_empty is False
