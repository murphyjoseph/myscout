from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from myscout.connectors.base import JobConnector, NormalizedJob

logger = logging.getLogger(__name__)

# Heuristic patterns for links that look like individual job postings.
_JOB_LINK_PATTERNS = [
    r"/jobs?/",
    r"/careers?/",
    r"/positions?/",
    r"/openings?/",
    r"/listing/",
    r"/apply/",
    r"/requisition/",
    r"/role/",
    r"/vacancy/",
]
_JOB_LINK_RE = re.compile("|".join(_JOB_LINK_PATTERNS), re.IGNORECASE)

# Links to skip even if they match a job pattern.
_SKIP_PATTERNS = re.compile(
    r"(\.pdf$|\.png$|\.jpg$|mailto:|javascript:|#$|/search$|/filter|/login|/sign)"
    r"|(/(team|about|blog|press|contact|faq|help|privacy|terms)/)",
    re.IGNORECASE,
)

DEFAULT_MAX_JOBS = 50
REQUEST_DELAY = 0.5  # seconds between requests to be polite


class SiteConnector(JobConnector):
    """Generic website scraper for company career pages.

    Fetches a careers/jobs listing page, discovers individual job links,
    then extracts details from each job page.

    Config in targets.yml:

        - company: Stripe
          connectors:
          - type: site
            url: https://stripe.com/jobs/search
            link_selector: "a[href*='/jobs/listing/']"  # optional CSS selector
            max_jobs: 50                                 # optional cap
            delay: 0.5                                   # seconds between requests

    Extraction strategy (per job page):
      1. JSON-LD JobPosting schema — cleanest when available
      2. HTML heuristics — title from <h1>/<title>, description from
         <main>/<article>/content containers
    """

    def fetch_jobs(self) -> list[NormalizedJob]:
        url = self.conn_cfg.get("url", "")
        if not url:
            logger.warning("Site connector requires 'url' in config.")
            return []

        max_jobs = self.conn_cfg.get("max_jobs", DEFAULT_MAX_JOBS)
        delay = self.conn_cfg.get("delay", REQUEST_DELAY)
        link_selector = self.conn_cfg.get("link_selector", "")

        # Phase 1: Discover job links from the listing page
        logger.info("Fetching listing page: %s", url)
        listing_html = self._fetch_page(url)
        if listing_html is None:
            return []

        soup = BeautifulSoup(listing_html, "html.parser")

        # Check listing page for JSON-LD with multiple JobPostings
        ld_jobs = self._extract_jsonld_jobs(soup, url)
        if ld_jobs:
            logger.info(
                "Found %d jobs via JSON-LD on listing page", len(ld_jobs)
            )
            return ld_jobs[:max_jobs]

        # Discover individual job links
        job_urls = self._discover_job_links(soup, url, link_selector)
        if not job_urls:
            logger.warning("No job links found on %s", url)
            return []

        logger.info("Discovered %d job links on %s", len(job_urls), url)
        job_urls = job_urls[:max_jobs]

        # Phase 2: Extract job details from each page
        jobs: list[NormalizedJob] = []
        for i, job_url in enumerate(job_urls):
            if i > 0 and delay:
                time.sleep(delay)

            logger.debug("Scraping job %d/%d: %s", i + 1, len(job_urls), job_url)
            job = self._extract_job(job_url)
            if job:
                jobs.append(job)

        logger.info("Scraped %d jobs from %s", len(jobs), url)
        return jobs

    # ── HTTP ───────────────────────────────────────────────────────

    def _fetch_page(self, url: str) -> str | None:
        """Fetch a page, following redirects. Returns HTML or None."""
        try:
            resp = httpx.get(
                url,
                timeout=30,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; MyScout/0.1; "
                        "+https://github.com/local-tool)"
                    ),
                },
            )
            if resp.status_code == 404:
                logger.warning("Page not found (404): %s", url)
                return None
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as e:
            logger.error("Failed to fetch %s: %s", url, e)
            return None

    # ── Link Discovery ─────────────────────────────────────────────

    def _discover_job_links(
        self, soup: BeautifulSoup, base_url: str, link_selector: str
    ) -> list[str]:
        """Find links to individual job postings on a listing page."""
        if link_selector:
            anchors = soup.select(link_selector)
        else:
            anchors = soup.find_all("a", href=True)

        base_domain = urlparse(base_url).netloc
        seen: set[str] = set()
        job_urls: list[str] = []

        for a in anchors:
            href = a.get("href", "")
            if not href:
                continue

            full_url = urljoin(base_url, href)
            # Strip fragment and query for dedup
            parsed = urlparse(full_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            if clean_url in seen:
                continue

            # Skip external links, non-job links, and noise
            if parsed.netloc and parsed.netloc != base_domain:
                # Allow links to known ATS domains
                if not _is_ats_domain(parsed.netloc):
                    continue

            if _SKIP_PATTERNS.search(full_url):
                continue

            # If no custom selector, require link to look like a job link
            if not link_selector and not _JOB_LINK_RE.search(full_url):
                continue

            seen.add(clean_url)
            job_urls.append(full_url)

        return job_urls

    # ── Job Extraction ─────────────────────────────────────────────

    def _extract_job(self, url: str) -> NormalizedJob | None:
        """Extract a single job posting from a URL."""
        html = self._fetch_page(url)
        if html is None:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Try JSON-LD first
        ld_jobs = self._extract_jsonld_jobs(soup, url)
        if ld_jobs:
            return ld_jobs[0]

        # Fall back to HTML heuristics
        return self._extract_from_html(soup, url)

    def _extract_from_html(self, soup: BeautifulSoup, url: str) -> NormalizedJob | None:
        """Extract job details from HTML using heuristics."""
        title = _extract_title(soup)

        if not title:
            logger.debug("No title found on %s, skipping", url)
            return None

        # Description — find main content container
        description = self._extract_description(soup)

        # Location — look for common patterns
        location = self._extract_location(soup)

        # Generate a stable external_id from the URL path
        external_id = urlparse(url).path.strip("/").replace("/", "-") or url

        remote_type = None
        if location and "remote" in location.lower():
            remote_type = "remote"

        return NormalizedJob(
            source="site",
            external_id=external_id,
            url=url,
            company=self.company,
            title=title,
            location=location,
            remote_type=remote_type,
            description=description,
            date_posted=None,
        )

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description text from common content containers."""
        # Try progressively broader selectors
        selectors = [
            "[class*='description']",
            "[class*='posting']",
            "[class*='content']",
            "[id*='content']",
            "article",
            "main",
            "[role='main']",
        ]
        content_el = None
        for sel in selectors:
            content_el = soup.select_one(sel)
            if content_el:
                break

        if content_el is None:
            content_el = soup.find("body")

        if content_el is None:
            return ""

        # Remove noise
        for tag in content_el.find_all(
            ["nav", "footer", "script", "style", "header", "iframe", "noscript"]
        ):
            tag.decompose()

        return content_el.get_text(separator="\n", strip=True)

    def _extract_location(self, soup: BeautifulSoup) -> str | None:
        """Try to find a location string from common patterns."""
        # 1. Semantic attributes and CSS classes
        for sel in [
            "[itemprop='jobLocation']",
            "[data-testid*='location']",
            "[class*='location']",
            "[class*='Location']",
        ]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) < 200:
                    return text

        # 2. Label-based: find exact labels like "Office locations", "Location",
        #    then grab sibling/child text from the same container.
        _label_exact = [
            re.compile(r"^(Office\s+)?locations?$", re.I),
            re.compile(r"^Remote\s+locations?$", re.I),
            re.compile(r"^Location$", re.I),
            re.compile(r"^Where$", re.I),
        ]
        for label_re in _label_exact:
            label_el = soup.find(string=label_re)
            if not label_el:
                continue
            parent = label_el.parent
            if not parent:
                continue
            container = parent.parent
            if not container:
                continue
            # Collect sibling text that isn't the label
            texts = []
            for child in container.children:
                if hasattr(child, "get_text"):
                    t = child.get_text(strip=True)
                    if t and not label_re.match(t):
                        texts.append(t)
            cleaned = ", ".join(texts)
            if cleaned and len(cleaned) < 200:
                return cleaned

        # 3. Meta tags
        meta = soup.find("meta", attrs={"name": "location"})
        if meta and meta.get("content"):
            return meta["content"]

        return None

    # ── JSON-LD Extraction ─────────────────────────────────────────

    def _extract_jsonld_jobs(
        self, soup: BeautifulSoup, page_url: str
    ) -> list[NormalizedJob]:
        """Extract JobPosting objects from JSON-LD script tags."""
        jobs: list[NormalizedJob] = []

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            postings = _find_job_postings(data)
            for p in postings:
                job = self._jsonld_to_normalized(p, page_url)
                if job:
                    jobs.append(job)

        return jobs

    def _jsonld_to_normalized(
        self, ld: dict[str, Any], page_url: str
    ) -> NormalizedJob | None:
        """Convert a JSON-LD JobPosting to NormalizedJob."""
        title = ld.get("title", "")
        if not title:
            return None

        # Company
        org = ld.get("hiringOrganization", {})
        company = self.company
        if isinstance(org, dict):
            company = org.get("name", self.company)

        # URL
        url = ld.get("url", page_url)

        # Location
        location = None
        remote_type = None
        job_loc = ld.get("jobLocation")
        if isinstance(job_loc, dict):
            addr = job_loc.get("address", {})
            if isinstance(addr, dict):
                parts = [
                    addr.get("addressLocality", ""),
                    addr.get("addressRegion", ""),
                    addr.get("addressCountry", ""),
                ]
                location = ", ".join(p for p in parts if p)
        elif isinstance(job_loc, list):
            locs = []
            for loc in job_loc:
                if isinstance(loc, dict):
                    addr = loc.get("address", {})
                    if isinstance(addr, dict):
                        parts = [
                            addr.get("addressLocality", ""),
                            addr.get("addressRegion", ""),
                        ]
                        locs.append(", ".join(p for p in parts if p))
            location = " | ".join(locs) if locs else None

        # Remote
        loc_type = ld.get("jobLocationType", "")
        if loc_type and "remote" in str(loc_type).lower():
            remote_type = "remote"
        elif location and "remote" in location.lower():
            remote_type = "remote"

        # Employment type
        emp_type = ld.get("employmentType", "")
        employment_type = None
        if isinstance(emp_type, str):
            employment_type = emp_type.lower().replace("_", "-")
        elif isinstance(emp_type, list) and emp_type:
            employment_type = emp_type[0].lower().replace("_", "-")

        # Description
        description = ld.get("description", "")

        # Date
        date_posted = None
        dp = ld.get("datePosted", "")
        if dp:
            try:
                date_posted = datetime.fromisoformat(dp.replace("Z", "+00:00"))
                if date_posted.tzinfo is None:
                    date_posted = date_posted.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Salary
        comp_min = None
        comp_max = None
        comp_currency = None
        salary = ld.get("baseSalary", {})
        if isinstance(salary, dict):
            comp_currency = salary.get("currency")
            value = salary.get("value", {})
            if isinstance(value, dict):
                comp_min = _to_float(value.get("minValue"))
                comp_max = _to_float(value.get("maxValue"))
                if comp_min is None and comp_max is None:
                    comp_min = _to_float(value.get("value"))
                    comp_max = comp_min

        # External ID from URL path or identifier
        external_id = ld.get("identifier", {})
        if isinstance(external_id, dict):
            external_id = external_id.get("value", "")
        if not external_id:
            external_id = urlparse(url).path.strip("/").replace("/", "-") or url

        return NormalizedJob(
            source="site",
            external_id=str(external_id),
            url=url,
            company=company,
            title=title,
            location=location,
            remote_type=remote_type,
            employment_type=employment_type,
            description=description,
            date_posted=date_posted,
            comp_min=comp_min,
            comp_max=comp_max,
            comp_currency=comp_currency,
        )


# ── Helpers ────────────────────────────────────────────────────────


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract job title using a priority cascade.

    1. <title> tag (usually most reliable on job pages)
    2. <h1> inside main/article content area (avoids nav h1s)
    3. First <h1> on the page (last resort)
    """
    # Try <title> first — clean up common noise suffixes
    title_tag = soup.find("title")
    if title_tag:
        raw = title_tag.get_text(strip=True)
        # Strip trailing noise like "... - Careers", "... | Company Name"
        # Only strip the LAST segment if it looks like filler (Careers, Jobs, etc.)
        noise_re = re.compile(
            r"\s*[|\-—·]\s*"
            r"(Careers?|Jobs?|Hiring|Open\s+Positions?|Work\s+with\s+us)$",
            re.IGNORECASE,
        )
        raw = noise_re.sub("", raw).strip()
        if raw:
            return raw

    # Try <h1> inside a content container (skips logo/nav h1s)
    for sel in ["main h1", "article h1", "[role='main'] h1",
                "[class*='content'] h1", "[class*='posting'] h1"]:
        h1 = soup.select_one(sel)
        if h1:
            text = h1.get_text(strip=True)
            if text:
                return text

    # Fallback: first h1
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return ""


def _find_job_postings(data: Any) -> list[dict[str, Any]]:
    """Recursively find all JobPosting objects in JSON-LD data."""
    results: list[dict[str, Any]] = []

    if isinstance(data, dict):
        if data.get("@type") == "JobPosting":
            results.append(data)
        # Check @graph arrays
        if "@graph" in data:
            results.extend(_find_job_postings(data["@graph"]))
    elif isinstance(data, list):
        for item in data:
            results.extend(_find_job_postings(item))

    return results


def _to_float(val: Any) -> float | None:
    """Safely convert a value to float."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _is_ats_domain(domain: str) -> bool:
    """Check if a domain is a known ATS platform (allow cross-domain links)."""
    ats_domains = {
        "boards.greenhouse.io",
        "jobs.lever.co",
        "jobs.ashbyhq.com",
        "apply.workable.com",
        "jobs.smartrecruiters.com",
        "careers.icims.com",
        "myworkdayjobs.com",
    }
    return any(ats in domain for ats in ats_domains)
