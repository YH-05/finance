"""Unit tests for market.etfcom.collectors module.

TickerCollector の動作を検証するテストスイート。
ETF.com スクリーナーページから ETF ティッカー一覧を取得するクラスのテスト。

Test TODO List:
- [x] TickerCollector: デフォルト値で初期化
- [x] TickerCollector: カスタム browser / config で初期化
- [x] TickerCollector: DataCollector を継承していること
- [x] TickerCollector: name プロパティ
- [x] fetch(): pd.DataFrame を返却する
- [x] fetch(): 返却 DataFrame に必須カラムが含まれること
- [x] _parse_screener_table(): テーブル行をパースする
- [x] _parse_screener_table(): '--' を NaN に変換する
- [x] _parse_screener_table(): 空テーブルで空リスト
- [x] _rows_to_dataframe(): dict リストを DataFrame に変換する
- [x] _rows_to_dataframe(): 空リストで空 DataFrame
- [x] validate(): 空 DataFrame で False
- [x] validate(): 非空で ticker 列ありで True
- [x] validate(): ticker 列なしで False
- [x] browser がコンストラクタで注入可能であること
- [x] structlog ロガーの使用
- [x] __all__ エクスポート
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from market.base_collector import DataCollector
from market.etfcom.types import ScrapingConfig

# =============================================================================
# Required columns constant
# =============================================================================

REQUIRED_COLUMNS = {"ticker", "name", "issuer", "category", "expense_ratio", "aum"}

# =============================================================================
# Sample HTML fixtures
# =============================================================================

SAMPLE_SCREENER_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head><title>ETF Screener | ETF.com</title></head>
<body>
<div id="etf-screener">
  <table class="screener-table">
    <thead>
      <tr>
        <th>Ticker</th>
        <th>Fund Name</th>
        <th>Issuer</th>
        <th>Segment</th>
        <th>Expense Ratio</th>
        <th>AUM</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="/SPY">SPY</a></td>
        <td>SPDR S&amp;P 500 ETF Trust</td>
        <td>State Street</td>
        <td>Equity: U.S. - Large Cap</td>
        <td>0.09%</td>
        <td>$500.00B</td>
      </tr>
      <tr>
        <td><a href="/VOO">VOO</a></td>
        <td>Vanguard S&amp;P 500 ETF</td>
        <td>Vanguard</td>
        <td>Equity: U.S. - Large Cap</td>
        <td>0.03%</td>
        <td>$751.49B</td>
      </tr>
      <tr>
        <td><a href="/QQQ">QQQ</a></td>
        <td>Invesco QQQ Trust</td>
        <td>Invesco</td>
        <td>Equity: U.S. - Large Cap Growth</td>
        <td>0.20%</td>
        <td>$280.00B</td>
      </tr>
    </tbody>
  </table>
</div>
</body>
</html>"""

SAMPLE_SCREENER_HTML_WITH_PLACEHOLDER = """\
<!DOCTYPE html>
<html lang="en">
<body>
<table class="screener-table">
  <thead>
    <tr>
      <th>Ticker</th>
      <th>Fund Name</th>
      <th>Issuer</th>
      <th>Segment</th>
      <th>Expense Ratio</th>
      <th>AUM</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="/SPY">SPY</a></td>
      <td>SPDR S&amp;P 500 ETF Trust</td>
      <td>State Street</td>
      <td>Equity: U.S. - Large Cap</td>
      <td>0.09%</td>
      <td>$500.00B</td>
    </tr>
    <tr>
      <td><a href="/PFFL">PFFL</a></td>
      <td>ETRACS 2xMonthly Pay Leveraged Preferred Stock</td>
      <td>--</td>
      <td>--</td>
      <td>--</td>
      <td>--</td>
    </tr>
  </tbody>
</table>
</body>
</html>"""

SAMPLE_EMPTY_TABLE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<body>
<table class="screener-table">
  <thead>
    <tr>
      <th>Ticker</th>
      <th>Fund Name</th>
      <th>Issuer</th>
      <th>Segment</th>
      <th>Expense Ratio</th>
      <th>AUM</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>
</body>
</html>"""


# =============================================================================
# Initialization tests
# =============================================================================


class TestTickerCollectorInit:
    """TickerCollector 初期化のテスト。"""

    def test_正常系_デフォルト値で初期化できる(self) -> None:
        """デフォルトの config で初期化されること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        assert collector._config is not None
        assert isinstance(collector._config, ScrapingConfig)

    def test_正常系_カスタムconfigで初期化できる(self) -> None:
        """カスタム ScrapingConfig で初期化されること。"""
        from market.etfcom.collectors import TickerCollector

        config = ScrapingConfig(polite_delay=5.0, headless=False)
        collector = TickerCollector(config=config)

        assert collector._config.polite_delay == 5.0
        assert collector._config.headless is False

    def test_正常系_browserを注入できる(self) -> None:
        """外部から browser を注入できること（DI パターン）。"""
        from market.etfcom.collectors import TickerCollector

        mock_browser = AsyncMock()
        collector = TickerCollector(browser=mock_browser)

        assert collector._browser_instance is mock_browser

    def test_正常系_browser_Noneでデフォルト(self) -> None:
        """browser=None の場合 _browser_instance が None であること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        assert collector._browser_instance is None

    def test_正常系_DataCollectorを継承している(self) -> None:
        """TickerCollector が DataCollector を継承していること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        assert isinstance(collector, DataCollector)

    def test_正常系_nameプロパティがTickerCollectorを返す(self) -> None:
        """name プロパティが 'TickerCollector' を返すこと。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        assert collector.name == "TickerCollector"


# =============================================================================
# _parse_screener_table() tests
# =============================================================================


class TestParseScreenerTable:
    """_parse_screener_table() のテスト。"""

    def test_正常系_テーブル行をパースする(self) -> None:
        """HTML テーブルから ETF 行を正しくパースすること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        rows = collector._parse_screener_table(SAMPLE_SCREENER_HTML)

        assert len(rows) == 3
        assert rows[0]["ticker"] == "SPY"
        assert rows[0]["name"] == "SPDR S&P 500 ETF Trust"
        assert rows[1]["ticker"] == "VOO"
        assert rows[2]["ticker"] == "QQQ"

    def test_正常系_プレースホルダをNoneに変換する(self) -> None:
        """'--' プレースホルダーが None に変換されること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        rows = collector._parse_screener_table(SAMPLE_SCREENER_HTML_WITH_PLACEHOLDER)

        assert len(rows) == 2
        # PFFL row has '--' placeholders
        pffl_row = rows[1]
        assert pffl_row["ticker"] == "PFFL"
        assert pffl_row["issuer"] is None
        assert pffl_row["category"] is None
        assert pffl_row["expense_ratio"] is None
        assert pffl_row["aum"] is None

    def test_正常系_空テーブルで空リスト(self) -> None:
        """空のテーブルから空リストが返ること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        rows = collector._parse_screener_table(SAMPLE_EMPTY_TABLE_HTML)

        assert rows == []

    def test_正常系_テーブルなしのHTMLで空リスト(self) -> None:
        """テーブルが存在しない HTML から空リストが返ること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        rows = collector._parse_screener_table(
            "<html><body>No table here</body></html>"
        )

        assert rows == []


# =============================================================================
# _rows_to_dataframe() tests
# =============================================================================


class TestRowsToDataframe:
    """_rows_to_dataframe() のテスト。"""

    def test_正常系_dictリストをDataFrameに変換する(self) -> None:
        """dict のリストが pd.DataFrame に正しく変換されること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        rows: list[dict[str, str | None]] = [
            {
                "ticker": "SPY",
                "name": "SPDR S&P 500 ETF Trust",
                "issuer": "State Street",
                "category": "Equity: U.S. - Large Cap",
                "expense_ratio": "0.09%",
                "aum": "$500.00B",
            },
            {
                "ticker": "VOO",
                "name": "Vanguard S&P 500 ETF",
                "issuer": "Vanguard",
                "category": "Equity: U.S. - Large Cap",
                "expense_ratio": "0.03%",
                "aum": "$751.49B",
            },
        ]

        df = collector._rows_to_dataframe(rows)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert set(REQUIRED_COLUMNS).issubset(set(df.columns))
        assert df["ticker"].tolist() == ["SPY", "VOO"]

    def test_正常系_空リストで空DataFrame(self) -> None:
        """空リストから空 DataFrame が返ること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        df = collector._rows_to_dataframe([])

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_正常系_NoneがNaNに変換される(self) -> None:
        """None 値が NaN に変換されること。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        rows = [
            {
                "ticker": "PFFL",
                "name": "ETRACS 2xMonthly Pay",
                "issuer": None,
                "category": None,
                "expense_ratio": None,
                "aum": None,
            },
        ]

        df = collector._rows_to_dataframe(rows)

        assert len(df) == 1
        assert df["ticker"].iloc[0] == "PFFL"
        assert pd.isna(df["issuer"].iloc[0])
        assert pd.isna(df["expense_ratio"].iloc[0])


# =============================================================================
# validate() tests
# =============================================================================


class TestValidate:
    """validate() のテスト。"""

    def test_正常系_非空でticker列ありでTrue(self) -> None:
        """非空 DataFrame で ticker 列がある場合 True を返すこと。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        df = pd.DataFrame(
            {
                "ticker": ["SPY", "VOO"],
                "name": ["SPDR S&P 500", "Vanguard S&P 500"],
                "issuer": ["State Street", "Vanguard"],
                "category": ["Large Cap", "Large Cap"],
                "expense_ratio": ["0.09%", "0.03%"],
                "aum": ["$500B", "$751B"],
            }
        )

        assert collector.validate(df) is True

    def test_異常系_空DataFrameでFalse(self) -> None:
        """空 DataFrame で False を返すこと。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        df = pd.DataFrame()

        assert collector.validate(df) is False

    def test_異常系_ticker列なしでFalse(self) -> None:
        """ticker 列がない DataFrame で False を返すこと。"""
        from market.etfcom.collectors import TickerCollector

        collector = TickerCollector()
        df = pd.DataFrame(
            {
                "name": ["SPDR S&P 500"],
                "issuer": ["State Street"],
            }
        )

        assert collector.validate(df) is False


# =============================================================================
# fetch() tests (via _async_fetch)
# =============================================================================


class TestFetch:
    """fetch() / _async_fetch() のテスト。"""

    @pytest.mark.asyncio
    async def test_正常系_DataFrameを返却する(self) -> None:
        """_async_fetch() が pd.DataFrame を返却すること。"""
        from market.etfcom.collectors import TickerCollector

        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value=SAMPLE_SCREENER_HTML)
        mock_page.query_selector = AsyncMock(return_value=None)  # no next page
        mock_page.close = AsyncMock()

        mock_browser._ensure_browser = AsyncMock()
        mock_browser._navigate = AsyncMock(return_value=mock_page)
        mock_browser._accept_cookies = AsyncMock()
        mock_browser._click_display_100 = AsyncMock()
        mock_browser.close = AsyncMock()

        config = ScrapingConfig(
            polite_delay=0.0,
            delay_jitter=0.0,
            timeout=5.0,
            stability_wait=0.0,
        )
        collector = TickerCollector(browser=mock_browser, config=config)

        with patch("market.etfcom.collectors.asyncio.sleep", new_callable=AsyncMock):
            df = await collector._async_fetch()

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "ticker" in df.columns

    @pytest.mark.asyncio
    async def test_正常系_必須カラムが含まれること(self) -> None:
        """返却 DataFrame に必須カラムが全て含まれること。"""
        from market.etfcom.collectors import TickerCollector

        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value=SAMPLE_SCREENER_HTML)
        mock_page.query_selector = AsyncMock(return_value=None)
        mock_page.close = AsyncMock()

        mock_browser._ensure_browser = AsyncMock()
        mock_browser._navigate = AsyncMock(return_value=mock_page)
        mock_browser._accept_cookies = AsyncMock()
        mock_browser._click_display_100 = AsyncMock()
        mock_browser.close = AsyncMock()

        config = ScrapingConfig(
            polite_delay=0.0,
            delay_jitter=0.0,
            timeout=5.0,
            stability_wait=0.0,
        )
        collector = TickerCollector(browser=mock_browser, config=config)

        with patch("market.etfcom.collectors.asyncio.sleep", new_callable=AsyncMock):
            df = await collector._async_fetch()

        for col in REQUIRED_COLUMNS:
            assert col in df.columns, f"Missing required column: {col}"

    @pytest.mark.asyncio
    async def test_正常系_ページネーションで複数ページ取得(self) -> None:
        """複数ページのデータを結合して返すこと。"""
        from market.etfcom.collectors import TickerCollector

        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        # First call returns HTML with next button, second returns without
        mock_page.content = AsyncMock(
            side_effect=[SAMPLE_SCREENER_HTML, SAMPLE_SCREENER_HTML]
        )

        # First query returns a next button, second returns None
        mock_next_button = AsyncMock()
        mock_next_button.click = AsyncMock()
        mock_page.query_selector = AsyncMock(side_effect=[mock_next_button, None])
        mock_page.close = AsyncMock()

        mock_browser._ensure_browser = AsyncMock()
        mock_browser._navigate = AsyncMock(return_value=mock_page)
        mock_browser._accept_cookies = AsyncMock()
        mock_browser._click_display_100 = AsyncMock()
        mock_browser.close = AsyncMock()

        config = ScrapingConfig(
            polite_delay=0.0,
            delay_jitter=0.0,
            timeout=5.0,
            stability_wait=0.0,
        )
        collector = TickerCollector(browser=mock_browser, config=config)

        with patch("market.etfcom.collectors.asyncio.sleep", new_callable=AsyncMock):
            df = await collector._async_fetch()

        # 3 rows per page x 2 pages = 6 rows
        assert len(df) == 6


# =============================================================================
# Logging tests
# =============================================================================


class TestLogging:
    """ロギングのテスト。"""

    def test_正常系_loggerが定義されている(self) -> None:
        """モジュールレベルで structlog ロガーが定義されていること。"""
        import market.etfcom.collectors as collectors_module

        assert hasattr(collectors_module, "logger")


# =============================================================================
# __all__ export tests
# =============================================================================


class TestModuleExports:
    """__all__ エクスポートのテスト。"""

    def test_正常系_TickerCollectorがエクスポートされている(self) -> None:
        """__all__ に TickerCollector が含まれていること。"""
        from market.etfcom.collectors import __all__

        assert "TickerCollector" in __all__
