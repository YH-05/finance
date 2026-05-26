# 議論メモ: FILING_NLP indices_v1 Step2 1日目運用 + 4回の中断対処 + PC停止時の状態保全

**日付**: 2026-05-26
**議論ID**: disc-2026-05-26-step2-day1
**Project**: quants-filing-nlp-embedding
**関連**: [disc-2026-05-25-indices-v1-step1](2026-05-25_discussion-indices-v1-step1.md), [disc-2026-05-25-indices-v1-step2-launch](2026-05-25_discussion-indices-v1-step2-launch.md)

## 背景・コンテキスト

2026-05-25 18:06 に Step2 (SPX 500 CIK の SEC 10-K/10-Q chunks 生成) を起動。当初は NAS (`/Volumes/personal_folder/Quants/FILING_NLP_v2/`, smbfs) を出力先としていたが、本日 (2026-05-26) 中に **4 回の stall + 復旧サイクル** を経験。最終的に **ローカル SSD 出力に切替えた段階で安定稼働** へ到達した。

2026-05-26 18:08 にユーザーが PC シャットダウンを希望したため graceful stop。本メモは本日 1 日の運用知見と PC 起動後の Resume 手順を記録する。

## 本日の経緯 (4 サイクル + ローカル化)

| サイクル | 起動時刻 | 停止時刻 | 完了 CIK | per-CIK | 真因 |
|---------|---------|---------|---------|---------|------|
| stalled1 (前日継続) | 18:06 | 01:41 (実質) | 27 → 27 | 8.0 分/CIK | (持ち越し) |
| stalled2 | 07:36 | 09:34 | +36 → 63 | **3.3 分/CIK (好調)** | SMB fd stale (3+ 時間運用) |
| stalled3 | 11:14 | 11:56 | +1 → 64 | 42 分/CIK | **Mac 蓋閉じ → SMB 切断** |
| stalled4 | 12:36 | 13:21 | +2 → 66 | 22.5 分/CIK | remount 後の SMB 不安定 |
| stalled5 (NAS) | 13:24 | 13:46 (検知) | +0 → 66 | ∞ (完全停滞) | remount 効果消滅 |
| **LOCAL 切替** | **13:55** | **18:08 (PC停止)** | **+74 → 140** | **2.79 分/CIK (安定)** | - |

## 解決策の確定

### dec-2026-05-26-401: ローカル SSD 出力に恒久切替

**変更内容** (`notebook/FILING_NLP/pipeline/config.py:8-10`):
```python
# 旧
# NAS_ROOT = Path("/Volumes/personal_folder/Quants/FILING_NLP_v2")
# 新
NAS_ROOT = Path("/Users/yukihata/Desktop/quants/.tmp/FILING_NLP_v2_local")
```

**根拠**:
- pilot100 実測ベースで SPX 完走後の総容量 ~3GB (chunks 2.4MB/CIK + sections 3MB/CIK)
- ローカル SSD 27GB 空きで余裕
- errors 0 + 2.79 分/CIK 安定運用達成 (NAS 22.5 分/CIK の **8 倍速い**)
- 完走後 rsync で NAS に同期 (act-2026-05-26-402)

### dec-2026-05-26-402: Mac 蓋開放を運用ルール化

- `caffeinate -i` は CPU sleep 抑止のみ、LID_CLOSE トリガには無力
- 蓋を閉じると WiFi/Bluetooth/SMB セッションが瞬時切断 → 進捗ロス
- 外出時は外部モニター接続 (クラムシェル禁止)

## 現在の停止状態 (2026-05-26 18:08:45 JST)

| 項目 | 値 |
|------|-----|
| 完了 CIK | **140 / 500 (28.0%)** |
| 累積 filings | 8,110 |
| 累積 chunks | **658,473** |
| chunks 出力 | 329 MB (139 parquet) |
| sections 出力 | 401 MB (139 parquet) |
| filings_metadata | 1.1 MB (139 parquet) |
| errors.jsonl | 1 件 (DIS edgar cache lock, 致命的でない) |
| zero-chunk CIK | 1 件 (BNY, filings=0) |
| 整合性 | shards 139 ↔ checkpoint 140 - BNY 1 = 一致 ✅ |
| プロセス | SIGTERM で graceful stop, 全 PID 消失確認 |
| Resume スクリプト | `.tmp/FILING_NLP_v2_local/RESUME_STEP2.sh` (実行権限付き) |

## PC 起動後の Resume 手順

```bash
# 1 コマンドで再開
bash /Users/yukihata/Desktop/quants/.tmp/FILING_NLP_v2_local/RESUME_STEP2.sh
```

スクリプトは以下を含む:
- 二重起動チェック
- caffeinate + nohup での起動
- PID を `/tmp/indices_v1_spx_run.pid` に記録
- monitor コマンドを stdout 表示

### Resume 後の進捗確認

```bash
# 完了数スナップショット
uv run python -c "import json; d=json.load(open('/Users/yukihata/Desktop/quants/.tmp/FILING_NLP_v2_local/checkpoints/indices_v1_progress.json')); print(f'completed: {len(d[\"completed\"])} / 500')"

# ライブログ
tail -f /Users/yukihata/Desktop/quants/.tmp/FILING_NLP_v2_local/logs/indices_v1_run.log
```

### 完走見込み

- 残り 360 CIK × 2.79 分/CIK = **約 17 時間**
- Mac 蓋開放継続なら翌朝 (06:00 頃) には 350+ CIK、午後完走見込み

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-26-401 | 出力先をローカル SSD (.tmp/FILING_NLP_v2_local/) に恒久切替、完走後 rsync で NAS に同期 | SMB の 3+ 時間運用での fd stale 化が解消不能、4 回の remount で改善せず |
| dec-2026-05-26-402 | Step2/Step3 長期実行中は Mac 蓋を閉じない (クラムシェル禁止) | caffeinate -i は LID_CLOSE トリガに無力。stalled3 で実証 |

## アクションアイテム

### 新規

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-26-401 | PC 起動後に Step2 を Resume。`bash .tmp/FILING_NLP_v2_local/RESUME_STEP2.sh` 実行。Mac 蓋開放維持必須 | high | pending |
| act-2026-05-26-402 | Step2 完走後 ローカル SSD → NAS への rsync 同期 (chunks/sections/filings_metadata/checkpoints の 4 ディレクトリ) | medium | pending |
| act-2026-05-26-403 | Step3 完走後 config.py:NAS_ROOT を git checkout で元に戻す + CLI に --output-root オプション追加検討 | low | pending |

### 状態更新 (継続)

| ID | 状態 | 補足 |
|----|------|------|
| act-2026-05-25-104 | in_progress (suspended) | 140/500 完了、Resume 待ち |
| act-2026-05-25-204 | in_progress (suspended) | act-104 と同一作業 |
| act-2026-05-25-302 | pending | embed_indices.py への transformers v5 パッチ (Step3 前必須) |
| act-2026-05-25-303 | pending | Issue #3966 起票済み、CI dep test 追加が残課題 |

## 次回の議論トピック

1. **Resume 後の完走確認** (act-401 完了時): 500/500 CIK 達成 + 品質統計レポート (act-2026-05-25-107)
2. **NAS rsync 同期** (act-402): 完走後実行、所要時間と転送速度の実測
3. **act-302 embed_indices.py パッチ** (Step3 前必須): transformers v5 互換性のため tokenizer + model ロードに対応必要
4. **PR #3949 LOW 指摘修正 (Issue #3951)**: Step2 完走と並行 or 後で対応
5. **act-301 (RAY unresolved 6 件) の調査**: RAY 着手前までに片付ける

## 参考情報

- Step2 起動 PID 履歴: 39216 (stalled1) → 43269 → 65178 → 79088 → 89069 → 96002 (stalled5+LOCAL)
- ローカル出力先: `/Users/yukihata/Desktop/quants/.tmp/FILING_NLP_v2_local/`
- NAS 部分保存 (66 CIK 分): `/Volumes/personal_folder/Quants/FILING_NLP_v2/` (rsync 待ち)
- Resume スクリプト: `.tmp/FILING_NLP_v2_local/RESUME_STEP2.sh` (1.5KB, executable)
- 関連 Issue: #3948 (README), #3951 (LOW 修正), #3966 (transformers v5 regression)
- Neo4j Discussion: `disc-2026-05-26-step2-day1`
- 直前メモ: [2026-05-25 Step2 起動 + transformers v5 regression](2026-05-25_discussion-indices-v1-step2-launch.md)
