---
name: project-implementation
description: GitHub Project の Todo/In Progress Issue を依存関係順に自動実装しプッシュ。/project-implement コマンドで使用。複数 Issue を順次実装し、再開機能付き。
allowed-tools: Bash, Read, Write, Glob, Grep, Task
---

# Project Implementation

GitHub Project の Todo/In Progress ステータスの Issue を依存関係を考慮した順序で自動実装するスキルです。

## 目的

このスキルは以下を提供します：

- **複数 Issue の順次実装**: Project 内の Issue を依存関係順に自動実装
- **依存関係解析**: Issue 本文と Project フィールドから依存関係を解析し実装順序を決定
- **再開機能**: 中断時の状態を進捗ファイルに保存し、途中から再開可能
- **品質チェック統合**: 各 Issue 完了後に pre-commit と CI チェックを実行

## いつ使用するか

### プロアクティブ使用（自動で検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討：

1. **Project 一括実装の議論**
   - 「Project #X の Issue を全部実装して」
   - 「このプロジェクトを進めて」
   - 複数 Issue の一括実装の意思表示

2. **並行開発完了後**
   - worktree による並列開発後、残りを順次実装したい場合

### 明示的な使用（ユーザー要求）

- `/project-implement <project_number>` コマンドの実行時
- `/project-implement --resume` で中断した作業を再開

## プロセス

### Phase 0: 初期化・再開判定

```
Phase 0: 初期化
    │
    ├─ 引数解析
    │   └─ project_number の取得
    │
    ├─ 再開判定
    │   └─ .tmp/project-{番号}-progress.json の存在確認
    │       ├─ 存在する場合 → 再開モード
    │       └─ 存在しない場合 → 新規開始
    │
    ├─ ブランチ作成/切り替え
    │   └─ feature/project-{番号}
    │
    └─ 進捗ファイル初期化（新規の場合）
```

### Phase 1: Issue 取得・依存関係解析

```
Phase 1: Issue 取得・解析
    │
    ├─ Project Items 取得
    │   └─ gh project item-list <number> --owner "@me" --format json
    │
    ├─ Todo/In Progress フィルタリング
    │   └─ status が "Todo" または "In Progress" のみ
    │
    ├─ 依存関係抽出（各 Issue の body から）
    │   ├─ "depends on #XXX"
    │   ├─ "blocked by #XXX"
    │   ├─ "requires #XXX"
    │   └─ "## 依存タスク" セクション配下の "- [ ] #XXX"
    │
    ├─ Project の blocked フィールド確認
    │   └─ カスタムフィールドがあれば参照
    │
    └─ 実装順序決定
        ├─ 依存関係を考慮したトポロジカルソート
        └─ 同じ Wave 内は Issue 番号昇順
```

### Phase 2-N: 各 Issue の実装

```
Phase 2+: Issue 実装（繰り返し）
    │
    ├─ 次の Issue を取得
    │
    ├─ /clear コマンドでコンテキスト消去
    │   └─ 進捗ファイルに現在状態を保存してから実行
    │
    ├─ issue-implementation ロジック実行
    │   ├─ Phase 0: タイプ判定
    │   ├─ Phase 1-5: 開発（サブエージェント委譲）
    │   └─ 品質チェック（make check-all）
    │
    ├─ コミット & プッシュ
    │   └─ git commit && git push
    │
    ├─ PR 作成/更新
    │   ├─ 初回: gh pr create --base main
    │   └─ 2回目以降: プッシュで自動更新
    │
    ├─ CI チェック待機
    │   ├─ 成功 → 次の Issue へ
    │   └─ 失敗 → 解決試行（最大 3 回）
    │       ├─ 解決成功 → 次の Issue へ
    │       └─ 解決失敗 → 中断（PR は残す）
    │
    ├─ Issue ステータス更新
    │   └─ Project ステータスを Done に
    │
    └─ 進捗ファイル更新

※ 単一ブランチ（feature/project-{番号}）で全 Issue を実装
※ PR は最初に1つ作成し、以降はプッシュで更新
※ PR マージは全 Issue 完了後に手動で実施
```

### Phase Final: 完了処理

```
Phase Final: 完了処理
    │
    ├─ 完了レポート出力
    │   └─ PR URL を表示
    │
    └─ 進捗ファイル削除（全 Issue 完了時のみ）

※ 開発ブランチ（feature/project-{番号}）とPRはそのまま残す
※ PR マージはユーザーが手動で実施
```

## 依存関係判定

### Issue 本文のパターン

```markdown
## 依存タスク
- [ ] #123
- [ ] #124

depends on #125
blocked by #126
requires #127
```

### 正規表現パターン

```python
patterns = [
    r"depends on #(\d+)",
    r"depends_on:\s*#(\d+)",
    r"blocked by #(\d+)",
    r"requires #(\d+)",
    r"## 依存タスク\n(?:- \[[ x]\] #(\d+)\n?)+"
]
```

## 再開機能

### 進捗ファイル

ファイルパス: `.tmp/project-{番号}-progress.json`

```json
{
  "project_number": 1,
  "branch": "feature/project-1",
  "started_at": "2026-01-25T10:00:00Z",
  "updated_at": "2026-01-25T12:30:00Z",
  "issues": {
    "total": 5,
    "completed": ["#10", "#11"],
    "current": "#12",
    "pending": ["#13", "#14"],
    "failed": null
  },
  "status": "in_progress",
  "last_error": null
}
```

### 再開時の動作

1. 進捗ファイルを読み込み
2. `branch` に切り替え
3. `current` Issue から実装を再開
4. `completed` Issue はスキップ

## リソース

### ./guide.md

詳細ガイド：

- 各 Phase の詳細フロー
- 依存関係解析アルゴリズム
- エラーハンドリング詳細
- 再開機能の実装詳細

### ./template.md

テンプレート：

- 進捗ファイルスキーマ
- 完了レポートフォーマット
- エラーレポートフォーマット

## 使用例

### 例1: 新規実行

**状況**: Project #1 の Issue を一括実装したい

**コマンド**:
```bash
/project-implement 1
```

**処理**:
1. Phase 0: ブランチ `feature/project-1` を作成
2. Phase 1: Todo/In Progress の Issue を取得、依存関係解析
3. Phase 2+: 各 Issue を順次実装（依存関係順）
4. Phase Final: プッシュ、レポート出力

**期待される出力**:
```
================================================================================
                    /project-implement #1 完了
================================================================================

## サマリー
- Project: #1
- ブランチ: feature/project-1
- 実装した Issue: 5 件
- PR: #101

## 実装結果
| # | タイトル | 状態 | コミット |
|---|----------|------|----------|
| #10 | 機能A | Done | abc1234 |
| #11 | 機能B | Done | def5678 |
| #12 | 機能C | Done | ghi9012 |
| #13 | 機能D | Done | jkl3456 |
| #14 | 機能E | Done | mno7890 |

## 次のステップ
PR #101 をレビュー・マージしてください:
gh pr view 101 --web
================================================================================
```

---

### 例2: 途中で失敗

**状況**: Issue #12 の実装中に解決できないエラーが発生

**処理**:
1. Issue #10, #11 は正常完了
2. Issue #12 で CI 失敗
3. 自動修正試行（最大 3 回）失敗
4. PR は残したまま中断
5. 進捗ファイルにエラー状態を記録

**出力**:
```
================================================================================
                    /project-implement #1 中断
================================================================================

## 状況
- 完了: #10, #11 (2 件)
- 失敗: #12
- 未着手: #13, #14
- PR: #101 (CI 失敗中)

## エラー詳細
Issue #12 の CI チェックで失敗:
- mypy: error: src/module.py:45: Incompatible return type

## 再開方法
エラーを手動で修正後:
/project-implement --resume

## 進捗ファイル
.tmp/project-1-progress.json
================================================================================
```

---

### 例3: 再開

**状況**: 失敗したプロジェクト実装を再開

**コマンド**:
```bash
/project-implement --resume
```

**処理**:
1. 進捗ファイル読み込み
2. ブランチ `feature/project-1` に切り替え
3. Issue #12 から再開（current）
4. 残りの Issue を順次実装

---

### 例4: 依存関係がある場合

**状況**: Issue 間に依存関係がある

**Project Issue 構成**:
```
#10: 基盤機能（依存なし）
#11: 基盤機能（依存なし）
#12: 機能A（depends on #10, #11）
#13: 機能B（depends on #10）
#14: 統合テスト（depends on #12, #13）
```

**実装順序**:
1. Wave 1: #10, #11（依存なし、番号順）
2. Wave 2: #12, #13（Wave 1 に依存、番号順）
3. Wave 3: #14（Wave 2 に依存）

## 品質基準

### 必須（MUST）

- [ ] Project 情報が正しく取得されている
- [ ] 依存関係が正しく解析されている
- [ ] 実装順序が依存関係を考慮している
- [ ] 各 Issue 完了後にコミット・プッシュされている
- [ ] 各 Issue 完了後に CI チェックがパスしている
- [ ] 進捗ファイルが正しく更新されている
- [ ] 失敗時に適切に中断し、再開可能な状態にする

### 推奨（SHOULD）

- Issue の Project ステータスが Done に更新されている
- 完了レポートが出力されている
- /clear でコンテキストが消去されている

## 出力フォーマット

### 開始時

```
================================================================================
                    /project-implement #{number} 開始
================================================================================

## Project 情報
- Project: #{number}
- ブランチ: feature/project-{number}
- Todo/In Progress Issue: {count} 件

## 実装順序（依存関係考慮）
Wave 1: #10, #11
Wave 2: #12, #13
Wave 3: #14

Phase 0: 初期化 ✓ 完了
```

### 各 Issue 完了時

```
## Issue #{number} 完了
- タイトル: {title}
- コミット: {commit_hash}
- CI: PASS

進捗: {completed}/{total} ({percentage}%)
```

### 完了時

```
================================================================================
                    /project-implement #{number} 完了
================================================================================

## サマリー
- Project: #{number}
- ブランチ: feature/project-{number}
- 実装した Issue: {count} 件
- PR: #{pr_number}

## 実装結果
| # | タイトル | 状態 | コミット |
|---|----------|------|----------|
| #{n1} | {title1} | Done | {hash1} |
| #{n2} | {title2} | Done | {hash2} |

## 次のステップ
PR #{pr_number} をレビュー・マージしてください:
gh pr view {pr_number} --web
================================================================================
```

## エラーハンドリング

| ケース | 対処 |
|--------|------|
| Project が存在しない | エラー表示、プロジェクト一覧を案内 |
| Todo/In Progress Issue がない | 完了メッセージ表示 |
| 循環依存 | 警告表示、循環を除外して継続 |
| Issue 実装失敗 | 自動修正試行（最大 3 回） |
| 自動修正失敗 | 現在までをコミット、進捗保存、中断 |
| 再開時に進捗ファイルがない | 新規開始として処理 |
| ブランチが既に存在 | 既存ブランチに切り替え |

## 完了条件

- [ ] Phase 0: Project 情報取得、ブランチ作成/切り替え
- [ ] Phase 1: Issue 取得、依存関係解析、実装順序決定
- [ ] Phase 2+: 各 Issue の実装とコミット
- [ ] Phase Final: プッシュ、レポート出力

**中断時**:
- [ ] 現在までの変更がコミット・プッシュされている
- [ ] 進捗ファイルにエラー状態が記録されている
- [ ] 再開方法が案内されている

## 関連スキル

- **issue-implementation**: 単一 Issue の実装ロジック（このスキルで再利用）
- **plan-worktrees**: 依存関係解析・Wave 計算の参考
- **commit-and-pr**: コミット処理の参考
- **push**: プッシュ処理の参考

## 参考資料

- `CLAUDE.md`: プロジェクト全体のガイドライン
- `.claude/skills/issue-implementation/`: Issue 実装スキル
- `.claude/skills/plan-worktrees/SKILL.md`: 依存関係解析
- `docs/github-projects-automation.md`: Project 自動化
