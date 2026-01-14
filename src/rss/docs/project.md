# rss プロジェクト

## 概要

外部RSSフィードを収集・集約し、構造化データとして管理するPythonライブラリ。
金融メディア、経済データソース、個人ブログなど、様々なRSSフィードから情報を取得し、
JSON形式で保存・エクスポートする。

**主な用途:**
- 金融メディア（Bloomberg、Reuters、日経等）のニュースフィード収集
- 経済データソース（FRED、中央銀行等）の統計情報フィード取得
- 個人ブログや専門メディアからの情報収集
- 収集データのAIエージェント向け構造化API提供
- MCPサーバーとしてClaude Codeへの機能提供

## 主要機能

### フィード管理
- [ ] RSSフィードの登録・削除・一覧管理
- [ ] フィードメタデータ（URL、タイトル、カテゴリ、更新頻度等）の管理
- [ ] フィード取得スケジュール設定

### データ取得・パース
- [ ] RSS 2.0 / Atom フォーマット対応
- [ ] HTTP/HTTPS経由でのフィード取得
- [ ] エラーハンドリング（タイムアウト、404、パースエラー等）
- [ ] 差分取得（既存アイテムとの重複排除）

### データ保存・管理
- [ ] JSON形式でのローカル保存（data/raw/rss/）
- [ ] フィードアイテムの構造化データ管理（タイトル、URL、公開日時、内容等）
- [ ] メタデータ管理（取得日時、フィード情報等）

### 実行モード
- [ ] 手動実行API（Python関数呼び出し）
- [ ] 日次バッチ実行対応（スケジューラー連携）
- [ ] CLIインターフェース

### MCPサーバー機能
- [ ] Claude Code向けMCPサーバー実装
- [ ] フィード情報取得API（一覧、詳細）
- [ ] アイテム検索・フィルタリングAPI

## 技術的考慮事項

### 技術スタック
- **HTTPクライアント**: httpx（非同期対応）
- **RSSパーサー**: feedparser
- **データ形式**: JSON（標準ライブラリ）
- **MCPプロトコル**: mcp（Anthropic MCP SDK）
- **スケジューリング**: schedule または APScheduler（オプション）

### 制約・依存関係
- Python 3.12+
- ネットワークアクセスが必要
- 各RSSフィードのレート制限に注意
- feedparser によるパース結果の検証が必要

### データ構造設計
```python
# フィード情報
{
  "feed_id": "unique_id",
  "url": "https://example.com/feed.xml",
  "title": "Example Feed",
  "category": "finance",
  "last_fetched": "2026-01-14T10:00:00Z",
  "fetch_interval": "daily"
}

# フィードアイテム
{
  "item_id": "unique_id",
  "feed_id": "feed_unique_id",
  "title": "Article Title",
  "link": "https://example.com/article",
  "published": "2026-01-14T09:00:00Z",
  "summary": "Article summary...",
  "content": "Full content...",
  "author": "Author Name",
  "fetched_at": "2026-01-14T10:00:00Z"
}
```

## 成功基準

1. **機能完成度**
   - RSS 2.0 / Atom フィードを正常にパースできる
   - 10以上の主要金融メディアのフィードを取得できる
   - 構造化されたJSONデータが保存される
   - MCPサーバーとしてClaude Codeから利用できる

2. **品質基準**
   - テストカバレッジ 80% 以上
   - 型チェック（pyright）エラーなし
   - ドキュメント完備

3. **運用性**
   - 手動実行と日次バッチ実行の両方に対応
   - エラー時の適切なログ出力とリトライ機構
   - AIエージェントから利用可能なAPI提供

4. **柔軟性**
   - Pythonベースで拡張性の高い設計
   - MCPサーバーとしての機能提供
   - 他システムとの連携が容易

---

## 実装タスク

### フェーズ 1: 基盤実装（MVI: Minimum Viable Implementation）

#### 機能 1.1: 型定義（types.py）
- Issue: [#53](https://github.com/YH-05/finance/issues/53)
- 優先度: P0
- ステータス: todo
- 依存関係: なし
- 説明: RSS/Atomフィード管理に必要な型定義を実装
- 受け入れ条件:
  - [ ] `FetchInterval` Enumが3つの値を持つ（DAILY, WEEKLY, MANUAL）
  - [ ] `FetchStatus` Enumが3つの値を持つ（SUCCESS, FAILURE, PENDING）
  - [ ] `Feed` dataclassが全フィールドを持つ
  - [ ] `FeedItem` dataclassが全フィールドを持つ
  - [ ] `FeedsData` dataclassが version と feeds フィールドを持つ
  - [ ] `FeedItemsData` dataclassが version, feed_id, items フィールドを持つ
  - [ ] `HTTPResponse` dataclassが status_code, content, headers フィールドを持つ
  - [ ] `FetchResult` dataclassが feed_id, success, items_count, new_items, error_message フィールドを持つ
  - [ ] 全型がPython 3.12+の型ヒント（PEP 695）を使用
  - [ ] pyrightで型チェックエラー0件

---

> このファイルは `/new-project @src/rss/docs/project.md` で詳細化されました
