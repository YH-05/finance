# 議論メモ: edinet-sync launchd の NAS 書き込み失敗と修復方針

**日付**: 2026-05-27
**議論ID**: disc-2026-05-27-edinet-launchd-nas-failure
**参加**: ユーザー + AI
**関連議論**: [[disc-2026-03-28-edinet-launchd-nas-migration]], [[disc-2026-04-12-launchd-maintenance]]

## 背景・コンテキスト

EDINET DB の日次同期は 2026-03-28 から launchd（`com.quants.edinet-sync`）で毎日 08:00 に自動実行する設定で運用中。
`DATA_DIR=/Volumes/personal_folder/Projects/quants/data` を直接書き込み先としていた。

ユーザーから「NAS への保存が失敗している」との指摘があり原因調査を実施。

## 根本原因

**launchd セッションから NAS マウント `/Volumes/personal_folder` への書き込みが拒否されている。**

### エビデンス

`~/Library/Logs/quants/edinet-sync-error.log` 最新エラー:

```
PermissionError: [Errno 13] Permission denied: '/Volumes/personal_folder'
  at syncer.py:155 → rate_limit_path.parent.mkdir(parents=True, exist_ok=True)
```

`mkdir(parents=True, exist_ok=True)` が `/Volumes/personal_folder/Projects/quants/data/sqlite` を作る過程で、親ディレクトリが全て「存在しない」と判定され、最終的に `/Volumes/personal_folder` 自体への書き込みで Permission denied。

= launchd プロセスからは、GUI セッションでマウント済みの SMB の中身が**見えていない**（マウントポイントは存在するが中身は別ユーザーコンテキスト扱い）。

### タイムライン

| 日時 | 状態 |
|------|------|
| 〜2026-05-01 08:00 | 正常（NAS の `edinet.db` 最終更新時刻＝5/1 08:01） |
| 2026-05-02 以降 | 毎日 08:00 の launchd 起動時に PermissionError で即死 |
| 2026-05-27（現在） | 約3週間連続失敗中 |

### 周辺事実

- `.env`: `DATA_DIR=/Volumes/personal_folder/Projects/quants/data`
- 対話セッション（GUI/Terminal経由）からは NAS 読み書き可能
- 過去議論（2026-04-12）で **CACHE_DIR はローカル分離済**（SQLite I/O 不安定対策）
- メイン DB（edinet.db, ~10MB）はまだ NAS 直書き設定のまま残っていた

## 議論のサマリー

### 検討した解決方針

| 案 | 概要 | 採否 |
|----|------|------|
| A. DATA_DIR 完全ローカル化 + rsync ミラー | 最もシンプル | 不採用（複数PC共有DB運用に不向き） |
| B. launchd の NAS アクセス回復のみ | TCC許可付与 / 常時マウント | 部分採用（常時マウントは採用） |
| **C. ローカル DL → NAS 合体方式** | 2ステップで実行、テーブル単位マージ | **採用** |
| D. cron 等別ルートで実行 | launchd 統一運用が崩れる | 不採用 |

### 採用方式の構造

```
[launchd 08:00]
   ↓
1) NAS DB → ローカル DB に取得（既存データ）
   ↓
2) market.edinet.scripts.sync --daily 実行（ローカルに新規追記）
   ↓
3) ローカル DB → NAS DB へテーブル単位 INSERT OR REPLACE マージ
```

NAS 可視化は `/etc/auto_smb` で常時マウント化することで launchd セッションからも見える状態にする。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-27-001 | edinet-sync を「ローカル DL → NAS 合体」の2段構成にする | 単一書き込み先を NAS にする現方式は launchd 制約で破綻するため |
| dec-2026-05-27-002 | 1つの launchd ジョブ内で 2ステップを shell スクリプトで実行 | 責務分散しないことで運用と監視を単純化 |
| dec-2026-05-27-003 | NAS マウントは `/etc/auto_smb` + `/etc/auto_master` で常時マウント化 | launchd セッションからも NAS が見える状態を恒久化 |
| dec-2026-05-27-004 | DB 同期はテーブル単位 INSERT OR REPLACE マージ | 複数 PC から同一 NAS DB を更新するケースに備えた安全策 |

## アクションアイテム（実施結果）

| ID | 内容 | 状態 | 結果 |
|----|------|------|------|
| act-2026-05-27-001 | NAS常時マウント方式の検証 | ✅ 完了 | `/etc/auto_smb` はSIP保護で不可、LaunchDaemon でシステムマウントは成立するも per-uid SMB により yuki から読めず、最終的に **macOS TCC「Network Volumes」が本質的原因** と特定（dec-005）。LaunchDaemon等のartifactは全てクリーンアップ済み。 |
| act-2026-05-27-002 | `scripts/edinet_merge_to_nas.py` 実装 | ✅ 完了 | 6テーブル INSERT OR REPLACE、--dry-run/--source/--target対応、トランザクション保護。動作確認: 3839社/21869財務/21855比率を NAS と完全一致。 |
| act-2026-05-27-003 | Aqua-session 用 NAS 同期ラッパー実装 | ✅ 完了 | `scripts/sync_edinet_to_nas.sh` 実装。マウント検査・TCC書き込みテスト・ログ管理。週次手動運用や Login Items 経由を想定。 |
| act-2026-05-27-004 | `com.quants.edinet-sync.plist` 改修 | ✅ 完了 | `EDINET_DB_PATH=/Users/yuki/Desktop/quants/data/sqlite/edinet.db` を EnvironmentVariables に追加（act-007 と統合）。plutil OK、launchctl reload 済み。 |
| act-2026-05-27-005 | launchctl start で手動テスト | ✅ 完了 | exit code 0、stderr 0バイト、47社新規処理（1506→1553社、財務+661/比率+661）、Errors: 0。 |
| act-2026-05-27-006 | 旧 stderr ログをクリア & 動作確認 | ✅ 完了 | `edinet-sync-error.log.before-tcc-fix-2026-05-27` として退避。act-005 が実質的に翌朝の挙動を実証済み。 |
| act-2026-05-27-007 | DATA_DIR ローカル化 | ✅ 完了 | `.env` は変更せず（他ジョブへの波及回避）、plist EnvironmentVariables の `EDINET_DB_PATH` で edinet のみローカル化。`utils_core/settings.py` の `load_dotenv(override=True)` の挙動も判明。 |

## 真の根本原因（実施で判明）

| 仮説 | 検証結果 |
|------|----------|
| `/etc/auto_master` 修正で auto_smb 適用 | ❌ SIP 保護で書き込み拒否（cp/mv/printf >> 全て Operation not permitted） |
| LaunchDaemon でシステムマウント | ❌ マウント成立するも、per-uid SMB セッションのため yuki から ls 不可 |
| yuki セッションマウント + launchd 可視 | ❌ mount は見えるが ls/touch が **TCC で Operation not permitted** |
| **macOS TCC「Network Volumes」が真の原因** | ✅ 確定 — Terminal.app は TCC許可済みだが launchd 経由の /bin/sh / uv バイナリは未許可 |

## 副次的に判明した問題

- `polymarket-collect`, `pipeline-yfinance`, `pipeline-alphavantage`, `pipeline-sec-edgar`, `pipeline-nasdaq`, `fred-sync` の各 launchd ジョブも同じ TCC 制約により NAS 書き込みが失敗中（stderr に `Permission denied: '/Volumes/personal_folder'`）。これらは別 Issue で対応推奨。
- `/Users/yuki/Desktop/quants/data/sqlite` 他のローカルシンボリックリンクが旧 NAS パス `/Volumes/personal_folder/data/sqlite/` を指していた（現行 NAS パスは `/Volumes/personal_folder/Projects/quants/data/sqlite/`）。edinet 関連は実ディレクトリ化済み。

## 実装方針メモ

### NAS マウント永続化

```bash
# /etc/auto_smb（パスワードは Keychain 経由が望ましい）
/Volumes/personal_folder -fstype=smbfs ://yuki@DH2300-48C1.local/personal_folder

# /etc/auto_master 末尾に追加
/- auto_smb

# 反映
sudo automount -vc
```

### 想定スクリプト構成

```
scripts/
├── com.quants.edinet-sync.plist        # 改修対象
├── edinet_sync_with_nas.sh             # 新規（2ステップ実行）
└── edinet_merge_to_nas.py              # 新規（テーブル単位マージ）
```

`edinet_sync_with_nas.sh`:
1. NAS 可視性チェック（不可なら異常終了）
2. NAS edinet.db → ローカル `~/Desktop/quants/data/sqlite/edinet.db` にコピー
3. `uv run python -m market.edinet.scripts.sync --daily` を実行
4. `uv run python scripts/edinet_merge_to_nas.py` を実行（ローカル → NAS マージ）

### マージスクリプトの主要テーブル候補

edinet DB の主要テーブル:
- `companies`
- `financials`
- `ratios`
- `rate_limit_state`（同期不要、ローカルで完結）
- 他、`market.edinet.db.schemas` 配下を確認して列挙

各テーブルで PRIMARY KEY ベースに `INSERT OR REPLACE` で更新。

## 次回の議論トピック

- マージスクリプトの実装後の動作検証結果
- 他の launchd ジョブ（`pipeline-yfinance`, `pipeline-sec-edgar` 等）でも DATA_DIR が NAS を指している場合は同じ対処が必要かの棚卸し
- NAS 自動マウントが安定するか（数日運用後の評価）

## 参考情報

- 過去議論: `docs/plan/2026-03-28_discussion-edinet-launchd-nas-migration.md`
- 過去議論: `docs/plan/2026-04-12_discussion-launchd-maintenance.md`
- 現 plist: `~/Library/LaunchAgents/com.quants.edinet-sync.plist`
- エラーログ: `~/Library/Logs/quants/edinet-sync-error.log`
