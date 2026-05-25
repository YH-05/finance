"""indices_v1 universe builder.

4 米国インデックス (SPX/SOX/RIY/RAY) の Bloomberg JSON エクスポートを読み込み、
3 段フォールバック (Stage1 直接 join → Stage2 '/' → '-' 正規化 + all_tickers 突合 →
Stage3 edgar.Company(ticker) lookup) で CIK 解決し、universe_indices_v1.parquet と
membership_indices_v1.parquet を出力する CLI モジュール.

実行例
-------
    uv run python -m notebook.FILING_NLP.pipeline.universe_builder \\
        --indices SPX SOX RIY RAY \\
        --snapshot-date 2026-05-22 \\
        --index-dir 'notebook/US Index' \\
        --universe-out /Volumes/personal_folder/Quants/FILING_NLP_v2/universe/universe_indices_v1.parquet \\
        --membership-out /Volumes/personal_folder/Quants/FILING_NLP_v2/index_membership/membership_indices_v1.parquet
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from tenacity import (
    RetryError,
    retry,
    stop_after_attempt,
    wait_exponential,
)

# EDGAR_IDENTITY の .env ロードは main() 内で実行する (import 時の副作用を排除)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_PATH = _REPO_ROOT / ".env"

sys.path.insert(0, str(_REPO_ROOT))
from notebook.FILING_NLP.pipeline import config, utils  # noqa: E402

log = logging.getLogger(__name__)

# 出力カラムスキーマ (universe_indices_v1.parquet)
_UNIVERSE_COLUMNS = [
    "cik",
    "ticker",
    "isin",
    "sedol",
    "mkt_cap",
    "gics_sector",
    "gics_industry_group",
    "gics_industry",
    "gics_sub_industry",
    "index_name",
]


# ----------------------------------------------------------------------------
# Stage 0: load
# ----------------------------------------------------------------------------
def load_index_json(path: Path, index_name: str) -> pd.DataFrame:
    """Bloomberg JSON を DataFrame 化する.

    Parameters
    ----------
    path : Path
        ``YYYY-MM-DD_<INDEX> Index.json`` 形式のファイルパス.
    index_name : str
        index 名 (SPX/SOX/RIY/RAY).

    Returns
    -------
    pd.DataFrame
        columns: ticker, isin, sedol, mkt_cap, gics_sector,
        gics_industry_group, gics_industry, gics_sub_industry, index_name
    """
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    df = pd.DataFrame(records)
    rename_map = {
        "ticker": "ticker",
        "ISIN": "isin",
        "SEDOL": "sedol",
        "CUR_MKT_CAP": "mkt_cap",
        "GICS_SECTOR_NAME": "gics_sector",
        "GICS_INDUSTRY_GROUP_NAME": "gics_industry_group",
        "GICS_INDUSTRY_NAME": "gics_industry",
        "GICS_SUB_INDUSTRY_NAME": "gics_sub_industry",
    }
    df = df.rename(columns=rename_map)
    # 必須列が無ければ空で補完 (Bloomberg 出力のばらつき耐性)
    for col in (
        "ticker",
        "isin",
        "sedol",
        "mkt_cap",
        "gics_sector",
        "gics_industry_group",
        "gics_industry",
        "gics_sub_industry",
    ):
        if col not in df.columns:
            df[col] = None
    df["index_name"] = index_name
    keep = [
        "ticker",
        "isin",
        "sedol",
        "mkt_cap",
        "gics_sector",
        "gics_industry_group",
        "gics_industry",
        "gics_sub_industry",
        "index_name",
    ]
    return df[keep].reset_index(drop=True)


# ----------------------------------------------------------------------------
# Stage 1: ticker 完全一致
# ----------------------------------------------------------------------------
def _stage1_direct_join(
    tickers: pd.DataFrame, universe_v2: pd.DataFrame
) -> pd.DataFrame:
    """ticker 完全一致で CIK を解決する.

    universe_v2.ticker と Bloomberg ticker をそのまま join する.
    """
    uv = universe_v2[["cik", "ticker"]].drop_duplicates(subset=["ticker"])
    merged = tickers.merge(uv, on="ticker", how="left")
    resolved = merged[merged["cik"].notna()].copy()
    resolved["cik"] = resolved["cik"].astype("int64")
    return resolved.reset_index(drop=True)


# ----------------------------------------------------------------------------
# Stage 2: '/' → '-' 正規化 + all_tickers 突合
# ----------------------------------------------------------------------------
def _normalize_ticker(t: str) -> str:
    """Bloomberg の ``BF/B`` を EDGAR の ``BF-B`` に正規化."""
    return t.replace("/", "-") if isinstance(t, str) else t


def _all_tickers_to_set(value: Any) -> set[str]:
    """all_tickers 列の値 (list / ndarray / str / NaN) を set[str] に正規化."""
    if value is None:
        return set()
    # pandas/NumPy NaN
    if isinstance(value, float):
        return set()
    if isinstance(value, str):
        return {value}
    # list / ndarray / その他 iterable
    try:
        return {str(x) for x in value if x is not None and not (isinstance(x, float))}
    except TypeError:
        return set()


def _stage2_normalized_join(
    unresolved: pd.DataFrame, universe_v2: pd.DataFrame
) -> pd.DataFrame:
    """'/' → '-' 正規化 + all_tickers (list/string 両対応) 突合.

    1. Bloomberg ticker を正規化 (BF/B → BF-B)
    2. universe_v2 の all_tickers 列を展開した dict[ticker→cik] を構築
    3. 正規化後 ticker でマッチング

    Notes
    -----
    lookup dict 構築は vectorized (explode + dict comprehension) で行う。
    ``iterrows`` を使わないことで universe_v2 が数千行のとき
    10-50x の高速化が見込める。
    """
    # all_tickers 列を vectorize で展開して lookup dict を構築
    lookup: dict[str, int] = {}

    # まず ticker 列 (str 限定) を一括で dict に取り込む
    valid_ticker_mask = universe_v2["ticker"].apply(lambda x: isinstance(x, str))
    ticker_pairs = universe_v2.loc[valid_ticker_mask, ["ticker", "cik"]]
    # 早い者勝ち (setdefault) を保つため iter で順次反映
    for ticker_val, cik_val in zip(
        ticker_pairs["ticker"], ticker_pairs["cik"], strict=True
    ):
        lookup.setdefault(ticker_val, int(cik_val))

    # 次に all_tickers (list/ndarray/string/NaN) を set 化して explode
    if "all_tickers" in universe_v2.columns:
        normalized_sets = universe_v2["all_tickers"].apply(_all_tickers_to_set)
        exploded = (
            pd.DataFrame(
                {"all_tickers_set": normalized_sets, "cik": universe_v2["cik"]}
            )
            .explode("all_tickers_set")
            .dropna(subset=["all_tickers_set"])
        )
        for ticker_val, cik_val in zip(
            exploded["all_tickers_set"], exploded["cik"], strict=True
        ):
            lookup.setdefault(str(ticker_val), int(cik_val))

    if unresolved.empty:
        return pd.DataFrame(columns=pd.Index([*unresolved.columns.tolist(), "cik"]))

    # vectorize: normalized → fallback to raw ticker (Series.map で O(N))
    normalized_series = unresolved["ticker"].map(_normalize_ticker)
    cik_series = normalized_series.map(lookup)
    cik_series = cik_series.where(cik_series.notna(), unresolved["ticker"].map(lookup))

    matched_mask = cik_series.notna()
    if not matched_mask.any():
        return pd.DataFrame(columns=pd.Index([*unresolved.columns.tolist(), "cik"]))

    resolved = unresolved.loc[matched_mask].copy()
    resolved["cik"] = cik_series[matched_mask].astype("int64").to_numpy()
    return resolved.reset_index(drop=True)


# ----------------------------------------------------------------------------
# Stage 3: edgar.Company(ticker) lookup
# ----------------------------------------------------------------------------
def _edgar_company_factory(ticker: str) -> Any:
    """edgartools の Company(ticker) を遅延 import で呼び出す.

    別関数に切り出すことで monkeypatch を容易にする.
    """
    import edgar  # type: ignore[import-untyped]

    if "EDGAR_IDENTITY" in os.environ:
        edgar.set_identity(os.environ["EDGAR_IDENTITY"])
    return edgar.Company(ticker)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _edgar_lookup_with_retry(ticker: str) -> Any:
    """``_edgar_company_factory`` を tenacity でラップして呼び出す.

    Notes
    -----
    monkeypatch でのテスト容易化のため ``_edgar_company_factory`` と分離している。
    retry 設定: ``stop_after_attempt(3)``, ``wait_exponential(min=1, max=8)``,
    ``reraise=True`` (Network 例外を最大 3 回まで指数バックオフ再試行).
    """
    return _edgar_company_factory(ticker)


def _lookup_cik_via_edgar(ticker: str) -> int | None:
    """edgar.Company(ticker) で CIK を引く.

    tenacity で 3 回 retry (指数バックオフ). 全 retry 失敗 / Not Found は None を返す.
    """
    try:
        company = _edgar_lookup_with_retry(ticker)
    except RetryError:
        return None
    except Exception as e:
        log.warning("edgar lookup unexpected error for %s: %s", ticker, e)
        return None

    cik = getattr(company, "cik", None)
    # edgartools は Not Found 時に cik=-999999999 を返す
    if cik is None:
        return None
    try:
        cik_int = int(cik)
    except (TypeError, ValueError):
        return None
    if cik_int < 0:
        return None
    return cik_int


def _stage3_edgar_lookup(
    unresolved: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """edgar.Company(ticker) で未解決銘柄を解決.

    Returns
    -------
    tuple
        (resolved_df, unresolved_list)
    """
    resolved_rows: list[dict[str, Any]] = []
    unresolved_list: list[dict[str, Any]] = []
    for _, row in unresolved.iterrows():
        ticker = row["ticker"]
        cik = _lookup_cik_via_edgar(ticker)
        if cik is None:
            unresolved_list.append(
                {
                    "ticker": ticker,
                    "index_name": row.get("index_name"),
                    "reason": "edgar_not_found",
                }
            )
            continue
        new = row.to_dict()
        new["cik"] = int(cik)
        resolved_rows.append(new)

    if not resolved_rows:
        return (
            pd.DataFrame(columns=pd.Index([*unresolved.columns.tolist(), "cik"])),
            unresolved_list,
        )
    resolved = pd.DataFrame(resolved_rows)
    resolved["cik"] = resolved["cik"].astype("int64")
    return resolved.reset_index(drop=True), unresolved_list


# ----------------------------------------------------------------------------
# 3 段統合
# ----------------------------------------------------------------------------
def resolve_ciks_three_stage(
    tickers: pd.DataFrame, universe_v2: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """3 段フォールバック統合関数.

    各 stage の hit 数を INFO ログに出力する.

    Returns
    -------
    tuple
        (resolved DataFrame, unresolved list[dict])
    """
    total = len(tickers)

    # Stage 1: 直接 join
    s1 = _stage1_direct_join(tickers, universe_v2)
    s1_hit = len(s1)
    log.info("Stage 1: %d/%d hit", s1_hit, total)

    # Stage 1 未解決を抽出
    resolved_tickers = set(s1["ticker"].tolist())
    rest1 = tickers[~tickers["ticker"].isin(resolved_tickers)].copy()

    # Stage 2: 正規化 + all_tickers
    s2 = _stage2_normalized_join(rest1, universe_v2)
    s2_hit = len(s2)
    log.info("Stage 2: +%d (%d/%d)", s2_hit, s1_hit + s2_hit, total)

    resolved_after_s2 = pd.concat([s1, s2], ignore_index=True) if s2_hit else s1
    resolved_tickers_s2 = set(resolved_after_s2["ticker"].tolist())
    rest2 = tickers[~tickers["ticker"].isin(resolved_tickers_s2)].copy()

    # Stage 3: edgar lookup
    s3, unresolved_list = _stage3_edgar_lookup(rest2)
    s3_hit = len(s3)
    log.info(
        "Stage 3: +%d (%d/%d) | unresolved=%d",
        s3_hit,
        s1_hit + s2_hit + s3_hit,
        total,
        len(unresolved_list),
    )

    parts = [df for df in (s1, s2, s3) if len(df) > 0]
    resolved = (
        pd.concat(parts, ignore_index=True)
        if parts
        else pd.DataFrame(columns=pd.Index([*tickers.columns.tolist(), "cik"]))
    )
    if "cik" in resolved.columns and len(resolved) > 0:
        resolved["cik"] = resolved["cik"].astype("int64")
    return resolved, unresolved_list


# ----------------------------------------------------------------------------
# membership 構築
# ----------------------------------------------------------------------------
def build_membership(
    resolved: pd.DataFrame,
    index_names: list[str],
    snapshot_date: str,
) -> pd.DataFrame:
    """CIK 単位で 1 行に集約し in_<index> フラグ + snapshot_date を生成.

    Parameters
    ----------
    resolved : pd.DataFrame
        cik, index_name を含む解決済み DataFrame
    index_names : list[str]
        対象 index 一覧 (例: ['SPX', 'SOX', 'RIY', 'RAY'])
    snapshot_date : str
        スナップショット日付 ('YYYY-MM-DD')
    """
    if len(resolved) == 0:
        cols = ["cik"] + [f"in_{n.lower()}" for n in index_names] + ["snapshot_date"]
        return pd.DataFrame(columns=cols)

    # cik × index_name のクロステーブル
    flags = (
        resolved.assign(_present=True)
        .pivot_table(
            index="cik",
            columns="index_name",
            values="_present",
            aggfunc="any",
            fill_value=False,
        )
        .reset_index()
    )
    # 全 index_names について列を保証
    for idx in index_names:
        if idx not in flags.columns:
            flags[idx] = False
    # rename
    flags = flags.rename(columns={n: f"in_{n.lower()}" for n in index_names})
    flag_cols = [f"in_{n.lower()}" for n in index_names]
    for col in flag_cols:
        flags[col] = flags[col].astype(bool)
    flags["snapshot_date"] = snapshot_date
    flags["cik"] = flags["cik"].astype("int64")
    out_cols = ["cik", *flag_cols, "snapshot_date"]
    return flags[out_cols].sort_values("cik").reset_index(drop=True)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def _setup_logging() -> None:
    """StreamHandler のみの簡易 logging 設定.

    Notes
    -----
    universe_builder は短時間で完了する一回性スクリプトのため、
    ``run_indices.py`` / ``embed_indices.py`` のような FileHandler は持たない。
    """
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt, force=True)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="universe_builder",
        description="indices_v1 universe + membership builder (4 US indices)",
    )
    parser.add_argument(
        "--indices",
        nargs="+",
        default=["SPX", "SOX", "RIY", "RAY"],
        help="対象 index 一覧 (default: SPX SOX RIY RAY)",
    )
    parser.add_argument(
        "--snapshot-date",
        required=True,
        help="snapshot 日付 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--index-dir",
        required=True,
        help="Bloomberg JSON が置かれているディレクトリ",
    )
    parser.add_argument(
        "--universe-out",
        default=str(config.UNIVERSE_INDICES_V1_PARQUET),
        help="universe_indices_v1.parquet 出力パス",
    )
    parser.add_argument(
        "--membership-out",
        default=str(config.MEMBERSHIP_INDICES_V1_PARQUET),
        help="membership_indices_v1.parquet 出力パス",
    )
    parser.add_argument(
        "--unresolved-out",
        default=None,
        help="未解決 ticker を書き出す JSON パス (省略時は universe-out と同じディレクトリ)",
    )
    parser.add_argument(
        "--universe-v2",
        default=str(config.UNIVERSE_PARQUET),
        help="universe_v2.parquet 入力パス",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI エントリポイント."""
    _setup_logging()
    args = _parse_args(argv)

    # snapshot_date のバリデーション (パストラバーサル防止)
    snapshot_date = args.snapshot_date
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", snapshot_date):
        log.error("--snapshot-date must be YYYY-MM-DD, got %r", snapshot_date)
        return 2

    # .env から EDGAR_IDENTITY を取り込み (import 時の副作用を排除し main 内で実行)
    utils.load_edgar_identity_from_env(_ENV_PATH)

    index_dir = Path(args.index_dir)
    log.info("=" * 70)
    log.info("indices_v1 universe builder")
    log.info("=" * 70)
    log.info("indices: %s", args.indices)
    log.info("snapshot_date: %s", snapshot_date)
    log.info("index_dir: %s", index_dir)

    # universe_v2 ロード
    universe_v2_path = Path(args.universe_v2)
    log.info("loading universe_v2: %s", universe_v2_path)
    universe_v2 = pd.read_parquet(universe_v2_path)
    log.info("universe_v2 rows: %d", len(universe_v2))

    # 各 index JSON ロード + 連結
    frames: list[pd.DataFrame] = []
    for idx in args.indices:
        fname = config.INDEX_SOURCES.get(idx)
        if fname is None:
            log.warning("unknown index name (no INDEX_SOURCES entry): %s", idx)
            continue
        json_path = index_dir / fname.format(snapshot_date=snapshot_date)
        if not json_path.exists():
            log.warning("missing index JSON: %s", json_path)
            continue
        df = load_index_json(json_path, index_name=idx)
        log.info("loaded %s: %d rows", idx, len(df))
        frames.append(df)

    if not frames:
        log.error("no index data loaded")
        return 1

    tickers_all = pd.concat(frames, ignore_index=True)
    log.info("total ticker rows (before dedup): %d", len(tickers_all))

    # 3 段フォールバック (index ごとに resolve するため index_name を保ったまま渡す)
    resolved, unresolved_list = resolve_ciks_three_stage(tickers_all, universe_v2)
    log.info("resolved: %d / unresolved: %d", len(resolved), len(unresolved_list))

    # universe parquet (CIK dedup, 最初の出現を採用)
    universe_out = resolved.drop_duplicates(subset=["cik"], keep="first").reset_index(
        drop=True
    )
    # 必須列を確保
    for col in _UNIVERSE_COLUMNS:
        if col not in universe_out.columns:
            universe_out[col] = None
    universe_out = universe_out[_UNIVERSE_COLUMNS]

    universe_out_path = Path(args.universe_out)
    universe_out_path.parent.mkdir(parents=True, exist_ok=True)
    universe_out.to_parquet(universe_out_path, index=False)
    log.info("wrote universe: %s (%d rows)", universe_out_path, len(universe_out))

    # membership parquet
    membership = build_membership(
        resolved, index_names=args.indices, snapshot_date=snapshot_date
    )
    membership_out_path = Path(args.membership_out)
    membership_out_path.parent.mkdir(parents=True, exist_ok=True)
    membership.to_parquet(membership_out_path, index=False)
    log.info("wrote membership: %s (%d rows)", membership_out_path, len(membership))

    # unresolved JSON
    if unresolved_list:
        if args.unresolved_out:
            unresolved_out_path = Path(args.unresolved_out)
        else:
            unresolved_out_path = universe_out_path.parent / "unresolved_tickers.json"
        unresolved_out_path.parent.mkdir(parents=True, exist_ok=True)
        unresolved_out_path.write_text(
            json.dumps(unresolved_list, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log.warning(
            "wrote unresolved tickers: %s (%d entries)",
            unresolved_out_path,
            len(unresolved_list),
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
