# System Update: スキルベースシステム移行

## プロジェクト情報

| 項目 | 内容 |
|------|------|
| GitHub Project | [#18](https://github.com/users/YH-05/projects/18) |
| 計画書 | [docs/plan/2026-01-21_System-Update-Implementation.md](../../plan/2026-01-21_System-Update-Implementation.md) |
| 目的 | 既存のコマンドベースシステムをスキルベースのシステムに移行 |
| 最終更新 | 2026-01-22 |
| 進捗 | **25/34 Issue 完了** (フェーズ0-2完了、フェーズ3進行中) |

## フェーズ概要

| フェーズ | 内容 | ステータス |
|---------|------|----------|
| フェーズ 0 | 基盤整備（Project作成、テンプレート、仕様書） | ✅ Done |
| フェーズ 1 | レポジトリ管理スキル（7スキル作成） | ✅ Done |
| フェーズ 2 | コーディングスキル + Git操作スキル（3 + 9スキル作成） | ✅ Done |
| フェーズ 3 | 金融分析スキル（6スキル作成） | 🔄 In Progress |
| フェーズ 4 | 記事執筆スキル（後続） | ⏸️ Backlog |

---

## フェーズ 0: 基盤整備 ✅

### タスク

| # | タスク | 依存 | ステータス | Issue |
|---|--------|------|----------|-------|
| 0.1 | GitHub Project「System Update」の作成 | なし | ✅ Done | - |
| 0.2 | スキル標準構造テンプレートの作成 | なし | ✅ Done | [#598](https://github.com/YH-05/finance/issues/598) |
| 0.3 | スキルプリロード仕様書の作成 | 0.2 | ✅ Done | [#599](https://github.com/YH-05/finance/issues/599) |
| 0.4 | エージェントへのスキル参照パターンの確定 | 0.3 | ✅ Done | [#600](https://github.com/YH-05/finance/issues/600) |

---

## フェーズ 1: レポジトリ管理スキル ✅

### Wave 0: 基盤スキル（最優先・並列実装可）

#### skill-expert スキル（新規）

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 1 | skill-expert スキル SKILL.md の作成 | M | なし | ✅ Done | [#601](https://github.com/YH-05/finance/issues/601) |
| 2 | skill-expert スキル guide.md の作成 | M | #1 | ✅ Done | [#602](https://github.com/YH-05/finance/issues/602) |
| 3 | skill-expert スキル template.md の作成 | S | #1 | ✅ Done | [#603](https://github.com/YH-05/finance/issues/603) |

#### agent-expert スキル拡張

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 4 | agent-expert スキルにフロントマターレビュー機能を追加 | S | なし | ✅ Done | [#604](https://github.com/YH-05/finance/issues/604) |

#### workflow-expert スキル（新規）

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 5 | workflow-expert スキル SKILL.md の作成 | M | なし | ✅ Done | [#605](https://github.com/YH-05/finance/issues/605) |
| 6 | workflow-expert スキル guide.md の作成 | M | #5 | ✅ Done | [#606](https://github.com/YH-05/finance/issues/606) |

### Wave 1: レポジトリ管理スキル（並列実装可）

#### index スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 7 | index スキル SKILL.md の作成 | M | #3 | ✅ Done | [#607](https://github.com/YH-05/finance/issues/607) |
| 8 | index スキル guide.md の作成 | S | #7 | ✅ Done | [#608](https://github.com/YH-05/finance/issues/608) |
| 9 | 既存 /index コマンドを index スキルに置換 | S | #8 | ✅ Done | [#609](https://github.com/YH-05/finance/issues/609) |

#### プロジェクト管理スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 10 | プロジェクト管理スキル SKILL.md の作成 | M | #3 | ✅ Done | [#610](https://github.com/YH-05/finance/issues/610) |
| 11 | プロジェクト管理スキル guide.md の作成 | M | #10 | ✅ Done | [#611](https://github.com/YH-05/finance/issues/611) |
| 12 | 既存プロジェクト管理コマンド/スキルを置換 | M | #11 | ✅ Done | [#612](https://github.com/YH-05/finance/issues/612) |

#### タスク分解スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 13 | タスク分解スキル SKILL.md の作成 | M | #3 | ✅ Done | [#613](https://github.com/YH-05/finance/issues/613) |
| 14 | タスク分解スキル guide.md の作成 | M | #13 | ✅ Done | [#614](https://github.com/YH-05/finance/issues/614) |
| 15 | task-decomposer エージェントをスキルに統合 | M | #14 | ✅ Done | [#615](https://github.com/YH-05/finance/issues/615) |

#### Issue管理スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 16 | Issue管理スキル SKILL.md の作成 | M | #3 | ✅ Done | [#616](https://github.com/YH-05/finance/issues/616) |
| 17 | Issue管理スキル guide.md の作成 | M | #16 | ✅ Done | [#617](https://github.com/YH-05/finance/issues/617) |
| 18 | 既存 issue 系コマンドを Issue管理スキルに置換 | L | #17 | ✅ Done | [#618](https://github.com/YH-05/finance/issues/618) |

### Wave 2: 統合

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 19 | フェーズ1全スキルの統合テスト実施 | M | #4, #6, #9, #12, #15, #18 | ✅ Done | [#619](https://github.com/YH-05/finance/issues/619) |

---

## フェーズ 2: コーディングスキル + Git操作スキル ✅

### Wave 1: コーディングスキル ✅

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 2.1 | coding-standards スキルの作成 | L | フェーズ1完了 | ✅ Done | [#620](https://github.com/YH-05/finance/issues/620) |
| 2.2 | tdd-development スキルの作成 | L | フェーズ1完了 | ✅ Done | [#621](https://github.com/YH-05/finance/issues/621) |
| 2.3 | error-handling スキルの作成 | L | フェーズ1完了 | ✅ Done | [#622](https://github.com/YH-05/finance/issues/622) |

### Wave 2: Git操作スキル ✅

> **設計変更**: プランでは worktree-management / git-workflow の2つの統合スキルとして設計されていましたが、
> 各コマンドの独立性を考慮し、**個別スキル**として実装しました。

#### worktree 関連スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 2.4.1 | worktree スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.4.2 | worktree-done スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.4.3 | plan-worktrees スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.4.4 | create-worktrees スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.4.5 | delete-worktrees スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.4.6 | コマンドのスキル参照追加 | S | 2.4.1-2.4.5 | ✅ Done | - |

#### Git操作スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 2.5.1 | push スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.5.2 | commit-and-pr スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.5.3 | merge-pr スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.5.4 | gemini-search スキル SKILL.md の作成 | M | なし | ✅ Done | - |
| 2.5.5 | コマンドのスキル参照追加 | S | 2.5.1-2.5.4 | ✅ Done | - |

---

## フェーズ 3: 金融分析スキル 🔄

### Wave -1: finance-news-workflow スキル（優先実装）

#### finance-news-workflow スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 3.0.1 | finance-news-workflow SKILL.md の作成 | M | なし | ⬜ Todo | [#685](https://github.com/YH-05/finance/issues/685) |
| 3.0.2 | finance-news-workflow guide.md の作成 | M | #3.0.1 | ⬜ Todo | [#686](https://github.com/YH-05/finance/issues/686) |
| 3.0.3 | finance-news-workflow templates/ の作成 | S | #3.0.1 | ⬜ Todo | [#687](https://github.com/YH-05/finance/issues/687) |
| 3.0.4 | finance-news-workflow examples/ の作成 | S | #3.0.1 | ⬜ Todo | [#688](https://github.com/YH-05/finance/issues/688) |
| 3.0.5 | /collect-finance-news コマンドの更新 | S | #3.0.2 | ⬜ Todo | [#689](https://github.com/YH-05/finance/issues/689) |
| 3.0.6 | finance-news-orchestrator, collector エージェント更新 | S | #3.0.2 | ⬜ Todo | [#690](https://github.com/YH-05/finance/issues/690) |
| 3.0.7 | テーマ別エージェント群（6件）の更新 | M | #3.0.2 | ⬜ Todo | [#691](https://github.com/YH-05/finance/issues/691) |
| 3.0.8 | 既存 finance-news-collection スキルの統合・削除 | S | #3.0.5 | ⬜ Todo | [#692](https://github.com/YH-05/finance/issues/692) |
| 3.0.9 | finance-news-workflow 統合テスト | M | #3.0.7, #3.0.8 | ⬜ Todo | [#693](https://github.com/YH-05/finance/issues/693) |

### Wave 0: データ取得・基盤スキル（並列実装可）

#### market-data スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 3.1 | market-data スキル SKILL.md の作成 | M | なし | ⬜ Todo | - |
| 3.2 | market-data スキル guide.md の作成 | M | #3.1 | ⬜ Todo | - |
| 3.3 | market-data スキル examples/ の作成 | M | #3.1 | ⬜ Todo | - |
| 3.4 | market-data スキル エージェント統合 | S | #3.2 | ⬜ Todo | - |

#### rss-integration スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 3.5 | rss-integration スキル SKILL.md の作成 | M | なし | ⬜ Todo | - |
| 3.6 | rss-integration スキル guide.md の作成 | M | #3.5 | ⬜ Todo | - |
| 3.7 | rss-integration スキル examples/ の作成 | M | #3.5 | ⬜ Todo | - |
| 3.8 | rss-integration スキル エージェント統合 | S | #3.6 | ⬜ Todo | - |

### Wave 1: 分析スキル（並列実装可、Wave 0 依存）

#### technical-analysis スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 3.9 | technical-analysis スキル SKILL.md の作成 | M | #3.2 | ⬜ Todo | - |
| 3.10 | technical-analysis スキル guide.md の作成 | M | #3.9 | ⬜ Todo | - |
| 3.11 | technical-analysis スキル examples/ の作成 | M | #3.9 | ⬜ Todo | - |
| 3.12 | technical-analysis スキル エージェント統合 | S | #3.10 | ⬜ Todo | - |

#### financial-calculations スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 3.13 | financial-calculations スキル SKILL.md の作成 | M | #3.2 | ⬜ Todo | - |
| 3.14 | financial-calculations スキル guide.md の作成 | M | #3.13 | ⬜ Todo | - |
| 3.15 | financial-calculations スキル examples/ の作成 | M | #3.13 | ⬜ Todo | - |
| 3.16 | financial-calculations スキル エージェント統合 | S | #3.14 | ⬜ Todo | - |

### Wave 2: 外部連携スキル（並列実装可）

#### sec-edgar スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 3.17 | sec-edgar スキル SKILL.md の作成 | M | なし | ⬜ Todo | - |
| 3.18 | sec-edgar スキル guide.md の作成 | M | #3.17 | ⬜ Todo | - |
| 3.19 | sec-edgar スキル examples/ の作成 | M | #3.17 | ⬜ Todo | - |
| 3.20 | sec-edgar スキル エージェント統合 | S | #3.18 | ⬜ Todo | - |

#### web-research スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 3.21 | web-research スキル SKILL.md の作成 | M | なし | ⬜ Todo | - |
| 3.22 | web-research スキル guide.md の作成 | M | #3.21 | ⬜ Todo | - |
| 3.23 | web-research スキル examples/ の作成 | M | #3.21 | ⬜ Todo | - |
| 3.24 | web-research スキル エージェント統合 | S | #3.22 | ⬜ Todo | - |

### Wave 3: 統合テスト

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 3.25 | フェーズ3 全スキルの統合テスト実施 | M | #3.4, #3.8, #3.12, #3.16, #3.20, #3.24 | ⬜ Todo | - |

---

## 依存関係グラフ

```
フェーズ0（基盤整備）✅ DONE
    │
    ├── #598 スキル標準構造テンプレート ✅
    ├── #599 スキルプリロード仕様書 ✅ ← #598
    └── #600 スキル参照パターン ✅ ← #599
            │
            └── フェーズ1（レポジトリ管理）✅ DONE
                    │
                    ├── Wave 0 (基盤スキル) ✅
                    │   ├── skill-expert:   #601 ✅ -> #602 ✅, #603 ✅
                    │   ├── agent-expert:   #604 ✅
                    │   └── workflow-expert: #605 ✅ -> #606 ✅
                    │
                    ├── Wave 1 (レポジトリ管理) ✅
                    │   ├── index:        #607 ✅ -> #608 ✅ -> #609 ✅
                    │   ├── project-mgmt: #610 ✅ -> #611 ✅ -> #612 ✅
                    │   ├── task-decomp:  #613 ✅ -> #614 ✅ -> #615 ✅
                    │   └── issue-mgmt:   #616 ✅ -> #617 ✅ -> #618 ✅
                    │
                    └── Wave 2 (統合) ✅
                            └── #619 ✅ ← #604, #606, #609, #612, #615, #618
                    │
                    └── フェーズ2（コーディング + Git操作）✅ DONE
                            │
                            ├── Wave 1 (コーディングスキル) ✅
                            │   ├── #620 coding-standards ✅
                            │   ├── #621 tdd-development ✅
                            │   └── #622 error-handling ✅
                            │
                            └── Wave 2 (Git操作スキル) ✅
                                ├── worktree 関連: worktree, worktree-done, plan-worktrees,
                                │                  create-worktrees, delete-worktrees ✅
                                └── Git操作: push, commit-and-pr, merge-pr, gemini-search ✅
                                    │
                                    └── フェーズ3（金融分析）🔄 IN PROGRESS
                                            │
                                            ├── Wave -1 (finance-news-workflow) ⬜ ← 優先実装
                                            │   └── #685 -> #686, #687, #688 -> #689, #690, #691 -> #692 -> #693
                                            │
                                            ├── Wave 0 (データ取得・基盤) ⬜
                                            │   ├── market-data:      #3.1 -> #3.2, #3.3 -> #3.4
                                            │   └── rss-integration:  #3.5 -> #3.6, #3.7 -> #3.8
                                            │
                                            ├── Wave 1 (分析) ⬜ ← market-data
                                            │   ├── technical-analysis:     #3.9 -> #3.10, #3.11 -> #3.12
                                            │   └── financial-calculations: #3.13 -> #3.14, #3.15 -> #3.16
                                            │
                                            ├── Wave 2 (外部連携) ⬜
                                            │   ├── sec-edgar:     #3.17 -> #3.18, #3.19 -> #3.20
                                            │   └── web-research:  #3.21 -> #3.22, #3.23 -> #3.24
                                            │
                                            └── Wave 3 (統合) ⬜
                                                    └── #3.25 ← #3.4, #3.8, #3.12, #3.16, #3.20, #3.24
```

---

## Issue 一覧

### ステータス凡例

| アイコン | 状態 |
|---------|------|
| ✅ | 完了 (Done) |
| 🔄 | 進行中 (In Progress) |
| ⬜ | 未着手 (Todo) |
| ⏸️ | 保留 (Backlog) |

### フェーズ 0（完了）

| Issue | タイトル | ステータス |
|-------|---------|----------|
| [#598](https://github.com/YH-05/finance/issues/598) | スキル標準構造テンプレートの作成 | ✅ |
| [#599](https://github.com/YH-05/finance/issues/599) | スキルプリロード仕様書の作成 | ✅ |
| [#600](https://github.com/YH-05/finance/issues/600) | エージェントへのスキル参照パターンの確定 | ✅ |

### フェーズ 1（完了）

| Issue | タイトル | ステータス |
|-------|---------|----------|
| [#601](https://github.com/YH-05/finance/issues/601) | skill-expert スキル SKILL.md の作成 | ✅ |
| [#602](https://github.com/YH-05/finance/issues/602) | skill-expert スキル guide.md の作成 | ✅ |
| [#603](https://github.com/YH-05/finance/issues/603) | skill-expert スキル template.md の作成 | ✅ |
| [#604](https://github.com/YH-05/finance/issues/604) | agent-expert スキルにフロントマターレビュー機能を追加 | ✅ |
| [#605](https://github.com/YH-05/finance/issues/605) | workflow-expert スキル SKILL.md の作成 | ✅ |
| [#606](https://github.com/YH-05/finance/issues/606) | workflow-expert スキル guide.md の作成 | ✅ |
| [#607](https://github.com/YH-05/finance/issues/607) | index スキル SKILL.md の作成 | ✅ |
| [#608](https://github.com/YH-05/finance/issues/608) | index スキル guide.md の作成 | ✅ |
| [#609](https://github.com/YH-05/finance/issues/609) | 既存 /index コマンドを index スキルに置換 | ✅ |
| [#610](https://github.com/YH-05/finance/issues/610) | プロジェクト管理スキル SKILL.md の作成 | ✅ |
| [#611](https://github.com/YH-05/finance/issues/611) | プロジェクト管理スキル guide.md の作成 | ✅ |
| [#612](https://github.com/YH-05/finance/issues/612) | 既存プロジェクト管理コマンド/スキルを置換 | ✅ |
| [#613](https://github.com/YH-05/finance/issues/613) | タスク分解スキル SKILL.md の作成 | ✅ |
| [#614](https://github.com/YH-05/finance/issues/614) | タスク分解スキル guide.md の作成 | ✅ |
| [#615](https://github.com/YH-05/finance/issues/615) | task-decomposer エージェントをスキルに統合 | ✅ |
| [#616](https://github.com/YH-05/finance/issues/616) | Issue管理スキル SKILL.md の作成 | ✅ |
| [#617](https://github.com/YH-05/finance/issues/617) | Issue管理スキル guide.md の作成 | ✅ |
| [#618](https://github.com/YH-05/finance/issues/618) | 既存 issue 系コマンドを Issue管理スキルに置換 | ✅ |
| [#619](https://github.com/YH-05/finance/issues/619) | フェーズ1全スキルの統合テスト実施 | ✅ |

### フェーズ 2（完了）

#### Wave 1: コーディングスキル

| Issue | タイトル | ステータス |
|-------|---------|----------|
| [#620](https://github.com/YH-05/finance/issues/620) | coding-standards スキルの作成 | ✅ |
| [#621](https://github.com/YH-05/finance/issues/621) | tdd-development スキルの作成 | ✅ |
| [#622](https://github.com/YH-05/finance/issues/622) | error-handling スキルの作成 | ✅ |

#### Wave 2: Git操作スキル

> **Note**: Wave 2のスキルはIssue作成なしで直接実装されました。

| スキル | 説明 | ステータス |
|-------|------|----------|
| worktree | worktree作成 | ✅ |
| worktree-done | 開発完了クリーンアップ | ✅ |
| plan-worktrees | 並列開発計画 | ✅ |
| create-worktrees | worktree一括作成 | ✅ |
| delete-worktrees | worktree一括削除 | ✅ |
| push | コミット＆プッシュ | ✅ |
| commit-and-pr | コミット＆PR作成 | ✅ |
| merge-pr | PRマージ | ✅ |
| gemini-search | Gemini CLI Web検索 | ✅ |

### フェーズ 3（進行中）

| Issue                                               | タイトル                                          | ステータス |
| --------------------------------------------------- | --------------------------------------------- | ----- |
| [#685](https://github.com/YH-05/finance/issues/685) | finance-news-workflow SKILL.md の作成            | ⬜     |
| [#686](https://github.com/YH-05/finance/issues/686) | finance-news-workflow guide.md の作成            | ⬜     |
| [#687](https://github.com/YH-05/finance/issues/687) | finance-news-workflow templates/ の作成          | ⬜     |
| [#688](https://github.com/YH-05/finance/issues/688) | finance-news-workflow examples/ の作成           | ⬜     |
| [#689](https://github.com/YH-05/finance/issues/689) | /collect-finance-news コマンドの更新                 | ⬜     |
| [#690](https://github.com/YH-05/finance/issues/690) | finance-news-orchestrator, collector エージェント更新 | ⬜     |
| [#691](https://github.com/YH-05/finance/issues/691) | テーマ別エージェント群（6件）の更新                            | ⬜     |
| [#692](https://github.com/YH-05/finance/issues/692) | 既存 finance-news-collection スキルの統合・削除          | ⬜     |
| [#693](https://github.com/YH-05/finance/issues/693) | finance-news-workflow 統合テスト                   | ⬜     |

---

## 参照

### ドキュメント
- 計画書: [docs/plan/2026-01-21_System-Update-Implementation.md](../../plan/2026-01-21_System-Update-Implementation.md)
- フェーズ2詳細: [docs/plan/2026-01-21_Phase-2_Coding-Git-Skills.md](../../plan/2026-01-21_Phase-2_Coding-Git-Skills.md)

### ディレクトリ
- スキルディレクトリ: `.claude/skills/`
- エージェントディレクトリ: `.claude/agents/`
- コマンドディレクトリ: `.claude/commands/`

### フェーズ3 参照ライブラリ
| ライブラリ | パス | 用途 |
|-----------|------|------|
| market_analysis | `src/market_analysis/` | 市場データ取得・分析 |
| rss | `src/rss/` | RSS フィード管理 |
| SEC EDGAR MCP | `.mcp.json` (sec-edgar-mcp) | 企業財務データ |
| Tavily MCP | `.mcp.json` (tavily) | Web 検索 |

### フェーズ3 対象エージェント
| エージェント | スキル参照（予定） |
|-------------|-------------------|
| finance-technical-analysis | market-data, technical-analysis |
| finance-economic-analysis | market-data, financial-calculations |
| finance-market-data | market-data |
| finance-news-collector | rss-integration |
| finance-sec-filings | sec-edgar |
| finance-web | web-research |
| finance-fact-checker | sec-edgar, web-research |
| dr-source-aggregator | market-data, web-research |
| dr-stock-analyzer | market-data, technical-analysis, sec-edgar |
