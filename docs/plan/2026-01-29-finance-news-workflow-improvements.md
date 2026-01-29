# 金融ニュース収集ワークフロー改善計画

**作成日**: 2026-01-29
**最終更新**: 2026-01-29
**ステータス**: 設計確定

## 背景

2026-01-29 の `/finance-news-workflow` 実行で以下の問題が判明：

1. **Index テーマの Task 委譲失敗**: news-article-fetcher への委譲ができずIssue作成が保留
2. **Stock テーマの本文抽出失敗**: CNBC/Seeking Alpha の動的コンテンツ・ペイウォールで14件失敗
3. **AIエージェントのコンテキスト負荷**: 決定論的処理がAIエージェント内で実行されており非効率

### 実行結果サマリー

| テーマ | 新規Issue | 問題 |
|--------|----------|------|
| Index | 16件保留 | Task委譲失敗 |
| Stock | 0件 | 本文抽出失敗（CNBC動的コンテンツ） |
| Sector | 0件 | 全重複 |
| Macro (CNBC) | 8件 | 正常 |
| Macro (Other) | 6件 | 正常 |
| AI (CNBC) | 4件 | 正常 |
| AI (NASDAQ) | 6件 | 正常 |
| AI (Tech) | 6件 | 正常 |
| Finance (CNBC) | 8件 | 正常 |
| Finance (NASDAQ) | 5件 | 正常 |
| Finance (Other) | 4件 | 正常 |

### 現在のテーマ構成（11テーマ）

Phase 3-4 の簡素化により、元の6テーマから11テーマに分割済み:

| 元テーマ | 分割後 | エージェント数 |
|---------|--------|--------------|
| Index | index | 1 |
| Stock | stock | 1 |
| Sector | sector | 1 |
| Macro | macro_cnbc, macro_other | 2 |
| AI | ai_cnbc, ai_nasdaq, ai_tech | 3 |
| Finance | finance_cnbc, finance_nasdaq, finance_other | 3 |

---

## 確定アーキテクチャ

### 全体構造

```
prepare_news_session.py (Python CLI)
  ├── 既存Issue取得・URL抽出
  ├── RSS取得（全テーマ一括）
  ├── 公開日時フィルタリング
  ├── 重複チェック
  ├── ペイウォール事前チェック（Playwright使用）
  └── セッションファイル出力（.tmp/）

/finance-news-workflow (スキル)
  └── テーマエージェント × 11（並列呼び出し）
        ├── テーマ設定を保持（ラベル、Status Option ID等）
        ├── セッションファイルから自テーマの記事読み込み
        ├── news-article-fetcher に委譲（バッチ）
        │     ├── WebFetch + 要約生成
        │     ├── WebFetch失敗時 → Playwrightフォールバック
        │     ├── Playwright失敗時 → RSS Summaryフォールバック
        │     └── Issue作成 + Project追加
        ├── 結果を受け取り
        └── 取得成功/失敗の件数をログ出力（モニタリング）
```

### コンポーネント役割

| コンポーネント | 役割 |
|---------------|------|
| `prepare_news_session.py` | 決定論的前処理（RSS取得、フィルタリング、重複チェック、ペイウォール事前チェック） |
| テーマエージェント × 11 | 設定保持 + news-article-fetcher委譲 + モニタリング（件数ログ） |
| `news-article-fetcher` | 要約生成 + Issue作成 + Project追加（バッチ処理対応） |

### 廃止対象

| 対象 | ファイル | 理由 |
|------|----------|------|
| オーケストレーター | `.claude/agents/finance-news-orchestrator.md` | Python CLIに移行、ネスト削減 |

---

## Issue 1: Task 委譲の安定化

### 問題

- オーケストレーター → テーマエージェント → news-article-fetcher の3段ネストで不安定
- 一部テーマでTask委譲失敗

### 解決策（確定）

**news-article-fetcher委譲方式を維持しつつ、ネストを削減**

- オーケストレーター廃止 → ネスト1段削減
- スキルからテーマエージェントを直接呼び出し
- テーマエージェント → news-article-fetcher の2段ネストで安定化

### テーマエージェントの役割変更

| 役割 | 変更前 | 変更後 |
|------|--------|--------|
| テーマ設定保持 | ✅ | ✅ |
| RSS取得 | ✅ | ❌（Python CLIへ移動） |
| フィルタリング | ✅ | ❌（Python CLIへ移動） |
| 重複チェック | ✅ | ❌（Python CLIへ移動） |
| 要約生成 | ✅ | ❌（news-article-fetcherへ委譲） |
| Issue作成 | ✅ | ❌（news-article-fetcherへ委譲） |
| モニタリング（件数レポート） | ❌ | ✅（新規、ログ出力） |

---

## Issue 2: 動的コンテンツ・ペイウォール対応

### 問題

| ソース | 問題 | 影響件数 |
|--------|------|---------|
| CNBC | JavaScript で動的にコンテンツを読み込み | 12件 |
| Seeking Alpha | ペイウォール（無料記事もあり） | 2件 |

### 解決策（確定）

**Playwright事前チェック + フォールバック（Option C + D）**

#### Tier構成

```
Tier 1: httpx + trafilatura（高速、静的サイト用）
    ↓ 失敗時
Tier 2: MCP Playwright（動的サイト用）
    ├── mcp__playwright__browser_navigate
    ├── mcp__playwright__browser_snapshot
    └── HTML から本文抽出
    ↓ 失敗時
Tier 3: RSS Summary フォールバック
```

#### Playwright実行タイミング

| タイミング | 場所 | 目的 |
|-----------|------|------|
| 事前チェック | `prepare_news_session.py` | ペイウォール検出、アクセス可否判定 |
| フォールバック | `news-article-fetcher` | WebFetch失敗時の動的コンテンツ取得 |

#### ペイウォール判定基準

- 文章が途中で途切れている
- 有料記事と判断できる特徴（"Subscribe to read", "Premium content" 等のキーワード）

#### RSS Summaryフォールバック時のIssue本文

```markdown
## 概要

{rss_summary}

## 元記事

🔗 {article_url}

## 注意

⚠️ **本文の自動取得に失敗しました**

**失敗理由**: {failure_reason}
（例: ペイウォール検出、動的コンテンツ取得失敗、タイムアウト等）

上記はRSS要約です。詳細は元記事をご確認ください。
```

---

## Issue 3: AIエージェントのコンテキスト負荷削減

### 問題

決定論的処理がAIエージェント内で実行され、コンテキストを消費

| 処理 | 現在の実行場所 | 性質 |
|------|---------------|------|
| 既存Issue取得 | オーケストレーター | **決定論的** |
| RSS取得・フィルタリング | テーマエージェント | **決定論的** |
| 重複チェック | テーマエージェント | **決定論的** |
| 要約生成 | テーマエージェント | **非決定論的（AI必要）** |

### 解決策（確定）

**Python CLI前処理 + オーケストレーター廃止（Option F）**

#### `prepare_news_session.py` の機能

```python
#!/usr/bin/env python3
"""
Finance News Session Preparation Script

決定論的処理をPythonで事前実行し、AIエージェントのコンテキスト負荷を削減。
"""

def main():
    # 1. 既存Issue取得とURL抽出
    existing_issues = get_existing_issues(repo, days_back)
    existing_urls = {normalize_url(i["article_url"]) for i in existing_issues}

    # 2. RSS取得（全テーマ一括）
    items_by_theme = fetch_rss_items(config, days_back)

    # 3. 重複チェック
    for theme_key, items in items_by_theme.items():
        unique, dup_count = check_duplicates(items, existing_urls)

        # 4. ペイウォール事前チェック（Playwright使用）
        accessible, blocked = check_paywall_with_playwright(unique)

        session_data["themes"][theme_key] = {
            "articles": accessible,
            "blocked": blocked,  # 失敗理由付き
            "theme_config": config["themes"][theme_key],
        }

    # 5. セッションファイル出力
    output_path = f".tmp/news-{timestamp}.json"
    Path(output_path).write_text(json.dumps(session_data, ensure_ascii=False, indent=2))
```

#### セッションファイル形式

```json
{
  "session_id": "news-20260129-143000",
  "timestamp": "2026-01-29T14:30:00+09:00",
  "config": {
    "project_id": "PVT_...",
    "project_number": 15,
    "project_owner": "YH-05",
    "status_field_id": "PVTSSF_...",
    "published_date_field_id": "PVTF_..."
  },
  "themes": {
    "index": {
      "articles": [
        {
          "url": "https://...",
          "title": "...",
          "summary": "...",
          "feed_source": "CNBC - Markets",
          "published": "2026-01-29T12:00:00+00:00"
        }
      ],
      "blocked": [
        {
          "url": "https://...",
          "title": "...",
          "summary": "...",
          "reason": "ペイウォール検出"
        }
      ],
      "theme_config": {
        "name_ja": "株価指数",
        "github_status_id": "3925acc3"
      }
    }
  },
  "stats": {
    "total": 45,
    "duplicates": 12,
    "paywall_blocked": 5,
    "accessible": 28
  }
}
```

#### 効果

| 項目 | 現状 | 改善後 |
|------|------|--------|
| オーケストレーター | 必要（AI） | **廃止** |
| テーマエージェントの処理 | RSS取得+フィルタリング+重複チェック+要約+Issue作成 | **委譲+モニタリングのみ** |
| news-article-fetcherの処理 | 単発処理 | **バッチ処理（要約+Issue作成）** |
| コンテキスト使用量 | 既存Issue500件+RSS記事+処理ロジック | **投稿対象記事のみ** |
| Taskネスト | 3段（不安定） | **2段（安定）** |

---

## 対象ファイル一覧

### 新規作成

| ファイル | 説明 |
|----------|------|
| `scripts/prepare_news_session.py` | 決定論的前処理スクリプト |

### 更新対象

| ファイル | 変更内容 |
|----------|----------|
| `.claude/agents/finance-news-*.md` × 11 | 軽量化（設定保持+委譲+モニタリング） |
| `.claude/agents/news-article-fetcher.md` | バッチ処理対応、Playwrightフォールバック追加 |
| `.claude/skills/finance-news-workflow/SKILL.md` | オーケストレーター呼び出し → テーマエージェント直接呼び出し |
| `src/rss/article_content_checker.py` | Playwright統合、ペイウォール判定強化 |

### 廃止対象

| ファイル | 理由 |
|----------|------|
| `.claude/agents/finance-news-orchestrator.md` | Python CLIに役割移行 |

---

## 実装優先度

| 優先度 | 項目 | Issue | ステータス |
|--------|------|-------|----------|
| **P0** | Python CLI前処理 `prepare_news_session.py` | #1920 | 🆕 設計確定 |
| **P1** | テーマエージェント軽量化 + news-article-fetcher委譲 | #1921 | 🆕 設計確定 |
| **P2** | RSS Summary フォールバック | #1922 | 🆕 設計確定 |
| **P3** | Playwright統合（事前チェック + フォールバック） | #1853 | ⏳ 待機 |

---

## 関連 Issue

### 新規作成（2026-01-29）

- **#1920**: 決定論的前処理スクリプト prepare_news_session.py の実装
- **#1921**: テーマ別エージェントの軽量化とnews-article-fetcher委譲方式への統一
- **#1922**: 本文取得失敗時の RSS Summary フォールバック実装

### 既存

- #1855: ワークフロー処理の簡素化
- #1854: バックグラウンドエージェントのタイムアウト対策
- #1853: Tier 1 失敗時の自動フォールバック実装（Playwright統合）
- #1852: article_content_checker の閾値緩和

### GitHub Project

- **Project #26**: finance-news-workflow 改善
- URL: https://github.com/users/YH-05/projects/26

---

## 次のアクション

### Phase 1: 前処理スクリプト作成（#1920）

1. [ ] `scripts/prepare_news_session.py` の新規作成
   - 既存Issue取得・URL抽出
   - RSS取得・公開日時フィルタリング
   - 重複チェック
   - セッションファイル出力（.tmp/）

### Phase 2: エージェント軽量化（#1921）

2. [ ] テーマエージェント × 11 の軽量化
   - 設定保持 + news-article-fetcher委譲 + モニタリング
3. [ ] news-article-fetcher のバッチ処理対応
4. [ ] オーケストレーター廃止
5. [ ] スキルからテーマエージェント直接呼び出しに変更

### Phase 3: フォールバック実装（#1922, #1853）

6. [ ] RSS Summary フォールバック実装
   - Issue本文: RSS要約 + 失敗理由 + 元記事リンク
7. [ ] Playwright統合
   - `prepare_news_session.py` でペイウォール事前チェック
   - `news-article-fetcher` でWebFetch失敗時フォールバック
   - 判定基準: 文章途中切れ、有料記事キーワード検出

### Phase 4: 検証・最適化

8. [ ] 全11テーマで動作確認
9. [ ] パフォーマンス計測と最適化
