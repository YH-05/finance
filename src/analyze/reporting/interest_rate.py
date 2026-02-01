"""interest_rate.py

米国債利回りとFF金利を分析するInterestRateAnalyzerクラス。

FRED APIを使用して金利データを取得し、期間別の変化量計算と
イールドカーブ分析を提供する。

対象シリーズ:
- DGS2: 2年国債利回り
- DGS10: 10年国債利回り
- DGS30: 30年国債利回り
- FEDFUNDS: フェデラルファンド金利
- T10Y2Y: 10年-2年スプレッド
"""

from datetime import datetime
from typing import Any

import pandas as pd
from pandas import DataFrame

from market.fred import FREDFetcher
from market.fred.types import FetchOptions
from utils_core.logging import get_logger


class InterestRateAnalyzer:
    """米国債利回りとFF金利を分析するクラス.

    FRED APIを使用して金利データを取得し、期間別の変化量（差分）を計算する。
    また、イールドカーブの形状分析（逆イールド判定など）も行う。

    Attributes
    ----------
    target_series : list[str]
        分析対象のFREDシリーズID一覧

    Examples
    --------
    >>> analyzer = InterestRateAnalyzer()
    >>> data = analyzer.fetch_data()
    >>> changes = analyzer.calculate_changes(data, periods=["1D", "1W", "1M"])
    >>> summary = analyzer.get_summary()
    """

    # 分析対象のシリーズ
    TARGET_SERIES: list[str] = ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]

    # 期間の定義（営業日数）
    PERIOD_DAYS: dict[str, int] = {
        "1D": 1,
        "1W": 5,  # 1週間 = 5営業日
        "1M": 21,  # 1ヶ月 = 約21営業日
    }

    # イールドカーブの傾斜判定閾値
    SLOPE_THRESHOLDS: dict[str, float] = {
        "steep": 1.0,  # スプレッド > 1.0% → スティープ
        "flat": 0.2,  # スプレッド < 0.2% → フラット
    }

    def __init__(self) -> None:
        """InterestRateAnalyzerを初期化する."""
        self.logger = get_logger(__name__, component="InterestRateAnalyzer")
        self._fetcher: FREDFetcher | None = None
        self.logger.debug("InterestRateAnalyzer initialized")

    @property
    def target_series(self) -> list[str]:
        """分析対象のシリーズIDを返す.

        Returns
        -------
        list[str]
            FREDシリーズIDのリスト
        """
        return self.TARGET_SERIES.copy()

    def _get_fetcher(self) -> FREDFetcher:
        """FREDFetcherインスタンスを取得する.

        Returns
        -------
        FREDFetcher
            FRED APIクライアント
        """
        if self._fetcher is None:
            self._fetcher = FREDFetcher()
            self.logger.debug("FREDFetcher created")
        return self._fetcher

    def fetch_data(
        self,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
    ) -> dict[str, DataFrame]:
        """対象シリーズのデータをFREDから取得する.

        Parameters
        ----------
        start_date : datetime | str | None, optional
            データ取得開始日（デフォルト: 1年前）
        end_date : datetime | str | None, optional
            データ取得終了日（デフォルト: 今日）

        Returns
        -------
        dict[str, DataFrame]
            シリーズIDをキー、DataFrameを値とする辞書
            各DataFrameは 'value' 列を持ち、インデックスは日付

        Examples
        --------
        >>> analyzer = InterestRateAnalyzer()
        >>> data = analyzer.fetch_data()
        >>> data["DGS10"].head()
                     value
        2025-01-29    4.25
        2025-01-30    4.28
        ...
        """
        self.logger.info(
            "Fetching interest rate data",
            series=self.TARGET_SERIES,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        fetcher = self._get_fetcher()
        options = FetchOptions(
            symbols=self.TARGET_SERIES,
            start_date=start_date,
            end_date=end_date,
        )

        results = fetcher.fetch(options)

        data: dict[str, DataFrame] = {}
        for result in results:
            if not result.is_empty:
                data[result.symbol] = result.data
                self.logger.debug(
                    "Series fetched",
                    series_id=result.symbol,
                    rows=len(result.data),
                )
            else:
                self.logger.warning(
                    "Empty data for series",
                    series_id=result.symbol,
                )

        self.logger.info(
            "Data fetch completed",
            total_series=len(self.TARGET_SERIES),
            fetched_series=len(data),
        )

        return data

    def calculate_changes(
        self,
        data: dict[str, DataFrame],
        periods: list[str] | None = None,
    ) -> dict[str, dict[str, float | None]]:
        """期間別の変化量（差分）を計算する.

        Parameters
        ----------
        data : dict[str, DataFrame]
            fetch_data()で取得したデータ
        periods : list[str] | None, optional
            計算する期間のリスト（デフォルト: ["1D", "1W", "1M"]）

        Returns
        -------
        dict[str, dict[str, float | None]]
            シリーズIDをキー、期間別変化量を値とする辞書
            データ不足の場合はNone

        Examples
        --------
        >>> analyzer = InterestRateAnalyzer()
        >>> data = analyzer.fetch_data()
        >>> changes = analyzer.calculate_changes(data, periods=["1D", "1W"])
        >>> changes["DGS10"]["1D"]
        0.03  # 前日比+0.03%
        """
        if periods is None:
            periods = ["1D", "1W", "1M"]

        self.logger.info(
            "Calculating changes",
            series_count=len(data),
            periods=periods,
        )

        result: dict[str, dict[str, float | None]] = {}

        for series_id, df in data.items():
            result[series_id] = {}

            if df.empty or "value" not in df.columns:
                for period in periods:
                    result[series_id][period] = None
                continue

            # NaNを除去してソート
            clean_df = df.dropna(subset=["value"]).sort_index()

            if clean_df.empty:
                for period in periods:
                    result[series_id][period] = None
                continue

            latest_value = float(clean_df["value"].iloc[-1])

            for period in periods:
                days = self.PERIOD_DAYS.get(period)
                if days is None:
                    self.logger.warning(
                        "Unknown period",
                        period=period,
                    )
                    result[series_id][period] = None
                    continue

                if len(clean_df) <= days:
                    self.logger.debug(
                        "Insufficient data for period",
                        series_id=series_id,
                        period=period,
                        required_days=days,
                        available_days=len(clean_df),
                    )
                    result[series_id][period] = None
                    continue

                # 指定日数前の値を取得
                past_value = float(clean_df["value"].iloc[-(days + 1)])
                change = round(latest_value - past_value, 4)
                result[series_id][period] = change

                self.logger.debug(
                    "Change calculated",
                    series_id=series_id,
                    period=period,
                    latest=latest_value,
                    past=past_value,
                    change=change,
                )

        return result

    def analyze_yield_curve(
        self,
        data: dict[str, DataFrame],
    ) -> dict[str, Any]:
        """イールドカーブの形状を分析する.

        10年-2年スプレッドを使用して、イールドカーブの傾斜状態を判定する。

        Parameters
        ----------
        data : dict[str, DataFrame]
            fetch_data()で取得したデータ

        Returns
        -------
        dict[str, Any]
            イールドカーブ分析結果
            - is_inverted: 逆イールドかどうか
            - spread_10y_2y: 10年-2年スプレッド（%）
            - slope_status: 傾斜状態（steep/normal/flat/inverted）
            - dgs2_latest: 2年国債利回り
            - dgs10_latest: 10年国債利回り
            - dgs30_latest: 30年国債利回り

        Examples
        --------
        >>> analyzer = InterestRateAnalyzer()
        >>> data = analyzer.fetch_data()
        >>> result = analyzer.analyze_yield_curve(data)
        >>> result["is_inverted"]
        True  # 逆イールド状態
        """
        self.logger.info("Analyzing yield curve")

        result: dict[str, Any] = {
            "is_inverted": False,
            "spread_10y_2y": None,
            "slope_status": "unknown",
            "dgs2_latest": None,
            "dgs10_latest": None,
            "dgs30_latest": None,
        }

        # T10Y2Yスプレッドを取得
        if "T10Y2Y" in data and not data["T10Y2Y"].empty:
            spread_df = data["T10Y2Y"].dropna(subset=["value"])
            if not spread_df.empty:
                spread = float(spread_df["value"].iloc[-1])
                result["spread_10y_2y"] = spread
                result["is_inverted"] = spread < 0

                # 傾斜状態を判定
                if spread < 0:
                    result["slope_status"] = "inverted"
                elif spread >= self.SLOPE_THRESHOLDS["steep"]:
                    result["slope_status"] = "steep"
                elif spread <= self.SLOPE_THRESHOLDS["flat"]:
                    result["slope_status"] = "flat"
                else:
                    result["slope_status"] = "normal"

        # 各金利の最新値を取得
        for series_id, key in [
            ("DGS2", "dgs2_latest"),
            ("DGS10", "dgs10_latest"),
            ("DGS30", "dgs30_latest"),
        ]:
            if series_id in data and not data[series_id].empty:
                series_df = data[series_id].dropna(subset=["value"])
                if not series_df.empty:
                    result[key] = float(series_df["value"].iloc[-1])

        self.logger.info(
            "Yield curve analysis completed",
            is_inverted=result["is_inverted"],
            spread=result["spread_10y_2y"],
            slope_status=result["slope_status"],
        )

        return result

    def get_summary(
        self,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
    ) -> dict[str, Any]:
        """金利データのサマリーを取得する.

        データ取得、変化量計算、イールドカーブ分析を一括で実行し、
        結果をまとめたサマリーを返す。

        Parameters
        ----------
        start_date : datetime | str | None, optional
            データ取得開始日
        end_date : datetime | str | None, optional
            データ取得終了日

        Returns
        -------
        dict[str, Any]
            サマリー情報
            - generated_at: 生成日時
            - latest_values: 各シリーズの最新値
            - changes: 期間別変化量
            - yield_curve: イールドカーブ分析結果

        Examples
        --------
        >>> analyzer = InterestRateAnalyzer()
        >>> summary = analyzer.get_summary()
        >>> summary["latest_values"]["DGS10"]
        4.25
        >>> summary["changes"]["DGS10"]["1D"]
        0.03
        >>> summary["yield_curve"]["is_inverted"]
        False
        """
        self.logger.info("Generating interest rate summary")

        # データ取得
        data = self.fetch_data(start_date=start_date, end_date=end_date)

        # 最新値を抽出
        latest_values: dict[str, float | None] = {}
        for series_id in self.TARGET_SERIES:
            if series_id in data and not data[series_id].empty:
                df = data[series_id].dropna(subset=["value"])
                if not df.empty:
                    latest_values[series_id] = float(df["value"].iloc[-1])
                else:
                    latest_values[series_id] = None
            else:
                latest_values[series_id] = None

        # 変化量計算
        changes = self.calculate_changes(data, periods=["1D", "1W", "1M"])

        # イールドカーブ分析
        yield_curve = self.analyze_yield_curve(data)

        summary = {
            "generated_at": datetime.now().isoformat(),
            "latest_values": latest_values,
            "changes": changes,
            "yield_curve": yield_curve,
        }

        self.logger.info(
            "Summary generated",
            series_count=len(latest_values),
            has_yield_curve=yield_curve["spread_10y_2y"] is not None,
        )

        return summary


__all__ = ["InterestRateAnalyzer"]
