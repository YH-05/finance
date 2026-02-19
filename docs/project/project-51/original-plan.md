# ca-eval 構造化出力スキーマ定義 実装計画

## Context

ca-eval ワークフローの構造化出力JSONファイルに以下の問題がある：

1. **スキーマ定義の分散**: 各エージェントMarkdownにインライン記述されており独立ファイルがない
2. **定義と実出力の乖離**: claims.json を筆頭に、フィールド名・構造が定義と実出力で大きく異なる
3. **サンプル間の不一致**: AME版 vs ATCOA版で構造が異なる（fact-check.json のグループ化方向が逆等）
4. **sec-data.json のスキーマ未定義**: finance-sec-filings はca-eval専用でなくスキーマ定義なし
5. **Pydanticモデル不在**: 型安全性・バリデーションの仕組みがない

本計画で実施すること：
- 9つの構造化出力すべてのJSONスキーマをテンプレートファイルとして独立管理
- AME最新版（`CA_eval_20260218-1454_AME`）の実出力構造を正とする
- 各エージェント定義のインラインスキーマをテンプレート参照に置換
- SKILL.md にスキーマファイル一覧を追記

---

## 乖離マトリクス

| ファイル | タスク | 定義-実出力乖離 | サンプル間一貫性 | 統一方針 |
|---|---|---|---|---|
| `research-meta.json` | T0 | 小 | 低 | AME最新版に統一。`task_results`必須化 |
| `sec-data.json` | T1 | **定義なし** | 高 | 新規定義（AME実出力ベース） |
| `parsed-report.json` | T2 | 中 | 高 | AME版（`ca_candidates[]`フラット構造）に統一 |
| `claims.json` | T4 | **大** | 中 | AME版に統一。`rule_applications{}`オブジェクト形式 |
| `fact-check.json` | T5 | 中 | 低 | AME版（`fact_checks[].factual_claims_checked[]`ネスト）に統一 |
| `pattern-verification.json` | T6 | 中 | 中 | AME版（`pattern_results[]`）に統一 |
| `structured.json` | T7 | 未検証 | 中 | AME版（`rule_summary{}` + `patterns_detected{}`）に統一 |
| `critique.json` | T8 | 小 | 高 | ほぼ現状維持 |
| `accuracy-report.json` | T9 | 小 | 中 | AME版ベース + ATCOA有用フィールドをオプション追加 |

---

## 実装ステップ

### Step 1: スキーマテンプレートファイル作成（9ファイル新規作成）

配置先: `.claude/skills/ca-eval/templates/schemas/`

| ファイル | ベース | 主な変更点 |
|---|---|---|
| `research-meta.schema.md` | AME実出力 | `task_results`・`outputs`・`summary`を必須化 |
| `sec-data.schema.md` | AME実出力 | **新規定義**。`data_limitations`でSEC非対応を明示 |
| `parsed-report.schema.md` | AME実出力 | `ca_candidates[]`フラット構造。旧`sections[].advantage_candidates`廃止 |
| `claims.schema.md` | AME実出力 | `rule_applications{}`オブジェクト形式。旧`rule_evaluation.results[]`配列廃止 |
| `fact-check.schema.md` | AME実出力 | `fact_checks[].factual_claims_checked[]`ネスト構造。旧`verified_claims[]`フラット廃止 |
| `pattern-verification.schema.md` | AME実出力 | `pattern_results[]`統一。旧`pattern_matches[]`廃止 |
| `structured.schema.md` | AME実出力 | `rule_summary{}`文字列値。旧`five_layer_evaluation`・`confidence_rationale`廃止 |
| `critique.schema.md` | AME/ATCOA共通 | ほぼ現状維持。`suggested_revision`をオプション追加 |
| `accuracy-report.schema.md` | AME実出力 | `mode_determination{}`統一。ATCOA`data_quality_note`をオプション追加 |

**各スキーマファイルの共通フォーマット**:

```markdown
# {ファイル名} スキーマ

> 生成タスク: T{N} | 生成エージェント: {agent名}
> 読み込み先: {後続タスク一覧}

## JSONスキーマ

\```json
{AME版実出力に基づく完全なサンプルJSON}
\```

## フィールド説明

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|

## バリデーションルール

- {ルール1}
- {ルール2}
```

### Step 2: エージェント定義の修正（6ファイル修正）

各エージェントの `## 出力スキーマ` セクションのインラインJSONを削除し、テンプレート参照に置換。

| ファイル | 修正対象セクション | 参照先スキーマ |
|---|---|---|
| `ca-report-parser.md` | `## 出力スキーマ`（82〜139行） | `parsed-report.schema.md` |
| `ca-claim-extractor.md` | `## 出力スキーマ`（118〜189行） | `claims.schema.md` |
| `ca-fact-checker.md` | `## 出力スキーマ`（88〜141行） | `fact-check.schema.md` |
| `ca-pattern-verifier.md` | `## 出力スキーマ`（109〜175行） | `pattern-verification.schema.md` |
| `ca-report-generator.md` | `### Step 4: 構造化 JSON 生成`（111〜243行） | `structured.schema.md` |
| `ca-eval-lead.md` | T0, T8（793〜833行）, T9（906〜930行） | `research-meta.schema.md`, `critique.schema.md`, `accuracy-report.schema.md` |

**置換パターン**:
```markdown
## 出力スキーマ

スキーマ定義ファイルを Read で読み込み、フィールドと型に従って出力すること:

\```
.claude/skills/ca-eval/templates/schemas/{ファイル名}.schema.md
\```

**重要な制約**:
- フィールド名を変更してはならない
- 必須フィールドを省略してはならない
```

**ca-eval-lead.md 追加修正**:
- T1タスク説明に `sec-data.schema.md` への参照を追加
- T0の `research-meta.json` 生成箇所に `research-meta.schema.md` への参照を追加

### Step 3: SKILL.md の更新（1ファイル修正）

`## レポートフォーマットテンプレート` セクション（167〜172行）を `## テンプレートファイル` に拡張し、スキーマファイル一覧テーブルを追加。

```markdown
## テンプレートファイル

### レポートフォーマット（Markdown）
| テンプレート | パス | 用途 |
|---|---|---|
| draft-report | `templates/draft-report-format.md` | T7 ドラフトレポート |
| revised-report | `templates/revised-report-format.md` | T8 修正版レポート |

### 構造化出力スキーマ（JSON）
| スキーマ | 対応出力 | 生成タスク |
|---|---|---|
| `schemas/research-meta.schema.md` | `00_meta/research-meta.json` | T0 |
| `schemas/sec-data.schema.md` | `01_data_collection/sec-data.json` | T1 |
| `schemas/parsed-report.schema.md` | `01_data_collection/parsed-report.json` | T2 |
| `schemas/claims.schema.md` | `02_claims/claims.json` | T4 |
| `schemas/fact-check.schema.md` | `03_verification/fact-check.json` | T5 |
| `schemas/pattern-verification.schema.md` | `03_verification/pattern-verification.json` | T6 |
| `schemas/structured.schema.md` | `04_output/structured.json` | T7 |
| `schemas/critique.schema.md` | `04_output/critique.json` | T8 |
| `schemas/accuracy-report.schema.md` | `04_output/accuracy-report.json` | T9 |
```

---

## 対象ファイル一覧

### 新規作成（9ファイル）

```
.claude/skills/ca-eval/templates/schemas/
├── research-meta.schema.md
├── sec-data.schema.md
├── parsed-report.schema.md
├── claims.schema.md
├── fact-check.schema.md
├── pattern-verification.schema.md
├── structured.schema.md
├── critique.schema.md
└── accuracy-report.schema.md
```

### 修正（7ファイル）

```
.claude/agents/ca-report-parser.md
.claude/agents/ca-claim-extractor.md
.claude/agents/ca-fact-checker.md
.claude/agents/ca-pattern-verifier.md
.claude/agents/ca-report-generator.md
.claude/agents/deep-research/ca-eval-lead.md
.claude/skills/ca-eval/SKILL.md
```

---

## 実装順序と依存関係

```
Step 1: schemas/ 9ファイル作成（並列可能）
  ↓
Step 2: エージェント定義 6ファイル修正（Step 1完了後、各ファイル独立して修正可能）
  ↓
Step 3: SKILL.md 更新（Step 1, 2完了後）
```

---

## 検証方法

1. **スキーマの完全性**: 各スキーマファイルのJSONサンプルが `CA_eval_20260218-1454_AME` の実出力と構造一致することを確認
2. **エージェント定義の参照整合性**: 各エージェントがスキーマファイルのパスを正しく参照していることを確認
3. **SKILL.md の一覧網羅性**: 9スキーマすべてが一覧テーブルに含まれていることを確認
4. **実行テスト**: `/ca-eval` を実行し、出力JSONがスキーマに準拠していることを目視確認

---

## 将来検討事項（本計画のスコープ外）

- **Pydanticモデル化**: スキーマをPydanticモデルとして型定義し、バリデーション自動化
- **industry-context.json**: T3（industry-researcher）のスキーマ定義（現在スキップ中のため対象外）
- **five_layer_evaluation の復活**: PoC完了後に精度検証の精緻化で必要になる可能性
