"""Tests for myscout.scoring.scoring_engine pure functions."""

import pytest
from unittest.mock import MagicMock
from myscout.scoring.scoring_engine import (
    _normalize_title,
    _title_relevance,
    _must_have_ratio,
    _location_matches_country,
    _check_constraints,
)


# ── _normalize_title ────────────────────────────────────────────


class TestNormalizeTitle:
    def test_lowercases(self):
        assert _normalize_title("Senior Engineer") == "senior engineer"

    def test_strips_hyphens(self):
        assert _normalize_title("front-end") == "frontend"

    def test_strips_dots(self):
        assert _normalize_title("Sr.") == "sr"

    def test_preserves_numbers(self):
        assert _normalize_title("Level 3 Engineer") == "level 3 engineer"

    def test_strips_special_chars(self):
        # Special chars removed; spaces may not be collapsed (fine for `in` checks)
        result = _normalize_title("C++ / C# Dev!")
        assert "c" in result
        assert "dev" in result
        assert "+" not in result
        assert "#" not in result

    def test_empty_string(self):
        assert _normalize_title("") == ""


# ── _title_relevance ────────────────────────────────────────────


class TestTitleRelevance:
    def test_no_targets_returns_1(self):
        assert _title_relevance("anything", []) == 1.0

    def test_exact_match(self):
        assert _title_relevance("software engineer", ["software engineer"]) == 1.0

    def test_substring_match(self):
        assert _title_relevance("senior software engineer", ["software engineer"]) == 1.0

    def test_reverse_substring(self):
        # Job title is contained in target
        assert _title_relevance("engineer", ["software engineer"]) == 1.0

    def test_no_match(self):
        assert _title_relevance("account executive", ["software engineer"]) == 0.0

    def test_partial_word_overlap(self):
        result = _title_relevance("frontend engineer", ["software engineer"])
        # "engineer" overlaps (1/2 words) = 0.5
        assert result == pytest.approx(0.5)

    def test_normalized_match_hyphen(self):
        # "front-end" normalizes to "frontend", should match
        assert _title_relevance("front-end developer", ["frontend developer"]) == 1.0

    def test_normalized_match_dots(self):
        assert _title_relevance("sr. engineer", ["sr engineer"]) == 1.0

    def test_best_of_multiple_targets(self):
        targets = ["data scientist", "software engineer"]
        assert _title_relevance("software engineer", targets) == 1.0

    def test_case_insensitive(self):
        assert _title_relevance("Software Engineer", ["software engineer"]) == 1.0


# ── _must_have_ratio ────────────────────────────────────────────


class TestMustHaveRatio:
    def test_no_must_haves_returns_1(self):
        assert _must_have_ratio([], [], "") == 1.0

    def test_all_found_in_tags(self):
        assert _must_have_ratio(
            ["typescript", "react"],
            ["typescript", "react", "python"],
            "",
        ) == 1.0

    def test_none_found(self):
        assert _must_have_ratio(
            ["typescript", "react"], ["java", "spring"], ""
        ) == 0.0

    def test_partial_match(self):
        result = _must_have_ratio(
            ["typescript", "react"], ["typescript"], ""
        )
        assert result == pytest.approx(0.5)

    def test_found_in_full_text(self):
        result = _must_have_ratio(
            ["typescript"], [], "we use typescript daily"
        )
        assert result == 1.0

    def test_mixed_tags_and_text(self):
        result = _must_have_ratio(
            ["typescript", "react"],
            ["typescript"],
            "experience with react",
        )
        assert result == 1.0


# ── _location_matches_country ───────────────────────────────────


class TestLocationMatchesCountry:
    # US detection
    @pytest.mark.parametrize(
        "location",
        [
            "Arizona, United States",
            "Remote, US",
            "New York, NY",
            "San Francisco, CA",
            "Remote, Canada; Remote, US",
            "Remote, Americas",
            "Charlotte, NC",
            "DC, United States",
            "New York City, San Francisco, Seattle, Remote-US",
        ],
    )
    def test_us_locations_match(self, location: str):
        assert _location_matches_country(location.lower(), "US") is True

    @pytest.mark.parametrize(
        "location",
        [
            "Bangalore, India",
            "Berlin, Germany",
            "London, United Kingdom",
            "Dublin, Ireland",
            "Remote, APAC",
            "Remote - Brazil",
            "Remote, Canada",
            "Hybrid - Luxembourg",
            "Remote",
            "Distributed",
            "Manila, Philippines",
        ],
    )
    def test_non_us_locations_no_match(self, location: str):
        assert _location_matches_country(location.lower(), "US") is False

    # Other countries
    def test_uk_detection(self):
        assert _location_matches_country("london, united kingdom", "UK") is True
        assert _location_matches_country("edinburgh, scotland", "UK") is True

    def test_canada_detection(self):
        assert _location_matches_country("remote, canada", "CA") is True
        assert _location_matches_country("toronto, canada", "ca") is True

    def test_india_detection(self):
        assert _location_matches_country("bangalore, india", "IN") is True

    def test_germany_detection(self):
        assert _location_matches_country("berlin, germany", "DE") is True

    def test_full_country_name_as_input(self):
        # User can also write "United States" instead of "US"
        assert _location_matches_country(
            "arizona, united states", "united states"
        ) is True

    def test_case_insensitive_country(self):
        assert _location_matches_country("remote, us", "us") is True
        assert _location_matches_country("remote, us", "US") is True

    def test_no_false_positive_australia_for_us(self):
        # "Australia" contains "us" but should not match "US" country
        # because we use word-boundary matching
        assert _location_matches_country("perth, australia", "US") is False


# ── _check_constraints ──────────────────────────────────────────


class TestCheckConstraints:
    def _make_cj(self, **kwargs) -> MagicMock:
        cj = MagicMock()
        cj.location = kwargs.get("location", "")
        cj.remote_type = kwargs.get("remote_type", None)
        cj.comp_min = kwargs.get("comp_min", None)
        cj.comp_max = kwargs.get("comp_max", None)
        return cj

    def _make_feature(self, **kwargs) -> MagicMock:
        f = MagicMock()
        f.seniority = kwargs.get("seniority", None)
        return f

    def test_no_constraints_no_penalty(self):
        cj = self._make_cj(location="New York, NY")
        penalty = _check_constraints(cj, None, {}, {})
        assert penalty == 0.0

    def test_seniority_exclude_penalty(self):
        cj = self._make_cj()
        feature = self._make_feature(seniority="junior")
        penalty = _check_constraints(cj, feature, {}, {"exclude": ["junior"]})
        assert penalty == -50

    def test_seniority_allowed_no_penalty(self):
        cj = self._make_cj()
        feature = self._make_feature(seniority="senior")
        penalty = _check_constraints(cj, feature, {}, {"exclude": ["junior"]})
        assert penalty == 0.0

    def test_remote_not_allowed_penalty(self):
        cj = self._make_cj(remote_type="onsite")
        constraints = {"remote": {"allowed": ["remote"]}}
        penalty = _check_constraints(cj, None, constraints, {})
        assert penalty == -30

    def test_remote_allowed_no_penalty(self):
        cj = self._make_cj(remote_type="remote")
        constraints = {"remote": {"allowed": ["remote", "hybrid"]}}
        penalty = _check_constraints(cj, None, constraints, {})
        assert penalty == 0.0

    def test_location_exclude_penalty(self):
        cj = self._make_cj(location="Mumbai, India")
        constraints = {"locations": {"exclude": ["mumbai"]}}
        penalty = _check_constraints(cj, None, constraints, {})
        assert penalty == -30

    def test_country_filter_us_only(self):
        cj_us = self._make_cj(location="New York, NY")
        cj_india = self._make_cj(location="Bangalore, India")
        constraints = {"countries": {"include": ["US"]}}

        assert _check_constraints(cj_us, None, constraints, {}) == 0.0
        assert _check_constraints(cj_india, None, constraints, {}) == -100

    def test_country_filter_multiple(self):
        cj_us = self._make_cj(location="Remote, US")
        cj_uk = self._make_cj(location="London, United Kingdom")
        cj_india = self._make_cj(location="Bangalore, India")
        constraints = {"countries": {"include": ["US", "UK"]}}

        assert _check_constraints(cj_us, None, constraints, {}) == 0.0
        assert _check_constraints(cj_uk, None, constraints, {}) == 0.0
        assert _check_constraints(cj_india, None, constraints, {}) == -100

    def test_seniority_include_penalty(self):
        """Penalty when detected seniority is outside preferred levels."""
        cj = self._make_cj()
        feature = self._make_feature(seniority="junior")
        penalty = _check_constraints(cj, feature, {}, {"include": ["senior", "staff"]})
        assert penalty == -20

    def test_seniority_include_no_penalty_when_matching(self):
        cj = self._make_cj()
        feature = self._make_feature(seniority="senior")
        penalty = _check_constraints(cj, feature, {}, {"include": ["senior", "staff"]})
        assert penalty == 0.0

    def test_seniority_include_no_penalty_when_undetected(self):
        """Jobs with no detected seniority shouldn't be penalized."""
        cj = self._make_cj()
        feature = self._make_feature(seniority=None)
        penalty = _check_constraints(cj, feature, {}, {"include": ["senior"]})
        assert penalty == 0.0

    def test_seniority_include_and_exclude_stack(self):
        """Both include miss and exclude match should stack."""
        cj = self._make_cj()
        feature = self._make_feature(seniority="junior")
        seniority_cfg = {"include": ["senior"], "exclude": ["junior"]}
        penalty = _check_constraints(cj, feature, {}, seniority_cfg)
        # -50 (exclude) + -20 (include miss) = -70
        assert penalty == -70

    def test_location_include_bonus(self):
        """Bonus when job is in a preferred location."""
        cj = self._make_cj(location="Chicago, IL")
        constraints = {"locations": {"include": ["chicago"]}}
        penalty = _check_constraints(cj, None, constraints, {})
        assert penalty == 15

    def test_location_include_no_bonus_when_no_match(self):
        cj = self._make_cj(location="Austin, TX")
        constraints = {"locations": {"include": ["chicago"]}}
        penalty = _check_constraints(cj, None, constraints, {})
        assert penalty == 0.0

    def test_salary_below_minimum_penalty(self):
        """Penalty when extracted salary max is below user's minimum."""
        cj = self._make_cj(comp_min=100000, comp_max=130000)
        constraints = {"salary": {"min_usd": 150000}}
        penalty = _check_constraints(cj, None, constraints, {})
        assert penalty == -20

    def test_salary_above_minimum_no_penalty(self):
        cj = self._make_cj(comp_min=150000, comp_max=200000)
        constraints = {"salary": {"min_usd": 150000}}
        penalty = _check_constraints(cj, None, constraints, {})
        assert penalty == 0.0

    def test_salary_no_data_no_penalty(self):
        """Jobs without extracted salary shouldn't be penalized."""
        cj = self._make_cj(comp_min=None, comp_max=None)
        constraints = {"salary": {"min_usd": 150000}}
        penalty = _check_constraints(cj, None, constraints, {})
        assert penalty == 0.0

    def test_penalties_stack(self):
        cj = self._make_cj(location="Bangalore, India", remote_type="onsite")
        feature = self._make_feature(seniority="junior")
        constraints = {
            "remote": {"allowed": ["remote"]},
            "countries": {"include": ["US"]},
        }
        seniority_cfg = {"exclude": ["junior"]}
        penalty = _check_constraints(cj, feature, constraints, seniority_cfg)
        # -50 seniority + -30 remote + -100 country = -180
        assert penalty == -180
