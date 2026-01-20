import datetime

from rich.console import Console

from src.market_report import analysis, news


def get_mag_seven_sox_news() -> list[dict]:
    """直近1週間のマグニフィセント7銘柄とSOX Indexのニュースを取得する"""
    news_fetcher = news.YfinanceNewsFetcher()
    mag_seven_sox_ticker = [
        "NVDA",
        "AAPL",
        "GOOGL",
        "MSFT",
        "TSLA",
        "AMZN",
        "META",
        "^SOX",
    ]
    news_list = news_fetcher.get_multiple_stock_news(
        ticker_list=mag_seven_sox_ticker,
        count=50,
        after_timestamp=int(
            (datetime.datetime.now() - datetime.timedelta(days=7)).timestamp()
        ),
    )
    return news_list


def main():
    sector_analyzer = analysis.SectorAnalyzer()
    top_and_bottom = sector_analyzer.get_top_bottom_sectors()
    top_and_bottom_sectors: list[str] = [
        sector for sector, performance in top_and_bottom.items()
    ]

    console = Console()
    console.print(top_and_bottom)

    after_timestamp = int(
        (datetime.datetime.now() - datetime.timedelta(days=7)).timestamp()
    )

    news_fetcher = news.YfinanceNewsFetcher()

    sector_news: dict = news_fetcher.get_news(
        top_and_bottom_sectors[-1], news_count=300, after_timestamp=after_timestamp
    )  # ty:ignore[invalid-assignment]

    print(len(sector_news))
    console.print(sector_news)


if __name__ == "__main__":
    main()
