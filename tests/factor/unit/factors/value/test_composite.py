"""Unit tests for CompositeValueFactor class.

CompositeValueFactorは複数のバリュー指標（PER、PBR、配当利回り、EV/EBITDA）を
組み合わせた複合バリューファクターを計算するクラスである。

Issue #127: [factor] T13: CompositeValueFactor (factors/value/composite.py)
"""

from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: 実装が存在しないため、インポートは失敗する（Red状態）
# pytest.importorskipを使用して、実装後に自動的にテストが有効になる
composite_module = pytest.importorskip("factor.factors.value.composite")
CompositeValueFactor = composite_module.CompositeValueFactor


class TestCompositeValueFactorInheritance:
    """CompositeValueFactorがFactor基底クラスを正しく継承していることのテスト。"""

    def test_正常系_Factor基底クラスを継承している(self) -> None:
        """CompositeValueFactorがFactor基底クラスを継承していることを確認。"""
        from factor.core.base import Factor

        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert isinstance(factor, Factor)

    def test_正常系_name属性が定義されている(self) -> None:
        """CompositeValueFactorにname属性が定義されていることを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert hasattr(factor, "name")
        assert factor.name == "composite_value"

    def test_正常系_description属性が定義されている(self) -> None:
        """CompositeValueFactorにdescription属性が定義されていることを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert hasattr(factor, "description")
        assert len(factor.description) > 0

    def test_正常系_category属性がVALUEである(self) -> None:
        """CompositeValueFactorのcategoryがFactorCategory.VALUEであることを確認。"""
        from factor.enums import FactorCategory

        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert factor.category == FactorCategory.VALUE

    def test_正常系_computeメソッドが実装されている(self) -> None:
        """CompositeValueFactorにcomputeメソッドが実装されていることを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert hasattr(factor, "compute")
        assert callable(factor.compute)

    def test_正常系_validate_inputsメソッドが使用可能(self) -> None:
        """CompositeValueFactorでvalidate_inputsメソッドが使用可能であることを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert hasattr(factor, "validate_inputs")
        assert callable(factor.validate_inputs)


class TestCompositeValueFactorInit:
    """CompositeValueFactor初期化のテスト。"""

    def test_正常系_2つの指標で初期化できる(self) -> None:
        """2つの指標リストで初期化できることを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert factor.metrics == ["per", "pbr"]

    def test_正常系_全4指標で初期化できる(self) -> None:
        """全4指標で初期化できることを確認。"""
        metrics = ["per", "pbr", "dividend_yield", "ev_ebitda"]
        factor = CompositeValueFactor(metrics=metrics)
        assert factor.metrics == metrics

    def test_正常系_weightsなしでデフォルト等ウェイト(self) -> None:
        """weightsを指定しない場合、等ウェイトになることを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        # 等ウェイトなのでweightsはNoneまたは[0.5, 0.5]となる
        # 実装によっては内部でNoneのままかもしれないので、両方許容
        if factor.weights is not None:
            assert factor.weights == [0.5, 0.5]

    def test_正常系_カスタムウェイトを指定できる(self) -> None:
        """カスタムウェイトを指定できることを確認。"""
        factor = CompositeValueFactor(
            metrics=["per", "pbr"],
            weights=[0.7, 0.3],
        )
        assert factor.weights == [0.7, 0.3]

    def test_正常系_3つの指標とウェイトで初期化できる(self) -> None:
        """3つの指標とウェイトで初期化できることを確認。"""
        factor = CompositeValueFactor(
            metrics=["per", "pbr", "dividend_yield"],
            weights=[0.4, 0.4, 0.2],
        )
        assert factor.metrics == ["per", "pbr", "dividend_yield"]
        assert factor.weights == [0.4, 0.4, 0.2]

    def test_正常系_VALID_METRICS定数が定義されている(self) -> None:
        """VALID_METRICS定数が正しく定義されていることを確認。"""
        assert hasattr(CompositeValueFactor, "VALID_METRICS")
        expected_metrics = ("per", "pbr", "dividend_yield", "ev_ebitda")
        assert expected_metrics == CompositeValueFactor.VALID_METRICS

    def test_異常系_無効な指標名でValidationError(self) -> None:
        """無効な指標名を指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            CompositeValueFactor(metrics=["per", "invalid_metric"])

    def test_異常系_空の指標リストでValidationError(self) -> None:
        """空の指標リストを指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            CompositeValueFactor(metrics=[])

    def test_異常系_ウェイトと指標数が不一致でValidationError(self) -> None:
        """ウェイトの数と指標の数が一致しない場合ValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            CompositeValueFactor(
                metrics=["per", "pbr"],
                weights=[0.5, 0.3, 0.2],  # 3つのウェイトだが指標は2つ
            )

    def test_正常系_ウェイト合計が1でなくても動作する(self) -> None:
        """ウェイトの合計が1でなくても動作する（警告は出るかもしれないが例外は発生しない）。"""
        # ウェイトの合計が0.8でもエラーにはならない
        factor = CompositeValueFactor(
            metrics=["per", "pbr"],
            weights=[0.5, 0.3],  # 合計0.8
        )
        assert factor.weights == [0.5, 0.3]


class TestCompositeValueFactorCompute:
    """CompositeValueFactor.compute()の基本テスト。"""

    def _create_mock_provider(
        self,
        fundamentals_data: pd.DataFrame,
    ) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_fundamentals.return_value = fundamentals_data
        return provider

    def _create_fundamentals_df(
        self,
        dates: list[str],
        symbols: list[str],
        metrics: list[str],
        values: dict[str, dict[str, list[float]]],
    ) -> pd.DataFrame:
        """ファンダメンタルズDataFrameを作成するヘルパーメソッド。

        Parameters
        ----------
        dates : list[str]
            日付リスト
        symbols : list[str]
            シンボルリスト
        metrics : list[str]
            指標リスト
        values : dict[str, dict[str, list[float]]]
            values[symbol][metric] = [values...]

        Returns
        -------
        pd.DataFrame
            MultiIndex columns (symbol, metric) のDataFrame
        """
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, metrics],
            names=["symbol", "metric"],
        )

        data = []
        for symbol in symbols:
            for metric in metrics:
                data.append(values[symbol][metric])

        # Transpose to get dates as rows
        df = pd.DataFrame(
            np.array(data).T,
            index=index,
            columns=columns,
        )
        return df

    def test_正常系_デフォルト等ウェイトで複合ファクターを計算できる(self) -> None:
        """デフォルト等ウェイトで複合ファクター値が計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        metrics = ["per", "pbr"]
        values = {
            "AAPL": {"per": [15.0, 16.0], "pbr": [1.5, 1.6]},
            "GOOGL": {"per": [20.0, 21.0], "pbr": [2.0, 2.1]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=["per", "pbr"])
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == symbols

    def test_正常系_カスタムウェイトで複合ファクターを計算できる(self) -> None:
        """カスタムウェイトで複合ファクター値が計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        metrics = ["per", "pbr"]
        values = {
            "AAPL": {"per": [15.0, 16.0], "pbr": [1.5, 1.6]},
            "GOOGL": {"per": [20.0, 21.0], "pbr": [2.0, 2.1]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(
            metrics=["per", "pbr"],
            weights=[0.7, 0.3],
        )
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_正常系_3つの指標で複合ファクターを計算できる(self) -> None:
        """3つの指標で複合ファクター値が計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        metrics = ["per", "pbr", "dividend_yield"]
        values = {
            "AAPL": {
                "per": [15.0, 16.0],
                "pbr": [1.5, 1.6],
                "dividend_yield": [0.02, 0.02],
            },
            "GOOGL": {
                "per": [20.0, 21.0],
                "pbr": [2.0, 2.1],
                "dividend_yield": [0.01, 0.01],
            },
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == symbols

    def test_正常系_全4指標で複合ファクターを計算できる(self) -> None:
        """全4指標で複合ファクター値が計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        metrics = ["per", "pbr", "dividend_yield", "ev_ebitda"]
        values = {
            "AAPL": {
                "per": [15.0, 16.0],
                "pbr": [1.5, 1.6],
                "dividend_yield": [0.02, 0.02],
                "ev_ebitda": [10.0, 10.5],
            },
            "GOOGL": {
                "per": [20.0, 21.0],
                "pbr": [2.0, 2.1],
                "dividend_yield": [0.01, 0.01],
                "ev_ebitda": [12.0, 12.5],
            },
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == symbols


class TestCompositeValueFactorNormalization:
    """CompositeValueFactorの各指標正規化テスト。"""

    def _create_mock_provider(
        self,
        fundamentals_data: pd.DataFrame,
    ) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_fundamentals.return_value = fundamentals_data
        return provider

    def _create_fundamentals_df(
        self,
        dates: list[str],
        symbols: list[str],
        metrics: list[str],
        values: dict[str, dict[str, list[float]]],
    ) -> pd.DataFrame:
        """ファンダメンタルズDataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, metrics],
            names=["symbol", "metric"],
        )

        data = []
        for symbol in symbols:
            for metric in metrics:
                data.append(values[symbol][metric])

        df = pd.DataFrame(
            np.array(data).T,
            index=index,
            columns=columns,
        )
        return df

    def test_正常系_各指標が正規化されてから合成される(self) -> None:
        """各指標が正規化（z-scoreまたはpercentile rank）されてから合成されることを確認。

        正規化により、スケールの異なる指標（PER: 10-30 vs PBR: 0.5-3.0）が
        同等に扱われる。
        """
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["LOW_VALUE", "MID_VALUE", "HIGH_VALUE"]
        metrics = ["per", "pbr"]

        # PERとPBRでスケールが異なるが、正規化後は同等に扱われるべき
        values = {
            "LOW_VALUE": {
                "per": [10.0, 10.0],
                "pbr": [0.5, 0.5],
            },  # 低PER、低PBR（良い）
            "MID_VALUE": {"per": [20.0, 20.0], "pbr": [1.5, 1.5]},  # 中程度
            "HIGH_VALUE": {
                "per": [30.0, 30.0],
                "pbr": [3.0, 3.0],
            },  # 高PER、高PBR（悪い）
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 低PER・低PBR（LOW_VALUE）が最高スコアになるはず
        # 高PER・高PBR（HIGH_VALUE）が最低スコアになるはず
        assert (
            result.loc["2024-01-01", "LOW_VALUE"]
            > result.loc["2024-01-01", "MID_VALUE"]
        )
        assert (
            result.loc["2024-01-01", "MID_VALUE"]
            > result.loc["2024-01-01", "HIGH_VALUE"]
        )

    def test_正常系_ウェイトが異なると結果が変わる(self) -> None:
        """異なるウェイトで異なる結果が得られることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["A", "B"]
        metrics = ["per", "pbr"]

        # AはPER良好だがPBR悪い、BはPER悪いがPBR良好
        values = {
            "A": {
                "per": [10.0, 10.0],
                "pbr": [3.0, 3.0],
            },  # 低PER（良い）、高PBR（悪い）
            "B": {
                "per": [30.0, 30.0],
                "pbr": [0.5, 0.5],
            },  # 高PER（悪い）、低PBR（良い）
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)

        provider1 = self._create_mock_provider(fundamentals_df)
        provider2 = self._create_mock_provider(fundamentals_df)

        # PER重視
        factor_per_heavy = CompositeValueFactor(
            metrics=metrics,
            weights=[0.9, 0.1],
        )
        result_per_heavy = factor_per_heavy.compute(
            provider=provider1,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # PBR重視
        factor_pbr_heavy = CompositeValueFactor(
            metrics=metrics,
            weights=[0.1, 0.9],
        )
        result_pbr_heavy = factor_pbr_heavy.compute(
            provider=provider2,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # PER重視ならAが良い、PBR重視ならBが良い
        assert (
            result_per_heavy.loc["2024-01-01", "A"]
            > result_per_heavy.loc["2024-01-01", "B"]
        )
        assert (
            result_pbr_heavy.loc["2024-01-01", "B"]
            > result_pbr_heavy.loc["2024-01-01", "A"]
        )


class TestCompositeValueFactorDataFrameFormat:
    """CompositeValueFactor戻り値のDataFrameフォーマットテスト。"""

    def _create_mock_provider(
        self,
        fundamentals_data: pd.DataFrame,
    ) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_fundamentals.return_value = fundamentals_data
        return provider

    def _create_fundamentals_df(
        self,
        dates: list[str],
        symbols: list[str],
        metrics: list[str],
    ) -> pd.DataFrame:
        """ファンダメンタルズDataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, metrics],
            names=["symbol", "metric"],
        )
        np.random.seed(42)
        data = np.random.rand(len(dates), len(symbols) * len(metrics)) * 20 + 5
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_戻り値がDataFrameである(self) -> None:
        """戻り値がpd.DataFrameであることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        metrics = ["per", "pbr"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
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
        metrics = ["per", "pbr"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
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
        metrics = ["per", "pbr"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
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
        metrics = ["per", "pbr"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
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
        metrics = ["per", "pbr"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result.dtypes["AAPL"] is np.float64 or np.issubdtype(
            result.dtypes["AAPL"], np.floating
        )


class TestCompositeValueFactorValidation:
    """CompositeValueFactor入力バリデーションのテスト。"""

    def _create_mock_provider(self) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        return MagicMock()

    def test_異常系_空のユニバースでValidationError(self) -> None:
        """空のユニバースでValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        provider = self._create_mock_provider()
        factor = CompositeValueFactor(metrics=["per", "pbr"])

        with pytest.raises(ValidationError):
            factor.compute(
                provider=provider,
                universe=[],
                start_date="2024-01-01",
                end_date="2024-01-31",
            )

    def test_異常系_開始日が終了日より後でValidationError(self) -> None:
        """開始日が終了日より後の場合、ValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        provider = self._create_mock_provider()
        factor = CompositeValueFactor(metrics=["per", "pbr"])

        with pytest.raises(ValidationError):
            factor.compute(
                provider=provider,
                universe=["AAPL"],
                start_date="2024-12-31",
                end_date="2024-01-01",
            )

    def test_異常系_開始日と終了日が同じでValidationError(self) -> None:
        """開始日と終了日が同じ場合、ValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        provider = self._create_mock_provider()
        factor = CompositeValueFactor(metrics=["per", "pbr"])

        with pytest.raises(ValidationError):
            factor.compute(
                provider=provider,
                universe=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-01-01",
            )


class TestCompositeValueFactorEdgeCases:
    """CompositeValueFactorのエッジケーステスト。"""

    def _create_mock_provider(
        self,
        fundamentals_data: pd.DataFrame,
    ) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        provider = MagicMock()
        provider.get_fundamentals.return_value = fundamentals_data
        return provider

    def _create_fundamentals_df(
        self,
        dates: list[str],
        symbols: list[str],
        metrics: list[str],
        values: dict[str, dict[str, list[float]]],
    ) -> pd.DataFrame:
        """ファンダメンタルズDataFrameを作成するヘルパーメソッド。"""
        index = pd.DatetimeIndex(dates, name="Date")
        columns = pd.MultiIndex.from_product(
            [symbols, metrics],
            names=["symbol", "metric"],
        )

        data = []
        for symbol in symbols:
            for metric in metrics:
                data.append(values[symbol][metric])

        df = pd.DataFrame(
            np.array(data).T,
            index=index,
            columns=columns,
        )
        return df

    def test_正常系_NaN値を含むデータの処理(self) -> None:
        """NaN値を含むデータでも正しく処理されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        metrics = ["per", "pbr"]
        values = {
            "AAPL": {"per": [15.0, np.nan], "pbr": [1.5, 1.6]},
            "GOOGL": {"per": [20.0, 21.0], "pbr": [2.0, 2.1]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # NaN値を含む場合は結果もNaNになることがある
        assert isinstance(result, pd.DataFrame)

    def test_正常系_日付文字列とdatetimeの両方を受け付ける(self) -> None:
        """日付がstr形式とdatetime形式の両方で受け付けられることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL"]
        metrics = ["per", "pbr"]
        values = {
            "AAPL": {"per": [15.0, 16.0], "pbr": [1.5, 1.6]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider1 = self._create_mock_provider(fundamentals_df)
        provider2 = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=metrics)

        # 文字列形式
        result_str = factor.compute(
            provider=provider1,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # datetime形式
        result_dt = factor.compute(
            provider=provider2,
            universe=symbols,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
        )

        assert isinstance(result_str, pd.DataFrame)
        assert isinstance(result_dt, pd.DataFrame)

    def test_正常系_1つの指標のみでも動作する(self) -> None:
        """1つの指標のみでも複合ファクターとして動作することを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        metrics = ["per"]
        values = {
            "AAPL": {"per": [15.0, 16.0]},
            "GOOGL": {"per": [20.0, 21.0]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeValueFactor(metrics=["per"])
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)


class TestCompositeValueFactorMetadata:
    """CompositeValueFactorメタデータのテスト。"""

    def test_正常系_metadataプロパティが存在する(self) -> None:
        """metadataプロパティが存在することを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert hasattr(factor, "metadata")

    def test_正常系_metadata_nameがcomposite_valueである(self) -> None:
        """metadata.nameが'composite_value'であることを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert factor.metadata.name == "composite_value"

    def test_正常系_metadata_categoryがvalueである(self) -> None:
        """metadata.categoryが'value'であることを確認。"""
        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert factor.metadata.category == "value"

    def test_正常系_metadataがFactorMetadata型である(self) -> None:
        """metadataがFactorMetadata型であることを確認。"""
        from factor.core.base import FactorMetadata

        factor = CompositeValueFactor(metrics=["per", "pbr"])
        assert isinstance(factor.metadata, FactorMetadata)
