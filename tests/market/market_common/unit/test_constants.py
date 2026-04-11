"""Tests for market.market_common.constants module.

Tests verify all constant definitions for the ASEAN common module,
including MarketExchange enum, yfinance suffix mapping, screener exchange
mapping, screener market mapping, table name, DB path, and module exports.

Test TODO List:
- [x] Module exports: __all__ completeness and importability
- [x] MarketExchange Enum: 6 members, str inheritance, values
- [x] YFINANCE_SUFFIX_MAP: all 6 markets mapped to correct suffixes
- [x] SCREENER_EXCHANGE_MAP: all 6 markets mapped to screener names
- [x] SCREENER_MARKET_MAP: all 6 markets mapped to screener market names
- [x] TABLE_TICKERS: non-empty string
- [x] DB_PATH: absolute Path with correct format
- [x] Final annotations: all non-enum constants annotated with typing.Final
"""

from typing import get_type_hints

from market.market_common.constants import (
    DB_PATH,
    SCREENER_EXCHANGE_MAP,
    SCREENER_MARKET_MAP,
    TABLE_TICKERS,
    YFINANCE_SUFFIX_MAP,
    MarketExchange,
    __all__,
)

# =============================================================================
# Module exports
# =============================================================================


class TestModuleExports:
    """Test module __all__ exports and structure."""

    def test_正常系_モジュールがインポートできる(self) -> None:
        """constants モジュールが正常にインポートできること。"""
        from market.market_common import constants

        assert constants is not None

    def test_正常系_allが定義されている(self) -> None:
        """__all__ がリストとして定義されていること。"""
        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_正常系_allの全項目がモジュールに存在する(self) -> None:
        """__all__ の全項目がモジュールの属性として存在すること。"""
        from market.market_common import constants

        for name in __all__:
            assert hasattr(constants, name), (
                f"{name} is not defined in constants module"
            )

    def test_正常系_allが6項目を含む(self) -> None:
        """__all__ が全6定数をエクスポートしていること。"""
        expected = {
            "MarketExchange",
            "DB_PATH",
            "SCREENER_EXCHANGE_MAP",
            "SCREENER_MARKET_MAP",
            "TABLE_TICKERS",
            "YFINANCE_SUFFIX_MAP",
        }
        assert set(__all__) == expected

    def test_正常系_モジュールDocstringが存在する(self) -> None:
        """モジュールの docstring が存在すること。"""
        from market.market_common import constants

        assert constants.__doc__ is not None
        assert len(constants.__doc__) > 0


# =============================================================================
# MarketExchange Enum
# =============================================================================


class TestMarketExchangeEnum:
    """Test MarketExchange Enum definition."""

    def test_正常系_strを継承している(self) -> None:
        """MarketExchange が str と Enum を継承していること。"""
        from enum import Enum

        assert issubclass(MarketExchange, str)
        assert issubclass(MarketExchange, Enum)

    def test_正常系_6つのメンバーを持つ(self) -> None:
        """MarketExchange が ASEAN 6市場 + India 2市場の8メンバーを持つこと。"""
        assert len(MarketExchange) == 8

    def test_正常系_全メンバーの値が正しい(self) -> None:
        """MarketExchange の全メンバーの値が設計通りであること。"""
        assert MarketExchange.SGX.value == "SGX"
        assert MarketExchange.BURSA.value == "BURSA"
        assert MarketExchange.SET.value == "SET"
        assert MarketExchange.IDX.value == "IDX"
        assert MarketExchange.HOSE.value == "HOSE"
        assert MarketExchange.PSE.value == "PSE"
        assert MarketExchange.NSE.value == "NSE"
        assert MarketExchange.BSE.value == "BSE"

    def test_正常系_文字列として使用できる(self) -> None:
        """MarketExchange メンバーを文字列として直接使用できること。"""
        value: str = MarketExchange.SGX
        assert isinstance(value, str)
        assert value == "SGX"

    def test_正常系_全メンバー名が含まれている(self) -> None:
        """MarketExchange に ASEAN 6市場 + India 2市場が含まれていること。"""
        expected = {"SGX", "BURSA", "SET", "IDX", "HOSE", "PSE", "NSE", "BSE"}
        actual = {member.value for member in MarketExchange}
        assert actual == expected


# =============================================================================
# YFINANCE_SUFFIX_MAP
# =============================================================================


class TestYfinanceSuffixMap:
    """Test YFINANCE_SUFFIX_MAP constant."""

    def test_正常系_dictである(self) -> None:
        """YFINANCE_SUFFIX_MAP が dict であること。"""
        assert isinstance(YFINANCE_SUFFIX_MAP, dict)

    def test_正常系_全6市場が含まれている(self) -> None:
        """YFINANCE_SUFFIX_MAP が全8市場（ASEAN 6 + India 2）のエントリを含むこと。"""
        assert len(YFINANCE_SUFFIX_MAP) == 8
        for market in MarketExchange:
            assert market in YFINANCE_SUFFIX_MAP, (
                f"{market.value} is not in YFINANCE_SUFFIX_MAP"
            )

    def test_正常系_SGXのサフィックスが正しい(self) -> None:
        """SGX のサフィックスが .SI であること。"""
        assert YFINANCE_SUFFIX_MAP[MarketExchange.SGX] == ".SI"

    def test_正常系_BURSAのサフィックスが正しい(self) -> None:
        """BURSA のサフィックスが .KL であること。"""
        assert YFINANCE_SUFFIX_MAP[MarketExchange.BURSA] == ".KL"

    def test_正常系_SETのサフィックスが正しい(self) -> None:
        """SET のサフィックスが .BK であること。"""
        assert YFINANCE_SUFFIX_MAP[MarketExchange.SET] == ".BK"

    def test_正常系_IDXのサフィックスが正しい(self) -> None:
        """IDX のサフィックスが .JK であること。"""
        assert YFINANCE_SUFFIX_MAP[MarketExchange.IDX] == ".JK"

    def test_正常系_HOSEのサフィックスが正しい(self) -> None:
        """HOSE のサフィックスが .VN であること。"""
        assert YFINANCE_SUFFIX_MAP[MarketExchange.HOSE] == ".VN"

    def test_正常系_PSEのサフィックスが正しい(self) -> None:
        """PSE のサフィックスが .PS であること。"""
        assert YFINANCE_SUFFIX_MAP[MarketExchange.PSE] == ".PS"

    def test_正常系_NSEのサフィックスが正しい(self) -> None:
        """NSE のサフィックスが .NS であること。"""
        assert YFINANCE_SUFFIX_MAP[MarketExchange.NSE] == ".NS"

    def test_正常系_BSEのサフィックスが正しい(self) -> None:
        """BSE のサフィックスが .BO であること。"""
        assert YFINANCE_SUFFIX_MAP[MarketExchange.BSE] == ".BO"

    def test_正常系_全サフィックスがドットで始まる(self) -> None:
        """全サフィックスが . で始まること。"""
        for market, suffix in YFINANCE_SUFFIX_MAP.items():
            assert suffix.startswith("."), (
                f"Suffix for {market.value} does not start with '.': {suffix}"
            )

    def test_正常系_サフィックスに重複がない(self) -> None:
        """サフィックス値に重複がないこと。"""
        values = list(YFINANCE_SUFFIX_MAP.values())
        assert len(values) == len(set(values)), "Duplicate suffixes found"


# =============================================================================
# SCREENER_EXCHANGE_MAP
# =============================================================================


class TestScreenerExchangeMap:
    """Test SCREENER_EXCHANGE_MAP constant."""

    def test_正常系_dictである(self) -> None:
        """SCREENER_EXCHANGE_MAP が dict であること。"""
        assert isinstance(SCREENER_EXCHANGE_MAP, dict)

    def test_正常系_全6市場が含まれている(self) -> None:
        """SCREENER_EXCHANGE_MAP が ASEAN 6市場 + NSE の7エントリを含むこと。

        Notes
        -----
        BSE は tradingview-screener で市場="india" に NSE と重複するため、
        意図的に SCREENER_EXCHANGE_MAP から除外されている。
        NSE では exchange フィルタ ("NSE") により重複排除を実施する。
        """
        expected_markets = {
            MarketExchange.SGX,
            MarketExchange.BURSA,
            MarketExchange.SET,
            MarketExchange.IDX,
            MarketExchange.HOSE,
            MarketExchange.PSE,
            MarketExchange.NSE,
        }
        assert len(SCREENER_EXCHANGE_MAP) == 7
        for market in expected_markets:
            assert market in SCREENER_EXCHANGE_MAP, (
                f"{market.value} is not in SCREENER_EXCHANGE_MAP"
            )
        # BSE は意図的に除外
        assert MarketExchange.BSE not in SCREENER_EXCHANGE_MAP

    def test_正常系_値がstr型である(self) -> None:
        """SCREENER_EXCHANGE_MAP の値が全て str であること。"""
        for market, exchange in SCREENER_EXCHANGE_MAP.items():
            assert isinstance(exchange, str), (
                f"Value for {market.value} is not str: {type(exchange)}"
            )
            assert len(exchange.strip()) > 0, f"Value for {market.value} is empty"

    def test_正常系_値に重複がない(self) -> None:
        """SCREENER_EXCHANGE_MAP の値に重複がないこと。"""
        values = list(SCREENER_EXCHANGE_MAP.values())
        assert len(values) == len(set(values)), "Duplicate exchange names found"


# =============================================================================
# SCREENER_MARKET_MAP
# =============================================================================


class TestScreenerMarketMap:
    """Test SCREENER_MARKET_MAP constant."""

    def test_正常系_dictである(self) -> None:
        """SCREENER_MARKET_MAP が dict であること。"""
        assert isinstance(SCREENER_MARKET_MAP, dict)

    def test_正常系_全6市場が含まれている(self) -> None:
        """SCREENER_MARKET_MAP が ASEAN 6市場 + NSE の7エントリを含むこと。

        Notes
        -----
        BSE は tradingview-screener で市場="india" に NSE と重複するため、
        意図的に SCREENER_MARKET_MAP から除外されている。
        """
        expected_markets = {
            MarketExchange.SGX,
            MarketExchange.BURSA,
            MarketExchange.SET,
            MarketExchange.IDX,
            MarketExchange.HOSE,
            MarketExchange.PSE,
            MarketExchange.NSE,
        }
        assert len(SCREENER_MARKET_MAP) == 7
        for market in expected_markets:
            assert market in SCREENER_MARKET_MAP, (
                f"{market.value} is not in SCREENER_MARKET_MAP"
            )
        # BSE は意図的に除外
        assert MarketExchange.BSE not in SCREENER_MARKET_MAP

    def test_正常系_値がstr型である(self) -> None:
        """SCREENER_MARKET_MAP の値が全て str であること。"""
        for market, name in SCREENER_MARKET_MAP.items():
            assert isinstance(name, str), (
                f"Value for {market.value} is not str: {type(name)}"
            )
            assert len(name.strip()) > 0, f"Value for {market.value} is empty"

    def test_正常系_値が全て小文字である(self) -> None:
        """SCREENER_MARKET_MAP の値が全て小文字であること。"""
        for market, name in SCREENER_MARKET_MAP.items():
            assert name == name.lower(), (
                f"Value for {market.value} is not lowercase: {name}"
            )

    def test_正常系_値に重複がない(self) -> None:
        """SCREENER_MARKET_MAP の値に重複がないこと。"""
        values = list(SCREENER_MARKET_MAP.values())
        assert len(values) == len(set(values)), "Duplicate market names found"


# =============================================================================
# TABLE_TICKERS
# =============================================================================


class TestTableTickers:
    """Test TABLE_TICKERS constant."""

    def test_正常系_strである(self) -> None:
        """TABLE_TICKERS が str であること。"""
        assert isinstance(TABLE_TICKERS, str)

    def test_正常系_空でない(self) -> None:
        """TABLE_TICKERS が空文字列でないこと。"""
        assert len(TABLE_TICKERS.strip()) > 0

    def test_正常系_aseanを含む(self) -> None:
        """TABLE_TICKERS が asean を含むこと。"""
        assert "asean" in TABLE_TICKERS.lower()


# =============================================================================
# DB_PATH
# =============================================================================


class TestDBPath:
    """Test DB_PATH constant."""

    def test_正常系_Pathである(self) -> None:
        """DB_PATH が Path であること。"""
        from pathlib import Path

        assert isinstance(DB_PATH, Path)

    def test_正常系_絶対パスである(self) -> None:
        """DB_PATH が絶対パスであること。"""
        assert DB_PATH.is_absolute()

    def test_正常系_data_processedを含む(self) -> None:
        """DB_PATH が data/processed パスを含むこと。"""
        assert "data" in DB_PATH.parts
        assert "processed" in DB_PATH.parts

    def test_正常系_duckdb拡張子を含む(self) -> None:
        """DB_PATH が .duckdb 拡張子を含むこと。"""
        assert DB_PATH.suffix == ".duckdb"

    def test_正常系_aseanデータベースファイル名(self) -> None:
        """DB_PATH のファイル名が asean.duckdb であること。"""
        assert DB_PATH.name == "asean.duckdb"


# =============================================================================
# Final type annotations
# =============================================================================


class TestFinalAnnotations:
    """Test that non-enum constants have Final type annotations."""

    def test_正常系_非Enum定数にFinal型アノテーションが付与されている(self) -> None:
        """非Enum の __all__ 定数に typing.Final アノテーションが付与されていること。"""
        from market.market_common import constants

        annotations = get_type_hints(constants, include_extras=True)

        non_enum_names = [name for name in __all__ if name != "MarketExchange"]

        for name in non_enum_names:
            assert name in annotations, (
                f"{name} does not have a type annotation in the module"
            )
            annotation_str = str(annotations[name])
            assert "Final" in annotation_str, (
                f"{name} is not annotated with Final. Got: {annotation_str}"
            )
