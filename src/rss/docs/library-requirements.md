# ライブラリ要求定義書 (Library Requirements Document)

## ライブラリ概要

### 名称
**rss** - RSS フィード収集・集約ライブラリ

### ライブラリの目的
- **多様なフィード収集**: RSS 2.0 / Atom フォーマットに対応し、金融メディア、経済データソース、個人ブログなど多様なソースからフィードを収集
- **構造化データ管理**: フィード情報とアイテムをJSON形式で構造化して保存し、検索・分析を容易にする
- **AIエージェント連携**: MCPサーバーとして機能し、Claude Codeなどのエージェントから利用可能なAPI提供

### 解決する課題
金融情報の収集において、複数の情報源を手動で巡回するのは非効率である。
RSSフィードは標準化されているが、パース処理・データ保存・検索機能を毎回実装するのは手間がかかる。
本ライブラリは、外部RSSフィードの収集・パース・構造化保存を統合的に提供し、
AIエージェントからも利用可能なAPIを提供することで、金融情報収集の効率化と自動化を実現する。

### 提供する価値
- 金融メディア・経済データソースのRSSフィードを統一的に収集・管理
- JSON形式での構造化保存により、検索・分析が容易
- 手動実行と日次バッチ実行の両方に対応し、柔軟な運用が可能
- MCPサーバーとしてClaude Codeから直接利用できる
- Pythonベースで拡張性が高く、カスタム処理の追加が容易

## 想定利用者

### プライマリー利用者: Pythonアプリケーション開発者（経験2年以上）
- 金融情報の収集・分析を行うPythonアプリケーションを開発
- RSSフィードから情報を取得し、データベースやファイルに保存したい
- 複数の情報源からの収集を効率化したい
- AIエージェント（Claude Code等）と連携した自動化を期待
- 典型的な使用シナリオ:
  - 主要金融メディアのRSSフィードを日次で取得し、記事データベースを構築
  - 経済指標の更新情報をRSSで監視し、分析パイプラインをトリガー
  - Claude Codeから最新記事を検索・取得し、レポート生成に活用

### セカンダリー利用者: データアナリスト
- 金融ニュースや経済データの定性的分析を実施
- RSSフィードから収集したデータをJSON形式で取得し、分析ツールで処理
- 特定のキーワードやカテゴリでフィルタリングした情報が必要

## 成功指標

### 品質指標
- テストカバレッジ: 80%以上
  - 測定方法: pytest-cov による自動計測
- 型カバレッジ: 100%（py.typed 対応）
  - 測定方法: pyright による型チェックエラー0件
- ドキュメントカバレッジ: 全公開APIにNumPy形式のdocstring
  - 測定方法: コードレビューで確認

### パフォーマンス指標
- フィード取得時間: 1フィードあたり5秒以内（ネットワーク遅延除く）
  - 測定方法: 実フィードでのベンチマーク
- JSON保存・読込時間: 100アイテムあたり100ms以内
  - 測定方法: pytest-benchmark による計測
- メモリ使用量: 1000アイテム処理時に100MB以内
  - 測定方法: memory_profiler による計測

### 運用性指標
- フィード取得成功率: 95%以上（エラーハンドリング含む）
  - 測定方法: 日次バッチ実行ログの集計
- エラー時の適切なログ出力: 全エラーケースでログレベルERROR以上で記録
  - 測定方法: ログレビュー

## 技術的考慮事項

### 技術スタック
- **HTTPクライアント**: httpx（非同期対応）
- **RSSパーサー**: feedparser
- **データ形式**: JSON（標準ライブラリ）
- **ファイルロック**: filelock
- **MCPプロトコル**: mcp（Anthropic MCP SDK）
- **スケジューリング**: schedule または APScheduler（オプション）
- **CLI**: click（オプション）

### 依存ライブラリ

**必須依存**:
- `httpx>=0.27.0`: 非同期HTTP/HTTPSクライアント
- `feedparser>=6.0.0`: RSS/Atomパーサー
- `filelock>=3.20.0`: ファイルロック機構
- `structlog>=25.4.0`: 構造化ロギング（financeパッケージから継承）

**オプショナル依存**:
- `apscheduler>=3.10.0`: 日次バッチ実行用スケジューラー（P1機能）
- `mcp>=0.9.0`: MCPサーバー実装（P1機能）
- `click>=8.1.0`: CLIインターフェース（P1機能）

**pyproject.toml追加内容**:
```toml
[project]
dependencies = [
    # 既存の依存関係...
    "httpx>=0.27.0",
    "feedparser>=6.0.0",
]

[project.optional-dependencies]
scheduler = ["apscheduler>=3.10.0"]
mcp = ["mcp>=0.9.0"]
cli = ["click>=8.1.0"]
all = ["apscheduler>=3.10.0", "mcp>=0.9.0", "click>=8.1.0"]
```

### 制約・依存関係
- Python 3.12+
- ネットワークアクセスが必要
- 各RSSフィードのレート制限に注意
- feedparser によるパース結果の検証が必要

### データ構造設計

**feeds.json（フィード管理マスター）**:
```json
{
  "version": "1.0",
  "feeds": [
    {
      "feed_id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://example.com/feed.xml",
      "title": "Example Feed",
      "category": "finance",
      "fetch_interval": "daily",
      "created_at": "2026-01-14T10:00:00Z",
      "updated_at": "2026-01-14T10:00:00Z",
      "last_fetched": "2026-01-14T10:00:00Z",
      "last_status": "success",
      "enabled": true
    }
  ]
}
```

**{feed_id}/items.json（フィードアイテム保存）**:
```json
{
  "version": "1.0",
  "feed_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "item_id": "660e8400-e29b-41d4-a716-446655440001",
      "title": "Article Title",
      "link": "https://example.com/article",
      "published": "2026-01-14T09:00:00Z",
      "summary": "Article summary...",
      "content": "Full content...",
      "author": "Author Name",
      "fetched_at": "2026-01-14T10:00:00Z"
    }
  ]
}
```

**ファイルディレクトリ構造**:
```
data/raw/rss/
├── feeds.json                          # フィード管理マスター
├── .feeds.lock                         # feeds.json用ファイルロック
├── 550e8400-e29b-41d4-a716-446655440000/
│   ├── items.json                      # フィードアイテム
│   └── .items.lock                     # items.json用ファイルロック
└── 660e8400-e29b-41d4-a716-446655440001/
    ├── items.json
    └── .items.lock
```

## 機能要件

### コア機能(MVI)

#### 1. フィード管理（ユーザー・AI共同管理）

**使用例**:
Pythonアプリケーション開発者として、複数のRSSフィードを登録・管理するために、フィード情報の追加・削除・一覧取得APIが欲しい。
また、AIエージェントとして、ユーザーの指示に基づいてフィード情報を自動更新できる機能が欲しい。

**受け入れ条件**:
- [ ] フィード登録時に、URL、タイトル、カテゴリ、更新頻度を指定できる
- [ ] 登録済みフィードの一覧を取得できる
- [ ] フィードIDを指定してフィード情報を削除できる
- [ ] フィード情報を更新できる（URL、タイトル、カテゴリ、更新頻度）
- [ ] フィード情報はJSON形式で data/raw/rss/feeds.json に保存される
- [ ] feeds.jsonは手動編集可能な読みやすい形式（インデント付きJSON）
- [ ] 同一URLの重複登録はエラーとして検出される
- [ ] URLバリデーション: HTTP/HTTPSスキーマのみ許可
- [ ] フィードIDは自動生成（UUID v4形式）
- [ ] フィード追加時にURL到達性を確認（オプション、デフォルトON）

**共同管理の仕組み**:
- **手動管理**: Python API、CLI、feeds.jsonの直接編集
- **自動管理**: AIエージェント（Claude Code等）がMCP経由でフィードを追加・更新・削除
- **同期**: feeds.jsonを単一の真実のソース（Single Source of Truth）として管理
- **コンフリクト回避**: ファイルロック機構により同時書き込みを防止

**優先度**: P0(必須)

#### 2. RSS/Atomパース

**使用例**:
Pythonアプリケーション開発者として、様々なフォーマットのRSSフィードを統一的に扱うために、RSS 2.0とAtomの両方に対応したパース機能が欲しい

**受け入れ条件**:
- [ ] RSS 2.0フォーマットを正常にパースできる
- [ ] Atomフォーマットを正常にパースできる
- [ ] パース結果を統一的なデータ構造（title, link, published, summary, content, author）に変換できる
- [ ] パースエラー時に適切な例外を発生させる
- [ ] 不正なXML/HTMLをパースした際にエラーハンドリングが動作する

**優先度**: P0(必須)

#### 3. HTTP/HTTPSフィード取得

**使用例**:
Pythonアプリケーション開発者として、外部RSSフィードを安全に取得するために、HTTP/HTTPS経由でのフィード取得機能とエラーハンドリングが欲しい

**受け入れ条件**:
- [ ] HTTP/HTTPS経由でフィードを取得できる
- [ ] タイムアウト時間を設定できる（デフォルト10秒）
- [ ] 404エラー時に適切な例外を発生させる
- [ ] ネットワークエラー時にリトライ機構が動作する（最大3回、指数バックオフ: 1秒、2秒、4秒）
- [ ] リトライ対象エラー: タイムアウト、接続エラー、5xxエラー（500-599）
- [ ] リトライ対象外エラー: 4xxエラー（404等のクライアントエラー）、パースエラー
- [ ] User-Agentヘッダーを設定できる（デフォルト: "rss-feed-collector/0.1.0"）
- [ ] HTTPステータスコードをログに記録する
- [ ] リトライ時にログレベルWARNINGで記録する

**優先度**: P0(必須)

#### 4. 差分取得（重複排除）

**使用例**:
Pythonアプリケーション開発者として、同じアイテムを重複して保存しないために、既存アイテムとの差分を検出する機能が欲しい

**受け入れ条件**:
- [ ] アイテムの一意性をURL（link）で判定できる
- [ ] 既存アイテムと新規アイテムを区別できる
- [ ] 新規アイテムのみを抽出できる
- [ ] 取得済みアイテムの情報をキャッシュとして保持できる

**優先度**: P0(必須)

#### 5. JSON形式保存

**使用例**:
Pythonアプリケーション開発者として、取得したフィードデータを他システムと連携するために、JSON形式で保存する機能が欲しい

**受け入れ条件**:
- [ ] フィード情報を data/raw/rss/feeds.json に保存できる
- [ ] フィードアイテムを data/raw/rss/{feed_id}/items.json に保存できる
- [ ] JSON形式は UTF-8 エンコーディングで保存される
- [ ] 保存時に適切なディレクトリ構造が自動生成される
- [ ] 既存ファイルが存在する場合は差分追記ができる

**優先度**: P0(必須)

#### 6. 手動実行API

**使用例**:
Pythonアプリケーション開発者として、必要な時にフィードを取得するために、Python関数経由で手動実行できるAPIが欲しい

**受け入れ条件**:
- [ ] 特定のフィードIDを指定して取得を実行できる
- [ ] 全フィードを一括取得できる
- [ ] 取得結果（成功/失敗、アイテム数）を返す
- [ ] エラー時に適切な例外またはエラー情報を返す

**優先度**: P0(必須)

### APIインターフェース

```python
# フィード管理
from rss import FeedManager

manager = FeedManager()

# フィード登録
feed_id = manager.add_feed(
    url="https://example.com/feed.xml",
    title="Example Feed",
    category="finance",
    fetch_interval="daily"
)

# フィード一覧取得
feeds = manager.list_feeds()

# フィード更新
manager.update_feed(
    feed_id,
    title="Updated Feed Title",
    category="economics"
)

# フィード削除
manager.remove_feed(feed_id)

# フィード取得
from rss import FeedFetcher

fetcher = FeedFetcher(manager)

# 特定フィード取得
result = fetcher.fetch_feed(feed_id)
# result: {"success": True, "items_count": 10, "new_items": 5}

# 全フィード取得
results = fetcher.fetch_all()
# results: [{"feed_id": "...", "success": True, ...}, ...]

# フィードアイテム取得
from rss import FeedReader

reader = FeedReader()
items = reader.get_items(feed_id, limit=10)
# items: [{"title": "...", "link": "...", ...}, ...]

# キーワード検索（title, summary, contentを検索）
items = reader.search_items(
    query="金利",
    category="finance",
    fields=["title", "summary"],  # 検索対象フィールド（デフォルト: 全て）
    limit=50
)
# items: [{"title": "...", "link": "...", ...}, ...]
```

### 将来的な機能(Post-MVI)

#### 7. 日次バッチ実行

**使用例**:
Pythonアプリケーション開発者として、定期的にフィードを自動取得するために、スケジューラーと連携した日次バッチ実行機能が欲しい

**受け入れ条件**:
- [ ] APSchedulerを使用した日次スケジュール設定ができる
- [ ] 実行時刻を指定できる（デフォルト: 毎日午前6時）
- [ ] バッチ実行時に全登録フィードを順次取得する
- [ ] 各フィードの取得結果（成功/失敗）をログに記録する
- [ ] バッチ実行の開始・終了をINFOレベルでログ記録する
- [ ] エラー発生時もバッチ処理を継続する（1フィードの失敗が全体を止めない）
- [ ] バッチ実行の統計情報（成功数、失敗数、取得アイテム数）を出力する

**連携方法**:
```python
from rss import FeedFetcher, FeedManager
from apscheduler.schedulers.blocking import BlockingScheduler

manager = FeedManager()
fetcher = FeedFetcher(manager)
scheduler = BlockingScheduler()

# 毎日午前6時に実行
scheduler.add_job(
    fetcher.fetch_all,
    'cron',
    hour=6,
    minute=0
)

scheduler.start()
```

**優先度**: P1(重要)

#### 8. CLIインターフェース

**使用例**:
Pythonアプリケーション開発者として、コマンドラインから簡単にフィード管理と取得を実行するために、CLIインターフェースが欲しい

**受け入れ条件**:
- [ ] `rss-cli` コマンドでCLIを起動できる
- [ ] 以下のサブコマンドを提供:
  - `add`: フィード登録
  - `list`: フィード一覧表示
  - `update`: フィード情報更新
  - `remove`: フィード削除
  - `fetch`: フィード取得実行
  - `items`: アイテム一覧表示
  - `search`: アイテム検索
- [ ] `--help` オプションで使用方法を表示
- [ ] JSON形式での出力オプション（`--json`）
- [ ] エラー時に適切な終了コードを返す（0=成功、1=エラー）

**コマンド仕様**:
```bash
# フィード登録
rss-cli add --url https://example.com/feed.xml --title "Example" --category finance

# フィード一覧
rss-cli list
rss-cli list --json  # JSON形式

# フィード更新
rss-cli update <feed_id> --title "New Title"

# フィード削除
rss-cli remove <feed_id>

# フィード取得
rss-cli fetch <feed_id>        # 特定フィード
rss-cli fetch --all             # 全フィード

# アイテム一覧
rss-cli items <feed_id> --limit 10

# アイテム検索
rss-cli search --query "金利" --category finance
```

**優先度**: P1(重要)

#### 9. MCPサーバー機能

**使用例**:
Claude Codeユーザーとして、エージェントから直接RSSフィード情報を取得するために、MCPサーバー経由でのアクセス機能が欲しい

**受け入れ条件**:
- [ ] MCPプロトコル（stdio transport）に対応したサーバー実装
- [ ] 以下のMCPツールを提供:
  - `rss_list_feeds`: 登録済みフィード一覧を取得
  - `rss_get_items`: 指定フィードの最新アイテムを取得
  - `rss_search_items`: キーワード検索でアイテムを取得
  - `rss_add_feed`: 新規フィードを登録
  - `rss_update_feed`: フィード情報を更新
  - `rss_remove_feed`: フィードを削除
  - `rss_fetch_feed`: 指定フィードを即座に取得
- [ ] エラー時に適切なMCPエラーレスポンスを返す
- [ ] Claude Codeの `.mcp.json` に登録可能な形式で提供
- [ ] `claude mcp add` コマンドで簡単に追加可能

**Claude Code統合方法**:
```bash
# プロジェクトルートで実行
claude mcp add rss -- uvx rss-mcp

# または .mcp.json に追加
{
  "mcpServers": {
    "rss": {
      "command": "uvx",
      "args": ["rss-mcp"],
      "env": {
        "RSS_DATA_DIR": "./data/raw/rss"
      }
    }
  }
}
```

**MCPツール仕様例**:
```json
{
  "name": "rss_get_items",
  "description": "指定されたRSSフィードから最新アイテムを取得します",
  "inputSchema": {
    "type": "object",
    "properties": {
      "feed_id": {
        "type": "string",
        "description": "フィードID（省略時は全フィード）"
      },
      "limit": {
        "type": "integer",
        "description": "取得するアイテム数（デフォルト: 10）",
        "default": 10
      },
      "category": {
        "type": "string",
        "description": "カテゴリフィルタ（省略可）"
      }
    }
  }
}
```

**レスポンス例**:
```json
{
  "items": [
    {
      "item_id": "uuid-here",
      "feed_id": "feed-uuid",
      "feed_title": "Example Feed",
      "title": "記事タイトル",
      "link": "https://example.com/article",
      "published": "2026-01-14T09:00:00Z",
      "summary": "記事の要約...",
      "author": "著者名",
      "fetched_at": "2026-01-14T10:00:00Z"
    }
  ],
  "total": 100
}
```

**優先度**: P1(重要)

#### 10. フィルタリング・集約機能

カテゴリ、キーワード、日付範囲でのフィルタリングと集約機能

**優先度**: P2(できれば)

## 非機能要件

### パフォーマンス
- フィード取得時間: 1フィードあたり5秒以内（ネットワーク遅延除く）
  - ベンチマーク: 主要10フィードで測定
- JSON保存・読込時間: 100アイテムあたり100ms以内
  - ベンチマーク: pytest-benchmark で測定
- メモリ使用量: 1000アイテム処理時に100MB以内
  - プロファイリング: memory_profiler で測定
- 同時フィード取得: 最大5フィード並列取得対応（httpx async使用）

### 互換性
- Python 3.12+ 対応
  - 確認方法: CI/CDでPython 3.12, 3.13でテスト実行
- 主要な型チェッカー（pyright）対応
  - 確認方法: make typecheck でエラー0件
- 主要OSでの動作確認（Linux, macOS, Windows）
  - 確認方法: GitHub Actionsで3OS環境でテスト

### 信頼性
- 全公開APIのテストカバレッジ: 80%以上
  - 確認方法: pytest-cov で自動計測
- エラー発生時の明確なメッセージ
  - 確認方法: エラーメッセージに原因・対処法を含む
- ネットワークエラー時のリトライ機構
  - 確認方法: テストでリトライ動作を検証
- 不正なフィードへの対処
  - 確認方法: パースエラーを適切にハンドリング

### テスト要件
- ユニットテスト: 各関数・クラスの単体テスト
  - カバレッジ目標: 80%以上
- 統合テスト: フィード取得から保存までの統合テスト
  - モックサーバーを使用した実フィード模擬
- プロパティテスト: Hypothesisによるパース処理のテスト
  - 不正なXML/HTMLへの対処を検証

### セキュリティ
- HTTPS接続時の証明書検証
- User-Agent設定による適切な識別
- タイムアウト設定によるDoS対策
- 入力検証（URL形式、JSON構造）

### ロギング
- 全フィード取得操作をINFOレベルでログ記録
- エラー時はERRORレベルで詳細情報を記録
- 構造化ロギング（finance.utils.logging_config使用）

### エラーハンドリング

**カスタム例外クラス**:
```python
class RSSError(Exception):
    """RSS パッケージの基底例外"""
    pass

class FeedNotFoundError(RSSError):
    """フィードが見つからない"""
    pass

class FeedAlreadyExistsError(RSSError):
    """フィードが既に存在する"""
    pass

class FeedFetchError(RSSError):
    """フィード取得に失敗"""
    pass

class FeedParseError(RSSError):
    """フィードのパースに失敗"""
    pass

class InvalidURLError(RSSError):
    """無効なURL形式"""
    pass

class FileLockError(RSSError):
    """ファイルロック取得に失敗"""
    pass
```

**例外使用方針**:
- `FeedNotFoundError`: 存在しないフィードIDを指定した場合
- `FeedAlreadyExistsError`: 既に登録されているURLを再登録しようとした場合
- `FeedFetchError`: HTTP取得時のエラー（リトライ後も失敗）
- `FeedParseError`: RSS/Atomパース時のエラー
- `InvalidURLError`: URLバリデーション失敗時
- `FileLockError`: ファイルロック取得タイムアウト時

### ファイルロック機構

**実装方法**:
- `filelock` ライブラリを使用
- ロックファイル: `.feeds.lock`, `.items.lock`
- タイムアウト: 10秒（デフォルト）
- スコープ: feeds.json全体、items.json個別

**使用例**:
```python
from filelock import FileLock, Timeout

lock_file = data_dir / ".feeds.lock"
lock = FileLock(lock_file, timeout=10)

try:
    with lock:
        # feeds.json の読み書き
        pass
except Timeout:
    raise FileLockError(f"Failed to acquire lock: {lock_file}")
```

### 並列フィード取得

**実装方法**:
- `httpx.AsyncClient` を使用した非同期HTTP取得
- `asyncio.gather()` で並列実行
- 並列数: デフォルト5、最大10まで設定可能
- エラー時の挙動: 1フィードの失敗が他フィードに影響しない

**API仕様**:
```python
# 並列取得の設定
fetcher = FeedFetcher(manager, max_concurrent=5)

# 非同期実行
results = await fetcher.fetch_all_async()
# results: [{"feed_id": "...", "success": True, ...}, ...]

# 同期ラッパー（内部でasyncioを使用）
results = fetcher.fetch_all()  # デフォルトで並列実行
```

## スコープ外

明示的にスコープ外とする項目:
- RSSフィードの生成機能（取得・パースのみ）
- データベース（SQLite/DuckDB）への保存（JSON保存のみ）
- リアルタイム監視・通知機能（手動・日次バッチのみ）
- WebUIでのフィード管理（CLIとPython APIのみ）
- フィードコンテンツの自動翻訳・要約（生データのみ保存）
- 画像・動画の取得・保存（テキストデータのみ）
