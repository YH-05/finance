# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

```
src/rss/
├── core/                   # データ処理層
│   ├── http_client.py      # HTTP/HTTPS通信
│   ├── parser.py           # RSS/Atomパーサー
│   └── diff_detector.py    # 差分検出
├── services/               # サービス層
│   ├── feed_manager.py     # フィード管理
│   ├── feed_fetcher.py     # フィード取得
│   └── feed_reader.py      # アイテム読込
├── storage/                # データ永続化層
│   ├── json_storage.py     # JSON読み書き
│   └── lock_manager.py     # ファイルロック制御
├── validators/             # 入力検証
│   └── url_validator.py    # URL・文字列長検証
├── cli/                    # CLIインターフェース（P1機能）
│   └── main.py             # CLIエントリーポイント
├── mcp/                    # MCPサーバー（P1機能）
│   └── server.py           # MCPサーバー実装
├── types.py                # 型定義
├── exceptions.py           # カスタム例外クラス
├── __init__.py             # パッケージエントリーポイント
├── py.typed                # PEP 561マーカー
└── README.md               # パッケージ概要

tests/
├── unit/                   # ユニットテスト
│   ├── core/               # データ処理層のテスト
│   │   ├── test_http_client.py
│   │   ├── test_parser.py
│   │   └── test_diff_detector.py
│   ├── services/           # サービス層のテスト
│   │   ├── test_feed_manager.py
│   │   ├── test_feed_fetcher.py
│   │   └── test_feed_reader.py
│   ├── storage/            # データ永続化層のテスト
│   │   ├── test_json_storage.py
│   │   └── test_lock_manager.py
│   └── validators/         # 入力検証のテスト
│       └── test_url_validator.py
├── integration/            # 統合テスト
│   └── test_feed_workflow.py  # フィード登録→取得→検索
├── property/               # プロパティベーステスト
│   ├── test_parser_property.py
│   └── test_diff_detector_property.py
└── conftest.py             # テストフィクスチャ

data/raw/rss/               # データ保存先
├── feeds.json              # フィード管理マスター
├── .feeds.lock             # feeds.json用ロック
├── {feed_id}/              # フィードアイテムディレクトリ
│   ├── items.json          # アイテムデータ
│   └── .items.lock         # items.json用ロック

docs/                       # プロジェクトドキュメント
├── library-requirements.md      # LRD
├── functional-design.md         # 機能設計書
├── architecture.md              # アーキテクチャ設計書
└── repository-structure.md      # 本ドキュメント
```

## ディレクトリ詳細

### src/rss/ (パッケージルート)

#### core/ (データ処理層)

**役割**: HTTP通信、RSS/Atomパース、差分検出など、外部データの取得・変換を担当

**配置ファイル**:
- `http_client.py`: HTTPClient実装（httpx.AsyncClient使用、リトライ機構付き）
- `parser.py`: FeedParser実装（feedparser使用、RSS 2.0/Atom対応）
- `diff_detector.py`: DiffDetector実装（linkベースの差分検出）

**命名規則**:
- クラス名: PascalCase（例: `HTTPClient`, `FeedParser`, `DiffDetector`）
- ファイル名: snake_case（例: `http_client.py`, `parser.py`, `diff_detector.py`）

**依存関係**:
- 依存可能: `types.py`, `exceptions.py`, 外部ライブラリ（httpx, feedparser）
- 依存禁止: `services/`, `storage/`, `validators/`, `cli/`, `mcp/`

**例**:
```python
# core/http_client.py
from rss.types import HTTPResponse
from rss.exceptions import FeedFetchError
import httpx


class HTTPClient:
    async def fetch(
        self, url: str, timeout: int = 10, max_retries: int = 3
    ) -> HTTPResponse:
        ...
```

#### services/ (サービス層)

**役割**: ビジネスロジックの実装、フィード管理・取得・読込の統合制御

**配置ファイル**:
- `feed_manager.py`: FeedManager実装（フィード登録・更新・削除・一覧取得）
- `feed_fetcher.py`: FeedFetcher実装（フィード取得、並列取得対応）
- `feed_reader.py`: FeedReader実装（アイテム読込、キーワード検索）

**命名規則**:
- クラス名: PascalCase（例: `FeedManager`, `FeedFetcher`, `FeedReader`）
- ファイル名: snake_case（例: `feed_manager.py`, `feed_fetcher.py`, `feed_reader.py`）

**依存関係**:
- 依存可能: `core/`, `storage/`, `validators/`, `types.py`, `exceptions.py`
- 依存禁止: `cli/`, `mcp/`（UIレイヤーへの依存禁止）

**例**:
```python
# services/feed_manager.py
from rss.types import Feed, FeedsData, FetchInterval
from rss.storage.json_storage import JSONStorage
from rss.validators.url_validator import URLValidator
from rss.exceptions import FeedAlreadyExistsError


class FeedManager:
    def add_feed(
        self, url: str, title: str, category: str,
        fetch_interval: FetchInterval = FetchInterval.DAILY,
        validate_url: bool = True
    ) -> str:
        ...
```

#### storage/ (データ永続化層)

**役割**: JSON形式でのデータ保存・読込、ファイルロック制御

**配置ファイル**:
- `json_storage.py`: JSONStorage実装（feeds.json, items.jsonの読み書き）
- `lock_manager.py`: LockManager実装（filelock使用、タイムアウト制御）

**命名規則**:
- クラス名: PascalCase（例: `JSONStorage`, `LockManager`）
- ファイル名: snake_case（例: `json_storage.py`, `lock_manager.py`）

**依存関係**:
- 依存可能: `types.py`, `exceptions.py`, 外部ライブラリ（filelock）
- 依存禁止: `core/`, `services/`, `validators/`, `cli/`, `mcp/`

**例**:
```python
# storage/json_storage.py
from pathlib import Path
from rss.types import FeedsData, FeedItemsData
from rss.storage.lock_manager import LockManager


class JSONStorage:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.lock_manager = LockManager(data_dir)

    def save_feeds(self, data: FeedsData) -> None:
        with self.lock_manager.lock_feeds():
            ...
```

#### validators/ (入力検証)

**役割**: URL形式検証、文字列長検証

**配置ファイル**:
- `url_validator.py`: URLValidator実装（HTTP/HTTPSスキーマチェック、文字列長検証）

**命名規則**:
- クラス名: PascalCase（例: `URLValidator`）
- ファイル名: snake_case（例: `url_validator.py`）

**依存関係**:
- 依存可能: `exceptions.py`
- 依存禁止: `core/`, `services/`, `storage/`, `cli/`, `mcp/`

**例**:
```python
# validators/url_validator.py
from rss.exceptions import InvalidURLError


class URLValidator:
    def validate_url(self, url: str) -> bool:
        if not url.startswith(("http://", "https://")):
            raise InvalidURLError(f"HTTP/HTTPSスキーマのみ許可されます: {url}")
        return True
```

#### cli/ (CLIインターフェース、P1機能)

**役割**: コマンドライン操作の提供（click使用）

**配置ファイル**:
- `main.py`: CLIエントリーポイント（7つのサブコマンド実装）

**命名規則**:
- ファイル名: snake_case（例: `main.py`）
- コマンド関数名: 動詞形式（例: `add`, `list`, `update`, `remove`, `fetch`, `items`, `search`）

**依存関係**:
- 依存可能: `services/`, `types.py`, `exceptions.py`
- 依存禁止: `core/`, `storage/`, `validators/`（下位レイヤーへの直接依存禁止）

**例**:
```python
# cli/main.py
import click
from rss.services.feed_manager import FeedManager


@click.group()
def cli():
    """RSS フィード収集・集約ツール"""
    pass


@cli.command()
@click.option("--url", required=True, help="フィードURL")
@click.option("--title", required=True, help="フィードタイトル")
@click.option("--category", required=True, help="カテゴリ名")
def add(url: str, title: str, category: str):
    """新規フィードを登録する"""
    manager = FeedManager()
    feed_id = manager.add_feed(url, title, category)
    click.echo(f"フィードを登録しました (ID: {feed_id})")
```

#### mcp/ (MCPサーバー、P1機能)

**役割**: MCPプロトコル実装、Claude Code連携

**配置ファイル**:
- `server.py`: MCPサーバー実装（stdio transport、7つのMCPツール）

**命名規則**:
- ファイル名: snake_case（例: `server.py`）
- MCPツール名: `rss_` + 動詞形式（例: `rss_list_feeds`, `rss_get_items`, `rss_add_feed`）

**依存関係**:
- 依存可能: `services/`, `types.py`, `exceptions.py`
- 依存禁止: `core/`, `storage/`, `validators/`, `cli/`（下位レイヤーへの直接依存禁止）

**例**:
```python
# mcp/server.py
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from rss.services.feed_manager import FeedManager
from rss.services.feed_reader import FeedReader


async def main():
    server = Server("rss")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="rss_list_feeds", description="...", inputSchema={...}),
            Tool(name="rss_get_items", description="...", inputSchema={...}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "rss_list_feeds":
            manager = FeedManager()
            feeds = manager.list_feeds(**arguments)
            return {"feeds": [asdict(f) for f in feeds]}
        ...
```

#### types.py (型定義)

**役割**: 全モジュールで使用される型定義の集約

**配置内容**:
- Enum定義: `FetchInterval`, `FetchStatus`
- dataclass定義: `Feed`, `FeedItem`, `FeedsData`, `FeedItemsData`, `HTTPResponse`, `FetchResult`

**命名規則**:
- Enum: PascalCase + 単数形（例: `FetchInterval`, `FetchStatus`）
- dataclass: PascalCase + 単数形（例: `Feed`, `FeedItem`）

**依存関係**:
- 依存可能: 標準ライブラリのみ
- 依存禁止: 全てのプロジェクト内モジュール

**例**:
```python
# types.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class FetchInterval(str, Enum):
    """フィード取得間隔"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


@dataclass
class Feed:
    """フィード情報モデル"""
    feed_id: str
    url: str
    title: str
    category: str
    fetch_interval: FetchInterval
    created_at: datetime
    updated_at: datetime
    last_fetched: datetime | None
    last_status: str
    enabled: bool
```

#### exceptions.py (カスタム例外クラス)

**役割**: パッケージ固有の例外クラス定義

**配置内容**:
- 基底例外: `RSSError`
- 個別例外: `FeedNotFoundError`, `FeedAlreadyExistsError`, `FeedFetchError`, `FeedParseError`, `InvalidURLError`, `FileLockError`

**命名規則**:
- 例外クラス: PascalCase + `Error`サフィックス（例: `RSSError`, `FeedNotFoundError`）

**依存関係**:
- 依存可能: 標準ライブラリのみ
- 依存禁止: 全てのプロジェクト内モジュール

**例**:
```python
# exceptions.py
class RSSError(Exception):
    """RSS パッケージの基底例外"""
    pass


class FeedNotFoundError(RSSError):
    """フィードが見つからない"""
    pass


class FeedAlreadyExistsError(RSSError):
    """フィードが既に存在する"""
    pass
```

#### __init__.py (パッケージエントリーポイント)

**役割**: 公開APIのエクスポート

**配置内容**:
- サービス層の公開クラス: `FeedManager`, `FeedFetcher`, `FeedReader`
- 型定義の公開: `Feed`, `FeedItem`, `FetchInterval`, `FetchStatus`, `FetchResult`
- 例外クラスの公開: 全カスタム例外

**例**:
```python
# __init__.py
"""
RSS フィード収集・集約ライブラリ

Usage:
    from rss import FeedManager, FeedFetcher, FeedReader

    manager = FeedManager()
    feed_id = manager.add_feed(url="https://example.com/feed.xml", ...)
"""

from rss.services.feed_manager import FeedManager
from rss.services.feed_fetcher import FeedFetcher
from rss.services.feed_reader import FeedReader
from rss.types import Feed, FeedItem, FetchInterval, FetchStatus, FetchResult
from rss.exceptions import (
    RSSError,
    FeedNotFoundError,
    FeedAlreadyExistsError,
    FeedFetchError,
    FeedParseError,
    InvalidURLError,
    FileLockError,
)

__all__ = [
    "FeedManager",
    "FeedFetcher",
    "FeedReader",
    "Feed",
    "FeedItem",
    "FetchInterval",
    "FetchStatus",
    "FetchResult",
    "RSSError",
    "FeedNotFoundError",
    "FeedAlreadyExistsError",
    "FeedFetchError",
    "FeedParseError",
    "InvalidURLError",
    "FileLockError",
]
```

### tests/ (テストディレクトリ)

#### unit/ (ユニットテスト)

**役割**: 各モジュールの単体テスト

**構造**:
```
tests/unit/
├── core/                   # データ処理層のテスト
│   ├── test_http_client.py
│   ├── test_parser.py
│   └── test_diff_detector.py
├── services/               # サービス層のテスト
│   ├── test_feed_manager.py
│   ├── test_feed_fetcher.py
│   └── test_feed_reader.py
├── storage/                # データ永続化層のテスト
│   ├── test_json_storage.py
│   └── test_lock_manager.py
└── validators/             # 入力検証のテスト
    └── test_url_validator.py
```

**命名規則**:
- パターン: `test_[テスト対象ファイル名].py`
- 例: `http_client.py` → `test_http_client.py`
- テストクラス名: `Test[クラス名]`（例: `TestHTTPClient`）
- テスト関数名: `test_[機能]_[条件]`（例: `test_validate_url_with_invalid_schema`）

**カバレッジ目標**: 80%以上

#### integration/ (統合テスト)

**役割**: フルフロー（フィード登録 → 取得 → 検索）のテスト

**構造**:
```
tests/integration/
└── test_feed_workflow.py       # フルフローテスト
```

**テストケース例**:
- フィード登録 → 取得 → アイテム保存 → 検索
- 並列フィード取得
- ファイルロック競合のシミュレーション

#### property/ (プロパティベーステスト)

**役割**: Hypothesisによる不正入力への対処検証

**構造**:
```
tests/property/
├── test_parser_property.py         # 不正なXML/HTMLへの対処
└── test_diff_detector_property.py  # 任意のアイテムリストで差分検出
```

**テストケース例**:
```python
from hypothesis import given, strategies as st


@given(st.text(min_size=1, max_size=200))
def test_validate_title_with_random_string(title: str):
    """任意の1-200文字文字列は検証を通過する"""
    validator = URLValidator()
    assert validator.validate_title(title) is True
```

#### conftest.py (テストフィクスチャ)

**役割**: 共通テストフィクスチャの定義

**配置内容**:
- `tmp_data_dir`: 一時データディレクトリ
- `mock_feed_manager`: モックFeedManager
- `mock_rss_server`: モックRSSサーバー（pytest-httpserver使用）

### data/raw/rss/ (データ保存先)

**役割**: RSSフィードとアイテムのJSON保存

**構造**:
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

**ファイル形式**:
- UTF-8エンコーディング
- インデント付きJSON（手動編集可能）

**自動生成ルール**:
- `data/raw/rss/`: 初回保存時に自動生成
- `{feed_id}/`: フィードアイテム保存時に自動生成
- `.feeds.lock`, `.items.lock`: LockManagerが自動生成

**環境変数**:
- `RSS_DATA_DIR`: データディレクトリのカスタマイズ（デフォルト: `./data/raw/rss`）

### docs/ (ドキュメントディレクトリ)

**配置ドキュメント**:
- `library-requirements.md`: ライブラリ要求定義書（LRD）
- `functional-design.md`: 機能設計書
- `architecture.md`: アーキテクチャ設計書
- `repository-structure.md`: リポジトリ構造定義書（本ドキュメント）

## ファイル配置規則

### ソースファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| HTTP通信 | core/ | snake_case | http_client.py |
| パーサー | core/ | snake_case | parser.py |
| 差分検出 | core/ | snake_case | diff_detector.py |
| サービス | services/ | snake_case + `_service`サフィックス推奨 | feed_manager.py, feed_fetcher.py |
| ストレージ | storage/ | snake_case + `_storage`サフィックス推奨 | json_storage.py, lock_manager.py |
| バリデーター | validators/ | snake_case + `_validator`サフィックス | url_validator.py |
| CLIコマンド | cli/ | snake_case | main.py |
| MCPサーバー | mcp/ | snake_case | server.py |
| 型定義 | パッケージルート | types.py | types.py |
| 例外クラス | パッケージルート | exceptions.py | exceptions.py |

### テストファイル

| テスト種別 | 配置先 | 命名規則 | 例 |
|----------|--------|---------|-----|
| ユニットテスト | tests/unit/ | test_[対象].py | test_http_client.py |
| 統合テスト | tests/integration/ | test_[機能].py | test_feed_workflow.py |
| プロパティテスト | tests/property/ | test_[対象]_property.py | test_parser_property.py |

### 設定ファイル

| ファイル種別 | 配置先 | 命名規則 |
|------------|--------|---------|
| パッケージ設定 | プロジェクトルート | pyproject.toml |
| 型チェック設定 | pyproject.toml | [tool.pyright] |
| テスト設定 | pyproject.toml | [tool.pytest.ini_options] |
| リント設定 | pyproject.toml | [tool.ruff] |

## 命名規則

### ディレクトリ名

- **レイヤーディレクトリ**: 複数形、snake_case
  - 例: `services/`, `validators/`, `storage/`
- **機能ディレクトリ**: 単数形、snake_case
  - 例: `core/`, `cli/`, `mcp/`

### ファイル名

- **モジュールファイル**: snake_case
  - 例: `feed_manager.py`, `http_client.py`, `json_storage.py`
- **型定義ファイル**: `types.py`
- **例外クラスファイル**: `exceptions.py`

### テストファイル名

- パターン: `test_[テスト対象].py`
- 例: `test_feed_manager.py`, `test_http_client.py`

### クラス名

- **サービスクラス**: PascalCase + `Service`/`Manager`/`Fetcher`/`Reader`サフィックス
  - 例: `FeedManager`, `FeedFetcher`, `FeedReader`
- **データ処理クラス**: PascalCase + 機能名
  - 例: `HTTPClient`, `FeedParser`, `DiffDetector`
- **ストレージクラス**: PascalCase + `Storage`/`Manager`サフィックス
  - 例: `JSONStorage`, `LockManager`
- **バリデータークラス**: PascalCase + `Validator`サフィックス
  - 例: `URLValidator`

### 関数名

- **パブリックメソッド**: snake_case + 動詞形式
  - 例: `add_feed()`, `fetch_feed()`, `search_items()`
- **プライベートメソッド**: `_` + snake_case + 動詞形式
  - 例: `_fetch_feed_async()`, `_validate_url()`

## 依存関係のルール

### レイヤー間の依存

```
UIレイヤー (cli/, mcp/)
    ↓ (OK)
サービスレイヤー (services/)
    ↓ (OK)
データ処理レイヤー (core/)
データ永続化レイヤー (storage/)
入力検証レイヤー (validators/)
    ↓ (OK)
共通モジュール (types.py, exceptions.py)
```

**許可される依存**:
- UI → サービス (✅)
- サービス → データ処理・永続化・検証 (✅)
- 全レイヤー → 共通モジュール (✅)

**禁止される依存**:
- データ処理・永続化・検証 → サービス (❌)
- データ処理・永続化・検証 → UI (❌)
- サービス → UI (❌)
- データ処理 → データ永続化 (❌)（相互独立を維持）
- データ永続化 → データ処理 (❌)（相互独立を維持）

### モジュール間の依存

**循環依存の禁止**:
```python
# ❌ 悪い例: 循環依存
# feed_manager.py
from rss.services.feed_fetcher import FeedFetcher

# feed_fetcher.py
from rss.services.feed_manager import FeedManager  # 循環依存
```

**解決策: Protocolで型定義を抽出**:
```python
# types.py
from typing import Protocol


class FeedManagerProtocol(Protocol):
    def get_feed(self, feed_id: str) -> Feed: ...


# feed_fetcher.py
from rss.types import FeedManagerProtocol


class FeedFetcher:
    def __init__(self, manager: FeedManagerProtocol) -> None:
        self.manager = manager
```

## スケーリング戦略

### 機能の追加

新しい機能を追加する際の配置方針:

1. **小規模機能**: 既存ディレクトリに配置
   - 例: `feed_reader.py`に新規メソッド追加
2. **中規模機能**: レイヤー内に新規ファイルを作成
   - 例: `services/feed_validator.py`を追加
3. **大規模機能**: 独立したディレクトリとして分離
   - 例: `services/notification/`ディレクトリを作成

**例**:
```
# 小規模機能の追加
src/rss/services/
├── feed_manager.py         # 既存
├── feed_fetcher.py         # 既存
└── feed_reader.py          # 既存（新規メソッド追加）

# 中規模機能の追加
src/rss/services/
├── feed_manager.py         # 既存
├── feed_fetcher.py         # 既存
├── feed_reader.py          # 既存
└── feed_validator.py       # 新規ファイル

# 大規模機能の追加（P2機能: データベース対応）
src/rss/storage/
├── json_storage.py         # 既存
├── lock_manager.py         # 既存
├── database/               # 新規ディレクトリ
│   ├── sqlite_storage.py   # SQLite対応
│   └── duckdb_storage.py   # DuckDB対応
```

### ファイルサイズの管理

**ファイル分割の目安**:
- 1ファイル: 300行以下を推奨
- 300-500行: リファクタリングを検討
- 500行以上: 分割を強く推奨

**分割方法**:
```python
# 悪い例: 1ファイルに全機能
# feed_fetcher.py (800行)

# 良い例: 責務ごとに分割
# feed_fetcher.py (200行) - 基本的なフィード取得
# feed_fetcher_async.py (150行) - 非同期並列取得
# feed_fetcher_retry.py (100行) - リトライ機構
```

### P1機能の追加計画

**MCPサーバー機能**:
```
src/rss/mcp/
├── server.py               # MCPサーバー実装
├── tools/                  # MCPツール実装（規模に応じて分離）
│   ├── feed_tools.py       # フィード管理ツール
│   └── item_tools.py       # アイテム取得ツール
```

**CLIインターフェース**:
```
src/rss/cli/
├── main.py                 # CLIエントリーポイント
└── commands/               # コマンド実装（規模に応じて分離）
    ├── feed_commands.py    # フィード管理コマンド
    └── item_commands.py    # アイテム取得コマンド
```

## pyproject.toml設定

### エントリーポイント

```toml
[project.scripts]
rss-cli = "rss.cli.main:cli"      # P1機能
rss-mcp = "rss.mcp.server:main"   # P1機能
```

### オプショナル依存

```toml
[project.optional-dependencies]
scheduler = ["apscheduler>=3.10.0"]
mcp = ["mcp>=0.9.0"]
cli = ["click>=8.1.0"]
all = ["apscheduler>=3.10.0", "mcp>=0.9.0", "click>=8.1.0"]
```

## 除外設定

### .gitignore

```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.venv/
venv/

# テスト
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# データ（プロジェクト特有）
data/raw/rss/*.json
data/raw/rss/*/*.json
data/raw/rss/.*.lock
!data/raw/rss/.gitkeep

# ログ
*.log

# OS
.DS_Store
Thumbs.db
```

### Ruff除外設定 (pyproject.toml)

```toml
[tool.ruff]
exclude = [
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "*.egg-info",
]
```

## まとめ

本リポジトリ構造定義書は、rssライブラリの具体的なディレクトリ構造を定義しました。

**構造の特徴**:
- **レイヤードアーキテクチャの反映**: アーキテクチャ設計のレイヤー構造をディレクトリに反映
- **責務の明確化**: 各ディレクトリが単一の明確な役割を持つ
- **依存関係の制御**: レイヤー間の依存ルールにより、循環依存を防止
- **スケーラビリティ**: 機能追加に応じた拡張方針を明確化

**命名規則の統一**:
- ディレクトリ: snake_case、複数形（レイヤー）または単数形（機能）
- ファイル: snake_case、サフィックス推奨（`_service`, `_storage`等）
- クラス: PascalCase、サフィックス必須（`Service`, `Manager`, `Fetcher`等）
- 関数: snake_case、動詞形式

**テスト戦略の反映**:
- ユニットテスト: srcと同じ構造
- 統合テスト: 機能単位
- プロパティテスト: Hypothesis使用

次のステップは、この構造に基づいて各モジュールの実装とテストを進めることです。
