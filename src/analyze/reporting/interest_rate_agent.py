"""interest_rate_agent.py

AIエージェント向けの金利データ分析クラス。
JSON形式でイールドカーブ分析と金利変化データを出力する。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pandas import DataFrame
from utils_core.logging import get_logger

from analyze.reporting.interest_rate import InterestRateAnalyzer


@dataclass
class InterestRateResult:
    """金利分析結果を格納するデータクラス.

    Attributes
    ----------
    group : str
        データグループ名
    generated_at : str
        生成日時（ISO形式）
    periods : list[str]
        分析対象の期間リスト
    data : dict[str, dict[str, Any]]
        シリーズごとの最新値と変化量
        例: {"DGS10": {"latest": 4.25, "changes": {"1D": 0.02, "1W": 0.1}}}
    yield_curve : dict[str, Any]
        イールドカーブ分析結果
    data_freshness : dict[str, Any]
        データ鮮度情報（最新/最古の日付、日付ズレの有無）
    """

    group: str
    generated_at: str
    periods: list[str]
    data: dict[str, dict[str, Any]]
    yield_curve: dict[str, Any] = field(default_factory=dict)
    data_freshness: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換する."""
        return {
            "group": self.group,
            "generated_at": self.generated_at,
            "periods": self.periods,
            "data": self.data,
            "yield_curve": self.yield_curve,
            "data_freshness": self.data_freshness,
        }


class InterestRateAnalyzer4Agent:
    """AIエージェント向けの金利分析クラス.

    InterestRateAnalyzerの機能をラップし、AIエージェントが解釈しやすい
    JSON形式で結果を出力する。イールドカーブ分析と金利変化データを
    構造化して提供する。

    Examples
    --------
    >>> analyzer = InterestRateAnalyzer4Agent()
    >>> result = analyzer.get_interest_rate_data()
    >>> print(result.to_dict())
    {
        "group": "interest_rates",
        "generated_at": "2026-01-29T12:00:00",
        "periods": ["1D", "1W", "1M"],
        "data": {
            "DGS10": {"latest": 4.25, "changes": {"1D": 0.02, ...}},
            ...
        },
        "yield_curve": {"is_inverted": True, ...},
        "data_freshness": {...}
    }
    """

    # デフォルトの分析期間
    DEFAULT_PERIODS: list[str] = ["1D", "1W", "1M"]

    def __init__(self) -> None:
        self.logger = get_logger(__name__, component="InterestRateAnalyzer4Agent")
        self._analyzer = InterestRateAnalyzer()

    def _calculate_data_freshness(
        self,
        data: dict[str, DataFrame],
    ) -> dict[str, Any]:
        """各シリーズの最新日付とデータ鮮度情報を計算する.

        Parameters
        ----------
        data : dict[str, DataFrame]
            シリーズIDをキー、DataFrameを値とする辞書

        Returns
        -------
        dict[str, Any]
            データ鮮度情報
        """
        if not data:
            return {}

        latest_dates: dict[str, str] = {}
        for series_id, df in data.items():
            if df.empty or "value" not in df.columns:
                continue

            # NaNを除去して最新日付を取得
            valid_df = df.dropna(subset=["value"])
            if not valid_df.empty:
                max_date = valid_df.index.max()
                latest_dates[series_id] = max_date.strftime("%Y-%m-%d")

        if not latest_dates:
            return {}

        # 最新・最古の日付を計算
        date_values = list(latest_dates.values())
        newest_date = max(date_values)
        oldest_date = min(date_values)
        has_date_gap = newest_date != oldest_date

        # 日付ごとのシリーズをグループ化
        series_by_date: dict[str, list[str]] = {}
        for series_id, date_str in latest_dates.items():
            if date_str not in series_by_date:
                series_by_date[date_str] = []
            series_by_date[date_str].append(series_id)

        data_freshness: dict[str, Any] = {
            "newest_date": newest_date,
            "oldest_date": oldest_date,
            "has_date_gap": has_date_gap,
            "series_by_date": series_by_date,
        }

        if has_date_gap:
            self.logger.warning(
                "Date gap detected between series",
                newest_date=newest_date,
                oldest_date=oldest_date,
                series_counts={k: len(v) for k, v in series_by_date.items()},
            )

        return data_freshness

    def _extract_latest_values(
        self,
        data: dict[str, DataFrame],
    ) -> dict[str, float | None]:
        """各シリーズの最新値を抽出する.

        Parameters
        ----------
        data : dict[str, DataFrame]
            シリーズIDをキー、DataFrameを値とする辞書

        Returns
        -------
        dict[str, float | None]
            シリーズIDをキー、最新値を値とする辞書
        """
        latest_values: dict[str, float | None] = {}
        for series_id, df in data.items():
            if df.empty or "value" not in df.columns:
                latest_values[series_id] = None
                continue

            valid_df = df.dropna(subset=["value"])
            if not valid_df.empty:
                latest_values[series_id] = float(valid_df["value"].iloc[-1])
            else:
                latest_values[series_id] = None

        return latest_values

    def _build_data_structure(
        self,
        latest_values: dict[str, float | None],
        changes: dict[str, dict[str, float | None]],
    ) -> dict[str, dict[str, Any]]:
        """シリーズごとのデータ構造を構築する.

        Parameters
        ----------
        latest_values : dict[str, float | None]
            シリーズIDをキー、最新値を値とする辞書
        changes : dict[str, dict[str, float | None]]
            シリーズIDをキー、期間別変化量を値とする辞書

        Returns
        -------
        dict[str, dict[str, Any]]
            シリーズごとのlatestとchangesを含む辞書
        """
        data: dict[str, dict[str, Any]] = {}
        all_series = set(latest_values.keys()) | set(changes.keys())

        for series_id in all_series:
            data[series_id] = {
                "latest": latest_values.get(series_id),
                "changes": changes.get(series_id, {}),
            }

        return data

    def get_interest_rate_data(
        self,
        periods: list[str] | None = None,
    ) -> InterestRateResult:
        """金利データをJSON形式で取得する.

        Parameters
        ----------
        periods : list[str] | None, optional
            分析する期間のリスト（デフォルト: ["1D", "1W", "1M"]）

        Returns
        -------
        InterestRateResult
            構造化された金利分析結果

        Examples
        --------
        >>> analyzer = InterestRateAnalyzer4Agent()
        >>> result = analyzer.get_interest_rate_data()
        >>> print(result.data["DGS10"]["latest"])
        4.25
        >>> print(result.yield_curve["is_inverted"])
        True
        """
        if periods is None:
            periods = self.DEFAULT_PERIODS.copy()

        self.logger.info(
            "Getting interest rate data for agent",
            periods=periods,
        )

        # データ取得
        data = self._analyzer.fetch_data()

        # 最新値を抽出
        latest_values = self._extract_latest_values(data)

        # 変化量を計算
        changes = self._analyzer.calculate_changes(data, periods=periods)

        # データ構造を構築
        structured_data = self._build_data_structure(latest_values, changes)

        # イールドカーブ分析
        yield_curve = self._analyzer.analyze_yield_curve(data)

        # データ鮮度を計算
        data_freshness = self._calculate_data_freshness(data)

        self.logger.info(
            "Interest rate data generated",
            series_count=len(structured_data),
            has_date_gap=data_freshness.get("has_date_gap", False),
            is_inverted=yield_curve.get("is_inverted", False),
        )

        return InterestRateResult(
            group="interest_rates",
            generated_at=datetime.now().isoformat(),
            periods=periods,
            data=structured_data,
            yield_curve=yield_curve,
            data_freshness=data_freshness,
        )


def main() -> None:
    """エントリーポイント."""
    import json

    from utils_core.logging import setup_logging

    setup_logging(level="INFO", format="console", force=True)

    analyzer = InterestRateAnalyzer4Agent()

    # 金利データを取得
    print("\n=== Interest Rate Data (JSON) ===")
    result = analyzer.get_interest_rate_data()
    result_json = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    print(result_json)


if __name__ == "__main__":
    main()
