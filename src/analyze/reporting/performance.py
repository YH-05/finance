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
    def __init__(self) -> None:
        self.logger = get_logger(__name__, component="PerformanceAnalyzer")

    def _get_period_start_date(
        self,
        end_date: datetime,
        period_value: int | str,
    ) -> datetime:
        """期間の開始日を計算する.

        Parameters
        ----------
        end_date : datetime
            終了日（基準日）
        period_value : int | str
            期間値（営業日数または "mtd"/"ytd"）

        Returns
        -------
        datetime
            期間の開始日
        """
        if isinstance(period_value, int):
            # 営業日数の場合、カレンダー日数に変換（週末を考慮して約1.4倍）
            calendar_days = int(period_value * 1.4) + 5
            return end_date - timedelta(days=calendar_days)
        elif period_value == "mtd":
            # 月初来
            return end_date.replace(day=1)
        elif period_value == "ytd":
            # 年初来
            return end_date.replace(month=1, day=1)
        else:
            msg = f"Unknown period value: {period_value}"
            raise ValueError(msg)

    def calculate_returns(
        self,
        price_df: DataFrame,
        return_periods: dict[str, int | str],
    ) -> DataFrame:
        """各シンボル・各期間の騰落率を計算する.

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
            "Calculating returns",
            symbols=price_df["symbol"].nunique(),
            periods=list(return_periods.keys()),
        )

        results: list[dict[str, str | float]] = []

        for symbol in price_df["symbol"].unique():
            symbol_data = (
                price_df[price_df["symbol"] == symbol]
                .sort_values("Date")
                .reset_index(drop=True)
            )

            if symbol_data.empty:
                self.logger.warning("No data for symbol", symbol=symbol)
                continue

            # データはソート済みなので最後の行が最新
            latest_row = symbol_data.iloc[-1]
            latest_date = cast("Timestamp", pd.Timestamp(latest_row["Date"]))
            latest_price = float(latest_row["value"])

            for period_name, period_value in return_periods.items():
                try:
                    return_pct = self._calculate_single_return(
                        symbol_data=symbol_data,
                        latest_date=latest_date,
                        latest_price=latest_price,
                        period_value=period_value,
                    )

                    results.append(
                        {
                            "symbol": symbol,
                            "period": period_name,
                            "return_pct": return_pct,
                        }
                    )
                except (IndexError, ValueError) as e:
                    self.logger.warning(
                        "Failed to calculate return",
                        symbol=symbol,
                        period=period_name,
                        error=str(e),
                    )

        return DataFrame(results)

    def _calculate_single_return(
        self,
        symbol_data: DataFrame,
        latest_date: datetime | Timestamp,
        latest_price: float,
        period_value: int | str,
    ) -> float:
        """単一期間の騰落率を計算する.

        Parameters
        ----------
        symbol_data : DataFrame
            シンボルの価格データ
        latest_date : datetime
            最新日付
        latest_price : float
            最新価格
        period_value : int | str
            期間値

        Returns
        -------
        float
            騰落率（パーセント）
        """
        if isinstance(period_value, int):
            # 営業日数ベースの計算
            if len(symbol_data) <= period_value:
                msg = f"Insufficient data: need {period_value} days, have {len(symbol_data)}"
                raise ValueError(msg)
            start_price = symbol_data.iloc[-(period_value + 1)]["value"]
        else:
            # MTD/YTD の計算
            if period_value == "mtd":
                start_of_period = latest_date.replace(day=1)
            elif period_value == "ytd":
                start_of_period = latest_date.replace(month=1, day=1)
            else:
                msg = f"Unknown period: {period_value}"
                raise ValueError(msg)

            # 期間開始日以降の最初のデータを取得
            period_data = symbol_data[symbol_data["Date"] >= start_of_period]
            if period_data.empty:
                msg = f"No data for period start: {start_of_period}"
                raise ValueError(msg)
            start_price = period_data.iloc[0]["value"]

        return_pct = ((latest_price - start_price) / start_price) * 100
        return round(return_pct, 2)

    def get_price_dataframe(self, list_symbol: list[str]) -> DataFrame:
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

    def get_index_performance(self) -> DataFrame:
        """米国指数のパフォーマンス（騰落率）を計算する.

        Returns
        -------
        DataFrame
            騰落率データ（symbol, period, return_pct カラムを持つ）
        """
        symbols_us = get_symbols("indices", "us")
        self.logger.info(
            "Fetched symbols", symbol_count=len(symbols_us), symbols=symbols_us
        )
        price = self.get_price_dataframe(list_symbol=symbols_us)

        return_periods = get_return_periods()
        self.logger.info("Return periods", periods=list(return_periods.keys()))

        returns = self.calculate_returns(price, return_periods)
        self.logger.info(
            "Calculated returns",
            result_count=len(returns),
            symbols=returns["symbol"].nunique() if not returns.empty else 0,
        )

        return returns


def main():
    """パフォーマンス分析のエントリーポイント."""
    setup_logging(level="INFO", format="console", force=True)
    analyzer = PerformanceAnalyzer()

    # 米国指数の騰落率
    index_returns = analyzer.get_index_performance()
    print("\n=== US Index Performance ===")
    print(index_returns.pivot(index="symbol", columns="period", values="return_pct"))

    # MAG7の騰落率
    symbols_mag7 = get_symbols(group="mag7")
    price_mag7 = analyzer.get_price_dataframe(list_symbol=symbols_mag7)
    return_periods = get_return_periods()
    mag7_returns = analyzer.calculate_returns(price_mag7, return_periods)
    print("\n=== MAG7 Performance ===")
    print(mag7_returns.pivot(index="symbol", columns="period", values="return_pct"))


if __name__ == "__main__":
    main()
