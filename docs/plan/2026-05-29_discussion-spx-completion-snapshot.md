# 議論メモ: FILING_NLP_v2 SPX Step2 完走と進捗スナップショット

**日付**: 2026-05-29
**議論ID**: disc-2026-05-29-spx-completion-snapshot
**参加**: ユーザー + AI
**関連**: [disc-2026-05-27-ray-parallel-launch](2026-05-27_discussion-ray-parallel-launch.md), [disc-2026-05-27-step2-mac-mini-resume](2026-05-27_discussion-step2-mac-mini-resume.md)

## 背景・コンテキスト

- 2026-05-27 16:04:49 JST に Mac mini で SPX Step2 (run_id=20260525_180614) を単独再開 (PID 6210、170 CIK 起点)
- 同日 15:39-16:04 の RAY 並行起動実験で SMB 全断 → SIGTERM → unmount/remount → SPX のみ再開した経緯あり (dec-2026-05-27-018)
- 本セッションは進捗保存目的、SPX 完走を Decision として記録し ActionItem を再編成する

## Phase 1: コンテキスト復元の結果

| 項目 | 状態 |
|------|------|
| SPX プロセス (PID 6210) | exit (完走後) |
| RAY プロセス | 停止 (前回 SIGTERM のまま) |
| SMB マウント | ✅ 健全 |
| SPX checkpoint | ✅ **completed=500/500** failed=0 |
| RAY checkpoint | 7/2880 (前回の停止状態) |
| ローカル空き | 52GB / NAS 5.4TB |
| summary.json | ✅ 保存済み (NAS) |

## SPX 完走の事実

### summary.json (NAS)
```json
{
  "n_processed": 330,
  "n_failed": 0,
  "n_filings": 20139,
  "n_sections": 43233,
  "n_chunks": 1530210,
  "started_at": "2026-05-27T16:04:49.964914",
  "finished_at": "2026-05-28T20:20:44.064246",
  "elapsed_sec": 101754.1
}
```

### 統計
| 指標 | 値 |
|------|---|
| 再起動後の処理 CIK | 330 (170 → 500) |
| 経過時間 | **28.3 時間** (101,754 秒) |
| per-CIK 平均 | **5.14 分** |
| filings | 20,139 |
| sections | 43,233 |
| chunks | **1,530,210** |
| failed | 0 |
| errors.jsonl | 2 行 (5/26 のもの、再起動後は 0) |

### per-CIK 5.14 分の評価
- pilot100 想定: 2.79 分/CIK
- indices_v1 実測: 5.14 分/CIK (1.84 倍)
- 理由: indices_v1 は S&P 500 大企業中心。10-K/10-Q 履歴 2010+ で 60-90 filings/CIK となるため filing 数依存で増加。妥当な範囲。

### parquet 出力整合性
- checkpoint completed: 500
- sections parquet: **499** (1 件欠落)
- chunks parquet: **499** (1 件欠落)
- **欠落 CIK: 1137390** (checkpoint には完了として記録されているが sections/chunks ともに parquet ファイルなし)
- 候補仮説: (a) HTML パース失敗で空セクション、(b) 2010+ に 10-K/10-Q がゼロ、(c) トークン化段階で chunk 生成に至らず → 別アクションで分類調査

## 議論のサマリー

### 論点: 次フェーズの優先順位

候補:
1. **進捗保存のみ (今回採用)**
2. RAY 単独起動の計画策定
3. Step3 (embeddings) 着手計画
4. CIK 1137390 ギャップ調査

→ ユーザー選択: **1. 進捗保存のみ**

**判断根拠**: SPX 完走という大きなマイルストーンを Neo4j + docs/plan に確実に記録してから次フェーズに移る。RAY/Step3/ギャップ調査はいずれも単独で計画が必要なため別セッションで扱う。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-29-001 | SPX Step2 (indices_v1, run_id=20260525_180614) を 2026-05-28 20:21:09 JST に **完走完了**とする。500/500 CIK、20139 filings、43233 sections、1530210 chunks、failed 0。CIK 1137390 の parquet 欠落はフォローアップ (act-2026-05-29-002) | 再起動 16:04 から 28.3h、per-CIK 5.14 分。dec-2026-05-27-011/016/018 の有効性も実証 |

## ActionItem 状態更新

| ID | 旧状態 | 新状態 | 備考 |
|----|--------|--------|------|
| act-2026-05-27-009 (Step2 監視継続) | in_progress | **completed** | SPX 完走でターゲット消失 |
| act-2026-05-27-016 (SPX 単独監視) | in_progress | **completed** | SMB 再発なく 28h 完走 |
| act-2026-05-27-010 (Step2 summary + Step3 準備) | pending | **partially_completed** | summary 検証完了、Step3 着手は act-2026-05-29-003 に分離 |

## 新規アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-29-001 | RAY 単独起動計画策定。SMB セッションリセット (unmount/remount) → rate-rps 5 / workers 8 で起動。既存 RAY checkpoint (7 CIK) を起点に追記。SPX 重複 495 CIK は出力ディレクトリ別 (sections/indices_v1_ray/) のため後段で重複排除を検討 | high | pending |
| act-2026-05-29-002 | **CIK 1137390** ギャップ調査。仮説 (a) HTML パース失敗、(b) 2010+ に 10-K/10-Q ゼロ、(c) トークン化で chunk 生成に至らず。universe で ticker 特定 → EDGAR 検索 → zero-chunk 分類レポート作成 | medium | pending |
| act-2026-05-29-003 | Step3 (embed_indices.py) 起動計画。SPX 1,530,210 chunks を gte-Qwen2-1.5B-instruct (MPS bfloat16, batch 16, max_length 512) で 1536-dim embedding 生成。transformers v5 パッチ統合 (act-2026-05-25-302) と出力先・checkpoint 設計を確定 | medium | pending |

## 次回の議論トピック

- RAY 単独起動の rate-rps 引き上げ (3 → 5) と SMB セッション安定性の事前確認
- Step3 (embeddings) 着手の優先順位 (RAY 並列ではなく直列で実行する方針確認)
- CIK 1137390 を皮切りとした zero-chunk 分類とデータ品質レポート
- 監視閾値 (per-CIK 8min×3, progress 30min staleness) を indices_v1 実測 (5.14 分) ベースに再校正

## 参考情報

- summary.json: `/Volumes/personal_folder/Quants/FILING_NLP_v2/logs/indices_v1_summary.json`
- 完走ログ: `/Volumes/personal_folder/Quants/FILING_NLP_v2/logs/indices_v1_run.log` (最終行 `INDICES_V1 FINISHED: indices_v1`)
- sections/chunks: `sections/indices_v1/` (499 parquet), `chunks/indices_v1/` (499 parquet)
- 欠落 CIK: 1137390 (sections/chunks 両方)
- RAY checkpoint (再開起点): `checkpoints/indices_v1_ray_progress.json` (7 CIK)
- 関連 Decision: `dec-2026-05-27-011` (NAS 直接), `dec-2026-05-27-016` (run_id ベース checkpoint), `dec-2026-05-27-018` (SMB 並行禁止)
