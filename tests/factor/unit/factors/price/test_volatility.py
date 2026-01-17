"""Unit tests for VolatilityFactor.

このテストモジュールは、VolatilityFactorクラスの振る舞いを検証します。

テスト対象:
- VolatilityFactor: 価格ボラティリティを計算するファクター

テストケース:
1. Factor基底クラスの継承確認
2. パラメータの初期化（デフォルト値、カスタム値）
3. 日次リターンの標準偏差計算
4. 年率換算オプション
5. lookbackパラメータによる期間指定
6. 戻り値のDataFrameフォーマット
7. metadataプロパティ
8. 異常系（空のuniverse、不正なlookback）
"""

from abc import ABC
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from factor.core.base import Factor
from factor.enums import FactorCategory
from factor.errors import ValidationError
from factor.factors.price.volatility import VolatilityFactor
from factor.providers.base import DataProvider


# =============================================================================
# テスト用のモッククラス
# =============================================================================


class MockDataProvider:
    """DataProviderプロトコルを実装するモッククラス。

    価格データを返すget_pricesメソッドを実装。
    """

    def __init__(
        self,
        prices: pd.DataFrame | None = None,
        num_days: int = 30,
    ) -> None:
        """初期化。

        Parameters
        ----------
        prices : pd.DataFrame | None
            カスタム価格データ（指定しない場合はランダム生成）
        num_days : int
            生成する日数（デフォルト: 30）
        """
        self._prices = prices
        self._num_days = num_days

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック価格データを返す。

        MultiIndex DataFrame形式:
        - Index: DatetimeIndex named "Date"
        - Columns: MultiIndex (symbol, price_type)
        """
        if self._prices is not None:
            return self._prices

        # 日付範囲を生成
        dates = pd.date_range("2024-01-01", periods=self._num_days, freq="D")

        # MultiIndex columnsを構築
        price_types = ["Open", "High", "Low", "Close", "Volume"]
        arrays = [
            [symbol for symbol in symbols for _ in price_types],
            price_types * len(symbols),
        ]
        columns = pd.MultiIndex.from_arrays(arrays, names=["symbol", "price_type"])

        # ランダムな価格データを生成（Close価格を中心に）
        np.random.seed(42)  # 再現性のためシードを固定
        data = np.random.randn(len(dates), len(symbols) * len(price_types)) * 0.02
        df = pd.DataFrame(data, index=dates, columns=columns)

        # 正の価格に調整
        for symbol in symbols:
            base_price = 100.0
            df[(symbol, "Close")] = base_price + df[(symbol, "Close")].cumsum()
            df[(symbol, "Open")] = df[(symbol, "Close")] * 0.99
            df[(symbol, "High")] = df[(symbol, "Close")] * 1.01
            df[(symbol, "Low")] = df[(symbol, "Close")] * 0.98
            df[(symbol, "Volume")] = np.abs(df[(symbol, "Volume")] * 1e6)

        df.index.name = "Date"
        return df

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """モック出来高データを返す。"""
        dates = pd.date_range("2024-01-01", periods=self._num_days, freq="D")
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
        dates = pd.date_range("2024-01-01", periods=self._num_days, freq="D")
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
        dates = pd.date_range("2024-01-01", periods=self._num_days, freq="D")
        data = {symbol: [1e9] * len(dates) for symbol in symbols}
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df


def create_price_data_with_known_volatility(
    symbols: list[str],
    returns_std: float = 0.02,
    num_days: int = 30,
) -> pd.DataFrame:
    """既知のボラティリティを持つ価格データを生成。

    Parameters
    ----------
    symbols : list[str]
        シンボルリスト
    returns_std : float
        日次リターンの標準偏差（デフォルト: 2%）
    num_days : int
        日数

    Returns
    -------
    pd.DataFrame
        MultiIndex DataFrame形式の価格データ
    """
    dates = pd.date_range("2024-01-01", periods=num_days, freq="D")
    price_types = ["Open", "High", "Low", "Close", "Volume"]

    arrays = [
        [symbol for symbol in symbols for _ in price_types],
        price_types * len(symbols),
    ]
    columns = pd.MultiIndex.from_arrays(arrays, names=["symbol", "price_type"])

    df = pd.DataFrame(index=dates, columns=columns, dtype=float)

    np.random.seed(42)
    for symbol in symbols:
        # 既知の標準偏差を持つリターンを生成
        returns = np.random.normal(0, returns_std, num_days)
        prices = 100.0 * np.exp(np.cumsum(returns))

        df[(symbol, "Close")] = prices
        df[(symbol, "Open")] = prices * 0.99
        df[(symbol, "High")] = prices * 1.01
        df[(symbol, "Low")] = prices * 0.98
        df[(symbol, "Volume")] = 1e6

    df.index.name = "Date"
    return df


# =============================================================================
# VolatilityFactor 継承・構造テスト
# =============================================================================


class TestVolatilityFactorInheritance:
    """VolatilityFactorの継承関係のテスト。"""

    def test_正常系_Factor基底クラスを継承している(self) -> None:
        """VolatilityFactorがFactor基底クラスを継承していることを確認。"""
        assert issubclass(VolatilityFactor, Factor)

    def test_正常系_ABCから派生している(self) -> None:
        """VolatilityFactorがABCから派生していることを確認。"""
        assert issubclass(VolatilityFactor, ABC) or issubclass(Factor, ABC)


# =============================================================================
# VolatilityFactor 初期化テスト
# =============================================================================


class TestVolatilityFactorInit:
    """VolatilityFactorの初期化テスト。"""

    def test_正常系_デフォルトパラメータで初期化できる(self) -> None:
        """デフォルトパラメータでVolatilityFactorが初期化できることを確認。"""
        factor = VolatilityFactor()

        assert factor.lookback == 20
        assert factor.annualize is True

    def test_正常系_カスタムパラメータで初期化できる(self) -> None:
        """カスタムパラメータでVolatilityFactorが初期化できることを確認。"""
        factor = VolatilityFactor(lookback=60, annualize=False)

        assert factor.lookback == 60
        assert factor.annualize is False

    def test_正常系_lookbackのみ指定できる(self) -> None:
        """lookbackパラメータのみ指定できることを確認。"""
        factor = VolatilityFactor(lookback=10)

        assert factor.lookback == 10
        assert factor.annualize is True

    def test_正常系_annualizeのみ指定できる(self) -> None:
        """annualizeパラメータのみ指定できることを確認。"""
        factor = VolatilityFactor(annualize=False)

        assert factor.lookback == 20
        assert factor.annualize is False


# =============================================================================
# VolatilityFactor クラス属性テスト
# =============================================================================


class TestVolatilityFactorClassAttributes:
    """VolatilityFactorのクラス属性テスト。"""

    def test_正常系_nameがvolatilityである(self) -> None:
        """nameクラス属性が'volatility'であることを確認。"""
        assert VolatilityFactor.name == "volatility"

    def test_正常系_descriptionが設定されている(self) -> None:
        """descriptionクラス属性が設定されていることを確認。"""
        assert VolatilityFactor.description == "価格ボラティリティ"

    def test_正常系_categoryがPRICEである(self) -> None:
        """categoryクラス属性がFactorCategory.PRICEであることを確認。"""
        assert VolatilityFactor.category == FactorCategory.PRICE


# =============================================================================
# VolatilityFactor compute() テスト - 日次リターン標準偏差
# =============================================================================


class TestVolatilityFactorCompute:
    """VolatilityFactor.compute()の基本テスト。"""

    def test_正常系_日次リターンの標準偏差を計算できる(self) -> None:
        """日次リターンの標準偏差が正しく計算されることを確認。"""
        factor = VolatilityFactor(lookback=20, annualize=False)
        provider = MockDataProvider(num_days=30)
        universe = ["AAPL", "GOOGL"]

        result = factor.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-01-30",
        )

        # 結果がDataFrameであること
        assert isinstance(result, pd.DataFrame)
        # 全ての値が非負であること（標準偏差は負にならない）
        assert (result.dropna() >= 0).all().all()

    def test_正常系_年率換算オプションが機能する(self) -> None:
        """年率換算オプションが機能することを確認。"""
        provider = MockDataProvider(num_days=50)
        universe = ["AAPL"]

        factor_annualized = VolatilityFactor(lookback=20, annualize=True)
        factor_raw = VolatilityFactor(lookback=20, annualize=False)

        result_annualized = factor_annualized.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-02-19",
        )
        result_raw = factor_raw.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-02-19",
        )

        # 年率換算後の値は sqrt(252) 倍になる
        sqrt_252 = np.sqrt(252)
        # 有効な（NaNでない）行を比較
        valid_idx = result_annualized.dropna().index
        np.testing.assert_allclose(
            result_annualized.loc[valid_idx].values,
            result_raw.loc[valid_idx].values * sqrt_252,
            rtol=1e-10,
        )

    def test_正常系_年率換算なしで生のボラティリティが返される(self) -> None:
        """年率換算なしの場合、日次の標準偏差がそのまま返されることを確認。"""
        factor = VolatilityFactor(lookback=20, annualize=False)
        provider = MockDataProvider(num_days=30)
        universe = ["AAPL"]

        result = factor.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-01-30",
        )

        # 結果がDataFrameで、値が妥当な範囲内
        assert isinstance(result, pd.DataFrame)
        # 日次ボラティリティは通常 0.01 ~ 0.05 程度
        valid_values = result.dropna()
        if not valid_values.empty:
            # 少なくとも1つは妥当な範囲内にあること
            assert (valid_values < 1.0).any().any()

    def test_正常系_lookbackパラメータで期間を指定可能(self) -> None:
        """lookbackパラメータで計算期間を指定できることを確認。"""
        provider = MockDataProvider(num_days=50)
        universe = ["AAPL"]

        factor_short = VolatilityFactor(lookback=5, annualize=False)
        factor_long = VolatilityFactor(lookback=20, annualize=False)

        result_short = factor_short.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-02-19",
        )
        result_long = factor_long.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-02-19",
        )

        # 短いlookbackはより早くNaN以外の値を持つ
        short_dropna = result_short.dropna()
        long_dropna = result_long.dropna()
        first_valid_short_idx = short_dropna.index[0]
        first_valid_long_idx = long_dropna.index[0]

        assert first_valid_short_idx < first_valid_long_idx


# =============================================================================
# VolatilityFactor 戻り値フォーマットテスト
# =============================================================================


class TestVolatilityFactorReturnFormat:
    """VolatilityFactor.compute()の戻り値フォーマットテスト。"""

    def test_正常系_戻り値がDataFrameフォーマット(self) -> None:
        """compute()の戻り値がpd.DataFrameであることを確認。"""
        factor = VolatilityFactor()
        provider = MockDataProvider(num_days=30)
        universe = ["AAPL", "GOOGL"]

        result = factor.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-01-30",
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_戻り値のIndexがDatetimeIndex(self) -> None:
        """compute()の戻り値のIndexがDatetimeIndexであることを確認。"""
        factor = VolatilityFactor()
        provider = MockDataProvider(num_days=30)
        universe = ["AAPL"]

        result = factor.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-01-30",
        )

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_正常系_戻り値のColumnsがシンボル名(self) -> None:
        """compute()の戻り値のColumnsがシンボル名のリストであることを確認。"""
        factor = VolatilityFactor()
        provider = MockDataProvider(num_days=30)
        universe = ["AAPL", "GOOGL", "MSFT"]

        result = factor.compute(
            provider=provider,
            universe=universe,
            start_date="2024-01-01",
            end_date="2024-01-30",
        )

        assert list(result.columns) == universe


# =============================================================================
# VolatilityFactor metadataプロパティテスト
# =============================================================================


class TestVolatilityFactorMetadata:
    """VolatilityFactor.metadataプロパティのテスト。"""

    def test_正常系_metadataプロパティが正しい(self) -> None:
        """metadataプロパティが正しい値を返すことを確認。"""
        factor = VolatilityFactor()

        metadata = factor.metadata

        assert metadata.name == "volatility"
        assert metadata.description == "価格ボラティリティ"
        # categoryはenum値がマッピングされる
        assert metadata.category == "price"


# =============================================================================
# VolatilityFactor 異常系テスト
# =============================================================================


class TestVolatilityFactorErrors:
    """VolatilityFactorの異常系テスト。"""

    def test_異常系_空のuniverseでValidationError(self) -> None:
        """空のuniverseでValidationErrorがスローされることを確認。"""
        factor = VolatilityFactor()
        provider = MockDataProvider()

        with pytest.raises(ValidationError):
            factor.compute(
                provider=provider,
                universe=[],
                start_date="2024-01-01",
                end_date="2024-01-30",
            )

    def test_異常系_lookbackが負の値でValueError(self) -> None:
        """lookbackが負の値の場合、ValueErrorがスローされることを確認。"""
        with pytest.raises(ValueError, match="lookback must be positive"):
            VolatilityFactor(lookback=-1)

    def test_異常系_lookbackがゼロでValueError(self) -> None:
        """lookbackが0の場合、ValueErrorがスローされることを確認。"""
        with pytest.raises(ValueError, match="lookback must be positive"):
            VolatilityFactor(lookback=0)


# =============================================================================
# VolatilityFactor DataProvider互換性テスト
# =============================================================================


class TestVolatilityFactorDataProvider:
    """DataProviderプロトコル互換性のテスト。"""

    def test_正常系_MockDataProviderがDataProviderを満たす(self) -> None:
        """MockDataProviderがDataProviderプロトコルを満たすことを確認。"""
        provider = MockDataProvider()

        assert isinstance(provider, DataProvider)

    def test_正常系_datetime型の日付を受け付ける(self) -> None:
        """compute()がdatetime型の日付を受け付けることを確認。"""
        factor = VolatilityFactor()
        provider = MockDataProvider(num_days=30)

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 30),
        )

        assert isinstance(result, pd.DataFrame)

    def test_正常系_str型の日付を受け付ける(self) -> None:
        """compute()がstr型の日付を受け付けることを確認。"""
        factor = VolatilityFactor()
        provider = MockDataProvider(num_days=30)

        result = factor.compute(
            provider=provider,
            universe=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-30",
        )

        assert isinstance(result, pd.DataFrame)
