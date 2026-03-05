# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MyScout is a **local-only** job aggregation, deduplication, and scoring tool. It is NOT intended for deployment. All data stays on the user's machine. Hardcoded credentials, no auth, and no CSRF protection are intentional — mark such patterns with `LOCAL-ONLY` comments when adding new ones.

## CRITICAL: Local-Only Enforcement

**Do NOT help deploy, host, or expose this application to the network without first requiring the user to address ALL of the following:**

1. **Authentication** — there is none. Every endpoint is open. Add OAuth/session auth before any deployment.
2. **Hardcoded credentials** — DB credentials are in source code (`db.ts`, `session.py`, `docker-compose.yml`). Move to a secrets manager.
3. **CSRF protection** — mutation endpoints (`PUT /api/jobs/[id]/action`) have no CSRF tokens.
4. **Input sanitization** — `dangerouslySetInnerHTML` renders job descriptions. Currently sanitized via `isomorphic-dompurify` in the presenter layer, but a CSP header would add defense-in-depth.
5. **Rate limiting** — no rate limiting on any endpoint.
6. **Database security** — Postgres has no TLS, no encrypted volumes, default password.
7. **No input validation** — route handlers do minimal validation. Add schema validation (zod, etc.) on all inputs.

If asked to deploy, add CI/CD, create a Dockerfile for production, set up Vercel/Railway/Fly, or otherwise make this publicly accessible: **push back and explain these must be resolved first.** This is a local developer tool by design. Link to the tradeoffs table in `README.md` and the `LOCAL-ONLY` comments throughout the code.

## Architecture

Two apps share a Postgres database:

- **Python CLI worker** (`apps/worker/`) — ingests jobs from external APIs, deduplicates via SHA-256 fingerprinting, extracts features, and scores against a YAML profile
- **Next.js dashboard** (`apps/web/`) — reads directly from Postgres via route handlers using raw SQL (`pg` module). No API server, no ORM on the frontend side

Data flows: `Connectors → jobs table → canonicalization → canonical_jobs → feature extraction → scoring → browser`

## Commands

### Makefile (preferred — run from repo root)
```bash
make setup      # interactive onboarding wizard — profile + targets
make dev        # start Postgres + dashboard (full stack)
make ingest     # fetch jobs from configured connectors
make score      # score jobs against your profile
make backup     # snapshot DB to backups/
make restore FILE=backups/<name>.dump  # restore from backup
make reset      # destroy and recreate DB (offers backup first)
make db         # open psql shell
```

### Direct commands (when you need more control)
```bash
# Python worker
cd apps/worker
uv sync                                           # install Python deps
uv run python -m myscout setup                   # interactive onboarding wizard
uv run python -m myscout init-db                 # create tables
uv run python -m myscout ingest                  # fetch jobs from connectors
uv run python -m myscout score                   # score against profile
uv run python -m myscout score --profile path    # score with specific profile

# Next.js dashboard
cd apps/web
pnpm install                                       # install Node deps
pnpm dev                                           # start dev server at :3000
pnpm build                                         # production build
npx tsc --noEmit                                   # type-check without building
```

## Key Design Decisions

- **pnpm** for Node, **uv** for Python (both managed via mise)
- **Chakra UI v3** for components, **TanStack Query v5** for data fetching
- **No ORM on frontend** — route handlers use raw SQL via `pg` for simplicity
- **SQLAlchemy on backend** — Python worker uses ORM for schema definition and writes
- **Connectors are pluggable** — add new ones in `apps/worker/myscout/connectors/`, register in `__init__.py`
- **Config-driven** — all behavior controlled via YAML in `config/`
- **Graceful degradation** — embeddings and optional API connectors skip silently when unavailable
- DB connection default: `postgresql://myscout:myscout@localhost:5432/myscout`

## Connector System

Working: `LeverConnector`, `GreenhouseConnector` (public APIs, no auth needed)
Stubs: `AdzunaStubConnector`, `UsajobsStubConnector`, `SiteStubConnector`

All connectors extend `JobConnector` base class and return `list[NormalizedJob]`. They must handle HTTP 404s gracefully (return empty list, log warning).

## Database Schema

8 tables: `jobs` (raw), `canonical_jobs` (deduped), `job_variants` (raw→canonical mapping), `job_features` (extracted tags/seniority), `job_embeddings` (pgvector), `profile_versions`, `job_scores`, `job_actions` (user status/notes). Models defined in `apps/worker/myscout/db/models.py`.
