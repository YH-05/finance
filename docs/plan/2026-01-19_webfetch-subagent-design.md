# WebFetch専用サブエージェント設計計画

## 課題

`/collect-finance-news` コマンド実行時、各テーマエージェント（index, stock, sector, macro, ai）が直接 WebFetch を実行して記事本文を取得・要約生成を行っている。これにより：

1. **コンテキスト圧迫**: WebFetch結果（HTML→Markdown本文）がエージェントのコンテキストに蓄積
2. **5並列×複数記事**: 各エージェントが10件以上の記事をWebFetch → コンテキスト急速肥大化
3. **処理の重複**: 要約生成ロジックが5つのエージェントに重複記述

## 設計方針

WebFetch と要約生成を専用サブエージェントに分離し、テーマエージェントはコンパクトな結果のみを受け取る。

### アーキテクチャ

```
現在のフロー:
テーマエージェント
├── RSS取得（10件）
├── フィルタリング（5件残る）
├── 【問題】WebFetch × 5件（各記事の本文がコンテキストに蓄積）
├── 【問題】要約生成 × 5件（生成結果もコンテキストに）
└── GitHub Issue作成 × 5件

改善後のフロー:
テーマエージェント
├── RSS取得（10件）
├── フィルタリング（5件残る）
├── 【軽量化】news-article-fetcher サブエージェント呼び出し（URLリスト渡し）
│   └── サブエージェント内でWebFetch & 要約生成（閉じたコンテキスト）
│   └── 戻り値: {url, japanese_title, japanese_summary} のみ
└── GitHub Issue作成 × 5件（受け取った要約を使用）
```

## 実装計画

### 1. 新規エージェント作成

**ファイル**: `.claude/agents/news-article-fetcher.md`

**役割**:
- 記事URLを受け取り、WebFetchで本文取得
- 400字以上の日本語要約を生成（4セクション構成）
- 英語タイトルを日本語に翻訳
- コンパクトな結果のみを返す

**入力**:
```json
{
  "articles": [
    {
      "url": "https://...",
      "title": "Original Title",
      "summary": "RSS summary...",
      "theme": "index",
      "feed_source": "CNBC - Markets"
    }
  ]
}
```

**出力**:
```json
{
  "results": [
    {
      "url": "https://...",
      "original_title": "Original Title",
      "japanese_title": "日本語タイトル",
      "japanese_summary": "### 概要...",
      "success": true
    }
  ]
}
```

### 2. テーマエージェント修正

**対象ファイル**:
- `.claude/agents/finance-news-index.md`
- `.claude/agents/finance-news-stock.md`
- `.claude/agents/finance-news-sector.md`
- `.claude/agents/finance-news-macro.md`
- `.claude/agents/finance-news-ai.md`

**変更内容**:
- ステップ4.0（記事本文取得と要約生成）を削除
- 代わりに `news-article-fetcher` サブエージェントを呼び出し
- 戻り値の `japanese_title` と `japanese_summary` を使用してIssue作成

### 3. 共通処理ガイド更新

**ファイル**: `.claude/agents/finance_news_collector/common-processing-guide.md`

**変更内容**:
- Phase 4のステップ4.0を「サブエージェント呼び出し方式」に変更
- WebFetch関連の詳細手順をサブエージェント内に移動

## 修正対象ファイル一覧

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| `.claude/agents/news-article-fetcher.md` | 新規作成 | WebFetch専用サブエージェント |
| `.claude/agents/finance-news-index.md` | 修正 | WebFetch呼び出しをサブエージェント委譲に変更 |
| `.claude/agents/finance-news-stock.md` | 修正 | 同上 |
| `.claude/agents/finance-news-sector.md` | 修正 | 同上 |
| `.claude/agents/finance-news-macro.md` | 修正 | 同上 |
| `.claude/agents/finance-news-ai.md` | 修正 | 同上 |
| `.claude/agents/finance_news_collector/common-processing-guide.md` | 修正 | Phase 4の手順を更新 |
| `CLAUDE.md` | 修正 | エージェント一覧に追加 |

## サブエージェント詳細設計

### news-article-fetcher.md

```yaml
---
name: news-article-fetcher
description: 記事URLから本文を取得し、日本語要約を生成するサブエージェント
input: URLリストと記事メタデータ（バッチ処理）
output: 日本語タイトル・要約のJSONレスポンス
model: haiku  # 軽量モデルで十分（要約生成のみ）
color: gray
tools:
  - WebFetch
permissionMode: bypassPermissions
---
```

**処理フロー（バッチ方式）**:

1. 入力: フィルタリング済み記事リスト（全件一括）
2. 各記事URLに対して:
   a. WebFetchで本文取得（失敗時はフォールバック）
   b. 4セクション構成の日本語要約を生成
   c. 英語タイトルを日本語に翻訳
3. 結果をJSON形式で一括返却

**呼び出し例（テーマエージェントから）**:

```python
# フィルタリング後の記事リスト（例: 5件）
articles_to_fetch = [
    {"url": "https://...", "title": "...", "summary": "...", "feed_source": "..."},
    ...
]

# バッチでサブエージェントに渡す
result = Task(
    subagent_type="news-article-fetcher",
    prompt=f"""
以下の記事リストから本文を取得し、日本語要約を生成してください。

入力記事:
{json.dumps(articles_to_fetch, ensure_ascii=False)}

テーマ: {theme_name}

出力形式（JSON）:
{{
  "results": [
    {{
      "url": "...",
      "original_title": "...",
      "japanese_title": "...",
      "japanese_summary": "...",
      "success": true
    }}
  ]
}}
""",
    model="haiku"
)
```

**サブエージェントの出力**:

```json
{
  "results": [
    {
      "url": "https://www.cnbc.com/2026/01/19/...",
      "original_title": "S&P 500 hits new record high",
      "japanese_title": "S&P500が過去最高値を更新",
      "japanese_summary": "### 概要\n- S&P500指数が5,200ポイントで取引終了...",
      "success": true
    },
    {
      "url": "https://...",
      "original_title": "...",
      "japanese_title": "...",
      "japanese_summary": "⚠️ 記事本文の取得に失敗...",
      "success": false
    }
  ]
}
```

## テスト方法

1. **単体テスト**: `news-article-fetcher` を単独で呼び出し、1記事の要約生成を確認
2. **統合テスト**: `/collect-finance-news --dry-run --themes "index" --limit 3` で動作確認
3. **本番テスト**: `/collect-finance-news --themes "index" --limit 5` でIssue作成まで確認

## 期待される効果

| 指標 | 現在 | 改善後 |
|-----|------|--------|
| テーマエージェントのコンテキスト | 各記事の本文+要約が蓄積 | URLと結果のみ |
| 要約生成ロジック | 5ファイルに重複 | 1ファイルに集約 |
| 保守性 | 5ファイル同時修正が必要 | 1ファイルのみ修正 |
| 処理の独立性 | 低（WebFetch失敗がエージェント全体に影響） | 高（サブエージェント内で完結） |

## 実装手順

### Step 1: news-article-fetcher エージェント作成
1. `.claude/agents/news-article-fetcher.md` を作成
2. WebFetch + 要約生成 + タイトル翻訳のロジックを実装
3. 入出力フォーマットを定義

### Step 2: テーマエージェント修正
1. 各テーマエージェントの Phase 4 を修正
2. WebFetch 直接呼び出しを削除
3. news-article-fetcher 呼び出しに置換
4. 結果を使用してIssue作成

### Step 3: 共通処理ガイド更新
1. Phase 4 のステップ4.0を更新
2. サブエージェント呼び出し方式の説明を追加

### Step 4: CLAUDE.md 更新
1. エージェント一覧に news-article-fetcher を追加

### Step 5: テスト
1. `/collect-finance-news --dry-run --themes "index" --limit 3`
2. 動作確認後、本番テスト

## 検証方法

```bash
# 1. dry-runでフィルタリング〜要約生成まで確認
/collect-finance-news --dry-run --themes "index" --limit 3

# 2. 1テーマのみで本番テスト（Issue作成まで）
/collect-finance-news --themes "index" --limit 3

# 3. 全テーマで本番テスト
/collect-finance-news --limit 5
```
