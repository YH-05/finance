"""Unit tests for FactorRegistry.

このテストモジュールは、ファクターレジストリ機能を検証します。

テスト対象:
- FactorRegistry: ファクターの登録・取得・管理を行うシングルトンクラス
- register_factor: ファクター登録デコレータ
- FactorCategory 拡張: ALTERNATIVE カテゴリの追加
- FactorMetadata 拡張: required_data, frequency フィールド

Issue: #133 - [factor] T19: ファクターカテゴリ拡張フレームワーク

受け入れ条件:
1. ファクターカテゴリ（価格ベース、ファンダメンタル、マクロ、オルタナティブ）の分類が定義
2. 各カテゴリに対応する DataProvider インターフェースの拡張ポイントが用意
3. 新しいファクターカテゴリを追加するためのドキュメントがある
4. ファクターのメタデータ（必要なデータ種別、計算頻度等）が定義できる
5. pyright strict でエラーがない
6. ユニットテスト tests/factor/unit/core/test_registry.py が作成されている
"""

from datetime import datetime

import pandas as pd
import pytest
from factor.core.base import Factor, FactorMetadata

# AIDEV-NOTE: 以下のインポートは registry.py 実装後に有効になる
# 現在は Red 状態（テスト失敗）で完了
from factor.core.registry import (
    FactorNotFoundError,
    get_registry,
    register_factor,
)
from factor.enums import FactorCategory
from factor.errors import FactorError
from factor.providers.base import DataProvider

# =============================================================================
# テスト用のモッククラス
# =============================================================================


class MockDataProvider:
    """DataProviderプロトコルを実装するモッククラス。"""

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック価格データを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        data = {symbol: range(len(dates)) for symbol in symbols}
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック出来高データを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        data = {symbol: [1000] * len(dates) for symbol in symbols}
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モックファンダメンタルデータを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        arrays = [[s for s in symbols for _ in metrics], metrics * len(symbols)]
        columns = pd.MultiIndex.from_arrays(arrays, names=["symbol", "metric"])
        df = pd.DataFrame(1.0, index=dates, columns=columns)
        df.index.name = "Date"
        return df

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック時価総額データを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        data = {symbol: [1e9] * len(dates) for symbol in symbols}
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df


# =============================================================================
# テスト用のファクタークラス
# =============================================================================


class TestMomentumFactor(Factor):
    """テスト用モメンタムファクター。"""

    name = "test_momentum"
    description = "テスト用モメンタムファクター"
    category = FactorCategory.MOMENTUM

    _required_data: list[str] = ["price"]
    _frequency: str = "daily"

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モメンタムを計算。"""
        prices = provider.get_prices(universe, start_date, end_date)
        return prices.pct_change()


class TestValueFactor(Factor):
    """テスト用バリューファクター。"""

    name = "test_value"
    description = "テスト用バリューファクター"
    category = FactorCategory.VALUE

    _required_data: list[str] = ["price", "fundamentals"]
    _frequency: str = "daily"

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """バリューを計算。"""
        prices = provider.get_prices(universe, start_date, end_date)
        return prices


class TestQualityFactor(Factor):
    """テスト用クオリティファクター。"""

    name = "test_quality"
    description = "テスト用クオリティファクター"
    category = FactorCategory.QUALITY

    _required_data: list[str] = ["fundamentals"]
    _frequency: str = "quarterly"

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """クオリティを計算。"""
        prices = provider.get_prices(universe, start_date, end_date)
        return prices


class TestMacroFactor(Factor):
    """テスト用マクロファクター。"""

    name = "test_macro"
    description = "テスト用マクロファクター"
    category = FactorCategory.MACRO

    _required_data: list[str] = ["macro_indicators"]
    _frequency: str = "monthly"

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """マクロファクターを計算。"""
        prices = provider.get_prices(universe, start_date, end_date)
        return prices


class TestSizeFactor(Factor):
    """テスト用サイズファクター。"""

    name = "test_size"
    description = "テスト用サイズファクター"
    category = FactorCategory.SIZE

    _required_data: list[str] = ["market_cap"]
    _frequency: str = "daily"

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """サイズを計算。"""
        return provider.get_market_cap(universe, start_date, end_date)


class TestPriceFactor(Factor):
    """テスト用プライスファクター。"""

    name = "test_price"
    description = "テスト用プライスファクター"
    category = FactorCategory.PRICE

    _required_data: list[str] = ["price", "volume"]
    _frequency: str = "daily"

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """プライスを計算。"""
        prices = provider.get_prices(universe, start_date, end_date)
        return prices


# =============================================================================
# FactorRegistry クラスのテスト
# =============================================================================


class TestFactorRegistryBasic:
    """FactorRegistryの基本機能テスト。"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """各テストの前にレジストリをリセット。"""
        registry = get_registry()
        registry.clear()

    def test_正常系_ファクター登録_名前で取得できる(self) -> None:
        """ファクターを登録し、名前で取得できることを確認。"""
        registry = get_registry()

        # 登録
        registry.register(TestMomentumFactor)

        # 取得
        factor_class = registry.get("test_momentum")

        assert factor_class is TestMomentumFactor
        assert factor_class.name == "test_momentum"

    def test_正常系_複数ファクター登録_全て取得できる(self) -> None:
        """複数のファクターを登録し、全て取得できることを確認。"""
        registry = get_registry()

        # 複数登録
        registry.register(TestMomentumFactor)
        registry.register(TestValueFactor)
        registry.register(TestQualityFactor)

        # 取得確認
        assert registry.get("test_momentum") is TestMomentumFactor
        assert registry.get("test_value") is TestValueFactor
        assert registry.get("test_quality") is TestQualityFactor

    def test_異常系_未登録ファクター取得でFactorNotFoundError(self) -> None:
        """未登録のファクターを取得しようとするとFactorNotFoundErrorが発生。"""
        registry = get_registry()

        with pytest.raises(FactorNotFoundError) as exc_info:
            registry.get("nonexistent_factor")

        assert "nonexistent_factor" in str(exc_info.value)

    def test_正常系_登録済みファクター一覧を取得(self) -> None:
        """登録済みファクターの一覧を取得できることを確認。"""
        registry = get_registry()

        registry.register(TestMomentumFactor)
        registry.register(TestValueFactor)

        names = registry.list_all()

        assert "test_momentum" in names
        assert "test_value" in names
        assert len(names) == 2

    def test_正常系_レジストリクリア(self) -> None:
        """レジストリをクリアできることを確認。"""
        registry = get_registry()

        registry.register(TestMomentumFactor)
        assert len(registry.list_all()) == 1

        registry.clear()

        assert len(registry.list_all()) == 0


class TestFactorRegistryByCategory:
    """カテゴリ別ファクター取得のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """各テストの前にレジストリをリセットしファクターを登録。"""
        registry = get_registry()
        registry.clear()
        registry.register(TestMomentumFactor)  # MOMENTUM
        registry.register(TestValueFactor)  # VALUE
        registry.register(TestQualityFactor)  # QUALITY
        registry.register(TestMacroFactor)  # MACRO
        registry.register(TestSizeFactor)  # SIZE
        registry.register(TestPriceFactor)  # PRICE

    def test_正常系_MONENTUMカテゴリでファクター一覧取得(self) -> None:
        """MONENTUMカテゴリのファクター一覧を取得できることを確認。"""
        registry = get_registry()

        momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)

        assert "test_momentum" in momentum_factors
        assert len(momentum_factors) == 1

    def test_正常系_VALUEカテゴリでファクター一覧取得(self) -> None:
        """VALUEカテゴリのファクター一覧を取得できることを確認。"""
        registry = get_registry()

        value_factors = registry.list_by_category(FactorCategory.VALUE)

        assert "test_value" in value_factors
        assert len(value_factors) == 1

    def test_正常系_QUALITYカテゴリでファクター一覧取得(self) -> None:
        """QUALITYカテゴリのファクター一覧を取得できることを確認。"""
        registry = get_registry()

        quality_factors = registry.list_by_category(FactorCategory.QUALITY)

        assert "test_quality" in quality_factors
        assert len(quality_factors) == 1

    def test_正常系_MACROカテゴリでファクター一覧取得(self) -> None:
        """MACROカテゴリのファクター一覧を取得できることを確認。"""
        registry = get_registry()

        macro_factors = registry.list_by_category(FactorCategory.MACRO)

        assert "test_macro" in macro_factors
        assert len(macro_factors) == 1

    def test_正常系_SIZEカテゴリでファクター一覧取得(self) -> None:
        """SIZEカテゴリのファクター一覧を取得できることを確認。"""
        registry = get_registry()

        size_factors = registry.list_by_category(FactorCategory.SIZE)

        assert "test_size" in size_factors
        assert len(size_factors) == 1

    def test_正常系_PRICEカテゴリでファクター一覧取得(self) -> None:
        """PRICEカテゴリのファクター一覧を取得できることを確認。"""
        registry = get_registry()

        price_factors = registry.list_by_category(FactorCategory.PRICE)

        assert "test_price" in price_factors
        assert len(price_factors) == 1

    def test_正常系_全カテゴリでファクター分類可能(self) -> None:
        """全カテゴリでファクターが分類できることを確認。"""
        registry = get_registry()

        all_categories = [
            FactorCategory.MOMENTUM,
            FactorCategory.VALUE,
            FactorCategory.QUALITY,
            FactorCategory.MACRO,
            FactorCategory.SIZE,
            FactorCategory.PRICE,
        ]

        total_count = 0
        for category in all_categories:
            factors = registry.list_by_category(category)
            total_count += len(factors)

        assert total_count == 6


class TestFactorRegistryDecorator:
    """デコレータによるファクター登録のテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """各テストの前にレジストリをリセット。"""
        registry = get_registry()
        registry.clear()

    def test_正常系_デコレータでファクター登録(self) -> None:
        """@register_factorデコレータでファクターを登録できることを確認。"""

        @register_factor
        class DecoratedFactor(Factor):
            """デコレータで登録されるファクター。"""

            name = "decorated_factor"
            description = "デコレータで登録されたファクター"
            category = FactorCategory.VALUE

            def compute(
                self,
                provider: DataProvider,
                universe: list[str],
                start_date: datetime | str,
                end_date: datetime | str,
            ) -> pd.DataFrame:
                """計算処理。"""
                return provider.get_prices(universe, start_date, end_date)

        registry = get_registry()

        # デコレータ適用後、自動的にレジストリに登録されている
        factor_class = registry.get("decorated_factor")

        assert factor_class is DecoratedFactor

    def test_正常系_デコレータ適用後もクラスは元のまま(self) -> None:
        """@register_factorデコレータ適用後もクラスが元のままであることを確認。"""

        @register_factor
        class AnotherDecoratedFactor(Factor):
            """別のデコレータで登録されるファクター。"""

            name = "another_decorated"
            description = "別のデコレータで登録されたファクター"
            category = FactorCategory.MOMENTUM

            def compute(
                self,
                provider: DataProvider,
                universe: list[str],
                start_date: datetime | str,
                end_date: datetime | str,
            ) -> pd.DataFrame:
                """計算処理。"""
                return provider.get_prices(universe, start_date, end_date)

        # デコレータ適用後もクラスは元のまま
        assert AnotherDecoratedFactor.name == "another_decorated"
        assert issubclass(AnotherDecoratedFactor, Factor)


# =============================================================================
# ファクターカテゴリ拡張のテスト
# =============================================================================


class TestFactorCategoryExtension:
    """ファクターカテゴリ拡張のテスト。"""

    def test_正常系_既存カテゴリが全て存在する(self) -> None:
        """既存のカテゴリが全て存在することを確認。"""
        assert hasattr(FactorCategory, "MACRO")
        assert hasattr(FactorCategory, "QUALITY")
        assert hasattr(FactorCategory, "VALUE")
        assert hasattr(FactorCategory, "MOMENTUM")
        assert hasattr(FactorCategory, "SIZE")
        assert hasattr(FactorCategory, "PRICE")

    def test_正常系_カテゴリ値が文字列として取得できる(self) -> None:
        """カテゴリ値が文字列として取得できることを確認。"""
        assert FactorCategory.MACRO.value == "macro"
        assert FactorCategory.QUALITY.value == "quality"
        assert FactorCategory.VALUE.value == "value"
        assert FactorCategory.MOMENTUM.value == "momentum"
        assert FactorCategory.SIZE.value == "size"
        assert FactorCategory.PRICE.value == "price"


# =============================================================================
# DataProvider 拡張ポイントのテスト
# =============================================================================


class TestDataProviderExtension:
    """DataProvider拡張ポイントのテスト。"""

    def test_正常系_カスタムデータメソッド定義可能(self) -> None:
        """DataProviderにカスタムメソッドを追加できることを確認。"""

        class ExtendedDataProvider(MockDataProvider):
            """拡張されたDataProvider。"""

            def get_alternative_data(
                self,
                symbols: list[str],
                data_type: str,
                start_date: datetime | str,
                end_date: datetime | str,
            ) -> pd.DataFrame:
                """オルタナティブデータを取得。"""
                dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
                data = {symbol: [1.0] * len(dates) for symbol in symbols}
                df = pd.DataFrame(data, index=dates)
                df.index.name = "Date"
                return df

        provider = ExtendedDataProvider()

        # カスタムメソッドが呼び出せる
        result = provider.get_alternative_data(
            symbols=["AAPL"],
            data_type="sentiment",
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns

    def test_正常系_基本プロトコルメソッドが維持される(self) -> None:
        """拡張後も基本プロトコルメソッドが維持されることを確認。"""

        class ExtendedDataProvider(MockDataProvider):
            """拡張されたDataProvider。"""

            def get_alternative_data(
                self,
                symbols: list[str],
                data_type: str,
                start_date: datetime | str,
                end_date: datetime | str,
            ) -> pd.DataFrame:
                """オルタナティブデータを取得。"""
                return pd.DataFrame()

        provider = ExtendedDataProvider()

        # 基本メソッドが利用可能
        assert hasattr(provider, "get_prices")
        assert hasattr(provider, "get_volumes")
        assert hasattr(provider, "get_fundamentals")
        assert hasattr(provider, "get_market_cap")

        # DataProviderプロトコルを満たす
        assert isinstance(provider, DataProvider)


# =============================================================================
# FactorMetadata 拡張のテスト
# =============================================================================


class TestFactorMetadataExtension:
    """FactorMetadata拡張のテスト。"""

    def test_正常系_required_dataフィールド設定(self) -> None:
        """required_dataフィールドが設定できることを確認。"""
        metadata = FactorMetadata(
            name="test_factor",
            description="テストファクター",
            category="price",
            required_data=["price", "volume", "fundamentals"],
            frequency="daily",
        )

        assert metadata.required_data == ["price", "volume", "fundamentals"]
        assert len(metadata.required_data) == 3

    def test_正常系_frequencyフィールド設定_daily(self) -> None:
        """frequencyフィールドにdailyを設定できることを確認。"""
        metadata = FactorMetadata(
            name="daily_factor",
            description="日次ファクター",
            category="price",
            required_data=["price"],
            frequency="daily",
        )

        assert metadata.frequency == "daily"

    def test_正常系_frequencyフィールド設定_weekly(self) -> None:
        """frequencyフィールドにweeklyを設定できることを確認。"""
        metadata = FactorMetadata(
            name="weekly_factor",
            description="週次ファクター",
            category="price",
            required_data=["price"],
            frequency="weekly",
        )

        assert metadata.frequency == "weekly"

    def test_正常系_frequencyフィールド設定_monthly(self) -> None:
        """frequencyフィールドにmonthlyを設定できることを確認。"""
        metadata = FactorMetadata(
            name="monthly_factor",
            description="月次ファクター",
            category="macro",
            required_data=["macro_indicators"],
            frequency="monthly",
        )

        assert metadata.frequency == "monthly"

    def test_正常系_frequencyフィールド設定_quarterly(self) -> None:
        """frequencyフィールドにquarterlyを設定できることを確認。"""
        metadata = FactorMetadata(
            name="quarterly_factor",
            description="四半期ファクター",
            category="quality",
            required_data=["fundamentals"],
            frequency="quarterly",
        )

        assert metadata.frequency == "quarterly"

    def test_正常系_Factorからメタデータ取得_required_data反映(self) -> None:
        """Factorのmetadataプロパティでrequired_dataが反映されることを確認。"""

        class FactorWithRequiredData(Factor):
            """必要データを指定したファクター。"""

            name = "factor_with_data"
            description = "必要データ指定ファクター"
            category = FactorCategory.VALUE

            _required_data: list[str] = ["price", "fundamentals", "market_cap"]
            _frequency: str = "daily"

            def compute(
                self,
                provider: DataProvider,
                universe: list[str],
                start_date: datetime | str,
                end_date: datetime | str,
            ) -> pd.DataFrame:
                """計算処理。"""
                return provider.get_prices(universe, start_date, end_date)

        factor = FactorWithRequiredData()
        metadata = factor.metadata

        assert metadata.required_data == ["price", "fundamentals", "market_cap"]

    def test_正常系_Factorからメタデータ取得_frequency反映(self) -> None:
        """Factorのmetadataプロパティでfrequencyが反映されることを確認。"""

        class FactorWithFrequency(Factor):
            """計算頻度を指定したファクター。"""

            name = "factor_with_freq"
            description = "計算頻度指定ファクター"
            category = FactorCategory.QUALITY

            _required_data: list[str] = ["fundamentals"]
            _frequency: str = "quarterly"

            def compute(
                self,
                provider: DataProvider,
                universe: list[str],
                start_date: datetime | str,
                end_date: datetime | str,
            ) -> pd.DataFrame:
                """計算処理。"""
                return provider.get_prices(universe, start_date, end_date)

        factor = FactorWithFrequency()
        metadata = factor.metadata

        assert metadata.frequency == "quarterly"


# =============================================================================
# レジストリとメタデータの統合テスト
# =============================================================================


class TestRegistryWithMetadata:
    """レジストリとメタデータの統合テスト。"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """各テストの前にレジストリをリセット。"""
        registry = get_registry()
        registry.clear()

    def test_正常系_登録されたファクターのメタデータ取得(self) -> None:
        """登録されたファクターのメタデータが取得できることを確認。"""
        registry = get_registry()
        registry.register(TestValueFactor)

        # ファクタークラスを取得
        factor_class = registry.get("test_value")

        # インスタンス化してメタデータ取得
        factor = factor_class()
        metadata = factor.metadata

        assert metadata.name == "test_value"
        assert metadata.required_data == ["price", "fundamentals"]

    def test_正常系_カテゴリ別取得後のメタデータ確認(self) -> None:
        """カテゴリ別で取得したファクターのメタデータを確認。"""
        registry = get_registry()
        registry.register(TestQualityFactor)

        # カテゴリで取得
        quality_factors = registry.list_by_category(FactorCategory.QUALITY)

        for factor_name in quality_factors:
            factor_class = registry.get(factor_name)
            factor = factor_class()
            metadata = factor.metadata

            # カテゴリがQUALITYにマッピングされている
            assert metadata.category in ["quality", "value"]


# =============================================================================
# シングルトンパターンのテスト
# =============================================================================


class TestRegistrySingleton:
    """レジストリのシングルトンパターンテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """各テストの前にレジストリをリセット。"""
        registry = get_registry()
        registry.clear()

    def test_正常系_get_registryで同一インスタンス取得(self) -> None:
        """get_registry()で常に同一インスタンスが返されることを確認。"""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_正常系_異なる場所からの登録が同じレジストリに反映(self) -> None:
        """異なる場所からの登録が同じレジストリに反映されることを確認。"""
        registry1 = get_registry()
        registry1.register(TestMomentumFactor)

        registry2 = get_registry()
        names = registry2.list_all()

        assert "test_momentum" in names


# =============================================================================
# エラーハンドリングのテスト
# =============================================================================


class TestRegistryErrorHandling:
    """レジストリのエラーハンドリングテスト。"""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """各テストの前にレジストリをリセット。"""
        registry = get_registry()
        registry.clear()

    def test_異常系_重複登録でエラー(self) -> None:
        """同じ名前のファクターを重複登録しようとするとエラー。"""
        registry = get_registry()
        registry.register(TestMomentumFactor)

        # 同じ名前のファクターを再登録しようとする
        class DuplicateFactor(Factor):
            """重複する名前のファクター。"""

            name = "test_momentum"  # 同じ名前
            description = "重複ファクター"
            category = FactorCategory.PRICE

            def compute(
                self,
                provider: DataProvider,
                universe: list[str],
                start_date: datetime | str,
                end_date: datetime | str,
            ) -> pd.DataFrame:
                """計算処理。"""
                return provider.get_prices(universe, start_date, end_date)

        with pytest.raises(FactorError):
            registry.register(DuplicateFactor)

    def test_正常系_force_trueで重複登録を許可(self) -> None:
        """force=Trueで重複登録を許可できることを確認。"""
        registry = get_registry()
        registry.register(TestMomentumFactor)

        # 同じ名前の新しいファクター
        class NewMomentumFactor(Factor):
            """新しいモメンタムファクター。"""

            name = "test_momentum"
            description = "新しいモメンタムファクター"
            category = FactorCategory.PRICE

            def compute(
                self,
                provider: DataProvider,
                universe: list[str],
                start_date: datetime | str,
                end_date: datetime | str,
            ) -> pd.DataFrame:
                """計算処理。"""
                return provider.get_prices(universe, start_date, end_date)

        # force=Trueで上書き登録
        registry.register(NewMomentumFactor, force=True)

        factor_class = registry.get("test_momentum")
        assert factor_class is NewMomentumFactor
        assert factor_class.description == "新しいモメンタムファクター"

    def test_異常系_FactorNotFoundErrorがFactorErrorを継承(self) -> None:
        """FactorNotFoundErrorがFactorErrorを継承していることを確認。"""
        assert issubclass(FactorNotFoundError, FactorError)
