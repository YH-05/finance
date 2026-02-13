# AI投資バリューチェーン・トラッキング体制

**Project**: [#44 AI Investment Value Chain Tracking](https://github.com/users/YH-05/projects/44)
**Status**: In Progress (14/21 完了, 66.7%)
**Created**: 2026-02-10
**Updated**: 2026-02-13
**Type**: workflow（Deep Research拡張）

## 背景と目的

### 背景

- **種類**: ワークフロー（Deep Research機能の拡張）
- **課題**: AI技術の進展が投資判断に大きな影響を持つが、**AIバリューチェーン全体**（LLM開発、演算チップ、データセンター、電力、ロボティクス、SaaS）を金融市場の文脈で体系的にトラッキングする仕組みがない
- **位置付け**: 既存の `/deep-research --type theme` のデータ収集フェーズを自動化・定期実行化するもの
- **参照**: 既存の金融ニュース収集体制（`/finance-news-workflow`）の3フェーズアーキテクチャを踏襲

### 目的

1. AIバリューチェーン全体（77社）の企業ブログ/リリースを自動収集し、**金融市場・株式・AI投資環境との関連性**を付与してGitHub Issueとして登録する
2. **セレクタ駆動**のスクレイピング基盤を構築し、企業別CSS/XPathセレクタ + カスタムオーバーライドで全社をカバーする
3. Python側で決定論的処理を完結させ、AI側は投資視点での要約・重要度判定のみに限定する
4. Deep Researchワークフローのデータソースとして統合可能にする

### ユーザー要件

| 項目 | 決定 |
|------|------|
| スコープ | AIバリューチェーン全体（LLM〜電力・核融合まで） |
| 対象企業数 | 77社（10カテゴリ） |
| GitHub Project | 完全に独立した新Project |
| スクレイピング | セレクタ駆動（全社Webスクレイピング、RSS不使用） |
| MVP優先機能 | データ収集パイプライン |
| arXiv論文 | Phase 2以降 |
| レポート頻度 | 週次（MVP後に日次検討） |
| 記事読者 | 投資家向け |
| ログ基盤 | `utils_core.logging`（structlog） |
| 情報の観点 | 金融市場・株式・AI投資環境との関連性 |
| PDF対応 | ダウンロードのみ（テキスト抽出なし） |
| 設定管理 | Pythonファイル（カテゴリ別、型安全） |

---

## モニタリング対象企業（全77社）

### カテゴリ1: AI/LLM開発（11社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| OpenAI | — (MSFT関連) | openai.com/news/ | ChatGPT収益、MSFT27%持分、評価3000億ドル |
| Google DeepMind | GOOGL | deepmind.google/blog | Alphabet傘下、Gemini、TPU |
| Meta AI | META | ai.meta.com/blog | Llama OSS、Reality Labs |
| Anthropic | — (AMZN/GOOGL) | anthropic.com/research | Claude、AWS Bedrock、50億ドル+調達 |
| Microsoft AI | MSFT | microsoft.com/en-us/ai/blog | Copilot、Azure AI、OpenAI提携 |
| xAI | — | x.ai/news | Grok、200億ドル調達(2026-01) |
| Mistral AI | — | mistral.ai/news | 欧州AI代表、€17億調達 |
| Cohere | — | cohere.com/blog | エンタープライズAI、70億ドル評価 |
| Stability AI | — | stability.ai/news | Stable Diffusion、画像生成AI |
| Perplexity AI | — | perplexity.ai/hub | 検索型AI、急成長 |
| Inflection AI | — | inflection.ai/blog | MSFT/NVDA支援、13億ドル調達 |

### カテゴリ2: GPU・演算チップ（10社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| NVIDIA | NVDA | blogs.nvidia.com | AI GPU独占、H100/Blackwell |
| AMD | AMD | amd.com/en/blogs.html | MI300X、NVIDIA競合 |
| Intel | INTC | intc.com/news-events/press-releases | Xeon、AI推論転換 |
| Broadcom | AVGO | news.broadcom.com/releases | AI接続チップ、カスタムASIC |
| Qualcomm | QCOM | qualcomm.com/news/releases | エッジAI、Snapdragon |
| ARM Holdings | ARM | newsroom.arm.com/blog | AIエッジチップ設計IP |
| Marvell Technology | MRVL | marvell.com/blogs.html | DC接続チップ、カスタムシリコン |
| Cerebras Systems | — | cerebras.ai/blog | ウェーハスケールプロセッサ、評価230億ドル |
| SambaNova | — | sambanova.ai/blog | RDU、エネルギー効率型推論 |
| Tenstorrent | — | tenstorrent.com/vision | RISC-V + AI、Jim Keller率いる |

### カテゴリ3: 半導体製造装置（6社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| TSMC | TSM | pr.tsmc.com/english/latest-news | AI半導体製造独占、3nm/2nm |
| ASML | ASML | asml.com/news | EUVリソグラフィ独占 |
| Applied Materials | AMAT | appliedmaterials.com/us/en/newsroom.html | CVD/エッチング装置 |
| Lam Research | LRCX | newsroom.lamresearch.com | エッチング、先端パッケージ |
| KLA Corporation | KLAC | kla.com/advance | プロセス制御、歩留まり最適化 |
| Tokyo Electron | 8035.T | tel.co.jp/news | 前後工程装置、ボンディング |

### カテゴリ4: データセンター・クラウドインフラ（7社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| Equinix | EQIX | newsroom.equinix.com | グローバルDC、AI需要拡張 |
| Digital Realty | DLR | digitalrealty.com/about/newsroom | DC・接続、CapEx急増 |
| CoreWeave | CRWV | coreweave.com/newsroom | AI専用クラウド、NVIDIA GPU |
| Lambda Labs | — | lambda.ai/blog | AI向けクラウド、$1.5B調達 |
| Arista Networks | ANET | arista.com/en/company/news | DCネットワーキング |
| Vertiv | VRT | vertiv.com/en-us/about/news-and-insights | DC冷却・電力管理、液冷 |
| Super Micro Computer | SMCI | — (PR Newswire経由) | AIサーバー、Blackwell対応 |

### カテゴリ5: ネットワーキング（2社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| Cisco | CSCO | newsroom.cisco.com | ネットワークセキュリティ × AI |
| Juniper Networks | JNPR | newsroom.juniper.net | AI-native networking |

※ Arista Networks はカテゴリ4に統合

### カテゴリ6: 電力・エネルギーインフラ（7社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| Constellation Energy | CEG | constellationenergy.com/newsroom.html | 原子力発電、DC向け電力 |
| NextEra Energy | NEE | investor.nexteraenergy.com/news-releases | 米国最大再エネ、DC需要増 |
| Vistra Energy | VST | investor.vistracorp.com/news | Meta等AI企業向け電力契約 |
| Bloom Energy | BE | bloomenergy.com/newsroom | SOFC燃料電池、DC電源 |
| Eaton Corporation | ETN | eaton.com/.../news-releases.html | 電力管理・配電、DC向け |
| Schneider Electric | SU | blog.se.com | DC冷却・電力管理 |
| nVent Electric | NVT | blog.nvent.com | DC電気保護・配電 |

### カテゴリ7: 原子力・核融合（8社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| Oklo | OKLO | oklo.com/newsroom/news | 先進炉、Meta電力供給契約 |
| NuScale Power | SMR | nuscalepower.com/press-releases | SMR、DC向け電力 |
| Cameco | CCJ | cameco.com/media/news | ウラン採掘・精製、核燃料 |
| Centrus Energy | LEU | centrusenergy.com/news | LEU/HALEU供給、$900M拡張 |
| Commonwealth Fusion | — | cfs.energy/news-and-media | 核融合、Google/NVIDIA提携 |
| TAE Technologies | — | tae.com/category/press-releases | 核融合、Trump Media合併予定 |
| Helion Energy | — | helionenergy.com/news | 商用核融合発電所建設中 |
| General Fusion | — | generalfusion.com/post/category/press-releases | LM26プロトタイプ、NASDAQ上場予定 |

### カテゴリ8: フィジカルAI・ロボティクス（9社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| Tesla (Optimus) | TSLA | tesla.com/blog | Optimus、自社製造統合 |
| Intuitive Surgical | ISRG | investor.intuitivesurgical.com | da Vinci、医療ロボット |
| Fanuc | 6954.T | fanuc.co.jp | 産業ロボット・CNC |
| ABB | ABB | new.abb.com/news | ロボティクス・電化統合 |
| Boston Dynamics | — (Hyundai) | bostondynamics.com/blog | Atlas humanoid |
| Figure AI | — | figure.ai/news | Helix humanoid、物流向け |
| Physical Intelligence | — | physicalintelligence.company | 汎用ロボット基盤モデル |
| Agility Robotics | — | agilityrobotics.com/about/press | Digit humanoid、倉庫自動化 |
| Symbotic | SYM | symbotic.com/innovation-insights/blog | AI倉庫自動化 |

### カテゴリ9: SaaS・AI活用ソフトウェア（10社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| Salesforce | CRM | salesforce.com/blog | Einstein AI、Agentforce |
| ServiceNow | NOW | servicenow.com/community/.../blog | ワークフロー自動化 × AI |
| Palantir | PLTR | blog.palantir.com | データ分析、政府AI |
| Snowflake | SNOW | snowflake.com/en/engineering-blog | AI data cloud |
| Datadog | DDOG | datadoghq.com/blog | AI observability |
| CrowdStrike | CRWD | crowdstrike.com/en-us/blog | AI脅威検出 |
| MongoDB | MDB | mongodb.com/company/blog | Vector search |
| UiPath | PATH | uipath.com/newsroom | Agentic automation |
| C3.ai | AI | c3.ai/blog | エンタープライズAI |
| Databricks | — | databricks.com/blog | Unified AI governance |

### カテゴリ10: AI基盤・MLOps（7社）

| 企業 | ティッカー | ブログ/ニュースURL | 投資関連性 |
|------|----------|------------------|-----------|
| HuggingFace | — | huggingface.co/blog | OSS model hub、評価45億ドル |
| Scale AI | — | scale.com/blog | データラベリング、agentic AI |
| Weights & Biases | — | wandb.ai/fully-connected/blog | ML実験管理 |
| Together AI | — | together.ai/blog | OSS推論、Refuel.ai買収 |
| Anyscale | — | anyscale.com/blog | Ray framework |
| Replicate | — | replicate.com/blog | モデルホスティング |
| Elastic | ESTC | elastic.co/blog | Search × AI agent |

### 集計

| カテゴリ | 社数 |
|---------|------|
| AI/LLM開発 | 11 |
| GPU・演算チップ | 10 |
| 半導体製造装置 | 6 |
| DC・クラウドインフラ | 7 |
| ネットワーキング | 2 |
| 電力・エネルギー | 7 |
| 原子力・核融合 | 8 |
| フィジカルAI | 9 |
| SaaS | 10 |
| AI基盤・MLOps | 7 |
| **合計** | **77** |

---

## Deep Research との統合

### 位置付け

```
Deep Research エコシステム
├── /deep-research --type stock    → 個別銘柄分析
├── /deep-research --type sector   → セクター分析
├── /deep-research --type macro    → マクロ経済分析
├── /deep-research --type theme    → テーマ投資分析
│   └── AI投資テーマ分析時のデータソースとして活用
│
└── /ai-research-collect           → 【本プロジェクト】
    └── AIバリューチェーン全体の定期収集 → GitHub Issue蓄積
        ├── 10カテゴリ × 77社をカバー
        └── Deep Research の theme/stock/sector 分析で参照可能
```

### データ連携

- 本ワークフローで収集したIssueは、`/deep-research --type theme --topic "AI"` 実行時に参照データとして利用
- `dr-source-aggregator` がGitHub IssueからAI企業動向を取得可能
- `dr-sector-analyzer` がカテゴリ別の動向を分析可能
- 蓄積されたIssueを基に、週次AI投資レポート生成（Phase 2）

---

## アーキテクチャ

### セレクタ駆動スクレイピング

全77社を**企業別セレクタ設定**で処理する。大半の企業は設定のみで動作し、特殊なサイトのみカスタムオーバーライドで対応する。

```
セレクタ駆動アーキテクチャ

パターン1: 設定のみ（~55社）
  └── CompanyConfig に CSS/XPath セレクタを定義
      → CompanyScraperEngine が共通ロジックで処理
      例: AMD, TSMC, Constellation Energy, Salesforce

パターン2: 設定 + 軽微カスタム（~15社）
  └── CompanyConfig + extract_article_list() の部分オーバーライド
      → ページネーションや日付フォーマットが特殊
      例: Intel, Tesla, HuggingFace

パターン3: フルカスタム実装（~7社）
  └── BaseCompanyScraper を継承した完全カスタム
      → SPA/JS-heavy/特殊構造
      例: Perplexity AI, Cerebras, Physical Intelligence
```

### 全体構成

```
/ai-research-collect
  → ai-research-workflow スキル
    → Phase 1: Python CLI (prepare_ai_research_session.py)
        ├── CompanyScraperEngine（共通エンジン）
        │   ├── ScrapingPolicy（新規）
        │   │   ├── 7種UAローテーション（直前UA回避）
        │   │   ├── ドメイン別レートリミット（asyncio.Lock排他制御）
        │   │   └── 429リトライ（Retry-After対応、指数バックオフ2→4→8秒）
        │   ├── ArticleContentChecker（既存再利用）
        │   │   ├── httpx → Playwright → ペイウォール検出
        │   │   └── 3段階フォールバック
        │   ├── ArticleExtractor（既存再利用）
        │   │   └── trafilatura → lxml フォールバック
        │   ├── StructureValidator（新規）
        │   │   └── セレクタヒット率監視 → 構造変更検知
        │   └── PdfHandler（新規）
        │       └── PDFリンク検出 + ダウンロード（テキスト抽出なし）
        │
        ├── CompanyConfig（カテゴリ別Pythonファイル × 10）
        │   └── 企業ごとの URL + セレクタ + 投資コンテキスト
        │
        ├── BaseCompanyScraper + カスタム実装（~7社）
        │   └── SPA/JS-heavy 等の特殊サイト用
        │
        └── CompanyScraperRegistry
            └── 企業 → 実装のルーティング
    → Phase 2: AI（ai-research-article-fetcher × カテゴリ並列）
        └── 投資視点での要約生成 + 市場影響度判定 + Issue作成
    → Phase 3: 結果集約 + スクレイピング統計レポート
```

### Python → AI 役割分担

| Python側（決定論的） | AI側（高度判断） |
|---------------------|-----------------|
| 全77社Webスクレイピング | タイトル翻訳（英→日） |
| セレクタベース記事リスト抽出 | 投資視点4セクション要約生成 |
| 構造変更検知（セレクタヒット率） | 市場影響度判定（low/medium/high） |
| PDFダウンロード | 関連銘柄・セクターの特定 |
| 日付フィルタリング | Issue本文の文章構成 |
| URLベース重複チェック | |
| Top-N選択（公開日時降順） | |
| カテゴリ別JSON出力 | |
| スクレイピング統計レポート | |
| 構造化ログ出力 | |

### データフロー

```
ユーザー: /ai-research-collect --days 7 --categories all --top-n 10
  │
  ▼ Phase 1 (Python)
  prepare_ai_research_session.py
    ├── カテゴリ別 CompanyConfig 読み込み（77社）
    ├── CompanyScraperRegistry で企業→実装をルーティング:
    │   ├── 設定のみ企業: CompanyScraperEngine + CompanyConfig
    │   └── カスタム企業: BaseCompanyScraper 継承クラス
    ├── 企業ごとのスクレイピング:
    │   ├── ScrapingPolicy でUA/レートリミット制御
    │   ├── StructureValidator で構造変更チェック
    │   ├── ArticleContentChecker でアクセス性確認
    │   ├── ArticleExtractor で本文抽出
    │   └── PdfHandler でPDFリンク検出・ダウンロード
    ├── → ScrapedArticle 統一形式に変換
    ├── → 既存Issue URL抽出（重複チェック用）
    ├── → 日付フィルタ → 重複チェック → Top-N選択
    └── → .tmp/ai-research-batches/{category_key}.json 出力
  │
  ▼ Phase 2 (AI)
  ai-research-article-fetcher × カテゴリ数（並列）
    ├── タイトル翻訳
    ├── 投資視点4セクション要約（概要/技術的意義/市場影響/投資示唆）
    ├── 市場影響度判定 + 関連銘柄タグ付け
    ├── Issue作成（gh issue create + close）
    ├── ラベル付与（ai-research + カテゴリラベル + needs-review）
    └── GitHub Project追加 + Status/Date設定
  │
  ▼ Phase 3 (集約)
  カテゴリ別統計 + 構造変更レポート + スクレイピング統計サマリー
```

---

## コンポーネント詳細

### 1. CompanyScraperEngine（共通エンジン）

**パス**: `src/rss/services/company_scrapers/engine.py`

全企業共通のスクレイピングオーケストレーター。既存コンポーネントをコンポジションで組み合わせる。

```python
class CompanyScraperEngine:
    """全企業共通のスクレイピングエンジン.

    既存の ArticleContentChecker + ArticleExtractor を組み合わせ、
    ScrapingPolicy でbot対策、StructureValidator で構造変更検知を行う。
    """

    def __init__(
        self,
        policy: ScrapingPolicy,
        content_checker: ArticleContentChecker,  # 既存再利用
        extractor: ArticleExtractor,              # 既存再利用
        structure_validator: StructureValidator,
        pdf_handler: PdfHandler,
    ) -> None:
        self._policy = policy
        self._checker = content_checker
        self._extractor = extractor
        self._validator = structure_validator
        self._pdf = pdf_handler
        self._logger = get_logger(__name__, component="engine")

    async def scrape_company(
        self, config: CompanyConfig, max_articles: int = 10,
    ) -> CompanyScrapeResult:
        """1社分のスクレイピングを実行."""
        # 1. レートリミット待機 + UA設定
        await self._policy.acquire(config.domain)
        headers = self._policy.get_headers()

        # 2. ブログページ取得
        html = await self._fetch_page(config.blog_url, headers)

        # 3. 構造変更チェック
        validation = self._validator.validate(html, config)
        if validation.hit_rate == 0:
            self._logger.error("Structure changed", company=config.key)
            return CompanyScrapeResult(company=config.key, articles=[], validation=validation)

        # 4. 記事リスト抽出（セレクタベース）
        article_urls = self._extract_article_list(html, config)

        # 5. 各記事の処理
        articles = []
        for url in article_urls[:max_articles]:
            article = await self._process_article(url, config)
            if article:
                articles.append(article)

        return CompanyScrapeResult(
            company=config.key, articles=articles, validation=validation,
        )

    async def _process_article(
        self, url: str, config: CompanyConfig,
    ) -> ScrapedArticle | None:
        """1記事を処理（HTML or PDF）."""
        if self._pdf.is_pdf_url(url):
            metadata = await self._pdf.download(url, config.key)
            return ScrapedArticle(url=url, source_type="pdf", pdf=metadata)

        # HTML: 既存コンポーネントで処理
        check = await self._checker.check_article_content(url)
        if check.status != ContentStatus.ACCESSIBLE:
            return None

        extracted = await self._extractor.extract(url)
        pdf_links = self._pdf.find_pdf_links(check.raw_text)

        return ScrapedArticle(
            url=url, title=extracted.title, text=extracted.text,
            source_type="html", attached_pdfs=pdf_links,
        )
```

### 2. ScrapingPolicy（bot対策）

**パス**: `src/rss/services/company_scrapers/scraping_policy.py`

UA ローテーション + ドメイン別レートリミット + 429 リトライの3機能を提供。

```python
class ScrapingPolicy:
    """スクレイピングのbot対策ポリシー."""

    def __init__(
        self,
        domain_rate_limits: dict[str, float],
        user_agents: list[str] | None = None,
        max_retries: int = 3,
    ) -> None:
        self._rate_limits = domain_rate_limits
        self._user_agents = user_agents or DEFAULT_USER_AGENTS
        self._domain_locks: dict[str, asyncio.Lock] = {}
        self._last_request_time: dict[str, float] = {}
        self._last_ua_index: int = -1
        self._logger = get_logger(__name__, component="scraping_policy")

    async def acquire(self, domain: str) -> None:
        """ドメイン別レートリミットを適用（排他制御）."""
        ...

    def get_headers(self) -> dict[str, str]:
        """UAローテーション込みのHTTPヘッダを返す."""
        ...

    async def handle_429(self, response: httpx.Response, url: str) -> bool:
        """429応答を処理。Retry-After対応 + 指数バックオフ."""
        ...
```

**デフォルトUA（7種）**: Chrome/Firefox/Edge/Safari の最新版 + カスタム

### 3. StructureValidator（構造変更検知）

**パス**: `src/rss/services/company_scrapers/structure_validator.py`

企業のブログ/ニュースページの構造が変更された場合を検知する。

```python
class StructureValidator:
    """セレクタベースの構造変更検知."""

    def validate(self, html: str, config: CompanyConfig) -> StructureReport:
        """セレクタのヒット率を検証."""
        report = StructureReport(company=config.key)

        # 記事リストセレクタのヒット数
        article_hits = len(self._select(html, config.article_list_selector))
        report.article_list_hits = article_hits

        # 各記事のタイトル・日付セレクタのヒット率
        for article_el in self._select(html, config.article_list_selector):
            has_title = bool(self._select(article_el, config.article_title_selector))
            has_date = bool(self._select(article_el, config.article_date_selector))
            report.add(title_found=has_title, date_found=has_date)

        # ログ出力
        if report.hit_rate == 0:
            self._logger.error("Major structure change detected",
                             company=config.key)
        elif report.hit_rate < 0.5:
            self._logger.warning("Significant structure change",
                               company=config.key, hit_rate=report.hit_rate)
        elif report.hit_rate < 0.8:
            self._logger.warning("Partial structure change",
                               company=config.key, hit_rate=report.hit_rate)
        else:
            self._logger.info("Structure OK",
                            company=config.key, articles=article_hits)

        return report
```

### 4. PdfHandler（PDF対応）

**パス**: `src/rss/services/company_scrapers/pdf_handler.py`

PDFリンクの検出とダウンロードを行う。テキスト抽出は行わない。

```python
class PdfHandler:
    """PDFリンク検出 + ダウンロード."""

    def is_pdf_url(self, url: str) -> bool:
        """URL拡張子 or Content-Type でPDF判定."""
        ...

    def find_pdf_links(self, html: str) -> list[str]:
        """HTML内の全PDFリンクを検出."""
        ...

    async def download(self, url: str, company_key: str) -> PdfMetadata:
        """PDFをダウンロードしてメタデータを返す."""
        ...
```

**保存先**: `data/raw/ai-research/pdfs/{company_key}/{date}_{filename}.pdf`

### 5. CompanyConfig（企業設定）

**パス**: `src/rss/services/company_scrapers/configs/`（カテゴリ別Pythonファイル）

```python
@dataclass(frozen=True)
class CompanyConfig:
    """企業別スクレイピング設定."""
    key: str                           # "openai"
    name: str                          # "OpenAI"
    category: str                      # "ai_llm"
    blog_url: str                      # "https://openai.com/news/"

    # セレクタ（記事リスト抽出用）
    article_list_selector: str         # "article a[href]"
    article_title_selector: str        # "h2"
    article_date_selector: str | None  # "time[datetime]"

    # オプション
    requires_playwright: bool = False
    rate_limit_seconds: float = 3.0

    # 投資コンテキスト
    investment_context: InvestmentContext = ...

    @property
    def domain(self) -> str:
        """URLからドメインを抽出."""
        from urllib.parse import urlparse
        return urlparse(self.blog_url).netloc


@dataclass(frozen=True)
class InvestmentContext:
    """投資判断に必要なコンテキスト."""
    tickers: list[str]     # ["MSFT"]
    sectors: list[str]     # ["Software", "Cloud"]
    keywords: list[str]    # ["ChatGPT", "GPT", "API pricing"]
```

**設定例（`configs/ai_llm.py`）**:

```python
OPENAI = CompanyConfig(
    key="openai",
    name="OpenAI",
    category="ai_llm",
    blog_url="https://openai.com/news/",
    article_list_selector="a[href*='/index/']",
    article_title_selector="h3",
    article_date_selector="time",
    requires_playwright=False,
    rate_limit_seconds=5.0,
    investment_context=InvestmentContext(
        tickers=["MSFT"],
        sectors=["Software", "Cloud"],
        keywords=["ChatGPT", "GPT", "API pricing", "enterprise"],
    ),
)

# カテゴリ内全企業のリスト
AI_LLM_COMPANIES: list[CompanyConfig] = [
    OPENAI,
    GOOGLE_DEEPMIND,
    META_AI,
    ...
]
```

### 6. BaseCompanyScraper（カスタム実装用基底）

**パス**: `src/rss/services/company_scrapers/base.py`

SPA/JS-heavy 等の特殊サイト向け。設定のみでは対応できない企業用。

```python
class BaseCompanyScraper(ABC):
    """企業別スクレイパーの基底クラス."""

    def __init__(self, engine: CompanyScraperEngine) -> None:
        self._engine = engine
        self._logger = get_logger(
            f"{__name__}.{self.company_key}", company=self.company_key,
        )

    @property
    @abstractmethod
    def company_key(self) -> str: ...

    @property
    @abstractmethod
    def config(self) -> CompanyConfig: ...

    @abstractmethod
    async def extract_article_list(self, html: str) -> list[ArticleMetadata]:
        """記事リストを抽出（カスタムロジック）."""
        ...

    async def extract_article_content(
        self, url: str,
    ) -> ScrapedArticle | None:
        """記事本文を抽出（デフォルトはEngine委譲）."""
        return await self._engine._process_article(url, self.config)

    async def scrape_latest(
        self, max_articles: int = 10,
    ) -> CompanyScrapeResult:
        """最新記事を取得（共通フロー）."""
        await self._engine._policy.acquire(self.config.domain)
        headers = self._engine._policy.get_headers()
        html = await self._engine._fetch_page(self.config.blog_url, headers)

        articles_meta = await self.extract_article_list(html)
        articles = []
        for meta in articles_meta[:max_articles]:
            article = await self.extract_article_content(meta.url)
            if article:
                articles.append(article)

        return CompanyScrapeResult(
            company=self.company_key, articles=articles,
        )
```

### 7. CompanyScraperRegistry（ルーティング）

**パス**: `src/rss/services/company_scrapers/registry.py`

```python
class CompanyScraperRegistry:
    """企業 → 実装のルーティング."""

    def __init__(
        self,
        engine: CompanyScraperEngine,
        custom_scrapers: dict[str, type[BaseCompanyScraper]] | None = None,
    ) -> None:
        self._engine = engine
        self._custom: dict[str, BaseCompanyScraper] = {}
        for key, cls in (custom_scrapers or {}).items():
            self._custom[key] = cls(engine)

    async def scrape(
        self, config: CompanyConfig, max_articles: int = 10,
    ) -> CompanyScrapeResult:
        """企業に応じて適切な実装でスクレイピング."""
        if config.key in self._custom:
            return await self._custom[config.key].scrape_latest(max_articles)
        return await self._engine.scrape_company(config, max_articles)
```

### 8. ログ・エラーハンドリング設計

**ログ基盤**: `utils_core.logging`（structlog ベース）

#### ログ出力方針

```python
from utils_core.logging import get_logger, log_context, log_performance

logger = get_logger(__name__, component="ai_research")

# カテゴリ・企業レベルのコンテキスト
with log_context(phase="data_collection", category="gpu_chips", company="nvidia"):
    logger.info("Scraping started", url="https://blogs.nvidia.com/")

# パフォーマンス計測
@log_performance(logger)
async def scrape_category(category_key: str) -> list[CompanyScrapeResult]:
    ...
```

#### ログレベル使い分け

| レベル | 用途 |
|--------|------|
| DEBUG | HTTP応答詳細、HTMLパース中間結果、セレクタマッチ詳細 |
| INFO | カテゴリ開始/完了、企業別取得成功、Issue作成成功、構造OK |
| WARNING | 429レートリミット、構造部分変更（hit_rate < 0.8）、Playwright未インストール |
| ERROR | 構造完全変更（hit_rate = 0）、スクレイピング完全失敗、Issue作成失敗 |
| CRITICAL | 全カテゴリ失敗、設定ファイル読み込み不可 |

#### エラーハンドリングパターン

```python
class ScrapingError(Exception):
    """スクレイピング基盤の基底例外."""
    def __init__(self, message: str, domain: str, url: str) -> None:
        super().__init__(message)
        self.domain = domain
        self.url = url

class RateLimitError(ScrapingError):
    """レートリミット超過."""

class StructureChangedError(ScrapingError):
    """ページ構造変更検知."""

class BotDetectionError(ScrapingError):
    """bot検知によるブロック."""
```

### 9. ai-research-article-fetcher エージェント

**パス**: `.claude/agents/ai-research-article-fetcher.md`

**入力**: `{articles: [ScrapedArticle], issue_config: {...}, investment_context: {...}}`

**投資視点4セクション要約**:
1. **概要**: 発表内容の要約
2. **技術的意義**: 技術的なブレークスルーの評価
3. **市場影響**: 関連銘柄・セクターへの影響分析
4. **投資示唆**: 投資家にとっての意味合い

**カテゴリ別ラベル**: `ai-llm`, `ai-chips`, `ai-semicon`, `ai-datacenter`, `ai-network`, `ai-power`, `ai-nuclear`, `ai-robotics`, `ai-saas`, `ai-infra`

---

## ファイルマップ

### Wave 0: 共通基盤 + データ型（TDD実装）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `src/rss/services/company_scrapers/__init__.py` | 1KB |
| 新規 | `src/rss/services/company_scrapers/types.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/scraping_policy.py` | 3KB |
| 新規 | `src/rss/services/company_scrapers/structure_validator.py` | 3KB |
| 新規 | `src/rss/services/company_scrapers/pdf_handler.py` | 3KB |
| 新規 | `src/rss/services/company_scrapers/engine.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/base.py` | 4KB |
| 新規 | `src/rss/services/company_scrapers/registry.py` | 2KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_types.py` | 3KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_scraping_policy.py` | 5KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_structure_validator.py` | 4KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_pdf_handler.py` | 3KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_engine.py` | 6KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_registry.py` | 3KB |

### Wave 1: パイロットカテゴリ（AI/LLM 11社）+ カスタムスクレイパー

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `src/rss/services/company_scrapers/configs/__init__.py` | 1KB |
| 新規 | `src/rss/services/company_scrapers/configs/ai_llm.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/custom/__init__.py` | 1KB |
| 新規 | `src/rss/services/company_scrapers/custom/perplexity.py` | 4KB |
| 新規 | `tests/rss/unit/services/company_scrapers/configs/test_ai_llm.py` | 3KB |
| 新規 | `tests/rss/unit/services/company_scrapers/custom/test_perplexity.py` | 3KB |
| 新規 | `tests/rss/unit/services/company_scrapers/snapshots/ai_llm/` | HTMLスナップショット |

### Wave 2: 残りカテゴリ（66社の設定 + カスタムスクレイパー）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `src/rss/services/company_scrapers/configs/gpu_chips.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/configs/semiconductor.py` | 3KB |
| 新規 | `src/rss/services/company_scrapers/configs/data_center.py` | 4KB |
| 新規 | `src/rss/services/company_scrapers/configs/networking.py` | 2KB |
| 新規 | `src/rss/services/company_scrapers/configs/power_energy.py` | 4KB |
| 新規 | `src/rss/services/company_scrapers/configs/nuclear_fusion.py` | 4KB |
| 新規 | `src/rss/services/company_scrapers/configs/physical_ai.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/configs/saas.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/configs/ai_infra.py` | 4KB |
| 新規 | `src/rss/services/company_scrapers/custom/cerebras.py` | 4KB |
| 新規 | `src/rss/services/company_scrapers/custom/fanuc.py` | 4KB |
| 新規 | `src/rss/services/company_scrapers/custom/...` | 各4KB |
| 新規 | `tests/rss/unit/services/company_scrapers/configs/test_*.py` | 各2KB |
| 新規 | `tests/rss/unit/services/company_scrapers/snapshots/*/` | HTMLスナップショット |

### Wave 3: セッションスクリプト + エージェント

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `scripts/prepare_ai_research_session.py` | 20KB |
| 新規 | `.claude/agents/ai-research-article-fetcher.md` | 7KB |

### Wave 4: スキル定義・テンプレート

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `.claude/skills/ai-research-workflow/SKILL.md` | 8KB |
| 新規 | `.claude/skills/ai-research-workflow/guide.md` | 10KB |
| 新規 | `.claude/skills/ai-research-workflow/templates/issue-template.md` | 4KB |
| 新規 | `.claude/skills/ai-research-workflow/templates/summary-template.md` | 4KB |

### Wave 5: コマンド定義 + ドキュメント更新

| 操作 | ファイル |
|------|---------|
| 新規 | `.claude/commands/ai-research-collect.md` |
| 修正 | `CLAUDE.md`（コマンド/スキル/エージェント一覧に追加） |

---

## 見積もり

| Wave | 内容 | 見積もり |
|------|------|---------|
| Wave 0 | 共通基盤 TDD実装（Engine, Policy, Validator, PdfHandler, Registry, types） | 4-5時間 |
| Wave 1 | パイロット: AI/LLM 11社の設定 + Perplexityカスタム + HTMLスナップショット + 検証 | 3-4時間 |
| Wave 2 | 残りカテゴリ: 66社の設定（実装時に都度セレクタ調査）+ カスタムスクレイパー | 10-15時間 |
| Wave 3 | セッションスクリプト + エージェント | 4-5時間 |
| Wave 4 | スキル定義 + テンプレート | 2-3時間 |
| Wave 5 | コマンド + CLAUDE.md更新 | 1時間 |
| その他 | GitHub Project作成 | 1時間 |
| **合計** | | **25-34時間** |

---

## テスト戦略

### テスト種別

| 手法 | 対象 | CI |
|------|------|-----|
| HTMLスナップショットテスト | 各社のブログHTMLを保存し、セレクタ抽出を検証 | Yes |
| StructureValidator テスト | ヒット率閾値ロジック、構造変更パターン | Yes |
| ScrapingPolicy テスト | UAローテ、レートリミット、429処理 | Yes |
| PdfHandler テスト | PDF検出、ダウンロードロジック | Yes |
| Engine 統合テスト | コンポーネント連携（モック使用） | Yes |
| ライブ検証 | 実際のサイトに接続して構造確認 | No（手動） |

### HTMLスナップショットの管理

```
tests/rss/unit/services/company_scrapers/snapshots/
├── ai_llm/
│   ├── openai_blog.html       # OpenAI ブログページのスナップショット
│   ├── anthropic_research.html
│   └── ...
├── gpu_chips/
│   ├── nvidia_blog.html
│   └── ...
└── ...
```

- 初回は実サイトからHTMLを保存
- CI ではスナップショットに対してセレクタ抽出をテスト
- サイト構造変更時にスナップショットを更新

---

## リスク分析

| リスク | レベル | 軽減策 |
|--------|--------|--------|
| 77社のURL変更・構造変更 | **高** | StructureValidator で自動検知、セレクタヒット率の定期監視 |
| bot検知・WAF強化（特にBigTech） | **高** | ScrapingPolicy の多層防御（UA+レート+429）+ 構造化ログで早期検知 |
| セレクタ調査の工数超過 | **高** | パイロット（Wave 1: 11社）で工数を検証、残りに展開 |
| 企業設定の保守コスト | 中 | Python型安全、StructureValidator で変更を自動検知 |
| Playwright統合の安定性 | 中 | requires_playwright フラグで企業別制御 + 未インストール時スキップ |
| 大量リクエストによるIP制限 | 中 | ドメイン別レートリミット厳守、カテゴリ間の間隔確保 |
| PDFダウンロードの容量増大 | 低 | 期間制限（--days）+ max_articles_per_company で制御 |
| 既存ワークフローへの影響 | 低 | コンポジション（既存変更なし）+ カテゴリ分離 |

---

## 既存コードの再利用

### 直接再利用（変更なし）

| コンポーネント | 用途 | 再利用度 |
|--------------|------|---------|
| `src/rss/services/article_content_checker.py` | アクセス性チェック（httpx→Playwright→ペイウォール） | 90% |
| `src/rss/services/article_extractor.py` | 本文抽出（trafilatura→lxml） | 85% |
| `src/rss/core/http_client.py` | HTTPフェッチ + リトライ + バックオフ | 95% |
| `src/rss/utils/url_normalizer.py` | URL正規化 + 重複チェック | 70% |
| `src/utils_core/logging/` | 構造化ログ基盤 | 100% |

### フォーク＆修正

| 元ファイル | 新ファイル |
|-----------|-----------|
| `scripts/prepare_news_session.py` | `scripts/prepare_ai_research_session.py` |
| `.claude/agents/news-article-fetcher.md` | `.claude/agents/ai-research-article-fetcher.md` |
| `.claude/skills/finance-news-workflow/` | `.claude/skills/ai-research-workflow/` |

### 新規実装

| コンポーネント | サイズ | 内容 |
|--------------|--------|------|
| ScrapingPolicy | ~3KB | UA+レートリミット+429 |
| CompanyScraperEngine | ~5KB | 既存コンポーネントのオーケストレーター |
| StructureValidator | ~3KB | セレクタヒット率による構造変更検知 |
| PdfHandler | ~3KB | PDFリンク検出+ダウンロード |
| BaseCompanyScraper | ~4KB | カスタムスクレイパー基底 |
| CompanyScraperRegistry | ~2KB | 企業→実装ルーティング |
| CompanyConfig × 10カテゴリ | ~36KB | 77社のセレクタ設定 |
| カスタムスクレイパー | ~28KB | 特殊サイト用（~7社） |
| データ型 | ~5KB | ScrapedArticle, StructureReport 等 |
| カスタム例外 | ~1KB | ScrapingError 階層 |

---

## GitHub Project セットアップ（実装前の手動作業）

```bash
# 1. Project作成
gh project create --owner YH-05 --title 'AI Investment Value Chain Tracking'

# 2. Statusフィールドにオプション追加
#    - Company Release
#    - Product Update
#    - Partnership
#    - Earnings Impact
#    - Infrastructure

# 3. Categoryカスタムフィールド追加（Single Select）
#    ai-llm / ai-chips / ai-semicon / ai-datacenter / ai-network
#    ai-power / ai-nuclear / ai-robotics / ai-saas / ai-infra

# 4. Published Dateカスタムフィールド追加

# 5. Tickersカスタムフィールド追加（テキスト）

# 6. Impact Levelカスタムフィールド追加（Single Select: low/medium/high）

# 7. 取得したIDを configs 内の定数に反映
```

---

## MVPスコープ

### 含む

- CompanyScraperEngine（既存コンポーネントのコンポジション）
- ScrapingPolicy（UA+レートリミット+429）
- StructureValidator（セレクタヒット率による構造変更検知）
- PdfHandler（PDFリンク検出+ダウンロード、テキスト抽出なし）
- BaseCompanyScraper + CompanyScraperRegistry（カスタムスクレイパー基盤）
- CompanyConfig 77社分（10カテゴリ別Pythonファイル）
- カスタムスクレイパー（~7社分）
- HTMLスナップショットテスト
- 単体テスト（80%以上カバレッジ）
- ScrapedArticle 統一形式変換
- 日付フィルタリング + 重複チェック + Top-N選択
- **投資視点**AI要約生成 + Issue作成
- カテゴリ別ラベリング + 関連銘柄タグ付け
- GitHub Project連携
- `/ai-research-collect` コマンド
- スクレイピング統計レポート（構造変更レポート含む）
- `utils_core.logging` によるstructlogベースの構造化ログ
- カスタム例外階層（ScrapingError系）

### Phase 2以降（除外）

- **arXiv論文取得**（arXiv API + feedparser）
- **PDFテキスト抽出**（pdfplumber等）
- OSSリリース・ベンチマーク追跡（GitHub Trending / HuggingFace Model Hub）
- AI投資ディープリサーチ（`/deep-research --type theme --topic "AI"` との完全統合）
- 週次AI投資レポート（`/ai-research-report`）
- note記事作成パイプライン（`/ai-research-full`）
- 日次ダイジェスト
- プロキシローテーション
- Semantic Scholar API連携
- 企業追加の自動提案（新興AI企業の検出）

---

## 決定事項

- **セレクタ駆動アーキテクチャ**: 全77社を企業別セレクタ設定でカバー（RSS不使用）
- **既存コンポーネントのコンポジション**: RobustScraper 新規実装ではなく、ArticleContentChecker + ArticleExtractor を組み合わせ
- **設定のみ / カスタムの2層**: 大半は CompanyConfig のみ、特殊サイトのみ BaseCompanyScraper 継承
- **構造変更検知**: StructureValidator でセレクタヒット率を監視、変更時に WARNING/ERROR ログ
- **PDF対応**: ダウンロードのみ（テキスト抽出なし）。リンク先PDF + HTML内PDFの両方を収集
- **企業設定はPythonファイル**: カテゴリ別 .py に CompanyConfig を定義（型安全、IDE補完）
- **セレクタ調査は実装時に都度**: 事前一括調査ではなく、Wave 実装時に1社ずつ確認
- **パイロットカテゴリ**: AI/LLM 11社で先行実装・検証し、残りに展開
- **10カテゴリで投資バリューチェーン全体をカバー**: LLM〜核融合まで
- **既存コードは変更しない**: ArticleContentChecker, ArticleExtractor はそのまま利用
- **Playwrightは企業別制御**: requires_playwright フラグで個別に有効化
- **GitHub Projectは完全独立**: 金融ニュースProject #15とは分離
- **Deep Researchの拡張として位置付け**: `/deep-research --type theme` のデータソース自動化
- **投資家視点の要約**: 4セクション（概要/技術的意義/市場影響/投資示唆）
- **arXiv/PDFテキスト抽出はPhase 2以降**: MVPでは企業ブログ・リリースの収集に集中
- **ログは utils_core.logging**: structlogベースの構造化ログを全コンポーネントで使用
- **エラーは階層的カスタム例外**: ScrapingError → RateLimitError / StructureChangedError / BotDetectionError
