from __future__ import annotations

import logging
from datetime import datetime

import httpx

from myscout.connectors.base import JobConnector, NormalizedJob

logger = logging.getLogger(__name__)

# Remotive categories for filtering (optional)
CATEGORIES = [
    "software-dev", "customer-support", "design", "marketing",
    "sales", "product", "business", "data", "devops", "finance",
    "human-resources", "qa", "writing", "all-others",
]


class RemotiveConnector(JobConnector):
    """Fetches remote jobs from Remotive's public API.

    API: https://remotive.com/api/remote-jobs
    No auth required. Returns remote-only jobs across many companies.
    """

    def fetch_jobs(self) -> list[NormalizedJob]:
        category = self.conn_cfg.get("category", "software-dev")
        search = self.conn_cfg.get("search", "")
        limit = self.conn_cfg.get("limit", 200)

        params: dict[str, str | int] = {"limit": limit}
        if category:
            params["category"] = category
        if search:
            params["search"] = search

        logger.info("Fetching Remotive jobs (category=%s, search=%s)", category, search or "*")
        resp = httpx.get("https://remotive.com/api/remote-jobs", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        jobs: list[NormalizedJob] = []
        for j in data.get("jobs", []):
            date_posted = None
            pub_date = j.get("publication_date")
            if pub_date:
                try:
                    date_posted = datetime.fromisoformat(pub_date)
                except ValueError:
                    pass

            job_type_raw = (j.get("job_type") or "").lower()
            employment_map = {
                "full_time": "full-time",
                "part_time": "part-time",
                "contract": "contract",
                "freelance": "contract",
                "internship": "internship",
                "other": None,
            }
            employment_type = employment_map.get(job_type_raw, job_type_raw or None)

            location = j.get("candidate_required_location", "")

            # Remotive is a remote-only board
            jobs.append(NormalizedJob(
                source="remotive",
                external_id=str(j["id"]),
                url=j.get("url", ""),
                company=j.get("company_name", self.company),
                title=j.get("title", ""),
                location=location,
                remote_type="remote",
                employment_type=employment_type,
                description=j.get("description", ""),
                date_posted=date_posted,
            ))

        return jobs
