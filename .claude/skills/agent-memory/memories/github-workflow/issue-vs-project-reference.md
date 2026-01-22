---
summary: "GitHub IssueとProjectの参照形式の違い - #番号はIssueリンクになるため、Project参照は明示的リンク形式必須"
created: 2026-01-23
tags: [github, issue, project, markdown, リンク]
---

# GitHub Issue と Project の参照形式ルール

## 問題

GitHub Markdown では `#15` のような形式は自動的に **Issue #15 へのリンク** として解釈される。
GitHub Project を参照したい場合に `Project #15` や `GitHub Project #15` と書いても、`#15` 部分が Issue リンクになってしまう。

## 正しい参照形式

### Issue を参照する場合
```markdown
依存: #770
関連: #806, #812
```
→ `#番号` 形式でOK（自動的にIssueリンクになる）

### GitHub Project を参照する場合
```markdown
<!-- ❌ 間違い -->
GitHub Project #15 からニュースを取得
Project: #21

<!-- ✅ 正しい -->
[GitHub Project #15](https://github.com/users/YH-05/projects/15) からニュースを取得
Project: [#21](https://github.com/users/YH-05/projects/21)
```

## URL形式

```
https://github.com/users/{username}/projects/{project_number}
```

例:
- `https://github.com/users/YH-05/projects/15` (Finance News Collection)
- `https://github.com/users/YH-05/projects/21` (週次市場動向レポート)

## Issue 作成時のチェックリスト

- [ ] `Project #番号` という記述がないか確認
- [ ] `GitHub Project #番号` という記述がないか確認
- [ ] Project への参照は全て明示的リンク形式 `[GitHub Project #番号](URL)` になっているか確認
- [ ] 依存関係の `#番号` は実際に存在する Issue 番号か確認

## 発生した実例（Project #21）

Issue #770〜#780, #806, #812, #813 で以下の問題が発生:
- `計画書: docs/project/weekly-market-report.md` → 実際は `docs/project/project-21/project.md`
- `Project #15` → Issue #15 へのリンクになっていた
- `依存: #807` → 存在しない Issue（正しくは #812）

全て手動で修正が必要だった。
