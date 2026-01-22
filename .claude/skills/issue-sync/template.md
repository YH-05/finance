# Issue Sync Templates

コメント同期時のレポートテンプレート集です。

## 1. コメント同期結果レポート

```markdown
## コメント同期結果

### 対象 Issue
- [#123](URL): タイトル1
- [#124](URL): タイトル2

### 解析結果

#### ステータス更新
| Issue | 変更前 | 変更後 | 根拠 |
|-------|--------|--------|------|
| #123 | in_progress | done | 「対応完了しました」|

#### 受け入れ条件更新
| Issue | 条件 | 状態 | 根拠 |
|-------|------|------|------|
| #123 | Google OAuth対応 | ✅ 完了 | 「OAuth対応完了」|
| #123 | Apple Sign-In対応 | 📝 追加 | 「追加で必要」|

#### 新規サブタスク
- [#125](URL): GitHub OAuth対応（#123 から派生）

### 同期結果

#### project.md の更新
- 機能 1.1: ステータスを done に更新
- 機能 1.1: 受け入れ条件「Apple Sign-In対応」を追加
- 機能 1.3: 新規タスク「GitHub OAuth対応」を追加

#### GitHub Project の更新
- #123: ステータスを Done に更新
- #125: Project に追加、ステータスを Todo に設定

### 未処理のコメント
以下のコメントは解析対象外としました:
- [bot]: CI結果の自動コメント
- [user]: 絵文字のみのリアクション

## 次のステップ

- `/issue @{project_md_path}` で全体の同期状況を確認
- 新規サブタスクの実装を開始
```

## 2. comment-analyzer 出力形式

```yaml
extracted_updates:
  status_changes:
    - description: "完了"
      evidence: "対応完了しました"
      confidence: 0.95

  acceptance_criteria_updates:
    - criteria: "OAuth対応"
      status: "completed"
      confidence: 0.90

  new_subtasks:
    - title: "GitHub OAuth対応"
      confidence: 0.85

  requirement_changes:
    - change: "Apple Sign-In 追加"
      confidence: 0.80

confidence_summary:
  overall: 0.87
  needs_confirmation: false
```

## 3. 確信度別レポート

### HIGH (0.80+) - 自動適用

```markdown
### 自動適用された更新（確信度: HIGH）

| 種類 | 内容 | 確信度 | 根拠 |
|------|------|--------|------|
| ステータス | done | 0.95 | 「対応完了しました」|
| 受け入れ条件 | OAuth対応 ✅ | 0.90 | 「OAuth対応完了」|
```

### MEDIUM (0.70-0.79) - 適用、確認なし

```markdown
### 適用された更新（確信度: MEDIUM）

| 種類 | 内容 | 確信度 | 根拠 |
|------|------|--------|------|
| 新規サブタスク | #125 | 0.75 | 「別タスクとして対応」|
```

### LOW (< 0.70) - ユーザー確認必須

```markdown
### 確認が必要な更新（確信度: LOW）

以下の更新は確信度が低いため、ユーザー確認が必要です:

| 種類 | 内容 | 確信度 | 根拠 |
|------|------|--------|------|
| 仕様変更 | Apple Sign-In 追加 | 0.65 | 「あれば便利かも」|
```

## 4. 競合検出レポート

```markdown
### 競合検出

以下の競合が検出されました:

#### 競合 1: ステータスの不一致
- **Issue**: #123
- **コメント**: done（「対応完了」）
- **project.md**: in_progress
- **解決**: コメント優先（最新情報）

#### 競合 2: 複数の矛盾するコメント
- **Issue**: #124
- **コメント1**: 「完了」（2026-01-15）
- **コメント2**: 「やっぱり追加対応」（2026-01-18）
- **解決**: 最新のコメント優先 → in_progress
```

## 5. エラーレポート

```markdown
### 同期エラー

以下のエラーが発生しました:

| Issue | エラー | 対処 |
|-------|--------|------|
| #123 | コメント取得失敗 | リトライ後スキップ |
| #125 | Issue が存在しない | 参照を削除 |

### 推奨アクション

1. #123: 手動で `gh issue view 123` を確認
2. #125: project.md から削除された Issue への参照を削除
```

## 6. project.md 更新レポート

```markdown
### project.md の更新

#### 更新されたセクション

**機能 1.1: ユーザー認証**
```diff
- ステータス: in_progress
+ ステータス: done
```

**機能 1.1: 受け入れ条件**
```diff
- [ ] OAuth対応
+ [x] OAuth対応
+ - [ ] Apple Sign-In対応（新規追加）
```

**機能 1.3（新規追加）**
```markdown
### 機能 1.3: GitHub OAuth対応
- Issue: [#125](URL)
- 優先度: medium
- ステータス: todo
- 説明: GitHub OAuth による認証を追加
- 受け入れ条件:
  - [ ] GitHub OAuth で認証できること
```
```

## 7. GitHub Project 更新レポート

```markdown
### GitHub Project の更新

#### ステータス変更
| Issue | 変更前 | 変更後 |
|-------|--------|--------|
| #123 | In Progress | Done |
| #124 | Todo | In Progress |

#### 新規追加
| Issue | ステータス |
|-------|-----------|
| #125 | Todo |

#### フィールド更新
| Issue | フィールド | 値 |
|-------|-----------|-----|
| #125 | Priority | Medium |
| #125 | Sprint | Sprint 3 |
```

## 8. 同期サマリー

```markdown
## 同期サマリー

### 統計

| 項目 | 件数 |
|------|------|
| 処理した Issue | 5 |
| ステータス更新 | 3 |
| 受け入れ条件更新 | 7 |
| 新規サブタスク | 2 |
| 仕様変更 | 1 |
| スキップ | 1 |
| エラー | 0 |

### 確信度分布

| レベル | 件数 | 処理 |
|--------|------|------|
| HIGH (0.80+) | 8 | 自動適用 |
| MEDIUM (0.70-0.79) | 3 | 適用 |
| LOW (< 0.70) | 2 | ユーザー確認後適用 |
```
