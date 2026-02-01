"""
performance_agent.py

AIエージェント向けのパフォーマンス分析クラス。
JSON形式でクロスセクション・時系列分析が可能な構造を出力する。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pandas import DataFrame
from utils_core.logging import get_logger

from analyze.reporting.performance import PerformanceAnalyzer


@dataclass
class PerformanceResult:
    """パフォーマンス分析結果を格納するデータクラス.

    Attributes
    ----------
    group : str
        シンボルグループ名
    subgroup : str | None
        サブグループ名
    generated_at : str
        生成日時（ISO形式）
    periods : list[str]
        分析対象の期間リスト
    symbols : dict[str, dict[str, float]]
        シンボルごとの期間別騰落率
    summary : dict[str, Any]
        サマリー情報（最良/最悪パフォーマー、期間平均）
    latest_dates : dict[str, str]
        シンボルごとの最新取引日（ISO形式）
        市場ごとの取得タイミングのズレを確認するために使用
    data_freshness : dict[str, Any]
        データ鮮度情報（最新/最古の日付、日付ズレの有無）
    """

    group: str
    subgroup: str | None
    generated_at: str
    periods: list[str]
    symbols: dict[str, dict[str, float]]
    summary: dict[str, Any] = field(default_factory=dict)
    latest_dates: dict[str, str] = field(default_factory=dict)
    data_freshness: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換する."""
        return {
            "group": self.group,
            "subgroup": self.subgroup,
            "generated_at": self.generated_at,
            "periods": self.periods,
            "symbols": self.symbols,
            "summary": self.summary,
            "latest_dates": self.latest_dates,
            "data_freshness": self.data_freshness,
        }


class PerformanceAnalyzer4Agent:
    """AIエージェント向けのパフォーマンス分析クラス.

    PerformanceAnalyzerの機能をラップし、AIエージェントが解釈しやすい
    JSON形式で結果を出力する。クロスセクション分析（銘柄間比較）と
    時系列分析（期間別比較）の両方に対応した構造を提供する。

    Examples
    --------
    >>> analyzer = PerformanceAnalyzer4Agent()
    >>> # MAG7のパフォーマンスをJSON形式で取得
    >>> result = analyzer.get_group_performance("mag7")
    >>> print(result.to_dict())
    {
        "group": "mag7",
        "subgroup": null,
        "generated_at": "2026-01-26T12:00:00",
        "periods": ["1D", "1W", "MTD", ...],
        "symbols": {"AAPL": {"1D": 1.5, ...}, ...},
        "summary": {...}
    }
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__, component="PerformanceAnalyzer4Agent")
        self._analyzer = PerformanceAnalyzer()

    def _convert_to_result(
        self,
        returns_df: DataFrame,
        price_df: DataFrame,
        group: str,
        subgroup: str | None = None,
    ) -> PerformanceResult:
        """DataFrameをPerformanceResultに変換する.

        Parameters
        ----------
        returns_df : DataFrame
            騰落率データ（symbol, period, return_pct カラムを持つ）
        price_df : DataFrame
            価格データ（Date, symbol, variable, value カラムを持つ）
        group : str
            シンボルグループ名
        subgroup : str | None
            サブグループ名

        Returns
        -------
        PerformanceResult
            構造化されたパフォーマンス結果
        """
        if returns_df.empty:
            self.logger.warning(
                "Empty returns dataframe",
                group=group,
                subgroup=subgroup,
            )
            return PerformanceResult(
                group=group,
                subgroup=subgroup,
                generated_at=datetime.now().isoformat(),
                periods=[],
                symbols={},
                summary={},
                latest_dates={},
                data_freshness={},
            )

        # シンボルごとの期間別騰落率を構築
        symbols: dict[str, dict[str, float]] = {}
        for symbol in returns_df["symbol"].unique():
            symbol_data = returns_df[returns_df["symbol"] == symbol]
            symbols[str(symbol)] = {
                str(row["period"]): float(row["return_pct"])
                for _, row in symbol_data.iterrows()
            }

        # 期間リストを取得（順序を維持）
        period_order = [
            "1D",
            "WoW",
            "1W",
            "MTD",
            "1M",
            "3M",
            "6M",
            "YTD",
            "1Y",
            "3Y",
            "5Y",
        ]
        available_periods = returns_df["period"].unique().tolist()
        periods = [p for p in period_order if p in available_periods]
        # 順序にない期間があれば末尾に追加
        periods.extend([p for p in available_periods if p not in period_order])

        # サマリー情報を計算
        summary = self._calculate_summary(returns_df, periods)

        # 最新日付とデータ鮮度を計算
        latest_dates, data_freshness = self._calculate_data_freshness(price_df)

        self.logger.info(
            "Converted to PerformanceResult",
            group=group,
            subgroup=subgroup,
            symbol_count=len(symbols),
            period_count=len(periods),
            has_date_gap=data_freshness.get("has_date_gap", False),
        )

        return PerformanceResult(
            group=group,
            subgroup=subgroup,
            generated_at=datetime.now().isoformat(),
            periods=periods,
            symbols=symbols,
            summary=summary,
            latest_dates=latest_dates,
            data_freshness=data_freshness,
        )

    def _calculate_data_freshness(
        self,
        price_df: DataFrame,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """各銘柄の最新日付とデータ鮮度情報を計算する.

        Parameters
        ----------
        price_df : DataFrame
            価格データ（Date, symbol, variable, value カラムを持つ）

        Returns
        -------
        tuple[dict[str, str], dict[str, Any]]
            (最新日付の辞書, データ鮮度情報)
        """
        if price_df.empty:
            return {}, {}

        # NaN を除去して各銘柄の最新日付を取得
        valid_data = price_df.dropna(subset=["value"])

        latest_dates: dict[str, str] = {}
        for symbol in valid_data["symbol"].unique():
            symbol_data = valid_data[valid_data["symbol"] == symbol]
            if not symbol_data.empty:
                max_date = symbol_data["Date"].max()
                latest_dates[str(symbol)] = max_date.strftime("%Y-%m-%d")

        if not latest_dates:
            return {}, {}

        # データ鮮度情報を計算
        date_values = list(latest_dates.values())
        newest_date = max(date_values)
        oldest_date = min(date_values)
        has_date_gap = newest_date != oldest_date

        # 日付ごとの銘柄数をカウント
        date_counts: dict[str, list[str]] = {}
        for symbol, date_str in latest_dates.items():
            if date_str not in date_counts:
                date_counts[date_str] = []
            date_counts[date_str].append(symbol)

        data_freshness: dict[str, Any] = {
            "newest_date": newest_date,
            "oldest_date": oldest_date,
            "has_date_gap": has_date_gap,
            "symbols_by_date": date_counts,
        }

        if has_date_gap:
            self.logger.warning(
                "Date gap detected between symbols",
                newest_date=newest_date,
                oldest_date=oldest_date,
                date_counts={k: len(v) for k, v in date_counts.items()},
            )

        return latest_dates, data_freshness

    def _calculate_summary(
        self,
        returns_df: DataFrame,
        periods: list[str],
    ) -> dict[str, Any]:
        """サマリー情報を計算する.

        Parameters
        ----------
        returns_df : DataFrame
            騰落率データ
        periods : list[str]
            期間リスト

        Returns
        -------
        dict[str, Any]
            サマリー情報
        """
        if returns_df.empty:
            return {}

        # 最良パフォーマー（全期間で最高の騰落率）
        best_idx = returns_df["return_pct"].idxmax()
        best_row = returns_df.loc[best_idx]
        best_performer = {
            "symbol": best_row["symbol"],
            "period": best_row["period"],
            "return_pct": best_row["return_pct"],
        }

        # 最悪パフォーマー（全期間で最低の騰落率）
        worst_idx = returns_df["return_pct"].idxmin()
        worst_row = returns_df.loc[worst_idx]
        worst_performer = {
            "symbol": worst_row["symbol"],
            "period": worst_row["period"],
            "return_pct": worst_row["return_pct"],
        }

        # 期間別平均
        period_averages = (
            returns_df.groupby("period")["return_pct"].mean().round(2).to_dict()
        )
        # 期間順序を維持
        period_averages = {p: period_averages.get(p, 0.0) for p in periods}

        # 期間別の最良/最悪銘柄
        period_best: dict[str, dict[str, Any]] = {}
        period_worst: dict[str, dict[str, Any]] = {}
        for period in periods:
            period_data = returns_df[returns_df["period"] == period]
            if not period_data.empty:
                best_in_period = period_data.loc[period_data["return_pct"].idxmax()]
                worst_in_period = period_data.loc[period_data["return_pct"].idxmin()]
                period_best[period] = {
                    "symbol": best_in_period["symbol"],
                    "return_pct": best_in_period["return_pct"],
                }
                period_worst[period] = {
                    "symbol": worst_in_period["symbol"],
                    "return_pct": worst_in_period["return_pct"],
                }

        return {
            "best_performer": best_performer,
            "worst_performer": worst_performer,
            "period_averages": period_averages,
            "period_best": period_best,
            "period_worst": period_worst,
        }

    def get_group_performance(
        self,
        group: str,
        subgroup: str | None = None,
    ) -> PerformanceResult:
        """指定グループのパフォーマンスをJSON形式で取得する.

        Parameters
        ----------
        group : str
            シンボルグループ名（"indices", "mag7", "sectors" 等）
        subgroup : str | None, optional
            サブグループ名（"us", "global" 等）

        Returns
        -------
        PerformanceResult
            構造化されたパフォーマンス結果

        Examples
        --------
        >>> analyzer = PerformanceAnalyzer4Agent()
        >>> result = analyzer.get_group_performance("mag7")
        >>> print(result.symbols["AAPL"]["1D"])
        1.5
        >>> # 最新日付の確認
        >>> print(result.latest_dates)
        {"AAPL": "2026-01-24", ...}
        >>> # 日付ズレの確認
        >>> print(result.data_freshness["has_date_gap"])
        False
        """
        self.logger.info(
            "Getting group performance for agent",
            group=group,
            subgroup=subgroup,
        )

        returns_df, price_df = self._analyzer.get_group_performance_with_prices(
            group, subgroup
        )
        return self._convert_to_result(returns_df, price_df, group, subgroup)

    def get_index_performance(self) -> PerformanceResult:
        """米国指数のパフォーマンスを取得する.

        Returns
        -------
        PerformanceResult
            構造化されたパフォーマンス結果
        """
        return self.get_group_performance("indices", "us")

    def get_global_index_performance(self) -> PerformanceResult:
        """グローバル指数のパフォーマンスを取得する.

        Returns
        -------
        PerformanceResult
            構造化されたパフォーマンス結果
        """
        return self.get_group_performance("indices", "global")

    def get_mag7_performance(self) -> PerformanceResult:
        """MAG7銘柄のパフォーマンスを取得する.

        Returns
        -------
        PerformanceResult
            構造化されたパフォーマンス結果
        """
        return self.get_group_performance("mag7")

    def get_sector_performance(self) -> PerformanceResult:
        """セクターETFのパフォーマンスを取得する.

        Returns
        -------
        PerformanceResult
            構造化されたパフォーマンス結果
        """
        return self.get_group_performance("sectors")

    def get_commodity_performance(self) -> PerformanceResult:
        """コモディティのパフォーマンスを取得する.

        Returns
        -------
        PerformanceResult
            構造化されたパフォーマンス結果
        """
        return self.get_group_performance("commodities")


def main() -> None:
    """エントリーポイント."""
    import json

    from utils_core.logging import setup_logging

    setup_logging(level="INFO", format="console", force=True)

    analyzer = PerformanceAnalyzer4Agent()

    # MAG7のパフォーマンスを取得
    print("\n=== MAG7 Performance (JSON) ===")
    mag7_result = analyzer.get_mag7_performance()
    mag7_result_json = json.dumps(mag7_result.to_dict(), indent=2, ensure_ascii=False)
    print(mag7_result_json)

    # 米国指数のパフォーマンスを取得
    print("\n=== US Index Performance (JSON) ===")
    index_result = analyzer.get_index_performance()
    index_result_json = json.dumps(index_result.to_dict(), indent=2, ensure_ascii=False)
    print(index_result_json)

    # コモディティのパフォーマンスを取得
    print("\n=== Commodity Performance (JSON) ===")
    commodity_result = analyzer.get_commodity_performance()
    commodity_result_json = json.dumps(
        commodity_result.to_dict(), indent=2, ensure_ascii=False
    )
    print(commodity_result_json)


if __name__ == "__main__":
    main()
