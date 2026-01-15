# 金融市場や投資テーマに関連したニュースをRSSフィードなどから収集し、github projectに自動投稿する

**作成日**: 2026-01-15
**ステータス**: 計画中
**GitHub Project**: [Finance News Tracker #14](https://github.com/users/YH-05/projects/14)

## 背景と目的

### 背景

- **背景の種類**: 新しいニーズが発生
- **詳細**: 手動プロセスの自動化が必要
- **具体的な状況**: 金融情報ソースが多く、複数のRSSフィードやニュースサイトを毎日手動で確認する必要があり、追跡が困難な状況。効率化のために自動収集とGitHub Projectへの自動登録が求められている。

### 目的

金融市場や投資テーマに関連したニュースをRSSフィードから自動的に収集し、GitHub Projectに自動投稿することで、情報収集の効率化と一元管理を実現する。

## スコープ

### 含むもの

- **変更範囲**: 新規ファイルのみ（既存コードは変更しない）
- **影響ディレクトリ**:
  - `.claude/` - エージェント、コマンド、スキルの追加
  - `docs/` - ドキュメントの追加

### 含まないもの

- パフォーマンス最適化（まずは動作することを優先）
- 既存パッケージ（src/rss/等）の変更

## 成果物

| 種類 | 名前 | 説明 |
| ---- | ---- | ---- |
| エージェント | finance-news-collector | RSSフィードからニュースを収集し、GitHub Projectに投稿するエージェント |
| コマンド | /collect-finance-news | ニュース収集コマンド |
| スキル | finance-news-collection | 金融ニュース収集スキル |
| ドキュメント | finance-news-collection-guide.md | 使用方法ガイド |
| GitHub Project | Finance News Tracker | ニュース管理用プロジェクト |

## 成功基準

- [x] 特定のRSSフィードから金融ニュースを収集できる
- [x] 収集したニュースがGitHub Projectに自動登録される
- [x] ドキュメントが整備され、使い方が明確になる

## 技術的考慮事項

### 実装アプローチ

既存の `src/rss/` パッケージを活用し、以下の流れで実装:

1. RSS MCPサーバーを使用してフィード情報を取得
2. 金融関連のフィルタリングロジックを適用
3. GitHub CLI (gh) を使用してProjectへ自動登録
4. エージェント・コマンド・スキルの形で提供

### 依存関係

- **src/rss/** - RSS フィード収集機能（既存パッケージ）
- **GitHub CLI (gh)** - GitHub Project/Issueの操作
- **MCP サーバー (RSS)** - RSSフィード管理

### テスト要件

- **ユニットテスト** - フィルタリングロジック、データ変換処理
- **統合テスト** - RSS収集 → GitHub投稿の一連フロー
- **プロパティテスト** - 入力データのバリデーション

## タスク一覧

インタビュー結果から導出したタスク:

### 準備

- [ ] 既存 src/rss/ パッケージの調査
  - Issue: [#147](https://github.com/YH-05/finance/issues/147)
  - ステータス: todo
- [ ] RSS MCPサーバーのAPI確認
  - Issue: [#148](https://github.com/YH-05/finance/issues/148)
  - ステータス: todo
- [ ] GitHub CLI の project 操作方法の確認
  - Issue: [#149](https://github.com/YH-05/finance/issues/149)
  - ステータス: todo
- [ ] 金融ニュースフィルタリング基準の定義
  - Issue: [#150](https://github.com/YH-05/finance/issues/150)
  - ステータス: todo

### 実装

- [ ] finance-news-collector エージェントの作成
  - Issue: [#151](https://github.com/YH-05/finance/issues/151)
  - ステータス: todo

- [ ] /collect-finance-news コマンドの作成
  - Issue: [#152](https://github.com/YH-05/finance/issues/152)
  - ステータス: todo

- [ ] finance-news-collection スキルの作成
  - Issue: [#153](https://github.com/YH-05/finance/issues/153)
  - ステータス: todo

### テスト・検証

- [ ] ユニットテスト作成（フィルタリングロジック・データ変換処理）
  - Issue: [#154](https://github.com/YH-05/finance/issues/154)
  - ステータス: todo

- [ ] 統合テスト作成（RSS収集→GitHub投稿のE2E）
  - Issue: [#155](https://github.com/YH-05/finance/issues/155)
  - ステータス: todo

- [ ] プロパティテスト作成（RSSフィードデータのバリデーション）
  - Issue: [#156](https://github.com/YH-05/finance/issues/156)
  - ステータス: todo

- [ ] 手動テスト実施（実際のRSSフィード・GitHub Projectで動作確認）
  - Issue: [#157](https://github.com/YH-05/finance/issues/157)
  - ステータス: todo

### ドキュメント

- [ ] ドキュメント作成（finance-news-collection-guide.md）
  - Issue: [#158](https://github.com/YH-05/finance/issues/158)
  - ステータス: todo

- [ ] エージェント・コマンド・スキルのREADME更新
  - Issue: [#159](https://github.com/YH-05/finance/issues/159)
  - ステータス: todo

---

**最終更新**: 2026-01-15
