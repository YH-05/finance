# finance-news-collection スキル

RSSフィードから金融ニュースを自動収集し、GitHub Projectに投稿するワークフロースキルです。

## 概要

金融市場や投資テーマに関連したニュースをRSSフィードから自動収集し、フィルタリング・重複チェックを経て、GitHub Projectに自動投稿します。

## 主要コンポーネント

### エージェント: finance-news-collector

- **場所**: `.claude/agents/finance-news-collector.md`
- **役割**: RSS収集 → フィルタリング → 重複チェック → GitHub投稿

### コマンド: /collect-finance-news

- **場所**: `.claude/commands/collect-finance-news.md`
- **役割**: 金融ニュース収集の実行
- **引数**: `--project N`, `--limit N`, `--keywords "..."`, `--feed-id ID`, `--dry-run`

### 設定ファイル

- **フィルター設定**: `data/config/finance-news-filter.json`
- **内容**: キーワード、情報源、フィルタリング閾値

## 使用方法

### 基本的な実行

```bash
# 標準の金融ニュース収集
/collect-finance-news

# dry-runモード（GitHub投稿せず結果確認のみ）
/collect-finance-news --dry-run

# 取得数を制限
/collect-finance-news --limit 10
```

### 高度な使用例

```bash
# 特定キーワードで絞り込み
/collect-finance-news --keywords "日銀,金利,為替"

# 特定のフィードのみ対象
/collect-finance-news --feed-id "feed_nikkei_keizai"

# 別のGitHub Projectに投稿
/collect-finance-news --project 15
```

## ワークフロー

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
└── 収集結果のサマリー表示
```

## フィルタリング機能

### キーワードマッチング

金融関連キーワードを含む記事を検出:
- **金融政策**: 日銀, FRB, ECB, 金利, 政策金利
- **市場**: 株価, 為替, 円安, 円高, ドル円
- **経済指標**: GDP, CPI, 失業率, 景気
- **金融**: 投資, ファンド, 債券, 株式

### 除外判定

金融関連性の低い記事を除外:
- スポーツ、エンタメ、一般ニュース等

### 信頼性スコアリング

情報源の信頼性を評価:
- **Tier 1**: 日経新聞、Bloomberg、ロイター（信頼性: 高）
- **Tier 2**: Yahoo!ニュース、株探（信頼性: 中）
- **Tier 3**: その他のソース（信頼性: 低）

## 重複チェック

既存のGitHub Issueとの重複を検出:
- URL完全一致チェック
- タイトル類似度チェック（閾値: 70%）

## ベストプラクティス

1. **定期的な実行**: 毎日1回実行を推奨
2. **dry-runでの確認**: 初回や設定変更後は必ず確認
3. **フィルター調整**: 収集結果を見ながらキーワードを調整
4. **GitHub Projectの整理**: 定期的に古いIssueをクローズ

## エラーハンドリング

- **E001**: フィルター設定ファイルエラー
- **E002**: RSS MCP ツールエラー
- **E003**: GitHub CLI エラー
- **E004**: ネットワークエラー
- **E005**: GitHub API レート制限

詳細は `SKILL.md` を参照してください。

## 関連リソース

### ドキュメント

- **スキル詳細**: `SKILL.md`
- **計画書**: `docs/project/financial-news-rss-collector.md`
- **フィルタリング基準**: `docs/finance-news-filtering-criteria.md`

### コンポーネント

- **エージェント**: `.claude/agents/finance-news-collector.md`
- **コマンド**: `.claude/commands/collect-finance-news.md`
- **RSS MCPサーバー**: `src/rss/mcp/server.py`

### GitHub

- **GitHub Project**: [Finance News Tracker #14](https://github.com/users/YH-05/projects/14)
- **関連Issue**: [#151](https://github.com/YH-05/finance/issues/151), [#152](https://github.com/YH-05/finance/issues/152), [#153](https://github.com/YH-05/finance/issues/153)

## 制約事項

1. **GitHub API レート制限**: 1時間あたり5000リクエスト（認証済み）
2. **RSS記事の取得制限**: 1回のリクエストで最大100件
3. **重複チェックの範囲**: 直近100件のIssueのみ
4. **実行頻度**: 1日1回を推奨（フィードの更新頻度に依存）
