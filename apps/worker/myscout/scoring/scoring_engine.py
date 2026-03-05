from __future__ import annotations
import re
import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from myscout.db.models import CanonicalJob, JobFeature, JobScore, ProfileVersion

logger = logging.getLogger(__name__)


def _normalize_title(text: str) -> str:
    """Strip special characters and lowercase for title comparison.

    Only used for title matching — NOT for tech/keyword matching where
    characters like +, #, . are meaningful (c++, c#, .net).
    """
    return re.sub(r"[^a-z0-9\s]", "", text.lower())


def _title_relevance(title_lower: str, target_titles: list[str]) -> float:
    """Return best match ratio (0.0-1.0) of job title against target titles.

    Both sides are normalized (special chars stripped) so "front-end"
    matches "frontend", "Sr." matches "sr", etc.
    Returns 1.0 if no target titles are configured (no filter).
    """
    if not target_titles:
        return 1.0

    norm_title = _normalize_title(title_lower)

    best = 0.0
    for target in target_titles:
        norm_target = _normalize_title(target)
        if norm_target in norm_title or norm_title in norm_target:
            return 1.0
        target_words = set(norm_target.split())
        title_words = set(norm_title.split())
        overlap = len(target_words & title_words)
        if target_words:
            ratio = overlap / len(target_words)
            best = max(best, ratio)
    return best


def _must_have_ratio(
    must_have: list[str], tech_tags: list[str], full_text: str
) -> float:
    """Return match ratio (0.0-1.0) for must-have technologies.

    Returns 1.0 if no must-have techs are configured (no filter).
    """
    if not must_have:
        return 1.0
    matched = sum(1 for t in must_have if t in tech_tags or t in full_text)
    return matched / len(must_have)


_US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "MA", "MD",
    "ME", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}

# Map of shorthand country codes to location-string indicators.
# "US" gets special handling; others use simple substring matching.
_COUNTRY_ALIASES: dict[str, list[str]] = {
    "us": ["united states", "americas"],
    "uk": ["united kingdom", "england", "scotland", "wales"],
    "ca": ["canada"],
    "de": ["germany"],
    "fr": ["france"],
    "in": ["india"],
    "au": ["australia"],
    "ie": ["ireland"],
    "il": ["israel"],
    "jp": ["japan"],
    "br": ["brazil"],
    "mx": ["mexico"],
    "sg": ["singapore"],
    "nl": ["netherlands"],
    "es": ["spain"],
    "it": ["italy"],
    "kr": ["korea"],
    "se": ["sweden"],
    "pl": ["poland"],
}


def _location_matches_country(location_lower: str, country: str) -> bool:
    """Check if a location string indicates a given country."""
    country = country.lower().strip()

    # For short codes (2-3 chars), use word-boundary regex to avoid
    # false positives like "us" matching inside "australia".
    if len(country) <= 3:
        if re.search(rf"\b{re.escape(country)}\b", location_lower, re.IGNORECASE):
            return True
    else:
        # Longer names (e.g. "united states") are safe for substring match
        if country in location_lower:
            return True

    # Look up aliases for short codes
    aliases = _COUNTRY_ALIASES.get(country, [])
    for alias in aliases:
        if alias in location_lower:
            return True

    # Special US detection: state abbreviation patterns
    if country == "us":
        # Match ", XX" or "; XX" where XX is a US state code
        for match in re.finditer(r"[,;]\s*([A-Z]{2})\b", location_lower, re.IGNORECASE):
            if match.group(1).upper() in _US_STATE_CODES:
                return True

    return False


def _check_constraints(
    cj: CanonicalJob,
    feature: JobFeature | None,
    constraints: dict[str, Any],
    seniority_cfg: dict[str, Any],
) -> float:
    """Return a penalty/bonus for constraint checks.

    Negative values penalize mismatches, positive values reward preferred matches.
    """
    penalty = 0.0

    # Seniority exclude — hard penalty for explicitly unwanted levels
    seniority_exclude = [s.lower() for s in seniority_cfg.get("exclude", [])]
    if seniority_exclude and feature and feature.seniority:
        if feature.seniority.lower() in seniority_exclude:
            penalty -= 50

    # Seniority include — softer penalty when detected seniority is outside
    # preferred levels. Only applied when seniority is detected AND the user
    # has specified preferred levels. Jobs with undetected seniority are not
    # penalized (benefit of the doubt).
    seniority_include = [s.lower() for s in seniority_cfg.get("include", [])]
    if seniority_include and feature and feature.seniority:
        if feature.seniority.lower() not in seniority_include:
            penalty -= 20

    remote_cfg = constraints.get("remote", {})
    allowed_remote = [r.lower() for r in remote_cfg.get("allowed", [])]
    if allowed_remote and cj.remote_type:
        if cj.remote_type.lower() not in allowed_remote:
            penalty -= 30

    loc_cfg = constraints.get("locations", {})
    loc_exclude = [loc.lower() for loc in loc_cfg.get("exclude", [])]
    loc_lower = (cj.location or "").lower()
    if loc_exclude and loc_lower:
        for loc in loc_exclude:
            if loc in loc_lower:
                penalty -= 30
                break

    # Location include — small bonus for jobs in preferred locations.
    # This rewards proximity without penalizing jobs elsewhere.
    loc_include = [loc.lower() for loc in loc_cfg.get("include", [])]
    if loc_include and loc_lower:
        for loc in loc_include:
            if loc in loc_lower:
                penalty += 15
                break

    # Country filter — heavy penalty for jobs outside allowed countries
    country_cfg = constraints.get("countries", {})
    allowed_countries = [c.lower() for c in country_cfg.get("include", [])]
    if allowed_countries and loc_lower:
        if not any(_location_matches_country(loc_lower, c) for c in allowed_countries):
            penalty -= 100

    # Salary minimum — moderate penalty when extracted salary is below
    # the user's minimum. Penalty is moderate because salary extraction
    # from descriptions is imprecise.
    salary_cfg = constraints.get("salary", {})
    min_usd = salary_cfg.get("min_usd")
    if min_usd and cj.comp_max:
        if cj.comp_max < min_usd:
            penalty -= 20

    return penalty


def score_jobs(
    session: Session,
    canonical_jobs: list[CanonicalJob],
    profile_version: ProfileVersion,
    profile_cfg: dict[str, Any],
) -> None:
    weights = profile_cfg.get("scoring", {}).get("weights", {})
    profile = profile_cfg.get("profile", {})
    tech_prefs = profile.get("tech_preferences", {})
    keywords = profile.get("keywords", {})
    role_targets = profile.get("role_targets", {})
    constraints = profile.get("constraints", {})
    seniority_cfg = role_targets.get("seniority", {})

    target_titles = [t.lower() for t in role_targets.get("titles", [])]
    exclude_titles = [t.lower() for t in role_targets.get("exclude_titles", [])]
    must_have = [t.lower() for t in tech_prefs.get("must_have", [])]
    strong_plus = [t.lower() for t in tech_prefs.get("strong_plus", [])]
    avoid = [t.lower() for t in tech_prefs.get("avoid", [])]
    include_phrases = [p.lower() for p in keywords.get("include_phrases", [])]
    exclude_phrases = [p.lower() for p in keywords.get("exclude_phrases", [])]

    w_title = weights.get("title_match", 25)
    w_title_exclude = weights.get("penalty_exclude_title", -40)
    w_strong = weights.get("strong_plus_match", 10)
    w_avoid = weights.get("penalty_avoid_tech", -25)
    w_include = weights.get("include_phrase_bonus", 5)
    w_exclude = weights.get("penalty_exclude_phrase", -40)
    w_recency = weights.get("recency_bonus_max", 10)
    w_base = weights.get("base_score", 30)

    for cj in canonical_jobs:
        feature = session.query(JobFeature).filter_by(canonical_job_id=cj.id).first()
        tech_tags = [t.lower() for t in (feature.tech_tags or [])] if feature else []
        desc_lower = (cj.description_clean or "").lower()
        title_lower = (cj.title or "").lower()
        full_text = f"{title_lower} {desc_lower}"

        breakdown: dict[str, float] = {}

        # ── Hard gate (multiplicative) ────────────────────────────
        # Must-have tech is the hard requirement. If none of your
        # must-have skills appear, the job scores 0 — period.
        mh_ratio = _must_have_ratio(must_have, tech_tags, full_text)
        breakdown["must_have_match"] = round(mh_ratio, 2)

        # ── Title relevance (strong additive bonus) ───────────────
        # Title match is important but not a gate. A job with an
        # unusual title that still requires your tech stack can
        # surface — it just won't score as high as a perfect title.
        title_ratio = _title_relevance(title_lower, target_titles)
        title_bonus = round(title_ratio * w_title, 2)
        breakdown["title_match"] = title_bonus

        # ── Title exclusion penalty ───────────────────────────────
        # If the title contains words you flagged (e.g. "sales",
        # "recruiter", "account executive"), apply a heavy penalty.
        norm_title = _normalize_title(title_lower)
        title_exclude_count = sum(
            1 for t in exclude_titles if _normalize_title(t) in norm_title
        )
        title_exclude_score = round(title_exclude_count * w_title_exclude, 2) if title_exclude_count else 0
        breakdown["penalty_exclude_title"] = title_exclude_score

        # ── Additive components ───────────────────────────────────
        component_sum = w_base + title_bonus + title_exclude_score

        # Strong-plus match
        if strong_plus:
            matched = sum(1 for t in strong_plus if t in tech_tags or t in full_text)
            ratio = matched / len(strong_plus)
            sp_score = round(ratio * w_strong, 2)
        else:
            sp_score = 0
        breakdown["strong_plus_match"] = sp_score
        component_sum += sp_score

        # Include phrase bonus
        include_count = sum(1 for p in include_phrases if p in full_text)
        ip_score = round(include_count * w_include, 2) if include_count else 0
        breakdown["include_phrase_bonus"] = ip_score
        component_sum += ip_score

        # Avoid tech penalty
        avoid_count = sum(1 for t in avoid if t in tech_tags or t in full_text)
        avoid_score = round(avoid_count * w_avoid, 2) if avoid_count else 0
        breakdown["penalty_avoid_tech"] = avoid_score
        component_sum += avoid_score

        # Exclude phrase penalty
        exclude_count = sum(1 for p in exclude_phrases if p in full_text)
        exclude_score = round(exclude_count * w_exclude, 2) if exclude_count else 0
        breakdown["penalty_exclude_phrase"] = exclude_score
        component_sum += exclude_score

        # Constraint penalties (seniority, remote, location)
        constraint_penalty = _check_constraints(cj, feature, constraints, seniority_cfg)
        breakdown["constraint_penalty"] = round(constraint_penalty, 2)
        component_sum += constraint_penalty

        # Recency bonus
        recency = 0.0
        if cj.last_seen:
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            last_seen = cj.last_seen.replace(tzinfo=None) if cj.last_seen.tzinfo else cj.last_seen
            days_ago = (now_naive - last_seen).days
            if days_ago <= 7:
                recency = w_recency
            elif days_ago <= 30:
                recency = w_recency * (1 - (days_ago - 7) / 23)
        breakdown["recency_bonus"] = round(max(0, recency), 2)
        component_sum += breakdown["recency_bonus"]

        # Semantic similarity placeholder (requires embeddings)
        breakdown["semantic_similarity"] = 0

        # ── Final score ───────────────────────────────────────────
        # Must-have is the hard gate. If must_have_match is 0,
        # the entire score collapses to 0.
        # Title is already folded into component_sum as a bonus.
        total = round(component_sum * mh_ratio, 2)
        breakdown["total"] = total

        score = JobScore(
            canonical_job_id=cj.id,
            profile_version_id=profile_version.id,
            score_total=total,
            score_breakdown_json=breakdown,
            created_at=datetime.now(timezone.utc),
        )
        session.add(score)

    session.flush()
    logger.info("Scored %d jobs", len(canonical_jobs))
