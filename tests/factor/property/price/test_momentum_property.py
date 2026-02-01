"""Property-based tests for MomentumFactor.

Hypothesisを使用したプロパティベーステストにより、
MomentumFactorの数学的性質と不変条件を検証する。

テスト対象の不変条件:
1. パラメータ制約: lookback > skip_recent >= 0, lookback > 0
2. 出力形状: 入力universeと同じカラム数
3. モメンタム計算: 価格変動と符号の一致
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from factor.factors.price.momentum import MomentumFactor
from hypothesis import assume, given, settings
from hypothesis import strategies as st


class MockDataProvider:
    """テスト用のモックDataProvider。"""

    def __init__(self, prices_df: pd.DataFrame) -> None:
        """モックプロバイダーを初期化する。"""
        self._prices_df = prices_df

    def get_prices(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """価格データを返す。"""
        return self._prices_df

    def get_volumes(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """ボリュームデータを返す（未使用）。"""
        return pd.DataFrame()

    def get_fundamentals(
        self,
        symbols: list[str],
        metrics: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """ファンダメンタルデータを返す（未使用）。"""
        return pd.DataFrame()

    def get_market_cap(
        self,
        symbols: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """時価総額データを返す（未使用）。"""
        return pd.DataFrame()


def create_price_dataframe(
    symbols: list[str],
    dates: pd.DatetimeIndex,
    close_prices: dict[str, list[float]],
) -> pd.DataFrame:
    """テスト用の価格DataFrameを作成するヘルパー関数。"""
    data: dict[tuple[str, str], list[float]] = {}
    for symbol in symbols:
        prices = close_prices[symbol]
        data[(symbol, "Close")] = prices
        data[(symbol, "Open")] = prices
        data[(symbol, "High")] = [p * 1.01 for p in prices]
        data[(symbol, "Low")] = [p * 0.99 for p in prices]
        data[(symbol, "Volume")] = [1000000.0] * len(prices)

    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    df.columns = pd.MultiIndex.from_tuples(df.columns, names=["symbol", "price_type"])
    return df


class TestMomentumFactorParameterConstraints:
    """MomentumFactorのパラメータ制約のプロパティテスト。"""

    @given(
        lookback=st.integers(min_value=1, max_value=500),
        skip_recent=st.integers(min_value=0, max_value=499),
    )
    @settings(max_examples=100)
    def test_プロパティ_有効なパラメータで初期化成功(
        self,
        lookback: int,
        skip_recent: int,
    ) -> None:
        """lookback > skip_recent かつ両方正の値なら初期化が成功する。"""
        assume(skip_recent < lookback)

        factor = MomentumFactor(lookback=lookback, skip_recent=skip_recent)

        assert factor.lookback == lookback
        assert factor.skip_recent == skip_recent

    @given(lookback=st.integers(max_value=0))
    @settings(max_examples=50)
    def test_プロパティ_lookbackが0以下でValueError(self, lookback: int) -> None:
        """lookbackが0以下の場合、ValueErrorが発生する。"""
        with pytest.raises(ValueError, match="lookback must be positive"):
            MomentumFactor(lookback=lookback)

    @given(skip_recent=st.integers(max_value=-1))
    @settings(max_examples=50)
    def test_プロパティ_skip_recentが負でValueError(self, skip_recent: int) -> None:
        """skip_recentが負の場合、ValueErrorが発生する。"""
        with pytest.raises(ValueError, match="skip_recent must be non-negative"):
            MomentumFactor(lookback=100, skip_recent=skip_recent)

    @given(
        lookback=st.integers(min_value=1, max_value=100),
        skip_offset=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=50)
    def test_プロパティ_skip_recentがlookback以上でValueError(
        self,
        lookback: int,
        skip_offset: int,
    ) -> None:
        """skip_recent >= lookbackの場合、ValueErrorが発生する。"""
        skip_recent = lookback + skip_offset

        with pytest.raises(
            ValueError, match=r"skip_recent.*must be less than lookback"
        ):
            MomentumFactor(lookback=lookback, skip_recent=skip_recent)


class TestMomentumFactorOutputShape:
    """MomentumFactor出力形状のプロパティテスト。"""

    @given(
        num_symbols=st.integers(min_value=1, max_value=10),
        num_days=st.integers(min_value=30, max_value=100),
        lookback=st.integers(min_value=5, max_value=25),
    )
    @settings(max_examples=50)
    def test_プロパティ_出力カラム数がuniverseと一致(
        self,
        num_symbols: int,
        num_days: int,
        lookback: int,
    ) -> None:
        """出力DataFrameのカラム数が入力universeのサイズと一致する。"""
        symbols = [f"SYM{i}" for i in range(num_symbols)]
        dates = pd.date_range("2024-01-01", periods=num_days, freq="B")
        close_prices = {
            symbol: list(np.linspace(100, 150, num_days)) for symbol in symbols
        }

        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)
        factor = MomentumFactor(lookback=lookback, skip_recent=0)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        assert len(result.columns) == num_symbols
        assert set(result.columns) == set(symbols)

    @given(
        num_days=st.integers(min_value=30, max_value=100),
        lookback=st.integers(min_value=5, max_value=25),
    )
    @settings(max_examples=50)
    def test_プロパティ_出力行数が入力データと一致(
        self,
        num_days: int,
        lookback: int,
    ) -> None:
        """出力DataFrameの行数が入力データの行数と一致する。"""
        symbols = ["AAPL"]
        dates = pd.date_range("2024-01-01", periods=num_days, freq="B")
        close_prices = {"AAPL": list(np.linspace(100, 150, num_days))}

        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)
        factor = MomentumFactor(lookback=lookback, skip_recent=0)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        assert len(result) == num_days


class TestMomentumFactorMathematicalProperties:
    """MomentumFactor数学的性質のプロパティテスト。"""

    @given(
        start_price=st.floats(min_value=10, max_value=1000, allow_nan=False),
        end_price=st.floats(min_value=10, max_value=1000, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_プロパティ_モメンタムの符号が価格変動と一致(
        self,
        start_price: float,
        end_price: float,
    ) -> None:
        """価格上昇時は正のモメンタム、下落時は負のモメンタム。"""
        assume(abs(end_price - start_price) > 0.01)  # 微小な変化を除外

        lookback = 5
        num_days = lookback + 1
        symbols = ["TEST"]
        dates = pd.date_range("2024-01-01", periods=num_days, freq="B")

        # 線形に変化する価格
        prices = list(np.linspace(start_price, end_price, num_days))
        close_prices = {"TEST": prices}

        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)
        factor = MomentumFactor(lookback=lookback, skip_recent=0)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        # 最後の行のモメンタム値
        last_momentum = result["TEST"].iloc[-1]

        # 価格上昇なら正、下落なら負
        if end_price > start_price:
            assert last_momentum > 0, f"Expected positive momentum, got {last_momentum}"
        else:
            assert last_momentum < 0, f"Expected negative momentum, got {last_momentum}"

    @given(
        constant_price=st.floats(min_value=10, max_value=1000, allow_nan=False),
    )
    @settings(max_examples=50)
    def test_プロパティ_価格一定時はモメンタムがゼロ(
        self,
        constant_price: float,
    ) -> None:
        """価格が一定の場合、モメンタムは0になる。"""
        lookback = 5
        num_days = lookback + 5
        symbols = ["TEST"]
        dates = pd.date_range("2024-01-01", periods=num_days, freq="B")

        # 一定価格
        prices = [constant_price] * num_days
        close_prices = {"TEST": prices}

        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)
        factor = MomentumFactor(lookback=lookback, skip_recent=0)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        # 有効な値は全て0に近い
        valid_values = result["TEST"].dropna()
        np.testing.assert_allclose(np.asarray(valid_values), 0.0, atol=1e-10)

    @given(
        lookback=st.integers(min_value=5, max_value=20),
        skip_recent=st.integers(min_value=0, max_value=4),
    )
    @settings(max_examples=50)
    def test_プロパティ_lookback日前からNaNでなくなる(
        self,
        lookback: int,
        skip_recent: int,
    ) -> None:
        """最初のlookback日はNaN、それ以降は有効な値が存在する。"""
        assume(skip_recent < lookback)

        num_days = lookback + 10
        symbols = ["TEST"]
        dates = pd.date_range("2024-01-01", periods=num_days, freq="B")
        prices = list(np.linspace(100, 150, num_days))
        close_prices = {"TEST": prices}

        prices_df = create_price_dataframe(symbols, dates, close_prices)
        provider = MockDataProvider(prices_df)
        factor = MomentumFactor(lookback=lookback, skip_recent=skip_recent)

        result = factor.compute(
            provider=provider,
            universe=symbols,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        # 最初のlookback行はNaN
        assert result["TEST"].iloc[:lookback].isna().all()
        # lookback行目以降は有効な値
        assert result["TEST"].iloc[lookback:].notna().all()
