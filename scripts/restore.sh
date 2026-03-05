#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$ROOT_DIR/backups"

# If a file was passed, use it. Otherwise show available backups.
if [ "${1:-}" != "" ]; then
    BACKUP_FILE="$1"
else
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR"/*.dump 2>/dev/null)" ]; then
        echo "No backups found in $BACKUP_DIR"
        exit 1
    fi

    echo "Available backups:"
    echo ""
    ls -1t "$BACKUP_DIR"/*.dump | while read -r f; do
        SIZE=$(du -h "$f" | cut -f1)
        echo "  $(basename "$f")  ($SIZE)"
    done
    echo ""
    echo "Usage: make restore FILE=backups/<filename>.dump"
    exit 0
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "File not found: $BACKUP_FILE"
    exit 1
fi

echo "This will replace ALL current data with the backup."
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo "==> Dropping and recreating database..."
docker exec myscout-postgres psql -U myscout -d postgres -c "DROP DATABASE IF EXISTS myscout;"
docker exec myscout-postgres psql -U myscout -d postgres -c "CREATE DATABASE myscout OWNER myscout;"
docker exec myscout-postgres psql -U myscout -d myscout -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

echo "==> Restoring from $(basename "$BACKUP_FILE")..."
docker exec -i myscout-postgres pg_restore -U myscout -d myscout --no-owner < "$BACKUP_FILE"

echo "    Restore complete."
