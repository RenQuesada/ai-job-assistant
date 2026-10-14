import pytest
from pydantic import ValidationError

from core.schemas import TriagedGap

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

@pytest.mark.parametrize("level", [
    "Resume update",
    "Short-term",
    "Medium-term",
    "Long-term",
])
def test_triage_level_accepts_valid_level(level):
    gap = _make_gap(level)
    assert gap.triage_level == level