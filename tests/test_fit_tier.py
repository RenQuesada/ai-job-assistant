import pytest
from phase3.phase3 import _fit_tier_from_score

# Decorator for multiple tests
@pytest.mark.parametrize("score, expected", [
    (100, "Strong fit"),
    (80, "Strong fit"),
    (79, "Good fit"),
    (50, "Good fit"),
    (49, "Stretch"),
    (30, "Stretch"),
    (29, "Growth target"),
    (0, "Growth target"),
])
def test_fit_tier_from_score(score, expected):
    assert _fit_tier_from_score(score) == expected