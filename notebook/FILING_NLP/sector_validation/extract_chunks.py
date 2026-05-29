"""Sector 識別性検証フェーズの chunks 抽出ヘルパー.

ActionItem ``act-2026-05-29-005`` (n01_extract_and_embed.ipynb) の抽出ロジックを
モジュール化したもの。notebook と CLI 実行 (chunks_meta.parquet 生成) の双方から
re-use することで、抽出ロジックの重複を避ける。

設計方針 (dec-2026-05-29-005)
-----------------------------
- 入力: ``data/processed/sector_validation/ticker_list.csv`` (55 CIK)
- per-CIK ``chunks_cik{cik:010d}.parquet`` を読み、
  ``fiscal_year >= 2020 & form in (10-K, 10-Q)`` でフィルタ。
- ticker_list の ``sector`` / ``industry`` (GICS) を **cik で left join**。
- 全 CIK を ``pd.concat`` → ``reset_index(drop=True)`` で行順を確定
  (embeddings.npy の行 i ↔ chunks_meta 行 i を厳密一致させるため)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pandas as pd

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)

# 抽出フィルタのデフォルト (dec-2026-05-29-003)
FISCAL_YEAR_MIN: int = 2020
FORMS: tuple[str, ...] = ("10-K", "10-Q")


@dataclass
class ExtractionResult:
    """chunks 抽出結果.

    Attributes
    ----------
    chunks_meta : pandas.DataFrame
        元 chunks 全列 + ``sector`` + ``industry``。行順は確定済み
        (``reset_index(drop=True)``)。
    tickers_without_chunks : list[str]
        ticker_list に存在するが抽出後 0 行だった ticker。
    per_cik_counts : dict[int, int]
        CIK -> 抽出 chunks 数。
    """

    chunks_meta: pd.DataFrame
    tickers_without_chunks: list[str] = field(default_factory=list)
    per_cik_counts: dict[int, int] = field(default_factory=dict)


def load_ticker_list(ticker_list_csv: Path) -> pd.DataFrame:
    """ticker_list.csv を読み込む.

    Parameters
    ----------
    ticker_list_csv : Path
        ``ticker, cik, sector, industry, mkt_cap`` 列を持つ CSV。

    Returns
    -------
    pandas.DataFrame
        ``cik`` は int64 に正規化済み。
    """
    df = pd.read_csv(ticker_list_csv)
    df["cik"] = df["cik"].astype("int64")
    logger.info("ticker_list loaded", rows=len(df), path=str(ticker_list_csv))
    return df


def extract_chunks(
    ticker_list: pd.DataFrame,
    chunks_dir: Path,
    *,
    fiscal_year_min: int = FISCAL_YEAR_MIN,
    forms: tuple[str, ...] = FORMS,
) -> ExtractionResult:
    """ticker_list の 55 CIK から条件に合う chunks を抽出・結合する.

    各 CIK の ``chunks_cik{cik:010d}.parquet`` を読み、
    ``fiscal_year >= fiscal_year_min & form in forms`` でフィルタし、
    GICS ``sector`` / ``industry`` を cik で left join する。

    Parameters
    ----------
    ticker_list : pandas.DataFrame
        ``ticker``, ``cik``, ``sector``, ``industry`` 列を持つ DataFrame。
    chunks_dir : Path
        ``chunks_cik*.parquet`` が格納されたディレクトリ (``indices_v1``)。
    fiscal_year_min : int, optional
        抽出する最小 fiscal_year (デフォルト 2020)。
    forms : tuple[str, ...], optional
        抽出対象 form (デフォルト ``("10-K", "10-Q")``)。

    Returns
    -------
    ExtractionResult
        結合済み chunks_meta と統計情報。

    Raises
    ------
    FileNotFoundError
        いずれの CIK の parquet も見つからない場合。
    """
    gics = ticker_list[["cik", "sector", "industry"]].drop_duplicates("cik")
    frames: list[pd.DataFrame] = []
    tickers_without_chunks: list[str] = []
    per_cik_counts: dict[int, int] = {}
    missing_files = 0

    for row in ticker_list.itertuples(index=False):
        cik = int(row.cik)
        ticker = str(row.ticker)
        path = chunks_dir / f"chunks_cik{cik:010d}.parquet"
        if not path.exists():
            logger.warning(
                "chunks parquet not found", ticker=ticker, cik=cik, path=str(path)
            )
            missing_files += 1
            tickers_without_chunks.append(ticker)
            per_cik_counts[cik] = 0
            continue

        df = pd.read_parquet(path)
        mask = (df["fiscal_year"] >= fiscal_year_min) & (df["form"].isin(forms))
        filtered = df.loc[mask].copy()
        per_cik_counts[cik] = len(filtered)
        if filtered.empty:
            logger.warning("no chunks after filter", ticker=ticker, cik=cik)
            tickers_without_chunks.append(ticker)
            continue
        frames.append(filtered)

    if not frames:
        raise FileNotFoundError(
            f"No chunks extracted from {chunks_dir} for any of the "
            f"{len(ticker_list)} CIKs (missing files: {missing_files}). "
            "Mount the NAS volume and verify ticker_list.csv."
        )

    combined = pd.concat(frames, ignore_index=True)
    # GICS の sector/industry を cik で left join (GICS 列名のまま付与)
    combined = combined.merge(gics, on="cik", how="left")
    # 行順を確定 (embeddings.npy の行 i ↔ chunks_meta 行 i 厳密一致)
    chunks_meta = combined.reset_index(drop=True)

    logger.info(
        "chunks extracted",
        total_chunks=len(chunks_meta),
        ciks_with_chunks=len(frames),
        tickers_without_chunks=len(tickers_without_chunks),
    )
    return ExtractionResult(
        chunks_meta=chunks_meta,
        tickers_without_chunks=tickers_without_chunks,
        per_cik_counts=per_cik_counts,
    )
