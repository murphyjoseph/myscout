from __future__ import annotations
import hashlib
import re
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from myscout.db.models import Job, CanonicalJob, JobVariant

logger = logging.getLogger(__name__)


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def generate_fingerprint(company: str, title: str, location: str | None, description: str | None) -> str:
    parts = [
        normalize_text(company),
        normalize_text(title),
        normalize_text(location or "remote"),
        normalize_text(description)[:600],
    ]
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def canonicalize_job(session: Session, job: Job) -> CanonicalJob:
    """Canonicalize a raw job into the canonical_jobs table."""
    fp = generate_fingerprint(job.company, job.title, job.location, job.description_clean)
    now = datetime.now(timezone.utc)

    canonical = session.query(CanonicalJob).filter_by(fingerprint=fp).first()

    if canonical:
        canonical.last_seen = now
        logger.debug("Matched existing canonical job %d for %s", canonical.id, job.title)
    else:
        canonical = CanonicalJob(
            company=job.company,
            title=job.title,
            location=job.location,
            remote_type=job.remote_type,
            description_clean=job.description_clean,
            apply_url_best=job.url,
            fingerprint=fp,
            first_seen=now,
            last_seen=now,
            is_active=True,
        )
        session.add(canonical)
        session.flush()
        logger.info("Created canonical job %d: %s at %s", canonical.id, job.title, job.company)

    variant = JobVariant(
        canonical_job_id=canonical.id,
        job_id=job.id,
        source=job.source,
        external_id=job.external_id,
        url=job.url,
        date_seen=now,
    )
    session.add(variant)
    return canonical
