"""Unit tests for edgar.config module.

Tests for EdgarConfig dataclass, load_config(), and set_identity().
"""

import os
from pathlib import Path

import pytest

from edgar.config import (
    DEFAULT_CACHE_DIR,
    DEFAULT_CACHE_TTL_HOURS,
    DEFAULT_RATE_LIMIT_PER_SECOND,
    SEC_EDGAR_IDENTITY_ENV,
    EdgarConfig,
    load_config,
    set_identity,
)


class TestEdgarConfig:
    """Tests for EdgarConfig dataclass."""

    def test_正常系_EdgarConfigはデフォルト値を持つ(self) -> None:
        """EdgarConfig should have proper default values.

        Verify that EdgarConfig uses default values when instantiated
        without arguments.
        """
        config = EdgarConfig()

        assert config.identity == ""
        assert config.cache_dir == DEFAULT_CACHE_DIR
        assert config.cache_ttl_hours == DEFAULT_CACHE_TTL_HOURS
        assert config.rate_limit_per_second == DEFAULT_RATE_LIMIT_PER_SECOND

    def test_正常系_EdgarConfigはカスタム値を受け付ける(self) -> None:
        """EdgarConfig should accept custom values.

        Verify that EdgarConfig can be instantiated with custom values.
        """
        custom_dir = Path("/custom/cache")
        config = EdgarConfig(
            identity="John Doe john@example.com",
            cache_dir=custom_dir,
            cache_ttl_hours=48,
            rate_limit_per_second=5,
        )

        assert config.identity == "John Doe john@example.com"
        assert config.cache_dir == custom_dir
        assert config.cache_ttl_hours == 48
        assert config.rate_limit_per_second == 5

    def test_正常系_is_identity_configuredはidentityが設定済みならTrue(self) -> None:
        """is_identity_configured should return True when identity is set.

        Verify that the property correctly detects a configured identity.
        """
        config = EdgarConfig(identity="John Doe john@example.com")
        assert config.is_identity_configured is True

    def test_正常系_is_identity_configuredはidentityが空ならFalse(self) -> None:
        """is_identity_configured should return False when identity is empty.

        Verify that the property correctly detects an unconfigured identity.
        """
        config = EdgarConfig(identity="")
        assert config.is_identity_configured is False

    def test_エッジケース_is_identity_configuredは空白のみならFalse(self) -> None:
        """is_identity_configured should return False for whitespace-only identity.

        Verify that the property strips whitespace when checking.
        """
        config = EdgarConfig(identity="   ")
        assert config.is_identity_configured is False


class TestLoadConfig:
    """Tests for load_config function."""

    def test_正常系_環境変数からidentityを読み込む(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """load_config should read identity from environment variable.

        Verify that load_config reads SEC_EDGAR_IDENTITY from the environment.
        """
        monkeypatch.setenv(SEC_EDGAR_IDENTITY_ENV, "John Doe john@example.com")
        config = load_config()

        assert config.identity == "John Doe john@example.com"
        assert config.is_identity_configured is True

    def test_正常系_環境変数未設定で空のidentity(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """load_config should use empty identity when env var is not set.

        Verify that load_config returns empty identity when
        SEC_EDGAR_IDENTITY is not in the environment.
        """
        monkeypatch.delenv(SEC_EDGAR_IDENTITY_ENV, raising=False)
        config = load_config()

        assert config.identity == ""
        assert config.is_identity_configured is False

    def test_正常系_デフォルトのキャッシュ設定が適用される(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """load_config should apply default cache settings.

        Verify that cache_dir, cache_ttl_hours, and rate_limit_per_second
        have correct default values.
        """
        monkeypatch.delenv(SEC_EDGAR_IDENTITY_ENV, raising=False)
        config = load_config()

        assert config.cache_dir == DEFAULT_CACHE_DIR
        assert config.cache_ttl_hours == DEFAULT_CACHE_TTL_HOURS
        assert config.rate_limit_per_second == DEFAULT_RATE_LIMIT_PER_SECOND


class TestSetIdentity:
    """Tests for set_identity function."""

    def test_正常系_identityを設定できる(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """set_identity should set the environment variable.

        Verify that set_identity correctly sets SEC_EDGAR_IDENTITY.
        """
        monkeypatch.delenv(SEC_EDGAR_IDENTITY_ENV, raising=False)
        set_identity("John Doe", "john@example.com")

        assert os.environ.get(SEC_EDGAR_IDENTITY_ENV) == "John Doe john@example.com"

    def test_異常系_空の名前でValueError(self) -> None:
        """set_identity should raise ValueError for empty name.

        Verify that set_identity rejects empty name strings.
        """
        with pytest.raises(ValueError, match="Name must not be empty"):
            set_identity("", "john@example.com")

    def test_異常系_空のメールでValueError(self) -> None:
        """set_identity should raise ValueError for empty email.

        Verify that set_identity rejects empty email strings.
        """
        with pytest.raises(ValueError, match="Email must not be empty"):
            set_identity("John Doe", "")

    def test_異常系_空白のみの名前でValueError(self) -> None:
        """set_identity should raise ValueError for whitespace-only name.

        Verify that set_identity rejects whitespace-only name strings.
        """
        with pytest.raises(ValueError, match="Name must not be empty"):
            set_identity("   ", "john@example.com")

    def test_異常系_空白のみのメールでValueError(self) -> None:
        """set_identity should raise ValueError for whitespace-only email.

        Verify that set_identity rejects whitespace-only email strings.
        """
        with pytest.raises(ValueError, match="Email must not be empty"):
            set_identity("John Doe", "   ")
