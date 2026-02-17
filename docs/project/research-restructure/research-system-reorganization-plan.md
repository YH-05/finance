# リサーチシステム再構成計画

## Context

現在 finance プロジェクトには2つのリサーチシステムが並行して存在する:

1. **finance-research** — 記事リサーチ（Agent Teams、research-lead が制御、14エージェント）
2. **deep-research** — 投資分析（旧設計、dr-orchestrator が制御、11エージェント）

両者にはデータ収集・検証ロジックの重複が多く、用途の使い分けも不明確。本計画では:

- **deep-research を4つの独立コマンド+スキルに分割**（/dr-stock, /dr-industry, /dr-macro, /dr-theme）
- **finance-research をレポート・記事執筆に特化**（--format operations|article、--from-research 参照）
- **明確な責務分離**: deep-research = データ分析 → finance-research = コンテンツ作成

---

## アーキテクチャ

### After: 再構成後の全体像

```
[Deep Research（調査・分析）]
/dr-stock   → dr-stock-lead   → research/DR_stock_YYYYMMDD_TICKER/
/dr-industry→ dr-industry-lead → research/DR_industry_YYYYMMDD_SECTOR/
/dr-macro   → dr-macro-lead   → research/DR_macro_YYYYMMDD/
/dr-theme   → dr-theme-lead   → research/DR_theme_YYYYMMDD_TOPIC/
         ↓ ディレクトリ参照
[Finance Research（レポート・記事執筆）]
/finance-research --from-research {id} --format article|operations
         → articles/{article_id}/
```

### エージェント構成

**共有エージェント（全 /dr-* で再利用）:**
- finance-market-data（市場データ取得）
- finance-web（Web検索）
- finance-wiki（Wikipedia検索）
- finance-sec-filings（SEC EDGAR取得）
- dr-cross-validator（クロス検証）
- dr-confidence-scorer（信頼度スコア）
- dr-bias-detector（バイアス検出）
- dr-visualizer（チャート生成）
- dr-report-generator（レポート生成）

**タイプ固有エージェント:**

| /dr-* | 固有分析エージェント | SEC必須 | FRED重視 |
|-------|---------------------|---------|----------|
| /dr-stock | dr-stock-analyzer | Yes | No |
| /dr-industry | dr-sector-analyzer | Top N銘柄 | No |
| /dr-macro | dr-macro-analyzer + finance-economic-analysis | No | Yes |
| /dr-theme | dr-theme-analyzer | 関連銘柄 | No |

**新規 Lead エージェント（4つ、Agent Teams パターン）:**
- dr-stock-lead, dr-industry-lead, dr-macro-lead, dr-theme-lead

---

## 実装ファイル一覧

### 新規作成（20+ファイル）

**コマンド（4つ）:**
- `.claude/commands/dr-stock.md`
- `.claude/commands/dr-industry.md`
- `.claude/commands/dr-macro.md`
- `.claude/commands/dr-theme.md`

**スキル（4ディレクトリ）:**
```
.claude/skills/dr-stock/
├── SKILL.md              # スキル定義
└── templates/
    ├── stock-analysis.md  # 分析テンプレート（既存から移行）
    └── output/            # 出力テンプレート（既存から移行）

.claude/skills/dr-industry/
├── SKILL.md
└── templates/
    ├── industry-analysis.md  # sector-analysis.md をリネーム
    └── output/

.claude/skills/dr-macro/
├── SKILL.md
└── templates/
    ├── macro-analysis.md
    └── output/

.claude/skills/dr-theme/
├── SKILL.md
└── templates/
    ├── theme-analysis.md
    └── output/
```

**Lead エージェント（4つ）:**
- `.claude/agents/deep-research/dr-stock-lead.md`
- `.claude/agents/deep-research/dr-industry-lead.md`
- `.claude/agents/deep-research/dr-macro-lead.md`
- `.claude/agents/deep-research/dr-theme-lead.md`

### 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `.claude/commands/finance-research.md` | `--format operations\|article`, `--from-research {id}` オプション追加 |
| `.claude/agents/research-lead.md` | 参照モード実装、format 切り替え |
| `.claude/skills/deep-research/SKILL.md` | 4スキルへのルーター化（後方互換） |
| `CLAUDE.md` | コマンド・スキル・エージェント一覧更新 |

---

## 各 Lead エージェントのワークフロー設計

### 共通パターン（dr-stock-lead を基準）

```
Phase 0: 初期化
  TeamCreate → リサーチID生成 → ディレクトリ作成 → [HF0] 方針確認

Phase 1: データ収集（並列）
  task-1: finance-market-data → market_data.json
  task-2: finance-web → web_data.json
  task-3: finance-wiki → wiki_data.json
  task-4: finance-sec-filings → sec_data.json  ※タイプにより省略

Phase 2: クロス検証（Phase 1完了後、3並列）
  task-5: dr-cross-validator → cross_validation.json
  task-6: dr-confidence-scorer → confidence_scores.json
  task-7: dr-bias-detector → bias_detection.json
  [HF1] 中間結果確認

Phase 3: 分析（Phase 2完了後）
  task-8: タイプ固有アナライザー → {type}-analysis.json

Phase 4: 出力（Phase 3完了後）
  task-9: dr-report-generator → report.md
  task-10: dr-visualizer → charts/
  [HF2] 最終確認

Phase 5: シャットダウン → TeamDelete
```

### タイプ別の差異

| | Phase 1 | Phase 3 | データソース優先度 | 深度オプション |
|---|---|---|---|---|
| **dr-stock-lead** | 4タスク全て | dr-stock-analyzer | SEC EDGAR > market > Web | quick/standard/comprehensive |
| **dr-industry-lead** | 4タスク全て | dr-sector-analyzer | market > SEC(top N) > Web | quick/standard/comprehensive |
| **dr-macro-lead** | task-4(SEC)省略 + finance-economic-analysis追加 | dr-macro-analyzer | FRED > Web > market | quick/standard/comprehensive |
| **dr-theme-lead** | 4タスク全て | dr-theme-analyzer | Web > SEC(関連銘柄) > market | quick/standard/comprehensive |

### 出力ディレクトリ構造

```
research/{research_id}/
├── research-meta.json       # メタデータ（タイプ、深度、日時等）
├── 01_data_collection/      # Phase 1 出力
│   ├── market_data.json
│   ├── web_data.json
│   ├── wiki_data.json
│   └── sec_data.json
├── 02_validation/           # Phase 2 出力
│   ├── cross_validation.json
│   ├── confidence_scores.json
│   └── bias_detection.json
├── 03_analysis/             # Phase 3 出力
│   └── {type}-analysis.json
└── 05_output/               # Phase 4 出力
    ├── report.md
    ├── metadata.json
    └── charts/
```

---

## finance-research の拡張設計

### 新規オプション

```bash
# 既存（変更なし）
/finance-research --article {id} [--depth auto|shallow|deep]

# 新規: フォーマット指定
/finance-research --article {id} --format operations  # 運用チーム向けレポート
/finance-research --article {id} --format article      # note記事等（デフォルト）

# 新規: deep-research 結果参照
/finance-research --from-research DR_stock_20260210_AAPL --format article
```

### --from-research 時のフロー

```
1. research/{research_id}/ 存在確認
2. research-meta.json 読み込み（タイプ、分析結果の確認）
3. [HF1] 方針確認（参照モードであることを表示）
4. Phase 1〜4 スキップ（データ収集・分析は不要）
5. 分析結果を articles/{article_id}/01_research/ にシンボリックリンク or コピー
6. Phase 5: 可視化（finance-visualize でMermaid図生成）
7. 通常の記事作成フロー（/finance-edit）へ接続
```

### --format による出力の違い

| 要素 | operations | article |
|------|-----------|---------|
| タイトル | レポート形式（日付+対象） | キャッチーで読みやすい |
| Executive Summary | あり（300-500字） | Key Takeaways（3-5項目） |
| 詳細データ表 | あり（全指標） | 主要指標のみ |
| リスクマトリックス | あり | 主要リスク3点に簡略化 |
| 推奨事項 | 具体的アクション | 投資視点の示唆 |
| Appendix | あり（データソース、用語集） | なし |
| 免責事項 | 簡易版 | 完全版（note用） |
| ハッシュタグ | なし | あり |
| 文字数目安 | 5,000-15,000字 | 2,000-4,000字 |

---

## 実装順序

### Wave 1: 基盤（4スキル SKILL.md + テンプレート移行）

並列実行可能。既存テンプレートを各スキルディレクトリに移行しつつ、SKILL.md を作成。

- 1-1. `.claude/skills/dr-stock/` 作成 — `deep-research/research-templates/stock-analysis.md` を移行
- 1-2. `.claude/skills/dr-industry/` 作成 — `sector-analysis.md` を `industry-analysis.md` にリネームして移行
- 1-3. `.claude/skills/dr-macro/` 作成 — `macro-analysis.md` を移行
- 1-4. `.claude/skills/dr-theme/` 作成 — `theme-analysis.md` を移行
- 1-5. 各スキルに `output-templates/` を配置（`note-article.md`, `analysis-report.md`, `investment-memo.md`）

### Wave 2: Lead エージェント（Agent Teams パターン）

Wave 1 完了後。research-lead.md を参考に4つの lead を作成。

- 2-1. `dr-stock-lead.md` — **最初に実装**（他の基準になる）
- 2-2. `dr-industry-lead.md` — 2-1 を参考に
- 2-3. `dr-macro-lead.md` — Phase 1 で SEC 省略 + economic-analysis 追加
- 2-4. `dr-theme-lead.md` — 2-1 を参考に

### Wave 3: コマンド（エントリポイント）

Wave 2 完了後。各コマンドは対応する lead にパラメータを渡すのみ。

- 3-1. `.claude/commands/dr-stock.md`
- 3-2. `.claude/commands/dr-industry.md`
- 3-3. `.claude/commands/dr-macro.md`
- 3-4. `.claude/commands/dr-theme.md`

### Wave 4: finance-research 拡張

Wave 3 と並列実行可能。既存の finance-research を壊さないよう慎重に拡張。

- 4-1. `.claude/commands/finance-research.md` に `--format`, `--from-research` オプション追加
- 4-2. `.claude/agents/research-lead.md` に参照モード + format 切り替え実装

### Wave 5: 統合・ドキュメント

Wave 3, 4 完了後。

- 5-1. `.claude/skills/deep-research/SKILL.md` をルーター化
- 5-2. `CLAUDE.md` のコマンド・スキル・エージェント一覧更新
- 5-3. Quants プロジェクトへの同期（プロジェクト間同期ルール）

---

## 後方互換性

| 旧コマンド | 動作 |
|-----------|------|
| `/finance-research --article {id}` | 変更なし（format デフォルト = article） |
| deep-research スキル（`--type stock`） | ルーター経由で `/dr-stock` に転送 |

---

## 検証方法

1. `/dr-stock --ticker AAPL --depth standard` で `research/DR_stock_*_AAPL/` が生成されること
2. `/dr-industry --sector technology --depth quick` が動作すること
3. `/dr-macro --depth standard` が FRED データを優先して収集すること
4. `/dr-theme --topic "AI半導体" --depth comprehensive` が動作すること
5. `/finance-research --from-research DR_stock_*_AAPL --format article` で記事が生成されること
6. `/finance-research --from-research DR_stock_*_AAPL --format operations` でレポートが生成されること
7. 既存の `/finance-research --article {id}` が従来通り動作すること（回帰テスト）
