# Development Log

> Auto-maintained by Claude Code via PostToolUse hook. Each entry is a one-line summary of what changed.

## 2026-03-05

- Security: bind Postgres to 127.0.0.1, add NaN guards on route params, validate notes type, swap dompurify for isomorphic-dompurify, update stale CLAUDE.md docs
- Docs: create features.md (full feature inventory), roadmap.md (planned/ideas/completed), and this logs.md
- CLAUDE.md: add Documentation section referencing docs/features.md, roadmap.md, logs.md with update instructions
- Hook: add PostToolUse hook on Edit/Write to remind Claude to append log entries
- Onboarding: add `python -m myscout setup` interactive wizard (profile + targets with auto-detect)
- Makefile: add top-level Makefile with `make setup/dev/ingest/score/save/backup/restore/reset/db`
- DB backups: add `scripts/backup.sh` (pg_dump) and `scripts/restore.sh` (pg_restore), `reset.sh` now offers backup first
- Hook: add SessionStart hook to check for profile.yml
- Score command: auto-resolves profile.yml over example.profile.yml when present
- Docs: add architecture.md and dependencies.md to CLAUDE.md Documentation section with update guidance
- Docs: add markdownify (Python) and isomorphic-dompurify (Node) to dependencies.md
- Docs: update architecture.md scripts section with Makefile, backup/restore
- Docs: update features.md with Makefile table and backup/restore in DB section
- Scoring: add title_relevance scoring (30pts) and constraint_penalty (seniority/remote/location) to scoring engine — previously role_targets and constraints in profile were ignored
- Config: add title_relevance weight to profile.yml and example.profile.yml
- Scoring: redesign to multiplicative gate model — title_match and must_have_match are now 0-1 multipliers that gate the entire score; jobs missing both collapse to 0. Wire up include_phrases as additive bonus. 738/792 jobs now score 0 (irrelevant), 37 score 1-39, 9 score 40+

## 2026-03-07

- Scoring: refine gate model — must_have_match is now the sole hard gate (multiplier), title_match moved to strong additive bonus (+25). Jobs without must-have tech score 0; title boosts relevance but doesn't gatekeep
- Scoring: add exclude_titles penalty — configurable list of title keywords (sales, recruiter, account executive, etc.) that apply -40 per match. Stacks with must-have gate for double filtering
- Scoring: normalize title matching — strip special chars before comparison so "front-end" matches "frontend", "Sr." matches "sr", etc. Applied to both title bonus and exclude_titles penalty
- Salary: add regex-based salary extraction from job descriptions (extract_salary in feature_extractor.py), add comp_min/comp_max/comp_currency columns to canonical_jobs model + DB, backfill 204/807 jobs
- Salary: display salary on job list cards ($Xk – $Yk or "Salary not listed") and job detail page as badge. Full stack: types → API SQL → presenter → view
- Scoring: add country filter — `constraints.countries.include: ["US"]` applies -100 penalty to non-matching jobs. Smart detection handles "United States", "Remote, US", state codes (", NY"), and "Americas". 482/1376 jobs match US; 894 get filtered

## 2026-03-08

- Connectors: add AshbyConnector (public API, no auth — used by Ramp, Notion, Vercel, Linear). Verified with Ramp: 132 jobs
- Connectors: add RemotiveConnector (remote job aggregator, no auth, filterable by category/search). Verified: 5 software-dev jobs
- Connectors: add BrowserConnector (Playwright headless Chromium) for JS-heavy career sites (Workday, iCIMS, SPAs). Added `playwright` dependency
- Connectors: register ashby, remotive, browser in connector map (8 total connectors)
- Setup: detect_connectors now probes Ashby in addition to Lever and Greenhouse
- Config: update sources.yml with ashby, remotive, browser entries and updated type descriptions
- Docs: update features.md connector table, dependencies.md (playwright), dev log

## 2026-03-08

- Testing: add pytest (dev dep), create tests/ with 108 unit tests across 3 modules: feature_extractor (37), scoring_engine (58), fingerprint (13). All pure-function tests, no DB required
- Bugfix: tests caught false positive in country detection — "australia" contained substring "us". Fixed with word-boundary regex for short country codes
- Makefile: add `make test` command
- Ingestion: add ingest-time country filter — reads `countries.include` from profile.yml, skips non-matching jobs before DB insert. Reuses `_location_matches_country` from scoring engine. Jobs with no location are kept (benefit of the doubt). Logs skip count
- Testing: add high-value tests — connector parsing (33), scoring integration (16), presenter tests (62 via vitest), CLI config resolution (4). Total: 219 tests (157 Python + 62 TypeScript)
- Config audit: trace all config fields through code — found 4 unused profile fields, 3 missing weight defaults, stale weight names in setup.py
- Scoring: incorporate previously unused config fields — seniority.include (-20 penalty for non-preferred), locations.include (+15 bonus for preferred city), salary.min_usd (-20 penalty for below minimum)
- Config: fix setup.py weights to match current scoring engine — remove stale `semantic_similarity`/`must_have_match`, add `base_score`/`title_match`/`penalty_exclude_title`/`include_phrase_bonus`
- Config: add missing setup.py prompts — `exclude_titles`, `countries.include`
- Config: update example.profile.yml scoring section with accurate weight names, examples, and explanations
- Config: fix user's profile.yml to use correct weight names
