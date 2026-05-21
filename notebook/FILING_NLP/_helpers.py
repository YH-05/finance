"""FILING_NLP 実験用の共通ユーティリティ.

重要: このモジュールは ``transformers`` / ``sentence_transformers`` を
import する前にロードすること。``setup_hf_cache()`` がモジュール
トップで実行され、``HF_HOME`` を ``notebook/FILING_NLP/data/hf_cache``
に切り替える。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# パス定数
# ---------------------------------------------------------------------------

# このファイルがある notebook/FILING_NLP/ 直下
PKG_DIR: Path = Path(__file__).resolve().parent

# リポジトリルート ( notebook/FILING_NLP/_helpers.py → quants/ )
REPO_ROOT: Path = PKG_DIR.parent.parent

DATA_DIR: Path = PKG_DIR / "data"
HF_CACHE_DIR: Path = DATA_DIR / "hf_cache"
EDGAR_CACHE_DIR: Path = DATA_DIR / "edgar_cache"

FILINGS_PARQUET: Path = DATA_DIR / "filings.parquet"
SECTIONS_PARQUET: Path = DATA_DIR / "sections.parquet"
CHUNKS_PARQUET: Path = DATA_DIR / "chunks.parquet"
SENTIMENTS_PARQUET: Path = DATA_DIR / "sentiments.parquet"
EMBEDDINGS_PARQUET: Path = DATA_DIR / "embeddings.parquet"
ENTITIES_PARQUET: Path = DATA_DIR / "entities.parquet"
ENTITIES_GLINER_PARQUET: Path = DATA_DIR / "entities_gliner.parquet"


# ---------------------------------------------------------------------------
# HF キャッシュ設定 (transformers/sentence_transformers の import 前に必須)
# ---------------------------------------------------------------------------


def setup_hf_cache() -> Path:
    """HuggingFace のモデルキャッシュを notebook/FILING_NLP/data/hf_cache に向ける.

    Returns
    -------
    Path
        設定された HF_HOME のパス
    """
    HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(HF_CACHE_DIR)
    # HF v0.20+ では HUGGINGFACE_HUB_CACHE も有効
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(HF_CACHE_DIR / "hub")
    # MPS 上での未実装演算が出た場合は CPU フォールバック
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    return HF_CACHE_DIR


# モジュール import 時に自動実行
_HF_HOME = setup_hf_cache()


# ---------------------------------------------------------------------------
# SEC EDGAR identity 設定
# ---------------------------------------------------------------------------


def setup_edgar() -> str:
    """SEC EDGAR identity を .env から読み込み登録する.

    Returns
    -------
    str
        登録した identity 文字列

    Raises
    ------
    RuntimeError
        EDGAR_IDENTITY 環境変数が未設定の場合
    """
    identity = os.environ.get("EDGAR_IDENTITY")
    if not identity:
        # .env を直接読む（python-dotenv は依存に入っていないため手動パース）
        env_path = PKG_DIR.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("EDGAR_IDENTITY="):
                    identity = line.split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ["EDGAR_IDENTITY"] = identity
                    break
    if not identity:
        msg = (
            "EDGAR_IDENTITY が未設定です。.env に "
            "'EDGAR_IDENTITY=Name email@example.com' 形式で追加してください。"
        )
        raise RuntimeError(msg)

    # edgartools の set_identity は "Name email" 形式の単一文字列を受け取る
    import edgar

    edgar.set_identity(identity)
    return identity


# ---------------------------------------------------------------------------
# Torch device (Apple Silicon MPS を前提)
# ---------------------------------------------------------------------------


def get_device():  # type: ignore[no-untyped-def]
    """利用可能な torch device を返す（MPS 優先、なければ CPU）.

    Returns
    -------
    torch.device
        device 識別子
    """
    import torch

    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return torch.device("mps")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# セクション抽出は edgartools のネイティブ API に委譲
# ---------------------------------------------------------------------------
# 自前の正規表現抽出は廃止。notebook 側で以下を直接呼び出す:
#   - 10-K: filing.obj().risk_factors / .management_discussion (str)
#   - 10-Q: filing.obj()['Part II, Item 1A'] / ['Part I, Item 2']  (str | None)


# ---------------------------------------------------------------------------
# トークナイザベース・スライディングウィンドウ・チャンク化
# ---------------------------------------------------------------------------


def chunk_text(
    text: str,
    tokenizer,  # type: ignore[no-untyped-def]
    max_tokens: int = 510,
    stride: int = 128,
) -> list[str]:
    """テキストをトークン数ベースでスライディング分割する.

    BERT 系の 512 トークン制限（CLS/SEP を除く 510）に合わせる。
    ``stride`` 分の重複を持たせて文脈の連続性を保つ。

    Parameters
    ----------
    text : str
        対象テキスト
    tokenizer : transformers.PreTrainedTokenizer
        対応モデルのトークナイザ
    max_tokens : int
        1 チャンクあたり最大トークン数（特殊トークン除く）
    stride : int
        前チャンクとの重複トークン数

    Returns
    -------
    list[str]
        トークン境界で decode されたチャンク文字列リスト
    """
    if not text or not text.strip():
        return []

    encoding = tokenizer(
        text,
        add_special_tokens=False,
        truncation=False,
        return_attention_mask=False,
        return_offsets_mapping=False,
    )
    token_ids: list[int] = encoding["input_ids"]

    if len(token_ids) <= max_tokens:
        return [text]

    chunks: list[str] = []
    start = 0
    step = max_tokens - stride
    if step <= 0:
        msg = f"max_tokens ({max_tokens}) must exceed stride ({stride})"
        raise ValueError(msg)
    while start < len(token_ids):
        window = token_ids[start : start + max_tokens]
        chunk = tokenizer.decode(window, skip_special_tokens=True)
        chunks.append(chunk)
        if start + max_tokens >= len(token_ids):
            break
        start += step
    return chunks


# ---------------------------------------------------------------------------
# モデルロード（FinBERT / sentence-transformers）
# ---------------------------------------------------------------------------

FINBERT_MODEL_ID: str = "yiyanghkust/finbert-tone"
EMBEDDER_MODEL_ID: str = "BAAI/bge-large-en-v1.5"


def load_finbert(device=None):  # type: ignore[no-untyped-def]
    """FinBERT (yiyanghkust/finbert-tone) をロードする.

    Returns
    -------
    tuple
        (tokenizer, model) を返す。``model`` は ``.eval()`` 済み・指定 device 配置。
    """
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if device is None:
        device = get_device()

    tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL_ID)
    model.to(device)
    model.eval()
    return tokenizer, model


def load_embedder(device=None):  # type: ignore[no-untyped-def]
    """BAAI/bge-large-en-v1.5 を SentenceTransformer でロードする.

    Returns
    -------
    sentence_transformers.SentenceTransformer
        embedding モデル。``.encode()`` で使用。
    """
    from sentence_transformers import SentenceTransformer

    if device is None:
        device = get_device()

    model = SentenceTransformer(EMBEDDER_MODEL_ID, device=str(device))
    return model


# ---------------------------------------------------------------------------
# logger (notebook で使う想定)
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)
