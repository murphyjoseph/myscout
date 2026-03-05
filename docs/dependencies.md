# Dependencies Guide

A breakdown of every dependency in the project — what it does, why it's here, and whether it's required.

---

## System Requirements

These must be installed on your machine before anything else.

| Tool | What it does | Why we need it |
|---|---|---|
| **Docker Desktop** | Runs containers — isolated mini-servers on your machine | Postgres runs inside a Docker container so you don't need to install it natively. One `docker compose up` and you have a database. |
| **mise** | Version manager for dev tools (like nvm/pyenv but for everything) | Manages your Python, Node.js, pnpm, and uv installations. Ensures everyone uses the same versions. |
| **uv** | Python package manager written in Rust | Replaces pip and venv. Creates virtual environments and installs packages 10-100x faster. Run `mise use -g uv` to install. |
| **pnpm** | Node.js package manager | Replaces npm. Faster installs, uses less disk space via hard-linked shared store. The Next.js app uses this. |
| **Ollama** (optional) | Runs AI models locally | Used for generating embeddings to power semantic job matching. The app works without it — scoring falls back to keyword matching. |

---

## Docker Image

| Image | What it does |
|---|---|
| **pgvector/pgvector:pg16** | PostgreSQL 16 with the pgvector extension pre-installed. pgvector adds a `vector` column type and cosine similarity search to Postgres — this is how we store and compare job embeddings. Without pgvector you'd need a separate vector database like Pinecone or Weaviate. |

---

## Python Packages (apps/worker)

### Core — required for the app to function

| Package | What it does | How we use it |
|---|---|---|
| **sqlalchemy** | Python SQL toolkit and ORM (Object-Relational Mapper) | Defines the database schema as Python classes (`Job`, `CanonicalJob`, etc.) and handles all reads/writes to Postgres. Instead of writing raw SQL in Python, you work with objects. |
| **psycopg2-binary** | PostgreSQL driver for Python | The low-level connector that SQLAlchemy uses to actually talk to Postgres over the network. The `-binary` variant ships pre-compiled so you don't need PostgreSQL dev headers installed. |
| **alembic** | Database migration tool (built on SQLAlchemy) | Tracks schema changes over time. When you add a column or table, Alembic generates a migration script so the change is repeatable. Think of it as "git for your database schema." |
| **httpx** | Modern HTTP client for Python | Makes API calls to Lever and Greenhouse to fetch job postings. Also used to call the Ollama embeddings API. Chosen over `requests` because it supports async and has a cleaner API. |
| **pyyaml** | YAML parser | Reads the config files (`sources.yml`, `targets.yml`, `profile.yml`). YAML is used instead of JSON because it's more readable for configuration and supports comments. |
| **click** | CLI framework | Provides the `python -m myscout ingest` / `score` / `init-db` command interface. Handles argument parsing, help text, and subcommands. |
| **pgvector** | pgvector Python integration for SQLAlchemy | Adds the `Vector` column type to SQLAlchemy so we can store and query embeddings directly in Postgres. |
| **beautifulsoup4** | HTML parser | Used by the `save` command to extract job content from career page HTML, and by the site scraper connector stub. Parses the DOM to find job description containers and strips nav/footer/script noise. |
| **markdownify** | HTML → Markdown converter | Used by the `save` command to convert extracted job posting HTML into clean Markdown files stored in `saved_jobs/`. These Markdown files serve as training data for embedding-based scoring. |

### Optional

| Package | What it does | How we use it |
|---|---|---|
| **playwright** | Headless browser automation (Chromium) | Powers the `browser` connector type for crawling JS-heavy career sites (Workday, iCIMS, custom SPAs). Launches a real Chromium instance that renders JavaScript, then extracts job data from the DOM. Install browser with `uv run playwright install chromium`. ~150MB for the Chromium binary. |
| **openai** | OpenAI Python SDK | Listed as an optional dependency (`uv pip install -e ".[embeddings]"`). Only needed if you want to use OpenAI's embedding API instead of Ollama. Not installed by default. |

---

## Node Packages (apps/web)

### Core — required for the dashboard

| Package | What it does | How we use it |
|---|---|---|
| **next** (v16) | React framework with server-side rendering, routing, and API routes | The entire dashboard runs on Next.js. We use the App Router for file-based routing and Route Handlers as the API layer between the browser and Postgres. |
| **react** (v19) | UI library for building component-based interfaces | The foundation — every UI element is a React component. v19 adds the `use()` hook we use for unwrapping params promises in Next.js. |
| **react-dom** (v19) | React's DOM rendering layer | Pairs with React to render components into the browser. Separate package because React can also render to native (React Native) or other targets. |
| **@chakra-ui/react** (v3) | Component library | Provides pre-built, accessible UI components — `Box`, `Badge`, `Button`, `Input`, `Heading`, `Stack`, etc. Saves us from writing CSS from scratch while keeping things consistent. |
| **@emotion/react** | CSS-in-JS library | Chakra UI's styling engine. Generates scoped CSS at runtime from the style props you pass to Chakra components (like `p={4}` or `color="gray.500"`). |
| **@tanstack/react-query** (v5) | Data fetching and cache management | Handles all API calls from the browser to our route handlers. Caches responses, deduplicates requests, and automatically re-fetches when you invalidate (e.g., after marking a job as "APPLIED"). |
| **next-themes** | Dark/light mode for Next.js | Manages color mode toggling. Works with Chakra UI's theming system to persist your preference. |
| **pg** | PostgreSQL client for Node.js | The route handlers use this to query Postgres directly — no ORM on the frontend side. We write raw SQL for maximum control and minimal overhead. |
| **isomorphic-dompurify** | HTML sanitizer (works in Node + browser) | Sanitizes job description HTML before rendering with `dangerouslySetInnerHTML`. Called in the presenter layer so raw descriptions from external sources can't inject scripts. The "isomorphic" variant works in both server-side route handlers and client-side React. |
| **js-yaml** | YAML parser for JavaScript | Reads `config/profile.yml` in the `/api/profile` route handler to expose tech preferences (must_have, strong_plus, avoid) to the dashboard for tag highlighting. |

### Dev Dependencies

| Package | What it does |
|---|---|
| **typescript** | Static type checker for JavaScript. Catches bugs at compile time instead of runtime. |
| **@types/node** | TypeScript type definitions for Node.js built-in modules. |
| **@types/react** | TypeScript type definitions for React. |
| **@types/react-dom** | TypeScript type definitions for React DOM. |
| **@types/pg** | TypeScript type definitions for the `pg` PostgreSQL client. |
| **@types/js-yaml** | TypeScript type definitions for `js-yaml`. |

---

## Dependency Philosophy

This project intentionally keeps dependencies minimal:

- **No Prisma/Drizzle** on the frontend — raw SQL via `pg` is simpler for a local tool with no migration concerns on the JS side
- **No Express/Fastify** — Next.js Route Handlers eliminate the need for a separate API server
- **No Redis** — TanStack Query handles client-side caching; Postgres is fast enough for a single user
- **No authentication library** — local-only, single user
- **No Tailwind** — Chakra UI provides both components and styling in one package
- **No monorepo tooling** (Turborepo/Nx) — simple `apps/` directory convention is sufficient

Every dependency earns its place by solving a real problem. If you can remove one without losing functionality, do it.
