#!/usr/bin/env bash
set -euo pipefail

# Load env if present (backup.env in same folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/backup.env" ]]; then
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/backup.env"
fi

# Ensure required vars from backup.env
: "${PGUSER:?Need PGUSER}"
: "${PGDATABASE:?Need PGDATABASE}"
: "${PGPASSWORD:?Need PGPASSWORD}"
: "${S3_ENDPOINT:?Need S3_ENDPOINT}"
: "${S3_BUCKET:?Need S3_BUCKET}"
: "${S3_ACCESS_KEY:?Need S3_ACCESS_KEY}"
: "${S3_SECRET_KEY:?Need S3_SECRET_KEY}"
: "${BACKUP_DIR:?Need BACKUP_DIR}"
: "${RETENTION_DAYS:?Need RETENTION_DAYS}"

export PGPASSWORD

# Prepare local backup directory (once)
sudo mkdir -p "$BACKUP_DIR"
sudo chown "$USER":"$USER" "$BACKUP_DIR"

TIMESTAMP="$(date +'%Y-%m-%dT%H-%M-%S')"
BACKUP_FILE="${BACKUP_DIR}/${PGDATABASE}-${TIMESTAMP}.sql.gz"

echo "[INFO] Starting pg_dump for database '${PGDATABASE}' using docker exec..."

# Run pg_dump *inside* the Postgres container to avoid version mismatch issues
docker exec -t cyberoracle-db pg_dump -U "$PGUSER" "$PGDATABASE" \
  | gzip > "$BACKUP_FILE"

echo "[INFO] Backup created: $BACKUP_FILE"

# Configure MinIO alias (idempotent)
mc alias set localminio "$S3_ENDPOINT" "$S3_ACCESS_KEY" "$S3_SECRET_KEY"

# Ensure bucket exists
mc mb --ignore-existing "localminio/${S3_BUCKET}"

# Upload to MinIO
REMOTE_PATH="localminio/${S3_BUCKET}/$(basename "$BACKUP_FILE")"
echo "[INFO] Uploading to MinIO: $REMOTE_PATH"
mc cp "$BACKUP_FILE" "$REMOTE_PATH"

echo "[INFO] Upload complete."

# Local retention cleanup
echo "[INFO] Deleting local backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -type f -name "${PGDATABASE}-*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete || true

echo "[INFO] Backup job finished successfully."