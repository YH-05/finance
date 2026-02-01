---
name: issue-implementation-serial
description: |
  複数の GitHub Issue を連続実装し、1つの PR にまとめるスキル。
  各 Issue は issue-implement-single スキル（context: fork）で実行され、
  コンテキストが自動的に分離される。
allowed-tools: Bash, Read, Glob, Grep, Skill, AskUserQuestion
---

# Issue Implementation Serial

複数の GitHub Issue を連続実装し、1つの PR にまとめるオーケストレータースキルです。

## 目的

- 複数Issue を効率的に連続実装
- 各Issue実装時のコンテキスト増大を防止（context: fork 活用）
- 全Issueの変更を1つのPRにまとめる

---

## 入力

```
$ARGUMENTS = <issue_number1> [issue_number2] [issue_number3] ...
```

- 1つ以上の Issue 番号をスペース区切りで指定
- 単一Issue の場合も対応

---

## 処理フロー

### 単一Issue の場合

```
/issue-implement 123
       ↓
Skill(issue-implement-single, args="123")
       ↓
【context: fork で分離実行】
       ↓
サマリー返却 → 完了
```

### 複数Issue の場合

```
/issue-implement 958 959 960
       ↓
ブランチ作成: feature/issues-958-959-960
       ↓
┌─────────────────────────────────────────────┐
│ Issue #958                                   │
│ Skill(issue-implement-single, args="958 --skip-pr") │
│ → 分離コンテキストで実行                      │
│ → サマリーのみ返却                            │
│ → コミット済み                                │
└─────────────────────────────────────────────┘
       ↓ （コンテキスト分離済み）
┌─────────────────────────────────────────────┐
│ Issue #959                                   │
│ Skill(issue-implement-single, args="959 --skip-pr") │
│ → 分離コンテキストで実行                      │
│ → サマリーのみ返却                            │
│ → コミット済み                                │
└─────────────────────────────────────────────┘
       ↓ （コンテキスト分離済み）
┌─────────────────────────────────────────────┐
│ Issue #960                                   │
│ Skill(issue-implement-single, args="960 --skip-pr") │
│ → 分離コンテキストで実行                      │
│ → サマリーのみ返却                            │
│ → コミット済み                                │
└─────────────────────────────────────────────┘
       ↓
全Issueのサマリーを集約
       ↓
PR作成（全コミットをまとめて）
       ↓
Phase 6.5: PR設計レビュー（Task(pr-design)）
       ↓ 重大な問題?
  ├─ Yes → 警告出力（修正推奨）
  └─ No → 問題なし
       ↓
🚨 CIチェック検証（gh pr checks --watch）
       ↓ 全パス?
  ├─ Yes → 完了レポート出力
  └─ No → エラー修正 → プッシュ → 再検証（最大3回）
```

---

## コンテキスト分離の効果

### 従来方式（context fork なし）

```
Issue #958 実装 → コンテキスト +3000 tokens（蓄積）
Issue #959 実装 → コンテキスト +3000 tokens（蓄積）
Issue #960 実装 → コンテキスト +3000 tokens（蓄積）
────────────────────────────────────────────────
合計: +9000 tokens（親のコンテキストに蓄積）
```

### 新方式（context: fork 活用）

```
Issue #958 実装 → サマリー +100 tokens のみ
Issue #959 実装 → サマリー +100 tokens のみ
Issue #960 実装 → サマリー +100 tokens のみ
────────────────────────────────────────────────
合計: +300 tokens（約96%削減）
```

---

## 実装手順

### Step 1: 引数の解析

```python
# 概念的な処理
args = arguments.split()
issue_numbers = [int(n) for n in args if n.isdigit()]

if len(issue_numbers) == 0:
    # エラー: 引数なし
elif len(issue_numbers) == 1:
    # 単一Issueモード
else:
    # 複数Issue連続実装モード
```

### Step 2: ブランチ作成（複数Issueの場合）

```bash
# ブランチ名の決定
if [ ${#issue_numbers[@]} -eq 1 ]; then
    branch="feature/issue-${issue_numbers[0]}"
else
    branch="feature/issues-${issue_numbers[0]}-${issue_numbers[-1]}"
fi

# ブランチ作成
git checkout -b "$branch"
```

### Step 3: 各Issue の実装（Skill 呼び出し）

各Issue に対して `issue-implement-single` スキルを呼び出す:

```yaml
# Skill ツールの呼び出し
skill: "issue-implement-single"
args: "<issue_number> --skip-pr"  # 複数Issue時
```

**重要**:
- `--skip-pr` フラグにより、個別Issue実装時はPR作成をスキップ
- 各スキル実行は `context: fork` により分離されたコンテキストで実行
- 親には各Issueのサマリー（成功/失敗、コミットハッシュ等）のみ返却

### Step 4: 結果の集約

各Issue実装後に返却されるサマリーを集約:

```yaml
results:
  - issue: 958
    status: success
    commit: abc1234
  - issue: 959
    status: success
    commit: def5678
  - issue: 960
    status: failed
    error: "Phase 3 で失敗"
```

### Step 5: エラーハンドリング

いずれかのIssue実装が失敗した場合、ユーザーに確認:

```yaml
question: "Issue #960 でエラーが発生しました。どうしますか？"
header: "エラー対応"
options:
  - label: "スキップして次へ進む"
    description: "このIssueをスキップし、次のIssueに進む"
  - label: "停止してここまでをPR"
    description: "成功したIssueまでの変更でPRを作成"
  - label: "全て中断"
    description: "処理を中断し、変更はコミット済みのまま維持"
```

### Step 6: PR作成

全Issue（または成功したIssue）の実装完了後:

```bash
# プッシュ
git push -u origin "$branch"

# PR作成
gh pr create \
  --title "feat: Issue #958, #959, #960 を実装" \
  --body "$(cat <<'EOF'
## Summary

複数のIssueを連続実装しました。

### 実装したIssue
- #958: [タイトル] ✓
- #959: [タイトル] ✓
- #960: [タイトル] ✓

### 変更概要
- [サマリーから抽出]

## Test plan
- [ ] make check-all が成功することを確認
- [ ] 各Issueの受け入れ条件を確認

Fixes #958, #959, #960

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### Step 6.5: PR設計レビュー

**PR作成後、CIチェック前にコード設計品質を検証する。**

#### 6.5.1 pr-design サブエージェントの呼び出し

```yaml
subagent_type: "pr-design"
description: "PR design review"
prompt: |
  PR #{pr_number} のコード設計品質を検証してください。

  ## 検証対象PR
  - PR番号: {pr_number}
  - 対象Issue: {issue_numbers}

  ## 検証観点
  - SOLID原則（単一責任・開放閉鎖・リスコフ置換・IF分離・依存性逆転）
  - DRY原則（重複コード検出）
  - 抽象化レベルの一貫性
```

#### 6.5.2 レビュー結果の確認

pr-design の出力を確認し、重大な問題がある場合は警告を出力:

```yaml
design_review:
  score: 85  # 0-100
  solid_compliance:
    single_responsibility: "PASS"
    open_closed: "WARN"  # ← 警告あり
    ...
  issues:
    - severity: "HIGH"
      category: "solid"
      description: "if文の連鎖が検出されました"
      recommendation: "Strategy パターンへの置き換えを検討してください"
```

**判定基準**:

| スコア | 判定 | アクション |
|--------|------|-----------|
| 90-100 | 優秀 | Step 7 へ進む |
| 70-89 | 良好 | 警告を出力、Step 7 へ進む |
| 50-69 | 要改善 | **警告を出力、修正推奨（Step 7 前に修正可能）** |
| 0-49 | 問題あり | **重大な警告を出力、修正推奨（Step 7 前に修正可能）** |

#### 6.5.3 問題ありの場合

重大な問題（スコア50未満、または CRITICAL/HIGH の issue）がある場合:

1. **警告を出力**
   ```
   ⚠️ Step 6.5: PR設計レビューで問題を検出

   スコア: 45/100

   重大な問題:
   - [HIGH] SOLID: if文の連鎖が検出されました
     → Strategy パターンへの置き換えを検討してください

   推奨: CIチェック前にこれらの問題を修正してください。
   修正しない場合は、そのままCIチェックに進みます。
   ```

2. **ユーザーに確認**（オプション）
   - 修正してから CI へ進む
   - そのまま CI へ進む（レビュー指摘事項として記録）

3. **Step 7 へ進む**

#### 重要: レビュー結果は CI ブロックしない

pr-design のレビュー結果は**警告のみ**で、CI チェックはブロックしません。設計品質の問題は PR レビュー時にコメントとして残すことで、継続的な改善を促します。

---

### Step 7: 🚨 CIチェック検証（必須）

**PR作成後、GitHub Actions の CIチェックが全てパスするまで作業を完了としない。**

#### 7.1 CIチェックの完了待ち

```bash
# CIチェックの完了を待つ（最大10分）
gh pr checks <pr-number> --watch --fail-fast
```

#### 7.2 CIチェック結果の確認

```bash
# チェック結果を取得
gh pr checks <pr-number> --json name,state,bucket,description
```

チェック結果を分析:

| bucket | 意味 |
|--------|------|
| pass | 成功 |
| fail | 失敗 |
| pending | 実行中 |
| skipping | スキップ |

#### 7.3 全チェックがパスした場合

```
✅ CIチェック: 全てパス

| チェック名 | 状態 |
|------------|------|
| [name1]    | ✓    |
| [name2]    | ✓    |

→ 作業完了
```

#### 7.4 いずれかのチェックが失敗した場合

```
❌ CIチェックに失敗があります

| チェック名 | 状態 | 説明 |
|------------|------|------|
| [name1]    | ✗    | [description] |
```

**失敗時の対応フロー**:

1. **失敗したチェックのログを確認**
   ```bash
   gh run view <run-id> --log-failed
   ```

2. **エラー原因を分析し修正を実施**
   - lint/format エラー → `make format && make lint` で修正
   - typecheck エラー → 型エラーを修正
   - test エラー → テスト失敗の原因を修正

3. **修正をコミット・プッシュ**
   ```bash
   git add <修正ファイル>
   git commit -m "fix: CI エラーを修正"
   git push
   ```

4. **再度CIチェックを検証（Step 7.1 に戻る）**
   - 最大3回まで修正→再検証を繰り返す
   - 3回失敗した場合はユーザーに報告して終了

#### 重要: CIチェックをスキップしない

以下の理由により、CIチェック検証は**絶対にスキップしてはいけない**:

- ローカルの `make check-all` と GitHub Actions の実行環境は異なる可能性がある
- GitHub Actions 固有の問題（依存関係、環境変数等）を検出
- PR をマージ可能な状態で完了するのがこのスキルの責務

---

## 出力フォーマット

### 開始時

```
================================================================================
                    /issue-implement 開始
================================================================================

## 実装対象Issue
| # | Issue | タイトル |
|---|-------|----------|
| 1 | #958 | analyze → market依存関係の確立 |
| 2 | #959 | factor連携 |
| 3 | #960 | strategy連携 |

## 実行モード
複数Issue連続実装（context: fork による分離実行）

## ブランチ
feature/issues-958-960

================================================================================
```

### 各Issue完了時

```
--------------------------------------------------------------------------------
Issue #958 完了
--------------------------------------------------------------------------------
Status: ✓ Success
Type: python
Commit: abc1234
Files: 3 created, 2 modified
--------------------------------------------------------------------------------
```

### 完了時（CIチェック成功）

```
================================================================================
                    /issue-implement 完了
================================================================================

## サマリー
- 実装したIssue: 3件
- 成功: 3件
- 失敗: 0件
- 作成したPR: #500
- 設計レビュー: ✅ スコア 85/100
- CIチェック: ✅ 全てパス

## Issue別結果
| Issue | タイトル | 状態 | コミット |
|-------|----------|------|----------|
| #958 | analyze依存関係 | ✓ | abc1234 |
| #959 | factor連携 | ✓ | def5678 |
| #960 | strategy連携 | ✓ | ghi9012 |

## 作成したPR
- PR: #500
- URL: https://github.com/YH-05/finance/pull/500

## 設計レビュー結果
- スコア: 85/100
- SOLID原則: 全てPASS
- DRY原則: 問題なし
- 抽象化: 問題なし

## CIチェック結果
| チェック名 | 状態 |
|------------|------|
| check-all  | ✓    |

## 次のステップ
1. PRをレビュー: gh pr view 500 --web
2. PRをマージ: /merge-pr 500

================================================================================
```

### 完了時（CIチェック失敗→修正→成功）

```
================================================================================
                    /issue-implement 完了
================================================================================

## サマリー
- 実装したIssue: 3件
- 成功: 3件
- 失敗: 0件
- 作成したPR: #500
- 設計レビュー: ✅ スコア 85/100
- CIチェック: ✅ 全てパス（修正1回）

## CI修正履歴
| 回 | エラー内容 | 修正コミット |
|----|-----------|-------------|
| 1  | lint: unused import | fix1234 |

================================================================================
```

### 完了時（CIチェック修正不可）

```
================================================================================
                    /issue-implement 完了（⚠️ CI未解決）
================================================================================

## サマリー
- 実装したIssue: 3件
- 成功: 3件
- 失敗: 0件
- 作成したPR: #500
- 設計レビュー: ⚠️ スコア 45/100（要改善）
- CIチェック: ❌ 3回修正試行後も失敗

## CI失敗詳細
| チェック名 | 状態 | 説明 |
|------------|------|------|
| [name]     | ✗    | [description] |

## 次のステップ
1. CI失敗の詳細を確認: gh pr checks 500 --web
2. 手動で修正後にマージ: /merge-pr 500

================================================================================
```

---

## エラーハンドリング

| 状況 | 対処 |
|------|------|
| 引数なし | エラーメッセージを表示して終了 |
| Issue not found | 該当Issueをスキップするか確認 |
| 実装失敗 | ユーザーに続行/停止を確認 |
| 全Issue失敗 | エラーレポートを出力して終了 |
| CIチェック失敗 | エラー原因を分析し修正→再プッシュ→再検証（最大3回） |
| CIチェック修正不可（3回失敗） | 失敗詳細をユーザーに報告して終了 |

---

## 品質基準

### 必須（MUST）

- [ ] 各IssueがSkill(issue-implement-single)で実行されている
- [ ] 各Issue実装がcontext: forkで分離されている
- [ ] 各Issue完了時にコミットが作成されている
- [ ] 最後にPRが作成されている（複数Issue時）
- [ ] 完了レポートに全Issueの結果が含まれている
- [ ] **PR作成後にTask(pr-design)で設計レビューを実施（Step 6.5）**
- [ ] **PR作成後にCIチェックの完了を待ち、全チェックがパスしている（Step 7）**
- [ ] **CIチェック失敗時は修正を実施し、再検証している（最大3回）**

### 推奨（SHOULD）

- 各Issueのコミットメッセージに `Fixes #<number>` が含まれている
- PR本文に全ての実装Issueがリストされている
- 進捗レポートが各Issue完了時に出力されている

---

## 関連スキル

- **issue-implement-single**: 単一Issue実装（context: fork）
- **commit-and-pr**: コミットとPR作成
- **push**: コミットとプッシュ
