# Neo4j 手動同期手順（NAS 経由）

MacBook Air（メイン PC）の Neo4j データを、自宅 Mac へ NAS 経由で手動同期するための手順。

**初回検証日**: 2026-05-27（MacBook Air → 自宅 Mac、4 DB 同期成功）

## 概要

- **方式**: `neo4j-admin database dump` / `load` による論理バックアップ
- **転送経路**: NAS（`/Volumes/personal_folder`）を中継ストレージとして利用
- **同期方向**: MacBook Air ⇄ 自宅 Mac（双方向、「最後に書いた側が source」）
- **対象 DB**: `quants`, `research`, `note`, `creator`, `neo4j`（5 DB）
- **変更検知**: APOC `apoc.monitor.tx` の lastTxId 比較で**全 write 経路**の更新を検知（`push --if-changed`）
- **自動同期**: 3層（Stop hook / 毎時 launchd / 毎朝4時 launchd）。詳細は「[自動化](#自動化-claude-code-hooks-連動--launchd)」節

## 前提条件

| 項目 | 内容 |
|------|------|
| Neo4j バージョン | 両 Mac で `neo4j:5.26-enterprise` 必須（マイナーバージョン差があると load 失敗の可能性） |
| コンテナ名 | 両 Mac で `neo4j-enterprise`（`docker-compose.yml` で固定） |
| 認証 | ユーザー `neo4j` / パスワード `gomasuke`（`NEO4J_PASSWORD` 環境変数で上書き可） |
| NAS マウント | 両 Mac で `/Volumes/personal_folder` にマウント済み |
| bind mount | 両 Mac とも `${HOME}/neo4j-data/enterprise/` を使用（`docker-compose.yml` で `${HOME}` 展開） |
| DB 存在 | 自宅 Mac 側に対象 DB が未作成でも OK（Phase 2 Step B で新規作成可能） |
| APOC | Core は `NEO4J_PLUGINS=["apoc"]` で自動DL。`push --if-changed` が使う `apoc.monitor.tx` は **APOC Extended** 専用のため、別途 `scripts/install-apoc-extended.sh` で手動導入（先頭2桁が Neo4j と一致する 5.26.x、現状 5.26.4）。未導入時は lastTxId 取得に失敗し「常に push」へ安全側に縮退 |

## 実測値（2026-06-02 時点）

| DB | dump サイズ | ノード数 | リレーション数 |
|----|------------|---------|---------------|
| `quants` | 1.7M | 3,809 | 8,366 |
| `research` | 64M | 34,059 | 529,078 |
| `note` | 480K | 838 | 983 |
| `creator` | 131M | 15,312 | 31,362 |
| `neo4j`（デフォルト） | 38K | 59 | 58 |
| **合計** | **約 197M** | **54,077** | **569,847** |

各 DB の dump 処理時間: 約 0.3〜1 秒（ローカル NVMe）。
自動 push（5 DB の dump → NAS 転送 → sync-state 更新）の所要時間: 約 1〜2 分（NAS 転送が大半）。
手動の全工程（dump → NAS 転送 → load → 件数検証）の所要時間: 約 30 分以内。

---

## Phase 1: MacBook Air（メイン PC）で dump → NAS へ転送

```bash
# 1. NAS マウント確認
ls /Volumes/personal_folder

# 2. NAS にダンプ置き場を作成
mkdir -p /Volumes/personal_folder/neo4j-dumps

# 3. コンテナ内に作業ディレクトリを作成
docker exec neo4j-enterprise mkdir -p /tmp/dumps

# 4. 各 DB を停止 → dump → 起動
for DB in quants research note creator neo4j; do
  echo "=== Dumping $DB ==="
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system "STOP DATABASE $DB WAIT"
  docker exec neo4j-enterprise neo4j-admin database dump $DB \
    --to-path=/tmp/dumps --overwrite-destination=true
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system "START DATABASE $DB WAIT"
done

# 5. コンテナから NAS へコピー
for DB in quants research note creator neo4j; do
  docker cp neo4j-enterprise:/tmp/dumps/$DB.dump /Volumes/personal_folder/neo4j-dumps/
done

# 6. 確認（タイムスタンプとサイズをチェック）
ls -lh /Volumes/personal_folder/neo4j-dumps/

# 7. 一時ファイル削除
docker exec neo4j-enterprise rm -rf /tmp/dumps
```

> 💡 `STOP DATABASE ... WAIT` の `WAIT` を付けることでアクティブな接続が切れるまで待ちます。これを省くとアクティブセッション中は STOP が完了しません。

---

## Phase 2: 自宅 Mac で NAS から取り込み → load

自宅 Mac で以下を実行する。

### Step 0: 事前確認

```bash
# NAS マウント確認 (5 ファイルが見えること)
ls -lh /Volumes/personal_folder/neo4j-dumps/

# コンテナ稼働確認 (Status が "Up X minutes (healthy)" であること)
docker ps --filter "name=neo4j-enterprise" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# health が starting の場合は healthy になるまで待つ
until [ "$(docker inspect -f '{{.State.Health.Status}}' neo4j-enterprise 2>/dev/null)" = "healthy" ]; do
  echo "waiting Neo4j to become healthy..."
  sleep 2
done

# 既存 DB の確認 (Step A/B の判断に使う)
docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system \
  "SHOW DATABASES YIELD name, currentStatus"
```

### Step 1: NAS から dump をコンテナへ投入

```bash
# 作業ディレクトリ作成
docker exec neo4j-enterprise mkdir -p /tmp/dumps

# 5 ファイルをコンテナへコピー
for DB in quants research note creator neo4j; do
  echo "=== Copying $DB.dump ==="
  docker cp /Volumes/personal_folder/neo4j-dumps/$DB.dump neo4j-enterprise:/tmp/dumps/
done

# 確認 (MacBook Air と同じサイズか)
docker exec neo4j-enterprise ls -lh /tmp/dumps/
```

> ⚠️ **`docker cp` の宛先パスは必ず先頭 `/` 付き**で指定すること。`neo4j-enterprise:tmp/dumps/`（先頭 `/` なし）でも環境によっては `/tmp/dumps/` に展開される場合があるが、挙動が不安定なため絶対パス推奨。

### Step 2-A: DB が既に存在する場合（上書き load）

```bash
for DB in quants research note creator neo4j; do
  echo "=== [$DB] Loading (overwrite) ==="
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system "STOP DATABASE $DB WAIT"
  docker exec neo4j-enterprise neo4j-admin database load $DB \
    --from-path=/tmp/dumps --overwrite-destination=true
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system "START DATABASE $DB WAIT"
done
```

### Step 2-B: DB が未登録の場合（新規作成 + load）✅ 検証済み

新規構築した Neo4j コンテナで初めて load する場合の標準手順。`load` を先にして、その後 `CREATE DATABASE` で DBMS に登録する。

```bash
for DB in quants research note creator neo4j; do
  echo ""
  echo "============================================"
  echo "  [$DB] load + register"
  echo "============================================"

  # 1. dump からファイル展開 (DB が未登録なので STOP 不要)
  docker exec neo4j-enterprise neo4j-admin database load $DB \
    --from-path=/tmp/dumps --overwrite-destination=true

  # 2. DBMS に登録 (これをやらないと SHOW DATABASES に出ない)
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system \
    "CREATE DATABASE $DB IF NOT EXISTS WAIT"
done

# 5 DB すべて online か確認
docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system \
  "SHOW DATABASES YIELD name, currentStatus WHERE name IN ['quants','research','note','creator','neo4j'] RETURN name, currentStatus"
```

### Step 3: 件数検証

```bash
for DB in quants research note creator neo4j; do
  echo "=== $DB ==="
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d $DB \
    "MATCH (n) RETURN count(n) AS nodes"
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d $DB \
    "MATCH ()-[r]->() RETURN count(r) AS relationships"
done
```

MacBook Air 側で同じコマンドを実行し、件数が完全一致すれば同期成功。

### Step 4: クリーンアップ

```bash
# コンテナ内の一時 dump を削除
docker exec neo4j-enterprise rm -rf /tmp/dumps

# NAS 上の dump は次回同期まで保持してもよい (再 load 用バックアップ)
```

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `Database '<name>' does not exist` (load 時) | DB 未登録 | Step 2-B に切り替え |
| `Failed to load database... store format ...` | バージョン差 (5.26 以外) | コンテナを `5.26-enterprise` に揃える |
| `STOP DATABASE` が完了しない | アクティブな接続あり | Claude Code / Browser UI を一度閉じてから再試行、または `STOP DATABASE ... WAIT` を使う |
| `mkdir /host_mnt/Volumes/...: permission denied` | bind mount 先（外付け SSD）が切断 | `${HOME}/neo4j-data/` 構成に切り替え（`docker-compose.yml` 修正） |
| `docker cp` 後にコンテナ内で `*.dump` が見つからない | 宛先パスの先頭 `/` 漏れ | `find / -name "*.dump"` で実際の場所を探す |
| load 後に件数が 0 | DB 未起動 or 異なる DBMS にロード | `START DATABASE <name> WAIT`、`SHOW DATABASES` で確認 |
| `cypher-shell ... \| grep -q "1 row"` の起動待ちループが終わらない | Neo4j 5.x の cypher-shell は `1 row` を出力しないため判定が永久に失敗 | `until [ "$(docker inspect -f '{{.State.Health.Status}}' neo4j-enterprise)" = "healthy" ]; do ...` で healthcheck の結果を見る |

---

## 既存環境のセットアップ（自宅 Mac 初回構築）

自宅 Mac に Neo4j コンテナがまだない場合、または `/Volumes/NeoData/` 等の古い構成のコンテナがある場合のセットアップ手順。

### 1. 古いコンテナの削除（必要に応じて）

```bash
docker rm neo4j-enterprise 2>/dev/null
# 残骸コンテナがあれば併せて削除
docker ps -a --format "{{.Names}}" | grep neo4j | xargs -r docker rm
```

### 2. ローカルデータディレクトリ作成

```bash
mkdir -p ~/neo4j-data/enterprise/{data,logs,plugins,import}
```

### 3. quants リポジトリ取得（未取得の場合）

```bash
cd ~/Desktop
git clone git@github.com:YH-05/quants.git
cd quants
```

### 4. コンテナ起動

```bash
cd ~/Desktop/quants
docker compose up -d neo4j

# 起動完了を待つ (初回は APOC ダウンロードで 1〜2 分)
# Neo4j 5.x の cypher-shell は "1 row" を出力しないため、healthcheck の結果で判定する
until [ "$(docker inspect -f '{{.State.Health.Status}}' neo4j-enterprise 2>/dev/null)" = "healthy" ]; do
  echo "waiting Neo4j startup..."
  sleep 3
done
echo "Neo4j is ready"
```

### 5. APOC Extended 導入（`push --if-changed` 用）

`NEO4J_PLUGINS=["apoc"]` は Core のみ自動DLするため、変更検知に使う `apoc.monitor.tx`（Extended）を手動導入する。

```bash
cd ~/Desktop/quants
./scripts/install-apoc-extended.sh        # ~/neo4j-data/enterprise/plugins/ に Extended jar を配置
docker restart neo4j-enterprise           # 反映
# 確認 (lastTxId が返れば OK)
docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d neo4j \
  "CALL apoc.monitor.tx() YIELD lastTxId RETURN lastTxId"
```

その後 Phase 2 Step 1 から進める。

---

## 注意点

| 項目 | 内容 |
|------|------|
| **バージョン一致** | 両 Mac とも Neo4j 5.26 Enterprise でないと load 失敗の可能性 |
| **DB 存在** | 自宅 Mac に DB が未登録の場合は Step 2-B で対応 |
| **データサイズ** | 現状約 197MB（5 DB の dump 合計）。NAS の SMB 帯域に依存 |
| **停止時間** | dump 時は DB ごとに数秒〜数十秒停止 (load 時は overwrite なので接続不可) |
| **双方向同期** | 2026-05-27 から双方向対応 (「最後に書いた側が source」)。同時書き込みは想定しない |
| **`.DS_Store` 等** | macOS が SMB に作るメタファイル。dump 整合性には影響なし |
| **ユーザー名差** | MacBook Air (`yukihata`) と自宅 Mac (`yuki`) でユーザー名が異なるが、`${HOME}` 展開で吸収 |

## 自動化 (Claude Code hooks 連動 + launchd)

`scripts/neo4j_sync.sh` を Claude Code の hooks と launchd で自動実行する。書き込み経路に依存しない **lastTxId 変更検知**（`push --if-changed`）を中心に、以下の **3 層**で全 write 経路をカバーする。

| 層 | トリガ | コマンド | カバー範囲 |
|----|--------|----------|-----------|
| B1 | Claude 応答終了ごと（Stop hook） | `push --if-changed` | Claude セッション内の更新（MCP / 非MCP 問わず） |
| B2 | 1 時間ごと（launchd `com.quants.neo4j-push-changed`） | `push --if-changed` | セッション外の更新（毎朝3時の `pipeline-scraped-to-neo4j`、手動 cypher-shell 等） |
| 保険 | 毎日 04:00 JST（launchd `com.quants.neo4j-push`） | `push`（無条件） | 上記が漏れても毎日 full backup |

3 層は NAS 上の `mkdir` ロックで排他されるため競合しない。逆方向は SessionStart hook の `pull --auto`（NAS の `last_source != hostname` なら load）。

### 変更検知 (lastTxId / APOC Extended)

`push --if-changed` は各 DB の `lastTxId`（最終コミット トランザクションID）を `apoc.monitor.tx`（**APOC Extended**）で取得し、`~/.neo4j-sync-txid.json` の前回 push 時 baseline と比較する。差分があれば dump → NAS push、無変化なら skip（軽量）。

- 「どの経路で書いたか」ではなく「**DB が変わったか**」を見るため、MCP・Bash・cypher-shell・launchd パイプラインなど全 write 経路の更新を検知できる。
- baseline は dump 前に確定するため、dump 中の書き込みは次回検知に倒れる（取りこぼしより再 push（無害）を優先する安全側設計）。
- lastTxId 取得失敗時（APOC Extended 未導入等）は「常に push」へ縮退する。
- APOC Extended 導入: `./scripts/install-apoc-extended.sh` → `docker restart neo4j-enterprise`。

### Hooks 構成 (`.claude/settings.json`)

| Hook | matcher | 動作 |
|------|---------|------|
| SessionStart | (なし) | `neo4j_sync.sh pull --auto` を実行。NAS の `last_source != hostname` なら 5 DB を load |
| PostToolUse | `mcp__neo4j-cypher__write_neo4j_cypher` | `touch $HOME/.neo4j-sync-dirty`（dirty フラグ機構の互換維持。検知自体は lastTxId 方式が担うため必須ではない） |
| Stop | (なし) | `neo4j_sync.sh push --if-changed` を同期実行（lastTxId が前回 push 時から変化していれば push） |

### NAS 上の `sync-state.json`

`/Volumes/personal_folder/neo4j-dumps/sync-state.json`:

```json
{
  "last_source": "YukinoMac-mini",
  "last_dump_at": "2026-06-01T23:20:52Z",
  "dbs": ["quants", "research", "note", "creator", "neo4j"]
}
```

`pull --auto` は `last_source != hostname` のときだけ load を実行する。これにより「自分が書き込んだ dump を自分に load し直す」ループを防ぐ。

### サブコマンド一覧

```bash
./scripts/neo4j_sync.sh push              # dump + NAS push + sync-state.json 更新
./scripts/neo4j_sync.sh push --if-changed # lastTxId(APOC) が前回 push 時から変化していれば push (Stop hook / 毎時 launchd 用)
./scripts/neo4j_sync.sh push --if-dirty   # dirty フラグがあれば push、なければ skip (互換用)
./scripts/neo4j_sync.sh pull              # 強制 pull (NAS → load)
./scripts/neo4j_sync.sh pull --auto       # last_source != hostname なら pull (SessionStart hook 用)
./scripts/neo4j_sync.sh status            # 現在の dirty / sync-state / lock を表示
./scripts/neo4j_sync.sh dump              # 強制 dump (sync-state は更新しない、互換用)
./scripts/neo4j_sync.sh load              # 強制 load (互換用)
./scripts/neo4j_sync.sh verify            # 件数表示
```

### 排他制御

NAS 上に `.neo4j-sync.lock` ディレクトリを `mkdir` ベースで作成。同時 push/pull を防止する。
30 秒待っても取得できなければ `die`。stale ロックは `rmdir /Volumes/personal_folder/neo4j-dumps/.neo4j-sync.lock` で手動解除。

### macOS 通知

`osascript` で通知センターに以下を表示：

- 成功時: 「Pushed/Pulled <N> DBs from <source>」（N は対象 DB 数 = 現状 5）
- エラー時: 「neo4j-sync ❌ <エラーメッセージ>」

### 全 write 経路の自動同期

lastTxId 変更検知（`push --if-changed`）により、**書き込み経路に関係なく**自動同期される。個別スクリプトに dirty フラグ更新を埋め込む必要はない（`dec-2026-06-02-004` で不要化）。

| 経路 | 自動同期されるタイミング |
|------|------------------------|
| `mcp__neo4j-cypher__write_neo4j_cypher`（Claude Code 経由） | Stop hook の `push --if-changed`（B1） |
| Claude セッション内の Bash 実行（`cypher-shell` / bolt スクリプト / `save-to-graph` 投入等） | Stop hook の `push --if-changed`（B1） |
| セッション外の launchd / cron / 手動端末（例: `pipeline-scraped-to-neo4j`, `migrate_author_ids.py`） | 毎時 launchd `push --if-changed`（B2、最大1時間）／毎朝4時 `push`（保険） |
| Neo4j Browser UI / 直接 `cypher-shell` | 同上（次の Stop hook か毎時 launchd で検知） |

> 旧方式（`mcp__neo4j-cypher__write_neo4j_cypher` のみ dirty 化 → Stop hook `push --if-dirty`）は MCP 以外の書き込みを取りこぼしていた（`disc-2026-06-02-neo4j-backup-automation` 参照）。dirty フラグ機構は互換のため残置している。

### ログ

- `~/Library/Logs/neo4j-sync.log`: スクリプト本体の全アクション
- `~/Library/Logs/quants/neo4j-push.log`: 毎朝4時 launchd（無条件 push）
- `~/Library/Logs/quants/neo4j-push-changed.log`: 毎時 launchd（push --if-changed）

## 関連

- バックアップ自動化議論: [docs/plan/2026-06-02_discussion-neo4j-backup-automation.md](plan/2026-06-02_discussion-neo4j-backup-automation.md)
- 双方向化議論: [docs/plan/2026-05-27_discussion-neo4j-bidirectional-sync.md](plan/2026-05-27_discussion-neo4j-bidirectional-sync.md)
- 初回確立議論: [docs/plan/2026-05-26_discussion-neo4j-multi-pc-sync.md](plan/2026-05-26_discussion-neo4j-multi-pc-sync.md)
- 同期スクリプト: `scripts/neo4j_sync.sh`
- APOC Extended インストーラ: `scripts/install-apoc-extended.sh`
- launchd: `scripts/com.quants.neo4j-push.plist`（毎朝4時）, `scripts/com.quants.neo4j-push-changed.plist`（毎時）
- Docker Compose 設定: `docker-compose.yml`
- 接続設定: `.env` の `NEO4J_URI` / `NEO4J_PASSWORD`
