# 議論メモ: FILING_NLP 埋め込みパイプライン設計

**日付**: 2026-05-22
**議論ID**: disc-2026-05-22-filing-nlp-embedding
**Project**: quants-filing-nlp-embedding
**参加**: ユーザー + AI (Claude)
**対象 notebook**: `notebook/FILING_NLP/04_hierarchical_chunking.ipynb`, `05_embedding.ipynb`

## 背景・コンテキスト

10-K / 10-Q の Risk Factors (Item 1A) + MD&A (Item 7 / 10-Q Item 2) を階層的にチャンク化し、gte-Qwen2-1.5B-instruct で 1536 次元の埋め込みを生成。後段で Chamfer 類似度を用いて以下の分析を行う:

- **Time-section**: 同 ticker の年度間比較 → 新規追加された sub-risk 検出
- **Cross-section**: 同期間の異 ticker 比較 → 差別化要因の抽出

対象: 9 ticker (AAPL/MSFT/GOOGL/NVDA/TSLA/AVGO/AMAT/AMZN/META) × (10-K × 3 年 + 10-Q × 4 Q) = 63 filings。

## 議論のサマリー

### 1. チャンクサイズの決定 (MAX_TOKENS = 512)

懸念: 長文 chunk は gte-Qwen2 の last-token pooling で意味が薄まる。

検討:
- 256-512 tok が gte-Qwen2 系の MTEB sweet spot
- 10-K Risk Factor 1 個が typically 200-500 tok → 1 chunk = 1 sub-risk が自然
- Chamfer 計算で chunk が細かい方が新規シグナルが立つ

→ **MAX_TOKENS = 512** に決定。

### 2. 埋め込みパフォーマンス最適化

M3 Mac 16GB での実測:

| 設定 | ms/chunk | 全件見積もり |
|------|---------|------------|
| batch=8, random | 604 | 45 分 |
| batch=32, random | 608 | 45 分 |
| batch=32, **length-sort** | 870 | 65 分 (**悪化**) |

length-sort は理論上 padding waste を減らすはずが、MPS が seq_len ごとにカーネル再コンパイルするため逆効果。

→ **random batching + batch_size=32** を採用、追加最適化はせず 45 分の実行を許容。

### 3. リジューム機能の実装

NaN-marker 方式:
- `embeddings.npy` を `(N, 1536)` の NaN 配列で初期化
- 10 batch (約 3 分) ごとに `np.save()`
- 再実行時は `np.isnan().any(axis=1)` で最初の未処理行から再開
- `FORCE_REENCODE=True` で既存ファイルを無視可能

### 4. メタデータ設計

- `embeddings.npy`: float32 (N, 1536), L2 正規化済み
- `chunks_meta.parquet`: text 列含む全カラム (Chamfer 結果の解釈時に即読める)
- chunk_id: 行順から 6 桁 zero-pad で採番

### 5. テーブルノイズ問題の発見

Cell 14 (oversize 調査) の結果:

```
上限超過 chunk 数: 40 / 4490 (0.9%)
(no title) subsection の chunk: 645 / 4490
うちテーブル系: 115 (2.6% of total)
集中先: MSFT 10-Q item_7 (54), AMAT 10-Q item_7 (47), AMZN 10-Q item_7 (14)
```

原因: edgartools `markdown=False` で財務テーブルが plain text (`Three Months Ended ... (In millions)`) として残る。

対策: **テーブル除外 + bullet 段落化** を上流で実装 (heading-detect セル + apply-chunking セル)。

### 6. HF キャッシュの統一

03-2 が `~/.cache/huggingface/` に既に 6.6 GB ダウンロード済みだったのに、04/05 が `HF_HOME=data/hf_cache` を指定したため重複ダウンロードが発生。両 notebook から `HF_HOME` 関連 4 行を削除して default を使うように変更。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-22-emb-001 | MAX_TOKENS=512 | last-token pooling 特性 + Risk Factor 粒度マッチ + MTEB プラトー |
| dec-2026-05-22-emb-002 | MPS + bfloat16 + batch=32, random batching | length-sort は MPS recompilation で逆効果 |
| dec-2026-05-22-emb-003 | NaN-marker checkpoint (10 batch ごと) | 45 分実行のクラッシュ耐性 |
| dec-2026-05-22-emb-004 | chunks_meta.parquet に text 列含む | Chamfer 結果の即時テキスト確認 |
| dec-2026-05-22-emb-005 | HF キャッシュは default 使用 (`~/.cache/huggingface/`) | 6.6 GB の重複 DL 回避 |
| dec-2026-05-22-emb-006 | テーブル系 chunk (115 件 / 2.6%) を `_is_table_like()` で除外 | Chamfer ノイズ削減 |
| dec-2026-05-22-emb-007 | `_preprocess()` で bullet (•) を段落区切りに昇格 | bullet list の oversize 解消 |
| dec-2026-05-22-emb-008 | 06_chamfer_similarity で対称・非対称両方を実装 | time/cross-section 両用途 |

## アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-05-22-emb-001 | 04 notebook Cell 5-8 を再実行、新 helpers のテスト pass + chunks_hier.parquet 再生成 | 高 |
| act-2026-05-22-emb-002 | 04 Cell 14 再実行、oversize chunk 数が 5-15 件 (40 件→減少) であることを検証 | 高 |
| act-2026-05-22-emb-003 | 05 で `FORCE_REENCODE=True` で Cell 6 実行 (45 分)、その後 False に戻す | 高 |
| act-2026-05-22-emb-004 | 05 Cell 7 で NaN=0, norm≈1.0, ticker/section 識別性を検証 | 高 |
| act-2026-05-22-emb-005 | 06_chamfer_similarity.ipynb を作成 (対称+非対称、time+cross filter) | 中 |
| act-2026-05-22-emb-006 | oversize > 1% 残った場合のみ Lv 2 (clause-split) + Lv 3 (token-split) 追加 | 低 |

## 実装変更履歴

| ファイル | セル | 変更内容 |
|---------|------|---------|
| `04_hierarchical_chunking.ipynb` | setup-imports (Cell 1) | `HF_HOME` 関連 4 行削除 |
| `04_hierarchical_chunking.ipynb` | heading-detect (Cell 5) | `_preprocess`, `_is_table_like`, `TABLE_MARKER_RE` 追加 + テスト 5 ケース |
| `04_hierarchical_chunking.ipynb` | apply-chunking (Cell 8) | `_is_table_like()` でテーブル chunk を skip |
| `04_hierarchical_chunking.ipynb` | (新規) Cell 11-14 | 検証統計の追加 (subsection breakdown / sanity check / sample chunks / oversize 調査) |
| `05_embedding.ipynb` | (新規) | 全 9 セル新規作成 |
| `05_embedding.ipynb` | setup-imports (Cell 1) | `HF_HOME` 設定なし (default cache 使用) |
| `05_embedding.ipynb` | next-step-placeholder (Cell 6) | リジューム対応の全件エンコード実装 |
| `05_embedding.ipynb` | (新規 Cell 7) | エンコード結果の健全性チェック |

## 次回の議論トピック

1. **06_chamfer_similarity.ipynb の詳細設計**:
   - 対称 Chamfer の正規化方法 (mean of mins / Hungarian matching / etc.)
   - 非対称 Chamfer の閾値判定 (新規 sub-risk 検出のしきい値)
   - 比較フィルタリングのインタフェース (`(ticker_a, item_key_a, date_a) vs (ticker_b, item_key_b, date_b)`)

2. **Chamfer 結果の可視化**:
   - Heatmap (year × ticker × item)
   - 変化検知の top-K 表示
   - 新規/類似 sub-risk のグルーピング

3. **truncated chunk (>512 tok) への対応** (アクション 006):
   - Lv 2+3 ハイブリッド (clause-split → token-split fallback) 実装の要否
   - 上流対策 (edgartools の出力改善 / 別ライブラリ検討)

## 参考情報

### 関連 commit (本セッション前)

- `9152004 feat(filing_nlp): 階層チャンキング notebook + edgartools 境界バグ議論メモ追加`
- `5d7df5f feat(filing_nlp): 03-2 notebook に gte-Qwen2 埋め込みデモを追加`

### 関連 Discussion / Project

- `disc-2026-05-22-edgartools-10k-boundary` (同日、edgartools 境界バグの別議論)
- `Project: quants-analyst-tacit-knowledge` (アナリスト Y チームの暗黙知形式化 — 本パイプラインの最終的な consumer)

### 技術ノート

- gte-Qwen2-1.5B-instruct: HuggingFace `~/.cache/huggingface/hub/` に 6.6 GB
- chunks_hier.parquet サイズ: 約 3-5 MB (text 込み)
- embeddings.npy サイズ: ~26 MB (4490 × 1536 × 4 byte)
- `transformers 4.45+` 互換性: `use_cache=False` 必須 (modeling_qwen.py の DynamicCache 旧 API)
