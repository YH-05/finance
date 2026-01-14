"""
calendar_utils.py

マクロ経済指標と企業決算の予定日を取得するユーティリティモジュール。
"""

import datetime
import os

# srcディレクトリの親ディレクトリ(Quants)へのパスを解決してインポートできるようにする
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from fredapi import Fred

sys.path.append(str(Path(__file__).parent.parent))

from src.fred_database_utils import FredDataProcessor


class MacroCalendar:
    """
    FRED APIを使用して、主要なマクロ経済指標の発表予定を取得するクラス。
    """

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("FRED_API_KEY")
        self.fred = Fred(api_key=self.api_key)
        self.fred_processor = FredDataProcessor()

        # 監視対象の主要シリーズID
        self.target_series = {
            "CPIAUCSL": "CPI (Consumer Price Index)",
            "PCEPI": "PCE Price Index",
            "PAYEMS": "Nonfarm Payrolls",
            "UNRATE": "Unemployment Rate",
            "GDP": "GDP",
            "FEDFUNDS": "FOMC / Fed Funds Rate",
        }

    def get_upcoming_releases(self, days: int = 14) -> List[Dict]:
        """
        向こう指定日数間の主要指標発表予定を取得する。

        Parameters
        ----------
        days : int
            取得する期間（日数）。デフォルトは14日。

        Returns
        -------
        List[Dict]
            発表予定のリスト。各要素は {"date": str, "series_id": str, "name": str} の辞書。
        """
        upcoming_releases = []
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=days)

        # 注: fredapiには直接リリース予定を取得する便利なメソッドが少ないため、
        # get_series_release_dates を使用して、各シリーズのリリース日を確認する。
        # ただし、これは過去のリリース日も含むため、未来の日付でフィルタリングする必要がある。
        # また、FREDのリリーススケジュールはAPI経由だと直近のものしか取れない場合がある。

        for series_id, name in self.target_series.items():
            try:
                # リリースIDを取得（シリーズIDからリリースIDを特定するのは少し複雑だが、
                # ここでは簡易的にget_series_release_datesを試みる）
                # get_series_release_datesは通常、過去のデータを返す。
                # 未来のデータが取れるかはシリーズによる。

                # 多くのケースでFRED APIのget_release_datesは既知のリリース日を返す。
                # 未来の日付が含まれているか確認。

                # 1. シリーズに関連するリリース情報を取得
                releases = self.fred.get_series_release_dates(series_id)

                if releases is not None and not releases.empty:
                    # 未来の日付をフィルタリング
                    future_releases = releases[releases >= pd.Timestamp(today)]
                    future_releases = future_releases[
                        future_releases <= pd.Timestamp(end_date)
                    ]

                    for date in future_releases:
                        upcoming_releases.append(
                            {
                                "date": date.strftime("%Y-%m-%d"),
                                "series_id": series_id,
                                "name": name,
                            }
                        )

            except Exception as e:
                print(f"Warning: Failed to fetch release dates for {series_id}: {e}")
                continue

        # 日付順にソート
        upcoming_releases.sort(key=lambda x: x["date"])
        return upcoming_releases


class EarningsCalendar:
    """
    yfinanceを使用して、企業決算発表予定を取得するクラス。
    """

    def __init__(self):
        self.data_dir = (
            Path(os.environ.get("FRED_DIR", ".")).parent / "MSCI_KOKUSAI"
        )  # Quants/data/MSCI_KOKUSAI

    def _get_universe_tickers(self) -> List[str]:
        """
        MSCI KOKUSAI構成銘柄リスト（最新のParquetファイル）からティッカーを取得する。
        """
        try:
            # ファイル名パターンに一致する最新のファイルを探す
            files = list(
                self.data_dir.glob(
                    "MSCI_KOKUSAI_Constituents_with_Factset_Symbols_*.parquet"
                )
            )
            if not files:
                print("Warning: No universe file found.")
                return []

            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            df = pd.read_parquet(latest_file)

            # 'Ticker'カラムがあると想定
            if "Ticker" in df.columns:
                return df["Ticker"].tolist()
            elif "Symbol" in df.columns:
                return df["Symbol"].tolist()
            else:
                print("Warning: Ticker column not found in universe file.")
                return []

        except Exception as e:
            print(f"Warning: Failed to load universe tickers: {e}")
            return []

    def get_upcoming_earnings(
        self, tickers: Optional[List[str]] = None, days: int = 14
    ) -> List[Dict]:
        """
        指定されたティッカー、またはユニバース全体の決算発表予定を取得する。

        Parameters
        ----------
        tickers : List[str], optional
            チェック対象のティッカーリスト。Noneの場合はユニバース全体を対象とする。
        days : int
            取得する期間（日数）。デフォルトは14日。

        Returns
        -------
        List[Dict]
            決算発表予定のリスト。
        """
        if tickers is None:
            tickers = self._get_universe_tickers()

        earnings_events = []

        # 基準日設定 (タイムゾーンなしで扱う)
        now = pd.Timestamp.now().normalize()
        end_date = now + pd.Timedelta(days=days)
        start_date = now - pd.Timedelta(days=7)  # 過去7日間も振り返り用に取得

        print(f"Checking earnings for {len(tickers)} tickers...")

        count = 0
        for ticker in tickers:
            if len(tickers) > 100 and count % 50 == 0:
                print(f"Processed {count}/{len(tickers)}...")
            count += 1

            try:
                t = yf.Ticker(ticker)

                # get_earnings_dates() は将来と過去の決算日を含むDataFrameを返す
                # Indexは 'Earnings Date' (datetime64[ns, America/New_York] 等)
                dates_df = t.get_earnings_dates()

                if dates_df is not None and not dates_df.empty:
                    # タイムゾーンを削除して比較しやすくする
                    # indexがDatetimeIndexであることを確認
                    if isinstance(dates_df.index, pd.DatetimeIndex):
                        # tz_localize(None) でナイーブなdatetimeにする
                        dates_df.index = dates_df.index.tz_localize(None)

                        # 期間でフィルタリング
                        mask = (dates_df.index >= start_date) & (
                            dates_df.index <= end_date
                        )
                        filtered_df = dates_df.loc[mask]

                        for date_idx, row in filtered_df.iterrows():
                            # date_idx は Timestamp
                            d = date_idx.date()

                            # ステータス判定
                            status = "Upcoming" if d >= now.date() else "Recent"

                            # EPS予想などがあれば取得
                            eps_est = row.get("EPS Estimate", None)
                            if pd.isna(eps_est):
                                eps_est = None

                            earnings_events.append(
                                {
                                    "date": d.strftime("%Y-%m-%d"),
                                    "ticker": ticker,
                                    "name": ticker,
                                    "status": status,
                                    "eps_estimate": eps_est,
                                }
                            )

            except Exception:
                continue

        # 日付順にソート
        earnings_events.sort(key=lambda x: x["date"])
        return earnings_events


if __name__ == "__main__":
    # テスト実行
    print("--- Macro Calendar Test ---")
    macro = MacroCalendar()
    print(macro.get_upcoming_releases())

    print("\n--- Earnings Calendar Test (Mag7 Only) ---")
    earnings = EarningsCalendar()
    mag7 = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
    print(earnings.get_upcoming_earnings(tickers=mag7))
