from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import logging

import curl_cffi
import pandas as pd
from pandas import DataFrame
from rich.console import Console
import yfinance as yf

from src.market_report import analysis


def get_multiple_earnings_dates(symbol_list: list[str], limit: int = 12) -> DataFrame:
    """複数銘柄のearnings datesを取得する"""
    logger = logging.getLogger(__name__)
    earnings_dates = []
    session = curl_cffi.requests.Session(impersonate="safari15_5")

    for symbol in symbol_list:
        try:
            ticker = yf.Ticker(symbol, session=session)
            _df: DataFrame = ticker.get_earnings_dates(limit=limit)

            # Noneチェック
            if _df is None:
                logger.warning(f"{symbol}: データがNoneです")
                continue

            # 空チェック
            if _df.empty:
                logger.info(f"{symbol}: データが空です")
                continue

            # データ処理
            earnings_dates.append(_df.reset_index().assign(symbol=symbol))

        except AttributeError as e:
            logger.error(f"{symbol}: get_earnings_dates()メソッドエラー - {e}")
            continue

        except KeyError as e:
            logger.debug(f"{symbol}: カラムエラー - {e}")
            continue

        except Exception as e:
            logger.error(f"{symbol}: 予期しないエラー - {type(e).__name__}: {e}")
            continue

    if not earnings_dates:
        logger.warning("全銘柄でデータ取得に失敗しました")
        return pd.DataFrame()
    df_earnings_dates = pd.concat(earnings_dates, ignore_index=True)
    return df_earnings_dates


def filter_upcoming_earnings_dates(
    df_earnings_dates: DataFrame, date_range: int
) -> DataFrame:
    """複数銘柄の今後のearnings datesを取得する"""
    # date_range以内の決算発表をフィルタリングする
    # future_date = datetime.now() + timedelta(days=date_range)
    future_date = pd.Timestamp.now(tz="America/New_York") + pd.Timedelta(
        days=date_range
    )
    upcoming_earings_dates = df_earnings_dates.loc[
        (df_earnings_dates["Earnings Date"] <= future_date)
        & (
            df_earnings_dates["Earnings Date"]
            >= pd.Timestamp.now(tz="America/New_York")
        )
    ]
    if upcoming_earings_dates.empty:
        upcoming_earings_dates = pd.DataFrame(
            columns=upcoming_earings_dates.columns.tolist()
        )

    return upcoming_earings_dates


def get_upcoming_earnings_dates(
    symbol_list: list[str], date_range: int, limit: int = 12
) -> DataFrame:
    """複数銘柄の今後のearnings datesを取得する"""
    all_earnings_dates = get_multiple_earnings_dates(symbol_list, limit=limit)

    # date_range以内の決算発表をフィルタリングする
    # future_date = datetime.now() + timedelta(days=date_range)
    future_date = pd.Timestamp.now(tz="America/New_York") + pd.Timedelta(
        days=date_range
    )

    upcoming_earings_dates = all_earnings_dates.loc[
        (all_earnings_dates["Earnings Date"] <= future_date)
        & (
            all_earnings_dates["Earnings Date"]
            >= pd.Timestamp.now(tz="America/New_York")
        )
    ]
    if upcoming_earings_dates.empty():
        upcoming_earings_dates = pd.DataFrame(
            columns=upcoming_earings_dates.columns.tolist()
        )

    return upcoming_earings_dates


def get_upcoming_earnings_dates_of_top_companies():
    """今後1週間の決算予定企業を取得する(yfinanceの独自定義セクターのtop companiesが対象)"""
    top_companies_analyzer = analysis.TopCompaniesAnalyzer()
    top_companies = top_companies_analyzer.get_all_sectors_top_companies()

    upcoming_earnings_dates = []
    for sector in top_companies["Sector"].unique().tolist():
        sector_top_companies = top_companies.loc[
            top_companies["Sector"] == sector
        ].index.tolist()

        logger.info(f"Sector: {sector}")
        logger.info(f"Top Companies: {sector_top_companies}")

        sector_upcoming_earnings_dates = get_upcoming_earnings_dates(
            symbol_list=sector_top_companies, date_range=7
        )
        sector_upcoming_earnings_dates["Sector"] = sector
        console.print(f"[yellow bold]{sector}[/yellow bold]")
        console.print(sector_upcoming_earnings_dates)
        upcoming_earnings_dates.append(sector_upcoming_earnings_dates)

    upcoming_earnings_dates = pd.concat(upcoming_earnings_dates, ignore_index=True)

    return upcoming_earnings_dates


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    top_companies_analyzer = analysis.TopCompaniesAnalyzer()
    top_companies = top_companies_analyzer.get_all_sectors_top_companies()

    sectors = top_companies["Sector"].unique().tolist()

    def process_sector(sector: str) -> DataFrame:
        """セクターごとの処理"""
        sector_top_companies = top_companies.loc[
            top_companies["Sector"] == sector
        ].index.tolist()

        logger.info(f"Sector: {sector} - 処理開始")

        earnings_dates = get_multiple_earnings_dates(symbol_list=sector_top_companies)
        earnings_dates["Sector"] = sector

        logger.info(f"Sector: {sector} - 完了 ({len(earnings_dates)}件)")

        return earnings_dates

    # 並列処理
    upcoming_earnings_dates = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        # 全セクターを並列実行
        futures = {
            executor.submit(process_sector, sector): sector for sector in sectors
        }

        # 完了したものから結果を取得
        for future in as_completed(futures):
            sector = futures[future]
            try:
                result = future.result()
                upcoming_earnings_dates.append(result)
            except Exception as e:
                logger.error(f"Sector: {sector} - エラー: {e}")

    df_earnings_dates = pd.concat(upcoming_earnings_dates, ignore_index=True)
    df_upcoming_earnings_dates = filter_upcoming_earnings_dates(
        df_earnings_dates=df_earnings_dates, date_range=7
    )

    # for sector in top_companies["Sector"].unique().tolist():
    #     sector_top_companies = top_companies.loc[
    #         top_companies["Sector"] == sector
    #     ].index.tolist()

    #     logger.info(f"Sector: {sector}")
    #     logger.info(f"Top Companies: {sector_top_companies}")

    #     earnings_dates = get_multiple_earnings_dates(symbol_list=sector_top_companies)
    #     earnings_dates["Sector"] = sector
    #     upcoming_earnings_dates.append(earnings_dates)

    # df_upcoming_earnings_dates = pd.concat(upcoming_earnings_dates, ignore_index=True)

    return df_upcoming_earnings_dates


if __name__ == "__main__":
    console = Console()
    console.print(main())
