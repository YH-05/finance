"""並列パイプライン実行 + チェックポイント.

CIK 単位でワークを分散し、ThreadPoolExecutor で並列実行する。
Rate limiter で SEC へのリクエスト頻度を制御する。
進捗と失敗を JSON で永続化し、resume 可能にする。
"""

from __future__ import annotations

import json
import logging
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from . import config
from .extractor import (
    count_tokens,
    get_section,
    is_table_like,
    paragraph_pack,
    remove_tables_from_text,
    split_subsections,
)
from .rate_limiter import TokenBucket

logger = logging.getLogger(__name__)


# =============================================================================
# 単一 filing 処理
# =============================================================================


def process_filing(
    filing: Any,
    cik: int,
    ticker: str,
    form: str,
    tokenizer: Any,
    rate_limiter: TokenBucket,
) -> tuple[list[dict], list[dict], dict]:
    """1 filing × 全 Item を抽出して (section_rows, chunk_rows, metadata) を返す.

    metadata は filing 1 件分: status, n_sections, n_chunks など.
    """
    fid = str(filing.accession_number)
    filing_date = str(filing.filing_date)
    fiscal_year = int(filing_date[:4])

    meta = {
        "filing_id": fid,
        "cik": cik,
        "ticker": ticker,
        "form": form,
        "filing_date": filing_date,
        "fiscal_year": fiscal_year,
        "status": "pending",
        "n_sections": 0,
        "n_chunks": 0,
        "error": None,
    }

    # filing.obj() で TenK / TenQ を取得 (SEC リクエストが発生する可能性)
    rate_limiter.acquire()
    try:
        obj = filing.obj()
    except Exception as e:
        meta["status"] = "obj_fail"
        meta["error"] = f"{type(e).__name__}: {e}"
        return [], [], meta

    # document アクセス (DOM)
    try:
        doc = obj.document
    except Exception:
        doc = None

    specs = config.ITEM_SPECS_BY_FORM.get(form, [])
    section_rows: list[dict] = []
    chunk_rows: list[dict] = []

    for section_key, section_role, part, item in specs:
        # text 抽出 (primary path: get_item_with_part)
        rate_limiter.acquire()
        try:
            text = obj.get_item_with_part(part, item, markdown=False)
        except Exception as e:
            logger.debug(
                "get_item_with_part fail: %s %s/%s: %s", ticker, part, item, e
            )
            continue
        if not isinstance(text, str) or not text.strip():
            continue

        original_len = len(text)
        tables_removed = 0
        dom_section_found = False

        # DOM table 除外 (best-effort)
        if doc is not None:
            sec, _key = get_section(doc, part, item)
            if sec is not None:
                dom_section_found = True
                try:
                    tbls = sec.tables() if callable(sec.tables) else sec.tables
                except Exception:
                    tbls = None
                if tbls:
                    text, tables_removed = remove_tables_from_text(text, list(tbls))

        section_row = {
            "filing_id": fid,
            "cik": cik,
            "ticker": ticker,
            "form": form,
            "filing_date": filing_date,
            "fiscal_year": fiscal_year,
            "section_key": section_key,
            "section_role": section_role,
            "part": part,
            "item": item,
            "text": text,
            "char_count": len(text),
            "char_count_before_table_removal": original_len,
            "tables_removed": tables_removed,
            "dom_section_found": dom_section_found,
        }
        section_rows.append(section_row)

        # subsection 分割 → paragraph packing → safety net
        subs = split_subsections(text)
        for sub_idx, (title, body) in enumerate(subs):
            chunks = paragraph_pack(body, tokenizer, max_tokens=config.MAX_TOKENS)
            for chunk_idx, c in enumerate(chunks):
                if is_table_like(c):
                    continue
                chunk_rows.append(
                    {
                        "filing_id": fid,
                        "cik": cik,
                        "ticker": ticker,
                        "form": form,
                        "filing_date": filing_date,
                        "fiscal_year": fiscal_year,
                        "section_key": section_key,
                        "section_role": section_role,
                        "subsection_idx": sub_idx,
                        "subsection_title": title,
                        "chunk_idx": chunk_idx,
                        "text": c,
                        "token_count": count_tokens(c, tokenizer),
                    }
                )

    meta["status"] = "success" if section_rows else "no_sections"
    meta["n_sections"] = len(section_rows)
    meta["n_chunks"] = len(chunk_rows)
    return section_rows, chunk_rows, meta


# =============================================================================
# 単一 CIK 処理 (全 form × 全期間)
# =============================================================================


def process_cik(
    cik: int,
    ticker: str,
    tokenizer: Any,
    rate_limiter: TokenBucket,
    forms: tuple[str, ...] = config.FORMS_TARGET,
    year_cutoff: int = config.YEAR_CUTOFF,
) -> dict:
    """1 CIK 分の全 filing を処理して結果を集約.

    Returns
    -------
    dict with keys:
        cik, ticker, status, sections, chunks, filings_meta, errors
    """
    import edgar  # 遅延 import (子プロセスで Identity 設定後に使う場合に備え)

    result: dict[str, Any] = {
        "cik": cik,
        "ticker": ticker,
        "status": "pending",
        "sections": [],
        "chunks": [],
        "filings_meta": [],
        "errors": [],
        "started_at": datetime.now().isoformat(),
    }

    # Company オブジェクト取得 (CIK ベース)
    rate_limiter.acquire()
    try:
        co = edgar.Company(cik)
        if co is None or getattr(co, "cik", None) in (None, -999999999):
            result["status"] = "company_not_found"
            return result
    except Exception as e:
        result["status"] = "company_fail"
        result["errors"].append(
            {"phase": "company_fetch", "error": f"{type(e).__name__}: {e}"}
        )
        return result

    # form × CIK で filings を取得 (10-K / 10-Q 別)
    for form in forms:
        rate_limiter.acquire()
        try:
            fs = co.get_filings(form=form)
        except Exception as e:
            result["errors"].append(
                {
                    "phase": "get_filings",
                    "form": form,
                    "error": f"{type(e).__name__}: {e}",
                }
            )
            continue

        try:
            df = fs.to_pandas()
        except Exception:
            df = None
        if df is None or len(df) == 0:
            continue
        df["filing_date"] = df["filing_date"].astype(str)
        df["form"] = df["form"].astype(str)

        # filter: amendment 除外 + year cutoff
        filtered = df[
            (df["form"] == form) & (df["filing_date"] >= f"{year_cutoff}-01-01")
        ].copy()

        # 各 filing を処理
        for _, frow in filtered.iterrows():
            # accession_number でフィルタした Filing オブジェクトを取得する必要がある
            # fs (Filings) から取り出す
            acc = frow["accession_number"]
            try:
                # fs は遅延評価。filter で 1 件に絞る
                fres = [f for f in fs if str(f.accession_number) == str(acc)]
                if not fres:
                    continue
                filing = fres[0]
            except Exception as e:
                result["errors"].append(
                    {
                        "phase": "filing_lookup",
                        "accession": str(acc),
                        "error": f"{type(e).__name__}: {e}",
                    }
                )
                continue

            try:
                sec_rows, chk_rows, meta = process_filing(
                    filing, cik, ticker, form, tokenizer, rate_limiter
                )
                result["sections"].extend(sec_rows)
                result["chunks"].extend(chk_rows)
                result["filings_meta"].append(meta)
                if meta.get("error"):
                    result["errors"].append(
                        {
                            "phase": "process_filing",
                            "accession": str(acc),
                            "form": form,
                            "error": meta["error"],
                        }
                    )
            except Exception as e:
                result["errors"].append(
                    {
                        "phase": "process_filing",
                        "accession": str(acc),
                        "form": form,
                        "error": f"{type(e).__name__}: {e}",
                        "traceback": traceback.format_exc(limit=3),
                    }
                )

    result["status"] = "success"
    result["finished_at"] = datetime.now().isoformat()
    return result


# =============================================================================
# Checkpoint 管理
# =============================================================================


class Checkpoint:
    """CIK 単位の処理状況を JSON で永続化."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            self.data = {
                "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "started_at": datetime.now().isoformat(),
                "completed": {},  # cik -> {status, finished_at, n_sections, n_chunks}
            }
            self._save()

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp.json")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=1))
        tmp.replace(self.path)

    def is_done(self, cik: int) -> bool:
        with self.lock:
            return str(cik) in self.data["completed"]

    def mark_done(self, cik: int, summary: dict) -> None:
        with self.lock:
            self.data["completed"][str(cik)] = {
                "finished_at": datetime.now().isoformat(),
                **summary,
            }
            self._save()


# =============================================================================
# 出力 (year shard, append-safe)
# =============================================================================


class ShardWriter:
    """per-CIK parquet writer. CIK 単位で 1 ファイル新規作成 (read-modify-write 無し).

    各 CIK の output を ``{name_prefix}_cik{cik:010d}.parquet`` として書き出す。
    flush() は no-op (互換性のため残置)。
    本 writer は thread-safe (per-CIK write は独立ファイルなので競合なし)。
    """

    def __init__(self, out_dir: Path, name_prefix: str) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.name_prefix = name_prefix

    def write_cik(self, cik: int, rows: list[dict]) -> Path | None:
        """1 CIK 分の rows を per-CIK parquet として一度に書き出す.

        Returns
        -------
        Path | None
            書き出したファイルパス. rows が空なら None.
        """
        if not rows:
            return None
        df = pd.DataFrame(rows)
        path = self.out_dir / f"{self.name_prefix}_cik{int(cik):010d}.parquet"
        df.to_parquet(path, index=False)
        return path

    def flush(self) -> dict[int, int]:
        """互換性のための no-op."""
        return {}


# =============================================================================
# Parallel runner
# =============================================================================


def run_pipeline(
    universe: pd.DataFrame,
    tokenizer: Any,
    sections_dir: Path,
    chunks_dir: Path,
    filings_metadata_dir: Path,
    checkpoint_path: Path,
    errors_path: Path,
    max_workers: int = config.DEFAULT_MAX_WORKERS,
    rate_rps: float = config.RATE_LIMIT_RPS,
    rate_burst: int = config.RATE_LIMIT_BURST,
    flush_every: int = 20,
    use_tqdm: bool = False,
) -> dict:
    """Universe (DataFrame: cik, ticker) を並列処理.

    Parameters
    ----------
    universe : DataFrame
        cik, ticker カラム必須.
    flush_every : int
        N CIK ごとに parquet flush.

    Returns
    -------
    dict
        summary 統計.
    """
    rate_limiter = TokenBucket(rate=rate_rps, capacity=rate_burst)
    checkpoint = Checkpoint(checkpoint_path)
    sections_writer = ShardWriter(sections_dir, "sections")
    chunks_writer = ShardWriter(chunks_dir, "chunks")
    filings_writer = ShardWriter(filings_metadata_dir, "filings_metadata")

    todo = [
        (int(r["cik"]), str(r["ticker"]))
        for _, r in universe.iterrows()
        if not checkpoint.is_done(int(r["cik"]))
    ]
    logger.info(
        "Universe %d, todo %d (skipped %d via checkpoint)",
        len(universe),
        len(todo),
        len(universe) - len(todo),
    )

    errors_path.parent.mkdir(parents=True, exist_ok=True)
    errors_fp = errors_path.open("a", encoding="utf-8")

    summary = {
        "n_processed": 0,
        "n_failed": 0,
        "n_filings": 0,
        "n_sections": 0,
        "n_chunks": 0,
        "started_at": datetime.now().isoformat(),
    }

    def _worker(cik: int, ticker: str) -> dict:
        return process_cik(cik, ticker, tokenizer, rate_limiter)

    t0 = time.time()
    last_print = t0

    if use_tqdm:
        from tqdm.auto import tqdm

        pbar = tqdm(total=len(todo), desc="CIKs", unit="cik", smoothing=0.05)
    else:
        pbar = None

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_worker, cik, ticker): (cik, ticker) for cik, ticker in todo}
        done_since_flush = 0
        for fut in as_completed(futures):
            cik, ticker = futures[fut]
            try:
                r = fut.result()
            except Exception as e:
                summary["n_failed"] += 1
                errors_fp.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "cik": cik,
                            "ticker": ticker,
                            "phase": "worker_fatal",
                            "error": f"{type(e).__name__}: {e}",
                            "traceback": traceback.format_exc(limit=3),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                errors_fp.flush()
                checkpoint.mark_done(cik, {"status": "fatal", "error": str(e)})
                continue

            # === 結果書き出し (per-CIK parquet を「先に」書く) ===
            # この順序が重要: parquet write → checkpoint mark_done の順にする。
            # kill 時の挙動:
            #   - parquet write 前 kill: checkpoint なし → resume で再処理 (安全)
            #   - parquet write 後 kill: checkpoint なし → resume で再処理し既存ファイルを上書き (安全)
            #   - mark_done 後 kill: checkpoint あり, データもある (安全)
            try:
                sections_writer.write_cik(cik, r["sections"])
                chunks_writer.write_cik(cik, r["chunks"])
                filings_writer.write_cik(cik, r["filings_meta"])
            except Exception as e:
                logger.error("write_cik failed for CIK %d (%s): %s", cik, ticker, e)
                errors_fp.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "cik": cik,
                            "ticker": ticker,
                            "phase": "write_cik",
                            "error": f"{type(e).__name__}: {e}",
                            "traceback": traceback.format_exc(limit=3),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                errors_fp.flush()
                # mark_done せずに continue (resume で再処理)
                continue

            # エラー log
            for err in r.get("errors", []):
                errors_fp.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "cik": cik,
                            "ticker": ticker,
                            **err,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            if r.get("errors"):
                errors_fp.flush()

            checkpoint.mark_done(
                cik,
                {
                    "status": r["status"],
                    "ticker": ticker,
                    "n_filings": len(r["filings_meta"]),
                    "n_sections": len(r["sections"]),
                    "n_chunks": len(r["chunks"]),
                    "n_errors": len(r["errors"]),
                },
            )

            summary["n_processed"] += 1
            summary["n_filings"] += len(r["filings_meta"])
            summary["n_sections"] += len(r["sections"])
            summary["n_chunks"] += len(r["chunks"])
            done_since_flush += 1

            if pbar is not None:
                pbar.update(1)
                pbar.set_postfix(
                    filings=summary["n_filings"],
                    chunks=summary["n_chunks"],
                    errs=summary["n_failed"],
                    last=f"{ticker}({len(r['chunks'])})",
                )
            else:
                # 進捗ログ (5 秒に 1 回)
                now = time.time()
                if now - last_print >= 5:
                    elapsed = now - t0
                    rate = summary["n_processed"] / max(elapsed, 1)
                    eta = (len(todo) - summary["n_processed"]) / max(rate, 0.001)
                    logger.info(
                        "Progress: %d/%d CIKs (%.1f%%) | filings=%d sections=%d "
                        "chunks=%d | rate=%.2f CIK/s | ETA=%.0f min",
                        summary["n_processed"],
                        len(todo),
                        100 * summary["n_processed"] / max(len(todo), 1),
                        summary["n_filings"],
                        summary["n_sections"],
                        summary["n_chunks"],
                        rate,
                        eta / 60,
                    )
                    last_print = now

    # 最終 flush (per-CIK writer では no-op だが互換性のため呼ぶ)
    sections_writer.flush()
    chunks_writer.flush()
    filings_writer.flush()
    errors_fp.close()
    if pbar is not None:
        pbar.close()

    summary["finished_at"] = datetime.now().isoformat()
    summary["elapsed_sec"] = round(time.time() - t0, 1)
    return summary
