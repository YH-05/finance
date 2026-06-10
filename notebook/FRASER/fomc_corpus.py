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
  - minutes: 会合最終日。公表日は 2005年以降=会合+3週間、
    1993-2004年=次回会合の3日後（6-8週遅れ）。バックテストでは要変換。
- 直近の press_conference は「PRELIMINARY（冒頭発言のみ）」のことがある。
  完全版（Q&A込み）への差し替えはFRASER側で後日行われる。
  目安: 語数 < 3000 なら暫定版。

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


def download_texts(
    rows: list[dict],
    doc_types: tuple[str, ...] = ("statement", "minutes", "press_conference", "beige_book"),
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


if __name__ == "__main__":
    main()
