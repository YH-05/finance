"""indices_v1 パイプライン共通ユーティリティ.

`run_indices.py`, `embed_indices.py`, `universe_builder.py` で重複していた
以下の処理を集約する:

- ``load_edgar_identity_from_env``: ``.env`` からの EDGAR_IDENTITY 読み込み
- ``setup_pipeline_logging``: StreamHandler + FileHandler の logging 初期化
- ``assert_nas_mounted``: NAS マウント検証 (fail-fast)
- ``validate_index_filter``: index_filter 列名のバリデーション
- ``mask_edgar_identity``: ログ出力用の個人情報マスキング
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path

# index_filter として受け付ける値 (membership parquet の列名と一致)
INDEX_FILTER_CHOICES: tuple[str, ...] = ("in_spx", "in_sox", "in_riy", "in_ray")


def load_edgar_identity_from_env(env_path: Path) -> bool:
    """``.env`` ファイルから EDGAR_IDENTITY を読み込み環境変数に注入する.

    既に環境変数が設定されている場合はスキップする。

    Parameters
    ----------
    env_path : Path
        ``.env`` ファイルのパス.

    Returns
    -------
    bool
        環境変数を新規設定した場合 True、既存値がある/ファイルが存在しない場合 False.
    """
    if not env_path.exists():
        return False
    if os.environ.get("EDGAR_IDENTITY"):
        return False
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if line.startswith("EDGAR_IDENTITY="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                os.environ["EDGAR_IDENTITY"] = value
                return True
            return False
    return False


def mask_edgar_identity(identity: str | None) -> str:
    """EDGAR_IDENTITY をログ出力用にマスクする.

    EDGAR_IDENTITY は ``"FirstName LastName email@example.com"`` 形式で個人情報を含む。
    NAS 共有環境のログファイルへの平文出力を避けるため、姓名の先頭トークンのみ残す。

    Parameters
    ----------
    identity : str | None
        EDGAR_IDENTITY 環境変数の値.

    Returns
    -------
    str
        ``"FirstName ***"`` 形式 (未設定の場合は ``"(not set)"``).
    """
    if not identity:
        return "(not set)"
    head = identity.split(maxsplit=1)[0]
    return f"{head} ***"


def setup_pipeline_logging(run_id: str, logs_dir: Path, *, suffix: str = "run") -> Path:
    """StreamHandler + FileHandler の logging 設定を行う.

    Parameters
    ----------
    run_id : str
        ログファイル名のプレフィックス.
    logs_dir : Path
        ログ出力ディレクトリ (存在しなければ作成).
    suffix : str
        ログファイル名のサフィックス (デフォルト ``"run"``).
        ``"{run_id}_{suffix}.log"`` 形式でファイル名が決まる.

    Returns
    -------
    Path
        実際に書き込まれるログファイルのパス.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{run_id}_{suffix}.log"
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path, encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers, force=True)
    return log_path


def assert_nas_mounted(nas_root: Path) -> None:
    """NAS マウントポイントが存在することを検証 (fail-fast).

    存在しない場合は ``SystemExit(2)`` で即時終了する。

    Parameters
    ----------
    nas_root : Path
        NAS ルートディレクトリ (``config.NAS_ROOT``).

    Raises
    ------
    SystemExit
        NAS が未マウントの場合 (exit code 2).
    """
    if not nas_root.exists():
        msg = (
            f"NAS not mounted: {nas_root}\n"
            "Please mount the personal_folder volume before running this pipeline."
        )
        sys.stderr.write(msg + "\n")
        raise SystemExit(2)


def validate_index_filter(index_filter: str, membership: pd.DataFrame) -> None:
    """``index_filter`` 引数が membership parquet の列として存在することを検証.

    Parameters
    ----------
    index_filter : str
        絞り込みに使う列名 (``in_spx`` など).
    membership : pd.DataFrame
        membership parquet をロードした DataFrame.

    Raises
    ------
    ValueError
        指定された列が存在しない場合.
    """
    if index_filter not in membership.columns:
        msg = (
            f"index_filter {index_filter!r} not found in membership columns: "
            f"{list(membership.columns)}"
        )
        raise ValueError(msg)
