---
name: push
description: 変更をコミットしてリモートにプッシュ。/push コマンドで使用。コミットメッセージ自動生成、ステージング、プッシュを一括実行。
allowed-tools: Read, Bash
---

# Push - コミット & プッシュ

変更をコミットし、リモートリポジトリにプッシュします。

> **関連コマンド**:
>
> - コミット + プッシュ → `/push`（このコマンド）
> - コミット + プッシュ + PR 作成 → `/commit-and-pr`

## 実行手順

### ステップ 1: 変更状態の確認

以下のコマンドを並列で実行:

```bash
git status                    # 変更状態を確認
git diff --stat               # 変更ファイルの統計
git log --oneline -3          # 最新のコミットを確認
```

**変更がない場合**:

```
変更がありません。コミットするものがないため、処理を終了します。
```

### ステップ 2: コミットの作成（未コミットの変更がある場合）

#### 2.1 変更内容の分析

```bash
git diff                      # 未ステージの変更
git diff --staged             # ステージ済みの変更
```

#### 2.2 コミットメッセージの作成

変更内容を分析し、以下のフォーマットでコミットメッセージを作成:

```
<type>: <簡潔な説明>

<詳細な説明（必要に応じて）>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

**type の種類**:

| type     | 用途                           |
| -------- | ------------------------------ |
| feat     | 新機能                         |
| fix      | バグ修正                       |
| refactor | リファクタリング               |
| docs     | ドキュメントのみの変更         |
| test     | テストの追加・修正             |
| chore    | ビルド、設定ファイルなどの変更 |

#### 2.3 コミットの実行

```bash
git add -A
git commit -m "$(cat <<'EOF'
<コミットメッセージ>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

### ステップ 3: リモートブランチの確認

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "no-upstream"
```

### ステップ 4: プッシュの実行

**リモートトラッキングブランチがある場合**:

```bash
git push
```

**初回プッシュ（リモートトラッキングブランチがない場合）**:

```bash
git push -u origin $(git rev-parse --abbrev-ref HEAD)
```

### ステップ 5: 結果の表示

```
コミット & プッシュが完了しました。

ブランチ: <branch-name>
コミット: <commit-hash> <commit-message>
リモート: origin

次のステップ:
- PR を作成する場合: gh pr create
- 変更を続ける場合: 作業を継続
```

## 注意事項

1. **main/master ブランチへの直接プッシュ**

    - 可能な限り避ける
    - 必要な場合は実行前に確認

2. **フォースプッシュ**

    - このコマンドでは `--force` を使用しない
    - フォースプッシュが必要な場合は手動で実行

3. **機密ファイル**
    - `.env`、`credentials.json` などはコミットしない
    - 検出した場合は警告を表示

## 使用例

```bash
# 変更をコミットしてプッシュ
/push

# PR も作成したい場合
/commit-and-pr
```
