"""Unit tests for market.schema module.

TDD Red Phase: These tests are designed to fail initially.
The implementation (market.schema) does not exist yet.

Test TODO List:
## Metadata Schemas
- [ ] StockDataMetadata: symbol, source, fetched_at, from_cache, record_count, date_range
- [ ] EconomicDataMetadata: series_id, source, fetched_at, from_cache, record_count

## Config Schemas
- [ ] DataSourceConfig: api_key, base_url, timeout
- [ ] CacheConfig: enabled, ttl_seconds, max_size_mb
- [ ] ExportConfig: default_format, output_dir, compression
- [ ] MarketConfig: data_sources, cache, export

## Validation Functions
- [ ] validate_stock_metadata: validate stock data metadata
- [ ] validate_economic_metadata: validate economic data metadata
- [ ] validate_config: validate market config
"""

from datetime import datetime

import pytest

# =============================================================================
# StockDataMetadata Tests
# =============================================================================


class TestStockDataMetadata:
    """Tests for StockDataMetadata Pydantic model.

    StockDataMetadata represents metadata for stock price data.
    Required fields: symbol, source, fetched_at
    Optional fields: from_cache, record_count, date_range
    """

    def test_正常系_必須フィールドのみで作成される(self) -> None:
        """必須フィールドのみで StockDataMetadata が作成されることを確認。"""
        from market.schema import StockDataMetadata

        metadata = StockDataMetadata(
            symbol="AAPL",
            source="yfinance",
            fetched_at=datetime(2026, 1, 25, 10, 0, 0),
        )

        assert metadata.symbol == "AAPL"
        assert metadata.source == "yfinance"
        assert metadata.fetched_at == datetime(2026, 1, 25, 10, 0, 0)

    def test_正常系_全フィールドで作成される(self) -> None:
        """全フィールドで StockDataMetadata が作成されることを確認。"""
        from market.schema import DateRange, StockDataMetadata

        metadata = StockDataMetadata(
            symbol="AAPL",
            source="yfinance",
            fetched_at=datetime(2026, 1, 25, 10, 0, 0),
            from_cache=False,
            record_count=252,
            date_range=DateRange(start="2025-01-25", end="2026-01-25"),
        )

        assert metadata.symbol == "AAPL"
        assert metadata.source == "yfinance"
        assert metadata.from_cache is False
        assert metadata.record_count == 252
        assert metadata.date_range is not None
        assert metadata.date_range.start == "2025-01-25"
        assert metadata.date_range.end == "2026-01-25"

    def test_正常系_デフォルト値が設定される(self) -> None:
        """オプションフィールドにデフォルト値が設定されることを確認。"""
        from market.schema import StockDataMetadata

        metadata = StockDataMetadata(
            symbol="AAPL",
            source="yfinance",
            fetched_at=datetime(2026, 1, 25, 10, 0, 0),
        )

        assert metadata.from_cache is False
        assert metadata.record_count is None
        assert metadata.date_range is None

    def test_異常系_symbolがない場合ValidationError(self) -> None:
        """symbol がない場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import StockDataMetadata

        with pytest.raises(ValidationError) as exc_info:
            StockDataMetadata(
                source="yfinance",
                fetched_at=datetime(2026, 1, 25, 10, 0, 0),
            )  # type: ignore[call-arg]

        assert "symbol" in str(exc_info.value)

    def test_異常系_sourceがない場合ValidationError(self) -> None:
        """source がない場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import StockDataMetadata

        with pytest.raises(ValidationError) as exc_info:
            StockDataMetadata(
                symbol="AAPL",
                fetched_at=datetime(2026, 1, 25, 10, 0, 0),
            )  # type: ignore[call-arg]

        assert "source" in str(exc_info.value)

    def test_異常系_fetched_atがない場合ValidationError(self) -> None:
        """fetched_at がない場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import StockDataMetadata

        with pytest.raises(ValidationError) as exc_info:
            StockDataMetadata(
                symbol="AAPL",
                source="yfinance",
            )  # type: ignore[call-arg]

        assert "fetched_at" in str(exc_info.value)

    def test_異常系_symbolが不正な型の場合ValidationError(self) -> None:
        """symbol が不正な型の場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import StockDataMetadata

        with pytest.raises(ValidationError):
            StockDataMetadata(
                symbol=123,  # type: ignore[arg-type]
                source="yfinance",
                fetched_at=datetime(2026, 1, 25, 10, 0, 0),
            )

    def test_異常系_record_countが負の値の場合ValidationError(self) -> None:
        """record_count が負の値の場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import StockDataMetadata

        with pytest.raises(ValidationError) as exc_info:
            StockDataMetadata(
                symbol="AAPL",
                source="yfinance",
                fetched_at=datetime(2026, 1, 25, 10, 0, 0),
                record_count=-1,
            )

        assert "record_count" in str(exc_info.value)

    def test_正常系_ISO形式の文字列でfetched_atを設定(self) -> None:
        """ISO形式の文字列で fetched_at を設定できることを確認。"""
        from market.schema import StockDataMetadata

        metadata = StockDataMetadata(
            symbol="AAPL",
            source="yfinance",
            fetched_at="2026-01-25T10:00:00Z",  # type: ignore[arg-type]
        )

        assert isinstance(metadata.fetched_at, datetime)

    def test_正常系_to_dictでJSON互換の辞書に変換(self) -> None:
        """to_dict メソッドで JSON 互換の辞書に変換できることを確認。"""
        from market.schema import StockDataMetadata

        metadata = StockDataMetadata(
            symbol="AAPL",
            source="yfinance",
            fetched_at=datetime(2026, 1, 25, 10, 0, 0),
            from_cache=False,
            record_count=252,
        )

        data = metadata.model_dump()
        assert data["symbol"] == "AAPL"
        assert data["source"] == "yfinance"
        assert data["from_cache"] is False
        assert data["record_count"] == 252


# =============================================================================
# DateRange Tests
# =============================================================================


class TestDateRange:
    """Tests for DateRange Pydantic model.

    DateRange represents a date range for data queries.
    """

    def test_正常系_文字列日付で作成される(self) -> None:
        """文字列日付で DateRange が作成されることを確認。"""
        from market.schema import DateRange

        date_range = DateRange(start="2025-01-25", end="2026-01-25")

        assert date_range.start == "2025-01-25"
        assert date_range.end == "2026-01-25"

    def test_異常系_startがない場合ValidationError(self) -> None:
        """start がない場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import DateRange

        with pytest.raises(ValidationError):
            DateRange(end="2026-01-25")  # type: ignore[call-arg]

    def test_異常系_endがない場合ValidationError(self) -> None:
        """end がない場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import DateRange

        with pytest.raises(ValidationError):
            DateRange(start="2025-01-25")  # type: ignore[call-arg]


# =============================================================================
# EconomicDataMetadata Tests
# =============================================================================


class TestEconomicDataMetadata:
    """Tests for EconomicDataMetadata Pydantic model.

    EconomicDataMetadata represents metadata for economic indicator data (e.g., FRED).
    Required fields: series_id, source, fetched_at
    Optional fields: from_cache, record_count, title, units, frequency
    """

    def test_正常系_必須フィールドのみで作成される(self) -> None:
        """必須フィールドのみで EconomicDataMetadata が作成されることを確認。"""
        from market.schema import EconomicDataMetadata

        metadata = EconomicDataMetadata(
            series_id="GDP",
            source="fred",
            fetched_at=datetime(2026, 1, 25, 10, 0, 0),
        )

        assert metadata.series_id == "GDP"
        assert metadata.source == "fred"
        assert metadata.fetched_at == datetime(2026, 1, 25, 10, 0, 0)

    def test_正常系_全フィールドで作成される(self) -> None:
        """全フィールドで EconomicDataMetadata が作成されることを確認。"""
        from market.schema import EconomicDataMetadata

        metadata = EconomicDataMetadata(
            series_id="GDP",
            source="fred",
            fetched_at=datetime(2026, 1, 25, 10, 0, 0),
            from_cache=True,
            record_count=100,
            title="Gross Domestic Product",
            units="Billions of Dollars",
            frequency="Quarterly",
        )

        assert metadata.series_id == "GDP"
        assert metadata.title == "Gross Domestic Product"
        assert metadata.units == "Billions of Dollars"
        assert metadata.frequency == "Quarterly"

    def test_正常系_デフォルト値が設定される(self) -> None:
        """オプションフィールドにデフォルト値が設定されることを確認。"""
        from market.schema import EconomicDataMetadata

        metadata = EconomicDataMetadata(
            series_id="GDP",
            source="fred",
            fetched_at=datetime(2026, 1, 25, 10, 0, 0),
        )

        assert metadata.from_cache is False
        assert metadata.record_count is None
        assert metadata.title is None
        assert metadata.units is None
        assert metadata.frequency is None

    def test_異常系_series_idがない場合ValidationError(self) -> None:
        """series_id がない場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import EconomicDataMetadata

        with pytest.raises(ValidationError) as exc_info:
            EconomicDataMetadata(
                source="fred",
                fetched_at=datetime(2026, 1, 25, 10, 0, 0),
            )  # type: ignore[call-arg]

        assert "series_id" in str(exc_info.value)


# =============================================================================
# DataSourceConfig Tests
# =============================================================================


class TestDataSourceConfig:
    """Tests for DataSourceConfig Pydantic model.

    DataSourceConfig represents configuration for a data source.
    Optional fields: api_key, base_url, timeout, rate_limit
    """

    def test_正常系_空のConfigが作成される(self) -> None:
        """オプションのみなので空の DataSourceConfig が作成できることを確認。"""
        from market.schema import DataSourceConfig

        config = DataSourceConfig()

        assert config.api_key is None
        assert config.timeout == 30  # デフォルト値
        assert config.rate_limit is None

    def test_正常系_全フィールドで作成される(self) -> None:
        """全フィールドで DataSourceConfig が作成されることを確認。"""
        from market.schema import DataSourceConfig

        config = DataSourceConfig(
            api_key="test_api_key",
            base_url="https://api.example.com",
            timeout=60,
            rate_limit=100,
        )

        assert config.api_key == "test_api_key"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 60
        assert config.rate_limit == 100

    def test_正常系_timeoutのデフォルト値が30(self) -> None:
        """timeout のデフォルト値が 30 であることを確認。"""
        from market.schema import DataSourceConfig

        config = DataSourceConfig()

        assert config.timeout == 30

    def test_異常系_timeoutが負の値の場合ValidationError(self) -> None:
        """timeout が負の値の場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import DataSourceConfig

        with pytest.raises(ValidationError) as exc_info:
            DataSourceConfig(timeout=-1)

        assert "timeout" in str(exc_info.value)

    def test_異常系_rate_limitが負の値の場合ValidationError(self) -> None:
        """rate_limit が負の値の場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import DataSourceConfig

        with pytest.raises(ValidationError) as exc_info:
            DataSourceConfig(rate_limit=-1)

        assert "rate_limit" in str(exc_info.value)


# =============================================================================
# CacheConfig Tests
# =============================================================================


class TestCacheConfig:
    """Tests for CacheConfig Pydantic model.

    CacheConfig represents cache configuration.
    Optional fields: enabled, ttl_seconds, max_size_mb
    """

    def test_正常系_デフォルト値で作成される(self) -> None:
        """デフォルト値で CacheConfig が作成されることを確認。"""
        from market.schema import CacheConfig

        config = CacheConfig()

        assert config.enabled is True  # デフォルトで有効
        assert config.ttl_seconds == 3600  # デフォルト1時間
        assert config.max_size_mb == 100  # デフォルト100MB

    def test_正常系_全フィールドで作成される(self) -> None:
        """全フィールドで CacheConfig が作成されることを確認。"""
        from market.schema import CacheConfig

        config = CacheConfig(
            enabled=False,
            ttl_seconds=7200,
            max_size_mb=500,
        )

        assert config.enabled is False
        assert config.ttl_seconds == 7200
        assert config.max_size_mb == 500

    def test_異常系_ttl_secondsが負の値の場合ValidationError(self) -> None:
        """ttl_seconds が負の値の場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import CacheConfig

        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(ttl_seconds=-1)

        assert "ttl_seconds" in str(exc_info.value)

    def test_異常系_max_size_mbが負の値の場合ValidationError(self) -> None:
        """max_size_mb が負の値の場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import CacheConfig

        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(max_size_mb=-1)

        assert "max_size_mb" in str(exc_info.value)


# =============================================================================
# ExportConfig Tests
# =============================================================================


class TestExportConfig:
    """Tests for ExportConfig Pydantic model.

    ExportConfig represents export configuration.
    Optional fields: default_format, output_dir, compression
    """

    def test_正常系_デフォルト値で作成される(self) -> None:
        """デフォルト値で ExportConfig が作成されることを確認。"""
        from market.schema import ExportConfig

        config = ExportConfig()

        assert config.default_format == "parquet"  # デフォルト
        assert config.output_dir == "data/exports"  # デフォルト
        assert config.compression is None

    def test_正常系_全フィールドで作成される(self) -> None:
        """全フィールドで ExportConfig が作成されることを確認。"""
        from market.schema import ExportConfig

        config = ExportConfig(
            default_format="csv",
            output_dir="/custom/path",
            compression="gzip",
        )

        assert config.default_format == "csv"
        assert config.output_dir == "/custom/path"
        assert config.compression == "gzip"

    @pytest.mark.parametrize(
        "format_value",
        ["parquet", "csv", "json"],
    )
    def test_パラメトライズ_有効なフォーマットで作成できる(
        self, format_value: str
    ) -> None:
        """有効なフォーマットで ExportConfig が作成できることを確認。"""
        from market.schema import ExportConfig

        # Use a type narrowing approach for test
        config = ExportConfig(
            default_format=format_value  # type: ignore[arg-type]
        )

        assert config.default_format == format_value

    def test_異常系_不正なフォーマットでValidationError(self) -> None:
        """不正なフォーマットの場合 ValidationError が発生することを確認。"""
        from pydantic import ValidationError

        from market.schema import ExportConfig

        with pytest.raises(ValidationError) as exc_info:
            ExportConfig(default_format="invalid_format")  # type: ignore[arg-type]

        assert "default_format" in str(exc_info.value)


# =============================================================================
# MarketConfig Tests
# =============================================================================


class TestMarketConfig:
    """Tests for MarketConfig Pydantic model.

    MarketConfig represents the complete market data configuration.
    Optional fields: data_sources, cache, export
    """

    def test_正常系_デフォルト値で作成される(self) -> None:
        """デフォルト値で MarketConfig が作成されることを確認。"""
        from market.schema import MarketConfig

        config = MarketConfig()

        assert config.data_sources == {}
        assert config.cache is not None
        assert config.export is not None

    def test_正常系_全フィールドで作成される(self) -> None:
        """全フィールドで MarketConfig が作成されることを確認。"""
        from market.schema import (
            CacheConfig,
            DataSourceConfig,
            ExportConfig,
            MarketConfig,
        )

        config = MarketConfig(
            data_sources={
                "yfinance": DataSourceConfig(timeout=30),
                "fred": DataSourceConfig(api_key="xxx", timeout=30),
            },
            cache=CacheConfig(
                enabled=True,
                ttl_seconds=3600,
                max_size_mb=100,
            ),
            export=ExportConfig(
                default_format="parquet",
                output_dir="data/exports",
            ),
        )

        assert "yfinance" in config.data_sources
        assert "fred" in config.data_sources
        assert config.data_sources["fred"].api_key == "xxx"
        assert config.cache.enabled is True
        assert config.export.default_format == "parquet"

    def test_正常系_辞書形式でdata_sourcesを設定(self) -> None:
        """辞書形式で data_sources を設定できることを確認。"""
        from typing import Any

        from market.schema import MarketConfig

        # Test runtime dict-to-model conversion
        data_sources: dict[str, Any] = {
            "yfinance": {"timeout": 30},
            "fred": {"api_key": "xxx", "timeout": 30},
        }
        config = MarketConfig(data_sources=data_sources)  # type: ignore[arg-type]

        assert config.data_sources["yfinance"].timeout == 30
        assert config.data_sources["fred"].api_key == "xxx"

    def test_正常系_JSONからロード(self) -> None:
        """JSON 文字列から MarketConfig をロードできることを確認。"""
        import json

        from market.schema import MarketConfig

        json_data = json.dumps(
            {
                "data_sources": {
                    "yfinance": {"timeout": 30},
                    "fred": {"api_key": "xxx", "timeout": 30},
                },
                "cache": {
                    "enabled": True,
                    "ttl_seconds": 3600,
                    "max_size_mb": 100,
                },
                "export": {
                    "default_format": "parquet",
                    "output_dir": "data/exports",
                },
            }
        )

        config = MarketConfig.model_validate_json(json_data)

        assert config.data_sources["yfinance"].timeout == 30
        assert config.cache.enabled is True
        assert config.export.default_format == "parquet"


# =============================================================================
# Validation Functions Tests
# =============================================================================


class TestValidateStockMetadata:
    """Tests for validate_stock_metadata function.

    validate_stock_metadata validates stock data metadata dictionary.
    Returns: (is_valid, errors)
    """

    def test_正常系_有効なデータで検証成功(self) -> None:
        """有効なデータで検証が成功することを確認。"""
        from market.schema import validate_stock_metadata

        data = {
            "symbol": "AAPL",
            "source": "yfinance",
            "fetched_at": "2026-01-25T10:00:00Z",
            "from_cache": False,
            "record_count": 252,
            "date_range": {
                "start": "2025-01-25",
                "end": "2026-01-25",
            },
        }

        is_valid, errors = validate_stock_metadata(data)

        assert is_valid is True
        assert errors == []

    def test_正常系_必須フィールドのみで検証成功(self) -> None:
        """必須フィールドのみで検証が成功することを確認。"""
        from market.schema import validate_stock_metadata

        data = {
            "symbol": "AAPL",
            "source": "yfinance",
            "fetched_at": "2026-01-25T10:00:00Z",
        }

        is_valid, errors = validate_stock_metadata(data)

        assert is_valid is True
        assert errors == []

    def test_異常系_必須フィールドがない場合検証失敗(self) -> None:
        """必須フィールドがない場合、検証が失敗することを確認。"""
        from market.schema import validate_stock_metadata

        data = {
            "source": "yfinance",
            "fetched_at": "2026-01-25T10:00:00Z",
        }

        is_valid, errors = validate_stock_metadata(data)

        assert is_valid is False
        assert len(errors) > 0
        assert any("symbol" in str(e).lower() for e in errors)

    def test_異常系_型が不正な場合検証失敗(self) -> None:
        """型が不正な場合、検証が失敗することを確認。"""
        from market.schema import validate_stock_metadata

        data = {
            "symbol": 123,  # should be str
            "source": "yfinance",
            "fetched_at": "2026-01-25T10:00:00Z",
        }

        is_valid, errors = validate_stock_metadata(data)

        assert is_valid is False
        assert len(errors) > 0


class TestValidateEconomicMetadata:
    """Tests for validate_economic_metadata function.

    validate_economic_metadata validates economic data metadata dictionary.
    Returns: (is_valid, errors)
    """

    def test_正常系_有効なデータで検証成功(self) -> None:
        """有効なデータで検証が成功することを確認。"""
        from market.schema import validate_economic_metadata

        data = {
            "series_id": "GDP",
            "source": "fred",
            "fetched_at": "2026-01-25T10:00:00Z",
            "from_cache": False,
            "record_count": 100,
            "title": "Gross Domestic Product",
        }

        is_valid, errors = validate_economic_metadata(data)

        assert is_valid is True
        assert errors == []

    def test_異常系_必須フィールドがない場合検証失敗(self) -> None:
        """必須フィールドがない場合、検証が失敗することを確認。"""
        from market.schema import validate_economic_metadata

        data = {
            "source": "fred",
            "fetched_at": "2026-01-25T10:00:00Z",
        }

        is_valid, errors = validate_economic_metadata(data)

        assert is_valid is False
        assert any("series_id" in str(e).lower() for e in errors)


class TestValidateConfig:
    """Tests for validate_config function.

    validate_config validates market configuration dictionary.
    Returns: (is_valid, errors)
    """

    def test_正常系_有効な設定で検証成功(self) -> None:
        """有効な設定で検証が成功することを確認。"""
        from market.schema import validate_config

        config = {
            "data_sources": {
                "yfinance": {"timeout": 30},
                "fred": {"api_key": "xxx", "timeout": 30},
            },
            "cache": {
                "enabled": True,
                "ttl_seconds": 3600,
                "max_size_mb": 100,
            },
            "export": {
                "default_format": "parquet",
                "output_dir": "data/exports",
            },
        }

        is_valid, errors = validate_config(config)

        assert is_valid is True
        assert errors == []

    def test_正常系_空の設定で検証成功(self) -> None:
        """空の設定（デフォルト値使用）で検証が成功することを確認。"""
        from market.schema import validate_config

        config: dict = {}

        is_valid, errors = validate_config(config)

        assert is_valid is True
        assert errors == []

    def test_異常系_不正なtimeout値で検証失敗(self) -> None:
        """不正な timeout 値で検証が失敗することを確認。"""
        from market.schema import validate_config

        config = {
            "data_sources": {
                "yfinance": {"timeout": -1},  # invalid
            },
        }

        is_valid, errors = validate_config(config)

        assert is_valid is False
        assert len(errors) > 0

    def test_異常系_不正なフォーマット値で検証失敗(self) -> None:
        """不正な format 値で検証が失敗することを確認。"""
        from market.schema import validate_config

        config = {
            "export": {
                "default_format": "invalid_format",  # invalid
            },
        }

        is_valid, errors = validate_config(config)

        assert is_valid is False
        assert len(errors) > 0
