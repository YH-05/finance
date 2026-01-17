"""Unit tests for factor package __init__.py exports.

This module tests that all public APIs are properly exported from the
factor package root and subpackages.

TDD Red Phase: These tests are expected to FAIL until the implementation
exports all required classes in factor/__init__.py.
"""


class TestPackageRootImport:
    """Test that main classes can be imported from package root."""

    # =========================================================================
    # Core Classes - Already Exported
    # =========================================================================

    def test_正常系_Factorがルートからインポートできる(self) -> None:
        """Factor基底クラスがパッケージルートからインポートできることを確認。"""
        from factor import Factor

        assert Factor is not None

    def test_正常系_FactorComputeOptionsがルートからインポートできる(self) -> None:
        """FactorComputeOptionsがパッケージルートからインポートできることを確認。"""
        from factor import FactorComputeOptions

        assert FactorComputeOptions is not None

    def test_正常系_FactorMetadataがルートからインポートできる(self) -> None:
        """FactorMetadataがパッケージルートからインポートできることを確認。"""
        from factor import FactorMetadata

        assert FactorMetadata is not None

    def test_正常系_FactorRegistryがルートからインポートできる(self) -> None:
        """FactorRegistryがパッケージルートからインポートできることを確認。"""
        from factor import FactorRegistry

        assert FactorRegistry is not None

    # =========================================================================
    # Core Classes - NOT YET Exported (Expected to FAIL)
    # =========================================================================

    def test_正常系_Normalizerがルートからインポートできる(self) -> None:
        """Normalizerがパッケージルートからインポートできることを確認。"""
        from factor import Normalizer

        assert Normalizer is not None

    def test_正常系_Orthogonalizerがルートからインポートできる(self) -> None:
        """Orthogonalizerがパッケージルートからインポートできることを確認。"""
        from factor import Orthogonalizer

        assert Orthogonalizer is not None

    def test_正常系_PCAResultがルートからインポートできる(self) -> None:
        """PCAResultがパッケージルートからインポートできることを確認。"""
        from factor import PCAResult

        assert PCAResult is not None

    def test_正常系_YieldCurvePCAがルートからインポートできる(self) -> None:
        """YieldCurvePCAがパッケージルートからインポートできることを確認。"""
        from factor import YieldCurvePCA

        assert YieldCurvePCA is not None

    def test_正常系_ReturnCalculatorがルートからインポートできる(self) -> None:
        """ReturnCalculatorがパッケージルートからインポートできることを確認。"""
        from factor import ReturnCalculator

        assert ReturnCalculator is not None

    def test_正常系_ReturnConfigがルートからインポートできる(self) -> None:
        """ReturnConfigがパッケージルートからインポートできることを確認。"""
        from factor import ReturnConfig

        assert ReturnConfig is not None

    # =========================================================================
    # Price Factors - NOT YET Exported (Expected to FAIL)
    # =========================================================================

    def test_正常系_MomentumFactorがルートからインポートできる(self) -> None:
        """MomentumFactorがパッケージルートからインポートできることを確認。"""
        from factor import MomentumFactor

        assert MomentumFactor is not None

    def test_正常系_ReversalFactorがルートからインポートできる(self) -> None:
        """ReversalFactorがパッケージルートからインポートできることを確認。"""
        from factor import ReversalFactor

        assert ReversalFactor is not None

    def test_正常系_VolatilityFactorがルートからインポートできる(self) -> None:
        """VolatilityFactorがパッケージルートからインポートできることを確認。"""
        from factor import VolatilityFactor

        assert VolatilityFactor is not None

    # =========================================================================
    # Value Factors - Already Exported
    # =========================================================================

    def test_正常系_ValueFactorがルートからインポートできる(self) -> None:
        """ValueFactorがパッケージルートからインポートできることを確認。"""
        from factor import ValueFactor

        assert ValueFactor is not None

    def test_正常系_CompositeValueFactorがルートからインポートできる(self) -> None:
        """CompositeValueFactorがパッケージルートからインポートできることを確認。"""
        from factor import CompositeValueFactor

        assert CompositeValueFactor is not None

    # =========================================================================
    # Quality Factors - NOT YET Exported (Expected to FAIL)
    # =========================================================================

    def test_正常系_QualityFactorがルートからインポートできる(self) -> None:
        """QualityFactorがパッケージルートからインポートできることを確認。"""
        from factor import QualityFactor

        assert QualityFactor is not None

    def test_正常系_CompositeQualityFactorがルートからインポートできる(self) -> None:
        """CompositeQualityFactorがパッケージルートからインポートできることを確認。"""
        from factor import CompositeQualityFactor

        assert CompositeQualityFactor is not None

    def test_正常系_ROICFactorがルートからインポートできる(self) -> None:
        """ROICFactorがパッケージルートからインポートできることを確認。"""
        from factor import ROICFactor

        assert ROICFactor is not None

    def test_正常系_ROICTransitionLabelerがルートからインポートできる(self) -> None:
        """ROICTransitionLabelerがパッケージルートからインポートできることを確認。"""
        from factor import ROICTransitionLabeler

        assert ROICTransitionLabeler is not None

    # =========================================================================
    # Size Factors - NOT YET Exported (Expected to FAIL)
    # =========================================================================

    def test_正常系_SizeFactorがルートからインポートできる(self) -> None:
        """SizeFactorがパッケージルートからインポートできることを確認。"""
        from factor import SizeFactor

        assert SizeFactor is not None

    # =========================================================================
    # Validation Classes - Already Exported
    # =========================================================================

    def test_正常系_ICAnalyzerがルートからインポートできる(self) -> None:
        """ICAnalyzerがパッケージルートからインポートできることを確認。"""
        from factor import ICAnalyzer

        assert ICAnalyzer is not None

    def test_正常系_ICResultがルートからインポートできる(self) -> None:
        """ICResultがパッケージルートからインポートできることを確認。"""
        from factor import ICResult

        assert ICResult is not None

    def test_正常系_QuantileAnalyzerがルートからインポートできる(self) -> None:
        """QuantileAnalyzerがパッケージルートからインポートできることを確認。"""
        from factor import QuantileAnalyzer

        assert QuantileAnalyzer is not None

    # =========================================================================
    # Providers - NOT YET Exported (Expected to FAIL)
    # =========================================================================

    def test_正常系_DataProviderがルートからインポートできる(self) -> None:
        """DataProviderがパッケージルートからインポートできることを確認。"""
        from factor import DataProvider

        assert DataProvider is not None

    def test_正常系_YFinanceProviderがルートからインポートできる(self) -> None:
        """YFinanceProviderがパッケージルートからインポートできることを確認。"""
        from factor import YFinanceProvider

        assert YFinanceProvider is not None

    def test_正常系_Cacheがルートからインポートできる(self) -> None:
        """Cacheがパッケージルートからインポートできることを確認。"""
        from factor import Cache

        assert Cache is not None

    # =========================================================================
    # Types - Already Exported (Partial)
    # =========================================================================

    def test_正常系_FactorConfigがルートからインポートできる(self) -> None:
        """FactorConfigがパッケージルートからインポートできることを確認。"""
        from factor import FactorConfig

        assert FactorConfig is not None

    def test_正常系_FactorResultがルートからインポートできる(self) -> None:
        """FactorResultがパッケージルートからインポートできることを確認。"""
        from factor import FactorResult

        assert FactorResult is not None

    def test_正常系_QuantileResultがルートからインポートできる(self) -> None:
        """QuantileResultがパッケージルートからインポートできることを確認。"""
        from factor import QuantileResult

        assert QuantileResult is not None

    def test_正常系_OrthogonalizationResultがルートからインポートできる(self) -> None:
        """OrthogonalizationResultがパッケージルートからインポートできることを確認。"""
        from factor import OrthogonalizationResult

        assert OrthogonalizationResult is not None

    def test_正常系_FactorCategoryがルートからインポートできる(self) -> None:
        """FactorCategoryがパッケージルートからインポートできることを確認。"""
        from factor import FactorCategory

        assert FactorCategory is not None

    def test_正常系_NormalizationMethodがルートからインポートできる(self) -> None:
        """NormalizationMethodがパッケージルートからインポートできることを確認。"""
        from factor import NormalizationMethod

        assert NormalizationMethod is not None

    # =========================================================================
    # Errors - Partial Export
    # =========================================================================

    def test_正常系_FactorErrorがルートからインポートできる(self) -> None:
        """FactorErrorがパッケージルートからインポートできることを確認。"""
        from factor import FactorError

        assert FactorError is not None

    def test_正常系_DataFetchErrorがルートからインポートできる(self) -> None:
        """DataFetchErrorがパッケージルートからインポートできることを確認。"""
        from factor import DataFetchError

        assert DataFetchError is not None

    def test_正常系_ValidationErrorがルートからインポートできる(self) -> None:
        """ValidationErrorがパッケージルートからインポートできることを確認。"""
        from factor import ValidationError

        assert ValidationError is not None

    def test_正常系_InsufficientDataErrorがルートからインポートできる(self) -> None:
        """InsufficientDataErrorがパッケージルートからインポートできることを確認。"""
        from factor import InsufficientDataError

        assert InsufficientDataError is not None

    def test_正常系_NormalizationErrorがルートからインポートできる(self) -> None:
        """NormalizationErrorがパッケージルートからインポートできることを確認。"""
        from factor import NormalizationError

        assert NormalizationError is not None

    def test_正常系_OrthogonalizationErrorがルートからインポートできる(self) -> None:
        """OrthogonalizationErrorがパッケージルートからインポートできることを確認。"""
        from factor import OrthogonalizationError

        assert OrthogonalizationError is not None


class TestSubpackageImport:
    """Test that classes can be imported from subpackages."""

    def test_正常系_providersからDataProviderがインポートできる(self) -> None:
        """factor.providersからDataProviderがインポートできることを確認。"""
        from factor.providers import DataProvider

        assert DataProvider is not None

    def test_正常系_providersからYFinanceProviderがインポートできる(self) -> None:
        """factor.providersからYFinanceProviderがインポートできることを確認。"""
        from factor.providers import YFinanceProvider

        assert YFinanceProvider is not None

    def test_正常系_providersからCacheがインポートできる(self) -> None:
        """factor.providersからCacheがインポートできることを確認。"""
        from factor.providers import Cache

        assert Cache is not None

    def test_正常系_validationからICAnalyzerがインポートできる(self) -> None:
        """factor.validationからICAnalyzerがインポートできることを確認。"""
        from factor.validation import ICAnalyzer

        assert ICAnalyzer is not None

    def test_正常系_validationからICResultがインポートできる(self) -> None:
        """factor.validationからICResultがインポートできることを確認。"""
        from factor.validation import ICResult

        assert ICResult is not None

    def test_正常系_validationからQuantileAnalyzerがインポートできる(self) -> None:
        """factor.validationからQuantileAnalyzerがインポートできることを確認。"""
        from factor.validation import QuantileAnalyzer

        assert QuantileAnalyzer is not None


class TestAllDefinition:
    """Test that __all__ is properly defined with all public APIs."""

    def test_正常系_allが定義されている(self) -> None:
        """__all__が定義されていることを確認。"""
        import factor

        assert hasattr(factor, "__all__")
        assert isinstance(factor.__all__, list)

    def test_正常系_allに全公開APIが含まれている(self) -> None:
        """__all__に全ての公開APIが含まれていることを確認。"""
        import factor

        # 必須の公開API一覧
        expected_exports = [
            # Core
            "Factor",
            "FactorComputeOptions",
            "FactorMetadata",
            "FactorRegistry",
            "Normalizer",
            "Orthogonalizer",
            "PCAResult",
            "YieldCurvePCA",
            "ReturnCalculator",
            "ReturnConfig",
            # Price Factors
            "MomentumFactor",
            "ReversalFactor",
            "VolatilityFactor",
            # Value Factors
            "ValueFactor",
            "CompositeValueFactor",
            # Quality Factors
            "QualityFactor",
            "CompositeQualityFactor",
            "ROICFactor",
            "ROICTransitionLabeler",
            # Size Factors
            "SizeFactor",
            # Validation
            "ICAnalyzer",
            "ICResult",
            "QuantileAnalyzer",
            # Providers
            "DataProvider",
            "YFinanceProvider",
            "Cache",
            # Types
            "FactorConfig",
            "FactorResult",
            "QuantileResult",
            "OrthogonalizationResult",
            "FactorCategory",
            "NormalizationMethod",
            # Errors
            "FactorError",
            "DataFetchError",
            "ValidationError",
            "InsufficientDataError",
            "NormalizationError",
            "OrthogonalizationError",
        ]

        missing_exports = [
            name for name in expected_exports if name not in factor.__all__
        ]

        assert not missing_exports, f"Missing exports in __all__: {missing_exports}"

    def test_正常系_allの各要素が実際にインポート可能(self) -> None:
        """__all__に定義された各要素が実際にインポート可能であることを確認。"""
        import factor

        for name in factor.__all__:
            assert hasattr(
                factor, name
            ), f"{name} is in __all__ but not accessible from package"


class TestBulkImport:
    """Test bulk import patterns."""

    def test_正常系_複数クラスを一度にインポートできる(self) -> None:
        """複数のクラスを一度にインポートできることを確認。"""
        from factor import (
            Factor,
            FactorConfig,
            FactorResult,
            ICAnalyzer,
            QuantileAnalyzer,
            ValueFactor,
        )

        assert Factor is not None
        assert FactorConfig is not None
        assert FactorResult is not None
        assert ICAnalyzer is not None
        assert QuantileAnalyzer is not None
        assert ValueFactor is not None

    def test_正常系_主要ファクタークラスを一括インポートできる(self) -> None:
        """主要なファクタークラスを一括でインポートできることを確認。"""
        from factor import (
            CompositeQualityFactor,
            CompositeValueFactor,
            MomentumFactor,
            QualityFactor,
            ReversalFactor,
            ROICFactor,
            SizeFactor,
            ValueFactor,
            VolatilityFactor,
        )

        factors = [
            MomentumFactor,
            ReversalFactor,
            VolatilityFactor,
            ValueFactor,
            CompositeValueFactor,
            QualityFactor,
            CompositeQualityFactor,
            ROICFactor,
            SizeFactor,
        ]

        for factor_cls in factors:
            assert factor_cls is not None

    def test_正常系_コア機能クラスを一括インポートできる(self) -> None:
        """コア機能クラスを一括でインポートできることを確認。"""
        from factor import (
            Normalizer,
            Orthogonalizer,
            PCAResult,
            ReturnCalculator,
            ReturnConfig,
            YieldCurvePCA,
        )

        core_classes = [
            Normalizer,
            Orthogonalizer,
            PCAResult,
            YieldCurvePCA,
            ReturnCalculator,
            ReturnConfig,
        ]

        for cls in core_classes:
            assert cls is not None

    def test_正常系_プロバイダークラスを一括インポートできる(self) -> None:
        """プロバイダークラスを一括でインポートできることを確認。"""
        from factor import Cache, DataProvider, YFinanceProvider

        providers = [DataProvider, YFinanceProvider, Cache]

        for provider_cls in providers:
            assert provider_cls is not None

    def test_正常系_エラークラスを一括インポートできる(self) -> None:
        """エラークラスを一括でインポートできることを確認。"""
        from factor import (
            DataFetchError,
            FactorError,
            InsufficientDataError,
            NormalizationError,
            OrthogonalizationError,
            ValidationError,
        )

        errors = [
            FactorError,
            DataFetchError,
            ValidationError,
            InsufficientDataError,
            NormalizationError,
            OrthogonalizationError,
        ]

        for error_cls in errors:
            assert error_cls is not None
            assert issubclass(error_cls, Exception)
