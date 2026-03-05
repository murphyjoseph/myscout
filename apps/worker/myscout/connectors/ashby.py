from __future__ import annotations

import logging
from datetime import datetime

import httpx

from myscout.connectors.base import JobConnector, NormalizedJob

logger = logging.getLogger(__name__)


class AshbyConnector(JobConnector):
    """Fetches jobs from Ashby's public posting API.

    Used by: Ramp, Notion, Vercel, Linear, and many other tech companies.
    API docs: https://developers.ashbyhq.com/docs/public-api
    """

    def fetch_jobs(self) -> list[NormalizedJob]:
        slug = self.conn_cfg.get("slug", "")
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"

        logger.info("Fetching Ashby jobs for %s", slug)
        resp = httpx.get(url, timeout=30)
        if resp.status_code == 404:
            logger.warning("Ashby board not found for slug: %s (404)", slug)
            return []
        resp.raise_for_status()
        data = resp.json()

        jobs: list[NormalizedJob] = []
        for j in data.get("jobs", []):
            if not j.get("isListed", True):
                continue

            location = j.get("location", "")
            workplace_type = (j.get("workplaceType") or "").lower()
            is_remote = j.get("isRemote", False)

            if is_remote or workplace_type == "remote":
                remote_type = "remote"
            elif workplace_type == "hybrid":
                remote_type = "hybrid"
            else:
                remote_type = "onsite"

            emp_raw = (j.get("employmentType") or "").lower()
            employment_map = {
                "fulltime": "full-time",
                "parttime": "part-time",
                "contract": "contract",
                "intern": "internship",
                "internship": "internship",
            }
            employment_type = employment_map.get(emp_raw, emp_raw or None)

            date_posted = None
            published = j.get("publishedAt")
            if published:
                try:
                    date_posted = datetime.fromisoformat(published)
                except ValueError:
                    pass

            # Ashby returns HTML descriptions
            description = j.get("descriptionHtml") or j.get("descriptionPlain", "")

            jobs.append(NormalizedJob(
                source="ashby",
                external_id=j["id"],
                url=j.get("jobUrl", ""),
                company=self.company,
                title=j.get("title", ""),
                location=location,
                remote_type=remote_type,
                employment_type=employment_type,
                description=description,
                date_posted=date_posted,
            ))

        return jobs
