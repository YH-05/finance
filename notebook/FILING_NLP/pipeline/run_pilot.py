"""Task #3 パイロット実行: 100 社ランダムサンプリング × ヒストリカル全期間.

実行例:
    uv run python -m notebook.FILING_NLP.pipeline.run_pilot
    uv run python -m notebook.FILING_NLP.pipeline.run_pilot --n 100 --seed 42 --workers 8
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# .env から EDGAR_IDENTITY を読み込み (子プロセスでも使えるよう環境変数で渡す)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_PATH = _REPO_ROOT / ".env"
if _ENV_PATH.exists() and not os.environ.get("EDGAR_IDENTITY"):
    for line in _ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line.startswith("EDGAR_IDENTITY="):
            os.environ["EDGAR_IDENTITY"] = (
                line.split("=", 1)[1].strip().strip('"').strip("'")
            )
            break

import pandas as pd  # noqa: E402

import edgar  # noqa: E402

if "EDGAR_IDENTITY" not in os.environ:
    raise RuntimeError(
        "EDGAR_IDENTITY 環境変数 (または .env) が必要です。 "
        "'Name email@example.com' 形式で設定してください。"
    )
edgar.set_identity(os.environ["EDGAR_IDENTITY"])


# edgartools の legacy parser 警告を抑制
class _LegacyParserFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "falling back to legacy parser" not in record.getMessage()


logging.getLogger("edgar.core").addFilter(_LegacyParserFilter())

# ----------------------------------------------------------------------------
# モジュール import (rate limiter, runner, config)
# ----------------------------------------------------------------------------
sys.path.insert(0, str(_REPO_ROOT))
from notebook.FILING_NLP.pipeline import config, runner  # noqa: E402


def _setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path, encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers, force=True)


def _load_tokenizer():
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(
        config.TOKENIZER_MODEL_ID, trust_remote_code=True
    )
    return tok


def main() -> None:
    parser = argparse.ArgumentParser(description="FILING_NLP v2 pilot runner")
    parser.add_argument("--n", type=int, default=100, help="サンプル銘柄数")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument(
        "--workers",
        type=int,
        default=config.DEFAULT_MAX_WORKERS,
        help="ThreadPoolExecutor の最大 workers 数",
    )
    parser.add_argument(
        "--rate", type=float, default=config.RATE_LIMIT_RPS, help="req/sec 上限"
    )
    parser.add_argument("--run-id", type=str, default="pilot", help="run id (出力名)")
    args = parser.parse_args()

    # 出力先 (NAS)
    nas = config.NAS_ROOT
    sections_dir = nas / "sections" / args.run_id
    chunks_dir = nas / "chunks" / args.run_id
    filings_dir = nas / "filings_metadata" / args.run_id
    checkpoint_path = nas / "checkpoints" / f"{args.run_id}_progress.json"
    errors_path = nas / "logs" / f"{args.run_id}_errors.jsonl"
    log_path = nas / "logs" / f"{args.run_id}_run.log"

    _setup_logging(log_path)
    log = logging.getLogger("pilot")
    log.info("=" * 80)
    log.info("PILOT RUN: %s", args.run_id)
    log.info("=" * 80)
    log.info("args: %s", vars(args))
    log.info("EDGAR_IDENTITY: %s", os.environ.get("EDGAR_IDENTITY"))
    log.info("output sections: %s", sections_dir)
    log.info("output chunks:   %s", chunks_dir)
    log.info("checkpoint:      %s", checkpoint_path)
    log.info("errors log:      %s", errors_path)

    # Universe ロード
    log.info("loading universe from %s", config.UNIVERSE_PARQUET)
    universe = pd.read_parquet(config.UNIVERSE_PARQUET)
    log.info("universe size: %d companies", len(universe))

    # ランダムサンプリング
    sample = universe.sample(n=args.n, random_state=args.seed).reset_index(drop=True)
    log.info(
        "sampled %d CIKs (seed=%d). exchange dist: %s",
        len(sample),
        args.seed,
        sample["exchange"].value_counts().to_dict(),
    )
    log.info(
        "sample tickers head: %s",
        sample[["cik", "ticker", "exchange", "company"]]
        .head(10)
        .to_string(index=False),
    )

    # Tokenizer
    log.info("loading tokenizer: %s", config.TOKENIZER_MODEL_ID)
    tokenizer = _load_tokenizer()
    log.info("tokenizer ready: %s", type(tokenizer).__name__)

    # 実行
    log.info("starting pipeline with workers=%d rate=%.1f rps", args.workers, args.rate)
    summary = runner.run_pipeline(
        universe=sample,
        tokenizer=tokenizer,
        sections_dir=sections_dir,
        chunks_dir=chunks_dir,
        filings_metadata_dir=filings_dir,
        checkpoint_path=checkpoint_path,
        errors_path=errors_path,
        max_workers=args.workers,
        rate_rps=args.rate,
    )

    log.info("=" * 80)
    log.info("PILOT FINISHED")
    log.info("=" * 80)
    for k, v in summary.items():
        log.info("  %s: %s", k, v)

    # サマリ別ファイル保存
    summary_path = nas / "logs" / f"{args.run_id}_summary.json"
    import json

    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("summary saved: %s", summary_path)


if __name__ == "__main__":
    main()
