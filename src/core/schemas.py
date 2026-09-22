from pydantic import BaseModel
from typing import Literal, Optional

class CompanyResearch(BaseModel):
    """Represents information researched about a company."""
    company_size: Optional[str] = None
    recent_news: Optional[str] = None
    culture_signals: Optional[str] = None
    other_notes: Optional[str] = None

class JobPosting(BaseModel):
    """Represents structured information extracted from a job posting."""
    job_title: str
    company: str
    location: Optional[str] = None
    remote: Optional[str] = None # (e.g. "Remote", "Hybrid", "On-site") or None if not stated

    required_skills: list[str]
    preferred_skills: list[str] # Can be empty list, not all postings have bonus skills

    experience_level: str # (e.g. "3-5 years", "Entry-level", or "Senior")
    education: Optional[str] = None

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

    responsibilities: list[str]
    posting_age_days: Optional[int] = None # null if no date found in posting
    company_research: Optional[CompanyResearch] = None

class SkillFrequency(BaseModel):
    """Represents how frequently a skill appears across job postings."""
    skill: str
    count: int

class MarketAnalysis(BaseModel):
    """Represents patterns and trends identified across multiple job postings."""
    postings_analyzed: int
    top_required_skills: list[SkillFrequency]
    top_preferred_skills: list[SkillFrequency]

    experience_level_summary: str  # e.g. "Mostly 3-5 years; one entry-level/internship, one senior"
    education_summary: str

    salary_range_summary: str  # e.g. "Observed range $70K-$147K; N of 8 postings disclosed salary"

    common_responsibilities: list[str]
    role_pattern_notes: str  # (e.g. "Mix of backend API work, and specialized CMS/registry roles")

    culture_and_industry_trends: str  # Synthesized from company_research across postings
    notable_observations: list[str]

class WorkExperience(BaseModel):
    """Represents the candidate's work experience."""
    role: str
    company: str
    duration: Optional[str] = None
    responsibilities: list[str]
    achievements: list[str]

class Education(BaseModel):
    """Represents the candidate's educational background."""
    degree: str
    institution: str
    relevant_coursework: list[str]

class Project(BaseModel):
    """Represents a project included in the candidate's resume."""
    name: str
    description: str
    technologies: list[str]

class ResumeData(BaseModel):
    """Represents structured information extracted from the candidate's resume."""
    hard_skills: list[str]
    soft_skills: list[str]

    work_experience: list[WorkExperience]
    education: list[Education]
    certifications: list[str]
    projects: list[Project]

    keywords_domain_expertise: list[str]

class TriagedGap(BaseModel):
    """Represents a skill gap and its recommended priority for improvement."""
    skill: str
    frequency_in_postings: int  # num of analyzed postings requesting this skill
    triage_level: str  # "Short-term" | "Medium-term" | "Long-term"
    recommendation: str  # specific, actionable skills (e.g. not "learn AWS")

class GapAnalysis(BaseModel):
    """Represents the identified strengths, skill gaps, and unique value of the candidate."""
    strengths: list[str]
    gaps: list[TriagedGap]
    unique_value: list[str]
    summary: str

class LegitimacySignal(BaseModel):
    """Represents one individual signal from the legitimacy analysis"""
    signal_type: Literal["red", "green", "yellow"]
    description: str
    evidence: str  # evidence found that supports the signal

class LegitimacyAssessment(BaseModel):
    """Represents the entire legitimacy evaluation"""
    verdict: str  # "Green" | "Yellow" | "Red"
    confidence_score: int  # how confident the agent is in the verdict (0-100)
    signals: list[LegitimacySignal]
    recommendation: str

class FitAssessment(BaseModel):
    """Represents how well a candidate's qualifications match a job posting."""
    score: int  # 0-100
    tier: str  # "Strong fit" | "Good fit" | "Stretch" | "Growth target"
    requirements_met: list[str]
    requirements_gap: list[str]
    overall_assessment: str

class ApplicationAdvice(BaseModel):
    """Represents recommendations for tailoring the candidate's application to a job posting."""
    resume_adaptation: list[str]  # specific, concrete suggestions
    cover_letter_guidance: list[str]
    interview_prep_questions: list[str]
    interview_prep_skills_to_review: list[str]
    interview_prep_company_research: list[str]
    interview_prep_talking_points: list[str]

class ApplicationReport(BaseModel):
    """Represents the final structured analysis of a job posting and candidate."""
    legitimacy: LegitimacyAssessment
    fit: FitAssessment
    resume_adaptation: list[str]
    cover_letter_guidance: list[str]
    interview_prep_questions: list[str]
    interview_prep_skills_to_review: list[str]
    interview_prep_company_research: list[str]
    interview_prep_talking_points: list[str]
