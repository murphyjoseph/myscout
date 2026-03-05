from __future__ import annotations
import logging
from datetime import datetime, timezone
import httpx
from myscout.connectors.base import JobConnector, NormalizedJob

logger = logging.getLogger(__name__)


class LeverConnector(JobConnector):
    """Fetches jobs from Lever's public postings API."""

    def fetch_jobs(self) -> list[NormalizedJob]:
        slug = self.conn_cfg.get("slug", "")
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"

        logger.info("Fetching Lever postings for %s", slug)
        resp = httpx.get(url, timeout=30)
        if resp.status_code == 404:
            logger.warning("Lever board not found for slug: %s (404)", slug)
            return []
        resp.raise_for_status()
        postings = resp.json()

        jobs: list[NormalizedJob] = []
        for p in postings:
            location = None
            remote_type = None
            categories = p.get("categories", {})
            loc = categories.get("location", "") or ""
            if "remote" in loc.lower():
                remote_type = "remote"
            location = loc

            commitment = categories.get("commitment", "")
            employment_type = commitment.lower() if commitment else None

            posted_at = p.get("createdAt")
            date_posted = None
            if posted_at:
                date_posted = datetime.fromtimestamp(posted_at / 1000, tz=timezone.utc)

            desc_parts = []
            for li in p.get("lists", []):
                desc_parts.append(li.get("text", ""))
                desc_parts.append(li.get("content", ""))
            description = "\n".join(filter(None, desc_parts)) or p.get("descriptionPlain", "")

            jobs.append(NormalizedJob(
                source="lever",
                external_id=p["id"],
                url=p.get("hostedUrl", ""),
                company=self.company,
                title=p.get("text", ""),
                location=location,
                remote_type=remote_type,
                employment_type=employment_type,
                description=description,
                date_posted=date_posted,
            ))

        return jobs
