"""Reuters ニューススクレイパー（mode A: サイトマップ・メタデータ収集）.

ロイターの news-sitemap から記事メタデータと関連 RIC を収集し、RIC を NASDAQ
ティッカーへ変換して :class:`~news_scraper.types.Article` へマップする。本文取得
（mode B、Playwright 経由）は本モジュールでは実装しない。

設計の正本は ``docs/plan/2026-06-10_reuters-scraping-design.md``（特に §3.0 ETL 方針 /
§5 RIC→NASDAQ 変換 / §9 実測）。PoC ``.tmp/reuters_mode_a_poc.py`` を製品コードへ移植・
整理したもの。既存 news_scraper パターン（``session.py`` / ``retry.py`` / ``types.Article``）
を踏襲する。

処理フロー（mode A）
--------------------
1. ``fetch_sitemap_index`` で news-sitemap-index → サブサイトマップ URL 群を取得
   （curl_cffi コールド取得、DataDome 通過可能）。
2. 各サブサイトマップを取得し ``parse_sitemap_xml`` で ``SitemapEntry`` を抽出
   （loc / title / pub_date / lastmod / keywords / stock_tickers）。
3. ``convert_rics`` で米株 RIC → NASDAQ ティッカーへ変換し、指数 / FX / 先物 / 国際株を
   ``rics_nonus`` に分離。
4. ``entry_to_article`` で :class:`Article` へマップ（``content=""``、
   ``ticker`` = NASDAQ ティッカーのカンマ区切り）。
5. ``collect_reuters_news`` が **無フィルタで全件** を ``DataFrame`` として返す
   （raw レイヤー）。``save_reuters_news`` で日付別 parquet に保存する。

重要な設計判断（設計書 §3.0 / §9）
----------------------------------
- **収集は無フィルタ全件保存**: news-sitemap で取得できる記事を言語 / カテゴリで
  絞らず全件保存する。実測スナップショット（3,799 件）の言語分布は es 2,602 /
  latam 588 / en 438 ... と es が支配的で、収集時に en 限定すると 88% を取りこぼす。
  言語 / カテゴリの絞り込みは分析段階の :func:`filter_articles` で行う。
- **言語判定は URL セクションで行う**: ``<news:language>`` は多言語記事でも en と
  誤タグ付けされ信頼できない（生値は ``metadata.sitemap_lang_tag`` に参考保持）。
- **ticker は NASDAQ 形式**: リポジトリ基準形式（``normalize_ticker`` の入力形式）。
  クラス株はドット表記（``BFb.N`` → ``BF.B``）。
- **純関数は I/O フリー**: ネットワークアクセスは ``fetch_*`` / ``collect_*`` のみに
  閉じ込め、変換・パースの純関数からは分離する。

拡張ポイント（mode B: 本文取得・未実装）
----------------------------------------
Reuters の記事 HTML / 内部 API は DataDome により 401 でブロックされるため、本文取得は
Playwright（実ブラウザ）が事実上必須（設計書 §2.2）。mode B を追加する場合は CNBC /
NASDAQ の Playwright パターンに倣い、以下を遅延 import で追加する:

- ``fetch_article_playwright(url) -> str``: 実ブラウザで記事 HTML を取得。
- ``extract_fusion_json(html) -> dict``: ``Fusion.globalContent`` をインライン抽出。
- ``parse_article(html) -> Article``: Fusion JSON → Article（フォールバック JSON-LD /
  trafilatura）。本文は ``content_elements[]`` を結合し ``content`` に格納、重複排除キーは
  Arc ``id`` を使う。
"""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET  # nosec B405
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import cast

import pandas as pd
from curl_cffi import requests

from utils_core.logging import get_logger

from .exceptions import ScraperError
from .retry import classify_http_error, create_retry_decorator
from .session import create_session
from .types import Article, ScraperConfig, get_delay

logger = get_logger(__name__)

# サイトマップ / ディレクトリ取得用リトライデコレータ（429/5xx を指数バックオフで再試行）。
# yfinance.py の確立パターンに合わせて module レベルで生成する。
_fetch_retry = create_retry_decorator(max_attempts=3)


# ============================================================
# 定数
# ============================================================
REUTERS_NEWS_SITEMAP_INDEX: str = (
    "https://www.reuters.com/arc/outboundfeeds/news-sitemap-index/?outputType=xml"
)
"""ニュースサイトマップインデックス URL（86 サブ・コールド取得可）."""

REUTERS_SOURCE: str = "reuters"
""":class:`Article.source` に格納するソース識別子."""

NASDAQ_LISTED_URL: str = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
"""NASDAQ 上場銘柄ディレクトリ URL（パイプ区切り、col0=Symbol）."""

NASDAQ_OTHER_LISTED_URL: str = (
    "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
)
"""NASDAQ 以外の上場銘柄ディレクトリ URL（col0=ACT Symbol、col7=NASDAQ Symbol）."""

SITEMAP_NS: dict[str, str] = {
    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
}
"""サイトマップ / Google ニュースサイトマップの XML 名前空間マップ."""

US_EQUITY_SUFFIXES: frozenset[str] = frozenset(
    {"O", "OQ", "N", "A", "P", "K", "PK", "DG", "PH"}
)
"""米国取引所サフィックス（RIC root == NASDAQ ティッカー）."""

SUFFIX_EXCHANGE: dict[str, str] = {
    "O": "NASDAQ",
    "OQ": "NASDAQ",
    "N": "NYSE",
    "A": "NYSE American",
    "P": "NYSE Arca",
    "K": "NYSE",
    "PK": "OTC/Pink",
    "DG": "NYSE",
    "PH": "Philadelphia",
}
"""米国取引所サフィックス → 上場市場名（メタデータ用）."""

# Reuters の多言語版セクションコード（URL パス先頭）。
# news:language タグは多言語記事でも "en" と誤タグ付けされるため、URL で判定する。
# robots.txt の Disallow（/fr/ /it/ /es/ /pt/ /de/ /latam/）にも対応。
NON_EN_SECTIONS: frozenset[str] = frozenset(
    {
        "es",
        "pt",
        "fr",
        "de",
        "it",
        "ar",
        "ja",
        "jp",
        "zh",
        "cn",
        "ko",
        "ru",
        "latam",
        "br",
        "uk-spanish",
    }
)
"""英語以外の多言語版セクションコード（URL パス先頭セグメント）."""

# 連続先物 RIC の検出（末尾 cN / cvN）
_FUTURE_RE = re.compile(r"c\d+$|cv\d+$")
# 優先株 root の検出（``_p`` + シリーズ小文字 1 文字、例 ``AAM_pa``）。
# クラス株判定より先に評価する（クラス株 root 末尾の小文字 1 文字と区別するため）。
_PREFERRED_RE = re.compile(r"^([A-Z0-9]+)_p([a-z])$")
# クラス株 root の検出（末尾小文字 1 文字）
_CLASS_SHARE_RE = re.compile(r"^([A-Z0-9]+)([a-z])$")
# loc から section / subsection を抽出（最終セグメント=slug を除く）
_SECTION_RE = re.compile(r"https?://[^/]+/(.+?)/[^/]*$")

# 保存ベースディレクトリ（本番 raw レイヤー）
_DEFAULT_BASE_DIR = Path("data/raw/news/reuters")

# Article.to_dict() のキー順（出力列の Article 11 列）
_ARTICLE_COLUMNS: tuple[str, ...] = (
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
)


# ============================================================
# データモデル
# ============================================================
@dataclass
class SitemapEntry:
    """ニュースサイトマップ 1 記事分のメタデータ.

    Attributes
    ----------
    loc : str
        記事 URL（``<loc>``）。mode A の重複排除キー。
    title : str
        記事タイトル（``<news:title>``）。
    pub_date : str
        公開日時（``<news:publication_date>``、ISO 8601）。
    lastmod : str
        サイトマップ最終更新日時（``<lastmod>``）。
    keywords : str
        ``<news:keywords>``（GUID / USN 等）。
    rics_raw : list[str]
        ``<news:stock_tickers>`` の RIC リスト（カンマ分割済み）。
    section : str
        URL 先頭セグメント（例 ``business``）。
    subsection : str
        URL 先頭 2 セグメント（例 ``business/energy``）。
    language : str
        URL セクションから判定した言語（``en`` / ``es`` / ``pt`` ...）。
    lang_tag : str
        ``<news:language>`` の生値。多言語でも en と誤タグ付けされるため信頼せず
        参考保持のみ。
    """

    loc: str
    title: str = ""
    pub_date: str = ""
    lastmod: str = ""
    keywords: str = ""
    rics_raw: list[str] = field(default_factory=list)
    section: str = ""
    subsection: str = ""
    language: str = ""
    lang_tag: str = ""


@dataclass
class RicConversion:
    """RIC 変換結果.

    Attributes
    ----------
    nasdaq : list[str]
        米株 NASDAQ ティッカー（クラス株はドット表記、普通株のみ）。
    exchanges : list[str]
        ``nasdaq`` と同順・同数の上場市場名。
    preferred : list[str]
        米国優先株の **best-effort・近似** シンボル（ドット表記、例 ``AAM.A``）。
        普通株（``nasdaq``）とは別バケットに分離し、``ticker`` には混入させない。
    nonus : list[str]
        指数 / FX / 先物 / 国際株（NASDAQ ティッカー対象外）。
    dropped : list[str]
        ``.UL``（Reuters 非上場）等の破棄対象 RIC。
    """

    nasdaq: list[str] = field(default_factory=list)
    exchanges: list[str] = field(default_factory=list)
    preferred: list[str] = field(default_factory=list)
    nonus: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)


# ============================================================
# 純関数: サイトマップパース
# ============================================================
def parse_sitemap_xml(xml: str) -> list[SitemapEntry]:
    """サブサイトマップ XML から ``SitemapEntry`` 群を抽出する.

    各 ``<url>`` 要素から loc / title / pub_date / lastmod / keywords / stock_tickers を
    取り出す。section / subsection は URL パスの階層から、language は URL セクションが
    :data:`NON_EN_SECTIONS` に含まれるかで判定する（``<news:language>`` は多言語記事でも
    en と誤タグ付けされ信頼できないため、生値は ``lang_tag`` にのみ保持）。

    Parameters
    ----------
    xml : str
        サブサイトマップの XML 文字列。

    Returns
    -------
    list[SitemapEntry]
        記事メタデータのリスト（``<url>`` 要素と同数・同順）。

    Examples
    --------
    >>> xml = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
    >>> parse_sitemap_xml(xml)
    []
    """
    root = ET.fromstring(xml.encode("utf-8"))  # nosec B314
    entries: list[SitemapEntry] = []

    for url_el in root.findall(".//s:url", SITEMAP_NS):
        loc = url_el.findtext("s:loc", default="", namespaces=SITEMAP_NS)
        lastmod = url_el.findtext("s:lastmod", default="", namespaces=SITEMAP_NS)
        title = url_el.findtext(
            ".//news:title", default="", namespaces=SITEMAP_NS
        ).strip()
        pub_date = url_el.findtext(
            ".//news:publication_date", default="", namespaces=SITEMAP_NS
        )
        keywords = url_el.findtext(
            ".//news:keywords", default="", namespaces=SITEMAP_NS
        ).strip()
        lang_tag = (
            url_el.findtext(".//news:language", default="", namespaces=SITEMAP_NS)
            .strip()
            .lower()
        )
        tickers_raw = url_el.findtext(
            ".//news:stock_tickers", default="", namespaces=SITEMAP_NS
        )
        rics = [t.strip() for t in tickers_raw.split(",") if t.strip()]

        section, subsection = _parse_section(loc)
        # 言語は URL セクションで判定（news:language は誤タグで信頼不可）
        language = section if section in NON_EN_SECTIONS else "en"

        entries.append(
            SitemapEntry(
                loc=loc,
                title=title,
                pub_date=pub_date,
                lastmod=lastmod,
                keywords=keywords,
                rics_raw=rics,
                section=section,
                subsection=subsection,
                language=language,
                lang_tag=lang_tag,
            )
        )

    logger.debug("Parsed sitemap XML", entry_count=len(entries))
    return entries


def _parse_section(loc: str) -> tuple[str, str]:
    """記事 URL から section / subsection を抽出する.

    URL パス ``/{section}/{subsection}/{slug}/`` から先頭 1 / 2 セグメントを返す。

    Parameters
    ----------
    loc : str
        記事 URL。

    Returns
    -------
    tuple[str, str]
        ``(section, subsection)``。抽出できない場合は ``("", "")``。
    """
    m = _SECTION_RE.match(loc)
    if not m:
        return "", ""
    parts = m.group(1).split("/")
    section = parts[0]
    subsection = "/".join(parts[:2]) if len(parts) >= 2 else ""
    return section, subsection


# ============================================================
# 純関数: RIC → NASDAQ ティッカー変換
# ============================================================
def _ric_to_nasdaq(ric: str) -> str:
    """米株 RIC の root を NASDAQ ティッカーへ変換する.

    root が ``^[A-Z0-9]+[a-z]$``（クラス株）の場合、末尾小文字をドット表記へ変換する
    （例 ``BFb`` → ``BF.B``）。それ以外は root をそのまま返す。

    Parameters
    ----------
    ric : str
        米株 RIC（例 ``AAPL.O``、``BFb.N``）。

    Returns
    -------
    str
        NASDAQ ティッカー（例 ``AAPL``、``BF.B``）。
    """
    root = ric.split(".", maxsplit=1)[0]
    m = _CLASS_SHARE_RE.match(root)
    if m:  # クラス株: BFb -> BF.B
        return f"{m.group(1)}.{m.group(2).upper()}"
    return root


def _ric_to_preferred(ric: str) -> str:
    """米国優先株 RIC の root を **best-effort・近似** シンボルへ変換する.

    優先株は Reuters で ``XXX_p{series}``（``_p`` + シリーズ小文字）と表記される
    （例 ``AAM_pa``）。NASDAQ 形式の近似シンボルは ``{base}.{series.upper()}``
    （ドット表記、リポジトリの NASDAQ 形式・NASDAQ ディレクトリと整合）として返す
    （例 ``AAM_pa`` → ``AAM.A``）。

    .. note::
        優先株シンボルは **best-effort・近似** であり、実際の取引所表記
        （``XXX-A`` / ``XXX.PRA`` 等）と完全一致は保証しない。普通株 ``ticker`` には
        混入させず、:attr:`RicConversion.preferred` バケットにのみ格納する。

    Parameters
    ----------
    ric : str
        米国優先株 RIC（例 ``AAM_pa.N``）。root が優先株パターンに一致する前提。

    Returns
    -------
    str
        近似 NASDAQ 形式シンボル（例 ``AAM.A``）。
    """
    root = ric.split(".", maxsplit=1)[0]
    m = _PREFERRED_RE.match(root)
    if m:  # 優先株: AAM_pa -> AAM.A（best-effort・近似）
        return f"{m.group(1)}.{m.group(2).upper()}"
    return root


def convert_rics(rics: list[str]) -> RicConversion:
    """RIC 群を NASDAQ ティッカー / 対象外に分類する（設計書 §5）.

    判定優先順:

    1. 先頭 ``.``（``.SPX`` 等） → 指数 → ``nonus``
    2. 末尾 ``=``（``EUR=`` 等） → FX → ``nonus``
    3. 末尾 ``cN`` / ``cvN``（``CLc1`` 等） → 連続先物 → ``nonus``
    4. ``.{米国サフィックス}``（``AAPL.O`` 等） → 米株
       a. root が優先株パターン ``^([A-Z0-9]+)_p([a-z])$``（``AAM_pa`` 等） →
          **優先株** → ``preferred``（best-effort・近似シンボル ``AAM.A``）。
          優先株判定はクラス株判定より先に行い、``nasdaq``/``exchanges`` には入れない。
       b. それ以外 → **普通株** → ``nasdaq``
          （クラス株は末尾小文字 → ドット表記、例 ``BFb.N`` → ``BF.B``）
    5. ``.UL`` → Reuters 非上場 → ``dropped``
    6. その他 ``.{suffix}``（``7203.T`` 等） → 国際株 → ``nonus``
    7. サフィックスなし（Reuters 固有等） → ``nonus``

    すべての入力 RIC は ``nasdaq`` / ``preferred`` / ``nonus`` / ``dropped`` の
    いずれか 1 つに一意に分類される
    （``len(nasdaq) + len(preferred) + len(nonus) + len(dropped) == len(rics)``）。

    .. note::
        優先株シンボルは **best-effort・近似** であり、実際の取引所表記
        （``XXX-A`` / ``XXX.PRA`` 等）との完全一致は保証しない。``ticker`` は普通株のみ
        を保つため、優先株は ``nasdaq``/``exchanges`` には入れず ``preferred`` に分離する。

    Parameters
    ----------
    rics : list[str]
        RIC のリスト（``<news:stock_tickers>`` 由来）。

    Returns
    -------
    RicConversion
        分類結果。``exchanges`` は ``nasdaq``（普通株）と同順・同数の上場市場名。

    Examples
    --------
    >>> conv = convert_rics(["AAPL.O", ".SPX", "BFb.N", "AAM_pa.N"])
    >>> conv.nasdaq
    ['AAPL', 'BF.B']
    >>> conv.preferred
    ['AAM.A']
    >>> conv.nonus
    ['.SPX']
    """
    out = RicConversion()
    for ric in rics:
        if ric.startswith(".") or ric.endswith("=") or _FUTURE_RE.search(ric):  # 指数
            out.nonus.append(ric)
        elif "." in ric:
            suffix = ric.split(".")[-1]
            if suffix in US_EQUITY_SUFFIXES:  # 米株
                root = ric.split(".", maxsplit=1)[0]
                # 優先株判定はクラス株判定より先に行う（AAM_pa を BF.B 規則で誤変換させない）
                if _PREFERRED_RE.match(root):  # 優先株（best-effort・近似）
                    out.preferred.append(_ric_to_preferred(ric))
                else:  # 普通株（クラス株含む）
                    out.nasdaq.append(_ric_to_nasdaq(ric))
                    out.exchanges.append(SUFFIX_EXCHANGE.get(suffix, suffix))
            elif suffix == "UL":  # Reuters 非上場
                out.dropped.append(ric)
            else:  # 国際株
                out.nonus.append(ric)
        else:  # サフィックスなし（Reuters 固有等）
            out.nonus.append(ric)
    return out


# ============================================================
# 純関数: Article へのマップ
# ============================================================
def entry_to_article(entry: SitemapEntry) -> Article:
    """``SitemapEntry`` を :class:`Article` へマップする（mode A: 本文なし）.

    ``ticker`` には :func:`convert_rics` の NASDAQ 普通株ティッカー（複数はカンマ区切り）
    を、``category`` には subsection（なければ section）を格納する。優先株は ``ticker`` に
    含めず ``metadata.rics_preferred`` にのみ best-effort で保持する。本文 ``content`` は
    mode A では取得しないため空文字。``article_id`` は重複排除キーとして ``loc`` を使う。
    元 RIC や非米株 RIC・上場市場等の補助情報は ``metadata`` に保持する。

    Parameters
    ----------
    entry : SitemapEntry
        サイトマップから抽出した記事メタデータ。

    Returns
    -------
    Article
        マップ済み記事（``source="reuters"``、``content=""``）。

    Examples
    --------
    >>> entry = SitemapEntry(loc="https://www.reuters.com/business/x/", title="t")
    >>> article = entry_to_article(entry)
    >>> article.source
    'reuters'
    """
    conv = convert_rics(entry.rics_raw)
    return Article(
        title=entry.title,
        url=entry.loc,
        published=entry.pub_date,
        summary="",  # サイトマップに要約はない
        category=entry.subsection or entry.section,
        source=REUTERS_SOURCE,
        content="",  # mode A は本文を取得しない
        ticker=",".join(conv.nasdaq),  # NASDAQ ティッカー
        author="",
        article_id=entry.loc,  # mode A の重複排除キーは URL
        metadata={
            "section": entry.section,
            "subsection": entry.subsection,
            "language": entry.language,
            "sitemap_lang_tag": entry.lang_tag,
            "rics_raw": entry.rics_raw,
            "rics_nasdaq": conv.nasdaq,
            "listing_exchanges": conv.exchanges,
            "rics_preferred": conv.preferred,
            "rics_nonus": conv.nonus,
            "rics_dropped": conv.dropped,
            "keywords": entry.keywords,
            "lastmod": entry.lastmod,
        },
    )


# ============================================================
# 純関数: 分析時フィルタ
# ============================================================
def filter_articles(
    df: pd.DataFrame,
    lang: str = "all",
    sections: set[str] | None = None,
    exclude_sections: set[str] | None = None,
) -> pd.DataFrame:
    """保存済み全件データを言語 / カテゴリで絞り込む（分析時フィルタ）.

    収集（:func:`collect_reuters_news`）は無フィルタ全件保存するため、言語 / カテゴリの
    絞り込みは本関数（分析段階）で行う。保存データに付与済みの ``language`` /
    ``section`` / ``subsection`` 列を使う。``sections`` は section 粒度（``business``）でも
    subsection 粒度（``business/energy``）でも OR マッチする。

    Parameters
    ----------
    df : pd.DataFrame
        :func:`collect_reuters_news` が返した全件データ。
    lang : str
        言語コード（``en`` / ``es`` ...）。``"all"`` で言語フィルタなし。
    sections : set[str] | None
        含めるカテゴリ集合（section / subsection 両粒度を OR マッチ）。
        None でカテゴリ include フィルタなし。
    exclude_sections : set[str] | None
        除外するカテゴリ集合（section / subsection 両粒度を OR マッチ）。
        None で除外なし。

    Returns
    -------
    pd.DataFrame
        フィルタ後のデータフレーム（入力の部分集合）。

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame(
    ...     [{"language": "en", "section": "business", "subsection": "business/x"}]
    ... )
    >>> len(filter_articles(df, lang="en"))
    1
    """
    if df.empty:
        # 列が無い空 DataFrame でも安全に空を返す（収集 0 件のケース）
        return df

    out = df
    if lang and lang != "all":
        out = out.loc[out["language"] == lang]
    if sections:
        section_list = list(sections)
        out = out.loc[
            out["section"].isin(section_list) | out["subsection"].isin(section_list)
        ]
    if exclude_sections:
        exclude_list = list(exclude_sections)
        out = out.loc[
            ~(out["section"].isin(exclude_list) | out["subsection"].isin(exclude_list))
        ]
    return cast("pd.DataFrame", out)


# ============================================================
# 純関数: NASDAQ ディレクトリ照合バリデーション
# ============================================================
def validate_nasdaq_tickers(
    df: pd.DataFrame,
    directory: set[str],
) -> pd.DataFrame:
    """変換済み NASDAQ ティッカーを公式ディレクトリと照合する（純関数・I/O なし、設計書 §6 Phase 4）.

    各行の ``metadata.rics_nasdaq`` を ``directory``（:func:`load_nasdaq_directory` の
    返り値）と照合し、実在するティッカーを ``nasdaq_matched``、未一致を
    ``nasdaq_unmatched`` 列（いずれも ``list[str]``）として付与した **新しい**
    ``DataFrame`` を返す（入力 ``df`` は破壊しない）。未一致は上場廃止 / 改名 / M&A /
    上場前 / 優先株近似等で発生しうる（設計書 §9.4 実測 実在率 93.4%）。

    Parameters
    ----------
    df : pd.DataFrame
        :func:`collect_reuters_news` が返した全件データ（``metadata`` 列を持つ）。
    directory : set[str]
        NASDAQ 公式シンボル集合（:func:`load_nasdaq_directory`）。

    Returns
    -------
    pd.DataFrame
        ``nasdaq_matched`` / ``nasdaq_unmatched`` 列を付与した新 DataFrame。
        入力が空のときは入力をそのまま返す（空 DF ガード）。

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame([{"metadata": {"rics_nasdaq": ["AAPL", "DELISTED"]}}])
    >>> out = validate_nasdaq_tickers(df, {"AAPL"})
    >>> out.iloc[0]["nasdaq_matched"]
    ['AAPL']
    >>> out.iloc[0]["nasdaq_unmatched"]
    ['DELISTED']
    """
    if df.empty:
        # 列が無い空 DataFrame でも安全に空を返す（収集 0 件のケース）
        return df

    out = df.copy()

    def _matched(meta: object) -> list[str]:
        tickers = meta.get("rics_nasdaq", []) if isinstance(meta, dict) else []
        return [t for t in tickers if t in directory]

    def _unmatched(meta: object) -> list[str]:
        tickers = meta.get("rics_nasdaq", []) if isinstance(meta, dict) else []
        return [t for t in tickers if t not in directory]

    out["nasdaq_matched"] = out["metadata"].apply(_matched)
    out["nasdaq_unmatched"] = out["metadata"].apply(_unmatched)
    logger.debug(
        "Validated NASDAQ tickers", rows=len(out), directory_size=len(directory)
    )
    return out


# ============================================================
# I/O: サイトマップ取得
# ============================================================
def _fetch_text(session: requests.Session, url: str, timeout: int = 30) -> str | None:
    """URL を GET してテキストを返す（最終失敗時は None）.

    ``retry.py`` の確立パターンに従い、内部の GET を :func:`create_retry_decorator`
    でデコレートして指数バックオフ・リトライする。非 200 応答は
    :func:`classify_http_error` で分類し、リトライ可能なエラー（429 /
    5xx → :class:`RetryableError`）は最大 3 回まで再試行、リトライ不可のエラー
    （403 / 404 / 401 等 → :class:`PermanentError`）は即座に送出する。

    **外部契約**: 最終的に失敗（リトライ上限到達 / PermanentError / 接続例外）した
    場合は例外を握りつぶして ``None`` を返す。呼び出し側
    （:func:`collect_reuters_news`）は該当ページをスキップできる。

    Parameters
    ----------
    session : requests.Session
        curl_cffi セッション。
    url : str
        取得対象 URL。
    timeout : int
        タイムアウト秒数。

    Returns
    -------
    str | None
        レスポンステキスト。最終失敗時は None。
    """

    @_fetch_retry
    def _do_fetch() -> str:
        resp = session.get(url, timeout=timeout)
        if resp.status_code != 200:
            # 429/5xx は RetryableError でリトライ、403/404 等は PermanentError で即送出
            raise classify_http_error(resp.status_code, resp)
        return resp.text

    try:
        return _do_fetch()
    except ScraperError as e:
        logger.warning(
            "Fetch failed (giving up)",
            url=url,
            status=getattr(e, "status_code", None),
            error=str(e),
        )
        return None
    except Exception as e:
        logger.error("Fetch failed (unexpected)", url=url, error=str(e))
        return None


def fetch_sitemap_index(session: requests.Session, limit: int) -> list[str]:
    """news-sitemap-index からサブサイトマップ URL を取得する（先頭 ``limit`` 件）.

    Parameters
    ----------
    session : requests.Session
        curl_cffi セッション（``create_session`` で作成）。
    limit : int
        取得するサブサイトマップ URL の最大件数。

    Returns
    -------
    list[str]
        サブサイトマップ URL のリスト（取得失敗時は空リスト）。

    Examples
    --------
    >>> from news_scraper.session import create_session
    >>> session = create_session()
    >>> urls = fetch_sitemap_index(session, limit=3)  # doctest: +SKIP
    """
    xml = _fetch_text(session, REUTERS_NEWS_SITEMAP_INDEX)
    if not xml:
        return []

    root = ET.fromstring(xml.encode("utf-8"))  # nosec B314
    locs = [el.text for el in root.findall(".//s:sitemap/s:loc", SITEMAP_NS) if el.text]
    logger.info(
        "Sitemap index parsed",
        total_subs=len(locs),
        using=min(limit, len(locs)),
    )
    return locs[:limit]


def load_nasdaq_directory(session: requests.Session) -> set[str]:
    """NASDAQ 公式シンボルディレクトリを取得してティッカー集合を返す（設計書 §6 Phase 4）.

    ``nasdaqlisted.txt`` / ``otherlisted.txt`` を :func:`_fetch_text` で取得し、
    パイプ区切りをパースする。``nasdaqlisted`` は col0（Symbol）、``otherlisted`` は
    col0（ACT Symbol）＋ col7（NASDAQ Symbol、存在時）を集合へ追加する。各ファイルの
    ヘッダ行と ``File Creation Time`` フッタ行はスキップする。取得失敗時は当該ファイル分を
    空として扱う（両方失敗なら空集合）。

    Parameters
    ----------
    session : requests.Session
        curl_cffi セッション（``create_session`` で作成）。

    Returns
    -------
    set[str]
        NASDAQ 公式シンボル集合。:func:`validate_nasdaq_tickers` の照合対象。

    Examples
    --------
    >>> from news_scraper.session import create_session
    >>> session = create_session()
    >>> directory = load_nasdaq_directory(session)  # doctest: +SKIP
    """
    symbols: set[str] = set()

    listed = _fetch_text(session, NASDAQ_LISTED_URL)
    if listed:
        for line in listed.splitlines()[1:]:  # ヘッダ行をスキップ
            if line.startswith("File Creation Time"):
                continue
            cols = line.split("|")
            if cols and cols[0]:
                symbols.add(cols[0])  # Symbol

    other = _fetch_text(session, NASDAQ_OTHER_LISTED_URL)
    if other:
        for line in other.splitlines()[1:]:  # ヘッダ行をスキップ
            if line.startswith("File Creation Time"):
                continue
            cols = line.split("|")
            if cols and cols[0]:
                symbols.add(cols[0])  # ACT Symbol
                if len(cols) >= 8 and cols[7]:
                    symbols.add(cols[7])  # NASDAQ Symbol

    logger.info("NASDAQ directory loaded", symbols=len(symbols))
    return symbols


# ============================================================
# I/O: 収集オーケストレーション
# ============================================================
def collect_reuters_news(
    config: ScraperConfig | None = None,
    pages: int = 86,
    since: str | None = None,
) -> pd.DataFrame:
    """Reuters mode A 収集（無フィルタ全件保存）を実行する.

    **取得時は言語 / カテゴリで一切フィルタせず、スクレイピング可能な全件を返す**
    （raw レイヤー、設計書 §3.0 / §9）。言語 / section / subsection は列・metadata として
    全件に付与し、絞り込みは分析段階（:func:`filter_articles`）で行う。``since`` は増分の
    収集範囲制御のみ（内容フィルタではない）。重複排除キーは ``loc``。

    Parameters
    ----------
    config : ScraperConfig | None
        スクレイパー設定（None でデフォルト）。``delay`` / ``jitter`` でレート制御。
    pages : int
        取得するサブサイトマップ数（news-sitemap は全 86。全件保存なら 86）。
    since : str | None
        増分収集用。``pub_date >= YYYY-MM-DD`` の記事のみ取得（収集範囲制御）。
        None なら直近約 48h 全件。

    Returns
    -------
    pd.DataFrame
        収集結果（無フィルタ全件）。列は Article 11 列 +
        ``language`` / ``section`` / ``subsection`` の計 14 列。取得失敗時は空。

    Examples
    --------
    >>> df = collect_reuters_news(pages=3)  # doctest: +SKIP
    >>> sorted(df.columns)  # doctest: +SKIP
    """
    if config is None:
        config = ScraperConfig()

    logger.info(
        "Reuters mode A collect start (no content filter)",
        pages=pages,
        since=since,
    )

    session = create_session(impersonate=config.impersonate, proxy=config.proxy)

    sub_urls = fetch_sitemap_index(session, limit=pages)
    if not sub_urls:
        logger.error("No sitemap sub-URLs obtained (blocked?)")
        return pd.DataFrame()

    all_entries: list[SitemapEntry] = []
    for i, url in enumerate(sub_urls):
        time.sleep(get_delay(config))
        xml = _fetch_text(session, url, timeout=config.timeout)
        if not xml:
            continue
        entries = parse_sitemap_xml(xml)
        all_entries.extend(entries)
        logger.info("Sub-sitemap parsed", page=i, entries=len(entries))

    # 増分収集の範囲制御のみ（言語 / カテゴリは収集時にフィルタしない）
    if since:
        before = len(all_entries)
        all_entries = [
            e for e in all_entries if e.pub_date and e.pub_date[:10] >= since
        ]
        logger.info(
            "Incremental range",
            since=since,
            kept=len(all_entries),
            dropped=before - len(all_entries),
        )

    # 重複排除（loc）
    unique_entries = _dedupe_by_loc(all_entries)

    articles = [entry_to_article(e) for e in unique_entries]

    # 分析時フィルタ用に language / section / subsection を列へ昇格（全件・無フィルタ）。
    # 収集 0 件でも Article 11 列 + 言語系 3 列の計 14 列を保証する。
    if not articles:
        empty_columns = (*_ARTICLE_COLUMNS, "language", "section", "subsection")
        logger.info("Reuters mode A collect completed", rows=0)
        return pd.DataFrame({col: pd.Series(dtype="object") for col in empty_columns})

    df = pd.DataFrame([a.to_dict() for a in articles])
    df["language"] = df["metadata"].apply(lambda m: m.get("language", ""))
    df["section"] = df["metadata"].apply(lambda m: m.get("section", ""))
    df["subsection"] = df["metadata"].apply(lambda m: m.get("subsection", ""))

    logger.info("Reuters mode A collect completed", rows=len(df))
    return df


def _dedupe_by_loc(entries: list[SitemapEntry]) -> list[SitemapEntry]:
    """loc をキーに ``SitemapEntry`` を重複排除する（初出を保持）.

    Parameters
    ----------
    entries : list[SitemapEntry]
        重複を含みうるエントリのリスト。

    Returns
    -------
    list[SitemapEntry]
        loc が一意なエントリのリスト（入力順を保持）。
    """
    seen: set[str] = set()
    unique: list[SitemapEntry] = []
    for e in entries:
        if e.loc not in seen:
            seen.add(e.loc)
            unique.append(e)
    return unique


# ============================================================
# I/O: 永続化
# ============================================================
def save_reuters_news(
    df: pd.DataFrame,
    base_dir: Path = _DEFAULT_BASE_DIR,
) -> Path:
    """収集した Reuters ニュースを日付別 parquet に保存する.

    ``{base_dir}/{YYYY-MM-DD}/reuters_{timestamp}.parquet`` に保存し、必要な
    ディレクトリを生成する。``metadata`` 列（dict / list を含む）は parquet が空構造体を
    書き込めないため文字列化して保存する（``nasdaq._save_articles_by_date`` と同じ対応）。

    Parameters
    ----------
    df : pd.DataFrame
        :func:`collect_reuters_news` が返した全件データ。
    base_dir : Path
        保存ベースディレクトリ（デフォルト ``data/raw/news/reuters``）。

    Returns
    -------
    Path
        保存した parquet ファイルのパス。

    Examples
    --------
    >>> import pandas as pd
    >>> df = collect_reuters_news()  # doctest: +SKIP
    >>> save_reuters_news(df)  # doctest: +SKIP
    """
    now = datetime.now()
    date_dir = base_dir / now.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    timestamp = now.strftime("%Y%m%d_%H%M%S")
    path = date_dir / f"reuters_{timestamp}.parquet"

    # metadata（dict / list）は pyarrow が空構造体を書き込めないため文字列化する。
    df_to_save = df.copy()
    if "metadata" in df_to_save.columns:
        df_to_save["metadata"] = df_to_save["metadata"].apply(
            lambda v: str(v) if isinstance(v, (dict, list)) else v
        )

    df_to_save.to_parquet(path, index=False)
    logger.info("Saved Reuters news (full, unfiltered)", rows=len(df), path=str(path))
    return path
