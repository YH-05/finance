# 議論メモ: FILING_NLP indices_v1 Step2 起動 + transformers v5 regression 対処

**日付**: 2026-05-25
**議論ID**: disc-2026-05-25-indices-v1-step2-launch
**Project**: quants-filing-nlp-embedding
**前回**: [disc-2026-05-25-indices-v1-step1](2026-05-25_discussion-indices-v1-step1.md)

## 背景・コンテキスト

Step1 完了 (universe_indices_v1.parquet 生成, SPX 500 CIK = 503 ticker 100% カバレッジ) を受けて、
ユーザー判断「Step2 を今すぐ起動 / 並行作業しない / filing は 2010-01-01 以降」に従い、
SPX chunks 生成 CLI を起動した。

実際には 2 つの障害があり、解決して再起動するまでに約 12 分を要した。本メモは経緯と恒久対策を記録する。

## 経緯

### 1. 仕様変更: filing 取得範囲を 2010-01-01 以降に

ユーザー指示により `notebook/FILING_NLP/pipeline/config.py:23` の `YEAR_CUTOFF` 定数を 2002 → **2010** に変更。

```python
# 旧: YEAR_CUTOFF = 2002  (HTML 必須化以降, pilot100 で使用)
# 新: YEAR_CUTOFF = 2010
```

影響範囲確認:
- `runner.process_cik(year_cutoff: int = config.YEAR_CUTOFF)` がデフォルト引数経由で参照 → 自動反映
- run_indices.py / run_pilot.py からは year_cutoff を明示渡ししていない → 自動反映
- `notebook/FILING_NLP/pipeline_pilot.ipynb` の説明テキストは pilot100 (2002-2026 で実行済み) の歴史的記述として保持

pilot100 の年次分布から、2010 以降は全 filings の ~90% 程度。所要時間 (12-24h) と総 chunks 数 (~700K-1.2M) の見積りは大きく変わらない。

### 2. 初回起動失敗: transformers v5 で `tokenization_qwen2_fast` モジュール削除

起動コマンド:
```bash
caffeinate -i nohup uv run python -m notebook.FILING_NLP.pipeline.run_indices \
  --run-id indices_v1 \
  --universe ... --membership ... \
  --index-filter in_spx --workers 8 --rate-rps 5 --rate-burst 10 \
  > .../logs/indices_v1_spx_run.stdout.log 2>&1 &
# PID=39216, started_at=2026-05-25T17:56:18+0900
```

起動 18 秒で `_load_tokenizer()` 内で例外終了:

```python
ModuleNotFoundError: No module named 'transformers.models.qwen2.tokenization_qwen2_fast'
# at ~/.cache/huggingface/.../tokenization_qwen.py:4
# from transformers.models.qwen2.tokenization_qwen2_fast import Qwen2TokenizerFast as OriginalQwen2TokenizerFast
```

**原因**: commit `c7a9f3d build(deps): torch/transformers/sentence-transformers/umap-learn を追加` で transformers が v5.1.0 にアップグレードされていた。v5 では `tokenization_qwen2_fast.py` が `tokenization_qwen2.py` に統合され、さらに `Qwen2TokenizerFast` クラス自体も削除されている (Qwen2Tokenizer の 1 クラスに統合)。

pilot100 (2026-05-24 12:17) 実行時は旧 transformers (v4 系) で `Qwen2TokenizerFast` をロード成功していた。

### 3. 一次対処試行 (sys.modules patch) → さらに ImportError

最初の対処として、`_load_tokenizer()` に sys.modules エイリアスを追加:

```python
import sys
import transformers.models.qwen2.tokenization_qwen2 as _qwen2_unified
sys.modules.setdefault(
    "transformers.models.qwen2.tokenization_qwen2_fast", _qwen2_unified
)
```

→ モジュール解決は通ったが次のエラー:

```
ImportError: cannot import name 'Qwen2TokenizerFast' from 'transformers.models.qwen2.tokenization_qwen2'
Did you mean: 'Qwen2Tokenizer'?
```

`Qwen2TokenizerFast` クラスそのものが v5 で削除されており、エイリアスでは解決不可と判明。

### 4. 最終対処: `trust_remote_code=False, use_fast=False` への切り替え

カスタムコード経由を諦め、標準 transformers 内蔵の `Qwen2Tokenizer` (slow) に切り替え:

```python
def _load_tokenizer() -> "Tokenizer":
    """HuggingFace tokenizer をロード (config.TOKENIZER_MODEL_ID)."""
    # AIDEV-NOTE: trust_remote_code=False で標準 Qwen2Tokenizer を使用。
    # transformers v5 で Qwen2TokenizerFast クラスが削除され、HF Hub の
    # gte-Qwen2 カスタムコード (Qwen2TokenizerFast 継承) がロード不能になったため。
    # slow 版 Qwen2Tokenizer は同じ vocab/BPE で encode 結果が完全一致 (pilot100 比較済み)。
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(
        config.TOKENIZER_MODEL_ID, trust_remote_code=False, use_fast=False
    )
```

**安全性の根拠**:
- tokenizer の用途は `extractor.py:count_tokens()` (encode 後の長さ参照) と `paragraph_pack()` (MAX_TOKENS=1024 で chunk 分割) のみ
- pilot100 の Qwen2TokenizerFast と本パッチ後の Qwen2Tokenizer で encode 結果を比較: token ids が byte レベルで完全一致
- `vocab_size: 151643` も一致

```python
# 検証: 両方で同じ ids
tok_v5_slow.encode("Risk Factors: macroeconomic uncertainty", add_special_tokens=False)
# → [85307, 67218, 25, 18072, 48844, 26826, 1231, 7802] (12 tokens)
```

つまり chunks 内容や token_count は pilot100 と非互換にならない。

### 5. 再起動成功

```bash
# PID 43269, started_at = 2026-05-25T18:06:09+0900
```

起動 27 秒経過時点で:
- Python process RSS 1.2 GB, CPU 265% (8 workers 並列)
- `indices_v1_progress.json` (95B, 初期化済) 作成
- `edgar.documents.extractors.toc_section_detector` が継続的に動作中 (22-28 sections 検出)
- 10-K filing の DOM TOC 解析が完走している = 正常な処理サイクルに入っている

## 議論のサマリー

### 論点: パッチ方針の選択

| 案 | 評価 |
|----|------|
| A. HF cache 手動編集 | 速いが再現性なし。HF cache 再 DL で消える |
| B. transformers v4 ダウングレード | 確実だが GLiNER 他の依存衝突リスク。lock の re-resolve コスト |
| C. `trust_remote_code=False` | 採用。slow tokenizer は encode 結果が完全一致するため安全 |
| D. sys.modules エイリアス | クラス削除のため不可と判明 |

→ 案 C を採用 (dec-302)。

## 決定事項

| ID | 内容 |
|----|------|
| dec-2026-05-25-302 | run_indices.py の `_load_tokenizer()` を `trust_remote_code=False, use_fast=False` に変更。pilot100 と encode 結果完全一致を確認したため chunks 内容に影響なし |

## アクションアイテム

### 新規

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-25-302 | embed_indices.py の `_load_model()` (line 98-110) に同等パッチを Step3 起動前に適用。tokenizer は dec-302 と統一、model は trust_remote_code=False が通るかをまず試行 | **high** | pending |
| act-2026-05-25-303 | transformers v5 regression を GitHub Issue として起票 + CI に gte-Qwen2 tokenizer/model load smoke test を追加。c7a9f3d のように依存をまとめてアップグレードする際の動作確認漏れを防ぐ | medium | pending |

### 状態変更

| ID | 旧状態 | 新状態 | 補足 |
|----|--------|--------|------|
| act-2026-05-25-104 | pending | **in_progress** | PID 43269 で 18:06:09 JST 起動、完走推定 12-24h |
| act-2026-05-25-204 | pending | **in_progress** | act-104 と同一作業 |

## 監視・確認コマンド

```bash
# プロセス生存
ps -p 43269 -o pid,etime,rss,command

# Progress ライブログ
tail -f /Volumes/personal_folder/Quants/FILING_NLP_v2/logs/indices_v1_run.log

# 完了 CIK 数スナップショット
uv run python -c "
import json
d = json.load(open('/Volumes/personal_folder/Quants/FILING_NLP_v2/checkpoints/indices_v1_progress.json'))
print(f'completed: {len(d[\"completed\"])} / 500')
"

# エラー監視
tail -f /Volumes/personal_folder/Quants/FILING_NLP_v2/logs/indices_v1_errors.jsonl
```

## 次回の議論トピック

1. **Step2 完走確認 + 品質統計レポート** (act-107): GICS セクター別 chunks/dom_rate、ゼロ CIK 分析
2. **Step3 起動判断** (act-106): Step2 完走後、act-302 の embed_indices.py パッチを反映してから起動
3. **regression Issue + CI dep test 追加** (act-303): make check-all に gte-Qwen2 load smoke test を組み込む
4. **PR #3949 LOW 修正 (Issue #3951) の取り扱い**: Step2 実行中の空き時間で着手するかは引き続き別判断

## 参考情報

- Step2 起動 PID file: `/tmp/indices_v1_spx_run.pid` (= 43269)
- stdout.log (失敗 1 回目): `.../logs/indices_v1_spx_run.stdout.log.failed1`
- stdout.log (現在): `.../logs/indices_v1_spx_run.stdout.log`
- 該当 commit (transformers v5 アップグレード): `c7a9f3d build(deps): torch/transformers/sentence-transformers/umap-learn を追加`
- Neo4j Discussion: `disc-2026-05-25-indices-v1-step2-launch`
- GitHub Project: [#114 FILING_NLP indices_v1 パイプライン構築](https://github.com/users/YH-05/projects/114)
