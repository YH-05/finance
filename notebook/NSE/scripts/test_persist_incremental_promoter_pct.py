"""aggregate_owner_candidate() の promoter_total_pct 算出ロジックのテスト.

一部の XBRL 開示（新規上場企業等）では PromoterAndPromoterGroup の「総合計」行
（sub_category が空/NaN、または Indian/Foreign）が省略され、
DirectorsAndDirectorsRelatives 等の内訳行のみが存在するケースがある。
この場合 promoter_total_pct が誤って 0.0 になり、Stage1 閾値判定
（build_nifty750_universe.py の promoter_total_pct >= 10）に影響する。

参照実例: INDGN, IXIGO, FIRSTCRY, PINELABS, SAMHI
（notebook/NSE/data/cache/nse/nse_index_20260630.db で確認済み）
"""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_module(filename: str):
    spec = importlib.util.spec_from_file_location(
        filename.removesuffix(".py"), SCRIPTS_DIR / filename
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


persist_incremental = _load_module("persist_incremental.py")
persist_rev1_missing = _load_module("persist_rev1_missing.py")

SCHEMA = """
CREATE TABLE shareholding_detail (
    symbol TEXT,
    report_date TEXT,
    category TEXT,
    sub_category TEXT,
    shareholder_name TEXT,
    pan TEXT,
    num_shareholders INTEGER,
    num_fully_paid_shares INTEGER,
    num_voting_rights INTEGER,
    pct_total_shares REAL,
    pct_fully_diluted REAL,
    num_shares_demat INTEGER,
    is_category_total INTEGER,
    fetched_at TEXT
);
CREATE TABLE stocks (symbol TEXT, company_name TEXT, isin TEXT);
"""


def make_conn(rows: list[tuple]) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO shareholding_detail (symbol, report_date, category, sub_category, "
        "shareholder_name, pan, num_shareholders, num_fully_paid_shares, num_voting_rights, "
        "pct_total_shares, pct_fully_diluted, num_shares_demat, is_category_total, fetched_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    return conn


def row(
    symbol: str,
    sub_category: str | None,
    pct: float,
    is_total: int = 1,
    name: str = "TOTAL",
) -> tuple:
    return (
        symbol,
        "2026-03-31",
        "PromoterAndPromoterGroup",
        sub_category,
        name,
        "",
        1,
        0,
        0,
        pct,
        pct,
        0,
        is_total,
        "2026-07-15T00:00:00Z",
    )


@pytest.mark.parametrize(
    "module",
    [persist_incremental, persist_rev1_missing],
    ids=["persist_incremental", "persist_rev1_missing"],
)
class TestAggregateOwnerCandidatePromoterTotalPct:
    def test_正常系_総合計行がある場合はその値をpromoter_total_pctに使う(
        self, module
    ) -> None:
        conn = make_conn(
            [
                row("DUMMY", "", 55.0),
                row("DUMMY", "DirectorsAndDirectorsRelatives", 10.0),
            ]
        )
        result = module.aggregate_owner_candidate(conn, "DUMMY", "INE000A00000")
        assert result is not None
        assert result["promoter_total_pct"] == 55.0

    def test_異常系_総合計行が省略され内訳行のみの場合はnatural_pct_sumにフォールバックする(
        self, module
    ) -> None:
        # INDGN 実例を再現: 総合計行(sub_category='')が存在せず、
        # DirectorsAndDirectorsRelatives=21.04 + KeyManagerialPersonnel=0.38 のみ
        conn = make_conn(
            [
                row("INDGN", "DirectorsAndDirectorsRelatives", 21.04),
                row("INDGN", "KeyManagerialPersonnel", 0.38),
            ]
        )
        result = module.aggregate_owner_candidate(conn, "INDGN", "INE000A00001")
        assert result is not None
        assert result["promoter_total_pct"] == pytest.approx(21.42)
        assert result["promoter_total_pct"] == result["natural_pct_sum"]

    def test_エッジケース_内訳行も総合計行もない場合はpromoter_total_pctが0のまま(
        self, module
    ) -> None:
        conn = make_conn(
            [
                row("NOPROM", "OtherIndianShareholders", 5.0),
            ]
        )
        result = module.aggregate_owner_candidate(conn, "NOPROM", "INE000A00002")
        assert result is not None
        assert result["promoter_total_pct"] == 0.0
        assert result["natural_pct_sum"] == 0.0

    def test_正常系_IndianForeign分割の総合計はそのまま合算される(self, module) -> None:
        conn = make_conn(
            [
                row("SPLIT", "Indian", 30.0),
                row("SPLIT", "Foreign", 20.0),
                row("SPLIT", "DirectorsAndDirectorsRelatives", 1.0),
            ]
        )
        result = module.aggregate_owner_candidate(conn, "SPLIT", "INE000A00003")
        assert result is not None
        assert result["promoter_total_pct"] == pytest.approx(50.0)
