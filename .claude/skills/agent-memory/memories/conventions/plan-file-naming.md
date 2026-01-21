---
summary: "docs/plan/ ディレクトリの計画書ファイル命名規則 - YYYY-MM-DD_内容.md形式"
created: 2026-01-19
tags: [conventions, naming, docs]
related: [docs/plan/]
---

# docs/plan/ 計画書ファイル命名規則

## 命名形式

```
YYYY-MM-DD_ファイル内容.md
```

## ルール

1. **日付**: ファイル作成日を `YYYY-MM-DD` 形式で先頭に付与
2. **内容**: 計画の主題を英語のケバブケース（kebab-case）で表現
3. **区切り**: 日付と内容の間はアンダースコア `_` で区切る

## 例

| 計画内容 | ファイル名 |
|---------|-----------|
| analysis.py の Issue 化計画 | `2026-01-19_analysis-py-issue-creation.md` |
| WebFetch サブエージェント設計 | `2026-01-19_webfetch-subagent-design.md` |
| ディープリサーチワークフロー | `2026-01-19_deep-research-workflow.md` |
| marimo ダッシュボード計画 | `2026-01-17_marimo-dashboard-plan.md` |
| ニュース収集パフォーマンス改善 | `2026-01-19_news-collector-performance.md` |

## 禁止

- ランダムな名前（例: `fluffy-watching-spindle.md`, `jiggly-noodling-tulip.md`）は使用しない
- 内容が分からない抽象的な名前は避ける
