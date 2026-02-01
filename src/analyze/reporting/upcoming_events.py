"""決算発表日および経済指標発表予定を取得するモジュール.

yfinance を使用して決算発表日を取得する。
ticker.calendar を優先的に使用し、KeyError が発生した場合は
get_earnings_dates() にフォールバックする。

FRED API を使用して経済指標の発表予定を取得する。

Issue: #2419 (決算発表日), #2420 (経済指標発表予定)
参照:
- https://github.com/ranaroussi/yfinance/issues/2143
- https://fred.stlouisfed.org/docs/api/fred/release_dates.html

Examples
--------
>>> # 決算発表日
>>> analyzer = UpcomingEventsAnalyzer()
>>> results = analyzer.get_upcoming_earnings(days_ahead=14)
>>> for r in results:
...     print(f"{r.symbol}: {r.earnings_date}")

>>> # 経済指標発表予定
>>> result = get_upcoming_economic_releases(days_ahead=14)
>>> for item in result["upcoming_economic_releases"]:
...     print(f"{item['name_ja']}: {item['release_date']}")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import httpx
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from pandas import DataFrame, Timestamp
from utils_core.logging import get_logger

logger = get_logger(__name__, module="upcoming_events")


# =============================================================================
# Constants
# =============================================================================

TOP20_SYMBOLS = [
    # MAG7
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    # Top 8-15
    "BRK-B",
    "LLY",
    "V",
    "UNH",
    "JPM",
    "XOM",
    "JNJ",
    "MA",
    # Top 16-20
    "PG",
    "HD",
    "AVGO",
    "CVX",
    "MRK",
]

# Major economic releases to track from FRED
# See: https://fred.stlouisfed.org/docs/api/fred/release_dates.html
MAJOR_RELEASES: list[dict[str, Any]] = [
    {
        "release_id": 10,
        "name": "Employment Situation",
        "name_ja": "雇用統計",
        "importance": "high",
    },
    {
        "release_id": 50,
        "name": "Gross Domestic Product",
        "name_ja": "GDP速報",
        "importance": "high",
    },
    {
        "release_id": 21,
        "name": "Consumer Price Index",
        "name_ja": "消費者物価指数",
        "importance": "high",
    },
    {
        "release_id": 53,
        "name": "FOMC Statement",
        "name_ja": "FOMC声明",
        "importance": "high",
    },
    {
        "release_id": 46,
        "name": "Producer Price Index",
        "name_ja": "生産者物価指数",
        "importance": "medium",
    },
    {
        "release_id": 328,
        "name": "Personal Income and Outlays",
        "name_ja": "個人所得・支出",
        "importance": "medium",
    },
    {
        "release_id": 83,
        "name": "Industrial Production",
        "name_ja": "鉱工業生産",
        "importance": "low",
    },
    {
        "release_id": 120,
        "name": "Retail Sales",
        "name_ja": "小売売上高",
        "importance": "medium",
    },
]

# FRED API configuration
FRED_API_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY_ENV = "FRED_API_KEY"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class EarningsDateInfo:
    """決算発表日情報を格納するデータクラス.

    Attributes
    ----------
    symbol : str
        ティッカーシンボル（例: "AAPL"）
    name : str
        企業名（例: "Apple Inc."）
    earnings_date : datetime
        決算発表予定日（タイムゾーン付き）
    source : str
        データソース（"calendar" または "earnings_dates"）
    """

    symbol: str
    name: str
    earnings_date: datetime
    source: str = field(default="unknown")

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換する.

        Returns
        -------
        dict[str, Any]
            シリアライズ可能な辞書
        """
        return {
            "symbol": self.symbol,
            "name": self.name,
            "earnings_date": self.earnings_date.strftime("%Y-%m-%d"),
            "source": self.source,
        }


@dataclass
class EconomicReleaseInfo:
    """経済指標発表予定情報を格納するデータクラス.

    Attributes
    ----------
    release_id : int
        FRED リリースID（例: 10）
    name : str
        リリース名（例: "Employment Situation"）
    name_ja : str
        日本語名（例: "雇用統計"）
    release_date : datetime
        発表予定日（タイムゾーン付き）
    importance : str
        重要度（"high", "medium", "low"）
    """

    release_id: int
    name: str
    name_ja: str
    release_date: datetime
    importance: Literal["high", "medium", "low"]

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換する.

        Returns
        -------
        dict[str, Any]
            シリアライズ可能な辞書
        """
        return {
            "release_id": self.release_id,
            "name": self.name,
            "name_ja": self.name_ja,
            "release_date": self.release_date.strftime("%Y-%m-%d"),
            "importance": self.importance,
        }


# =============================================================================
# Analyzer Class
# =============================================================================


class UpcomingEventsAnalyzer:
    """S&P500時価総額上位20社の決算発表日を取得するクラス.

    yfinance の ticker.calendar を優先的に使用し、
    KeyError が発生した場合は get_earnings_dates() にフォールバックする。

    Attributes
    ----------
    default_symbols : list[str]
        デフォルトの対象銘柄（TOP20）

    Examples
    --------
    >>> analyzer = UpcomingEventsAnalyzer()
    >>> results = analyzer.get_upcoming_earnings(days_ahead=14)
    >>> for r in results:
    ...     print(f"{r.symbol}: {r.earnings_date}")
    """

    def __init__(self, symbols: list[str] | None = None) -> None:
        """初期化.

        Parameters
        ----------
        symbols : list[str] | None, optional
            対象銘柄リスト。指定しない場合はTOP20を使用
        """
        self.default_symbols = symbols if symbols is not None else TOP20_SYMBOLS.copy()
        self.logger = get_logger(__name__, component="UpcomingEventsAnalyzer")
        self.logger.debug(
            "UpcomingEventsAnalyzer initialized",
            symbol_count=len(self.default_symbols),
        )

    def get_earnings_date_for_symbol(
        self,
        symbol: str,
    ) -> EarningsDateInfo | None:
        """単一銘柄の次回決算発表日を取得する.

        ticker.calendar を優先的に使用し、KeyError が発生した場合は
        get_earnings_dates() にフォールバックする。

        Parameters
        ----------
        symbol : str
            ティッカーシンボル（例: "AAPL"）

        Returns
        -------
        EarningsDateInfo | None
            決算発表日情報。取得できない場合は None
        """
        self.logger.debug("Fetching earnings date", symbol=symbol)

        try:
            ticker = yf.Ticker(symbol)

            # 企業名を取得
            info = ticker.info
            company_name = info.get("shortName", symbol)

            # 1. ticker.calendar を試行
            earnings_date, source = self._try_calendar(ticker, symbol)

            # 2. カレンダーで取得できなかった場合、get_earnings_dates にフォールバック
            if earnings_date is None:
                earnings_date, source = self._try_earnings_dates(ticker, symbol)

            if earnings_date is None:
                self.logger.debug("No earnings date found", symbol=symbol)
                return None

            self.logger.debug(
                "Earnings date found",
                symbol=symbol,
                earnings_date=earnings_date.isoformat(),
                source=source,
            )

            return EarningsDateInfo(
                symbol=symbol,
                name=company_name,
                earnings_date=earnings_date,
                source=source,
            )

        except Exception as e:
            self.logger.warning(
                "Failed to fetch earnings date",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def _try_calendar(
        self,
        ticker: yf.Ticker,
        symbol: str,
    ) -> tuple[datetime | None, str]:
        """ticker.calendar から決算日を取得する.

        Parameters
        ----------
        ticker : yf.Ticker
            yfinance の Ticker オブジェクト
        symbol : str
            ティッカーシンボル

        Returns
        -------
        tuple[datetime | None, str]
            (決算日, ソース) のタプル。取得できない場合は (None, "")
        """
        try:
            # yfinance の calendar は dict | DataFrame | None を返す可能性がある
            # 型定義が不完全なため、明示的に型アノテーションを付与
            calendar: dict[str, Any] | DataFrame | None = ticker.calendar

            if calendar is None:  # pyright: ignore[reportUnnecessaryComparison]
                self.logger.debug("calendar is None", symbol=symbol)
                return None, ""

            # calendar は dict または DataFrame の場合がある（実行時チェック必須）
            earnings_date_raw: Any = None
            if isinstance(calendar, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
                earnings_date_raw = calendar.get("Earnings Date")
            elif isinstance(calendar, DataFrame):  # pyright: ignore[reportUnnecessaryIsInstance]
                if "Earnings Date" in calendar.columns:
                    earnings_date_raw = calendar["Earnings Date"].iloc[0]
                elif "Earnings Date" in calendar.index:
                    earnings_date_raw = calendar.loc["Earnings Date"].iloc[0]
                else:
                    self.logger.debug("No Earnings Date in calendar", symbol=symbol)
                    return None, ""
            else:
                self.logger.debug(
                    "Unexpected calendar type",
                    symbol=symbol,
                    calendar_type=type(calendar).__name__,
                )
                return None, ""

            if earnings_date_raw is None:
                return None, ""

            earnings_date = self._parse_datetime(earnings_date_raw)
            return earnings_date, "calendar"

        except KeyError as e:
            self.logger.debug(
                "KeyError in calendar",
                symbol=symbol,
                error=str(e),
            )
            return None, ""
        except Exception as e:
            self.logger.debug(
                "Error accessing calendar",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None, ""

    def _try_earnings_dates(
        self,
        ticker: yf.Ticker,
        symbol: str,
    ) -> tuple[datetime | None, str]:
        """get_earnings_dates() から決算日を取得する.

        Parameters
        ----------
        ticker : yf.Ticker
            yfinance の Ticker オブジェクト
        symbol : str
            ティッカーシンボル

        Returns
        -------
        tuple[datetime | None, str]
            (決算日, ソース) のタプル。取得できない場合は (None, "")
        """
        try:
            earnings_df = ticker.get_earnings_dates(limit=10)

            if earnings_df is None or earnings_df.empty:
                self.logger.debug("No earnings dates data", symbol=symbol)
                return None, ""

            # 将来の最も近い決算日を取得
            now = datetime.now(tz=timezone.utc)

            for idx in earnings_df.index:
                ts = pd.Timestamp(str(idx))
                if bool(pd.isna(ts)):
                    continue

                dt = self._parse_datetime(ts)
                if dt is None:
                    continue

                if dt > now:
                    return dt, "earnings_dates"

            self.logger.debug("No future earnings date found", symbol=symbol)
            return None, ""

        except Exception as e:
            self.logger.debug(
                "Error in get_earnings_dates",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None, ""

    def _parse_datetime(self, value: Any) -> datetime | None:
        """様々な形式の日付を datetime に変換する.

        Parameters
        ----------
        value : Any
            日付を表す値（datetime, Timestamp, str など）

        Returns
        -------
        datetime | None
            タイムゾーン付きの datetime。変換できない場合は None
        """
        if value is None:
            return None

        if pd.isna(value):
            return None

        try:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    return value.replace(tzinfo=timezone.utc)
                return value

            if isinstance(value, Timestamp):
                if value.tzinfo is None:
                    result = value.tz_localize(timezone.utc).to_pydatetime()
                else:
                    result = value.to_pydatetime()
                # NaT チェック（to_pydatetime() は NaTType を返す可能性あり）
                if not isinstance(result, datetime):  # pyright: ignore[reportUnnecessaryIsInstance]
                    return None
                return result

            # 文字列の場合
            ts = pd.Timestamp(str(value))
            if ts.tzinfo is None:
                result = ts.tz_localize(timezone.utc).to_pydatetime()
            else:
                result = ts.to_pydatetime()
            # NaT チェック
            if not isinstance(result, datetime):
                return None
            return result

        except Exception:
            return None

    def get_upcoming_earnings(
        self,
        symbols: list[str] | None = None,
        days_ahead: int = 14,
    ) -> list[EarningsDateInfo]:
        """複数銘柄の決算発表日を取得する.

        Parameters
        ----------
        symbols : list[str] | None, optional
            対象銘柄リスト。指定しない場合はデフォルト銘柄を使用
        days_ahead : int, default=14
            何日先までの決算を取得するか

        Returns
        -------
        list[EarningsDateInfo]
            決算発表日情報のリスト（日付順にソート済み）
        """
        if symbols is None:
            symbols = self.default_symbols

        self.logger.info(
            "Fetching upcoming earnings",
            symbol_count=len(symbols),
            days_ahead=days_ahead,
        )

        now = datetime.now(tz=timezone.utc)
        cutoff_date = now + timedelta(days=days_ahead)

        results: list[EarningsDateInfo] = []

        for symbol in symbols:
            earnings_info = self.get_earnings_date_for_symbol(symbol)

            if earnings_info is None:
                continue

            # 期間フィルタリング
            if now < earnings_info.earnings_date <= cutoff_date:
                results.append(earnings_info)
                self.logger.debug(
                    "Added upcoming earnings",
                    symbol=symbol,
                    earnings_date=earnings_info.earnings_date.isoformat(),
                )

        # 決算日で昇順ソート
        results.sort(key=lambda x: x.earnings_date)

        self.logger.info(
            "Upcoming earnings fetch completed",
            total_found=len(results),
            symbols_checked=len(symbols),
        )

        return results

    def to_dataframe(self, earnings_list: list[EarningsDateInfo]) -> DataFrame:
        """決算発表日情報をDataFrameに変換する.

        Parameters
        ----------
        earnings_list : list[EarningsDateInfo]
            決算発表日情報のリスト

        Returns
        -------
        DataFrame
            symbol, name, earnings_date, source カラムを持つDataFrame
        """
        if not earnings_list:
            return DataFrame(
                columns=pd.Index(["symbol", "name", "earnings_date", "source"]),
            )

        data = [info.to_dict() for info in earnings_list]
        return DataFrame(data)

    def to_json_output(
        self,
        earnings_list: list[EarningsDateInfo],
    ) -> dict[str, Any]:
        """JSON出力形式に変換する.

        Parameters
        ----------
        earnings_list : list[EarningsDateInfo]
            決算発表日情報のリスト

        Returns
        -------
        dict[str, Any]
            JSON シリアライズ可能な辞書
        """
        return {
            "upcoming_earnings": [info.to_dict() for info in earnings_list],
        }


# =============================================================================
# Convenience Function
# =============================================================================


def get_upcoming_earnings(
    symbols: list[str] | None = None,
    days_ahead: int = 14,
) -> dict[str, Any]:
    """S&P500時価総額上位20社の決算発表日を取得する.

    Parameters
    ----------
    symbols : list[str] | None, optional
        対象銘柄リスト。指定しない場合はTOP20を使用
    days_ahead : int, default=14
        何日先までの決算を取得するか

    Returns
    -------
    dict[str, Any]
        JSON シリアライズ可能な辞書

    Examples
    --------
    >>> result = get_upcoming_earnings(days_ahead=7)
    >>> for item in result["upcoming_earnings"]:
    ...     print(f"{item['symbol']}: {item['earnings_date']}")
    """
    logger.info(
        "Getting upcoming earnings",
        symbols=symbols,
        days_ahead=days_ahead,
    )

    analyzer = UpcomingEventsAnalyzer(symbols=symbols)
    earnings = analyzer.get_upcoming_earnings(days_ahead=days_ahead)

    return analyzer.to_json_output(earnings)


def get_upcoming_economic_releases(
    days_ahead: int = 14,
    releases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """主要経済指標の発表予定を取得する.

    FRED API を使用して、MAJOR_RELEASES に定義された経済指標の
    発表予定を取得する。

    Parameters
    ----------
    days_ahead : int, default=14
        何日先までの発表予定を取得するか
    releases : list[dict[str, Any]] | None, optional
        取得対象のリリース。指定しない場合は MAJOR_RELEASES を使用

    Returns
    -------
    dict[str, Any]
        JSON シリアライズ可能な辞書

    Examples
    --------
    >>> result = get_upcoming_economic_releases(days_ahead=7)
    >>> for item in result["upcoming_economic_releases"]:
    ...     print(f"{item['name_ja']}: {item['release_date']}")

    Notes
    -----
    FRED API キーは環境変数 FRED_API_KEY から取得する。
    API キーがない場合やエラー時は空リストを返す。
    """
    load_dotenv()
    api_key = os.environ.get(FRED_API_KEY_ENV)

    if not api_key:
        logger.warning(
            "FRED API key not found",
            env_var=FRED_API_KEY_ENV,
        )
        return {"upcoming_economic_releases": []}

    target_releases = releases if releases is not None else MAJOR_RELEASES

    logger.info(
        "Getting upcoming economic releases",
        days_ahead=days_ahead,
        release_count=len(target_releases),
    )

    now = datetime.now(tz=timezone.utc)
    cutoff_date = now + timedelta(days=days_ahead)

    # FRED API の日付形式
    realtime_start = now.strftime("%Y-%m-%d")
    realtime_end = cutoff_date.strftime("%Y-%m-%d")

    results: list[EconomicReleaseInfo] = []

    # 各リリースの発表予定を取得
    for release in target_releases:
        release_id = release["release_id"]

        try:
            url = f"{FRED_API_BASE_URL}/release/dates"
            params = {
                "release_id": release_id,
                "api_key": api_key,
                "file_type": "json",
                "realtime_start": realtime_start,
                "realtime_end": realtime_end,
                "include_release_dates_with_no_data": "true",
            }

            logger.debug(
                "Fetching release dates",
                release_id=release_id,
                release_name=release["name"],
            )

            response = httpx.get(url, params=params, timeout=10.0)
            response.raise_for_status()

            data = response.json()
            release_dates = data.get("release_dates", [])

            for rd in release_dates:
                date_str = rd.get("date")
                if not date_str:
                    continue

                release_date = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )

                # 期間フィルタリング（now < release_date <= cutoff）
                if not (now < release_date <= cutoff_date):
                    continue

                info = EconomicReleaseInfo(
                    release_id=release_id,
                    name=release["name"],
                    name_ja=release["name_ja"],
                    release_date=release_date,
                    importance=release["importance"],
                )
                results.append(info)

                logger.debug(
                    "Found release date",
                    release_id=release_id,
                    release_name=release["name"],
                    release_date=date_str,
                )

        except httpx.HTTPStatusError as e:
            logger.warning(
                "FRED API HTTP error",
                release_id=release_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            continue
        except httpx.RequestError as e:
            logger.warning(
                "FRED API request error",
                release_id=release_id,
                error=str(e),
            )
            continue
        except Exception as e:
            logger.warning(
                "Failed to fetch release dates",
                release_id=release_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            continue

    # 発表日で昇順ソート
    results.sort(key=lambda x: x.release_date)

    logger.info(
        "Economic releases fetch completed",
        total_found=len(results),
        releases_checked=len(target_releases),
    )

    return {
        "upcoming_economic_releases": [info.to_dict() for info in results],
    }


__all__ = [
    "MAJOR_RELEASES",
    "TOP20_SYMBOLS",
    "EarningsDateInfo",
    "EconomicReleaseInfo",
    "UpcomingEventsAnalyzer",
    "get_upcoming_earnings",
    "get_upcoming_economic_releases",
]
