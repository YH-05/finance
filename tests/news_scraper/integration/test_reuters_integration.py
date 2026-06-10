"""reuters.py の統合テスト.

対象モジュール: src/news_scraper/reuters.py（mode A）

ネットワークアクセスはモックで置き換える（実ネットワークアクセスは行わない）。
- collect_reuters_news: curl_cffi の session.get をモックし、index XML + サブ XML
  フィクスチャを返す → 期待件数・列・無フィルタ全件を検証
- save_reuters_news: tmp_path で parquet round-trip
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from news_scraper.types import ScraperConfig

if TYPE_CHECKING:
    from pathlib import Path

# サイトマップインデックス XML（サブサイトマップ 1 件のみ）
INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://www.reuters.com/arc/outboundfeeds/news-sitemap/?outputType=xml</loc>
    <lastmod>2026-06-10T12:00:00Z</lastmod>
  </sitemap>
</sitemapindex>
"""

# サブサイトマップ XML（英語2件 + スペイン語1件 = 全3件、言語混在）
SUB_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  <url>
    <loc>https://www.reuters.com/business/energy/apple-2026-06-10/</loc>
    <lastmod>2026-06-10T12:00:00Z</lastmod>
    <news:news>
      <news:publication>
        <news:name>Reuters</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>2026-06-10T11:30:00Z</news:publication_date>
      <news:title>Apple earnings</news:title>
      <news:keywords>USN/AAPL</news:keywords>
      <news:stock_tickers>AAPL.O</news:stock_tickers>
    </news:news>
  </url>
  <url>
    <loc>https://www.reuters.com/world/us/congress-2026-06-10/</loc>
    <lastmod>2026-06-10T10:00:00Z</lastmod>
    <news:news>
      <news:publication>
        <news:name>Reuters</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>2026-06-10T09:45:00Z</news:publication_date>
      <news:title>Congress budget</news:title>
    </news:news>
  </url>
  <url>
    <loc>https://www.reuters.com/es/mercados/peso-2026-06-10/</loc>
    <lastmod>2026-06-10T08:00:00Z</lastmod>
    <news:news>
      <news:publication>
        <news:name>Reuters</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>2026-06-10T07:30:00Z</news:publication_date>
      <news:title>El peso mexicano</news:title>
      <news:stock_tickers>MXN=</news:stock_tickers>
    </news:news>
  </url>
</urlset>
"""


def _make_mock_session() -> MagicMock:
    """index XML → サブ XML の順で text を返すモックセッションを作る."""
    mock_session = MagicMock()

    def _get(url: str, *args: object, **kwargs: object) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 200
        if "news-sitemap-index" in url:
            resp.text = INDEX_XML
        else:
            resp.text = SUB_XML
        return resp

    mock_session.get.side_effect = _get
    return mock_session


@pytest.mark.integration
class TestCollectReutersNews:
    """collect_reuters_news() の統合テスト."""

    def test_正常系_index経由でサブXMLを収集し全件返す(self) -> None:
        """index → サブ XML を辿り、無フィルタで全 3 件を返すことを確認。"""
        from news_scraper.reuters import collect_reuters_news

        config = ScraperConfig(delay=0.0, jitter=0.0)

        with (
            patch(
                "news_scraper.reuters.create_session",
                return_value=_make_mock_session(),
            ),
            patch("news_scraper.reuters.time.sleep"),
        ):
            df = collect_reuters_news(config=config, pages=1)

        # 無フィルタ全件（英語2 + スペイン語1）
        assert len(df) == 3

    def test_正常系_言語列が全件に付与される(self) -> None:
        """language/section/subsection 列が全件に付与されることを確認。"""
        from news_scraper.reuters import collect_reuters_news

        config = ScraperConfig(delay=0.0, jitter=0.0)

        with (
            patch(
                "news_scraper.reuters.create_session",
                return_value=_make_mock_session(),
            ),
            patch("news_scraper.reuters.time.sleep"),
        ):
            df = collect_reuters_news(config=config, pages=1)

        for col in ("language", "section", "subsection"):
            assert col in df.columns

        # スペイン語記事も収集されている（無フィルタ全件保存）
        assert "es" in set(df["language"])
        assert "en" in set(df["language"])

    def test_正常系_出力列がArticle11列プラス言語系3列(self) -> None:
        """出力列が Article 11 列 + language/section/subsection の計 14 列であることを確認。"""
        from news_scraper.reuters import collect_reuters_news

        config = ScraperConfig(delay=0.0, jitter=0.0)

        with (
            patch(
                "news_scraper.reuters.create_session",
                return_value=_make_mock_session(),
            ),
            patch("news_scraper.reuters.time.sleep"),
        ):
            df = collect_reuters_news(config=config, pages=1)

        expected = {
            "title",
            "url",
            "published",
            "summary",
            "category",
            "source",
            "content",
            "ticker",
            "author",
            "article_id",
            "metadata",
            "language",
            "section",
            "subsection",
        }
        assert set(df.columns) == expected

    def test_正常系_米株RICはNASDAQティッカーになる(self) -> None:
        """AAPL.O が ticker=AAPL に変換され、MXN= は ticker なしになることを確認。"""
        from news_scraper.reuters import collect_reuters_news

        config = ScraperConfig(delay=0.0, jitter=0.0)

        with (
            patch(
                "news_scraper.reuters.create_session",
                return_value=_make_mock_session(),
            ),
            patch("news_scraper.reuters.time.sleep"),
        ):
            df = collect_reuters_news(config=config, pages=1)

        apple = df[df["url"].str.contains("apple")].iloc[0]
        assert apple["ticker"] == "AAPL"

        peso = df[df["url"].str.contains("peso")].iloc[0]
        assert peso["ticker"] == ""  # MXN= は nonus（米株でない）

    def test_正常系_重複locは排除される(self) -> None:
        """同一 loc が複数回現れても重複排除されることを確認。"""
        from news_scraper.reuters import collect_reuters_news

        # index が同じサブ URL を2回返す（サブ XML は同一内容 = loc 重複）
        index_xml_dup = INDEX_XML.replace(
            "</sitemapindex>",
            "  <sitemap>\n"
            "    <loc>https://www.reuters.com/arc/outboundfeeds/news-sitemap/?outputType=xml&amp;from=50</loc>\n"
            "  </sitemap>\n"
            "</sitemapindex>",
        )

        mock_session = MagicMock()

        def _get(url: str, *args: object, **kwargs: object) -> MagicMock:
            resp = MagicMock()
            resp.status_code = 200
            resp.text = index_xml_dup if "news-sitemap-index" in url else SUB_XML
            return resp

        mock_session.get.side_effect = _get

        config = ScraperConfig(delay=0.0, jitter=0.0)
        with (
            patch("news_scraper.reuters.create_session", return_value=mock_session),
            patch("news_scraper.reuters.time.sleep"),
        ):
            df = collect_reuters_news(config=config, pages=2)

        # 2 サブを辿るが loc は重複するため 3 件のまま
        assert len(df) == 3

    def test_エッジケース_index取得失敗で空DataFrame(self) -> None:
        """index XML が非200のとき空 DataFrame を返すことを確認。"""
        from news_scraper.reuters import collect_reuters_news

        mock_session = MagicMock()
        resp = MagicMock()
        resp.status_code = 403
        resp.text = "blocked"
        mock_session.get.return_value = resp

        config = ScraperConfig(delay=0.0, jitter=0.0)
        with (
            patch("news_scraper.reuters.create_session", return_value=mock_session),
            patch("news_scraper.reuters.time.sleep"),
        ):
            df = collect_reuters_news(config=config, pages=1)

        assert df.empty


# NASDAQ 公式ディレクトリのサンプル（パイプ区切り）
NASDAQ_LISTED_TXT = (
    "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size\n"
    "AAPL|Apple Inc. - Common Stock|Q|N|N|100\n"
    "File Creation Time: 0610202612:00|||||\n"
)
OTHER_LISTED_TXT = (
    "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\n"
    "BA|Boeing Company|N|BA|N|100|N|BA\n"
    "File Creation Time: 0610202612:00|||||||\n"
)


@pytest.mark.integration
class TestNasdaqDirectoryValidation:
    """load_nasdaq_directory → validate_nasdaq_tickers の統合（照合ラウンドトリップ）."""

    def test_正常系_ディレクトリ取得から照合まで(self) -> None:
        """ディレクトリ集合を取得し、収集 df の rics_nasdaq を matched/unmatched 付与する。"""
        from news_scraper.reuters import (
            load_nasdaq_directory,
            validate_nasdaq_tickers,
        )

        mock_session = MagicMock()

        def _get(url: str, *args: object, **kwargs: object) -> MagicMock:
            resp = MagicMock()
            resp.status_code = 200
            resp.headers = {}
            if "nasdaqlisted" in url:
                resp.text = NASDAQ_LISTED_TXT
            else:
                resp.text = OTHER_LISTED_TXT
            return resp

        mock_session.get.side_effect = _get

        with patch("news_scraper.reuters.time.sleep"):
            directory = load_nasdaq_directory(mock_session)

        assert {"AAPL", "BA"} <= directory

        df = pd.DataFrame(
            [
                {"metadata": {"rics_nasdaq": ["AAPL", "DELISTED"]}},
                {"metadata": {"rics_nasdaq": ["BA"]}},
            ]
        )

        result = validate_nasdaq_tickers(df, directory)

        assert result.iloc[0]["nasdaq_matched"] == ["AAPL"]
        assert result.iloc[0]["nasdaq_unmatched"] == ["DELISTED"]
        assert result.iloc[1]["nasdaq_matched"] == ["BA"]


@pytest.mark.integration
class TestSaveReutersNews:
    """save_reuters_news() の統合テスト."""

    def test_正常系_parquetラウンドトリップ(self, tmp_path: Path) -> None:
        """保存した parquet を読み戻して内容が一致することを確認。"""
        from news_scraper.reuters import save_reuters_news

        df = pd.DataFrame(
            [
                {
                    "title": "Apple earnings",
                    "url": "https://www.reuters.com/business/energy/apple/",
                    "published": "2026-06-10T11:30:00Z",
                    "summary": "",
                    "category": "business/energy",
                    "source": "reuters",
                    "content": "",
                    "ticker": "AAPL",
                    "author": "",
                    "article_id": "https://www.reuters.com/business/energy/apple/",
                    "metadata": {"section": "business", "rics_nasdaq": ["AAPL"]},
                    "language": "en",
                    "section": "business",
                    "subsection": "business/energy",
                }
            ]
        )

        path = save_reuters_news(df, base_dir=tmp_path)

        assert path.exists()
        assert path.suffix == ".parquet"

        loaded = pd.read_parquet(path)
        assert len(loaded) == 1
        assert loaded.iloc[0]["ticker"] == "AAPL"
        assert loaded.iloc[0]["source"] == "reuters"

    def test_正常系_日付ディレクトリが生成される(self, tmp_path: Path) -> None:
        """{base_dir}/{YYYY-MM-DD}/ のディレクトリ階層が作られることを確認。"""
        from news_scraper.reuters import save_reuters_news

        df = pd.DataFrame(
            [
                {
                    "title": "x",
                    "url": "https://www.reuters.com/x/",
                    "published": "2026-06-10T11:30:00Z",
                    "summary": "",
                    "category": "business",
                    "source": "reuters",
                    "content": "",
                    "ticker": "",
                    "author": "",
                    "article_id": "https://www.reuters.com/x/",
                    "metadata": {},
                    "language": "en",
                    "section": "business",
                    "subsection": "",
                }
            ]
        )

        path = save_reuters_news(df, base_dir=tmp_path)

        # base_dir/{YYYY-MM-DD}/reuters_{ts}.parquet
        assert path.parent.parent == tmp_path
        assert path.name.startswith("reuters_")
