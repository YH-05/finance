"""Unit tests for ReversalFactor.

このテストモジュールは、ReversalFactorクラスの振る舞いを検証します。

テスト対象:
- ReversalFactor: 短期リバーサルファクター

受け入れ条件:
- [ ] Factor 基底クラスを継承している
- [ ] 短期リターンの反転（符号反転）を計算できる
- [ ] lookback パラメータで期間を指定可能
- [ ] 戻り値が正しい DataFrame フォーマット
- [ ] ドキュメントとサンプルコードがある
- [ ] pyright strict でエラーがない
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from factor.core.base import Factor
from factor.enums import FactorCategory
from factor.errors import ValidationError
from factor.factors.price.reversal import ReversalFactor
from factor.providers.base import DataProvider

# =============================================================================
# テスト用のモッククラス
# =============================================================================


class MockDataProvider:
    """DataProviderプロトコルを実装するモッククラス。"""

    def __init__(self, prices: pd.DataFrame | None = None) -> None:
        """Initialize with optional custom price data."""
        self._prices = prices

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック価格データを返す。"""
        if self._prices is not None:
            return self._prices

        # デフォルトのモックデータ: 各銘柄で異なる価格推移
        dates = pd.date_range("2024-01-01", "2024-01-20", freq="D")
        data = {
            "AAPL": [100.0 + i for i in range(len(dates))],  # 上昇トレンド
            "GOOGL": [100.0 - i * 0.5 for i in range(len(dates))],  # 下落トレンド
            "MSFT": [100.0 + np.sin(i / 3) * 5 for i in range(len(dates))],  # 振動
        }
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        # symbolsでフィルタリング
        available_cols = [s for s in symbols if s in df.columns]
        if available_cols:
            return df.loc[:, available_cols]
        return df

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック出来高データを返す。"""
        dates = pd.date_range("2024-01-01", "2024-01-20", freq="D")
        data = {symbol: [1000000] * len(dates) for symbol in symbols}
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
        dates = pd.date_range("2024-01-01", "2024-01-20", freq="D")
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
        dates = pd.date_range("2024-01-01", "2024-01-20", freq="D")
        data = {symbol: [1e12] * len(dates) for symbol in symbols}
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df


# =============================================================================
# ReversalFactor クラスの構造テスト
# =============================================================================


class TestReversalFactorInheritance:
    """ReversalFactorの継承構造テスト。"""

    def test_正常系_Factor基底クラスを継承している(self) -> None:
        """ReversalFactorがFactor基底クラスを継承していることを確認。"""
        assert issubclass(ReversalFactor, Factor)

    def test_正常系_インスタンス化できる(self) -> None:
        """ReversalFactorがインスタンス化できることを確認。"""
        factor = ReversalFactor()
        assert factor is not None
        assert isinstance(factor, Factor)

    def test_正常系_インスタンスがFactorプロトコルを満たす(self) -> None:
        """ReversalFactorインスタンスがFactorの全メソッドを持つことを確認。"""
        factor = ReversalFactor()
        assert hasattr(factor, "compute")
        assert hasattr(factor, "validate_inputs")
        assert hasattr(factor, "metadata")


class TestReversalFactorClassAttributes:
    """ReversalFactorクラス属性のテスト。"""

    def test_正常系_nameがreversalである(self) -> None:
        """name属性が'reversal'であることを確認。"""
        assert ReversalFactor.name == "reversal"

    def test_正常系_descriptionが設定されている(self) -> None:
        """description属性が設定されていることを確認。"""
        assert ReversalFactor.description is not None
        assert len(ReversalFactor.description) > 0

    def test_正常系_categoryがPRICEである(self) -> None:
        """category属性がFactorCategory.PRICEであることを確認。"""
        assert ReversalFactor.category == FactorCategory.PRICE


class TestReversalFactorMetadata:
    """ReversalFactor.metadataプロパティのテスト。"""

    def test_正常系_metadataが取得できる(self) -> None:
        """metadataプロパティが正しく動作することを確認。"""
        factor = ReversalFactor()
        metadata = factor.metadata

        assert metadata.name == "reversal"
        assert "price" in metadata.category.lower()


# =============================================================================
# ReversalFactor 初期化テスト
# =============================================================================


class TestReversalFactorInit:
    """ReversalFactor初期化のテスト。"""

    def test_正常系_デフォルトlookbackは5(self) -> None:
        """デフォルトのlookbackが5であることを確認。"""
        factor = ReversalFactor()
        assert factor.lookback == 5

    def test_正常系_lookbackをカスタマイズできる(self) -> None:
        """lookbackパラメータをカスタマイズできることを確認。"""
        factor = ReversalFactor(lookback=10)
        assert factor.lookback == 10

    def test_正常系_lookback1でも動作する(self) -> None:
        """lookback=1でもインスタンス化できることを確認。"""
        factor = ReversalFactor(lookback=1)
        assert factor.lookback == 1

    def test_異常系_lookbackが0でエラー(self) -> None:
        """lookbackが0の場合にValidationErrorがスローされることを確認。"""
        with pytest.raises(ValidationError):
            ReversalFactor(lookback=0)

    def test_異常系_lookbackが負でエラー(self) -> None:
        """lookbackが負の場合にValidationErrorがスローされることを確認。"""
        with pytest.raises(ValidationError):
            ReversalFactor(lookback=-1)


# =============================================================================
# ReversalFactor.compute() テスト
# =============================================================================


class TestReversalFactorCompute:
    """ReversalFactor.compute()メソッドのテスト。"""

    def test_正常系_DataFrameを返す(self) -> None:
        """compute()がpd.DataFrameを返すことを確認。"""
        factor = ReversalFactor()
        provider = MockDataProvider()
        universe = ["AAPL", "GOOGL", "MSFT"]

        result = factor.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-01-20",
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_indexがDatetimeIndex(self) -> None:
        """戻り値のindexがDatetimeIndexであることを確認。"""
        factor = ReversalFactor()
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-20",
        )

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_columnsがsymbolsと一致する(self) -> None:
        """戻り値のcolumnsがuniverseと一致することを確認。"""
        factor = ReversalFactor()
        provider = MockDataProvider()
        universe = ["AAPL", "GOOGL"]

        result = factor.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-01-20",
        )

        assert list(result.columns) == universe

    def test_正常系_datetime型の日付を受け付ける(self) -> None:
        """compute()がdatetime型の日付を受け付けることを確認。"""
        factor = ReversalFactor()
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 20),
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_str型の日付を受け付ける(self) -> None:
        """compute()がstr型の日付を受け付けることを確認。"""
        factor = ReversalFactor()
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-20",
        )

        assert isinstance(result, pd.DataFrame)


class TestReversalFactorReversalCalculation:
    """リバーサル計算ロジックのテスト。"""

    def test_正常系_上昇銘柄は負のスコア(self) -> None:
        """上昇した銘柄が負のリバーサルスコアを持つことを確認。

        リバーサルは短期リターンの符号反転なので、
        上昇した銘柄 → 正のリターン → 負のリバーサルスコア
        """
        # 明確に上昇するデータを作成
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        prices = pd.DataFrame(
            {
                "AAPL": [
                    100.0,
                    101.0,
                    102.0,
                    103.0,
                    104.0,
                    105.0,
                    106.0,
                    107.0,
                    108.0,
                    109.0,
                ]
            },
            index=dates,
        )
        prices.index.name = "Date"

        factor = ReversalFactor(lookback=5)
        provider = MockDataProvider(prices=prices)

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        # lookback期間後の値（NaNでない最初の値）が負であることを確認
        non_nan_values = result["AAPL"].dropna()
        assert len(non_nan_values) > 0
        # 上昇トレンドなので、リバーサルスコアは負
        assert (non_nan_values < 0).all()

    def test_正常系_下落銘柄は正のスコア(self) -> None:
        """下落した銘柄が正のリバーサルスコアを持つことを確認。

        リバーサルは短期リターンの符号反転なので、
        下落した銘柄 → 負のリターン → 正のリバーサルスコア
        """
        # 明確に下落するデータを作成
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        prices = pd.DataFrame(
            {
                "GOOGL": [
                    109.0,
                    108.0,
                    107.0,
                    106.0,
                    105.0,
                    104.0,
                    103.0,
                    102.0,
                    101.0,
                    100.0,
                ]
            },
            index=dates,
        )
        prices.index.name = "Date"

        factor = ReversalFactor(lookback=5)
        provider = MockDataProvider(prices=prices)

        result = factor.compute(
            provider=provider,
            universe=["GOOGL"],
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        # 下落トレンドなのでリバーサルスコアは正
        non_nan_values = result["GOOGL"].dropna()
        assert len(non_nan_values) > 0
        assert (non_nan_values > 0).all()

    def test_正常系_横ばい銘柄はゼロに近いスコア(self) -> None:
        """横ばいの銘柄がゼロに近いリバーサルスコアを持つことを確認。"""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="D")
        prices = pd.DataFrame(
            {"FLAT": [100.0] * len(dates)},
            index=dates,
        )
        prices.index.name = "Date"

        factor = ReversalFactor(lookback=5)
        provider = MockDataProvider(prices=prices)

        result = factor.compute(
            provider=provider,
            universe=["FLAT"],
            start_date="2024-01-01",
            end_date="2024-01-10",
        )

        non_nan_values = result["FLAT"].dropna()
        assert len(non_nan_values) > 0
        assert np.allclose(non_nan_values, 0.0, atol=1e-10)

    def test_正常系_lookback期間分のNaNが発生する(self) -> None:
        """lookback期間分のNaNが結果の先頭に発生することを確認。"""
        factor = ReversalFactor(lookback=5)
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-20",
        )

        # 最初のlookback個の値がNaNであることを確認
        assert result["AAPL"].iloc[:5].isna().all()
        # lookback以降は値があることを確認
        assert not result["AAPL"].iloc[5:].isna().all()

    def test_正常系_計算式が正しい(self) -> None:
        """リバーサル計算式 -(P_t / P_{t-lookback} - 1) が正しいことを確認。"""
        dates = pd.date_range("2024-01-01", "2024-01-06", freq="D")
        prices = pd.DataFrame(
            {"TEST": [100.0, 102.0, 104.0, 106.0, 108.0, 110.0]},
            index=dates,
        )
        prices.index.name = "Date"

        factor = ReversalFactor(lookback=5)
        provider = MockDataProvider(prices=prices)

        result = factor.compute(
            provider=provider,
            universe=["TEST"],
            start_date="2024-01-01",
            end_date="2024-01-06",
        )

        # 最後の日: P_t=110, P_{t-5}=100
        # リターン = 110/100 - 1 = 0.1
        # リバーサル = -0.1
        expected = -(110.0 / 100.0 - 1)
        actual = result["TEST"].iloc[-1]
        assert np.isclose(actual, expected, rtol=1e-10)


class TestReversalFactorLookbackVariations:
    """異なるlookback値でのテスト。"""

    @pytest.mark.parametrize("lookback", [1, 3, 5, 10, 20])
    def test_正常系_様々なlookbackで動作する(self, lookback: int) -> None:
        """様々なlookback値でcompute()が正常に動作することを確認。"""
        factor = ReversalFactor(lookback=lookback)
        provider = MockDataProvider()

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-20",
        )

        assert isinstance(result, pd.DataFrame)
        # lookback期間分のNaN + それ以降の値
        assert result["AAPL"].iloc[:lookback].isna().all()


# =============================================================================
# ReversalFactor.validate_inputs() テスト
# =============================================================================


class TestReversalFactorValidateInputs:
    """ReversalFactor.validate_inputs()メソッドのテスト。"""

    def test_正常系_有効な入力で例外なし(self) -> None:
        """有効な入力値でvalidate_inputs()が例外をスローしないことを確認。"""
        factor = ReversalFactor()

        factor.validate_inputs(
            universe=["AAPL", "GOOGL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 20),
        )

    def test_異常系_空のuniverseでValidationError(self) -> None:
        """空のuniverseでValidationErrorがスローされることを確認。"""
        factor = ReversalFactor()

        with pytest.raises(ValidationError):
            factor.validate_inputs(
                universe=[],
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 20),
            )

    def test_異常系_start_dateがend_dateより後でValidationError(self) -> None:
        """start_dateがend_dateより後の場合にValidationErrorがスローされることを確認。"""
        factor = ReversalFactor()

        with pytest.raises(ValidationError):
            factor.validate_inputs(
                universe=["AAPL"],
                start_date=datetime(2024, 12, 31),
                end_date=datetime(2024, 1, 1),
            )


# =============================================================================
# ReversalFactor Docstring テスト
# =============================================================================


class TestReversalFactorDocstring:
    """ReversalFactor docstringのテスト。"""

    def test_正常系_クラスにdocstringがある(self) -> None:
        """ReversalFactorクラスにdocstringが存在することを確認。"""
        assert ReversalFactor.__doc__ is not None
        assert len(ReversalFactor.__doc__) > 0

    def test_正常系_computeメソッドにdocstringがある(self) -> None:
        """compute()メソッドにdocstringが存在することを確認。"""
        assert ReversalFactor.compute.__doc__ is not None
        assert len(ReversalFactor.compute.__doc__) > 0

    def test_正常系_docstringにExamplesセクションがある(self) -> None:
        """docstringにExamplesセクションが含まれていることを確認。"""
        assert "Examples" in (ReversalFactor.__doc__ or "")


# =============================================================================
# DataProvider プロトコル互換性テスト
# =============================================================================


class TestDataProviderProtocol:
    """DataProviderプロトコル互換性のテスト。"""

    def test_正常系_MockDataProviderがDataProviderを満たす(self) -> None:
        """MockDataProviderがDataProviderプロトコルを満たすことを確認。"""
        provider = MockDataProvider()
        assert isinstance(provider, DataProvider)
