#!/usr/bin/env bash
set -euo pipefail

echo "[healthcheck] $(date)"
echo

# 1) Docker available?
command -v docker >/dev/null || { echo "FAIL: docker not found"; exit 2; }

# 2) Compose services up?
if docker compose ps >/dev/null 2>&1; then
  echo "Docker Compose services:"
  docker compose ps
else
  echo "WARN: docker compose not available or not in this directory"
fi
echo

# 3) Postgres reachable? (adjust service name/user/db if needed)
PG_SERVICE="${PG_SERVICE:-postgres}"
PG_USER="${PG_USER:-postgres}"
PG_DB="${PG_DB:-postgres}"

if docker compose ps --services | grep -qx "$PG_SERVICE"; then
  echo "Checking Postgres connectivity ($PG_SERVICE)..."
  docker compose exec -T "$PG_SERVICE" pg_isready -U "$PG_USER" -d "$PG_DB" \
    && echo "PASS: Postgres is ready" \
    || { echo "FAIL: Postgres not ready"; exit 3; }
else
  echo "WARN: service '$PG_SERVICE' not found in docker compose"
fi

echo
echo "PASS: healthcheck complete"
