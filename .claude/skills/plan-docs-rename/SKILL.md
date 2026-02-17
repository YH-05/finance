---
name: plan-docs-rename
description: plan modeで生成されたランダム名プランを日付ベース命名（YYYY-MM-DD_内容名.md）にリネーム。
allowed-tools: Read, Bash, Glob
---

# Plan Docs Rename

plan mode で生成されたランダム名のプランファイルを、意味のある日付ベースの命名規則に従ってリネームするスキルです。

## 目的

plan mode は便利ですが、エクスポートされるファイル名がランダム（例: `fluffy-watching-spindle.md`）なため、以下の問題があります：

- 📁 ファイルの内容が一目で分からない
- 🔍 後から探すのが困難
- 📚 整理・管理がしにくい

このスキルは、これらの問題を解決します。

## いつ使用するか

- plan mode 終了直後に `/plan-docs-rename` で実行
- `docs/plan/` 内のランダム名ファイルを整理したい時

## 命名規則

以下の形式に従ってリネームします：

```
YYYY-MM-DD_内容名.md
```

**例**:
- `2026-02-17_dr-industry-lead-design.md`
- `2026-02-16_notebooklm-mcp-server-plan.md`
- `2026-02-09_nasdaq-stock-screener-implementation-plan.md`

この規則は `.claude/skills/agent-memory/memories/conventions/plan-file-naming.md` で定義されています。

## プロセス

### 1. ランダム名ファイルの検出

`docs/plan/` 内のランダム名ファイル（3語ハイフン区切り形式）を検出し、最新のものを取得：

```bash
# ランダム名ファイルのパターン例
# - fluffy-watching-spindle.md
# - jiggly-noodling-tulip.md
# - jazzy-sprouting-dijkstra.md

# 最新のランダム名ファイルを取得
find docs/plan -name '*-*-*.md' -type f -exec stat -f "%m %N" {} \; | sort -rn | head -1
```

### 2. ファイル情報の取得

- **作成日時**: ファイルメタデータから取得（`stat` コマンド）
- **タイトル**: 最初の見出し（`# タイトル`）を抽出

### 3. ケバブケース化

タイトルを英語のケバブケース（kebab-case）に変換：

- 日本語 → ローマ字変換（または英訳）
- スペース → ハイフン
- 大文字 → 小文字
- 記号 → 削除
- 連続ハイフン → 単一ハイフン

**例**:
- "DR Industry Lead Design" → `dr-industry-lead-design`
- "NotebookLM MCP Server Plan" → `notebooklm-mcp-server-plan`

### 4. リネーム実行

```bash
mv docs/plan/old-name.md docs/plan/YYYY-MM-DD_new-name.md
```

### 5. 確認レポート

リネーム結果を報告：

```
✅ プランファイルをリネームしました

変更前: docs/plan/jazzy-sprouting-dijkstra.md
変更後: docs/plan/2026-02-17_dr-industry-lead-design.md

日付: 2026-02-17（ファイル作成日時）
タイトル: DR Industry Lead Design
```

## リソース

### ./guide.md

詳細な実装ガイド：

- ランダム名ファイルの検出パターン
- 日付取得の具体的なコマンド
- タイトル抽出とケバブケース化のロジック
- エラーハンドリング

## 使用例

### 例1: plan mode 直後のリネーム

**状況**: plan mode でプランを作成し、`docs/plan/jazzy-sprouting-dijkstra.md` が生成された

**実行**:
```bash
/plan-docs-rename
```

**結果**:
```
✅ プランファイルをリネームしました

変更前: docs/plan/jazzy-sprouting-dijkstra.md
変更後: docs/plan/2026-02-17_dr-industry-lead-design.md
```

---

### 例2: 対象ファイルが見つからない場合

**状況**: `docs/plan/` に既にリネーム済みのファイルしかない

**実行**:
```bash
/plan-docs-rename
```

**結果**:
```
ℹ️ リネーム対象のファイルが見つかりませんでした

docs/plan/ 内のファイル:
- 2026-02-17_dr-industry-lead-design.md
- 2026-02-16_notebooklm-mcp-server-plan.md

全てのファイルは既に適切な命名規則に従っています。
```

---

### 例3: タイトルが見つからない場合

**状況**: プランファイルに見出し（`# タイトル`）が存在しない

**実行**:
```bash
/plan-docs-rename
```

**結果**:
```
⚠️ プランのタイトルを抽出できませんでした

ファイル: docs/plan/jazzy-sprouting-dijkstra.md

対処法:
1. ファイルを開いて最初に見出し（# タイトル）を追加
2. 手動でリネーム: mv docs/plan/jazzy-sprouting-dijkstra.md docs/plan/YYYY-MM-DD_内容名.md
```

## 品質基準

### 必須（MUST）

- [ ] ランダム名ファイルが正しく検出される
- [ ] 日付が `YYYY-MM-DD` 形式で取得される
- [ ] タイトルがケバブケース化される
- [ ] リネーム前後のファイル名が報告される
- [ ] ファイルが存在しない場合は適切なメッセージを表示

### 推奨（SHOULD）

- タイトルが見つからない場合は代替手段を提示
- リネーム済みファイルはスキップ
- エラー発生時は原因と対処法を明示

## 完了条件

- [ ] ランダム名ファイルが検出され、リネームされる
- [ ] リネーム結果が報告される
- [ ] エラーケースが適切に処理される

## 関連リソース

- **命名規則メモリ**: `.claude/skills/agent-memory/memories/conventions/plan-file-naming.md`
- **既存のプラン例**: `docs/plan/2026-*-*.md`
