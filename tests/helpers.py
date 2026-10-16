from core.schemas import FitAssessment

FIT_CATEGORY_MAXES = {
    "core_skills_score": 40,
    "experience_relevance_score": 25,
    "experience_level_score": 15,
    "preferred_skills_score": 10,
    "education_domain_score": 10,
}

def make_fit(
    core_skills_score: int = 20,
    experience_relevance_score: int = 10,
    experience_level_score: int = 10,
    preferred_skills_score: int = 5,
    education_domain_score: int = 5,
) -> FitAssessment:
    return FitAssessment(
        core_skills_score=core_skills_score,
        experience_relevance_score=experience_relevance_score,
        experience_level_score=experience_level_score,
        preferred_skills_score=preferred_skills_score,
        education_domain_score=education_domain_score,
        score=50,
        tier="Good fit",
        requirements_met=["Python"],
        requirements_gap=["Docker"],
        overall_assessment="Solid match on core skills",
    )