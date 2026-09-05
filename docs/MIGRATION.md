# 開発環境の移行手順書（Mac → 新PC）

作成日: 2026-09-05
対象: `YukinoMac-mini` から quants の開発環境を撤退させ、別PCで引き継ぐ

---

## 1. 前提と方針

- **GitHub が履歴の正本**。移行時点でローカルに未push コミット・stash は 0 件だった
- **NAS (`/Volumes/personal_folder`) は引き続き使用する**。実データ 20GB は元から NAS 上にある
- Mac の削除は **新PCでの稼働確認が終わってから**行う（手順は §9）
- Neo4j は quants 専用ではなく **note / research / creator と共有**する 4 DB 構成。
  Mac 側では **quants データベースのみ**を削除し、コンテナと他 3 DB は残す

### 資産の所在マップ

| 資産 | 所在 | Mac 削除時 |
|---|---|---|
| ソースコード・ドキュメント・ノートブック | GitHub `YH-05/quants` | 失われない |
| 実データ 20GB (`DATA_DIR`) | NAS `Projects/quants/data/` | 失われない |
| `.env` / `.mcp.json` / `.claude/settings.json` | NAS `Projects/quants/` (sync-nas で同期) | 失われない |
| Neo4j quants DB | NAS `neo4j-dumps/quants.dump` | dump 済み（§6） |
| `data/cache/market_data.db` (120MB) | **Mac のみ** → NAS へ退避済み | 退避済み |
| `.venv` (2.0GB) | Mac のみ | `uv sync` で再構築 |
| HuggingFace モデルキャッシュ (6.6GB) | Mac のみ | 初回実行時に再ダウンロード |

---

## 2. 移行用バックアップの内容

退避先: `/Volumes/personal_folder/quants-migration-2026-09-05/`

| パス | 内容 | 検証 |
|---|---|---|
| `repo-untracked/market_data.db` | 120MB。yfinance 等の市場データキャッシュ。**NAS に存在しなかった唯一の実データ** | SHA-256 一致 |
| `repo-untracked/data-sqlite/` | `edinet.db` (sqlite3 `.backup` で整合コピー)、`_sync_state.json`、`_rate_limit.json` | `integrity_check: ok` / 全 6 テーブルの行数一致 |
| `repo-untracked/.env`, `.mcp.json`, `.mcp.json.bak` | 秘密情報 | SHA-256 一致 |
| `repo-untracked/2026-05-11_nse-owner-obsolete/` | `trash/` の内容 16MB。中身未検証のため保険として退避 | SHA-256 一致 |
| `orphan-worktree/feature-prj38.tar.gz` | 2.7MB。§8 参照 | — |
| `launchd/*.plist` | 13 ファイル。定期実行ジョブの定義 | SHA-256 一致 |
| `scripts/start-quants-neo4j.sh` | Neo4j 自動起動スクリプト | SHA-256 一致 |
| `neo4j/quants.dump` | 1.6MB。2026-09-05 15:48 取得 | §6 の基準値で検証 |

`edinet.db` を除く 26 ファイルは SHA-256 で元ファイルとの一致を確認済み。

---

## 3. 落とし穴（先に読むこと）

### 3-1. NAS のデータが二重化している

NAS には quants のデータ置き場が **2 つ**あり、同名ファイルが両方に存在する。

| 場所 | 参照元 | 実態 |
|---|---|---|
| `/Volumes/personal_folder/Projects/quants/data/` | `.env` の `DATA_DIR` | **正本**。20GB、日次ジョブが更新中 |
| `/Volumes/personal_folder/data/` | リポジトリ内 `data/` の symlink 8 本 | 旧構成。23MB、2026-04-02 以降ほぼ停止 |

例えば `market/all_performance_20260129-1437.json` は両方に同一内容で存在するため、
どちらを見ているか気づきにくい。**`DATA_DIR` 側が正しい。**

### 3-2. `data/` 配下の symlink 8 本は新PCで壊れる

`data/{duckdb,investment_theme,macroeconomics,market,news,processed,stock,Transcript}` は
`/Volumes/personal_folder/data/...` を指す symlink で、**Git 管理下**にある。
つまり clone した時点で新PCにも同じ symlink が再現される。

- **Mac / Linux**: NAS を同じパスにマウントすれば動くが、§3-1 のとおり参照先は旧データ。
  **`DATA_DIR` 経由に統一することを推奨**（symlink を削除するか、正本側に張り替える）
- **Windows**: symlink は機能しない。git の `core.symlinks` 設定次第でリンクの中身を書いた
  ただのテキストファイルになる。`DATA_DIR` 経由のコードパスのみを使うこと

### 3-3. `.env` の `CACHE_DIR` だけローカル絶対パス

`DATA_DIR` と `FRED_HISTORICAL_CACHE_DIR` は NAS を指すが、`CACHE_DIR` だけ
`/Users/yuki/Desktop/quants/data` というこの Mac 固有のパスになっている。
新PCでは自分のリポジトリパスに書き換えること。

### 3-4. 旧ユーザー名 `yukihata` / 旧プロジェクト名 `finance` の残骸

過去のマシン移行の残骸が以下に残っている（今回は未修正）。

| ファイル | 箇所 | 内容 |
|---|---|---|
| `.claude/settings.json` | 8 | `/Users/yukihata/Desktop/finance/...` の permissions allowlist |
| `.claude/settings.local.json` | 15 | 同上（マシン固有ファイル・NAS 同期対象外） |
| `.claude/sync-config.yaml` | 1 | `local_path: /Users/yukihata/Desktop/Quants` |

権限許可リストの変更にあたるため意図的に触っていない。新PCで整理すること。

---

## 4. 新PC セットアップ手順

### 4-1. 前提ソフトウェア

| 必須 | 用途 |
|---|---|
| Python 3.12 系（`>=3.12,<3.13`） | pyproject.toml で固定 |
| `uv` | 依存管理・実行。Makefile 全体が uv 前提 |
| Docker | Neo4j コンテナ |
| `gh` CLI | GitHub Projects 連携 |
| NAS (SMB) マウント | 宅内 NAS の `personal_folder` 共有。接続情報は Mac の Finder サイドバー、または NAS 管理画面で確認する |

| 任意 | 用途 |
|---|---|
| `pandoc` | `/md2docx` スキル（Word 変換）を使う場合のみ |
| `blpapi` | Bloomberg Terminal / BPipe のアクセス権がある場合のみ |

Ruff / pyright / pytest / Hypothesis は `uv sync` で自動導入される。

### 4-2. 手順

```bash
# 1. clone
git clone https://github.com/YH-05/quants.git
cd quants

# 2. 依存構築
uv sync --all-extras

# 3. NAS をマウント（パスは OS に合わせる）
#    macOS: /Volumes/personal_folder
#    Linux: /mnt/personal_folder 等
#    Windows: ネットワークドライブに割り当て

# 4. 秘密情報を配置（§5）
cp .env.example .env
#    NAS から取得する場合:
#    cp /Volumes/personal_folder/Projects/quants/.env .env
#    cp /Volumes/personal_folder/Projects/quants/.mcp.json .mcp.json

# 5. NAS のパスを新環境に合わせて書き換え
#    DATA_DIR / FRED_HISTORICAL_CACHE_DIR / CACHE_DIR

# 6. GitHub 認証（keyring は移行不可なので再ログイン必須）
gh auth login

# 7. Neo4j 起動と復元（§6）
bash scripts/start-neo4j.sh

# 8. 動作確認（§7）
make check-all
```

---

## 5. 秘密情報の再設定

`.env` は 19 変数。値は以下のいずれかから取得する。

1. NAS `Projects/quants/.env`（sync-nas で同期済み。2026-09-05 15:27 時点）
2. 移行バックアップ `quants-migration-2026-09-05/repo-untracked/.env`

変数の一覧と役割は `.env.example` を参照。

**keyring 方式のため物理コピーできないもの**:

- `gh` CLI 認証 → 新PCで `gh auth login`（scopes: `gist`, `project`, `read:org`, `repo`, `workflow`）
- NotebookLM のブラウザセッション → 新PCで再ログイン
- alphaxiv MCP の OAuth → 初回接続時にブラウザ認証

---

## 6. Neo4j の復元

### 6-1. 復元

```bash
# コンテナ起動
docker compose up -d neo4j

# NAS の dump から quants DB を復元
NEO4J_DBS=quants bash scripts/neo4j_sync.sh load
```

`scripts/neo4j_sync.sh` は `NAS_DUMP_DIR`（既定 `/Volumes/personal_folder/neo4j-dumps`）を
参照する。NAS のマウントパスが違う場合は環境変数で上書きすること。

### 6-2. 復元の検証（基準値）

Mac 側で dump した時点の quants DB の内容。新PCで一致すれば復元成功。

| 項目 | 値 |
|---|---|
| ノード総数 | 3,809 |
| リレーション総数 | 8,366 |

ラベル別ノード数:

| ラベル | 件数 | | ラベル | 件数 |
|---|---:|---|---|---:|
| Author | 935 | | DataRequirement | 43 |
| Claim | 885 | | Project | 11 |
| Source | 788 | | Insight | 11 |
| Decision | 272 | | Anomaly | 10 |
| ActionItem | 261 | | Fact | 7 |
| Method | 145 | | MarketRegime | 6 |
| Topic | 141 | | | |
| Entity | 108 | | | |
| Discussion | 105 | | | |
| PerformanceEvidence | 81 | | | |

確認コマンド:

```bash
docker exec neo4j-enterprise cypher-shell -u neo4j -p "$NEO4J_PASSWORD" -d quants \
  "MATCH (n) RETURN count(n); MATCH ()-[r]->() RETURN count(r);"
```

### 6-3. 注意: 他 3 DB のダンプは古い

NAS の `note.dump` / `research.dump` / `creator.dump` / `neo4j.dump` は
**2026-06-05 付**で 3 ヶ月古い。これらは note-finance など他プロジェクトの資産であり、
今回の移行では触っていない。他プロジェクトも移行する場合は別途 dump を取り直すこと。

---

## 7. 動作確認チェックリスト

新PCで以下が全て通れば、Mac を削除してよい。

- [ ] `uv sync --all-extras` が成功する
- [ ] `make check-all` が成功する（format / lint / typecheck / test）
- [ ] NAS がマウントされ、`$DATA_DIR` 配下が読める
- [ ] Neo4j が起動し、quants DB のノード数が 3,809 と一致する（§6-2）
- [ ] `gh auth status` が `YH-05` として認証済みを返す
- [ ] `.mcp.json` の MCP サーバーが接続できる
- [ ] `market_data.db` を NAS から復元した（必要な場合）
- [ ] 移植したい定期ジョブが新PCで動作する（§8）

---

## 8. 定期実行ジョブ（launchd 13 個）

Mac の `~/Library/LaunchAgents/` に登録されている。plist は移行バックアップの
`launchd/` に退避済み。**新PCへは OS に応じて移植が必要**
（Linux は systemd timer / cron、Windows はタスクスケジューラ）。

| ジョブ | スケジュール | 実行内容 |
|---|---|---|
| `com.quants.neo4j` | ログイン時 (RunAtLoad) | `start-quants-neo4j.sh` で Neo4j コンテナ起動 |
| `com.quants.pipeline-nasdaq` | 毎日 1:00 | `market.pipeline --phase 1 --days-back 7` |
| `com.quants.pipeline-alphavantage` | 毎日 2:00 | `market.pipeline --phase 2 --av-budget 25` |
| `com.quants.pipeline-sec-edgar` | 毎日 2:00 | `market.pipeline --phase 3` |
| `com.quants.pipeline-yfinance` | 毎日 2:00 | `market.pipeline --phase 4` |
| `com.quants.etfcom-daily` | 毎日 3:00 | `market.etfcom --frequency daily` |
| `com.quants.neo4j-push` | 毎日 4:00 | `neo4j_sync.sh push`（NAS へ dump） |
| `com.quants.etfcom-weekly` | 日曜 4:00 | `market.etfcom --frequency weekly` |
| `com.quants.etfcom-monthly` | 毎月 1 日 5:00 | `market.etfcom --frequency monthly` |
| `com.quants.fred-sync` | 毎日 6:00 | `market.fred.scripts.sync_historical --auto` |
| `com.quants.edinet-sync` | 毎日 8:00 | `market.edinet.scripts.sync --daily` |
| `com.quants.polymarket-collect` | 0:30 / 6:30 / 12:30 / 18:30 | `market.polymarket` |
| `com.quants.neo4j-push-changed` | 1 時間ごと | `neo4j_sync.sh push --if-changed` |

全ジョブが `/Users/yuki/.local/bin/uv` と `/Users/yuki/Desktop/quants/.env` を
**絶対パスで参照**している。移植時は全て書き換えること。

---

## 9. Mac からの撤退手順

**新PCで §7 のチェックリストが全て通ってから実行すること。**

`scripts/decommission-mac.sh` を使う。既定は dry-run で、何も削除しない。

```bash
# 1. 何が削除されるかを確認（既定・安全）
bash scripts/decommission-mac.sh

# 2. 実際に削除
bash scripts/decommission-mac.sh --execute
```

このスクリプトが行うこと:

1. NAS の移行バックアップが揃っているかを検証（欠けていれば中断）
2. `com.quants.*` の launchd ジョブ 13 個を unload して plist を削除
3. Neo4j の **quants データベースのみ** drop（コンテナと他 3 DB は残す）
4. `~/.local/bin/start-quants-neo4j.sh` を削除
5. リポジトリ `~/Desktop/quants` を削除
6. 孤立 worktree `~/Desktop/.worktrees/Quants` を削除

**このスクリプトが触らないもの**:

- `~/neo4j-data/`（4 DB 共有のため。note-finance が毎日 3:00 に書き込んでいる）
- `com.note-finance.*` の launchd ジョブ 16 個
- `~/Desktop/Quants_data/`（27GB の FNSPID データセット。判断保留）
- NAS 上の一切のデータ

---

## 10. 未決事項

| 項目 | 状況 |
|---|---|
| 移行先 PC の OS | 未定。symlink・launchd の移植方針が変わる（§3-2, §8） |
| `~/Desktop/Quants_data/` 27GB | 判断保留。FNSPID 公開データセットで再取得可能 |
| `data/` の 20GB を NAS 参照のままにするか、新PCにローカルコピーするか | 未定 |
| 13 個の定期ジョブを全て新PCで有効化するか | 未定 |
| 旧ユーザー名 `yukihata` パスの整理（§3-4） | 未実施 |
| Slack MCP / Reddit MCP の接続エラー | 移行前から発生。原因未調査 |
