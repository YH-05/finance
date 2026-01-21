from collections import defaultdict
from datetime import date, datetime, timedelta

import curl_cffi
from rich.console import Console
import yfinance as yf


console = Console()


class YfinanceNewsFetcher:
    """yfinanceからニュースを取得するクラス"""

    def __init__(self):
        self.today = date.today()
        self.session = curl_cffi.requests.Session(impersonate="safari15_5")

    def _convert_to_unix_timestamp(self, time_str: str):
        dt: datetime = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        timestamp = int(dt.timestamp())
        return timestamp

    def _news_filter(
        self,
        news_list: list[dict],
        after_timestamp: int | None = None,
        before_timestamp: int | None = None,
    ) -> list:
        for article in news_list:
            if isinstance(article.get("providerPublishTime", 0), str):
                article["providerPublishTime"] = self._convert_to_unix_timestamp(
                    article.get("providerPublishTime", 0)
                )

        if after_timestamp:
            news_list = [
                article
                for article in news_list
                if article.get("providerPublishTime", 0) >= after_timestamp
            ]
        if before_timestamp:
            news_list = [
                article
                for article in news_list
                if article.get("providerPublishTime", 0) <= before_timestamp
            ]

        # 時刻順に並べてtimestampをフォーマット
        news_list = sorted(
            news_list, key=lambda x: x["providerPublishTime"], reverse=True
        )
        for news in news_list:
            news["providerPublishTime"] = datetime.fromtimestamp(
                news["providerPublishTime"]
            ).strftime("%Y/%m/%d %H:%M")

        return news_list

    def _get_news_by_search(
        self,
        query: str,
        news_count: int = 15,
        after_timestamp: int | None = None,
        before_timestamp: int | None = None,
    ) -> list:
        """クエリに基づきニュースを取得する(Searchクラス使用)"""

        try:
            news_list: list[dict] = yf.Search(query, news_count=news_count).news
            news_list = [
                {
                    k: news[k]
                    for k in [
                        "title",  # タイトル
                        "publisher",  # ニュース元
                        "providerPublishTime",  # ニュース発表時刻
                        "relatedTickers",  # 関連するティッカー
                        "link",  # 記事URL
                    ]
                    if k in news
                }
                for news in news_list
            ]

            news_list = self._news_filter(
                news_list=news_list,
                after_timestamp=after_timestamp,
                before_timestamp=before_timestamp,
            )

            return news_list
        except Exception as e:
            print(f"Error: {e} ({type(e)})")
            return []

    def _get_news_by_ticker(
        self,
        ticker: str,
        count: int = 15,
        after_timestamp: int | None = None,
        before_timestamp: int | None = None,
    ) -> list:
        """クエリに基づきニュースを取得する(Tickerクラス使用)"""

        def _extract_news_fields(news_content: dict) -> dict:
            """ニュースから必要なフィールドを抽出"""
            return {
                "title": news_content.get("title"),
                "summary": news_content.get("summary"),
                "providerPublishTime": news_content.get("pubDate"),
                "publisher": news_content.get("provider", {}).get("displayName"),
                "link": news_content.get("canonicalUrl", {}).get("url"),
            }

        try:
            news_list: list[dict] = [
                s["content"] for s in yf.Ticker(ticker).get_news(count=count)
            ]
            news_list: list[dict] = [
                {
                    k: news[k]
                    for k in [
                        "title",  # タイトル
                        "summary",  # summary
                        "pubDate",  # ニュース発表時刻
                        "provider",  # ニュース配信元
                        "canonicalUrl",  # url
                    ]
                    if k in news
                }
                for news in news_list
            ]
            news_list: list[dict] = [_extract_news_fields(s) for s in news_list]

            news_list: list[dict] = self._news_filter(
                news_list=news_list,
                after_timestamp=after_timestamp,
                before_timestamp=before_timestamp,
            )

            return news_list
        except Exception as e:
            print(f"Error: {e} ({type(e)})")
            return []

    def get_news(
        self,
        query: str,
        news_count: int = 15,
        after_timestamp: int | None = None,
        before_timestamp: int | None = None,
    ) -> list:
        """クエリを指定してニュース取得"""
        return self._get_news_by_search(
            query=query,
            after_timestamp=after_timestamp,
            before_timestamp=before_timestamp,
        )

    def get_us_market_news(
        self,
        query="US Market",
        news_count: int = 15,
        after_timestamp: int | None = None,
        before_timestamp: int | None = None,
    ) -> list:
        """US株式市場のニュース取得"""
        return self._get_news_by_search(
            query=query,
            after_timestamp=after_timestamp,
            before_timestamp=before_timestamp,
        )

    def get_stock_news(
        self,
        ticker,
        count: int = 15,
        after_timestamp: int | None = None,
        before_timestamp: int | None = None,
    ) -> list:
        """個別銘柄のニュース取得"""

        return self._get_news_by_ticker(
            ticker=ticker,
            count=count,
            after_timestamp=after_timestamp,
            before_timestamp=before_timestamp,
        )

    def get_multiple_stock_news(
        self,
        ticker_list: list[str],
        count: int = 15,
        after_timestamp: int | None = None,
        before_timestamp: int | None = None,
    ) -> list:
        """複数の個別銘柄のニュースを一括取得"""

        news_list = []

        for ticker in ticker_list:
            news = self._get_news_by_ticker(
                ticker=ticker,
                count=count,
                after_timestamp=after_timestamp,
                before_timestamp=before_timestamp,
            )
            news = [{"ticker": [ticker], **n} for n in news]
            news_list.extend(news)

        # title, summary, providerPublishTime, publisher, linkが重複している辞書をまとめる
        # tickerは配列にまとめなおす
        # ex) ["MSFT"] -> ["MSFT", "META"]
        news_dict = {}
        for news in news_list:
            key = (
                news["title"],
                news["summary"],
                news["providerPublishTime"],
                news["publisher"],
                news["link"],
            )
            if key in news_dict:
                # すでに存在する場合、tickerを追加
                news_dict[key]["ticker"].extend(news["ticker"])
            else:
                # 新規の場合、そのまま追加
                news_dict[key] = news.copy()
        news_list = list(news_dict.values())
        for news in news_list:
            news["ticker"] = sorted(set(news["ticker"]))

        return news_list


def main():
    news_fetcher = YfinanceNewsFetcher()
    news_list = news_fetcher.get_stock_news("NVDA")
    console.print(news_list)


if __name__ == "__main__":
    main()
