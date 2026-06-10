"""reuters.py のプロパティベーステスト（Hypothesis）.

対象モジュール: src/news_scraper/reuters.py（mode A）

純関数の不変条件を検証する:
- convert_rics: 全 RIC が一意に分類される（len 保存）
- parse_sitemap_xml: 返り entry 数 == <url> 数
- filter_articles: 返りは入力の部分集合・lang フィルタ後は全行が当該言語
"""

from __future__ import annotations

import pandas as pd
from hypothesis import given
from hypothesis import strategies as st

# RIC を生成するストラテジー（各資産クラスを網羅）
_us_suffix = st.sampled_from(["O", "OQ", "N", "A", "P", "K", "PK", "DG", "PH"])
_intl_suffix = st.sampled_from(["T", "AX", "L", "HK", "MI", "NS", "TO", "PA", "DE"])
_root = st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=5)

_us_equity_ric = st.builds(lambda r, s: f"{r}.{s}", _root, _us_suffix)
_class_share_ric = st.builds(
    lambda r, c, s: f"{r}{c}.{s}",
    _root,
    st.sampled_from(["a", "b", "c"]),
    _us_suffix,
)
# 優先株 RIC（root が ``XXX_p{series}`` 形式、例 ``AAM_pa.N``）
_preferred_ric = st.builds(
    lambda r, c, s: f"{r}_p{c}.{s}",
    _root,
    st.sampled_from(["a", "b", "c", "d"]),
    _us_suffix,
)
_index_ric = st.builds(lambda r: f".{r}", _root)
_fx_ric = st.builds(lambda r: f"{r}=", _root)
_future_ric = st.builds(lambda r, n: f"{r}c{n}", _root, st.integers(1, 9))
_intl_ric = st.builds(lambda r, s: f"{r}.{s}", _root, _intl_suffix)
_ul_ric = st.builds(lambda r: f"{r}.UL", _root)
_bare_ric = _root

_any_ric = st.one_of(
    _us_equity_ric,
    _class_share_ric,
    _preferred_ric,
    _index_ric,
    _fx_ric,
    _future_ric,
    _intl_ric,
    _ul_ric,
    _bare_ric,
)


class TestConvertRicsProperty:
    """convert_rics() の不変条件."""

    @given(rics=st.lists(_any_ric, max_size=30))
    def test_プロパティ_全RICが一意に分類される(self, rics: list[str]) -> None:
        """nasdaq + preferred + nonus + dropped の総数が入力 RIC 数と一致することを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(rics)
        total = (
            len(conv.nasdaq) + len(conv.preferred) + len(conv.nonus) + len(conv.dropped)
        )

        assert total == len(rics)

    @given(rics=st.lists(_any_ric, max_size=30))
    def test_プロパティ_exchangesはnasdaqと同数(self, rics: list[str]) -> None:
        """exchanges は nasdaq（普通株）と同じ要素数（同順の上場市場）であることを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(rics)

        assert len(conv.exchanges) == len(conv.nasdaq)

    @given(rics=st.lists(_any_ric, max_size=30))
    def test_プロパティ_優先株は普通株tickerに混入しない(self, rics: list[str]) -> None:
        """preferred の要素はドット表記で、nasdaq（普通株）と重複しないことを確認。"""
        from news_scraper.reuters import convert_rics

        conv = convert_rics(rics)

        # preferred は普通株（nasdaq）に混入しない
        for sym in conv.preferred:
            assert "." in sym  # best-effort ドット表記
            assert sym not in conv.nasdaq


# XML 用に安全な文字（< > & を除外し XML エスケープ不要にする）
_xml_safe_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "Zs", "P"),
        blacklist_characters="<>&\"'",
    ),
    max_size=40,
)
_slug = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=20
)


def _build_sitemap_xml(items: list[tuple[str, str]]) -> str:
    """(section, title) のリストからサブサイトマップ XML を構築する."""
    urls = []
    for section, title in items:
        urls.append(
            "  <url>\n"
            f"    <loc>https://www.reuters.com/{section}/article-slug/</loc>\n"
            "    <lastmod>2026-06-10T12:00:00Z</lastmod>\n"
            "    <news:news>\n"
            "      <news:publication>\n"
            "        <news:name>Reuters</news:name>\n"
            "        <news:language>en</news:language>\n"
            "      </news:publication>\n"
            "      <news:publication_date>2026-06-10T11:30:00Z</news:publication_date>\n"
            f"      <news:title>{title}</news:title>\n"
            "    </news:news>\n"
            "  </url>\n"
        )
    body = "".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        f"{body}</urlset>\n"
    )


class TestParseSitemapXmlProperty:
    """parse_sitemap_xml() の不変条件."""

    @given(
        items=st.lists(
            st.tuples(_slug, _xml_safe_text),
            max_size=20,
        )
    )
    def test_プロパティ_エントリ数はurl数と一致する(
        self, items: list[tuple[str, str]]
    ) -> None:
        """返り SitemapEntry 数が <url> 要素数と一致することを確認。"""
        from news_scraper.reuters import parse_sitemap_xml

        xml = _build_sitemap_xml(items)
        entries = parse_sitemap_xml(xml)

        assert len(entries) == len(items)


def _build_articles_df(rows: list[tuple[str, str]]) -> pd.DataFrame:
    """(language, section) のリストから filter_articles 用 DataFrame を作る."""
    return pd.DataFrame(
        [
            {
                "language": lang,
                "section": section,
                "subsection": f"{section}/sub",
            }
            for lang, section in rows
        ]
    )


class TestFilterArticlesProperty:
    """filter_articles() の不変条件."""

    @given(
        rows=st.lists(
            st.tuples(
                st.sampled_from(["en", "es", "pt", "fr"]),
                st.sampled_from(["business", "markets", "world", "sports"]),
            ),
            max_size=30,
        ),
        lang=st.sampled_from(["all", "en", "es", "pt", "fr"]),
    )
    def test_プロパティ_返りは入力の部分集合(
        self, rows: list[tuple[str, str]], lang: str
    ) -> None:
        """フィルタ結果の行数は入力以下であることを確認。"""
        from news_scraper.reuters import filter_articles

        df = _build_articles_df(rows)
        result = filter_articles(df, lang=lang)

        assert len(result) <= len(df)

    @given(
        rows=st.lists(
            st.tuples(
                st.sampled_from(["en", "es", "pt", "fr"]),
                st.sampled_from(["business", "markets", "world"]),
            ),
            min_size=1,
            max_size=30,
        ),
        lang=st.sampled_from(["en", "es", "pt", "fr"]),
    )
    def test_プロパティ_langフィルタ後は全行が当該言語(
        self, rows: list[tuple[str, str]], lang: str
    ) -> None:
        """lang フィルタ後の全行の language が指定言語と一致することを確認。"""
        from news_scraper.reuters import filter_articles

        df = _build_articles_df(rows)
        result = filter_articles(df, lang=lang)

        if not result.empty:
            assert (result["language"] == lang).all()
