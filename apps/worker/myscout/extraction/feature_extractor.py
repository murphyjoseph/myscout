from __future__ import annotations
import logging
import re
from typing import Any
from sqlalchemy.orm import Session
from myscout.db.models import CanonicalJob, JobFeature

logger = logging.getLogger(__name__)

COMMON_TECH = [
    "python", "javascript", "typescript", "react", "vue", "angular", "node",
    "nextjs", "next.js", "django", "flask", "fastapi", "rails", "ruby",
    "java", "kotlin", "swift", "go", "golang", "rust", "c++", "c#",
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform",
    "postgres", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "graphql", "rest", "grpc", "kafka", "rabbitmq",
    "machine learning", "ml", "ai", "llm", "nlp", "deep learning",
    "ci/cd", "git", "linux", "sql", "nosql",
    "figma", "tailwind", "css", "html", "sass",
]

SENIORITY_PATTERNS = {
    "intern": r"\bintern\b",
    "junior": r"\b(junior|jr\.?|entry.level)\b",
    "mid": r"\b(mid.level|intermediate)\b",
    "senior": r"\b(senior|sr\.?)\b",
    "staff": r"\bstaff\b",
    "principal": r"\bprincipal\b",
    "lead": r"\b(lead|manager|director)\b",
}


def extract_tech_tags(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for tech in COMMON_TECH:
        if tech in text_lower:
            found.append(tech)
    return sorted(set(found))


def detect_seniority(title: str) -> str | None:
    title_lower = title.lower()
    for level, pattern in SENIORITY_PATTERNS.items():
        if re.search(pattern, title_lower):
            return level
    return None


def extract_salary(text: str) -> tuple[float | None, float | None]:
    """Extract salary range from description text.

    Looks for patterns like:
      $150,000 - $200,000
      $180k-$220k
      $150,000 to $200,000
      $160,000
    Returns (min, max) in raw dollars. If only one number found, both are the same.
    """
    # Pattern: $XXX,XXX (optional k suffix) with optional range
    pattern = r"\$\s*([\d,]+)\s*[kK]?\s*(?:[-–—to/]+\s*\$?\s*([\d,]+)\s*[kK]?)?"
    matches = re.findall(pattern, text)

    salaries: list[float] = []
    for match in matches:
        for part in match:
            if not part:
                continue
            num = float(part.replace(",", ""))
            # Handle k suffix: if original text has k/K after this number
            # Also catch small numbers that are clearly in thousands
            if num < 1000:
                num *= 1000
            if 30_000 <= num <= 1_000_000:
                salaries.append(num)

    if not salaries:
        return None, None
    return min(salaries), max(salaries)


def detect_remote(location: str | None, remote_type: str | None) -> str:
    if remote_type:
        return remote_type
    if location and "remote" in location.lower():
        return "remote"
    if location and "hybrid" in location.lower():
        return "hybrid"
    return "onsite"


def extract_features(
    session: Session,
    canonical_jobs: list[CanonicalJob],
    profile_cfg: dict[str, Any],
) -> None:
    for cj in canonical_jobs:
        existing = session.query(JobFeature).filter_by(canonical_job_id=cj.id).first()

        text = (cj.description_clean or "") + " " + (cj.title or "")

        # Always extract salary (even if features exist) since it lives on canonical_jobs
        if cj.comp_min is None:
            comp_min, comp_max = extract_salary(text)
            if comp_min is not None:
                cj.comp_min = comp_min
                cj.comp_max = comp_max
                cj.comp_currency = "USD"

        if existing:
            continue

        tech_tags = extract_tech_tags(text)
        seniority = detect_seniority(cj.title)
        remote_flag = detect_remote(cj.location, cj.remote_type)

        feature = JobFeature(
            canonical_job_id=cj.id,
            tech_tags=tech_tags,
            seniority=seniority,
            remote_flag=remote_flag,
            extracted_json={"tech_tags": tech_tags, "seniority": seniority, "remote": remote_flag},
        )
        session.add(feature)

    session.flush()
    logger.info("Extracted features for %d canonical jobs", len(canonical_jobs))
