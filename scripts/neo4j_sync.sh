#!/usr/bin/env bash
# Neo4j 複数 PC 同期スクリプト (dump/load + NAS 中継)
#
# Usage:
#   ./scripts/neo4j_sync.sh dump            # Phase 1: dump 4 DBs to NAS
#   ./scripts/neo4j_sync.sh load            # Phase 2: load 4 DBs from NAS
#   ./scripts/neo4j_sync.sh verify          # ノード/リレーション件数を表示
#
# Environment variables:
#   NEO4J_CONTAINER  (default: neo4j-enterprise)
#   NEO4J_USER       (default: neo4j)
#   NEO4J_PASSWORD   (default: gomasuke)
#   NEO4J_DBS        (default: "quants research note creator") space-separated
#   NAS_DUMP_DIR     (default: /Volumes/personal_folder/neo4j-dumps)
#
# Reference: docs/neo4j-sync-via-nas.md

set -euo pipefail

CONTAINER="${NEO4J_CONTAINER:-neo4j-enterprise}"
USER_NAME="${NEO4J_USER:-neo4j}"
PASSWORD="${NEO4J_PASSWORD:-gomasuke}"
DBS="${NEO4J_DBS:-quants research note creator}"
NAS_DIR="${NAS_DUMP_DIR:-/Volumes/personal_folder/neo4j-dumps}"
CONTAINER_DUMP_DIR="/tmp/dumps"

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

die() {
  echo "ERROR: $*" >&2
  exit 1
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
  log "Checking prerequisites..."
  docker ps --filter "name=^${CONTAINER}$" --format '{{.Names}}' | grep -q "^${CONTAINER}$" \
    || die "Container '$CONTAINER' is not running. Start it with: docker compose up -d neo4j"

  [ -d "$NAS_DIR" ] || mkdir -p "$NAS_DIR" \
    || die "Failed to create NAS dump dir: $NAS_DIR (is NAS mounted?)"

  log "Container: $CONTAINER (running)"
  log "NAS dir:   $NAS_DIR"
  log "DBs:       $DBS"
}

# ----------------------------------------------------------------------------
# Phase 1: dump → NAS
# ----------------------------------------------------------------------------
cmd_dump() {
  check_prereqs

  log "Creating container dump dir..."
  docker exec "$CONTAINER" mkdir -p "$CONTAINER_DUMP_DIR"

  for db in $DBS; do
    log "=== [$db] Dumping ==="
    cypher_system "STOP DATABASE $db WAIT" | tail -2
    docker exec "$CONTAINER" neo4j-admin database dump "$db" \
      --to-path="$CONTAINER_DUMP_DIR" --overwrite-destination=true 2>&1 | tail -3
    cypher_system "START DATABASE $db WAIT" | tail -2
  done

  log "Copying dumps to NAS: $NAS_DIR"
  for db in $DBS; do
    docker cp "${CONTAINER}:${CONTAINER_DUMP_DIR}/${db}.dump" "${NAS_DIR}/"
  done

  log "Cleaning up container dump dir..."
  docker exec "$CONTAINER" rm -rf "$CONTAINER_DUMP_DIR"

  log "Done. Files on NAS:"
  ls -lh "$NAS_DIR"
}

# ----------------------------------------------------------------------------
# Phase 2: NAS → load
# ----------------------------------------------------------------------------
cmd_load() {
  check_prereqs

  log "Verifying NAS dump files..."
  for db in $DBS; do
    [ -f "${NAS_DIR}/${db}.dump" ] || die "Missing dump file: ${NAS_DIR}/${db}.dump"
  done

  log "Copying dumps into container..."
  docker exec "$CONTAINER" mkdir -p "$CONTAINER_DUMP_DIR"
  for db in $DBS; do
    docker cp "${NAS_DIR}/${db}.dump" "${CONTAINER}:${CONTAINER_DUMP_DIR}/"
  done

  for db in $DBS; do
    log "=== [$db] Loading ==="

    # Check if DB exists
    local exists
    exists=$(cypher_system "SHOW DATABASE $db YIELD name RETURN count(name) AS c" \
      | tail -1 | tr -d ' ' || echo "0")

    if [ "$exists" = "1" ]; then
      log "  DB exists -> overwrite load"
      cypher_system "STOP DATABASE $db WAIT" | tail -2
      docker exec "$CONTAINER" neo4j-admin database load "$db" \
        --from-path="$CONTAINER_DUMP_DIR" --overwrite-destination=true 2>&1 | tail -3
      cypher_system "START DATABASE $db WAIT" | tail -2
    else
      log "  DB does not exist -> load + CREATE DATABASE"
      docker exec "$CONTAINER" neo4j-admin database load "$db" \
        --from-path="$CONTAINER_DUMP_DIR" --overwrite-destination=true 2>&1 | tail -3
      cypher_system "CREATE DATABASE $db IF NOT EXISTS WAIT" | tail -2
    fi
  done

  log "Cleaning up container dump dir..."
  docker exec "$CONTAINER" rm -rf "$CONTAINER_DUMP_DIR"

  log "Done. Database status:"
  local dbs_list
  dbs_list=$(echo "$DBS" | tr ' ' ',' | sed "s/,/','/g")
  cypher_system "SHOW DATABASES YIELD name, currentStatus WHERE name IN ['${dbs_list}'] RETURN name, currentStatus"
}

# ----------------------------------------------------------------------------
# verify: 件数表示
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
# main
# ----------------------------------------------------------------------------
case "${1:-}" in
  dump)   cmd_dump ;;
  load)   cmd_load ;;
  verify) cmd_verify ;;
  *)
    cat <<EOF
Usage: $0 {dump|load|verify}

  dump    Phase 1: Dump 4 DBs from this Mac's Neo4j to NAS
  load    Phase 2: Load 4 DBs from NAS into this Mac's Neo4j
  verify  Display node/relationship counts for each DB

Environment variables:
  NEO4J_CONTAINER  Container name (default: neo4j-enterprise)
  NEO4J_USER       Neo4j user     (default: neo4j)
  NEO4J_PASSWORD   Neo4j password (default: gomasuke)
  NEO4J_DBS        Space-separated DB list
                   (default: "quants research note creator")
  NAS_DUMP_DIR     NAS dump directory
                   (default: /Volumes/personal_folder/neo4j-dumps)

Reference: docs/neo4j-sync-via-nas.md
EOF
    exit 1
    ;;
esac
