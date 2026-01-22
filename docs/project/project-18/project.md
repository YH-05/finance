# System Update: スキルベースシステム移行

## プロジェクト情報

| 項目 | 内容 |
|------|------|
| GitHub Project | [#18](https://github.com/users/YH-05/projects/18) |
| 計画書 | [docs/plan/2026-01-21_System-Update-Implementation.md](../../plan/2026-01-21_System-Update-Implementation.md) |
| 目的 | 既存のコマンドベースシステムをスキルベースのシステムに移行 |

## フェーズ概要

| フェーズ | 内容 | ステータス |
|---------|------|----------|
| フェーズ 0 | 基盤整備（Project作成、テンプレート、仕様書） | Done |
| フェーズ 1 | レポジトリ管理スキル（7スキル作成） | Todo |
| フェーズ 2 | コーディングスキル（3スキル作成） | Todo |
| フェーズ 3 | 金融分析スキル（後続） | Backlog |
| フェーズ 4 | 記事執筆スキル（後続） | Backlog |

---

## フェーズ 0: 基盤整備

### タスク

| # | タスク | 依存 | ステータス | Issue |
|---|--------|------|----------|-------|
| 0.1 | GitHub Project「System Update」の作成 | なし | Done | - |
| 0.2 | スキル標準構造テンプレートの作成 | なし | Done | [#598](https://github.com/YH-05/finance/issues/598) |
| 0.3 | スキルプリロード仕様書の作成 | 0.2 | Done | [#599](https://github.com/YH-05/finance/issues/599) |
| 0.4 | エージェントへのスキル参照パターンの確定 | 0.3 | Done | [#600](https://github.com/YH-05/finance/issues/600) |

---

## フェーズ 1: レポジトリ管理スキル

### Wave 0: 基盤スキル（最優先・並列実装可）

#### skill-expert スキル（新規）

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 1 | skill-expert スキル SKILL.md の作成 | M | なし | Done | [#601](https://github.com/YH-05/finance/issues/601) |
| 2 | skill-expert スキル guide.md の作成 | M | #1 | Done | [#602](https://github.com/YH-05/finance/issues/602) |
| 3 | skill-expert スキル template.md の作成 | S | #1 | Done | [#603](https://github.com/YH-05/finance/issues/603) |

#### agent-expert スキル拡張

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 4 | agent-expert スキルにフロントマターレビュー機能を追加 | S | なし | Done | [#604](https://github.com/YH-05/finance/issues/604) |

#### workflow-expert スキル（新規）

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 5 | workflow-expert スキル SKILL.md の作成 | M | なし | Done | [#605](https://github.com/YH-05/finance/issues/605) |
| 6 | workflow-expert スキル guide.md の作成 | M | #5 | Done | [#606](https://github.com/YH-05/finance/issues/606) |

### Wave 1: レポジトリ管理スキル（並列実装可）

#### index スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 7 | index スキル SKILL.md の作成 | M | #3 | Todo | [#607](https://github.com/YH-05/finance/issues/607) |
| 8 | index スキル guide.md の作成 | S | #7 | Todo | [#608](https://github.com/YH-05/finance/issues/608) |
| 9 | 既存 /index コマンドを index スキルに置換 | S | #8 | Todo | [#609](https://github.com/YH-05/finance/issues/609) |

#### プロジェクト管理スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 10 | プロジェクト管理スキル SKILL.md の作成 | M | #3 | Todo | [#610](https://github.com/YH-05/finance/issues/610) |
| 11 | プロジェクト管理スキル guide.md の作成 | M | #10 | Todo | [#611](https://github.com/YH-05/finance/issues/611) |
| 12 | 既存プロジェクト管理コマンド/スキルを置換 | M | #11 | Todo | [#612](https://github.com/YH-05/finance/issues/612) |

#### タスク分解スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 13 | タスク分解スキル SKILL.md の作成 | M | #3 | Done | [#613](https://github.com/YH-05/finance/issues/613) |
| 14 | タスク分解スキル guide.md の作成 | M | #13 | Done | [#614](https://github.com/YH-05/finance/issues/614) |
| 15 | task-decomposer エージェントをスキルに統合 | M | #14 | Todo | [#615](https://github.com/YH-05/finance/issues/615) |

#### Issue管理スキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 16 | Issue管理スキル SKILL.md の作成 | M | #3 | Done | [#616](https://github.com/YH-05/finance/issues/616) |
| 17 | Issue管理スキル guide.md の作成 | M | #16 | Todo | [#617](https://github.com/YH-05/finance/issues/617) |
| 18 | 既存 issue 系コマンドを Issue管理スキルに置換 | L | #17 | Todo | [#618](https://github.com/YH-05/finance/issues/618) |

### Wave 2: 統合

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 19 | フェーズ1全スキルの統合テスト実施 | M | #4, #6, #9, #12, #15, #18 | Todo | [#619](https://github.com/YH-05/finance/issues/619) |

---

## フェーズ 2: コーディングスキル

| # | タスク | 工数 | 依存 | ステータス | Issue |
|---|--------|------|------|----------|-------|
| 2.1 | coding-standards スキルの作成 | L | フェーズ1完了 | Todo | [#620](https://github.com/YH-05/finance/issues/620) |
| 2.2 | tdd-development スキルの作成 | L | フェーズ1完了 | Todo | [#621](https://github.com/YH-05/finance/issues/621) |
| 2.3 | error-handling スキルの作成 | L | フェーズ1完了 | Todo | [#622](https://github.com/YH-05/finance/issues/622) |

---

## 依存関係グラフ

```
フェーズ0（基盤整備）
    │
    ├── #598 スキル標準構造テンプレート
    ├── #599 スキルプリロード仕様書 ← #598
    └── #600 スキル参照パターン ← #599
            │
            └── フェーズ1（レポジトリ管理）
                    │
                    ├── Wave 0 (基盤スキル - 最優先)
                    │   ├── skill-expert:   #601 -> #602, #603
                    │   ├── agent-expert:   #604
                    │   └── workflow-expert: #605 -> #606
                    │
                    ├── Wave 1 (レポジトリ管理) ← #603
                    │   ├── index:        #607 -> #608 -> #609
                    │   ├── project-mgmt: #610 -> #611 -> #612
                    │   ├── task-decomp:  #613 -> #614 -> #615
                    │   └── issue-mgmt:   #616 -> #617 -> #618
                    │
                    └── Wave 2 (統合)
                            └── #619 ← #604, #606, #609, #612, #615, #618
                    │
                    └── フェーズ2（コーディング）
                            ├── #620 coding-standards
                            ├── #621 tdd-development
                            └── #622 error-handling
```

---

## Issue 一覧

| Issue | タイトル | フェーズ |
|-------|---------|---------|
| [#598](https://github.com/YH-05/finance/issues/598) | スキル標準構造テンプレートの作成 | 0 |
| [#599](https://github.com/YH-05/finance/issues/599) | スキルプリロード仕様書の作成 | 0 |
| [#600](https://github.com/YH-05/finance/issues/600) | エージェントへのスキル参照パターンの確定 | 0 |
| [#601](https://github.com/YH-05/finance/issues/601) | skill-expert スキル SKILL.md の作成 | 1 |
| [#602](https://github.com/YH-05/finance/issues/602) | skill-expert スキル guide.md の作成 | 1 |
| [#603](https://github.com/YH-05/finance/issues/603) | skill-expert スキル template.md の作成 | 1 |
| [#604](https://github.com/YH-05/finance/issues/604) | agent-expert スキルにフロントマターレビュー機能を追加 | 1 |
| [#605](https://github.com/YH-05/finance/issues/605) | workflow-expert スキル SKILL.md の作成 | 1 |
| [#606](https://github.com/YH-05/finance/issues/606) | workflow-expert スキル guide.md の作成 | 1 |
| [#607](https://github.com/YH-05/finance/issues/607) | index スキル SKILL.md の作成 | 1 |
| [#608](https://github.com/YH-05/finance/issues/608) | index スキル guide.md の作成 | 1 |
| [#609](https://github.com/YH-05/finance/issues/609) | 既存 /index コマンドを index スキルに置換 | 1 |
| [#610](https://github.com/YH-05/finance/issues/610) | プロジェクト管理スキル SKILL.md の作成 | 1 |
| [#611](https://github.com/YH-05/finance/issues/611) | プロジェクト管理スキル guide.md の作成 | 1 |
| [#612](https://github.com/YH-05/finance/issues/612) | 既存プロジェクト管理コマンド/スキルを置換 | 1 |
| [#613](https://github.com/YH-05/finance/issues/613) | タスク分解スキル SKILL.md の作成 | 1 |
| [#614](https://github.com/YH-05/finance/issues/614) | タスク分解スキル guide.md の作成 | 1 |
| [#615](https://github.com/YH-05/finance/issues/615) | task-decomposer エージェントをスキルに統合 | 1 |
| [#616](https://github.com/YH-05/finance/issues/616) | Issue管理スキル SKILL.md の作成 | 1 |
| [#617](https://github.com/YH-05/finance/issues/617) | Issue管理スキル guide.md の作成 | 1 |
| [#618](https://github.com/YH-05/finance/issues/618) | 既存 issue 系コマンドを Issue管理スキルに置換 | 1 |
| [#619](https://github.com/YH-05/finance/issues/619) | フェーズ1全スキルの統合テスト実施 | 1 |
| [#620](https://github.com/YH-05/finance/issues/620) | coding-standards スキルの作成 | 2 |
| [#621](https://github.com/YH-05/finance/issues/621) | tdd-development スキルの作成 | 2 |
| [#622](https://github.com/YH-05/finance/issues/622) | error-handling スキルの作成 | 2 |

---

## 参照

- 計画書: [docs/plan/2026-01-21_System-Update-Implementation.md](../../plan/2026-01-21_System-Update-Implementation.md)
- スキルディレクトリ: `.claude/skills/`
- エージェントディレクトリ: `.claude/agents/`
- コマンドディレクトリ: `.claude/commands/`
