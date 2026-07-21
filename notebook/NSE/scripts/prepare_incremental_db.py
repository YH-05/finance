"""前回版 DB をコピーし、増分更新作業用の「今回版」DB を作成する.

sqlite3.Connection.backup() を使用したオンラインバックアップにより、
WAL モードでの未チェックポイントデータも含めて安全に複製する。

入力:
- --source-db で指定する SQLite DB ファイル（コピー元、前回版）

出力:
- --target-db で指定する SQLite DB ファイル（コピー先、今回作業用）
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_DB = ROOT / "notebook/NSE/data/cache/nse/nse_index.db"
DEFAULT_TARGET_DB = ROOT / "notebook/NSE/data/cache/nse/nse_index_20260630.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="前回版 DB のコピーから増分更新作業用の今回版 DB を作成する"
    )
    parser.add_argument(
        "--source-db",
        type=Path,
        default=DEFAULT_SOURCE_DB,
        help=f"コピー元 DB ファイルパス（デフォルト: {DEFAULT_SOURCE_DB}）",
    )
    parser.add_argument(
        "--target-db",
        type=Path,
        default=DEFAULT_TARGET_DB,
        help=f"コピー先 DB ファイルパス（デフォルト: {DEFAULT_TARGET_DB}）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="target-db が既に存在する場合に上書きする",
    )
    return parser.parse_args()


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_db(source_db: Path, target_db: Path) -> None:
    log.info(f"Backing up {source_db} -> {target_db}")
    src_conn = sqlite3.connect(source_db)
    try:
        dst_conn = sqlite3.connect(target_db)
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()


def main() -> None:
    args = parse_args()

    if not args.source_db.exists():
        raise FileNotFoundError(f"source-db が見つかりません: {args.source_db}")

    if args.target_db.exists() and not args.force:
        raise FileExistsError(
            f"target-db が既に存在します: {args.target_db}"
            "（上書きする場合は --force を指定してください）"
        )

    backup_db(args.source_db, args.target_db)

    source_size = args.source_db.stat().st_size
    target_size = args.target_db.stat().st_size
    source_hash = sha256sum(args.source_db)
    target_hash = sha256sum(args.target_db)

    log.info(f"Source: {args.source_db}")
    log.info(f"  size={source_size:,} bytes, sha256={source_hash}")
    log.info(f"Target: {args.target_db}")
    log.info(f"  size={target_size:,} bytes, sha256={target_hash}")

    if source_hash == target_hash:
        log.info("整合性確認: OK（ハッシュ一致）")
    else:
        log.info(
            "整合性確認: ハッシュ不一致（sqlite3 backup API はページ配置の都合で"
            "バイト単位一致しない場合がある。論理内容の一致はテーブル件数で確認すること）"
        )


if __name__ == "__main__":
    main()
