# 議論メモ: FILING_NLP indices_v1 — SPX 先行で 4 インデックス union universe の chunks+embedding パイプライン構築

**日付**: 2026-05-25
**議論ID**: disc-2026-05-25-indices-v1-pipeline
**Project**: quants-filing-nlp-embedding
**参加**: ユーザー + AI (Claude)
**前回**: [disc-2026-05-25-filing-nlp-v2-strategy-c](2026-05-25_discussion-filing-nlp-v2-strategy-c.md)

## 背景・コンテキスト

前回 (disc-2026-05-25-filing-nlp-v2-strategy-c) で NYSE+Nasdaq 6,000 CIK の universe_v2.parquet を構築し、ランダム 100 銘柄パイロット (pipeline_pilot.ipynb) を実行した。結果:

- 100 ランダム CIK のうち 44 銘柄が chunks ゼロ (小型株/OTC 経験/古い filings)
- DOM section 取得率: item_1 37.3%, item_1a 57.1%, item_2 78.7%, item_7 37.3%

ランダムサンプリングだと品質バラツキが大きく分析対象として扱いにくい。
そこで universe 戦略を**「事前定義された米国インデックス構成銘柄」**ベースに転換する判断を行った。

**インプット**: `notebook/US Index/2026-05-22_{SPX|SOX|RIY|RAY} Index.json` (Bloomberg エクスポート、ticker + ISIN + SEDOL + GICS 4 階層 + 時価総額付き)

## 議論のサマリー

### 1. スコープ確定

| 候補 | 選択 |
|---|---|
| chunks 生成まで (最小) | × |
| **chunks + embedding 生成まで (中スコープ)** | ✓ |
| chunks + embedding + 分析・指標 (フル) | × |

Chamfer 類似度・セクター比較・新規検出等の **分析フェーズは別議論**として分離。

### 2. 展開計画

| 候補 | 選択 |
|---|---|
| SPX 503 だけ単発、完走後に判断 | × |
| SPX → RIY → RAY と段階拡張 (別 run_id) | × |
| **4 インデックス union universe で設計、SPX のみ先実行** | ✓ |

理由: **RIY ⊃ SPX ⊃ SOX** の部分集合関係があり、別 run_id にすると同 CIK が重複 fetch される。union universe + `index_membership.parquet` でメンバーシップを別管理することで CIK 単位 1 回 fetch で済む。

### 3. pilot100 の扱い

既存 NAS データ (sections/pilot100 等) は **残置**。run_id=indices_v1 を sections/indices_v1 等として並列設置。
checkpoint-flush race bug 修正の検証データとして参照保持。pilot100 ∩ SPX の重複は最大数銘柄でコスト軽微。

### 4. 生存バイアス

2026/5/22 SPX 構成銘柄で 2002-2026 全期間を取ると「過去 SPX にいたが現在除外された銘柄」が完全欠落する。
今回は **5/22 スナップショットで割り切る**。「2026/5/22 時点 SPX 構成銘柄の長期ヒストリカル分析」として README/notebook 冒頭に明示。
過去構成銘柄の補完は将来の独立議論とする。

### 5. 実装スタイル

| 候補 | 選択 |
|---|---|
| notebook 拡張型 | × |
| **CLI スクリプト中心型** | ✓ |
| 両方提供 (CLI 主、notebook ラッパー) | × |

長時間実行 (chunks fetch ~12-24h, embedding ~10h) では nohup/tmux と組み合わせやすい CLI が安全。notebook (pipeline_indices_v1.ipynb) は CLI 起動コマンド表示 + 進捗 poll + 完走後の品質統計セルに割り切る。

### 6. Universe 構築の 3 段フォールバック

ユーザー指摘 (「SPX 493 ではなく 503 全件カバーが必要」) を受けて以下を実装方針として確定。

| Step | 戦略 | SPX 実測 hit |
|---|---|---|
| 1 | universe_v2.parquet の ticker 完全一致 | 493 / 503 |
| 2 | `'/' → '-'` 正規化 + `all_tickers` 列突合 | 501 / 503 |
| 3 | `edgar.find_company_by_ticker()` で SEC EDGAR 個別 lookup | 503 / 503 (見込) |

未解決銘柄は `unresolved_tickers.json` にダンプして警告。pilot100 のような silent な欠落を防ぐ。

### 7. 規模試算 (SPX 全期間)

| 指標 | 推定値 |
|---|---|
| SPX 銘柄数 | 503 |
| chunks 推定 (pilot100 比 ×1.5 補正) | ~1.7M |
| chunks fetch 時間 (workers=8, rate=5rps) | 12-24h |
| embedding ストレージ (1536 dim float32) | ~9.4 GB |
| embedding 生成時間 (M3 16GB MPS bfloat16 batch16) | ~9-10h |
| NAS 合計使用増分 | ~18 GB |

## 決定事項

| ID | 内容 | コンテキスト |
|---|---|---|
| dec-2026-05-25-101 | Universe = 4 米国インデックス (SPX/SOX/RIY/RAY) の union を 5/22 スナップショットで構築、CIK dedup 後 (~2900) を indices_v1 のユニバースとする。`index_membership.parquet` で in_spx/in_sox/in_riy/in_ray フラグ保持 | RIY⊃SPX⊃SOX の部分集合関係を活用、CIK 単位 1 回 fetch |
| dec-2026-05-25-102 | スコープ = chunks 生成 + gte-Qwen2-1.5B embedding 生成まで | M3 MPS で SPX embedding ~10h 完了見込のため一晩運用可能 |
| dec-2026-05-25-103 | pilot100 は NAS に残置、indices_v1 を並列設置 | checkpoint-flush race bug 修正の検証データ参照 |
| dec-2026-05-25-104 | 2026/5/22 SPX スナップショットで割り切り、生存バイアスは README に明示 | 短期完走を優先、過去構成銘柄補完は将来議論 |
| dec-2026-05-25-105 | CLI スクリプト中心実装 (universe_builder.py / run_indices.py / embed_indices.py)、notebook は CLI ラッパー | 長時間実行で nohup 組み合わせやすく kill 耐性高い |
| dec-2026-05-25-106 | Universe 構築は 3 段フォールバック (universe_v2 直接 join → 正規化 join → SEC EDGAR lookup)、未解決は unresolved_tickers.json で警告 | SPX 全 503 銘柄カバレッジを DoD に、silent 欠落防止 |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|---|---|---|---|
| act-2026-05-25-101 | `pipeline/universe_builder.py` 実装 (3 段フォールバック CIK 解決 + universe_indices_v1.parquet + membership_indices_v1.parquet 出力、SPX 503 全件解決を DoD) | 高 | pending |
| act-2026-05-25-102 | `pipeline/run_indices.py` 実装 (run_pilot.py 汎用化、`--run-id` `--universe` `--membership` `--index-filter` CLI 引数追加) | 高 | pending |
| act-2026-05-25-103 | `pipeline_indices_v1.ipynb` 新規作成 (CLI ラッパー + 進捗 poll + 集計セル) | 高 | pending |
| act-2026-05-25-104 | SPX フィルタで chunks 生成 CLI 起動、完走確認 (推定 12-24h) | 高 | pending |
| act-2026-05-25-105 | `pipeline/embed_indices.py` 実装 (gte-Qwen2 MPS, per-CIK shard, resume) | 高 | pending |
| act-2026-05-25-106 | SPX embedding CLI 起動、完走確認 (推定 9-10h) | 高 | pending |
| act-2026-05-25-107 | 品質統計レポート (GICS セクター別 chunks/embedding 分布、ゼロ CIK 分析) | 中 | pending |
| act-2026-05-25-108 | 生存バイアスの記載を README/notebook 冒頭に明示 | 中 | pending |
| act-2026-05-25-109 | SPX 完走判断後、RIY → RAY に index_filter 切替で展開 | 低 | pending |

## 成果物 (実装予定)

### 新規ファイル

| パス | 役割 |
|---|---|
| `notebook/FILING_NLP/pipeline/universe_builder.py` | 4 インデックス JSON → universe + membership parquet |
| `notebook/FILING_NLP/pipeline/run_indices.py` | run_pilot.py の汎用化 (--index-filter) |
| `notebook/FILING_NLP/pipeline/embed_indices.py` | gte-Qwen2 per-CIK shard embedding 生成 |
| `notebook/FILING_NLP/pipeline_indices_v1.ipynb` | CLI ラッパー + 進捗 poll + 品質統計 |

### NAS 新規ディレクトリ / ファイル

```
/Volumes/personal_folder/Quants/FILING_NLP_v2/
├── universe/
│   └── universe_indices_v1.parquet         (新規: SPX∪SOX∪RIY∪RAY + GICS + 時価総額)
├── index_membership/
│   └── membership_indices_v1.parquet       (新規: in_spx/in_sox/in_riy/in_ray + snapshot_date)
├── sections/indices_v1/                    (新規)
├── chunks/indices_v1/                      (新規)
├── filings_metadata/indices_v1/            (新規)
├── embeddings/indices_v1/                  (新規)
├── checkpoints/
│   ├── indices_v1_progress.json            (新規: sections/chunks 共有)
│   └── indices_v1_embed_progress.json      (新規: embedding 専用)
└── logs/
    ├── indices_v1_errors.jsonl
    ├── indices_v1_run.log
    ├── indices_v1_embed_errors.jsonl
    └── indices_v1_embed.log
```

### CLI 起動コマンド (運用テンプレート)

```bash
# Step 1: Universe + index membership 構築
python -m notebook.FILING_NLP.pipeline.universe_builder \
  --indices SPX SOX RIY RAY \
  --snapshot-date 2026-05-22 \
  --index-dir "notebook/US Index" \
  --universe-out /Volumes/personal_folder/Quants/FILING_NLP_v2/universe/universe_indices_v1.parquet \
  --membership-out /Volumes/personal_folder/Quants/FILING_NLP_v2/index_membership/membership_indices_v1.parquet

# Step 2: SPX フィルタで chunks 生成 (一晩運用)
nohup python -m notebook.FILING_NLP.pipeline.run_indices \
  --run-id indices_v1 \
  --universe /Volumes/personal_folder/Quants/FILING_NLP_v2/universe/universe_indices_v1.parquet \
  --membership /Volumes/personal_folder/Quants/FILING_NLP_v2/index_membership/membership_indices_v1.parquet \
  --index-filter in_spx \
  --workers 8 --rate-rps 5 \
  > /Volumes/personal_folder/Quants/FILING_NLP_v2/logs/indices_v1_spx_run.log 2>&1 &

# Step 3: SPX embedding 生成 (一晩運用)
nohup python -m notebook.FILING_NLP.pipeline.embed_indices \
  --run-id indices_v1 \
  --membership /Volumes/personal_folder/Quants/FILING_NLP_v2/index_membership/membership_indices_v1.parquet \
  --index-filter in_spx \
  --batch-size 16 --device mps --dtype bfloat16 \
  > /Volumes/personal_folder/Quants/FILING_NLP_v2/logs/indices_v1_spx_embed.log 2>&1 &

# Step 4 以降: RIY/RAY 展開 (SPX 完走判断後)
# 上記 Step 2/3 の --index-filter in_spx を in_riy / in_ray に変更するだけ。
# 既処理 CIK は checkpoint で skip され重複 fetch なし。
```

## 次回の議論トピック

1. **SPX chunks 完走後の品質レビュー** — pilot100 比較で DOM 成功率がどれだけ改善するか
2. **embedding 完走後の分析設計** — Chamfer 類似度、セクター比較、Risk Factors 経時変化の指標化
3. **生存バイアス補正** — historical SPX 構成銘柄の取り込み要否
4. **RIY/RAY 展開のタイミング** — SPX 単体で十分な分析素材になるかの判断
5. **embeddings の vector DB 化** — ChromaDB / FAISS index 化の要否

## 参考情報

- 前回議論: [2026-05-25_discussion-filing-nlp-v2-strategy-c.md](2026-05-25_discussion-filing-nlp-v2-strategy-c.md)
- 前々回: [2026-05-22_discussion-filing-nlp-embedding.md](2026-05-22_discussion-filing-nlp-embedding.md)
- 参照ノートブック: `notebook/FILING_NLP/pipeline_pilot.ipynb` (pilot100 ベース)
- インデックスソース: `notebook/US Index/2026-05-22_*.json` (Bloomberg エクスポート)

### Universe 構築実測値 (SPX)

| Step | 累積 hit | 詳細 |
|---|---|---|
| Step 1 (ticker 完全一致) | 493/503 | 未マッチ: BF/B, BRK/B, CBOE, CMCSA, DTE, FOXA, GOOGL, MRSH, NWSA, PRU |
| Step 2 ('/' → '-' + all_tickers) | 501/503 | hit: BF/B→BF-B, BRK/B→BRK-B, CMCSA, DTE, FOXA, GOOGL, NWSA, PRU |
| Step 3 (SEC EDGAR lookup) | 503/503 (見込) | 残: CBOE, MRSH |
