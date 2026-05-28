# 議論メモ: FILING_NLP_v2 Step2 SPX 完走 (500/500 CIK)

**日付**: 2026-05-28
**議論ID**: disc-2026-05-28-step2-completion
**参加**: ユーザー + AI
**関連**: [disc-2026-05-27-step2-mac-mini-resume](2026-05-27_discussion-step2-mac-mini-resume.md), [disc-2026-05-27-filing-nlp-v2-nas-sync](2026-05-27_discussion-filing-nlp-v2-nas-sync.md), [disc-2026-05-26-step2-day1](2026-05-26_step2-day1-shutdown-and-resume-plan.md)

## 背景・コンテキスト

SPX 500 CIK の SEC 10-K/10-Q chunks 生成 (FILING_NLP_v2 Step2) を 2026-05-28 20:20:44 JST に完走。
2026-05-25 18:06 の初回起動から実通算 50 時間、Mac mini resume (5/27 12:29) からは 31h 51m。
複数回の中断・再起動 (MacBook Air 4 stall + PC シャットダウン → Mac mini resume → 16:04 外的再起動) を経た上で、
A 案 (NAS 直接書き込み) で **failed=0 / 進捗ロスゼロ** の完走を達成した。

## 完走時の最終統計

| 指標 | 値 |
|------|-----|
| 完了 CIK | **500 / 500 (100%)** |
| 失敗 CIK | **0** |
| 全 filings | 20,139 |
| 全 sections | 43,233 |
| 全 chunks | **1,530,210** |
| 平均 chunks/CIK | 約 4,263 (pilot100 1,380 の **3.1 倍**) |
| zero-chunk CIK | **1 件** (cik=1137390、status=success/n_sections=0) |
| 新規 errors | **0** (古い 2026-05-26 BKNG SMB stale 2 件のまま) |
| sections parquet | 499 (zero-chunk 除く) |
| chunks parquet | 499 |
| filings_metadata parquet | 499 |
| TOC events 累計 | 18,086 |

### 実行時間

| ベース | 値 |
|------|-----|
| 最新プロセス (PID 6210, 16:04:42 起動 → 20:20:44 完了) | **28h 16m** (elapsed 101,754 sec) |
| Mac mini resume 全体 (5/27 12:29 → 5/28 20:20) | **31h 51m** |
| 最初の MacBook Air 起動 (5/25 18:06) からの通算 | 約 50 時間 |

## 議論のサマリー

### 完走時間が pilot 推定 (17h) より 1.7 倍長い理由

| 要因 | 影響 |
|------|------|
| SPX 大型エンタープライズ偏向 | 平均 chunks/CIK = pilot 1,380 → SPX 4,263 (**3 倍**) |
| Qwen2Tokenizer (slow 版) の encode 重さ | transformers v5 で fast 廃止、70KB+ MD&A で線形以上に劣化 |
| 8 workers × SEC rate=5rps | 実効並列度 4-5 程度 (推定) |
| Mac mini SMB 書き込み速度 | 安定、ボトルネックなし |

### 16:04 外的再起動の透過処理

- 旧 PID 57168 (12:29 起動) が 16:03 頃 kill された (ray run 並列実行による外的要因、ユーザー確認済み)
- 16:04:42 に RESUME_STEP2_MAC_MINI.sh で新プロセス起動 → checkpoint で **187 CIK skip** して seamless resume
- 進捗ロス・データ重複ゼロ
- per-CIK parquet + mark_done 順序固定 (dec-2026-05-25-011) が中断耐性を実運用で再確認

### 監視閾値の評価

| 閾値 | 結果 |
|------|------|
| per-CIK 8min × 連続3 | 一部抵触 (大型 CIK 61.2 min) があったが連続でなく停止判断には未到達 |
| errors > 5 | 終始ゼロ |
| progress 30min 停滞 | 起動初期 (12:29-13:15) の 45 分のみ抵触、第一号完了後は常時 10 分以内に更新 |

→ 閾値設計は SPX 大型 CIK には **per-CIK 8min が tight すぎる**。次回は 12-15 min への緩和検討余地あり。

### 完走予測精度

| 確認時点 | 予測 ETA | 実績との誤差 |
|---------|---------|-------------|
| 5/27 12:29 起動時 | 17 時間後 (翌日 4-5 時) | -16h (大幅楽観) |
| 5/27 13:30 初期 | 5/29 03:30 頃 | +31h (過剰悲観、起動オーバーヘッド込み) |
| 5/27 15:02 | 5/28 22:23 頃 | +2h (近い) |
| 5/27 19:04 | 5/28 12:09 頃 | -8h (直近 60 分過大評価) |
| **5/28 5:58** | **5/28 20:50** | **+30 min (実績 20:20:44、誤差 30 分以内 ✅)** |

→ **直近 30 件平均ペース** (~12 CIK/hour) が安定見積もり指標として有効。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-28-001 | A 案 (NAS 直接書き込み) の有効性実証完了 (500/500, failed 0, errors 0)。Step3 embedding と他指数 (SOX/RIY/RAY) も同方式で実行 | Mac mini 蓋無し据置 + SMB ESTABLISHED + 監視閾値で停止判断なく完走 |
| dec-2026-05-28-002 | per-CIK checkpoint + mark_done 順序固定の中断耐性を実運用で再確認。Step3 など長時間バッチ処理でも同パターン採用 | 16:04 の外的再起動を透過的に処理、進捗ロス・データ重複ゼロ |
| dec-2026-05-28-003 | SPX 完走時間 28h 16m は pilot 推定 1.7 倍。原因 (3 倍 chunks/CIK / Qwen2Tokenizer slow / 実効並列度 4-5) を記録し、Step3 embedding は MPS GPU で別物のため再見積もり必要 | 最終予測精度 30 分以内、直近 30 件平均が安定指標 |

## アクションアイテム

### 更新

| ID | 状態 | 補足 |
|----|------|------|
| act-2026-05-27-009 | **completed** | Step2 監視継続 → 完走で目的達成 |
| act-2026-05-27-010 | 維持 (in_progress 相当) | act-2026-05-28-001/002 に派生 |

### 新規

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-28-001 | Step2 完走品質統計レポート作成 (zero-chunk CIK=1137390 銘柄分類 / chunks 分布 / DOM rate / pilot100 比較) | medium | pending |
| act-2026-05-28-002 | Step3 embed_indices.py 着手 (transformers v5 パッチ + MPS bfloat16 + 1536 次元 + per-CIK checkpoint) | high | pending |
| act-2026-05-28-003 | 他指数 (SOX/RIY/RAY) Step2 実行計画 (membership 件数確認 → 直列 or 並列判断) | medium | pending |
| act-2026-05-28-004 | 本セッション残骸クリーンアップ (.tmp/step2_resume/ の stale PID/log) | low | pending |

## 次回の議論トピック

1. **act-2026-05-28-002 Step3 着手**: transformers v5 パッチ実装、MPS GPU での速度実測、per-CIK checkpoint の再利用
2. **act-2026-05-28-001 品質統計レポート**: zero-chunk CIK 1137390 の銘柄調査、SPX 大型 CIK の chunk 分布分析
3. **act-2026-05-28-003 他指数の進め方**: Step3 と並列か直列か、Mac mini の負荷配分
4. **監視閾値の調整**: per-CIK 8min → 12-15min への緩和、SPX 大型対応のチューニング

## 参考情報

- 実装パッケージ: `notebook/FILING_NLP/pipeline/`
- 実行スクリプト: `notebook/FILING_NLP/pipeline/run_indices.py`
- NAS 出力: `/Volumes/personal_folder/Quants/FILING_NLP_v2/{sections,chunks,filings_metadata}/indices_v1/`
- checkpoint: `/Volumes/personal_folder/Quants/FILING_NLP_v2/checkpoints/indices_v1_progress.json`
- summary.json: `/Volumes/personal_folder/Quants/FILING_NLP_v2/logs/indices_v1_summary.json`
- 起動ログ: `.tmp/step2_resume/launch_20260527_160442.log` (最終)
- 起動スクリプト: `.tmp/step2_resume/RESUME_STEP2_MAC_MINI.sh` (再利用可)
- 監視スクリプト: `.tmp/step2_resume/monitor_step2.sh` (再利用可)
- 関連 Decision: dec-2026-05-25-011 (per-CIK 方式), dec-2026-05-26-401/402 (ローカル切替・蓋禁止), dec-2026-05-27-008/009/010/011/012/013, dec-2026-05-28-001/002/003
