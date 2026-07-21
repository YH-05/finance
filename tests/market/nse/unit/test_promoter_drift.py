"""Unit tests for market.nse.analysis.promoter_drift module.

``shareholdings`` テーブル (四半期ごとの promoter 比率時系列) から、
前回判定時点と比較して promoter 比率が変化した銘柄（＝オーナー判定の
再実行が必要な銘柄）を検出する ``detect_promoter_drift`` のテストスイート。

Test TODO List:
- [x] detect_promoter_drift(): 閾値以上の変化がある銘柄を検出
- [x] detect_promoter_drift(): 閾値未満の変化は除外される
- [x] detect_promoter_drift(): 変化量が閾値ちょうどの場合は検出される（境界値、>=）
- [x] detect_promoter_drift(): Stage1 10%閾値を上方に跨ぐ場合、変化量が閾値未満でも検出される
- [x] detect_promoter_drift(): Stage1 10%閾値を下方に跨ぐ場合、変化量が閾値未満でも検出される
- [x] detect_promoter_drift(): 10%閾値を跨がない場合、変化量が閾値未満なら除外される
- [x] detect_promoter_drift(): 直近データが1件のみの銘柄は比較対象なしとして除外される
- [x] detect_promoter_drift(): 最新promoter_pctがNULLの場合は除外される
- [x] detect_promoter_drift(): 前回promoter_pctがNULLの場合は除外される
- [x] detect_promoter_drift(): as_on_dateのDD-MMM-YYYY文字列比較バグを回避し年をまたいでも正しくlatest/previousを判定する
- [x] detect_promoter_drift(): 3時点以上のデータがある場合、直近2件のみを比較に使う
- [x] detect_promoter_drift(): 複数銘柄が混在していても銘柄ごとに独立して判定される
- [x] detect_promoter_drift(): shareholdingsテーブルが空の場合、空のDataFrameを返す
- [x] detect_promoter_drift(): 戻り値の型・列構成を検証
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pandas as pd
import pytest

from market.nse.analysis.promoter_drift import detect_promoter_drift

if TYPE_CHECKING:
    from collections.abc import Iterator

_SHAREHOLDINGS_SCHEMA = """
CREATE TABLE shareholdings (
    symbol              TEXT NOT NULL,
    as_on_date          TEXT NOT NULL,
    promoter_pct        REAL,
    public_pct          REAL,
    employee_trust_pct  REAL DEFAULT 0,
    submission_date     TEXT,
    broadcast_date      TEXT,
    xbrl_url            TEXT,
    fetched_at          TEXT NOT NULL,
    PRIMARY KEY (symbol, as_on_date)
)
"""


@pytest.fixture()
def conn() -> Iterator[sqlite3.Connection]:
    """shareholdings テーブルのみを持つインメモリ SQLite 接続。"""
    connection = sqlite3.connect(":memory:")
    connection.execute(_SHAREHOLDINGS_SCHEMA)
    connection.commit()
    yield connection
    connection.close()


def _insert(
    connection: sqlite3.Connection,
    symbol: str,
    as_on_date: str,
    promoter_pct: float | None,
    fetched_at: str = "2026-01-01T00:00:00+00:00",
) -> None:
    """shareholdings テーブルに1行挿入するテストヘルパー。"""
    connection.execute(
        "INSERT INTO shareholdings (symbol, as_on_date, promoter_pct, fetched_at) "
        "VALUES (?, ?, ?, ?)",
        (symbol, as_on_date, promoter_pct, fetched_at),
    )
    connection.commit()


class TestDetectPromoterDrift:
    """detect_promoter_drift() 関数のテスト。"""

    def test_正常系_閾値以上の変化がある銘柄を検出する(
        self, conn: sqlite3.Connection
    ) -> None:
        """前回比 promoter_pct 差が threshold_pct 以上の銘柄が検出されること。"""
        _insert(conn, "RELIANCE", "31-MAR-2024", 50.0)
        _insert(conn, "RELIANCE", "31-MAR-2025", 47.0)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert list(result["symbol"]) == ["RELIANCE"]
        row = result.iloc[0]
        assert row["previous_as_on_date"] == "31-MAR-2024"
        assert row["latest_as_on_date"] == "31-MAR-2025"
        assert row["previous_promoter_pct"] == pytest.approx(50.0)
        assert row["latest_promoter_pct"] == pytest.approx(47.0)
        assert row["pct_change"] == pytest.approx(-3.0)
        assert row["crossed_stage1_threshold"] == False  # noqa: E712

    def test_正常系_閾値未満の変化は除外される(self, conn: sqlite3.Connection) -> None:
        """promoter_pct 差が threshold_pct 未満の銘柄は結果に含まれないこと。"""
        _insert(conn, "INFY", "31-MAR-2024", 13.0)
        _insert(conn, "INFY", "31-MAR-2025", 13.5)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert result.empty

    def test_エッジケース_変化量が閾値ちょうどの場合は検出される(
        self, conn: sqlite3.Connection
    ) -> None:
        """abs(差) == threshold_pct の境界値は「以上」として検出されること。"""
        _insert(conn, "TCS", "31-MAR-2024", 72.0)
        _insert(conn, "TCS", "31-MAR-2025", 73.0)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert list(result["symbol"]) == ["TCS"]
        assert result.iloc[0]["pct_change"] == pytest.approx(1.0)

    def test_エッジケース_Stage1閾値を上方に跨ぐ場合は変化量が閾値未満でも検出される(
        self, conn: sqlite3.Connection
    ) -> None:
        """9.5%→10.2%（変化量0.7 < threshold_pct=1.0）でも10%跨ぎのため検出されること。"""
        _insert(conn, "SMALLCAP1", "31-MAR-2024", 9.5)
        _insert(conn, "SMALLCAP1", "31-MAR-2025", 10.2)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert list(result["symbol"]) == ["SMALLCAP1"]
        row = result.iloc[0]
        assert row["pct_change"] == pytest.approx(0.7)
        assert row["crossed_stage1_threshold"] == True  # noqa: E712

    def test_エッジケース_Stage1閾値を下方に跨ぐ場合は変化量が閾値未満でも検出される(
        self, conn: sqlite3.Connection
    ) -> None:
        """10.5%→9.8%（変化量0.7 < threshold_pct=1.0）でも10%跨ぎのため検出されること。"""
        _insert(conn, "SMALLCAP2", "31-MAR-2024", 10.5)
        _insert(conn, "SMALLCAP2", "31-MAR-2025", 9.8)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert list(result["symbol"]) == ["SMALLCAP2"]
        assert result.iloc[0]["crossed_stage1_threshold"] == True  # noqa: E712

    def test_エッジケース_10パーセント閾値を跨がず変化量も閾値未満なら除外される(
        self, conn: sqlite3.Connection
    ) -> None:
        """両時点とも10%以上（跨ぎなし）かつ変化量が閾値未満の銘柄は除外されること。"""
        _insert(conn, "LARGECAP1", "31-MAR-2024", 55.0)
        _insert(conn, "LARGECAP1", "31-MAR-2025", 55.4)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert result.empty

    def test_エッジケース_直近データが1件のみの銘柄は除外される(
        self, conn: sqlite3.Connection
    ) -> None:
        """比較対象（前回データ）が存在しない銘柄は結果に含まれないこと。"""
        _insert(conn, "NEWLIST", "31-MAR-2025", 60.0)
        _insert(conn, "RELIANCE", "31-MAR-2024", 50.0)
        _insert(conn, "RELIANCE", "31-MAR-2025", 47.0)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert "NEWLIST" not in list(result["symbol"])
        assert list(result["symbol"]) == ["RELIANCE"]

    def test_エッジケース_最新promoter_pctがNULLの場合は除外される(
        self, conn: sqlite3.Connection
    ) -> None:
        """最新時点の promoter_pct が NULL の銘柄は比較不能として除外されること。"""
        _insert(conn, "NULLCASE1", "31-MAR-2024", 50.0)
        _insert(conn, "NULLCASE1", "31-MAR-2025", None)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert result.empty

    def test_エッジケース_前回promoter_pctがNULLの場合は除外される(
        self, conn: sqlite3.Connection
    ) -> None:
        """前回時点の promoter_pct が NULL の銘柄は比較不能として除外されること。"""
        _insert(conn, "NULLCASE2", "31-MAR-2024", None)
        _insert(conn, "NULLCASE2", "31-MAR-2025", 50.0)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert result.empty

    def test_正常系_DD_MMM_YYYY文字列比較バグを回避して年内の月順を正しく判定する(
        self, conn: sqlite3.Connection
    ) -> None:
        """ "31-MAR-2025" > "31-DEC-2025" となる文字列比較バグ（M > D）を回避すること。

        単純な ORDER BY as_on_date や MAX(as_on_date) は DD-MMM-YYYY の
        テキスト比較になり、"31-MAR-2025" が "31-DEC-2025" より「大きい」と
        誤判定される既知の不具合がある（過去の Phase 4 対象選定で発生）。
        iso_date 変換を経由することで、実際の時系列順（DEC > MAR）で
        latest/previous を正しく判定できることを検証する。
        """
        _insert(conn, "TESTCO", "31-MAR-2025", 9.0)
        _insert(conn, "TESTCO", "31-DEC-2025", 15.0)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert list(result["symbol"]) == ["TESTCO"]
        row = result.iloc[0]
        assert row["latest_as_on_date"] == "31-DEC-2025"
        assert row["previous_as_on_date"] == "31-MAR-2025"
        assert row["latest_promoter_pct"] == pytest.approx(15.0)
        assert row["previous_promoter_pct"] == pytest.approx(9.0)
        assert row["pct_change"] == pytest.approx(6.0)
        assert row["crossed_stage1_threshold"] == True  # noqa: E712

    def test_正常系_3時点以上ある場合は直近2件のみを比較に使う(
        self, conn: sqlite3.Connection
    ) -> None:
        """3時点以上のデータがある銘柄で、最も古い行が比較に使われないこと。"""
        _insert(conn, "MULTIYEAR", "30-JUN-2023", 5.0)
        _insert(conn, "MULTIYEAR", "31-DEC-2023", 20.0)
        _insert(conn, "MULTIYEAR", "30-JUN-2024", 21.0)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert list(result["symbol"]) == ["MULTIYEAR"]
        row = result.iloc[0]
        assert row["latest_as_on_date"] == "30-JUN-2024"
        assert row["previous_as_on_date"] == "31-DEC-2023"
        assert row["pct_change"] == pytest.approx(1.0)

    def test_正常系_複数銘柄が混在していても銘柄ごとに独立して判定される(
        self, conn: sqlite3.Connection
    ) -> None:
        """変化ありの銘柄のみが抽出され、変化なしの銘柄は含まれないこと。"""
        _insert(conn, "CHANGED", "31-MAR-2024", 30.0)
        _insert(conn, "CHANGED", "31-MAR-2025", 35.0)
        _insert(conn, "UNCHANGED", "31-MAR-2024", 40.0)
        _insert(conn, "UNCHANGED", "31-MAR-2025", 40.1)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert list(result["symbol"]) == ["CHANGED"]

    def test_エッジケース_shareholdingsが空の場合は空のDataFrameを返す(
        self, conn: sqlite3.Connection
    ) -> None:
        """データが1件も無い場合でも例外を発生させず空の DataFrame を返すこと。"""
        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_正常系_戻り値の型と列構成を検証する(
        self, conn: sqlite3.Connection
    ) -> None:
        """戻り値が pd.DataFrame で、必須列を全て含むこと。"""
        _insert(conn, "RELIANCE", "31-MAR-2024", 50.0)
        _insert(conn, "RELIANCE", "31-MAR-2025", 47.0)

        result = detect_promoter_drift(conn, threshold_pct=1.0)

        assert isinstance(result, pd.DataFrame)
        expected_columns = {
            "symbol",
            "previous_as_on_date",
            "latest_as_on_date",
            "previous_promoter_pct",
            "latest_promoter_pct",
            "pct_change",
            "crossed_stage1_threshold",
        }
        assert expected_columns.issubset(set(result.columns))
