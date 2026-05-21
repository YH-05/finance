# 10-K/10-Q × FinBERT × Embedding クオンツ分析実験 設計仕様書

**作成日**: 2026-05-21
**スコープ**: notebook 上での実験的分析（パイプライン化はしない）
**実装フォルダ**: `notebook/FILING_NLP/`

---

## 1. ゴールとスコープ

### ゴール

AAPL / MSFT / GOOGL の **10-K × 5年（15件）+ 10-Q × 15四半期（45件）= 計60件** のファイリングを対象に、notebook 上で次の3点を実験する。

1. **技術検証**: edgar からのテキスト取得 → チャンク化 → FinBERT 推論 → embedding 計算が一連で回ること
2. **テキスト変化検知**: 同一銘柄の前年同期 vs 今期で Risk Factors (Item 1A) / MD&A (Item 7) の embedding コサイン類似度を計算し、「内容が大きく変わった四半期」を可視化
3. **クラスタリング・類似銘柄**: 3銘柄 × 5年の embedding を 2D 投影（UMAP / PCA）して、銘柄ごとの軌跡が分離するか確認

### スコープ外（YAGNI）

- **新規 src/ パッケージは作らない**。`src/embedding` への組み込みもしない（現状 News 専用で密結合のため、改修コストが目的に見合わない）
- **パイプライン化しない**。CLI / make ターゲット / GitHub Project への登録は今回スコープ外
- **DB スキーマを作らない**。中間データは notebook フォルダ配下の Parquet で完結
- **テストを書かない**（実験フェーズ）

### 成果物

- `notebook/FILING_NLP/` 配下に `.ipynb` × 3個 + 共通 helper `.py` × 1個
- `notebook/FILING_NLP/data/` 配下に HF モデルキャッシュ、edgar キャッシュ、中間 Parquet 5ファイル

---

## 2. アーキテクチャとデータフロー

### レイヤー構造

```
┌─────────────────────────────────────────────────────────┐
│ notebook/FILING_NLP/                                    │
│   01_fetch_and_chunk.ipynb     ← 取得 + チャンク化      │
│   02_finbert_sentiment.ipynb   ← FinBERT 推論           │
│   03_embedding_analysis.ipynb  ← 埋め込み + 分析        │
│   _helpers.py                  ← 共通の薄いユーティリティ │
└─────────────────────────────────────────────────────────┘
                         │
                         │ uses (薄いラッパー)
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 既存 src/edgar/  ← そのまま利用                          │
│   EdgarFetcher / BatchFetcher                           │
│   SectionExtractor (10-K = デフォルト, 10-Q = custom_patterns) │
│   CacheManager (SQLite, テキスト)                       │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ notebook/FILING_NLP/data/                               │
│   hf_cache/             ← HF_HOME (~1.7GB)              │
│   edgar_cache/          ← edgar.CacheManager の SQLite  │
│   filings.parquet       : 取得ファイリング一覧           │
│   sections.parquet      : セクション分割テキスト         │
│   chunks.parquet        : FinBERT/embedding 用チャンク   │
│   sentiments.parquet    : FinBERT 推論結果              │
│   embeddings.parquet    : 埋め込みベクトル              │
└─────────────────────────────────────────────────────────┘
```

### データフロー

```
[1] BatchFetcher.fetch(["AAPL","MSFT","GOOGL"], FORM_10K, limit=5)
                       BatchFetcher.fetch(...,    FORM_10Q, limit=15)
       │
       ▼  60 件の Filing オブジェクト
[2] SectionExtractor.extract_section(filing, "item_1a" / "item_7")
       (10-Q は新規 SECTION_PATTERNS_10Q で part_1_item_2 など)
       │
       ▼  sections.parquet
       │   columns: filing_id, ticker, form, filing_date, fiscal_period,
       │            section_key, text, char_count
       │
       ▼  _helpers.chunk_text(text, tokenizer, max_tokens=510, stride=128)
[3] chunks.parquet
       columns: filing_id, ticker, form, section_key, chunk_idx, text, token_count
       │
       ├──────────────────────────────────────────┐
       ▼                                          ▼
[4a] FinBERT (yiyanghkust/finbert-tone)     [4b] sentence-transformers
       推論 → {positive, negative, neutral}        (BAAI/bge-large-en-v1.5)
       sentiments.parquet                          → embeddings.parquet
       columns: filing_id, chunk_idx,              columns: filing_id, chunk_idx,
                pos, neg, neu, label                        vector(list[float]×1024)
       │                                          │
       └──────────────────────────────────────────┘
                        │
                        ▼
       notebook 上で集約・可視化（pandas / plotly / umap-learn）
```

### キー設計判断

| 判断 | 理由 |
|------|------|
| 中間データは **Parquet 5ファイル** に分離 | notebookセル間で `pd.read_parquet` で部分ロードでき、巨大ベクトル列を毎回読まずに済む |
| ChromaDB は使わない | 60ファイリング × 数十チャンク = 数千ベクトル規模。Parquet + numpy で十分。`src/embedding` 流用も検討したが、News 用 ID/メタ構造が固定で割に合わない |
| FinBERT は `yiyanghkust/finbert-tone` を採用 | 金融テキスト特化、トーン3クラス（pos/neg/neu） |
| Embedding は `BAAI/bge-large-en-v1.5` を採用 | MTEB 上位・1024次元・金融ドメインでの利用例も多い。FinBERT トークナイザと別物なので注意 |
| チャンク化は **510トークン・stride 128** | FinBERT は 512 上限（CLS/SEP 込み）、embedding 側も同じチャンクを使うことで分析比較を簡単にする |

---

## 3. 依存追加と環境準備

### `pyproject.toml` への依存追加

`dependencies` (main) に直接追加する（optional ではない）。

```toml
# 既存 dependencies の末尾に追加
"torch>=2.3.0,<3.0.0",
"transformers>=4.40.0,<5.0.0",
"sentence-transformers>=3.0.0",
"umap-learn>=0.5.5",
```

`uv sync` で導入完了。

| パッケージ | 用途 | 初回 DL |
|-----------|------|---------|
| `torch` | FinBERT/sentence-transformers のバックエンド | ~200MB |
| `transformers` | FinBERT 推論 (`AutoModelForSequenceClassification`) | 数MB |
| `sentence-transformers` | bge embedding 用ラッパー | 数MB |
| `umap-learn` | クラスタリング可視化 | 数MB |

### Apple Silicon MPS 前提

`_helpers.py` で `device = torch.device("mps")` を固定。MPS で問題発生時のみ `PYTORCH_ENABLE_MPS_FALLBACK=1` を併用して CPU フォールバック。

### モデルキャッシュ配置

`HF_HOME` を `notebook/FILING_NLP/data/hf_cache` に向ける（プロジェクト内に配置）。

| モデル | サイズ |
|--------|--------|
| `yiyanghkust/finbert-tone` | ~440MB |
| `BAAI/bge-large-en-v1.5` | ~1.3GB |

合計 約 **1.7GB** の初回ダウンロード。

### SEC EDGAR identity

`.env` の `EDGAR_IDENTITY` を `_helpers.setup_edgar()` で読み込み、未設定なら `RuntimeError` で停止。

### ディレクトリ作成

```bash
mkdir -p notebook/FILING_NLP/data/hf_cache
mkdir -p notebook/FILING_NLP/data/edgar_cache
```

### `.gitignore` 追記

```
notebook/FILING_NLP/data/
```

---

## 4. notebook 別の責務と中身

各 notebook は **「中間ファイルを書き出す」「次の notebook がそれを読む」** という直列パイプライン。途中から再開できるよう各セル単位で Parquet 保存。

### `_helpers.py`

| 関数 / 定数 | 目的 |
|------|------|
| `setup_hf_cache()` | `HF_HOME` を `notebook/FILING_NLP/data/hf_cache` に設定（モジュール import 時に自動実行） |
| `setup_edgar()` | `.env` から `EDGAR_IDENTITY` 読み込み・SEC EDGAR identity 登録 |
| `get_device()` | `torch.device("mps")` を返す |
| `SECTION_PATTERNS_10Q` | `dict[str, re.Pattern]`。10-Q の Part I Item 2 (MD&A) / Part II Item 1A (Risk Factors) パターン定義 |
| `chunk_text(text, tokenizer, max_tokens=510, stride=128)` | トークナイザベースのスライディングウィンドウチャンク化 |
| `load_finbert(device)` | `yiyanghkust/finbert-tone` のモデル+トークナイザ取得 |
| `load_embedder(device)` | `SentenceTransformer("BAAI/bge-large-en-v1.5", device=...)` 取得 |
| `DATA_DIR` / `HF_CACHE_DIR` / `EDGAR_CACHE_DIR` | パス定数 |

**重要**: `setup_hf_cache()` はモジュールトップで実行し、`from _helpers import ...` を notebook 1セル目に固定。これにより transformers/sentence-transformers import 前に `HF_HOME` が確定する。

### `01_fetch_and_chunk.ipynb`

**入力**: なし（外部 SEC EDGAR）
**出力**: `filings.parquet`, `sections.parquet`, `chunks.parquet`

| セル | 内容 |
|------|------|
| 1 | imports + `setup_edgar()` + `device = get_device()` |
| 2 | `BatchFetcher.fetch(["AAPL","MSFT","GOOGL"], FORM_10K, limit=5)` → 15件 |
| 3 | `BatchFetcher.fetch(["AAPL","MSFT","GOOGL"], FORM_10Q, limit=15)` → 45件 |
| 4 | 取得結果を flatten → `filings.parquet` に保存（filing_id, ticker, form, filing_date, accession_number） |
| 5 | `SectionExtractor(cache=CacheManager(...))` で 10-K の Item 1A / Item 7 を抽出 |
| 6 | `SectionExtractor(custom_patterns=SECTION_PATTERNS_10Q, cache=...)` で 10-Q の同等セクションを抽出 |
| 7 | 全セクションテキストを `sections.parquet` に保存 |
| 8 | FinBERT トークナイザロード → 各セクションを `chunk_text()` でスライディング分割 |
| 9 | `chunks.parquet` 保存（filing_id, ticker, form, section_key, chunk_idx, text, token_count） |

**実行時間目安**: SEC EDGAR rate limit 10req/sec、初回 fetch で数分。2回目以降はキャッシュヒット。

### `02_finbert_sentiment.ipynb`

**入力**: `chunks.parquet`
**出力**: `sentiments.parquet`

| セル | 内容 |
|------|------|
| 1 | imports + `load_finbert(device)` |
| 2 | `pd.read_parquet("chunks.parquet")` |
| 3 | バッチ推論ループ（batch_size=32 程度、tqdm で進捗）→ pos / neg / neu 3クラス確率 |
| 4 | `sentiments.parquet` 保存（filing_id, chunk_idx, pos, neg, neu, label=argmax） |
| 5 | 集約: filing × section 単位で平均センチメント計算 |
| 6 | 可視化: AAPL の年次 Risk Factors の neg スコア推移（plotly line chart） |
| 7 | 可視化: 3銘柄の MD&A センチメント比較 |

**推論件数目安**: 60ファイリング × 2セクション × 平均10チャンク = ~1200推論 → MPS で数分。

### `03_embedding_analysis.ipynb`

**入力**: `chunks.parquet`
**出力**: `embeddings.parquet`

| セル | 内容 |
|------|------|
| 1 | imports + `load_embedder(device)` |
| 2 | `pd.read_parquet("chunks.parquet")` |
| 3 | `model.encode(texts, batch_size=16, show_progress_bar=True, normalize_embeddings=True)` |
| 4 | `embeddings.parquet` 保存（filing_id, chunk_idx, vector=list[float×1024]） |
| 5 | **変化検知**: filing × section 単位で chunk embedding を平均プーリング → 同一銘柄 × 同一セクションで filing_date 順にコサイン類似度の系列を計算 |
| 6 | 変化検知の可視化: AAPL の Risk Factors の前期比類似度の時系列（dip = 大きな変更） |
| 7 | **クラスタリング**: 全 filing × section の平均ベクトルを UMAP で 2D 投影、ticker で色分け |
| 8 | **類似銘柄**: AAPL の最新 10-K の Item 1A ベクトルに対して、MSFT/GOOGL の Item 1A との類似度をテーブル表示 |

**推論件数目安**: chunks 同数 (~1200) を embedding。bge-large は FinBERT より重いため MPS で 5〜10 分目安。

### 中間ファイルのスキーマ

```
filings.parquet
  filing_id (str, PK), ticker, form, filing_date, accession_number,
  fiscal_year, fiscal_period

sections.parquet
  filing_id (FK), section_key, text, char_count

chunks.parquet
  filing_id (FK), section_key, chunk_idx (int), text, token_count

sentiments.parquet
  filing_id (FK), section_key, chunk_idx, pos (float), neg (float), neu (float), label (str)

embeddings.parquet
  filing_id (FK), section_key, chunk_idx, vector (list[float], len=1024)
```

---

## 5. リスク・前提・初動

### リスクと対処

| リスク | 対処 |
|--------|------|
| **10-Q の Risk Factors / MD&A セクション抽出が安定しない**（10-K と異なり Part I/II 構造で Item 番号も意味が違う）| `_helpers.py` の `SECTION_PATTERNS_10Q` を AAPL の最新 10-Q で先に手動検証 → 抽出失敗 filing は notebook 上でログに残し、`sections.parquet` から欠落 |
| **MPS で transformers モデルが落ちる**（特定演算で `Placeholder` エラー等の既知問題）| `_helpers.get_device()` でフォールバック chain `mps → cpu` を実装。MPS が無効な場合は `PYTORCH_ENABLE_MPS_FALLBACK=1` 環境変数を併用 |
| **edgartools と src/edgar 名前衝突**（README 内 Notes に既出）| `_helpers.py` import 前に `src/edgar` が PYTHONPATH 解決されるよう notebook 冒頭で `sys.path` を確認 |
| **HF_HOME 切替の順序ミス**（transformers import 後に setenv しても効かない）| `_helpers.py` のモジュールトップで `setup_hf_cache()` を実行、`from _helpers import ...` を notebook 1セル目に固定 |
| **bge-large-en-v1.5 トークン上限とチャンク戦略のミスマッチ**（bge は 512 トークン上限、FinBERT と同じ）| 同じ tokenizer ベースで 510 トークンチャンクを採用するが、bge は内部で別 tokenizer を持つため厳密には差異あり → 初回 notebook で `model.tokenizer` のトークン数も確認しログ出力 |
| **初回 1.7GB DL の通信失敗** | HF はレジューム対応のため通常は再実行で完了。問題発生時のみログ提示 |
| **EDGAR_IDENTITY 未設定** | `_helpers.setup_edgar()` で未設定なら明示的に `RuntimeError` を出して止める |

### 前提（実装プラン側で確認が必要）

- `.env` に `EDGAR_IDENTITY="Name <email>"` が既にあるかどうか → 実装プラン側でまず `cat .env | grep EDGAR` を確認
- `data/cache/edgar/` に既存キャッシュがあるか → あれば 01 notebook の fetch 時間を短縮
- `pyproject.toml` の dependencies 末尾に追加するため、現状の末尾行を確認してから edit

### 実装フェーズ（writing-plans 側で具体化）

```
Phase 1: 環境準備
  - pyproject.toml に依存4つ追加
  - uv sync
  - notebook/FILING_NLP/ ディレクトリ作成
  - .gitignore に notebook/FILING_NLP/data/ 追加

Phase 2: _helpers.py 実装
  - setup_hf_cache / setup_edgar / get_device
  - SECTION_PATTERNS_10Q（AAPL の 10-Q で手動検証含む）
  - chunk_text / load_finbert / load_embedder
  - スモークセル（FinBERT 1チャンク推論で動作確認）

Phase 3: 01_fetch_and_chunk.ipynb
  - SEC EDGAR 取得 → セクション抽出 → チャンク化 → 3 Parquet 保存

Phase 4: 02_finbert_sentiment.ipynb
  - FinBERT 推論 → sentiments.parquet → 可視化

Phase 5: 03_embedding_analysis.ipynb
  - bge embedding → embeddings.parquet → 変化検知 + UMAP + 類似度
```

### 成功判定

- [ ] `01_fetch_and_chunk.ipynb` を Run All で実行し、エラーなく 60 filing × 2 section の chunks.parquet が生成される（10-Q 抽出失敗は許容、ただしログで件数把握）
- [ ] `02_finbert_sentiment.ipynb` を Run All で実行し、`sentiments.parquet` の各行が pos+neg+neu ≈ 1.0 を満たす
- [ ] `03_embedding_analysis.ipynb` を Run All で実行し、UMAP 散布図で AAPL / MSFT / GOOGL が**ある程度**分離するか、しないかを目視判断できる（成功・失敗の判断ではなく、観察結果が出ること自体が成功）
