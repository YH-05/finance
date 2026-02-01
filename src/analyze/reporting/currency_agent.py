"""currency_agent.py

AIエージェント向けの為替分析クラス。
JSON形式でクロスセクション・時系列分析が可能な構造を出力する。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pandas import DataFrame
from utils_core.logging import get_logger

from analyze.reporting.currency import CurrencyAnalyzer


@dataclass
class CurrencyResult:
    """為替分析結果を格納するデータクラス.

    Attributes
    ----------
    group : str
        シンボルグループ名
    subgroup : str | None
        サブグループ名
    base_currency : str
        基準通貨（JPY）
    generated_at : str
        生成日時（ISO形式）
    periods : list[str]
        分析対象の期間リスト
    symbols : dict[str, dict[str, float]]
        通貨ペアごとの期間別騰落率
    summary : dict[str, Any]
        サマリー情報（最強/最弱通貨、期間平均）
    latest_dates : dict[str, str]
        通貨ペアごとの最新取引日（ISO形式）
    data_freshness : dict[str, Any]
        データ鮮度情報（最新/最古の日付、日付ズレの有無）
    """

    group: str
    subgroup: str | None
    base_currency: str
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
            "base_currency": self.base_currency,
            "generated_at": self.generated_at,
            "periods": self.periods,
            "symbols": self.symbols,
            "summary": self.summary,
            "latest_dates": self.latest_dates,
            "data_freshness": self.data_freshness,
        }


class CurrencyAnalyzer4Agent:
    """AIエージェント向けの為替分析クラス.

    CurrencyAnalyzerの機能をラップし、AIエージェントが解釈しやすい
    JSON形式で結果を出力する。クロスセクション分析（通貨間比較）と
    時系列分析（期間別比較）の両方に対応した構造を提供する。

    Examples
    --------
    >>> analyzer = CurrencyAnalyzer4Agent()
    >>> # 円クロス為替のパフォーマンスをJSON形式で取得
    >>> result = analyzer.get_currency_performance()
    >>> print(result.to_dict())
    {
        "group": "currencies",
        "subgroup": "jpy_crosses",
        "base_currency": "JPY",
        "generated_at": "2026-01-26T12:00:00",
        "periods": ["1D", "1W", "1M"],
        "symbols": {"USDJPY=X": {"1D": 0.16, ...}, ...},
        "summary": {...}
    }
    """

    # 期間の順序定義
    PERIOD_ORDER: list[str] = ["1D", "1W", "1M"]

    def __init__(self) -> None:
        self.logger = get_logger(__name__, component="CurrencyAnalyzer4Agent")
        self._analyzer = CurrencyAnalyzer()

    def _convert_to_result(
        self,
        currency_data: dict[str, DataFrame],
        returns: dict[str, dict[str, float | None]],
    ) -> CurrencyResult:
        """為替データをCurrencyResultに変換する.

        Parameters
        ----------
        currency_data : dict[str, DataFrame]
            通貨ペアごとの価格データ
        returns : dict[str, dict[str, float | None]]
            通貨ペアごとの期間別騰落率

        Returns
        -------
        CurrencyResult
            構造化された為替分析結果
        """
        if not currency_data or not returns:
            self.logger.warning("Empty currency data or returns")
            return CurrencyResult(
                group="currencies",
                subgroup="jpy_crosses",
                base_currency="JPY",
                generated_at=datetime.now().isoformat(),
                periods=[],
                symbols={},
                summary={},
                latest_dates={},
                data_freshness={},
            )

        # 通貨ペアごとの期間別騰落率を構築（None を除外）
        symbols: dict[str, dict[str, float]] = {}
        all_periods: set[str] = set()

        for symbol, period_returns in returns.items():
            symbol_data: dict[str, float] = {}
            for period, return_pct in period_returns.items():
                if return_pct is not None:
                    symbol_data[period] = return_pct
                    all_periods.add(period)
            if symbol_data:
                symbols[symbol] = symbol_data

        # 期間リストを正しい順序で構築
        periods = [p for p in self.PERIOD_ORDER if p in all_periods]
        # 順序にない期間があれば末尾に追加
        periods.extend([p for p in all_periods if p not in self.PERIOD_ORDER])

        # サマリー情報を計算
        summary = self._calculate_summary(symbols, periods)

        # 最新日付とデータ鮮度を計算
        latest_dates, data_freshness = self._calculate_data_freshness(currency_data)

        self.logger.info(
            "Converted to CurrencyResult",
            symbol_count=len(symbols),
            period_count=len(periods),
            has_date_gap=data_freshness.get("has_date_gap", False),
        )

        return CurrencyResult(
            group="currencies",
            subgroup="jpy_crosses",
            base_currency="JPY",
            generated_at=datetime.now().isoformat(),
            periods=periods,
            symbols=symbols,
            summary=summary,
            latest_dates=latest_dates,
            data_freshness=data_freshness,
        )

    def _calculate_data_freshness(
        self,
        currency_data: dict[str, DataFrame],
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """各通貨ペアの最新日付とデータ鮮度情報を計算する.

        Parameters
        ----------
        currency_data : dict[str, DataFrame]
            通貨ペアごとの価格データ

        Returns
        -------
        tuple[dict[str, str], dict[str, Any]]
            (最新日付の辞書, データ鮮度情報)
        """
        if not currency_data:
            return {}, {}

        latest_dates: dict[str, str] = {}
        for symbol, df in currency_data.items():
            if not df.empty:
                # NaN を除去して最新日付を取得
                clean_df = df.dropna(subset=["close"])
                if not clean_df.empty:
                    max_date = clean_df.index.max()
                    latest_dates[symbol] = max_date.strftime("%Y-%m-%d")

        if not latest_dates:
            return {}, {}

        # データ鮮度情報を計算
        date_values = list(latest_dates.values())
        newest_date = max(date_values)
        oldest_date = min(date_values)
        has_date_gap = newest_date != oldest_date

        # 日付ごとの通貨ペア数をカウント
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
                "Date gap detected between currency pairs",
                newest_date=newest_date,
                oldest_date=oldest_date,
                date_counts={k: len(v) for k, v in date_counts.items()},
            )

        return latest_dates, data_freshness

    def _calculate_summary(
        self,
        symbols: dict[str, dict[str, float]],
        periods: list[str],
    ) -> dict[str, Any]:
        """サマリー情報を計算する.

        Parameters
        ----------
        symbols : dict[str, dict[str, float]]
            通貨ペアごとの期間別騰落率
        periods : list[str]
            期間リスト

        Returns
        -------
        dict[str, Any]
            サマリー情報
        """
        if not symbols or not periods:
            return {}

        # 全期間・全通貨ペアの騰落率をフラット化
        all_returns: list[tuple[str, str, float]] = []
        for symbol, period_returns in symbols.items():
            for period, return_pct in period_returns.items():
                all_returns.append((symbol, period, return_pct))

        if not all_returns:
            return {}

        # 最強通貨（最高の騰落率 = 円に対して最も上昇した通貨）
        strongest = max(all_returns, key=lambda x: x[2])
        strongest_currency = {
            "symbol": strongest[0],
            "period": strongest[1],
            "return_pct": strongest[2],
        }

        # 最弱通貨（最低の騰落率 = 円に対して最も下落/上昇が少なかった通貨）
        weakest = min(all_returns, key=lambda x: x[2])
        weakest_currency = {
            "symbol": weakest[0],
            "period": weakest[1],
            "return_pct": weakest[2],
        }

        # 期間別平均
        period_averages: dict[str, float] = {}
        for period in periods:
            period_returns = [r[2] for r in all_returns if r[1] == period]
            if period_returns:
                avg = sum(period_returns) / len(period_returns)
                period_averages[period] = round(avg, 2)

        # 期間別の最強/最弱通貨
        period_best: dict[str, dict[str, Any]] = {}
        period_worst: dict[str, dict[str, Any]] = {}
        for period in periods:
            period_data = [(r[0], r[2]) for r in all_returns if r[1] == period]
            if period_data:
                best = max(period_data, key=lambda x: x[1])
                worst = min(period_data, key=lambda x: x[1])
                period_best[period] = {
                    "symbol": best[0],
                    "return_pct": best[1],
                }
                period_worst[period] = {
                    "symbol": worst[0],
                    "return_pct": worst[1],
                }

        return {
            "strongest_currency": strongest_currency,
            "weakest_currency": weakest_currency,
            "period_averages": period_averages,
            "period_best": period_best,
            "period_worst": period_worst,
        }

    def get_currency_performance(self) -> CurrencyResult:
        """円クロス為替のパフォーマンスをJSON形式で取得する.

        Returns
        -------
        CurrencyResult
            構造化された為替分析結果

        Examples
        --------
        >>> analyzer = CurrencyAnalyzer4Agent()
        >>> result = analyzer.get_currency_performance()
        >>> print(result.symbols["USDJPY=X"]["1D"])
        0.16
        >>> # 最強通貨の確認
        >>> print(result.summary["strongest_currency"])
        {"symbol": "EURJPY=X", "period": "1M", "return_pct": 1.5}
        """
        self.logger.info("Getting currency performance for agent")

        # CurrencyAnalyzer からデータを取得
        currency_data = self._analyzer.fetch_data()
        returns = self._analyzer.calculate_returns(
            currency_data, periods=["1D", "1W", "1M"]
        )

        return self._convert_to_result(currency_data, returns)


def main() -> None:
    """エントリーポイント."""
    import json

    from utils_core.logging import setup_logging

    setup_logging(level="INFO", format="console", force=True)

    analyzer = CurrencyAnalyzer4Agent()

    # 円クロス為替のパフォーマンスを取得
    print("\n=== Currency Performance (JSON) ===")
    result = analyzer.get_currency_performance()
    result_json = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    print(result_json)


if __name__ == "__main__":
    main()
