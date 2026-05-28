# 議論メモ: FILING_NLP_v2 Step2 Mac mini 再開 + SMB fd 劣化監視運用

**日付**: 2026-05-27
**議論ID**: disc-2026-05-27-step2-mac-mini-resume
**参加**: ユーザー + AI
**関連**: [disc-2026-05-27-filing-nlp-v2-nas-sync](2026-05-27_discussion-filing-nlp-v2-nas-sync.md), [disc-2026-05-26-step2-day1](2026-05-26_step2-day1-shutdown-and-resume-plan.md)

## 背景・コンテキスト

- 2026-05-26 18:08 に MacBook Air PC シャットダウンで Step2 (SPX 500 CIK の SEC 10-K/10-Q chunks 生成) を 140/500 CIK (28%) で中断
- 2026-05-27 11:00 にローカル SSD → NAS 同期完了 (sections/chunks/filings_metadata/indices_v1/ × 139 parquet + checkpoint 140 CIK)
- 残 360 CIK (約 17 時間) の再開タイミングと出力先が未決 (act-2026-05-27-007)
- 本セッションは自宅 Mac mini (蓋無し据置機, hostname: YukinoMac-mini.local, ユーザー: yuki) から起動

## Phase 1: コンテキスト復元の結果

| 項目 | 状態 |
|------|------|
| NAS マウント | ✅ /Volumes/personal_folder (smbfs, 5.4TB) |
| ローカル空き | 56GB |
| HF cache (gte-Qwen2-1.5B-instruct) | ✅ /Users/yuki/.cache/huggingface/hub/ |
| config.py L10 | ⚠️ MacBook Air ローカルパス `/Users/yukihata/...` のまま |
| ローカル `.tmp/FILING_NLP_v2_local/` | ❌ 存在せず |
| NAS checkpoint | ✅ completed: 140 / 500, run_id: 20260525_180614 |
| `.env` の EDGAR_IDENTITY | ❌ `SEC_EDGAR_IDENTITY` のみ存在 |

## 議論のサマリー

### 論点 A: 残 360 CIK の出力先

候補:
1. **NAS 直接 + 監視 (推奨)**: config.py を NAS_ROOT に戻し、Mac mini から NAS 直接書き込み
2. ローカル SSD 完走 → rsync: 実証済みの安定動作だが Mac mini パス修正 + 完走後 rsync 必要
3. 二重保存: ローカル + 定期 NAS rsync 並列実行
4. 待機: 今回は再開しない

→ ユーザー選択: **1. NAS 直接 + 監視**

**判断根拠**:
- Mac mini は蓋無し据置機 → MacBook Air の `LID_CLOSE → SMB 切断` (stalled3 主因) は構造的に発生しない
- 既に NAS に 140 CIK + checkpoint が同期済み → 追加 rsync 不要
- 残 17 時間で完走 → 翌朝完了見込み
- per-CIK checkpoint で部分障害時の resume 可能

### 論点 B: SMB fd 劣化検知とフォールバック基準

候補:
1. **シンプル閾値監視 (推奨)**: 自動検知 + 人判断切替
2. 人扇視ベース (1時間ごと手動確認)
3. 常時タイムアウト付き 3 時間 remount (事前 cron スケジュール)
4. 監視なし

→ ユーザー選択: **1. シンプル閾値監視**

**閾値**:
| 指標 | 閾値 |
|------|------|
| per-CIK 処理時間 | 連続 3 CIK で 8 分以上 |
| errors.jsonl | 5 件超 |
| progress.json | 30 分以上更新なし |

いずれか抵触 → B 案 (ローカル SSD + 後追い rsync) に切替。自動 kill せず人間判断。

### 論点 C: 起動手順

候補:
1. **今すぐ (git checkout) (推奨)**: 即起動
2. 今すぐ (手動編集): config.py 手動編集
3. コマンドだけドラフト: 起動はユーザー
4. 今日は起動しない

→ ユーザー選択: **1. 今すぐ**

**実装上の発見**: `git checkout` は indices_v1 拡張定数を巻き戻すため使用せず、Edit ツールで L8-10 のみ NAS パスに変更 + AIDEV-NOTE を 2026-05-27 復帰記録に更新。

## 実行と検証

### 起動
- スクリプト: `/Users/yuki/Desktop/quants/.tmp/step2_resume/RESUME_STEP2_MAC_MINI.sh`
- 監視スクリプト: `/Users/yuki/Desktop/quants/.tmp/step2_resume/monitor_step2.sh`
- 起動時刻: **2026-05-27 11:46:22 JST**
- PID: **48222**
- run_id: **20260525_180614** (既存 checkpoint と一致)
- index_filter: in_spx (500 CIK)
- workers: 8, rate-rps: 5
- 環境変数: `EDGAR_IDENTITY="Yuki youxitiankaggle@gmail.com"` (インライン、.env は SEC_EDGAR_IDENTITY のみ)

### 確認結果
- NAS マウント確認 ✅
- universe + membership parquet 確認 ✅
- checkpoint completed=140 確認 ✅
- EDGAR Identity 設定成功 (`edgar.core` ログ確認)
- universe 500 CIK ロード成功 ✅
- tokenizer ロード開始

### 完走見込み
- 残 360 CIK × 2.79 分/CIK = **約 17 時間**
- 完走予定: **2026-05-28 04:00 頃**

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-27-011 | Step2 残 360 CIK の出力先を NAS 直接書き込みに決定 (A 案) | Mac mini 蓋無し → LID_CLOSE 構造的に発生なし。NAS に 140 CIK 既同期 |
| dec-2026-05-27-012 | SMB fd 劣化検知のシンプル閾値監視を採用 (per-CIK 8min×連続3 / errors >5 / progress 30min 停滞 → B案切替、人判断式) | pilot 実測 per-CIK 2.79 分が安定動作点、明確な劣化サインで判定 |
| dec-2026-05-27-013 | config.py L8-10 を Edit で NAS 復帰 (git checkout は indices_v1 拡張定数を巻き戻すため不可)。EDGAR_IDENTITY は起動スクリプト内インライン | .env は SEC_EDGAR_IDENTITY のみ存在のため起動時注入 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-27-009 | Step2 再開プロセス (PID=48222) の閾値監視継続。閾値抵触時に B 案切替 | high | in_progress |
| act-2026-05-27-010 | Step2 完走後の summary 検証 + zero-chunk CIK 最終分類 + Step3 (embed_indices.py) 着手準備 (act-2026-05-25-302 transformers v5 パッチ統合判断含む) | medium | pending |
| act-2026-05-27-011 | act-2026-05-27-007 (Step2 出力先決定) を dec-2026-05-27-011 で解決済みクローズ | low | completed |

## 次回の議論トピック

- Step2 完走後の品質統計レポート (act-2026-05-25-107 の派生)
- Step3 embed_indices.py の transformers v5 パッチ対応 (act-2026-05-25-302)
- 4 指数 (SPX/SOX/RIY/RAY) のうち SPX 完走後、残 3 指数の処理計画
- 監視中に閾値抵触した場合の B 案切替プレイブック整備

## 参考情報

- 起動スクリプト: `.tmp/step2_resume/RESUME_STEP2_MAC_MINI.sh`
- 監視スクリプト: `.tmp/step2_resume/monitor_step2.sh`
- PID ファイル: `.tmp/step2_resume/step2.pid`
- 起動ログ: `.tmp/step2_resume/launch_20260527_114618.log`
- NAS ライブログ: `/Volumes/personal_folder/Quants/FILING_NLP_v2/logs/20260525_180614_run.log`
- 進捗 checkpoint: `/Volumes/personal_folder/Quants/FILING_NLP_v2/checkpoints/indices_v1_progress.json`
- 関連 Decision: `dec-2026-05-26-401` (ローカル SSD 切替), `dec-2026-05-26-402` (Mac 蓋閉じ禁止), `dec-2026-05-27-008` (NAS rsync 同期方式)
