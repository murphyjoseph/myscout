from __future__ import annotations

import logging
import click
from pathlib import Path
from myscout.db.session import get_engine, get_session
from myscout.db.models import Base

logger = logging.getLogger("myscout")

CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
SAVED_JOBS_DIR = Path(__file__).resolve().parents[3] / "saved_jobs"


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool) -> None:
    """myscout: local job ingestion and scoring engine."""
    setup_logging(verbose)


@cli.command()
def setup() -> None:
    """Interactive setup wizard — creates profile.yml and configures targets."""
    from myscout.setup import run_setup
    run_setup()


@cli.command()
def init_db() -> None:
    """Create all database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database tables created.")


def _load_country_filter() -> list[str]:
    """Load allowed countries from profile.yml for ingest-time filtering.

    Returns an empty list (no filtering) if profile doesn't exist or has no
    country constraint configured.
    """
    import yaml

    profile_path = CONFIG_DIR / "profile.yml"
    if not profile_path.exists():
        return []
    try:
        with open(profile_path) as f:
            cfg = yaml.safe_load(f)
        countries = (
            cfg.get("profile", {})
            .get("constraints", {})
            .get("countries", {})
            .get("include", [])
        )
        return [c.lower() for c in countries] if countries else []
    except Exception:
        return []


@cli.command()
@click.option("--sources", default=str(CONFIG_DIR / "sources.yml"), help="Path to sources.yml")
@click.option("--targets", default=str(CONFIG_DIR / "targets.yml"), help="Path to targets.yml")
def ingest(sources: str, targets: str) -> None:
    """Ingest jobs from all enabled connectors."""
    import yaml
    from myscout.connectors import get_connector
    from myscout.canonicalization.fingerprint import canonicalize_job
    from myscout.scoring.scoring_engine import _location_matches_country
    from myscout.db.models import Job
    from datetime import datetime, timezone

    with open(sources) as f:
        sources_cfg = yaml.safe_load(f)
    with open(targets) as f:
        targets_cfg = yaml.safe_load(f)

    enabled_sources = {s["id"]: s for s in sources_cfg["sources"] if s.get("enabled")}

    allowed_countries = _load_country_filter()
    if allowed_countries:
        logger.info("Country filter active: %s", ", ".join(c.upper() for c in allowed_countries))

    session = get_session()
    total_ingested = 0
    total_skipped_country = 0

    for target in targets_cfg["targets"]:
        company = target["company"]
        for conn_cfg in target.get("connectors", []):
            conn_type = conn_cfg["type"]
            if conn_type not in enabled_sources:
                logger.debug("Skipping disabled connector %s for %s", conn_type, company)
                continue

            logger.info("Ingesting %s via %s", company, conn_type)
            try:
                connector = get_connector(conn_type, company, conn_cfg, enabled_sources[conn_type])
                if connector is None:
                    logger.warning("No connector implementation for type: %s", conn_type)
                    continue

                normalized_jobs = connector.fetch_jobs()
                logger.info("Fetched %d jobs from %s/%s", len(normalized_jobs), company, conn_type)

                for nj in normalized_jobs:
                    # Skip jobs outside allowed countries at ingest time.
                    # Jobs with no location are kept (benefit of the doubt).
                    if allowed_countries and nj.location:
                        loc_lower = nj.location.lower()
                        if not any(_location_matches_country(loc_lower, c) for c in allowed_countries):
                            total_skipped_country += 1
                            continue

                    existing = session.query(Job).filter_by(
                        source=nj.source, external_id=nj.external_id
                    ).first()

                    if existing:
                        existing.date_seen = datetime.now(timezone.utc)
                        logger.debug("Updated date_seen for %s", nj.external_id)
                    else:
                        job = Job(
                            source=nj.source,
                            external_id=nj.external_id,
                            url=nj.url,
                            company=nj.company,
                            title=nj.title,
                            location=nj.location,
                            remote_type=nj.remote_type,
                            employment_type=nj.employment_type,
                            description_raw=nj.description,
                            description_clean=nj.description,
                            date_posted=nj.date_posted,
                            date_seen=datetime.now(timezone.utc),
                            comp_min=nj.comp_min,
                            comp_max=nj.comp_max,
                            comp_currency=nj.comp_currency,
                        )
                        session.add(job)
                        session.flush()

                        canonicalize_job(session, job)
                        total_ingested += 1

                session.commit()
            except Exception:
                logger.exception("Error ingesting %s via %s", company, conn_type)
                session.rollback()

    if total_skipped_country:
        logger.info("Skipped %d jobs outside allowed countries", total_skipped_country)
    logger.info("Ingestion complete. %d new jobs added.", total_ingested)
    session.close()


def _default_profile() -> str:
    """Prefer profile.yml over example.profile.yml when it exists."""
    custom = CONFIG_DIR / "profile.yml"
    if custom.exists():
        return str(custom)
    return str(CONFIG_DIR / "example.profile.yml")


@cli.command()
@click.option("--profile", default=None, help="Path to profile YAML")
def score(profile: str | None) -> None:
    """Score all canonical jobs against a profile."""
    import yaml
    import json
    from myscout.scoring.scoring_engine import score_jobs
    from myscout.extraction.feature_extractor import extract_features
    from myscout.db.models import CanonicalJob, ProfileVersion
    from datetime import datetime, timezone

    if profile is None:
        profile = _default_profile()
    logger.info("Using profile: %s", profile)

    with open(profile) as f:
        profile_cfg = yaml.safe_load(f)

    session = get_session()

    pv = ProfileVersion(
        profile_json=json.dumps(profile_cfg),
        created_at=datetime.now(timezone.utc),
    )
    session.add(pv)
    session.flush()

    canonical_jobs = session.query(CanonicalJob).filter_by(is_active=True).all()
    logger.info("Scoring %d canonical jobs", len(canonical_jobs))

    extract_features(session, canonical_jobs, profile_cfg)
    score_jobs(session, canonical_jobs, pv, profile_cfg)

    session.commit()
    logger.info("Scoring complete.")
    session.close()


@cli.command("add-target")
@click.argument("company", required=False)
@click.option("--type", "conn_type", type=click.Choice(["auto", "lever", "greenhouse", "ashby", "site", "adzuna"]), default="auto", help="Connector type (default: auto-detect)")
@click.option("--slug", default=None, help="Board slug (for lever/greenhouse/ashby)")
@click.option("--url", "site_url", default=None, help="Careers page URL (for site connector)")
def add_target(company: str | None, conn_type: str, slug: str | None, site_url: str | None) -> None:
    """Add a target company to config/targets.yml.

    Auto-detects Lever, Greenhouse, and Ashby boards by probing their APIs.

    \b
    Examples:
      myscout add-target                           # interactive
      myscout add-target "Stripe"                  # auto-detect
      myscout add-target "Stripe" --type site --url https://stripe.com/jobs/search
    """
    from myscout.setup import add_company_interactive
    from myscout.targets import (
        detect_connectors,
        slugify,
        load_targets,
        save_targets,
    )

    # Load existing targets
    data = load_targets()
    targets = data["targets"]

    existing_names = {t["company"].lower() for t in targets}

    if company is None:
        # Interactive mode — reuse setup wizard flow
        result = add_company_interactive()
        if not result:
            return
    elif conn_type == "auto":
        # Auto-detect from company name
        s = slug or slugify(company)
        click.echo(f"  Checking APIs for \"{s}\"...")
        found = detect_connectors(s)

        # Try without hyphens
        if not found and "-" in s:
            alt = s.replace("-", "")
            click.echo(f"  Trying \"{alt}\"...")
            found = detect_connectors(alt)
            if found:
                s = alt

        if not found:
            click.secho(f"  No board found for \"{s}\". Try --type site --url <careers-page>", fg="yellow")
            return

        connectors = []
        for ct, count in found:
            click.secho(f"    {ct.capitalize():12s} {count} jobs found", fg="green")
            connectors.append({"type": ct, "slug": s})

        result = {"company": company, "connectors": connectors}
    elif conn_type == "site":
        if not site_url:
            click.secho("  --url is required for site connector.", fg="red")
            return
        result = {
            "company": company,
            "connectors": [{"type": "site", "url": site_url}],
        }
    elif conn_type in ("lever", "greenhouse", "ashby"):
        s = slug or slugify(company)
        result = {
            "company": company,
            "connectors": [{"type": conn_type, "slug": s}],
        }
    elif conn_type == "adzuna":
        what = click.prompt("  Search keywords", default=company)
        result = {
            "company": f"Adzuna: {what}",
            "connectors": [{"type": "adzuna", "what": what, "country": "us", "results_per_page": 50, "max_pages": 2}],
        }
    else:
        return

    # Duplicate check
    if result["company"].lower() in existing_names:
        click.secho(f"  \"{result['company']}\" is already in targets.yml.", fg="yellow")
        if not click.confirm("  Add anyway?", default=False):
            return

    targets.append(result)
    save_targets(data)

    click.secho(f"  Added {result['company']}.", fg="green")
    click.echo("  Run `make ingest` to fetch jobs.")


def _register_training_example(saved_path: Path, outcome: str) -> None:
    """Add a saved job to profile.yml's training_examples section."""
    import yaml

    profile_path = CONFIG_DIR / "profile.yml"
    if not profile_path.exists():
        logger.debug("No profile.yml found — skipping training_examples registration")
        return

    # Use path relative to project root (e.g. "saved_jobs/vercel-site-engineer.md")
    relative_path = str(saved_path.relative_to(saved_path.parents[1]))

    try:
        raw = profile_path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw) or {}
    except Exception:
        logger.warning("Could not parse profile.yml — skipping registration")
        return

    profile = doc.setdefault("profile", {})
    examples = profile.setdefault("training_examples", {})
    category = examples.setdefault(outcome, [])

    if relative_path in category:
        logger.info("Already registered in profile.yml")
        return

    category.append(relative_path)

    # Rewrite the file preserving the header comment
    header_lines = []
    for line in raw.splitlines(keepends=True):
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break
    header = "".join(header_lines)

    body = yaml.dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True)
    profile_path.write_text(header + body, encoding="utf-8")
    logger.info("Registered %s in profile.yml under training_examples.%s", relative_path, outcome)


@cli.command()
@click.argument("url")
@click.option("--outcome", type=click.Choice(["good_shot", "got_interview", "aspirational"]), default="good_shot", help="How this job relates to your goals")
def save(url: str, outcome: str) -> None:
    """Save a job posting URL as markdown to saved_jobs/."""
    import re
    import httpx
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md

    logger.info("Fetching %s", url)
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract title
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else "Unknown"

    # Try to extract company and job title from page title
    # Common patterns: "Job Title - Company", "Job Title | Company", "Company - Job Title"
    company = "Unknown"
    job_title = page_title
    for sep in [" - ", " | ", " — ", " · "]:
        if sep in page_title:
            parts = page_title.split(sep)
            # Heuristic: shorter part is usually the company
            if len(parts) == 2:
                if len(parts[0]) < len(parts[1]):
                    company, job_title = parts[0].strip(), parts[1].strip()
                else:
                    job_title, company = parts[0].strip(), parts[1].strip()
            break

    # Extract main content — try common job description containers
    content_el = None
    for selector in ["article", "main", "[class*='description']", "[class*='posting']", "[class*='content']", "[id*='content']"]:
        content_el = soup.select_one(selector)
        if content_el:
            break

    if content_el is None:
        content_el = soup.find("body")

    # Remove nav, footer, scripts, styles
    for tag in content_el.find_all(["nav", "footer", "script", "style", "header", "iframe"]):
        tag.decompose()

    # Convert to markdown
    body_md = md(str(content_el), heading_style="ATX", strip=["img"])
    # Clean up excessive whitespace
    body_md = re.sub(r"\n{3,}", "\n\n", body_md.strip())

    # Generate filename
    slug = re.sub(r"[^\w\s-]", "", f"{company} {job_title}".lower())
    slug = re.sub(r"[\s]+", "-", slug.strip())[:80]
    output_path = SAVED_JOBS_DIR / f"{slug}.md"

    # Avoid overwriting
    counter = 1
    while output_path.exists():
        output_path = SAVED_JOBS_DIR / f"{slug}-{counter}.md"
        counter += 1

    frontmatter = f"""---
company: {company}
title: {job_title}
url: {url}
outcome: {outcome}
---

"""
    output_path.write_text(frontmatter + body_md, encoding="utf-8")
    logger.info("Saved to %s", output_path)

    # Auto-register in profile.yml under training_examples
    _register_training_example(output_path, outcome)
