# finance_news_workflow のログ品質・運用改善

## 問題概要

2026-02-07 の実行ログ（`logs/news-workflow-2026-02-07.log`）を解析した結果、以下の運用上の問題を特定した。

### ログ解析結果サマリー

| 指標 | 値 |
|------|-----|
| ログ行数 | 53,774行（10.6MB） |
| 収集記事数 | 552件（31フィード成功、1フィード失敗） |
| 抽出失敗 | 224件（うち211件が「Body text too short or empty」） |
| 要約失敗 | 73件（全て JSON parse error） |
| 重複検出（Publish時） | 72件 |
| Issue作成 | 131件 |
| ERROR | 60件（403 Forbidden: 30、ReadTimeout: 30） |
| WARNING | 446件（Connection pool full: 380、discarding data: 6） |

### 根本原因の分類

#### 1. ログノイズ（全体の70%以上）

`httpcore` の DEBUG ログが **15,164行**（全体の28%）、`urllib3.connectionpool` の Connection pool full 警告が **380件**。ワークフロー固有のログが埋もれて運用時の問題追跡が困難。

```
# httpcore のDEBUGログ例（1リクエストあたり約10行出力される）
2026-02-07T07:35:10.475045+00:00 [DEBUG] connect_tcp.started host='hnrss.org' port=443 ...
2026-02-07T07:35:10.955323+00:00 [DEBUG] connect_tcp.complete return_value=<...>
2026-02-07T07:35:10.958747+00:00 [DEBUG] start_tls.started ssl_context=<...>
2026-02-07T07:35:11.368711+00:00 [DEBUG] start_tls.complete return_value=<...>
2026-02-07T07:35:11.372487+00:00 [DEBUG] send_request_headers.started ...
2026-02-07T07:35:11.375878+00:00 [DEBUG] send_request_headers.complete
2026-02-07T07:35:11.377701+00:00 [DEBUG] send_request_body.started ...
2026-02-07T07:35:11.379500+00:00 [DEBUG] send_request_body.complete
2026-02-07T07:35:11.381073+00:00 [DEBUG] receive_response_headers.started ...
2026-02-07T07:35:11.758843+00:00 [DEBUG] receive_response_headers.complete ...
```

#### 2. ワークフロー完了サマリーの欠如

`run_workflow()` の成功時ログが `logger.debug` レベルのため、通常実行時（console=INFO）ではコンソールに結果が表示されない。ログファイルの末尾にも最終サマリーが記録されていない。

```python
# 現在のコード（debug レベル）
logger.debug(
    "Workflow completed successfully",
    total_collected=result.total_collected,
    total_published=result.total_published,
    elapsed_seconds=result.elapsed_seconds,
)
```

#### 3. 同一URL記事の重複Issue作成

`este-lauder-el-tariffs.html` が Issue #3225（category=finance）と Issue #3226（category=stock）の両方で作成されている。Publisher のバッチ内重複チェックが不十分。

```
53723:[info] Issue created successfully issue_number=3225 article_url=.../este-lauder-el-tariffs.html
53731:[info] Issue created successfully issue_number=3226 article_url=.../este-lauder-el-tariffs.html
```

#### 4. 403ドメインへの無駄なリトライ

以下のドメインは常に403を返すが、リトライが実行されログが膨張する。

| ドメイン | 失敗回数 | エラー種別 |
|----------|----------|-----------|
| `nasdaq.com` | 30件 | ReadTimeout（各30秒待機） |
| `investing.com` | 21件 | 403 Forbidden |
| `nytimes.com` | 3件 | 403 Forbidden |
| `investors.com` | 3件 | 403 Forbidden |

nasdaq.com の30件タイムアウトだけで **最低15分** のワークフロー遅延が発生。

#### 5. CNBC記事の大量抽出失敗

211件の「Body text too short or empty」のうち、大半がCNBC記事。ペイウォールまたはJavaScript依存のコンテンツが原因の可能性が高い。

---

## 改善計画

### Issue 1: サードパーティライブラリのログ抑制

**優先度**: 高（ログ量70%削減見込み）

#### 対象ファイル

- `src/news/scripts/finance_news_workflow.py` の `setup_logging()` 関数

#### 変更内容

`setup_logging()` 内で、ノイズの多いサードパーティロガーのログレベルを引き上げる。

```python
# 抑制対象のサードパーティロガー
NOISY_LOGGERS = {
    "httpcore": logging.WARNING,
    "httpcore.connection": logging.WARNING,
    "httpcore.http11": logging.WARNING,
    "httpx": logging.WARNING,
    "urllib3": logging.WARNING,
    "urllib3.connectionpool": logging.ERROR,
    "trafilatura": logging.WARNING,
    "trafilatura.downloads": logging.WARNING,
    "trafilatura.core": logging.WARNING,
}
```

#### 期待効果

| 指標 | 変更前 | 変更後（推定） |
|------|--------|---------------|
| ログ行数 | 53,774行 | 約16,000行 |
| ファイルサイズ | 10.6MB | 約3MB |
| httpcore ログ | 15,164行 | 0行 |
| urllib3 警告 | 380行 | 0行 |

#### 受け入れ条件

- [ ] `setup_logging()` 内でサードパーティロガーのレベルが設定されている
- [ ] ワークフロー自体のDEBUGログ（`news.*` モジュール）は引き続きファイルに出力される
- [ ] `--verbose` オプション指定時もサードパーティロガーは抑制される（`--verbose` はワークフローのDEBUGのみ対象）
- [ ] 既存テストが全て通る

---

### Issue 2: ワークフロー完了サマリーの改善

**優先度**: 高（運用監視に必須）

#### 対象ファイル

- `src/news/scripts/finance_news_workflow.py` の `run_workflow()` 関数
- `src/news/scripts/finance_news_workflow.py` の `print_failure_summary()` 関数

#### 変更内容

##### 2a. 完了サマリーを INFO レベルに変更し、全主要メトリクスを出力

```python
# run_workflow() 内
logger.info(
    "Workflow completed",
    total_collected=result.total_collected,
    total_extracted=result.total_extracted,
    total_summarized=result.total_summarized,
    total_published=result.total_published,
    total_duplicates=result.total_duplicates,
    extraction_failures=len(result.extraction_failures),
    summarization_failures=len(result.summarization_failures),
    publication_failures=len(result.publication_failures),
    elapsed_seconds=result.elapsed_seconds,
)
```

##### 2b. `print_failure_summary()` の内容をログにも出力

現在 `print()` のみで出力しており、ログファイルに残らない。`logger.warning()` を併用する。

```python
def print_failure_summary(result: WorkflowResult) -> None:
    # ... 既存の print() に加えて ...
    if total_failures > 0:
        logger.warning(
            "Workflow completed with failures",
            extraction_failures=len(result.extraction_failures),
            summarization_failures=len(result.summarization_failures),
            publication_failures=len(result.publication_failures),
            total_failures=total_failures,
        )
```

#### 受け入れ条件

- [ ] ワークフロー完了時に INFO レベルで全メトリクスがログ出力される
- [ ] 失敗がある場合は WARNING レベルで失敗件数がログ出力される
- [ ] `print()` による人間向け出力も引き続き機能する
- [ ] 既存テストが全て通る

---

### Issue 3: バッチ内URL重複チェックの強化

**優先度**: 中（データ品質への直接的影響）

#### 対象ファイル

- `src/news/publisher.py` の `publish_batch()` メソッド

#### 変更内容

`publish_batch()` 内で、既存Issue URLだけでなく **現在のバッチ内で既に公開済みのURL** もチェックする。

```python
async def publish_batch(self, articles, dry_run=False):
    existing_urls = await self._get_existing_issues(days=7)
    batch_published_urls: set[str] = set()  # バッチ内重複検出用

    for article in articles:
        url = str(article.url)
        if self._is_duplicate(article, existing_urls) or url in batch_published_urls:
            # 重複としてスキップ
            ...
            continue

        # 公開処理
        result = await self.publish(article, dry_run=dry_run)
        if result.publication_status == PublicationStatus.SUCCESS:
            batch_published_urls.add(url)
        results.append(result)
```

#### 受け入れ条件

- [ ] 同一バッチ内で同じURLの記事が複数回Issueとして作成されない
- [ ] バッチ内重複はログに記録される
- [ ] 既存の重複チェック（既存Issue vs 新規記事）は引き続き動作する
- [ ] 既存テストが全て通る

---

### Issue 4: 抽出スキップドメインの設定サポート

**優先度**: 中（不要リトライとログ膨張の防止）

#### 対象ファイル

- `data/config/news-collection-config.yaml`（設定追加）
- `src/news/config/models.py`（設定モデル追加）
- `src/news/orchestrator.py`（フィルタリング実装）

#### 変更内容

##### 4a. 設定ファイルにスキップドメインリストを追加

```yaml
extraction:
  skip_domains:
    - "nytimes.com"
    - "investors.com"
    - "investing.com"
```

##### 4b. Orchestrator で抽出前にドメインフィルタリング

```python
# orchestrator.py の _extract_batch_with_progress() 前段
def _should_skip_extraction(self, url: str) -> bool:
    """既知の失敗ドメインをスキップ判定する。"""
    skip_domains = self._config.extraction.skip_domains or []
    parsed = urlparse(url)
    return any(domain in parsed.netloc for domain in skip_domains)
```

##### 4c. スキップされた記事はRSSの `summary` をフォールバックとして使用

抽出をスキップした記事は、RSSフィードの `summary` フィールドを本文として使い、要約→公開のパイプラインに乗せる。完全スキップではなく、品質は落ちるが記事は公開される。

#### 受け入れ条件

- [ ] 設定ファイルで `skip_domains` を指定できる
- [ ] 該当ドメインの記事は抽出をスキップし、RSS summary をフォールバックとして使用する
- [ ] スキップした記事のログが INFO レベルで出力される
- [ ] 設定が空の場合は既存動作と同じ（全記事を抽出）
- [ ] 既存テストが全て通る

---

### Issue 5: ステージ間の進捗ログ追加

**優先度**: 低（運用利便性の向上）

#### 対象ファイル

- `src/news/scripts/finance_news_workflow.py` の `run_workflow()` 関数

#### 変更内容

各ステージの開始・終了をINFOレベルでログ出力する。現在は orchestrator 内部のログに依存しているが、スクリプト側でもステージ単位の所要時間を記録する。

```python
async def run_workflow(...) -> int:
    ...
    # orchestrator.run() の代わりに、ステージ呼び出しを明示的にログ
    # ※ orchestrator 内部の実装次第で、run() の前後にタイミングログを追加する形でもよい
    import time
    start = time.monotonic()
    result = await orchestrator.run(...)
    elapsed = time.monotonic() - start

    logger.info(
        "Workflow pipeline completed",
        elapsed_seconds=round(elapsed, 1),
    )
```

#### 受け入れ条件

- [ ] ワークフロー全体の所要時間が INFO レベルでログ出力される
- [ ] 既存テストが全て通る

---

### Issue 6: ログファイルのサイズ管理

**優先度**: 低（ディスク管理）

#### 対象ファイル

- `src/news/scripts/finance_news_workflow.py` の `setup_logging()` 関数
- `src/utils_core/logging.py`（必要に応じて）

#### 変更内容

Issue 1 のサードパーティログ抑制により、ファイルサイズは約3MBに削減される見込み。それでも長期運用では増加するため、`RotatingFileHandler` の導入を検討する。

ただし、Issue 1 の効果を測定した上で判断する。Issue 1 で十分な削減が得られれば本 Issue は不要。

#### 受け入れ条件

- [ ] Issue 1 適用後のログサイズを測定し、3MB以下であれば本Issueはクローズ
- [ ] 3MB超の場合、`RotatingFileHandler`（maxBytes=5MB, backupCount=3）を導入

---

## 実装順序

```
Issue 1（ログ抑制） ─── 最優先、他に依存なし
  │
  ├── Issue 2（完了サマリー） ─── Issue 1 と並行可能
  │
  ├── Issue 5（進捗ログ） ─── Issue 2 と一緒に実装可能
  │
  └── Issue 6（ログサイズ管理） ─── Issue 1 の効果測定後に判断

Issue 3（バッチ内重複） ─── 独立して実装可能
Issue 4（スキップドメイン） ─── 独立して実装可能
```

### 推奨実装フロー

1. **Phase 1**: Issue 1 + Issue 2 + Issue 5（ログ品質の基盤改善）
2. **Phase 2**: Issue 3 + Issue 4（データ品質・パフォーマンス改善）
3. **Phase 3**: Issue 6（効果測定後の判断）

---

## 関連ファイル

| ファイル | 役割 |
|----------|------|
| `src/news/scripts/finance_news_workflow.py` | CLIエントリポイント、ログ設定 |
| `src/news/orchestrator.py` | パイプライン制御 |
| `src/news/publisher.py` | GitHub Issue作成、重複チェック |
| `src/news/summarizer.py` | 記事要約（Claude SDK） |
| `src/news/config/models.py` | 設定モデル |
| `data/config/news-collection-config.yaml` | ワークフロー設定 |
| `src/utils_core/logging.py` | ログ設定ユーティリティ |
| `docs/project/project-32/project.md` | 関連プロジェクト（RSS UA / Summarizer 空レスポンス / 重複チェック前倒し） |

## 関連プロジェクト

- **project-32**: `finance_news_workflow` の信頼性向上（RSS UA / Summarizer 空レスポンス / 重複チェック前倒し）
  - project-32 で対応済みの RSS UA 設定やSummarizer空レスポンス対策は本プロジェクトのスコープ外
  - Issue 3（バッチ内重複）は project-32 の重複チェック前倒しとは異なる問題（同一バッチ内の重複）
