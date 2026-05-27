#!/usr/bin/env bash
# Neo4j 複数 PC 同期スクリプト (dump/load + NAS 中継 + Claude Code hooks 連動)
#
# Usage:
#   ./scripts/neo4j_sync.sh dump            # 強制 dump → NAS
#   ./scripts/neo4j_sync.sh load            # 強制 NAS → load
#   ./scripts/neo4j_sync.sh verify          # ノード/リレーション件数を表示
#   ./scripts/neo4j_sync.sh push            # dump → NAS + sync-state.json 更新
#   ./scripts/neo4j_sync.sh push --if-dirty # dirty フラグがあれば push
#   ./scripts/neo4j_sync.sh pull            # 強制 pull (NAS → load)
#   ./scripts/neo4j_sync.sh pull --auto     # NAS の last_source != hostname なら pull
#   ./scripts/neo4j_sync.sh status          # 現在の dirty/sync 状態を表示
#
# Environment variables:
#   NEO4J_CONTAINER  (default: neo4j-enterprise)
#   NEO4J_USER       (default: neo4j)
#   NEO4J_PASSWORD   (default: gomasuke)
#   NEO4J_DBS        (default: "quants research note creator") space-separated
#   NAS_DUMP_DIR     (default: /Volumes/personal_folder/neo4j-dumps)
#   NEO4J_SYNC_DIRTY (default: $HOME/.neo4j-sync-dirty)
#   NEO4J_SYNC_LOG   (default: $HOME/Library/Logs/neo4j-sync.log)
#
# Reference: docs/neo4j-sync-via-nas.md

set -euo pipefail

CONTAINER="${NEO4J_CONTAINER:-neo4j-enterprise}"
USER_NAME="${NEO4J_USER:-neo4j}"
PASSWORD="${NEO4J_PASSWORD:-gomasuke}"
DBS="${NEO4J_DBS:-quants research note creator}"
NAS_DIR="${NAS_DUMP_DIR:-/Volumes/personal_folder/neo4j-dumps}"
CONTAINER_DUMP_DIR="/tmp/dumps"
DIRTY_FLAG="${NEO4J_SYNC_DIRTY:-$HOME/.neo4j-sync-dirty}"
LOG_FILE="${NEO4J_SYNC_LOG:-$HOME/Library/Logs/neo4j-sync.log}"
SYNC_STATE_FILE="$NAS_DIR/sync-state.json"
LOCK_DIR="$NAS_DIR/.neo4j-sync.lock"
LOCK_TIMEOUT="${NEO4J_SYNC_LOCK_TIMEOUT:-30}"
HOSTNAME_SHORT="$(hostname -s)"

mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
log() {
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  echo "$msg"
  echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

die() {
  log "ERROR: $*"
  notify_error "$*"
  exit 1
}

notify() {
  local title="$1"
  local message="$2"
  local subtitle="${3:-}"
  osascript -e "display notification \"$message\" with title \"$title\" subtitle \"$subtitle\"" 2>/dev/null || true
}

notify_error() {
  notify "neo4j-sync ❌" "$1" "$HOSTNAME_SHORT"
}

cypher_system() {
  docker exec "$CONTAINER" cypher-shell -u "$USER_NAME" -p "$PASSWORD" -d system "$1"
}

cypher_db() {
  local db="$1"
  local query="$2"
  docker exec "$CONTAINER" cypher-shell -u "$USER_NAME" -p "$PASSWORD" -d "$db" "$query"
}

check_prereqs() {
  docker ps --filter "name=^${CONTAINER}$" --format '{{.Names}}' | grep -q "^${CONTAINER}$" \
    || die "Container '$CONTAINER' is not running"

  [ -d "$NAS_DIR" ] || mkdir -p "$NAS_DIR" 2>/dev/null \
    || die "NAS dump dir unreachable: $NAS_DIR (is NAS mounted?)"
}

# ----------------------------------------------------------------------------
# Locking (mkdir-based on NAS)
# ----------------------------------------------------------------------------
acquire_lock() {
  local elapsed=0
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    if [ $elapsed -ge $LOCK_TIMEOUT ]; then
      die "Could not acquire lock (waited ${LOCK_TIMEOUT}s). Stale lock? Remove with: rmdir '$LOCK_DIR'"
    fi
    log "Waiting for sync lock... (${elapsed}s/${LOCK_TIMEOUT}s)"
    sleep 2
    elapsed=$((elapsed + 2))
  done
  trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT
}

# ----------------------------------------------------------------------------
# sync-state.json operations (jq-based)
# ----------------------------------------------------------------------------
read_sync_state() {
  if [ -f "$SYNC_STATE_FILE" ]; then
    cat "$SYNC_STATE_FILE"
  else
    echo '{}'
  fi
}

get_last_source() {
  read_sync_state | jq -r '.last_source // ""'
}

get_last_dump_at() {
  read_sync_state | jq -r '.last_dump_at // ""'
}

write_sync_state() {
  local now
  now="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  local dbs_json
  dbs_json=$(echo "$DBS" | tr ' ' '\n' | jq -R . | jq -s .)
  jq -n \
    --arg src "$HOSTNAME_SHORT" \
    --arg ts "$now" \
    --argjson dbs "$dbs_json" \
    '{last_source: $src, last_dump_at: $ts, dbs: $dbs}' > "$SYNC_STATE_FILE"
}

# ----------------------------------------------------------------------------
# dump → NAS (used by `dump` and `push`)
# ----------------------------------------------------------------------------
do_dump_to_nas() {
  log "Creating container dump dir..."
  docker exec "$CONTAINER" mkdir -p "$CONTAINER_DUMP_DIR"

  for db in $DBS; do
    log "=== [$db] Dumping ==="
    cypher_system "STOP DATABASE $db WAIT" 2>&1 | tail -2 | tee -a "$LOG_FILE"
    docker exec "$CONTAINER" neo4j-admin database dump "$db" \
      --to-path="$CONTAINER_DUMP_DIR" --overwrite-destination=true 2>&1 | tail -3 | tee -a "$LOG_FILE"
    cypher_system "START DATABASE $db WAIT" 2>&1 | tail -2 | tee -a "$LOG_FILE"
  done

  log "Copying dumps to NAS: $NAS_DIR"
  for db in $DBS; do
    docker cp "${CONTAINER}:${CONTAINER_DUMP_DIR}/${db}.dump" "${NAS_DIR}/" 2>&1 | tee -a "$LOG_FILE"
  done

  log "Cleaning up container dump dir..."
  docker exec "$CONTAINER" rm -rf "$CONTAINER_DUMP_DIR"
}

# ----------------------------------------------------------------------------
# NAS → load (used by `load` and `pull`)
# ----------------------------------------------------------------------------
do_load_from_nas() {
  log "Verifying NAS dump files..."
  for db in $DBS; do
    [ -f "${NAS_DIR}/${db}.dump" ] || die "Missing dump file: ${NAS_DIR}/${db}.dump"
  done

  log "Copying dumps into container..."
  docker exec "$CONTAINER" mkdir -p "$CONTAINER_DUMP_DIR"
  for db in $DBS; do
    docker cp "${NAS_DIR}/${db}.dump" "${CONTAINER}:${CONTAINER_DUMP_DIR}/" 2>&1 | tee -a "$LOG_FILE"
  done

  for db in $DBS; do
    log "=== [$db] Loading ==="

    local exists
    exists=$(cypher_system "SHOW DATABASE $db YIELD name RETURN count(name) AS c" 2>/dev/null \
      | tail -1 | tr -d ' ' || echo "0")

    if [ "$exists" = "1" ]; then
      log "  DB exists -> overwrite load"
      cypher_system "STOP DATABASE $db WAIT" 2>&1 | tail -2 | tee -a "$LOG_FILE"
      docker exec "$CONTAINER" neo4j-admin database load "$db" \
        --from-path="$CONTAINER_DUMP_DIR" --overwrite-destination=true 2>&1 | tail -3 | tee -a "$LOG_FILE"
      cypher_system "START DATABASE $db WAIT" 2>&1 | tail -2 | tee -a "$LOG_FILE"
    else
      log "  DB does not exist -> load + CREATE DATABASE"
      docker exec "$CONTAINER" neo4j-admin database load "$db" \
        --from-path="$CONTAINER_DUMP_DIR" --overwrite-destination=true 2>&1 | tail -3 | tee -a "$LOG_FILE"
      cypher_system "CREATE DATABASE $db IF NOT EXISTS WAIT" 2>&1 | tail -2 | tee -a "$LOG_FILE"
    fi
  done

  log "Cleaning up container dump dir..."
  docker exec "$CONTAINER" rm -rf "$CONTAINER_DUMP_DIR"
}

# ----------------------------------------------------------------------------
# cmd_dump / cmd_load: 既存互換 (sync-state.json 更新なし)
# ----------------------------------------------------------------------------
cmd_dump() {
  check_prereqs
  log "dump (legacy, no state update): host=$HOSTNAME_SHORT"
  do_dump_to_nas
  log "Done. Files on NAS:"
  ls -lh "$NAS_DIR" | tee -a "$LOG_FILE"
}

cmd_load() {
  check_prereqs
  log "load (legacy, no state check): host=$HOSTNAME_SHORT"
  do_load_from_nas
  log "Done."
}

# ----------------------------------------------------------------------------
# verify
# ----------------------------------------------------------------------------
cmd_verify() {
  check_prereqs
  for db in $DBS; do
    echo ""
    echo "=== $db ==="
    cypher_db "$db" "MATCH (n) RETURN count(n) AS nodes"
    cypher_db "$db" "MATCH ()-[r]->() RETURN count(r) AS relationships"
  done
}

# ----------------------------------------------------------------------------
# push: dump + NAS push + sync-state.json 更新
# ----------------------------------------------------------------------------
cmd_push() {
  local if_dirty="${1:-}"

  if [ "$if_dirty" = "--if-dirty" ]; then
    if [ ! -f "$DIRTY_FLAG" ]; then
      log "push --if-dirty: no dirty flag at $DIRTY_FLAG, skipping"
      exit 0
    fi
    log "push --if-dirty: dirty flag found, proceeding"
  fi

  check_prereqs
  acquire_lock

  log "push: host=$HOSTNAME_SHORT"
  do_dump_to_nas
  write_sync_state
  rm -f "$DIRTY_FLAG"

  log "Done. last_source updated to: $HOSTNAME_SHORT"
  notify "neo4j-sync ⬆️" "Pushed 4 DBs to NAS" "$HOSTNAME_SHORT"
}

# ----------------------------------------------------------------------------
# pull: NAS の last_source を確認して load (auto なら条件付き)
# ----------------------------------------------------------------------------
cmd_pull() {
  local auto="${1:-}"

  check_prereqs

  if [ ! -f "$SYNC_STATE_FILE" ]; then
    if [ "$auto" = "--auto" ]; then
      log "pull --auto: no sync-state.json yet, skipping"
      exit 0
    fi
    log "pull: no sync-state.json (initial state), proceeding anyway"
  fi

  local last_source
  last_source="$(get_last_source)"

  if [ "$auto" = "--auto" ]; then
    if [ -z "$last_source" ] || [ "$last_source" = "$HOSTNAME_SHORT" ]; then
      log "pull --auto: last_source='$last_source' (self or empty), skipping"
      exit 0
    fi
    log "pull --auto: last_source='$last_source' != self='$HOSTNAME_SHORT', will load"
  fi

  acquire_lock

  log "pull: host=$HOSTNAME_SHORT, source=$last_source"
  do_load_from_nas

  log "Done. Loaded from source: $last_source"
  notify "neo4j-sync ⬇️" "Pulled 4 DBs from $last_source" "$HOSTNAME_SHORT"
}

# ----------------------------------------------------------------------------
# status: 現在の状態を表示
# ----------------------------------------------------------------------------
cmd_status() {
  echo "=== neo4j-sync status ==="
  echo "Host:        $HOSTNAME_SHORT"
  echo "Container:   $CONTAINER"
  echo "DBs:         $DBS"
  echo "NAS dir:     $NAS_DIR"
  echo "Dirty flag:  $DIRTY_FLAG"

  if [ -f "$DIRTY_FLAG" ]; then
    echo "  → dirty (modified since last push): YES"
    echo "  → modified at: $(stat -f '%Sm' "$DIRTY_FLAG" 2>/dev/null || echo unknown)"
  else
    echo "  → dirty: no"
  fi

  echo ""
  echo "=== NAS sync-state.json ==="
  if [ -f "$SYNC_STATE_FILE" ]; then
    cat "$SYNC_STATE_FILE" | jq .
  else
    echo "  (no sync-state.json yet)"
  fi

  echo ""
  echo "=== Lock ==="
  if [ -d "$LOCK_DIR" ]; then
    echo "  LOCKED (created: $(stat -f '%Sm' "$LOCK_DIR" 2>/dev/null || echo unknown))"
  else
    echo "  unlocked"
  fi
}

# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
case "${1:-}" in
  dump)   cmd_dump ;;
  load)   cmd_load ;;
  verify) cmd_verify ;;
  push)   shift; cmd_push "${1:-}" ;;
  pull)   shift; cmd_pull "${1:-}" ;;
  status) cmd_status ;;
  *)
    cat <<EOF
Usage: $0 <command> [options]

Commands:
  dump              強制 dump → NAS (sync-state.json は更新しない、互換用)
  load              強制 NAS → load (互換用)
  verify            ノード/リレーション件数を表示
  push              dump + NAS push + sync-state.json 更新
  push --if-dirty   ~/.neo4j-sync-dirty があれば push、なければ skip
  pull              強制 pull (NAS → load) + sync-state.json 確認
  pull --auto       last_source != hostname なら pull、それ以外は skip
  status            現在の dirty / sync-state / lock を表示

Environment variables:
  NEO4J_CONTAINER  Container name (default: neo4j-enterprise)
  NEO4J_USER       Neo4j user     (default: neo4j)
  NEO4J_PASSWORD   Neo4j password (default: gomasuke)
  NEO4J_DBS        Space-separated DB list
                   (default: "quants research note creator")
  NAS_DUMP_DIR     NAS dump directory
                   (default: /Volumes/personal_folder/neo4j-dumps)
  NEO4J_SYNC_DIRTY Dirty flag file (default: \$HOME/.neo4j-sync-dirty)
  NEO4J_SYNC_LOG   Log file (default: \$HOME/Library/Logs/neo4j-sync.log)

Reference: docs/neo4j-sync-via-nas.md
EOF
    exit 1
    ;;
esac
