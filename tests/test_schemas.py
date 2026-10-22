import pytest
from pydantic import ValidationError

from core.schemas import TriagedGap, LegitimacyAssessment
from helpers import make_fit, FIT_CATEGORY_MAXES

# --- TriagedGap ---


def _make_gap(triage_level: str) -> TriagedGap:
    return TriagedGap(
        skill="Docker",
        frequency_in_postings=2,
        triage_level=triage_level,
        recommendation="Complete a Docker tutorial",
    )


def test_triage_level_rejects_unknown_level():
    with pytest.raises(ValidationError):
        _make_gap("Long term")


@pytest.mark.parametrize(
    "level",
    [
        "Resume update",
        "Short-term",
        "Medium-term",
        "Long-term",
    ],
)
def test_triage_level_accepts_valid_level(level):
    gap = _make_gap(level)
    assert gap.triage_level == level


# --- LegitimacyAssessment ---


def _make_assessment(
    verdict: str = "Green", confidence_score: int = 50
) -> LegitimacyAssessment:
    return LegitimacyAssessment(
        verdict=verdict,
        confidence_score=confidence_score,
        signals=[],
        recommendation="Proceed with the application",
    )


def test_assessment_rejects_unknown_verdict():
    with pytest.raises(ValidationError):
        _make_assessment(verdict="green")


@pytest.mark.parametrize("invalid_score", [-1, 101])
def test_assessment_rejects_out_of_range_confidence(invalid_score):
    with pytest.raises(ValidationError):
        _make_assessment(confidence_score=invalid_score)


@pytest.mark.parametrize("score", [0, 100])
def test_assessment_accepts_valid_confidence_value(score):
    assessment = _make_assessment(confidence_score=score)
    assert assessment.confidence_score == score


@pytest.mark.parametrize(
    "verdict",
    [
        "Green",
        "Yellow",
        "Red",
    ],
)
def test_assessment_accepts_valid_verdict(verdict):
    assessment = _make_assessment(verdict)
    assert assessment.verdict == verdict


# --- FitAssessment ---


OUT_OF_BOUNDS = [
    (field, max_score + 1) for field, max_score in FIT_CATEGORY_MAXES.items()
] + [(field, -1) for field in FIT_CATEGORY_MAXES]


@pytest.mark.parametrize("field, max_score", FIT_CATEGORY_MAXES.items())
def test_fit_accepts_category_at_max(field, max_score):
    assessment = make_fit(**{field: max_score})  # Pass by field name
    assert getattr(assessment, field) == max_score


@pytest.mark.parametrize("field, out_of_bounds_score", OUT_OF_BOUNDS)
def test_fit_rejects_category_out_of_bounds(field, out_of_bounds_score):
    with pytest.raises(ValidationError):
        make_fit(**{field: out_of_bounds_score})


@pytest.mark.parametrize("field", FIT_CATEGORY_MAXES.keys())
def test_fit_accepts_category_at_zero(field):
    assessment = make_fit(**{field: 0})
    assert getattr(assessment, field) == 0
