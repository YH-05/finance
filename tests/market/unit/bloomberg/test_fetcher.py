"""Unit tests for market.bloomberg.fetcher module.

TDD Red Phase: These tests are designed to fail initially.
The implementation (market.bloomberg.fetcher) does not exist yet.

Test TODO List:
- [x] BloombergFetcher: instantiation and basic properties
- [x] BloombergFetcher.get_historical_data(): historical data fetching
- [x] BloombergFetcher.get_reference_data(): reference data fetching
- [x] BloombergFetcher.get_financial_data(): financial data fetching
- [x] BloombergFetcher.get_news(): news fetching
- [x] BloombergFetcher.convert_identifiers(): identifier conversion
- [x] Validation errors for invalid inputs
- [x] Connection error handling
"""

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from market.bloomberg.fetcher import BloombergFetcher


class TestBloombergFetcherInstantiation:
    """Tests for BloombergFetcher instantiation."""

    def test_正常系_デフォルト設定でインスタンス化(self) -> None:
        """BloombergFetcher がデフォルト設定で初期化されることを確認。"""
        from market.bloomberg.fetcher import BloombergFetcher

        fetcher = BloombergFetcher()

        assert fetcher.host == "localhost"
        assert fetcher.port == 8194

    def test_正常系_カスタム設定でインスタンス化(self) -> None:
        """BloombergFetcher がカスタム設定で初期化されることを確認。"""
        from market.bloomberg.fetcher import BloombergFetcher

        fetcher = BloombergFetcher(host="192.168.1.100", port=8195)

        assert fetcher.host == "192.168.1.100"
        assert fetcher.port == 8195


class TestBloombergFetcherProperties:
    """Tests for BloombergFetcher properties."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    def test_正常系_source_propertyがBLOOMBERGを返す(
        self, fetcher: "BloombergFetcher"
    ) -> None:
        """source property が DataSource.BLOOMBERG を返すことを確認。"""
        from market.bloomberg.types import DataSource

        assert fetcher.source == DataSource.BLOOMBERG

    def test_正常系_ref_data_serviceが正しい(self, fetcher: "BloombergFetcher") -> None:
        """REF_DATA_SERVICE が正しいことを確認。"""
        assert fetcher.REF_DATA_SERVICE == "//blp/refdata"

    def test_正常系_news_serviceが正しい(self, fetcher: "BloombergFetcher") -> None:
        """NEWS_SERVICE が正しいことを確認。"""
        assert fetcher.NEWS_SERVICE == "//blp/news"


class TestBloombergFetcherValidation:
    """Tests for BloombergFetcher input validation."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    def test_異常系_空のsecuritiesリストでValidationError(
        self, fetcher: "BloombergFetcher"
    ) -> None:
        """空の securities リストで BloombergValidationError が発生することを確認。"""
        from market.bloomberg.types import BloombergFetchOptions
        from market.errors import BloombergValidationError

        options = BloombergFetchOptions(
            securities=[],
            fields=["PX_LAST"],
        )

        with pytest.raises(BloombergValidationError):
            fetcher.get_historical_data(options)

    def test_異常系_空のfieldsリストでValidationError(
        self, fetcher: "BloombergFetcher"
    ) -> None:
        """空の fields リストで BloombergValidationError が発生することを確認。"""
        from market.bloomberg.types import BloombergFetchOptions
        from market.errors import BloombergValidationError

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=[],
        )

        with pytest.raises(BloombergValidationError):
            fetcher.get_historical_data(options)

    def test_異常系_無効な日付範囲でValidationError(
        self, fetcher: "BloombergFetcher"
    ) -> None:
        """開始日が終了日より後の場合 BloombergValidationError が発生することを確認。"""
        from market.bloomberg.types import BloombergFetchOptions
        from market.errors import BloombergValidationError

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=["PX_LAST"],
            start_date="2024-12-31",
            end_date="2024-01-01",  # 開始日より前
        )

        with pytest.raises(BloombergValidationError, match="date range"):
            fetcher.get_historical_data(options)


class TestBloombergFetcherGetHistoricalData:
    """Tests for BloombergFetcher.get_historical_data() method."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create a sample historical data DataFrame."""
        return pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
                "PX_LAST": [150.0, 151.0, 152.0],
                "PX_VOLUME": [1000000, 1100000, 1200000],
            }
        )

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_ヒストリカルデータ取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
        sample_df: pd.DataFrame,
    ) -> None:
        """ヒストリカルデータが取得できることを確認。"""
        from market.bloomberg.types import BloombergFetchOptions, DataSource

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        # Mock the response processing (internal implementation detail)
        # This would be handled by the actual implementation
        fetcher._process_historical_response = MagicMock(return_value=sample_df)

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=["PX_LAST", "PX_VOLUME"],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        results = fetcher.get_historical_data(options)

        assert len(results) == 1
        assert results[0].security == "AAPL US Equity"
        assert results[0].source == DataSource.BLOOMBERG
        assert len(results[0].data) == 3

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_複数セキュリティのデータ取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
        sample_df: pd.DataFrame,
    ) -> None:
        """複数セキュリティのデータが取得できることを確認。"""
        from market.bloomberg.types import BloombergFetchOptions

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        fetcher._process_historical_response = MagicMock(return_value=sample_df)

        options = BloombergFetchOptions(
            securities=["AAPL US Equity", "GOOGL US Equity", "MSFT US Equity"],
            fields=["PX_LAST"],
        )

        results = fetcher.get_historical_data(options)

        assert len(results) == 3
        assert [r.security for r in results] == [
            "AAPL US Equity",
            "GOOGL US Equity",
            "MSFT US Equity",
        ]

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_オーバーライド付きデータ取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
        sample_df: pd.DataFrame,
    ) -> None:
        """オーバーライド付きでデータが取得できることを確認。"""
        from market.bloomberg.types import (
            BloombergFetchOptions,
            OverrideOption,
        )

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        fetcher._process_historical_response = MagicMock(return_value=sample_df)

        options = BloombergFetchOptions(
            securities=["7203 JP Equity"],
            fields=["PX_LAST"],
            overrides=[OverrideOption(field="CRNCY", value="USD")],
        )

        results = fetcher.get_historical_data(options)

        assert len(results) == 1


class TestBloombergFetcherGetReferenceData:
    """Tests for BloombergFetcher.get_reference_data() method."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_参照データ取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """参照データが取得できることを確認。"""
        from market.bloomberg.types import BloombergFetchOptions

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        sample_data = pd.DataFrame(
            {
                "security": ["AAPL US Equity"],
                "NAME": ["Apple Inc"],
                "GICS_SECTOR_NAME": ["Information Technology"],
            }
        )
        fetcher._process_reference_response = MagicMock(return_value=sample_data)

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=["NAME", "GICS_SECTOR_NAME"],
        )

        results = fetcher.get_reference_data(options)

        assert len(results) == 1
        assert results[0].security == "AAPL US Equity"


class TestBloombergFetcherGetFinancialData:
    """Tests for BloombergFetcher.get_financial_data() method."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_財務データ取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """財務データが取得できることを確認。"""
        from market.bloomberg.types import BloombergFetchOptions, OverrideOption

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        sample_data = pd.DataFrame(
            {
                "security": ["AAPL US Equity"],
                "IS_EPS": [6.5],
                "SALES_REV_TURN": [394328000000],
            }
        )
        fetcher._process_reference_response = MagicMock(return_value=sample_data)

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=["IS_EPS", "SALES_REV_TURN"],
            overrides=[
                OverrideOption(field="BEST_FPERIOD_OVERRIDE", value="1GQ"),
            ],
        )

        results = fetcher.get_financial_data(options)

        assert len(results) == 1


class TestBloombergFetcherConvertIdentifiers:
    """Tests for BloombergFetcher.convert_identifiers() method."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_ISINからTickerへ変換(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """ISIN から Ticker への変換ができることを確認。"""
        from market.bloomberg.types import IDType

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        fetcher._process_id_conversion = MagicMock(
            return_value={"US0378331005": "AAPL US Equity"}
        )

        result = fetcher.convert_identifiers(
            identifiers=["US0378331005"],
            from_type=IDType.ISIN,
            to_type=IDType.TICKER,
        )

        assert result["US0378331005"] == "AAPL US Equity"

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_複数識別子の変換(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """複数識別子の変換ができることを確認。"""
        from market.bloomberg.types import IDType

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        fetcher._process_id_conversion = MagicMock(
            return_value={
                "US0378331005": "AAPL US Equity",
                "US02079K3059": "GOOGL US Equity",
            }
        )

        result = fetcher.convert_identifiers(
            identifiers=["US0378331005", "US02079K3059"],
            from_type=IDType.ISIN,
            to_type=IDType.TICKER,
        )

        assert len(result) == 2
        assert result["US0378331005"] == "AAPL US Equity"
        assert result["US02079K3059"] == "GOOGL US Equity"


class TestBloombergFetcherGetNews:
    """Tests for BloombergFetcher news-related methods."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_セキュリティ別ニュース取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """セキュリティ別のニュースが取得できることを確認。"""
        from market.bloomberg.types import NewsStory

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        sample_stories = [
            NewsStory(
                story_id="BBG123",
                headline="Apple Reports Q4 Earnings",
                datetime=datetime(2024, 1, 15, 9, 30),
            ),
        ]
        fetcher._process_news_response = MagicMock(return_value=sample_stories)

        results = fetcher.get_historical_news_by_security(
            security="AAPL US Equity",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert len(results) == 1
        assert results[0].story_id == "BBG123"

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_ニュース本文取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """ニュース本文が取得できることを確認。"""
        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        fetcher._fetch_story_content = MagicMock(
            return_value="Apple Inc. reported quarterly earnings..."
        )

        result = fetcher.get_news_story_content(story_id="BBG123456789")

        assert "Apple Inc." in result


class TestBloombergFetcherConnectionErrors:
    """Tests for BloombergFetcher connection error handling."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @patch("market.bloomberg.fetcher.blpapi")
    def test_異常系_接続失敗でConnectionError(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """Bloomberg Terminal への接続失敗時に BloombergConnectionError が発生することを確認。"""
        from market.bloomberg.types import BloombergFetchOptions
        from market.errors import BloombergConnectionError

        # Mock setup - connection fails
        mock_session = MagicMock()
        mock_session.start.return_value = False
        mock_blpapi.Session.return_value = mock_session

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=["PX_LAST"],
        )

        with pytest.raises(BloombergConnectionError):
            fetcher.get_historical_data(options)

    @patch("market.bloomberg.fetcher.blpapi")
    def test_異常系_サービス開始失敗でSessionError(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """サービス開始失敗時に BloombergSessionError が発生することを確認。"""
        from market.bloomberg.types import BloombergFetchOptions
        from market.errors import BloombergSessionError

        # Mock setup - session starts but service fails
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = False
        mock_blpapi.Session.return_value = mock_session

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=["PX_LAST"],
        )

        with pytest.raises(BloombergSessionError):
            fetcher.get_historical_data(options)


class TestBloombergFetcherDataErrors:
    """Tests for BloombergFetcher data error handling."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @patch("market.bloomberg.fetcher.blpapi")
    def test_エッジケース_データなしで空結果(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """データが存在しない場合、空の結果を返すことを確認。"""
        from market.bloomberg.types import BloombergFetchOptions

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        fetcher._process_historical_response = MagicMock(return_value=pd.DataFrame())

        options = BloombergFetchOptions(
            securities=["AAPL US Equity"],
            fields=["PX_LAST"],
            start_date="1900-01-01",
            end_date="1900-12-31",
        )

        results = fetcher.get_historical_data(options)

        assert len(results) == 1
        assert results[0].is_empty

    @patch("market.bloomberg.fetcher.blpapi")
    def test_異常系_無効なセキュリティでDataError(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """無効なセキュリティで BloombergDataError が発生することを確認。"""
        from market.bloomberg.types import BloombergFetchOptions
        from market.errors import BloombergDataError

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        # Simulate Bloomberg returning an error for invalid security
        fetcher._process_historical_response = MagicMock(
            side_effect=BloombergDataError(
                "Invalid security",
                security="INVALID_TICKER Equity",
            )
        )

        options = BloombergFetchOptions(
            securities=["INVALID_TICKER Equity"],
            fields=["PX_LAST"],
        )

        with pytest.raises(BloombergDataError):
            fetcher.get_historical_data(options)


class TestBloombergFetcherIndexMembers:
    """Tests for BloombergFetcher.get_index_members() method."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_S_P500構成銘柄取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """S&P 500 の構成銘柄が取得できることを確認。"""
        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        sample_members = ["AAPL US Equity", "MSFT US Equity", "GOOGL US Equity"]
        fetcher._process_index_members = MagicMock(return_value=sample_members)

        results = fetcher.get_index_members(index="SPX Index")

        assert len(results) >= 3
        assert "AAPL US Equity" in results


class TestBloombergFetcherFieldInfo:
    """Tests for BloombergFetcher.get_field_info() method."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @patch("market.bloomberg.fetcher.blpapi")
    def test_正常系_フィールド情報取得(
        self,
        mock_blpapi: MagicMock,
        fetcher: "BloombergFetcher",
    ) -> None:
        """フィールド情報が取得できることを確認。"""
        from market.bloomberg.types import FieldInfo

        # Mock setup
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_blpapi.Session.return_value = mock_session

        sample_info = FieldInfo(
            field_id="PX_LAST",
            field_name="Last Price",
            description="The last traded price",
            data_type="Double",
        )
        fetcher._process_field_info = MagicMock(return_value=sample_info)

        result = fetcher.get_field_info(field_id="PX_LAST")

        assert result.field_id == "PX_LAST"
        assert result.field_name == "Last Price"


class TestBloombergFetcherDatabaseOperations:
    """Tests for BloombergFetcher database operations."""

    @pytest.fixture
    def fetcher(self) -> "BloombergFetcher":
        """Create a BloombergFetcher instance."""
        from market.bloomberg.fetcher import BloombergFetcher

        return BloombergFetcher()

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create a sample DataFrame."""
        return pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "PX_LAST": [150.0, 151.0],
            }
        )

    def test_正常系_SQLiteへデータ保存(
        self,
        fetcher: "BloombergFetcher",
        sample_df: pd.DataFrame,
        tmp_path: "Path",
    ) -> None:
        """データが SQLite に保存できることを確認。"""
        db_path = tmp_path / "test.db"

        fetcher.store_to_database(
            data=sample_df,
            db_path=str(db_path),
            table_name="historical_prices",
        )

        assert db_path.exists()

    def test_正常系_DB最新日付取得(
        self,
        fetcher: "BloombergFetcher",
        sample_df: pd.DataFrame,
        tmp_path: "Path",
    ) -> None:
        """DB から最新日付が取得できることを確認。"""
        import sqlite3

        db_path = tmp_path / "test.db"

        # Create table and insert data
        with sqlite3.connect(str(db_path)) as conn:
            sample_df.to_sql("historical_prices", conn, index=False)

        latest_date = fetcher.get_latest_date_from_db(
            db_path=str(db_path),
            table_name="historical_prices",
            date_column="date",
        )

        assert latest_date is not None
