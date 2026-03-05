#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "This will destroy all job data and recreate the database."

# Offer backup if the container is running
if docker exec myscout-postgres pg_isready -U myscout > /dev/null 2>&1; then
    read -p "Back up first? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        "$SCRIPT_DIR/backup.sh"
    fi
fi

read -p "Continue with reset? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo "==> Stopping containers and removing volume..."
docker compose -f "$ROOT_DIR/docker-compose.yml" down -v

echo "==> Starting fresh Postgres..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d

echo "==> Waiting for Postgres..."
until docker exec myscout-postgres pg_isready -U myscout > /dev/null 2>&1; do
    sleep 1
done

echo "==> Enabling pgvector extension..."
docker exec myscout-postgres psql -U myscout -d myscout -c \
    "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

echo "==> Recreating tables..."
cd "$ROOT_DIR/apps/worker"
uv run python -m myscout init-db

echo "Done. Database is empty and ready."
