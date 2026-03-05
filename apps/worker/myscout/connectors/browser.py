from __future__ import annotations

import hashlib
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from myscout.connectors.base import JobConnector, NormalizedJob

logger = logging.getLogger(__name__)


def _extract_text(element) -> str:
    """Extract visible text from a Playwright element handle."""
    return (element.inner_text() or "").strip()


def _is_job_link(href: str, text: str) -> bool:
    """Heuristic: does this link look like a job posting?"""
    if not href:
        return False
    job_patterns = [
        r"/jobs?/", r"/careers?/", r"/positions?/", r"/openings?/",
        r"/opportunities/", r"/vacancies/", r"/apply/", r"/posting/",
        r"/job-board/", r"/job_detail/", r"/requisition/", r"/role/",
    ]
    href_lower = href.lower()
    for pattern in job_patterns:
        if re.search(pattern, href_lower):
            return True
    text_lower = text.lower()
    if any(w in text_lower for w in ["apply", "view role", "view job", "learn more"]):
        return True
    return False


def _clean_html(page) -> str:
    """Extract main content HTML from the current page."""
    selectors = [
        "[class*='description']", "[class*='posting']", "[class*='job-detail']",
        "[class*='jobDescription']", "[class*='job_description']",
        "article", "main", "[role='main']",
    ]
    for sel in selectors:
        el = page.query_selector(sel)
        if el:
            return el.inner_html()
    body = page.query_selector("body")
    return body.inner_html() if body else ""


class BrowserConnector(JobConnector):
    """Crawls career pages using a headless browser (Playwright).

    Use this for JS-heavy career sites (Workday, iCIMS, custom SPAs) where
    the httpx-based SiteConnector can't render the content. Launches a real
    Chromium browser that executes JavaScript.

    Requires: uv add playwright && uv run playwright install chromium

    Config in targets.yml:

        - company: Apple
          connectors:
          - type: browser
            url: https://jobs.apple.com/en-us/search
            crawl:
              max_pages: 50               # max job pages to visit (default 50)
              delay: 1.5                  # seconds between requests (default 1.0)
              allowed_domains:            # stay within these domains
                - jobs.apple.com
              link_selector: null         # CSS selector for job links (auto-detect if null)
              title_selector: null        # CSS selector for title on detail page
              description_selector: null  # CSS selector for description on detail page
    """

    def fetch_jobs(self) -> list[NormalizedJob]:
        start_url = self.conn_cfg.get("url", "")
        if not start_url:
            logger.warning("Browser connector for %s has no url configured", self.company)
            return []

        crawl_cfg = self.conn_cfg.get("crawl", {})
        max_pages = crawl_cfg.get("max_pages", 50)
        delay = crawl_cfg.get("delay", 1.0)
        allowed_domains = crawl_cfg.get("allowed_domains", [])
        link_selector = crawl_cfg.get("link_selector")
        title_selector = crawl_cfg.get("title_selector")
        desc_selector = crawl_cfg.get("description_selector")

        if not allowed_domains:
            parsed = urlparse(start_url)
            allowed_domains = [parsed.netloc]

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error(
                "Playwright is required for browser crawling. "
                "Install: uv add playwright && uv run playwright install chromium"
            )
            return []

        logger.info("Crawling %s for %s (max %d pages)", start_url, self.company, max_pages)

        jobs: list[NormalizedJob] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            # Step 1: Visit listing page, find job links
            try:
                page.goto(start_url, wait_until="networkidle", timeout=30000)
            except Exception:
                logger.warning("Timeout loading %s, proceeding with partial content", start_url)

            page.wait_for_timeout(2000)

            job_urls: list[str] = []
            if link_selector:
                links = page.query_selector_all(link_selector)
            else:
                links = page.query_selector_all("a[href]")

            for link in links:
                href = link.get_attribute("href") or ""
                text = _extract_text(link)
                full_url = urljoin(start_url, href)

                parsed = urlparse(full_url)
                if parsed.netloc not in allowed_domains:
                    continue

                if link_selector or _is_job_link(full_url, text):
                    if full_url not in job_urls:
                        job_urls.append(full_url)

            logger.info("Found %d job links on listing page", len(job_urls))
            job_urls = job_urls[:max_pages]

            # Step 2: Visit each job page, extract data
            for i, job_url in enumerate(job_urls):
                try:
                    time.sleep(delay)
                    page.goto(job_url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(1000)

                    # Title
                    title = ""
                    if title_selector:
                        el = page.query_selector(title_selector)
                        if el:
                            title = _extract_text(el)
                    if not title:
                        for sel in ["h1", "[class*='title']", "[class*='heading']"]:
                            el = page.query_selector(sel)
                            if el:
                                title = _extract_text(el)
                                if title:
                                    break

                    # Description
                    description = ""
                    if desc_selector:
                        el = page.query_selector(desc_selector)
                        if el:
                            description = el.inner_html()
                    if not description:
                        description = _clean_html(page)

                    # Location (best effort)
                    location = None
                    for sel in [
                        "[class*='location']", "[class*='Location']",
                        "[data-testid*='location']", "[aria-label*='location']",
                    ]:
                        el = page.query_selector(sel)
                        if el:
                            location = _extract_text(el)
                            if location:
                                break

                    # Remote detection
                    remote_type = None
                    page_text = (page.inner_text("body") or "").lower()
                    if "remote" in (location or "").lower() or "remote" in page_text[:500]:
                        remote_type = "remote"
                    elif "hybrid" in (location or "").lower() or "hybrid" in page_text[:500]:
                        remote_type = "hybrid"

                    if not title:
                        logger.debug("Skipping %s — no title found", job_url)
                        continue

                    external_id = hashlib.sha256(job_url.encode()).hexdigest()[:16]

                    jobs.append(NormalizedJob(
                        source="browser",
                        external_id=external_id,
                        url=job_url,
                        company=self.company,
                        title=title,
                        location=location,
                        remote_type=remote_type,
                        description=description,
                        date_posted=datetime.now(timezone.utc),
                    ))

                    if (i + 1) % 10 == 0:
                        logger.info("Crawled %d/%d job pages", i + 1, len(job_urls))

                except Exception:
                    logger.warning("Failed to crawl %s", job_url, exc_info=True)
                    continue

            browser.close()

        logger.info("Crawled %d jobs from %s", len(jobs), self.company)
        return jobs
