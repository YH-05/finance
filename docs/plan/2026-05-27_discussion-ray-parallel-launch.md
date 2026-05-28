# 議論メモ: Russell 3000 (RAY) 並行起動の判断と設計

**日付**: 2026-05-27
**議論ID**: disc-2026-05-27-ray-parallel-launch
**参加**: ユーザー + AI
**関連**: [disc-2026-05-27-step2-mac-mini-resume](2026-05-27_discussion-step2-mac-mini-resume.md), [disc-2026-05-27-filing-nlp-v2-nas-sync](2026-05-27_discussion-filing-nlp-v2-nas-sync.md)

## 背景・コンテキスト

- 2026-05-27 11:46 に Mac mini で SPX Step2 (S&P 500) を NAS 直接書き込みで再開 (`dec-2026-05-27-011`)
- 15:26 時点で 165/500 CIK 完了、残 335 CIK ≒ 15.6 時間で完走見込み
- ユーザーが Russell 3000 (RAY Index) についても並行して SEC filings をダウンロードしたい意向を表明
- universe/membership は既に 4 指数 (SPX/SOX/RIY/RAY) 統合済み (2889 CIK)、`run_indices.py` は `--index-filter in_ray` を CLI サポート済み
- RAY 2880 CIK のうち SPX 重複 495、RAY-only 2385

## Phase 1: コンテキスト復元の結果

| 項目 | 状態 |
|------|------|
| SPX Step2 プロセス | ✅ PID 57168 稼働中 (caffeinate 配下, `--index-filter in_spx --workers 8 --rate-rps 5`) |
| SPX checkpoint | 165/500 CIK 完了 (run_id=20260525_180614) |
| universe (4 指数統合) | ✅ 2889 CIK (`universe_indices_v1.parquet`) |
| membership in_ray | ✅ 2880 True、RAY-only 2385、SPX 重複 495 |
| RAY Index source | ✅ `notebook/FILING_NLP/2026-05-22_RAY Index.json` (2906 銘柄) |
| run_indices.py CLI | ✅ `--index-filter in_ray` サポート済み |
| checkpoint パス分離 | ❌ `config.INDICES_V1_PROGRESS_PATH` 固定 → 並行で衝突 |
| Mac mini リソース | M1 8 コア 16GB / NAS 5.4TB / ローカル 57GB |

## 議論のサマリー

### 論点 A: 実行タイミング (順次 vs 並行)

候補:
1. **順次 (Plan A)**: SPX 完走後に RAY 起動 (改修不要、合計 5.3 日)
2. **並行 (Plan B)**: SPX 稼働中に RAY 並列起動 (改修必要、短縮効果 1-1.5 日)
3. 段階並行: SPX 残小くなってから RAY 起動
4. 判断保留

→ ユーザー選択: **2. 並行 (Plan B)**

**判断根拠**:
- universe/membership と CLI が既に RAY 対応済みで改修コスト最小
- 短縮効果 1-1.5 日は無視できない (RAY 単独 4.6 日)
- 監視・劣化フォールバックは既存運用 (`dec-2026-05-27-012`) を拡張可能

### 論点 B: SEC EDGAR rate-rps と workers 配分

候補:
1. Conservative: SPX 3+4w / RAY 2+4w (合計 5 rps + 8 workers)
2. Balanced: SPX 4+6w / RAY 3+4w (合計 7 rps + 10 workers)
3. **Aggressive: SPX 5+8w 現状維持 / RAY 3+4w (合計 8 rps + 12 workers)**
4. Full: SPX 5+8w / RAY 5+8w (合計 10 rps + 16 workers, 上限ギリ)

→ ユーザー選択: **3. Aggressive**

**判断根拠**:
- SPX を遅延させたくない (165 CIK 既投資)
- 合計 8 rps は SEC 公式 10 rps の 80%、burst で一時 10 rps 越えても TokenBucket 制約で復帰
- Mac mini 8 コアに 12 workers は I/O 中心のため許容範囲 (各プロセス内では HTTP I/O 待機が支配的)

### 論点 C: checkpoint パスの改修方針

候補:
1. **A. `run_indices.py` を run_id ベースに改修 (1 行)**
2. B. `--checkpoint-path` CLI オプション追加
3. C. `config.py` に `INDICES_V1_RAY_PROGRESS_PATH` 追加
4. D. シンボリックリンクで島に見せる

→ ユーザー選択: **A. run_id ベース改修**

**実装内容** (run_indices.py L231):
```python
- checkpoint_path = config.INDICES_V1_PROGRESS_PATH
+ checkpoint_path = config.CHECKPOINTS_DIR / f'{args.run_id}_progress.json'
```

**判断根拠**:
- 1 行修正で SPX (run_id=indices_v1) は `indices_v1_progress.json` のまま完全互換
- RAY (run_id=indices_v1_ray) は `indices_v1_ray_progress.json` で自動分離
- SPX 稼働中に適用可能 (起動済みプロセスはメモリロード済みのため影響なし)

### 論点 D: SMB fd 劣化時のフォールバック

候補:
1. **RAY 優先停止 → SPX 単独継続**
2. 両方停止 → NAS remount → SPX 単独再開
3. SPX を B 案 (ローカル) 切替 + RAY 一時停止
4. 監視継続 + 人判断のみ

→ ユーザー選択: **1. RAY 優先停止 → SPX 単独継続**

**判断根拠**:
- SPX 復元コスト高 (既に 165 CIK 投資)
- 並行による負荷増加が劣化主因と仮定し、RAY を切り離せば SPX 単独運用に戻る
- ローカル退避 (B 案) は RAY (84-140GB) の容量制約で不可

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-27-014 | RAY (Russell 3000) を SPX Step2 稼働中に並行起動 (Plan B)。RAY-only 2385 CIK 対象、SPX 重複 495 は SPX 側で取得済み | universe/membership/CLI が既に RAY 対応、改修コスト最小 |
| dec-2026-05-27-015 | 並行時リソース配分: SPX 5+8w 現状維持 / RAY 3+4w (合計 8 rps + 12 workers) | SEC 公式 10 rps の 80%、SPX 遅延回避 |
| dec-2026-05-27-016 | `run_indices.py` L231 の checkpoint_path を `config.CHECKPOINTS_DIR / f'{args.run_id}_progress.json'` に改修。SPX 互換維持 (indices_v1_progress.json)、RAY は indices_v1_ray_progress.json | 1 行修正で衝突回避、SPX 稼働中適用可 |
| dec-2026-05-27-017 | SMB fd 劣化指標抵触時は RAY 優先停止 → SPX 単独継続 → SPX 完走後 RAY を NAS で単独再開 | SPX 復元コスト高、ローカル退避は RAY 容量制約で不可 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-27-012 | run_indices.py L231 を 1 行修正 (checkpoint_path を run_id ベースに) | high | pending |
| act-2026-05-27-013 | RAY 起動スクリプト `.tmp/step2_resume/LAUNCH_RAY.sh` 作成 + nohup + caffeinate で起動 (`--run-id indices_v1_ray --index-filter in_ray --workers 4 --rate-rps 3`) | high | pending |
| act-2026-05-27-014 | 多 PID 対応の監視スクリプト `.tmp/step2_resume/monitor_step2_dual.sh` 作成。SPX (PID 57168) と RAY (新 PID) を個別に閾値監視 | high | pending |
| act-2026-05-27-015 | RAY 完走後 (約 7 日見込み) の summary 検証 + zero-chunk CIK 分類 + Step3 (embed_indices.py) の indices_v1_ray 拡張 | medium | pending |

## 時間試算

| ケース | SPX 残時間 | RAY 完走時間 | 合計 |
|--------|-----------|-------------|------|
| 順次 (Plan A) | 15.6h | RAY-only 2385 × 2.79min = 111h | **5.3 日** |
| 並行 (Plan B) | 15.6h (現状維持) | RAY 3 rps なら ~165h (約 6.9 日) | **約 7 日 (SPX 並行)** |

並行効果は SEC rate limit がボトルネックでない場合に顕著。Mac mini CPU は I/O 待機支配なので並行で実質的にスループット改善が見込まれる。

## 並行実行の事後検証 (2026-05-27 15:39 起動 → 16:04 強制終了)

### 経緯
| 時刻 | イベント |
|------|---------|
| 15:39 | RAY 並行起動 (PID 96678, workers 4, rate 3 rps) |
| 15:42 | 初回監視: 両プロセス健全 (SPX 168, RAY 1) |
| 15:58 | 最後の正常チェック (SPX 170, RAY 7) |
| **15:59** | **SMB 全断検知** (Bash session の stat/ls すべて Permission denied) |
| 16:00-16:03 | ALERT 連続発火、両プロセスは CPU 稼働中だが新規 open 不能 |
| 16:04 | ユーザー判断で両方 SIGTERM → 4 秒で graceful exit |
| 16:04 | `diskutil unmount force` + `open smb://` で SMB remount 成功 |
| 16:04 | SPX 単独再起動 (PID 6210, skipped 170 / todo 330) |

### 観察された破綻パターン
1. SPX 単独運用での SMB 劣化は過去 3 時間サイクル (`dec-2026-05-26-402`)
2. **並行運用では約 20 分で破綻** (約 8 倍速い劣化)
3. 並行書き込み圧力 (合計 8 rps + 12 workers + tokenizer×2 メモリ占有) が SMB セッション耐性を超えた
4. プロセスは fd を持っているため CPU 上は稼働継続するが、次の open/flush で失敗する

### 追加決定事項

| ID | 内容 |
|----|------|
| **dec-2026-05-27-018** | Mac mini + SMB NAS 環境では SPX/RAY 並行起動を**禁止**。本日 20 分で破綻、運用不可と判断 |
| **dec-2026-05-27-019** | 将来並行を再試行する場合の前提: (a) NFS/iSCSI 移行、(b) ローカル完走 → rsync、(c) 別 PC 実行、(d) Tailscale + SSH/scp。SMB 据え置きでは並行非推奨 |

### ActionItem 状態更新
| ID | 旧状態 | 新状態 | 備考 |
|----|--------|--------|------|
| act-2026-05-27-013 | completed | **rolled_back** | RAY 起動 → 20 分で全断 |
| act-2026-05-27-014 | completed | **rolled_back** | 監視は機能したが Bash session 経由の stat が劣化検知に転用された |
| **act-2026-05-27-016** | (新規) | in_progress | SPX 単独再起動 (PID 6210, 16:04) の閾値監視継続 |

### RAY checkpoint の保持
`/Volumes/personal_folder/Quants/FILING_NLP_v2/checkpoints/indices_v1_ray_progress.json` (7 CIK 完了) は削除せず保持。SPX 完走後の RAY 単独実行で起点として再利用可能。

## 次回の議論トピック

- SPX 単独再起動 (16:04, 170 CIK 起点) の安定性と完走見込み更新
- RAY 単独実行のタイミング (SPX 完走後、約 17h 後)
- SMB セッション耐性の構造的解決 (NFS / iSCSI / Tailscale + scp)
- Step3 (embed_indices.py) の indices_v1_ray 対応 (act-015)

## 参考情報

- 起動スクリプト雛形: `.tmp/step2_resume/RESUME_STEP2_MAC_MINI.sh` (SPX 用)
- 監視スクリプト雛形: `.tmp/step2_resume/monitor_step2.sh`
- universe: `/Volumes/personal_folder/Quants/FILING_NLP_v2/universe/universe_indices_v1.parquet`
- membership: `/Volumes/personal_folder/Quants/FILING_NLP_v2/index_membership/membership_indices_v1.parquet`
- RAY checkpoint (作成予定): `/Volumes/personal_folder/Quants/FILING_NLP_v2/checkpoints/indices_v1_ray_progress.json`
- RAY 出力 (作成予定): `sections/indices_v1_ray/`, `chunks/indices_v1_ray/`
- 関連 Decision: `dec-2026-05-27-011` (NAS 直接書き込み), `dec-2026-05-27-012` (SMB fd 監視閾値), `dec-2026-05-27-013` (config.py NAS パス復帰)
