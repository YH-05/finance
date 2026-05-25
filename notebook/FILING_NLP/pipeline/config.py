"""パイプライン全体の定数とパス."""

from __future__ import annotations

from pathlib import Path

# === NAS ストレージ ===
NAS_ROOT = Path("/Volumes/personal_folder/Quants/FILING_NLP_v2")
UNIVERSE_DIR = NAS_ROOT / "universe"
UNIVERSE_PARQUET = UNIVERSE_DIR / "universe_v2.parquet"
FILINGS_METADATA_DIR = NAS_ROOT / "filings_metadata"
SECTIONS_DIR = NAS_ROOT / "sections"
CHUNKS_DIR = NAS_ROOT / "chunks"
CHECKPOINTS_DIR = NAS_ROOT / "checkpoints"
LOGS_DIR = NAS_ROOT / "logs"

# === Filter rules (確定済み判断) ===
# Q1: amendment 除外 (原版のみ)
FORMS_TARGET: tuple[str, ...] = ("10-K", "10-Q")
FORMS_EXCLUDE: tuple[str, ...] = ("10-K/A", "10-Q/A")

# Q2: 2002 年以降 (HTML 必須化以降)
YEAR_CUTOFF = 2002

# === Item specs (form ごと) ===
# (section_key, section_role, part, item)
ITEM_SPECS_10K: list[tuple[str, str, str, str]] = [
    ("item_1", "business", "Part I", "Item 1"),
    ("item_1a", "risk_factors", "Part I", "Item 1A"),
    ("item_7", "mda", "Part II", "Item 7"),
]
ITEM_SPECS_10Q: list[tuple[str, str, str, str]] = [
    ("item_1a", "risk_factors", "Part II", "Item 1A"),
    ("item_2", "mda", "Part I", "Item 2"),
]
ITEM_SPECS_BY_FORM: dict[str, list[tuple[str, str, str, str]]] = {
    "10-K": ITEM_SPECS_10K,
    "10-Q": ITEM_SPECS_10Q,
}

# === Chunking ===
MAX_TOKENS = 1024
TOKENIZER_MODEL_ID = "Alibaba-NLP/gte-Qwen2-1.5B-instruct"

# === Rate limit / parallelism ===
# SEC 公式 ~10 req/sec 上限。安全マージン取って 5 req/sec。
RATE_LIMIT_RPS = 5.0
RATE_LIMIT_BURST = 10
DEFAULT_MAX_WORKERS = 8

# === HF cache (tokenizer) ===
HF_CACHE_DIR = Path.home() / ".cache" / "huggingface"

# ============================================================
# indices_v1 用定数 (act-101 / act-105)
# ============================================================
UNIVERSE_INDICES_V1_PARQUET: Path = (
    NAS_ROOT / "universe" / "universe_indices_v1.parquet"
)
MEMBERSHIP_INDICES_V1_PARQUET: Path = (
    NAS_ROOT / "index_membership" / "membership_indices_v1.parquet"
)
EMBEDDINGS_DIR: Path = NAS_ROOT / "embeddings"
INDICES_V1_PROGRESS_PATH: Path = CHECKPOINTS_DIR / "indices_v1_progress.json"
INDICES_V1_EMBED_PROGRESS_PATH: Path = (
    CHECKPOINTS_DIR / "indices_v1_embed_progress.json"
)

# Embedding (gte-Qwen2-1.5B-instruct, MPS bfloat16)
EMBEDDING_BATCH_SIZE: int = 16
EMBEDDING_MAX_LENGTH: int = 512
EMBEDDING_DTYPE: str = "bfloat16"
EMBEDDING_DEVICE: str = "mps"
EMBEDDING_VECTOR_DIM: int = 1536

# 4 インデックス JSON ファイル名パターン (snapshot_date と組み合わせ)
INDEX_SOURCES: dict[str, str] = {
    "SPX": "{snapshot_date}_SPX Index.json",
    "SOX": "{snapshot_date}_SOX Index.json",
    "RIY": "{snapshot_date}_RIY Index.json",
    "RAY": "{snapshot_date}_RAY Index.json",
}
