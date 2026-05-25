"""Tests for ``market.fraser.constants`` module."""

from typing import Final, get_type_hints

from market.fraser import constants
from market.fraser.constants import (
    ALLOWED_HOSTS,
    BASE_URL,
    DEFAULT_REQUESTS_PER_HOUR,
    DEFAULT_REQUESTS_PER_MINUTE,
    DEFAULT_TIMEOUT,
    DOC_TYPE_SUBDIRS,
    FRASER_API_KEY_ENV,
    KNOWN_TITLE_IDS,
    MAX_RESPONSE_BODY_LOG,
)


class TestBaseUrl:
    """Tests for ``BASE_URL``."""

    def test_正常系_URLが正しい値(self) -> None:
        assert BASE_URL == "https://fraser.stlouisfed.org/api"

    def test_正常系_httpsスキーム(self) -> None:
        assert BASE_URL.startswith("https://")


class TestAllowedHosts:
    """Tests for ``ALLOWED_HOSTS``."""

    def test_正常系_frozensetである(self) -> None:
        assert isinstance(ALLOWED_HOSTS, frozenset)

    def test_正常系_fraserホストを含む(self) -> None:
        assert "fraser.stlouisfed.org" in ALLOWED_HOSTS

    def test_正常系_他のホストを含まない(self) -> None:
        assert "evil.example.com" not in ALLOWED_HOSTS
        assert "www.alphavantage.co" not in ALLOWED_HOSTS

    def test_正常系_要素数が1(self) -> None:
        assert len(ALLOWED_HOSTS) == 1


class TestEnvironmentVariableNames:
    """Tests for environment variable name constants."""

    def test_正常系_APIキー環境変数名(self) -> None:
        assert FRASER_API_KEY_ENV == "FRASER_API_KEY"


class TestSecurityConstants:
    """Tests for security-related constants."""

    def test_正常系_レスポンスボディログ最大値(self) -> None:
        assert MAX_RESPONSE_BODY_LOG == 2048

    def test_正常系_レスポンスボディログ最大値は正の値(self) -> None:
        assert MAX_RESPONSE_BODY_LOG > 0


class TestRateLimitDefaults:
    """Tests for rate limit default constants."""

    def test_正常系_デフォルト毎分リクエスト数(self) -> None:
        assert DEFAULT_REQUESTS_PER_MINUTE == 30

    def test_正常系_デフォルト毎時リクエスト数(self) -> None:
        assert DEFAULT_REQUESTS_PER_HOUR == 1800

    def test_正常系_毎時は毎分の60倍(self) -> None:
        assert DEFAULT_REQUESTS_PER_HOUR == DEFAULT_REQUESTS_PER_MINUTE * 60


class TestHttpDefaults:
    """Tests for HTTP default configuration constants."""

    def test_正常系_デフォルトタイムアウト(self) -> None:
        assert DEFAULT_TIMEOUT == 30.0

    def test_正常系_タイムアウトは正の値(self) -> None:
        assert DEFAULT_TIMEOUT > 0


class TestKnownTitleIds:
    """Tests for ``KNOWN_TITLE_IDS``."""

    def test_正常系_FOMCMinutesのIDは677(self) -> None:
        assert KNOWN_TITLE_IDS["fomc_minutes"] == 677

    def test_正常系_6キーを持つ(self) -> None:
        assert len(KNOWN_TITLE_IDS) == 6
        assert set(KNOWN_TITLE_IDS.keys()) == {
            "fomc_minutes",
            "fomc_statements",
            "fomc_press_conferences",
            "beige_book",
            "monetary_policy_report",
            "frb_speeches",
        }

    def test_正常系_未確定キーはNone(self) -> None:
        for key in (
            "fomc_statements",
            "fomc_press_conferences",
            "beige_book",
            "monetary_policy_report",
            "frb_speeches",
        ):
            assert KNOWN_TITLE_IDS[key] is None


class TestDocTypeSubdirs:
    """Tests for ``DOC_TYPE_SUBDIRS``."""

    def test_正常系_6キーを持つ(self) -> None:
        assert len(DOC_TYPE_SUBDIRS) == 6

    def test_正常系_キーがKNOWN_TITLE_IDSと一致(self) -> None:
        assert set(DOC_TYPE_SUBDIRS.keys()) == set(KNOWN_TITLE_IDS.keys())

    def test_正常系_FOMCMinutesのサブディレクトリ(self) -> None:
        assert DOC_TYPE_SUBDIRS["fomc_minutes"] == "fomc/minutes"

    def test_正常系_BeigeBookのサブディレクトリ(self) -> None:
        assert DOC_TYPE_SUBDIRS["beige_book"] == "beige_book"

    def test_正常系_全サブディレクトリが空でない文字列(self) -> None:
        for value in DOC_TYPE_SUBDIRS.values():
            assert isinstance(value, str)
            assert len(value) > 0


class TestFinalAnnotations:
    """Tests that all module constants are annotated with ``Final``."""

    def test_正常系_全定数がFinal宣言(self) -> None:
        """Verify each public constant uses ``typing.Final`` in its annotation.

        ``typing.get_type_hints(include_extras=True)`` returns the
        evaluated annotation expressions. For ``Final[X]`` the typing
        origin is ``Final``. Asserting on the origin catches the
        regression where someone strips the ``Final`` wrapper.
        """
        hints = get_type_hints(constants, include_extras=True)
        expected_names = {
            "BASE_URL",
            "ALLOWED_HOSTS",
            "MAX_RESPONSE_BODY_LOG",
            "FRASER_API_KEY_ENV",
            "DEFAULT_REQUESTS_PER_MINUTE",
            "DEFAULT_REQUESTS_PER_HOUR",
            "DEFAULT_TIMEOUT",
            "KNOWN_TITLE_IDS",
            "DOC_TYPE_SUBDIRS",
        }
        for name in expected_names:
            assert name in hints, f"{name} missing from module hints"
            hint = hints[name]
            # ``Final[X]`` exposes its parametrisation via __origin__.
            origin = getattr(hint, "__origin__", None)
            assert origin is Final, f"{name} is not annotated as Final, got {hint!r}"


class TestAllExports:
    """Tests for ``__all__`` completeness."""

    def test_正常系_allが定義されている(self) -> None:
        assert hasattr(constants, "__all__")

    def test_正常系_全定数がallに含まれる(self) -> None:
        expected = {
            "ALLOWED_HOSTS",
            "BASE_URL",
            "DEFAULT_REQUESTS_PER_HOUR",
            "DEFAULT_REQUESTS_PER_MINUTE",
            "DEFAULT_TIMEOUT",
            "DOC_TYPE_SUBDIRS",
            "FRASER_API_KEY_ENV",
            "KNOWN_TITLE_IDS",
            "MAX_RESPONSE_BODY_LOG",
        }
        assert set(constants.__all__) == expected
