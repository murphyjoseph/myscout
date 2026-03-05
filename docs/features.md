# MyScout Features

> Last updated: 2026-03-05

## Ingestion Pipeline

### Connector System
Pluggable connectors fetch jobs from external sources and normalize them into a common format.

| Connector | Source | Status |
|-----------|--------|--------|
| LeverConnector | Lever public postings API | Working |
| GreenhouseConnector | Greenhouse public board API | Working |
| AshbyConnector | Ashby public posting API (Ramp, Notion, Vercel, Linear) | Working |
| RemotiveConnector | Remotive remote job aggregator (no auth) | Working |
| AdzunaConnector | Adzuna job search API (requires free API key) | Working |
| SiteConnector | Generic website scraper (httpx + BeautifulSoup + JSON-LD) | Working |
| BrowserConnector | Headless browser crawler (Playwright, for JS-heavy SPAs) | Working |
| UsajobsStubConnector | USAJOBS.gov API | Stub |

All connectors extend `JobConnector` and return `list[NormalizedJob]`. HTTP 404s return empty lists with a warning logged. New connectors are registered in `apps/worker/myscout/connectors/__init__.py`.

### Deduplication & Canonicalization
- SHA-256 fingerprint from `company | title | location | first_600_chars(description)`
- `canonical_jobs` table holds one record per unique job
- `job_variants` table tracks every raw source that maps to a canonical job
- `first_seen` / `last_seen` updated on re-sighting

### Feature Extraction
Runs automatically during scoring. Extracts per canonical job:

- **Tech tags** — matches 60+ technologies (python, react, kubernetes, terraform, etc.) against description text
- **Seniority** — regex detection of intern/junior/mid/senior/staff/principal/lead in title
- **Remote flag** — inferred from location field and `remote_type` column

Results stored in `job_features` table.

## Scoring

Config-driven scoring against a YAML profile (`config/profile.yml`).

| Component | Description | Default Weight |
|-----------|-------------|----------------|
| Must-have tech match | % of required tech found | +20 |
| Strong-plus tech match | % of nice-to-have tech found | +10 |
| Avoid tech penalty | Per avoided tech found in listing | -25 each |
| Exclude phrase penalty | Per dealbreaker phrase found | -40 each |
| Recency bonus | Full bonus ≤7 days, linear decay to 30 days | +10 max |
| Semantic similarity | Embedding comparison to training examples | +55 max (stub) |

Score breakdowns stored as JSON per job per profile version. Weights are configurable in `profile.yml` under `scoring.weights`.

## Web Dashboard

Next.js 16 App Router application at `localhost:3000`.

### Jobs List (`/jobs`)
- Filter bar: status, minimum score, remote type, source
- Job cards showing: title, company, location, remote/seniority badges, score (color-coded), tech tags, description snippet, last-seen date
- Tech tag highlighting: must-have (amber), strong-plus (green), avoid (red) based on profile
- Sorted by score descending
- Loading, empty, and error states

### Job Detail (`/jobs/:id`)
- Full job header with all metadata badges
- Score breakdown table with per-component +/- coloring
- Source variants list with links to original postings
- HTML description (sanitized via isomorphic-dompurify)
- Status selector (NEW, SAVED, APPLIED, SKIPPED, INTERVIEWING)
- Notes editor with save
- Apply button linking to best URL

### API Routes
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/jobs` | GET | List with filters, parameterized SQL |
| `/api/jobs/:id` | GET | Detail + variants |
| `/api/jobs/:id/action` | PUT | Update status/notes (LOCAL-ONLY: no auth) |
| `/api/profile` | GET | Tech preferences from profile.yml (LOCAL-ONLY: no auth) |

## Setup & Onboarding

Interactive CLI wizard: `python -m myscout setup`

1. **Prerequisite check** — verifies docker, uv, pnpm; warns if ollama missing
2. **Profile creation** — prompts for role targets, seniority, constraints, tech preferences, keywords
3. **Company detection** — auto-probes Lever/Greenhouse APIs with slugified company name
4. Outputs `config/profile.yml` and `config/targets.yml`

`dev.sh` checks for `profile.yml` and nudges toward setup if missing.

## Configuration

All behavior driven by YAML files in `config/`:

| File | Purpose |
|------|---------|
| `sources.yml` | Connector registry with enable/disable flags |
| `targets.yml` | Companies to track with connector type + slug |
| `profile.yml` | Personal scoring profile (gitignored) |
| `example.profile.yml` | Documented template for profile creation |

## Job Saving

`python -m myscout save <url> --outcome <type>` saves a job posting as markdown to `saved_jobs/`. Outcomes: `good_shot`, `got_interview`, `aspirational`. These files are training data for future embedding-based scoring.

## Makefile

Top-level `Makefile` provides short commands that wrap the underlying scripts and CLI:

| Command | Purpose |
|---------|---------|
| `make setup` | Interactive onboarding wizard (profile + targets) |
| `make dev` | Full startup (Postgres, deps, tables, ingest, score, dev server) |
| `make ingest` | Fetch jobs from all enabled connectors |
| `make score` | Score jobs against profile |
| `make save URL=... OUTCOME=...` | Save a job posting URL to markdown |
| `make backup` | Snapshot DB to `backups/` (timestamped pg_dump) |
| `make restore FILE=...` | Restore DB from a `.dump` backup |
| `make reset` | Destroy and recreate DB (offers backup first) |
| `make db` | Open psql shell |

## Scripts

| Script | Purpose |
|--------|---------|
| `dev.sh` | Full startup (Postgres, deps, tables, ingest, score, dev server) |
| `ingest.sh` | Run ingestion pipeline |
| `score.sh` | Run scoring against profile |
| `save.sh` | Save a job URL to markdown |
| `backup.sh` | pg_dump to `backups/` with timestamp |
| `restore.sh` | pg_restore from a `.dump` file |
| `reset.sh` | Destroy and recreate database (offers backup first) |

## Database

Postgres 16 + pgvector, managed via Docker. Backups via `make backup` (pg_dump custom format) to `backups/` directory (gitignored). Restore with `make restore FILE=...`. Reset offers backup automatically before destroying data.

8 tables:

`jobs` → `canonical_jobs` ← `job_variants`
`canonical_jobs` → `job_features`, `job_embeddings`, `job_scores`, `job_actions`
`profile_versions` → `job_scores`

Schema defined in `apps/worker/myscout/db/models.py` (SQLAlchemy). Frontend queries via raw parameterized SQL.
