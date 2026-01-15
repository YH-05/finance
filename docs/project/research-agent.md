# リサーチエージェントの追加

**作成日**: 2026-01-13
**ステータス**: 完了
**GitHub Project**: [#7](https://github.com/users/YH-05/projects/7)
**完了日**: 2026-01-15

## 背景と目的

### 背景

- 背景の種類: 新しいニーズが発生
- 詳細: 新機能の追加と既存機能の拡張
- 具体的な状況: note記事用に画像を収集するエージェントを追加したい。特定サイトからデータを収集する機能が必要。

### 目的

新しいエージェントを `.claude/agents/` に追加し、note記事作成のための画像収集・リサーチ機能を提供する。

## スコープ

### 含むもの

- 変更範囲: 新規ファイル作成 + 既存ファイルの修正
- 影響ディレクトリ:
  - `.claude/` - エージェント定義ファイル
  - `docs/` - ドキュメント

### 含まないもの

- パフォーマンス最適化（まずは動作することを優先）

## 成果物

| 種類 | 名前 | 説明 |
| ---- | ---- | ---- |
| エージェント | research-image-collector | note記事用の画像収集エージェント |
| ドキュメント | エージェント使用ガイド | 使い方と設定方法 |

## 成功基準

- [x] 特定の入力に対して期待する出力が得られる（画像URLリストなど）
- [x] ドキュメントが整備される（使い方が明確になる）

## 技術的考慮事項

### 実装アプローチ

既存パターンに従う - リポジトリ内の類似エージェント（finance-web, finance-wiki等）を参考に実装

### 依存関係

- 既存のエージェント/コマンド - 金融リサーチ系エージェントのパターンを参照
- 外部API - Web検索、画像取得等

### テスト要件

- ユニットテスト - 個別関数のテスト
- 統合テスト - エージェント全体の動作確認

## タスク一覧

GitHub Issues との対応:

### 準備

- [x] 既存リサーチ系エージェントの調査（finance-web, finance-wiki等）
  - Issue: [#47](https://github.com/YH-05/finance/issues/47)
  - ステータス: done
  - 成果物: [調査レポート](./research-agent-survey.md)
- [x] 画像収集の要件定義（対象サイト、フォーマット、保存先）
  - Issue: [#48](https://github.com/YH-05/finance/issues/48)
  - ステータス: done
  - 成果物: [要件定義書](./image-collection-requirements.md)

### 実装

- [x] 画像収集エージェントの定義ファイル作成
  - Issue: [#49](https://github.com/YH-05/finance/issues/49)
  - ステータス: done
  - 成果物: [エージェント定義](../../.claude/agents/research-image-collector.md)
- [x] agents.md への登録と /index 更新
  - Issue: [#50](https://github.com/YH-05/finance/issues/50)
  - ステータス: done

### ドキュメント

- [x] エージェント使用ガイドの作成
  - Issue: [#51](https://github.com/YH-05/finance/issues/51)
  - ステータス: done
  - 成果物: [使用ガイド](../image-collector-guide.md)

---

**最終更新**: 2026-01-15
**更新内容**: プロジェクトステータスを「完了」に更新、GitHub Project #7 の全Issue (#47-51) と同期
