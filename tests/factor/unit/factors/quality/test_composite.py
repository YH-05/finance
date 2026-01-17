"""Unit tests for CompositeQualityFactor class.

CompositeQualityFactorは複数のクオリティ指標（ROE、ROA、利益安定性、負債比率）を
組み合わせた複合クオリティファクターを計算するクラスである。

Issue #129: [factor] T15: CompositeQualityFactor (factors/quality/composite.py)
"""

from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: 実装が存在しないため、インポートは失敗する（Red状態）
# pytest.importorskipを使用して、実装後に自動的にテストが有効になる
composite_module = pytest.importorskip("factor.factors.quality.composite")
CompositeQualityFactor = composite_module.CompositeQualityFactor


class TestCompositeQualityFactorInheritance:
    """CompositeQualityFactorがFactor基底クラスを正しく継承していることのテスト。"""

    def test_正常系_Factor基底クラスを継承している(self) -> None:
        """CompositeQualityFactorがFactor基底クラスを継承していることを確認。"""
        from factor.core.base import Factor

        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert isinstance(factor, Factor)

    def test_正常系_name属性が定義されている(self) -> None:
        """CompositeQualityFactorにname属性が定義されていることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert hasattr(factor, "name")
        assert factor.name == "composite_quality"

    def test_正常系_description属性が定義されている(self) -> None:
        """CompositeQualityFactorにdescription属性が定義されていることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert hasattr(factor, "description")
        assert len(factor.description) > 0

    def test_正常系_category属性がQUALITYである(self) -> None:
        """CompositeQualityFactorのcategoryがFactorCategory.QUALITYであることを確認。"""
        from factor.enums import FactorCategory

        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert factor.category == FactorCategory.QUALITY

    def test_正常系_computeメソッドが実装されている(self) -> None:
        """CompositeQualityFactorにcomputeメソッドが実装されていることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert hasattr(factor, "compute")
        assert callable(factor.compute)

    def test_正常系_validate_inputsメソッドが使用可能(self) -> None:
        """CompositeQualityFactorでvalidate_inputsメソッドが使用可能であることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert hasattr(factor, "validate_inputs")
        assert callable(factor.validate_inputs)


class TestCompositeQualityFactorInit:
    """CompositeQualityFactor初期化のテスト。"""

    def test_正常系_2つの指標で初期化できる(self) -> None:
        """2つの指標リストで初期化できることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert factor.metrics == ["roe", "roa"]

    def test_正常系_全4指標で初期化できる(self) -> None:
        """全4指標で初期化できることを確認。"""
        metrics = ["roe", "roa", "earnings_stability", "debt_ratio"]
        factor = CompositeQualityFactor(metrics=metrics)
        assert factor.metrics == metrics

    def test_正常系_weightsなしでデフォルト等ウェイト(self) -> None:
        """weightsを指定しない場合、等ウェイトになることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        # 等ウェイトなのでweightsはNoneまたは[0.5, 0.5]となる
        # 実装によっては内部でNoneのままかもしれないので、両方許容
        if factor.weights is not None:
            assert factor.weights == [0.5, 0.5]

    def test_正常系_カスタムウェイトを指定できる(self) -> None:
        """カスタムウェイトを指定できることを確認。"""
        factor = CompositeQualityFactor(
            metrics=["roe", "roa"],
            weights=[0.7, 0.3],
        )
        assert factor.weights == [0.7, 0.3]

    def test_正常系_3つの指標とウェイトで初期化できる(self) -> None:
        """3つの指標とウェイトで初期化できることを確認。"""
        factor = CompositeQualityFactor(
            metrics=["roe", "roa", "earnings_stability"],
            weights=[0.4, 0.4, 0.2],
        )
        assert factor.metrics == ["roe", "roa", "earnings_stability"]
        assert factor.weights == [0.4, 0.4, 0.2]

    def test_正常系_VALID_METRICS定数が定義されている(self) -> None:
        """VALID_METRICS定数が正しく定義されていることを確認。"""
        assert hasattr(CompositeQualityFactor, "VALID_METRICS")
        expected_metrics = ("roe", "roa", "earnings_stability", "debt_ratio")
        assert expected_metrics == CompositeQualityFactor.VALID_METRICS

    def test_異常系_無効な指標名でValidationError(self) -> None:
        """無効な指標名を指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            CompositeQualityFactor(metrics=["roe", "invalid_metric"])

    def test_異常系_空の指標リストでValidationError(self) -> None:
        """空の指標リストを指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            CompositeQualityFactor(metrics=[])

    def test_異常系_ウェイトと指標数が不一致でValidationError(self) -> None:
        """ウェイトの数と指標の数が一致しない場合ValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            CompositeQualityFactor(
                metrics=["roe", "roa"],
                weights=[0.5, 0.3, 0.2],  # 3つのウェイトだが指標は2つ
            )

    def test_正常系_ウェイト合計が1でなくても動作する(self) -> None:
        """ウェイトの合計が1でなくても動作する（警告は出るかもしれないが例外は発生しない）。"""
        # ウェイトの合計が0.8でもエラーにはならない
        factor = CompositeQualityFactor(
            metrics=["roe", "roa"],
            weights=[0.5, 0.3],  # 合計0.8
        )
        assert factor.weights == [0.5, 0.3]


class TestCompositeQualityFactorCompute:
    """CompositeQualityFactor.compute()の基本テスト。"""

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
        metrics = ["roe", "roa"]
        values = {
            "AAPL": {"roe": [0.15, 0.16], "roa": [0.10, 0.11]},
            "GOOGL": {"roe": [0.20, 0.21], "roa": [0.12, 0.13]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=["roe", "roa"])
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
        metrics = ["roe", "roa"]
        values = {
            "AAPL": {"roe": [0.15, 0.16], "roa": [0.10, 0.11]},
            "GOOGL": {"roe": [0.20, 0.21], "roa": [0.12, 0.13]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(
            metrics=["roe", "roa"],
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
        metrics = ["roe", "roa", "earnings_stability"]
        values = {
            "AAPL": {
                "roe": [0.15, 0.16],
                "roa": [0.10, 0.11],
                "earnings_stability": [0.90, 0.91],
            },
            "GOOGL": {
                "roe": [0.20, 0.21],
                "roa": [0.12, 0.13],
                "earnings_stability": [0.85, 0.86],
            },
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
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
        metrics = ["roe", "roa", "earnings_stability", "debt_ratio"]
        values = {
            "AAPL": {
                "roe": [0.15, 0.16],
                "roa": [0.10, 0.11],
                "earnings_stability": [0.90, 0.91],
                "debt_ratio": [0.30, 0.31],
            },
            "GOOGL": {
                "roe": [0.20, 0.21],
                "roa": [0.12, 0.13],
                "earnings_stability": [0.85, 0.86],
                "debt_ratio": [0.40, 0.41],
            },
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == symbols


class TestCompositeQualityFactorNormalization:
    """CompositeQualityFactorの各指標正規化テスト。"""

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

        正規化により、スケールの異なる指標（ROE: 0.05-0.30 vs debt_ratio: 0.1-0.9）が
        同等に扱われる。
        """
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["HIGH_QUALITY", "MID_QUALITY", "LOW_QUALITY"]
        metrics = ["roe", "roa"]

        # ROEとROAで良い銘柄が高スコアになるべき
        values = {
            "HIGH_QUALITY": {
                "roe": [0.30, 0.30],
                "roa": [0.20, 0.20],
            },  # 高ROE、高ROA（良い）
            "MID_QUALITY": {"roe": [0.15, 0.15], "roa": [0.10, 0.10]},  # 中程度
            "LOW_QUALITY": {
                "roe": [0.05, 0.05],
                "roa": [0.02, 0.02],
            },  # 低ROE、低ROA（悪い）
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高ROE・高ROA（HIGH_QUALITY）が最高スコアになるはず
        # 低ROE・低ROA（LOW_QUALITY）が最低スコアになるはず
        assert (
            result.loc["2024-01-01", "HIGH_QUALITY"]
            > result.loc["2024-01-01", "MID_QUALITY"]
        )
        assert (
            result.loc["2024-01-01", "MID_QUALITY"]
            > result.loc["2024-01-01", "LOW_QUALITY"]
        )

    def test_正常系_debt_ratioは符号反転される(self) -> None:
        """debt_ratioは低いほど良いため、符号反転されてから合成されることを確認。

        低負債比率の銘柄がより高いスコアを得るべき。
        """
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["LOW_DEBT", "HIGH_DEBT"]
        metrics = ["debt_ratio"]

        values = {
            "LOW_DEBT": {"debt_ratio": [0.20, 0.20]},  # 低負債（良い）
            "HIGH_DEBT": {"debt_ratio": [0.80, 0.80]},  # 高負債（悪い）
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 低負債の方が高スコア（符号反転されている）
        assert (
            result.loc["2024-01-01", "LOW_DEBT"] > result.loc["2024-01-01", "HIGH_DEBT"]
        )

    def test_正常系_debt_ratio以外は符号反転されない(self) -> None:
        """ROE、ROA、earnings_stabilityは高いほど良いため、符号反転されないことを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["HIGH_ROE", "LOW_ROE"]
        metrics = ["roe"]

        values = {
            "HIGH_ROE": {"roe": [0.30, 0.30]},  # 高ROE（良い）
            "LOW_ROE": {"roe": [0.05, 0.05]},  # 低ROE（悪い）
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高ROEの方が高スコア（符号反転されていない）
        assert (
            result.loc["2024-01-01", "HIGH_ROE"] > result.loc["2024-01-01", "LOW_ROE"]
        )

    def test_正常系_ウェイトが異なると結果が変わる(self) -> None:
        """異なるウェイトで異なる結果が得られることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["A", "B"]
        metrics = ["roe", "roa"]

        # AはROE良好だがROA悪い、BはROE悪いがROA良好
        values = {
            "A": {
                "roe": [0.30, 0.30],
                "roa": [0.02, 0.02],
            },  # 高ROE（良い）、低ROA（悪い）
            "B": {
                "roe": [0.05, 0.05],
                "roa": [0.20, 0.20],
            },  # 低ROE（悪い）、高ROA（良い）
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)

        provider1 = self._create_mock_provider(fundamentals_df)
        provider2 = self._create_mock_provider(fundamentals_df)

        # ROE重視
        factor_roe_heavy = CompositeQualityFactor(
            metrics=metrics,
            weights=[0.9, 0.1],
        )
        result_roe_heavy = factor_roe_heavy.compute(
            provider=provider1,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # ROA重視
        factor_roa_heavy = CompositeQualityFactor(
            metrics=metrics,
            weights=[0.1, 0.9],
        )
        result_roa_heavy = factor_roa_heavy.compute(
            provider=provider2,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # ROE重視ならAが良い、ROA重視ならBが良い
        assert (
            result_roe_heavy.loc["2024-01-01", "A"]
            > result_roe_heavy.loc["2024-01-01", "B"]
        )
        assert (
            result_roa_heavy.loc["2024-01-01", "B"]
            > result_roa_heavy.loc["2024-01-01", "A"]
        )


class TestCompositeQualityFactorDataFrameFormat:
    """CompositeQualityFactor戻り値のDataFrameフォーマットテスト。"""

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
        data = np.random.rand(len(dates), len(symbols) * len(metrics)) * 0.3
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_戻り値がDataFrameである(self) -> None:
        """戻り値がpd.DataFrameであることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        metrics = ["roe", "roa"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
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
        metrics = ["roe", "roa"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
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
        metrics = ["roe", "roa"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
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
        metrics = ["roe", "roa"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
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
        metrics = ["roe", "roa"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert result.dtypes["AAPL"] is np.float64 or np.issubdtype(
            result.dtypes["AAPL"], np.floating
        )


class TestCompositeQualityFactorValidation:
    """CompositeQualityFactor入力バリデーションのテスト。"""

    def _create_mock_provider(self) -> MagicMock:
        """モックDataProviderを作成するヘルパーメソッド。"""
        return MagicMock()

    def test_異常系_空のユニバースでValidationError(self) -> None:
        """空のユニバースでValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        provider = self._create_mock_provider()
        factor = CompositeQualityFactor(metrics=["roe", "roa"])

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
        factor = CompositeQualityFactor(metrics=["roe", "roa"])

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
        factor = CompositeQualityFactor(metrics=["roe", "roa"])

        with pytest.raises(ValidationError):
            factor.compute(
                provider=provider,
                universe=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-01-01",
            )


class TestCompositeQualityFactorEdgeCases:
    """CompositeQualityFactorのエッジケーステスト。"""

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
        metrics = ["roe", "roa"]
        values = {
            "AAPL": {"roe": [0.15, np.nan], "roa": [0.10, 0.11]},
            "GOOGL": {"roe": [0.20, 0.21], "roa": [0.12, 0.13]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
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
        metrics = ["roe", "roa"]
        values = {
            "AAPL": {"roe": [0.15, 0.16], "roa": [0.10, 0.11]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider1 = self._create_mock_provider(fundamentals_df)
        provider2 = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)

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
        metrics = ["roe"]
        values = {
            "AAPL": {"roe": [0.15, 0.16]},
            "GOOGL": {"roe": [0.20, 0.21]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=["roe"])
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_負のROE値を含むデータの処理(self) -> None:
        """負のROE値（赤字企業）を含むデータでも処理されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["NEGATIVE_ROE", "POSITIVE_ROE"]
        metrics = ["roe", "roa"]
        values = {
            "NEGATIVE_ROE": {"roe": [-0.10, -0.10], "roa": [-0.05, -0.05]},
            "POSITIVE_ROE": {"roe": [0.15, 0.15], "roa": [0.10, 0.10]},
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, metrics, values)
        provider = self._create_mock_provider(fundamentals_df)

        factor = CompositeQualityFactor(metrics=metrics)
        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        assert isinstance(result, pd.DataFrame)
        # 正のROEの銘柄が高スコアになるはず
        assert (
            result.loc["2024-01-01", "POSITIVE_ROE"]
            > result.loc["2024-01-01", "NEGATIVE_ROE"]
        )


class TestCompositeQualityFactorMetadata:
    """CompositeQualityFactorメタデータのテスト。"""

    def test_正常系_metadataプロパティが存在する(self) -> None:
        """metadataプロパティが存在することを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert hasattr(factor, "metadata")

    def test_正常系_metadata_nameがcomposite_qualityである(self) -> None:
        """metadata.nameが'composite_quality'であることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert factor.metadata.name == "composite_quality"

    def test_正常系_metadata_categoryがqualityである(self) -> None:
        """metadata.categoryが'quality'であることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert factor.metadata.category == "quality"

    def test_正常系_metadataがFactorMetadata型である(self) -> None:
        """metadataがFactorMetadata型であることを確認。"""
        from factor.core.base import FactorMetadata

        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert isinstance(factor.metadata, FactorMetadata)


class TestCompositeQualityFactorDocumentation:
    """CompositeQualityFactorのドキュメントとサンプルコードのテスト。"""

    def test_正常系_クラスにdocstringが存在する(self) -> None:
        """CompositeQualityFactorクラスにdocstringが存在することを確認。"""
        assert CompositeQualityFactor.__doc__ is not None
        assert len(CompositeQualityFactor.__doc__) > 0

    def test_正常系_computeメソッドにdocstringが存在する(self) -> None:
        """computeメソッドにdocstringが存在することを確認。"""
        assert CompositeQualityFactor.compute.__doc__ is not None
        assert len(CompositeQualityFactor.compute.__doc__) > 0

    def test_正常系_initメソッドにdocstringが存在する(self) -> None:
        """__init__メソッドにdocstringが存在することを確認。"""
        assert CompositeQualityFactor.__init__.__doc__ is not None
        assert len(CompositeQualityFactor.__init__.__doc__) > 0


class TestCompositeQualityFactorPyrightStrict:
    """CompositeQualityFactorがpyright strictで型エラーがないことのテスト。

    このテストクラスは型の一貫性を確認するためのものです。
    実際の型チェックはpyrightで行われますが、
    ここではランタイムで型の基本的な整合性を確認します。
    """

    def test_正常系_metricsの型がlist_strである(self) -> None:
        """metrics属性の型がlist[str]であることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert isinstance(factor.metrics, list)
        for metric in factor.metrics:
            assert isinstance(metric, str)

    def test_正常系_weightsの型がlist_floatまたはNoneである(self) -> None:
        """weights属性の型がlist[float] | Noneであることを確認。"""
        factor_no_weights = CompositeQualityFactor(metrics=["roe", "roa"])
        assert factor_no_weights.weights is None or isinstance(
            factor_no_weights.weights, list
        )

        factor_with_weights = CompositeQualityFactor(
            metrics=["roe", "roa"],
            weights=[0.6, 0.4],
        )
        assert isinstance(factor_with_weights.weights, list)
        for weight in factor_with_weights.weights:
            assert isinstance(weight, float)

    def test_正常系_name属性の型がstrである(self) -> None:
        """name属性の型がstrであることを確認。"""
        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert isinstance(factor.name, str)

    def test_正常系_category属性の型がFactorCategoryである(self) -> None:
        """category属性の型がFactorCategoryであることを確認。"""
        from factor.enums import FactorCategory

        factor = CompositeQualityFactor(metrics=["roe", "roa"])
        assert isinstance(factor.category, FactorCategory)
