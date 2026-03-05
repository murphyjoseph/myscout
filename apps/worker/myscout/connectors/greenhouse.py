from __future__ import annotations
import logging
from datetime import datetime, timezone
import httpx
from myscout.connectors.base import JobConnector, NormalizedJob

logger = logging.getLogger(__name__)


class GreenhouseConnector(JobConnector):
    """Fetches jobs from Greenhouse's public board API."""

    def fetch_jobs(self) -> list[NormalizedJob]:
        slug = self.conn_cfg.get("slug", "")
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

        logger.info("Fetching Greenhouse jobs for %s", slug)
        resp = httpx.get(url, timeout=30)
        if resp.status_code == 404:
            logger.warning("Greenhouse board not found for slug: %s (404)", slug)
            return []
        resp.raise_for_status()
        data = resp.json()

        jobs: list[NormalizedJob] = []
        for j in data.get("jobs", []):
            location = j.get("location", {}).get("name", "")
            remote_type = None
            if location and "remote" in location.lower():
                remote_type = "remote"

            updated = j.get("updated_at")
            date_posted = None
            if updated:
                date_posted = datetime.fromisoformat(updated.replace("Z", "+00:00"))

            description = j.get("content", "")

            jobs.append(NormalizedJob(
                source="greenhouse",
                external_id=str(j["id"]),
                url=j.get("absolute_url", ""),
                company=self.company,
                title=j.get("title", ""),
                location=location,
                remote_type=remote_type,
                description=description,
                date_posted=date_posted,
            ))

        return jobs
