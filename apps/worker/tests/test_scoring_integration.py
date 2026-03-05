"""Integration tests for the scoring pipeline.

Tests the full score_jobs() function with realistic mock data,
verifying that the multiplicative gate model and all additive
components interact correctly.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from myscout.scoring.scoring_engine import score_jobs


def _make_cj(
    *,
    id: int = 1,
    title: str = "Software Engineer",
    description: str = "Build things with TypeScript and React.",
    location: str = "Remote, US",
    remote_type: str = "remote",
) -> MagicMock:
    """Create a mock CanonicalJob."""
    cj = MagicMock()
    cj.id = id
    cj.title = title
    cj.description_clean = description
    cj.location = location
    cj.remote_type = remote_type
    cj.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
    return cj


def _make_feature(*, tech_tags: list[str] | None = None, seniority: str | None = None) -> MagicMock:
    f = MagicMock()
    f.tech_tags = tech_tags or []
    f.seniority = seniority
    return f


def _make_profile(
    *,
    titles: list[str] | None = None,
    exclude_titles: list[str] | None = None,
    must_have: list[str] | None = None,
    strong_plus: list[str] | None = None,
    avoid: list[str] | None = None,
    include_phrases: list[str] | None = None,
    exclude_phrases: list[str] | None = None,
    remote_allowed: list[str] | None = None,
    seniority_exclude: list[str] | None = None,
    countries_include: list[str] | None = None,
    weights: dict | None = None,
) -> dict:
    """Build a realistic profile config."""
    return {
        "profile": {
            "role_targets": {
                "titles": titles or [],
                "exclude_titles": exclude_titles or [],
                "seniority": {
                    "include": [],
                    "exclude": seniority_exclude or [],
                },
            },
            "constraints": {
                "remote": {"allowed": remote_allowed or []},
                "locations": {"include": [], "exclude": []},
                "countries": {"include": countries_include or []},
                "employment_type": {"include": []},
                "salary": {"min_usd": None},
            },
            "tech_preferences": {
                "must_have": must_have or [],
                "strong_plus": strong_plus or [],
                "avoid": avoid or [],
            },
            "keywords": {
                "include_phrases": include_phrases or [],
                "exclude_phrases": exclude_phrases or [],
            },
        },
        "scoring": {
            "weights": weights or {},
        },
    }


class TestScoringIntegration:
    """Full pipeline tests — score_jobs with mock session."""

    def _run_score(self, cj, feature, profile_cfg):
        """Run score_jobs and return the breakdown dict."""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = feature
        pv = MagicMock()
        pv.id = 1

        scores_added = []
        original_add = session.add

        def capture_add(obj):
            scores_added.append(obj)

        session.add = capture_add

        score_jobs(session, [cj], pv, profile_cfg)

        # The score object is the one added to the session
        assert len(scores_added) == 1
        return scores_added[0]

    def test_perfect_match_scores_high(self):
        cj = _make_cj(title="Senior Software Engineer")
        feature = _make_feature(tech_tags=["typescript", "react", "python"])
        profile = _make_profile(
            titles=["software engineer"],
            must_have=["typescript", "react"],
            strong_plus=["python"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_total > 40

    def test_must_have_gate_zeros_score(self):
        """Jobs with none of the must-have tech should score 0."""
        cj = _make_cj(
            title="Software Engineer",
            description="Build things with Java and Spring Boot.",
        )
        feature = _make_feature(tech_tags=["java", "spring"])
        profile = _make_profile(
            titles=["software engineer"],
            must_have=["typescript", "react"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_total == 0
        assert score_obj.score_breakdown_json["must_have_match"] == 0

    def test_partial_must_have_scales_score(self):
        """Having 50% of must-have techs should halve the score."""
        cj = _make_cj(description="We use typescript and java.")
        feature = _make_feature(tech_tags=["typescript", "java"])
        profile = _make_profile(must_have=["typescript", "react"])

        score_obj = self._run_score(cj, feature, profile)
        breakdown = score_obj.score_breakdown_json
        assert breakdown["must_have_match"] == 0.5
        # Total should be roughly half of what a full match would be
        assert 0 < score_obj.score_total < 40

    def test_title_bonus_adds_points(self):
        cj = _make_cj(title="Software Engineer")
        feature = _make_feature(tech_tags=["typescript"])
        profile = _make_profile(
            titles=["software engineer"],
            must_have=["typescript"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["title_match"] > 0

    def test_no_title_target_still_scores(self):
        """With no title targets configured, jobs should still get a score."""
        cj = _make_cj(title="Weird Title Nobody Configured")
        feature = _make_feature(tech_tags=["typescript"])
        profile = _make_profile(must_have=["typescript"])

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_total > 0

    def test_exclude_title_penalty(self):
        cj = _make_cj(title="Sales Engineer")
        feature = _make_feature(tech_tags=["typescript"])
        profile = _make_profile(
            must_have=["typescript"],
            exclude_titles=["sales"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["penalty_exclude_title"] < 0

    def test_avoid_tech_penalty(self):
        cj = _make_cj(description="We use PHP and WordPress daily.")
        feature = _make_feature(tech_tags=["php", "wordpress"])
        profile = _make_profile(
            must_have=["php"],  # So it doesn't get gated
            avoid=["wordpress"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["penalty_avoid_tech"] < 0

    def test_exclude_phrase_penalty(self):
        cj = _make_cj(description="Must have active security clearance required.")
        feature = _make_feature(tech_tags=["python"])
        profile = _make_profile(
            must_have=["python"],
            exclude_phrases=["clearance required"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["penalty_exclude_phrase"] < 0

    def test_include_phrase_bonus(self):
        cj = _make_cj(description="We love developer experience and open source.")
        feature = _make_feature(tech_tags=["typescript"])
        profile = _make_profile(
            must_have=["typescript"],
            include_phrases=["developer experience", "open source"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["include_phrase_bonus"] > 0

    def test_country_constraint_penalty(self):
        cj = _make_cj(location="Bangalore, India")
        feature = _make_feature(tech_tags=["typescript"])
        profile = _make_profile(
            must_have=["typescript"],
            countries_include=["US"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["constraint_penalty"] < 0

    def test_remote_constraint_penalty(self):
        cj = _make_cj(remote_type="onsite")
        feature = _make_feature(tech_tags=["typescript"])
        profile = _make_profile(
            must_have=["typescript"],
            remote_allowed=["remote"],
        )

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["constraint_penalty"] < 0

    def test_recency_bonus_for_fresh_job(self):
        cj = _make_cj()
        cj.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
        feature = _make_feature(tech_tags=["typescript"])
        profile = _make_profile(must_have=["typescript"])

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["recency_bonus"] > 0

    def test_no_recency_for_old_job(self):
        cj = _make_cj()
        cj.last_seen = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=60)
        feature = _make_feature(tech_tags=["typescript"])
        profile = _make_profile(must_have=["typescript"])

        score_obj = self._run_score(cj, feature, profile)
        assert score_obj.score_breakdown_json["recency_bonus"] == 0

    def test_multiple_penalties_stack(self):
        """A job with avoid tech, exclude phrases, AND wrong country should be heavily penalized."""
        cj = _make_cj(
            title="Account Executive",
            description="Sell our PHP WordPress product. Clearance required.",
            location="Mumbai, India",
            remote_type="onsite",
        )
        feature = _make_feature(tech_tags=["php", "wordpress"])
        profile = _make_profile(
            titles=["software engineer"],
            exclude_titles=["account executive"],
            must_have=["php"],  # So it passes the gate
            avoid=["wordpress"],
            exclude_phrases=["clearance required"],
            remote_allowed=["remote"],
            countries_include=["US"],
        )

        score_obj = self._run_score(cj, feature, profile)
        # Should be deeply negative due to stacked penalties
        assert score_obj.score_total < 0

    def test_empty_profile_gives_base_score(self):
        """A completely empty profile should give a non-zero base score."""
        cj = _make_cj()
        feature = _make_feature()
        profile = _make_profile()

        score_obj = self._run_score(cj, feature, profile)
        # Default base_score weight is 30
        assert score_obj.score_total > 0

    def test_no_feature_still_works(self):
        """Jobs without extracted features should still score (using text-based matching)."""
        cj = _make_cj(description="We use typescript and react extensively.")
        feature = None  # No extracted features
        profile = _make_profile(must_have=["typescript", "react"])

        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = feature
        pv = MagicMock()
        pv.id = 1

        scores_added = []
        session.add = lambda obj: scores_added.append(obj)

        score_jobs(session, [cj], pv, profile)

        assert len(scores_added) == 1
        # Must-have found in text, so score should be > 0
        assert scores_added[0].score_total > 0
