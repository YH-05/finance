# フェーズ 0: 基盤整備

> 元ドキュメント: `2026-01-21_System-Update-Implementation.md`

## 概要

既存のコマンドベースシステムをスキルベースのシステムに移行し、エージェントへのスキルプリロード機構を実装する。これにより、より柔軟で保守性の高いシステムを実現する。

## 決定事項

| 項目 | 決定内容 | 備考 |
|------|----------|------|
| 移行範囲 | ワークフロー/複雑ロジックを含むコマンドを優先 | |
| 後方互換性 | コマンドは廃止（スキル移行後、削除） | |
| スキル構造 | ナレッジベース（SKILL.md + guide.md + examples/）| Python スクリプト不要 |
| スキルプリロード | フロントマター方式（skills: でスキル指定、公式仕様準拠） | スキルコンテンツが自動注入 |
| エージェント移行 | 段階的移行（新規スキル作成時に関連エージェントを更新） | |
| 開始カテゴリ | レポジトリ管理 | |
| GitHub Project | 新規「System Update」を作成 | |
| 移行方式 | 即時置換（並存期間なし） | スキル完成後すぐに既存コマンド削除 |
| ツール活用 | 既存MCP/CLI/組み込みツール | Python スクリプト実装不要 |
| 実装順序 | 並列実装 | Wave単位で並列化 |

---

## 目標

- GitHub Project の作成
- スキルプリロード仕様の確定
- テンプレート整備

## タスク

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 0.1 | GitHub Project「System Update」の作成 | なし | Project URL |
| 0.2 | スキル標準構造テンプレートの作成 | なし | `template/skill/` |
| 0.3 | スキルプリロード仕様書の作成 | 0.2 | `docs/skill-preload-spec.md` |
| 0.4 | エージェントへのスキル参照パターンの確定 | 0.3 | 仕様書更新 |

---

## スキル標準構造

```
.claude/skills/{skill-name}/
├── SKILL.md           # エントリーポイント（必須）
├── guide.md           # 詳細ガイド（オプション）
├── template.md        # 出力テンプレート（オプション）
└── examples/          # 使用例・パターン集（オプション）
```

**設計方針**: スキルは「ナレッジ（知識・手順・テンプレート）」を提供し、実際の処理は既存ツール（MCP サーバー、gh CLI、組み込みツール）を活用する。

---

## スキルプリロード実装方式: フロントマター skills フィールド

サブエージェントのフロントマターに `skills:` フィールドを記述し、起動時にスキルコンテンツをコンテキストに注入する方式を採用（[公式ドキュメント](https://code.claude.com/docs/ja/sub-agents)準拠）。

```yaml
---
name: feature-implementer
description: TDDで機能を実装するサブエージェント
skills:
  - coding-standards
  - tdd-development
  - error-handling
allowed-tools: Read, Edit, Bash, Grep, Task
---

# 機能実装エージェント

プリロードされたスキルの規約とパターンに従って実装してください。
```

**重要な特性**:
- スキル名のリスト形式（配列）で指定
- 各スキルの**完全なコンテンツ**がサブエージェントのコンテキストに注入される
- サブエージェントは**親の会話からスキルを継承しない** - 明示的にリストする必要がある

**メリット**:
- Claude Code 公式仕様に準拠
- フロントマターで依存関係が明示される
- スキルコンテンツが自動的にコンテキストに読み込まれる

---

## 活用する既存ツール

スキルは以下の既存ツールを活用し、Python スクリプトの実装は行わない。

| カテゴリ | ツール | 用途 |
|---------|--------|------|
| ファイルシステム | `mcp__filesystem__directory_tree` | ディレクトリ構造取得（excludePatterns対応） |
| ファイルシステム | `mcp__filesystem__list_directory` | ディレクトリ一覧 |
| ファイルシステム | `mcp__filesystem__search_files` | ファイル検索（glob パターン） |
| Git | `mcp__git__*` | Git操作全般 |
| GitHub | Bash + `gh` CLI | Issue/PR/Project操作 |
| ファイル操作 | Read, Write, Edit, Glob, Grep | 組み込みツール |
| コード品質 | Bash + `ruff`, `pyright` | リント・型チェック |

---

## スキルフォルダ構成（全フェーズ）

```
.claude/skills/
├── skill-expert/              # 新規スキル（最優先）
├── agent-expert/              # 拡張（レビュー機能追加、最優先）
├── workflow-expert/           # 新規スキル（最優先）
├── index/                     # 新規スキル
├── project-management/        # 新規スキル
├── task-decomposition/        # 新規スキル（task-decomposerエージェントのみ統合）
└── issue-management/          # 新規スキル（issue系コマンドを統合）
```

---

## 完了基準

- [ ] GitHub Project「System Update」が作成されている
- [ ] スキル標準構造のテンプレートが存在する
- [ ] スキルプリロード仕様書が完成している

---

## リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| スキルプリロードでプロンプトが長くなりすぎる | guide.md は必要時のみ読み込み |
| 移行中の機能破壊 | 移行検証テストで同等性を確認 |
| gh CLI 認証エラー | 明確なエラーメッセージと `gh auth login` 案内 |
| MCP ツールの動作不安定 | Bash + gh CLI へのフォールバック手順を guide.md に記載 |

---

## 次のアクション

1. **GitHub Project「System Update」の作成**
2. スキル標準構造テンプレートの作成
3. スキルプリロード仕様書の作成

---

## 関連ドキュメント

- [フェーズ1: レポジトリ管理スキル](./2026-01-21_Phase-1_Repository-Management.md)
- [フェーズ2: コーディング+Git操作スキル](./2026-01-21_Phase-2_Coding-Git-Skills.md)
- [フェーズ3: 金融分析スキル](./2026-01-21_Phase-3_Finance-Skills.md)
