"""Tests for market.retry module.

Tests verify the shared RetryConfig frozen dataclass including:

- Module exports: __all__ completeness and importability
- RetryConfig: frozen, defaults, field types
- RetryConfig: max_attempts range validation
- Backward compatibility: from market.bse.types import RetryConfig

Test TODO List:
- [x] Module exports: __all__ completeness and importability
- [x] RetryConfig: frozen, defaults, field types
- [x] RetryConfig: max_attempts range validation
- [x] Backward compatibility: from market.bse.types import RetryConfig
"""

from dataclasses import FrozenInstanceError

import pytest

from market.retry import RetryConfig, __all__

# =============================================================================
# Module exports
# =============================================================================


class TestModuleExports:
    """Test market.retry module __all__ exports and structure."""

    def test_正常系_モジュールがインポートできる(self) -> None:
        """market.retry モジュールが正常にインポートできること。"""
        import market.retry as retry_module

        assert retry_module is not None

    def test_正常系_allが定義されている(self) -> None:
        """__all__ がリストとして定義されていること。"""
        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_正常系_allにRetryConfigが含まれる(self) -> None:
        """__all__ に RetryConfig が含まれていること。"""
        assert "RetryConfig" in __all__

    def test_正常系_allの全項目がモジュールに存在する(self) -> None:
        """__all__ の全項目がモジュールの属性として存在すること。"""
        import market.retry as retry_module

        for name in __all__:
            assert hasattr(retry_module, name), (
                f"{name} is not defined in market.retry module"
            )


# =============================================================================
# RetryConfig dataclass
# =============================================================================


class TestRetryConfig:
    """Test RetryConfig frozen dataclass in market.retry."""

    def test_正常系_frozenである(self) -> None:
        """RetryConfig がフィールド変更不可であること。"""
        config = RetryConfig()
        with pytest.raises(FrozenInstanceError):
            config.max_attempts = 10  # type: ignore[misc]

    def test_正常系_デフォルト値が正しい(self) -> None:
        """RetryConfig のデフォルト値が設計通りであること。"""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_正常系_カスタム値で生成できる(self) -> None:
        """RetryConfig をカスタム値で生成できること。"""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=60.0,
            exponential_base=3.0,
            jitter=False,
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 60.0
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_正常系_全フィールドが存在する(self) -> None:
        """RetryConfig が設計通りの5フィールドを持つこと。"""
        config = RetryConfig()
        assert hasattr(config, "max_attempts")
        assert hasattr(config, "initial_delay")
        assert hasattr(config, "max_delay")
        assert hasattr(config, "exponential_base")
        assert hasattr(config, "jitter")

    def test_正常系_境界値でmax_attemptsが受け入れられる(self) -> None:
        """max_attempts の境界値（1, 10）が受け入れられること。"""
        config_min = RetryConfig(max_attempts=1)
        assert config_min.max_attempts == 1
        config_max = RetryConfig(max_attempts=10)
        assert config_max.max_attempts == 10

    def test_異常系_max_attemptsが範囲外でValueError(self) -> None:
        """max_attempts が範囲外の場合 ValueError が発生すること。"""
        with pytest.raises(ValueError, match="max_attempts must be between 1 and 10"):
            RetryConfig(max_attempts=0)
        with pytest.raises(ValueError, match="max_attempts must be between 1 and 10"):
            RetryConfig(max_attempts=11)

    def test_正常系_フィールドの型が正しい(self) -> None:
        """RetryConfig フィールドの型が設計通りであること。"""
        config = RetryConfig()
        assert isinstance(config.max_attempts, int)
        assert isinstance(config.initial_delay, float)
        assert isinstance(config.max_delay, float)
        assert isinstance(config.exponential_base, float)
        assert isinstance(config.jitter, bool)


# =============================================================================
# Backward compatibility
# =============================================================================


class TestBackwardCompatibility:
    """Test backward compatibility of RetryConfig re-export in market.bse.types."""

    def test_正常系_bse_typesからインポートできる(self) -> None:
        """from market.bse.types import RetryConfig が成功すること。"""
        from market.bse.types import RetryConfig as BseRetryConfig

        assert BseRetryConfig is not None

    def test_正常系_bseのRetryConfigとmarket_retryのRetryConfigが同一クラス(
        self,
    ) -> None:
        """market.bse.types.RetryConfig と market.retry.RetryConfig が同一クラスであること。"""
        from market.bse.types import RetryConfig as BseRetryConfig
        from market.retry import RetryConfig as MarketRetryConfig

        assert BseRetryConfig is MarketRetryConfig

    def test_正常系_bse経由でインスタンス生成できる(self) -> None:
        """market.bse.types.RetryConfig でインスタンス生成できること。"""
        from market.bse.types import RetryConfig as BseRetryConfig

        config = BseRetryConfig(max_attempts=5)
        assert config.max_attempts == 5

    def test_正常系_bseのallにRetryConfigが含まれる(self) -> None:
        """market.bse.types.__all__ に RetryConfig が含まれていること。"""
        from market.bse.types import __all__ as bse_all

        assert "RetryConfig" in bse_all
