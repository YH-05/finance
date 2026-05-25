# 議論メモ: FILING_NLP v2 — Strategy C で 6,000 社ヒストリカル全期間にスケールアップ

**日付**: 2026-05-25
**議論ID**: disc-2026-05-25-filing-nlp-v2-strategy-c
**Project**: quants
**参加**: ユーザー + AI (Claude)
**前回**: [disc-2026-05-22-filing-nlp-embedding](2026-05-22_discussion-filing-nlp-embedding.md)

## 背景・コンテキスト

2026-05-22 の議論では 9 銘柄 × 10-K(3年) + 10-Q(4Q) = 63 filings の小規模スコープで階層チャンキング + gte-Qwen2 + Chamfer 類似度のパイプラインを設計し、`04_hierarchical_chunking.ipynb` / `05_embedding.ipynb` を実装した。

今回のセッションでは以下を目的に **大幅なスコープ拡張** を実施:

1. **対象セクション拡張**: Item 1 Business を追加（10-K のみ）
2. **対象銘柄拡張**: 9 銘柄 → **NYSE+Nasdaq 6,000 unique CIK**
3. **対象期間拡張**: 5 年 → **filing_date >= 2002-01-01 の全期間**
4. **データ品質チェック基盤の構築**

## 議論のサマリー

### 1. Item 1 Business 追加の動機と設計

- 既存の Item 1A (Risk Factors) + Item 7 (MD&A) に加え、**Item 1 (Business)** を embedding 対象に追加
- 10-Q の Item 1 (Financial Statements) は数値テーブル中心のため対象外
- `section_key` の命名規則を変更:
  - 旧: 意味で統一 (`item_1a`, `item_7`) — 10-K/10-Q で同じキー
  - 新: **form 内 Item 番号そのまま** (10-K の MD&A は `item_7`、10-Q の MD&A は `item_2`)
  - 別軸 `section_role` (`business` / `risk_factors` / `mda`) で form 横断集計可能に

### 2. チャンキング戦略の進化 (Strategy A → B → C)

**markdown=True の no-op 判定**:
- 9 銘柄 × 5 年 × 3 item = 135 ケースで `obj.get_item_with_part(part, item, markdown=True)` と `markdown=False` を比較
- **全 135/135 で md_len == txt_len 一致**、AAPL 2025 Item 1 は byte 一致
- 結論: 現行 edgartools では markdown フラグは get_item_with_part に対して no-op

**edgartools DOM API の発見**:
- `obj.document.sections` — Item 単位の Section オブジェクト（confidence, detection_method, text, tables, node, start_offset/end_offset を持つ）
- `obj.document.tables` — TableNode の構造化リスト (semantic_type=FINANCIAL/METRICS/GENERAL 等、rows/cells/headers 完全保持)
- `obj.document.headings` — heading リスト (level 属性付き)
- `obj.document.walk()` — 全 DOM ノード走査 (HeadingNode/ParagraphNode/TextNode/TableNode/ContainerNode)

**section_keys の 2 命名規則問題**:
- AAPL / NVDA / AVGO / META: snake_case (`part_i_item_1`)
- MSFT / GOOGL / AMZN / AMAT: 生 Item ラベル (`Item 1`)
- 両方を順に try する `get_section()` ヘルパーで 9/9 銘柄カバー

**Strategy C (hybrid DOM + heuristic)**:

```
Filing
  └ Item (edgartools API)
      ├ Text 抽出      ← get_item_with_part(part, item) — 9/9 銘柄で動く
      ├ Table 除外     ← doc.sections[X].tables() — 40/45 filings で DOM-level
      │                   失敗時は _is_table_like ヒューリスティック fallback
      └ Subsection 検出 ← 強シグナル正規表現 + Title Case 判定 (04 + Business 拡張 18 パターン)
          └ Paragraph packing ← 段落単位で max_tokens まで詰める
              └ Chunk (gte-Qwen2 tokenizer, MAX_TOKENS=1024)
```

### 3. MAX_TOKENS=1024 への変更

- 04 では 512、本パイプラインでは **1024** に拡大
- 理由: gte-Qwen2-1.5B-instruct の理論上限 32K に対し実用最適、Item 1 Business の長文記述単位と合致
- M3 16GB MPS bfloat16 で batch 8-16 が動くことを smoke test で確認

### 4. Universe 確定 (6,000 unique CIK)

- `edgar.get_company_tickers()` → 10,532 rows (with CIK, ticker, exchange, company)
- Filter `exchange in ['Nasdaq', 'NYSE']` → 7,424 rows
- CIK で dedup（BRK-A/B のような複数 ticker を一本化、最短 ticker を代表に） → **6,000 unique CIK**
  - Nasdaq: 3,392 社
  - NYSE: 2,608 社
- 出力: `/Volumes/personal_folder/Quants/FILING_NLP_v2/universe/universe_v2.parquet`

### 5. NAS ストレージ構成

`/Volumes/personal_folder/Quants/FILING_NLP_v2/` (5.4 TB NAS) 配下に集約:

```
FILING_NLP_v2/
├── universe/               # universe_v2.parquet (確定 CIK リスト)
├── filings_metadata/       # filings_metadata_cik{10桁}.parquet
├── sections/               # sections_cik{10桁}.parquet
├── chunks/                 # chunks_cik{10桁}.parquet (per-CIK 方式)
├── checkpoints/            # progress.json
└── logs/                   # errors.jsonl, run.log
```

### 6. パイプライン基盤の実装

`notebook/FILING_NLP/pipeline/` パッケージとして実装:

- `config.py` — パス定数、フィルター規則、ITEM_SPECS_10K/10Q、MAX_TOKENS, RATE_LIMIT
- `rate_limiter.py` — `TokenBucket` (thread-safe, SEC ~10 req/sec を 5-7 で安全運用)
- `extractor.py` — `get_section()`, `remove_tables_from_text()`, `split_subsections()`, `paragraph_pack()`, `is_table_like()` を関数化（01b notebook から）
- `runner.py` — `process_filing()`, `process_cik()`, `Checkpoint`, `ShardWriter`, `run_pipeline()` (ThreadPoolExecutor 並列 + tqdm 進捗)
- `run_pilot.py` — CLI エントリ
- `pipeline_pilot.ipynb` — tqdm 進捗 + RESET フラグ付きの notebook フロー

### 7. checkpoint-flush race bug の発見と修正

**症状**: pilot100 で 44/100 CIK が「chunks 0」、しかも smoke test で chunks 生成された 5 銘柄 (SWKH/XCUR/KEX/GMED/QBTS) が全て 0。

**原因**: `ShardWriter` が memory buffer + 周期 flush 方式。`checkpoint.mark_done()` が flush より先に呼ばれていたため、kill 時に buffer 内データが失われたまま checkpoint には「完了」記録され、resume で永久 skip されていた。

**修正**:
- `ShardWriter` を **per-CIK parquet 直接書き出し方式** に変更 (`chunks_cik{10桁}.parquet`)
- `write_cik() → mark_done()` 順序を担保
- 失敗時は `mark_done()` を呼ばず continue → resume で再処理（安全）

### 8. データ品質チェックの全銘柄展開戦略

| Phase | スコープ | 推定処理時間 | ストレージ |
|---|---|---|---|
| Pilot | 100 ランダム CIK × 全期間 | 50-90 分 | 1-3 GB |
| Production | 6,000 CIK × 全期間 | 3-5 日 (workers=8) | 45-110 GB |

## 決定事項

| ID | 内容 |
|---|---|
| dec-2026-05-25-001 | Item 1 Business を抽出対象に追加 (10-K のみ) |
| dec-2026-05-25-002 | `section_key` = form 内 Item 番号、`section_role` = 意味タグの 2 軸スキーマ採用 |
| dec-2026-05-25-003 | MAX_TOKENS を 512 → 1024 へ拡張 |
| dec-2026-05-25-004 | Strategy C (hybrid DOM + heuristic) を抽出戦略に確定 |
| dec-2026-05-25-005 | `markdown=True` は no-op と判明、plain text + DOM API のハイブリッド採用 |
| dec-2026-05-25-006 | `doc.sections` キーの 2 命名規則を `get_section()` ヘルパーで吸収 |
| dec-2026-05-25-007 | Universe = NYSE+Nasdaq 6,000 unique CIK (OTC 除外、CIK dedup) |
| dec-2026-05-25-008 | filing 期間 = `filing_date >= 2002-01-01`、amendment 除外 |
| dec-2026-05-25-009 | ストレージ = NAS `/Volumes/personal_folder/Quants/FILING_NLP_v2/` |
| dec-2026-05-25-010 | 出力形式 = per-CIK parquet (`chunks_cik{10桁}.parquet`) |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|---|---|---|---|
| act-2026-05-25-001 | `pipeline_pilot.ipynb` (100 銘柄) 完走、Cell 7-9 の品質サマリ取得 | 高 | in_progress |
| act-2026-05-25-002 | Pilot 結果から DOM 取得失敗パターン分類 (TSLA 系 / 2002-2005 / no_sections) | 高 | pending |
| act-2026-05-25-003 | logger noise 抑制 (`transformers.logging.set_verbosity_error()`, `edgar.documents.extractors.hybrid_section_detector` → ERROR) | 中 | pending |
| act-2026-05-25-004 | 本実行 (6,000 社 × 全期間 × 10-K + 10-Q) を起動 | 高 | pending |
| act-2026-05-25-005 | 本実行後にデータ品質統計分析レポート作成 | 中 | pending |
| act-2026-05-25-006 | 下流の embedding 生成 notebook (02b) 実装 | 中 | pending |

## 成果物

### 新規ファイル

| パス | 役割 |
|---|---|
| `notebook/FILING_NLP/01b_fetch_with_business.ipynb` | Strategy C 単体実行用 notebook (22 セル) |
| `notebook/FILING_NLP/pipeline/__init__.py` | パッケージ初期化 |
| `notebook/FILING_NLP/pipeline/config.py` | パス・定数・ITEM_SPECS |
| `notebook/FILING_NLP/pipeline/rate_limiter.py` | TokenBucket |
| `notebook/FILING_NLP/pipeline/extractor.py` | Strategy C のコアロジック |
| `notebook/FILING_NLP/pipeline/runner.py` | 並列パイプライン + チェックポイント |
| `notebook/FILING_NLP/pipeline/run_pilot.py` | CLI エントリ |
| `notebook/FILING_NLP/pipeline_pilot.ipynb` | tqdm 進捗付きパイロット notebook |
| `/Volumes/personal_folder/Quants/FILING_NLP_v2/universe/universe_v2.parquet` | 確定 universe (6,000 unique CIK) |

### 修正ファイル

なし（既存の 02-05 notebook には影響なし）。

## 次回の議論トピック

1. **パイロット結果の解釈** — DOM section 取得成功率、subsection 検出妥当性、Item 1 Business の chunk 規模
2. **本実行のリソース計画** — 並列度、レート上限、NAS 書き込み速度、想定エラー率
3. **データ品質統計分析** — 取得失敗パターンの分類と Phase 3 調整項目
4. **embedding パイプライン (02b)** — M3 16GB MPS バッチ設計、resume 機構

## 参考情報

- 前回議論: [2026-05-22_discussion-filing-nlp-embedding.md](2026-05-22_discussion-filing-nlp-embedding.md)
- 関連: [2026-05-22_discussion-edgartools-10k-boundary.md](2026-05-22_discussion-edgartools-10k-boundary.md)
- 04 階層チャンキング notebook: `notebook/FILING_NLP/04_hierarchical_chunking.ipynb`
- 既存 universe ベース: `data/config/` 配下の universe 系（参考）
