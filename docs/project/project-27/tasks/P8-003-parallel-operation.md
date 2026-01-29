# P8-003: 既存ワークフローとの並行運用確認

## 概要

新しい Python 版ワークフローと既存のエージェントベースワークフローの並行運用を確認する。

## フェーズ

Phase 8: ドキュメント・移行

## 依存タスク

- P8-002: CLAUDE.md 更新

## 成果物

- 並行運用確認レポート（Markdown）

## 確認内容

### 1. 重複チェック

両ワークフローが同じ記事を二重登録しないことを確認：

- [ ] 新ワークフローの重複チェックが既存 Issue を検出できる
- [ ] 既存ワークフローも新ワークフローが作成した Issue を検出できる
- [ ] Issue 本文の URL 形式が統一されている

### 2. Project 設定

両ワークフローが同じ GitHub Project を使用：

- [ ] Project ID が一致（PVT_kwHOBoK6AM4BMpw_）
- [ ] Status フィールド ID が一致
- [ ] PublishedDate フィールド ID が一致
- [ ] Status Option ID が一致

### 3. Issue フォーマット

Issue 本文のフォーマットが互換：

- [ ] タイトルプレフィックス（[Status]）が一致
- [ ] URL の記載形式が一致（**URL**: https://...）
- [ ] メタデータセクションが一致

### 4. 動作確認

実際に両ワークフローを実行：

```bash
# Python 版（ドライラン）
uv run python -m news.scripts.finance_news_workflow --dry-run --max-articles 10

# 既存版（テーマ1つのみ）
# /finance-news-workflow で index のみ実行
```

### 5. 移行計画

```
Phase 1: 並行運用
  - 新ワークフローをドライランで1週間運用
  - エラーログを監視

Phase 2: 段階的移行
  - 1つの Status（例: index）を新ワークフローに移行
  - 問題なければ他の Status も順次移行

Phase 3: 完全移行
  - 全 Status を新ワークフローに移行
  - 既存ワークフローを非推奨化（削除は手動指示後）
```

## 受け入れ条件

- [ ] 重複チェックが両方向で機能することを確認
- [ ] Project 設定の互換性を確認
- [ ] Issue フォーマットの互換性を確認
- [ ] ドライラン実行で問題がないことを確認
- [ ] 移行計画が文書化されている

## 参照

- project.md: 並行運用について セクション
- `data/config/news-collection-config.yaml`: GitHub 設定
