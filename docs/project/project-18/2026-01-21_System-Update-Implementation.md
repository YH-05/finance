# System Update: スキルベースシステムへのマイグレーション計画

## 概要

既存のコマンドベースシステムをスキルベースのシステムに移行し、エージェントへのスキルプリロード機構を実装する。これにより、より柔軟で保守性の高いシステムを実現する。

---

## フェーズ構成

| フェーズ | 内容 | ドキュメント |
|---------|------|-------------|
| **フェーズ 0** | 基盤整備（GitHub Project、スキル構造テンプレート、プリロード仕様） | [2026-01-21_Phase-0_Foundation.md](./2026-01-21_Phase-0_Foundation.md) |
| **フェーズ 1** | レポジトリ管理スキル（skill-expert, agent-expert, workflow-expert, index, project-management, task-decomposition, issue-management） | [2026-01-21_Phase-1_Repository-Management.md](./2026-01-21_Phase-1_Repository-Management.md) |
| **フェーズ 2** | コーディングスキル + Git操作スキル（coding-standards, tdd-development, error-handling, worktree-management, git-workflow） | [2026-01-21_Phase-2_Coding-Git-Skills.md](./2026-01-21_Phase-2_Coding-Git-Skills.md) |
| **フェーズ 3** | 金融分析スキル（finance-news-workflow, market-data, rss-integration, technical-analysis, financial-calculations, sec-edgar, web-research） | [2026-01-21_Phase-3_Finance-Skills.md](./2026-01-21_Phase-3_Finance-Skills.md) |
| **フェーズ 4** | 記事執筆スキル（後続フェーズ） | 未作成 |

---

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

## スキルプリロード実装方式

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
```

**重要な特性**:
- スキル名のリスト形式（配列）で指定
- 各スキルの**完全なコンテンツ**がサブエージェントのコンテキストに注入される
- サブエージェントは**親の会話からスキルを継承しない** - 明示的にリストする必要がある

---

## 全体依存関係

```
フェーズ0（基盤整備）
    │
    └── フェーズ1（レポジトリ管理）
            │
            └── フェーズ2（コーディング + Git操作）
                    │
                    └── フェーズ3（金融分析）
                            │
                            └── フェーズ4（記事執筆）
```

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

1. **GitHub Project「System Update」の作成**（フェーズ0）
2. **Issue #1-#19 を作成**（フェーズ1: スキル作成・統合）
3. **Wave 0 のスキル作成開始**（skill-expert, agent-expert, workflow-expert を並列・最優先）
4. **Wave 1 のスキル作成**（index, project-management, task-decomposition, issue-management を並列）

---

## 詳細ドキュメント

各フェーズの詳細（タスク分解、受け入れ条件、重要ファイル一覧など）は以下のドキュメントを参照：

- [フェーズ0: 基盤整備](./2026-01-21_Phase-0_Foundation.md)
- [フェーズ1: レポジトリ管理スキル](./2026-01-21_Phase-1_Repository-Management.md)
- [フェーズ2: コーディング+Git操作スキル](./2026-01-21_Phase-2_Coding-Git-Skills.md)
- [フェーズ3: 金融分析スキル](./2026-01-21_Phase-3_Finance-Skills.md)
