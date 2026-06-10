"""reuters.py の単体テスト.

対象モジュール: src/news_scraper/reuters.py（mode A: サイトマップ・メタデータ収集）

t-wada 流 TDD（Red→Green→Refactor）で作成。純関数（convert_rics /
parse_sitemap_xml / entry_to_article / filter_articles）を中心に検証する。
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# --- サンプル XML フィクスチャ ---

# サブサイトマップ XML（stock_tickers あり/なし、英語/スペイン語記事を含む）
SAMPLE_SUB_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  <url>
    <loc>https://www.reuters.com/business/energy/apple-earnings-beat-2026-06-10/</loc>
    <lastmod>2026-06-10T12:00:00Z</lastmod>
    <news:news>
      <news:publication>
        <news:name>Reuters</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>2026-06-10T11:30:00Z</news:publication_date>
      <news:title>Apple earnings beat expectations</news:title>
      <news:keywords>USN/AAPL, GUID/123</news:keywords>
      <news:stock_tickers>AAPL.O, .SPX</news:stock_tickers>
    </news:news>
  </url>
  <url>
    <loc>https://www.reuters.com/world/us/congress-debate-2026-06-10/</loc>
    <lastmod>2026-06-10T10:00:00Z</lastmod>
    <news:news>
      <news:publication>
        <news:name>Reuters</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>2026-06-10T09:45:00Z</news:publication_date>
      <news:title>Congress debates new budget</news:title>
      <news:keywords>GUID/456</news:keywords>
    </news:news>
  </url>
  <url>
    <loc>https://www.reuters.com/es/mercados/peso-mexicano-2026-06-10/</loc>
    <lastmod>2026-06-10T08:00:00Z</lastmod>
    <news:news>
      <news:publication>
        <news:name>Reuters</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>2026-06-10T07:30:00Z</news:publication_date>
      <news:title>El peso mexicano sube</news:title>
      <news:keywords>USN/MXN</news:keywords>
      <news:stock_tickers>MXN=</news:stock_tickers>
    </news:news>
  </url>
</urlset>
"""

# サイトマップインデックス XML（サブサイトマップ URL を列挙）
SAMPLE_SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://www.reuters.com/arc/outboundfeeds/news-sitemap/?outputType=xml</loc>
    <lastmod>2026-06-10T12:00:00Z</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://www.reuters.com/arc/outboundfeeds/news-sitemap/?outputType=xml&amp;from=50</loc>
    <lastmod>2026-06-10T11:00:00Z</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://www.reuters.com/arc/outboundfeeds/news-sitemap/?outputType=xml&amp;from=100</loc>
    <lastmod>2026-06-10T10:00:00Z</lastmod>
  </sitemap>
</sitemapindex>
"""


class TestConvertRics:
    """convert_rics() のテスト（§5 RIC→NASDAQ 変換ルール）."""

    def test_正常系_NASDAQ米株RICをサフィックス除去する(self) -> None:
        """AAPL.O → NASDAQ ティッカー AAPL になることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["AAPL.O"])

        assert conv.nasdaq == ["AAPL"]
        assert conv.nonus == []
        assert conv.dropped == []
        assert conv.exchanges == ["NASDAQ"]

    def test_正常系_NYSE米株RICをサフィックス除去する(self) -> None:
        """BA.N → NASDAQ ティッカー BA・上場市場 NYSE になることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["BA.N"])

        assert conv.nasdaq == ["BA"]
        assert conv.exchanges == ["NYSE"]

    def test_正常系_クラス株は末尾小文字をドット表記に変換する(self) -> None:
        """BFb.N → BF.B にクラス株変換されることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["BFb.N"])

        assert conv.nasdaq == ["BF.B"]
        assert conv.exchanges == ["NYSE"]

    def test_正常系_指数RICはnonusに分類される(self) -> None:
        """.SPX（先頭ドット=指数）は nonus に退避されることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics([".SPX"])

        assert conv.nonus == [".SPX"]
        assert conv.nasdaq == []

    def test_正常系_FXRICはnonusに分類される(self) -> None:
        """EUR=（末尾イコール=FX）は nonus に退避されることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["EUR="])

        assert conv.nonus == ["EUR="]
        assert conv.nasdaq == []

    def test_正常系_先物RICはnonusに分類される(self) -> None:
        """CLc1（末尾 cN=連続先物）は nonus に退避されることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["CLc1"])

        assert conv.nonus == ["CLc1"]
        assert conv.nasdaq == []

    def test_正常系_国際株RICはnonusに分類される(self) -> None:
        """7203.T（その他サフィックス=国際株）は nonus に退避されることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["7203.T"])

        assert conv.nonus == ["7203.T"]
        assert conv.nasdaq == []

    def test_正常系_UL接尾辞はdroppedに分類される(self) -> None:
        """XXX.UL（Reuters 非上場）は dropped に分類されることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["XXX.UL"])

        assert conv.dropped == ["XXX.UL"]
        assert conv.nasdaq == []
        assert conv.nonus == []

    def test_正常系_混在RICを正しく分類する(self) -> None:
        """米株/指数/FX/先物/国際株/破棄の混在で各分類が正しいことを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(
            ["AAPL.O", "BFb.N", ".SPX", "EUR=", "CLc1", "7203.T", "XXX.UL"]
        )

        assert conv.nasdaq == ["AAPL", "BF.B"]
        assert conv.exchanges == ["NASDAQ", "NYSE"]
        assert conv.nonus == [".SPX", "EUR=", "CLc1", "7203.T"]
        assert conv.dropped == ["XXX.UL"]

    def test_エッジケース_空リストで空の結果(self) -> None:
        """空の RIC リストですべての分類が空になることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics([])

        assert conv.nasdaq == []
        assert conv.exchanges == []
        assert conv.nonus == []
        assert conv.dropped == []
        assert conv.preferred == []

    def test_正常系_米国優先株RICはpreferredに分類される(self) -> None:
        """AAM_pa.N（米国優先株）が preferred に best-effort 変換されることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["AAM_pa.N"])

        # best-effort・近似: root AAM_pa → base AAM + series A → AAM.A（ドット表記）
        assert conv.preferred == ["AAM.A"]
        # 普通株（nasdaq）にも exchanges にも入れない
        assert conv.nasdaq == []
        assert conv.exchanges == []
        assert conv.nonus == []
        assert conv.dropped == []

    def test_正常系_優先株は普通株tickerに混入しない(self) -> None:
        """優先株 RIC が普通株 RIC と混在しても nasdaq には普通株のみ残ることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["AAPL.O", "AAM_pa.N"])

        assert conv.nasdaq == ["AAPL"]
        assert conv.exchanges == ["NASDAQ"]
        assert conv.preferred == ["AAM.A"]

    def test_正常系_優先株シリーズ複数を区別する(self) -> None:
        """_pa / _pb の異なるシリーズがそれぞれ .A / .B になることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["AAM_pa.N", "AAM_pb.N"])

        assert conv.preferred == ["AAM.A", "AAM.B"]
        assert conv.nasdaq == []

    def test_正常系_クラス株は優先株判定の影響を受けない(self) -> None:
        """BFb.N（_p なしのクラス株）は従来どおり BF.B（nasdaq）のまま不変であることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["BFb.N"])

        assert conv.nasdaq == ["BF.B"]
        assert conv.preferred == []
        assert conv.exchanges == ["NYSE"]

    def test_正常系_優先株を含む混在RICを正しく分類する(self) -> None:
        """普通株/クラス株/優先株/指数/破棄の混在で 4 バケットが正しいことを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(["AAPL.O", "BFb.N", "AAM_pa.N", ".SPX", "XXX.UL"])

        assert conv.nasdaq == ["AAPL", "BF.B"]
        assert conv.preferred == ["AAM.A"]
        assert conv.nonus == [".SPX"]
        assert conv.dropped == ["XXX.UL"]
        # 不変条件: 4 バケットの総数 == 入力数
        total = (
            len(conv.nasdaq) + len(conv.preferred) + len(conv.nonus) + len(conv.dropped)
        )
        assert total == 5


class TestParseSitemapXml:
    """parse_sitemap_xml() のテスト."""

    def test_正常系_URL数分のエントリを抽出する(self) -> None:
        """サンプル XML から 3 件の SitemapEntry が抽出されることを確認。"""
        from news_scraper.reuters import parse_sitemap_xml

        entries = parse_sitemap_xml(SAMPLE_SUB_SITEMAP_XML)

        assert len(entries) == 3

    def test_正常系_各フィールドが正しく抽出される(self) -> None:
        """1 件目の loc/title/pub_date/lastmod/keywords/rics_raw が正しいことを確認。"""
        from news_scraper.reuters import parse_sitemap_xml

        entries = parse_sitemap_xml(SAMPLE_SUB_SITEMAP_XML)
        e = entries[0]

        assert e.loc == (
            "https://www.reuters.com/business/energy/apple-earnings-beat-2026-06-10/"
        )
        assert e.title == "Apple earnings beat expectations"
        assert e.pub_date == "2026-06-10T11:30:00Z"
        assert e.lastmod == "2026-06-10T12:00:00Z"
        assert e.keywords == "USN/AAPL, GUID/123"
        assert e.rics_raw == ["AAPL.O", ".SPX"]

    def test_正常系_sectionとsubsectionをURLから抽出する(self) -> None:
        """business/energy の section/subsection が URL から抽出されることを確認。"""
        from news_scraper.reuters import parse_sitemap_xml

        entries = parse_sitemap_xml(SAMPLE_SUB_SITEMAP_XML)
        e = entries[0]

        assert e.section == "business"
        assert e.subsection == "business/energy"

    def test_正常系_英語記事はlanguageがenになる(self) -> None:
        """world/us 記事は NON_EN_SECTIONS 外なので language=en になることを確認。"""
        from news_scraper.reuters import parse_sitemap_xml

        entries = parse_sitemap_xml(SAMPLE_SUB_SITEMAP_XML)
        e = entries[1]

        assert e.section == "world"
        assert e.language == "en"

    def test_正常系_スペイン語記事はlanguageがesになる(self) -> None:
        """/es/ 記事は URL セクション判定で language=es になることを確認。"""
        from news_scraper.reuters import parse_sitemap_xml

        entries = parse_sitemap_xml(SAMPLE_SUB_SITEMAP_XML)
        e = entries[2]

        assert e.section == "es"
        assert e.language == "es"

    def test_正常系_newslanguageタグは生値をlang_tagに保持する(self) -> None:
        """news:language は誤タグでも lang_tag に生値（en）を保持することを確認。"""
        from news_scraper.reuters import parse_sitemap_xml

        entries = parse_sitemap_xml(SAMPLE_SUB_SITEMAP_XML)

        # スペイン語記事でも news:language は "en" と誤タグ付けされる
        assert entries[2].lang_tag == "en"
        assert entries[2].language == "es"  # URL 判定が優先

    def test_エッジケース_stock_tickersなしでrics_rawが空(self) -> None:
        """stock_tickers タグがない記事は rics_raw が空リストになることを確認。"""
        from news_scraper.reuters import parse_sitemap_xml

        entries = parse_sitemap_xml(SAMPLE_SUB_SITEMAP_XML)

        assert entries[1].rics_raw == []


class TestEntryToArticle:
    """entry_to_article() のテスト."""

    def test_正常系_NASDAQティッカーがカンマ区切りで設定される(self) -> None:
        """複数の米株 RIC が ticker にカンマ区切りで連結されることを確認。"""
        from news_scraper.reuters import SitemapEntry, entry_to_article

        entry = SitemapEntry(
            loc="https://www.reuters.com/business/x/",
            title="Multi ticker",
            rics_raw=["AAPL.O", "MSFT.O"],
            section="business",
            subsection="business/x",
            language="en",
        )
        article = entry_to_article(entry)

        assert article.ticker == "AAPL,MSFT"

    def test_正常系_本文は空文字でmodeAを表す(self) -> None:
        """mode A は本文を取得しないため content が空文字であることを確認。"""
        from news_scraper.reuters import SitemapEntry, entry_to_article

        entry = SitemapEntry(loc="https://www.reuters.com/business/x/")
        article = entry_to_article(entry)

        assert article.content == ""

    def test_正常系_categoryはsubsection優先(self) -> None:
        """category は subsection があればそれ、なければ section になることを確認。"""
        from news_scraper.reuters import SitemapEntry, entry_to_article

        entry_with_sub = SitemapEntry(
            loc="https://www.reuters.com/business/energy/x/",
            section="business",
            subsection="business/energy",
        )
        assert entry_to_article(entry_with_sub).category == "business/energy"

        entry_no_sub = SitemapEntry(
            loc="https://www.reuters.com/business/",
            section="business",
            subsection="",
        )
        assert entry_to_article(entry_no_sub).category == "business"

    def test_正常系_article_idはlocになる(self) -> None:
        """mode A の重複排除キーである article_id が loc になることを確認。"""
        from news_scraper.reuters import SitemapEntry, entry_to_article

        loc = "https://www.reuters.com/business/x/"
        entry = SitemapEntry(loc=loc)
        article = entry_to_article(entry)

        assert article.article_id == loc
        assert article.url == loc

    def test_正常系_sourceはreuters(self) -> None:
        """source が "reuters" であることを確認。"""
        from news_scraper.reuters import REUTERS_SOURCE, SitemapEntry, entry_to_article

        article = entry_to_article(SitemapEntry(loc="https://www.reuters.com/x/"))

        assert article.source == "reuters"
        assert article.source == REUTERS_SOURCE

    def test_正常系_metadataに必須キーがすべて含まれる(self) -> None:
        """metadata に section/subsection/language/rics_* 等のキーが含まれることを確認。"""
        from news_scraper.reuters import SitemapEntry, entry_to_article

        entry = SitemapEntry(
            loc="https://www.reuters.com/business/energy/x/",
            title="t",
            pub_date="2026-06-10T00:00:00Z",
            lastmod="2026-06-10T01:00:00Z",
            keywords="USN/AAPL",
            rics_raw=["AAPL.O", ".SPX"],
            section="business",
            subsection="business/energy",
            language="en",
            lang_tag="en",
        )
        meta = entry_to_article(entry).metadata

        for key in (
            "section",
            "subsection",
            "language",
            "sitemap_lang_tag",
            "rics_raw",
            "rics_nasdaq",
            "listing_exchanges",
            "rics_nonus",
            "rics_preferred",
            "rics_dropped",
            "keywords",
            "lastmod",
        ):
            assert key in meta, f"metadata missing key: {key}"

        assert meta["section"] == "business"
        assert meta["subsection"] == "business/energy"
        assert meta["language"] == "en"
        assert meta["sitemap_lang_tag"] == "en"
        assert meta["rics_raw"] == ["AAPL.O", ".SPX"]
        assert meta["rics_nasdaq"] == ["AAPL"]
        assert meta["rics_nonus"] == [".SPX"]

    def test_正常系_優先株RICはrics_preferredとtickerに反映される(self) -> None:
        """優先株 RIC が metadata.rics_preferred に入り ticker（普通株）には入らないことを確認。"""
        from news_scraper.reuters import SitemapEntry, entry_to_article

        entry = SitemapEntry(
            loc="https://www.reuters.com/business/x/",
            title="Preferred",
            rics_raw=["AAPL.O", "AAM_pa.N"],
            section="business",
            subsection="business/x",
            language="en",
        )
        article = entry_to_article(entry)

        # ticker は普通株のみ（優先株は混入しない）
        assert article.ticker == "AAPL"
        assert article.metadata["rics_preferred"] == ["AAM.A"]
        assert article.metadata["rics_nasdaq"] == ["AAPL"]


def _make_filter_df() -> pd.DataFrame:
    """filter_articles テスト用の DataFrame を作成する."""
    return pd.DataFrame(
        [
            {
                "title": "English business",
                "language": "en",
                "section": "business",
                "subsection": "business/energy",
            },
            {
                "title": "English sports",
                "language": "en",
                "section": "sports",
                "subsection": "sports/soccer",
            },
            {
                "title": "Spanish markets",
                "language": "es",
                "section": "es",
                "subsection": "es/mercados",
            },
            {
                "title": "English markets",
                "language": "en",
                "section": "markets",
                "subsection": "markets/us",
            },
        ]
    )


class TestFilterArticles:
    """filter_articles() のテスト（分析時フィルタ）."""

    def test_正常系_lang指定で当該言語のみ残す(self) -> None:
        """lang="en" で英語記事のみ残ることを確認。"""
        from news_scraper.reuters import filter_articles

        df = filter_articles(_make_filter_df(), lang="en")

        assert len(df) == 3
        assert (df["language"] == "en").all()

    def test_正常系_lang_allで全件残す(self) -> None:
        """lang="all" でフィルタされず全件残ることを確認。"""
        from news_scraper.reuters import filter_articles

        df = filter_articles(_make_filter_df(), lang="all")

        assert len(df) == 4

    def test_正常系_sectionsをsection粒度でフィルタする(self) -> None:
        """sections={business} で section=business の記事のみ残ることを確認。"""
        from news_scraper.reuters import filter_articles

        df = filter_articles(_make_filter_df(), sections={"business"})

        assert len(df) == 1
        assert df.iloc[0]["section"] == "business"

    def test_正常系_sectionsをsubsection粒度でフィルタする(self) -> None:
        """sections={markets/us} で subsection 粒度マッチすることを確認。"""
        from news_scraper.reuters import filter_articles

        df = filter_articles(_make_filter_df(), sections={"markets/us"})

        assert len(df) == 1
        assert df.iloc[0]["subsection"] == "markets/us"

    def test_正常系_exclude_sectionsで除外する(self) -> None:
        """exclude_sections={sports} で sports を除外することを確認。"""
        from news_scraper.reuters import filter_articles

        df = filter_articles(_make_filter_df(), exclude_sections={"sports"})

        assert len(df) == 3
        assert "sports" not in set(df["section"])

    def test_エッジケース_空DataFrameで空を返す(self) -> None:
        """空 DataFrame を渡しても例外なく空を返すことを確認。"""
        from news_scraper.reuters import filter_articles

        empty = pd.DataFrame({"language": [], "section": [], "subsection": []})
        df = filter_articles(empty, lang="en", sections={"business"})

        assert df.empty


def _resp(status_code: int, text: str = "") -> MagicMock:
    """status_code / text を持つレスポンスモックを作る."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = {}
    return resp


class TestFetchText:
    """_fetch_text() のリトライ・エラー分類テスト.

    実ネットワークアクセス・実待機は発生させない（session.get をモックし、
    tenacity の待機 sleep をパッチする）。
    """

    def test_正常系_200で本文テキストを返す(self) -> None:
        """200 応答で resp.text をそのまま返すことを確認。"""
        from news_scraper.reuters import _fetch_text

        session = MagicMock()
        session.get.return_value = _resp(200, "<xml>ok</xml>")

        with patch("tenacity.nap.time.sleep"):
            result = _fetch_text(session, "https://www.reuters.com/x")

        assert result == "<xml>ok</xml>"
        assert session.get.call_count == 1  # 200 はリトライしない

    def test_正常系_500がリトライされ最終的に200で成功する(self) -> None:
        """500 → 200 の順でリトライし、最終的に本文を返すことを確認。"""
        from news_scraper.reuters import _fetch_text

        session = MagicMock()
        session.get.side_effect = [_resp(500), _resp(200, "recovered")]

        # tenacity の待機 sleep をパッチし、実待機を発生させない
        with patch("tenacity.nap.time.sleep"):
            result = _fetch_text(session, "https://www.reuters.com/x")

        assert result == "recovered"
        assert session.get.call_count == 2  # 500 で1回リトライ

    def test_異常系_404は即座にNoneを返しリトライしない(self) -> None:
        """404（PermanentError）はリトライせず即 None を返すことを確認。"""
        from news_scraper.reuters import _fetch_text

        session = MagicMock()
        session.get.return_value = _resp(404)

        with patch("tenacity.nap.time.sleep"):
            result = _fetch_text(session, "https://www.reuters.com/missing")

        assert result is None
        assert session.get.call_count == 1  # 404 はリトライしない

    def test_異常系_500がリトライ上限を超えたらNoneを返す(self) -> None:
        """500 が継続しリトライ上限（3回）に達したら None を返すことを確認。"""
        from news_scraper.reuters import _fetch_text

        session = MagicMock()
        session.get.return_value = _resp(500)

        with patch("tenacity.nap.time.sleep"):
            result = _fetch_text(session, "https://www.reuters.com/x")

        assert result is None
        assert session.get.call_count == 3  # max_attempts=3

    def test_異常系_例外発生時はNoneを返す(self) -> None:
        """session.get が例外を投げても握りつぶして None を返すことを確認。"""
        from news_scraper.reuters import _fetch_text

        session = MagicMock()
        session.get.side_effect = Exception("connection reset")

        with patch("tenacity.nap.time.sleep"):
            result = _fetch_text(session, "https://www.reuters.com/x")

        assert result is None


# NASDAQ 公式ディレクトリのサンプル（パイプ区切り）
SAMPLE_NASDAQ_LISTED = (
    "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size\n"
    "AAPL|Apple Inc. - Common Stock|Q|N|N|100\n"
    "MSFT|Microsoft Corporation - Common Stock|Q|N|N|100\n"
    "File Creation Time: 0610202612:00|||||\n"
)
SAMPLE_OTHER_LISTED = (
    "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\n"
    "BF.B|Brown-Forman Corporation Class B|N|BF.B|N|100|N|BF.B\n"
    "BA|Boeing Company|N|BA|N|100|N|BA\n"
    "GOOGL|Alphabet Inc. Class A|Q|GOOGL|N|100|N|GOOG.L\n"
    "File Creation Time: 0610202612:00|||||||\n"
)


class TestLoadNasdaqDirectory:
    """load_nasdaq_directory() のテスト（I/O、session.get をモック）."""

    def test_正常系_両ファイルからシンボル集合を構築する(self) -> None:
        """nasdaqlisted の col0 と otherlisted の col0/col7 を集合化することを確認。"""
        from news_scraper.reuters import load_nasdaq_directory

        session = MagicMock()

        def _get(url: str, *args: object, **kwargs: object) -> MagicMock:
            resp = MagicMock()
            resp.status_code = 200
            resp.headers = {}
            if "nasdaqlisted" in url:
                resp.text = SAMPLE_NASDAQ_LISTED
            else:
                resp.text = SAMPLE_OTHER_LISTED
            return resp

        session.get.side_effect = _get

        with patch("tenacity.nap.time.sleep"):
            directory = load_nasdaq_directory(session)

        # nasdaqlisted col0
        assert "AAPL" in directory
        assert "MSFT" in directory
        # otherlisted col0（ACT Symbol）
        assert "BF.B" in directory
        assert "BA" in directory
        # otherlisted col7（NASDAQ Symbol、ACT と異なる場合も追加）
        assert "GOOGL" in directory
        assert "GOOG.L" in directory

    def test_正常系_ヘッダとフッタ行はスキップされる(self) -> None:
        """ヘッダ行（Symbol...）と File Creation Time フッタ行が含まれないことを確認。"""
        from news_scraper.reuters import load_nasdaq_directory

        session = MagicMock()

        def _get(url: str, *args: object, **kwargs: object) -> MagicMock:
            resp = MagicMock()
            resp.status_code = 200
            resp.headers = {}
            resp.text = (
                SAMPLE_NASDAQ_LISTED if "nasdaqlisted" in url else SAMPLE_OTHER_LISTED
            )
            return resp

        session.get.side_effect = _get

        with patch("tenacity.nap.time.sleep"):
            directory = load_nasdaq_directory(session)

        assert "Symbol" not in directory
        assert "ACT Symbol" not in directory
        # File Creation Time 行の col0 は混入しない
        assert not any(s.startswith("File Creation Time") for s in directory)

    def test_エッジケース_取得失敗時は空集合を返す(self) -> None:
        """両ファイルが取得失敗（None）のとき空集合を返すことを確認。"""
        from news_scraper.reuters import load_nasdaq_directory

        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 404
        resp.headers = {}
        resp.text = ""
        session.get.return_value = resp

        with patch("tenacity.nap.time.sleep"):
            directory = load_nasdaq_directory(session)

        assert directory == set()


class TestValidateNasdaqTickers:
    """validate_nasdaq_tickers() のテスト（純関数・I/O なし）."""

    @staticmethod
    def _df(rows: list[dict[str, object]]) -> pd.DataFrame:
        return pd.DataFrame(rows)

    def test_正常系_matchedとunmatchedを付与する(self) -> None:
        """rics_nasdaq を directory と照合し matched/unmatched 列を付与することを確認。"""
        from news_scraper.reuters import validate_nasdaq_tickers

        df = self._df(
            [
                {"metadata": {"rics_nasdaq": ["AAPL", "DELISTED"]}},
                {"metadata": {"rics_nasdaq": ["MSFT"]}},
            ]
        )
        directory = {"AAPL", "MSFT"}

        result = validate_nasdaq_tickers(df, directory)

        assert result.iloc[0]["nasdaq_matched"] == ["AAPL"]
        assert result.iloc[0]["nasdaq_unmatched"] == ["DELISTED"]
        assert result.iloc[1]["nasdaq_matched"] == ["MSFT"]
        assert result.iloc[1]["nasdaq_unmatched"] == []

    def test_正常系_純関数で入力dfを破壊しない(self) -> None:
        """入力 DataFrame に検証列を追加しない（新しい DataFrame を返す）ことを確認。"""
        from news_scraper.reuters import validate_nasdaq_tickers

        df = self._df([{"metadata": {"rics_nasdaq": ["AAPL"]}}])

        result = validate_nasdaq_tickers(df, {"AAPL"})

        assert "nasdaq_matched" in result.columns
        assert "nasdaq_matched" not in df.columns  # 元 df は不変

    def test_エッジケース_rics_nasdaqなしで空リストになる(self) -> None:
        """metadata に rics_nasdaq がない行は matched/unmatched とも空になることを確認。"""
        from news_scraper.reuters import validate_nasdaq_tickers

        df = self._df([{"metadata": {}}])

        result = validate_nasdaq_tickers(df, {"AAPL"})

        assert result.iloc[0]["nasdaq_matched"] == []
        assert result.iloc[0]["nasdaq_unmatched"] == []

    def test_エッジケース_空DataFrameで空を返す(self) -> None:
        """空 DataFrame を渡しても例外なく空を返すことを確認（空 DF ガード）。"""
        from news_scraper.reuters import validate_nasdaq_tickers

        df = pd.DataFrame()

        result = validate_nasdaq_tickers(df, {"AAPL"})

        assert result.empty


class TestConstants:
    """モジュール定数のテスト."""

    def test_正常系_米株サフィックスと取引所マップが整合する(self) -> None:
        """US_EQUITY_SUFFIXES の全要素が SUFFIX_EXCHANGE に存在することを確認。"""
        from news_scraper.reuters import SUFFIX_EXCHANGE, US_EQUITY_SUFFIXES

        for suffix in US_EQUITY_SUFFIXES:
            assert suffix in SUFFIX_EXCHANGE

    def test_正常系_サイトマップインデックスURLが定義される(self) -> None:
        """REUTERS_NEWS_SITEMAP_INDEX が Reuters の URL であることを確認。"""
        from news_scraper.reuters import REUTERS_NEWS_SITEMAP_INDEX

        assert "reuters.com" in REUTERS_NEWS_SITEMAP_INDEX
        assert "news-sitemap-index" in REUTERS_NEWS_SITEMAP_INDEX

    def test_正常系_非英語セクションにesが含まれる(self) -> None:
        """NON_EN_SECTIONS に主要多言語コードが含まれることを確認。"""
        from news_scraper.reuters import NON_EN_SECTIONS

        assert "es" in NON_EN_SECTIONS
        assert "pt" in NON_EN_SECTIONS
        assert "latam" in NON_EN_SECTIONS

    def test_正常系_NASDAQディレクトリURLが定義される(self) -> None:
        """NASDAQ_LISTED_URL / NASDAQ_OTHER_LISTED_URL が定義されることを確認。"""
        from news_scraper.reuters import NASDAQ_LISTED_URL, NASDAQ_OTHER_LISTED_URL

        assert NASDAQ_LISTED_URL == (
            "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
        )
        assert NASDAQ_OTHER_LISTED_URL == (
            "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
        )
