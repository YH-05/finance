"""Unit tests for market.nse.constants module.

Tests verify all constant definitions for the NSE data retrieval module,
including API URLs, SSRF prevention whitelist, default HTTP headers,
User-Agent rotation list, polite delay, timeout, delay jitter,
cookie refresh interval, output directory, column name mappings, and
XBRL namespace constants.

Test TODO List:
- [x] Module exports: __all__ completeness and importability
- [x] API URLs: BASE_URL and API_BASE_URL format and domain
- [x] API URLs: CORPORATE_SHARE_HOLDINGS_ENDPOINT derived from API_BASE_URL
- [x] Security: ALLOWED_HOSTS contains NSE domain
- [x] Bot-blocking: DEFAULT_USER_AGENTS count, Mozilla prefix, uniqueness
- [x] Bot-blocking: DEFAULT_POLITE_DELAY, DEFAULT_TIMEOUT, DEFAULT_DELAY_JITTER values
- [x] Session: COOKIE_REFRESH_INTERVAL value
- [x] Headers: DEFAULT_HEADERS required keys and values
- [x] Output: DEFAULT_OUTPUT_SUBDIR format
- [x] Column mapping: EQUITY_QUOTE_COLUMN_NAME_MAP, INDEX_CONSTITUENTS_COLUMN_NAME_MAP
- [x] XBRL namespaces: XBRL_SHP_NS, XBRLI_NS, XBRLDI_NS are Final[str]
- [x] Final annotations: all constants annotated with typing.Final
"""

from typing import get_type_hints

from market.nse.constants import (
    ALLOWED_HOSTS,
    API_BASE_URL,
    BASE_URL,
    COOKIE_REFRESH_INTERVAL,
    CORPORATE_SHARE_HOLDINGS_ENDPOINT,
    DEFAULT_DELAY_JITTER,
    DEFAULT_HEADERS,
    DEFAULT_OUTPUT_SUBDIR,
    DEFAULT_POLITE_DELAY,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENTS,
    EQUITY_QUOTE_COLUMN_NAME_MAP,
    FINANCIAL_RESULT_COLUMN_NAME_MAP,
    INDEX_CONSTITUENTS_COLUMN_NAME_MAP,
    XBRL_SHP_NS,
    XBRLDI_NS,
    XBRLI_NS,
    __all__,
)

# =============================================================================
# Module exports
# =============================================================================


class TestModuleExports:
    """Test module __all__ exports and structure."""

    def test_正常系_モジュールがインポートできる(self) -> None:
        """constants モジュールが正常にインポートできること。"""
        from market.nse import constants

        assert constants is not None

    def test_正常系_allが定義されている(self) -> None:
        """__all__ がリストとして定義されていること。"""
        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_正常系_allの全項目がモジュールに存在する(self) -> None:
        """__all__ の全項目がモジュールの属性として存在すること。"""
        from market.nse import constants

        for name in __all__:
            assert hasattr(constants, name), (
                f"{name} is not defined in constants module"
            )

    def test_正常系_allが25項目を含む(self) -> None:
        """__all__ が全25定数をエクスポートしていること（XBRL_SHP_NS_PATTERN 追加）。"""
        assert len(__all__) == 25

    def test_正常系_モジュールDocstringが存在する(self) -> None:
        """モジュールの docstring が存在すること。"""
        from market.nse import constants

        assert constants.__doc__ is not None
        assert len(constants.__doc__) > 0


# =============================================================================
# API URL constants
# =============================================================================


class TestAPIURLConstants:
    """Test NSE API URL constants."""

    def test_正常系_BASE_URLがhttpsで始まる(self) -> None:
        """BASE_URL が https:// で始まること。"""
        assert isinstance(BASE_URL, str)
        assert BASE_URL.startswith("https://")

    def test_正常系_BASE_URLがnseindiaドメインを含む(self) -> None:
        """BASE_URL が www.nseindia.com ドメインを含むこと。"""
        assert "www.nseindia.com" in BASE_URL

    def test_正常系_BASE_URLが正しい値(self) -> None:
        """BASE_URL が設計通りの値であること。"""
        assert BASE_URL == "https://www.nseindia.com"

    def test_正常系_API_BASE_URLがhttpsで始まる(self) -> None:
        """API_BASE_URL が https:// で始まること。"""
        assert isinstance(API_BASE_URL, str)
        assert API_BASE_URL.startswith("https://")

    def test_正常系_API_BASE_URLがnseindiaのapiパスを含む(self) -> None:
        """API_BASE_URL が nseindia.com/api パスを含むこと。"""
        assert "nseindia.com/api" in API_BASE_URL

    def test_正常系_API_BASE_URLが正しい値(self) -> None:
        """API_BASE_URL が設計通りの値であること。"""
        assert API_BASE_URL == "https://www.nseindia.com/api"

    def test_正常系_BASE_URLがAPI_BASE_URLのプレフィックスである(self) -> None:
        """BASE_URL が API_BASE_URL のプレフィックスであること。"""
        assert API_BASE_URL.startswith(BASE_URL)

    def test_正常系_CORPORATE_SHARE_HOLDINGS_ENDPOINTがAPI_BASE_URLで始まる(
        self,
    ) -> None:
        """CORPORATE_SHARE_HOLDINGS_ENDPOINT が API_BASE_URL で始まること。"""
        assert isinstance(CORPORATE_SHARE_HOLDINGS_ENDPOINT, str)
        assert CORPORATE_SHARE_HOLDINGS_ENDPOINT.startswith(API_BASE_URL)

    def test_正常系_CORPORATE_SHARE_HOLDINGS_ENDPOINTがhttpsで始まる(self) -> None:
        """CORPORATE_SHARE_HOLDINGS_ENDPOINT が https:// で始まること。"""
        assert CORPORATE_SHARE_HOLDINGS_ENDPOINT.startswith("https://")

    def test_正常系_CORPORATE_SHARE_HOLDINGS_ENDPOINTがcorporate_share_holdingsを含む(
        self,
    ) -> None:
        """CORPORATE_SHARE_HOLDINGS_ENDPOINT に corporate-share-holdings を含むこと。"""
        assert "corporate-share-holdings" in CORPORATE_SHARE_HOLDINGS_ENDPOINT

    def test_正常系_CORPORATE_SHARE_HOLDINGS_ENDPOINTがAPI_BASE_URLを結合して生成される(
        self,
    ) -> None:
        """CORPORATE_SHARE_HOLDINGS_ENDPOINT が API_BASE_URL から正しく組み立てられること。"""
        assert (
            f"{API_BASE_URL}/corporate-share-holdings-master"
        ) == CORPORATE_SHARE_HOLDINGS_ENDPOINT


# =============================================================================
# XBRL namespace constants
# =============================================================================


class TestXBRLNamespaceConstants:
    """Test XBRL namespace constants for corporate shareholding parsing."""

    def test_正常系_XBRL_SHP_NSが空でない文字列である(self) -> None:
        """XBRL_SHP_NS が空でない文字列であること。"""
        assert isinstance(XBRL_SHP_NS, str)
        assert len(XBRL_SHP_NS.strip()) > 0

    def test_正常系_XBRL_SHP_NSがURLフォーマットである(self) -> None:
        """XBRL_SHP_NS が URL フォーマットであること（http/https プレフィックス）。"""
        assert XBRL_SHP_NS.startswith("http")

    def test_正常系_XBRLI_NSが空でない文字列である(self) -> None:
        """XBRLI_NS が空でない文字列であること。"""
        assert isinstance(XBRLI_NS, str)
        assert len(XBRLI_NS.strip()) > 0

    def test_正常系_XBRLI_NSがxbrl_orgドメインを含む(self) -> None:
        """XBRLI_NS が xbrl.org ドメインを含むこと。"""
        assert "xbrl.org" in XBRLI_NS

    def test_正常系_XBRLDI_NSが空でない文字列である(self) -> None:
        """XBRLDI_NS が空でない文字列であること。"""
        assert isinstance(XBRLDI_NS, str)
        assert len(XBRLDI_NS.strip()) > 0

    def test_正常系_XBRLDI_NSがxbrl_orgドメインを含む(self) -> None:
        """XBRLDI_NS が xbrl.org ドメインを含むこと。"""
        assert "xbrl.org" in XBRLDI_NS

    def test_正常系_3つのXBRL定数が互いに異なる(self) -> None:
        """XBRL_SHP_NS / XBRLI_NS / XBRLDI_NS が互いに異なる値であること。"""
        namespaces = {XBRL_SHP_NS, XBRLI_NS, XBRLDI_NS}
        assert len(namespaces) == 3


# =============================================================================
# Security constants
# =============================================================================


class TestSecurityConstants:
    """Test SSRF prevention constants."""

    def test_正常系_ALLOWED_HOSTSがfrozensetである(self) -> None:
        """ALLOWED_HOSTS が frozenset であること。"""
        assert isinstance(ALLOWED_HOSTS, frozenset)

    def test_正常系_ALLOWED_HOSTSにwww_nseindiaが含まれる(self) -> None:
        """ALLOWED_HOSTS に www.nseindia.com が含まれること。"""
        assert "www.nseindia.com" in ALLOWED_HOSTS

    def test_正常系_ALLOWED_HOSTSにnsearchivesが含まれる(self) -> None:
        """ALLOWED_HOSTS に nsearchives.nseindia.com が含まれること。"""
        assert "nsearchives.nseindia.com" in ALLOWED_HOSTS

    def test_正常系_ALLOWED_HOSTSが2件含む(self) -> None:
        """ALLOWED_HOSTS が2つのホストを含むこと（www + nsearchives）。"""
        assert len(ALLOWED_HOSTS) == 2


# =============================================================================
# Bot-blocking countermeasure constants
# =============================================================================


class TestBotBlockingConstants:
    """Test bot-blocking countermeasure constants."""

    def test_正常系_DEFAULT_USER_AGENTSが12件含む(self) -> None:
        """DEFAULT_USER_AGENTS が12種類のUser-Agent文字列を含むこと。"""
        assert isinstance(DEFAULT_USER_AGENTS, list)
        assert len(DEFAULT_USER_AGENTS) == 12

    def test_正常系_各UserAgentにMozillaが含まれる(self) -> None:
        """全User-AgentにMozillaプレフィックスが含まれること。"""
        for ua in DEFAULT_USER_AGENTS:
            assert "Mozilla" in ua, f"User-Agent does not contain 'Mozilla': {ua}"

    def test_正常系_UserAgent文字列が空でない(self) -> None:
        """全User-Agent文字列が空文字列でないこと。"""
        for ua in DEFAULT_USER_AGENTS:
            assert isinstance(ua, str)
            assert len(ua.strip()) > 0

    def test_正常系_UserAgentが重複していない(self) -> None:
        """User-Agent文字列に重複がないこと。"""
        assert len(DEFAULT_USER_AGENTS) == len(set(DEFAULT_USER_AGENTS))

    def test_正常系_DEFAULT_POLITE_DELAYが正の浮動小数点数(self) -> None:
        """DEFAULT_POLITE_DELAY が正の float (0.5) であること。"""
        assert isinstance(DEFAULT_POLITE_DELAY, float)
        assert DEFAULT_POLITE_DELAY > 0
        assert DEFAULT_POLITE_DELAY == 0.5

    def test_正常系_DEFAULT_TIMEOUTが正の浮動小数点数(self) -> None:
        """DEFAULT_TIMEOUT が正の float (30.0) であること。"""
        assert isinstance(DEFAULT_TIMEOUT, float)
        assert DEFAULT_TIMEOUT > 0
        assert DEFAULT_TIMEOUT == 30.0

    def test_正常系_DEFAULT_DELAY_JITTERが正の浮動小数点数(self) -> None:
        """DEFAULT_DELAY_JITTER が正の float (0.1) であること。"""
        assert isinstance(DEFAULT_DELAY_JITTER, float)
        assert DEFAULT_DELAY_JITTER > 0
        assert DEFAULT_DELAY_JITTER == 0.1


# =============================================================================
# Session management constants
# =============================================================================


class TestSessionManagementConstants:
    """Test session management constants."""

    def test_正常系_COOKIE_REFRESH_INTERVALが正の浮動小数点数(self) -> None:
        """COOKIE_REFRESH_INTERVAL が正の float (300.0) であること。"""
        assert isinstance(COOKIE_REFRESH_INTERVAL, float)
        assert COOKIE_REFRESH_INTERVAL > 0
        assert COOKIE_REFRESH_INTERVAL == 300.0

    def test_正常系_COOKIE_REFRESH_INTERVALが5分相当(self) -> None:
        """COOKIE_REFRESH_INTERVAL が 5分（300秒）相当であること。"""
        assert COOKIE_REFRESH_INTERVAL == 300.0


# =============================================================================
# HTTP Headers constants
# =============================================================================


class TestHTTPHeaderConstants:
    """Test default HTTP header constants."""

    def test_正常系_DEFAULT_HEADERSが必須ヘッダーを含む(self) -> None:
        """DEFAULT_HEADERS が必須ヘッダーを全て含むこと。"""
        assert isinstance(DEFAULT_HEADERS, dict)
        assert "User-Agent" in DEFAULT_HEADERS
        assert "Accept" in DEFAULT_HEADERS
        assert "Accept-Language" in DEFAULT_HEADERS
        assert "Accept-Encoding" in DEFAULT_HEADERS
        assert "Referer" in DEFAULT_HEADERS
        assert "X-Requested-With" in DEFAULT_HEADERS

    def test_正常系_DEFAULT_HEADERSの値が空でない(self) -> None:
        """DEFAULT_HEADERS の各値が空文字列でないこと。"""
        for key, value in DEFAULT_HEADERS.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(value.strip()) > 0, f"Header {key} has empty value"

    def test_正常系_DEFAULT_HEADERSのAcceptがJSONを含む(self) -> None:
        """DEFAULT_HEADERS の Accept が application/json を含むこと。"""
        assert "application/json" in DEFAULT_HEADERS["Accept"]

    def test_正常系_DEFAULT_HEADERSのUserAgentにMozillaが含まれる(self) -> None:
        """DEFAULT_HEADERS の User-Agent に Mozilla が含まれること。"""
        assert "Mozilla" in DEFAULT_HEADERS["User-Agent"]

    def test_正常系_DEFAULT_HEADERSのRefererがnseindiaを含む(self) -> None:
        """DEFAULT_HEADERS の Referer が nseindia.com を含むこと。"""
        assert "nseindia.com" in DEFAULT_HEADERS["Referer"]

    def test_正常系_DEFAULT_HEADERSのXRequestedWithがXMLHttpRequest(self) -> None:
        """DEFAULT_HEADERS の X-Requested-With が XMLHttpRequest であること。"""
        assert DEFAULT_HEADERS["X-Requested-With"] == "XMLHttpRequest"


# =============================================================================
# Output directory constants
# =============================================================================


class TestOutputConstants:
    """Test output directory constants."""

    def test_正常系_DEFAULT_OUTPUT_SUBDIRが空でない文字列(self) -> None:
        """DEFAULT_OUTPUT_SUBDIR が空でない文字列であること。"""
        assert isinstance(DEFAULT_OUTPUT_SUBDIR, str)
        assert len(DEFAULT_OUTPUT_SUBDIR.strip()) > 0

    def test_正常系_DEFAULT_OUTPUT_SUBDIRがraw_を含む(self) -> None:
        """DEFAULT_OUTPUT_SUBDIR が raw/ パスを含むこと。"""
        assert "raw/" in DEFAULT_OUTPUT_SUBDIR

    def test_正常系_DEFAULT_OUTPUT_SUBDIRがnseを含む(self) -> None:
        """DEFAULT_OUTPUT_SUBDIR が nse を含むこと。"""
        assert "nse" in DEFAULT_OUTPUT_SUBDIR

    def test_正常系_DEFAULT_OUTPUT_SUBDIRが正しい値(self) -> None:
        """DEFAULT_OUTPUT_SUBDIR が設計通りの値であること。"""
        assert DEFAULT_OUTPUT_SUBDIR == "raw/nse"


# =============================================================================
# Column name mapping constants
# =============================================================================


class TestEquityQuoteColumnNameMap:
    """Test equity quote column name mapping constants."""

    def test_正常系_EQUITY_QUOTE_COLUMN_NAME_MAPがdictである(self) -> None:
        """EQUITY_QUOTE_COLUMN_NAME_MAP が dict であること。"""
        assert isinstance(EQUITY_QUOTE_COLUMN_NAME_MAP, dict)

    def test_正常系_EQUITY_QUOTE_COLUMN_NAME_MAPが主要カラムを含む(self) -> None:
        """EQUITY_QUOTE_COLUMN_NAME_MAP が主要レスポンスカラムをマッピングすること。"""
        expected_keys = {
            "symbol",
            "companyName",
            "series",
            "lastPrice",
            "change",
            "pChange",
            "previousClose",
            "open",
            "close",
            "totalTradedVolume",
            "totalTradedValue",
            "yearHigh",
            "yearLow",
        }
        assert expected_keys.issubset(set(EQUITY_QUOTE_COLUMN_NAME_MAP.keys()))

    def test_正常系_EQUITY_QUOTE_COLUMN_NAME_MAPの値がsnake_caseである(self) -> None:
        """EQUITY_QUOTE_COLUMN_NAME_MAP の値が snake_case 形式であること。"""
        for key, value in EQUITY_QUOTE_COLUMN_NAME_MAP.items():
            assert isinstance(value, str)
            assert len(value.strip()) > 0, f"Mapping for {key} is empty"
            assert value == value.lower(), (
                f"Value '{value}' for key '{key}' is not lowercase"
            )
            assert " " not in value, f"Value '{value}' for key '{key}' contains spaces"

    def test_正常系_EQUITY_QUOTE_COLUMN_NAME_MAPのlastPriceがlast_priceにマッピング(
        self,
    ) -> None:
        """EQUITY_QUOTE_COLUMN_NAME_MAP の lastPrice が last_price にマッピングされること。"""
        assert EQUITY_QUOTE_COLUMN_NAME_MAP["lastPrice"] == "last_price"

    def test_正常系_EQUITY_QUOTE_COLUMN_NAME_MAPのpreviousCloseがprev_closeにマッピング(
        self,
    ) -> None:
        """EQUITY_QUOTE_COLUMN_NAME_MAP の previousClose が prev_close にマッピングされること。"""
        assert EQUITY_QUOTE_COLUMN_NAME_MAP["previousClose"] == "prev_close"

    def test_正常系_EQUITY_QUOTE_COLUMN_NAME_MAPのpChangeがpct_changeにマッピング(
        self,
    ) -> None:
        """EQUITY_QUOTE_COLUMN_NAME_MAP の pChange が pct_change にマッピングされること。"""
        assert EQUITY_QUOTE_COLUMN_NAME_MAP["pChange"] == "pct_change"


class TestIndexConstituentsColumnNameMap:
    """Test index constituents column name mapping constants."""

    def test_正常系_INDEX_CONSTITUENTS_COLUMN_NAME_MAPがdictである(self) -> None:
        """INDEX_CONSTITUENTS_COLUMN_NAME_MAP が dict であること。"""
        assert isinstance(INDEX_CONSTITUENTS_COLUMN_NAME_MAP, dict)

    def test_正常系_INDEX_CONSTITUENTS_COLUMN_NAME_MAPが主要カラムを含む(self) -> None:
        """INDEX_CONSTITUENTS_COLUMN_NAME_MAP が主要カラムをマッピングすること。"""
        expected_keys = {
            "symbol",
            "lastPrice",
            "previousClose",
            "change",
            "pChange",
            "totalTradedVolume",
            "yearHigh",
            "yearLow",
        }
        assert expected_keys.issubset(set(INDEX_CONSTITUENTS_COLUMN_NAME_MAP.keys()))

    def test_正常系_INDEX_CONSTITUENTS_COLUMN_NAME_MAPの値がsnake_caseである(
        self,
    ) -> None:
        """INDEX_CONSTITUENTS_COLUMN_NAME_MAP の値が snake_case 形式であること。"""
        for key, value in INDEX_CONSTITUENTS_COLUMN_NAME_MAP.items():
            assert isinstance(value, str)
            assert len(value.strip()) > 0, f"Mapping for {key} is empty"
            assert value == value.lower(), (
                f"Value '{value}' for key '{key}' is not lowercase"
            )
            assert " " not in value, f"Value '{value}' for key '{key}' contains spaces"

    def test_正常系_dayHighがday_highにマッピング(self) -> None:
        """INDEX_CONSTITUENTS_COLUMN_NAME_MAP の dayHigh が day_high にマッピングされること。"""
        assert INDEX_CONSTITUENTS_COLUMN_NAME_MAP["dayHigh"] == "day_high"

    def test_正常系_perChange365dがpct_change_365dにマッピング(self) -> None:
        """perChange365d が pct_change_365d にマッピングされること。"""
        assert INDEX_CONSTITUENTS_COLUMN_NAME_MAP["perChange365d"] == "pct_change_365d"


class TestFinancialResultColumnNameMap:
    """Test financial result column name mapping constants."""

    def test_正常系_FINANCIAL_RESULT_COLUMN_NAME_MAPがdictである(self) -> None:
        """FINANCIAL_RESULT_COLUMN_NAME_MAP が dict であること。"""
        assert isinstance(FINANCIAL_RESULT_COLUMN_NAME_MAP, dict)

    def test_正常系_FINANCIAL_RESULT_COLUMN_NAME_MAPが主要カラムを含む(self) -> None:
        """FINANCIAL_RESULT_COLUMN_NAME_MAP が主要カラムをマッピングすること。"""
        expected_keys = {
            "symbol",
            "fromDate",
            "toDate",
            "income",
            "profitAfterTax",
            "eps",
        }
        assert expected_keys.issubset(set(FINANCIAL_RESULT_COLUMN_NAME_MAP.keys()))

    def test_正常系_fromDateがfrom_dateにマッピング(self) -> None:
        """fromDate が from_date にマッピングされること。"""
        assert FINANCIAL_RESULT_COLUMN_NAME_MAP["fromDate"] == "from_date"

    def test_正常系_profitAfterTaxがprofit_after_taxにマッピング(self) -> None:
        """profitAfterTax が profit_after_tax にマッピングされること。"""
        assert FINANCIAL_RESULT_COLUMN_NAME_MAP["profitAfterTax"] == "profit_after_tax"


# =============================================================================
# Final type annotations
# =============================================================================


class TestFinalAnnotations:
    """Test that all constants have Final type annotations."""

    def test_正常系_全定数にFinal型アノテーションが付与されている(self) -> None:
        """__all__ の全定数に typing.Final アノテーションが付与されていること。"""
        from market.nse import constants

        annotations = get_type_hints(constants, include_extras=True)

        for name in __all__:
            assert name in annotations, (
                f"{name} does not have a type annotation in the module"
            )
            annotation_str = str(annotations[name])
            assert "Final" in annotation_str, (
                f"{name} is not annotated with Final. Got: {annotation_str}"
            )
