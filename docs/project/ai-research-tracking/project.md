# AI先端研究トラッキング体制

**Project**: TBD（GitHub Project未作成）
**Status**: Planning
**Created**: 2026-02-10
**Type**: workflow

## 背景と目的

### 背景

- **種類**: ワークフロー（新規構築）
- **課題**: AI研究の進展が投資判断に大きな影響を持つが、論文・企業リリースを体系的にトラッキングする仕組みがない
- **参照**: 既存の金融ニュース収集体制（`/finance-news-workflow`）の3フェーズアーキテクチャを踏襲

### 目的

1. arXiv論文 + AI企業ブログ/リリースを自動収集し、GitHub Issueとして登録する
2. 堅牢なWebスクレイピング基盤（RobustScraper）をbot検知対策・レートリミット対策込みで構築する
3. Python側で決定論的処理を完結させ、AI側は要約・重要度判定のみに限定する

### ユーザー要件

| 項目 | 決定 |
|------|------|
| スコープ | コアのみ（論文 + 企業リリース） |
| GitHub Project | 完全に独立した新Project |
| arXiv取得方法 | arXiv API（専用Pythonスクリプト） |
| MVP優先機能 | データ収集パイプライン |
| 企業ブログ取得 | RSS対応→FeedReader、非対応→RobustScraper |
| OSS追跡 | Phase 2以降 |
| レポート頻度 | 週次（MVP後に日次検討） |
| 記事読者 | 投資家向け |

---

## アーキテクチャ

### 全体構成

```
/ai-research-collect
  → ai-research-workflow スキル
    → Phase 1: Python CLI (prepare_ai_research_session.py)
        ├── arXiv API（feedparserでAtom解析）
        ├── 企業ブログRSS（FeedReader）
        └── RSS非対応サイト（RobustScraper）
            ├── 7種UAローテーション（直前UA回避）
            ├── ドメイン別レートリミット（asyncio.Lock排他制御）
            ├── 429リトライ（Retry-After対応、指数バックオフ2→4→8秒）
            └── 3段階フォールバック: trafilatura → Playwright → lxml
    → Phase 2: AI（ai-research-article-fetcher × 並列）
        └── 要約生成 + 重要度判定 + Issue作成のみ
    → Phase 3: 結果集約 + スクレイピング統計レポート
```

### Python → AI 役割分担

| Python側（決定論的） | AI側（高度判断） |
|---------------------|-----------------|
| arXiv API呼び出し | タイトル翻訳（英→日） |
| RSSフィード取得 | 4セクション要約生成 |
| Webスクレイピング（RobustScraper） | 重要度判定（low/medium/high） |
| 日付フィルタリング | Issue本文の文章構成 |
| URL + arXiv IDベース重複チェック | |
| Top-N選択（公開日時降順） | |
| テーマ別JSON出力 | |
| スクレイピング統計レポート | |

### データフロー

```
ユーザー: /ai-research-collect --days 7 --themes all --top-n 10
  │
  ▼ Phase 1 (Python)
  prepare_ai_research_session.py
    ├── arXiv API → 論文メタデータ+アブストラクト
    ├── FeedReader → 企業ブログRSS記事
    ├── RobustScraper → RSS非対応企業ブログ記事（本文含む）
    ├── → ArticleData統一形式に変換
    ├── → 既存Issue URL抽出（重複チェック用）
    ├── → 日付フィルタ → 重複チェック → Top-N選択
    └── → .tmp/ai-research-batches/{theme_key}.json 出力
  │
  ▼ Phase 2 (AI)
  ai-research-article-fetcher × テーマ数（並列）
    ├── タイトル翻訳
    ├── 4セクション要約生成（概要/手法/結果/意義）
    ├── 重要度判定
    ├── Issue作成（gh issue create + close）
    ├── ラベル付与（ai-research + needs-review）
    └── GitHub Project追加 + Status/Date設定
  │
  ▼ Phase 3 (集約)
  テーマ別統計 + スクレイピング統計（ScrapeStats）サマリー
```

---

## コンポーネント詳細

### 1. RobustScraper クラス

**パス**: `src/rss/services/robust_scraper.py`

既存の `ArticleExtractor` をコンポジションでラップし、bot検知対策・レートリミット対策・テキスト抽出対策を統合する堅牢なWebスクレイピングモジュール。

#### インターフェース

```python
class RobustScraper:
    async def scrape(self, url: str) -> ScrapedArticle: ...
    async def scrape_batch(self, urls: list[str]) -> list[ScrapedArticle]: ...
    def get_stats(self) -> ScrapeStats: ...
```

#### 設定

```python
RobustScraper(
    domain_rate_limits: dict[str, float],  # ドメイン別レートリミット（秒）
    user_agents: list[str],                 # UAプール
    max_retries: int = 3,                   # 最大リトライ回数
    use_playwright: bool = True,            # Playwrightフォールバック有効化
)
```

#### UA ローテーション

7種類のリアルブラウザUA（Chrome 3 + Firefox 2 + Safari 1 + Edge 1）をリクエストごとにランダム選択。直前UAを記録して回避。

| # | ブラウザ | OS |
|---|---------|------|
| 1 | Chrome 120 | macOS |
| 2 | Chrome 121 | Windows |
| 3 | Chrome 119 | Linux |
| 4 | Firefox 121 | macOS |
| 5 | Firefox 122 | Windows |
| 6 | Safari 17.2 | macOS |
| 7 | Edge 120 | Windows |

#### ドメイン別レートリミット

`asyncio.Lock` + `last_access_time` 辞書でドメイン別排他制御。

| ドメイン | 間隔（秒） |
|---------|-----------|
| arxiv.org | 3.0 |
| openai.com | 5.0 |
| blog.google | 5.0 |
| ai.meta.com | 5.0 |
| anthropic.com | 5.0 |
| huggingface.co | 3.0 |
| www.microsoft.com | 5.0 |
| `__default__` | 2.0 |

#### 429リトライ戦略

- **Retry-Afterヘッダ**: あればその値（秒）をwait
- **指数バックオフ**: なければ 2秒 → 4秒 → 8秒
- **最大リトライ**: 3回
- **超過時**: `ScrapeStatus.RATE_LIMITED` で返却
- **その他リトライ対象**: 5xx、ConnectionError、TimeoutException

#### 3段階テキスト抽出フォールバック

| Stage | 手法 | 特徴 | 所要時間 |
|-------|------|------|---------|
| 1 | trafilatura | 高速・軽量、多くのサイトに対応 | 0.5-2秒 |
| 2 | Playwright headless | JS-heavy SPA対応 | 3-5秒 |
| 3 | lxml直接解析 | 最終手段、JS非対応 | 0.5-1秒 |

- 成功条件: テキスト長 >= 100文字
- Stage 2はオプショナル（`use_playwright=False` でスキップ）
- Playwright未インストール時は自動スキップ

#### リクエストヘッダ

```
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.9,ja;q=0.8
Accept-Encoding: gzip, deflate, br
Referer: https://www.google.com/
DNT: 1
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: cross-site
User-Agent: <ローテーション>
```

#### データ型

```python
@dataclass
class ScrapedArticle:
    url: str
    title: str | None
    text: str | None
    author: str | None
    date: str | None
    source: str | None
    language: str | None
    status: ScrapeStatus
    error: str | None
    extraction_method: str          # trafilatura / playwright / lxml
    retry_count: int
    user_agent_used: str

class ScrapeStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    PAYWALL = "PAYWALL"
    PLAYWRIGHT_REQUIRED = "PLAYWRIGHT_REQUIRED"

@dataclass
class ScrapeStats:
    total_requests: int
    success_count: int
    failed_count: int
    rate_limited_count: int
    timeout_count: int
    paywall_count: int
    domain_stats: dict[str, DomainStats]
    fallback_stats: dict[str, int]      # trafilatura/playwright/lxml 使用回数
    avg_response_time_ms: float
    total_retries: int

@dataclass
class DomainStats:
    domain: str
    requests: int
    success: int
    failed: int
    rate_limited: int
    avg_response_time_ms: float
```

### 2. prepare_ai_research_session.py

**パス**: `scripts/prepare_ai_research_session.py`

`prepare_news_session.py` をフォーク・拡張。3種類のデータソースを統一処理。

**引数**: `--days <int>` `--themes <string>` `--top-n <int>` `--output <path>`

**処理フロー**:
1. `ai-research-themes.json` 読み込み
2. テーマ別にデータ収集:
   - `arxiv_categories[]` → arXiv API呼び出し（feedparser）
   - `feeds[]` → FeedReader
   - `scrape_urls[]` → RobustScraper.scrape_batch()
3. 全データを ArticleData 統一形式に変換
4. 既存GitHub Issue URL抽出（重複チェック用）
5. 日付フィルタリング → URL + arXiv ID 重複チェック → Top-N選択
6. テーマ別JSON出力（`.tmp/ai-research-batches/`）
7. スクレイピング統計出力（RobustScraper.get_stats()）

### 3. ai-research-themes.json

**パス**: `data/config/ai-research-themes.json`

```json
{
  "themes": {
    "papers_llm": {
      "label": "LLM論文",
      "arxiv_categories": ["cs.CL"],
      "feeds": [],
      "scrape_urls": []
    },
    "papers_ml": {
      "label": "ML論文",
      "arxiv_categories": ["cs.AI", "cs.LG"],
      "feeds": [],
      "scrape_urls": []
    },
    "company_openai": {
      "label": "OpenAI",
      "arxiv_categories": [],
      "feeds": ["openai-blog"],
      "scrape_urls": [],
      "scraper_overrides": { "use_playwright": true }
    },
    "company_google": {
      "label": "Google AI",
      "arxiv_categories": [],
      "feeds": ["google-ai-blog"],
      "scrape_urls": []
    },
    "company_meta": {
      "label": "Meta AI",
      "arxiv_categories": [],
      "feeds": [],
      "scrape_urls": ["https://ai.meta.com/blog/"]
    },
    "company_anthropic": {
      "label": "Anthropic",
      "arxiv_categories": [],
      "feeds": ["anthropic-blog"],
      "scrape_urls": []
    }
  },
  "default_scraper_config": {
    "domain_rate_limits": {
      "arxiv.org": 3.0,
      "openai.com": 5.0,
      "blog.google": 5.0,
      "ai.meta.com": 5.0,
      "anthropic.com": 5.0,
      "__default__": 2.0
    },
    "max_retries": 3,
    "use_playwright": true
  },
  "project": { "...": "GitHub Project設定（ID, フィールドID等）" },
  "execution": {
    "batch_size": 5,
    "max_articles_per_theme": 10
  }
}
```

### 4. ai-research-article-fetcher エージェント

**パス**: `.claude/agents/ai-research-article-fetcher.md`

データ収集済みの記事データを受け取り、AI判断処理のみを実行。

**入力**: `{articles: [ArticleData], issue_config: {...}}`

**処理**:
1. タイトル翻訳（英→日）
2. 4セクション要約生成（概要 / 手法・アプローチ / 主要結果 / 意義・影響）
3. 重要度判定（low / medium / high）
4. Issue本文生成 + 作成（`gh issue create` + close）
5. ラベル付与（`ai-research` + `needs-review`）
6. GitHub Project追加 + Status/Date設定

**出力**: `{created_issues: [...], skipped: [...], stats: {...}}`

### 5. ai-research-workflow スキル

**パス**: `.claude/skills/ai-research-workflow/`

3フェーズワークフローのオーケストレーション定義。

### 6. /ai-research-collect コマンド

**パス**: `.claude/commands/ai-research-collect.md`

```
/ai-research-collect [--days 7] [--themes all] [--top-n 10]
```

---

## ファイルマップ

### Wave 0: RobustScraper（TDD実装）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `src/rss/services/robust_scraper.py` | 15KB |
| 新規 | `tests/rss/unit/services/test_robust_scraper.py` | 18KB |
| 修正 | `src/rss/services/__init__.py` | - |

**TDD計画**（12ステップ）:

1. Red: ScrapedArticle/ScrapeStatus/ScrapeStats データクラスのテスト → Green: データクラス実装
2. Red: RobustScraper初期化テスト（デフォルト値、カスタム値） → Green: `__init__` 実装
3. Red: `scrape()` で trafilatura 成功時のテスト → Green: `scrape()` Stage 1 実装
4. Red: UAローテーションテスト（ランダム選択、直前UA回避） → Green: `_select_user_agent()` 実装
5. Red: リクエストヘッダテスト（必須ヘッダ存在確認） → Green: `_build_headers()` 実装
6. Red: ドメイン別レートリミットテスト（待機時間検証） → Green: `_wait_for_rate_limit()` 実装
7. Red: 429リトライテスト（Retry-After有無、指数バックオフ） → Green: `_handle_429()` 実装
8. Red: Stage 2（Playwright）フォールバックテスト → Green: `_try_playwright()` 実装
9. Red: Stage 3（lxml）フォールバックテスト → Green: Stage 3 実装
10. Red: `scrape_batch()` テスト（複数URL、ドメイン混在） → Green: `scrape_batch()` 実装
11. Red: `get_stats()` 統計テスト → Green: 統計追跡・レポート実装
12. Refactor: 全テスト通過確認後、コード整理

### Wave 1: 基盤ファイル（Wave 0 完了後）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `data/config/ai-research-themes.json` | 5KB |
| 新規 | `scripts/prepare_ai_research_session.py` | 22KB |
| 新規 | `.claude/agents/ai-research-article-fetcher.md` | 7KB |
| 修正 | `data/raw/rss/feeds.json` | - |

### Wave 2: スキル定義・テンプレート（Wave 1 完了後）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `.claude/skills/ai-research-workflow/SKILL.md` | 8KB |
| 新規 | `.claude/skills/ai-research-workflow/guide.md` | 8KB |
| 新規 | `.claude/skills/ai-research-workflow/templates/issue-template.md` | 4KB |
| 新規 | `.claude/skills/ai-research-workflow/templates/summary-template.md` | 4KB |

### Wave 3: コマンド定義（Wave 2 完了後）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `.claude/commands/ai-research-collect.md` | 1KB |

### Wave 4: ドキュメント更新（全完了後）

| 操作 | ファイル |
|------|---------|
| 修正 | `CLAUDE.md`（コマンド/スキル/エージェント一覧に追加） |

---

## 見積もり

| Wave | 内容 | 見積もり |
|------|------|---------|
| Wave 0 | RobustScraper TDD実装 + テスト | 3-4時間 |
| Wave 1 | 基盤ファイル（themes.json, スクリプト, エージェント, RSS） | 4-5時間 |
| Wave 2 | スキル定義 + テンプレート | 2-3時間 |
| Wave 3 | コマンド定義 | 30分 |
| Wave 4 | CLAUDE.md更新 | 30分 |
| その他 | RSSフィード存在確認 + GitHub Project作成 | 1-2時間 |
| **合計** | | **11-14時間** |

---

## リスク分析

| リスク | レベル | 軽減策 |
|--------|--------|--------|
| RobustScraperの非同期制御の複雑さ | **高** | TDDで各機能を個別テスト、独立メソッド切り出し |
| Playwright統合の安定性 | 中 | オプショナル化 + timeout設定 + 未インストール時スキップ |
| 企業ブログのWAF強化 | 中 | 多層防御（UA+ヘッダ+レート+Playwright）+ 運用フォールバック |
| テストのモック複雑さ | 中 | 独立メソッド切り出し + conftest.pyフィクスチャ |
| arXiv APIレート制限/形式変更 | 中 | domain_rate_limits遵守 + パーステスト |
| 企業ブログRSS廃止 | 中 | 2段構え（RSS → scrape_urlsフォールバック） |
| Wave 0がWave 1のブロッカー | 中 | 段階的実装（最低限のscrape()でWave 1並行開始可） |
| 既存ワークフローへの影響 | 低 | コンポジション（既存変更なし）+ カテゴリ分離 |
| GitHub Project作成 | 低 | 手動作成 + ID後置換 |

---

## 既存コードの再利用

### 直接再利用

- `src/rss/services/article_extractor.py` - RobustScraperのStage 1として
- `src/rss/services/article_content_checker.py` - Playwrightロジック参照
- `src/rss/core/http_client.py` - バックオフ計算パターン
- `src/rss/services/feed_reader.py` - RSSフィード読み込み
- `src/rss/utils/url_normalizer.py` - URL正規化
- `scripts/prepare_news_session.py` - フィルタリング/重複チェック関数

### フォーク＆修正

- `prepare_news_session.py` → `prepare_ai_research_session.py`
- `news-article-fetcher.md` → `ai-research-article-fetcher.md`
- `finance-news-workflow/SKILL.md` → `ai-research-workflow/SKILL.md`
- `finance-news-themes.json` → `ai-research-themes.json`

### 新規実装

- **RobustScraper** クラス全体（UA+レートリミット+429+フォールバック+統計）
- **データクラス**: ScrapedArticle, ScrapeStatus, ScrapeStats, DomainStats
- **arXiv API** 呼び出し + Atom解析
- **ArticleData統一変換**: arXiv/RSS/RobustScraper → 共通形式
- **arXiv IDベース重複チェック**
- **AI研究向け4セクション要約**（概要/手法/結果/意義）
- **重要度判定ロジック**

---

## GitHub Project セットアップ（実装前の手動作業）

```bash
# 1. Project作成
gh project create --owner YH-05 --title 'AI Research Tracking'

# 2. Statusフィールドにオプション追加
#    - Paper
#    - Company Release

# 3. Published Dateカスタムフィールド追加

# 4. 取得したIDを ai-research-themes.json に反映
```

---

## MVPスコープ

### 含む

- RobustScraperクラス（UA+レートリミット+429+フォールバック+統計）
- RobustScraperの単体テスト（80%以上カバレッジ）
- arXiv API論文取得（cs.AI, cs.CL, cs.LG）
- 企業ブログRSS取得
- RSS非対応企業ブログのWebスクレイピング（RobustScraperベース）
- ArticleData統一形式変換
- 日付フィルタリング + 重複チェック + Top-N選択
- AI要約生成 + Issue作成
- GitHub Project連携
- `/ai-research-collect` コマンド
- スクレイピング統計レポート

### Phase 2以降（除外）

- OSSリリース・ベンチマーク追跡
- Semantic Scholar API連携
- GitHub Trending / HuggingFace Model Hub
- AI研究ディープリサーチ（`/ai-research-deep`）
- 週次AI研究レポート（`/ai-research-report`）
- note記事作成パイプライン（`/ai-research-full`）
- 日次ダイジェスト
- プロキシローテーション

---

## 決定事項

- **既存ArticleExtractorは変更しない**: RobustScraperがコンポジションでラップ
- **RSSフィードが確認できたブログのみfeeds.json登録**: 非対応ブログはscrape_urlsで管理
- **Playwrightはオプショナル**: 未インストール環境でも動作可能
- **GitHub Projectは完全独立**: 金融ニュースProject #15とは分離
- **テーマ設定はJSON**: ai-research-themes.json でデータソース+スクレイピング設定を一元管理
