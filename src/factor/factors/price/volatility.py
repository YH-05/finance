"""VolatilityFactor - Price volatility factor implementation.

このモジュールはボラティリティファクターを実装します。
日次リターンの標準偏差を計算し、オプションで年率換算します。

Classes
-------
VolatilityFactor
    価格ボラティリティを計算するファクター実装。

Examples
--------
>>> from factor.factors.price.volatility import VolatilityFactor
>>> from factor.providers import YFinanceProvider
>>>
>>> factor = VolatilityFactor(lookback=20, annualize=True)
>>> provider = YFinanceProvider()
>>> result = factor.compute(
...     provider=provider,
...     universe=["AAPL", "GOOGL"],
...     start_date="2024-01-01",
...     end_date="2024-12-31",
... )
>>> result.columns.tolist()
['AAPL', 'GOOGL']
"""

from datetime import datetime

import numpy as np
import pandas as pd
from utils_core.logging import get_logger

from factor.core.base import Factor
from factor.enums import FactorCategory
from factor.providers.base import DataProvider

logger = get_logger(__name__)

# 年間営業日数（年率換算用）
TRADING_DAYS_PER_YEAR = 252


class VolatilityFactor(Factor):
    """ボラティリティファクター。

    日次リターンの標準偏差を計算し、オプションで年率換算します。
    低ボラティリティ銘柄選好戦略（Low Volatility Anomaly）などの
    ファクター投資に活用できます。

    Parameters
    ----------
    lookback : int, default=20
        ルックバック期間（営業日）。この期間の日次リターンの
        標準偏差を計算します。
    annualize : bool, default=True
        年率換算するかどうか。Trueの場合、sqrt(252)を乗算します。

    Attributes
    ----------
    lookback : int
        ルックバック期間
    annualize : bool
        年率換算フラグ

    Notes
    -----
    計算式:
        volatility = std(daily_returns, window=lookback)
        if annualize:
            volatility = volatility * sqrt(252)

    Examples
    --------
    >>> factor = VolatilityFactor(lookback=20, annualize=True)
    >>> factor.lookback
    20
    >>> factor.annualize
    True
    """

    name = "volatility"
    description = "価格ボラティリティ"
    category = FactorCategory.PRICE

    # メタデータ用のオプション属性
    _required_data: list[str] = ["price"]
    _frequency: str = "daily"
    _lookback_period: int | None = 20
    _higher_is_better: bool = False  # 低ボラティリティが好ましい場合

    def __init__(
        self,
        lookback: int = 20,
        annualize: bool = True,
    ) -> None:
        """初期化。

        Parameters
        ----------
        lookback : int, default=20
            ルックバック期間（営業日）
        annualize : bool, default=True
            年率換算するか

        Raises
        ------
        ValueError
            lookbackが正の整数でない場合
        """
        if lookback <= 0:
            raise ValueError(f"lookback must be positive, got {lookback}")

        self.lookback = lookback
        self.annualize = annualize

        logger.debug(
            "VolatilityFactor initialized",
            lookback=lookback,
            annualize=annualize,
        )

    def compute(
        self,
        provider: DataProvider,
        universe: list[str],
        start_date: datetime | str,
        end_date: datetime | str,
    ) -> pd.DataFrame:
        """ボラティリティファクター値を計算。

        日次リターンのローリング標準偏差を計算します。
        annualize=Trueの場合、sqrt(252)を乗算して年率換算します。

        Parameters
        ----------
        provider : DataProvider
            データプロバイダー
        universe : list[str]
            対象銘柄リスト
        start_date : datetime | str
            開始日
        end_date : datetime | str
            終了日

        Returns
        -------
        pd.DataFrame
            ボラティリティ値
            - Index: DatetimeIndex named "Date"
            - Columns: 銘柄シンボル
            - Values: ボラティリティ値（年率換算時はsqrt(252)倍）

        Raises
        ------
        ValidationError
            universeが空の場合

        Examples
        --------
        >>> factor = VolatilityFactor(lookback=20, annualize=True)
        >>> provider = MockDataProvider()
        >>> result = factor.compute(
        ...     provider=provider,
        ...     universe=["AAPL", "GOOGL"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-06-30",
        ... )
        >>> result.shape[1]
        2
        """
        logger.debug(
            "Computing volatility factor",
            universe_size=len(universe),
            start_date=str(start_date),
            end_date=str(end_date),
            lookback=self.lookback,
            annualize=self.annualize,
        )

        # 入力バリデーション
        self.validate_inputs(universe, start_date, end_date)

        # 価格データを取得
        prices_df = provider.get_prices(universe, start_date, end_date)

        # Close価格を抽出してDataFrameに変換
        close_prices = self._extract_close_prices(prices_df, universe)

        # 日次リターンを計算
        returns = close_prices.pct_change()

        # ローリング標準偏差を計算
        volatility_result = returns.rolling(window=self.lookback).std()

        # rollingの結果をDataFrameとして確保
        if isinstance(volatility_result, pd.Series):
            volatility = volatility_result.to_frame()
        else:
            volatility = pd.DataFrame(volatility_result)

        # 年率換算
        if self.annualize:
            volatility = volatility * np.sqrt(TRADING_DAYS_PER_YEAR)

        logger.info(
            "Volatility factor computed",
            universe_size=len(universe),
            valid_rows=volatility.dropna().shape[0],
        )

        return volatility

    def _extract_close_prices(
        self,
        prices_df: pd.DataFrame,
        universe: list[str],
    ) -> pd.DataFrame:
        """価格DataFrameからClose価格を抽出。

        Parameters
        ----------
        prices_df : pd.DataFrame
            MultiIndex形式の価格データ
        universe : list[str]
            銘柄リスト

        Returns
        -------
        pd.DataFrame
            Close価格のみを含むDataFrame
        """
        close_prices = pd.DataFrame(index=prices_df.index)

        for symbol in universe:
            if isinstance(prices_df.columns, pd.MultiIndex):
                # MultiIndex形式の場合
                close_prices[symbol] = prices_df[(symbol, "Close")]
            else:
                # シンプルなColumns形式の場合
                close_prices[symbol] = prices_df[symbol]

        close_prices.index.name = "Date"
        return close_prices


__all__ = [
    "VolatilityFactor",
]


__all__ = [
    "VolatilityFactor",
]
