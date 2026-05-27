# 議論メモ: FILING_NLP_v2 indices_v1 ローカル SSD → NAS 同期実施

**日付**: 2026-05-27
**議論ID**: disc-2026-05-27-filing-nlp-v2-nas-sync
**参加**: ユーザー + AI

## 背景・コンテキスト

- 2026-05-25 18:06 JST に SPX 500 CIK の Step2 (10-K/10-Q chunks 生成) を NAS (`/Volumes/personal_folder/Quants/FILING_NLP_v2/`) で開始
- 2026-05-26 に SMB stale fd 問題で 4 回の stall サイクルを経験 (Mac 蓋閉じ + 3 時間連続使用での fd 劣化)
- B 案として出力先をローカル SSD (`.tmp/FILING_NLP_v2_local/`) に切替、errors 0 件 + 2.79分/CIK で安定稼働
- 2026-05-26 夜に PC シャットダウンで Step2 中断 (140/500 CIK = 28%)
- `notebook/FILING_NLP/pipeline/config.py` L8-10 の AIDEV-NOTE に「完走後 rsync で NAS に同期予定」と明記
- ユーザーが MacBook Air のローカル新規データを NAS に同期する要求 (`/project-discuss` から)

## 議論のサマリー

### 論点 A: 同期の目的・運用方針

候補:
1. **Step2 を NAS で再開**: ローカル成果を NAS に同期 → config.py 戻し → Step2 再開 (SMB stale 再発リスク)
2. **完走後に NAS 移行**: Step2 をローカルで完走 (残 17 時間) → まとめて NAS rsync (ローカル残 31GB ギリギリ)
3. **二重保存**: ローカル出力 + 定期 NAS rsync (冗長運用)
4. **ローカル成果のみ同期**: 今あるローカル分のみ NAS に上書き、Step2 の今後の出力先は別決定

→ ユーザー選択: **4. ローカル成果のみ同期** (今すぐ片付ける目的)

### 論点 B: rsync オプション (`--delete` の扱い)

候補:
1. `--delete` あり: NAS をローカルのスナップショットに完全置換
2. `--delete` なし: 追加・上書きのみで NAS のみのファイル残す
3. dry-run で差分確認してから決める

→ ユーザー選択: **3. dry-run で差分確認してから決める**

**dry-run 結果 (重要発見)**:
- トップレベル `--delete` で 299 ファイル削除予定
- うち `sections/pilot100/` (132MB), `chunks/pilot100/` (105MB), `sections/smoke/` (11MB) が消失対象
- `disc-2026-05-25-indices-v1-pipeline` で「pilot100 は NAS に残置」と決定済み
- → トップレベル `--delete` は危険、サブディレクトリ単位に絞るべき

### 論点 B': 同期範囲 (pilot100/smoke 保護)

候補:
1. `indices_v1` サブディレクトリ単位で `--delete` (推奨)
2. トップレベル + `--exclude=pilot100,smoke`
3. `--delete` なしで追加・上書きのみ

→ ユーザー選択: **1. indices_v1 サブディレクトリ単位で --delete (推奨)**

### 実行と検証

**dry-run (最終)**:
| 対象 | 転送サイズ | 削除対象 |
|------|----------|----------|
| `sections/indices_v1/` | 420MB | 0 件 ✅ |
| `chunks/indices_v1/` | 344MB | 0 件 ✅ |
| `filings_metadata/indices_v1/` | 1MB | 0 件 ✅ |
| `universe/` | 423KB (2ファイル) | (--delete なし) |
| `index_membership/` | 23KB (1ファイル) | (--delete なし) |
| **合計** | **約766MB** | — |

ローカルが完全上位集合のため、`indices_v1` 内 `--delete` は実質ノーオペで安全。

**本実行 (5 つ直列、SMB 並列回避)**:
- 経過時間: **303 秒 (5分3秒)**
- 平均スループット: 3.3MB/sec
- SMB エラー: **0 件**
- 完了: 2026-05-27 11:00 頃

**検証**:
- ローカル/NAS ともに `sections/chunks/filings_metadata/indices_v1` = **139 ファイル一致**
- pilot100 無事保持 (sections 132MB / chunks 105MB)
- サイズ完全一致 (差はディレクトリブロック単位のみ)

## 追加実施: checkpoints 同期

ユーザー指示で本セッション中に追加同期。

**比較**:
| 場所 | completed CIK | タイムスタンプ |
|------|--------------|---------------|
| ローカル | **140** ✅ | 2026-05-26 18:01 |
| NAS (古い) | 66 | 2026-05-26 13:21 |

**実行**: `rsync -av` (`--delete` なし)

- `checkpoints/indices_v1_progress.json` のみ上書き (26KB)
- `checkpoints/pilot100_progress.json` (19KB) と `smoke_progress.json` (1KB) は保持
- 結果: NAS 側 `indices_v1_progress.json` が 140 CIK 完了状態に更新

## 自宅 Mac mini で Step2 を再開する場合の手順

NAS 上にデータと進捗が揃ったため、自宅 Mac mini で再開可能:

1. `personal_folder` を SMB マウント
2. `git pull` で最新コード取得
3. `notebook/FILING_NLP/pipeline/config.py` L10 を NAS パスに戻す:
   ```python
   NAS_ROOT = Path("/Volumes/personal_folder/Quants/FILING_NLP_v2")
   ```
4. `uv sync --all-extras`
5. HF cache に `Alibaba-NLP/gte-Qwen2-1.5B-instruct` が無ければダウンロード
6. `run_indices.py` を `run_id=20260525_180614` 指定で再開 (completed 140 CIK は自動スキップ)

**残時間見積**: 2.79分/CIK × 360 CIK ≈ 17時間

**注意点**:
- Mac mini は据置で蓋がないため `LID_CLOSE` トリガによる SMB 切断は発生しない
- ただし 3時間超の連続 SMB 書き込みでの fd 劣化は別問題として残る
- 実際の再開判断は `act-2026-05-27-007` (出力先決定) の結論を待つ

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-27-008 | FILING_NLP_v2 のローカル → NAS 同期は `indices_v1` サブディレクトリ単位で `rsync -av --delete` を使用。universe/index_membership は個別ファイル単位で `--delete` なし差分同期。checkpoints/logs は触らない | トップレベル `--delete` は pilot100/smoke 消失のため除外。dry-run で `indices_v1` 内削除 0 件確認済み |
| dec-2026-05-27-009 | 本セッションは「ローカル成果のみ同期」スコープに限定。Step2 再開時の出力先 (NAS / ローカル継続 / 二重保存) と config.py NAS_ROOT 戻しは別セッション決定 | SMB stale 問題の再発リスク (dec-2026-05-26-402: Mac 蓋閉じ禁止) と、ローカル残量 31GB (85% 使用) / 完走 15-25GB 想定で余裕薄 |
| dec-2026-05-27-010 | checkpoints は `rsync -av` (`--delete` なし) で追加同期。`indices_v1_progress.json` のみ上書き、`pilot100_progress.json` と `smoke_progress.json` は保持 | ユーザー要求「追加同期」のため `--delete` なし。indices_v1 は 140 CIK > 66 CIK で上書き必要、pilot100/smoke は無関係なため残置価値あり |

## アクションアイテム

| ID | 内容 | 優先度 | 期限 |
|----|------|--------|------|
| act-2026-05-27-007 | Step2 (SPX 500 CIK 残 360) 再開時の出力先決定。候補: (1) NAS 戻し + 蓋閉じ厳禁 + 3 時間 remount 運用 (2) ローカル完走後一括同期 (3) 二重保存。判断材料: ローカル残量、SMB 安定性、Step2 残 17 時間 | medium | 未定 |
| act-2026-05-27-008 | 自宅 Mac mini で Step2 再開する場合の準備手順実行 (SMB マウント / git pull / config.py NAS_ROOT 戻し / uv sync / HF cache / run_id=20260525_180614 で再開)。act-007 で「Mac mini + NAS 出力で再開」が決まった後に実施 | medium | 未定 |

## 次回の議論トピック

- Step2 再開時の出力先と運用方針 (act-2026-05-27-007 の判断)
- 自宅 Mac mini vs MacBook Air の使い分け (Mac mini は据置で LID_CLOSE 無し、安定性高)
- config.py `NAS_ROOT` 戻しのタイミング
- SMB stale 問題の根本対処 (Tailscale + SSH/scp 移行検討の余地)

## 参考情報

- 関連 Discussion: `disc-2026-05-26-step2-day1` (4 回 stall 経緯)
- 関連 Discussion: `disc-2026-05-25-indices-v1-pipeline` (pilot100 残置決定)
- 関連 Decision: `dec-2026-05-26-402` (Mac 蓋閉じ禁止運用)
- 実装ファイル: `notebook/FILING_NLP/pipeline/config.py`
- RESUME スクリプト: `.tmp/FILING_NLP_v2_local/RESUME_STEP2.sh`
