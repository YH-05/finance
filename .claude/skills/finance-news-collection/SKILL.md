---
name: finance-news-collection
description: 金融ニュース収集のワークフロー定義をスキルとして作成する。
allowed-tools: Task, MCPSearch, Bash, Read, Write
---

# 金融ニュース収集スキル

このスキルは、RSSフィードから金融ニュースを自動的に収集し、GitHub Projectに投稿するためのワークフローを定義します。

## 概要

金融市場や投資テーマに関連したニュースをRSSフィードから自動収集し、フィルタリング・重複チェックを経て、GitHub Projectに自動投稿します。

## 主要コンポーネント

### 1. エージェント: finance-news-collector

RSSフィードからニュースを収集し、GitHub Projectに投稿する自動化エージェント。

- **ファイル**: `.claude/agents/finance-news-collector.md`
- **役割**: RSS収集 → フィルタリング → 重複チェック → GitHub投稿
- **入力**: RSS MCP tools, `data/config/finance-news-filter.json`
- **出力**: GitHub Project issues

### 2. コマンド: /collect-finance-news

金融ニュース収集を実行するCLIコマンド。

- **ファイル**: `.claude/commands/collect-finance-news.md`
- **役割**: エージェントを起動し、収集パラメータを指定
- **引数**: `--project N`, `--limit N`, `--keywords "..."`, `--feed-id ID`, `--dry-run`

### 3. 設定ファイル: finance-news-filter.json

フィルタリング基準を定義する設定ファイル。

- **ファイル**: `data/config/finance-news-filter.json`
- **内容**: キーワード、情報源、フィルタリング閾値

## 使用方法

### 基本的な使用例

```bash
# 標準の金融ニュース収集
/collect-finance-news

# dry-runモード（GitHub投稿せず結果確認のみ）
/collect-finance-news --dry-run

# 取得数を制限
/collect-finance-news --limit 10

# 特定キーワードで絞り込み
/collect-finance-news --keywords "日銀,金利,為替"

# 特定のフィードのみ対象
/collect-finance-news --feed-id "feed_nikkei_keizai"

# 別のGitHub Projectに投稿
/collect-finance-news --project 15
```

## ワークフロー

### Phase 1: 初期化

```
[1] フィルター設定ファイル確認
    ↓
    data/config/finance-news-filter.json を読み込む
    ↓ 存在しない場合
    エラーメッセージ表示 → 処理中断

[2] RSS MCP ツール確認
    ↓
    MCPSearch で rss ツールを検索・ロード
    ↓ 利用できない場合
    エラーメッセージ表示 → 処理中断

[3] GitHub CLI 確認
    ↓
    gh コマンドが利用可能か確認
    ↓ 利用できない場合
    エラーメッセージ表示 → 処理中断
```

### Phase 2: ニュース収集

```
[4] finance-news-collector エージェント起動
    ↓
    Task tool でエージェントを起動
    ↓
    パラメータ:
    - project_number: GitHub Project番号
    - limit: 取得記事数の上限
    - keywords: 追加フィルタリング用キーワード
    - feed_id: 特定フィードID（オプション）
    - dry_run: dry-runモード（true/false）

[5] RSS記事取得
    ↓
    RSS MCP ツール (mcp__rss__list_feeds, mcp__rss__get_items) を使用
    ↓
    金融カテゴリのフィードから記事を取得

[6] フィルタリング処理
    ↓
    キーワードマッチング（金融関連キーワード）
    ↓
    除外判定（非金融キーワード）
    ↓
    信頼性スコアリング（情報源のTier評価）

[7] 重複チェック
    ↓
    既存GitHub Issueとの比較
    ↓
    URLの完全一致チェック
    ↓
    タイトルの類似度チェック

[8] GitHub Project投稿
    ↓
    gh issue create コマンドで Issue を作成
    ↓
    Project に自動追加
```

### Phase 3: 結果報告

```
[9] 収集結果のサマリー表示
    ↓
    - 取得記事数
    - 金融キーワードマッチ数
    - 除外数
    - 重複数
    - 新規投稿数
    ↓
    投稿されたニュースの抜粋リスト表示
```

## フィルタリングロジック

### キーワードマッチング

金融関連キーワードを含む記事を検出:

```python
# 金融キーワードカテゴリ
include_keywords = {
    "monetary_policy": ["日銀", "FRB", "ECB", "金利", "政策金利"],
    "market": ["株価", "為替", "円安", "円高", "ドル円"],
    "economic_indicators": ["GDP", "CPI", "失業率", "景気"],
    "finance": ["投資", "ファンド", "債券", "株式"]
}

# 最低マッチ数: 1つ以上のキーワードにマッチする必要がある
```

### 除外判定

金融関連性の低い記事を除外:

```python
# 除外キーワードカテゴリ
exclude_keywords = {
    "sports": ["野球", "サッカー", "オリンピック"],
    "entertainment": ["映画", "音楽", "芸能"],
    "general": ["天気", "レシピ", "旅行"]
}

# 除外ルール:
# - 除外キーワードを含む
# - かつ、金融キーワードを含まない場合に除外
```

### 信頼性スコアリング

情報源の信頼性を評価:

```python
# 情報源のTier分類
tier1 = ["nikkei.com", "bloomberg.co.jp", "reuters.com"]  # 信頼性: 高
tier2 = ["yahoo.co.jp/news", "kabutan.jp"]                # 信頼性: 中
tier3 = ["その他のソース"]                                 # 信頼性: 低

# スコア計算
score = tier × keyword_match_ratio × 100

# 例:
# - Tier 1 × 0.8 = 80点
# - Tier 2 × 0.6 = 60点
```

## 重複チェック

既存のGitHub Issueとの重複を検出:

### URL完全一致チェック

```python
# 既存Issueと同じURLの記事は投稿しない
if new_item.link in existing_issue_urls:
    skip_item()
```

### タイトル類似度チェック

```python
# タイトルの類似度を計算
similarity = calculate_title_similarity(new_title, existing_title)

# 閾値: 0.7（70%以上の類似度で重複と判定）
if similarity >= 0.7:
    skip_item()
```

## エラーハンドリング

### E001: フィルター設定ファイルエラー

**発生条件**:
- `data/config/finance-news-filter.json` が存在しない
- JSON形式が不正

**対処法**:
1. `docs/finance-news-filtering-criteria.md` を参照
2. サンプルファイルをコピー:
   ```bash
   cp data/config/finance-news-filter.json.sample data/config/finance-news-filter.json
   ```
3. 必要に応じて設定をカスタマイズ

### E002: RSS MCP ツールエラー

**発生条件**:
- RSS MCPサーバーが起動していない
- `.mcp.json` の設定が不正

**対処法**:
1. `.mcp.json` に RSS MCPサーバーの設定があるか確認
2. MCPサーバーが正しく起動しているか確認
3. Claude Code を再起動

### E003: GitHub CLI エラー

**発生条件**:
- `gh` コマンドがインストールされていない
- GitHub認証が切れている

**対処法**:
```bash
# インストール
brew install gh  # macOS

# 認証
gh auth login
```

### E004: ネットワークエラー

**発生条件**:
- RSS フィードへの接続失敗
- GitHub API への接続失敗

**対処法**:
- リトライロジック（最大3回、指数バックオフ）を実行
- 一時的なエラーの場合は時間をおいて再実行

### E005: GitHub API レート制限

**発生条件**:
- 1時間あたり5000リクエストを超過

**対処法**:
```bash
# 取得数を減らして実行
/collect-finance-news --limit 10

# または1時間待機してから再実行
```

## 設定カスタマイズ

### フィルター設定の編集

```bash
# フィルター設定ファイルを編集
vi data/config/finance-news-filter.json
```

編集可能な項目:
- `keywords.include`: 金融関連キーワード（カテゴリ別）
- `keywords.exclude`: 除外キーワード
- `sources.tier1/tier2/tier3`: 情報源のTier分類
- `filtering.min_keyword_matches`: 最低キーワードマッチ数
- `filtering.title_similarity_threshold`: タイトル類似度閾値

### RSS フィードの追加

RSS MCPツールを使用して新しいフィードを追加:

```python
# MCPツールでフィードを追加
mcp__rss__add_feed(
    url="https://example.com/finance/rss",
    title="新しい金融ニュースソース",
    category="finance",
    fetch_interval="daily",
    enabled=True
)
```

## ベストプラクティス

### 1. 定期的な実行

```bash
# 毎日1回実行を推奨
/collect-finance-news

# cron/schedulerで自動化も可能
```

### 2. dry-runでの確認

```bash
# 初めて実行する場合や設定変更後は dry-run で確認
/collect-finance-news --dry-run

# 問題なければ本番実行
/collect-finance-news
```

### 3. フィルター設定の調整

```bash
# 収集結果を確認しながら、フィルター設定を調整
# - キーワードが足りない場合: keywords.include に追加
# - ノイズが多い場合: keywords.exclude に追加
# - 信頼性スコアを調整: sources のTier分類を見直し
```

### 4. GitHub Project の整理

```bash
# 定期的に古いIssueをクローズ
gh issue list --project "Finance News Tracker" --state open

# 不要なIssueをクローズ
gh issue close 200
```

## サンプルコード

### Python APIの直接利用

エージェントやコマンドを使わず、Python APIを直接使用する場合:

```python
from pathlib import Path
from rss.services.feed_manager import FeedManager
from rss.services.feed_reader import FeedReader
from rss.types import FetchInterval

# データディレクトリ
data_dir = Path("data/raw/rss")

# フィード追加
manager = FeedManager(data_dir)
feed = manager.add_feed(
    url="https://example.com/finance/rss",
    title="日経新聞 - 経済",
    category="finance",
    fetch_interval=FetchInterval.DAILY,
    enabled=True
)

# 記事取得
reader = FeedReader(data_dir)
items = reader.get_items(feed_id=feed.feed_id, limit=10)

for item in items:
    print(f"- {item.title}")
    print(f"  公開日: {item.published}")
    print(f"  URL: {item.link}")
```

### キーワード検索

```python
# "日銀"に関する記事を検索
items = reader.search_items(
    query="日銀",
    category="finance",
    fields=["title", "summary", "content"],
    limit=50
)

print(f"検索結果: {len(items)}件")
for item in items:
    print(f"- {item.title}")
```

## 制約事項

1. **GitHub API レート制限**: 1時間あたり5000リクエスト（認証済み）
2. **RSS記事の取得制限**: 1回のリクエストで最大100件
3. **重複チェックの範囲**: 直近100件のIssueのみ
4. **実行頻度**: 1日1回を推奨（フィードの更新頻度に依存）

## 関連リソース

### ドキュメント

- **計画書**: `docs/project/financial-news-rss-collector.md`
- **フィルタリング基準**: `docs/finance-news-filtering-criteria.md`
- **RSS パッケージ調査**: `docs/project/rss-package-investigation.md`

### コンポーネント

- **エージェント**: `.claude/agents/finance-news-collector.md`
- **コマンド**: `.claude/commands/collect-finance-news.md`
- **RSS MCPサーバー**: `src/rss/mcp/server.py`
- **フィード管理**: `src/rss/services/feed_manager.py`
- **フィード取得**: `src/rss/services/feed_fetcher.py`
- **フィード読み込み**: `src/rss/services/feed_reader.py`

### GitHub

- **GitHub Project**: [Finance News Tracker #14](https://github.com/users/YH-05/projects/14)
- **関連Issue**: [#151](https://github.com/YH-05/finance/issues/151), [#152](https://github.com/YH-05/finance/issues/152)

## 今後の拡張

- [ ] 機械学習ベースのフィルタリング
- [ ] センチメント分析の追加
- [ ] トピッククラスタリング
- [ ] 自動タグ付け機能
- [ ] Slack/Discord通知機能
- [ ] RSS以外の情報源の追加（Twitter API、Webスクレイピング等）
