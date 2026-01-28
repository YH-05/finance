# finance-news-workflow コンテキスト最適化 実装プラン

## 背景

`/finance-news-workflow` コマンドでテーマ別サブエージェントがコンテキストオーバーを起こしている。

### 現状の問題

| 問題 | 詳細 |
|------|------|
| エージェント定義が巨大 | 各テーマエージェント 679-712行（5ファイル計 3,500行以上） |
| 既存Issueデータが冗長 | `body`フィールド（本文全体）を保持している |
| 一括処理 | 全記事を1コンテキストで処理 |

---

## 対策概要

| 対策 | 効果 |
|------|------|
| 1. エージェント定義の軽量化 | 各700行 → 100行以下（85%削減） |
| 2. 既存Issue検索の最適化 | URLとタイトルのみ取得（データ量70%削減） |
| 3. バッチ処理導入 | 5件ずつ処理（メモリ使用量削減） |

---

## Phase 1: エージェント定義の軽量化

### 対象ファイル

| ファイル | 現在の行数 | 目標 |
|---------|-----------|------|
| `.claude/agents/finance-news-index.md` | 712行 | 80行 |
| `.claude/agents/finance-news-stock.md` | 679行 | 80行 |
| `.claude/agents/finance-news-sector.md` | （確認必要） | 80行 |
| `.claude/agents/finance-news-macro.md` | 686行 | 80行 |
| `.claude/agents/finance-news-ai.md` | 682行 | 80行 |
| `.claude/agents/finance-news-finance.md` | （確認必要） | 80行 |

### 変更内容

#### 1.1 エージェント定義の新構造

各テーマエージェントは以下の情報のみを保持：

```markdown
---
name: finance-news-{theme}
description: {theme_ja}関連ニュースを収集・投稿するテーマ別エージェント
model: inherit
tools:
  - Read
  - Bash
  - MCPSearch
  - Task
  - mcp__rss__fetch_feed
  - mcp__rss__get_items
permissionMode: bypassPermissions
---

# {theme_ja} ニュース収集エージェント

## テーマ定義

| 項目 | 値 |
|------|-----|
| テーマキー | `{theme}` |
| GitHub Status ID | `{status_id}` |
| カテゴリ名 | {category_name} |
| 判定基準 | {判定基準の1行説明} |

## 処理フロー

**共通処理ガイドに従って実行**:
`.claude/skills/finance-news-workflow/common-processing-guide.md`

1. 一時ファイルからセッションデータを読み込む
2. 担当フィードからRSS取得
3. 公開日時フィルタリング（--days）
4. AI判断によるテーマ分類
5. 重複チェック
6. バッチ処理でIssue作成（5件ずつ）
7. 結果報告

## テーマ固有の設定

### 担当フィード
セッションファイルの `feed_assignments.{theme}` から読み込み

### 判定基準
{テーマ固有の判定基準 3-5行}

## 参照

- 共通処理ガイド: `.claude/skills/finance-news-workflow/common-processing-guide.md`
- テーマ設定: `data/config/finance-news-themes.json`
```

#### 1.2 削除する内容

- 詳細なPythonコード例（共通処理ガイドに集約済み）
- Phase別の詳細フロー説明
- エラーハンドリングの詳細コード
- GraphQL APIの詳細クエリ

#### 1.3 共通処理ガイドの確認

既存の `common-processing-guide.md`（1453行）は変更不要。
エージェントが必要に応じて参照する。

---

## Phase 2: 既存Issue検索の最適化

### 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `.claude/agents/finance-news-orchestrator.md` | 既存Issue取得ロジックの修正 |

### 変更内容

#### 2.1 gh issue list の出力フィールドを削減

**現在**:
```bash
gh issue list \
    --json number,title,body,createdAt
```

**変更後**:
```bash
gh issue list \
    --json number,title,createdAt
```

`body` フィールドを削除。

#### 2.2 URL抽出方式の変更

**現在**: オーケストレーターがIssue本文から正規表現でURLを抽出
**変更後**: Issueタイトルからのみ重複判定（URLは使用しない）

**理由**:
- `body` を取得しなければURL抽出不可
- タイトル類似度（Jaccard係数 0.85）で十分な重複判定が可能
- URLなしでも同一記事は同一タイトルになるため

#### 2.3 一時ファイル構造の変更

**現在**:
```json
{
  "existing_issues": [
    {
      "number": 344,
      "title": "[マクロ経済] FRB、利上げを決定",
      "article_url": "https://www.cnbc.com/...",
      "createdAt": "2026-01-21T08:22:33Z"
    }
  ]
}
```

**変更後**:
```json
{
  "existing_issues": [
    {
      "number": 344,
      "title": "[マクロ経済] FRB、利上げを決定",
      "createdAt": "2026-01-21T08:22:33Z"
    }
  ]
}
```

`article_url` フィールドを削除。

#### 2.4 重複チェックロジックの変更

**対象ファイル**: `.claude/skills/finance-news-workflow/common-processing-guide.md`

**変更内容**:
- `is_duplicate()` 関数からURL一致チェックを削除
- タイトル類似度チェックのみに統一

```python
def is_duplicate(
    new_item: dict,
    existing_issues: list[dict],
    threshold: float = 0.85,
) -> tuple[bool, int | None, str | None]:
    """タイトル類似度のみで重複チェック"""

    new_title = new_item.get('title', '')

    for issue in existing_issues:
        issue_title = issue.get('title', '')
        similarity = calculate_title_similarity(new_title, issue_title)

        if similarity >= threshold:
            return True, issue.get('number'), f"タイトル類似({similarity:.0%})"

    return False, None, None
```

---

## Phase 3: バッチ処理導入

### 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `.claude/skills/finance-news-workflow/common-processing-guide.md` | バッチ処理セクション追加 |
| `.claude/agents/finance-news-*.md` | バッチ処理への参照追加 |

### 変更内容

#### 3.1 バッチ処理の導入

**概念**:
```
全記事（例: 25件）
    ↓
バッチ1: 記事1-5 → news-article-fetcher → Issue作成
バッチ2: 記事6-10 → news-article-fetcher → Issue作成
バッチ3: 記事11-15 → news-article-fetcher → Issue作成
バッチ4: 記事16-20 → news-article-fetcher → Issue作成
バッチ5: 記事21-25 → news-article-fetcher → Issue作成
```

#### 3.2 共通処理ガイドへの追加

`common-processing-guide.md` に以下のセクションを追加:

```markdown
## Phase 4: GitHub投稿（バッチ処理）

### バッチ処理の概要

コンテキスト使用量を削減するため、記事を5件ずつバッチ処理します。

| パラメータ | 値 |
|-----------|-----|
| バッチサイズ | 5件 |
| 処理順序 | 公開日時の新しい順 |

### バッチ処理フロー

```python
BATCH_SIZE = 5

def process_in_batches(filtered_items: list[dict], stats: dict) -> list[dict]:
    """記事をバッチ処理でIssue作成"""

    created_issues = []

    # 公開日時の新しい順にソート
    sorted_items = sorted(
        filtered_items,
        key=lambda x: x.get("published", ""),
        reverse=True
    )

    # バッチに分割
    for i in range(0, len(sorted_items), BATCH_SIZE):
        batch = sorted_items[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1

        ログ出力: f"バッチ {batch_num} 処理中... ({len(batch)}件)"

        # バッチをnews-article-fetcherに渡す
        fetch_results = call_article_fetcher(batch)

        # Issue作成
        for item, result in zip(batch, fetch_results):
            if result["success"]:
                issue = create_issue(item, result)
                if issue:
                    created_issues.append(issue)
                    stats["created"] += 1

        ログ出力: f"バッチ {batch_num} 完了"

    return created_issues
```

### バッチ間の状態管理

- 各バッチの結果は `created_issues` リストに追記
- 統計カウンタ（stats）は全バッチで共有
- バッチ失敗時も次のバッチは継続
```

#### 3.3 news-article-fetcherの活用

現在の `news-article-fetcher` は既にバッチ処理に対応（複数記事を一括処理）。
変更不要。

---

## 実装順序

| 順序 | 作業 | 依存 |
|------|------|------|
| 1 | Phase 2: オーケストレーターの修正 | なし |
| 2 | Phase 2: 共通処理ガイドの重複チェック修正 | 1 |
| 3 | Phase 3: 共通処理ガイドにバッチ処理追加 | なし |
| 4 | Phase 1: テーマエージェント6ファイルの軽量化 | 2, 3 |

---

## 変更ファイル一覧

| ファイル | 変更種別 |
|---------|---------|
| `.claude/agents/finance-news-orchestrator.md` | 修正 |
| `.claude/agents/finance-news-index.md` | 大幅修正 |
| `.claude/agents/finance-news-stock.md` | 大幅修正 |
| `.claude/agents/finance-news-sector.md` | 大幅修正 |
| `.claude/agents/finance-news-macro.md` | 大幅修正 |
| `.claude/agents/finance-news-ai.md` | 大幅修正 |
| `.claude/agents/finance-news-finance.md` | 大幅修正 |
| `.claude/skills/finance-news-workflow/common-processing-guide.md` | 修正 |

---

## 検証方法

### 1. 単体テスト

```bash
# テーマエージェント単体での動作確認（dry-run）
/finance-news-workflow --days 1 --themes "index" --dry-run
```

### 2. 統合テスト

```bash
# 全テーマでの動作確認（dry-run）
/finance-news-workflow --days 1 --dry-run
```

### 3. 本番テスト

```bash
# 少量データでの本番実行
/finance-news-workflow --days 1 --themes "index"
```

### 4. 確認項目

- [ ] テーマエージェントがコンテキストオーバーなく完了する
- [ ] 重複チェックが正しく動作する（タイトル類似度）
- [ ] バッチ処理が正しく動作する（5件ずつ）
- [ ] 結果レポートが正しく出力される
- [ ] GitHub Issueが正しく作成される

---

## リスクと対策

| リスク | 対策 |
|--------|------|
| URL重複チェック廃止による誤検出 | タイトル類似度閾値を0.85に設定（現状と同じ） |
| エージェント軽量化による情報不足 | 共通処理ガイドへの参照を明示 |
| バッチ処理のオーバーヘッド | バッチサイズ5件は十分小さい |

---

## 期待効果

| 指標 | 現状 | 改善後 |
|------|------|--------|
| テーマエージェント行数 | 679-712行 | 80行（88%削減） |
| 既存Issueデータ量 | body含む全フィールド | title, number, createdAtのみ |
| 1バッチのコンテキスト | 全記事 | 5件 |
