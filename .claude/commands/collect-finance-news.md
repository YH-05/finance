---
description: RSSフィードから金融ニュースを収集し、GitHub Projectに自動投稿します。
argument-hint: [--project N] [--limit N] [--keywords "..."] [--feed-id ID]
---

金融ニュース収集を実行します。

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| --project | - | 15 | GitHub Project番号（Finance News Collection） |
| --limit | - | 50 | 取得する記事数の最大値 |
| --keywords | - | - | 追加フィルタリング用キーワード（カンマ区切り） |
| --feed-id | - | - | 特定のフィードIDのみを対象とする |
| --dry-run | - | false | GitHub投稿せずに収集結果のみ表示 |

## 処理フロー

```
Phase 1: 初期化
├── フィルター設定ファイル確認
├── RSS MCP ツール確認
└── GitHub CLI 確認

Phase 2: ニュース収集
├── finance-news-collector エージェント起動
├── RSS記事取得
├── フィルタリング処理
├── 重複チェック
└── GitHub Project投稿

Phase 3: 結果報告
└── 投稿ニュースのサマリー表示
```

## 実行手順

### Phase 1: 初期化

1. **フィルター設定ファイル確認**
   ```bash
   # data/config/finance-news-filter.json の存在確認
   if [ ! -f "data/config/finance-news-filter.json" ]; then
       echo "エラー: フィルター設定ファイルが見つかりません"
       echo "作成方法: docs/finance-news-filtering-criteria.md を参照"
       exit 1
   fi
   ```

2. **RSS MCP ツール確認**
   ```
   MCPSearch: select:mcp__rss__list_feeds

   ツールが利用できない場合:
   - エラーメッセージ表示
   - .mcp.json の設定確認を促す
   - 処理を中断
   ```

3. **GitHub CLI 確認**
   ```bash
   # gh コマンドの確認
   if ! command -v gh &> /dev/null; then
       echo "エラー: GitHub CLI (gh) がインストールされていません"
       echo "インストール方法: https://cli.github.com/"
       exit 1
   fi

   # 認証確認
   if ! gh auth status &> /dev/null; then
       echo "エラー: GitHub認証が必要です"
       echo "認証方法: gh auth login"
       exit 1
   fi
   ```

### Phase 2: ニュース収集

4. **finance-news-collector エージェント起動**
   ```
   Task: finance-news-collector
   Parameters:
     - project_number: {project}
     - limit: {limit}
     - keywords: {keywords}
     - feed_id: {feed_id}
     - dry_run: {dry_run}

   Processing:
   1. RSS MCPツールで金融フィードを取得
   2. フィルター設定に基づいて記事をフィルタリング
   3. 既存GitHub Issueとの重複チェック
   4. 信頼性スコアリング
   5. GitHub Projectに投稿（dry-runでない場合）
   ```

5. **エージェント実行ログ監視**
   ```
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
   ```

### Phase 3: 結果報告

6. **収集結果のサマリー表示**

   ```markdown
   ## 金融ニュース収集完了

   ### 実行パラメータ
   - **GitHub Project**: #15 (Finance News Collection)
   - **取得上限**: 50件
   - **追加キーワード**: {keywords}

   ### 収集結果
   - **取得記事数**: 50件
   - **金融キーワードマッチ**: 35件
   - **除外**: 5件
   - **重複**: 10件
   - **新規投稿**: 20件

   ### 投稿されたニュース（抜粋）

   1. **日銀、政策金利を引き上げ** [#200]
      - ソース: 日経新聞
      - 信頼性: 95/100
      - URL: https://github.com/YH-05/finance/issues/200

   2. **米ドル円、150円台に上昇** [#201]
      - ソース: Bloomberg
      - 信頼性: 92/100
      - URL: https://github.com/YH-05/finance/issues/201

   3. **S&P500、史上最高値を更新** [#202]
      - ソース: ロイター
      - 信頼性: 90/100
      - URL: https://github.com/YH-05/finance/issues/202

   ### 次のアクション

   - GitHub Projectで詳細を確認: https://github.com/users/YH-05/projects/15
   - 再度収集を実行: /collect-finance-news
   ```

## dry-run モード

GitHub投稿せずに収集結果のみを確認できます。

```bash
/collect-finance-news --dry-run
```

出力例:
```markdown
## 金融ニュース収集（dry-run）

### フィルタリング結果

✅ **投稿候補: 20件**

1. 日銀、政策金利を引き上げ
   - ソース: 日経新聞
   - 信頼性: 95/100
   - キーワード: 日銀, 政策金利, 金利
   - URL: https://www.nikkei.com/article/...

2. 米ドル円、150円台に上昇
   - ソース: Bloomberg
   - 信頼性: 92/100
   - キーワード: 為替, 円安, ドル
   - URL: https://www.bloomberg.co.jp/...

...

❌ **除外: 5件**

- スポーツニュース（金融関連性なし）
- エンタメニュース（金融関連性なし）
...

🔄 **重複: 10件**

- Issue #190: 既に投稿済み
...

### 実際に投稿する場合

/collect-finance-news
```

## エラーハンドリング

### E001: フィルター設定ファイルエラー

**発生条件**:
- `data/config/finance-news-filter.json` が存在しない
- JSON形式が不正

**対処法**:
```
エラー: フィルター設定ファイルが見つかりません

期待されるパス: data/config/finance-news-filter.json

対処法:
1. docs/finance-news-filtering-criteria.md を参照
2. サンプルファイルをコピー:
   cp data/config/finance-news-filter.json.sample data/config/finance-news-filter.json
3. 必要に応じて設定をカスタマイズ
```

### E002: RSS MCP ツールエラー

**発生条件**:
- RSS MCPサーバーが起動していない
- .mcp.json の設定が不正

**対処法**:
```
エラー: RSS MCPツールが利用できません

確認項目:
1. .mcp.json に RSS MCPサーバーの設定があるか確認
2. MCPサーバーが正しく起動しているか確認
3. Claude Code を再起動

詳細: docs/project/financial-news-rss-collector.md を参照
```

### E003: GitHub CLI エラー

**発生条件**:
- `gh` コマンドがインストールされていない
- GitHub認証が切れている

**対処法**:
```
エラー: GitHub CLI (gh) がインストールされていません

インストール方法:
- macOS: brew install gh
- Linux: https://cli.github.com/
- Windows: https://cli.github.com/

認証方法:
gh auth login
```

### E004: ネットワークエラー

**発生条件**:
- RSS フィードへの接続失敗
- GitHub API への接続失敗

**対処法**:
- エラーログを確認
- リトライ（最大3回、指数バックオフ）
- 一時的なエラーの場合は時間をおいて再実行

### E005: GitHub API レート制限

**発生条件**:
- 1時間あたり5000リクエストを超過

**対処法**:
```
エラー: GitHub API レート制限に達しました

対処法:
- 1時間待機してから再実行
- または --limit オプションで取得数を減らす:
  /collect-finance-news --limit 10
```

## 高度な使用例

### 例1: 特定のキーワードでフィルタリング

```bash
/collect-finance-news --keywords "日銀,金利,為替"
```

金融キーワードに加えて、指定したキーワードでさらに絞り込みます。

### 例2: 特定のフィードのみ収集

```bash
/collect-finance-news --feed-id "feed_nikkei_keizai"
```

日経新聞の経済カテゴリのみから記事を収集します。

### 例3: 少量のニュースを収集

```bash
/collect-finance-news --limit 10
```

テスト用に10件のみ収集します。

### 例4: 別のGitHub Projectに投稿

```bash
/collect-finance-news --project 14
```

Finance News Collection以外のプロジェクトに投稿します（通常は不要）。

## 設定カスタマイズ

### フィルター設定の編集

```bash
# フィルター設定ファイルを編集
vi data/config/finance-news-filter.json
```

編集可能な項目:
- **keywords.include**: 金融関連キーワード（カテゴリ別）
- **keywords.exclude**: 除外キーワード
- **sources.tier1/tier2/tier3**: 情報源のTier分類
- **filtering.min_keyword_matches**: 最低キーワードマッチ数
- **filtering.title_similarity_threshold**: タイトル類似度閾値

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

## 制約事項

1. **GitHub API レート制限**: 1時間あたり5000リクエスト（認証済み）
2. **RSS記事の取得制限**: 1回のリクエストで最大100件
3. **重複チェックの範囲**: 直近100件のIssueのみ
4. **実行頻度**: 1日1回を推奨（フィードの更新頻度に依存）

## 関連リソース

- **スキル**: `.claude/skills/finance-news-collection/`
- **エージェント**: `.claude/agents/finance-news-collector.md`
- **計画書**: `docs/project/financial-news-rss-collector.md`
- **フィルタリング基準**: `docs/finance-news-filtering-criteria.md`
- **GitHub Project**: https://github.com/users/YH-05/projects/15

## 関連コマンド

- **フィード管理**: RSS MCPツールで直接管理
- **Issue確認**: `gh issue list --label "news"`
- **設定確認**: `cat data/config/finance-news-filter.json`
