# MyScout

A local-only job aggregation, deduplication, and scoring tool. MyScout ingests jobs from multiple sources (Lever, Greenhouse, and more), deduplicates them into canonical records, scores them against your personal profile, and displays everything in a local Next.js dashboard.

**This project is not intended for deployment.** It runs entirely on your machine with no authentication, no cloud services, and no external dependencies beyond Docker for Postgres.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Job Sources     │     │  Python CLI  │     │  Next.js UI  │
│  (Lever, GH...) │────▶│  Worker      │────▶│  Dashboard   │
└─────────────────┘     └──────┬───────┘     └──────┬───────┘
                               │                     │
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

### 2. Set Up Python Worker
```bash
cd apps/worker
uv sync
uv run python -m myscout init-db
```

### 3. Configure Targets

Edit `config/targets.yml` to add companies you want to track:

```yaml
targets:
  - company: Stripe
    connectors:
      - type: lever
        slug: stripe

  - company: Airbnb
    connectors:
      - type: site
        url: https://careers.airbnb.com/positions/
        crawl:
          mode: sitemap_or_links
          max_pages: 50
          allowed_domains:
            - careers.airbnb.com
```

### 4. Run Ingestion & Scoring
```bash
./scripts/ingest.sh
./scripts/score.sh --profile config/example.profile.yml
```

### 5. Start the Dashboard
```bash
cd apps/web
pnpm install
pnpm dev
```

Or use the all-in-one script:
```bash
./scripts/dev.sh
```

Visit `http://localhost:3000/jobs`

## Adding Companies

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

### Custom career page (stub)
The site scraper connector is a stub — implement the crawl logic for your target:
```yaml
- company: CompanyName
  connectors:
    - type: site
      url: https://example.com/careers
      crawl:
        mode: sitemap_or_links
        max_pages: 50
        allowed_domains:
          - example.com
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
2. Copy `config/example.profile.yml` to `config/profile.yml`
3. Fill in your preferences (titles, tech stack, keywords)
4. Add your target companies to `config/targets.yml`
5. Add `config/profile.yml` to `.gitignore` to keep your data private

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
| No input sanitization on HTML rendering | You control the data source | Sanitize all HTML, CSP headers |

If you ever want to turn this into a hosted product, you'd need to address all of the above. But for a local dev tool, they keep the codebase simple and dependency-free.

## Project Structure

```
apps/
  web/                    # Next.js dashboard
  worker/
    myscout/
      connectors/         # Source connectors (Lever, Greenhouse, stubs)
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
