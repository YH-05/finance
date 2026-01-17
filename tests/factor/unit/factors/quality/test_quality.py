"""Unit tests for QualityFactor class.

QualityFactorはROE、ROA、利益安定性、負債比率などの
クオリティ指標を計算するファクタークラスである。

AIDEV-NOTE: TDDのRed状態として、実装前にテストを作成している。
テストはQualityFactorの仕様に基づいて作成されている。
"""

from datetime import datetime
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: 実装が存在しないため、インポートは失敗する（Red状態）
# pytest.importorskipを使用して、実装後に自動的にテストが有効になる
quality_module = pytest.importorskip("factor.factors.quality.quality")
QualityFactor = quality_module.QualityFactor


class TestQualityFactorInheritance:
    """QualityFactorがFactor基底クラスを正しく継承していることのテスト。"""

    def test_正常系_Factor基底クラスを継承している(self) -> None:
        """QualityFactorがFactor基底クラスを継承していることを確認。"""
        from factor.core.base import Factor

        factor = QualityFactor()
        assert isinstance(factor, Factor)

    def test_正常系_name属性が定義されている(self) -> None:
        """QualityFactorにname属性が定義されていることを確認。"""
        factor = QualityFactor()
        assert hasattr(factor, "name")
        assert factor.name == "quality"

    def test_正常系_description属性が定義されている(self) -> None:
        """QualityFactorにdescription属性が定義されていることを確認。"""
        factor = QualityFactor()
        assert hasattr(factor, "description")
        assert len(factor.description) > 0

    def test_正常系_category属性がQUALITYである(self) -> None:
        """QualityFactorのcategoryがFactorCategory.QUALITYであることを確認。"""
        from factor.enums import FactorCategory

        factor = QualityFactor()
        assert factor.category == FactorCategory.QUALITY

    def test_正常系_computeメソッドが実装されている(self) -> None:
        """QualityFactorにcomputeメソッドが実装されていることを確認。"""
        factor = QualityFactor()
        assert hasattr(factor, "compute")
        assert callable(factor.compute)

    def test_正常系_validate_inputsメソッドが使用可能(self) -> None:
        """QualityFactorでvalidate_inputsメソッドが使用可能であることを確認。"""
        factor = QualityFactor()
        assert hasattr(factor, "validate_inputs")
        assert callable(factor.validate_inputs)


class TestQualityFactorInit:
    """QualityFactor初期化のテスト。"""

    def test_正常系_デフォルト値で初期化される(self) -> None:
        """デフォルトのmetric(roe)で初期化されることを確認。"""
        factor = QualityFactor()
        assert factor.metric == "roe"

    def test_正常系_metricにroeを指定できる(self) -> None:
        """metric='roe'で初期化できることを確認。"""
        factor = QualityFactor(metric="roe")
        assert factor.metric == "roe"

    def test_正常系_metricにroaを指定できる(self) -> None:
        """metric='roa'で初期化できることを確認。"""
        factor = QualityFactor(metric="roa")
        assert factor.metric == "roa"

    def test_正常系_metricにearnings_stabilityを指定できる(self) -> None:
        """metric='earnings_stability'で初期化できることを確認。"""
        factor = QualityFactor(metric="earnings_stability")
        assert factor.metric == "earnings_stability"

    def test_正常系_metricにdebt_ratioを指定できる(self) -> None:
        """metric='debt_ratio'で初期化できることを確認。"""
        factor = QualityFactor(metric="debt_ratio")
        assert factor.metric == "debt_ratio"

    def test_異常系_無効なmetricでValidationError(self) -> None:
        """無効なmetricを指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            QualityFactor(metric="invalid_metric")

    def test_異常系_空文字metricでValidationError(self) -> None:
        """空文字のmetricを指定するとValidationErrorが発生することを確認。"""
        from factor.errors import ValidationError

        with pytest.raises(ValidationError):
            QualityFactor(metric="")

    def test_正常系_VALID_METRICS定数が定義されている(self) -> None:
        """VALID_METRICS定数が正しく定義されていることを確認。"""
        assert hasattr(QualityFactor, "VALID_METRICS")
        expected_metrics = ("roe", "roa", "earnings_stability", "debt_ratio")
        assert expected_metrics == QualityFactor.VALID_METRICS


class TestQualityFactorComputeROE:
    """QualityFactor.compute()のROE計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = QualityFactor(metric="roe")

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
            [symbols, ["roe"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_ROEファクター値が計算される(self) -> None:
        """ROEファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
        symbols = ["AAPL", "GOOGL", "MSFT"]
        values = {
            "AAPL": [0.15, 0.16, 0.17],  # 15%, 16%, 17% ROE
            "GOOGL": [0.20, 0.21, 0.22],  # 20%, 21%, 22% ROE
            "MSFT": [0.25, 0.26, 0.27],  # 25%, 26%, 27% ROE
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

    def test_正常系_高ROE銘柄が高スコアになる(self) -> None:
        """高ROE銘柄が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["HIGH_ROE", "LOW_ROE"]
        values = {"HIGH_ROE": [0.25, 0.25], "LOW_ROE": [0.05, 0.05]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高ROEの方が高スコア
        assert (
            result.loc["2024-01-01", "HIGH_ROE"] > result.loc["2024-01-01", "LOW_ROE"]
        )


class TestQualityFactorComputeROA:
    """QualityFactor.compute()のROA計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = QualityFactor(metric="roa")

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
            [symbols, ["roa"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_ROAファクター値が計算される(self) -> None:
        """ROAファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        values = {
            "AAPL": [0.10, 0.11],  # 10%, 11% ROA
            "GOOGL": [0.08, 0.09],  # 8%, 9% ROA
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

    def test_正常系_高ROA銘柄が高スコアになる(self) -> None:
        """高ROA銘柄が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["HIGH_ROA", "LOW_ROA"]
        values = {"HIGH_ROA": [0.15, 0.15], "LOW_ROA": [0.02, 0.02]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高ROAの方が高スコア
        assert (
            result.loc["2024-01-01", "HIGH_ROA"] > result.loc["2024-01-01", "LOW_ROA"]
        )


class TestQualityFactorComputeEarningsStability:
    """QualityFactor.compute()の利益安定性計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = QualityFactor(metric="earnings_stability")

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
            [symbols, ["earnings_stability"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_利益安定性ファクター値が計算される(self) -> None:
        """利益安定性ファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["STABLE", "VOLATILE"]
        # 高い値は安定性が高いことを示す
        values = {"STABLE": [0.95, 0.95], "VOLATILE": [0.50, 0.50]}
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

    def test_正常系_高安定性銘柄が高スコアになる(self) -> None:
        """高い利益安定性の銘柄が高スコアになることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["STABLE", "VOLATILE"]
        values = {"STABLE": [0.95, 0.95], "VOLATILE": [0.30, 0.30]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 高安定性の方が高スコア
        assert result.loc["2024-01-01", "STABLE"] > result.loc["2024-01-01", "VOLATILE"]


class TestQualityFactorComputeDebtRatio:
    """QualityFactor.compute()の負債比率計算テスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = QualityFactor(metric="debt_ratio")

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
            [symbols, ["debt_ratio"]],
            names=["symbol", "metric"],
        )
        data = np.array([values[s] for s in symbols]).T
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_負債比率ファクター値が計算される(self) -> None:
        """負債比率ファクター値が正しく計算されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["LOW_DEBT", "HIGH_DEBT"]
        # 低い値は良い（負債が少ない）
        values = {"LOW_DEBT": [0.20, 0.20], "HIGH_DEBT": [0.80, 0.80]}
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

    def test_正常系_低負債比率銘柄が高スコアになる(self) -> None:
        """低負債比率の銘柄が高スコアになることを確認。

        負債比率は低いほど良いため、ファクター値は符号反転されるべき。
        """
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["LOW_DEBT", "HIGH_DEBT"]
        values = {"LOW_DEBT": [0.20, 0.20], "HIGH_DEBT": [0.80, 0.80]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, values)
        provider = self._create_mock_provider(fundamentals_df)

        result = self.factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # 低負債の方が高スコア（符号反転されている）
        assert (
            result.loc["2024-01-01", "LOW_DEBT"] > result.loc["2024-01-01", "HIGH_DEBT"]
        )


class TestQualityFactorDataFrameFormat:
    """QualityFactor戻り値のDataFrameフォーマットテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = QualityFactor(metric="roe")

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
        data = np.random.rand(len(dates), len(symbols)) * 0.3  # 0-30% ROE
        return pd.DataFrame(data, index=index, columns=columns)

    def test_正常系_戻り値がDataFrameである(self) -> None:
        """戻り値がpd.DataFrameであることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["AAPL", "GOOGL"]
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe")
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
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe")
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
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe")
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
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe")
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
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe")
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


class TestQualityFactorValidation:
    """QualityFactor入力バリデーションのテスト。"""

    def setup_method(self) -> None:
        """テストフィクスチャのセットアップ。"""
        self.factor = QualityFactor(metric="roe")

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


class TestQualityFactorEdgeCases:
    """QualityFactorのエッジケーステスト。"""

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
            "AAPL": [0.15, np.nan],
            "GOOGL": [0.20, 0.25],
        }
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe", values)
        provider = self._create_mock_provider(fundamentals_df)
        factor = QualityFactor(metric="roe")

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
        values = {"ZERO": [0.0, 0.0], "POSITIVE": [0.10, 0.10]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe", values)
        provider = self._create_mock_provider(fundamentals_df)
        factor = QualityFactor(metric="roe")

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-01-02",
        )

        # ゼロ値も処理される（エラーにならない）
        assert isinstance(result, pd.DataFrame)

    def test_正常系_負のROE値を含むデータの処理(self) -> None:
        """負のROE値（赤字企業）を含むデータでも処理されることを確認。"""
        dates = ["2024-01-01", "2024-01-02"]
        symbols = ["NEGATIVE", "POSITIVE"]
        values = {"NEGATIVE": [-0.10, -0.10], "POSITIVE": [0.15, 0.15]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe", values)
        provider = self._create_mock_provider(fundamentals_df)
        factor = QualityFactor(metric="roe")

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
        values = {"AAPL": [0.15, 0.16]}
        fundamentals_df = self._create_fundamentals_df(dates, symbols, "roe", values)
        provider = self._create_mock_provider(fundamentals_df)
        factor = QualityFactor(metric="roe")

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


class TestQualityFactorMetadata:
    """QualityFactorメタデータのテスト。"""

    def test_正常系_metadataプロパティが存在する(self) -> None:
        """metadataプロパティが存在することを確認。"""
        factor = QualityFactor()
        assert hasattr(factor, "metadata")

    def test_正常系_metadata_nameがqualityである(self) -> None:
        """metadata.nameが'quality'であることを確認。"""
        factor = QualityFactor()
        assert factor.metadata.name == "quality"

    def test_正常系_metadata_categoryがqualityである(self) -> None:
        """metadata.categoryが'quality'であることを確認。"""
        factor = QualityFactor()
        assert factor.metadata.category == "quality"

    def test_正常系_metadataがFactorMetadata型である(self) -> None:
        """metadataがFactorMetadata型であることを確認。"""
        from factor.core.base import FactorMetadata

        factor = QualityFactor()
        assert isinstance(factor.metadata, FactorMetadata)
