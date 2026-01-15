---
name: project-status-sync
description: "GitHub ProjectsのIssue完了状態とdocs/project/のプロジェクトドキュメントを同期する。開発完了後にドキュメントを実態に合わせて更新。"
allowed-tools: Read, Edit, Bash, Grep, TodoWrite
---

# Project Status Sync

GitHub ProjectsのIssue完了状態とdocs/project/配下のプロジェクトドキュメント（マークダウンファイル）を同期するスキルです。

## 目的

このスキルは以下の場合に使用します：

- **開発完了後のドキュメント更新**: GitHub Project上のIssueが完了したら、対応するプロジェクトドキュメントのタスクステータスを同期
- **プロジェクト完了の記録**: 全Issueが完了したプロジェクトのステータスを「完了」に更新し、完了日を記録
- **ドキュメントと実態の整合性確保**: GitHub ProjectsとドキュメントのIssue/タスク状態の不整合を解消

## いつ使用するか

### プロアクティブ使用（自動で使用を検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討してください：

1. **GitHub Projectの全Issue完了時**
   - 特定のGitHub Projectに紐づく全Issueが「Done」になった
   - プロジェクトの最終マイルストーン達成

2. **複数Issueの一括完了時**
   - 一度に複数のIssueをクローズした
   - PRマージにより複数Issueが自動クローズされた

3. **プロジェクトドキュメントレビュー時**
   - プロジェクト計画書の見直し
   - ステータスレポート作成の前

### 明示的な使用（ユーザー要求）

- 「GitHub Projectとドキュメントを同期して」
- 「プロジェクトドキュメントを更新して」
- 「Issue完了状態を反映して」

## プロセス

### ステップ 1: 対象プロジェクトの特定

```bash
# docs/project/ 配下のプロジェクトドキュメント一覧
ls docs/project/*.md

# 各ドキュメントのGitHub Project番号を確認
grep -n "GitHub Project" docs/project/*.md
```

**確認項目**:
- プロジェクトドキュメントのファイル名
- 対応するGitHub Project番号（例: #7, #11, #14）

### ステップ 2: GitHub Projectの現在状態を取得

各GitHub Projectについて、Issue一覧とステータスを取得：

```bash
# Project #14 の例
gh project item-list 14 --owner YH-05 --format json --limit 100
```

**取得情報**:
- Issue番号
- タイトル
- ステータス（Todo, In Progress, Done）
- リンクされたPR

### ステップ 3: ドキュメントとの比較

プロジェクトドキュメントを読み込み、タスク一覧のステータスとGitHub Issueの実際のステータスを比較：

```bash
# ドキュメントを読み込む
cat docs/project/project-name.md

# タスク一覧セクションを確認
grep -A 50 "## タスク一覧" docs/project/project-name.md
```

**不整合のパターン**:

| ドキュメント | GitHub | 対処 |
|------------|--------|------|
| `- [ ]` (todo) | Done | ✓ → `- [x]` に更新 |
| `ステータス: todo` | Done | → `ステータス: done` に更新 |
| `ステータス: 計画中` | 全Done | → `ステータス: 完了` に更新 |

### ステップ 4: ドキュメントの更新

TodoWriteでタスクを管理しながら、以下を更新：

#### 4.1 個別タスクのステータス更新

```markdown
# 更新前
- [ ] 既存 src/rss/ パッケージの調査
  - Issue: [#147](https://github.com/YH-05/finance/issues/147)
  - ステータス: todo

# 更新後
- [x] 既存 src/rss/ パッケージの調査
  - Issue: [#147](https://github.com/YH-05/finance/issues/147)
  - ステータス: done
  - 調査結果: `docs/project/rss-package-investigation.md` 参照
```

**ポイント**:
- `- [ ]` を `- [x]` に変更
- `ステータス: todo` を `ステータス: done` に変更
- 成果物へのリンクを追加（該当する場合）

#### 4.2 プロジェクト全体のステータス更新

全Issueが完了している場合：

```markdown
# 更新前
**ステータス**: 計画中
**作成日**: 2026-01-15

# 更新後
**ステータス**: 完了
**作成日**: 2026-01-15
**完了日**: 2026-01-15
```

#### 4.3 GitHub Issueテーブルの更新

Issue一覧テーブルがある場合、ステータス列を追加：

```markdown
# 更新前
| # | タイトル | ラベル | Phase |
|---|---------|--------|-------|
| 147 | パッケージ調査 | enhancement | 1 |

# 更新後
| # | タイトル | ラベル | Phase | ステータス |
|---|---------|--------|-------|----------|
| [#147](https://github.com/YH-05/finance/issues/147) | パッケージ調査 | enhancement | 1 | Done |
```

**追加要素**:
- Issue番号にGitHubへのリンクを追加
- ステータス列を追加
- 全Issue完了を明記（「全Issue完了 (YYYY-MM-DD)」）

#### 4.4 最終更新情報の記録

```markdown
---

**最終更新**: 2026-01-15
**更新内容**: プロジェクトステータスを「完了」に更新、全Issue (#147-159) と GitHub Project #14 の状態を同期
```

### ステップ 5: 変更のコミット・プッシュ

```bash
# 変更状態を確認
git status
git diff --stat

# ステージング
git add docs/project/*.md

# コミット
git commit -m "docs: GitHub Projects とドキュメントを同期

変更内容:
- project-name.md を GitHub Project #XX と同期
- タスク (#YY, #ZZ) のステータスを done に更新
- プロジェクトステータスを「完了」に更新
- GitHub Issue へのリンクを追加

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# プッシュ
git push
```

## 使用例

### 例1: 単一プロジェクトの同期

```
User: GitHub Project #14のIssueが全部完了したので、ドキュメントと同期して
Assistant: GitHub Project #14の状態を確認します。

[TodoWrite, Bash, Read, Editを使用して同期作業を実行]

完了しました。以下を更新：
- financial-news-rss-collector.md のタスク (#147-150) を done に更新
- プロジェクトステータスを「完了」に更新
- 完了日を追加
- コミット・プッシュ完了
```

### 例2: 複数プロジェクトの一括同期

```
User: docs/project/配下のドキュメントとGitHub Projectsの状況を同期させて
Assistant: 3つのプロジェクトドキュメント全てを確認・同期します。

[TodoWriteで進捗管理しながら、各プロジェクトを順番に処理]

完了しました：
- research-agent.md (GitHub Project #7) と同期
- note-content-enhancement.md (GitHub Project #11) と同期
- financial-news-rss-collector.md (GitHub Project #14) と同期
- 全ての変更をコミット・プッシュ完了
```

## ガイドライン

### ドキュメント更新の原則

1. **GitHub Projectが信頼できる情報源**: ドキュメントではなくGitHub Projectの状態が実態
2. **成果物へのリンク**: 完了タスクには、成果物（ドキュメント・コード）へのリンクを追加
3. **コミットメッセージの明確化**: どのプロジェクト・Issueを同期したかを明記
4. **完了日の記録**: プロジェクト完了時には完了日を追加

### 注意事項

- タスクの「完了」判断はGitHub IssueがCloseかつPRがマージ済みを基準とする
- ドキュメント側のステータスを優先せず、必ず GitHub の実態と同期させる
- 全Issue完了の場合のみ、プロジェクトステータスを「完了」にする
- 成果物が存在する場合は必ずリンクを追加する

## 関連スキル・コマンド

- `/issue` - GitHub Issue と project.md の双方向同期（開発中のタスク管理）
- `/sync-issue` - Issue コメントからの進捗・タスク同期
- `/project-refine` - プロジェクト健全性チェックとタスク再構成
- `/worktree-done` - worktree開発完了後のクリーンアップ
