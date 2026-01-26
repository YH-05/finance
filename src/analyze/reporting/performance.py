"""
performance.py

指数・株式・セクターやコモディティのパフォーマンスを計測

"""

from datetime import datetime, timedelta
from typing import cast

import pandas as pd
from pandas import DataFrame, Timestamp

from analyze.config import get_return_periods, get_symbol_group, get_symbols
from database.utils.logging_config import get_logger, setup_logging
from market.yfinance import FetchOptions, YFinanceFetcher


class PerformanceAnalyzer:
    """symbols.yamlで定義したシンボルグループのパフォーマンスを計測する.

    symbols.yamlで定義された任意のグループ（indices, mag7, sectors等）に対して、
    複数期間（1D, 1W, MTD, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y）の騰落率を一括計算する。

    Examples
    --------
    >>> analyzer = PerformanceAnalyzer()
    >>> # 米国指数のパフォーマンス
    >>> us_returns = analyzer.get_group_performance("indices", "us")
    >>> # MAG7のパフォーマンス
    >>> mag7_returns = analyzer.get_group_performance("mag7")
    >>> # セクターETFのパフォーマンス
    >>> sector_returns = analyzer.get_group_performance("sectors")
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__, component="PerformanceAnalyzer")

    def calculate_returns(
        self,
        price_df: DataFrame,
        return_periods: dict[str, int | str],
    ) -> DataFrame:
        """各シンボル・各期間の騰落率を pct_change で計算する.

        pandas の groupby + pct_change を使用することで、
        データ欠損時にも堅牢に騰落率を計算できる。

        Parameters
        ----------
        price_df : DataFrame
            価格データ（Date, symbol, variable, value カラムを持つ）
        return_periods : dict[str, int | str]
            期間定義（例: {"1W": 5, "MTD": "mtd", "YTD": "ytd"}）

        Returns
        -------
        DataFrame
            騰落率データ（symbol, period, return_pct カラムを持つ）
        """
        self.logger.info(
            "Calculating returns with pct_change",
            symbols=price_df["symbol"].nunique(),
            periods=list(return_periods.keys()),
        )

        if price_df.empty:
            return DataFrame({"symbol": [], "period": [], "return_pct": []})

        # 日付でソートし、銘柄でグループ化
        sorted_df = price_df.sort_values(["symbol", "Date"]).reset_index(drop=True)

        results: list[dict[str, str | float]] = []

        # 営業日数ベースの期間を pct_change で一括計算
        int_periods = {k: v for k, v in return_periods.items() if isinstance(v, int)}
        str_periods = {k: v for k, v in return_periods.items() if isinstance(v, str)}

        # 営業日数ベースの騰落率を計算
        if int_periods:
            results.extend(self._calculate_int_period_returns(sorted_df, int_periods))

        # MTD/YTD/WoW などの日付ベースの騰落率を計算
        if str_periods:
            results.extend(self._calculate_str_period_returns(sorted_df, str_periods))

        return DataFrame(results)

    def _calculate_int_period_returns(
        self,
        sorted_df: DataFrame,
        int_periods: dict[str, int],
    ) -> list[dict[str, str | float]]:
        """営業日数ベースの騰落率を pct_change で計算する.

        グローバル市場の休日などで NaN が含まれる場合があるため、
        銘柄ごとに NaN を除去してから pct_change を計算する。

        Parameters
        ----------
        sorted_df : DataFrame
            日付・銘柄でソート済みの価格データ
        int_periods : dict[str, int]
            営業日数ベースの期間定義

        Returns
        -------
        list[dict[str, str | float]]
            騰落率の結果リスト
        """
        results: list[dict[str, str | float]] = []

        for period_name, period_days in int_periods.items():
            # 各銘柄ごとに NaN を除去して pct_change を計算
            for symbol in sorted_df["symbol"].unique():
                symbol_data = sorted_df[sorted_df["symbol"] == symbol].copy()

                # NaN を含む行を除去（休日やデータ欠損対応）
                symbol_data = symbol_data.dropna(subset=["value"])

                if len(symbol_data) <= period_days:
                    self.logger.debug(
                        "Insufficient data after dropna",
                        symbol=symbol,
                        period=period_name,
                        period_days=period_days,
                        available_rows=len(symbol_data),
                    )
                    continue

                # pct_change で騰落率を計算
                pct_changes = symbol_data["value"].pct_change(
                    periods=period_days,
                    fill_method=None,
                )

                # 最新の値を取得
                latest_pct = pct_changes.iloc[-1]

                if pd.notna(latest_pct):
                    results.append(
                        {
                            "symbol": str(symbol),
                            "period": period_name,
                            "return_pct": round(latest_pct * 100, 2),
                        }
                    )
                else:
                    self.logger.debug(
                        "pct_change returned NaN",
                        symbol=symbol,
                        period=period_name,
                        period_days=period_days,
                    )

        return results

    def _calculate_str_period_returns(
        self,
        sorted_df: DataFrame,
        str_periods: dict[str, str],
    ) -> list[dict[str, str | float]]:
        """日付ベースの騰落率（MTD/YTD/WoW）を計算する.

        グローバル市場の休日などで NaN が含まれる場合があるため、
        銘柄ごとに NaN を除去してから計算する。

        Parameters
        ----------
        sorted_df : DataFrame
            日付・銘柄でソート済みの価格データ
        str_periods : dict[str, str]
            日付ベースの期間定義

        Returns
        -------
        list[dict[str, str | float]]
            騰落率の結果リスト
        """
        results: list[dict[str, str | float]] = []

        for symbol in sorted_df["symbol"].unique():
            symbol_data = cast("DataFrame", sorted_df[sorted_df["symbol"] == symbol])

            # NaN を含む行を除去（休日やデータ欠損対応）
            symbol_data = symbol_data.dropna(subset=["value"])

            if symbol_data.empty:
                continue

            latest_row = symbol_data.iloc[-1]
            latest_date = cast("Timestamp", pd.Timestamp(latest_row["Date"]))
            latest_price = float(latest_row["value"])

            for period_name, period_value in str_periods.items():
                try:
                    return_pct = self._calculate_date_based_return(
                        symbol_data=symbol_data,
                        latest_date=latest_date,
                        latest_price=latest_price,
                        period_value=period_value,
                    )

                    if return_pct is not None:
                        results.append(
                            {
                                "symbol": str(symbol),
                                "period": period_name,
                                "return_pct": return_pct,
                            }
                        )
                except (IndexError, ValueError) as e:
                    self.logger.warning(
                        "Failed to calculate date-based return",
                        symbol=symbol,
                        period=period_name,
                        error=str(e),
                    )

        return results

    def _calculate_date_based_return(
        self,
        symbol_data: DataFrame,
        latest_date: datetime | Timestamp,
        latest_price: float,
        period_value: str,
    ) -> float | None:
        """日付ベースの騰落率を計算する.

        Parameters
        ----------
        symbol_data : DataFrame
            シンボルの価格データ
        latest_date : datetime | Timestamp
            最新日付
        latest_price : float
            最新価格
        period_value : str
            期間値（"mtd", "ytd", "prev_tue"）

        Returns
        -------
        float | None
            騰落率（パーセント）、計算不可の場合は None
        """
        if period_value == "mtd":
            start_of_period = latest_date.replace(day=1)
        elif period_value == "ytd":
            start_of_period = latest_date.replace(month=1, day=1)
        elif period_value == "prev_tue":
            # 先週火曜日を計算（週は月曜始まり）
            weekday = latest_date.weekday()
            days_to_prev_tue = weekday + 6
            start_of_period = latest_date - timedelta(days=days_to_prev_tue)
        else:
            self.logger.warning("Unknown period value", period_value=period_value)
            return None

        # 期間開始日以降の最初のデータを取得
        period_data = symbol_data[symbol_data["Date"] >= start_of_period]
        if period_data.empty:
            return None

        start_price = float(period_data.iloc[0]["value"])
        if start_price == 0:
            return None

        return_pct = ((latest_price - start_price) / start_price) * 100
        return round(return_pct, 2)

    def get_close_dataframe(self, list_symbol: list[str]) -> DataFrame:
        fetch_options = FetchOptions(
            symbols=list_symbol,
            start_date=(datetime.today() - timedelta(days=365 * 5 + 30)).strftime(
                "%Y-%m-%d"
            ),
            end_date=datetime.today().strftime("%Y-%m-%d"),
        )
        fetcher = YFinanceFetcher()
        all_data = fetcher.fetch(fetch_options)

        dfs: list[DataFrame] = [
            data.data[["close"]]
            .reset_index()
            .rename(columns={"close": "value"})
            .assign(symbol=data.symbol, variable="close")
            .reindex(columns=["Date", "symbol", "variable", "value"])
            for data in all_data
        ]

        df: DataFrame = pd.concat(dfs).sort_values("Date", ignore_index=True)
        return df

    def get_group_performance(
        self,
        group: str,
        subgroup: str | None = None,
    ) -> DataFrame:
        """指定グループのパフォーマンス（騰落率）を計算する.

        Parameters
        ----------
        group : str
            シンボルグループ名（"indices", "mag7", "sectors" 等）
        subgroup : str | None, optional
            サブグループ名（"us", "global" 等、indicesの場合に使用）

        Returns
        -------
        DataFrame
            騰落率データ（symbol, period, return_pct カラムを持つ）

        Examples
        --------
        >>> analyzer = PerformanceAnalyzer()
        >>> # 米国指数
        >>> us_indices = analyzer.get_group_performance("indices", "us")
        >>> # MAG7
        >>> mag7 = analyzer.get_group_performance("mag7")
        """
        returns, _ = self.get_group_performance_with_prices(group, subgroup)
        return returns

    def get_group_performance_with_prices(
        self,
        group: str,
        subgroup: str | None = None,
    ) -> tuple[DataFrame, DataFrame]:
        """指定グループのパフォーマンスと価格データを取得する.

        騰落率と価格データを一度に取得することで、
        最新日付の確認や追加分析が可能になる。

        Parameters
        ----------
        group : str
            シンボルグループ名（"indices", "mag7", "sectors" 等）
        subgroup : str | None, optional
            サブグループ名（"us", "global" 等、indicesの場合に使用）

        Returns
        -------
        tuple[DataFrame, DataFrame]
            (騰落率データ, 価格データ) のタプル
            - 騰落率データ: symbol, period, return_pct カラム
            - 価格データ: Date, symbol, variable, value カラム
        """
        symbols = get_symbols(group, subgroup)
        if not symbols:
            self.logger.warning(
                "No symbols found for group",
                group=group,
                subgroup=subgroup,
            )
            return (
                DataFrame({"symbol": [], "period": [], "return_pct": []}),
                DataFrame({"Date": [], "symbol": [], "variable": [], "value": []}),
            )

        self.logger.info(
            "Fetched symbols",
            group=group,
            subgroup=subgroup,
            symbol_count=len(symbols),
            symbols=symbols,
        )

        price = self.get_close_dataframe(list_symbol=symbols)
        return_periods = get_return_periods()
        self.logger.info("Return periods", periods=list(return_periods.keys()))

        returns = self.calculate_returns(price, return_periods)
        self.logger.info(
            "Calculated returns",
            group=group,
            result_count=len(returns),
            symbols=returns["symbol"].nunique() if not returns.empty else 0,
        )

        return returns, price

    def get_group_close(
        self,
        group: str,
        subgroup: str | None = None,
    ) -> DataFrame:
        """指定グループの終値データを取得する.

        Parameters
        ----------
        group : str
            シンボルグループ名（"indices", "mag7", "sectors" 等）
        subgroup : str | None, optional
            サブグループ名（"us", "global" 等、indicesの場合に使用）

        Returns
        -------
        DataFrame
            終値データ（Date, symbol, variable, value カラムを持つ）

        Examples
        --------
        >>> analyzer = PerformanceAnalyzer()
        >>> # 米国指数の終値
        >>> us_close = analyzer.get_group_close("indices", "us")
        >>> # MAG7の終値
        >>> mag7_close = analyzer.get_group_close("mag7")
        """
        symbols = get_symbols(group, subgroup)
        if not symbols:
            self.logger.warning(
                "No symbols found for group",
                group=group,
                subgroup=subgroup,
            )
            return DataFrame({"Date": [], "symbol": [], "variable": [], "value": []})

        self.logger.info(
            "Fetching close prices",
            group=group,
            subgroup=subgroup,
            symbol_count=len(symbols),
            symbols=symbols,
        )

        close_df = self.get_close_dataframe(list_symbol=symbols)
        self.logger.info(
            "Fetched close prices",
            group=group,
            result_count=len(close_df),
            symbols=close_df["symbol"].nunique() if not close_df.empty else 0,
        )

        return close_df

    def get_index_performance(self) -> DataFrame:
        """米国指数のパフォーマンス（騰落率）を計算する.

        Returns
        -------
        DataFrame
            騰落率データ（symbol, period, return_pct カラムを持つ）

        Note
        ----
        get_group_performance("indices", "us") のエイリアス
        """
        return self.get_group_performance("indices", "us")

    def get_global_index_performance(self) -> DataFrame:
        """グローバル指数のパフォーマンス（騰落率）を計算する.

        Returns
        -------
        DataFrame
            騰落率データ（symbol, period, return_pct カラムを持つ）

        Note
        ----
        get_group_performance("indices", "global") のエイリアス
        """
        return self.get_group_performance("indices", "global")

    def get_mag7_performance(self) -> DataFrame:
        """MAG7銘柄のパフォーマンス（騰落率）を計算する.

        Returns
        -------
        DataFrame
            騰落率データ（symbol, period, return_pct カラムを持つ）

        Note
        ----
        get_group_performance("mag7") のエイリアス
        """
        return self.get_group_performance("mag7")

    def get_sector_performance(self) -> DataFrame:
        """セクターETFのパフォーマンス（騰落率）を計算する.

        Returns
        -------
        DataFrame
            騰落率データ（symbol, period, return_pct カラムを持つ）

        Note
        ----
        get_group_performance("sectors") のエイリアス
        """
        return self.get_group_performance("sectors")

    def get_index_close(self) -> DataFrame:
        """米国指数の終値データを取得する.

        Returns
        -------
        DataFrame
            終値データ（Date, symbol, variable, value カラムを持つ）

        Note
        ----
        get_group_close("indices", "us") のエイリアス
        """
        return self.get_group_close("indices", "us")

    def get_global_index_close(self) -> DataFrame:
        """グローバル指数の終値データを取得する.

        Returns
        -------
        DataFrame
            終値データ（Date, symbol, variable, value カラムを持つ）

        Note
        ----
        get_group_close("indices", "global") のエイリアス
        """
        return self.get_group_close("indices", "global")

    def get_mag7_close(self) -> DataFrame:
        """MAG7銘柄の終値データを取得する.

        Returns
        -------
        DataFrame
            終値データ（Date, symbol, variable, value カラムを持つ）

        Note
        ----
        get_group_close("mag7") のエイリアス
        """
        return self.get_group_close("mag7")

    def get_sector_close(self) -> DataFrame:
        """セクターETFの終値データを取得する.

        Returns
        -------
        DataFrame
            終値データ（Date, symbol, variable, value カラムを持つ）

        Note
        ----
        get_group_close("sectors") のエイリアス
        """
        return self.get_group_close("sectors")


def main():
    """パフォーマンス分析のエントリーポイント."""
    setup_logging(level="INFO", format="console", force=True)
    analyzer = PerformanceAnalyzer()

    # 期間の表示順序を定義
    period_order = ["1D", "WoW", "1W", "MTD", "1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y"]

    # 米国指数の騰落率
    index_returns = analyzer.get_index_performance()
    print("\n=== US Index Performance ===")
    print(index_returns)
    pivot_index = index_returns.pivot(
        index="symbol", columns="period", values="return_pct"
    ).sort_values("1D", ascending=False)
    print(pivot_index.reindex(columns=period_order))

    # グローバル指数の騰落率
    global_returns = analyzer.get_global_index_performance()
    print("\n=== Global Index Performance ===")
    pivot_global = global_returns.pivot(
        index="symbol", columns="period", values="return_pct"
    ).sort_values("1D", ascending=False)
    print(pivot_global.reindex(columns=period_order))

    # MAG7の騰落率
    mag7_returns = analyzer.get_mag7_performance()
    print("\n=== MAG7 Performance ===")
    pivot_mag7 = mag7_returns.pivot(
        index="symbol", columns="period", values="return_pct"
    ).sort_values("1D", ascending=False)
    print(pivot_mag7.reindex(columns=period_order))

    # セクターETFの騰落率
    sector_returns = analyzer.get_sector_performance()
    print("\n=== Sector ETF Performance ===")
    pivot_sector = sector_returns.pivot(
        index="symbol", columns="period", values="return_pct"
    ).sort_values("1D", ascending=False)
    print(pivot_sector.reindex(columns=period_order))


if __name__ == "__main__":
    main()
