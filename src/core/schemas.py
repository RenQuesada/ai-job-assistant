from pydantic import BaseModel
from typing import Literal, Optional

class CompanyResearch(BaseModel):
    """docstring comment"""
    company_size: Optional[str] = None
    recent_news: Optional[str] = None
    culture_signals: Optional[str] = None
    other_notes: Optional[str] = None

class JobPosting(BaseModel):
    job_title: str
    company: str
    location: Optional[str] = None
    remote: Optional[str] = None # e.g. "Remote", "Hybrid", "On-site", or None if not stated

    required_skills: list[str]
    preferred_skills: list[str] # can be empty list, not all postings have bonus skills

    experience_level: str # e.g. "3-5 years", "Entry-level", or "Senior"
    education: Optional[str] = None

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

    responsibilities: list[str]

    posting_age_days: Optional[int] = None # null if no date found in posting
    company_research: Optional[CompanyResearch] = None

class SkillFrequency(BaseModel):
    skill: str
    count: int

class MarketAnalysis(BaseModel):
    """docstring comment"""
    postings_analyzed: int
    top_required_skills: list[SkillFrequency]
    top_preferred_skills: list[SkillFrequency]

    experience_level_summary: str  # e.g. "Mostly 3-5 years; one entry-level/internship, one senior"
    education_summary: str

    salary_range_summary: str  # e.g. "Observed range $70K-$147K; N of 8 postings disclosed salary"

    common_responsibilities: list[str]
    role_pattern_notes: str  # e.g. "Mix of backend API work, full-stack, and specialized CMS/registry roles"

    culture_and_industry_trends: str  # synthesized from company_research across postings

    notable_observations: list[str]

class WorkExperience(BaseModel):
    role: str
    company: str
    duration: Optional[str] = None
    responsibilities: list[str]
    achievements: list[str]

class Education(BaseModel):
    degree: str
    institution: str
    relevant_coursework: list[str]

class Project(BaseModel):
    name: str
    description: str
    technologies: list[str]

class ResumeData(BaseModel):
    hard_skills: list[str]
    soft_skills: list[str]
    work_experience: list[WorkExperience]
    education: list[Education]
    certifications: list[str]
    projects: list[Project]
    keywords_domain_expertise: list[str]

class TriagedGap(BaseModel):
    """docstring comment"""
    skill: str
    frequency_in_postings: int  # number of analyzed postings requesting this skill
    triage_level: str  # "Quick win" | "Short-term" | "Medium-term" | "Long-term"
    recommendation: str  # specific, actionable skills - not "learn AWS"

class GapAnalysis(BaseModel):
    """docstring comment"""
    strengths: list[str]
    gaps: list[TriagedGap]
    unique_value: list[str]
    summary: str

class LegitimacySignal(BaseModel):
    """Represents one individual signal from the legitimacy analysis"""
    signal_type: Literal["red", "green", "yellow"]
    description: str
    evidence: str  # what was actually found that supports this signal

class LegitimacyAssessment(BaseModel):
    """docstring comment"""
    verdict: str  # "Green" | "Yellow" | "Red"
    confidence_score: int  # 0-100, how confident the agent is in the verdict
    signals: list[LegitimacySignal]
    recommendation: str  # plain-language advice to the user

class FitAssessment(BaseModel):
    """docstring comment"""
    score: int  # 0-100
    tier: str  # "Strong fit" | "Good fit" | "Stretch" | "Growth target"
    requirements_met: list[str]
    requirements_gap: list[str]
    overall_assessment: str

class ApplicationAdvice(BaseModel):
    """docstring comment"""
    resume_adaptation: list[str]  # specific, concrete suggestions
    cover_letter_guidance: list[str]
    interview_prep_questions: list[str]
    interview_prep_skills_to_review: list[str]
    interview_prep_company_research: list[str]
    interview_prep_talking_points: list[str]

class ApplicationReport(BaseModel):
    """docstring comment"""
    legitimacy: LegitimacyAssessment
    fit: FitAssessment
    resume_adaptation: list[str]  # specific, concrete suggestions
    cover_letter_guidance: list[str]
    interview_prep_questions: list[str]
    interview_prep_skills_to_review: list[str]
    interview_prep_company_research: list[str]
    interview_prep_talking_points: list[str]
