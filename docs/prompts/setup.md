You are a senior staff engineer. Build a local-only OSS-first monorepo called "job-scout" that ingests jobs from multiple sources, deduplicates them into canonical job records, scores them against a configurable user profile, and displays them in a Next.js UI.

This project **must run entirely locally** and require **no authentication, no cloud services, and no deployment**. It is intentionally designed as a **local developer tool**, not a hosted product. The architecture should prioritize simplicity, maintainability, and the ability for others to **fork the repository and customize it privately**.

The OSS version must remain **agnostic to any individual user's data**. Personal data (resume text, job examples, API keys, etc.) should be stored only in configs that users add in their own fork.

---

# Tech Stack

## Frontend

- Next.js (App Router)
- TypeScript
- **pnpm** as the package manager
- **Chakra UI** for UI components
- **TanStack Query** for data fetching and caching
- **TanStack Form** (only if forms are needed; do not introduce unnecessary complexity)
- Minimal dependencies
- UI reads directly from Postgres using **Next.js route handlers or server actions**
- No authentication system
- No deployment configuration

The frontend should be designed as a **local dashboard tool**, not a public web application.

Make sure the frontend follows exactly the front-end-architecture.md file.

---

## Backend Processing

Python worker CLI responsible for ingestion and scoring.

- Python 3.11+
- SQLAlchemy
- Alembic migrations
- Optional embeddings support (skip gracefully if API keys absent)

No HTTP API is required. The worker runs via CLI commands.

---

## Database

- Postgres running via Docker
- pgvector extension enabled

---

# Architecture Principles

- **Local-first**: everything runs locally
- **Never intended for deployment**
- **OSS-safe**: no secrets or personal data
- **Fork-friendly**: users should easily maintain a private fork
- **Config-driven**: behavior controlled via YAML configs
- **Connector-based ingestion system**
- **Canonical deduplication layer for jobs**
- **Clean modular Python package structure**
- **Minimal infrastructure**

---

# Repository Structure

job-scout/
apps/
web/ # Next.js UI
worker/
myscout/
connectors/
base.py
lever.py
greenhouse.py
adzuna_stub.py
usajobs_stub.py
site_stub.py
canonicalization/
fingerprint.py
scoring/
scoring_engine.py
extraction/
feature_extractor.py
db/
models.py
migrations/
cli.py
config/
example.profile.yml
sources.yml
targets.yml
data/
examples/
scripts/
dev.sh
ingest.sh
score.sh
docker-compose.yml
.env.example
README.md

---

# Configuration Files

## config/example.profile.yml

Defines the user's job preferences and scoring model.

Must support:

profile:
role_targets:
titles: []
seniority:
include: []
exclude: []

constraints:
remote:
allowed: ["remote","hybrid"]
locations:
include: []
exclude: []
employment_type:
include: ["full-time"]
salary:
min_usd: null

tech_preferences:
must_have: []
strong_plus: []
avoid: []

keywords:
include_phrases: []
exclude_phrases: []

training_examples:
good_shot: []
got_interview: []
aspirational: []

scoring:
weights:
semantic_similarity: 55
must_have_match: 20
strong_plus_match: 10
penalty_avoid_tech: -25
penalty_exclude_phrase: -40
recency_bonus_max: 10

---

## config/sources.yml

Defines global connector availability and credentials.

sources:

- id: adzuna
  type: api
  enabled: false
  credentials:
  app_id_env: ADZUNA_APP_ID
  api_key_env: ADZUNA_API_KEY

- id: usajobs
  type: api
  enabled: false
  credentials:
  api_key_env: USAJOBS_API_KEY
  email_env: USAJOBS_EMAIL

- id: greenhouse
  type: board
  enabled: true

- id: lever
  type: board
  enabled: true

- id: site
  type: scraper
  enabled: true

---

## config/targets.yml

Defines specific companies or career pages to monitor.

targets:

- company: Airbnb
  connectors:
  - type: site
    url: https://careers.airbnb.com/positions/
    crawl:
    mode: sitemap_or_links
    max_pages: 50
    allowed_domains:
    - careers.airbnb.com

- company: Stripe
  connectors:
  - type: lever
    slug: stripe

- company: ExampleCo
  connectors:
  - type: greenhouse
    slug: exampleco

---

# Database Schema

## jobs (raw ingestion records)

- id
- source
- external_id
- url
- company
- title
- location
- remote_type
- employment_type
- description_raw
- description_clean
- date_posted
- date_seen
- comp_min
- comp_max
- comp_currency
- created_at

Unique constraints:

(source, external_id)
or fallback unique index on url

---

## canonical_jobs (deduplicated jobs)

- id
- company
- title
- location
- remote_type
- description_clean
- apply_url_best
- fingerprint
- first_seen
- last_seen
- is_active

fingerprint must be unique.

---

## job_variants

Maps raw jobs to canonical jobs.

- id
- canonical_job_id
- job_id
- source
- external_id
- url
- date_seen

---

## job_features

- id
- canonical_job_id
- tech_tags (text[])
- seniority
- remote_flag
- extracted_json

---

## job_embeddings

- canonical_job_id
- embedding vector

---

## profile_versions

- id
- profile_json
- created_at

---

## job_scores

- canonical_job_id
- profile_version_id
- score_total
- score_breakdown_json
- created_at

---

## job_actions

- canonical_job_id
- status (NEW, SAVED, APPLIED, SKIPPED, INTERVIEWING)
- notes
- updated_at

---

# Canonical Deduplication System

All ingested jobs must be canonicalized.

Steps:

1. Normalize fields:

- lowercase company/title
- remove punctuation
- trim whitespace

2. Generate fingerprint:

sha256(
normalize(company) +
normalize(title) +
normalize(location_or_remote) +
first_600_chars(description_clean)
)

3. If fingerprint exists:
   reuse canonical job

4. If not:
   create new canonical job

5. Insert mapping row in job_variants.

---

# Connector Interface

Define base class:

class JobConnector:
def fetch_jobs(self) -> list[NormalizedJob]

NormalizedJob schema:

- source
- external_id
- url
- company
- title
- location
- remote_type
- employment_type
- description
- date_posted
- compensation fields

---

# Implement Working Connectors

Lever:

https://api.lever.co/v0/postings/{slug}?mode=json

Greenhouse:

https://boards-api.greenhouse.io/v1/boards/{slug}/jobs

---

# Provide Stub Connectors

- Adzuna
- USAJOBS
- Site scraper

---

# Worker CLI Commands

python -m myscout ingest

- load sources.yml and targets.yml
- run enabled connectors
- normalize jobs
- insert into jobs table
- run canonicalization
- create job_variants mapping

python -m myscout score

- load profile.yml
- create profile_version
- clean descriptions
- extract tech tags and seniority
- optionally compute embeddings
- apply scoring algorithm
- write job_scores

---

# Next.js UI

## /jobs

List canonical jobs sorted by score_total.

Display:

- title
- company
- remote/location
- score
- top scoring reasons
- status

Filters:

- status
- minimum score
- remote_type
- source

---

## /jobs/[id]

Job detail page:

- description
- extracted tech tags
- score breakdown
- sources found (from job_variants)
- action controls

Actions:

- mark saved
- mark applied
- skip
- add notes

---

# Scripts

scripts/dev.sh

start postgres via docker-compose
start Next.js dev server

scripts/ingest.sh

run ingestion worker

scripts/score.sh

run scoring worker

---

# README Must Include

- project overview
- architecture explanation
- explanation that the project is **local-only and not intended for deployment**
- how deduplication works
- how to configure targets.yml
- how to fork privately for personal profile data
- instructions to add companies like Airbnb or Stripe
- instructions to add additional connectors

---

# Quality Constraints

- minimal dependencies
- strongly typed models
- readable modular code
- clear logging
- graceful behavior if optional APIs are missing
- easy for developers to fork and customize

---

Now generate the repository including key files, code, configs, scripts, and README.
