#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# ── Profile check ────────────────────────────────────────
if [ ! -f "$ROOT_DIR/config/profile.yml" ]; then
    echo ""
    echo "  No profile.yml found. For personalized scoring, run:"
    echo "    make setup"
    echo ""
    echo "  Continuing with example profile for now..."
    echo ""
fi

# ── Postgres ──────────────────────────────────────────────
echo "==> Starting Postgres..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d

echo "==> Waiting for Postgres to be ready..."
until docker exec myscout-postgres pg_isready -U myscout > /dev/null 2>&1; do
    sleep 1
done
echo "    Postgres is ready."

echo "==> Enabling pgvector extension..."
docker exec myscout-postgres psql -U myscout -d myscout -c \
    "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

# ── Python worker ─────────────────────────────────────────
echo "==> Installing Python dependencies..."
cd "$ROOT_DIR/apps/worker"
uv sync --quiet

echo "==> Initializing database tables..."
uv run python -m myscout init-db

# ── Next.js ───────────────────────────────────────────────
echo "==> Installing Node dependencies..."
cd "$ROOT_DIR/apps/web"
pnpm install --silent

# ── Optional: seed with real data ─────────────────────────
JOB_COUNT=$(docker exec myscout-postgres psql -U myscout -d myscout -tAc \
    "SELECT count(*) FROM canonical_jobs;" 2>/dev/null || echo "0")

if [ "$JOB_COUNT" = "0" ]; then
    echo ""
    echo "==> No jobs found. Running initial ingestion & scoring..."
    cd "$ROOT_DIR/apps/worker"
    uv run python -m myscout ingest
    uv run python -m myscout score
    echo "    Done. Jobs ingested and scored."
fi

# ── Start ─────────────────────────────────────────────────
echo ""
echo "==> Starting Next.js dev server..."
echo "    Dashboard: http://localhost:3000/jobs"
echo ""
cd "$ROOT_DIR/apps/web"
pnpm dev
