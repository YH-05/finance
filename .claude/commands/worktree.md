---
description: 新しいworktreeとブランチを作成して開発を開始
---

# /worktree - 開発用Worktree作成

新しい開発・実装を行う際に、メインブランチから新しいworktreeとブランチを派生させて、そのworktreeで開発を開始します。

**目的**: 並行開発のための独立した作業環境を即座に準備

## 使用例

```bash
# 機能名を指定
/worktree user-authentication

# ブランチタイプを含めて指定
/worktree fix/login-bug
/worktree feature/new-api
```

---

## ステップ 0: 引数解析

1. 引数から機能名を取得
2. **引数がない場合**: AskUserQuestion でヒアリング

```yaml
questions:
  - question: "開発する機能の名前を入力してください"
    header: "機能名"
    options:
      - label: "feature/..."
        description: "新機能の開発"
      - label: "fix/..."
        description: "バグ修正"
      - label: "refactor/..."
        description: "リファクタリング"
```

3. ブランチタイプの判定:
   - `feature/`, `fix/`, `refactor/`, `docs/`, `test/`, `release/` で始まる場合: そのまま使用
   - それ以外: `feature/` をプレフィックスとして追加

---

## ステップ 1: 事前チェック

### 1.1 リポジトリの確認

```bash
# gitリポジトリのルートを取得
git rev-parse --show-toplevel
```

**gitリポジトリでない場合**:

```
エラー: gitリポジトリではありません。
gitリポジトリ内で実行してください。
```

### 1.2 メインブランチの特定

```bash
# メインブランチを検出
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main"
```

### 1.3 未コミットの変更チェック

```bash
git status --porcelain
```

**未コミットの変更がある場合**:

```
警告: 未コミットの変更があります。

オプション:
1. 変更をコミットしてから worktree を作成
2. 変更をスタッシュしてから worktree を作成
3. 変更はそのままにして worktree を作成（推奨）

worktree は独立した作業環境なので、現在の変更に影響しません。
```

### 1.4 既存ブランチ・worktree のチェック

```bash
# 同名ブランチが存在するかチェック
git branch --list "<branch-name>"

# 既存のworktree一覧
git worktree list
```

**同名のブランチが存在する場合**:

```
警告: ブランチ '<branch-name>' は既に存在します。

オプション:
1. 既存ブランチの worktree を作成（新しいブランチは作らない）
2. 別の名前でブランチを作成
3. 処理を中断
```

---

## ステップ 2: Worktree パスの決定

### 2.1 ディレクトリ構造

worktree は親ディレクトリの `.worktrees/` フォルダに作成します:

```
parent-directory/
├── pydev-claude-code/          # メインリポジトリ (現在地)
└── .worktrees/
    └── pydev-claude-code/
        ├── feature-user-auth/  # worktree 1
        ├── fix-login-bug/      # worktree 2
        └── ...
```

### 2.2 パス生成ロジック

```python
# 例: /worktree feature/user-authentication
repo_name = "pydev-claude-code"
branch_name = "feature/user-authentication"
worktree_dir_name = branch_name.replace("/", "-")  # "feature-user-authentication"
worktree_path = f"../.worktrees/{repo_name}/{worktree_dir_name}"
```

---

## ステップ 3: Worktree 作成

### 3.1 ディレクトリ作成

```bash
mkdir -p ../.worktrees/$(basename $(pwd))
```

### 3.2 Worktree 作成コマンド

**新しいブランチを作成する場合（通常）**:

```bash
git worktree add -b <branch-name> <worktree-path> <base-branch>
```

**既存のブランチを使用する場合**:

```bash
git worktree add <worktree-path> <branch-name>
```

### 3.3 MCP設定ファイルのコピー

`.mcp.json` は `.gitignore` に含まれているため worktree にコピーされません。
MCP を使用するために、メインリポジトリから新しい worktree にコピーします。

```bash
# メインリポジトリのルートパスを取得
main_repo_path=$(git worktree list | head -1 | awk '{print $1}')

# .mcp.json が存在する場合はコピー
if [ -f "${main_repo_path}/.mcp.json" ]; then
    cp "${main_repo_path}/.mcp.json" "<worktree-path>/.mcp.json"
fi
```

### 3.4 作成確認

```bash
# 作成されたworktreeの確認
git worktree list

# 新しいworktreeでの状態確認
git -C <worktree-path> status
git -C <worktree-path> log --oneline -1

# .mcp.json がコピーされたか確認
ls -la <worktree-path>/.mcp.json 2>/dev/null && echo "✓ .mcp.json コピー済み"
```

---

## ステップ 4: 結果の表示

### 成功時の出力

```
✓ Worktree を作成しました

ブランチ: <branch-name>
ベース: <base-branch> (<commit-hash>)
パス: <absolute-worktree-path>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  重要: 新しいworktreeに移動してください
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

このセッションでは別ディレクトリに移動できません。
**新しいターミナルを開いて**、以下のコマンドを実行してください:

    cd <absolute-worktree-path>
    claude

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 開発完了後

1. 変更をコミット & プッシュ: /push
2. PRを作成: /commit-and-pr
3. worktreeを削除: /worktree-done <branch-name>
```

---

## ステップ 5: 既存 Worktree の管理（オプション）

### 5.1 一覧表示

```bash
git worktree list
```

### 5.2 Worktree の削除

```bash
# worktree を削除（ディレクトリも削除）
git worktree remove <worktree-path>

# 強制削除（未コミットの変更がある場合）
git worktree remove --force <worktree-path>
```

### 5.3 孤立した Worktree のクリーンアップ

```bash
# 参照が壊れたworktreeをクリーンアップ
git worktree prune
```

---

## ブランチ命名規則

CLAUDE.md の Git 規則に従います:

| プレフィックス | 用途 | 例 |
|----------------|------|-----|
| `feature/` | 新機能 | `feature/user-auth` |
| `fix/` | バグ修正 | `fix/login-timeout` |
| `refactor/` | リファクタリング | `refactor/api-client` |
| `docs/` | ドキュメント | `docs/api-reference` |
| `test/` | テスト追加 | `test/integration-tests` |
| `release/` | リリース準備 | `release/v1.2.0` |

---

## エラーハンドリング

### E1: ディスク容量不足

```
エラー: worktree を作成できません。
ディスク容量が不足している可能性があります。

解決方法:
1. 不要なworktreeを削除: git worktree remove <path>
2. 不要なブランチを削除: git branch -d <branch>
3. ディスク使用量を確認: df -h
```

### E2: パーミッションエラー

```
エラー: ディレクトリを作成できません。
パーミッションを確認してください。

対象パス: <path>
```

### E3: ベースブランチが古い

```
警告: ローカルの <base-branch> がリモートより古い可能性があります。

オプション:
1. fetch してから作成（推奨）
2. 現在の状態で作成
```

---

## 関連コマンド

| コマンド | 説明 |
|----------|------|
| `/push` | 変更をコミット & プッシュ |
| `/commit-and-pr` | コミット & PR作成 |
| `/issue` | Issue管理・タスク分解 |

---

## 完了条件

このワークフローは、以下の全ての条件を満たした時点で完了:

- ステップ 1: 事前チェックが完了している
- ステップ 2: worktree パスが決定している
- ステップ 3: worktree が正常に作成されている（`git worktree list` で確認）
- ステップ 3.3: `.mcp.json` が存在する場合、worktree にコピーされている
- ステップ 4: 次のステップがユーザーに案内されている
