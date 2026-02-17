---
description: リサーチベースのプロジェクト計画ワークフロー。リサーチ→設計→タスク分解→GitHub Project 登録を一貫実行。
argument-hint: [プロジェクト名] [--type package|agent|skill|command|workflow|docs] [@src/*/docs/project.md] [@docs/plan/*.md]
---

リサーチベースのプロジェクト計画ワークフローを実行します。

## スキルの読み込み

**plan-project** スキルを読み込んでください。
スキルの SKILL.md と guide.md に詳細なワークフロー手順が記載されています。

## 引数

| 引数 | 必須 | 説明 | 例 |
|------|------|------|-----|
| プロジェクト名 | - | プロジェクト名（テキスト） | `"認証システムの実装"` |
| --type | - | プロジェクトタイプ | `--type agent` |
| @src/* | - | パッケージパス | `@src/market_analysis/docs/project.md` |
| @docs/plan/* | - | プランファイルパス | `@docs/plan/2026-02-15_example.md` |

**プランファイル対応**:
- `@docs/plan/*.md` を引数に指定すると、Phase 4 で `docs/project/project-{N}/original-plan.md` として移動
- プランファイルからプロジェクト名とタイプを推測して実行

## 実行手順

guide.md の Phase 0〜4 を順番に実行してください：

1. **Phase 0**: 引数パース → タイプ判定 → セッション作成 → [HF0] 方向確認
2. **Phase 1**: Task(project-researcher) → [HF1] リサーチ結果確認
3. **Phase 2**: Task(project-planner) → [HF2] 計画承認
4. **Phase 3**: Task(project-decomposer) → [HF3] タスク確認
5. **Phase 4**: GitHub Project 作成 → Issue 登録 → project.md 作成 → 完了レポート

各 Phase の HF（Human Feedback）ゲートでは必ず AskUserQuestion でユーザー確認を取得してから次に進んでください。

## 注意事項

- セッションデータは `.tmp/plan-project-{session_id}/` に保存
- エージェントへのデータ渡しは JSON ファイル経由（`.claude/rules/subagent-data-passing.md` 準拠）
- Issue のタイトル・本文は日本語で記述
