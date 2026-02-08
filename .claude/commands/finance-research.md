---
description: 金融記事のリサーチワークフローを実行します。データ収集→分析→検証→可視化の一連の処理を自動化します。
argument-hint: --article <article_id> [--depth auto|shallow|deep] [--parallel] [--use-teams]
---

金融記事のリサーチワークフローを実行します。

## 実装切り替え（--use-teams）

| フラグ | 実装 | エージェント | 説明 |
|--------|------|-------------|------|
| なし（デフォルト） | 旧実装 | Task ベース（12エージェント逐次/並列起動） | コマンド内で Phase 1〜5 を制御 |
| `--use-teams` | 新実装 | `research-lead` + Agent Teams | 12チームメイトを依存関係グラフで管理 |

### ルーティングロジック

```
引数に --use-teams が含まれる？
├── Yes → research-lead（Agent Teams）を起動
│         └── TeamCreate → 12タスク登録 → チームメイト起動 → 監視 → シャットダウン
└── No  → 旧実装で実行（以下の Phase 1〜5 を従来通り実行）
```

### --use-teams 使用時

`--use-teams` が指定された場合、パラメータをパースした後に `research-lead` エージェントに制御を委譲します。

```yaml
委譲先: research-lead
渡すパラメータ:
  - article_id: 記事ID
  - depth: リサーチ深度（auto/shallow/deep）
  - force: 強制再実行フラグ

委譲方法: |
  research-lead エージェントに以下を伝えて起動:

  ## パラメータ
  - article_id: {article_id}
  - depth: {depth}
  - force: {force}

  research-lead が Agent Teams ワークフローを実行します。
  詳細は .claude/agents/research-lead.md を参照。
```

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| --article | ○ | - | 記事ID（例: market_report_001_us-market-weekly） |
| --depth | - | auto | リサーチ深度（auto/shallow/deep） |
| --parallel | - | true | 並列処理モード |
| --force | - | false | 強制再実行（既存データを上書き） |
| --use-teams | - | false | Agent Teams 版で実行。research-lead + 12チームメイトによる依存関係ベースのワークフロー |

## 処理フロー（旧実装、デフォルト）

`--use-teams` が指定されていない場合、以下の処理フローを実行します。

```
Phase 1: クエリ生成
├── finance-query-generator → queries.json
└── [自動]

Phase 2: データ収集（並列）
├── finance-market-data → market_data/data.json
├── finance-web → raw-data.json (web_search)
├── finance-wiki → raw-data.json (wikipedia)
├── finance-sec-filings → raw-data.json (sec_filings)
└── [HF2] データ確認（任意）

Phase 3: データ処理
├── finance-source → sources.json
└── finance-claims → claims.json

Phase 3.5: センチメント分析
└── finance-sentiment-analyzer → sentiment_analysis.json

Phase 4: 分析・検証
├── finance-claims-analyzer → analysis.json
├── finance-fact-checker → fact-checks.json
├── finance-decisions → decisions.json
└── [HF3] 主張採用確認（推奨）

Phase 5: 可視化
├── finance-visualize → visualize/
└── [HF4] チャート確認（任意）
```

## 実行手順（旧実装）

### Phase 1: クエリ生成

1. **article-meta.json の確認**
   - 記事フォルダの存在確認
   - カテゴリ、シンボル、期間の取得

2. **finance-query-generator 実行**
   - Task ツールでエージェント起動
   ```
   Task: finance-query-generator
   Input: article_id, topic, category, symbols, date_range
   Output: 01_research/queries.json
   ```

3. **workflow 更新**
   - article-meta.json の workflow.data_collection.queries = "done"

### Phase 2: データ収集（並列）

4. **並列エージェント実行**

   以下を並列で実行（Task ツールを複数同時呼び出し）：

   ```
   Task 1: finance-market-data
   - symbols から株価・指数データ取得
   - fred_series から経済指標取得
   → 01_research/market_data/data.json

   Task 2: finance-web
   - queries.json の web_search を実行
   → 01_research/raw-data.json (web_search セクション)

   Task 3: finance-wiki
   - queries.json の wikipedia を実行
   → 01_research/raw-data.json (wikipedia セクション)

   Task 4: finance-sec-filings
   - symbols から企業のSEC開示情報を取得
   - 決算書、10-K、10-Q、8-Kなどを分析
   → 01_research/raw-data.json (sec_filings セクション)
   ```

5. **workflow 更新**
   - market_data = "done"
   - web_search = "done"
   - wiki_search = "done"
   - sec_filings = "done"

6. **[HF2] データ確認（任意）**
   ```
   データ収集が完了しました。

   収集結果:
   - 市場データ: {count}件
   - Web検索: {count}件
   - Wikipedia: {count}件
   - SEC開示情報: {count}件

   データを確認しますか？ (y/n)
   確認する場合は raw-data.json を表示します。
   ```

### Phase 3: データ処理

7. **finance-source 実行**
   ```
   Task: finance-source
   Input: raw-data.json
   Output: sources.json, article-meta.json (tags更新)
   ```

8. **finance-claims 実行**
   ```
   Task: finance-claims
   Input: sources.json
   Output: claims.json
   ```

9. **workflow 更新**
   - sources = "done"
   - claims = "done"

### Phase 3.5: センチメント分析

10. **finance-sentiment-analyzer 実行**
    ```
    Task: finance-sentiment-analyzer
    Input: raw-data.json (web_search, sec_filings), sources.json
    Output: sentiment_analysis.json
    ```

11. **workflow 更新**
    - sentiment_analysis = "done"

### Phase 4: 分析・検証

12. **分析エージェント実行**

    カテゴリに応じて適切なエージェントを実行：

    ```
    # market_report, stock_analysis, quant_analysis の場合
    Task: finance-technical-analysis
    Input: market_data/data.json
    Output: technical_analysis.json

    # economic_indicators, market_report の場合
    Task: finance-economic-analysis
    Input: market_data/data.json
    Output: economic_analysis.json
    ```

13. **検証エージェント実行（並列）**

    ```
    Task 1: finance-claims-analyzer
    Input: claims.json, sources.json
    Output: analysis.json

    Task 2: finance-fact-checker
    Input: claims.json, sources.json
    Output: fact-checks.json
    ```

14. **finance-decisions 実行**
    ```
    Task: finance-decisions
    Input: claims.json, fact-checks.json
    Output: decisions.json
    ```

15. **[HF3] 主張採用確認（推奨）**
    ```
    分析が完了しました。

    主張の採用判定結果:
    - 採用 (accept): {count}件
    - 不採用 (reject): {count}件
    - 保留 (hold): {count}件

    採用判定を確認・修正しますか？ (y/n)
    確認する場合は decisions.json を表示します。
    ```

16. **workflow 更新**
    - analysis = "done"
    - fact_checks = "done"
    - decisions = "done"

### Phase 5: 可視化

17. **finance-visualize 実行**
    ```
    Task: finance-visualize
    Input: claims.json, decisions.json, market_data/data.json, sentiment_analysis.json
    Output: visualize/summary.md, visualize/charts/
    ```

18. **[HF4] チャート確認（任意）**
    ```
    可視化が完了しました。

    生成されたファイル:
    - visualize/summary.md
    - visualize/charts/ ({count}件)

    チャートを確認しますか？ (y/n)
    ```

19. **workflow 更新**
    - visualize = "done"

## 完了報告

```markdown
## リサーチ完了

### 記事情報
- **記事ID**: {article_id}
- **トピック**: {topic}

### 収集結果
- 市場データ: {market_data_count}件
- Webソース: {web_count}件
- Wikipedia: {wiki_count}件
- SEC開示情報: {sec_count}件

### 分析結果
- 抽出した主張: {claims_count}件
- センチメント分析: {sentiment_score}
- 採用判定:
  - 採用: {accept_count}件
  - 不採用: {reject_count}件
  - 保留: {hold_count}件

### 生成ファイル
- `01_research/queries.json`
- `01_research/raw-data.json`
- `01_research/market_data/data.json`
- `01_research/sources.json`
- `01_research/claims.json`
- `01_research/sentiment_analysis.json`
- `01_research/analysis.json`
- `01_research/fact-checks.json`
- `01_research/decisions.json`
- `01_research/visualize/`

### 次のステップ

**記事執筆**: `/finance-edit --article {article_id}`
```

## エラーハンドリング

### 記事フォルダが存在しない

```
エラー: 記事フォルダが存在しません

指定された記事ID: {article_id}
期待されるパス: articles/{article_id}/

対処法:
- /new-finance-article でまず記事フォルダを作成してください
```

### 部分的な失敗

一部のエージェントが失敗しても、可能な限り処理を継続します。
失敗したエージェントは workflow で "failed" とマークされます。

```
警告: 一部の処理が失敗しました

失敗した処理:
- finance-web: ネットワークエラー

成功した処理で続行します。
失敗した処理は後で再実行できます:
/finance-research --article {article_id} --force
```

## 深度オプション

| 深度 | 説明 |
|------|------|
| shallow | 基本的な情報収集のみ。クエリ数を制限。 |
| deep | 詳細な情報収集。追加クエリ生成、複数回の検証。 |
| auto | claims-analyzer の判定に基づいて自動で deep に移行。 |

## 関連コマンド・エージェント

- **前提コマンド**: `/new-finance-article`
- **次のコマンド**: `/finance-edit`

### 旧実装（デフォルト）使用エージェント

| エージェント | 説明 |
|-------------|------|
| `finance-query-generator` | クエリ生成（Phase 1） |
| `finance-market-data` | 市場データ取得（Phase 2） |
| `finance-web` | Web検索（Phase 2） |
| `finance-wiki` | Wikipedia検索（Phase 2） |
| `finance-sec-filings` | SEC開示情報取得（Phase 2） |
| `finance-source` | ソース抽出（Phase 3） |
| `finance-claims` | 主張抽出（Phase 3） |
| `finance-sentiment-analyzer` | センチメント分析（Phase 3.5） |
| `finance-claims-analyzer` | 主張分析（Phase 4） |
| `finance-fact-checker` | ファクトチェック（Phase 4） |
| `finance-decisions` | 採用判定（Phase 4） |
| `finance-visualize` | 可視化（Phase 5） |

### --use-teams モード使用エージェント

| エージェント | 説明 | タスク |
|-------------|------|--------|
| `research-lead` | リーダーエージェント（ワークフロー制御） | - |
| `finance-query-generator` | クエリ生成 | task-1 |
| `finance-market-data` | 市場データ取得 | task-2 |
| `finance-web` | Web検索 | task-3 |
| `finance-wiki` | Wikipedia検索 | task-4 |
| `finance-sec-filings` | SEC開示情報取得 | task-5 |
| `finance-source` | ソース抽出 | task-6 |
| `finance-claims` | 主張抽出 | task-7 |
| `finance-sentiment-analyzer` | センチメント分析 | task-8 |
| `finance-claims-analyzer` | 主張分析 | task-9 |
| `finance-fact-checker` | ファクトチェック | task-10 |
| `finance-decisions` | 採用判定 | task-11 |
| `finance-visualize` | 可視化 | task-12 |

---

# Agent Teams 版（--use-teams）

`--use-teams` を指定すると、`research-lead` エージェントに制御が移譲され、Agent Teams API を使用してリサーチワークフローを実行します。

## --use-teams 処理フロー

```
Phase 1: パラメータ解析（コマンド側で実行）
├── article_id, depth, force の解析
├── 記事フォルダの存在確認
└── research-lead に委譲
    │
    ↓
research-lead（Agent Teams ワークフロー）
├── Phase 1: TeamCreate（research-team）
├── Phase 1.5: 初期化 + [HF1] リサーチ方針確認（必須）
├── Phase 2: タスク登録・依存関係設定
│   ├── 深度に応じた条件付きタスク登録
│   │   ├── shallow: task-1〜7, task-12（8タスク）
│   │   └── deep/auto: task-1〜12（12タスク）
│   └── addBlockedBy で依存関係を宣言的に設定
├── Phase 3: チームメイト起動・タスク割り当て
│   ├── query-generator → market-data & web & wiki & sec-filings（4並列）
│   ├── source-extractor → claims-extractor → sentiment-analyzer
│   ├── claims-analyzer & fact-checker（2並列）
│   └── decision-maker → visualizer
├── Phase 4: 実行監視
│   ├── [HF2] データ確認（任意）
│   ├── [HF3] 主張採用確認（推奨、shallow時スキップ）
│   ├── [HF4] チャート確認（任意）
│   └── auto 深度: gap_score による動的タスク追加判定
└── Phase 5: シャットダウン・クリーンアップ
    ├── 全チームメイトに shutdown_request 送信
    ├── article-meta.json の workflow 更新
    └── TeamDelete でクリーンアップ
```

## --use-teams 使用例

```bash
# Agent Teams 版でリサーチ実行（深度auto）
/finance-research --article market_report_001_us-market-weekly --use-teams

# Agent Teams 版 + shallow モード
/finance-research --article market_report_001_us-market-weekly --depth shallow --use-teams

# Agent Teams 版 + deep モード
/finance-research --article market_report_001_us-market-weekly --depth deep --use-teams

# Agent Teams 版 + 強制再実行
/finance-research --article market_report_001_us-market-weekly --use-teams --force
```

## 旧実装との比較

| 項目 | 旧実装（デフォルト） | 新実装（--use-teams） |
|------|---------------------|----------------------|
| アーキテクチャ | コマンド内で Task ツール逐次/並列呼び出し | Agent Teams（リーダー + 12チームメイト） |
| エージェント | 12エージェントを直接制御 | `research-lead` + 同12エージェント |
| データ受け渡し | Task ツール間の暗黙的な共有 | ファイルベース（research_dir 内、並列書き込み競合対策済み） |
| 並列制御 | Task ツールの同時呼び出し | addBlockedBy による宣言的な依存関係管理 |
| エラーハンドリング | コマンド内で個別処理 | 依存関係マトリックスによる自動制御（必須/任意依存） |
| 深度対応 | コマンド内で条件分岐 | タスク登録の条件分岐 + auto 深度の動的タスク追加 |
| HF ポイント | コマンド内で直接表示 | リーダーがメイン会話でユーザーに提示 |

## 関連ファイル

- **リーダーエージェント**: `.claude/agents/research-lead.md`
- **旧オーケストレーター**: `.claude/agents/deep-research/dr-orchestrator.md`
- **共通パターン**: `docs/agent-teams-patterns.md`
