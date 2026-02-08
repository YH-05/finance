# Issue 本文テンプレート

GitHub Issue 作成時に使用するテンプレートです。

## テンプレート

```markdown
## 概要

{タスクの概要を1-2文で記載}

## 詳細

{詳細な説明}

### 背景

{なぜこのタスクが必要か（リサーチ結果から抽出）}

### 実装方針

{implementation-plan.json から抽出した方針}

## 受け入れ条件

- [ ] {測定可能な条件1}
- [ ] {測定可能な条件2}
- [ ] {測定可能な条件3}

## 参考

- **参考実装**: {既存の類似ファイルパス}
- **計画書**: docs/project/project-{N}/project.md
- **GitHub Project**: [#{project_number}]({project_url})

## 依存関係

- **依存先**: #{先行Issue番号}（{タスク名}）
- **ブロック対象**: #{後続Issue番号}（{タスク名}）

## Wave

**Wave {N}** — {並行開発可能 / Wave N-1 完了後}
```

## タイトル規則

Issue タイトルは日本語で記述し、Wave 番号をプレフィックスに含める：

```
[Wave{N}] {日本語タイトル}
```

例：
- `[Wave1] project-researcher エージェント定義の作成`
- `[Wave2] 詳細ガイド（guide.md）の作成`
- `[Wave3] CLAUDE.md への登録と /new-project 非推奨化`

## ラベル自動判定

| プロジェクトタイプ | デフォルトラベル |
|------------------|----------------|
| package | `enhancement` |
| agent | `enhancement` |
| skill | `enhancement` |
| command | `enhancement` |
| workflow | `enhancement` |
| docs | `documentation` |
| general | `enhancement` |
