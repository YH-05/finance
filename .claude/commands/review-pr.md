---
description: PRレビュー（コード品質・セキュリティ・テスト）
---

# /review-pr - PRレビュー

> **役割の明確化**: このコマンドは**PRの包括的レビュー**に特化しています。
>
> - コード品質の自動修正 → `/ensure-quality`
> - 詳細な分析レポート → `/analyze`
> - セキュリティ検証のみ → `/scan`

**目的**: Pull Requestの変更内容を多角的にレビューし、フィードバックを提供する

## 実行方法

```bash
# PRレビューを実行
/review-pr
```

- GitHub PRがある場合: PR情報を取得してレビュー
- PRがない場合: ローカル差分（main...HEAD）をレビュー

## 実行フロー

### ステップ 1: PR/差分の取得

#### 1.1 GitHub PRの確認

```bash
# PRが存在するか確認
gh pr view --json number,title,body,files,additions,deletions,baseRefName,headRefName 2>/dev/null
```

**PRがある場合**:
- PR情報（タイトル、説明、変更ファイル）を取得
- `gh pr diff` で差分を取得

**PRがない場合**:
- ローカル差分モードに切り替え
- `git diff main...HEAD` で差分を取得
- `git diff main...HEAD --name-only` で変更ファイルリストを取得

#### 1.2 エラーチェック

- PRなし かつ mainブランチ上 → エラーメッセージを表示して終了
- 差分なし → 「変更がありません」と報告して終了

### ステップ 2: マルチサブエージェントレビュー（並列実行）

3つのサブエージェントを**並列**で起動してレビューを実行します。

#### 2.1 code-analyzer サブエージェント（コード品質）

```yaml
subagent_type: "code-analyzer"
description: "PR code quality review"
prompt: |
  PRの変更コードをレビューしてください。

  ## 対象ファイル
  [変更ファイルリスト]

  ## 差分
  [git diff の内容]

  ## レビュー観点
  1. 可読性（命名・ドキュメント・コメント）
  2. 設計（単一責任・DRY・抽象化レベル）
  3. 命名（変数名・関数名・一貫性）
  4. SOLID原則（S/O/L/I/D）

  ## 出力
  YAML形式で以下を出力:
  - score: 0-100
  - strengths: 良い点のリスト
  - issues: 問題点（critical/high/medium/low別）
  - solid_compliance: 各原則のPASS/WARN/FAIL
```

#### 2.2 security-scanner サブエージェント（セキュリティ）

```yaml
subagent_type: "security-scanner"
description: "PR security review"
prompt: |
  PRの変更コードをセキュリティ観点でレビューしてください。

  ## 対象ファイル
  [変更ファイルリスト]

  ## 差分
  [git diff の内容]

  ## レビュー観点
  1. 脆弱性（インジェクション・乱数・パストラバーサル・機密情報）
  2. 入力検証（ユーザー入力・サニタイゼーション・型チェック）
  3. 認証/認可（アクセス制御・認証チェック・セッション管理）

  ## 出力
  YAML形式で以下を出力:
  - score: 0-100
  - vulnerability_count: 重大度別件数
  - findings: 検出された問題（id/severity/category/location/description/recommendation/cwe_id）
```

#### 2.3 implementation-validator サブエージェント（テスト）

```yaml
subagent_type: "implementation-validator"
description: "PR test review"
prompt: |
  PRの変更に対するテストをレビューしてください。

  ## 対象ファイル
  [変更ファイルリスト]

  ## 差分
  [git diff の内容]

  ## レビュー観点
  1. カバレッジ（テスト有無・正常系・エッジケース）
  2. テストケースの妥当性（テスト名・アサーション・モック使用）
  3. テストの品質（独立性・再現性・可読性）

  ## 出力
  YAML形式で以下を出力:
  - score: 0-100
  - coverage_assessment: GOOD/FAIR/POOR
  - edge_cases_covered: true/false
  - missing_tests: 不足テストケースのリスト
  - test_quality: isolation/reproducibility/readability のPASS/WARN/FAIL
```

### ステップ 3: レビュー結果の統合と出力

サブエージェントからの結果を統合して**3つの出力**を生成します。

#### 3.1 マークダウン出力（ターミナル標準出力）

```markdown
# PR レビュー結果

## PR情報
- **タイトル**: [PRタイトル]
- **ブランチ**: [base] <- [head]
- **変更ファイル数**: [数]
- **追加行数**: [数] / **削除行数**: [数]

## 総合評価

| 観点 | スコア | 評価 |
|------|--------|------|
| コード品質 | [0-100] | [評価] |
| セキュリティ | [0-100] | [評価] |
| テスト | [0-100] | [評価] |
| **総合** | **[0-100]** | **[評価]** |

評価基準: 80+ 良好 / 60-79 改善推奨 / 60未満 要対応

## コード品質レビュー

### 良い点
- [良い点1]
- [良い点2]

### 改善が必要な点

#### [必須] 重大な問題
- **ファイル**: `[パス]:[行番号]`
- **問題**: [説明]
- **推奨修正**: [修正案]

#### [推奨] 改善提案
- [改善提案1]
- [改善提案2]

## セキュリティレビュー

### 検出された問題
| 重大度 | 件数 |
|--------|------|
| CRITICAL | [数] |
| HIGH | [数] |
| MEDIUM | [数] |
| LOW | [数] |

### 詳細
- **ID**: SEC-001
- **重大度**: [CRITICAL/HIGH/MEDIUM/LOW]
- **ファイル**: `[パス]:[行番号]`
- **問題**: [説明]
- **推奨修正**: [修正案]

## テストレビュー

### カバレッジ評価
- 変更コードのテストカバレッジ: [評価]
- エッジケースの網羅性: [評価]

### 不足しているテスト
- [テストケース1]
- [テストケース2]

## 推奨アクション

### 必須対応（マージ前に修正必要）
1. [アクション1]
2. [アクション2]

### 推奨対応（改善のため）
1. [アクション1]
2. [アクション2]

---
レビュー実行日時: [YYYY-MM-DD HH:MM:SS]
```

#### 3.2 YAMLレポート出力

**出力先**: `docs/pr-review-YYYYMMDD-HHMMSS.yaml`

```yaml
# PRレビューレポート
# 生成日時: YYYY-MM-DD HH:MM:SS
# 生成コマンド: /review-pr

metadata:
  generated_at: "YYYY-MM-DD HH:MM:SS"
  pr_number: 123  # PRがある場合、なければnull
  pr_title: "[PRタイトル]"
  base_branch: "main"
  head_branch: "[ブランチ名]"
  review_mode: "remote"  # remote | local

pr_info:
  files_changed: 0
  additions: 0
  deletions: 0
  changed_files:
    - path: "[ファイルパス]"
      additions: 0
      deletions: 0

scores:
  code_quality: 0  # 0-100
  security: 0  # 0-100
  test: 0  # 0-100
  overall: 0  # 0-100

code_quality:
  strengths:
    - "[良い点]"

  issues:
    critical: []
    high: []
    medium: []
    low: []

  solid_compliance:
    single_responsibility: "PASS"  # PASS/WARN/FAIL
    open_closed: "PASS"
    liskov_substitution: "PASS"
    interface_segregation: "PASS"
    dependency_inversion: "PASS"

security:
  vulnerability_count:
    critical: 0
    high: 0
    medium: 0
    low: 0

  findings:
    - id: "SEC-001"
      severity: "CRITICAL"
      category: "[カテゴリ]"
      location: "[ファイル]:[行番号]"
      description: "[問題の説明]"
      recommendation: "[修正案]"
      cwe_id: "CWE-XX"

test:
  coverage_assessment: "GOOD"  # GOOD/FAIR/POOR
  edge_cases_covered: true
  missing_tests: []

  test_quality:
    isolation: "PASS"  # PASS/WARN/FAIL
    reproducibility: "PASS"
    readability: "PASS"

recommended_actions:
  required:  # マージ前に必須
    - priority: 1
      action: "[アクション]"
      related_issues: []

  suggested:  # 推奨
    - priority: 1
      action: "[アクション]"

summary:
  verdict: "APPROVE"  # APPROVE/REQUEST_CHANGES/COMMENT
  comment: "[総合コメント]"
```

#### 3.3 GitHub PRコメント投稿（PRがある場合のみ）

```bash
gh pr review --comment --body "$(cat <<'EOF'
## PR レビュー結果

### 総合評価: [評価]

| 観点 | スコア | 評価 |
|------|--------|------|
| コード品質 | [0-100] | [評価] |
| セキュリティ | [0-100] | [評価] |
| テスト | [0-100] | [評価] |

### 主要な発見事項

#### 改善が必要な点
- [問題1の要約]
- [問題2の要約]

#### 良い点
- [良い点1]
- [良い点2]

### 推奨アクション
1. [最優先アクション]
2. [次のアクション]

---
Automated review by Claude Code
EOF
)"
```

### ステップ 4: 完了報告

レビュー完了をユーザーに報告:

1. マークダウンをターミナルに出力
2. YAMLファイルの保存場所を通知
3. GitHubコメントの投稿結果を通知（PRがある場合）

## エラーハンドリング

| 状況 | 対処 |
|------|------|
| PRなし + mainブランチ上 | 「レビュー対象がありません。feature ブランチで実行してください」と表示 |
| gh コマンド利用不可 | ローカルモードで続行し、GitHub コメント投稿をスキップ |
| 差分なし | 「変更がありません」と報告して終了 |
| サブエージェントエラー | 部分的な結果を出力し、エラーを報告 |

## 注意事項

- レビューは詳細な分析のため、数分かかる場合があります
- サブエージェントは並列実行されるため、効率的に処理されます
- セキュリティレビューは補完的なツールとして使用し、専門的なセキュリティ監査の代替にはなりません
- YAMLレポートは `docs/` ディレクトリに日付・時刻付きで保存されます
