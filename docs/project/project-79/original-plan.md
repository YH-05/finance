# ローカル埋め込みバックエンド統合 設計書

| 項目 | 内容 |
|------|------|
| 作成日 | 2026-04-10 |
| 対象パッケージ | `src/embedding/` |
| ステータス | Draft |
| 関連 | M3 Mac 16GB ローカル環境での埋め込みベクトル生成 |

---

## 1. 背景と目的

### 背景

`src/embedding/` パッケージは現在、ニュース記事 JSON を入力として ChromaDB に格納するパイプラインを提供している。ただし格納されるベクトルは **すべて 768 次元のゼロベクトル（ダミー）** であり、実際の埋め込みモデルは未統合。

クオンツ分析のために、ローカルに保存したマークダウンファイル（リサーチレポート、トランスクリプト要約、SEC EDGAR 抽出テキスト等）を実埋め込みベクトルとして ChromaDB に格納し、ベクトル検索・類似度計算に使えるようにしたい。

### 目的

1. **モデル切り替え可能な埋め込みエンジンを `embedding` パッケージに統合する**
2. **マークダウンディレクトリを再帰的に取り込んで埋め込み・格納する新パイプラインを追加する**
3. **既存ニュースパイプラインの挙動を壊さず、段階的に実埋め込みへ移行する道を用意する**

### 制約

- 実行環境は M3 Mac 16GB（Apple Silicon）
- Apache 2.0 / MIT 等の商用利用可能ライセンスのモデルのみ採用
- 既存テスト・既存 ChromaDB データへの破壊的影響を避ける

---

## 2. スコープ

### 含む

- `EmbeddingBackend` 抽象基底クラスの設計と `SentenceTransformersBackend` 実装
- マークダウンディレクトリ再帰収集 reader
- マークダウン専用パイプライン
- ChromaDB コレクション命名規則（モデル別自動命名）
- CLI サブコマンド `embed-md` の追加
- 既存ニュースパイプラインへの後方互換オプション追加
- 単体・プロパティ・統合テスト

### 含まない（将来課題）

- `OllamaBackend` / `MLXBackend` の実装（インターフェースは用意するが実装は後回し）
- マークダウンのチャンキング（`#`/`##` 単位の分割）
- YAML frontmatter サポート
- マークダウン以外の入力フォーマット（PDF / HTML / TXT 等）
- プロファイル化（事前定義された複数ソース）
- ベクトル検索 CLI / API
- 既存ダミーベクトルデータのマイグレーション

---

## 3. アーキテクチャ

### 3.1 ディレクトリ構造

```
src/embedding/
├── __init__.py
├── __main__.py
├── backends/                    # 新規（バックエンド層）
│   ├── __init__.py
│   ├── base.py                  # EmbeddingBackend 抽象基底クラス
│   ├── factory.py               # create_backend()
│   └── sentence_transformers.py # SentenceTransformersBackend
├── markdown/                    # 新規（マークダウンパイプライン）
│   ├── __init__.py
│   ├── reader.py                # ディレクトリ再帰 + メタデータ抽出
│   └── pipeline.py              # マークダウン用パイプライン
├── chromadb_store.py            # 既存（拡張: backend オプション）
├── pipeline.py                  # 既存（後方互換: backend オプション）
├── reader.py                    # 既存（ニュース記事 JSON reader）
├── extractor.py                 # 既存
├── rate_limiter.py              # 既存
├── types.py                     # 既存（拡張: EmbeddingConfig 追加）
└── cli.py                       # 既存（拡張: embed-md サブコマンド）
```

### 3.2 依存関係（パッケージ内）

```
backends/base.py
    ↑
    │
backends/sentence_transformers.py
backends/factory.py ────────────┐
    ↑                           │
    │                           │
markdown/pipeline.py ───────────┤
chromadb_store.py（拡張）───────┤
pipeline.py（既存・拡張） ──────┘
    ↑
cli.py
```

### 3.3 外部依存追加

`pyproject.toml` の embedding 関連 extras に追加:

```toml
sentence-transformers = ">=2.7.0"
torch = ">=2.0.0"            # MPS バックエンド利用
```

`chromadb`, `numpy`, `trafilatura`, `playwright` は既存。

---

## 4. EmbeddingBackend インターフェース

### 4.1 抽象基底クラス

```python
# backends/base.py
from abc import ABC, abstractmethod
import numpy as np


class EmbeddingBackend(ABC):
    """テキスト埋め込みバックエンドの抽象基底クラス."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """モデル名（HuggingFace ID 等）."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """埋め込みベクトルの次元数."""

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """複数テキストを埋め込む.

        Returns
        -------
        np.ndarray
            shape = (len(texts), dimension), dtype = float32
        """

    def embed_one(self, text: str) -> np.ndarray:
        """単一テキスト用ヘルパー（デフォルト実装）."""
        return self.embed([text])[0]
```

### 4.2 SentenceTransformersBackend

```python
# backends/sentence_transformers.py
class SentenceTransformersBackend(EmbeddingBackend):
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
        device: str = "auto",       # "auto" / "mps" / "cpu" / "cuda"
        batch_size: int = 32,
        normalize: bool = True,     # L2 正規化
    ) -> None: ...

    @property
    def model_name(self) -> str: ...

    @property
    def dimension(self) -> int:
        """初回 embed() 後にキャッシュされる、もしくは model.get_sentence_embedding_dimension()."""

    def embed(self, texts: list[str]) -> np.ndarray:
        """SentenceTransformer.encode() のラッパー."""
```

**device の自動検出**:
- `"auto"`: `torch.backends.mps.is_available()` → `mps`、それ以外は `cpu`
- 明示指定（`mps`/`cpu`）はそのまま採用

**normalize**:
- `True` の場合、各ベクトルを L2 正規化（コサイン類似度 = 内積として扱える）
- ChromaDB のデフォルト距離は L2 だが、normalize 済みベクトルなら内積/コサインと等価

### 4.3 Factory

```python
# backends/factory.py
def create_backend(config: EmbeddingConfig) -> EmbeddingBackend:
    """EmbeddingConfig からバックエンドインスタンスを生成."""
    if config.backend == "sentence-transformers":
        return SentenceTransformersBackend(
            model_name=config.model_name,
            device=config.device,
            batch_size=config.batch_size,
            normalize=config.normalize,
        )
    msg = f"Unknown backend: {config.backend}"
    raise ValueError(msg)
```

将来 `"ollama"` / `"mlx"` を追加する際は、ここに分岐を追加するだけ。

---

## 5. EmbeddingConfig

```python
# types.py に追加
@dataclass
class EmbeddingConfig:
    """埋め込みバックエンド設定."""

    backend: str = "sentence-transformers"
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    device: str = "auto"
    batch_size: int = 32
    normalize: bool = True
```

---

## 6. マークダウンパイプライン

### 6.1 reader

```python
# markdown/reader.py
@dataclass
class MarkdownDocument:
    """マークダウン文書の表現."""

    source_path: str        # 入力ディレクトリからの相対パス（POSIX 形式）
    filename: str           # ファイル名のみ
    title: str              # 最初の H1 見出し、なければ filename
    content: str            # 全文
    file_size: int          # バイト数
    file_mtime: str         # ISO 8601


def read_markdown_directory(
    input_dir: Path,
    pattern: str = "**/*.md",
) -> list[MarkdownDocument]:
    """ディレクトリを再帰的に走査して MarkdownDocument のリストを返す."""


def extract_title(content: str, fallback: str) -> str:
    """マークダウンの最初の H1 (`# title`) を抽出。なければ fallback."""
```

**仕様詳細**:
- `input_dir.rglob(pattern)` で `*.md` を収集
- ソート順: `source_path` 昇順（再現性のため）
- 空ファイルはスキップ（warning ログ）
- UTF-8 デコードエラーはスキップ（warning ログ）

### 6.2 pipeline

```python
# markdown/pipeline.py
@dataclass
class MarkdownPipelineConfig:
    """マークダウンパイプライン設定."""

    input_dir: Path
    chromadb_path: Path
    base_collection_name: str           # ユーザー指定
    embedding: EmbeddingConfig
    pattern: str = "**/*.md"


def run_markdown_pipeline(
    config: MarkdownPipelineConfig,
) -> dict[str, int]:
    """マークダウンパイプラインを実行.

    1. read_markdown_directory()
    2. derive_collection_name() でコレクション名生成
    3. create_backend() でバックエンド生成
    4. get_existing_ids() で既存 ID 取得
    5. 新規ドキュメントのみ抽出
    6. backend.embed() で実埋め込み
    7. store_markdown_documents() で ChromaDB 格納

    Returns
    -------
    dict[str, int]
        - total_files
        - already_in_chromadb
        - new_documents
        - embedded
        - stored
    """
```

**ID 生成**:
- ChromaDB ID = `sha256(source_path)[:16]`
- ファイルパスベースなので、内容更新時は同じ ID で上書き判定が可能（将来課題: mtime ベースの差分更新）

**チャンキング**: なし。1ファイル = 1ドキュメント = 1埋め込み（YAGNI）

---

## 7. ChromaDB 格納（拡張）

### 7.1 コレクション命名

```python
# chromadb_store.py に追加
def derive_collection_name(base_name: str, model_name: str) -> str:
    """ベース名とモデル名から最終コレクション名を導出.

    Examples
    --------
    >>> derive_collection_name("research-docs", "Qwen/Qwen3-Embedding-0.6B")
    'research-docs__qwen3-embedding-0.6b'
    >>> derive_collection_name("news", "BAAI/bge-m3")
    'news__bge-m3'
    """
    slug = model_name.split("/")[-1].lower().replace("_", "-")
    return f"{base_name}__{slug}"
```

### 7.2 マークダウン用 store 関数

```python
def store_markdown_documents(
    documents: list[MarkdownDocument],
    embeddings: np.ndarray,
    chromadb_path: Path,
    collection_name: str,
    backend: EmbeddingBackend,
) -> int:
    """マークダウン文書を ChromaDB に格納.

    Metadata
    --------
    - source_path: str
    - filename: str
    - title: str
    - file_size: int
    - file_mtime: str (ISO 8601)
    - embedded_at: str (ISO 8601)
    - embedding_model: str
    - embedding_dim: int
    """
```

### 7.3 既存 store_articles の後方互換

```python
def store_articles(
    articles: list[ArticleRecord],
    results: list[ExtractionResult],
    chromadb_path: Path,
    collection_name: str,
    dummy_dim: int,
    backend: EmbeddingBackend | None = None,  # 新規追加
) -> int:
    """
    backend=None の場合: 従来通りダミーベクトル
    backend 指定時: backend.embed() で実埋め込み計算
    """
```

`PipelineConfig` にも対応する `embedding_backend: EmbeddingBackend | None = None` を追加し、`run_pipeline()` を後方互換のまま拡張。

---

## 8. CLI

### 8.1 既存（変更なし）

```bash
uv run python -m embedding              # ニュースパイプライン（ダミーベクトル）
```

### 8.2 新規サブコマンド

```bash
uv run python -m embedding embed-md \
    --input-dir research/ \
    --collection research-docs \
    --model Qwen/Qwen3-Embedding-0.6B \
    --device auto \
    --batch-size 32 \
    --chromadb-path data/chromadb
```

**オプション**:

| オプション | デフォルト | 説明 |
|----------|----------|------|
| `--input-dir` | (必須) | マークダウンディレクトリ |
| `--collection` | (必須) | ベースコレクション名 |
| `--model` | `Qwen/Qwen3-Embedding-0.6B` | モデル名 |
| `--device` | `auto` | `auto`/`mps`/`cpu` |
| `--batch-size` | `32` | バッチサイズ |
| `--chromadb-path` | `<DATA_DIR>/chromadb` | ChromaDB パス |
| `--pattern` | `**/*.md` | glob パターン |
| `--no-normalize` | (フラグ) | L2 正規化を無効化 |

---

## 9. テスト戦略

### 9.1 テスト構成

```
tests/embedding/
├── unit/
│   ├── backends/
│   │   ├── test_factory.py
│   │   └── test_sentence_transformers.py     # SentenceTransformer はモック
│   ├── markdown/
│   │   ├── test_reader.py
│   │   └── test_pipeline.py                  # backend はモック
│   ├── test_collection_naming.py
│   └── test_types.py
├── property/
│   ├── test_backend_properties.py            # shape / normalize 不変条件
│   └── test_collection_naming_properties.py
└── integration/
    ├── test_markdown_pipeline_e2e.py         # backend モック + ChromaDB
    └── test_real_qwen3_embedding.py          # @pytest.mark.slow（実モデル）
```

### 9.2 主要テストケース

#### unit / backends

- `SentenceTransformersBackend` がモデル名・次元数を正しく公開する
- `embed([])` が `shape=(0, dim)` を返す
- `embed([text])` の shape が `(1, dim)` で float32
- `normalize=True` 時の L2 norm が ≒1
- `device="auto"` 時の MPS 検出ロジック
- `create_backend(config)` の分岐動作
- 未知の backend 名で `ValueError`

#### unit / markdown / reader

- 単一ファイル読み込み
- 再帰的なディレクトリ走査
- 空ファイルのスキップ
- UTF-8 デコードエラーのスキップ
- `extract_title()`: H1 あり / H1 なし / 複数 H1（最初を使用）
- ソート順の再現性

#### unit / markdown / pipeline

- 全フローのモック統合（reader + backend + chromadb_store すべてモック）
- 既存 ID のスキップ
- 全件新規 / 全件既存 / 混在
- 空ディレクトリで空結果

#### unit / collection_naming

- `derive_collection_name("research", "Qwen/Qwen3-Embedding-0.6B")` → `"research__qwen3-embedding-0.6b"`
- スラッシュなしモデル名: `"bge-m3"` → `"research__bge-m3"`
- アンダースコア変換: `"foo_bar"` → `"foo-bar"`

#### property

- `embed(texts)` の shape == `(len(texts), dimension)`（任意の長さ・内容）
- `normalize=True` 時、各ベクトルの L2 norm が `1.0 ± 1e-5`
- `derive_collection_name` の冪等性

#### integration

- マークダウンパイプライン E2E（backend モック + 一時 ChromaDB）
- 既存ニュースパイプラインの後方互換（`backend=None` でダミー動作）
- 実モデル統合（`@pytest.mark.slow`）: Qwen3-Embedding-0.6B で 3 ファイル埋め込み

### 9.3 モック戦略

- `SentenceTransformer` 自体は重いので unit テストでは必ずモック
- 統合テストの実モデルテストは `@pytest.mark.slow` でデフォルト除外
- ChromaDB は `PersistentClient(tmp_path)` で各テストごとに分離

---

## 10. 実装ステップ（TDD ベース）

| Step | 内容 | 委譲先 |
|------|------|--------|
| 1 | `pyproject.toml` に `sentence-transformers`, `torch` を追加 | 直接 |
| 2 | `types.py` に `EmbeddingConfig` を追加 | feature-implementer |
| 3 | `backends/base.py`（抽象基底クラス）+ unit テスト | test-writer → feature-implementer |
| 4 | `backends/sentence_transformers.py` + unit テスト（モック）+ property テスト | test-writer → feature-implementer |
| 5 | `backends/factory.py` + unit テスト | test-writer → feature-implementer |
| 6 | `markdown/reader.py` + unit テスト | test-writer → feature-implementer |
| 7 | `chromadb_store.py` 拡張: `derive_collection_name`, `store_markdown_documents` + unit テスト | test-writer → feature-implementer |
| 8 | `markdown/pipeline.py` + integration テスト（モック） | test-writer → feature-implementer |
| 9 | `pipeline.py` 後方互換拡張（`embedding_backend` オプション）+ 既存テスト全通過確認 | feature-implementer |
| 10 | `cli.py` に `embed-md` サブコマンド追加 + テスト | feature-implementer |
| 11 | 実モデル統合テスト（`@pytest.mark.slow`） | test-integration-writer |
| 12 | quality-checker --auto-fix で `make check-all` 通過 | quality-checker |

各 Step で Red → Green → Refactor サイクルを守る。

---

## 11. リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| sentence-transformers + torch が大きい依存 | uv sync が遅くなる | `[project.optional-dependencies]` の `embedding` extras に分離 |
| MPS バックエンドが特定モデルで未対応 op を持つ | 実行時エラー | `PYTORCH_ENABLE_MPS_FALLBACK=1` をドキュメント明記、`device="cpu"` フォールバック |
| Qwen3-Embedding-0.6B 初回ロードが遅い | UX 悪化 | 初回ロードは進捗表示、CLI に `--warmup` オプションは追加せず実測確認 |
| 既存ニュースパイプラインが壊れる | 既存テスト失敗 | `backend=None` がデフォルトを保証、既存テストを必ず通す |
| ChromaDB 次元数不一致エラー | 実行時例外 | `derive_collection_name` でモデル別コレクションに自動分離 |
| pyright が `sentence_transformers` の型を解決できない | 型チェック失敗 | `# type: ignore[import-untyped]` または stub 追加 |

---

## 12. 受け入れ基準

- [ ] `EmbeddingBackend` 抽象基底クラスと `SentenceTransformersBackend` が実装されている
- [ ] `create_backend()` Factory が動作する
- [ ] `markdown/reader.py` がマークダウンディレクトリを再帰的に走査できる
- [ ] `markdown/pipeline.py` が ChromaDB に実埋め込みベクトルを格納できる
- [ ] `derive_collection_name()` でモデル別コレクション名が自動生成される
- [ ] 各ドキュメントの metadata に `embedding_model`, `embedding_dim` が記録される
- [ ] 既存ニュースパイプライン (`run_pipeline`) は `backend=None` で従来通り動作する（既存テスト全通過）
- [ ] CLI `embed-md` サブコマンドが動作する
- [ ] 単体・プロパティ・統合テストが追加され `make check-all` が通る
- [ ] 実モデル統合テスト（`@pytest.mark.slow`）が手動で通る

---

## 13. 将来課題

- `OllamaBackend`（Qwen3-Embedding-8B Q4 等）
- `MLXBackend`（Apple Silicon ネイティブ最適化）
- マークダウンチャンキング（見出し単位 / 固定トークン）
- YAML frontmatter サポート
- ベクトル検索 CLI / API
- プロファイル化（複数ソースの事前定義）
- マークダウン以外の入力（PDF / HTML / TXT）
- 既存ダミーベクトルデータのマイグレーションスクリプト
- mtime ベースの差分更新（内容変更の自動検知）

---

## 関連ドキュメント

- 既存パッケージ: `src/embedding/`
- コーディング規約: `.claude/rules/coding-standards.md`
- テスト戦略: `.claude/rules/testing-strategy.md`
- サブエージェント データ渡し: `.claude/rules/subagent-data-passing.md`
