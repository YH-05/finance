"""Unit tests for SizeFactor class.

SizeFactorは時価総額、売上高、総資産などの
サイズ指標を計算するファクタークラスである。
"""

from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: 実装が存在しないため、インポートは失敗する（Red状態）
# pytest.importorskipを使用して、実装後に自動的にテストが有効になる
size_module = pytest.importorskip("factor.factors.size.size")
SizeFactor = size_module.SizeFactor


class TestSizeFactorInheritance:
    """SizeFactorがFactor基底クラスを正しく継承していることのテスト。"""

    def test_正常系_Factor基底クラスを継承している(self) -> None:
        """SizeFactorがFactor基底クラスを継承していることを確認。"""
        from factor.core.base import Factor

        factor = SizeFactor()
        assert isinstance(factor, Factor)

    def test_正常系_name属性が定義されている(self) -> None:
        """SizeFactorにname属性が定義されていることを確認。"""
        factor = SizeFactor()
        assert hasattr(factor, "name")
        assert factor.name == "size"

    def test_正常系_description属性が定義されている(self) -> None:
        """SizeFactorにdescription属性が定義されていることを確認。"""
        factor = SizeFactor()
        assert hasattr(factor, "description")
        assert len(factor.description) > 0

    def test_正常系_category属性がSIZEである(self) -> None:
        """SizeFactorのcategoryがFactorCategory.SIZEであることを確認。"""
        from factor.enums import FactorCategory

        factor = SizeFactor()
        assert factor.category == FactorCategory.SIZE

    def test_正常系_computeメソッドが実装されている(self) -> None:
        """SizeFactorにcomputeメソッドが実装されていることを確認。"""
        factor = SizeFactor()
        assert hasattr(factor, "compute")
        assert callable(factor.compute)

    def test_正常系_validate_inputsメソッドが使用可能(self) -> None:
        """SizeFactorでvalidate_inputsメソッドが使用可能であることを確認。"""
        factor = SizeFactor()
        assert hasattr(factor, "validate_inputs")
        assert callable(factor.validate_inputs)


class TestSizeFactorInit:
    """SizeFactor初期化のテスト。"""

    def test_正常系_デフォルト値で初期化される(self) -> None:
        """デフォルトのmetric(market_cap)とinvert(False)とlog_transform(True)で初期化されることを確認。"""
        factor = SizeFactor()
        assert factor.metric == "market_cap"
        assert factor.invert is False
        assert factor.log_transform is True

    def test_正常系_metricにmarket_capを指定できる(self) -> None:
        """metric='market_cap'で初期化できることを確認。"""
        factor = SizeFactor(metric="market_cap")
        assert factor.metric == "market_cap"

    def test_正常系_metricにrevenueを指定できる(self) -> None:
        """metric='revenue'で初期化できることを確認。"""
        factor = SizeFactor(metric="revenue")
        assert factor.metric == "revenue"

    def test_正常系_metricにtotal_assetsを指定できる(self) -> None:
        """metric='total_assets'で初期化できることを確認。"""
        factor = SizeFactor(metric="total_assets")
        assert factor.metric == "total_assets"

    def test_正常系_invertにTrueを指定できる(self) -> None:
        """invert=Trueで初期化できることを確認。"""
        factor = SizeFactor(invert=True)
        assert factor.invert is True

    def test_正常系_log_transformにFalseを指定できる(self) -> None:
        """log_transform=Falseで初期化できることを確認。"""
        factor = SizeFactor(log_transform=False)
        assert factor.log_transform is False

    def test_正常系_全パラメータを同時に指定できる(self) -> None:
        """metric、invert、log_transformを同時に指定できることを確認。"""
        factor = SizeFactor(metric="revenue", invert=True, log_transform=False)
        assert factor.metric == "revenue"
        assert factor.invert is True
        assert factor.log_transform is False

    def test_異常系_無効なmetricでValidationError(self) -> None:
        """無効なmetricを指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            SizeFactor(metric="invalid_metric")

    def test_異常系_空文字metricでValidationError(self) -> None:
        """空文字のmetricを指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            SizeFactor(metric="")

    def test_正常系_VALID_METRICS定数が定義されている(self) -> None:
        """VALID_METRICS定数が正しく定義されていることを確認。"""
        assert hasattr(SizeFactor, "VALID_METRICS")
        expected_metrics = ("market_cap", "revenue", "total_assets")
        assert expected_metrics == SizeFactor.VALID_METRICS


class TestSizeFactorComputeMarketCap:
    """SizeFactor.compute()の時価総額計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = SizeFactor(metric="market_cap", invert=False, log_transform=True)

    def _create_mock_provider(self, market_cap_data: pd.DataFrame) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_market_cap.return_value = market_cap_data
        return provider

    def _create_market_cap_df(
        self,
        dates: list[str],
        symbols: list[str],
        values: dict[str, list[float]],
    ) -> pd.DataFrame:
        """時価総額DataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        data = {symbol: values[symbol] for symbol in symbols}
        return pd.DataFrame(data, index=index)

    def test_正常系_時価総額ファクター値が計算される(self) -> None:
        """時価総額ファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
        symbols = ["AAPL", "GOOGL", "MSFT"]
        # 時価総額（兆円単位相当）
        values = {
            "AAPL": [3.0e12, 3.1e12, 3.2e12],
            "GOOGL": [2.0e12, 2.1e12, 2.2e12],
            "MSFT": [2.5e12, 2.6e12, 2.7e12],
        }
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_provider(market_cap_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-03",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3  # 3日分
        assert list(result.columns) == symbols

    def test_正常系_log_transformがTrueの場合対数変換される(self) -> None:
        """log_transform=Trueの場合、対数変換されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["SMALL", "LARGE"]
        values = {"SMALL": [1.0e9, 1.0e9], "LARGE": [1.0e12, 1.0e12]}
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_provider(market_cap_df)

        factor_log = SizeFactor(metric="market_cap", invert=False, log_transform=True)
        result = factor_log.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 対数変換されていると値の差が小さくなる
        # log(1e12) - log(1e9) = 3 * log(10) ≈ 6.9
        diff = result.loc["2024-01-01", "LARGE"] - result.loc["2024-01-01", "SMALL"]
        assert diff < 10  # 対数変換されていれば差は10未満

    def test_正常系_log_transformがFalseの場合対数変換されない(self) -> None:
        """log_transform=Falseの場合、対数変換されないことを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["SMALL", "LARGE"]
        values = {"SMALL": [1.0e9, 1.0e9], "LARGE": [1.0e12, 1.0e12]}
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_provider(market_cap_df)

        factor_no_log = SizeFactor(
            metric="market_cap", invert=False, log_transform=False
        )
        result = factor_no_log.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 対数変換されていないと元の値がそのまま
        assert result.loc["2024-01-01", "LARGE"] == 1.0e12
        assert result.loc["2024-01-01", "SMALL"] == 1.0e9

    def test_正常系_invertがFalseの場合大型株が高スコア(self) -> None:
        """invert=Falseの場合、大型株が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["SMALL_CAP", "LARGE_CAP"]
        values = {"SMALL_CAP": [1.0e9, 1.0e9], "LARGE_CAP": [1.0e12, 1.0e12]}
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_provider(market_cap_df)

        factor = SizeFactor(metric="market_cap", invert=False)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 大型株の方が高スコア
        assert (
            result.loc["2024-01-01", "LARGE_CAP"]
            > result.loc["2024-01-01", "SMALL_CAP"]
        )

    def test_正常系_invertがTrueの場合小型株が高スコア(self) -> None:
        """invert=Trueの場合、小型株が高スコアになることを確認（小型株プレミアム）。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["SMALL_CAP", "LARGE_CAP"]
        values = {"SMALL_CAP": [1.0e9, 1.0e9], "LARGE_CAP": [1.0e12, 1.0e12]}
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_provider(market_cap_df)

        factor = SizeFactor(metric="market_cap", invert=True)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 小型株の方が高スコア（小型株プレミアム）
        assert (
            result.loc["2024-01-01", "SMALL_CAP"]
            > result.loc["2024-01-01", "LARGE_CAP"]
        )


class TestSizeFactorComputeRevenue:
    """SizeFactor.compute()の売上高計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = SizeFactor(metric="revenue", invert=False, log_transform=True)

    def _create_mock_provider(self, fundamentals_data: pd.DataFrame) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_fundamentals.return_value = fundamentals_data
        return provider

    def _create_fundamentals_df(
        self,
        dates: list[str],
        symbols: list[str],
        values: dict[str, list[float]],
    ) -> pd.DataFrame:
        """ファンダメンタルズDataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, ["revenue"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_売上高ファクター値が計算される(self) -> None:
        """売上高ファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        values = {
            "AAPL": [400e9, 410e9],
            "GOOGL": [300e9, 310e9],
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == symbols

    def test_正常系_高売上高銘柄が高スコアになる(self) -> None:
        """高売上高銘柄が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["HIGH_REV", "LOW_REV"]
        values = {"HIGH_REV": [500e9, 500e9], "LOW_REV": [50e9, 50e9]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = SizeFactor(metric="revenue", invert=False)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高売上高の方が高スコア
        assert (
            result.loc["2024-01-01", "HIGH_REV"] > result.loc["2024-01-01", "LOW_REV"]
        )


class TestSizeFactorComputeTotalAssets:
    """SizeFactor.compute()の総資産計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = SizeFactor(
            metric="total_assets", invert=False, log_transform=True
        )

    def _create_mock_provider(self, fundamentals_data: pd.DataFrame) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_fundamentals.return_value = fundamentals_data
        return provider

    def _create_fundamentals_df(
        self,
        dates: list[str],
        symbols: list[str],
        values: dict[str, list[float]],
    ) -> pd.DataFrame:
        """ファンダメンタルズDataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, ["total_assets"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_総資産ファクター値が計算される(self) -> None:
        """総資産ファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["BANK_A", "BANK_B"]
        values = {
            "BANK_A": [500e9, 510e9],
            "BANK_B": [300e9, 310e9],
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == symbols

    def test_正常系_高総資産銘柄が高スコアになる(self) -> None:
        """高総資産銘柄が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["HIGH_ASSETS", "LOW_ASSETS"]
        values = {"HIGH_ASSETS": [1e12, 1e12], "LOW_ASSETS": [100e9, 100e9]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = SizeFactor(metric="total_assets", invert=False)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高総資産の方が高スコア
        assert (
            result.loc["2024-01-01", "HIGH_ASSETS"]
            > result.loc["2024-01-01", "LOW_ASSETS"]
        )


class TestSizeFactorSmallCapPremium:
    """SizeFactor符号反転オプション（小型株プレミアム）のテスト。"""

    def _create_mock_market_cap_provider(
        self, market_cap_data: pd.DataFrame
    ) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_market_cap.return_value = market_cap_data
        return provider

    def _create_market_cap_df(
        self,
        dates: list[str],
        symbols: list[str],
        values: dict[str, list[float]],
    ) -> pd.DataFrame:
        """時価総額DataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        data = {symbol: values[symbol] for symbol in symbols}
        return pd.DataFrame(data, index=index)

    def test_正常系_invertがTrueで小型株プレミアムを実現(self) -> None:
        """invert=Trueで小型株が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["MICRO_CAP", "SMALL_CAP", "LARGE_CAP"]
        values = {
            "MICRO_CAP": [1.0e8, 1.0e8],  # マイクロキャップ
            "SMALL_CAP": [1.0e10, 1.0e10],  # スモールキャップ
            "LARGE_CAP": [1.0e12, 1.0e12],  # ラージキャップ
        }
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_market_cap_provider(market_cap_df)

        factor = SizeFactor(metric="market_cap", invert=True, log_transform=True)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # スコアの順序: MICRO_CAP > SMALL_CAP > LARGE_CAP
        assert (
            result.loc["2024-01-01", "MICRO_CAP"]
            > result.loc["2024-01-01", "SMALL_CAP"]
        )
        assert (
            result.loc["2024-01-01", "SMALL_CAP"]
            > result.loc["2024-01-01", "LARGE_CAP"]
        )

    def test_正常系_invertがFalseで大型株が高スコア(self) -> None:
        """invert=Falseで大型株が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["MICRO_CAP", "SMALL_CAP", "LARGE_CAP"]
        values = {
            "MICRO_CAP": [1.0e8, 1.0e8],
            "SMALL_CAP": [1.0e10, 1.0e10],
            "LARGE_CAP": [1.0e12, 1.0e12],
        }
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_market_cap_provider(market_cap_df)

        factor = SizeFactor(metric="market_cap", invert=False, log_transform=True)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # スコアの順序: LARGE_CAP > SMALL_CAP > MICRO_CAP
        assert (
            result.loc["2024-01-01", "LARGE_CAP"]
            > result.loc["2024-01-01", "SMALL_CAP"]
        )
        assert (
            result.loc["2024-01-01", "SMALL_CAP"]
            > result.loc["2024-01-01", "MICRO_CAP"]
        )


class TestSizeFactorDataFrameFormat:
    """SizeFactor戻り値のDataFrameフォーマットテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = SizeFactor(metric="market_cap")

    def _create_mock_provider(self, market_cap_data: pd.DataFrame) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_market_cap.return_value = market_cap_data
        return provider

    def _create_market_cap_df(
        self,
        dates: list[str],
        symbols: list[str],
    ) -> pd.DataFrame:
        """時価総額DataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        np.random.seed(42)
        data = {symbol: np.random.rand(len(dates)) * 1e12 for symbol in symbols}
        return pd.DataFrame(data, index=index)

    def test_正常系_戻り値がDataFrameである(self) -> None:
        """戻り値がpd.DataFrameであることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        market_cap_df = self._create_market_cap_df(dates, symbols)
        provider = self._create_mock_provider(market_cap_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_インデックスがDatetimeIndexである(self) -> None:
        """インデックスがDatetimeIndexであることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL"]
        market_cap_df = self._create_market_cap_df(dates, symbols)
        provider = self._create_mock_provider(market_cap_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_インデックス名がDateである(self) -> None:
        """インデックス名が'Date'であることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL"]
        market_cap_df = self._create_market_cap_df(dates, symbols)
        provider = self._create_mock_provider(market_cap_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result.index.name == "Date"

    def test_正常系_カラムがユニバースと一致する(self) -> None:
        """カラムがユニバースのシンボルと一致することを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL", "MSFT"]
        market_cap_df = self._create_market_cap_df(dates, symbols)
        provider = self._create_mock_provider(market_cap_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert list(result.columns) == symbols

    def test_正常系_値がfloat型である(self) -> None:
        """ファクター値がfloat型であることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL"]
        market_cap_df = self._create_market_cap_df(dates, symbols)
        provider = self._create_mock_provider(market_cap_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result.dtypes["AAPL"] is np.float64 or np.issubdtype(
            result.dtypes["AAPL"], np.floating
        )


class TestSizeFactorValidation:
    """SizeFactor入力バリデーションのテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = SizeFactor(metric="market_cap")

    def _create_mock_provider(self) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        return MagicMock()

    def test_異常系_空のユニバースでValidationError(self) -> None:
        """空のユニバースでValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        provider = self._create_mock_provider()

        with pytest.raises(ValidationError):
            self.factor.compute(
                provider=provider,
                universe=[],
                start_date="2024-01-01",
                end_date="2024-01-31",
            )

    def test_異常系_開始日が終了日より後でValidationError(self) -> None:
        """開始日が終了日より後の場合、ValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        provider = self._create_mock_provider()

        with pytest.raises(ValidationError):
            self.factor.compute(
                provider=provider,
                universe=["AAPL"],
                start_date="2024-12-31",
                end_date="2024-01-01",
            )

    def test_異常系_開始日と終了日が同じでValidationError(self) -> None:
        """開始日と終了日が同じ場合、ValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        provider = self._create_mock_provider()

        with pytest.raises(ValidationError):
            self.factor.compute(
                provider=provider,
                universe=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-01-01",
            )


class TestSizeFactorEdgeCases:
    """SizeFactorのエッジケーステスト。"""

    def _create_mock_market_cap_provider(
        self, market_cap_data: pd.DataFrame
    ) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_market_cap.return_value = market_cap_data
        return provider

    def _create_market_cap_df(
        self,
        dates: list[str],
        symbols: list[str],
        values: dict[str, list[float]],
    ) -> pd.DataFrame:
        """時価総額DataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        data = {symbol: values[symbol] for symbol in symbols}
        return pd.DataFrame(data, index=index)

    def test_正常系_NaN値を含むデータの処理(self) -> None:
        """NaN値を含むデータでも正しく処理されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        values = {
            "AAPL": [1.0e12, np.nan],
            "GOOGL": [2.0e12, 2.5e12],
        }
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_market_cap_provider(market_cap_df)
        factor = SizeFactor(metric="market_cap")

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # NaN値を含む行も処理される
        assert pd.isna(result.loc["2024-01-02", "AAPL"])
        assert not pd.isna(result.loc["2024-01-02", "GOOGL"])

    def test_正常系_ゼロ値を含むデータの処理_log_transformあり(self) -> None:
        """ゼロ値を含むデータで対数変換時の処理を確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["ZERO", "POSITIVE"]
        values = {"ZERO": [0.0, 0.0], "POSITIVE": [1.0e12, 1.0e12]}
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_market_cap_provider(market_cap_df)
        factor = SizeFactor(metric="market_cap", log_transform=True)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # ゼロ値の対数はNaNまたは-infになるが、処理自体は成功する
        assert isinstance(result, pd.DataFrame)

    def test_正常系_負の値を含むデータの処理(self) -> None:
        """負の値を含むデータでも処理されることを確認（異常データ）。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["NEGATIVE", "POSITIVE"]
        values = {"NEGATIVE": [-1.0e9, -1.0e9], "POSITIVE": [1.0e12, 1.0e12]}
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_market_cap_provider(market_cap_df)
        factor = SizeFactor(metric="market_cap", log_transform=False)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # エラーにならずに処理される
        assert isinstance(result, pd.DataFrame)

    def test_正常系_日付文字列とdatetimeの両方を受け付ける(self) -> None:
        """日付がstr形式とdatetime形式の両方で受け付けられることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL"]
        values = {"AAPL": [1.0e12, 1.1e12]}
        market_cap_df = self._create_market_cap_df(dates, symbols, values)
        provider = self._create_mock_market_cap_provider(market_cap_df)
        factor = SizeFactor(metric="market_cap")

        # 文字列形式
        result_str = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # datetime形式
        result_dt = factor.compute(
            provider=provider,
            universe=symbols,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
        )

        assert isinstance(result_str, pd.DataFrame)
        assert isinstance(result_dt, pd.DataFrame)


class TestSizeFactorMetadata:
    """SizeFactorメタデータのテスト。"""

    def test_正常系_metadataプロパティが存在する(self) -> None:
        """metadataプロパティが存在することを確認。"""
        factor = SizeFactor()
        assert hasattr(factor, "metadata")

    def test_正常系_metadata_nameがsizeである(self) -> None:
        """metadata.nameが'size'であることを確認。"""
        factor = SizeFactor()
        assert factor.metadata.name == "size"

    def test_正常系_metadata_categoryがsizeである(self) -> None:
        """metadata.categoryが'size'であることを確認。"""
        factor = SizeFactor()
        assert factor.metadata.category == "size"

    def test_正常系_metadataがFactorMetadata型である(self) -> None:
        """metadataがFactorMetadata型であることを確認。"""
        from factor.core.base import FactorMetadata

        factor = SizeFactor()
        assert isinstance(factor.metadata, FactorMetadata)


class TestSizeFactorMetricSelection:
    """metric パラメータによる指標選択テスト。"""

    def test_正常系_market_cap選択時にget_market_capが呼ばれる(self) -> None:
        """metric='market_cap'の場合、get_market_capが呼ばれることを確認。"""
        provider = MagicMock()
        index = pd.DatetimeIndex(["2024-01-01", "2024-01-02"], name="Date")
        provider.get_market_cap.return_value = pd.DataFrame(
            {"AAPL": [1e12, 1.1e12]}, index=index
        )

        factor = SizeFactor(metric="market_cap")
        factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        provider.get_market_cap.assert_called_once()
        provider.get_fundamentals.assert_not_called()

    def test_正常系_revenue選択時にget_fundamentalsが呼ばれる(self) -> None:
        """metric='revenue'の場合、get_fundamentalsが呼ばれることを確認。"""
        provider = MagicMock()
        index = pd.DatetimeIndex(["2024-01-01", "2024-01-02"], name="Date")
        columns = pd.MultiIndex.from_product(
            [["AAPL"], ["revenue"]], names=["symbol", "metric"]
        )
        provider.get_fundamentals.return_value = pd.DataFrame(
            [[100e9], [110e9]], index=index, columns=columns
        )

        factor = SizeFactor(metric="revenue")
        factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        provider.get_fundamentals.assert_called_once()
        provider.get_market_cap.assert_not_called()

    def test_正常系_total_assets選択時にget_fundamentalsが呼ばれる(self) -> None:
        """metric='total_assets'の場合、get_fundamentalsが呼ばれることを確認。"""
        provider = MagicMock()
        index = pd.DatetimeIndex(["2024-01-01", "2024-01-02"], name="Date")
        columns = pd.MultiIndex.from_product(
            [["AAPL"], ["total_assets"]], names=["symbol", "metric"]
        )
        provider.get_fundamentals.return_value = pd.DataFrame(
            [[500e9], [510e9]], index=index, columns=columns
        )

        factor = SizeFactor(metric="total_assets")
        factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        provider.get_fundamentals.assert_called_once()
        provider.get_market_cap.assert_not_called()
