import pytest

from phase3.phase3 import (
    _fit_tier_from_score,
    _normalize_fit_assessment,
    _fallback_fit_assessment,
)
from helpers import make_fit


@pytest.mark.parametrize(
    "score, expected",
    [
        (100, "Strong fit"),
        (80, "Strong fit"),
        (79, "Good fit"),
        (50, "Good fit"),
        (49, "Stretch"),
        (30, "Stretch"),
        (29, "Growth target"),
        (0, "Growth target"),
    ],
)
def test_fit_tier_from_score(score, expected):
    assert _fit_tier_from_score(score) == expected


# --- _normalize_fit_assessment ---


@pytest.mark.parametrize(
    "categories, expected_score, expected_tier",
    [
        # All categories at max: 40 + 25 + 15 + 10 + 10
        (
            {
                "core_skills_score": 40,
                "experience_relevance_score": 25,
                "experience_level_score": 15,
                "preferred_skills_score": 10,
                "education_domain_score": 10,
            },
            100,
            "Strong fit",
        ),
        # Lowest Strong fit: 40 + 20 + 10 + 5 + 5
        ({"core_skills_score": 40, "experience_relevance_score": 20}, 80, "Strong fit"),
        # Highest Good fit: 40 + 19 + 10 + 5 + 5
        ({"core_skills_score": 40, "experience_relevance_score": 19}, 79, "Good fit"),
    ],
)
def test_normalize_computes_score_from_categories(
    categories, expected_score, expected_tier
):
    fit = _normalize_fit_assessment(make_fit(**categories))

    assert fit.score == expected_score
    assert fit.tier == expected_tier


# --- _fallback_fit_assessment ---


def test_fallback_returns_stretch_with_reason():
    fit = _fallback_fit_assessment("timeout")

    assert fit.score == 35
    assert fit.tier == "Stretch"
    assert "timeout" in fit.overall_assessment
