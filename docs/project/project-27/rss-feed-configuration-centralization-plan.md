# RSS フィード設定一元化計画

## 概要

finance-news-workflow の RSS フィード設定を一元化し、`data/config/finance-news-themes.json` を Single Source of Truth とする。

## 設計方針

- **振り分け方式**: 静的定義（themes.json でテーマ別にフィードを事前定義）
- **オーケストレーターの役割**: 設定の読み込みとセッションへの伝達のみ
- **識別子形式**: UUID を維持（既存互換性）

## 現状の問題

```
data/config/finance-news-themes.json
  feeds = [{feed_id, title}, ...]  ← title情報あり
         ↓
finance-news-orchestrator.md
         ↓ (セッション保存時)
.tmp/news-collection-{timestamp}.json
  feed_assignments = {index: [feed_id, ...]}  ← title が失われる！
         ↓
finance-news-*.md (6エージェント)
  ASSIGNED_FEEDS = [{feed_id, title}, ...]  ← 再度ハードコード！
```

**問題点**:
1. themes.json の title 情報がセッションで失われる
2. 6 つのサブエージェント全てでフィードリストがハードコード
3. フィード追加/変更時に 7 ファイルの更新が必要

## 改善後のデータフロー

```
data/config/finance-news-themes.json  ← 唯一の設定ソース
  feeds = [{feed_id, title}, ...]
         ↓
finance-news-orchestrator.md
         ↓ (完全なフィードオブジェクトを保存)
.tmp/news-collection-{timestamp}.json
  feed_assignments = {index: [{feed_id, title}, ...]}  ← title 保持！
         ↓
finance-news-*.md (6エージェント)
  セッションから読み込み  ← ハードコード削除！
```

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `.claude/agents/finance-news-orchestrator.md` | feed_assignments に完全なフィードオブジェクトを保存 |
| `.claude/agents/finance-news-index.md` | ASSIGNED_FEEDS ハードコード削除、セッション参照に変更 |
| `.claude/agents/finance-news-stock.md` | 同上 |
| `.claude/agents/finance-news-sector.md` | 同上 |
| `.claude/agents/finance-news-macro.md` | 同上 |
| `.claude/agents/finance-news-ai.md` | 同上 |
| `.claude/agents/finance-news-finance.md` | 同上 |

## 詳細な変更内容

### 1. finance-news-orchestrator.md

**変更箇所**: Phase 3 のセッション情報保存部分（約 line 188-194）

**Before**:
```json
"feed_assignments": {
    "index": ["b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c04", ...],
    "stock": ["b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c12", ...],
    ...
}
```

**After**:
```json
"feed_assignments": {
    "index": [
        {"feed_id": "b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c04", "title": "CNBC - Markets"},
        {"feed_id": "b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c05", "title": "CNBC - Investing"},
        ...
    ],
    ...
}
```

### 2. 各テーマエージェント（6ファイル共通）

#### a. ドキュメントテーブルの更新

**Before**:
```markdown
## 担当フィード

| フィード名 | feed_id |
|-----------|---------|
| CNBC - Markets | `b1a2c3d4-...` |
| CNBC - Investing | `b1a2c3d4-...` |
```

**After**:
```markdown
## 担当フィード

**設定ソース**: `data/config/finance-news-themes.json` → `themes.{theme}.feeds`

セッションファイルから動的に読み込まれます。設定変更は themes.json のみで完結します。
```

#### b. 実装コード部分

**Before**:
```python
ASSIGNED_FEEDS = [
    {"feed_id": "b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c04", "title": "CNBC - Markets"},
    {"feed_id": "b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c05", "title": "CNBC - Investing"},
    ...
]
```

**After**:
```python
# セッションファイルからフィード割り当てを読み込み
# （オーケストレーターが themes.json から抽出済み）
ASSIGNED_FEEDS = session_data["feed_assignments"]["index"]
```

## 検証方法

### 1. 単体検証

```bash
# 1テーマのみでワークフローを実行
# セッションファイルに title が含まれていることを確認
cat .tmp/news-collection-*.json | jq '.feed_assignments.index[0]'
# 期待: {"feed_id": "...", "title": "CNBC - Markets"}
```

### 2. 統合検証

```bash
# フルワークフローを実行
/finance-news-workflow

# 確認項目:
# - 6テーマ全てが正常動作
# - Issue作成が正常
# - フィード情報がIssue本文に正しく記載
```

### 3. 設定変更テスト

```bash
# themes.json のフィードを1つ追加/削除
# ワークフロー再実行で反映されることを確認
```

## 期待される効果

| 項目 | Before | After |
|------|--------|-------|
| フィード追加時の編集ファイル数 | 7 | 1 |
| 設定の重複 | あり | なし |
| title 情報の一貫性 | 不整合リスク | 保証 |

## 作業順序

1. `finance-news-orchestrator.md` を修正（セッション保存形式変更）
2. `finance-news-index.md` を修正（パターン確立）
3. 残り 5 エージェントを同様に修正
4. 検証実行
