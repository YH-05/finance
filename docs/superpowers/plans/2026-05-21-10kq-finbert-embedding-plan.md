# 10-K/10-Q × FinBERT × Embedding 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AAPL/MSFT/GOOGL × 過去5年の 10-K + 10-Q を対象に、notebook/FILING_NLP/ 配下で FinBERT センチメント分析と bge embedding によるテキスト変化検知・クラスタリングを実験する環境を構築する。

**Architecture:** 既存 `src/edgar` をそのまま利用してファイリング取得・セクション抽出。`notebook/FILING_NLP/_helpers.py` に薄い共通ユーティリティ（HF_HOME 設定、MPS device、10-Q セクションパターン、チャンク化、モデルロード）。3 個の .ipynb は `scripts/build_filing_nlp_notebooks.py` で `nbformat` から生成する。中間データは `notebook/FILING_NLP/data/` 配下に Parquet 5 ファイル（gitignore 対象）。

**Tech Stack:** Python 3.12 / uv / torch (MPS) / transformers / sentence-transformers / umap-learn / nbformat / pandas / pyarrow / plotly

**Spec:** [docs/superpowers/specs/2026-05-21-10kq-finbert-embedding-design.md](../specs/2026-05-21-10kq-finbert-embedding-design.md)

---

## Task 1: 依存パッケージを追加し uv sync する

**Files:**
- Modify: `pyproject.toml:60-63`（既存 `dependencies` リスト末尾。`"xlwings>=0.35.0",` の直後に追加）

- [ ] **Step 1: pyproject.toml の dependencies に 4 パッケージを追加**

`pyproject.toml` の `dependencies` リスト（行 7 から始まる）の末尾、`"xlwings>=0.35.0",`（行 62）の直後に以下を追加:

```toml
    # NLP for filings (10-K/10-Q FinBERT + embedding)
    "torch>=2.3.0,<3.0.0",
    "transformers>=4.40.0,<5.0.0",
    "sentence-transformers>=3.0.0",
    "umap-learn>=0.5.5",
```

- [ ] **Step 2: 依存解決を実行**

Run: `cd /Users/yukihata/Desktop/quants && uv sync`
Expected: 新パッケージ4つ（torch, transformers, sentence-transformers, umap-learn）+ 推移的依存（tokenizers, safetensors, scikit-learn, numba, llvmlite 等）が解決・インストールされる。エラーなく完了すること。

- [ ] **Step 3: torch が MPS を認識できるか確認**

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "import torch; print('mps:', torch.backends.mps.is_available(), torch.backends.mps.is_built())"
```
Expected: `mps: True True`（Apple Silicon かつ macOS 12.3+ の前提）

- [ ] **Step 4: コミット**

```bash
git add pyproject.toml uv.lock
git commit -m "$(cat <<'EOF'
build(deps): torch/transformers/sentence-transformers/umap-learn を追加

10-K/10-Q × FinBERT × embedding 実験 (notebook/FILING_NLP/) で使用。
FinBERT (yiyanghkust/finbert-tone) と BAAI/bge-large-en-v1.5 を MPS 上で
推論するためのバックエンド・ラッパーと、可視化用 UMAP を追加。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: ディレクトリ作成 + .gitignore 設定 + .env 確認

**Files:**
- Create: `notebook/FILING_NLP/` （空ディレクトリ）
- Create: `notebook/FILING_NLP/data/hf_cache/`
- Create: `notebook/FILING_NLP/data/edgar_cache/`
- Modify: `.gitignore`（末尾に追加）
- Read: `.env`（EDGAR_IDENTITY 確認）

- [ ] **Step 1: 必要なディレクトリを作成**

Run:
```bash
cd /Users/yukihata/Desktop/quants
mkdir -p notebook/FILING_NLP/data/hf_cache
mkdir -p notebook/FILING_NLP/data/edgar_cache
```

- [ ] **Step 2: .gitignore の末尾に notebook/FILING_NLP/data/ を追加**

`.gitignore` の末尾（最終行 `research/ca_strategy_poc/workspace/` の後）に以下を追加:

```
# FILING_NLP experiment data (HF cache 1.7GB + edgar cache + intermediate parquets)
notebook/FILING_NLP/data/
```

- [ ] **Step 3: .env に EDGAR_IDENTITY が設定されているか確認**

Run: `grep -i "EDGAR_IDENTITY" /Users/yukihata/Desktop/quants/.env || echo "NOT SET"`
Expected: 既に設定されていれば値が表示される。`NOT SET` の場合は次の Step で追加する。

- [ ] **Step 4: 未設定なら .env に EDGAR_IDENTITY を追加**

`EDGAR_IDENTITY` が未設定の場合のみ、`.env` の末尾に以下の行を追加（YH-05 のメールを使用）:

```
EDGAR_IDENTITY=YH-05 youxitiancore@gmail.com
```

SEC EDGAR の Fair Access Policy では「氏名 メールアドレス」形式が推奨される。`.env` は既に `.gitignore` 対象のため、コミット不要。

- [ ] **Step 5: ディレクトリ作成を確認**

Run: `ls -la /Users/yukihata/Desktop/quants/notebook/FILING_NLP/data/`
Expected: `hf_cache/` と `edgar_cache/` の 2 ディレクトリが表示される。

- [ ] **Step 6: コミット**

```bash
cd /Users/yukihata/Desktop/quants
git add .gitignore
git commit -m "$(cat <<'EOF'
chore(gitignore): notebook/FILING_NLP/data/ を除外

HF モデルキャッシュ (~1.7GB) と edgar キャッシュ・中間 Parquet を
プロジェクト外に持ち出さないため gitignore 対象に追加。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: _helpers.py 初版（パス定数 + HF_HOME 設定 + edgar identity + device）

**Files:**
- Create: `notebook/FILING_NLP/_helpers.py`

- [ ] **Step 1: _helpers.py を新規作成（パス定数 + setup_hf_cache + setup_edgar + get_device）**

`notebook/FILING_NLP/_helpers.py` に以下の内容を書く:

```python
"""FILING_NLP 実験用の共通ユーティリティ.

重要: このモジュールは ``transformers`` / ``sentence_transformers`` を
import する前にロードすること。``setup_hf_cache()`` がモジュール
トップで実行され、``HF_HOME`` を ``notebook/FILING_NLP/data/hf_cache``
に切り替える。
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# パス定数
# ---------------------------------------------------------------------------

# このファイルがある notebook/FILING_NLP/ 直下
PKG_DIR: Path = Path(__file__).resolve().parent

DATA_DIR: Path = PKG_DIR / "data"
HF_CACHE_DIR: Path = DATA_DIR / "hf_cache"
EDGAR_CACHE_DIR: Path = DATA_DIR / "edgar_cache"

FILINGS_PARQUET: Path = DATA_DIR / "filings.parquet"
SECTIONS_PARQUET: Path = DATA_DIR / "sections.parquet"
CHUNKS_PARQUET: Path = DATA_DIR / "chunks.parquet"
SENTIMENTS_PARQUET: Path = DATA_DIR / "sentiments.parquet"
EMBEDDINGS_PARQUET: Path = DATA_DIR / "embeddings.parquet"

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

    # 既存の edgar.config.set_identity を使う
    parts = identity.rsplit(" ", 1)
    if len(parts) == 2:
        name, email = parts
    else:
        name, email = "Anonymous", identity

    from edgar.config import set_identity

    set_identity(name, email)
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
# logger (notebook で使う想定)
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)
```

- [ ] **Step 2: import スモーク (HF_HOME / device / edgar identity)**

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "
import sys
sys.path.insert(0, 'notebook/FILING_NLP')
import _helpers
print('HF_HOME:', _helpers.HF_CACHE_DIR)
print('HF_HOME env:', __import__('os').environ.get('HF_HOME'))
print('device:', _helpers.get_device())
identity = _helpers.setup_edgar()
print('identity:', identity)
"
```
Expected:
- `HF_HOME: .../notebook/FILING_NLP/data/hf_cache`
- `HF_HOME env: .../notebook/FILING_NLP/data/hf_cache`
- `device: mps`
- `identity:` の後に `.env` の値が表示される

EDGAR_IDENTITY 未設定の場合、`RuntimeError` で停止すること。Task 2 Step 4 を実施したか確認。

- [ ] **Step 3: コミット**

```bash
git add notebook/FILING_NLP/_helpers.py
git commit -m "$(cat <<'EOF'
feat(filing_nlp): _helpers.py 初版 (HF cache/edgar identity/device)

notebook/FILING_NLP/ 配下の実験用共通ユーティリティ。
- setup_hf_cache: HF_HOME をプロジェクト内 hf_cache へ切替（import 時自動実行）
- setup_edgar: .env から EDGAR_IDENTITY 読込 + edgar.config.set_identity
- get_device: Apple Silicon MPS 優先 (CPU フォールバック)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: _helpers.py に 10-Q セクションパターン + チャンク化を追加

**Files:**
- Modify: `notebook/FILING_NLP/_helpers.py`（末尾に追加）

- [ ] **Step 1: SECTION_PATTERNS_10Q を _helpers.py に追加**

`notebook/FILING_NLP/_helpers.py` の末尾（logger 定義の後）に以下を追加:

```python
# ---------------------------------------------------------------------------
# 10-Q セクションパターン (edgar.SectionExtractor の custom_patterns 用)
# ---------------------------------------------------------------------------

# 10-Q の構造: Part I (Financial Information) / Part II (Other Information)
# - Part I Item 2: Management's Discussion and Analysis (MD&A) → 10-K の Item 7 相当
# - Part II Item 1A: Risk Factors → 10-K の Item 1A 相当
# キー名は 10-K の SectionKey 値に揃え、後段の集計で同じカラムで扱えるようにする。
SECTION_PATTERNS_10Q: dict[str, re.Pattern[str]] = {
    "item_7": re.compile(  # MD&A (Part I Item 2)
        r"(?i)item\s+2[\.\s]+management'?s?\s+discussion\s+and\s+analysis",
    ),
    "item_1a": re.compile(  # Risk Factors (Part II Item 1A)
        r"(?i)item\s+1a[\.\s]+risk\s+factors",
    ),
}
```

- [ ] **Step 2: chunk_text を _helpers.py に追加**

同ファイル末尾に以下を追加:

```python
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
```

- [ ] **Step 3: chunk_text スモーク (FinBERT トークナイザはまだなので bert-base-uncased で試す)**

注意: ここでは公開済みかつ軽量な `bert-base-uncased` を使うのではなく、Task 5 で FinBERT をロードしてからチャンク化スモークを行う方がモデル DL を一回で済ませられる。本タスクでは関数定義の構文確認のみ行う:

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "
import sys
sys.path.insert(0, 'notebook/FILING_NLP')
import _helpers
print('SECTION_PATTERNS_10Q keys:', list(_helpers.SECTION_PATTERNS_10Q.keys()))
print('chunk_text signature:', _helpers.chunk_text.__doc__.splitlines()[0])
"
```
Expected:
- `SECTION_PATTERNS_10Q keys: ['item_7', 'item_1a']`
- `chunk_text signature: テキストをトークン数ベースでスライディング分割する.`

- [ ] **Step 4: コミット**

```bash
git add notebook/FILING_NLP/_helpers.py
git commit -m "$(cat <<'EOF'
feat(filing_nlp): 10-Q セクションパターンとトークンベースチャンク化を追加

- SECTION_PATTERNS_10Q: edgar.SectionExtractor の custom_patterns 用。
  10-Q の Part I Item 2 (MD&A) と Part II Item 1A (Risk Factors) を
  10-K の SectionKey 値 (item_7 / item_1a) に揃えて定義。
- chunk_text: BERT 系 512 上限に合わせ max_tokens=510, stride=128 で
  スライディング分割。FinBERT / bge いずれにも流用可能。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: _helpers.py に FinBERT/embedding モデルロード追加 + 初回 DL スモーク

**Files:**
- Modify: `notebook/FILING_NLP/_helpers.py`（末尾に追加）

⚠️ **このタスクで初回 ~1.7GB のモデルダウンロードが発生します。インターネット環境とディスク空き容量を確認してから実行してください。**

- [ ] **Step 1: load_finbert / load_embedder を _helpers.py に追加**

ファイル末尾に以下を追加:

```python
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
    import torch  # noqa: F401  (ensure available)
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
```

- [ ] **Step 2: FinBERT 初回 DL + 1 サンプル推論スモーク**

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "
import sys, time
sys.path.insert(0, 'notebook/FILING_NLP')
import _helpers
t0 = time.time()
tok, mdl = _helpers.load_finbert()
print(f'FinBERT loaded in {time.time()-t0:.1f}s; device={next(mdl.parameters()).device}')
import torch
enc = tok('Apple revenue grew strongly this quarter.', return_tensors='pt').to(next(mdl.parameters()).device)
with torch.no_grad():
    out = mdl(**enc)
probs = out.logits.softmax(dim=-1).cpu().numpy()[0]
print('label order:', mdl.config.id2label)
print('probs:', dict(zip(mdl.config.id2label.values(), probs.round(3))))
"
```
Expected:
- 初回は数十秒〜数分かけてモデル DL（`hf_cache/` 配下に保存）
- `device=mps:0`（MPS 利用時）
- `probs` で `{'Positive': ~0.9, 'Negative': ~0.0, 'Neutral': ~0.1}` 程度（センチメントが positive 寄り）

- [ ] **Step 3: chunk_text スモーク (FinBERT トークナイザで実テキスト)**

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "
import sys
sys.path.insert(0, 'notebook/FILING_NLP')
import _helpers
tok, _ = _helpers.load_finbert()
text = 'The Company faces material risks. ' * 200  # 約 1200 トークン
chunks = _helpers.chunk_text(text, tok, max_tokens=510, stride=128)
print('input chars:', len(text), 'chunks:', len(chunks))
for i, c in enumerate(chunks):
    print(f'  chunk[{i}] tokens={len(tok.encode(c, add_special_tokens=False))}')
"
```
Expected:
- 3 チャンク前後生成され、各チャンクのトークン数が 510 以下
- 隣接チャンクで重複部分が見える

- [ ] **Step 4: embedder 初回 DL + 1 サンプル encode スモーク**

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "
import sys, time
sys.path.insert(0, 'notebook/FILING_NLP')
import _helpers
t0 = time.time()
model = _helpers.load_embedder()
print(f'embedder loaded in {time.time()-t0:.1f}s; device={model.device}')
vec = model.encode(['Apple 10-K risk factors.'], normalize_embeddings=True)
print('shape:', vec.shape, 'norm:', float((vec**2).sum()**0.5))
"
```
Expected:
- 初回は数分かけて bge-large-en-v1.5 を DL（~1.3GB）
- `shape: (1, 1024)` `norm: 1.0`（normalize_embeddings=True のため）

- [ ] **Step 5: HF キャッシュサイズ確認**

Run: `du -sh /Users/yukihata/Desktop/quants/notebook/FILING_NLP/data/hf_cache/`
Expected: `1.5G` 前後（FinBERT ~440MB + bge ~1.3GB）

- [ ] **Step 6: コミット**

```bash
git add notebook/FILING_NLP/_helpers.py
git commit -m "$(cat <<'EOF'
feat(filing_nlp): FinBERT / bge-large-en-v1.5 モデルロード関数を追加

- load_finbert: yiyanghkust/finbert-tone を transformers でロード、
  指定 device (MPS 既定) に配置・eval モード。
- load_embedder: BAAI/bge-large-en-v1.5 を SentenceTransformer でロード。
- FINBERT_MODEL_ID / EMBEDDER_MODEL_ID: モデル ID 定数。

スモーク確認: FinBERT は MPS で 1 文の pos/neg/neu 推論成功、
embedder は 1024 次元・正規化済みベクトルを返却。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: scripts/build_filing_nlp_notebooks.py を作成し 3 .ipynb を生成

**Files:**
- Create: `scripts/build_filing_nlp_notebooks.py`
- Create: `notebook/FILING_NLP/01_fetch_and_chunk.ipynb`
- Create: `notebook/FILING_NLP/02_finbert_sentiment.ipynb`
- Create: `notebook/FILING_NLP/03_embedding_analysis.ipynb`

実験 notebook を再現性高く管理するため、`nbformat` で .ipynb をスクリプトから生成する。notebook を直接編集する代わりに、このスクリプトを編集・再実行する運用を取る（既存依存 `nbformat>=5.10.4` を利用、追加インストール不要）。

- [ ] **Step 1: scripts/build_filing_nlp_notebooks.py を新規作成（フレーム + 01 ノートブック定義）**

`scripts/build_filing_nlp_notebooks.py` に以下を書く:

```python
"""notebook/FILING_NLP/*.ipynb を nbformat で生成するスクリプト.

実行方法::

    uv run python scripts/build_filing_nlp_notebooks.py

各 notebook のセル定義はこのファイル内で管理する。
セル内容を変更したい場合はここを編集して再実行すること。
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

OUT_DIR = Path(__file__).resolve().parent.parent / "notebook" / "FILING_NLP"


def _md(src: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(src)


def _code(src: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(src)


def _save(nb: nbf.NotebookNode, name: str) -> None:
    path = OUT_DIR / name
    nbf.write(nb, path)
    print(f"wrote: {path}")


# ---------------------------------------------------------------------------
# 01_fetch_and_chunk.ipynb
# ---------------------------------------------------------------------------


def build_01_fetch_and_chunk() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    }
    nb.cells = [
        _md(
            "# 01 Fetch & Chunk\n\n"
            "AAPL/MSFT/GOOGL の 10-K × 5年 + 10-Q × 15四半期 = 60 件を取得し、\n"
            "Item 1A (Risk Factors) と Item 7/Item 2 (MD&A) を抽出、\n"
            "FinBERT トークナイザで 510 トークンチャンクに分割する。"
        ),
        _code(
            "# Cell 1: imports + setup (必ず最初に _helpers を import)\n"
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path.cwd()))\n"
            "import _helpers\n"
            "_ = _helpers.setup_edgar()\n"
            "device = _helpers.get_device()\n"
            "print('device:', device)\n"
            "print('DATA_DIR:', _helpers.DATA_DIR)\n"
        ),
        _code(
            "# Cell 2: 10-K を 3 銘柄 × 5 年取得\n"
            "from edgar.batch import BatchFetcher\n"
            "from edgar.types import FilingType\n"
            "\n"
            "TICKERS = ['AAPL', 'MSFT', 'GOOGL']\n"
            "fetcher = BatchFetcher(max_workers=3)\n"
            "filings_10k = fetcher.fetch(\n"
            "    cik_or_tickers=TICKERS, form=FilingType.FORM_10K, limit=5,\n"
            ")\n"
            "for t, r in filings_10k.items():\n"
            "    print(t, len(r) if not isinstance(r, Exception) else f'ERR: {r}')\n"
        ),
        _code(
            "# Cell 3: 10-Q を 3 銘柄 × 15 四半期取得\n"
            "filings_10q = fetcher.fetch(\n"
            "    cik_or_tickers=TICKERS, form=FilingType.FORM_10Q, limit=15,\n"
            ")\n"
            "for t, r in filings_10q.items():\n"
            "    print(t, len(r) if not isinstance(r, Exception) else f'ERR: {r}')\n"
        ),
        _code(
            "# Cell 4: filings メタを 1 つの DataFrame に統合し filings.parquet 保存\n"
            "import pandas as pd\n"
            "\n"
            "all_filing_objs = []\n"
            "for d, label in [(filings_10k, '10-K'), (filings_10q, '10-Q')]:\n"
            "    for ticker, result in d.items():\n"
            "        if isinstance(result, Exception):\n"
            "            continue\n"
            "        for f in result:\n"
            "            all_filing_objs.append((ticker, label, f))\n"
            "\n"
            "df_filings = pd.DataFrame([\n"
            "    {\n"
            "        'filing_id': str(getattr(f, 'accession_no', '') or getattr(f, 'accession_number', '')),\n"
            "        'ticker': ticker,\n"
            "        'form': form,\n"
            "        'filing_date': pd.Timestamp(str(getattr(f, 'filing_date', ''))),\n"
            "        'accession_number': str(getattr(f, 'accession_no', '') or getattr(f, 'accession_number', '')),\n"
            "    }\n"
            "    for ticker, form, f in all_filing_objs\n"
            "])\n"
            "df_filings = df_filings.sort_values(['ticker', 'form', 'filing_date']).reset_index(drop=True)\n"
            "df_filings.to_parquet(_helpers.FILINGS_PARQUET)\n"
            "print('saved:', _helpers.FILINGS_PARQUET, 'rows:', len(df_filings))\n"
            "df_filings.head()\n"
        ),
        _code(
            "# Cell 5: 10-K のセクション抽出 (Item 1A, Item 7)\n"
            "from edgar.cache import CacheManager\n"
            "from edgar.extractors import SectionExtractor\n"
            "from edgar.types import SectionKey\n"
            "\n"
            "cache = CacheManager(cache_dir=_helpers.EDGAR_CACHE_DIR)\n"
            "extractor_10k = SectionExtractor(cache=cache)\n"
            "\n"
            "section_rows = []\n"
            "for ticker, form, f in all_filing_objs:\n"
            "    if form != '10-K':\n"
            "        continue\n"
            "    fid = str(getattr(f, 'accession_no', '') or getattr(f, 'accession_number', ''))\n"
            "    for key in [SectionKey.ITEM_1A.value, SectionKey.ITEM_7.value]:\n"
            "        text = extractor_10k.extract_section(f, key)\n"
            "        if text:\n"
            "            section_rows.append({\n"
            "                'filing_id': fid, 'section_key': key,\n"
            "                'text': text, 'char_count': len(text),\n"
            "            })\n"
            "        else:\n"
            "            print(f'10-K miss: {ticker} {fid} {key}')\n"
            "print('10-K sections extracted:', len(section_rows))\n"
        ),
        _code(
            "# Cell 6: 10-Q のセクション抽出 (custom_patterns で Item 2 / Item 1A)\n"
            "extractor_10q = SectionExtractor(\n"
            "    cache=cache,\n"
            "    custom_patterns=_helpers.SECTION_PATTERNS_10Q,\n"
            ")\n"
            "for ticker, form, f in all_filing_objs:\n"
            "    if form != '10-Q':\n"
            "        continue\n"
            "    fid = str(getattr(f, 'accession_no', '') or getattr(f, 'accession_number', ''))\n"
            "    for key in ['item_7', 'item_1a']:\n"
            "        text = extractor_10q.extract_section(f, key)\n"
            "        if text:\n"
            "            section_rows.append({\n"
            "                'filing_id': fid, 'section_key': key,\n"
            "                'text': text, 'char_count': len(text),\n"
            "            })\n"
            "        else:\n"
            "            print(f'10-Q miss: {ticker} {fid} {key}')\n"
            "print('total sections:', len(section_rows))\n"
        ),
        _code(
            "# Cell 7: sections.parquet 保存\n"
            "df_sections = pd.DataFrame(section_rows)\n"
            "df_sections.to_parquet(_helpers.SECTIONS_PARQUET)\n"
            "print('saved:', _helpers.SECTIONS_PARQUET, 'rows:', len(df_sections))\n"
            "df_sections.groupby(['section_key']).size()\n"
        ),
        _code(
            "# Cell 8: FinBERT トークナイザでチャンク化\n"
            "from tqdm.auto import tqdm\n"
            "tokenizer, _model = _helpers.load_finbert()\n"
            "del _model  # チャンク化はトークナイザのみ必要\n"
            "\n"
            "chunk_rows = []\n"
            "for row in tqdm(df_sections.to_dict('records'), desc='chunking'):\n"
            "    chunks = _helpers.chunk_text(row['text'], tokenizer)\n"
            "    for i, c in enumerate(chunks):\n"
            "        chunk_rows.append({\n"
            "            'filing_id': row['filing_id'],\n"
            "            'section_key': row['section_key'],\n"
            "            'chunk_idx': i,\n"
            "            'text': c,\n"
            "            'token_count': len(tokenizer.encode(c, add_special_tokens=False)),\n"
            "        })\n"
            "print('total chunks:', len(chunk_rows))\n"
        ),
        _code(
            "# Cell 9: chunks.parquet 保存 + ticker/form 結合\n"
            "df_chunks = pd.DataFrame(chunk_rows).merge(\n"
            "    df_filings[['filing_id', 'ticker', 'form', 'filing_date']],\n"
            "    on='filing_id', how='left',\n"
            ")\n"
            "df_chunks.to_parquet(_helpers.CHUNKS_PARQUET)\n"
            "print('saved:', _helpers.CHUNKS_PARQUET, 'rows:', len(df_chunks))\n"
            "df_chunks.groupby(['ticker', 'form', 'section_key']).size()\n"
        ),
    ]
    return nb


if __name__ == "__main__":
    _save(build_01_fetch_and_chunk(), "01_fetch_and_chunk.ipynb")
    print("01 done. 02 / 03 は後続タスクで追加。")
```

- [ ] **Step 2: スクリプトを実行して 01 ノートブックを生成**

Run: `cd /Users/yukihata/Desktop/quants && uv run python scripts/build_filing_nlp_notebooks.py`
Expected:
```
wrote: .../notebook/FILING_NLP/01_fetch_and_chunk.ipynb
01 done. 02 / 03 は後続タスクで追加。
```

- [ ] **Step 3: 生成された .ipynb の構造を確認**

Run:
```bash
uv run python -c "
import nbformat
nb = nbformat.read('notebook/FILING_NLP/01_fetch_and_chunk.ipynb', as_version=4)
print('cells:', len(nb.cells))
for i, c in enumerate(nb.cells):
    head = c.source.splitlines()[0] if c.source else ''
    print(f'  [{i}] {c.cell_type}: {head[:60]}')
"
```
Expected: 10 セル前後（Markdown 1 + Code 9）、各 Code セルの先頭コメントが想定通り。

- [ ] **Step 4: コミット**

```bash
git add scripts/build_filing_nlp_notebooks.py notebook/FILING_NLP/01_fetch_and_chunk.ipynb
git commit -m "$(cat <<'EOF'
feat(filing_nlp): notebook ビルダースクリプト + 01_fetch_and_chunk.ipynb

scripts/build_filing_nlp_notebooks.py で nbformat 経由 .ipynb 生成。
notebook を直接編集する代わりにスクリプト編集 → 再実行で再現性確保。

01_fetch_and_chunk.ipynb:
- 3 銘柄 × (10-K 5年 + 10-Q 15Q) = 60 件を BatchFetcher で取得
- SectionExtractor で Item 1A / Item 7 を抽出 (10-Q は custom_patterns)
- FinBERT トークナイザで 510 トークンチャンクに分割
- filings/sections/chunks の 3 Parquet を data/ に保存

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: 01_fetch_and_chunk.ipynb を実行して動作確認

⚠️ **このタスクで初回 SEC EDGAR から 60 ファイリングを取得します。レート制限 10req/sec の制約で数分かかります。**

- [ ] **Step 1: Jupyter で notebook を開いて Run All（もしくは nbconvert --execute で実行）**

GUI で実行する場合:
```bash
cd /Users/yukihata/Desktop/quants
uv run jupyter notebook notebook/FILING_NLP/01_fetch_and_chunk.ipynb
```

CLI でヘッドレス実行する場合（推奨。ログだけ残せば足りる）:
```bash
cd /Users/yukihata/Desktop/quants
uv run jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.timeout=1800 \
    --inplace notebook/FILING_NLP/01_fetch_and_chunk.ipynb
```
Expected:
- セル 2/3 で `AAPL 5 / MSFT 5 / GOOGL 5` (10-K) と `AAPL 15 / MSFT 15 / GOOGL 15` (10-Q) 程度の出力
- セル 5/6 で `10-K miss` / `10-Q miss` 行があれば数を記録（10-Q は構造差で取りこぼし可能性あり、許容）
- セル 9 で `df_chunks.groupby(['ticker','form','section_key']).size()` の出力に 12 グループ（3 銘柄 × 2 form × 2 section）全部現れる

- [ ] **Step 2: 出力 Parquet が生成されたか確認**

Run:
```bash
ls -la /Users/yukihata/Desktop/quants/notebook/FILING_NLP/data/*.parquet
```
Expected: `filings.parquet`, `sections.parquet`, `chunks.parquet` の 3 ファイルが存在。

- [ ] **Step 3: 各 Parquet の行数と最低限の中身を検証**

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "
import pandas as pd
import sys; sys.path.insert(0, 'notebook/FILING_NLP')
import _helpers
for name, path in [('filings', _helpers.FILINGS_PARQUET), ('sections', _helpers.SECTIONS_PARQUET), ('chunks', _helpers.CHUNKS_PARQUET)]:
    df = pd.read_parquet(path)
    print(f'{name}: rows={len(df)} cols={list(df.columns)}')
print()
df_chunks = pd.read_parquet(_helpers.CHUNKS_PARQUET)
print('chunks per (ticker, form, section):')
print(df_chunks.groupby(['ticker','form','section_key']).size())
"
```
Expected:
- `filings: rows=60`（多少前後あり）
- `sections: rows≥80`（60 × 2 = 120 が上限、10-Q 抽出失敗で減る可能性あり）
- `chunks: rows≥数百`（テキスト長による）

- [ ] **Step 4: data/ がコミット対象外であることを確認**

Run: `cd /Users/yukihata/Desktop/quants && git status notebook/FILING_NLP/data/`
Expected: 何も表示されない（.gitignore でブロックされている）。

- [ ] **Step 5: ノートブック自体の更新分があればコミット**

`jupyter nbconvert --execute --inplace` 実行で .ipynb の outputs が埋まる。これはコミットしてもしなくても良いが、execution 結果を残す方針で:

```bash
cd /Users/yukihata/Desktop/quants
git add notebook/FILING_NLP/01_fetch_and_chunk.ipynb
git diff --cached --stat | head -5
git commit -m "$(cat <<'EOF'
chore(filing_nlp): 01_fetch_and_chunk.ipynb の実行結果を記録

3 銘柄 × (10-K + 10-Q) = 60 ファイリングの取得・セクション抽出・
チャンク化を実行し、outputs を含めて記録。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

実行結果から取りこぼし件数が多い (例: 10-Q セクション抽出ミス >50%) 場合は SECTION_PATTERNS_10Q の見直しが必要。issue として `docs/superpowers/notes/` 等に記録し、後続タスクで対応する。

---

## Task 8: scripts に 02_finbert_sentiment.ipynb 定義を追加して生成 → 実行

**Files:**
- Modify: `scripts/build_filing_nlp_notebooks.py`
- Create: `notebook/FILING_NLP/02_finbert_sentiment.ipynb`

- [ ] **Step 1: build_02_finbert_sentiment 関数を scripts に追加**

`scripts/build_filing_nlp_notebooks.py` の `build_01_fetch_and_chunk` 関数の後、`if __name__ == "__main__":` ブロックの前に以下を追加:

```python
# ---------------------------------------------------------------------------
# 02_finbert_sentiment.ipynb
# ---------------------------------------------------------------------------


def build_02_finbert_sentiment() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    }
    nb.cells = [
        _md(
            "# 02 FinBERT Sentiment\n\n"
            "`chunks.parquet` を読み込み、FinBERT (yiyanghkust/finbert-tone) で\n"
            "各チャンクの positive / negative / neutral 確率を推論する。\n"
            "filing × section 単位で集約して可視化。"
        ),
        _code(
            "# Cell 1: imports + FinBERT ロード\n"
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path.cwd()))\n"
            "import _helpers\n"
            "import torch\n"
            "import pandas as pd\n"
            "from tqdm.auto import tqdm\n"
            "\n"
            "device = _helpers.get_device()\n"
            "tokenizer, model = _helpers.load_finbert(device)\n"
            "print('device:', device, 'labels:', model.config.id2label)\n"
        ),
        _code(
            "# Cell 2: chunks 読み込み\n"
            "df_chunks = pd.read_parquet(_helpers.CHUNKS_PARQUET)\n"
            "print('chunks:', len(df_chunks))\n"
            "df_chunks.head(3)\n"
        ),
        _code(
            "# Cell 3: バッチ推論 (pos/neg/neu)\n"
            "BATCH_SIZE = 32\n"
            "id2label = model.config.id2label\n"
            "label_names = [id2label[i] for i in range(len(id2label))]\n"
            "\n"
            "all_probs = []\n"
            "texts = df_chunks['text'].tolist()\n"
            "for start in tqdm(range(0, len(texts), BATCH_SIZE), desc='finbert'):\n"
            "    batch = texts[start:start+BATCH_SIZE]\n"
            "    enc = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors='pt').to(device)\n"
            "    with torch.no_grad():\n"
            "        out = model(**enc)\n"
            "    probs = out.logits.softmax(dim=-1).cpu().numpy()\n"
            "    all_probs.extend(probs.tolist())\n"
            "print('done. samples:', len(all_probs))\n"
        ),
        _code(
            "# Cell 4: sentiments.parquet 保存\n"
            "import numpy as np\n"
            "probs_arr = np.array(all_probs)\n"
            "label_to_col = {n.lower(): n.lower()[:3] for n in label_names}  # Positive->pos など\n"
            "# 列名を明示的に pos/neg/neu に統一\n"
            "name2idx = {n.lower(): i for i, n in enumerate(label_names)}\n"
            "df_sent = df_chunks[['filing_id','ticker','form','section_key','chunk_idx','filing_date']].copy()\n"
            "df_sent['pos'] = probs_arr[:, name2idx['positive']]\n"
            "df_sent['neg'] = probs_arr[:, name2idx['negative']]\n"
            "df_sent['neu'] = probs_arr[:, name2idx['neutral']]\n"
            "df_sent['label'] = [label_names[i] for i in probs_arr.argmax(axis=1)]\n"
            "df_sent.to_parquet(_helpers.SENTIMENTS_PARQUET)\n"
            "print('saved:', _helpers.SENTIMENTS_PARQUET, 'rows:', len(df_sent))\n"
            "df_sent.head()\n"
        ),
        _code(
            "# Cell 5: filing × section 単位で平均センチメント集約\n"
            "agg = df_sent.groupby(['ticker','form','section_key','filing_id','filing_date'])[['pos','neg','neu']].mean().reset_index()\n"
            "agg = agg.sort_values(['ticker','section_key','filing_date'])\n"
            "agg.head(10)\n"
        ),
        _code(
            "# Cell 6: AAPL の Risk Factors (Item 1A) の neg スコア推移\n"
            "import plotly.express as px\n"
            "aapl_risk = agg[(agg['ticker']=='AAPL') & (agg['section_key']=='item_1a')].copy()\n"
            "fig = px.line(\n"
            "    aapl_risk, x='filing_date', y='neg', color='form', markers=True,\n"
            "    title='AAPL Risk Factors (Item 1A) - FinBERT negative score over time',\n"
            ")\n"
            "fig.show()\n"
        ),
        _code(
            "# Cell 7: 3 銘柄 × MD&A センチメント比較 (pos - neg)\n"
            "mda = agg[agg['section_key']=='item_7'].copy()\n"
            "mda['net_sentiment'] = mda['pos'] - mda['neg']\n"
            "fig = px.line(\n"
            "    mda, x='filing_date', y='net_sentiment', color='ticker', markers=True, line_dash='form',\n"
            "    title='MD&A net sentiment (pos - neg) by ticker/form',\n"
            ")\n"
            "fig.show()\n"
        ),
    ]
    return nb
```

- [ ] **Step 2: __main__ ブロックの末尾に 02 の save 呼び出しを追加**

`if __name__ == "__main__":` ブロックを以下に置き換える:

```python
if __name__ == "__main__":
    _save(build_01_fetch_and_chunk(), "01_fetch_and_chunk.ipynb")
    _save(build_02_finbert_sentiment(), "02_finbert_sentiment.ipynb")
    print("01, 02 done. 03 は後続タスクで追加。")
```

- [ ] **Step 3: スクリプトを実行して 02 ノートブックを生成**

Run: `cd /Users/yukihata/Desktop/quants && uv run python scripts/build_filing_nlp_notebooks.py`
Expected: `wrote: .../02_finbert_sentiment.ipynb` の出力。

- [ ] **Step 4: 02 ノートブックを実行**

Run:
```bash
cd /Users/yukihata/Desktop/quants
uv run jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.timeout=1800 \
    --inplace notebook/FILING_NLP/02_finbert_sentiment.ipynb
```
Expected:
- セル 1 で `device: mps` 表示
- セル 3 で tqdm progress bar が進行（数分）
- セル 4 で `saved: .../sentiments.parquet` と件数表示
- セル 6/7 で plotly 図が埋め込まれる

- [ ] **Step 5: sentiments.parquet を検証 (pos+neg+neu ≈ 1.0)**

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "
import pandas as pd, sys
sys.path.insert(0, 'notebook/FILING_NLP')
import _helpers
df = pd.read_parquet(_helpers.SENTIMENTS_PARQUET)
sums = (df['pos'] + df['neg'] + df['neu'])
print('rows:', len(df))
print('sum stats:', sums.describe().to_string())
print('label dist:')
print(df['label'].value_counts())
"
```
Expected:
- `min`, `max` ともに 1.0 近傍 (±1e-3)
- ラベル分布は Neutral 多めだが Positive/Negative も出ている

- [ ] **Step 6: コミット**

```bash
cd /Users/yukihata/Desktop/quants
git add scripts/build_filing_nlp_notebooks.py notebook/FILING_NLP/02_finbert_sentiment.ipynb
git commit -m "$(cat <<'EOF'
feat(filing_nlp): 02_finbert_sentiment.ipynb で FinBERT 推論を追加

chunks.parquet 全件を batch_size=32 で FinBERT 推論し、
pos/neg/neu 確率と argmax ラベルを sentiments.parquet に保存。
AAPL Risk Factors の neg スコア推移と MD&A net sentiment 比較を
plotly で可視化。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: scripts に 03_embedding_analysis.ipynb 定義を追加して生成 → 実行

**Files:**
- Modify: `scripts/build_filing_nlp_notebooks.py`
- Create: `notebook/FILING_NLP/03_embedding_analysis.ipynb`

- [ ] **Step 1: build_03_embedding_analysis 関数を scripts に追加**

`scripts/build_filing_nlp_notebooks.py` の `build_02_finbert_sentiment` 関数の後、`if __name__ == "__main__":` ブロックの前に以下を追加:

```python
# ---------------------------------------------------------------------------
# 03_embedding_analysis.ipynb
# ---------------------------------------------------------------------------


def build_03_embedding_analysis() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    }
    nb.cells = [
        _md(
            "# 03 Embedding Analysis\n\n"
            "`chunks.parquet` を BAAI/bge-large-en-v1.5 で 1024 次元 embedding 化し、\n"
            "1) 同一銘柄・同一セクションの年次変化検知\n"
            "2) UMAP による 2D 投影クラスタリング\n"
            "3) 銘柄間類似度比較\n"
            "を行う。"
        ),
        _code(
            "# Cell 1: imports + embedder ロード\n"
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path.cwd()))\n"
            "import _helpers\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "from tqdm.auto import tqdm\n"
            "\n"
            "device = _helpers.get_device()\n"
            "model = _helpers.load_embedder(device)\n"
            "print('device:', device, 'dim:', model.get_sentence_embedding_dimension())\n"
        ),
        _code(
            "# Cell 2: chunks 読み込み\n"
            "df_chunks = pd.read_parquet(_helpers.CHUNKS_PARQUET)\n"
            "print('chunks:', len(df_chunks))\n"
        ),
        _code(
            "# Cell 3: バッチ encode (normalize_embeddings=True で cos sim = dot product)\n"
            "vectors = model.encode(\n"
            "    df_chunks['text'].tolist(),\n"
            "    batch_size=16, show_progress_bar=True,\n"
            "    normalize_embeddings=True,\n"
            ")\n"
            "print('vectors shape:', vectors.shape)\n"
        ),
        _code(
            "# Cell 4: embeddings.parquet 保存 (vector 列は list[float])\n"
            "df_emb = df_chunks[['filing_id','ticker','form','section_key','chunk_idx','filing_date']].copy()\n"
            "df_emb['vector'] = list(vectors)\n"
            "df_emb.to_parquet(_helpers.EMBEDDINGS_PARQUET)\n"
            "print('saved:', _helpers.EMBEDDINGS_PARQUET, 'rows:', len(df_emb))\n"
        ),
        _code(
            "# Cell 5: filing × section 単位で平均プーリング → コサイン類似度 (前期比)\n"
            "def _avg_pool(group):\n"
            "    return np.mean(np.vstack(group['vector'].values), axis=0)\n"
            "\n"
            "pooled = (\n"
            "    df_emb.groupby(['ticker','form','section_key','filing_id','filing_date'])\n"
            "    .apply(lambda g: pd.Series({'mean_vec': _avg_pool(g)}))\n"
            "    .reset_index()\n"
            ")\n"
            "pooled = pooled.sort_values(['ticker','form','section_key','filing_date']).reset_index(drop=True)\n"
            "\n"
            "rows = []\n"
            "for (ticker, form, section), g in pooled.groupby(['ticker','form','section_key']):\n"
            "    g = g.sort_values('filing_date').reset_index(drop=True)\n"
            "    for i in range(1, len(g)):\n"
            "        v_prev = g.loc[i-1, 'mean_vec']\n"
            "        v_now = g.loc[i, 'mean_vec']\n"
            "        cos = float(np.dot(v_prev, v_now) / (np.linalg.norm(v_prev)*np.linalg.norm(v_now)))\n"
            "        rows.append({\n"
            "            'ticker': ticker, 'form': form, 'section_key': section,\n"
            "            'filing_date': g.loc[i, 'filing_date'],\n"
            "            'cos_sim_prev': cos,\n"
            "            'diff_score': 1.0 - cos,\n"
            "        })\n"
            "df_change = pd.DataFrame(rows)\n"
            "df_change.head()\n"
        ),
        _code(
            "# Cell 6: 変化検知の可視化 (Item 1A の前期比 diff 推移)\n"
            "import plotly.express as px\n"
            "risk_diff = df_change[df_change['section_key']=='item_1a']\n"
            "fig = px.line(\n"
            "    risk_diff, x='filing_date', y='diff_score', color='ticker', markers=True, line_dash='form',\n"
            "    title='Risk Factors (Item 1A) - cosine distance to previous filing',\n"
            ")\n"
            "fig.show()\n"
        ),
        _code(
            "# Cell 7: UMAP 2D 投影 (ticker で色分け)\n"
            "import umap\n"
            "X = np.vstack(pooled['mean_vec'].values)\n"
            "reducer = umap.UMAP(n_components=2, metric='cosine', random_state=42)\n"
            "X2 = reducer.fit_transform(X)\n"
            "pooled_plot = pooled.copy()\n"
            "pooled_plot['x'] = X2[:,0]\n"
            "pooled_plot['y'] = X2[:,1]\n"
            "fig = px.scatter(\n"
            "    pooled_plot, x='x', y='y', color='ticker', symbol='section_key',\n"
            "    hover_data=['form','filing_date'],\n"
            "    title='UMAP projection of filing×section embeddings',\n"
            ")\n"
            "fig.show()\n"
        ),
        _code(
            "# Cell 8: 類似銘柄 - AAPL 最新 10-K Item 1A vs MSFT/GOOGL 最新 Item 1A\n"
            "latest_risk = (\n"
            "    pooled[(pooled['form']=='10-K') & (pooled['section_key']=='item_1a')]\n"
            "    .sort_values('filing_date').groupby('ticker').tail(1).reset_index(drop=True)\n"
            ")\n"
            "vecs = {row['ticker']: row['mean_vec'] for _, row in latest_risk.iterrows()}\n"
            "import itertools\n"
            "sim_rows = []\n"
            "for a, b in itertools.combinations(vecs.keys(), 2):\n"
            "    cos = float(np.dot(vecs[a], vecs[b]) / (np.linalg.norm(vecs[a])*np.linalg.norm(vecs[b])))\n"
            "    sim_rows.append({'a': a, 'b': b, 'cosine': cos})\n"
            "pd.DataFrame(sim_rows).sort_values('cosine', ascending=False)\n"
        ),
    ]
    return nb
```

- [ ] **Step 2: __main__ ブロックを更新して 03 も生成**

`if __name__ == "__main__":` ブロックを以下に置き換える:

```python
if __name__ == "__main__":
    _save(build_01_fetch_and_chunk(), "01_fetch_and_chunk.ipynb")
    _save(build_02_finbert_sentiment(), "02_finbert_sentiment.ipynb")
    _save(build_03_embedding_analysis(), "03_embedding_analysis.ipynb")
    print("01, 02, 03 done.")
```

- [ ] **Step 3: スクリプトを実行して 03 ノートブックを生成**

Run: `cd /Users/yukihata/Desktop/quants && uv run python scripts/build_filing_nlp_notebooks.py`
Expected: `wrote: .../03_embedding_analysis.ipynb`

- [ ] **Step 4: 03 ノートブックを実行**

Run:
```bash
cd /Users/yukihata/Desktop/quants
uv run jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.timeout=1800 \
    --inplace notebook/FILING_NLP/03_embedding_analysis.ipynb
```
Expected:
- セル 1 で `dim: 1024` 表示
- セル 3 で encode の progress bar が進行（5〜10分）
- セル 4 で `embeddings.parquet` 保存
- セル 6, 7 で plotly 図が埋め込まれる
- セル 8 で AAPL/MSFT/GOOGL の最新 Item 1A 類似度テーブルが表示

- [ ] **Step 5: embeddings.parquet を検証 (次元 1024 + 正規化)**

Run:
```bash
cd /Users/yukihata/Desktop/quants && uv run python -c "
import pandas as pd, numpy as np, sys
sys.path.insert(0, 'notebook/FILING_NLP')
import _helpers
df = pd.read_parquet(_helpers.EMBEDDINGS_PARQUET)
v = np.vstack(df['vector'].values)
print('rows:', len(df), 'shape:', v.shape)
norms = np.linalg.norm(v, axis=1)
print('norms min/mean/max:', float(norms.min()), float(norms.mean()), float(norms.max()))
"
```
Expected:
- `shape: (N, 1024)`
- `norms` がすべて 1.0 近傍 (±1e-4)

- [ ] **Step 6: 成功判定の最終確認**

Spec の成功判定 3 項目をチェックリストとして検証:

1. `01_fetch_and_chunk.ipynb` → chunks.parquet が生成され、12 グループ (3 ticker × 2 form × 2 section) 全部に行がある → Task 7 Step 3 で確認済み
2. `02_finbert_sentiment.ipynb` → sentiments.parquet の各行で pos+neg+neu ≈ 1.0 → Task 8 Step 5 で確認済み
3. `03_embedding_analysis.ipynb` → UMAP 散布図が表示され、AAPL/MSFT/GOOGL の分離具合を目視判断可能 → セル 7 の plotly 図で確認

- [ ] **Step 7: コミット**

```bash
cd /Users/yukihata/Desktop/quants
git add scripts/build_filing_nlp_notebooks.py notebook/FILING_NLP/03_embedding_analysis.ipynb
git commit -m "$(cat <<'EOF'
feat(filing_nlp): 03_embedding_analysis.ipynb で bge embedding 分析を追加

chunks.parquet を BAAI/bge-large-en-v1.5 で 1024 次元正規化 embedding 化し、
embeddings.parquet に保存。3 つの分析:
- 変化検知: filing × section 平均プーリング後、前期比コサイン距離を計算
- クラスタリング: UMAP 2D 投影で ticker × section の分布を可視化
- 類似銘柄: AAPL/MSFT/GOOGL の最新 10-K Item 1A 間の類似度テーブル

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## 完了基準

- [ ] 全 9 タスクが完了し、各タスクの最終 commit が main にマージされている（直接 main にコミット運用）
- [ ] `notebook/FILING_NLP/` 配下に `_helpers.py` + 3 .ipynb が存在
- [ ] `notebook/FILING_NLP/data/` 配下に 5 Parquet ファイル + HF キャッシュが存在（gitignore 対象）
- [ ] Spec の成功判定 3 項目（Task 9 Step 6）が全てパス

## 後続検討事項（このプランの範囲外）

- 10-Q セクション抽出の取りこぼし率が高い場合の `SECTION_PATTERNS_10Q` 改善
- chunk_text の文境界分割（現状は単純トークン分割のため、文の途中で切れる）
- パイプライン化（src/ パッケージ化、CI 統合）
- 大規模ユニバース（S&P500 等）への拡張時のストレージ・キャッシュ戦略
