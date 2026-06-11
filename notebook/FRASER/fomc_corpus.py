"""FOMC 4種文書（声明文・記者会見・Minutes・Beige Book）のヒストリカル取得.

FRASER title 677（FOMC Meeting Minutes, Transcripts, and Other Documents、
1933年〜現在、約1,040 item）から、ファイル名規約ベースで4種の文書を分類し、
プレーンテキスト（.txt）を一括ダウンロードする。

分類ルールは2026-06-10に全1,038 item・7,338ファイルの全数調査で導出・検証済み。
年次カウントが歴史的事実と一致することを確認している:
- statement:        1994年〜（1994-98年は政策変更時のみ、1999年5月から毎会合）
- minutes:          1993年〜（現代版Minutes。それ以前のMoA/RoPA/MoD等は対象外）
- press_conference: 2011年4月〜（2018年まで四半期会合のみ、2019年から毎会合）
- beige_book:       1983年〜（公開版）
- redbook:          1970-1983年（Beige Bookの非公開時代の前身。参考用に分類）

Point-in-Time 注意:
- doc_date はファイル名に埋め込まれた文書日付。
  - statement / press_conference: 公表日と同じ（会合最終日）
  - beige_book: 公表日（会合の約2週間前）
  - minutes: 会合最終日。公表日は 2004-12-14会合分以降=会合+3週間、
    それ以前（1993〜2004-11）=次回会合の3日後（6-8週遅れ）。
- `poit` サブコマンドで release_date 列を追加できる（add_release_dates 参照）。
- press_conference のFRASERテキストは直近分が「PRELIMINARY（冒頭発言のみ、
  語数 < 3000）」のため分析には使用しない。完全版（Q&A込み）は
  `download-presconf-pdf` でfederalreserve.gov公式PDFを全件取得し、
  PDFから抽出したテキストを正とする（抽出は別工程）。

使い方:
    export FRASER_API_KEY=...  # または .env に記載
    uv run python notebook/FRASER/fomc_corpus.py inventory
    uv run python notebook/FRASER/fomc_corpus.py download --types statement,minutes
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import time
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("fomc_corpus")

BASE_URL = "https://fraser.stlouisfed.org/api"
TITLE_ID = 677
USER_AGENT = "Mozilla/5.0 (quants research; contact: youxitiancore@gmail.com)"
API_SLEEP_SEC = 2.1  # レート制限 30 req/min
DOWNLOAD_SLEEP_SEC = 0.5  # テキスト取得はAPI制限対象外だが礼儀として

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
INVENTORY_PATH = DATA_DIR / "fomc_inventory.csv"
TEXT_DIR = DATA_DIR / "texts"
PDF_DIR = DATA_DIR / "pdfs"

# 議長記者会見トランスクリプト完全版（Q&A込み）のFRB公式PDF。
# 2011-04-27（初回）〜直近まで全件この形式で存在することを確認済み（2026-06-11）。
# FRASERのpress_conferenceテキストは直近分がPRELIMINARY版のため、
# このPDFから抽出したテキストを正とする（dec-2026-06-11-001）。
FED_PRESCONF_PDF_URL = (
    "https://www.federalreserve.gov/mediacenter/files/FOMCpresconf{ymd}.pdf"
)

# 4種文書の分類ルール（拡張子を除いたファイル名に適用）
# 順序に意味あり: 最初にマッチしたルールを採用
CLASSIFY_RULES: list[tuple[str, re.Pattern[str]]] = [
    # --- Beige Book（公開版 1983〜） ---
    ("beige_book", re.compile(r"^beigebook_(\d{8})$", re.I)),  # 2012-現在
    ("beige_book", re.compile(r"^fullreport(\d{8})$")),  # 2009-2012
    ("beige_book", re.compile(r"^(\d{8})beigebook$")),  # 2003-2007
    ("beige_book", re.compile(r"^(\d{8})beige$")),  # 2008
    ("beige_book", re.compile(r"^fomc\d{8}beige(\d{8})$")),  # 1983-2002
    # --- Redbook（Beige Book前身、当時非公開 1970-1983） ---
    ("redbook", re.compile(r"^fomc\d{8}redbook(\d{8})$")),
    # --- FOMC声明文（1994〜） ---
    ("statement", re.compile(r"^(\d{8})statement$")),  # 1994-2019
    ("statement", re.compile(r"^monetary(\d{8})a\d$")),  # 2019-現在
    # --- Minutes 現代版（1993〜） ---
    ("minutes", re.compile(r"^(\d{8})min$")),  # 1993-2007
    ("minutes", re.compile(r"^fomcminutes(\d{8})$")),  # 2007-現在
    # --- 議長記者会見（2011年4月〜） ---
    # _final / -final / _f は後日差し替えられた完全版の命名
    ("press_conference", re.compile(r"^fomcpresconf(\d{8})([-_](final|f))?$", re.I)),
]

DOC_TYPES = ("statement", "minutes", "press_conference", "beige_book", "redbook")


def classify_filename(filename: str) -> tuple[str, str] | None:
    """ファイル名を4種文書に分類し (doc_type, doc_date) を返す.

    Parameters
    ----------
    filename : str
        textUrl末尾のファイル名（例: "fomcminutes20260429.txt"）

    Returns
    -------
    tuple[str, str] | None
        (doc_type, doc_date "YYYY-MM-DD")。対象外ファイルは None。
    """
    base = filename.rsplit(".", 1)[0]
    for doc_type, rx in CLASSIFY_RULES:
        m = rx.match(base)
        if m:
            d = m.group(1)
            doc_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
            return doc_type, doc_date
    return None


def fetch_items(api_key: str) -> list[dict]:
    """title 677 の全itemレコードをAPIから取得する."""
    headers = {"X-API-Key": api_key, "User-Agent": USER_AGENT}
    records: list[dict] = []
    page = 1
    while True:
        url = f"{BASE_URL}/title/{TITLE_ID}/items"
        resp = requests.get(
            url, headers=headers, params={"limit": 100, "page": page}, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("records", [])
        records.extend(batch)
        total = data.get("total", 0)
        logger.info("fetched page %d (%d/%d items)", page, len(records), total)
        if len(records) >= total or not batch:
            break
        page += 1
        time.sleep(API_SLEEP_SEC)
    return records


def build_inventory(items: list[dict]) -> list[dict]:
    """itemレコード群から4種文書のインベントリ行を構築する."""
    rows = []
    for r in items:
        item_id = r["recordInfo"]["recordIdentifier"][0]
        meeting_date = r.get("originInfo", {}).get("sortDate", "")
        meeting_title = r["titleInfo"][0]["title"]
        loc = r.get("location", {})
        text_urls = loc.get("textUrl", [])
        pdf_by_base = {
            u.rsplit("/", 1)[-1].rsplit(".", 1)[0]: u for u in loc.get("pdfUrl", [])
        }
        for url in text_urls:
            filename = url.rsplit("/", 1)[-1]
            result = classify_filename(filename)
            if result is None:
                continue
            doc_type, doc_date = result
            base = filename.rsplit(".", 1)[0]
            rows.append(
                {
                    "item_id": item_id,
                    "meeting_date": meeting_date,
                    "meeting_title": meeting_title,
                    "doc_type": doc_type,
                    "doc_date": doc_date,
                    "filename": filename,
                    "text_url": url,
                    "pdf_url": pdf_by_base.get(base, ""),
                }
            )
    rows.sort(key=lambda x: (x["doc_type"], x["doc_date"]))
    logger.info("inventory built: %d files", len(rows))
    for dt in DOC_TYPES:
        n = sum(1 for x in rows if x["doc_type"] == dt)
        dates = [x["doc_date"] for x in rows if x["doc_type"] == dt]
        if dates:
            logger.info("  %-18s %4d files  %s 〜 %s", dt, n, min(dates), max(dates))
    return rows


def save_inventory(rows: list[dict], path: Path = INVENTORY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    logger.info("saved inventory: %s", path)


def load_inventory(path: Path = INVENTORY_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# Minutes 迅速公表（会合最終日+3週間）の開始会合。
# FRBは2004-12-14会合分からexpedited release（+3週）を適用
# （同会合のMinutesは2005-01-04公表 = ちょうど+21日）。
# それ以前（1993〜2004-11）は「次回会合の約3日後」に公表。
MINUTES_EXPEDITED_START = date(2004, 12, 14)


def _roll_forward_weekend(d: date) -> date:
    """土日着地を翌月曜にロールする（FRBは週末に公表しない。PoiT保守側）."""
    if d.weekday() == 5:  # Sat
        return d + timedelta(days=2)
    if d.weekday() == 6:  # Sun
        return d + timedelta(days=1)
    return d


def add_release_dates(rows: list[dict]) -> list[dict]:
    """各行に Point-in-Time 用の release_date 列を追加する.

    変換ルール:
    - statement / press_conference / beige_book / redbook:
      doc_date がそのまま公表日（モジュールdocstring参照）→ release_date = doc_date
    - minutes: doc_date は会合最終日のため変換が必要。
      - doc_date >= 2004-12-14: 会合最終日 + 21日（expedited release）
      - 1993〜2004-11: 次回会合の会合最終日 + 3日（旧方針、6-8週遅れ）
      計算結果が土日の場合は翌月曜にロール。

    注意: 2020年COVID臨時会合等、実際の公表が数日ずれた例外が稀にある
    （例: 2020-03-15会合分の実公表は2020-04-08、本計算では2020-04-06）。
    厳密なイベントスタディには実公表日の個別確認を推奨。
    """
    minutes_dates = sorted(
        {date.fromisoformat(r["doc_date"]) for r in rows if r["doc_type"] == "minutes"}
    )

    def next_meeting(d: date) -> date | None:
        for m in minutes_dates:
            if m > d:
                return m
        return None

    for r in rows:
        doc_date = date.fromisoformat(r["doc_date"])
        if r["doc_type"] != "minutes":
            r["release_date"] = r["doc_date"]
            continue
        if doc_date >= MINUTES_EXPEDITED_START:
            release = doc_date + timedelta(days=21)
        else:
            nxt = next_meeting(doc_date)
            if nxt is None:
                # 次回会合が未開催（通常は発生しない: 旧方針期間は1993-2004のみ）
                logger.warning("no next meeting for minutes %s", r["doc_date"])
                r["release_date"] = ""
                continue
            release = nxt + timedelta(days=3)
        r["release_date"] = _roll_forward_weekend(release).isoformat()

    n_minutes = sum(1 for r in rows if r["doc_type"] == "minutes")
    n_old = sum(
        1
        for r in rows
        if r["doc_type"] == "minutes"
        and date.fromisoformat(r["doc_date"]) < MINUTES_EXPEDITED_START
    )
    logger.info(
        "release_date added: %d rows (minutes %d: old-policy %d / expedited %d)",
        len(rows),
        n_minutes,
        n_old,
        n_minutes - n_old,
    )
    return rows


def download_texts(
    rows: list[dict],
    doc_types: tuple[str, ...] = (
        "statement",
        "minutes",
        "press_conference",
        "beige_book",
    ),
    out_dir: Path = TEXT_DIR,
) -> dict[str, int]:
    """インベントリの指定doc_typeのテキストをダウンロードする（取得済みはスキップ）.

    保存先: out_dir/{doc_type}/{doc_date}_{filename}
    """
    headers = {"User-Agent": USER_AGENT}
    stats = {"downloaded": 0, "skipped": 0, "failed": 0}
    targets = [r for r in rows if r["doc_type"] in doc_types]
    logger.info("download targets: %d files (types=%s)", len(targets), doc_types)
    for r in targets:
        dest_dir = out_dir / r["doc_type"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{r['doc_date']}_{r['filename']}"
        if dest.exists() and dest.stat().st_size > 0:
            stats["skipped"] += 1
            continue
        try:
            resp = requests.get(r["text_url"], headers=headers, timeout=60)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            stats["downloaded"] += 1
            logger.info("downloaded %s (%d bytes)", dest.name, len(resp.content))
        except requests.RequestException as e:
            stats["failed"] += 1
            logger.error("failed %s: %s", r["text_url"], e)
        time.sleep(DOWNLOAD_SLEEP_SEC)
    logger.info("download done: %s", stats)
    return stats


def download_presconf_pdfs(rows: list[dict], out_dir: Path = PDF_DIR) -> dict[str, int]:
    """全記者会見の完全版トランスクリプトPDFをfederalreserve.govから取得する.

    インベントリの press_conference 行から会見日を抽出し、
    FED_PRESCONF_PDF_URL 形式のPDFを一括ダウンロードする（取得済みはスキップ）。
    保存先: out_dir/press_conference/{doc_date}_FOMCpresconf{YYYYMMDD}.pdf

    レスポンスが %PDF で始まらない場合（エラーページ等）は保存せず failed 扱い。
    テキスト抽出は別工程（act-2026-06-11-002）で行う。
    """
    headers = {"User-Agent": USER_AGENT}
    stats = {"downloaded": 0, "skipped": 0, "failed": 0}
    dates = sorted({r["doc_date"] for r in rows if r["doc_type"] == "press_conference"})
    dest_dir = out_dir / "press_conference"
    dest_dir.mkdir(parents=True, exist_ok=True)
    logger.info("presconf pdf targets: %d meetings", len(dates))
    for doc_date in dates:
        ymd = doc_date.replace("-", "")
        url = FED_PRESCONF_PDF_URL.format(ymd=ymd)
        dest = dest_dir / f"{doc_date}_FOMCpresconf{ymd}.pdf"
        if dest.exists() and dest.stat().st_size > 0:
            stats["skipped"] += 1
            continue
        try:
            resp = requests.get(url, headers=headers, timeout=60)
            resp.raise_for_status()
            if not resp.content.startswith(b"%PDF"):
                stats["failed"] += 1
                logger.error("not a PDF (got %d bytes): %s", len(resp.content), url)
                continue
            dest.write_bytes(resp.content)
            stats["downloaded"] += 1
            logger.info("downloaded %s (%d bytes)", dest.name, len(resp.content))
        except requests.RequestException as e:
            stats["failed"] += 1
            logger.error("failed %s: %s", url, e)
        time.sleep(DOWNLOAD_SLEEP_SEC)
    logger.info("presconf pdf download done: %s", stats)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory", help="API経由でitem一覧を取得しインベントリCSVを更新")
    p_dl = sub.add_parser("download", help="インベントリに基づきテキストをダウンロード")
    p_dl.add_argument(
        "--types",
        default="statement,minutes,press_conference,beige_book",
        help="対象doc_type（カンマ区切り。redbookも指定可）",
    )
    sub.add_parser(
        "poit", help="インベントリにrelease_date列を追加（Point-in-Time変換）"
    )
    sub.add_parser(
        "download-presconf-pdf",
        help="全記者会見の完全版PDFをfederalreserve.govから一括取得",
    )
    args = parser.parse_args()

    load_dotenv(SCRIPT_DIR.parent.parent / ".env")

    if args.command == "inventory":
        api_key = os.getenv("FRASER_API_KEY")
        if not api_key:
            raise SystemExit("FRASER_API_KEY not set. Add it to .env or environment.")
        items = fetch_items(api_key)
        rows = build_inventory(items)
        save_inventory(rows)
    elif args.command == "download":
        rows = load_inventory()
        doc_types = tuple(t.strip() for t in args.types.split(","))
        unknown = set(doc_types) - set(DOC_TYPES)
        if unknown:
            raise SystemExit(f"unknown doc_type: {unknown}. valid: {DOC_TYPES}")
        download_texts(rows, doc_types)
    elif args.command == "poit":
        rows = load_inventory()
        rows = add_release_dates(rows)
        save_inventory(rows)
    elif args.command == "download-presconf-pdf":
        rows = load_inventory()
        download_presconf_pdfs(rows)


if __name__ == "__main__":
    main()
