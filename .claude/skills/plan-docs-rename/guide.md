# Plan Docs Rename - 詳細ガイド

plan mode で生成されたランダム名プランファイルを日付ベース命名にリネームする詳細な実装ガイドです。

## 概要

このガイドでは、以下の処理フローを詳細に説明します：

```
1. ランダム名ファイル検出
   ↓
2. ファイル情報取得（作成日時・タイトル）
   ↓
3. タイトルのケバブケース化
   ↓
4. リネーム実行
   ↓
5. 結果レポート
```

## 1. ランダム名ファイルの検出

### 検出パターン

plan mode が生成するランダム名ファイルは以下の特徴があります：

```
{adjective1}-{adjective2}-{noun}.md
```

**例**:
- `fluffy-watching-spindle.md`
- `jiggly-noodling-tulip.md`
- `jazzy-sprouting-dijkstra.md`

### 検出コマンド

**基本パターン**:

```bash
# パターン: 3語ハイフン区切りの .md ファイル
find docs/plan -name '*-*-*.md' -type f
```

**最新ファイルのみ取得**（推奨）:

```bash
# macOS の場合
find docs/plan -name '*-*-*.md' -type f -exec stat -f "%m %N" {} \; | sort -rn | head -1 | awk '{print $2}'

# Linux の場合
find docs/plan -name '*-*-*.md' -type f -printf "%T@ %p\n" | sort -rn | head -1 | awk '{print $2}'
```

**説明**:
- `stat -f "%m %N"`: 修正時刻（Unixタイムスタンプ）とファイル名を出力
- `sort -rn`: 数値として降順ソート（最新が先頭）
- `head -1`: 最初の1行（最新ファイル）のみ取得
- `awk '{print $2}'`: ファイル名部分のみ抽出

### 除外パターン

既にリネーム済みのファイル（`YYYY-MM-DD_*.md` 形式）は除外：

```bash
# リネーム済みファイルの例
# - 2026-02-17_dr-industry-lead-design.md
# - 2026-02-16_notebooklm-mcp-server-plan.md

# これらは 3語ハイフン区切りパターンに一致しないため自動的に除外される
```

### エラーハンドリング

**対象ファイルが見つからない場合**:

```bash
if [ -z "$file" ]; then
  echo "ℹ️ リネーム対象のファイルが見つかりませんでした"
  ls -1 docs/plan/*.md
  exit 0
fi
```

## 2. ファイル情報の取得

### 2.1 作成日時の取得

**macOS の場合**:

```bash
# ファイル作成日時を取得（Unixタイムスタンプ）
stat -f "%B" "$file"

# 人間が読める形式で取得
stat -f "%Sm" -t "%Y-%m-%d" "$file"
```

**Linux の場合**:

```bash
# ファイル作成日時を取得
stat -c "%W" "$file"

# 修正日時を代替で使用（作成日時が取得できない場合）
stat -c "%y" "$file" | cut -d' ' -f1
```

**推奨実装**:

```bash
# クロスプラットフォーム対応
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  file_date=$(stat -f "%Sm" -t "%Y-%m-%d" "$file")
else
  # Linux
  file_date=$(stat -c "%y" "$file" | cut -d' ' -f1)
fi
```

### 2.2 タイトルの抽出

**方法**: 最初の見出し（`# タイトル`）を抽出

```bash
# 最初の見出し行を取得
title=$(grep -m 1 '^# ' "$file" | sed 's/^# //')
```

**説明**:
- `grep -m 1 '^# '`: 先頭が `# ` で始まる行を最初の1つだけ取得
- `sed 's/^# //'`: 先頭の `# ` を削除

**エラーハンドリング**:

```bash
if [ -z "$title" ]; then
  echo "⚠️ プランのタイトルを抽出できませんでした"
  echo ""
  echo "ファイル: $file"
  echo ""
  echo "対処法:"
  echo "1. ファイルを開いて最初に見出し（# タイトル）を追加"
  echo "2. 手動でリネーム: mv $file docs/plan/YYYY-MM-DD_内容名.md"
  exit 1
fi
```

## 3. タイトルのケバブケース化

### 変換ルール

1. **小文字化**: 全て小文字に変換
2. **スペース**: ハイフンに置換
3. **記号削除**: 英数字とハイフン以外を削除
4. **連続ハイフン**: 単一ハイフンに正規化
5. **前後のハイフン**: 削除

### 実装例

```bash
# タイトルをケバブケースに変換
kebab_title=$(echo "$title" | \
  tr '[:upper:]' '[:lower:]' | \     # 小文字化
  sed 's/ /-/g' | \                  # スペース → ハイフン
  sed 's/[^a-z0-9-]//g' | \          # 英数字とハイフン以外削除
  sed 's/--*/-/g' | \                # 連続ハイフン → 単一
  sed 's/^-//; s/-$//')              # 前後のハイフン削除
```

### 変換例

| 元タイトル | ケバブケース |
|-----------|-------------|
| `DR Industry Lead Design` | `dr-industry-lead-design` |
| `NotebookLM MCP Server Plan` | `notebooklm-mcp-server-plan` |
| `NASDAQ Stock Screener Implementation Plan` | `nasdaq-stock-screener-implementation-plan` |
| `News Workflow Analysis (2026-02-02)` | `news-workflow-analysis-2026-02-02` |

### 日本語タイトルの処理

日本語タイトルの場合は、ローマ字変換または英訳を検討：

```bash
# 日本語が含まれる場合の検出
if echo "$title" | grep -q '[ぁ-ん]'; then
  echo "⚠️ 日本語のタイトルが検出されました: $title"
  echo ""
  echo "対処法:"
  echo "1. プラン内のタイトルを英語に変更"
  echo "2. 手動でリネーム時に英語名を指定"
  exit 1
fi
```

**将来の拡張**: LLM を使用して日本語を英語に翻訳することも検討可能

## 4. リネーム実行

### 新しいファイル名の構築

```bash
# YYYY-MM-DD_内容名.md 形式
new_file="docs/plan/${file_date}_${kebab_title}.md"
```

### リネームの実行

```bash
# ファイルをリネーム
mv "$file" "$new_file"

# 成功確認
if [ $? -eq 0 ]; then
  echo "✅ プランファイルをリネームしました"
  echo ""
  echo "変更前: $file"
  echo "変更後: $new_file"
else
  echo "❌ リネームに失敗しました"
  exit 1
fi
```

### 重複チェック

```bash
# 同名ファイルが既に存在する場合
if [ -f "$new_file" ]; then
  echo "⚠️ 同名のファイルが既に存在します"
  echo ""
  echo "既存: $new_file"
  echo "リネーム元: $file"
  echo ""
  echo "対処法:"
  echo "1. プラン内のタイトルを変更して重複を避ける"
  echo "2. 手動で異なる名前を指定してリネーム"
  exit 1
fi
```

## 5. 結果レポート

### 成功時のレポート

```
✅ プランファイルをリネームしました

変更前: docs/plan/jazzy-sprouting-dijkstra.md
変更後: docs/plan/2026-02-17_dr-industry-lead-design.md

日付: 2026-02-17（ファイル作成日時）
タイトル: DR Industry Lead Design
```

### 対象ファイルなし時のレポート

```
ℹ️ リネーム対象のファイルが見つかりませんでした

docs/plan/ 内のファイル:
- 2026-02-17_dr-industry-lead-design.md
- 2026-02-16_notebooklm-mcp-server-plan.md

全てのファイルは既に適切な命名規則に従っています。
```

## エラーケース一覧

| エラー | 原因 | 対処法 |
|--------|------|--------|
| 対象ファイルなし | `docs/plan/` にランダム名ファイルがない | 新しいプランを作成するか、既存ファイルを確認 |
| タイトル抽出失敗 | 見出し（`# タイトル`）が存在しない | プランに見出しを追加 |
| 日本語タイトル | タイトルに日本語が含まれる | タイトルを英語に変更 |
| 重複ファイル | 同名のファイルが既に存在 | タイトルを変更して重複回避 |
| リネーム失敗 | ファイルシステムエラー | 権限やディスク容量を確認 |

## 統合スクリプト例

```bash
#!/bin/bash

# リネーム対象の最新ランダム名ファイルを取得
file=$(find docs/plan -name '*-*-*.md' -type f -exec stat -f "%m %N" {} \; | sort -rn | head -1 | awk '{print $2}')

# 対象ファイルが見つからない場合
if [ -z "$file" ]; then
  echo "ℹ️ リネーム対象のファイルが見つかりませんでした"
  ls -1 docs/plan/*.md
  exit 0
fi

# ファイル作成日時を取得
file_date=$(stat -f "%Sm" -t "%Y-%m-%d" "$file")

# タイトルを抽出
title=$(grep -m 1 '^# ' "$file" | sed 's/^# //')

# タイトルが見つからない場合
if [ -z "$title" ]; then
  echo "⚠️ プランのタイトルを抽出できませんでした"
  echo ""
  echo "ファイル: $file"
  exit 1
fi

# タイトルをケバブケースに変換
kebab_title=$(echo "$title" | \
  tr '[:upper:]' '[:lower:]' | \
  sed 's/ /-/g' | \
  sed 's/[^a-z0-9-]//g' | \
  sed 's/--*/-/g' | \
  sed 's/^-//; s/-$//')

# 新しいファイル名
new_file="docs/plan/${file_date}_${kebab_title}.md"

# 重複チェック
if [ -f "$new_file" ]; then
  echo "⚠️ 同名のファイルが既に存在します: $new_file"
  exit 1
fi

# リネーム実行
mv "$file" "$new_file"

# 結果レポート
echo "✅ プランファイルをリネームしました"
echo ""
echo "変更前: $file"
echo "変更後: $new_file"
echo ""
echo "日付: $file_date（ファイル作成日時）"
echo "タイトル: $title"
```

## ベストプラクティス

### DO（推奨）

- plan mode 終了直後に即座にリネーム
- タイトルは英語で明確に記述
- ファイル作成日時をそのまま使用（plan 作成日と一致）

### DON'T（非推奨）

- 複数のプランを作成してからまとめてリネーム（タイトルが曖昧になりがち）
- 日本語タイトルを使用（ケバブケース化が困難）
- 手動でランダム名ファイルを削除（リネームの方が履歴が残る）

## 関連スキル

- `/plan-project`: プロジェクト計画を作成（plan mode の代替）

## 将来の拡張案

- LLM を使用した日本語タイトルの自動英訳
- `--all` オプションで全ランダム名ファイルを一括リネーム
- リネーム履歴の記録（`docs/plan/.rename-history.json`）
- インタラクティブモード（リネーム前に確認）
