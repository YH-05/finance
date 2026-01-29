# 金融ニュース収集ワークフロー改善計画

**作成日**: 2026-01-29
**最終更新**: 2026-01-29
**ステータス**: 実装中

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

## Issue 1: Task 委譲の不安定性

### 現状

- エージェント定義では `news-article-fetcher` への Task 委譲を設計
- 実行時に一部エージェント（Index）で Task ツールが利用できず保留
- 他のエージェント（Macro, AI, Finance）は直接 `gh issue create` を実行して成功

### 実装状況

| 項目 | 状態 |
|------|------|
| `news-article-fetcher` エージェント | 存在（`.claude/agents/news-article-fetcher.md`） |
| テーマエージェントの Task 委譲設計 | 定義に残存 |
| 直接実行方式への移行 | **未完了** |

### 原因分析

1. **ネストした Task 呼び出しの制限**: サブエージェントがさらにサブエージェントを呼び出す際の制限
2. **LLM 判断のばらつき**: 同じ定義でもエージェントごとに異なる実行パスを選択

### 改善案

#### Option A: 直接実行方式に統一（推奨）

`news-article-fetcher` への委譲をやめ、各テーマエージェントが直接 Issue 作成を実行。

**メリット**:
- シンプルな処理フロー
- ネスト制限を回避
- 実績あり（Macro, AI, Finance で成功）

**デメリット**:
- 各エージェント定義にIssue作成ロジックが重複
- WebFetch + 要約生成の処理が各エージェントに分散

**変更内容**:
```markdown
# finance-news-index.md の Phase 4 を変更

Phase 4: Issue作成（直接実行）
├── WebFetch で記事本文取得
├── 日本語要約生成
├── gh issue create 実行
├── gh project item-add 実行
└── Status/Date フィールド設定
```

#### Option B: 委譲を維持しつつ信頼性向上

`news-article-fetcher` 委譲を維持しつつ、フォールバック処理を追加。

**メリット**:
- 処理ロジックを一元管理
- 共通処理の再利用

**デメリット**:
- 複雑な制御フロー
- ネスト制限の根本解決にならない

**変更内容**:
```markdown
Phase 4: バッチ投稿（フォールバック付き）
├── Task(news-article-fetcher) 試行
├── 失敗時 → 直接 gh issue create にフォールバック
└── 結果をマージして報告
```

### 推奨

**Option A（直接実行方式）** を推奨。理由：
- Macro, AI, Finance で実績あり
- シンプルで予測可能な動作
- メンテナンスコストが低い

### 実装アクション

1. [ ] 各テーマエージェント定義から `news-article-fetcher` への Task 委譲を削除
2. [ ] 直接 `gh issue create` を実行するフローに統一
3. [ ] `news-article-fetcher.md` の削除または非推奨化

---

## Issue 2: CNBC 動的コンテンツの本文抽出

### 現状

Stock テーマで以下の問題が発生：

| ソース | 問題 | 影響件数 |
|--------|------|---------|
| CNBC | JavaScript で動的にコンテンツを読み込み | 12件 |
| Seeking Alpha | ペイウォール | 2件 |

trafilatura（現在の本文抽出ライブラリ）は静的 HTML のみ対応。

### 失敗した記事例

- Samsung's profit triples, beating estimates as AI chip demand fuels memory shortage
- Microsoft stock drops 7% on slowing cloud growth
- IBM jumps 8% on earnings beat
- Meta shares jump 10% on stronger-than-expected revenue forecast
- Chip giant ASML surges 7% as AI boom fuels record orders

### 改善案

#### Option C: Playwright ヘッドレスブラウザ導入

MCP Playwright サーバーを活用して動的コンテンツを取得。

**実装方針**:
```python
# article_content_checker.py の Tier 構成を拡張

Tier 1: httpx + trafilatura（高速、静的サイト用）
    ↓ 失敗時
Tier 2: MCP Playwright（動的サイト用）
    ├── mcp__playwright__browser_navigate
    ├── mcp__playwright__browser_snapshot
    └── HTML から本文抽出
    ↓ 失敗時
Tier 3: WebFetch（フォールバック）
```

**対象サイト**:
- cnbc.com（動的コンテンツ）
- bloomberg.com（一部動的）
- その他 JavaScript 依存サイト

**メリット**:
- JavaScript 実行後のコンテンツ取得可能
- ペイウォール回避（一部）
- 既存 MCP インフラを活用

**デメリット**:
- 処理時間増加（ブラウザ起動オーバーヘッド）
- リソース消費増加

#### Option D: RSS Summary ベース簡易 Issue

本文取得できない場合、RSS の summary 情報で簡易 Issue を作成。

**実装方針**:
```python
# 本文取得失敗時のフォールバック

if content_extraction_failed:
    issue_body = f"""
## 概要
{rss_summary}

## 元記事
🔗 {article_url}

⚠️ 本文の自動取得に失敗したため、RSS 要約を表示しています。
"""
```

**メリット**:
- 情報の取り漏れを防止
- 実装が簡単

**デメリット**:
- 要約品質が RSS 依存
- 詳細情報が不足

#### Option E: 代替フィード追加

CNBC の代わりに静的コンテンツを提供するソースを追加。

**候補フィード**:
- Yahoo Finance（静的）
- Reuters（静的）
- Investing.com（静的）

**メリット**:
- 抽出成功率向上
- 多様なソースからの情報収集

**デメリット**:
- フィード管理の複雑化
- 重複記事の増加

### 推奨

**Option C + D の組み合わせ** を推奨：
1. Playwright で動的サイト対応（優先度高いニュース）
2. 失敗時は RSS Summary で簡易 Issue（情報取り漏れ防止）

---

## Issue 3: AIエージェントのコンテキスト負荷削減

### 現状の問題

現在、以下の決定論的処理がAIエージェント内で実行されており、コンテキストを消費している:

| 処理 | 現在の実行場所 | 性質 |
|------|---------------|------|
| 既存Issue取得 (`gh issue list`) | オーケストレーター | **決定論的** |
| Issue本文からURL抽出 | オーケストレーター | **決定論的** |
| セッションファイル作成 | オーケストレーター | **決定論的** |
| RSSフィード取得 | テーマ別エージェント | **決定論的** |
| 公開日時フィルタリング | テーマ別エージェント | **決定論的** |
| URL重複チェック | テーマ別エージェント | **決定論的** |
| URL正規化 | テーマ別エージェント | **決定論的** |
| Issue作成・Project追加 | テーマ別エージェント | **決定論的** |

### AIエージェントが担当すべき処理

| 処理 | 性質 |
|------|------|
| 記事本文の要約生成 | **非決定論的（AI必要）** |
| 記事の関連性判定（テーマ分類） | **非決定論的（AI必要）** |

### 改善案

#### Option F: Python CLIによる前処理パイプライン（推奨）

決定論的処理をPythonスクリプトに移行し、AIエージェントは要約生成のみに特化させる。

**アーキテクチャ変更**:

```
[現状]
/finance-news-workflow
  → オーケストレーター（AI）
      → 既存Issue取得、URL抽出、セッション作成
  → テーマ別エージェント（AI）×11
      → RSS取得、フィルタリング、重複チェック
      → WebFetch、要約、Issue作成

[改善後]
scripts/prepare_news_session.py（Python CLI）
  → 既存Issue取得、URL抽出
  → RSS取得（全テーマ一括）
  → 公開日時フィルタリング
  → URL重複チェック
  → ペイウォール事前チェック
  → セッションファイル作成（投稿対象記事リスト付き）

/finance-news-workflow
  → テーマ別エージェント（AI）×11【軽量化】
      → セッションファイルから投稿対象記事を読み込み
      → 要約生成のみ（WebFetch → 要約）
      → Issue作成（テンプレート埋め込み）
```

**`scripts/prepare_news_session.py` の主要機能**:

```python
#!/usr/bin/env python3
"""
Finance News Session Preparation Script

決定論的処理をPythonで事前実行し、AIエージェントのコンテキスト負荷を削減。
"""

def main():
    # 1. 既存Issue取得とURL抽出
    existing_issues = get_existing_issues(repo, days_back)
    existing_urls = {normalize_url(i["article_url"]) for i in existing_issues if i["article_url"]}

    # 2. RSS取得（全テーマ一括）
    items_by_theme = fetch_rss_items(config, days_back)

    # 3. 重複チェック
    for theme_key, items in items_by_theme.items():
        unique, dup_count = check_duplicates(items, existing_urls)

        # 4. ペイウォール事前チェック
        accessible, blocked = check_paywall(unique)

        session_data["themes"][theme_key] = {
            "articles": accessible,  # 投稿対象のみ
            "theme_config": config["themes"][theme_key],
        }

    # 5. セッションファイル出力
    Path(output_path).write_text(json.dumps(session_data, ensure_ascii=False, indent=2))
```

**セッションファイル形式（改善後）**:

```json
{
  "session_id": "news-20260129-143000",
  "timestamp": "2026-01-29T14:30:00+09:00",
  "config": { ... },
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
      "theme_config": {
        "name_ja": "株価指数",
        "github_status_id": "3925acc3"
      }
    }
  },
  "stats": {
    "total": 45,
    "duplicates": 12,
    "paywall_blocked": 5
  }
}
```

**メリット**:

| 項目 | 現状 | 改善後 |
|------|------|--------|
| オーケストレーター | 必要 | **不要**（Pythonスクリプトに移行） |
| テーマエージェントの処理 | RSS取得+フィルタリング+重複チェック+要約+Issue作成 | **要約生成のみ** |
| コンテキスト使用量 | 既存Issue500件+RSS記事+処理ロジック | **投稿対象記事のみ** |
| 処理時間 | 全てAI処理 | 前処理Pythonで高速化 |
| エラー耐性 | AI判断に依存 | 決定論的処理は確実 |
| 再実行性 | 全処理やり直し | セッションファイルから再開可能 |

**デメリット**:

- Pythonスクリプトの新規作成が必要
- 2段階実行（Python → AI）のオーケストレーションが必要

### 実装フェーズ

#### Phase 1: `prepare_news_session.py` 作成（高優先）

```bash
uv run python scripts/prepare_news_session.py --days 7 --themes all
```

出力:
```json
{
  "session_file": ".tmp/news-20260129-143000.json",
  "stats": {
    "total": 45,
    "duplicates": 12,
    "paywall_blocked": 5
  }
}
```

#### Phase 2: テーマ別エージェント簡素化

処理フローを以下に変更:

```
Phase 1: セッションファイル読み込み
├── .tmp/{session_id}.json から articles を取得
└── 投稿対象記事のみ（重複・ペイウォール除外済み）

Phase 2: 要約生成（AI処理）
├── WebFetch で記事本文取得
└── 日本語要約生成（400字）

Phase 3: Issue作成（決定論的）
├── テンプレートに埋め込み
├── gh issue create
├── Project追加・Status設定
└── 公開日時設定
```

#### Phase 3: オーケストレーター廃止（オプション）

Pythonスクリプトが安定したら、`finance-news-orchestrator` を廃止。
`/finance-news-workflow` スキルで直接 Python スクリプトを呼び出す。

---

## 実装優先度

| 優先度 | 項目 | 工数 | 効果 | ステータス |
|--------|------|------|------|----------|
| **P0** | Option F: Python CLI前処理 | 中 | **最大** | 🆕 新規 |
| P1 | Option A: 直接実行方式 | 小 | 高 | 🔄 実装中 |
| P2 | Option D: RSS Summary フォールバック | 小 | 中 | ⏳ 待機 |
| P3 | Option C: Playwright 導入 | 中 | 高 | ⏳ 待機 |
| P4 | Option E: 代替フィード追加 | 小 | 中 | ⏳ 待機 |

### 推奨実装順序

```
Phase 1（即時）
├── Option F-Phase1: prepare_news_session.py 作成
└── Option A: 直接実行方式への統一

Phase 2（短期）
├── Option F-Phase2: テーマ別エージェント簡素化
└── Option D: RSS Summary フォールバック

Phase 3（中期）
├── Option F-Phase3: オーケストレーター廃止
└── Option C: Playwright 導入
```

---

## 関連 Issue

### 新規作成（2026-01-29）

- **#1920**: 決定論的前処理スクリプト prepare_news_session.py の実装（Option F-Phase1）
- **#1921**: テーマ別エージェントの直接実行方式への統一（Option A）
- **#1922**: 本文取得失敗時の RSS Summary フォールバック実装（Option D）

### 既存

- #1855: ワークフロー処理の簡素化
- #1854: バックグラウンドエージェントのタイムアウト対策
- #1853: Tier 1 失敗時の自動フォールバック実装（Option C関連）
- #1852: article_content_checker の閾値緩和

### GitHub Project

- **Project #26**: finance-news-workflow 改善
- URL: https://github.com/users/YH-05/projects/26

---

## 次のアクション

### 即時対応（P0-P1）

1. [ ] **Option F-Phase1**: `scripts/prepare_news_session.py` の新規作成
   - 既存Issue取得・URL抽出
   - RSS取得・公開日時フィルタリング
   - 重複チェック・ペイウォール事前チェック
   - セッションファイル出力

2. [ ] **Option A**: 各テーマエージェントから `news-article-fetcher` への Task 委譲を削除
   - 直接 Issue 作成に統一
   - `news-article-fetcher.md` の非推奨化

### 短期対応（P2）

3. [ ] **Option F-Phase2**: テーマ別エージェント簡素化
   - セッションファイルから投稿対象記事を読み込み
   - 要約生成とIssue作成に特化

4. [ ] **Option D**: RSS Summary フォールバック実装
   - 本文取得失敗時のフォールバック処理

### 中期対応（P3）

5. [ ] **Option F-Phase3**: オーケストレーター廃止
   - `/finance-news-workflow` スキルで直接 Python スクリプト呼び出し

6. [ ] **Option C**: Playwright 統合
   - 動的コンテンツ対応

7. [ ] パフォーマンス計測と最適化
