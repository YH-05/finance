"""Sector 識別性検証フェーズ用の 55 ticker 選定スクリプト.

ActionItem ``act-2026-05-29-004`` の実装.

SPX universe (``2026-05-22_SPX Index.json``) から「11 GICS sector x 各 5 ticker」=
最大 55 銘柄を、時価総額 (``CUR_MKT_CAP``) 降順 + GICS_INDUSTRY 分散 dedupe で
選定する。chunks parquet (``indices_v1``) に実在する ticker のみを採用し、
``data/processed/sector_validation/ticker_list.csv`` に出力する。

Notes
-----
- chunks parquet は ``columns=["ticker", "cik"]`` で列プルーニング読込し、
  全文 (``text``) は読まない（1.53M 行の text 読込は厳禁）。
- ticker は SPX 側・chunks 側ともに Bloomberg 形式（例 ``BRK/B``）の可能性が
  あるため、大文字化 + ``/`` ``.`` の ``-`` 変換で正規化して突合する。
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from utils_core.logging import get_logger

logger = get_logger(__name__)

# --- パス定義 -----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPX_JSON_PATH = PROJECT_ROOT / "notebook" / "FILING_NLP" / "2026-05-22_SPX Index.json"
CHUNKS_DIR = Path("/Volumes/personal_folder/Quants/FILING_NLP_v2/chunks/indices_v1")
OUTPUT_CSV_PATH = (
    PROJECT_ROOT / "data" / "processed" / "sector_validation" / "ticker_list.csv"
)

# --- 選定パラメータ -----------------------------------------------------------
TICKERS_PER_SECTOR = 5


def normalize_ticker(ticker: str) -> str:
    """ticker を突合用の正規化キーに変換する.

    大文字化し、Bloomberg 形式の ``/`` と区切り ``.`` を EDGAR 形式の ``-`` に
    変換する。両方向の表記揺れ（``BRK/B`` / ``BRK.B`` / ``BRK-B``）を同一キーに
    寄せる。

    Parameters
    ----------
    ticker : str
        正規化対象の ticker。

    Returns
    -------
    str
        正規化済みキー（例 ``"BRK-B"``）。
    """
    return ticker.strip().upper().replace("/", "-").replace(".", "-")


@dataclass
class ChunkUniverse:
    """chunks parquet 由来の実在銘柄ユニバース.

    Attributes
    ----------
    by_norm : dict[str, tuple[str, int]]
        正規化キー -> (chunks 側実 ticker 表記, cik)。
    raw_pairs : list[tuple[str, int]]
        読み取った全 (ticker, cik) ペア。
    """

    by_norm: dict[str, tuple[str, int]] = field(default_factory=dict)
    raw_pairs: list[tuple[str, int]] = field(default_factory=list)


def build_chunk_universe(chunks_dir: Path) -> ChunkUniverse:
    """chunks parquet 群から (ticker, cik) ユニバースを構築する.

    各 parquet は 1 ファイル = 1 CIK のため、``columns=["ticker", "cik"]`` で
    列プルーニングし、先頭 1 行のみ参照する。

    Parameters
    ----------
    chunks_dir : Path
        ``chunks_cik*.parquet`` が格納されたディレクトリ。

    Returns
    -------
    ChunkUniverse
        正規化キー索引付きの実在銘柄ユニバース。

    Raises
    ------
    FileNotFoundError
        chunks ディレクトリにファイルが存在しない場合。
    """
    files = sorted(chunks_dir.glob("chunks_cik*.parquet"))
    if not files:
        raise FileNotFoundError(
            f"No chunks parquet found under {chunks_dir}. "
            "Mount the NAS volume and retry."
        )
    logger.info("Scanning chunks parquet", file_count=len(files))

    universe = ChunkUniverse()
    for path in files:
        table = pq.read_table(path, columns=["ticker", "cik"])
        if table.num_rows == 0:
            logger.warning("Empty chunks parquet skipped", path=str(path))
            continue
        ticker = str(table["ticker"][0].as_py())
        cik = int(table["cik"][0].as_py())
        universe.raw_pairs.append((ticker, cik))
        universe.by_norm[normalize_ticker(ticker)] = (ticker, cik)

    logger.info(
        "Chunk universe built",
        unique_tickers=len(universe.by_norm),
        raw_pairs=len(universe.raw_pairs),
    )
    return universe


def load_spx_universe(json_path: Path) -> pd.DataFrame:
    """SPX universe JSON を DataFrame 化する.

    Parameters
    ----------
    json_path : Path
        SPX universe JSON（top-level は list）。

    Returns
    -------
    pandas.DataFrame
        ``ticker``, ``CUR_MKT_CAP``, ``GICS_SECTOR_NAME``,
        ``GICS_INDUSTRY_NAME`` 等を含む DataFrame。
    """
    with json_path.open(encoding="utf-8") as fh:
        records = json.load(fh)
    df = pd.DataFrame(records)
    logger.info("SPX universe loaded", record_count=len(df))
    return df


@dataclass
class SelectionResult:
    """ticker 選定結果.

    Attributes
    ----------
    rows : list[dict[str, object]]
        採用銘柄。``ticker``, ``cik``, ``sector``, ``industry``, ``mkt_cap``。
    excluded_unmatched : list[dict[str, object]]
        chunks に突合できず除外した JSON 銘柄。
    relaxed_sectors : dict[str, int]
        industry dedupe を緩めて補充した sector -> 補充件数。
    """

    rows: list[dict[str, object]] = field(default_factory=list)
    excluded_unmatched: list[dict[str, object]] = field(default_factory=list)
    relaxed_sectors: dict[str, int] = field(default_factory=dict)


def select_tickers(
    spx: pd.DataFrame,
    universe: ChunkUniverse,
    per_sector: int = TICKERS_PER_SECTOR,
) -> SelectionResult:
    """sector ごとに時価総額順 + industry 分散で ticker を選定する.

    Parameters
    ----------
    spx : pandas.DataFrame
        SPX universe DataFrame。
    universe : ChunkUniverse
        chunks 由来の実在銘柄ユニバース。
    per_sector : int, optional
        各 sector の採用上限（デフォルト 5）。

    Returns
    -------
    SelectionResult
        採用銘柄・除外銘柄・補充情報を保持する結果。
    """
    result = SelectionResult()

    # chunks に突合できない JSON 銘柄を除外（除外理由を記録）
    def matched(row: pd.Series) -> bool:
        return normalize_ticker(str(row["ticker"])) in universe.by_norm

    matchable = spx[spx.apply(matched, axis=1)].copy()
    for _, row in spx[~spx.apply(matched, axis=1)].iterrows():
        result.excluded_unmatched.append(
            {
                "ticker": row["ticker"],
                "sector": row["GICS_SECTOR_NAME"],
                "reason": "chunks 非実在（ticker 突合不可）",
            }
        )
    logger.info(
        "Match filtering done",
        matchable=len(matchable),
        excluded=len(result.excluded_unmatched),
    )

    for sector, group in matchable.groupby("GICS_SECTOR_NAME", sort=True):
        ordered = group.sort_values("CUR_MKT_CAP", ascending=False)

        seen_industries: set[str] = set()
        seen_ciks: set[int] = set()
        primary: list[dict[str, object]] = []  # industry dedupe を満たす採用
        leftovers: list[pd.Series] = []  # dedupe で弾かれた候補（補充用）

        for _, row in ordered.iterrows():
            norm_key = normalize_ticker(str(row["ticker"]))
            chunk_ticker, cik = universe.by_norm[norm_key]
            if cik in seen_ciks:
                # GOOG/GOOGL のような同一企業（同一 cik）の重複を除去
                continue

            industry = row["GICS_INDUSTRY_NAME"]
            entry = {
                "ticker": chunk_ticker,
                "cik": cik,
                "sector": sector,
                "industry": industry,
                "mkt_cap": float(row["CUR_MKT_CAP"]),
            }
            if industry in seen_industries:
                leftovers.append(row)
                continue
            if len(primary) >= per_sector:
                leftovers.append(row)
                continue
            primary.append(entry)
            seen_industries.add(industry)
            seen_ciks.add(cik)

        # industry dedupe で per_sector 未満なら、dedupe を緩めて時価総額順に補充
        if len(primary) < per_sector:
            relaxed_count = 0
            for row in leftovers:
                if len(primary) >= per_sector:
                    break
                norm_key = normalize_ticker(str(row["ticker"]))
                chunk_ticker, cik = universe.by_norm[norm_key]
                if cik in seen_ciks:
                    continue
                primary.append(
                    {
                        "ticker": chunk_ticker,
                        "cik": cik,
                        "sector": sector,
                        "industry": row["GICS_INDUSTRY_NAME"],
                        "mkt_cap": float(row["CUR_MKT_CAP"]),
                    }
                )
                seen_ciks.add(cik)
                relaxed_count += 1
            if relaxed_count:
                result.relaxed_sectors[sector] = relaxed_count
                logger.info(
                    "Industry dedupe relaxed to backfill",
                    sector=sector,
                    backfilled=relaxed_count,
                    final_count=len(primary),
                )

        if len(primary) < per_sector:
            logger.warning(
                "Sector under target (candidate exhausted)",
                sector=sector,
                selected=len(primary),
                target=per_sector,
            )

        result.rows.extend(primary)

    logger.info("Selection complete", total_selected=len(result.rows))
    return result


def write_output(rows: list[dict[str, object]], output_path: Path) -> int:
    """採用銘柄を CSV に書き出す.

    Parameters
    ----------
    rows : list[dict[str, object]]
        採用銘柄（``ticker``, ``cik``, ``sector``, ``industry``, ``mkt_cap``）。
    output_path : Path
        出力先 CSV パス。

    Returns
    -------
    int
        書き出した行数。
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["ticker", "cik", "sector", "industry", "mkt_cap"])
    df.to_csv(output_path, index=False)
    logger.info("CSV written", path=str(output_path), rows=len(df))
    return len(df)


def _humanize_cap(mkt_cap: float) -> str:
    """時価総額を 10 億ドル単位の可読文字列に変換する.

    Parameters
    ----------
    mkt_cap : float
        時価総額（ドル）。

    Returns
    -------
    str
        例 ``"3,520.4B"``。
    """
    return f"{mkt_cap / 1e9:,.1f}B"


def print_report(result: SelectionResult, output_path: Path, total_rows: int) -> None:
    """選定結果を標準出力に Markdown で要約する.

    Parameters
    ----------
    result : SelectionResult
        選定結果。
    output_path : Path
        出力 CSV の絶対パス。
    total_rows : int
        CSV 総行数。
    """
    by_sector: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in result.rows:
        by_sector[str(row["sector"])].append(row)

    print("\n# Sector 識別性検証 — 55 ticker 選定結果\n")
    for sector in sorted(by_sector):
        entries = by_sector[sector]
        print(f"## {sector} ({len(entries)} 件)\n")
        print("| ticker | industry | mkt_cap |")
        print("|--------|----------|--------:|")
        for e in sorted(entries, key=lambda x: -float(x["mkt_cap"])):
            print(
                f"| {e['ticker']} | {e['industry']} | "
                f"{_humanize_cap(float(e['mkt_cap']))} |"
            )
        print()

    print("## Sector 別採用件数\n")
    print("| sector | 採用件数 |")
    print("|--------|---------:|")
    for sector in sorted(by_sector):
        print(f"| {sector} | {len(by_sector[sector])} |")
    print()

    if result.relaxed_sectors:
        print("## industry dedupe を緩めて補充した sector\n")
        for sector, n in sorted(result.relaxed_sectors.items()):
            print(f"- {sector}: {n} 件補充")
        print()

    if result.excluded_unmatched:
        print("## chunks に突合できず除外した JSON 銘柄\n")
        print("| ticker | sector |")
        print("|--------|--------|")
        for e in result.excluded_unmatched:
            print(f"| {e['ticker']} | {e['sector']} |")
        print()

    print(f"出力: {output_path}  （総行数 {total_rows}）")


def main() -> None:
    """エンドツーエンドの選定パイプラインを実行する."""
    logger.info("Ticker selection started")
    universe = build_chunk_universe(CHUNKS_DIR)
    spx = load_spx_universe(SPX_JSON_PATH)
    result = select_tickers(spx, universe)
    total_rows = write_output(result.rows, OUTPUT_CSV_PATH)
    print_report(result, OUTPUT_CSV_PATH.resolve(), total_rows)
    logger.info("Ticker selection finished", total_rows=total_rows)


if __name__ == "__main__":
    main()
