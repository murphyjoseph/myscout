"""Tests for myscout.extraction.feature_extractor pure functions."""

import pytest
from myscout.extraction.feature_extractor import (
    extract_tech_tags,
    detect_seniority,
    extract_salary,
    detect_remote,
)


# ── extract_tech_tags ────────────────────────────────────────────


class TestExtractTechTags:
    def test_finds_common_tech(self):
        text = "We use Python and React with PostgreSQL"
        tags = extract_tech_tags(text)
        assert "python" in tags
        assert "react" in tags
        assert "postgresql" in tags

    def test_case_insensitive(self):
        tags = extract_tech_tags("TYPESCRIPT and DOCKER are required")
        assert "typescript" in tags
        assert "docker" in tags

    def test_returns_sorted_unique(self):
        text = "python python python react"
        tags = extract_tech_tags(text)
        assert tags == sorted(set(tags))
        assert tags.count("python") == 1

    def test_empty_text(self):
        assert extract_tech_tags("") == []

    def test_no_matches(self):
        assert extract_tech_tags("We need a great communicator") == []

    def test_partial_match_in_word(self):
        # "go" should match as a substring in text
        tags = extract_tech_tags("Experience with go and rust")
        assert "go" in tags
        assert "rust" in tags

    def test_nextjs_variants(self):
        assert "nextjs" in extract_tech_tags("Built with NextJS")
        assert "next.js" in extract_tech_tags("Experience with Next.js")


# ── detect_seniority ────────────────────────────────────────────


class TestDetectSeniority:
    @pytest.mark.parametrize(
        "title, expected",
        [
            ("Senior Software Engineer", "senior"),
            ("Sr. Frontend Developer", "senior"),
            ("Junior Developer", "junior"),
            ("Jr. Engineer", "junior"),
            ("Staff Engineer", "staff"),
            ("Principal Architect", "principal"),
            ("Engineering Lead", "lead"),
            ("Engineering Manager", "lead"),
            ("Director of Engineering", "lead"),
            ("Intern - Software Engineering", "intern"),
            ("Entry-Level Software Developer", "junior"),
            ("Mid-Level Backend Engineer", "mid"),
        ],
    )
    def test_detects_level(self, title: str, expected: str):
        assert detect_seniority(title) == expected

    def test_no_seniority(self):
        assert detect_seniority("Software Engineer") is None

    def test_case_insensitive(self):
        assert detect_seniority("SENIOR ENGINEER") == "senior"


# ── extract_salary ──────────────────────────────────────────────


class TestExtractSalary:
    def test_range_with_dash(self):
        assert extract_salary("$150,000 - $200,000") == (150_000, 200_000)

    def test_range_with_to(self):
        assert extract_salary("$150,000 to $200,000") == (150_000, 200_000)

    def test_k_suffix(self):
        mn, mx = extract_salary("$150k-$200k")
        assert mn == 150_000
        assert mx == 200_000

    def test_single_value(self):
        mn, mx = extract_salary("$180,000")
        assert mn == 180_000
        assert mx == 180_000

    def test_no_salary(self):
        assert extract_salary("Competitive compensation package") == (None, None)

    def test_empty_text(self):
        assert extract_salary("") == (None, None)

    def test_filters_unreasonable_values(self):
        # $5 shouldn't be treated as salary even after *1000
        assert extract_salary("Save $5 on your next order") == (None, None)

    def test_range_with_en_dash(self):
        mn, mx = extract_salary("$120,000\u2013$160,000")
        assert mn == 120_000
        assert mx == 160_000

    def test_embedded_in_description(self):
        text = "This role pays $140,000 - $180,000 per year. Great benefits!"
        mn, mx = extract_salary(text)
        assert mn == 140_000
        assert mx == 180_000

    def test_small_k_values(self):
        mn, mx = extract_salary("Salary: $80k - $120k")
        assert mn == 80_000
        assert mx == 120_000


# ── detect_remote ───────────────────────────────────────────────


class TestDetectRemote:
    def test_explicit_remote_type(self):
        assert detect_remote("New York", "remote") == "remote"

    def test_remote_type_takes_precedence(self):
        assert detect_remote("Remote - NYC", "hybrid") == "hybrid"

    def test_location_contains_remote(self):
        assert detect_remote("Remote - US", None) == "remote"

    def test_location_contains_hybrid(self):
        assert detect_remote("Hybrid - San Francisco", None) == "hybrid"

    def test_defaults_to_onsite(self):
        assert detect_remote("New York, NY", None) == "onsite"

    def test_none_location(self):
        assert detect_remote(None, None) == "onsite"
