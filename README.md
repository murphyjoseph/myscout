# MyScout

A local-only job aggregation, deduplication, and scoring tool. MyScout ingests jobs from multiple sources (Lever, Greenhouse, Ashby, Adzuna, Remotive, custom career sites, and more), deduplicates them into canonical records, scores them against your personal profile, and displays everything in a local Next.js dashboard.

**This project is not intended for deployment.** It runs entirely on your machine with no authentication, no cloud services, and no external dependencies beyond Docker for Postgres.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Job Sources     │     │  Python CLI  │     │  Next.js UI  │
│  (Lever, GH,    │────▶│  Worker      │────▶│  Dashboard   │
│   Ashby, ...)   │     └──────┬───────┘     └──────┬───────┘
└─────────────────┘            │                     │
                         ┌─────▼─────────────────────▼──┐
                         │    Postgres + pgvector        │
                         │    (Docker)                   │
                         └──────────────────────────────┘
```

**Key design decisions:**
- **No API layer** — Next.js reads directly from Postgres via route handlers
- **Connector-based ingestion** — each source is a pluggable Python class
- **Canonical deduplication** — SHA-256 fingerprinting merges the same job across sources
- **Config-driven scoring** — YAML profile defines what you're looking for
- **Fork-friendly** — personal data lives only in config files you add to your fork

## How Deduplication Works

Every ingested job is fingerprinted using:
```
sha256(normalize(company) + normalize(title) + normalize(location) + first_600_chars(description))
```

If a fingerprint already exists, the job is linked as a variant of the existing canonical record. This means a job posted on both Lever and Greenhouse (or scraped from a career page) is only shown once, with all sources tracked.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- pnpm
- [uv](https://docs.astral.sh/uv/) (`mise use -g uv`)

### 1. Start Postgres
```bash
docker compose up -d
```

### 2. Run the Setup Wizard
```bash
make setup
```

This walks you through creating your profile (job titles, tech preferences, constraints) and adding target companies. It auto-detects whether companies use Lever, Greenhouse, or Ashby.

### 3. Ingest & Score
```bash
make ingest    # Fetch jobs from all configured connectors
make score     # Score jobs against your profile
```

### 4. Start the Dashboard
```bash
make dev       # Starts Postgres + Next.js dev server
```

Visit `http://localhost:3000/jobs`

See all available commands with `make help`.

## Adding Companies

### Quick add via CLI
```bash
make target COMPANY="Stripe"              # Auto-detects connector
make target COMPANY="Ramp" TYPE=ashby     # Specify connector type
```

### Lever-based career pages
Find the company's Lever slug (visible in their job posting URLs like `jobs.lever.co/{slug}/...`):
```yaml
- company: CompanyName
  connectors:
    - type: lever
      slug: their-slug
```

### Greenhouse-based career pages
Find the board slug from URLs like `boards.greenhouse.io/{slug}/jobs/...`:
```yaml
- company: CompanyName
  connectors:
    - type: greenhouse
      slug: their-slug
```

### Ashby-based career pages
For companies using Ashby (Ramp, Notion, Linear, Vercel):
```yaml
- company: CompanyName
  connectors:
    - type: ashby
      slug: their-slug
```

### Custom career page (site scraper)
The site scraper discovers job links from a listing page, then extracts details from each page using JSON-LD and HTML heuristics:
```yaml
- company: CompanyName
  connectors:
    - type: site
      url: https://example.com/careers
      link_selector: "a[href*='/jobs/']"   # optional CSS selector
      max_jobs: 50                          # optional, default 50
```

### Adzuna (search-based)
Requires a free API key — set `ADZUNA_APP_ID` and `ADZUNA_API_KEY` in `.env`:
```yaml
- company: Adzuna Search
  connectors:
    - type: adzuna
      what: "software engineer"
      country: us
      results_per_page: 50
      max_pages: 2
```

### Browser connector (JS-heavy SPAs)
For sites that require JavaScript rendering (Workday, iCIMS, custom SPAs). Requires Playwright:
```bash
uv run playwright install chromium
```
```yaml
- company: CompanyName
  connectors:
    - type: browser
      url: https://example.com/careers
```

## Adding Connectors

Create a new file in `apps/worker/myscout/connectors/`:

```python
from myscout.connectors.base import JobConnector, NormalizedJob

class MyConnector(JobConnector):
    def fetch_jobs(self) -> list[NormalizedJob]:
        # Fetch and return normalized job records
        ...
```

Register it in `apps/worker/myscout/connectors/__init__.py`:
```python
_CONNECTOR_MAP["myconnector"] = MyConnector
```

## Forking for Personal Use

1. Fork this repository privately
2. Run `make setup` to create your profile and add target companies
3. Or manually: copy `config/example.profile.yml` to `config/profile.yml` and fill in your preferences
4. `config/profile.yml` is already gitignored — your personal data stays on your machine

## Local-Only Tradeoffs

This project intentionally makes choices you should **never** make in a deployed application. These are called out with `LOCAL-ONLY` comments in the code:

| Tradeoff | Why it's fine here | What you'd do in production |
|---|---|---|
| Hardcoded DB credentials in source | Single-user, localhost only | Secrets manager (Vault, AWS SSM, etc.) |
| No authentication on any endpoint | Only you access it | OAuth, session tokens, API keys |
| No CSRF protection on mutations | No browser-based attacks against yourself | CSRF tokens on all state-changing requests |
| Raw SQL in route handlers | Simple, fast, no ORM overhead | Parameterized queries via an ORM or query builder with auth middleware |
| No rate limiting | You're the only user | Rate limiting per IP/user |
| Docker DB with no volume encryption | Local dev data only | Encrypted volumes, TLS connections |
| Job description HTML rendered via `dangerouslySetInnerHTML` | Sanitized with DOMPurify in the presenter layer | Additional CSP headers for defense-in-depth |

If you ever want to turn this into a hosted product, you'd need to address all of the above. But for a local dev tool, they keep the codebase simple and dependency-free.

## Project Structure

```
apps/
  web/                    # Next.js dashboard
  worker/
    myscout/
      connectors/         # Source connectors (Lever, Greenhouse, Ashby, Adzuna, Remotive, Site, Browser)
      canonicalization/    # Fingerprinting & dedup
      scoring/            # Profile-based scoring engine
      extraction/         # Tech tag & seniority extraction
      db/                 # SQLAlchemy models & migrations
      cli.py              # CLI entry point
config/                   # YAML configuration files
scripts/                  # Shell scripts for dev, ingest, score
docker-compose.yml        # Postgres with pgvector
```

## License

See [LICENSE](./LICENSE).
