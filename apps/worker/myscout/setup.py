"""Interactive setup wizard for MyScout."""

from __future__ import annotations

import logging
from pathlib import Path

import click
import yaml

from myscout.targets import (
    CONFIG_DIR,
    TARGETS_PATH,
    TARGETS_HEADER,
    slugify,
    detect_connectors,
    save_targets,
)

logger = logging.getLogger("myscout")

PROFILE_PATH = CONFIG_DIR / "profile.yml"

# ── Prerequisite checks ─────────────────────────────────────────────────────

PREREQS = [
    ("docker", "docker --version", True, "Required for Postgres database"),
    ("uv", "uv --version", True, "Required for Python dependency management"),
    ("pnpm", "pnpm --version", True, "Required for Next.js dashboard"),
    ("ollama", "ollama --version", False, "Optional — enables semantic scoring via embeddings"),
]


def check_prereqs() -> list[dict]:
    """Check for required and optional tools. Returns list of check results."""
    import subprocess

    results = []
    for name, cmd, required, description in PREREQS:
        try:
            subprocess.run(
                cmd.split(), capture_output=True, timeout=5, check=True,
            )
            results.append({"name": name, "ok": True, "required": required, "description": description})
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            results.append({"name": name, "ok": False, "required": required, "description": description})
    return results


def display_prereqs(results: list[dict]) -> bool:
    """Display prereq check results. Returns True if all required checks pass."""
    click.echo()
    click.secho("  Checking prerequisites...", bold=True)
    click.echo()

    all_required_ok = True
    for r in results:
        icon = click.style("  +", fg="green") if r["ok"] else click.style("  x", fg="red" if r["required"] else "yellow")
        status = r["description"]
        click.echo(f"  {icon}  {r['name']:10s} {status}")
        if r["required"] and not r["ok"]:
            all_required_ok = False

    click.echo()
    if not all_required_ok:
        click.secho("  Missing required tools. Install them before continuing.", fg="red")
        click.echo("  Tip: mise install docker uv pnpm  (if using mise)")
    return all_required_ok


# ── Prompt helpers ───────────────────────────────────────────────────────────

def prompt_list(text: str, *, example: str = "", default: str = "") -> list[str]:
    """Prompt for comma-separated input, return cleaned list."""
    hint = f"  (comma-separated, e.g. \"{example}\")" if example else "  (comma-separated, leave blank to skip)"
    click.echo(f"  {text}")
    raw = click.prompt(click.style(hint, dim=True), default=default, show_default=False, prompt_suffix="\n  > ")
    if not raw.strip():
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def prompt_choice_list(text: str, options: list[str], *, default: str = "") -> list[str]:
    """Prompt for a subset of known options."""
    opts_str = "/".join(options)
    click.echo(f"  {text}")
    raw = click.prompt(
        click.style(f"  (options: {opts_str})", dim=True),
        default=default, show_default=False, prompt_suffix="\n  > ",
    )
    if not raw.strip():
        return []
    chosen = [item.strip().lower() for item in raw.split(",") if item.strip()]
    valid = [c for c in chosen if c in options]
    invalid = [c for c in chosen if c not in options]
    if invalid:
        click.secho(f"  Skipping unknown options: {', '.join(invalid)}", fg="yellow")
    return valid


# ── Company slug detection ───────────────────────────────────────────────────

def add_company_interactive() -> dict | None:
    """Walk the user through adding a single target company. Returns target dict or None."""
    name = click.prompt("\n  Company name", prompt_suffix=": ").strip()
    if not name:
        return None

    slug = slugify(name)
    alt_slug = None

    click.echo(f"  Checking APIs for slug \"{slug}\"...")
    found = detect_connectors(slug)

    # If nothing found, try without hyphens (e.g., "palo-alto-networks" → "paloaltonetworks")
    if not found and "-" in slug:
        alt_slug = slug.replace("-", "")
        click.echo(f"  Trying \"{alt_slug}\"...")
        found = detect_connectors(alt_slug)
        if found:
            slug = alt_slug

    if not found:
        click.secho(f"  No jobs found on Lever or Greenhouse for \"{slug}\".", fg="yellow")
        custom = click.prompt(
            "  Enter a custom slug (or press Enter to skip)",
            default="", show_default=False,
        ).strip()
        if custom:
            click.echo(f"  Checking \"{custom}\"...")
            found = detect_connectors(custom)
            slug = custom
        if not found:
            click.secho("  Could not find jobs. Skipping this company.", fg="yellow")
            return None

    connectors = []
    for conn_type, count in found:
        click.secho(f"    {conn_type.capitalize():12s} {count} jobs found", fg="green")
        connectors.append({"type": conn_type, "slug": slug})

    # If both found, let user pick or keep both
    if len(found) > 1:
        keep = click.prompt(
            "  Both connectors found. Keep both, or choose one? [both/lever/greenhouse]",
            default="both",
        ).strip().lower()
        if keep in ("lever", "greenhouse"):
            connectors = [c for c in connectors if c["type"] == keep]

    return {"company": name, "connectors": connectors}


# ── Profile building ─────────────────────────────────────────────────────────

SENIORITY_OPTIONS = ["intern", "junior", "mid", "senior", "staff", "principal", "lead"]
REMOTE_OPTIONS = ["remote", "hybrid", "onsite"]
EMPLOYMENT_OPTIONS = ["full-time", "part-time", "contract", "internship"]


def build_profile() -> dict:
    """Walk through profile questions, return profile dict."""
    click.echo()
    click.secho("  Step 1: Your Profile", bold=True)
    click.secho("  " + "-" * 45, dim=True)
    click.echo()

    # Role targets
    titles = prompt_list(
        "What job titles are you looking for?",
        example="software engineer, frontend developer",
    )
    exclude_titles = prompt_list(
        "Title keywords to filter out?",
        example="sales, recruiter, account executive, customer success",
    )
    seniority_include = prompt_choice_list(
        "What seniority levels?",
        SENIORITY_OPTIONS,
        default="senior, staff",
    )
    seniority_exclude = prompt_choice_list(
        "Any seniority levels to exclude?",
        SENIORITY_OPTIONS,
    )

    click.echo()

    # Constraints
    remote = prompt_choice_list(
        "Work arrangement?",
        REMOTE_OPTIONS,
        default="remote, hybrid",
    )
    countries_include = prompt_list("Allowed countries?", example="US, UK, CA")
    locations_include = prompt_list("Preferred locations?", example="San Francisco, New York, Austin")
    locations_exclude = prompt_list("Locations to exclude?", example="Beijing, Mumbai")
    employment = prompt_choice_list(
        "Employment type?",
        EMPLOYMENT_OPTIONS,
        default="full-time",
    )

    min_salary_str = click.prompt(
        click.style("  (leave blank to skip)", dim=True) + "\n  Minimum salary (USD)",
        default="", show_default=False, prompt_suffix=": ",
    ).strip()
    min_salary = int(min_salary_str) if min_salary_str.isdigit() else None

    click.echo()

    # Tech preferences
    must_have = prompt_list("Must-have technologies?", example="typescript, react, python")
    strong_plus = prompt_list("Nice-to-have technologies?", example="nextjs, graphql, tailwind")
    avoid = prompt_list("Technologies to avoid?", example="php, wordpress, cobol")

    click.echo()

    # Keywords
    include_phrases = prompt_list("Bonus phrases in job descriptions?", example="developer experience, open source")
    exclude_phrases = prompt_list("Dealbreaker phrases?", example="clearance required, on-call rotation")

    return {
        "profile": {
            "role_targets": {
                "titles": titles,
                "exclude_titles": exclude_titles,
                "seniority": {
                    "include": seniority_include,
                    "exclude": seniority_exclude,
                },
            },
            "constraints": {
                "remote": {"allowed": remote},
                "countries": {"include": countries_include},
                "locations": {
                    "include": locations_include,
                    "exclude": locations_exclude,
                },
                "employment_type": {"include": employment},
                "salary": {"min_usd": min_salary},
            },
            "tech_preferences": {
                "must_have": must_have,
                "strong_plus": strong_plus,
                "avoid": avoid,
            },
            "keywords": {
                "include_phrases": include_phrases,
                "exclude_phrases": exclude_phrases,
            },
            "training_examples": {
                "good_shot": [],
                "got_interview": [],
                "aspirational": [],
            },
        },
        "scoring": {
            "weights": {
                "base_score": 30,
                "title_match": 25,
                "penalty_exclude_title": -40,
                "strong_plus_match": 10,
                "include_phrase_bonus": 5,
                "penalty_avoid_tech": -25,
                "penalty_exclude_phrase": -40,
                "recency_bonus_max": 10,
            },
        },
    }


# ── Targets building ────────────────────────────────────────────────────────

def build_targets() -> dict:
    """Walk through adding target companies, return targets dict."""
    click.echo()
    click.secho("  Step 2: Target Companies", bold=True)
    click.secho("  " + "-" * 45, dim=True)
    click.echo("  Add companies whose job boards you want to track.")
    click.echo("  We'll auto-detect if they use Lever or Greenhouse.")

    targets = []
    while True:
        if targets:
            if not click.confirm("\n  Add another company?", default=True):
                break
        else:
            if not click.confirm("\n  Add a company?", default=True):
                break

        result = add_company_interactive()
        if result:
            targets.append(result)
            click.secho(f"  Added {result['company']}.", fg="green")

    return {"targets": targets}


# ── YAML writing ─────────────────────────────────────────────────────────────

PROFILE_HEADER = """\
# MyScout Profile — generated by `python -m myscout setup`
# Edit freely. See config/example.profile.yml for full documentation.
# This file is gitignored — your personal data stays on your machine.

"""

def write_yaml(path: Path, header: str, data: dict) -> None:
    """Write a YAML file with a comment header."""
    body = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    path.write_text(header + body, encoding="utf-8")


# ── Main command ─────────────────────────────────────────────────────────────

def run_setup() -> None:
    """Run the full interactive setup wizard."""
    click.echo()
    click.secho("  MyScout Setup", bold=True, fg="cyan")
    click.secho("  " + "=" * 45, fg="cyan")

    # Prereqs
    results = check_prereqs()
    if not display_prereqs(results):
        if not click.confirm("  Continue anyway?", default=False):
            raise SystemExit(1)

    # Check for existing profile
    if PROFILE_PATH.exists():
        click.secho(f"  Found existing profile at {PROFILE_PATH}", fg="yellow")
        if not click.confirm("  Overwrite it?", default=False):
            click.echo("  Keeping existing profile.")
            profile_data = None
        else:
            profile_data = build_profile()
    else:
        profile_data = build_profile()

    # Targets
    targets_data = build_targets()

    # Write files
    click.echo()
    if profile_data:
        write_yaml(PROFILE_PATH, PROFILE_HEADER, profile_data)
        click.secho(f"  Wrote {PROFILE_PATH}", fg="green")

    if targets_data["targets"]:
        save_targets(targets_data)
        click.secho(f"  Wrote {TARGETS_PATH}", fg="green")
    else:
        click.echo("  No companies added. You can edit config/targets.yml later.")

    # Summary
    click.echo()
    click.secho("  Setup complete!", bold=True, fg="green")
    click.echo()
    click.echo("  Next steps:")
    click.echo("    make dev       Start Postgres + dashboard")
    click.echo("    make ingest    Fetch jobs from your targets")
    click.echo("    make score     Score jobs against your profile")
    click.echo()
    click.echo("  Tip: save job postings you like with:")
    click.echo("    make save URL=<url>")
    click.echo()
