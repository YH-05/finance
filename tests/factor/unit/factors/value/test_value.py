"""Unit tests for ValueFactor class.

ValueFactorはPER、PBR、配当利回り、EV/EBITDAなどの
バリュー指標を計算するファクタークラスである。
"""

from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: 実装が存在しないため、インポートは失敗する（Red状態）
# pytest.importorskipを使用して、実装後に自動的にテストが有効になる
value_module = pytest.importorskip("factor.factors.value.value")
ValueFactor = value_module.ValueFactor


class TestValueFactorInheritance:
    """ValueFactorがFactor基底クラスを正しく継承していることのテスト。"""

    def test_正常系_Factor基底クラスを継承している(self) -> None:
        """ValueFactorがFactor基底クラスを継承していることを確認。"""
        from factor.core.base import Factor

        factor = ValueFactor()
        assert isinstance(factor, Factor)

    def test_正常系_name属性が定義されている(self) -> None:
        """ValueFactorにname属性が定義されていることを確認。"""
        factor = ValueFactor()
        assert hasattr(factor, "name")
        assert factor.name == "value"

    def test_正常系_description属性が定義されている(self) -> None:
        """ValueFactorにdescription属性が定義されていることを確認。"""
        factor = ValueFactor()
        assert hasattr(factor, "description")
        assert len(factor.description) > 0

    def test_正常系_category属性がVALUEである(self) -> None:
        """ValueFactorのcategoryがFactorCategory.VALUEであることを確認。"""
        from factor.enums import FactorCategory

        factor = ValueFactor()
        assert factor.category == FactorCategory.VALUE

    def test_正常系_computeメソッドが実装されている(self) -> None:
        """ValueFactorにcomputeメソッドが実装されていることを確認。"""
        factor = ValueFactor()
        assert hasattr(factor, "compute")
        assert callable(factor.compute)

    def test_正常系_validate_inputsメソッドが使用可能(self) -> None:
        """ValueFactorでvalidate_inputsメソッドが使用可能であることを確認。"""
        factor = ValueFactor()
        assert hasattr(factor, "validate_inputs")
        assert callable(factor.validate_inputs)


class TestValueFactorInit:
    """ValueFactor初期化のテスト。"""

    def test_正常系_デフォルト値で初期化される(self) -> None:
        """デフォルトのmetric(per)とinvert(True)で初期化されることを確認。"""
        factor = ValueFactor()
        assert factor.metric == "per"
        assert factor.invert is True

    def test_正常系_metricにperを指定できる(self) -> None:
        """metric='per'で初期化できることを確認。"""
        factor = ValueFactor(metric="per")
        assert factor.metric == "per"

    def test_正常系_metricにpbrを指定できる(self) -> None:
        """metric='pbr'で初期化できることを確認。"""
        factor = ValueFactor(metric="pbr")
        assert factor.metric == "pbr"

    def test_正常系_metricにdividend_yieldを指定できる(self) -> None:
        """metric='dividend_yield'で初期化できることを確認。"""
        factor = ValueFactor(metric="dividend_yield")
        assert factor.metric == "dividend_yield"

    def test_正常系_metricにev_ebitdaを指定できる(self) -> None:
        """metric='ev_ebitda'で初期化できることを確認。"""
        factor = ValueFactor(metric="ev_ebitda")
        assert factor.metric == "ev_ebitda"

    def test_正常系_invertにFalseを指定できる(self) -> None:
        """invert=Falseで初期化できることを確認。"""
        factor = ValueFactor(invert=False)
        assert factor.invert is False

    def test_正常系_metricとinvertを同時に指定できる(self) -> None:
        """metricとinvertを同時に指定できることを確認。"""
        factor = ValueFactor(metric="pbr", invert=False)
        assert factor.metric == "pbr"
        assert factor.invert is False

    def test_異常系_無効なmetricでValidationError(self) -> None:
        """無効なmetricを指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            ValueFactor(metric="invalid_metric")

    def test_異常系_空文字metricでValidationError(self) -> None:
        """空文字のmetricを指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            ValueFactor(metric="")

    def test_正常系_VALID_METRICS定数が定義されている(self) -> None:
        """VALID_METRICS定数が正しく定義されていることを確認。"""
        assert hasattr(ValueFactor, "VALID_METRICS")
        expected_metrics = ("per", "pbr", "dividend_yield", "ev_ebitda")
        assert expected_metrics == ValueFactor.VALID_METRICS


class TestValueFactorComputePER:
    """ValueFactor.compute()のPER計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = ValueFactor(metric="per", invert=True)

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
        # MultiIndex DataFrame構造を作成
        # Index: Date, Columns: (symbol, metric)
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, ["per"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_PERファクター値が計算される(self) -> None:
        """PERファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
        symbols = ["AAPL", "GOOGL", "MSFT"]
        values = {
            "AAPL": [15.0, 16.0, 17.0],
            "GOOGL": [20.0, 21.0, 22.0],
            "MSFT": [25.0, 26.0, 27.0],
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-03",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3  # 3日分
        assert list(result.columns) == symbols

    def test_正常系_invertがTrueの場合符号が反転する(self) -> None:
        """invert=Trueの場合、ファクター値の符号が反転することを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        values = {"AAPL": [15.0, 15.0], "GOOGL": [30.0, 30.0]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor_inverted = ValueFactor(metric="per", invert=True)
        result = factor_inverted.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 低PER（AAPL=15）の方が高スコアになる
        assert result.loc["2024-01-01", "AAPL"] > result.loc["2024-01-01", "GOOGL"]

    def test_正常系_invertがFalseの場合符号が反転しない(self) -> None:
        """invert=Falseの場合、元の値が維持されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        values = {"AAPL": [15.0, 15.0], "GOOGL": [30.0, 30.0]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor_not_inverted = ValueFactor(metric="per", invert=False)
        result = factor_not_inverted.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高PER（GOOGL=30）の方が高スコアになる
        assert result.loc["2024-01-01", "GOOGL"] > result.loc["2024-01-01", "AAPL"]


class TestValueFactorComputePBR:
    """ValueFactor.compute()のPBR計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = ValueFactor(metric="pbr", invert=True)

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
            [symbols, ["pbr"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_PBRファクター値が計算される(self) -> None:
        """PBRファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        values = {
            "AAPL": [1.5, 1.6],
            "GOOGL": [2.0, 2.1],
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

    def test_正常系_低PBR銘柄が高スコアになる(self) -> None:
        """invert=Trueで低PBR銘柄が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["LOW_PBR", "HIGH_PBR"]
        values = {"LOW_PBR": [0.8, 0.8], "HIGH_PBR": [3.0, 3.0]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 低PBRの方が高スコア
        assert (
            result.loc["2024-01-01", "LOW_PBR"] > result.loc["2024-01-01", "HIGH_PBR"]
        )


class TestValueFactorComputeDividendYield:
    """ValueFactor.compute()の配当利回り計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        # 配当利回りは高い方が良いのでinvert=False
        self.factor = ValueFactor(metric="dividend_yield", invert=False)

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
            [symbols, ["dividend_yield"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_配当利回りファクター値が計算される(self) -> None:
        """配当利回りファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["HIGH_YIELD", "LOW_YIELD"]
        values = {"HIGH_YIELD": [0.05, 0.05], "LOW_YIELD": [0.01, 0.01]}
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

    def test_正常系_高配当利回り銘柄が高スコアになる(self) -> None:
        """高配当利回り銘柄が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["HIGH_YIELD", "LOW_YIELD"]
        values = {"HIGH_YIELD": [0.05, 0.05], "LOW_YIELD": [0.01, 0.01]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高配当利回りの方が高スコア
        assert (
            result.loc["2024-01-01", "HIGH_YIELD"]
            > result.loc["2024-01-01", "LOW_YIELD"]
        )


class TestValueFactorComputeEVEBITDA:
    """ValueFactor.compute()のEV/EBITDA計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = ValueFactor(metric="ev_ebitda", invert=True)

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
            [symbols, ["ev_ebitda"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_EV_EBITDAファクター値が計算される(self) -> None:
        """EV/EBITDAファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["LOW_EV", "HIGH_EV"]
        values = {"LOW_EV": [5.0, 5.0], "HIGH_EV": [15.0, 15.0]}
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

    def test_正常系_低EV_EBITDA銘柄が高スコアになる(self) -> None:
        """低EV/EBITDA銘柄が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["LOW_EV", "HIGH_EV"]
        values = {"LOW_EV": [5.0, 5.0], "HIGH_EV": [15.0, 15.0]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 低EV/EBITDAの方が高スコア
        assert result.loc["2024-01-01", "LOW_EV"] > result.loc["2024-01-01", "HIGH_EV"]

    def test_正常系_EV_EBITDAデータが欠損の場合NaN(self) -> None:
        """EV/EBITDAデータが欠損の場合、NaNが返されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["VALID", "MISSING"]
        values = {"VALID": [10.0, 10.0], "MISSING": [np.nan, np.nan]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert not pd.isna(result.loc["2024-01-01", "VALID"])
        assert pd.isna(result.loc["2024-01-01", "MISSING"])


class TestValueFactorDataFrameFormat:
    """ValueFactor戻り値のDataFrameフォーマットテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = ValueFactor(metric="per")

    def _create_mock_provider(self, fundamentals_data: pd.DataFrame) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_fundamentals.return_value = fundamentals_data
        return provider

    def _create_fundamentals_df(
        self,
        dates: list[str],
        symbols: list[str],
        metric: str,
    ) -> pd.DataFrame:
        """ファンダメンタルズDataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, [metric]],
            names=["symbol", "metric"],
        )
        np.random.seed(42)
        data = np.random.rand(len(dates), len(symbols)) * 20 + 5
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_戻り値がDataFrameである(self) -> None:
        """戻り値がpd.DataFrameであることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per")
        provider = self._create_mock_provider(fundamentals_df)

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
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per")
        provider = self._create_mock_provider(fundamentals_df)

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
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per")
        provider = self._create_mock_provider(fundamentals_df)

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
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per")
        provider = self._create_mock_provider(fundamentals_df)

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
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per")
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result.dtypes["AAPL"] is np.float64 or np.issubdtype(
            result.dtypes["AAPL"], np.floating
        )


class TestValueFactorValidation:
    """ValueFactor入力バリデーションのテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = ValueFactor(metric="per")

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


class TestValueFactorEdgeCases:
    """ValueFactorのエッジケーステスト。"""

    def _create_mock_provider(self, fundamentals_data: pd.DataFrame) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_fundamentals.return_value = fundamentals_data
        return provider

    def _create_fundamentals_df(
        self,
        dates: list[str],
        symbols: list[str],
        metric: str,
        values: dict[str, list[float]],
    ) -> pd.DataFrame:
        """ファンダメンタルズDataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, [metric]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_NaN値を含むデータの処理(self) -> None:
        """NaN値を含むデータでも正しく処理されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        values = {
            "AAPL": [15.0, np.nan],
            "GOOGL": [20.0, 25.0],
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per", values)
        provider = self._create_mock_provider(fundamentals_df)
        factor = ValueFactor(metric="per")

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # NaN値を含む行も処理される
        assert pd.isna(result.loc["2024-01-02", "AAPL"])
        assert not pd.isna(result.loc["2024-01-02", "GOOGL"])

    def test_正常系_ゼロ値を含むデータの処理(self) -> None:
        """ゼロ値を含むデータでも正しく処理されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["ZERO", "POSITIVE"]
        values = {"ZERO": [0.0, 0.0], "POSITIVE": [10.0, 10.0]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per", values)
        provider = self._create_mock_provider(fundamentals_df)
        factor = ValueFactor(metric="per", invert=True)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # ゼロ値も処理される（エラーにならない）
        assert isinstance(result, pd.DataFrame)

    def test_正常系_負のPER値を含むデータの処理(self) -> None:
        """負のPER値（赤字企業）を含むデータでも処理されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["NEGATIVE", "POSITIVE"]
        values = {"NEGATIVE": [-5.0, -5.0], "POSITIVE": [15.0, 15.0]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per", values)
        provider = self._create_mock_provider(fundamentals_df)
        factor = ValueFactor(metric="per", invert=True)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_日付文字列とdatetimeの両方を受け付ける(self) -> None:
        """日付がstr形式とdatetime形式の両方で受け付けられることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL"]
        values = {"AAPL": [15.0, 16.0]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "per", values)
        provider = self._create_mock_provider(fundamentals_df)
        factor = ValueFactor(metric="per")

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


class TestValueFactorMetadata:
    """ValueFactorメタデータのテスト。"""

    def test_正常系_metadataプロパティが存在する(self) -> None:
        """metadataプロパティが存在することを確認。"""
        factor = ValueFactor()
        assert hasattr(factor, "metadata")

    def test_正常系_metadata_nameがvalueである(self) -> None:
        """metadata.nameが'value'であることを確認。"""
        factor = ValueFactor()
        assert factor.metadata.name == "value"

    def test_正常系_metadata_categoryがvalueである(self) -> None:
        """metadata.categoryが'value'であることを確認。"""
        factor = ValueFactor()
        assert factor.metadata.category == "value"

    def test_正常系_metadataがFactorMetadata型である(self) -> None:
        """metadataがFactorMetadata型であることを確認。"""
        from factor.core.base import FactorMetadata

        factor = ValueFactor()
        assert isinstance(factor.metadata, FactorMetadata)
