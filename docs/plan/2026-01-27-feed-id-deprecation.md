# feed_id 廃止計画

## 概要

RSS フィード管理で使用している `feed_id`（UUID形式）を廃止し、URL を直接識別子として使用する方式に移行する。

## 背景

### 現状の問題

1. **二重管理**: `feeds.json` と各エージェントの両方で feed_id を管理
2. **可読性**: UUID を見ても何のフィードか分からない
3. **過剰設計**: 個人プロジェクトの規模では UUID による管理は不要
4. **同期コスト**: フィード追加時にエージェント側の更新が必要

### 期待される効果

- 設定の一元化（URL のみで識別）
- 可読性の向上
- メンテナンスコストの削減

## 影響範囲

### 調査結果サマリー

| カテゴリ | ファイル数 | 影響度 |
|----------|-----------|--------|
| エージェント (.claude/agents/) | 13 | 高 |
| スキル (.claude/skills/) | 1 | 中 |
| コマンド (.claude/commands/) | 1 | 低 |
| Python コア (src/rss/) | 12 | 高 |
| テスト (tests/rss/) | 18 | 中 |
| スクリプト (scripts/) | 2 | 低 |
| 設定 (.mcp.json, feeds.json) | 2 | 高 |

**合計**: 約 50 ファイル

### 主要な変更対象

#### 1. MCP サーバー (src/rss/mcp/server.py)

7 つの MCP ツールが feed_id をパラメータとして使用：

| ツール | 現在のパラメータ | 変更後 |
|--------|-----------------|--------|
| `rss_get_items` | `feed_id` | `url` or `title` |
| `rss_update_feed` | `feed_id` | `url` |
| `rss_remove_feed` | `feed_id` | `url` |
| `rss_fetch_feed` | `feed_id` | `url` |

#### 2. ストレージ層 (src/rss/storage/json_storage.py)

現在の構造:
```
data/raw/rss/
├── feeds.json
├── {feed_id_1}/
│   └── items.json
├── {feed_id_2}/
│   └── items.json
└── ...
```

#### 3. エージェント群

| エージェント | feed_id 使用箇所 |
|--------------|-----------------|
| finance-news-orchestrator | テーマ別フィードマッピング |
| finance-news-index | MCP ツール呼び出し |
| finance-news-stock | MCP ツール呼び出し |
| finance-news-sector | MCP ツール呼び出し |
| finance-news-macro | MCP ツール呼び出し |
| finance-news-finance | MCP ツール呼び出し |
| finance-news-ai | MCP ツール呼び出し |

## 実装方針

### 識別子の選択

**採用**: URL をプライマリキーとして使用

理由:
- URL は一意性が保証される（RSSフィードのソース）
- 変更頻度は低い
- 可読性は title より劣るが、プログラム的には安定

**補助**: title を人間向け表示に使用

### マイグレーション戦略

**段階的移行**（後方互換性を維持しながら移行）

```
Phase 1: 準備
  ↓
Phase 2: MCP サーバー改修（両方サポート）
  ↓
Phase 3: ストレージ改修
  ↓
Phase 4: エージェント改修
  ↓
Phase 5: テスト更新
  ↓
Phase 6: feed_id 完全削除
```

## 実装計画

### Phase 1: 準備（1日）

#### 1.1 型定義の更新設計

```python
# src/rss/types.py

# 変更前
class Feed(TypedDict):
    feed_id: str  # UUID v4
    url: str
    title: str
    ...

# 変更後
class Feed(TypedDict):
    url: str      # プライマリキー
    title: str
    ...
    # feed_id は削除
```

#### 1.2 ディレクトリ構造設計

```
# 変更前: UUID ベース
data/raw/rss/{feed_id}/items.json

# 変更後: URL ハッシュベース
data/raw/rss/{url_hash}/items.json

# url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
```

#### 1.3 設定ファイルマッピング作成

```python
# data/config/feed-url-mapping.json（移行用）
{
  "b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c14": "https://search.cnbc.com/...",
  ...
}
```

### Phase 2: MCP サーバー改修（2日）

#### 2.1 URL ベース API の追加

```python
# src/rss/mcp/server.py

@server.tool()
async def rss_get_items(
    url: str | None = None,        # 新規追加
    feed_id: str | None = None,    # 非推奨（互換性維持）
    title: str | None = None,      # 新規追加（補助）
    limit: int = 50
) -> dict:
    """RSS フィードのアイテムを取得

    Parameters
    ----------
    url : str, optional
        フィード URL（推奨）
    feed_id : str, optional
        フィード ID（非推奨、後方互換性のため）
    title : str, optional
        フィードタイトル（部分一致検索）
    """
    if url:
        feed = find_feed_by_url(url)
    elif feed_id:
        # 非推奨警告をログに出力
        logger.warning(f"feed_id is deprecated, use url instead: {feed_id}")
        feed = find_feed_by_id(feed_id)
    elif title:
        feed = find_feed_by_title(title)
    ...
```

#### 2.2 変更対象ツール

| ツール | 変更内容 |
|--------|----------|
| `rss_list_feeds` | 変更なし（全件取得） |
| `rss_get_items` | url/title パラメータ追加 |
| `rss_search_items` | 変更なし（キーワード検索） |
| `rss_add_feed` | 戻り値から feed_id 削除 |
| `rss_update_feed` | url で識別に変更 |
| `rss_remove_feed` | url で識別に変更 |
| `rss_fetch_feed` | url で識別に変更 |

### Phase 3: ストレージ層改修（2日）

#### 3.1 ディレクトリ構造の移行

```python
# src/rss/storage/json_storage.py

def _get_feed_dir(self, url: str) -> Path:
    """URL からフィードディレクトリを取得"""
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return self.data_dir / url_hash

def migrate_storage(self):
    """feed_id ベースから URL ベースへ移行"""
    feeds = self.load_feeds()
    for feed in feeds:
        old_dir = self.data_dir / feed.get("feed_id", "")
        new_dir = self._get_feed_dir(feed["url"])
        if old_dir.exists() and not new_dir.exists():
            shutil.move(old_dir, new_dir)
```

#### 3.2 feeds.json 構造変更

```json
// 変更前
{
  "feeds": [
    {
      "feed_id": "b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c14",
      "url": "https://...",
      "title": "CNBC - Health Care"
    }
  ]
}

// 変更後
{
  "feeds": [
    {
      "url": "https://...",
      "title": "CNBC - Health Care"
    }
  ]
}
```

### Phase 4: エージェント・スキル改修（2日）

#### 4.1 オーケストレーター改修

```python
# .claude/agents/finance-news-orchestrator.md

# 変更前
FEED_ASSIGNMENTS = {
    "sector": [
        {"feed_id": "b1a2c3d4-...", "title": "CNBC - Health Care"},
    ]
}

# 変更後
FEED_ASSIGNMENTS = {
    "sector": [
        {"url": "https://search.cnbc.com/...", "title": "CNBC - Health Care"},
    ]
}
```

#### 4.2 テーマエージェント改修（6ファイル）

```python
# 変更前
result = mcp__rss__fetch_feed(feed_id=feed["feed_id"])
result = mcp__rss__get_items(feed_id=feed["feed_id"])

# 変更後
result = mcp__rss__fetch_feed(url=feed["url"])
result = mcp__rss__get_items(url=feed["url"])
```

#### 4.3 変更対象エージェント一覧

| エージェント | 主な変更 |
|--------------|----------|
| finance-news-orchestrator.md | FEED_ASSIGNMENTS 構造変更 |
| finance-news-index.md | MCP 呼び出しパラメータ変更 |
| finance-news-stock.md | MCP 呼び出しパラメータ変更 |
| finance-news-sector.md | MCP 呼び出しパラメータ変更 |
| finance-news-macro.md | MCP 呼び出しパラメータ変更 |
| finance-news-finance.md | MCP 呼び出しパラメータ変更 |
| finance-news-ai.md | MCP 呼び出しパラメータ変更 |

### Phase 5: テスト更新（1日）

#### 5.1 テスト修正対象

| テストファイル | 変更内容 |
|----------------|----------|
| test_feed_manager.py | feed_id → url |
| test_feed_reader.py | feed_id → url |
| test_feed_fetcher.py | feed_id → url |
| test_json_storage.py | ディレクトリ構造変更 |
| test_mcp_server.py | API パラメータ変更 |

#### 5.2 マイグレーションテスト追加

```python
def test_storage_migration():
    """feed_id ベースから URL ベースへの移行テスト"""
    ...
```

### Phase 6: クリーンアップ（1日）

#### 6.1 後方互換性コード削除

- MCP ツールから `feed_id` パラメータを完全削除
- 型定義から `feed_id` フィールドを削除
- マイグレーションコードを削除

#### 6.2 ドキュメント更新

- CLAUDE.md 更新
- README.md 更新
- エージェント/スキルのドキュメント更新

## スケジュール

| Phase | 内容 | 期間 | 担当 |
|-------|------|------|------|
| 1 | 準備・設計 | 1日 | - |
| 2 | MCP サーバー改修 | 2日 | - |
| 3 | ストレージ層改修 | 2日 | - |
| 4 | エージェント改修 | 2日 | - |
| 5 | テスト更新 | 1日 | - |
| 6 | クリーンアップ | 1日 | - |

**合計**: 約 9 日間

## リスクと対策

### リスク1: データ損失

**対策**:
- 移行前にバックアップを作成
- 移行スクリプトにロールバック機能を実装

### リスク2: MCP ツール互換性

**対策**:
- Phase 2 で後方互換性を維持
- Phase 6 まで両方のパラメータをサポート

### リスク3: エージェント動作不良

**対策**:
- 各エージェントの単体テストを実施
- ステージング環境での動作確認

## 代替案

### 案A: 部分的移行（採用）

MCP API は URL ベースに移行するが、内部ストレージは URL ハッシュを使用

### 案B: title ベース移行

**却下理由**: title は一意性が保証されない（同名フィードの可能性）

### 案C: 現状維持

**却下理由**: 長期的なメンテナンスコストが高い

## チェックリスト

### Phase 1
- [ ] 型定義の更新設計完了
- [ ] ディレクトリ構造設計完了
- [ ] マイグレーションスクリプト設計完了

### Phase 2
- [ ] `rss_get_items` に url パラメータ追加
- [ ] `rss_update_feed` に url パラメータ追加
- [ ] `rss_remove_feed` に url パラメータ追加
- [ ] `rss_fetch_feed` に url パラメータ追加
- [ ] 非推奨警告の実装

### Phase 3
- [ ] `_get_feed_dir()` の実装
- [ ] `migrate_storage()` の実装
- [ ] feeds.json 構造変更
- [ ] データバックアップ作成
- [ ] マイグレーション実行

### Phase 4
- [ ] finance-news-orchestrator.md 更新
- [ ] finance-news-index.md 更新
- [ ] finance-news-stock.md 更新
- [ ] finance-news-sector.md 更新
- [ ] finance-news-macro.md 更新
- [ ] finance-news-finance.md 更新
- [ ] finance-news-ai.md 更新
- [ ] common-processing-guide.md 更新

### Phase 5
- [ ] ユニットテスト更新
- [ ] 統合テスト更新
- [ ] マイグレーションテスト追加
- [ ] 全テスト通過確認

### Phase 6
- [ ] feed_id パラメータ削除
- [ ] 後方互換性コード削除
- [ ] ドキュメント更新
- [ ] CLAUDE.md 更新

## 関連ファイル

### 主要ファイル
- `src/rss/types.py`
- `src/rss/mcp/server.py`
- `src/rss/storage/json_storage.py`
- `src/rss/services/feed_manager.py`
- `data/raw/rss/feeds.json`

### エージェント
- `.claude/agents/finance-news-orchestrator.md`
- `.claude/agents/finance-news-*.md` (6ファイル)

### スキル
- `.claude/skills/finance-news-workflow/common-processing-guide.md`

## 備考

- 本計画は段階的移行を前提としており、各 Phase 完了後に動作確認を行う
- 緊急時は Phase 2 の後方互換性機能を利用してロールバック可能
- 移行完了後は feed_id 関連コードを完全に削除し、コードベースを簡潔に保つ
