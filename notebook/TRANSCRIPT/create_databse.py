"""create_database.py"""

import json
import re
import sqlite3
from pathlib import Path

from tqdm import tqdm

# ========================================
# スキーマ定義（埋め込み）
# ========================================
SCHEMA_SQL = """
-- 銘柄マスタ
CREATE TABLE IF NOT EXISTS tickers (
    ticker          TEXT PRIMARY KEY,
    company_name    TEXT NOT NULL,
    country         TEXT,
    exchange        TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- トランスクリプト本体
CREATE TABLE IF NOT EXISTS documents (
    document_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT NOT NULL,
    date            DATE NOT NULL,
    title           TEXT NOT NULL,
    document_type   TEXT NOT NULL,
    period_type     TEXT,
    fiscal_year     INTEGER,
    fiscal_quarter  INTEGER,
    quarter_label   TEXT,
    event_name      TEXT,
    language        TEXT DEFAULT 'en',
    source_file     TEXT,
    raw_body        TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker) REFERENCES tickers(ticker),
    UNIQUE(ticker, date, title)
);

CREATE INDEX IF NOT EXISTS idx_documents_ticker        ON documents(ticker);
CREATE INDEX IF NOT EXISTS idx_documents_date          ON documents(date);
CREATE INDEX IF NOT EXISTS idx_documents_type          ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_ticker_type   ON documents(ticker, document_type);
CREATE INDEX IF NOT EXISTS idx_documents_ticker_date   ON documents(ticker, date);
CREATE INDEX IF NOT EXISTS idx_documents_fiscal        ON documents(ticker, fiscal_year, fiscal_quarter);

-- 参加者
CREATE TABLE IF NOT EXISTS participants (
    participant_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     INTEGER NOT NULL,
    name            TEXT NOT NULL,
    role            TEXT NOT NULL,
    title           TEXT,
    firm            TEXT,
    bio_id          TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_participants_doc  ON participants(document_id);
CREATE INDEX IF NOT EXISTS idx_participants_name ON participants(name);
CREATE INDEX IF NOT EXISTS idx_participants_firm ON participants(firm);

-- 発言
CREATE TABLE IF NOT EXISTS speeches (
    speech_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     INTEGER NOT NULL,
    seq             INTEGER NOT NULL,
    speaker         TEXT NOT NULL,
    role            TEXT,
    section         TEXT,
    text            TEXT NOT NULL,
    char_count      INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_speeches_doc      ON speeches(document_id);
CREATE INDEX IF NOT EXISTS idx_speeches_doc_seq  ON speeches(document_id, seq);
CREATE INDEX IF NOT EXISTS idx_speeches_speaker  ON speeches(speaker);
CREATE INDEX IF NOT EXISTS idx_speeches_role     ON speeches(role);

-- 全文検索
CREATE VIRTUAL TABLE IF NOT EXISTS speeches_fts USING fts5(
    text,
    speaker UNINDEXED,
    role UNINDEXED,
    content='speeches',
    content_rowid='speech_id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS speeches_ai AFTER INSERT ON speeches BEGIN
    INSERT INTO speeches_fts(rowid, text, speaker, role)
    VALUES (new.speech_id, new.text, new.speaker, new.role);
END;

CREATE TRIGGER IF NOT EXISTS speeches_ad AFTER DELETE ON speeches BEGIN
    DELETE FROM speeches_fts WHERE rowid = old.speech_id;
END;

CREATE TRIGGER IF NOT EXISTS speeches_au AFTER UPDATE ON speeches BEGIN
    UPDATE speeches_fts SET text=new.text WHERE rowid=new.speech_id;
END;
"""


def parse_quarter(quarter_str: str | None) -> tuple[int | None, int | None]:
    """'Q1 2023' -> (2023, 1) / 'Y 2023' -> (2023, None) / None -> (None, None)"""
    if not quarter_str:
        return None, None
    m = re.match(r"Q(\d)\s+(\d{4})", quarter_str)
    if m:
        return int(m.group(2)), int(m.group(1))
    m = re.match(r"Y\s+(\d{4})", quarter_str)
    if m:
        return int(m.group(1)), None
    return None, None


def detect_event_name(title: str, document_type: str) -> str | None:
    """カンファレンス系のイベント名を推定"""
    if document_type != "conference":
        return None
    if "WWDC" in title or "Worldwide Developers" in title:
        return "WWDC"
    if "iPhone Event" in title or "Special Event" in title:
        return "Product Event"
    return title  # そのまま


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA_SQL)
    return conn


def insert_document(conn: sqlite3.Connection, data: dict) -> int | None:
    """1つの transcript オブジェクトを挿入し、document_id を返す"""
    meta = data["metadata"]
    ticker = meta["ticker"]
    document_type = meta.get("document_type", "other")

    # tickers (UPSERT)
    conn.execute(
        """
        INSERT INTO tickers (ticker, company_name) VALUES (?, ?)
        ON CONFLICT(ticker) DO UPDATE SET company_name=excluded.company_name
    """,
        (ticker, meta["company"]),
    )

    # documents
    fiscal_year, fiscal_quarter = parse_quarter(meta.get("quarter"))
    source_file = Path(meta["source_file"]).name
    event_name = detect_event_name(meta["title"], document_type)

    try:
        cur = conn.execute(
            """
            INSERT INTO documents
                (ticker, date, title, document_type,
                    period_type, fiscal_year, fiscal_quarter, quarter_label,
                    event_name, language, source_file, raw_body)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ticker,
                meta["date"],
                meta["title"],
                document_type,
                meta.get("period_type"),
                fiscal_year,
                fiscal_quarter,
                meta.get("quarter"),
                event_name,
                meta.get("language", "en"),
                source_file,
                data.get("transcript_body"),
            ),
        )
        document_id = cur.lastrowid
    except sqlite3.IntegrityError:
        print(f"⚠️ 既存: {ticker} {meta['date']} {meta['title']}")
        return None

    # participants
    p_data = data.get("participants", {})
    for p in p_data.get("company_participants", []):
        conn.execute(
            """
            INSERT INTO participants (document_id, name, role, title, bio_id)
            VALUES (?, ?, 'company', ?, ?)
        """,
            (document_id, p["name"], p.get("title"), p.get("bio_id")),
        )

    for p in p_data.get("other_participants", []):
        conn.execute(
            """
            INSERT INTO participants (document_id, name, role, firm, bio_id)
            VALUES (?, ?, 'analyst', ?, ?)
        """,
            (document_id, p["name"], p.get("firm"), p.get("bio_id")),
        )

    # speeches
    speeches = [
        (
            document_id,
            seq,
            s["speaker"],
            s.get("role"),
            detect_section(s, document_type),
            s["text"],
            len(s["text"]),
        )
        for seq, s in enumerate(data.get("speeches", []))
    ]
    conn.executemany(
        """
        INSERT INTO speeches (document_id, seq, speaker, role, section, text, char_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        speeches,
    )

    return document_id


def detect_section(speech: dict, document_type: str) -> str | None:
    """Q&Aかpresentationか推定。カンファレンス系はNULL"""
    if document_type != "earnings":
        return None
    role = speech.get("role")
    if role == "analyst":
        return "qa"
    return "presentation"


def ingest_all(json_paths: list[str], db_path: str = "transcripts.db"):
    conn = init_db(db_path)
    for json_path in tqdm(json_paths, desc="Ingesting"):
        with open(json_path, "r", encoding="utf-8") as f:
            data_list = json.load(f)
        with conn:
            for data in data_list:
                insert_document(conn, data)
    conn.close()
    print("✅ 完了")
