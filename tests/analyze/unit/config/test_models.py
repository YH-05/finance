"""Tests for SymbolsConfig Pydantic model.

This module tests the Pydantic models for symbols.yaml configuration,
created for Issue #2709.
"""

from __future__ import annotations

from analyze.config.models import (
    CommoditySymbol,
    CurrencyPairSymbol,
    IndexSymbol,
    IndicesConfig,
    Mag7Symbol,
    ReturnPeriodsConfig,
    SectorStocksConfig,
    SectorStockSymbol,
    SectorSymbol,
    SymbolsConfig,
)


class TestSymbolInfo:
    """Tests for basic symbol info models."""

    def test_正常系_IndexSymbolを作成できる(self) -> None:
        """IndexSymbol インスタンスを正しく作成できることを確認."""
        symbol = IndexSymbol(symbol="^GSPC", name="S&P 500")
        assert symbol.symbol == "^GSPC"
        assert symbol.name == "S&P 500"

    def test_正常系_Mag7Symbolを作成できる(self) -> None:
        """Mag7Symbol インスタンスを正しく作成できることを確認."""
        symbol = Mag7Symbol(symbol="AAPL", name="Apple")
        assert symbol.symbol == "AAPL"
        assert symbol.name == "Apple"

    def test_正常系_SectorSymbolを作成できる(self) -> None:
        """SectorSymbol インスタンスを正しく作成できることを確認."""
        symbol = SectorSymbol(symbol="XLF", name="Financial Select Sector SPDR")
        assert symbol.symbol == "XLF"
        assert symbol.name == "Financial Select Sector SPDR"

    def test_正常系_CommoditySymbolを作成できる(self) -> None:
        """CommoditySymbol インスタンスを正しく作成できることを確認."""
        symbol = CommoditySymbol(symbol="GC=F", name="Gold Futures")
        assert symbol.symbol == "GC=F"
        assert symbol.name == "Gold Futures"

    def test_正常系_CurrencyPairSymbolを作成できる(self) -> None:
        """CurrencyPairSymbol インスタンスを正しく作成できることを確認."""
        symbol = CurrencyPairSymbol(symbol="USDJPY=X", name="米ドル/円")
        assert symbol.symbol == "USDJPY=X"
        assert symbol.name == "米ドル/円"

    def test_正常系_SectorStockSymbolを作成できる(self) -> None:
        """SectorStockSymbol インスタンスを正しく作成できることを確認."""
        symbol = SectorStockSymbol(
            symbol="JPM",
            name="JPMorgan Chase",
            sector="Financial",
        )
        assert symbol.symbol == "JPM"
        assert symbol.name == "JPMorgan Chase"
        assert symbol.sector == "Financial"


class TestIndicesConfig:
    """Tests for IndicesConfig model."""

    def test_正常系_IndicesConfigを作成できる(self) -> None:
        """IndicesConfig インスタンスを正しく作成できることを確認."""
        us_indices = [
            IndexSymbol(symbol="^GSPC", name="S&P 500"),
            IndexSymbol(symbol="^DJI", name="Dow Jones Industrial Average"),
        ]
        global_indices = [
            IndexSymbol(symbol="^N225", name="日経225"),
        ]
        config = IndicesConfig(us=us_indices, global_=global_indices)
        assert len(config.us) == 2
        assert len(config.global_) == 1

    def test_正常系_空のリストでも作成できる(self) -> None:
        """空のリストでも IndicesConfig を作成できることを確認."""
        config = IndicesConfig(us=[], global_=[])
        assert config.us == []
        assert config.global_ == []


class TestReturnPeriodsConfig:
    """Tests for ReturnPeriodsConfig model."""

    def test_正常系_ReturnPeriodsConfigを作成できる(self) -> None:
        """ReturnPeriodsConfig インスタンスを正しく作成できることを確認."""
        config = ReturnPeriodsConfig(
            d1=1,
            wow="prev_tue",
            w1=5,
            mtd="mtd",
            m1=21,
            m3=63,
            m6=126,
            ytd="ytd",
            y1=252,
            y3=756,
            y5=1260,
        )
        assert config.d1 == 1
        assert config.wow == "prev_tue"
        assert config.ytd == "ytd"


class TestSectorStocksConfig:
    """Tests for SectorStocksConfig model."""

    def test_正常系_SectorStocksConfigを作成できる(self) -> None:
        """SectorStocksConfig インスタンスを正しく作成できることを確認."""
        xlf_stocks = [
            SectorStockSymbol(symbol="JPM", name="JPMorgan Chase", sector="Financial"),
        ]
        config = SectorStocksConfig(XLF=xlf_stocks)
        assert len(config.XLF) == 1
        assert config.XLF[0].symbol == "JPM"


class TestSymbolsConfig:
    """Tests for SymbolsConfig model."""

    def test_正常系_最小限の設定で作成できる(self) -> None:
        """最小限の設定で SymbolsConfig を作成できることを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(us=[], global_=[]),
            mag7=[],
            commodities=[],
            currencies={},
            sectors=[],
            sector_stocks=SectorStocksConfig(),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )
        assert config.mag7 == []

    def test_正常系_get_symbolsでシンボルを取得できる(self) -> None:
        """get_symbols メソッドでシンボルリストを取得できることを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(
                us=[IndexSymbol(symbol="^GSPC", name="S&P 500")],
                global_=[],
            ),
            mag7=[Mag7Symbol(symbol="AAPL", name="Apple")],
            commodities=[],
            currencies={},
            sectors=[],
            sector_stocks=SectorStocksConfig(),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )

        # mag7 シンボルを取得
        mag7_symbols = config.get_symbols("mag7")
        assert mag7_symbols == ["AAPL"]

    def test_正常系_get_symbolsでサブグループを指定できる(self) -> None:
        """get_symbols でサブグループを指定できることを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(
                us=[
                    IndexSymbol(symbol="^GSPC", name="S&P 500"),
                    IndexSymbol(symbol="^DJI", name="Dow Jones"),
                ],
                global_=[IndexSymbol(symbol="^N225", name="日経225")],
            ),
            mag7=[],
            commodities=[],
            currencies={},
            sectors=[],
            sector_stocks=SectorStocksConfig(),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )

        us_indices = config.get_symbols("indices", "us")
        assert us_indices == ["^GSPC", "^DJI"]

        global_indices = config.get_symbols("indices", "global")
        assert global_indices == ["^N225"]

    def test_正常系_存在しないグループで空リストを返す(self) -> None:
        """存在しないグループ名で空リストを返すことを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(us=[], global_=[]),
            mag7=[],
            commodities=[],
            currencies={},
            sectors=[],
            sector_stocks=SectorStocksConfig(),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )
        symbols = config.get_symbols("nonexistent")
        assert symbols == []

    def test_正常系_存在しないサブグループで空リストを返す(self) -> None:
        """存在しないサブグループ名で空リストを返すことを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(us=[], global_=[]),
            mag7=[],
            commodities=[],
            currencies={},
            sectors=[],
            sector_stocks=SectorStocksConfig(),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )
        symbols = config.get_symbols("indices", "nonexistent")
        assert symbols == []


class TestSymbolsConfigGetSymbolGroup:
    """Tests for SymbolsConfig.get_symbol_group method."""

    def _create_test_config(self) -> SymbolsConfig:
        """テスト用の SymbolsConfig を作成."""
        return SymbolsConfig(
            indices=IndicesConfig(
                us=[
                    IndexSymbol(symbol="^GSPC", name="S&P 500"),
                    IndexSymbol(symbol="^DJI", name="Dow Jones"),
                ],
                global_=[IndexSymbol(symbol="^N225", name="日経225")],
            ),
            mag7=[
                Mag7Symbol(symbol="AAPL", name="Apple"),
                Mag7Symbol(symbol="MSFT", name="Microsoft"),
            ],
            commodities=[CommoditySymbol(symbol="GC=F", name="Gold Futures")],
            currencies={
                "jpy_crosses": [
                    CurrencyPairSymbol(symbol="USDJPY=X", name="米ドル/円")
                ],
            },
            sectors=[SectorSymbol(symbol="XLF", name="Financial Select Sector SPDR")],
            sector_stocks=SectorStocksConfig(
                XLF=[
                    SectorStockSymbol(
                        symbol="JPM", name="JPMorgan Chase", sector="Financial"
                    ),
                ],
            ),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )

    def test_正常系_mag7グループを取得(self) -> None:
        """get_symbol_group で mag7 グループを取得できることを確認."""
        config = self._create_test_config()

        group = config.get_symbol_group("mag7")

        assert len(group) == 2
        assert group[0] == {"symbol": "AAPL", "name": "Apple"}
        assert group[1] == {"symbol": "MSFT", "name": "Microsoft"}

    def test_正常系_indicesグループを取得(self) -> None:
        """get_symbol_group で indices グループを取得できることを確認."""
        config = self._create_test_config()

        # サブグループなしで全て取得
        group = config.get_symbol_group("indices")
        assert len(group) == 3

        # US サブグループ
        us_group = config.get_symbol_group("indices", "us")
        assert len(us_group) == 2
        assert us_group[0] == {"symbol": "^GSPC", "name": "S&P 500"}

        # Global サブグループ
        global_group = config.get_symbol_group("indices", "global")
        assert len(global_group) == 1
        assert global_group[0] == {"symbol": "^N225", "name": "日経225"}

    def test_正常系_commoditiesグループを取得(self) -> None:
        """get_symbol_group で commodities グループを取得できることを確認."""
        config = self._create_test_config()

        group = config.get_symbol_group("commodities")

        assert len(group) == 1
        assert group[0] == {"symbol": "GC=F", "name": "Gold Futures"}

    def test_正常系_currenciesグループを取得(self) -> None:
        """get_symbol_group で currencies グループを取得できることを確認."""
        config = self._create_test_config()

        # サブグループなしで全て取得
        group = config.get_symbol_group("currencies")
        assert len(group) == 1

        # jpy_crosses サブグループ
        jpy_group = config.get_symbol_group("currencies", "jpy_crosses")
        assert len(jpy_group) == 1
        assert jpy_group[0] == {"symbol": "USDJPY=X", "name": "米ドル/円"}

    def test_正常系_sectorsグループを取得(self) -> None:
        """get_symbol_group で sectors グループを取得できることを確認."""
        config = self._create_test_config()

        group = config.get_symbol_group("sectors")

        assert len(group) == 1
        assert group[0] == {"symbol": "XLF", "name": "Financial Select Sector SPDR"}

    def test_正常系_sector_stocksグループを取得(self) -> None:
        """get_symbol_group で sector_stocks グループを取得できることを確認."""
        config = self._create_test_config()

        # XLF サブグループ
        xlf_group = config.get_symbol_group("sector_stocks", "XLF")
        assert len(xlf_group) == 1
        assert xlf_group[0] == {"symbol": "JPM", "name": "JPMorgan Chase"}

    def test_正常系_存在しないグループで空リストを返す(self) -> None:
        """存在しないグループ名で空リストを返すことを確認."""
        config = self._create_test_config()

        group = config.get_symbol_group("nonexistent")

        assert group == []

    def test_正常系_存在しないサブグループで空リストを返す(self) -> None:
        """存在しないサブグループ名で空リストを返すことを確認."""
        config = self._create_test_config()

        group = config.get_symbol_group("indices", "nonexistent")

        assert group == []


class TestSymbolsConfigGetReturnPeriodsDict:
    """Tests for SymbolsConfig.get_return_periods_dict method."""

    def test_正常系_全ての期間定義を取得(self) -> None:
        """get_return_periods_dict で全ての期間定義を取得できることを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(us=[], global_=[]),
            mag7=[],
            commodities=[],
            currencies={},
            sectors=[],
            sector_stocks=SectorStocksConfig(),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )

        periods = config.get_return_periods_dict()

        assert periods["1D"] == 1
        assert periods["WoW"] == "prev_tue"
        assert periods["1W"] == 5
        assert periods["MTD"] == "mtd"
        assert periods["1M"] == 21
        assert periods["3M"] == 63
        assert periods["6M"] == 126
        assert periods["YTD"] == "ytd"
        assert periods["1Y"] == 252
        assert periods["3Y"] == 756
        assert periods["5Y"] == 1260


class TestSymbolsConfigEdgeCases:
    """Edge case tests for SymbolsConfig."""

    def test_エッジケース_全インデックスをサブグループなしで取得(self) -> None:
        """サブグループ未指定で全インデックスを取得できることを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(
                us=[IndexSymbol(symbol="^GSPC", name="S&P 500")],
                global_=[IndexSymbol(symbol="^N225", name="日経225")],
            ),
            mag7=[],
            commodities=[],
            currencies={},
            sectors=[],
            sector_stocks=SectorStocksConfig(),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )

        # サブグループなしで全インデックスを取得
        all_indices = config.get_symbols("indices")

        assert "^GSPC" in all_indices
        assert "^N225" in all_indices
        assert len(all_indices) == 2

    def test_エッジケース_全通貨ペアをサブグループなしで取得(self) -> None:
        """サブグループ未指定で全通貨ペアを取得できることを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(us=[], global_=[]),
            mag7=[],
            commodities=[],
            currencies={
                "jpy_crosses": [
                    CurrencyPairSymbol(symbol="USDJPY=X", name="米ドル/円"),
                ],
                "usd_crosses": [
                    CurrencyPairSymbol(symbol="EURUSD=X", name="ユーロ/ドル"),
                ],
            },
            sectors=[],
            sector_stocks=SectorStocksConfig(),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )

        # サブグループなしで全通貨ペアを取得
        all_currencies = config.get_symbols("currencies")

        assert "USDJPY=X" in all_currencies
        assert "EURUSD=X" in all_currencies
        assert len(all_currencies) == 2

    def test_エッジケース_全セクター株をサブグループなしで取得(self) -> None:
        """サブグループ未指定で全セクター株を取得できることを確認."""
        config = SymbolsConfig(
            indices=IndicesConfig(us=[], global_=[]),
            mag7=[],
            commodities=[],
            currencies={},
            sectors=[],
            sector_stocks=SectorStocksConfig(
                XLF=[
                    SectorStockSymbol(
                        symbol="JPM", name="JPMorgan Chase", sector="Financial"
                    ),
                ],
                XLK=[
                    SectorStockSymbol(
                        symbol="CRM", name="Salesforce", sector="Technology"
                    ),
                ],
            ),
            return_periods=ReturnPeriodsConfig(
                d1=1,
                wow="prev_tue",
                w1=5,
                mtd="mtd",
                m1=21,
                m3=63,
                m6=126,
                ytd="ytd",
                y1=252,
                y3=756,
                y5=1260,
            ),
        )

        # サブグループなしで全セクター株を取得
        all_sector_stocks = config.get_symbols("sector_stocks")

        assert "JPM" in all_sector_stocks
        assert "CRM" in all_sector_stocks
        assert len(all_sector_stocks) == 2


class TestSymbolsConfigIntegration:
    """Integration tests with symbols.yaml structure."""

    def test_正常系_YAMLからの変換をシミュレート(self) -> None:
        """symbols.yaml の構造からの変換をシミュレート."""
        # symbols.yaml の一部構造を再現
        yaml_data = {
            "indices": {
                "us": [
                    {"symbol": "^GSPC", "name": "S&P 500"},
                    {"symbol": "^DJI", "name": "Dow Jones Industrial Average"},
                ],
                "global": [
                    {"symbol": "^N225", "name": "日経225"},
                ],
            },
            "mag7": [
                {"symbol": "AAPL", "name": "Apple"},
                {"symbol": "MSFT", "name": "Microsoft"},
            ],
            "commodities": [
                {"symbol": "GC=F", "name": "Gold Futures"},
            ],
            "currencies": {
                "jpy_crosses": [
                    {"symbol": "USDJPY=X", "name": "米ドル/円"},
                ],
            },
            "sectors": [
                {"symbol": "XLF", "name": "Financial Select Sector SPDR"},
            ],
            "sector_stocks": {
                "XLF": [
                    {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "Financial"},
                ],
            },
            "return_periods": {
                "1D": 1,
                "WoW": "prev_tue",
                "1W": 5,
                "MTD": "mtd",
                "1M": 21,
                "3M": 63,
                "6M": 126,
                "YTD": "ytd",
                "1Y": 252,
                "3Y": 756,
                "5Y": 1260,
            },
        }

        # IndicesConfig の変換
        indices_config = IndicesConfig(
            us=[IndexSymbol(**item) for item in yaml_data["indices"]["us"]],
            global_=[IndexSymbol(**item) for item in yaml_data["indices"]["global"]],
        )

        # SymbolsConfig の構築
        config = SymbolsConfig(
            indices=indices_config,
            mag7=[Mag7Symbol(**item) for item in yaml_data["mag7"]],
            commodities=[CommoditySymbol(**item) for item in yaml_data["commodities"]],
            currencies={
                "jpy_crosses": [
                    CurrencyPairSymbol(**item)
                    for item in yaml_data["currencies"]["jpy_crosses"]
                ],
            },
            sectors=[SectorSymbol(**item) for item in yaml_data["sectors"]],
            sector_stocks=SectorStocksConfig(
                XLF=[
                    SectorStockSymbol(**item)
                    for item in yaml_data["sector_stocks"]["XLF"]
                ],
            ),
            return_periods=ReturnPeriodsConfig(
                d1=yaml_data["return_periods"]["1D"],
                wow=yaml_data["return_periods"]["WoW"],
                w1=yaml_data["return_periods"]["1W"],
                mtd=yaml_data["return_periods"]["MTD"],
                m1=yaml_data["return_periods"]["1M"],
                m3=yaml_data["return_periods"]["3M"],
                m6=yaml_data["return_periods"]["6M"],
                ytd=yaml_data["return_periods"]["YTD"],
                y1=yaml_data["return_periods"]["1Y"],
                y3=yaml_data["return_periods"]["3Y"],
                y5=yaml_data["return_periods"]["5Y"],
            ),
        )

        # 検証
        assert config.get_symbols("mag7") == ["AAPL", "MSFT"]
        assert config.get_symbols("indices", "us") == ["^GSPC", "^DJI"]
        assert config.get_symbols("indices", "global") == ["^N225"]
        assert config.get_symbols("commodities") == ["GC=F"]
        assert config.get_symbols("currencies", "jpy_crosses") == ["USDJPY=X"]
        assert config.get_symbols("sectors") == ["XLF"]
