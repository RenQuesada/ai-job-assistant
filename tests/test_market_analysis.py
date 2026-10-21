import asyncio
import pytest
from core.schemas import JobPosting
from phase1.market_analysis import compute_skill_frequencies, generate_market_analysis

# --- compute_skill_frequencies ---

def _make_posting(required: list[str], preferred: list[str] | None = None) -> JobPosting:
    # Fill unused fields with placeholders
    return JobPosting(
        job_title="Test Role",
        company="TestCo",
        required_skills=required,
        preferred_skills=preferred or [],
        experience_level="Entry-level",
        responsibilities=[],
    )

def test_counts_skill_across_postings():
    postings = [
        _make_posting(["Python", "SQL"]),
        _make_posting(["Python", "Docker"]),
        _make_posting(["Python"]),
    ]

    result = compute_skill_frequencies(postings, "required_skills")
    counts = {s.skill: s.count for s in result}

    assert counts["Python"] == 3
    assert counts["SQL"] == 1
    assert counts["Docker"] == 1

def test_skills_sorted_by_count_descending():
    postings = [
        _make_posting(["Python", "Docker"]),
        _make_posting(["Python", "SQL"]),
        _make_posting(["Python", "SQL"]),
    ]

    result = compute_skill_frequencies(postings, "required_skills")
    ranked = [(s.skill, s.count) for s in result]

    assert ranked == [("Python", 3), ("SQL", 2), ("Docker", 1)]

def test_topn_cutoff():
    postings = [
        _make_posting(["Java", "Docker"]),
        _make_posting(["Java", "SQL"]),
        _make_posting(["Java", "SQL"]),
    ]

    result = compute_skill_frequencies(postings, "required_skills", top_n=2)
    ranked = [(s.skill, s.count) for s in result]

    assert ranked == [("Java", 3), ("SQL", 2)]

def test_empty_posting():
    postings = []
    result = compute_skill_frequencies(postings, "preferred_skills")

    assert result == []

def test_skill_variants_counted_separately():
    # Exact match: variants counted separately
    postings = [
        _make_posting(["React.js"]),
        _make_posting(["React"]),
    ]

    result = compute_skill_frequencies(postings, "required_skills")
    counts = {s.skill: s.count for s in result}
    assert counts == {"React": 1, "React.js": 1}

def test_skill_map_merges_variants():
    postings = [
        _make_posting(["React"]),
        _make_posting(["React.js"]),
    ]
    skill_map = {"React": "React", "React.js": "React"}
    
    result = compute_skill_frequencies(postings, "required_skills", skill_map=skill_map)
    counts = {s.skill: s.count for s in result}
    
    assert counts == {"React": 2}

def test_counts_only_requested_field():
    postings = [
        _make_posting(["Python"], preferred=["Docker"]),
        _make_posting(["Docker"], preferred=["DevOps"]),
        _make_posting(["C++"], preferred=["SQL"]),
    ]

    result = compute_skill_frequencies(postings, "preferred_skills")
    counts = {s.skill: s.count for s in result}

    assert counts == {"Docker": 1, "DevOps": 1, "SQL": 1}

# --- generate_market_analysis ---

def test_generate_market_analysis_rejects_empty_postings(tmp_path):
    with pytest.raises(ValueError, match="No job postings found"):
        asyncio.run(generate_market_analysis(str(tmp_path)))
