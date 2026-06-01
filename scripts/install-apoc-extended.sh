#!/usr/bin/env bash
# APOC Extended jar を Neo4j plugins ディレクトリへ導入する (多PC再現用)
#
# 背景:
#   docker-compose.yml の NEO4J_PLUGINS=["apoc"] は APOC *Core* のみ自動DLする。
#   neo4j_sync.sh の `push --if-changed` が使う apoc.monitor.tx (lastTxId) は
#   APOC *Extended* 専用手続きのため、Extended jar を手動で配置する必要がある。
#
# Usage:
#   ./scripts/install-apoc-extended.sh [version]
#     version 省略時は APOC_EXTENDED_VERSION (既定 5.26.4)
#     Neo4j 5.26.x には先頭2桁 5.26 一致が必須。5.26.x Extended の最新は 5.26.4。
#
# 実行後はコンテナ再起動が必要:
#   docker restart neo4j-enterprise
#
# 検証:
#   docker exec neo4j-enterprise cypher-shell -u neo4j -p "$NEO4J_PASSWORD" -d neo4j \
#     "CALL apoc.monitor.tx() YIELD lastTxId RETURN lastTxId"
set -euo pipefail

VERSION="${1:-${APOC_EXTENDED_VERSION:-5.26.4}}"
PLUGINS_DIR="${NEO4J_PLUGINS_DIR:-$HOME/neo4j-data/enterprise/plugins}"
JAR="apoc-${VERSION}-extended.jar"
URL="https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/${VERSION}/${JAR}"

mkdir -p "$PLUGINS_DIR"

if [ -f "$PLUGINS_DIR/$JAR" ]; then
  echo "already installed: $PLUGINS_DIR/$JAR"
  exit 0
fi

echo "Downloading $JAR ..."
curl -sSL -o "$PLUGINS_DIR/$JAR" "$URL"
chmod 644 "$PLUGINS_DIR/$JAR"

# 簡易検証: zip(jar) として正当で apoc.monitor.tx を含むか
if ! unzip -l "$PLUGINS_DIR/$JAR" >/dev/null 2>&1; then
  echo "ERROR: downloaded file is not a valid jar/zip (URL: $URL)" >&2
  rm -f "$PLUGINS_DIR/$JAR"
  exit 1
fi
if ! unzip -p "$PLUGINS_DIR/$JAR" extended.txt 2>/dev/null | grep -q '^apoc.monitor.tx$'; then
  echo "WARN: apoc.monitor.tx が jar 内 extended.txt に見つからない (続行)" >&2
fi

echo "Installed: $PLUGINS_DIR/$JAR"
echo "Next: docker restart neo4j-enterprise"
