# AI投資バリューチェーン・トラッキング体制

**Project**: TBD（GitHub Project未作成）
**Status**: Planning
**Created**: 2026-02-10
**Updated**: 2026-02-10
**Type**: workflow（Deep Research拡張）

## 背景と目的

### 背景

- **種類**: ワークフロー（Deep Research機能の拡張）
- **課題**: AI技術の進展が投資判断に大きな影響を持つが、**AIバリューチェーン全体**（LLM開発、演算チップ、データセンター、電力、ロボティクス、SaaS）を金融市場の文脈で体系的にトラッキングする仕組みがない
- **位置付け**: 既存の `/deep-research --type theme` のデータ収集フェーズを自動化・定期実行化するもの
- **参照**: 既存の金融ニュース収集体制（`/finance-news-workflow`）の3フェーズアーキテクチャを踏襲

### 目的

1. AIバリューチェーン全体（70社以上）の企業ブログ/リリースを自動収集し、**金融市場・株式・AI投資環境との関連性**を付与してGitHub Issueとして登録する
2. **ティアベース**のスクレイピング基盤を構築し、RSS/汎用スクレイパー/企業別アダプタの3段階で効率的にカバーする
3. Python側で決定論的処理を完結させ、AI側は投資視点での要約・重要度判定のみに限定する
4. Deep Researchワークフローのデータソースとして統合可能にする

### ユーザー要件

| 項目 | 決定 |
|------|------|
| スコープ | AIバリューチェーン全体（LLM〜電力・核融合まで） |
| 対象企業数 | 70社以上（10カテゴリ） |
| GitHub Project | 完全に独立した新Project |
| スクレイピング | ティアベース（RSS → 汎用 → 企業別アダプタ） |
| MVP優先機能 | データ収集パイプライン |
| arXiv論文 | Phase 2以降 |
| レポート頻度 | 週次（MVP後に日次検討） |
| 記事読者 | 投資家向け |
| ログ基盤 | `utils_core.logging`（structlog） |
| 情報の観点 | 金融市場・株式・AI投資環境との関連性 |

---

## モニタリング対象企業（全70社以上）

### カテゴリ1: AI/LLM開発（11社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| OpenAI | — (MSFT関連) | openai.com/news/ | Tier 2: 汎用 | ChatGPT収益、MSFT27%持分、評価3000億ドル |
| Google DeepMind | GOOGL | deepmind.google/blog | Tier 1: RSS | Alphabet傘下、Gemini、TPU |
| Meta AI | META | ai.meta.com/blog | Tier 2: 汎用 | Llama OSS、Reality Labs |
| Anthropic | — (AMZN/GOOGL) | anthropic.com/research | Tier 2: 汎用 | Claude、AWS Bedrock、50億ドル+調達 |
| Microsoft AI | MSFT | microsoft.com/en-us/ai/blog | Tier 1: RSS | Copilot、Azure AI、OpenAI提携 |
| xAI | — | x.ai/news | Tier 2: 汎用 | Grok、200億ドル調達(2026-01) |
| Mistral AI | — | mistral.ai/news | Tier 2: 汎用 | 欧州AI代表、€17億調達 |
| Cohere | — | cohere.com/blog | Tier 2: 汎用 | エンタープライズAI、70億ドル評価 |
| Stability AI | — | stability.ai/news | Tier 2: 汎用 | Stable Diffusion、画像生成AI |
| Perplexity AI | — | perplexity.ai/hub | Tier 3: アダプタ | 検索型AI、急成長 |
| Inflection AI | — | inflection.ai/blog | Tier 2: 汎用 | MSFT/NVDA支援、13億ドル調達 |

### カテゴリ2: GPU・演算チップ（10社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| NVIDIA | NVDA | blogs.nvidia.com | Tier 1: RSS | AI GPU独占、H100/Blackwell |
| AMD | AMD | amd.com/en/blogs.html | Tier 2: 汎用 | MI300X、NVIDIA競合 |
| Intel | INTC | intc.com/news-events/press-releases | Tier 2: 汎用 | Xeon、AI推論転換 |
| Broadcom | AVGO | news.broadcom.com/releases | Tier 2: 汎用 | AI接続チップ、カスタムASIC |
| Qualcomm | QCOM | qualcomm.com/news/releases | Tier 2: 汎用 | エッジAI、Snapdragon |
| ARM Holdings | ARM | newsroom.arm.com/blog | Tier 2: 汎用 | AIエッジチップ設計IP |
| Marvell Technology | MRVL | marvell.com/blogs.html | Tier 2: 汎用 | DC接続チップ、カスタムシリコン |
| Cerebras Systems | — | cerebras.ai/blog | Tier 3: アダプタ | ウェーハスケールプロセッサ、評価230億ドル |
| SambaNova | — | sambanova.ai/blog | Tier 3: アダプタ | RDU、エネルギー効率型推論 |
| Tenstorrent | — | tenstorrent.com/vision | Tier 2: 汎用 | RISC-V + AI、Jim Keller率いる |

### カテゴリ3: 半導体製造装置（6社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| TSMC | TSM | pr.tsmc.com/english/latest-news | Tier 2: 汎用 | AI半導体製造独占、3nm/2nm |
| ASML | ASML | asml.com/news | Tier 2: 汎用 | EUVリソグラフィ独占 |
| Applied Materials | AMAT | appliedmaterials.com/us/en/newsroom.html | Tier 2: 汎用 | CVD/エッチング装置 |
| Lam Research | LRCX | newsroom.lamresearch.com | Tier 2: 汎用 | エッチング、先端パッケージ |
| KLA Corporation | KLAC | kla.com/advance | Tier 2: 汎用 | プロセス制御、歩留まり最適化 |
| Tokyo Electron | 8035.T | tel.co.jp/news | Tier 2: 汎用 | 前後工程装置、ボンディング |

### カテゴリ4: データセンター・クラウドインフラ（7社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| Equinix | EQIX | newsroom.equinix.com | Tier 2: 汎用 | グローバルDC、AI需要拡張 |
| Digital Realty | DLR | digitalrealty.com/about/newsroom | Tier 2: 汎用 | DC・接続、CapEx急増 |
| CoreWeave | CRWV | coreweave.com/newsroom | Tier 2: 汎用 | AI専用クラウド、NVIDIA GPU |
| Lambda Labs | — | lambda.ai/blog | Tier 3: アダプタ | AI向けクラウド、$1.5B調達 |
| Arista Networks | ANET | arista.com/en/company/news | Tier 2: 汎用 | DCネットワーキング |
| Vertiv | VRT | vertiv.com/en-us/about/news-and-insights | Tier 2: 汎用 | DC冷却・電力管理、液冷 |
| Super Micro Computer | SMCI | — (PR Newswire経由) | Tier 2: 汎用 | AIサーバー、Blackwell対応 |

### カテゴリ5: ネットワーキング（3社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| Cisco | CSCO | newsroom.cisco.com | Tier 1: RSS | ネットワークセキュリティ × AI |
| Juniper Networks | JNPR | newsroom.juniper.net | Tier 2: 汎用 | AI-native networking |
| Arista Networks | ANET | (カテゴリ4と同一) | — | — |

### カテゴリ6: 電力・エネルギーインフラ（7社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| Constellation Energy | CEG | constellationenergy.com/newsroom.html | Tier 2: 汎用 | 原子力発電、DC向け電力 |
| NextEra Energy | NEE | investor.nexteraenergy.com/news-releases | Tier 2: 汎用 | 米国最大再エネ、DC需要増 |
| Vistra Energy | VST | investor.vistracorp.com/news | Tier 2: 汎用 | Meta等AI企業向け電力契約 |
| Bloom Energy | BE | bloomenergy.com/newsroom | Tier 1: RSS | SOFC燃料電池、DC電源 |
| Eaton Corporation | ETN | eaton.com/.../news-releases.html | Tier 2: 汎用 | 電力管理・配電、DC向け |
| Schneider Electric | SU | blog.se.com | Tier 1: RSS | DC冷却・電力管理 |
| nVent Electric | NVT | blog.nvent.com | Tier 1: RSS | DC電気保護・配電 |

### カテゴリ7: 原子力・核融合（8社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| Oklo | OKLO | oklo.com/newsroom/news | Tier 2: 汎用 | 先進炉、Meta電力供給契約 |
| NuScale Power | SMR | nuscalepower.com/press-releases | Tier 2: 汎用 | SMR、DC向け電力 |
| Cameco | CCJ | cameco.com/media/news | Tier 2: 汎用 | ウラン採掘・精製、核燃料 |
| Centrus Energy | LEU | centrusenergy.com/news | Tier 2: 汎用 | LEU/HALEU供給、$900M拡張 |
| Commonwealth Fusion | — | cfs.energy/news-and-media | Tier 2: 汎用 | 核融合、Google/NVIDIA提携 |
| TAE Technologies | — | tae.com/category/press-releases | Tier 2: 汎用 | 核融合、Trump Media合併予定 |
| Helion Energy | — | helionenergy.com/news | Tier 2: 汎用 | 商用核融合発電所建設中 |
| General Fusion | — | generalfusion.com/post/category/press-releases | Tier 2: 汎用 | LM26プロトタイプ、NASDAQ上場予定 |

### カテゴリ8: フィジカルAI・ロボティクス（9社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| Tesla (Optimus) | TSLA | tesla.com/blog | Tier 2: 汎用 | Optimus、自社製造統合 |
| Intuitive Surgical | ISRG | investor.intuitivesurgical.com | Tier 1: RSS | da Vinci、医療ロボット |
| Fanuc | 6954.T | fanuc.co.jp | Tier 3: アダプタ | 産業ロボット・CNC |
| ABB | ABB | new.abb.com/news | Tier 2: 汎用 | ロボティクス・電化統合 |
| Boston Dynamics | — (Hyundai) | bostondynamics.com/blog | Tier 2: 汎用 | Atlas humanoid |
| Figure AI | — | figure.ai/news | Tier 2: 汎用 | Helix humanoid、物流向け |
| Physical Intelligence | — | physicalintelligence.company | Tier 2: 汎用 | 汎用ロボット基盤モデル |
| Agility Robotics | — | agilityrobotics.com/about/press | Tier 2: 汎用 | Digit humanoid、倉庫自動化 |
| Symbotic | SYM | symbotic.com/innovation-insights/blog | Tier 2: 汎用 | AI倉庫自動化 |

### カテゴリ9: SaaS・AI活用ソフトウェア（10社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| Salesforce | CRM | salesforce.com/blog | Tier 2: 汎用 | Einstein AI、Agentforce |
| ServiceNow | NOW | servicenow.com/community/.../blog | Tier 2: 汎用 | ワークフロー自動化 × AI |
| Palantir | PLTR | blog.palantir.com | Tier 2: 汎用 | データ分析、政府AI |
| Snowflake | SNOW | snowflake.com/en/engineering-blog | Tier 2: 汎用 | AI data cloud |
| Datadog | DDOG | datadoghq.com/blog | Tier 2: 汎用 | AI observability |
| CrowdStrike | CRWD | crowdstrike.com/en-us/blog | Tier 2: 汎用 | AI脅威検出 |
| MongoDB | MDB | mongodb.com/company/blog | Tier 2: 汎用 | Vector search |
| UiPath | PATH | uipath.com/newsroom | Tier 2: 汎用 | Agentic automation |
| C3.ai | AI | c3.ai/blog | Tier 2: 汎用 | エンタープライズAI |
| Databricks | — | databricks.com/blog | Tier 2: 汎用 | Unified AI governance |

### カテゴリ10: AI基盤・MLOps（7社）

| 企業 | ティッカー | ブログ/ニュースURL | 取得ティア | 投資関連性 |
|------|----------|------------------|----------|-----------|
| HuggingFace | — | huggingface.co/blog | Tier 2: 汎用 | OSS model hub、評価45億ドル |
| Scale AI | — | scale.com/blog | Tier 2: 汎用 | データラベリング、agentic AI |
| Weights & Biases | — | wandb.ai/fully-connected/blog | Tier 2: 汎用 | ML実験管理 |
| Together AI | — | together.ai/blog | Tier 2: 汎用 | OSS推論、Refuel.ai買収 |
| Anyscale | — | anyscale.com/blog | Tier 2: 汎用 | Ray framework |
| Replicate | — | replicate.com/blog | Tier 2: 汎用 | モデルホスティング |
| Elastic | ESTC | elastic.co/blog | Tier 2: 汎用 | Search × AI agent |

### 集計

| カテゴリ | 社数 | Tier 1 (RSS) | Tier 2 (汎用) | Tier 3 (アダプタ) |
|---------|------|-------------|-------------|----------------|
| AI/LLM開発 | 11 | 2 | 8 | 1 |
| GPU・演算チップ | 10 | 1 | 7 | 2 |
| 半導体製造装置 | 6 | 0 | 6 | 0 |
| DC・クラウドインフラ | 7 | 0 | 6 | 1 |
| ネットワーキング | 2 | 1 | 1 | 0 |
| 電力・エネルギー | 7 | 3 | 4 | 0 |
| 原子力・核融合 | 8 | 0 | 8 | 0 |
| フィジカルAI | 9 | 1 | 7 | 1 |
| SaaS | 10 | 0 | 10 | 0 |
| AI基盤・MLOps | 7 | 0 | 7 | 0 |
| **合計** | **77** | **8** | **64** | **5** |

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

### ティアベース・スクレイピング戦略

70社以上をカバーするため、**全企業に個別アダプタを書かない**。3ティアで効率的に処理する。

```
Tier 1: RSS（8社）
  └── FeedReader で取得。アダプタ不要。最も安定・高速。
      例: NVIDIA, Microsoft AI, Bloom Energy, Schneider Electric

Tier 2: 汎用スクレイパー（64社）
  └── RobustScraper + trafilatura で本文抽出。
      標準的なブログ/ニュースルーム構造に対応。
      bot対策（UA/レートリミット/429リトライ）込み。
      例: OpenAI, AMD, TSMC, Constellation Energy

Tier 3: 企業別アダプタ（5社）
  └── SPA/JS-heavy等、汎用では取得困難なサイト専用。
      BaseCompanyScraper を継承した個別実装。
      例: Perplexity AI, Cerebras, SambaNova, Lambda Labs, Fanuc
```

### 全体構成

```
/ai-research-collect
  → ai-research-workflow スキル（Deep Researchスキルの拡張）
    → Phase 1: Python CLI (prepare_ai_research_session.py)
        ├── Tier 1: FeedReader → RSS対応企業（8社）
        ├── Tier 2: RobustScraper → 汎用スクレイピング（64社）
        │   ├── 共通bot対策基盤
        │   │   ├── 7種UAローテーション（直前UA回避）
        │   │   ├── ドメイン別レートリミット（asyncio.Lock排他制御）
        │   │   ├── 429リトライ（Retry-After対応、指数バックオフ2→4→8秒）
        │   │   └── 3段階フォールバック: trafilatura → Playwright → lxml
        │   └── 構造化ログ（utils_core.logging）+ エラーハンドリング
        └── Tier 3: CompanyScraper → 企業別アダプタ（5社）
            └── BaseCompanyScraper 継承、ページ構造特化の抽出ロジック
    → Phase 2: AI（ai-research-article-fetcher × カテゴリ並列）
        └── 投資視点での要約生成 + 市場影響度判定 + Issue作成
    → Phase 3: 結果集約 + スクレイピング統計レポート
```

### Python → AI 役割分担

| Python側（決定論的） | AI側（高度判断） |
|---------------------|-----------------|
| RSS/Webスクレイピング（77社） | タイトル翻訳（英→日） |
| ティア別取得ルーティング | 投資視点4セクション要約生成 |
| 日付フィルタリング | 市場影響度判定（low/medium/high） |
| URLベース重複チェック | 関連銘柄・セクターの特定 |
| Top-N選択（公開日時降順） | Issue本文の文章構成 |
| カテゴリ別JSON出力 | |
| スクレイピング統計レポート | |
| 構造化ログ出力 | |

### データフロー

```
ユーザー: /ai-research-collect --days 7 --categories all --top-n 10
  │
  ▼ Phase 1 (Python)
  prepare_ai_research_session.py
    ├── ai-research-companies.json 読み込み（77社の定義）
    ├── カテゴリ別・ティア別にデータ収集:
    │   ├── Tier 1: FeedReader → RSS記事
    │   ├── Tier 2: RobustScraper → 汎用スクレイピング
    │   └── Tier 3: CompanyScraperRegistry → 企業別アダプタ
    ├── → ArticleData統一形式に変換
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
  カテゴリ別統計 + ティア別成功率 + スクレイピング統計サマリー
```

---

## コンポーネント詳細

### 1. ティアベース取得システム

#### Tier 1: RSS取得（FeedReader）

既存の `src/rss/services/feed_reader.py` をそのまま利用。新規コード不要。

**対象8社**: NVIDIA, Microsoft AI, Google DeepMind, Cisco, Bloom Energy, Schneider Electric, nVent Electric, Intuitive Surgical

#### Tier 2: 汎用スクレイパー（RobustScraper）

**パス**: `src/rss/services/company_scrapers/robust_scraper.py`

64社の標準的なブログ/ニュースルームからテキスト抽出。trafilatura ベースで大半のサイトに対応。

```python
class RobustScraper:
    def __init__(
        self,
        domain_rate_limits: dict[str, float],
        user_agents: list[str] | None = None,
        max_retries: int = 3,
        use_playwright: bool = True,
    ) -> None:
        self._logger = get_logger(__name__, component="robust_scraper")
        ...

    async def fetch_page(self, url: str) -> str:
        """URLからHTMLを取得（bot対策込み）."""
        ...

    async def scrape(self, url: str) -> ScrapedArticle:
        """URLからテキスト抽出まで実行."""
        ...

    async def scrape_batch(self, urls: list[str]) -> list[ScrapedArticle]:
        """複数URL一括スクレイピング."""
        ...

    def get_stats(self) -> ScrapeStats:
        """スクレイピング統計を返す."""
        ...
```

**bot対策**: UA ローテーション（7種）、ドメイン別レートリミット、429リトライ（指数バックオフ）、3段階フォールバック（trafilatura → Playwright → lxml）

#### Tier 3: 企業別アダプタ（CompanyScraper）

**パス**: `src/rss/services/company_scrapers/adapters/`

SPA/JS-heavy 等の特殊サイト向け。`BaseCompanyScraper` を継承。

**対象5社**: Perplexity AI, Cerebras, SambaNova, Lambda Labs, Fanuc

```python
class BaseCompanyScraper(ABC):
    """企業別スクレイパーの基底クラス."""

    def __init__(self, robust_scraper: RobustScraper) -> None:
        self._scraper = robust_scraper
        self._logger = get_logger(f"{__name__}.{self.company_key}", company=self.company_key)

    @property
    @abstractmethod
    def company_key(self) -> str: ...

    @property
    @abstractmethod
    def blog_url(self) -> str: ...

    @abstractmethod
    async def extract_article_list(self, html: str) -> list[ArticleMetadata]: ...

    @abstractmethod
    async def extract_article_content(self, html: str, url: str) -> ArticleContent: ...

    async def scrape_latest(self, max_articles: int = 10) -> list[ScrapedArticle]:
        """最新記事を取得（共通フロー）."""
        ...
```

### 2. ai-research-companies.json（企業定義マスタ）

**パス**: `data/config/ai-research-companies.json`

77社全ての定義を一元管理。ティア、URL、投資コンテキストを含む。

```json
{
  "categories": {
    "ai_llm": {
      "label": "AI/LLM開発",
      "github_label": "ai-llm",
      "companies": [
        {
          "key": "openai",
          "name": "OpenAI",
          "tier": 2,
          "urls": {
            "blog": "https://openai.com/news/",
            "newsroom": null,
            "rss": null
          },
          "playwright_required": false,
          "investment_context": {
            "tickers": ["MSFT"],
            "sectors": ["Software", "Cloud"],
            "keywords": ["ChatGPT", "GPT", "API pricing", "enterprise"]
          }
        },
        {
          "key": "nvidia_ai",
          "name": "NVIDIA",
          "tier": 1,
          "urls": {
            "blog": "https://blogs.nvidia.com/",
            "newsroom": "https://nvidianews.nvidia.com/news",
            "rss": "https://nvidianews.nvidia.com/rss"
          },
          "playwright_required": false,
          "investment_context": {
            "tickers": ["NVDA"],
            "sectors": ["Semiconductor", "Data Center"],
            "keywords": ["GPU", "CUDA", "H100", "Blackwell", "inference"]
          }
        }
      ]
    },
    "gpu_chips": {
      "label": "GPU・演算チップ",
      "github_label": "ai-chips",
      "companies": ["..."]
    },
    "semiconductor_equipment": {
      "label": "半導体製造装置",
      "github_label": "ai-semicon",
      "companies": ["..."]
    },
    "data_center": {
      "label": "データセンター・クラウド",
      "github_label": "ai-datacenter",
      "companies": ["..."]
    },
    "networking": {
      "label": "ネットワーキング",
      "github_label": "ai-network",
      "companies": ["..."]
    },
    "power_energy": {
      "label": "電力・エネルギー",
      "github_label": "ai-power",
      "companies": ["..."]
    },
    "nuclear_fusion": {
      "label": "原子力・核融合",
      "github_label": "ai-nuclear",
      "companies": ["..."]
    },
    "physical_ai": {
      "label": "フィジカルAI・ロボティクス",
      "github_label": "ai-robotics",
      "companies": ["..."]
    },
    "saas": {
      "label": "SaaS・AI活用ソフトウェア",
      "github_label": "ai-saas",
      "companies": ["..."]
    },
    "ai_infra": {
      "label": "AI基盤・MLOps",
      "github_label": "ai-infra",
      "companies": ["..."]
    }
  },
  "default_scraper_config": {
    "domain_rate_limits": {
      "openai.com": 5.0,
      "blog.google": 5.0,
      "ai.meta.com": 5.0,
      "anthropic.com": 5.0,
      "blogs.microsoft.com": 5.0,
      "developer.nvidia.com": 5.0,
      "huggingface.co": 3.0,
      "__default__": 3.0
    },
    "max_retries": 3,
    "use_playwright": true
  },
  "project": { "...": "GitHub Project設定（ID, フィールドID等）" },
  "execution": {
    "batch_size": 10,
    "max_articles_per_company": 5,
    "max_articles_per_category": 20,
    "concurrent_categories": 3
  }
}
```

### 3. ログ・エラーハンドリング設計

**ログ基盤**: `utils_core.logging`（structlog ベース）

#### ログ出力方針

```python
from utils_core.logging import get_logger, log_context, log_performance

logger = get_logger(__name__, component="ai_research")

# カテゴリ・企業レベルのコンテキスト
with log_context(phase="data_collection", category="gpu_chips", company="nvidia"):
    logger.info("Scraping started", tier=1, url="https://blogs.nvidia.com/")

# パフォーマンス計測
@log_performance(logger)
async def scrape_category(category_key: str) -> list[ScrapedArticle]:
    ...
```

#### ログレベル使い分け

| レベル | 用途 |
|--------|------|
| DEBUG | HTTP応答詳細、HTMLパース中間結果、フォールバック遷移 |
| INFO | カテゴリ開始/完了、企業別取得成功、Issue作成成功 |
| WARNING | 429レートリミット、Playwright未インストール、部分失敗 |
| ERROR | スクレイピング完全失敗、Issue作成失敗、アダプタエラー |
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

class AdapterError(ScrapingError):
    """企業別アダプタの抽出エラー."""

class BotDetectionError(ScrapingError):
    """bot検知によるブロック."""
```

### 4. ai-research-article-fetcher エージェント

**パス**: `.claude/agents/ai-research-article-fetcher.md`

**入力**: `{articles: [ArticleData], issue_config: {...}, investment_context: {...}}`

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
| 新規 | `src/rss/services/company_scrapers/__init__.py` | 2KB |
| 新規 | `src/rss/services/company_scrapers/types.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/robust_scraper.py` | 15KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_types.py` | 5KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_robust_scraper.py` | 18KB |
| 修正 | `src/rss/services/__init__.py` | - |

### Wave 1: 企業別アダプタ（Tier 3: 5社分、Wave 0完了後）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `src/rss/services/company_scrapers/base.py` | 8KB |
| 新規 | `src/rss/services/company_scrapers/adapters/__init__.py` | 1KB |
| 新規 | `src/rss/services/company_scrapers/adapters/perplexity.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/adapters/cerebras.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/adapters/sambanova.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/adapters/lambda_labs.py` | 5KB |
| 新規 | `src/rss/services/company_scrapers/adapters/fanuc.py` | 5KB |
| 新規 | `tests/rss/unit/services/company_scrapers/test_base.py` | 10KB |
| 新規 | `tests/rss/unit/services/company_scrapers/adapters/test_*.py` | 各5KB |

### Wave 2: 企業定義マスタ + セッションスクリプト（Wave 0,1完了後）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `data/config/ai-research-companies.json` | 25KB |
| 新規 | `scripts/prepare_ai_research_session.py` | 25KB |
| 新規 | `.claude/agents/ai-research-article-fetcher.md` | 7KB |
| 修正 | `data/raw/rss/feeds.json`（Tier 1企業のRSS追加） | - |

### Wave 3: スキル定義・テンプレート（Wave 2完了後）

| 操作 | ファイル | サイズ |
|------|---------|--------|
| 新規 | `.claude/skills/ai-research-workflow/SKILL.md` | 8KB |
| 新規 | `.claude/skills/ai-research-workflow/guide.md` | 10KB |
| 新規 | `.claude/skills/ai-research-workflow/templates/issue-template.md` | 4KB |
| 新規 | `.claude/skills/ai-research-workflow/templates/summary-template.md` | 4KB |

### Wave 4: コマンド定義 + ドキュメント更新（全完了後）

| 操作 | ファイル |
|------|---------|
| 新規 | `.claude/commands/ai-research-collect.md` |
| 修正 | `CLAUDE.md`（コマンド/スキル/エージェント一覧に追加） |

---

## 見積もり

| Wave | 内容 | 見積もり |
|------|------|---------|
| Wave 0 | RobustScraper TDD実装 + テスト | 4-5時間 |
| Wave 1 | BaseCompanyScraper + 5社アダプタ TDD | 5-7時間 |
| Wave 2 | 企業定義マスタ(77社) + セッションスクリプト + エージェント | 6-8時間 |
| Wave 3 | スキル定義 + テンプレート | 2-3時間 |
| Wave 4 | コマンド + CLAUDE.md更新 | 1時間 |
| その他 | 企業ブログ構造調査 + RSS確認 + GitHub Project作成 | 3-4時間 |
| **合計** | | **21-28時間** |

---

## リスク分析

| リスク | レベル | 軽減策 |
|--------|--------|--------|
| 77社のURL変更・構造変更 | **高** | ティアベースで影響を局所化、Tier 2汎用で大半をカバー |
| bot検知・WAF強化（特にBigTech） | **高** | 多層防御（UA+ヘッダ+レート+Playwright）+ 構造化ログで早期検知 |
| RobustScraperの非同期制御の複雑さ | **高** | TDDで各機能を個別テスト、独立メソッド切り出し |
| 企業定義マスタの保守コスト | 中 | JSON一元管理、企業追加は定義追加のみ |
| Tier 2で取得できないサイトの増加 | 中 | 定期的にTier 2成功率を監視、必要に応じてTier 3昇格 |
| Playwright統合の安定性 | 中 | オプショナル化 + timeout設定 + 未インストール時スキップ |
| 大量リクエストによるIP制限 | 中 | ドメイン別レートリミット厳守、カテゴリ間の間隔確保 |
| 既存ワークフローへの影響 | 低 | コンポジション（既存変更なし）+ カテゴリ分離 |

---

## 既存コードの再利用

### 直接再利用

- `src/rss/services/article_extractor.py` - RobustScraperのStage 1として
- `src/rss/services/article_content_checker.py` - Playwrightロジック参照
- `src/rss/core/http_client.py` - バックオフ計算パターン
- `src/rss/services/feed_reader.py` - Tier 1 RSS取得
- `src/rss/utils/url_normalizer.py` - URL正規化
- `scripts/prepare_news_session.py` - フィルタリング/重複チェック関数
- `src/utils_core/logging/` - 構造化ログ基盤

### フォーク＆修正

- `prepare_news_session.py` → `prepare_ai_research_session.py`
- `news-article-fetcher.md` → `ai-research-article-fetcher.md`
- `finance-news-workflow/SKILL.md` → `ai-research-workflow/SKILL.md`
- `finance-news-themes.json` → `ai-research-companies.json`

### 新規実装

- **RobustScraper**: UA+レートリミット+429+bot検知+フォールバック+統計
- **BaseCompanyScraper + CompanyScraperRegistry**: Tier 3基盤
- **企業別アダプタ**: 5社分の個別パーシングロジック
- **企業定義マスタ**: 77社のJSON定義
- **ティアルーティング**: Tier 1/2/3の自動振り分け
- **データクラス**: ScrapedArticle, ArticleMetadata, ArticleContent 等
- **カスタム例外**: ScrapingError → RateLimitError / AdapterError / BotDetectionError
- **投資視点4セクション要約**（概要/技術的意義/市場影響/投資示唆）
- **カテゴリ別ラベリング + 関連銘柄タグ付け**

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

# 7. 取得したIDを ai-research-companies.json に反映
```

---

## MVPスコープ

### 含む

- RobustScraper（UA+レートリミット+429+bot検知+フォールバック+統計）
- BaseCompanyScraper + CompanyScraperRegistry（Tier 3基盤）
- 企業別アダプタ 5社分（Perplexity, Cerebras, SambaNova, Lambda Labs, Fanuc）
- 企業定義マスタ 77社分（10カテゴリ）
- ティアベース取得ルーティング（Tier 1/2/3自動振り分け）
- 単体テスト（80%以上カバレッジ）
- Tier 1: RSS取得（8社）
- Tier 2: 汎用スクレイピング（64社）
- ArticleData統一形式変換
- 日付フィルタリング + 重複チェック + Top-N選択
- **投資視点**AI要約生成 + Issue作成
- カテゴリ別ラベリング + 関連銘柄タグ付け
- GitHub Project連携
- `/ai-research-collect` コマンド
- スクレイピング統計レポート（ティア別成功率含む）
- `utils_core.logging` によるstructlogベースの構造化ログ
- カスタム例外階層（ScrapingError系）

### Phase 2以降（除外）

- **arXiv論文取得**（arXiv API + feedparser）
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

- **ティアベースアーキテクチャ**: RSS(8社) → 汎用(64社) → アダプタ(5社)で77社をカバー
- **全企業に個別アダプタを書かない**: Tier 2汎用スクレイパーで大半をカバー
- **企業定義はJSONマスタで一元管理**: 企業追加はJSON追記のみ
- **10カテゴリで投資バリューチェーン全体をカバー**: LLM〜核融合まで
- **既存ArticleExtractorは変更しない**: RobustScraperがコンポジションでラップ
- **Playwrightはオプショナル**: 未インストール環境でも動作可能
- **GitHub Projectは完全独立**: 金融ニュースProject #15とは分離
- **Deep Researchの拡張として位置付け**: `/deep-research --type theme` のデータソース自動化
- **投資家視点の要約**: 4セクション（概要/技術的意義/市場影響/投資示唆）
- **arXivはPhase 2以降**: MVPでは企業ブログ・リリースに集中
- **ログは utils_core.logging**: structlogベースの構造化ログを全コンポーネントで使用
- **エラーは階層的カスタム例外**: ScrapingError → RateLimitError / AdapterError / BotDetectionError
