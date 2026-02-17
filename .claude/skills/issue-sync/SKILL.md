---
name: issue-sync
description: |
  GitHub Issue のコメントから進捗・タスク・仕様変更を同期するスキル。
  /sync-issue コマンドで使用。
  確信度ベースの自動適用と手動確認を組み合わせ。
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, Task
---

# Issue Sync

GitHub Issue のコメントから進捗情報・新規サブタスク・仕様変更を抽出し、`project.md` と GitHub Project に反映するナレッジベーススキルです。

## 目的

このスキルは以下を提供します：

- **コメント解析**: AI によるコメントからの情報抽出
- **確信度ベース確認**: 自動適用と手動確認の適切な使い分け
- **三方向同期**: Issue・project.md・GitHub Project の同期
- **ステータス更新**: 進捗に応じた自動ステータス更新

## いつ使用するか

### プロアクティブ使用（自動で検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討：

1. **進捗管理**
   - 「コメントの内容を反映して」
   - 「進捗を同期して」
   - Issue の状態と実態の不一致

### 明示的な使用（ユーザー要求）

- `/sync-issue <番号>` コマンドの実行時

## プロセス

### 全体フロー

```
/sync-issue #123
    │
    ├─ ステップ 1: データ取得
    │   ├─ Issue 情報取得
    │   ├─ コメント取得（GraphQL）
    │   ├─ project.md 読み込み
    │   └─ GitHub Project 情報取得
    │
    ├─ ステップ 2: コメント解析
    │   └─ comment-analyzer サブエージェント起動
    │
    ├─ ステップ 3: 競合解決・確認
    │   └─ 低確信度の場合ユーザー確認
    │
    ├─ ステップ 4: 同期実行
    │   └─ task-decomposer サブエージェント起動
    │
    └─ ステップ 5: 結果表示
```

### 確信度ベース確認

| レベル | 範囲 | アクション |
|--------|------|-----------|
| HIGH | 0.80+ | 自動適用 |
| MEDIUM | 0.70-0.79 | 適用、確認なし |
| LOW | < 0.70 | ユーザー確認必須 |

**確認必須ケース**:
- ステータスダウングレード（done → in_progress）
- 受け入れ条件の削除
- 複数の矛盾するステータス変更

## 活用ツールの使用方法

### gh CLI（コメント取得）

```bash
# コメント取得（GraphQL）
gh api graphql -f owner="{owner}" -f repo="{repo}" -F number={issue_number} -f query='
  query($owner:String!, $repo:String!, $number:Int!) {
    repository(owner:$owner, name:$repo) {
      issue(number:$number) {
        title
        body
        state
        comments(last:100) {
          nodes {
            author { login }
            body
            createdAt
          }
        }
      }
    }
  }
'
```

### GitHub Project 操作

```bash
# フィールド情報取得
gh project field-list {project_number} --owner @me --format json

# Item 一覧取得
gh project item-list {project_number} --owner @me --format json

# ステータス更新
gh project item-edit \
  --project-id {project_id} \
  --id {item_id} \
  --field-id {status_field_id} \
  --single-select-option-id {option_id}
```

### サブエージェント連携

| エージェント | 用途 |
|--------------|------|
| comment-analyzer | コメント解析、進捗抽出 |
| task-decomposer | 同期実行、project.md 更新 |

## リソース

このスキルには以下のリソースが含まれています：

### ./guide.md

コメント同期の詳細ガイド：

- comment-analyzer の出力形式
- 競合解決ルール
- task-decomposer の起動方法
- エラーハンドリング

### ./template.md

同期レポートテンプレート：

- ステータス更新レポート
- 受け入れ条件更新レポート
- project.md 更新レポート

## 使用例

### 例1: 単一 Issue 同期

**状況**: Issue コメントから進捗を自動抽出したい

**処理**:
```bash
/sync-issue #123
```

1. コメント取得
2. comment-analyzer で解析
3. 確信度判定（low: ユーザー確認）
4. task-decomposer で同期
5. project.md・GitHub Project 更新

**期待される出力**:
```markdown
## コメント同期結果

### ステータス更新
| Issue | 変更前 | 変更後 | 根拠 |
|-------|--------|--------|------|
| #123 | in_progress | done | 「対応完了」|

### 受け入れ条件更新
| Issue | 条件 | 状態 |
|-------|------|------|
| #123 | OAuth対応 | ✅ 完了 |
```

---

### 例2: project.md 紐づき全 Issue 同期

**状況**: プロジェクト全体の進捗を同期

**処理**:
```bash
/sync-issue @docs/project/research-agent.md
```

1. project.md から全 Issue 番号を抽出
2. 各 Issue のコメントを取得
3. 一括で解析・同期
4. project.md・GitHub Project を更新

## 品質基準

### 必須（MUST）

- [ ] Issue 情報とコメントが取得されている
- [ ] comment-analyzer による解析が完了している
- [ ] 確認が必要な場合はユーザー確認が完了している
- [ ] project.md と GitHub Project が同期されている

### 推奨（SHOULD）

- 低確信度の変更はユーザー確認を経ている
- 矛盾する変更が検出された場合は警告されている
- 同期結果レポートが出力されている

## 出力フォーマット

### 解析結果

```markdown
## 解析結果

### ステータス更新
| Issue | 変更前 | 変更後 | 根拠 | 確信度 |
|-------|--------|--------|------|--------|
| #123 | in_progress | done | 「対応完了しました」| 0.95 |

### 受け入れ条件更新
| Issue | 条件 | 状態 | 根拠 | 確信度 |
|-------|------|------|------|--------|
| #123 | OAuth対応 | ✅ 完了 | 「OAuth対応完了」| 0.90 |
| #123 | Apple Sign-In | 📝 追加 | 「追加で必要」| 0.80 |

### 新規サブタスク
- GitHub OAuth対応（確信度: 0.85）
```

### 同期結果

```markdown
## コメント同期結果

### 対象 Issue
- [#123](URL): タイトル1
- [#124](URL): タイトル2

### project.md の更新
- 機能 1.1: ステータスを done に更新
- 機能 1.1: 受け入れ条件「Apple Sign-In対応」を追加
- 機能 1.3: 新規タスク「GitHub OAuth対応」を追加

### GitHub Project の更新
- #123: ステータスを Done に更新
- #125: Project に追加、ステータスを Todo に設定

### 未処理のコメント
以下のコメントは解析対象外としました:
- [bot]: CI結果の自動コメント
- [user]: 絵文字のみのリアクション
```

## エラーハンドリング

| ケース | 対処 |
|--------|------|
| GitHub 認証エラー | `gh auth login` を案内 |
| Issue が存在しない | エラーメッセージを表示 |
| project.md が見つからない | `/issue` で作成を提案 |
| コメント取得に失敗 | リトライ後、部分同期を提案 |
| GraphQL クエリエラー | REST API にフォールバック |
| LLM 解析タイムアウト | 部分結果を使用して続行 |

## 競合解決ルール

| 状況 | 解決策 |
|------|--------|
| コメント vs project.md で状態が異なる | コメント優先（最新情報） |
| コメント vs GitHub Project で状態が異なる | コメント優先 |
| 複数コメントで矛盾 | 最新のコメント優先 |
| Issue が closed だが完了コメントなし | closed 状態を維持 |
| confidence < 0.70 | ユーザーに確認 |
| ステータスダウングレード | ユーザーに確認（再オープンの意図を確認） |

## 完了条件

このスキルは以下の条件を満たした場合に完了とする：

- [ ] 引数が正しく解析されている
- [ ] Issue 情報とコメントが取得されている
- [ ] comment-analyzer による解析が完了している
- [ ] 確認が必要な場合はユーザー確認が完了している
- [ ] task-decomposer による同期が完了している
- [ ] 結果が表示されている

## 関連スキル

- **issue-creation**: Issue の作成
- **issue-implementation**: Issue の自動実装
- **issue-refinement**: Issue のブラッシュアップ
- **project-file**: project.md の作成・管理

## 参考資料

- `CLAUDE.md`: プロジェクト全体のガイドライン
- `.claude/commands/sync-issue.md`: /sync-issue コマンド定義
- `docs/guidelines/github-projects-automation.md`: GitHub Projects 自動化
