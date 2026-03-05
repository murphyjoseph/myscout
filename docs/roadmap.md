# MyScout Roadmap

> Last updated: 2026-03-05

## In Progress

_Nothing currently in progress._

## Planned

### Embedding-Based Semantic Scoring
The highest-impact scoring improvement. Infrastructure is ready (pgvector, `job_embeddings` table, scoring weight configured at 55 points).

- [ ] Ollama integration — generate embeddings locally via `nomic-embed-text`
- [ ] OpenAI fallback — for users without Ollama
- [ ] Embed on ingest — generate embedding per canonical job during ingestion
- [ ] Embed training examples — generate embeddings from `saved_jobs/` markdown files
- [ ] Semantic similarity scoring — cosine similarity between job and training embeddings
- [ ] Graceful degradation — skip silently when no embedding provider available

### USAJOBS Connector
Federal job listings via USAJOBS.gov API.

- [ ] Implement `UsajobsStubConnector` with real API calls
- [ ] Map USAJOBS fields to `NormalizedJob`
- [ ] Add `USAJOBS_API_KEY` / `USAJOBS_EMAIL` to setup wizard

### Alembic Migrations
Wire up Alembic for Django-style `make migrate`. Infrastructure is half-done (dependency installed, `env.py` exists, `versions/` directory ready, `alembic.ini` is empty).

- [ ] Fill in `alembic.ini` with DB URL and migrations path
- [ ] Generate initial migration from current SQLAlchemy models
- [ ] Add `make migration MSG="..."` and `make migrate` to Makefile
- [ ] First real migration: add `employment_type` column to `canonical_jobs` table
- [ ] Wire `employment_type.include` constraint into scoring engine

### Company Research & Intelligence
Auto-enrich target companies with market research when added via `add-target`. Display on a company profile page in the dashboard so you can evaluate the company, not just the job.

**Data to collect:**
- Basics: founded, HQ, size (headcount range), industry, public/private
- Funding: series, total raised, last round, notable investors
- Culture: Glassdoor/Blind ratings, engineering blog URL, open source presence
- Tech: known tech stack, engineering team size
- Context: recent news, layoffs, acquisitions

**Potential sources (free, no auth):**
- [ ] Company website scraping (About page → structured summary via Ollama)
- [ ] Wikipedia/Wikidata API (founding date, size, public/private, industry)
- [ ] GitHub org (repo count, languages, activity as a proxy for eng culture)

**Potential sources (free tier, API key):**
- [ ] Crunchbase Basic API (series, investors, funding — best startup data)
- [ ] Clearbit Company API (logo, size, industry, tech stack)

**Infrastructure:**
- [ ] `companies` table (company_name, enrichment_json, last_enriched, source)
- [ ] Enrich on `add-target` (fetch + store), re-enrich on demand
- [ ] Dashboard: `/companies` list page, `/companies/:slug` detail page
- [ ] Link from job cards/detail to company profile
- [ ] Ollama summarization of scraped About pages into structured profiles (optional, graceful skip)

### Scheduled Ingestion & Score Alerts
Automated job discovery with notifications when high-scoring matches are found.

- [ ] Config file for alert settings (schedule, score threshold, notification method)
- [ ] Scheduled ingest + score runs (cron/launchd)
- [ ] Post-score check for new jobs above threshold
- [ ] SMS/push notification when matches are found

### Containerize Worker
Isolate the Python worker in Docker to limit blast radius from untrusted external data (job HTML, API responses). The worker parses content from Lever/Greenhouse and is the primary surface for supply-chain or parser-exploit risks.

- [ ] Add `Dockerfile` for `apps/worker`
- [ ] Add `worker` service to `docker-compose.yml` with config volume mount
- [ ] Ensure `saved_jobs/` is mounted for the `save` command
- [ ] Restrict network egress to only Postgres + known job API hosts
- [ ] Update `Makefile` / scripts to run worker commands via `docker compose exec`

## Ideas (Not Yet Planned)

### Dashboard Enhancements
- Bulk actions (skip/save multiple jobs at once)
- Search/full-text filtering across job descriptions
- Sort options beyond score (date, company, location)
- Pagination or virtual scrolling for large job sets
- Job comparison view (side-by-side)
- Application tracking timeline

### Scoring Improvements
- Company reputation signals
- Profile A/B testing (compare two profiles side-by-side)

### Data & Analytics
- Score distribution charts
- Ingestion stats (new jobs per run, duplicates caught)
- Company-level aggregation (which companies post most relevant jobs)
- Historical trend tracking

### Notifications (beyond alerts)
- Digest email (would require deployment considerations)

### Export & Integration
- Export filtered jobs to CSV/JSON
- Calendar integration for interview tracking
- Resume tailoring suggestions based on job features

## Completed

### 2026-03-08
- Adzuna connector — live API integration with search-based ingestion, salary data, country filtering
- Site scraper connector — two-phase scraper (link discovery + per-page extraction) with JSON-LD and HTML heuristic support
- `make target` / `add-target` CLI command for appending companies to targets.yml with auto-detection
- Extracted shared target utilities into `targets.py`

### 2026-03-05
- Security hardening: Postgres bound to localhost only, NaN guards on route params, notes type validation, isomorphic-dompurify swap, stale docs updated
- Interactive setup wizard with auto-detection of Lever/Greenhouse connectors
- Job saving CLI for training data collection

### Initial Release
- Connector system (Lever + Greenhouse)
- Ingestion → canonicalization → feature extraction → scoring pipeline
- Web dashboard with filtering, detail view, status tracking, notes
- Config-driven YAML system (sources, targets, profile)
- Dev scripts for full startup workflow
