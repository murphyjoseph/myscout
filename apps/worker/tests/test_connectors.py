"""Tests for connector parsing logic — verifies JSON→NormalizedJob conversion.

Each test mocks httpx.get with realistic fixture data from each API, then
checks that the connector correctly extracts and normalizes all fields.
No HTTP calls are made.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from myscout.connectors.base import NormalizedJob


# ── Fixtures ─────────────────────────────────────────────────────────

LEVER_FIXTURE = [
    {
        "id": "abc-123",
        "text": "Senior Software Engineer",
        "hostedUrl": "https://jobs.lever.co/company/abc-123",
        "categories": {
            "location": "Remote, US",
            "commitment": "Full-time",
        },
        "createdAt": 1709683200000,  # 2024-03-06T00:00:00Z
        "lists": [
            {"text": "Requirements", "content": "5+ years of experience"},
            {"text": "Stack", "content": "TypeScript, React, Node.js"},
        ],
        "descriptionPlain": "fallback description",
    },
]

GREENHOUSE_FIXTURE = {
    "jobs": [
        {
            "id": 12345,
            "title": "Backend Engineer",
            "location": {"name": "New York, NY"},
            "absolute_url": "https://boards.greenhouse.io/company/jobs/12345",
            "updated_at": "2024-03-06T12:00:00Z",
            "content": "<p>Build APIs with Python and FastAPI.</p>",
        },
        {
            "id": 12346,
            "title": "DevOps Engineer",
            "location": {"name": "Remote"},
            "absolute_url": "https://boards.greenhouse.io/company/jobs/12346",
            "updated_at": "2024-03-05T09:00:00Z",
            "content": "Manage Kubernetes clusters.",
        },
    ]
}

ASHBY_FIXTURE = {
    "jobs": [
        {
            "id": "ash-001",
            "title": "Product Designer",
            "jobUrl": "https://jobs.ashbyhq.com/company/ash-001",
            "location": "San Francisco, CA",
            "workplaceType": "Hybrid",
            "isRemote": False,
            "isListed": True,
            "employmentType": "FullTime",
            "publishedAt": "2024-03-06T18:30:00.000Z",
            "descriptionHtml": "<h2>Role</h2><p>Design product features.</p>",
        },
        {
            "id": "ash-002",
            "title": "Unlisted Role",
            "jobUrl": "https://jobs.ashbyhq.com/company/ash-002",
            "isListed": False,
            "descriptionHtml": "Should be skipped",
        },
        {
            "id": "ash-003",
            "title": "Remote SRE",
            "jobUrl": "https://jobs.ashbyhq.com/company/ash-003",
            "location": "Anywhere",
            "isRemote": True,
            "isListed": True,
            "employmentType": "Contract",
            "publishedAt": "2024-03-01T00:00:00.000Z",
            "descriptionPlain": "Plain text fallback",
        },
    ]
}

REMOTIVE_FIXTURE = {
    "jobs": [
        {
            "id": 9001,
            "title": "Fullstack Developer",
            "company_name": "RemoteCo",
            "url": "https://remotive.com/remote-jobs/9001",
            "candidate_required_location": "Worldwide",
            "job_type": "full_time",
            "publication_date": "2024-03-06T15:00:00",
            "description": "<p>Work on our SaaS platform.</p>",
        },
        {
            "id": 9002,
            "title": "Intern Engineer",
            "company_name": "StartupABC",
            "url": "https://remotive.com/remote-jobs/9002",
            "candidate_required_location": "US only",
            "job_type": "internship",
            "publication_date": "2024-03-04T10:00:00",
            "description": "Summer internship program.",
        },
    ]
}


def _mock_response(json_data, status_code=200):
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# ── Lever ────────────────────────────────────────────────────────────


class TestLeverConnector:
    @patch("myscout.connectors.lever.httpx.get")
    def test_parses_basic_fields(self, mock_get):
        from myscout.connectors.lever import LeverConnector

        mock_get.return_value = _mock_response(LEVER_FIXTURE)
        conn = LeverConnector("TestCo", {"slug": "testco"}, {})
        jobs = conn.fetch_jobs()

        assert len(jobs) == 1
        j = jobs[0]
        assert j.source == "lever"
        assert j.external_id == "abc-123"
        assert j.title == "Senior Software Engineer"
        assert j.company == "TestCo"
        assert j.url == "https://jobs.lever.co/company/abc-123"

    @patch("myscout.connectors.lever.httpx.get")
    def test_parses_location_and_remote(self, mock_get):
        from myscout.connectors.lever import LeverConnector

        mock_get.return_value = _mock_response(LEVER_FIXTURE)
        conn = LeverConnector("TestCo", {"slug": "testco"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].location == "Remote, US"
        assert jobs[0].remote_type == "remote"

    @patch("myscout.connectors.lever.httpx.get")
    def test_parses_employment_type(self, mock_get):
        from myscout.connectors.lever import LeverConnector

        mock_get.return_value = _mock_response(LEVER_FIXTURE)
        conn = LeverConnector("TestCo", {"slug": "testco"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].employment_type == "full-time"

    @patch("myscout.connectors.lever.httpx.get")
    def test_parses_date_from_millis(self, mock_get):
        from myscout.connectors.lever import LeverConnector

        mock_get.return_value = _mock_response(LEVER_FIXTURE)
        conn = LeverConnector("TestCo", {"slug": "testco"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].date_posted is not None
        assert jobs[0].date_posted.year == 2024

    @patch("myscout.connectors.lever.httpx.get")
    def test_assembles_description_from_lists(self, mock_get):
        from myscout.connectors.lever import LeverConnector

        mock_get.return_value = _mock_response(LEVER_FIXTURE)
        conn = LeverConnector("TestCo", {"slug": "testco"}, {})
        jobs = conn.fetch_jobs()

        desc = jobs[0].description
        assert "Requirements" in desc
        assert "TypeScript" in desc

    @patch("myscout.connectors.lever.httpx.get")
    def test_404_returns_empty(self, mock_get):
        from myscout.connectors.lever import LeverConnector

        mock_get.return_value = _mock_response({}, status_code=404)
        conn = LeverConnector("TestCo", {"slug": "nobody"}, {})
        jobs = conn.fetch_jobs()
        assert jobs == []

    @patch("myscout.connectors.lever.httpx.get")
    def test_nonremote_location(self, mock_get):
        from myscout.connectors.lever import LeverConnector

        fixture = [{
            **LEVER_FIXTURE[0],
            "categories": {"location": "San Francisco, CA", "commitment": ""},
        }]
        mock_get.return_value = _mock_response(fixture)
        conn = LeverConnector("TestCo", {"slug": "testco"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].location == "San Francisco, CA"
        assert jobs[0].remote_type is None


# ── Greenhouse ───────────────────────────────────────────────────────


class TestGreenhouseConnector:
    @patch("myscout.connectors.greenhouse.httpx.get")
    def test_parses_multiple_jobs(self, mock_get):
        from myscout.connectors.greenhouse import GreenhouseConnector

        mock_get.return_value = _mock_response(GREENHOUSE_FIXTURE)
        conn = GreenhouseConnector("ACME", {"slug": "acme"}, {})
        jobs = conn.fetch_jobs()

        assert len(jobs) == 2
        assert jobs[0].title == "Backend Engineer"
        assert jobs[1].title == "DevOps Engineer"

    @patch("myscout.connectors.greenhouse.httpx.get")
    def test_parses_location_name(self, mock_get):
        from myscout.connectors.greenhouse import GreenhouseConnector

        mock_get.return_value = _mock_response(GREENHOUSE_FIXTURE)
        conn = GreenhouseConnector("ACME", {"slug": "acme"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].location == "New York, NY"
        assert jobs[0].remote_type is None

    @patch("myscout.connectors.greenhouse.httpx.get")
    def test_detects_remote_in_location(self, mock_get):
        from myscout.connectors.greenhouse import GreenhouseConnector

        mock_get.return_value = _mock_response(GREENHOUSE_FIXTURE)
        conn = GreenhouseConnector("ACME", {"slug": "acme"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[1].remote_type == "remote"

    @patch("myscout.connectors.greenhouse.httpx.get")
    def test_parses_id_as_string(self, mock_get):
        from myscout.connectors.greenhouse import GreenhouseConnector

        mock_get.return_value = _mock_response(GREENHOUSE_FIXTURE)
        conn = GreenhouseConnector("ACME", {"slug": "acme"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].external_id == "12345"
        assert isinstance(jobs[0].external_id, str)

    @patch("myscout.connectors.greenhouse.httpx.get")
    def test_parses_iso_date(self, mock_get):
        from myscout.connectors.greenhouse import GreenhouseConnector

        mock_get.return_value = _mock_response(GREENHOUSE_FIXTURE)
        conn = GreenhouseConnector("ACME", {"slug": "acme"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].date_posted.year == 2024
        assert jobs[0].date_posted.month == 3

    @patch("myscout.connectors.greenhouse.httpx.get")
    def test_preserves_html_content(self, mock_get):
        from myscout.connectors.greenhouse import GreenhouseConnector

        mock_get.return_value = _mock_response(GREENHOUSE_FIXTURE)
        conn = GreenhouseConnector("ACME", {"slug": "acme"}, {})
        jobs = conn.fetch_jobs()

        assert "<p>" in jobs[0].description

    @patch("myscout.connectors.greenhouse.httpx.get")
    def test_404_returns_empty(self, mock_get):
        from myscout.connectors.greenhouse import GreenhouseConnector

        mock_get.return_value = _mock_response({}, status_code=404)
        conn = GreenhouseConnector("ACME", {"slug": "nope"}, {})
        assert conn.fetch_jobs() == []


# ── Ashby ────────────────────────────────────────────────────────────


class TestAshbyConnector:
    @patch("myscout.connectors.ashby.httpx.get")
    def test_skips_unlisted_jobs(self, mock_get):
        from myscout.connectors.ashby import AshbyConnector

        mock_get.return_value = _mock_response(ASHBY_FIXTURE)
        conn = AshbyConnector("Ramp", {"slug": "ramp"}, {})
        jobs = conn.fetch_jobs()

        # 3 in fixture, 1 unlisted → 2 returned
        assert len(jobs) == 2
        titles = [j.title for j in jobs]
        assert "Unlisted Role" not in titles

    @patch("myscout.connectors.ashby.httpx.get")
    def test_hybrid_workplace_type(self, mock_get):
        from myscout.connectors.ashby import AshbyConnector

        mock_get.return_value = _mock_response(ASHBY_FIXTURE)
        conn = AshbyConnector("Ramp", {"slug": "ramp"}, {})
        jobs = conn.fetch_jobs()

        designer = next(j for j in jobs if "Designer" in j.title)
        assert designer.remote_type == "hybrid"

    @patch("myscout.connectors.ashby.httpx.get")
    def test_is_remote_flag_overrides(self, mock_get):
        from myscout.connectors.ashby import AshbyConnector

        mock_get.return_value = _mock_response(ASHBY_FIXTURE)
        conn = AshbyConnector("Ramp", {"slug": "ramp"}, {})
        jobs = conn.fetch_jobs()

        sre = next(j for j in jobs if "SRE" in j.title)
        assert sre.remote_type == "remote"

    @patch("myscout.connectors.ashby.httpx.get")
    def test_employment_type_mapping(self, mock_get):
        from myscout.connectors.ashby import AshbyConnector

        mock_get.return_value = _mock_response(ASHBY_FIXTURE)
        conn = AshbyConnector("Ramp", {"slug": "ramp"}, {})
        jobs = conn.fetch_jobs()

        designer = next(j for j in jobs if "Designer" in j.title)
        sre = next(j for j in jobs if "SRE" in j.title)
        assert designer.employment_type == "full-time"
        assert sre.employment_type == "contract"

    @patch("myscout.connectors.ashby.httpx.get")
    def test_prefers_html_description(self, mock_get):
        from myscout.connectors.ashby import AshbyConnector

        mock_get.return_value = _mock_response(ASHBY_FIXTURE)
        conn = AshbyConnector("Ramp", {"slug": "ramp"}, {})
        jobs = conn.fetch_jobs()

        designer = next(j for j in jobs if "Designer" in j.title)
        assert "<h2>" in designer.description

    @patch("myscout.connectors.ashby.httpx.get")
    def test_falls_back_to_plain_description(self, mock_get):
        from myscout.connectors.ashby import AshbyConnector

        mock_get.return_value = _mock_response(ASHBY_FIXTURE)
        conn = AshbyConnector("Ramp", {"slug": "ramp"}, {})
        jobs = conn.fetch_jobs()

        sre = next(j for j in jobs if "SRE" in j.title)
        assert sre.description == "Plain text fallback"

    @patch("myscout.connectors.ashby.httpx.get")
    def test_parses_iso_date(self, mock_get):
        from myscout.connectors.ashby import AshbyConnector

        mock_get.return_value = _mock_response(ASHBY_FIXTURE)
        conn = AshbyConnector("Ramp", {"slug": "ramp"}, {})
        jobs = conn.fetch_jobs()

        designer = next(j for j in jobs if "Designer" in j.title)
        assert designer.date_posted.year == 2024
        assert designer.date_posted.month == 3
        assert designer.date_posted.day == 6

    @patch("myscout.connectors.ashby.httpx.get")
    def test_404_returns_empty(self, mock_get):
        from myscout.connectors.ashby import AshbyConnector

        mock_get.return_value = _mock_response({}, status_code=404)
        conn = AshbyConnector("Ramp", {"slug": "nope"}, {})
        assert conn.fetch_jobs() == []


# ── Remotive ─────────────────────────────────────────────────────────


class TestRemotiveConnector:
    @patch("myscout.connectors.remotive.httpx.get")
    def test_parses_jobs(self, mock_get):
        from myscout.connectors.remotive import RemotiveConnector

        mock_get.return_value = _mock_response(REMOTIVE_FIXTURE)
        conn = RemotiveConnector("Remotive", {"category": "software-dev"}, {})
        jobs = conn.fetch_jobs()

        assert len(jobs) == 2

    @patch("myscout.connectors.remotive.httpx.get")
    def test_all_jobs_are_remote(self, mock_get):
        from myscout.connectors.remotive import RemotiveConnector

        mock_get.return_value = _mock_response(REMOTIVE_FIXTURE)
        conn = RemotiveConnector("Remotive", {"category": "software-dev"}, {})
        jobs = conn.fetch_jobs()

        assert all(j.remote_type == "remote" for j in jobs)

    @patch("myscout.connectors.remotive.httpx.get")
    def test_company_from_api_not_constructor(self, mock_get):
        from myscout.connectors.remotive import RemotiveConnector

        mock_get.return_value = _mock_response(REMOTIVE_FIXTURE)
        conn = RemotiveConnector("Remotive", {"category": "software-dev"}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].company == "RemoteCo"
        assert jobs[1].company == "StartupABC"

    @patch("myscout.connectors.remotive.httpx.get")
    def test_employment_type_mapping(self, mock_get):
        from myscout.connectors.remotive import RemotiveConnector

        mock_get.return_value = _mock_response(REMOTIVE_FIXTURE)
        conn = RemotiveConnector("Remotive", {}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].employment_type == "full-time"
        assert jobs[1].employment_type == "internship"

    @patch("myscout.connectors.remotive.httpx.get")
    def test_id_converted_to_string(self, mock_get):
        from myscout.connectors.remotive import RemotiveConnector

        mock_get.return_value = _mock_response(REMOTIVE_FIXTURE)
        conn = RemotiveConnector("Remotive", {}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].external_id == "9001"
        assert isinstance(jobs[0].external_id, str)

    @patch("myscout.connectors.remotive.httpx.get")
    def test_parses_location(self, mock_get):
        from myscout.connectors.remotive import RemotiveConnector

        mock_get.return_value = _mock_response(REMOTIVE_FIXTURE)
        conn = RemotiveConnector("Remotive", {}, {})
        jobs = conn.fetch_jobs()

        assert jobs[0].location == "Worldwide"
        assert jobs[1].location == "US only"

    @patch("myscout.connectors.remotive.httpx.get")
    def test_source_is_remotive(self, mock_get):
        from myscout.connectors.remotive import RemotiveConnector

        mock_get.return_value = _mock_response(REMOTIVE_FIXTURE)
        conn = RemotiveConnector("Remotive", {}, {})
        jobs = conn.fetch_jobs()

        assert all(j.source == "remotive" for j in jobs)
