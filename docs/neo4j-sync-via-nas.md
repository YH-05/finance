# Neo4j 手動同期手順（NAS 経由）

MacBook Air（メイン PC）の Neo4j データを、自宅 Mac へ NAS 経由で手動同期するための手順。

**初回検証日**: 2026-05-27（MacBook Air → 自宅 Mac、4 DB 同期成功）

## 概要

- **方式**: `neo4j-admin database dump` / `load` による論理バックアップ
- **転送経路**: NAS（`/Volumes/personal_folder`）を中継ストレージとして利用
- **同期方向**: MacBook Air → 自宅 Mac（片方向）
- **対象 DB**: `quants`, `research`, `note`, `creator`

## 前提条件

| 項目 | 内容 |
|------|------|
| Neo4j バージョン | 両 Mac で `neo4j:5.26-enterprise` 必須（マイナーバージョン差があると load 失敗の可能性） |
| コンテナ名 | 両 Mac で `neo4j-enterprise`（`docker-compose.yml` で固定） |
| 認証 | ユーザー `neo4j` / パスワード `gomasuke`（`NEO4J_PASSWORD` 環境変数で上書き可） |
| NAS マウント | 両 Mac で `/Volumes/personal_folder` にマウント済み |
| bind mount | 両 Mac とも `${HOME}/neo4j-data/enterprise/` を使用（`docker-compose.yml` で `${HOME}` 展開） |
| DB 存在 | 自宅 Mac 側に対象 DB が未作成でも OK（Phase 2 Step B で新規作成可能） |

## 実測値（2026-05-27 時点）

| DB | dump サイズ | ノード数 | リレーション数 |
|----|------------|---------|---------------|
| `quants` | 1.7M | 3,789 | 8,345 |
| `research` | 59M | 28,100 | 516,807 |
| `note` | 478K | 838 | 983 |
| `creator` | 131M | 15,312 | 31,362 |
| **合計** | **約 191M** | **48,039** | **557,497** |

各 DB の dump 処理時間: 約 1.2〜3 秒（ローカル NVMe）。
全工程（dump → NAS 転送 → load → 件数検証）の所要時間: 約 30 分以内。

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
for DB in quants research note creator; do
  echo "=== Dumping $DB ==="
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system "STOP DATABASE $DB WAIT"
  docker exec neo4j-enterprise neo4j-admin database dump $DB \
    --to-path=/tmp/dumps --overwrite-destination=true
  docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system "START DATABASE $DB WAIT"
done

# 5. コンテナから NAS へコピー
for DB in quants research note creator; do
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
# NAS マウント確認 (4 ファイルが見えること)
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

# 4 ファイルをコンテナへコピー
for DB in quants research note creator; do
  echo "=== Copying $DB.dump ==="
  docker cp /Volumes/personal_folder/neo4j-dumps/$DB.dump neo4j-enterprise:/tmp/dumps/
done

# 確認 (MacBook Air と同じサイズか)
docker exec neo4j-enterprise ls -lh /tmp/dumps/
```

> ⚠️ **`docker cp` の宛先パスは必ず先頭 `/` 付き**で指定すること。`neo4j-enterprise:tmp/dumps/`（先頭 `/` なし）でも環境によっては `/tmp/dumps/` に展開される場合があるが、挙動が不安定なため絶対パス推奨。

### Step 2-A: DB が既に存在する場合（上書き load）

```bash
for DB in quants research note creator; do
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
for DB in quants research note creator; do
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

# 4 DB すべて online か確認
docker exec neo4j-enterprise cypher-shell -u neo4j -p gomasuke -d system \
  "SHOW DATABASES YIELD name, currentStatus WHERE name IN ['quants','research','note','creator'] RETURN name, currentStatus"
```

### Step 3: 件数検証

```bash
for DB in quants research note creator; do
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

その後 Phase 2 Step 1 から進める。

---

## 注意点

| 項目 | 内容 |
|------|------|
| **バージョン一致** | 両 Mac とも Neo4j 5.26 Enterprise でないと load 失敗の可能性 |
| **DB 存在** | 自宅 Mac に DB が未登録の場合は Step 2-B で対応 |
| **データサイズ** | 現状約 191MB（dump 圧縮後）。NAS の SMB 帯域に依存 |
| **停止時間** | dump 時は DB ごとに数秒〜数十秒停止 (load 時は overwrite なので接続不可) |
| **双方向同期** | 2026-05-27 から双方向対応 (「最後に書いた側が source」)。同時書き込みは想定しない |
| **`.DS_Store` 等** | macOS が SMB に作るメタファイル。dump 整合性には影響なし |
| **ユーザー名差** | MacBook Air (`yukihata`) と自宅 Mac (`yuki`) でユーザー名が異なるが、`${HOME}` 展開で吸収 |

## 自動化 (Claude Code hooks 連動)

2026-05-27 から、`scripts/neo4j_sync.sh` を Claude Code の hooks で自動実行する双方向同期に拡張。

### Hooks 構成 (`.claude/settings.json`)

| Hook | matcher | 動作 |
|------|---------|------|
| SessionStart | (なし) | `neo4j_sync.sh pull --auto` を実行。NAS の `last_source != hostname` なら 4 DB を load |
| PostToolUse | `mcp__neo4j-cypher__write_neo4j_cypher` | `touch $HOME/.neo4j-sync-dirty` (フラグだけ立てる軽量処理) |
| Stop | (なし) | `neo4j_sync.sh push --if-dirty` を同期実行 (dirty フラグがあれば push) |

### NAS 上の `sync-state.json`

`/Volumes/personal_folder/neo4j-dumps/sync-state.json`:

```json
{
  "last_source": "yukihatas-macbook-air",
  "last_dump_at": "2026-05-27T12:34:56Z",
  "dbs": ["quants", "research", "note", "creator"]
}
```

`pull --auto` は `last_source != hostname` のときだけ load を実行する。これにより「自分が書き込んだ dump を自分に load し直す」ループを防ぐ。

### サブコマンド一覧

```bash
./scripts/neo4j_sync.sh push              # dump + NAS push + sync-state.json 更新
./scripts/neo4j_sync.sh push --if-dirty   # dirty フラグがあれば push、なければ skip (Stop hook 用)
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

- 成功時: 「Pushed/Pulled 4 DBs from <source>」
- エラー時: 「neo4j-sync ❌ <エラーメッセージ>」

### Claude Code 経由以外の書き込み

| 経路 | 対応 |
|------|------|
| `mcp__neo4j-cypher__write_neo4j_cypher` (Claude Code 経由) | PostToolUse hook で自動 dirty 化 |
| `scripts/migrate_author_ids.py --execute` | スクリプト内で書き込み成功時に dirty フラグを touch (`migrated > 0`) |
| Neo4j Browser UI / 直接 `cypher-shell` | 手動 `./scripts/neo4j_sync.sh push` を実行 |
| その他カスタムスクリプト | `Path.home() / ".neo4j-sync-dirty"` を touch する処理を追加 |

### ログ

`~/Library/Logs/neo4j-sync.log` に全アクションを追記。

## 関連

- 双方向化議論: [docs/plan/2026-05-27_discussion-neo4j-bidirectional-sync.md](plan/2026-05-27_discussion-neo4j-bidirectional-sync.md)
- 初回確立議論: [docs/plan/2026-05-26_discussion-neo4j-multi-pc-sync.md](plan/2026-05-26_discussion-neo4j-multi-pc-sync.md)
- Docker Compose 設定: `docker-compose.yml`
- 接続設定: `.env` の `NEO4J_URI` / `NEO4J_PASSWORD`
