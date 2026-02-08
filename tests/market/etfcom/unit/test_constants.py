"""Tests for market.etfcom.constants module.

Tests verify all constant definitions for the ETF.com scraping module,
including bot-blocking countermeasure constants, URL patterns, CSS selectors,
and Playwright stealth settings.

Test TODO List:
- [x] Module exports: __all__ completeness and importability
- [x] Bot-blocking: DEFAULT_USER_AGENTS count, Mozilla prefix, uniqueness
- [x] Bot-blocking: BROWSER_IMPERSONATE_TARGETS count and non-empty
- [x] Bot-blocking: delay/timeout/headers values
- [x] Playwright stealth: viewport, init script content
- [x] URLs: https prefix, template placeholders, domain
- [x] CSS selectors: all selectors non-empty
- [x] Default settings: stability wait and max retries
- [x] Final annotations: all constants annotated with typing.Final
"""

from typing import get_type_hints

from market.etfcom.constants import (
    BROWSER_IMPERSONATE_TARGETS,
    CLASSIFICATION_DATA_ID,
    COOKIE_CONSENT_SELECTOR,
    DEFAULT_DELAY_JITTER,
    DEFAULT_HEADERS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_POLITE_DELAY,
    DEFAULT_STABILITY_WAIT,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENTS,
    DISPLAY_100_SELECTOR,
    ETFCOM_BASE_URL,
    FLOW_TABLE_ID,
    FUND_FLOWS_URL_TEMPLATE,
    NEXT_PAGE_SELECTOR,
    PROFILE_URL_TEMPLATE,
    SCREENER_URL,
    STEALTH_INIT_SCRIPT,
    STEALTH_VIEWPORT,
    SUMMARY_DATA_ID,
    __all__,
)

# =============================================================================
# Module exports
# =============================================================================


class TestModuleExports:
    """Test module __all__ exports and structure."""

    def test_正常系_モジュールがインポートできる(self) -> None:
        """constants モジュールが正常にインポートできること。"""
        from market.etfcom import constants

        assert constants is not None

    def test_正常系_allが定義されている(self) -> None:
        """__all__ がリストとして定義されていること。"""
        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_正常系_allの全項目がモジュールに存在する(self) -> None:
        """__all__ の全項目がモジュールの属性として存在すること。"""
        from market.etfcom import constants

        for name in __all__:
            assert hasattr(constants, name), (
                f"{name} is not defined in constants module"
            )

    def test_正常系_allが20項目を含む(self) -> None:
        """__all__ が全20定数をエクスポートしていること。"""
        assert len(__all__) == 20

    def test_正常系_モジュールDocstringが存在する(self) -> None:
        """モジュールの docstring が存在すること。"""
        from market.etfcom import constants

        assert constants.__doc__ is not None
        assert len(constants.__doc__) > 0


# =============================================================================
# Bot-blocking countermeasure constants
# =============================================================================


class TestBotBlockingConstants:
    """Test bot-blocking countermeasure constants."""

    def test_正常系_DEFAULT_USER_AGENTSが12件含む(self) -> None:
        """DEFAULT_USER_AGENTS が12種類のUser-Agent文字列を含むこと。"""
        assert isinstance(DEFAULT_USER_AGENTS, list)
        assert len(DEFAULT_USER_AGENTS) == 12

    def test_正常系_DEFAULT_USER_AGENTSが10種類以上含む(self) -> None:
        """DEFAULT_USER_AGENTS が10種類以上のUser-Agent文字列を含むこと。"""
        assert len(DEFAULT_USER_AGENTS) >= 10

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

    def test_正常系_BROWSER_IMPERSONATE_TARGETSが5種類以上含む(self) -> None:
        """BROWSER_IMPERSONATE_TARGETS が5種類以上含むこと。"""
        assert isinstance(BROWSER_IMPERSONATE_TARGETS, list)
        assert len(BROWSER_IMPERSONATE_TARGETS) >= 5

    def test_正常系_BROWSER_IMPERSONATE_TARGETSにchromeが含まれる(self) -> None:
        """BROWSER_IMPERSONATE_TARGETS にデフォルトの 'chrome' が含まれること。"""
        assert "chrome" in BROWSER_IMPERSONATE_TARGETS

    def test_正常系_BROWSER_IMPERSONATE_TARGETSが空文字列を含まない(self) -> None:
        """BROWSER_IMPERSONATE_TARGETS の各要素が空文字列でないこと。"""
        for target in BROWSER_IMPERSONATE_TARGETS:
            assert isinstance(target, str)
            assert len(target.strip()) > 0

    def test_正常系_DEFAULT_POLITE_DELAYが正の浮動小数点数(self) -> None:
        """DEFAULT_POLITE_DELAY が正の float (2.0) であること。"""
        assert isinstance(DEFAULT_POLITE_DELAY, float)
        assert DEFAULT_POLITE_DELAY > 0
        assert DEFAULT_POLITE_DELAY == 2.0

    def test_正常系_DEFAULT_DELAY_JITTERが正の浮動小数点数(self) -> None:
        """DEFAULT_DELAY_JITTER が正の float (1.0) であること。"""
        assert isinstance(DEFAULT_DELAY_JITTER, float)
        assert DEFAULT_DELAY_JITTER > 0
        assert DEFAULT_DELAY_JITTER == 1.0

    def test_正常系_DEFAULT_TIMEOUTが正の浮動小数点数(self) -> None:
        """DEFAULT_TIMEOUT が正の float (30.0) であること。"""
        assert isinstance(DEFAULT_TIMEOUT, float)
        assert DEFAULT_TIMEOUT > 0
        assert DEFAULT_TIMEOUT == 30.0

    def test_正常系_DEFAULT_HEADERSが必須ヘッダーを含む(self) -> None:
        """DEFAULT_HEADERS が Accept/Accept-Language/Accept-Encoding/Connection を含むこと。"""
        assert isinstance(DEFAULT_HEADERS, dict)
        assert "Accept" in DEFAULT_HEADERS
        assert "Accept-Language" in DEFAULT_HEADERS
        assert "Accept-Encoding" in DEFAULT_HEADERS
        assert "Connection" in DEFAULT_HEADERS

    def test_正常系_DEFAULT_HEADERSの値が空でない(self) -> None:
        """DEFAULT_HEADERS の各値が空文字列でないこと。"""
        for key, value in DEFAULT_HEADERS.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(value.strip()) > 0

    def test_正常系_DEFAULT_HEADERSにUserAgentが含まれない(self) -> None:
        """DEFAULT_HEADERS に User-Agent が含まれないこと（別途設定されるため）。"""
        assert "User-Agent" not in DEFAULT_HEADERS


# =============================================================================
# Playwright stealth constants
# =============================================================================


class TestPlaywrightStealthConstants:
    """Test Playwright stealth configuration constants."""

    def test_正常系_STEALTH_VIEWPORTがwidthとheightを含む(self) -> None:
        """STEALTH_VIEWPORT が width=1920, height=1080 であること。"""
        assert isinstance(STEALTH_VIEWPORT, dict)
        assert "width" in STEALTH_VIEWPORT
        assert "height" in STEALTH_VIEWPORT
        assert STEALTH_VIEWPORT["width"] == 1920
        assert STEALTH_VIEWPORT["height"] == 1080

    def test_正常系_STEALTH_VIEWPORTの値が正の整数(self) -> None:
        """STEALTH_VIEWPORT の各値が正の整数であること。"""
        for _key, value in STEALTH_VIEWPORT.items():
            assert isinstance(value, int)
            assert value > 0

    def test_正常系_STEALTH_INIT_SCRIPTが空でない(self) -> None:
        """STEALTH_INIT_SCRIPT が空でない文字列であること。"""
        assert isinstance(STEALTH_INIT_SCRIPT, str)
        assert len(STEALTH_INIT_SCRIPT.strip()) > 0

    def test_正常系_STEALTH_INIT_SCRIPTがwebdriver偽装を含む(self) -> None:
        """STEALTH_INIT_SCRIPT が navigator.webdriver 偽装コードを含むこと。"""
        assert "webdriver" in STEALTH_INIT_SCRIPT

    def test_正常系_STEALTH_INIT_SCRIPTがWebGL偽装を含む(self) -> None:
        """STEALTH_INIT_SCRIPT が WebGL vendor/renderer 偽装コードを含むこと。"""
        assert "WebGL" in STEALTH_INIT_SCRIPT or "webgl" in STEALTH_INIT_SCRIPT.lower()

    def test_正常系_STEALTH_INIT_SCRIPTがchrome_runtime偽装を含む(self) -> None:
        """STEALTH_INIT_SCRIPT が chrome.runtime 偽装コードを含むこと。"""
        assert "chrome" in STEALTH_INIT_SCRIPT.lower()

    def test_正常系_STEALTH_INIT_SCRIPTがJavaScriptとして有効な構造(self) -> None:
        """STEALTH_INIT_SCRIPT が JavaScript の基本構造を含むこと。"""
        # Object.defineProperty, prototype, window are common JS patterns
        assert "Object.defineProperty" in STEALTH_INIT_SCRIPT
        assert "window" in STEALTH_INIT_SCRIPT


# =============================================================================
# URL constants
# =============================================================================


class TestURLConstants:
    """Test URL pattern constants."""

    def test_正常系_ETFCOM_BASE_URLがhttpsで始まる(self) -> None:
        """ETFCOM_BASE_URL が https:// で始まること。"""
        assert isinstance(ETFCOM_BASE_URL, str)
        assert ETFCOM_BASE_URL.startswith("https://")

    def test_正常系_ETFCOM_BASE_URLがetfcomドメインを含む(self) -> None:
        """ETFCOM_BASE_URL が etf.com ドメインを含むこと。"""
        assert "etf.com" in ETFCOM_BASE_URL

    def test_正常系_SCREENER_URLがhttpsで始まる(self) -> None:
        """SCREENER_URL が https:// で始まること。"""
        assert isinstance(SCREENER_URL, str)
        assert SCREENER_URL.startswith("https://")

    def test_正常系_SCREENER_URLがBASE_URLから始まる(self) -> None:
        """SCREENER_URL が ETFCOM_BASE_URL を基にしていること。"""
        assert SCREENER_URL.startswith(ETFCOM_BASE_URL)

    def test_正常系_PROFILE_URL_TEMPLATEがhttpsで始まる(self) -> None:
        """PROFILE_URL_TEMPLATE が https:// で始まること。"""
        assert isinstance(PROFILE_URL_TEMPLATE, str)
        assert PROFILE_URL_TEMPLATE.startswith("https://")

    def test_正常系_PROFILE_URL_TEMPLATEにtickerプレースホルダーが含まれる(
        self,
    ) -> None:
        """PROFILE_URL_TEMPLATE に {ticker} プレースホルダーが含まれること。"""
        assert "{ticker}" in PROFILE_URL_TEMPLATE

    def test_正常系_PROFILE_URL_TEMPLATEをformatできる(self) -> None:
        """PROFILE_URL_TEMPLATE.format(ticker='SPY') が有効なURLを返すこと。"""
        url = PROFILE_URL_TEMPLATE.format(ticker="SPY")
        assert url == "https://www.etf.com/SPY"

    def test_正常系_FUND_FLOWS_URL_TEMPLATEがhttpsで始まる(self) -> None:
        """FUND_FLOWS_URL_TEMPLATE が https:// で始まること。"""
        assert isinstance(FUND_FLOWS_URL_TEMPLATE, str)
        assert FUND_FLOWS_URL_TEMPLATE.startswith("https://")

    def test_正常系_FUND_FLOWS_URL_TEMPLATEにtickerプレースホルダーが含まれる(
        self,
    ) -> None:
        """FUND_FLOWS_URL_TEMPLATE に {ticker} プレースホルダーが含まれること。"""
        assert "{ticker}" in FUND_FLOWS_URL_TEMPLATE

    def test_正常系_FUND_FLOWS_URL_TEMPLATEをformatできる(self) -> None:
        """FUND_FLOWS_URL_TEMPLATE.format(ticker='SPY') が有効なURLを返すこと。"""
        url = FUND_FLOWS_URL_TEMPLATE.format(ticker="SPY")
        assert url == "https://www.etf.com/SPY#702"


# =============================================================================
# CSS selector constants
# =============================================================================


class TestCSSSelectorConstants:
    """Test CSS selector constants."""

    def test_正常系_SUMMARY_DATA_IDが空でない(self) -> None:
        """SUMMARY_DATA_ID が空でない CSS セレクタであること。"""
        assert isinstance(SUMMARY_DATA_ID, str)
        assert len(SUMMARY_DATA_ID.strip()) > 0

    def test_正常系_SUMMARY_DATA_IDがdata_testidを含む(self) -> None:
        """SUMMARY_DATA_ID が data-testid セレクタであること。"""
        assert "data-testid" in SUMMARY_DATA_ID

    def test_正常系_CLASSIFICATION_DATA_IDが空でない(self) -> None:
        """CLASSIFICATION_DATA_ID が空でない CSS セレクタであること。"""
        assert isinstance(CLASSIFICATION_DATA_ID, str)
        assert len(CLASSIFICATION_DATA_ID.strip()) > 0

    def test_正常系_FLOW_TABLE_IDが空でない(self) -> None:
        """FLOW_TABLE_ID が空でない CSS セレクタであること。"""
        assert isinstance(FLOW_TABLE_ID, str)
        assert len(FLOW_TABLE_ID.strip()) > 0

    def test_正常系_COOKIE_CONSENT_SELECTORが空でない(self) -> None:
        """COOKIE_CONSENT_SELECTOR が空でない CSS セレクタであること。"""
        assert isinstance(COOKIE_CONSENT_SELECTOR, str)
        assert len(COOKIE_CONSENT_SELECTOR.strip()) > 0

    def test_正常系_DISPLAY_100_SELECTORが空でない(self) -> None:
        """DISPLAY_100_SELECTOR が空でない CSS セレクタであること。"""
        assert isinstance(DISPLAY_100_SELECTOR, str)
        assert len(DISPLAY_100_SELECTOR.strip()) > 0

    def test_正常系_NEXT_PAGE_SELECTORが空でない(self) -> None:
        """NEXT_PAGE_SELECTOR が空でない CSS セレクタであること。"""
        assert isinstance(NEXT_PAGE_SELECTOR, str)
        assert len(NEXT_PAGE_SELECTOR.strip()) > 0


# =============================================================================
# Default settings
# =============================================================================


class TestDefaultSettings:
    """Test default configuration constants."""

    def test_正常系_DEFAULT_STABILITY_WAITが正の数値(self) -> None:
        """DEFAULT_STABILITY_WAIT が正の数値であること。"""
        assert isinstance(DEFAULT_STABILITY_WAIT, (int, float))
        assert DEFAULT_STABILITY_WAIT > 0
        assert DEFAULT_STABILITY_WAIT == 2.0

    def test_正常系_DEFAULT_MAX_RETRIESが正の整数(self) -> None:
        """DEFAULT_MAX_RETRIES が正の整数であること。"""
        assert isinstance(DEFAULT_MAX_RETRIES, int)
        assert DEFAULT_MAX_RETRIES > 0
        assert DEFAULT_MAX_RETRIES == 3


# =============================================================================
# Final type annotations
# =============================================================================


class TestFinalAnnotations:
    """Test that all constants have Final type annotations."""

    def test_正常系_全定数にFinal型アノテーションが付与されている(self) -> None:
        """__all__ の全定数に typing.Final アノテーションが付与されていること。"""
        from market.etfcom import constants

        annotations = get_type_hints(constants, include_extras=True)

        for name in __all__:
            assert name in annotations, (
                f"{name} does not have a type annotation in the module"
            )
            annotation_str = str(annotations[name])
            assert "Final" in annotation_str, (
                f"{name} is not annotated with Final. Got: {annotation_str}"
            )
