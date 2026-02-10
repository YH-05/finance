# edgar - SEC EDGAR Filing Data Extraction Package

SEC EDGAR の有価証券報告書（Filing）データを取得・解析するパッケージ。edgartools ライブラリをバックエンドに使用し、10-K / 10-Q / 13F 等の Filing からテキスト抽出・セクション分割・バッチ処理・キャッシュ管理を提供します。

## インストール

```bash
# uv を使用（このリポジトリ内）
uv sync --all-extras
```

<!-- AUTO-GENERATED: QUICKSTART -->

## クイックスタート

### 最初の5分で試す

**SEC EDGAR から 10-K Filing のテキストを取得する**（最も基本的な使い方）

```python
from edgar.config import set_identity
from edgar.fetcher import EdgarFetcher
from edgar.extractors import TextExtractor
from edgar.types import FilingType

# 1. SEC EDGAR に身元を登録（SEC の Fair Access Policy に準拠）
set_identity("Your Name", "your_email@example.com")

# 2. フェッチャーで Apple の最新 10-K を取得
fetcher = EdgarFetcher()
filing = fetcher.fetch_latest("AAPL", FilingType.FORM_10K)

# 3. テキストを抽出
extractor = TextExtractor()
result = extractor.extract(filing)

# 4. 結果を確認
print(f"Filing ID: {result.filing_id}")
print(f"テキスト長: {len(result.text)} 文字")
```

### よくある使い方

#### 1. セクション別テキスト抽出

```python
from edgar.extractors import SectionExtractor
from edgar.types import SectionKey

# セクション抽出器を使って Item 単位でテキストを取得
section_extractor = SectionExtractor()
result = section_extractor.extract(filing)

# 各セクションにアクセス
for key, text in result.sections.items():
    print(f"{key.value}: {len(text)} 文字")

# 特定のセクションのみ取得
if SectionKey.ITEM_7 in result.sections:
    mda_text = result.sections[SectionKey.ITEM_7]
    print(f"MD&A: {mda_text[:200]}...")
```

#### 2. 複数企業のバッチ取得

```python
from edgar.batch import BatchFetcher, BatchExtractor
from edgar.types import FilingType

# バッチフェッチャーで複数企業の Filing を並列取得
batch_fetcher = BatchFetcher(max_workers=4)
results = batch_fetcher.fetch(
    cik_or_tickers=["AAPL", "MSFT", "GOOGL"],
    form=FilingType.FORM_10K,
    limit=1,
)

# 取得結果を確認（成功/失敗の混在あり）
for ticker, result in results.items():
    if isinstance(result, Exception):
        print(f"{ticker}: 取得失敗 - {result}")
    else:
        print(f"{ticker}: {len(result)} 件取得")

# バッチ抽出でテキストを並列抽出
batch_extractor = BatchExtractor(max_workers=4)
```

#### 3. キャッシュの活用

```python
from edgar.cache import CacheManager
from pathlib import Path

# キャッシュマネージャーを初期化
cache = CacheManager(cache_dir=Path("data/cache/edgar"))

# テキストをキャッシュに保存
cache.put("0001234567-24-000001", "Full filing text content...")

# キャッシュからテキストを取得（TTL 内であれば）
cached_text = cache.get("0001234567-24-000001")
if cached_text is not None:
    print("キャッシュヒット")
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->

## 実装状況

| モジュール | 状態 | 説明 |
|-----------|------|------|
| `types.py` | ✅ 実装済み | 型定義（FilingType, SectionKey, EdgarResult） |
| `errors.py` | ✅ 実装済み | エラークラス階層（EdgarError 他 4 種） |
| `config.py` | ✅ 実装済み | 設定管理（EdgarConfig, identity 管理） |
| `fetcher.py` | ✅ 実装済み | Filing 取得（EdgarFetcher） |
| `rate_limiter.py` | ✅ 実装済み | レート制限（RateLimiter）SEC EDGAR 10req/sec 制限準拠 |
| `extractors/` | ✅ 実装済み | テキスト・セクション抽出（TextExtractor, SectionExtractor） |
| `batch.py` | ✅ 実装済み | バッチ処理（BatchFetcher, BatchExtractor） |
| `cache/` | ✅ 実装済み | SQLite キャッシュ（CacheManager） |

<!-- END: IMPLEMENTATION -->

## サブモジュール

| モジュール | 説明 | 状態 |
|-----------|------|------|
| `edgar.types` | Filing 種別、セクションキー、結果データクラスの型定義 | ✅ 実装済み |
| `edgar.errors` | EdgarError 基底クラスとドメイン固有の例外 4 種 | ✅ 実装済み |
| `edgar.config` | SEC EDGAR identity 管理、キャッシュ・レート制限設定 | ✅ 実装済み |
| `edgar.fetcher` | edgartools ラッパー、CIK/ティッカーでの Filing 取得 | ✅ 実装済み |
| `edgar.rate_limiter` | スレッドセーフなレート制限器（トークンバケット方式） | ✅ 実装済み |
| `edgar.extractors` | テキスト抽出（TextExtractor）、セクション分割（SectionExtractor） | ✅ 実装済み |
| `edgar.batch` | 並列バッチ取得（BatchFetcher）、並列バッチ抽出（BatchExtractor） | ✅ 実装済み |
| `edgar.cache` | SQLite ベースの TTL 付きキャッシュ（CacheManager） | ✅ 実装済み |

<!-- AUTO-GENERATED: API -->

## 公開 API

### 主要クラス

#### EdgarFetcher

SEC EDGAR から Filing を取得するメインクラス。edgartools の `Company` クラスを内部で使用します。

**基本的な使い方**:

```python
from edgar.fetcher import EdgarFetcher
from edgar.types import FilingType

fetcher = EdgarFetcher()

# 最新の10-Kを取得
filing = fetcher.fetch_latest("AAPL", FilingType.FORM_10K)

# 複数件取得
filings = fetcher.fetch("AAPL", FilingType.FORM_10K, limit=5)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `fetch(cik_or_ticker, form, limit)` | 指定条件で Filing を取得 | `list[Any]` |
| `fetch_latest(cik_or_ticker, form)` | 最新の Filing を 1 件取得 | `Any \| None` |

---

#### TextExtractor

Filing オブジェクトからクリーンなテキストを抽出します。

**基本的な使い方**:

```python
from edgar.extractors import TextExtractor

extractor = TextExtractor()
result = extractor.extract(filing)

print(f"Filing ID: {result.filing_id}")
print(f"テキスト長: {len(result.text)} 文字")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `extract(filing)` | Filing からテキストを抽出 | `EdgarResult` |

---

#### SectionExtractor

Filing テキストから Item 単位のセクションを分割・抽出します。

**基本的な使い方**:

```python
from edgar.extractors import SectionExtractor
from edgar.types import SectionKey

extractor = SectionExtractor()
result = extractor.extract(filing)

# セクション別テキストにアクセス
business = result.sections.get(SectionKey.ITEM_1, "")
risks = result.sections.get(SectionKey.ITEM_1A, "")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `extract(filing)` | Filing からセクション別テキストを抽出 | `EdgarResult` |

---

#### BatchFetcher

複数企業の Filing を ThreadPoolExecutor で並列取得します。

**基本的な使い方**:

```python
from edgar.batch import BatchFetcher
from edgar.types import FilingType

batch_fetcher = BatchFetcher(max_workers=4)
results = batch_fetcher.fetch(
    cik_or_tickers=["AAPL", "MSFT", "GOOGL"],
    form=FilingType.FORM_10K,
    limit=1,
)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `fetch(cik_or_tickers, form, limit)` | 複数企業の Filing を並列取得 | `dict[str, list[Any] \| Exception]` |

---

#### BatchExtractor

複数 Filing のテキスト・セクション抽出を並列実行します。

**基本的な使い方**:

```python
from edgar.batch import BatchExtractor

batch_extractor = BatchExtractor(max_workers=4)
results = batch_extractor.extract_text(filings)
section_results = batch_extractor.extract_sections(filings)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `extract_text(filings)` | 複数 Filing のテキストを並列抽出 | `dict[str, EdgarResult \| Exception]` |
| `extract_sections(filings)` | 複数 Filing のセクションを並列抽出 | `dict[str, EdgarResult \| Exception]` |

---

#### CacheManager

SQLite ベースの TTL 付きキャッシュマネージャー。Filing テキストのキャッシュにより再取得コストを削減します。

**基本的な使い方**:

```python
from edgar.cache import CacheManager
from pathlib import Path

cache = CacheManager(cache_dir=Path("data/cache/edgar"))

# キャッシュに保存
cache.put("0001234567-24-000001", "Filing text content...")

# キャッシュから取得（TTL 内であれば）
text = cache.get("0001234567-24-000001")
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `get(filing_id)` | キャッシュから Filing テキストを取得 | `str \| None` |
| `put(filing_id, text)` | Filing テキストをキャッシュに保存 | `None` |

---

#### RateLimiter

SEC EDGAR の Fair Access Policy（10 requests/second）を遵守するためのスレッドセーフなレート制限器。

**基本的な使い方**:

```python
from edgar.rate_limiter import RateLimiter

# デフォルト（10 requests/second）
limiter = RateLimiter()

# カスタム設定
limiter = RateLimiter(max_requests_per_second=5)

# リクエスト前に呼び出す（必要に応じて自動でスリープ）
limiter.acquire()
# ... API リクエストを実行
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|----------|------|--------|
| `acquire()` | リクエスト許可を取得（必要に応じてブロック） | `None` |

**注意**: EdgarFetcher は内部で RateLimiter を自動使用するため、通常は明示的に使用する必要はありません。

---

### データ型

#### FilingType

SEC Filing のフォーム種別を表す列挙型。

```python
from edgar.types import FilingType

FilingType.FORM_10K   # 年次報告書 (10-K)
FilingType.FORM_10Q   # 四半期報告書 (10-Q)
FilingType.FORM_13F   # 機関投資家保有報告書 (13F)

# 文字列からの変換
filing_type = FilingType.from_string("10-K")
```

#### SectionKey

Filing セクションの識別子。

```python
from edgar.types import SectionKey

SectionKey.ITEM_1    # Business（事業内容）
SectionKey.ITEM_1A   # Risk Factors（リスク要因）
SectionKey.ITEM_7    # MD&A（経営者による分析）
SectionKey.ITEM_8    # Financial Statements（財務諸表）
```

#### EdgarResult

Filing データ抽出の結果を格納するデータクラス。

```python
from edgar.types import EdgarResult, SectionKey

result = EdgarResult(
    filing_id="0001234567-24-000001",
    text="Full filing text content",
    sections={SectionKey.ITEM_1: "Business section text"},
    metadata={"company": "Apple Inc."},
)
```

---

### 設定クラス

#### EdgarConfig

SEC EDGAR アクセスの設定を管理するデータクラス。

```python
from edgar.config import EdgarConfig, load_config, set_identity

# 環境変数から設定を読み込み
config = load_config()
print(config.is_identity_configured)

# Identity を設定（SEC Fair Access Policy 準拠）
set_identity("Your Name", "your_email@example.com")
```

---

### エラークラス

| クラス | 説明 |
|--------|------|
| `EdgarError` | 基底例外クラス（message + context） |
| `FilingNotFoundError` | Filing が見つからない、取得失敗 |
| `SectionNotFoundError` | セクション抽出失敗 |
| `CacheError` | キャッシュ操作失敗 |
| `RateLimitError` | SEC EDGAR レート制限超過 |

```python
from edgar.errors import EdgarError, FilingNotFoundError

try:
    filings = fetcher.fetch("INVALID", FilingType.FORM_10K)
except FilingNotFoundError as e:
    print(f"Filing not found: {e}")
    print(f"Context: {e.context}")
except EdgarError as e:
    print(f"Edgar error: {e}")
```

<!-- END: API -->

<!-- AUTO-GENERATED: STRUCTURE -->

## ディレクトリ構造

```
edgar/
├── __init__.py              # 公開 API エクスポート
├── README.md                # パッケージドキュメント
├── types.py                 # 型定義（FilingType, SectionKey, EdgarResult）
├── errors.py                # エラークラス階層
├── config.py                # 設定管理（EdgarConfig, set_identity）
├── fetcher.py               # EdgarFetcher（edgartools ラッパー）
├── rate_limiter.py          # RateLimiter（SEC EDGAR レート制限）
├── batch.py                 # BatchFetcher, BatchExtractor（並列処理）
│
├── extractors/              # テキスト・セクション抽出
│   ├── __init__.py
│   ├── _helpers.py          # 共通ヘルパー関数（accession_number/text 取得）
│   ├── text.py              # TextExtractor（テキスト抽出）
│   └── section.py           # SectionExtractor（セクション分割）
│
└── cache/                   # キャッシュ管理
    ├── __init__.py
    └── manager.py           # CacheManager（SQLite ベース TTL キャッシュ）
```

<!-- END: STRUCTURE -->

## 開発

### テスト実行

```bash
# 全テスト
uv run pytest tests/edgar/

# カバレッジ付き
uv run pytest tests/edgar/ --cov=src/edgar --cov-report=term-missing

# 単体テストのみ
uv run pytest tests/edgar/unit/
```

### 品質チェック

```bash
# フォーマット
uv run ruff format src/edgar/ tests/edgar/

# リント
uv run ruff check src/edgar/ tests/edgar/

# 型チェック
uv run pyright src/edgar/
```

## 関連ドキュメント

- [プロジェクト計画書](../../docs/project/project-41/project.md)
- [コーディング規約](../../docs/coding-standards.md)
- [テスト戦略](../../docs/testing-strategy.md)

## ライセンス

MIT License
