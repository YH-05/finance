"""Tests for market.etfcom.constants module.

Tests verify all constant definitions for the ETF.com scraping module,
including bot-blocking countermeasure constants, URL patterns, CSS selectors,
and Playwright stealth settings.
"""

from typing import Final, get_type_hints

import pytest


class TestModuleExports:
    """Test module __all__ exports and structure."""

    def test_正常系_モジュールがインポートできる(self) -> None:
        from market.etfcom import constants

        assert constants is not None

    def test_正常系_allが定義されている(self) -> None:
        from market.etfcom.constants import __all__

        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_正常系_allの全項目がモジュールに存在する(self) -> None:
        from market.etfcom import constants
        from market.etfcom.constants import __all__

        for name in __all__:
            assert hasattr(constants, name), (
                f"{name} is not defined in constants module"
            )

    def test_正常系_モジュールDocstringが存在する(self) -> None:
        from market.etfcom import constants

        assert constants.__doc__ is not None
        assert len(constants.__doc__) > 0


class TestBotBlockingConstants:
    """Test bot-blocking countermeasure constants."""

    def test_正常系_DEFAULT_USER_AGENTSが10種類以上含む(self) -> None:
        from market.etfcom.constants import DEFAULT_USER_AGENTS

        assert isinstance(DEFAULT_USER_AGENTS, list)
        assert len(DEFAULT_USER_AGENTS) >= 10

    def test_正常系_各UserAgentにMozillaが含まれる(self) -> None:
        from market.etfcom.constants import DEFAULT_USER_AGENTS

        for ua in DEFAULT_USER_AGENTS:
            assert "Mozilla" in ua, f"User-Agent does not contain 'Mozilla': {ua}"

    def test_正常系_UserAgent文字列が空でない(self) -> None:
        from market.etfcom.constants import DEFAULT_USER_AGENTS

        for ua in DEFAULT_USER_AGENTS:
            assert isinstance(ua, str)
            assert len(ua.strip()) > 0

    def test_正常系_UserAgentが重複していない(self) -> None:
        from market.etfcom.constants import DEFAULT_USER_AGENTS

        assert len(DEFAULT_USER_AGENTS) == len(set(DEFAULT_USER_AGENTS))

    def test_正常系_BROWSER_IMPERSONATE_TARGETSが5種類以上含む(self) -> None:
        from market.etfcom.constants import BROWSER_IMPERSONATE_TARGETS

        assert isinstance(BROWSER_IMPERSONATE_TARGETS, list)
        assert len(BROWSER_IMPERSONATE_TARGETS) >= 5

    def test_正常系_BROWSER_IMPERSONATE_TARGETSが空文字列を含まない(self) -> None:
        from market.etfcom.constants import BROWSER_IMPERSONATE_TARGETS

        for target in BROWSER_IMPERSONATE_TARGETS:
            assert isinstance(target, str)
            assert len(target.strip()) > 0

    def test_正常系_DEFAULT_POLITE_DELAYが正の浮動小数点数(self) -> None:
        from market.etfcom.constants import DEFAULT_POLITE_DELAY

        assert isinstance(DEFAULT_POLITE_DELAY, float)
        assert DEFAULT_POLITE_DELAY > 0
        assert DEFAULT_POLITE_DELAY == 2.0

    def test_正常系_DEFAULT_DELAY_JITTERが正の浮動小数点数(self) -> None:
        from market.etfcom.constants import DEFAULT_DELAY_JITTER

        assert isinstance(DEFAULT_DELAY_JITTER, float)
        assert DEFAULT_DELAY_JITTER > 0
        assert DEFAULT_DELAY_JITTER == 1.0

    def test_正常系_DEFAULT_TIMEOUTが正の浮動小数点数(self) -> None:
        from market.etfcom.constants import DEFAULT_TIMEOUT

        assert isinstance(DEFAULT_TIMEOUT, float)
        assert DEFAULT_TIMEOUT > 0
        assert DEFAULT_TIMEOUT == 30.0

    def test_正常系_DEFAULT_HEADERSが必須ヘッダーを含む(self) -> None:
        from market.etfcom.constants import DEFAULT_HEADERS

        assert isinstance(DEFAULT_HEADERS, dict)
        assert "Accept" in DEFAULT_HEADERS
        assert "Accept-Language" in DEFAULT_HEADERS
        assert "Accept-Encoding" in DEFAULT_HEADERS
        assert "Connection" in DEFAULT_HEADERS

    def test_正常系_DEFAULT_HEADERSの値が空でない(self) -> None:
        from market.etfcom.constants import DEFAULT_HEADERS

        for key, value in DEFAULT_HEADERS.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(value.strip()) > 0


class TestPlaywrightStealthConstants:
    """Test Playwright stealth configuration constants."""

    def test_正常系_STEALTH_VIEWPORTがwidthとheightを含む(self) -> None:
        from market.etfcom.constants import STEALTH_VIEWPORT

        assert isinstance(STEALTH_VIEWPORT, dict)
        assert "width" in STEALTH_VIEWPORT
        assert "height" in STEALTH_VIEWPORT
        assert STEALTH_VIEWPORT["width"] == 1920
        assert STEALTH_VIEWPORT["height"] == 1080

    def test_正常系_STEALTH_VIEWPORTの値が正の整数(self) -> None:
        from market.etfcom.constants import STEALTH_VIEWPORT

        for _key, value in STEALTH_VIEWPORT.items():
            assert isinstance(value, int)
            assert value > 0

    def test_正常系_STEALTH_INIT_SCRIPTが空でない(self) -> None:
        from market.etfcom.constants import STEALTH_INIT_SCRIPT

        assert isinstance(STEALTH_INIT_SCRIPT, str)
        assert len(STEALTH_INIT_SCRIPT.strip()) > 0

    def test_正常系_STEALTH_INIT_SCRIPTがwebdriver偽装を含む(self) -> None:
        from market.etfcom.constants import STEALTH_INIT_SCRIPT

        assert "webdriver" in STEALTH_INIT_SCRIPT

    def test_正常系_STEALTH_INIT_SCRIPTがWebGL偽装を含む(self) -> None:
        from market.etfcom.constants import STEALTH_INIT_SCRIPT

        assert "WebGL" in STEALTH_INIT_SCRIPT or "webgl" in STEALTH_INIT_SCRIPT.lower()

    def test_正常系_STEALTH_INIT_SCRIPTがchrome_runtime偽装を含む(self) -> None:
        from market.etfcom.constants import STEALTH_INIT_SCRIPT

        assert "chrome" in STEALTH_INIT_SCRIPT.lower()


class TestURLConstants:
    """Test URL pattern constants."""

    def test_正常系_ETFCOM_BASE_URLがhttpsで始まる(self) -> None:
        from market.etfcom.constants import ETFCOM_BASE_URL

        assert isinstance(ETFCOM_BASE_URL, str)
        assert ETFCOM_BASE_URL.startswith("https://")

    def test_正常系_SCREENER_URLがhttpsで始まる(self) -> None:
        from market.etfcom.constants import SCREENER_URL

        assert isinstance(SCREENER_URL, str)
        assert SCREENER_URL.startswith("https://")

    def test_正常系_PROFILE_URL_TEMPLATEがhttpsで始まる(self) -> None:
        from market.etfcom.constants import PROFILE_URL_TEMPLATE

        assert isinstance(PROFILE_URL_TEMPLATE, str)
        assert PROFILE_URL_TEMPLATE.startswith("https://")

    def test_正常系_FUND_FLOWS_URL_TEMPLATEがhttpsで始まる(self) -> None:
        from market.etfcom.constants import FUND_FLOWS_URL_TEMPLATE

        assert isinstance(FUND_FLOWS_URL_TEMPLATE, str)
        assert FUND_FLOWS_URL_TEMPLATE.startswith("https://")

    def test_正常系_URLテンプレートにプレースホルダーが含まれる(self) -> None:
        from market.etfcom.constants import (
            FUND_FLOWS_URL_TEMPLATE,
            PROFILE_URL_TEMPLATE,
        )

        # URL templates should contain format placeholders
        assert "{" in PROFILE_URL_TEMPLATE
        assert "{" in FUND_FLOWS_URL_TEMPLATE

    def test_正常系_ETFCOM_BASE_URLがetfcomドメインを含む(self) -> None:
        from market.etfcom.constants import ETFCOM_BASE_URL

        assert "etf.com" in ETFCOM_BASE_URL


class TestCSSSelectorConstants:
    """Test CSS selector constants."""

    def test_正常系_SUMMARY_DATA_IDが空でない(self) -> None:
        from market.etfcom.constants import SUMMARY_DATA_ID

        assert isinstance(SUMMARY_DATA_ID, str)
        assert len(SUMMARY_DATA_ID.strip()) > 0

    def test_正常系_CLASSIFICATION_DATA_IDが空でない(self) -> None:
        from market.etfcom.constants import CLASSIFICATION_DATA_ID

        assert isinstance(CLASSIFICATION_DATA_ID, str)
        assert len(CLASSIFICATION_DATA_ID.strip()) > 0

    def test_正常系_FLOW_TABLE_IDが空でない(self) -> None:
        from market.etfcom.constants import FLOW_TABLE_ID

        assert isinstance(FLOW_TABLE_ID, str)
        assert len(FLOW_TABLE_ID.strip()) > 0

    def test_正常系_COOKIE_CONSENT_SELECTORが空でない(self) -> None:
        from market.etfcom.constants import COOKIE_CONSENT_SELECTOR

        assert isinstance(COOKIE_CONSENT_SELECTOR, str)
        assert len(COOKIE_CONSENT_SELECTOR.strip()) > 0

    def test_正常系_DISPLAY_100_SELECTORが空でない(self) -> None:
        from market.etfcom.constants import DISPLAY_100_SELECTOR

        assert isinstance(DISPLAY_100_SELECTOR, str)
        assert len(DISPLAY_100_SELECTOR.strip()) > 0

    def test_正常系_NEXT_PAGE_SELECTORが空でない(self) -> None:
        from market.etfcom.constants import NEXT_PAGE_SELECTOR

        assert isinstance(NEXT_PAGE_SELECTOR, str)
        assert len(NEXT_PAGE_SELECTOR.strip()) > 0


class TestDefaultSettings:
    """Test default configuration constants."""

    def test_正常系_DEFAULT_STABILITY_WAITが正の数値(self) -> None:
        from market.etfcom.constants import DEFAULT_STABILITY_WAIT

        assert isinstance(DEFAULT_STABILITY_WAIT, (int, float))
        assert DEFAULT_STABILITY_WAIT > 0

    def test_正常系_DEFAULT_MAX_RETRIESが正の整数(self) -> None:
        from market.etfcom.constants import DEFAULT_MAX_RETRIES

        assert isinstance(DEFAULT_MAX_RETRIES, int)
        assert DEFAULT_MAX_RETRIES > 0


class TestFinalAnnotations:
    """Test that all constants have Final type annotations."""

    def test_正常系_全定数にFinal型アノテーションが付与されている(self) -> None:
        """Verify all exported constants have Final type annotations.

        This test checks the module's type annotations to ensure all
        constants in __all__ are annotated with typing.Final.
        """
        from market.etfcom import constants
        from market.etfcom.constants import __all__

        annotations = get_type_hints(constants, include_extras=True)

        for name in __all__:
            assert name in annotations, (
                f"{name} does not have a type annotation in the module"
            )
            annotation_str = str(annotations[name])
            assert "Final" in annotation_str, (
                f"{name} is not annotated with Final. Got: {annotation_str}"
            )
