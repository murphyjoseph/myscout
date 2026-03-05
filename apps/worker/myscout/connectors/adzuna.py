from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx

from myscout.connectors.base import JobConnector, NormalizedJob

logger = logging.getLogger(__name__)

# Adzuna API country codes — the {country} segment in the URL.
# Full list: gb, us, au, br, ca, de, fr, in, nl, nz, pl, ru, sg, za
DEFAULT_COUNTRY = "us"
DEFAULT_RESULTS_PER_PAGE = 50
MAX_PAGES = 3  # cap to avoid burning through rate limits


class AdzunaConnector(JobConnector):
    """Fetches jobs from Adzuna's search API.

    Unlike board connectors (Lever, Greenhouse), Adzuna is a job search engine.
    Configure search parameters in targets.yml:

        - company: Adzuna Search
          connectors:
          - type: adzuna
            what: "software engineer"
            country: us
            results_per_page: 50
            max_pages: 2

    Credentials are read from env vars ADZUNA_APP_ID and ADZUNA_API_KEY.
    """

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def fetch_jobs(self) -> list[NormalizedJob]:
        app_id = os.environ.get("ADZUNA_APP_ID", "")
        api_key = os.environ.get("ADZUNA_API_KEY", "")

        if not app_id or not api_key:
            logger.warning(
                "Adzuna credentials missing. "
                "Set ADZUNA_APP_ID and ADZUNA_API_KEY environment variables."
            )
            return []

        what = self.conn_cfg.get("what", "")
        if not what:
            logger.warning("Adzuna connector requires 'what' (search keywords) in config.")
            return []

        country = self.conn_cfg.get("country", DEFAULT_COUNTRY)
        where = self.conn_cfg.get("where", "")
        what_exclude = self.conn_cfg.get("what_exclude", "")
        results_per_page = self.conn_cfg.get("results_per_page", DEFAULT_RESULTS_PER_PAGE)
        max_pages = self.conn_cfg.get("max_pages", MAX_PAGES)
        salary_min = self.conn_cfg.get("salary_min")
        full_time = self.conn_cfg.get("full_time")

        all_jobs: list[NormalizedJob] = []

        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/{country}/search/{page}"
            params: dict[str, str | int] = {
                "app_id": app_id,
                "app_key": api_key,
                "what": what,
                "results_per_page": results_per_page,
                "content-type": "application/json",
            }
            if where:
                params["where"] = where
            if what_exclude:
                params["what_exclude"] = what_exclude
            if salary_min is not None:
                params["salary_min"] = salary_min
            if full_time:
                params["full_time"] = 1

            logger.info(
                "Fetching Adzuna page %d for '%s' in %s",
                page, what, country.upper(),
            )
            try:
                resp = httpx.get(url, params=params, timeout=30)
            except httpx.HTTPError as e:
                logger.error("Adzuna HTTP error: %s", e)
                break

            if resp.status_code == 401:
                logger.error("Adzuna auth failed (401). Check ADZUNA_APP_ID and ADZUNA_API_KEY.")
                return []
            if resp.status_code == 400:
                logger.error("Adzuna bad request (400): %s", resp.text[:300])
                return []
            if resp.status_code != 200:
                logger.warning("Adzuna returned %d on page %d", resp.status_code, page)
                break

            data = resp.json()
            results = data.get("results", [])
            if not results:
                logger.debug("No more results on page %d", page)
                break

            for r in results:
                company_name = r.get("company", {}).get("display_name", "Unknown")
                location_data = r.get("location", {})
                # Build location from area array (includes country) rather
                # than display_name (which omits it).  Reversed so it reads
                # "City, County, State, US" — matches the country filter.
                area = location_data.get("area", [])
                if area:
                    location = ", ".join(reversed(area))
                else:
                    location = location_data.get("display_name", "")

                remote_type = None
                if location and "remote" in location.lower():
                    remote_type = "remote"

                # contract_time: "full_time", "part_time", "contract"
                employment_type = r.get("contract_time")

                date_posted = None
                created = r.get("created")
                if created:
                    try:
                        date_posted = datetime.fromisoformat(
                            created.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass

                # Salary — Adzuna often returns predicted salaries.
                # We include them but could flag predicted ones later.
                comp_min = r.get("salary_min")
                comp_max = r.get("salary_max")

                # Adzuna only provides a description snippet, not the full posting.
                description = r.get("description", "")

                all_jobs.append(NormalizedJob(
                    source="adzuna",
                    external_id=str(r.get("id", "")),
                    url=r.get("redirect_url", ""),
                    company=company_name,
                    title=r.get("title", ""),
                    location=location,
                    remote_type=remote_type,
                    employment_type=employment_type,
                    description=description,
                    date_posted=date_posted,
                    comp_min=comp_min,
                    comp_max=comp_max,
                    comp_currency=r.get("salary_currency"),
                ))

            logger.info("Got %d jobs from Adzuna page %d", len(results), page)

        logger.info("Adzuna total: %d jobs fetched for '%s'", len(all_jobs), what)
        return all_jobs
