"""Tests for currencies section in symbols.yaml.

This module tests the currencies section added to symbols.yaml for Issue #2414.
"""

from __future__ import annotations

import pytest

from analyze.config import get_symbol_group, get_symbols, load_symbols_config


class TestCurrenciesSection:
    """Tests for currencies section in symbols.yaml."""

    def test_正常系_currenciesセクションが存在する(self) -> None:
        """currencies セクションが symbols.yaml に存在することを確認."""
        config = load_symbols_config()
        assert "currencies" in config, "currencies セクションが存在しない"

    def test_正常系_jpy_crossesサブグループが存在する(self) -> None:
        """currencies.jpy_crosses サブグループが存在することを確認."""
        config = load_symbols_config()
        assert "currencies" in config
        assert isinstance(config["currencies"], dict)
        assert "jpy_crosses" in config["currencies"]

    def test_正常系_6通貨ペアが定義されている(self) -> None:
        """jpy_crosses に6通貨ペアが正しく定義されていることを確認."""
        symbols = get_symbols("currencies", "jpy_crosses")
        assert len(symbols) == 6, f"期待: 6通貨ペア, 実際: {len(symbols)}通貨ペア"

    def test_正常系_get_symbolsで通貨シンボルを取得できる(self) -> None:
        """get_symbols で通貨シンボルのリストを取得できることを確認."""
        symbols = get_symbols("currencies", "jpy_crosses")

        expected_symbols = [
            "USDJPY=X",
            "EURJPY=X",
            "GBPJPY=X",
            "AUDJPY=X",
            "CADJPY=X",
            "CHFJPY=X",
        ]

        assert symbols == expected_symbols

    def test_正常系_全通貨ペアにsymbolとnameが含まれる(self) -> None:
        """各通貨ペアに symbol と name フィールドが含まれることを確認."""
        currency_pairs = get_symbol_group("currencies", "jpy_crosses")

        for pair in currency_pairs:
            assert "symbol" in pair, f"symbol フィールドがない: {pair}"
            assert "name" in pair, f"name フィールドがない: {pair}"

    def test_正常系_各通貨ペアの名前が正しい(self) -> None:
        """各通貨ペアの name が正しい日本語名であることを確認."""
        currency_pairs = get_symbol_group("currencies", "jpy_crosses")

        expected_names = {
            "USDJPY=X": "米ドル/円",
            "EURJPY=X": "ユーロ/円",
            "GBPJPY=X": "英ポンド/円",
            "AUDJPY=X": "豪ドル/円",
            "CADJPY=X": "カナダドル/円",
            "CHFJPY=X": "スイスフラン/円",
        }

        for pair in currency_pairs:
            symbol = pair["symbol"]
            expected_name = expected_names.get(symbol)
            assert expected_name is not None, f"予期しないシンボル: {symbol}"
            assert pair["name"] == expected_name, (
                f"名前が一致しない: {symbol}, 期待: {expected_name}, 実際: {pair['name']}"
            )


class TestExistingSymbolGroupsUnchanged:
    """既存のシンボルグループに影響がないことを確認するテスト."""

    def test_正常系_indicesグループが正常に動作する(self) -> None:
        """indices グループが引き続き正常に動作することを確認."""
        us_indices = get_symbols("indices", "us")
        assert "^GSPC" in us_indices, "S&P 500 が含まれていない"
        assert "^DJI" in us_indices, "Dow Jones が含まれていない"

    def test_正常系_mag7グループが正常に動作する(self) -> None:
        """mag7 グループが引き続き正常に動作することを確認."""
        mag7 = get_symbols("mag7")
        assert len(mag7) == 7, f"MAG7 は7銘柄であるべき: {len(mag7)}"
        assert "AAPL" in mag7

    def test_正常系_sectorsグループが正常に動作する(self) -> None:
        """sectors グループが引き続き正常に動作することを確認."""
        sectors = get_symbols("sectors")
        assert "XLF" in sectors, "Financial セクターが含まれていない"
        assert "XLK" in sectors, "Technology セクターが含まれていない"

    def test_正常系_commoditiesグループが正常に動作する(self) -> None:
        """commodities グループが引き続き正常に動作することを確認."""
        commodities = get_symbols("commodities")
        assert "GC=F" in commodities, "Gold が含まれていない"
        assert "CL=F" in commodities, "Crude Oil が含まれていない"
