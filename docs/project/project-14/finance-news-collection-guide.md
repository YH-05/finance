# 金融ニュース収集機能 - 使用方法ガイド

**作成日**: 2026-01-15
**バージョン**: 1.0

## 目次

1. [概要](#概要)
2. [セットアップ手順](#セットアップ手順)
3. [使用例](#使用例)
4. [トラブルシューティング](#トラブルシューティング)
5. [高度な使用方法](#高度な使用方法)

---

## 概要

金融ニュース収集機能は、RSSフィードから金融・投資関連のニュースを自動的に収集し、GitHub Projectに自動投稿する機能です。

### 主な機能

- **自動収集**: RSSフィードから最新の金融ニュースを取得
- **インテリジェントフィルタリング**: 金融関連キーワードに基づいた記事の自動抽出
- **重複排除**: 既存のニュースとの重複を自動検出
- **GitHub統合**: 収集したニュースを自動的にGitHub Projectに登録

### ワークフロー

```
RSSフィード取得
    ↓
金融キーワードでフィルタリング
    ↓
重複チェック
    ↓
GitHub Projectに自動投稿
```

---

## セットアップ手順

### 前提条件

以下のツールとサービスが必要です。

#### 1. RSS MCPサーバー

RSSフィードの管理と取得を行うMCPサーバーが必要です。

**確認方法**:
```bash
# .mcp.json にRSS MCPサーバーの設定があるか確認
cat .mcp.json | grep -A 5 "rss"
```

**設定例**（`.mcp.json`）:
```json
{
  "mcpServers": {
    "rss": {
      "command": "python",
      "args": ["-m", "rss.mcp.server"],
      "env": {
        "RSS_DATA_DIR": "data/raw/rss"
      }
    }
  }
}
```

#### 2. GitHub CLI

GitHub Projectへの投稿に使用します。

**確認方法**:
```bash
# GitHub CLI がインストールされているか確認
gh --version

# 認証状態を確認
gh auth status
```

**インストール方法**:
- **macOS**: `brew install gh`
- **Linux**: [公式サイト](https://cli.github.com/) からインストール
- **Windows**: [公式サイト](https://cli.github.com/) からインストール

**認証方法**:
```bash
gh auth login
```

#### 3. Python環境

- **Python**: 3.12以上
- **パッケージマネージャー**: uv

**確認方法**:
```bash
python --version  # 3.12以上
uv --version      # インストール済み
```

### インストール手順

#### ステップ1: 依存関係のインストール

```bash
# プロジェクトルートで実行
uv sync --all-extras
```

#### ステップ2: フィルター設定ファイルの作成

金融ニュースのフィルタリング基準を定義する設定ファイルを作成します。

**設定ファイルのパス**:
```
data/config/finance-news-filter.json
```

**設定ファイルの内容**:
```json
{
  "version": "1.0",
  "keywords": {
    "include": {
      "market": ["株価", "為替", "金利", "相場", "株式", "債券", "stock", "forex", "bond"],
      "policy": ["金融政策", "日銀", "FRB", "金利", "量的緩和", "GDP", "CPI", "monetary policy"],
      "corporate": ["決算", "業績", "M&A", "上場", "IPO", "earnings", "acquisition"],
      "investment": ["投資", "ファンド", "ETF", "REIT", "investment", "fund", "portfolio"]
    },
    "exclude": {
      "sports": ["サッカー", "野球", "バスケ", "テニス", "オリンピック"],
      "entertainment": ["映画", "音楽", "ドラマ", "アニメ", "芸能人"],
      "politics": ["選挙", "内閣改造"],
      "general": ["事故", "災害"]
    }
  },
  "sources": {
    "tier1": ["nikkei.com", "reuters.com", "bloomberg.com", "wsj.com"],
    "tier2": ["asahi.com", "yomiuri.co.jp", "toyokeizai.net", "diamond.jp", "forbes.com"],
    "tier3": []
  },
  "filtering": {
    "min_keyword_matches": 1,
    "title_similarity_threshold": 0.85,
    "time_window_hours": 1,
    "min_reliability_score": 2
  }
}
```

**設定ファイルの作成**:
```bash
# ディレクトリ作成
mkdir -p data/config

# 設定ファイル作成（エディタで編集）
vi data/config/finance-news-filter.json
```

#### ステップ3: RSSフィードの登録

金融ニュースソースのRSSフィードを登録します。

**MCPツールを使用した登録方法**:

```python
# Claude Codeで実行
mcp__rss__add_feed(
    url="https://www.nikkei.com/rss/...",
    title="日経新聞 - 経済",
    category="finance",
    fetch_interval="daily",
    enabled=True
)
```

**主要な金融ニュースソース例**:
- 日経新聞（経済、マーケット）
- ロイター（日本語版 - マーケット）
- Bloomberg（日本語版）
- 東洋経済オンライン

#### ステップ4: GitHub Projectの確認

ニュースを投稿するGitHub Projectが存在するか確認します。

**デフォルト設定**:
- **Project名**: Finance News Tracker
- **Project番号**: 14

**確認方法**:
```bash
# GitHub Projectの一覧を表示
gh project list --owner @me
```

---

## 使用例

### 基本的な使用方法

#### コマンド実行

```bash
/collect-finance-news
```

このコマンドを実行すると、以下の処理が自動的に実行されます。

1. RSSフィードから金融カテゴリの記事を取得（最大50件）
2. 金融キーワードでフィルタリング
3. 既存のGitHub Issueとの重複チェック
4. 信頼性スコアリング
5. GitHub Project #14 に自動投稿

**実行例**:
```
[INFO] フィルター設定ファイル読み込み: data/config/finance-news-filter.json
[INFO] RSS MCPツールをロード中...
[INFO] 金融フィード数: 7件
[INFO] 記事取得中... (limit=50)
[INFO] 記事取得数: 50件 / 150件
[INFO] フィルタリング中...
[INFO] 金融キーワードマッチ: 35件
[INFO] 除外判定: 5件除外
[INFO] 重複チェック: 10件重複
[INFO] 投稿対象: 20件
[INFO] GitHub Issue作成中...
[INFO] GitHub Issue作成成功: #200 - 日銀、政策金利を引き上げ
[INFO] GitHub Issue作成成功: #201 - 米ドル円、150円台に上昇
...
[INFO] 処理完了: 20件のニュースを投稿しました
```

### パラメータ設定例

#### 例1: 取得件数を制限

```bash
/collect-finance-news --limit 10
```

テスト用や少量のニュースを確認したい場合に使用します。

#### 例2: 追加のキーワードでフィルタリング

```bash
/collect-finance-news --keywords "日銀,金利,為替"
```

特定のトピックに絞ってニュースを収集します。

#### 例3: 特定のフィードのみ収集

```bash
/collect-finance-news --feed-id "feed_nikkei_keizai"
```

特定の情報源（例: 日経新聞の経済カテゴリ）のみから記事を収集します。

**フィードIDの確認方法**:
```python
# MCPツールでフィード一覧を取得
mcp__rss__list_feeds(category="finance", enabled_only=True)
```

#### 例4: dry-runモード（投稿せずに確認）

```bash
/collect-finance-news --dry-run
```

GitHub Projectに投稿せず、収集結果のみを表示します。フィルタリング精度を確認したい場合に便利です。

**dry-run出力例**:
```
## 金融ニュース収集（dry-run）

### フィルタリング結果

✅ 投稿候補: 20件

1. 日銀、政策金利を引き上げ
   - ソース: 日経新聞
   - キーワード: 日銀, 政策金利, 金利
   - URL: https://www.nikkei.com/article/...

2. 米ドル円、150円台に上昇
   - ソース: Bloomberg
   - キーワード: 為替, 円安, ドル
   - URL: https://www.bloomberg.co.jp/...

❌ 除外: 5件
🔄 重複: 10件
```

#### 例5: 別のGitHub Projectに投稿

```bash
/collect-finance-news --project 15
```

デフォルトの Finance News Tracker（Project #14）以外のプロジェクトに投稿します。

### フィルタリング設定のカスタマイズ

#### キーワードの追加

```bash
# フィルター設定ファイルを編集
vi data/config/finance-news-filter.json
```

**追加例**:
```json
{
  "keywords": {
    "include": {
      "market": ["株価", "為替", "金利", "仮想通貨", "ビットコイン"],  // 仮想通貨を追加
      ...
    }
  }
}
```

#### 除外キーワードの追加

特定のトピックを除外したい場合:

```json
{
  "keywords": {
    "exclude": {
      "sports": ["サッカー", "野球", "ゴルフ"],  // ゴルフを追加
      ...
    }
  }
}
```

#### 情報源の追加

```json
{
  "sources": {
    "tier1": ["nikkei.com", "reuters.com", "bloomberg.com", "ft.com"],  // Financial Timesを追加
    ...
  }
}
```

---

## トラブルシューティング

### よくあるエラーと対処法

#### E001: フィルター設定ファイルエラー

**エラーメッセージ**:
```
エラー: フィルター設定ファイルが見つかりません
期待されるパス: data/config/finance-news-filter.json
```

**原因**:
- 設定ファイルが存在しない
- JSONフォーマットが不正

**対処法**:
1. 設定ファイルが存在するか確認
   ```bash
   ls -la data/config/finance-news-filter.json
   ```

2. 存在しない場合は作成
   ```bash
   mkdir -p data/config
   vi data/config/finance-news-filter.json
   # 「セットアップ手順」のサンプルを参照して作成
   ```

3. JSONフォーマットを検証
   ```bash
   python -m json.tool data/config/finance-news-filter.json
   ```

#### E002: RSS MCPツールエラー

**エラーメッセージ**:
```
エラー: RSS MCPツールが利用できません
```

**原因**:
- RSS MCPサーバーが起動していない
- `.mcp.json` の設定が不正

**対処法**:
1. `.mcp.json` の設定を確認
   ```bash
   cat .mcp.json | grep -A 5 "rss"
   ```

2. Claude Codeを再起動

3. MCPサーバーの設定を確認
   ```bash
   # RSS MCPサーバーが正しく動作するか確認
   python -m rss.mcp.server
   ```

#### E003: GitHub CLIエラー

**エラーメッセージ**:
```
エラー: GitHub CLI (gh) がインストールされていません
```

**原因**:
- `gh` コマンドがインストールされていない
- GitHub認証が切れている

**対処法**:
1. GitHub CLIをインストール
   ```bash
   # macOS
   brew install gh

   # Linux/Windows
   # https://cli.github.com/ からインストール
   ```

2. 認証を実施
   ```bash
   gh auth login
   ```

3. 認証状態を確認
   ```bash
   gh auth status
   ```

#### E004: ネットワークエラー

**エラーメッセージ**:
```
エラー: RSS記事取得エラー: HTTPエラー (timeout)
```

**原因**:
- RSSフィードへの接続失敗
- ネットワーク問題

**対処法**:
1. ネットワーク接続を確認
   ```bash
   ping google.com
   ```

2. 時間をおいて再実行（自動リトライは最大3回）

3. 特定のフィードで失敗する場合、そのフィードを無効化
   ```python
   # MCPツールでフィードを無効化
   mcp__rss__update_feed(
       feed_id="problem_feed_id",
       enabled=False
   )
   ```

#### E005: GitHub API レート制限

**エラーメッセージ**:
```
エラー: GitHub API レート制限に達しました
```

**原因**:
- 1時間あたり5000リクエストを超過

**対処法**:
1. 1時間待機してから再実行

2. または取得件数を減らす
   ```bash
   /collect-finance-news --limit 10
   ```

3. レート制限状況を確認
   ```bash
   gh api rate_limit
   ```

### デバッグ方法

#### ログレベルの変更

詳細なログを出力する場合:

```bash
# 環境変数でログレベルを設定
export LOG_LEVEL=DEBUG

# コマンド実行
/collect-finance-news
```

#### dry-runモードでの確認

投稿前にフィルタリング結果を確認:

```bash
/collect-finance-news --dry-run
```

#### 段階的なデバッグ

1. **フィード一覧の確認**
   ```python
   mcp__rss__list_feeds(category="finance", enabled_only=True)
   ```

2. **記事取得のテスト**
   ```python
   mcp__rss__get_items(feed_id=None, limit=5)
   ```

3. **フィルター設定の検証**
   ```bash
   cat data/config/finance-news-filter.json | python -m json.tool
   ```

### ログの確認方法

#### ログファイルの場所

実行ログは標準出力に表示されます。保存する場合:

```bash
/collect-finance-news 2>&1 | tee finance-news-collection.log
```

#### ログの内容

```
[INFO] フィルター設定ファイル読み込み: ...
[INFO] RSS MCPツールをロード中...
[INFO] 金融フィード数: 7件
[INFO] 記事取得数: 50件 / 150件
[INFO] 金融キーワードマッチ: 35件
[DEBUG] マッチしたキーワード: ["株価", "為替", "金利"]
[INFO] 除外判定: 5件除外
[DEBUG] 除外理由: スポーツニュース
[INFO] 重複チェック: 10件重複
[INFO] GitHub Issue作成成功: #200 - ...
```

---

## 高度な使用方法

### 定期実行の設定

#### cronを使用した定期実行

毎日午前6時に自動実行する例:

**crontabの編集**:
```bash
crontab -e
```

**設定内容**:
```cron
# 毎日午前6時に金融ニュースを収集
0 6 * * * cd /path/to/finance && /collect-finance-news >> /var/log/finance-news.log 2>&1
```

#### GitHub Actionsを使用した定期実行

`.github/workflows/collect-finance-news.yml`:

```yaml
name: Collect Finance News

on:
  schedule:
    - cron: '0 6 * * *'  # 毎日午前6時（UTC）
  workflow_dispatch:      # 手動実行も可能

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --all-extras

      - name: Collect finance news
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          /collect-finance-news --limit 50
```

### カスタムフィルターの作成

#### 特定トピック専用のフィルター

例: 日銀関連ニュースのみを収集

**専用設定ファイル**: `data/config/boj-news-filter.json`

```json
{
  "version": "1.0",
  "keywords": {
    "include": {
      "boj": ["日銀", "日本銀行", "金融政策決定会合", "黒田", "植田", "BOJ", "Bank of Japan"]
    },
    "exclude": {}
  },
  "filtering": {
    "min_keyword_matches": 1
  }
}
```

**実行方法**（エージェントを直接編集）:
1. `.claude/agents/finance-news-collector.md` を編集
2. フィルター設定ファイルのパスを変更
3. コマンド実行

#### カテゴリ別フィルター

複数のフィルター設定を用意し、カテゴリごとに収集:

- `data/config/stock-news-filter.json` - 株式市場専用
- `data/config/forex-news-filter.json` - 為替市場専用
- `data/config/policy-news-filter.json` - 金融政策専用

### GitHub Projectのカスタマイズ

#### カスタムフィールドの追加

GitHub Projectにカスタムフィールドを追加して、より詳細な分類が可能:

1. **カテゴリ**: 単一選択（株式、為替、金融政策、企業、etc.）
2. **地域**: 単一選択（日本、米国、欧州、アジア）

#### 自動ラベリング

収集したニュースに自動的にラベルを付与:

```bash
# Issueにラベルを追加
gh issue edit {issue_number} --add-label "finance,news,auto-collected"
```

#### Projectビューのカスタマイズ

- **カテゴリ別ビュー**: 株式、為替、金融政策などでグルーピング
- **日付別ビュー**: 公開日時でソート

---

## 制約事項

### API制限

1. **GitHub API レート制限**:
   - 認証済み: 1時間あたり5000リクエスト
   - 対処法: `--limit` オプションで取得件数を調整

2. **RSS記事の取得制限**:
   - 1回のリクエストで最大100件
   - 対処法: オフセットを使用してページネーション

### パフォーマンス

1. **重複チェックの範囲**:
   - 直近100件のIssueのみを対象
   - 理由: GitHub API のパフォーマンスを考慮

2. **実行頻度の推奨**:
   - 1日1回を推奨
   - 理由: RSSフィードの更新頻度、APIレート制限

### その他

- **フィルタリング精度**: キーワードベースのため完璧ではない
  - 対処法: 定期的にキーワードリストを更新

- **言語**: 現在は日本語と英語のみサポート
  - 対処法: 必要に応じて他言語のキーワードを追加

---

## 関連リソース

### ドキュメント

- **プロジェクト計画書**: `docs/project/financial-news-rss-collector.md`
- **フィルタリング基準**: `docs/finance-news-filtering-criteria.md`
- **RSSパッケージドキュメント**: `src/rss/README.md`

### コード

- **エージェント定義**: `.claude/agents/finance-news-collector.md`
- **コマンド定義**: `.claude/commands/collect-finance-news.md`
- **RSS MCP実装**: `src/rss/mcp/server.py`

### 外部リンク

- **GitHub Project**: [Finance News Tracker #14](https://github.com/users/YH-05/projects/14)
- **GitHub CLI Documentation**: https://cli.github.com/manual/
- **RSS MCP Server**: プロジェクト内の `src/rss/` パッケージ

---

## FAQ

### Q1: ニュースが全く収集されない

**A**: 以下を確認してください。
1. フィルター設定ファイルが存在するか
2. RSSフィードが登録されているか（`mcp__rss__list_feeds`）
3. キーワードマッチ条件が厳しすぎないか（`min_keyword_matches` を減らす）

### Q2: 同じニュースが複数回投稿される

**A**: 重複チェックの精度を上げてください。
1. `title_similarity_threshold` を下げる（例: 0.75）
2. 重複チェックの範囲を広げる（エージェントのロジックを変更）

### Q3: 関係ないニュースが混ざる

**A**: フィルター設定を調整してください。
1. 除外キーワードを追加
2. `min_keyword_matches` を増やす（例: 2以上）

### Q4: dry-runと実際の結果が異なる

**A**: GitHub Issueとの重複チェックが dry-run では実行されないためです。
- dry-run: フィルタリングのみ確認
- 本番実行: フィルタリング + 重複チェック

### Q5: 定期実行を停止したい

**A**: cronやGitHub Actionsの設定を無効化してください。
```bash
# crontabの編集
crontab -e
# 該当行をコメントアウトまたは削除
```

---

**最終更新**: 2026-01-15
**バージョン**: 1.0
