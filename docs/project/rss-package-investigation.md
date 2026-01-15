# src/rss/ パッケージ調査報告

**作成日**: 2026-01-15
**関連Issue**: #147
**調査目的**: 既存の `src/rss/` パッケージの構造とAPIを調査し、金融ニュース収集機能での活用方法を明確化する

---

## 1. パッケージ概要

### 1.1 基本情報

- **パッケージ名**: `rss`
- **バージョン**: 0.1.0
- **目的**: RSS/Atomフィードの取得、パース、差分検出、永続化、スケジューリング機能を提供
- **実装状況**: 全モジュール実装済み（5,515行）

### 1.2 主要機能

1. **フィード登録・管理**: URL検証、カテゴリ分類、取得間隔設定
2. **フィード取得・パース**: RSS 2.0/Atom対応、並列取得（最大10並列）
3. **差分検出**: 新規エントリーのみ抽出（重複除外）
4. **JSON永続化**: フィード情報・エントリーをJSON形式で保存
5. **検索機能**: キーワード検索、カテゴリフィルタ、ページング
6. **MCP統合**: Claude Codeから利用可能な7つのMCPツール
7. **バッチスケジューリング**: APSchedulerによる自動取得（オプション）

---

## 2. パッケージ構造

### 2.1 ディレクトリ構成

```
src/rss/
├── __init__.py              # 公開API定義
├── types.py                 # 型定義（Feed, FeedItem, FetchResult等）
├── exceptions.py            # カスタム例外
├── cli/                     # CLIインターフェース
│   └── main.py
├── core/                    # コア機能
│   ├── http_client.py       # HTTPリクエスト（httpx使用）
│   ├── parser.py            # RSS/Atomパーサー（feedparser使用）
│   └── diff_detector.py     # 差分検出（link重複チェック）
├── services/                # サービス層（ビジネスロジック）
│   ├── feed_manager.py      # フィード管理
│   ├── feed_fetcher.py      # フィード取得（並列処理対応）
│   ├── feed_reader.py       # フィード読み込み・検索
│   └── batch_scheduler.py   # バッチスケジューリング
├── storage/                 # 永続化層
│   ├── json_storage.py      # JSON保存/読み込み
│   └── lock_manager.py      # ファイルロック（並列安全性）
├── validators/              # バリデーション
│   └── url_validator.py     # URL検証
├── mcp/                     # MCP統合
│   └── server.py            # MCPサーバー（7ツール提供）
└── utils/
    └── logging_config.py    # 構造化ロギング
```

### 2.2 レイヤー分離

```
┌─────────────────────────┐
│   MCP Server Layer      │  MCPツール（7個）
├─────────────────────────┤
│   Service Layer         │  FeedManager, FeedFetcher, FeedReader
├─────────────────────────┤
│   Core Layer            │  HTTPClient, Parser, DiffDetector
├─────────────────────────┤
│   Storage Layer         │  JSONStorage, LockManager
└─────────────────────────┘
```

---

## 3. 公開API

### 3.1 主要クラス

#### 3.1.1 FeedManager（フィード管理）

**責務**: フィード登録・更新・削除・一覧取得

```python
from pathlib import Path
from rss import FeedManager, FetchInterval

manager = FeedManager(Path("data/raw/rss"))

# フィード登録
feed = manager.add_feed(
    url="https://jp.reuters.com/world/rss",
    title="Reuters Japan - World",
    category="finance",
    fetch_interval=FetchInterval.DAILY,
    validate_url=False,  # URL到達性チェック（任意）
    enabled=True,
)

# フィード一覧
feeds = manager.list_feeds(category="finance", enabled_only=True)

# フィード更新
manager.update_feed(
    feed.feed_id,
    title="New Title",
    enabled=False,
)

# フィード削除
manager.remove_feed(feed.feed_id)

# プリセット一括登録
from pathlib import Path
result = manager.apply_presets(Path("data/config/rss-presets.json"))
print(f"Added: {result.added}, Skipped: {result.skipped}")
```

**主要メソッド**:
- `add_feed(url, title, category, ...)` → Feed
- `list_feeds(category=None, enabled_only=False)` → list[Feed]
- `get_feed(feed_id)` → Feed
- `update_feed(feed_id, ...)` → Feed
- `remove_feed(feed_id)` → None
- `apply_presets(presets_file)` → PresetApplyResult

#### 3.1.2 FeedFetcher（フィード取得）

**責務**: フィード取得・パース・差分検出・保存を統合

```python
from pathlib import Path
from rss import FeedFetcher

fetcher = FeedFetcher(Path("data/raw/rss"))

# 全フィード取得（並列処理）
results = fetcher.fetch_all(category="finance", max_concurrent=5)
for result in results:
    if result.success:
        print(f"{result.feed_id}: {result.new_items} new items")
    else:
        print(f"{result.feed_id}: ERROR - {result.error_message}")

# 個別フィード取得
import asyncio
result = asyncio.run(fetcher.fetch_feed(feed.feed_id))
```

**主要メソッド**:
- `fetch_feed(feed_id)` → FetchResult (async)
- `fetch_all_async(category=None, max_concurrent=5)` → list[FetchResult] (async)
- `fetch_all(category=None, max_concurrent=5)` → list[FetchResult] (同期版)

**並列制御**:
- デフォルト並列数: 5
- 最大並列数: 10（上限あり）
- asyncio.Semaphoreによる並列制御

#### 3.1.3 FeedReader（フィード読み込み・検索）

**責務**: 保存済みフィードの読み込み・検索・フィルタリング

```python
from pathlib import Path
from rss import FeedReader

reader = FeedReader(Path("data/raw/rss"))

# 全エントリー取得（ページング）
items = reader.get_items(limit=10, offset=0)

# 特定フィードのエントリー取得
items = reader.get_items(feed_id="550e8400-...", limit=20)

# キーワード検索
results = reader.search_items(
    query="金融政策",
    category="finance",
    fields=["title", "summary", "content"],
    limit=50,
)

for item in results:
    print(f"{item.title}: {item.link}")
```

**主要メソッド**:
- `get_items(feed_id=None, limit=None, offset=0)` → list[FeedItem]
- `search_items(query, category=None, fields=None, limit=None)` → list[FeedItem]

**検索仕様**:
- 部分一致・大文字小文字不問
- デフォルト検索フィールド: title, summary, content
- published日付降順でソート（新しい順）

#### 3.1.4 BatchScheduler（バッチスケジューリング）

**責務**: 定時バッチ実行（APScheduler統合）

```python
from pathlib import Path
from rss import BatchScheduler

# 毎日午前6時に自動取得
scheduler = BatchScheduler.create_from_data_dir(
    Path("data/raw/rss"),
    hour=6,
    minute=0,
)

# 手動実行
stats = scheduler.run_batch()
print(f"Success: {stats.success_count}/{stats.total_feeds}")
print(f"New items: {stats.new_items}")

# バックグラウンド起動
scheduler.start(blocking=False)
# ... アプリケーション処理 ...
scheduler.stop()
```

**注意**: APSchedulerは `finance[scheduler]` extra依存として提供

### 3.2 データモデル

#### 3.2.1 Feed（フィード情報）

```python
@dataclass
class Feed:
    feed_id: str              # UUID v4
    url: str                  # HTTP/HTTPS URL
    title: str                # フィードタイトル（1-200文字）
    category: str             # カテゴリ（1-50文字）
    fetch_interval: FetchInterval  # DAILY, WEEKLY, MANUAL
    created_at: str           # ISO 8601形式
    updated_at: str           # ISO 8601形式
    last_fetched: str | None  # 最終取得日時
    last_status: FetchStatus  # SUCCESS, FAILURE, PENDING
    enabled: bool             # 有効/無効
```

#### 3.2.2 FeedItem（エントリー）

```python
@dataclass
class FeedItem:
    item_id: str          # UUID v4
    title: str            # エントリータイトル
    link: str             # URL
    published: str | None # 公開日時（ISO 8601）
    summary: str | None   # 要約
    content: str | None   # 本文
    author: str | None    # 著者
    fetched_at: str       # 取得日時（ISO 8601）
```

#### 3.2.3 FetchResult（取得結果）

```python
@dataclass
class FetchResult:
    feed_id: str               # フィードID
    success: bool              # 成功/失敗
    items_count: int           # 総アイテム数
    new_items: int             # 新規アイテム数
    error_message: str | None  # エラーメッセージ
```

#### 3.2.4 BatchStats（バッチ統計）

```python
@dataclass
class BatchStats:
    total_feeds: int        # 処理フィード数
    success_count: int      # 成功数
    failure_count: int      # 失敗数
    total_items: int        # 総アイテム数
    new_items: int          # 新規アイテム数
    started_at: str         # 開始日時
    completed_at: str       # 完了日時
    duration_seconds: float # 所要時間（秒）
```

### 3.3 例外クラス

```python
from rss import (
    RSSError,                  # 基底例外
    FeedNotFoundError,         # フィード未発見
    FeedAlreadyExistsError,    # フィード重複
    FeedFetchError,            # 取得失敗
    FeedParseError,            # パース失敗
    InvalidURLError,           # URL不正
    FileLockError,             # ファイルロック失敗
)

try:
    manager.add_feed("invalid-url", "Title", "finance")
except InvalidURLError as e:
    print(f"Invalid URL: {e}")
```

---

## 4. MCP統合

### 4.1 利用可能なMCPツール（7個）

Claude Codeから以下のツールが利用可能:

| ツール名 | 機能 | パラメータ |
|---------|------|-----------|
| `rss_list_feeds` | フィード一覧取得 | category, enabled_only |
| `rss_get_items` | アイテム取得 | feed_id, limit, offset |
| `rss_search_items` | キーワード検索 | query, category, fields, limit |
| `rss_add_feed` | フィード追加 | url, title, category, fetch_interval, validate_url, enabled |
| `rss_update_feed` | フィード更新 | feed_id, title, category, fetch_interval, enabled |
| `rss_remove_feed` | フィード削除 | feed_id |
| `rss_fetch_feed` | 即時取得 | feed_id |

### 4.2 MCP設定例

`.mcp.json`:
```json
{
  "mcpServers": {
    "rss": {
      "command": "uvx",
      "args": ["--from", ".", "rss-mcp"],
      "env": {
        "RSS_DATA_DIR": "./data/raw/rss"
      }
    }
  }
}
```

### 4.3 MCPツール使用例

```python
# Claude Code内で
# 1. フィード一覧取得
await rss_list_feeds(category="finance", enabled_only=True)

# 2. フィード追加
await rss_add_feed(
    url="https://jp.reuters.com/world/rss",
    title="Reuters Japan",
    category="finance",
    fetch_interval="daily"
)

# 3. 即時取得
await rss_fetch_feed(feed_id="550e8400-...")

# 4. キーワード検索
await rss_search_items(query="金利", category="finance", limit=20)
```

---

## 5. データ永続化

### 5.1 保存形式

**ストレージ**: JSON形式（`data/raw/rss/` 配下）

```
data/raw/rss/
├── .feeds.json            # フィード登録情報
└── {feed_id}/
    └── items.json         # フィードエントリー
```

### 5.2 フィード登録データ（.feeds.json）

```json
{
  "version": "1.0",
  "feeds": [
    {
      "feed_id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://jp.reuters.com/world/rss",
      "title": "Reuters Japan - World",
      "category": "finance",
      "fetch_interval": "daily",
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-01-15T10:00:00Z",
      "last_fetched": "2026-01-15T10:30:00Z",
      "last_status": "success",
      "enabled": true
    }
  ]
}
```

### 5.3 エントリーデータ（{feed_id}/items.json）

```json
{
  "version": "1.0",
  "feed_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "item_id": "a1b2c3d4-...",
      "title": "日銀、金融政策決定会合を開催",
      "link": "https://jp.reuters.com/article/...",
      "published": "2026-01-15T09:00:00Z",
      "summary": "日本銀行は15日、金融政策決定会合を開催し...",
      "content": null,
      "author": null,
      "fetched_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

### 5.4 並列安全性

- **ファイルロック**: `storage/lock_manager.py` による排他制御
- **ロックファイル**: `.feeds.lock`, `.items-{feed_id}.lock`
- **タイムアウト**: デフォルト10秒（FileLockError発生）

---

## 6. エラーハンドリング

### 6.1 例外階層

```
Exception
└── RSSError（基底）
    ├── FeedNotFoundError         # フィード未発見
    ├── FeedAlreadyExistsError    # URL重複
    ├── FeedFetchError            # HTTP取得失敗
    ├── FeedParseError            # RSS/Atomパース失敗
    ├── InvalidURLError           # URL検証失敗
    └── FileLockError             # ファイルロック失敗
```

### 6.2 エラーハンドリング例

```python
from rss import FeedManager, FeedAlreadyExistsError, InvalidURLError

manager = FeedManager(Path("data/raw/rss"))

try:
    feed = manager.add_feed(
        url="https://example.com/feed.xml",
        title="Example",
        category="finance",
    )
except InvalidURLError as e:
    print(f"URL validation failed: {e}")
except FeedAlreadyExistsError as e:
    print(f"Feed already exists: {e}")
```

### 6.3 ロギング

**ロガー取得**:
```python
from rss import get_logger

logger = get_logger(__name__, module="my_module")
logger.info("Processing started", item_count=10)
```

**ログ出力形式**:
- 構造化ロギング（キーワード引数による追加フィールド）
- JSON/Text形式切り替え可能（環境変数 `LOG_FORMAT`）
- ログレベル設定: `LOG_LEVEL` 環境変数

---

## 7. 金融ニュース収集での活用方法

### 7.1 基本フロー

```
1. フィード登録（FeedManager）
   ↓
2. 定期取得設定（BatchScheduler / 手動実行）
   ↓
3. フィード取得・パース（FeedFetcher）
   ↓
4. 差分検出・保存（自動）
   ↓
5. キーワード検索（FeedReader）
   ↓
6. 記事作成に活用
```

### 7.2 活用シナリオ

#### シナリオ1: 主要金融ニュースの自動収集

```python
from pathlib import Path
from rss import FeedManager, FeedFetcher, FetchInterval

# 1. フィード登録
manager = FeedManager(Path("data/raw/rss"))

finance_feeds = [
    ("https://jp.reuters.com/world/rss", "Reuters Japan - World", "finance"),
    ("https://www.bloomberg.co.jp/feed/news.rss", "Bloomberg Japan", "finance"),
    ("https://www.nikkei.com/news/feed/", "日経新聞", "finance"),
]

for url, title, category in finance_feeds:
    try:
        manager.add_feed(
            url=url,
            title=title,
            category=category,
            fetch_interval=FetchInterval.DAILY,
        )
        print(f"Added: {title}")
    except FeedAlreadyExistsError:
        print(f"Already exists: {title}")

# 2. 全フィード取得
fetcher = FeedFetcher(Path("data/raw/rss"))
results = fetcher.fetch_all(category="finance", max_concurrent=5)

# 3. 結果確認
total_new_items = sum(r.new_items for r in results if r.success)
print(f"Total new items: {total_new_items}")
```

#### シナリオ2: トピック別ニュース検索

```python
from pathlib import Path
from rss import FeedReader

reader = FeedReader(Path("data/raw/rss"))

# 金利関連ニュース検索
interest_rate_news = reader.search_items(
    query="金利",
    category="finance",
    fields=["title", "summary"],
    limit=50,
)

print(f"Found {len(interest_rate_news)} articles about interest rates")
for item in interest_rate_news[:10]:
    print(f"- {item.title}")
    print(f"  URL: {item.link}")
    print(f"  Published: {item.published}")
    print()
```

#### シナリオ3: MCP経由での記事収集

**Claude Codeとの連携**:

```
User: 最近の金融政策に関するニュースを5件取得して

Claude Code: [MCPツール使用]
-> rss_search_items(query="金融政策", category="finance", limit=5)

結果:
1. 日銀、金融政策決定会合を開催（2026-01-15）
2. FRB、利上げ幅を0.25%に縮小（2026-01-14）
3. ECB、金融政策を据え置き（2026-01-13）
...

User: これらの記事を元に分析記事を作成して

Claude Code: [記事作成処理]
```

### 7.3 推奨される実装パターン

#### パターン1: プリセット管理

**金融ニュースフィードのプリセット定義**（`data/config/finance-news-presets.json`）:

```json
{
  "version": "1.0",
  "presets": [
    {
      "url": "https://jp.reuters.com/world/rss",
      "title": "Reuters Japan - World",
      "category": "finance",
      "fetch_interval": "daily",
      "enabled": true
    },
    {
      "url": "https://www.bloomberg.co.jp/feed/markets.rss",
      "title": "Bloomberg Markets",
      "category": "finance",
      "fetch_interval": "daily",
      "enabled": true
    }
  ]
}
```

**一括登録**:
```python
result = manager.apply_presets(Path("data/config/finance-news-presets.json"))
print(f"Added: {result.added}, Skipped: {result.skipped}, Failed: {result.failed}")
```

#### パターン2: カテゴリ別フィルタリング

```python
# 金融ニュースのみ取得
finance_feeds = manager.list_feeds(category="finance", enabled_only=True)

# カテゴリ別取得
results = fetcher.fetch_all(category="finance", max_concurrent=5)
```

**推奨カテゴリ分類**:
- `finance`: 金融・経済ニュース全般
- `markets`: 市場ニュース
- `central-bank`: 中央銀行関連
- `economics`: 経済指標・レポート
- `crypto`: 暗号資産
- `stocks`: 株式市場

#### パターン3: 定期実行（スケジューラー）

```python
from pathlib import Path
from rss import BatchScheduler

# 毎日午前6時に自動取得
scheduler = BatchScheduler.create_from_data_dir(
    Path("data/raw/rss"),
    hour=6,
    minute=0,
)

# バックグラウンド起動
scheduler.start(blocking=False)

# 必要に応じて手動実行
stats = scheduler.run_batch()
print(f"Fetched: {stats.new_items} new items")
```

### 7.4 記事作成ワークフローへの統合

#### 提案: 金融ニュース収集→記事作成パイプライン

```python
# 1. ニュース収集
from pathlib import Path
from rss import FeedFetcher, FeedReader

fetcher = FeedFetcher(Path("data/raw/rss"))
fetcher.fetch_all(category="finance")

# 2. トピック検索
reader = FeedReader(Path("data/raw/rss"))
items = reader.search_items(
    query="日銀 金利",
    category="finance",
    limit=20,
)

# 3. 記事作成用データとして利用
for item in items:
    article_data = {
        "title": item.title,
        "url": item.link,
        "published": item.published,
        "summary": item.summary,
    }
    # → 既存の記事作成ワークフローに渡す
```

### 7.5 制約と考慮事項

#### 7.5.1 技術的制約

- **フィード形式**: RSS 2.0, Atom のみ対応（JSON Feedは未対応）
- **差分検出**: linkフィールドによる重複判定（GUIDは使用しない）
- **並列実行**: 最大10並列まで（セマフォ制御）
- **永続化**: JSON形式のみ（データベース未対応）

#### 7.5.2 運用上の考慮点

- **取得頻度**: 同一フィードへの過度なアクセスを避ける（推奨: 1時間以上の間隔）
- **エラーハンドリング**: `FeedFetchError`発生時のリトライ戦略
- **ストレージ容量**: エントリー蓄積によるディスク容量増加（定期的なクリーンアップ推奨）
- **URL検証**: `validate_url=True` は初回登録時のみ推奨（定期取得では不要）

#### 7.5.3 拡張検討事項

現在のパッケージに**含まれていない**機能:
- ✗ データベース永続化（現在はJSON）
- ✗ フルテキスト検索（現在は部分一致のみ）
- ✗ エントリーの自動分類・タグ付け
- ✗ 重要度スコアリング
- ✗ 重複記事検出（異なるフィードの同一ニュース）
- ✗ 要約生成・翻訳機能

これらの機能が必要な場合、別パッケージとして実装を検討。

---

## 8. まとめ

### 8.1 主要な発見

1. **完成度**: 全モジュール実装済み、テスト済み、本番利用可能
2. **柔軟性**: 並列取得、カテゴリ分類、検索機能など金融ニュース収集に必要な機能を網羅
3. **統合性**: MCP統合により、Claude Codeから直接利用可能
4. **拡張性**: プリセット機能、バッチスケジューラーなど運用を考慮した設計

### 8.2 金融ニュース収集への適用性

**適している用途**:
- ✓ 主要金融メディアからのニュース自動収集
- ✓ トピック別ニュース検索・フィルタリング
- ✓ 記事作成の情報ソース管理
- ✓ MCP経由での対話的ニュース取得

**適していない用途**:
- ✗ リアルタイム速報（定期取得のため遅延あり）
- ✗ 大規模なアーカイブ検索（全文検索未対応）
- ✗ 記事の自動要約・分類（AI連携が必要）

### 8.3 次のステップ

1. **即座に利用可能**: 既存パッケージをそのまま活用
   - 金融ニュースフィードのプリセット作成
   - MCPツールの動作確認
   - 記事作成ワークフローへの統合検討

2. **将来的な拡張検討**:
   - データベース永続化（DuckDB統合）
   - AI連携（要約生成、重要度スコアリング）
   - 重複記事検出（異なるソースの同一ニュース）

---

## 付録

### A. 利用可能なAPI一覧

| クラス | メソッド | 説明 |
|-------|---------|------|
| `FeedManager` | `add_feed()` | フィード登録 |
| | `list_feeds()` | フィード一覧 |
| | `get_feed()` | フィード取得 |
| | `update_feed()` | フィード更新 |
| | `remove_feed()` | フィード削除 |
| | `apply_presets()` | プリセット一括登録 |
| `FeedFetcher` | `fetch_feed()` | 個別取得（async） |
| | `fetch_all_async()` | 全件取得（async） |
| | `fetch_all()` | 全件取得（同期） |
| `FeedReader` | `get_items()` | エントリー取得 |
| | `search_items()` | キーワード検索 |
| `BatchScheduler` | `run_batch()` | 手動バッチ実行 |
| | `start()` | スケジューラー起動 |
| | `stop()` | スケジューラー停止 |

### B. データモデル一覧

| モデル | 用途 |
|-------|------|
| `Feed` | フィード情報 |
| `FeedItem` | エントリー |
| `FetchResult` | 取得結果 |
| `BatchStats` | バッチ統計 |
| `FetchInterval` | 取得間隔（Enum） |
| `FetchStatus` | ステータス（Enum） |
| `PresetFeed` | プリセット定義 |
| `PresetsConfig` | プリセット設定 |
| `PresetApplyResult` | プリセット適用結果 |

### C. 例外一覧

| 例外 | 発生条件 |
|-----|---------|
| `RSSError` | 基底例外 |
| `FeedNotFoundError` | フィードが見つからない |
| `FeedAlreadyExistsError` | URL重複 |
| `FeedFetchError` | HTTP取得失敗 |
| `FeedParseError` | RSS/Atomパース失敗 |
| `InvalidURLError` | URL検証失敗 |
| `FileLockError` | ファイルロック取得失敗 |

### D. 参考リンク

- パッケージREADME: `src/rss/README.md`
- 実装ドキュメント: `src/rss/docs/`
- テストコード: `tests/rss/`
- MCPサーバー: `src/rss/mcp/server.py`
