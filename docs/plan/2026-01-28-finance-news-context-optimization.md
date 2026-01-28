# finance-news-workflow コンテキスト最適化 実装プラン

## 背景

`/finance-news-workflow` コマンドでテーマ別サブエージェントがコンテキストオーバーを起こしている。

### 現状の問題

| 問題 | 詳細 |
|------|------|
| エージェント定義が巨大 | 各テーマエージェント 539-712行（6ファイル計 4,002行） |
| Issue作成ロジックの重複 | 各テーマエージェントがIssue作成・Project追加・Status/Date設定を個別実装 |
| 一括処理 | 全記事を1コンテキストで処理（article-fetcher呼び出し含む） |

### 現状のアーキテクチャ

```
オーケストレーター (405行)
├── 既存Issue取得（gh issue list --json number,title,body,createdAt）
├── body → article_url 抽出・キャッシュ
└── セッションファイル作成 (.tmp/news-collection-{timestamp}.json)
    ↓
テーマエージェント × 6（各539-712行、並列実行）
├── RSS取得 → 日時フィルタ → テーママッチ → 重複チェック
├── news-article-fetcher 呼び出し（WebFetch + 要約生成）
├── Issue作成（gh issue create）
├── Project追加（gh project item-add）
├── Status設定（GraphQL API）
└── 公開日時設定（GraphQL API）
    ↓
news-article-fetcher (332行, Haiku)
├── WebFetch で記事本文取得
└── 日本語4セクション要約生成
```

**問題の核心**: テーマエージェントがIssue作成からProject設定まで全て担当しているため、
エージェント定義が700行規模になり、処理中のコンテキストも肥大化する。

---

## 対策概要

| 対策 | 効果 |
|------|------|
| 1. article-fetcher拡張（Issue作成統合） | テーマエージェントからIssue作成ロジック（約250行）を除去 |
| 2. テーマエージェント軽量化 | 各700行 → 200-300行（60-70%削減） |
| 3. バッチ処理導入 | 5件ずつarticle-fetcher呼び出し（コンテキスト分割） |

### 改善後のアーキテクチャ

```
オーケストレーター (405行、変更なし)
├── 既存Issue取得（body → article_url 抽出、URL重複チェック維持）
└── セッションファイル作成
    ↓
テーマエージェント × 6（各200-300行、並列実行）
├── RSS取得 → 日時フィルタ → テーママッチ → 重複チェック
└── 5件ずつ news-article-fetcher に委譲（バッチ処理）
    ↓
news-article-fetcher（拡張版、Sonnet）
├── WebFetch で記事本文取得
├── 日本語4セクション要約生成
├── Issue作成（gh issue create + close）
├── Project追加（gh project item-add）
├── Status設定（GraphQL API）
└── 公開日時設定（GraphQL API）
```

---

## Phase 1: article-fetcher 拡張（WebFetch + Issue作成統合）

### 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `.claude/agents/news-article-fetcher.md` | Issue作成ロジック追加、モデル変更 |

### 変更内容

#### 1.1 モデル変更

```yaml
# 変更前
model: haiku

# 変更後
model: sonnet
```

**理由**: Issue作成にBashツール（`gh`コマンド）とGraphQL APIの実行が必要。
Haikuでは複雑なシェルコマンド連携が不安定。

#### 1.2 ツール追加

```yaml
# 変更前
tools:
  - WebFetch

# 変更後
tools:
  - WebFetch
  - Bash
```

**理由**: `gh issue create`, `gh project item-add`, `gh api graphql` の実行に必要。

#### 1.3 入力形式の拡張

**現在の入力**:
```json
{
  "articles": [
    {
      "url": "https://www.cnbc.com/...",
      "title": "S&P 500 hits new record high",
      "summary": "The index closed at 5,200...",
      "feed_source": "CNBC - Markets",
      "theme": "index"
    }
  ],
  "theme": "index"
}
```

**拡張後の入力**:
```json
{
  "articles": [
    {
      "url": "https://www.cnbc.com/...",
      "title": "S&P 500 hits new record high",
      "summary": "The index closed at 5,200...",
      "feed_source": "CNBC - Markets",
      "published": "2026-01-19T12:00:00+00:00"
    }
  ],
  "issue_config": {
    "theme_key": "index",
    "theme_label": "株価指数",
    "status_option_id": "3925acc3",
    "project_id": "PVT_kwHOBoK6AM4BMpw_",
    "project_number": 15,
    "project_owner": "YH-05",
    "repo": "YH-05/finance",
    "status_field_id": "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
    "published_date_field_id": "PVTF_lAHOBoK6AM4BMpw_zg8BzrI"
  }
}
```

**追加フィールド**:

| フィールド | 説明 | 用途 |
|-----------|------|------|
| `articles[].published` | 記事公開日時 | Issue本文の「公開日」、Projectの日付フィールド |
| `issue_config.theme_key` | テーマキー | Issue本文の「カテゴリ」「備考」 |
| `issue_config.theme_label` | テーマ日本語名 | Issueタイトルプレフィックス `[{theme_label}]` |
| `issue_config.status_option_id` | Status設定値 | GraphQL APIでStatusフィールド設定 |
| `issue_config.project_id` | Project ID | GraphQL APIで使用 |
| `issue_config.project_number` | Project番号 | `gh project item-add` で使用 |
| `issue_config.project_owner` | Projectオーナー | `gh project item-add` で使用 |
| `issue_config.repo` | リポジトリ | `gh issue create` で使用 |
| `issue_config.status_field_id` | StatusフィールドID | GraphQL APIで使用 |
| `issue_config.published_date_field_id` | 公開日フィールドID | GraphQL APIで使用 |

#### 1.4 出力形式の拡張

**現在の出力**:
```json
{
  "results": [
    {
      "url": "https://...",
      "original_title": "...",
      "japanese_title": "...",
      "japanese_summary": "### 概要\n...",
      "success": true
    }
  ],
  "stats": { "total": 5, "success": 4, "failed": 1 }
}
```

**拡張後の出力**:
```json
{
  "created_issues": [
    {
      "issue_number": 200,
      "issue_url": "https://github.com/YH-05/finance/issues/200",
      "title": "[株価指数] S&P500が過去最高値を更新",
      "article_url": "https://www.cnbc.com/...",
      "published_date": "2026-01-19"
    }
  ],
  "skipped": [
    {
      "url": "https://...",
      "title": "...",
      "reason": "要約フォーマット不正（### 概要 で始まらない）"
    }
  ],
  "stats": {
    "total": 5,
    "fetch_success": 4,
    "fetch_failed": 1,
    "issue_created": 3,
    "issue_failed": 1,
    "skipped_format": 0
  }
}
```

#### 1.5 新しい処理フロー

```
各記事に対して:
  1. WebFetch → 記事本文取得
  2. 日本語4セクション要約生成
  3. タイトル翻訳
  4. 要約フォーマット検証（### 概要 で始まるか）
  5. URL必須検証
  6. Issue作成（gh issue create + close）
  7. Project追加（gh project item-add）
  8. Status設定（GraphQL API）
  9. 公開日時設定（GraphQL API）
```

#### 1.6 Issue作成ロジック（テーマエージェントから移植）

以下のロジックをテーマエージェントから移植:

**Issue本文テンプレート**:
```bash
body=$(cat <<EOF
${japanese_summary}

### 情報源URL

${article_url}

### 公開日

${published_jst}(JST)

### 収集日時

${collected_at}(JST)

### カテゴリ

${theme_label}

### フィード/情報源名

${feed_source}

### 備考・メモ

- テーマ: ${theme_label}
- AI判定理由: ${判定理由}

---

**自動収集**: このIssueは \`/finance-news-workflow\` コマンドによって自動作成されました。
EOF
)
```

**Issue作成 → close → Project追加 → Status/Date設定**:
```bash
# Issue作成
issue_url=$(gh issue create \
    --repo ${repo} \
    --title "[${theme_label}] ${japanese_title}" \
    --body "$body" \
    --label "news")

issue_number=$(echo "$issue_url" | grep -oE '[0-9]+$')

# close
gh issue close "$issue_number" --repo ${repo}

# Project追加
gh project item-add ${project_number} \
    --owner ${project_owner} \
    --url ${issue_url}

# Status設定（GraphQL）
# 公開日時設定（GraphQL）
```

#### 1.7 エラーハンドリング

| エラー | 対処 |
|--------|------|
| WebFetch失敗 | フォールバック要約生成（RSS summaryベース） |
| 要約フォーマット不正 | `skipped`に記録、Issue作成スキップ |
| Issue作成失敗 | `stats.issue_failed` カウント、次の記事へ |
| Project追加失敗 | 警告ログ、Issue作成は成功扱い |
| Status/Date設定失敗 | 警告ログ、Issue作成は成功扱い |

#### 1.8 既存機能の維持

以下は変更なし:
- WebFetchのプロンプト内容
- 4セクション要約フォーマット（概要・背景・市場への影響・今後の見通し）
- URL保持ルール（入力URLをそのまま使用、リダイレクト先URL禁止）
- テーマ別重点項目テーブル
- 要約品質基準（400字以上）

---

## Phase 2: テーマエージェント軽量化

### 対象ファイル

| ファイル | 現在の行数 | 目標 |
|---------|-----------|------|
| `.claude/agents/finance-news-index.md` | 712行 | 200-300行 |
| `.claude/agents/finance-news-stock.md` | 679行 | 200-300行 |
| `.claude/agents/finance-news-sector.md` | 704行 | 200-300行 |
| `.claude/agents/finance-news-macro.md` | 686行 | 200-300行 |
| `.claude/agents/finance-news-ai.md` | 682行 | 200-300行 |
| `.claude/agents/finance-news-finance.md` | 539行 | 200-300行 |

### 変更内容

#### 2.1 残す内容（テーマ固有情報）

| セクション | 内容 | 行数目安 |
|-----------|------|---------|
| frontmatter | name, model, tools, permissions | 15行 |
| テーマ定義 | テーマキー、Status ID、キーワード | 15行 |
| 担当フィード | セッションファイルからの読み込み方法 | 10行 |
| 重要ルール | 入力データ検証、フィード直接取得、重複回避 | 20行 |
| 処理フロー概要 | Phase 1-5の概要図（新フロー） | 30行 |
| Phase 1: 初期化 | MCPツールロード、セッション読み込み | 30行 |
| Phase 2: RSS取得 | フィードフェッチ、記事取得 | 25行 |
| Phase 2.5: 日時フィルタ | 共通処理ガイド参照 + 簡潔な説明 | 10行 |
| Phase 3: フィルタリング | キーワードマッチング、除外、重複チェック | 20行 |
| **Phase 4: バッチ投稿（新）** | 5件ずつarticle-fetcherに委譲 | 40行 |
| Phase 5: 結果報告 | 統計テーブル出力 | 30行 |
| 判定例 | テーマ固有の具体例 | 15行 |
| 参考資料 | リンク一覧 | 10行 |
| **合計** | | **約270行** |

#### 2.2 削除する内容

| セクション | 現在の行数 | 理由 |
|-----------|-----------|------|
| Phase 4: Issue作成の詳細 | 約100行 | article-fetcherに移管 |
| ステップ4.1: Issue作成bashコード | 約50行 | article-fetcherに移管 |
| ステップ4.2: Project追加 | 約10行 | article-fetcherに移管 |
| ステップ4.3: Status設定GraphQL | 約40行 | article-fetcherに移管 |
| ステップ4.4: 公開日時設定GraphQL | 約30行 | article-fetcherに移管 |
| エラーハンドリング詳細コード | 約60行 | 共通処理ガイド参照に |
| Phase 1の詳細Pythonコード | 約30行 | 共通処理ガイド参照に |
| Phase 2の詳細Pythonコード | 約60行 | 共通処理ガイド参照に |
| 実行ログ例 | 約30行 | 冗長のため削除 |
| **合計削除** | **約410行** | |

#### 2.3 新しいPhase 4（バッチ投稿）の内容

テーマエージェントのPhase 4は以下に置き換え:

```markdown
### Phase 4: バッチ投稿（article-fetcherに委譲）

フィルタリング済み記事を5件ずつ `news-article-fetcher` に委譲します。
article-fetcher が WebFetch → 要約生成 → Issue作成 → Project追加 → Status/Date設定を一括実行します。

#### バッチ処理フロー

```python
BATCH_SIZE = 5

# 公開日時の新しい順にソート
sorted_items = sorted(filtered_items, key=lambda x: x.get("published", ""), reverse=True)

all_created = []
for i in range(0, len(sorted_items), BATCH_SIZE):
    batch = sorted_items[i:i + BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    ログ出力: f"バッチ {batch_num} 処理中... ({len(batch)}件)"

    # article-fetcher に委譲
    result = Task(
        subagent_type="news-article-fetcher",
        description=f"バッチ{batch_num}: 記事取得・要約・Issue作成",
        prompt=f"""以下の記事を処理してください。

入力:
{json.dumps({
    "articles": [
        {
            "url": item["link"],
            "title": item["title"],
            "summary": item.get("summary", ""),
            "feed_source": item["source_feed"],
            "published": item.get("published", "")
        }
        for item in batch
    ],
    "issue_config": {
        "theme_key": "index",
        "theme_label": "株価指数",
        "status_option_id": "3925acc3",
        ...  # セッションファイルから取得
    }
}, ensure_ascii=False, indent=2)}
""")

    # 結果集約
    all_created.extend(result.get("created_issues", []))
    stats["created"] += result["stats"]["issue_created"]
    stats["failed"] += result["stats"]["issue_failed"]
```

#### issue_config の構築

セッションファイルの `config` とテーマ固有設定を組み合わせて `issue_config` を構築:

```python
issue_config = {
    "theme_key": "index",
    "theme_label": "株価指数",
    "status_option_id": "3925acc3",  # テーマ固有
    "project_id": session_data["config"]["project_id"],
    "project_number": session_data["config"]["project_number"],
    "project_owner": session_data["config"]["project_owner"],
    "repo": "YH-05/finance",
    "status_field_id": session_data["config"]["status_field_id"],
    "published_date_field_id": session_data["config"]["published_date_field_id"]
}
```
```

#### 2.4 処理フロー概要図の更新

**現在**:
```
Phase 4: GitHub投稿（このエージェントが直接実行）
├── URL必須バリデーション
├── 【サブエージェント委譲】news-article-fetcher で記事本文取得・要約生成
│   └── 戻り値: {url, japanese_title, japanese_summary} のみ受け取り
├── Issue作成（gh issue create）
├── Project 15に追加（gh project item-add）
├── Status設定（GraphQL API）
└── 公開日時設定（GraphQL API）
```

**変更後**:
```
Phase 4: バッチ投稿（article-fetcherに委譲）
├── URL必須バリデーション
├── 5件ずつバッチ分割
└── 各バッチ → news-article-fetcher（Sonnet）
    ├── WebFetch → 要約生成
    ├── Issue作成 + close
    ├── Project追加
    ├── Status設定
    └── 公開日時設定
```

---

## Phase 3: 共通処理ガイド更新

### 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `.claude/skills/finance-news-workflow/common-processing-guide.md` | 新フロー反映・バッチ処理セクション追加 |

### 変更内容

#### 3.1 Phase 4セクションの更新

既存のPhase 4（GitHub投稿）セクションを新フローに更新:
- Issue作成の詳細手順 → 「article-fetcherに委譲」に変更
- article-fetcherへの入力データ形式を記載
- バッチ処理フロー（5件ずつ）を記載

#### 3.2 バッチ処理セクションの追加

```markdown
### バッチ処理

コンテキスト使用量を削減するため、記事を5件ずつ `news-article-fetcher` に委譲します。

| パラメータ | 値 |
|-----------|-----|
| バッチサイズ | 5件 |
| 処理順序 | 公開日時の新しい順 |
| 委譲先 | news-article-fetcher（Sonnet） |
| 委譲範囲 | WebFetch + 要約生成 + Issue作成 + Project追加 + Status/Date設定 |

#### バッチ間の状態管理

- 各バッチの結果（created_issues）はテーマエージェント側で集約
- 統計カウンタ（stats）は全バッチで共有
- バッチ失敗時も次のバッチは継続
- 重複チェックはテーマエージェント側（バッチ分割前）に完了済み
```

#### 3.3 article-fetcher入力データ形式の追加

共通処理ガイドに `issue_config` の完全な仕様を追記:

```markdown
### article-fetcher 入力仕様

#### articles[] の必須フィールド

| フィールド | 必須 | 説明 |
|-----------|------|------|
| url | ✅ | 元記事URL（RSSのlinkフィールド） |
| title | ✅ | 記事タイトル |
| summary | ✅ | RSS概要（フォールバック用） |
| feed_source | ✅ | フィード名 |
| published | ✅ | 公開日時（ISO 8601） |

#### issue_config の必須フィールド

| フィールド | 説明 | 例 |
|-----------|------|-----|
| theme_key | テーマキー | `"index"` |
| theme_label | テーマ日本語名 | `"株価指数"` |
| status_option_id | StatusのOption ID | `"3925acc3"` |
| project_id | Project ID | `"PVT_kwHOBoK6AM4BMpw_"` |
| project_number | Project番号 | `15` |
| project_owner | Projectオーナー | `"YH-05"` |
| repo | リポジトリ | `"YH-05/finance"` |
| status_field_id | StatusフィールドID | `"PVTSSF_lAHOBoK6AM4BMpw_zg739ZE"` |
| published_date_field_id | 公開日フィールドID | `"PVTF_lAHOBoK6AM4BMpw_zg8BzrI"` |
```

#### 3.4 重複チェックロジックは変更なし

URL一致チェック + タイトル類似度チェックの2段階は維持。
`is_duplicate()` 関数、`normalize_url()` 関数は変更不要。

#### 3.5 issue_config をセッションファイルから構築する方法の追記

テーマエージェントがセッションファイルから `issue_config` を構築するパターンを追記:

```python
def build_issue_config(session_data: dict, theme_key: str, theme_label: str, status_option_id: str) -> dict:
    """セッションデータからissue_configを構築"""
    config = session_data["config"]
    return {
        "theme_key": theme_key,
        "theme_label": theme_label,
        "status_option_id": status_option_id,
        "project_id": config["project_id"],
        "project_number": config["project_number"],
        "project_owner": config["project_owner"],
        "repo": "YH-05/finance",
        "status_field_id": config["status_field_id"],
        "published_date_field_id": config["published_date_field_id"],
    }
```

---

## Phase 4: オーケストレーター・ルール更新

### 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `.claude/agents/finance-news-orchestrator.md` | セッションファイルにproject設定追加 |
| `.claude/rules/subagent-data-passing.md` | article-fetcher用データ構造追記 |

### 変更内容

#### 4.1 オーケストレーターのセッションファイル拡張

**現在のconfig**:
```json
{
  "config": {
    "project_number": 15,
    "project_owner": "YH-05",
    "days_back": 7
  }
}
```

**拡張後のconfig**:
```json
{
  "config": {
    "project_number": 15,
    "project_owner": "YH-05",
    "days_back": 7,
    "project_id": "PVT_kwHOBoK6AM4BMpw_",
    "status_field_id": "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
    "published_date_field_id": "PVTF_lAHOBoK6AM4BMpw_zg8BzrI"
  }
}
```

**追加フィールド**: `project_id`, `status_field_id`, `published_date_field_id`

**理由**: テーマエージェントがarticle-fetcherに `issue_config` を渡す際に必要。
現在はテーマエージェントにハードコードされているが、セッションファイル経由で一元管理する。

**変更規模**: オーケストレーターの `ステップ3.1: 一時ファイル作成` セクションにフィールドを3つ追加するのみ。

#### 4.2 subagent-data-passing.md の更新

**変更内容**: article-fetcher用の新しいデータ構造を追記。

**追記セクション**:

```markdown
### ルール6: article-fetcherへのデータ渡し

article-fetcherにはIssue作成に必要な全情報を渡すこと:

**必須**: `articles[]` と `issue_config` の両方を含めること。

```json
{
  "articles": [
    {
      "url": "https://...",           // ✅ 必須: 元記事URL
      "title": "...",                 // ✅ 必須: 記事タイトル
      "summary": "...",              // ✅ 必須: RSS概要
      "feed_source": "CNBC - Markets", // ✅ 必須: フィード名
      "published": "2026-01-19T..."   // ✅ 必須: 公開日時
    }
  ],
  "issue_config": {
    "theme_key": "index",             // ✅ 必須: テーマキー
    "theme_label": "株価指数",         // ✅ 必須: テーマ日本語名
    "status_option_id": "3925acc3",   // ✅ 必須: Status設定値
    "project_id": "PVT_...",          // ✅ 必須: Project ID
    "project_number": 15,             // ✅ 必須: Project番号
    "project_owner": "YH-05",        // ✅ 必須: Projectオーナー
    "repo": "YH-05/finance",         // ✅ 必須: リポジトリ
    "status_field_id": "PVTSSF_...",  // ✅ 必須: StatusフィールドID
    "published_date_field_id": "PVTF_..." // ✅ 必須: 公開日フィールドID
  }
}
```
```

#### 4.3 既存Issueデータ構造は変更なし

URL重複チェックを維持するため、既存Issueのデータ構造（`article_url` フィールド含む）は変更しない。

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

---

## 実装順序

| 順序 | Phase | 作業 | 依存 |
|------|-------|------|------|
| 1 | Phase 1 | article-fetcherの拡張（Issue作成統合） | なし |
| 2 | Phase 4 | オーケストレーターにproject設定追加 | なし |
| 3 | Phase 3 | 共通処理ガイドの更新（新フロー・バッチ処理） | 1 |
| 4 | Phase 2 | テーマエージェント6ファイルの軽量化 | 1, 3 |
| 5 | Phase 4 | subagent-data-passing.md更新 | 1 |

**並列実行可能**: 順序1と2は並列実行可能。順序4と5は並列実行可能。

---

## 変更ファイル一覧

| ファイル | 変更種別 | Phase |
|---------|---------|-------|
| `.claude/agents/news-article-fetcher.md` | 大幅修正 | 1 |
| `.claude/agents/finance-news-orchestrator.md` | 軽微修正 | 4 |
| `.claude/agents/finance-news-index.md` | 大幅修正 | 2 |
| `.claude/agents/finance-news-stock.md` | 大幅修正 | 2 |
| `.claude/agents/finance-news-sector.md` | 大幅修正 | 2 |
| `.claude/agents/finance-news-macro.md` | 大幅修正 | 2 |
| `.claude/agents/finance-news-ai.md` | 大幅修正 | 2 |
| `.claude/agents/finance-news-finance.md` | 大幅修正 | 2 |
| `.claude/skills/finance-news-workflow/common-processing-guide.md` | 修正 | 3 |
| `.claude/rules/subagent-data-passing.md` | 追記 | 4 |

**変更なし**: オーケストレーターのURL抽出ロジック、重複チェックロジック（`is_duplicate`）、
テーマ設定ファイル（`finance-news-themes.json`）

---

## 検証方法

### 1. Phase 1 検証（article-fetcher単体）

```bash
# article-fetcherを直接呼び出し、1件のIssue作成を確認
# 入力: 1記事 + issue_config
# 確認: Issue作成・close・Project追加・Status/Date設定
```

### 2. Phase 2 検証（テーマエージェント単体）

```bash
# 軽量化後のテーマエージェント単体での動作確認
/finance-news-workflow --days 1 --themes "index" --dry-run
```

### 3. 統合テスト

```bash
# 全テーマでの動作確認（dry-run）
/finance-news-workflow --days 1 --dry-run
```

### 4. 本番テスト

```bash
# 少量データでの本番実行
/finance-news-workflow --days 1 --themes "index"
```

### 5. 確認項目

- [ ] article-fetcherがIssue作成・Project追加・Status/Date設定を正しく実行する
- [ ] テーマエージェントがコンテキストオーバーなく完了する
- [ ] バッチ処理が正しく動作する（5件ずつarticle-fetcher呼び出し）
- [ ] 重複チェックが正しく動作する（URL一致 + タイトル類似度）
- [ ] 結果レポートが正しく出力される（created_issues集約）
- [ ] 既存の4セクション要約フォーマットが維持される

---

## リスクと対策

| リスク | 対策 |
|--------|------|
| article-fetcherの責務増大でSonnetコスト増 | バッチ5件で呼び出し回数を制限。Haiku時代のWebFetchコストは変わらない |
| article-fetcher内でgh/GraphQL失敗 | 個別記事の失敗は次の記事に影響しない設計。statsで失敗件数を報告 |
| テーマエージェント軽量化で情報不足 | テーマ固有情報（キーワード・判定基準・判定例）は全て残す |
| issue_config の設定ミス | セッションファイルから自動構築。テーマ固有設定のみエージェント内に保持 |
| バッチ間で新規作成Issueとの重複 | 重複チェックはバッチ分割前にテーマエージェント側で完了。バッチ間重複なし |

---

## 期待効果

| 指標 | 現状 | 改善後 |
|------|------|--------|
| テーマエージェント行数 | 539-712行 | 200-300行（57-68%削減） |
| テーマエージェント内のIssue作成コード | 約250行 | 0行（article-fetcherに移管） |
| 1バッチの処理件数 | 全記事（最大50件） | 5件 |
| article-fetcherモデル | Haiku（WebFetch+要約のみ） | Sonnet（+Issue作成） |
| URL重複チェック | ✅ 維持 | ✅ 維持 |
| オーケストレーター変更 | - | 軽微（config 3フィールド追加） |
