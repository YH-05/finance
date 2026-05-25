"""Unit tests for ``market.fraser.types`` module.

Covers:

- ``FraserConfig`` default values, custom values, repr secrecy
  (CWE-532), ``__post_init__`` validation, frozen immutability.
- ``RetryConfig`` defaults and immutability.
- ``FetchOptions`` defaults and immutability.
- ``DocType`` member count, values, and ``str`` inheritance.
"""

from pathlib import Path

import pytest

from market.fraser.constants import (
    BASE_URL,
    DEFAULT_REQUESTS_PER_HOUR,
    DEFAULT_REQUESTS_PER_MINUTE,
    DEFAULT_TIMEOUT,
)
from market.fraser.errors import FraserValidationError
from market.fraser.types import (
    DocType,
    FetchOptions,
    FraserConfig,
    RetryConfig,
)

# =============================================================================
# RetryConfig Tests
# =============================================================================


class TestRetryConfig:
    """Tests for ``RetryConfig`` frozen dataclass."""

    def test_正常系_デフォルト値で生成できる(self) -> None:
        config = RetryConfig()
        assert config.max_attempts == 5
        assert config.base_wait == 1.0
        assert config.max_wait == 60.0

    def test_正常系_カスタム値で生成できる(self) -> None:
        config = RetryConfig(max_attempts=3, base_wait=2.0, max_wait=30.0)
        assert config.max_attempts == 3
        assert config.base_wait == 2.0
        assert config.max_wait == 30.0

    def test_エッジケース_frozenで属性変更不可(self) -> None:
        config = RetryConfig()
        with pytest.raises(AttributeError):
            config.max_attempts = 10


# =============================================================================
# FraserConfig Tests
# =============================================================================


class TestFraserConfigDefaults:
    """Tests for ``FraserConfig`` default values."""

    def test_正常系_デフォルト値で生成できる(self) -> None:
        config = FraserConfig()
        assert config.api_key == ""
        assert config.base_url == BASE_URL
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.requests_per_minute == DEFAULT_REQUESTS_PER_MINUTE
        assert config.requests_per_hour == DEFAULT_REQUESTS_PER_HOUR
        assert isinstance(config.retry_config, RetryConfig)

    def test_正常系_カスタム値で生成できる(self) -> None:
        retry = RetryConfig(max_attempts=2)
        config = FraserConfig(
            api_key="custom-key",
            base_url="https://fraser.stlouisfed.org/api",
            timeout=5.0,
            requests_per_minute=10,
            requests_per_hour=600,
            retry_config=retry,
        )
        assert config.api_key == "custom-key"
        assert config.timeout == 5.0
        assert config.requests_per_minute == 10
        assert config.requests_per_hour == 600
        assert config.retry_config is retry


class TestFraserConfigReprSecrecy:
    """Tests verifying ``api_key`` does not leak via repr (CWE-532)."""

    def test_正常系_api_keyがreprに含まれない(self) -> None:
        config = FraserConfig(api_key="secret123")
        assert "secret123" not in repr(config)

    def test_正常系_api_keyフィールド名もreprに含まれない(self) -> None:
        config = FraserConfig(api_key="anything")
        assert "api_key" not in repr(config)


class TestFraserConfigValidation:
    """Tests for ``FraserConfig.__post_init__`` validation."""

    def test_異常系_timeoutがゼロでFraserValidationError(self) -> None:
        with pytest.raises(FraserValidationError, match="timeout must be positive"):
            FraserConfig(timeout=0)

    def test_異常系_timeoutが負でFraserValidationError(self) -> None:
        with pytest.raises(FraserValidationError, match="timeout must be positive"):
            FraserConfig(timeout=-1.0)

    def test_異常系_requests_per_minuteがゼロでFraserValidationError(self) -> None:
        with pytest.raises(
            FraserValidationError, match="requests_per_minute must be >= 1"
        ):
            FraserConfig(requests_per_minute=0)

    def test_異常系_requests_per_minuteが負でFraserValidationError(self) -> None:
        with pytest.raises(
            FraserValidationError, match="requests_per_minute must be >= 1"
        ):
            FraserConfig(requests_per_minute=-5)

    def test_異常系_FraserValidationErrorがfield属性を持つ(self) -> None:
        with pytest.raises(FraserValidationError) as exc_info:
            FraserConfig(timeout=-1.0)
        assert exc_info.value.field == "timeout"
        assert exc_info.value.value == -1.0


class TestFraserConfigImmutability:
    """Tests for ``FraserConfig`` immutability (frozen dataclass)."""

    def test_エッジケース_frozenでapi_key変更不可(self) -> None:
        config = FraserConfig()
        with pytest.raises(AttributeError):
            config.api_key = "changed"

    def test_エッジケース_frozenでtimeout変更不可(self) -> None:
        config = FraserConfig()
        with pytest.raises(AttributeError):
            config.timeout = 99.0


# =============================================================================
# FetchOptions Tests
# =============================================================================


class TestFetchOptions:
    """Tests for ``FetchOptions`` frozen dataclass."""

    def test_正常系_デフォルト値(self) -> None:
        options = FetchOptions()
        assert options.use_cache is True
        assert options.prefer == "txt"
        assert options.download_dir is None

    def test_正常系_カスタム値(self) -> None:
        path = Path("/tmp/fraser")
        options = FetchOptions(use_cache=False, prefer="pdf", download_dir=path)
        assert options.use_cache is False
        assert options.prefer == "pdf"
        assert options.download_dir == path

    def test_エッジケース_frozenで変更不可(self) -> None:
        options = FetchOptions()
        with pytest.raises(AttributeError):
            options.use_cache = False


# =============================================================================
# DocType Enum Tests
# =============================================================================


class TestDocType:
    """Tests for the ``DocType`` enum."""

    def test_正常系_メンバー数が6(self) -> None:
        assert len(DocType) == 6

    def test_正常系_全メンバーの値(self) -> None:
        expected = {
            "FOMC_MINUTES": "fomc_minutes",
            "FOMC_STATEMENTS": "fomc_statements",
            "FOMC_PRESS_CONFERENCES": "fomc_press_conferences",
            "BEIGE_BOOK": "beige_book",
            "FRB_SPEECHES": "frb_speeches",
            "MONETARY_POLICY_REPORT": "monetary_policy_report",
        }
        for name, value in expected.items():
            assert DocType[name].value == value

    def test_正常系_str継承(self) -> None:
        assert isinstance(DocType.FOMC_MINUTES, str)
        assert DocType.FOMC_MINUTES == "fomc_minutes"

    def test_正常系_キーがKNOWN_TITLE_IDSに含まれる(self) -> None:
        from market.fraser.constants import KNOWN_TITLE_IDS

        for member in DocType:
            assert member.value in KNOWN_TITLE_IDS
