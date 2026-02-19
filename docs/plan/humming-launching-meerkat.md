# Finance News Workflow 改善計画

## Context

`finance_news_workflow.py` (Python CLI版パイプライン) の改善プロジェクト。現在の課題:

1. **信頼性**: 抽出成功率が56% (273/490) と低い。CNBC anti-scraping (216件失敗)、壊れたフィード4件
2. **パフォーマンス**: 抽出30s/記事、要約60s/記事、公開5s/記事。並列処理の余地あり
3. **GitHub API レート制限**: 記事ごとに1 Issue × 4 API コール = 100記事で400コール。カテゴリ別Issue方式に移行して98%削減

**対象**: Python CLI版 (`orchestrator.py` + `publisher.py`)
**カテゴリ**: 11テーマ → 6カテゴリに統合 (index, stock, sector, macro, ai, finance)

---

## Wave 1: データモデル・設定追加 (基盤)

### 1-1. カテゴリ別モデル追加

**ファイル**: `src/news/models.py`

```python
class CategoryGroup(BaseModel):
    """カテゴリ別にグループ化された記事群。"""
    category: str               # "index", "stock" 等
    category_label: str         # "株価指数", "個別銘柄" 等
    date: str                   # "2026-02-09"
    articles: list[SummarizedArticle]

class CategoryPublishResult(BaseModel):
    """カテゴリ別Issue公開結果。"""
    category: str
    category_label: str
    date: str
    issue_number: int | None
    issue_url: str | None
    article_count: int
    status: PublicationStatus
    error_message: str | None = None
```

### 1-2. WorkflowResult にカテゴリ結果フィールド追加

**ファイル**: `src/news/models.py`

- `category_results: list[CategoryPublishResult]` を追加

### 1-3. 設定にカテゴリラベルと公開形式追加

**ファイル**: `data/config/news-collection-config.yaml`

```yaml
publishing:
  format: "per_category"       # "per_category" | "per_article"
  export_markdown: true        # ローカルMarkdownエクスポート
  export_dir: "data/exports/news-workflow"

category_labels:
  index: "株価指数"
  stock: "個別銘柄"
  sector: "セクター"
  macro: "マクロ経済"
  ai: "AI関連"
  finance: "金融"
```

**ファイル**: `src/news/config/models.py` に対応する Pydantic モデル追加

### 1-4. テスト

- `CategoryGroup`, `CategoryPublishResult` のモデルテスト
- 設定読み込みテスト

---

## Wave 2: カテゴリグルーピング・Markdown生成

### 2-1. ArticleGrouper 実装

**新規ファイル**: `src/news/grouper.py`

```python
class ArticleGrouper:
    """記事をカテゴリ・日付でグループ化。"""

    def __init__(self, status_mapping: dict[str, str], category_labels: dict[str, str]):
        ...

    def group(self, articles: list[SummarizedArticle]) -> list[CategoryGroup]:
        """記事を6カテゴリにグループ化。

        1. 記事の source.category → status_mapping で正規化 (tech→ai, market→index 等)
        2. 日付抽出 (published → YYYY-MM-DD)
        3. (category, date) でグループ化
        4. CategoryGroup リスト返却
        """
```

**既存マッピング** (`news-collection-config.yaml:status_mapping`):
- `tech` → `ai`, `market` → `index`, `finance` → `finance`
- `economy` → `macro`, `earnings` → `stock`, `etfs` → `sector`
- サブテーマ (`macro_cnbc`, `ai_tech` 等) → 親カテゴリに統合

### 2-2. CategoryMarkdownGenerator 実装

**新規ファイル**: `src/news/markdown_generator.py`

```python
class CategoryMarkdownGenerator:
    """カテゴリ別Issue本文Markdownを生成。"""

    def generate_issue_body(self, group: CategoryGroup) -> str:
        """Issue本文のMarkdown生成。"""

    def generate_issue_title(self, group: CategoryGroup) -> str:
        """タイトル: '[株価指数] ニュースまとめ - 2026-02-09'"""
```

**Issue本文テンプレート**:

```markdown
# [{category_label}] ニュースまとめ - {date}

> {article_count}件の記事を収集

## 記事一覧

### 1. {title}
**ソース**: {source} | **公開日**: {published}
**URL**: {url}

#### 概要
{overview}

#### キーポイント
- {point_1}
- {point_2}

#### 市場への影響
{market_impact}

---

### 2. {next_title}
...
```

### 2-3. MarkdownExporter 実装

**場所**: `src/news/markdown_generator.py` に同居

```python
class MarkdownExporter:
    """カテゴリ別MarkdownをローカルファイルにExport。"""

    def export(self, group: CategoryGroup, export_dir: Path) -> Path:
        """data/exports/news-workflow/YYYY-MM-DD/index.md 等に出力。"""
```

### 2-4. テスト

- `ArticleGrouper` の単体テスト + Hypothesis プロパティテスト
- `CategoryMarkdownGenerator` のテスト（出力形式検証）
- `MarkdownExporter` のファイル出力テスト

---

## Wave 3: Publisher リファクタリング (カテゴリ別Issue作成)

### 3-1. publish_category_batch() メソッド追加

**ファイル**: `src/news/publisher.py`

```python
async def publish_category_batch(
    self,
    groups: list[CategoryGroup],
    dry_run: bool = False,
) -> list[CategoryPublishResult]:
    """カテゴリ別にIssueを作成。

    各CategoryGroupにつき1 Issue作成:
    1. 既存Issue検索 (タイトルで重複チェック)
    2. Issue作成 (gh issue create)
    3. Project追加 + Status/Date設定
    """
```

### 3-2. カテゴリ別重複チェック

**ファイル**: `src/news/publisher.py`

```python
async def _check_category_issue_exists(
    self, category_label: str, date: str
) -> int | None:
    """既存のカテゴリIssueを検索。

    検索: gh issue list --search '[{category_label}] ニュースまとめ - {date}'
    """
```

### 3-3. テスト

- `publish_category_batch()` のモックテスト
- 重複チェックのテスト
- dry_run モードのテスト

---

## Wave 4: Orchestrator 統合

### 4-1. orchestrator.py の run() 更新

**ファイル**: `src/news/orchestrator.py`

```python
# 既存パイプライン:
# Collect → Extract → Summarize → Publish (per article)

# 新パイプライン:
# Collect → Extract → Summarize → Group → Export(md) → Publish (per category)
```

変更点:
1. 要約完了後に `ArticleGrouper.group()` 呼び出し
2. `MarkdownExporter.export()` でローカルファイル出力
3. `Publisher.publish_category_batch()` でカテゴリ別Issue作成
4. `WorkflowResult` に `category_results` を追加

### 4-2. CLI オプション追加

**ファイル**: `src/news/scripts/finance_news_workflow.py`

```bash
# 新オプション
--format per-category     # カテゴリ別 (デフォルト)
--format per-article      # 旧方式 (レガシー)
--export-only             # Markdownエクスポートのみ (Issue作成なし)
```

### 4-3. テスト

- Orchestrator 統合テスト（モック）
- CLI引数パーステスト

---

## Wave 5: 信頼性改善

### 5-1. 壊れたフィードの修正

**ファイル**: `data/config/rss-presets.json`

- MarketWatch: URL更新 or 削除
- Yahoo Finance: 429対策（遅延追加）or 削除
- Financial Times: URL更新 or 削除
- CNBC Markets: フォーマット修正 or 削除

### 5-2. ドメイン別レート制限

**新規ファイル**: `src/news/extractors/rate_limiter.py`

```python
class DomainRateLimiter:
    """ドメイン別のリクエスト間隔制御。"""

    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0):
        self._last_request: dict[str, float] = {}

    async def wait(self, domain: str) -> None:
        """前回リクエストからの経過時間に基づき待機。"""
```

### 5-3. User-Agent 改善

**ファイル**: `src/news/extractors/trafilatura.py`

- セッション固定UA（同一ドメインで同じUA使用）
- モバイルUA追加
- Accept-Language, Referer ヘッダーランダム化

### 5-4. テスト

- `DomainRateLimiter` のテスト
- UA ローテーションのテスト

---

## Wave 6: パフォーマンス改善

### 6-1. 要約並列度の向上

**ファイル**: `src/news/orchestrator.py`

- `summarization.concurrency`: 3 → 5 (Claude API の実際のスループットに合わせて調整)

### 6-2. 公開処理の高速化

カテゴリ別Issue方式により自動的に改善:
- 旧: 100記事 × 4コール = 400 API コール
- 新: 6カテゴリ × 4コール = 24 API コール

### 6-3. 重複チェックキャッシュ

**ファイル**: `src/news/publisher.py`

- 既存 `_get_existing_issues()` のレスポンスをメモリキャッシュ
- 同一バッチ内で複数回呼ばない（現在は1回だけ呼んでいるので問題なし）

### 6-4. 実行メトリクス追加

**ファイル**: `src/news/orchestrator.py`

- ステージ別処理時間をログ出力
- ドメイン別抽出成功率のサマリー

---

## Wave 7: テスト・ドキュメント

### 7-1. 統合テスト

**ファイル**: `tests/news/integration/test_category_workflow.py`

- E2E テスト（モック GitHub API）
- カテゴリグルーピング → Markdown生成 → Issue作成の一連フロー

### 7-2. ドキュメント更新

- `src/news/README.md` の更新
- 設定ファイルのコメント追加

---

## 変更ファイル一覧

| ファイル | 変更内容 | Wave |
|---------|---------|------|
| `src/news/models.py` | CategoryGroup, CategoryPublishResult 追加 | 1 |
| `src/news/config/models.py` | PublishingConfig, CategoryLabelsConfig 追加 | 1 |
| `data/config/news-collection-config.yaml` | publishing, category_labels セクション追加 | 1 |
| `src/news/grouper.py` | **新規**: ArticleGrouper | 2 |
| `src/news/markdown_generator.py` | **新規**: CategoryMarkdownGenerator, MarkdownExporter | 2 |
| `src/news/publisher.py` | publish_category_batch(), _check_category_issue_exists() 追加 | 3 |
| `src/news/orchestrator.py` | Group/Export/CategoryPublish ステージ追加 | 4 |
| `src/news/scripts/finance_news_workflow.py` | --format, --export-only オプション追加 | 4 |
| `data/config/rss-presets.json` | 壊れたフィード修正/削除 | 5 |
| `src/news/extractors/rate_limiter.py` | **新規**: DomainRateLimiter | 5 |
| `src/news/extractors/trafilatura.py` | UA改善、ヘッダーランダム化 | 5 |
| `src/news/README.md` | ドキュメント更新 | 7 |

## テストファイル

| テストファイル | Wave |
|--------------|------|
| `tests/news/unit/test_models_category.py` | 1 |
| `tests/news/unit/test_grouper.py` | 2 |
| `tests/news/property/test_grouper_property.py` | 2 |
| `tests/news/unit/test_markdown_generator.py` | 2 |
| `tests/news/unit/test_publisher_category.py` | 3 |
| `tests/news/unit/test_rate_limiter.py` | 5 |
| `tests/news/integration/test_category_workflow.py` | 7 |

---

## 既存コードの再利用

| 既存コード | パス | 再利用方法 |
|-----------|------|-----------|
| `status_mapping` | `news-collection-config.yaml:9-33` | カテゴリ正規化に利用 |
| `github_status_ids` | `news-collection-config.yaml:35-41` | Status設定に利用 |
| `Publisher._add_to_project()` | `publisher.py` | カテゴリIssueのProject追加に流用 |
| `Publisher._get_existing_issues()` | `publisher.py` | 重複チェックの基盤に改修 |
| `_generate_issue_body()` | `publisher.py` | 個別記事用→カテゴリ用に分岐 |

---

## 検証方法

### 1. 単体テスト
```bash
uv run pytest tests/news/unit/test_grouper.py tests/news/unit/test_markdown_generator.py tests/news/unit/test_publisher_category.py -v
```

### 2. 全テスト回帰
```bash
uv run pytest tests/news/ -v
```

### 3. 品質チェック
```bash
make check-all
```

### 4. dry-run 実行
```bash
uv run python -m news.scripts.finance_news_workflow --dry-run --format per-category
```

### 5. Markdown エクスポート確認
```bash
uv run python -m news.scripts.finance_news_workflow --export-only
ls data/exports/news-workflow/2026-02-09/
# → index.md, stock.md, sector.md, macro.md, ai.md, finance.md
```

### 6. 実 Issue 作成テスト (少量)
```bash
uv run python -m news.scripts.finance_news_workflow --max-articles 5 --status index
```

---

## 成功基準

- [ ] 6カテゴリ × 1 Issue/日 でGitHub APIコール98%削減
- [ ] 抽出成功率 56% → 70%以上（レート制限導入による改善）
- [ ] `make check-all` パス
- [ ] 既存テスト全パス + 新規テスト追加
- [ ] dry-run で正しいMarkdown出力を確認
