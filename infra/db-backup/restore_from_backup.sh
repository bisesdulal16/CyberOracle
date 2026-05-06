#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/backup.env"

if [ -f "$ENV_FILE" ]; then
  source "$ENV_FILE"
fi

DB_CONTAINER="${DB_CONTAINER:-cyberoracle-db-1}"
DB_USER="${DB_USER:-postgres}"
RESTORE_DB="${RESTORE_DB:-cyberoracle_restore_test}"
LOCAL_BACKUP_DIR="${LOCAL_BACKUP_DIR:-/tmp/cyberoracle-backups}"
MINIO_ALIAS="${MINIO_ALIAS:-localminio}"
S3_BUCKET="${S3_BUCKET:-cyberoracle-backups}"
S3_ENDPOINT="${S3_ENDPOINT:-http://localhost:9000}"
S3_ACCESS_KEY="${S3_ACCESS_KEY:-minioadmin}"
S3_SECRET_KEY="${S3_SECRET_KEY:-minioadmin}"

BACKUP_FILE="${1:-latest}"

mkdir -p "$LOCAL_BACKUP_DIR"

echo "[INFO] Restore target database: $RESTORE_DB"

if [ "$BACKUP_FILE" = "latest" ]; then
  echo "[INFO] Fetching latest backup from MinIO bucket: $S3_BUCKET"

  mc alias set "$MINIO_ALIAS" "$S3_ENDPOINT" "$S3_ACCESS_KEY" "$S3_SECRET_KEY" >/dev/null

  LATEST_FILE="$(mc ls "$MINIO_ALIAS/$S3_BUCKET" | awk '{print $NF}' | grep '\.sql\.gz$' | sort | tail -n 1)"

  if [ -z "$LATEST_FILE" ]; then
    echo "[ERROR] No .sql.gz backup found in MinIO bucket."
    exit 1
  fi

  mc cp "$MINIO_ALIAS/$S3_BUCKET/$LATEST_FILE" "$LOCAL_BACKUP_DIR/$LATEST_FILE"
  BACKUP_PATH="$LOCAL_BACKUP_DIR/$LATEST_FILE"
else
  BACKUP_PATH="$BACKUP_FILE"
fi

if [ ! -f "$BACKUP_PATH" ]; then
  echo "[ERROR] Backup file not found: $BACKUP_PATH"
  exit 1
fi

echo "[INFO] Using backup: $BACKUP_PATH"

echo "[INFO] Dropping old restore test database if it exists..."
docker exec "$DB_CONTAINER" dropdb -U "$DB_USER" --if-exists "$RESTORE_DB"

echo "[INFO] Creating restore test database..."
docker exec "$DB_CONTAINER" createdb -U "$DB_USER" "$RESTORE_DB"

echo "[INFO] Restoring backup into $RESTORE_DB..."
gunzip -c "$BACKUP_PATH" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$RESTORE_DB" >/dev/null

echo "[INFO] Listing restored tables..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$RESTORE_DB" -c "\dt"

echo "[INFO] Restore validation complete."
