# MyScout System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           YOUR MACHINE (localhost)                          │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        CONFIG (YAML files)                           │   │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────────┐   │   │
│  │  │ sources.yml      │  │ targets.yml  │  │ example.profile.yml   │   │   │
│  │  │ connector toggle │  │ companies &  │  │ role prefs, tech,     │   │   │
│  │  │ & credentials    │  │ board slugs  │  │ keywords, weights     │   │   │
│  │  └─────────────────┘  └──────────────┘  └───────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     PYTHON WORKER CLI (uv)                           │   │
│  │                     python -m myscout                               │   │
│  │                                                                      │   │
│  │  ┌─────────────┐   ┌────────────────┐   ┌────────────────────────┐  │   │
│  │  │  CONNECTORS  │   │ CANONICALIZE   │   │   SCORE                │  │   │
│  │  │              │   │                │   │                        │  │   │
│  │  │ ┌──────────┐ │   │ Normalize text │   │ Match must_have techs  │  │   │
│  │  │ │ Lever    │─┼──▶│ SHA-256 finger │──▶│ Match strong_plus      │  │   │
│  │  │ │ (httpx)  │ │   │ Dedup & merge  │   │ Penalize avoid techs   │  │   │
│  │  │ └──────────┘ │   │ Link variants  │   │ Penalize bad phrases   │  │   │
│  │  │ ┌──────────┐ │   └────────────────┘   │ Recency bonus          │  │   │
│  │  │ │Greenhouse│ │                         │ (Semantic similarity)  │  │   │
│  │  │ │ (httpx)  │ │                         └────────────────────────┘  │   │
│  │  │ └──────────┘ │            │                       │                │   │
│  │  │ ┌──────────┐ │            │                       │                │   │
│  │  │ │ Adzuna   │ │            │    SQLAlchemy ORM      │                │   │
│  │  │ │ (stub)   │ │            │         │              │                │   │
│  │  │ └──────────┘ │            ▼         ▼              ▼                │   │
│  │  │ ┌──────────┐ │   ┌────────────────────────────────────────────┐    │   │
│  │  │ │ USAJOBS  │ │   │              WRITES TO DB                  │    │   │
│  │  │ │ (stub)   │ │   │  jobs, canonical_jobs, job_variants,       │    │   │
│  │  │ └──────────┘ │   │  job_features, job_scores, profile_versions│    │   │
│  │  │ ┌──────────┐ │   └─────────────────────┬──────────────────────┘    │   │
│  │  │ │  Site    │ │                          │                          │   │
│  │  │ │ (stub)   │ │                          │                          │   │
│  │  │ └──────────┘ │                          │                          │   │
│  │  └─────────────┘                           │                          │   │
│  └────────────────────────────────────────────┼──────────────────────────┘   │
│                                               │                             │
│                                               ▼                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    DOCKER CONTAINER                                    │  │
│  │                                                                        │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │  │
│  │  │              PostgreSQL 16 + pgvector                            │  │  │
│  │  │              image: pgvector/pgvector:pg16                       │  │  │
│  │  │              port: 5432 → localhost:5432                         │  │  │
│  │  │                                                                  │  │  │
│  │  │  ┌────────────┐ ┌───────────────┐ ┌────────────┐ ┌───────────┐  │  │  │
│  │  │  │   jobs     │ │canonical_jobs │ │job_variants│ │job_scores │  │  │  │
│  │  │  │ (raw data) │ │ (deduped)     │ │ (mapping)  │ │ (ranked)  │  │  │  │
│  │  │  └────────────┘ └───────────────┘ └────────────┘ └───────────┘  │  │  │
│  │  │  ┌────────────┐ ┌───────────────┐ ┌────────────┐                │  │  │
│  │  │  │job_features│ │job_embeddings │ │job_actions │                │  │  │
│  │  │  │ (tags etc) │ │ (pgvector)    │ │ (status)   │                │  │  │
│  │  │  └────────────┘ └───────────────┘ └────────────┘                │  │  │
│  │  │                                                                  │  │  │
│  │  │         Data stored in Docker volume: pgdata                     │  │  │
│  │  └──────────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                               │                             │
│                                               │ SELECT (pg module)          │
│                                               │ no ORM on frontend          │
│                                               ▼                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                     NEXT.JS 16 DASHBOARD (pnpm)                       │  │
│  │                     http://localhost:3000                              │  │
│  │                                                                        │  │
│  │  ┌─────────────────────┐     ┌──────────────────────────────────────┐  │  │
│  │  │   Route Handlers     │     │           React UI                   │  │  │
│  │  │   (Server-side)      │     │           (Client-side)              │  │  │
│  │  │                      │     │                                      │  │  │
│  │  │ GET /api/jobs         │◀───│  /jobs          Job list + filters   │  │  │
│  │  │ GET /api/jobs/[id]    │◀───│  /jobs/[id]     Detail + actions     │  │  │
│  │  │ PUT /api/jobs/[id]/   │◀───│                                      │  │  │
│  │  │     action            │     │  ┌────────────┐ ┌────────────────┐  │  │  │
│  │  │                      │     │  │ Chakra UI  │ │ TanStack Query │  │  │  │
│  │  │ Raw SQL via pg ──────┼─┐   │  │ (components│ │ (data fetching │  │  │  │
│  │  │ module (no ORM)      │ │   │  │  & layout) │ │  & caching)    │  │  │  │
│  │  └─────────────────────┘ │   │  └────────────┘ └────────────────┘  │  │  │
│  │                           │   └──────────────────────────────────────┘  │  │
│  │                           │                                             │  │
│  │                           └──── Queries Postgres directly               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    NOTHING LEAVES YOUR MACHINE
```

## Data Flow

```
                External APIs                     Your Config
                (public, no auth)                 (YAML files)
                     │                                 │
                     ▼                                 ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  INGEST  │──▶│  DEDUP   │──▶│ EXTRACT  │──▶│  SCORE   │──▶│ DISPLAY  │
│          │   │          │   │          │   │          │   │          │
│ Fetch    │   │ Finger-  │   │ Detect   │   │ Match    │   │ Sort by  │
│ from     │   │ print    │   │ tech     │   │ against  │   │ score    │
│ Lever,   │   │ SHA-256  │   │ tags,    │   │ profile  │   │ Filter   │
│ Green-   │   │ Merge    │   │ seniority│   │ weights  │   │ by status│
│ house    │   │ variants │   │ remote   │   │ Recency  │   │ Mark     │
│          │   │          │   │          │   │ bonus    │   │ actions  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     CLI            CLI            CLI            CLI          Browser
 `ingest`       (automatic)    `score`        `score`     localhost:3000
```

## Tools & Dependencies

```
RUNTIME                         PURPOSE                      INSTALLED VIA
──────────────────────────────────────────────────────────────────────────
Docker Desktop                  Runs Postgres container       brew / manual
PostgreSQL 16                   Database                      Docker image
pgvector extension              Vector embeddings (optional)  Docker image
Python 3.11+                    Worker CLI                    mise
uv                              Python package manager        mise
Node.js 18+                     Next.js runtime               mise
pnpm                            Node package manager          mise

PYTHON PACKAGES                 PURPOSE
──────────────────────────────────────────────────────────────────────────
sqlalchemy                      ORM for worker ↔ Postgres
alembic                         Database migrations
httpx                           HTTP client for API connectors
click                           CLI framework
pyyaml                          Config file parsing
psycopg2-binary                 Postgres driver (Python)
pgvector                        Vector type support
beautifulsoup4                  HTML parsing (save command, site scraper)
markdownify                     HTML → Markdown (save command)

NODE PACKAGES                   PURPOSE
──────────────────────────────────────────────────────────────────────────
next 16                         React framework / route handlers
react 19                        UI library
@chakra-ui/react 3              Component library
@tanstack/react-query 5         Data fetching & cache
next-themes                     Dark/light mode
pg                              Postgres driver (Node)
isomorphic-dompurify            HTML sanitization for job descriptions
```

## Commands

All commands are available via the top-level Makefile:

```
make help         Show all commands
make setup        Interactive onboarding wizard — creates profile.yml + targets
make dev          Start Postgres + dashboard (full stack)
make ingest       Fetch jobs from all configured connectors
make score        Score jobs against your profile
make save         Save a job URL — usage: make save URL=https://... OUTCOME=good_shot
make backup       Snapshot the database to backups/
make restore      Restore from backup — usage: make restore FILE=backups/<name>.dump
make reset        Destroy and recreate DB (offers backup first)
make db           Open psql shell
```

### Shell Scripts (called by Makefile)

```
./scripts/dev.sh                Start everything (first run: auto-ingests)
./scripts/ingest.sh             Fetch jobs from all enabled connectors
./scripts/score.sh              Score all jobs against your profile
./scripts/save.sh               Save a job URL to markdown
./scripts/backup.sh             pg_dump to backups/ with timestamp
./scripts/restore.sh            pg_restore from a .dump file
./scripts/reset.sh              Destroy DB and start fresh (offers backup first)
```
