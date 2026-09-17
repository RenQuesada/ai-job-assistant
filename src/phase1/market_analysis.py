import json
from collections import Counter
from pathlib import Path
from core.client import client
from core.cost import calculate_cost
from core.extract import get_file_contents, MODEL
from core.schemas import JobPosting, MarketAnalysis, SkillFrequency
from core.logging_setup import logger

def load_market_analysis(path: str = "data/analysis/market-analysis.json") -> MarketAnalysis:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    return MarketAnalysis(**data)

def load_all_postings(jobs_dir: str = "data/jobs") -> list[JobPosting]:
    postings = []
    for path in Path(jobs_dir).glob("*.json"):
        if path.name.startswith("."):  # skip .manifest.json
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        postings.append(JobPosting(**data))
    logger.debug(f"Loaded {len(postings)} postings from {jobs_dir}")

    return postings

def compute_skill_frequencies(postings: list[JobPosting], field: str, top_n: int = 10) -> list[SkillFrequency]:
    counter = Counter()
    for posting in postings:
        skills = getattr(posting, field)
        counter.update(skills)
    frequencies = [
        SkillFrequency(skill=skill, count=count)
        for skill, count in counter.most_common(top_n)
    ]
    logger.debug(f"Computed {field} frequencies: top {len(frequencies)} of {len(counter)} distinct skills")

    return frequencies

async def generate_market_analysis(jobs_dir: str = "data/jobs") -> MarketAnalysis:
    postings = load_all_postings(jobs_dir)

    top_required = compute_skill_frequencies(postings, "required_skills")
    top_preferred = compute_skill_frequencies(postings, "preferred_skills")

    system_prompt = get_file_contents("src/prompts/market_analysis_system_prompt.md")

    postings_json = json.dumps([p.model_dump() for p in postings], indent=2)
    skills_json = json.dumps({
        "top_required_skills": [s.model_dump() for s in top_required],
        "top_preferred_skills": [s.model_dump() for s in top_preferred],
    }, indent=2)

    logger.debug(f"Requesting market analysis synthesis from {MODEL} for {len(postings)} postings")

    completion = await client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Here is the pre-computed skill frequency data:\n{skills_json}\n\n"
                f"Here is the full structured data for all {len(postings)} postings:\n{postings_json}\n\n"
                "Analyze this data and produce the market analysis fields."
            )},
        ],
        response_format=MarketAnalysis,
    )

    cost = calculate_cost(completion.model_dump())
    logger.debug(f"Cost: ${cost['total']:.6f} | Tokens: {cost['tokens']['total']}")

    analysis = completion.choices[0].message.parsed
    analysis.postings_analyzed = len(postings)
    analysis.top_required_skills = top_required
    analysis.top_preferred_skills = top_preferred

    return analysis

def save_market_analysis_json(analysis: MarketAnalysis, path: str = "data/analysis/market-analysis.json") -> str:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(analysis.model_dump_json(indent=2), encoding="utf-8")
    logger.debug(f"Saved market analysis JSON to {out_path}")

    return str(out_path)

def render_market_analysis_report(analysis: MarketAnalysis) -> str:
    lines = [
        "# Job Market Analysis Report",
        "",
        f"**Postings analyzed:** {analysis.postings_analyzed}",
        "",
        "## Top Required Skills",
        "",
    ]
    for s in analysis.top_required_skills:
        lines.append(f"- {s.skill} ({s.count}/{analysis.postings_analyzed})")

    lines += ["", "## Top Preferred Skills", ""]
    for s in analysis.top_preferred_skills:
        lines.append(f"- {s.skill} ({s.count}/{analysis.postings_analyzed})")

    lines += [
        "",
        "## Experience Level",
        "",
        analysis.experience_level_summary,
        "",
        "## Education",
        "",
        analysis.education_summary,
        "",
        "## Salary Range",
        "",
        analysis.salary_range_summary,
        "",
        "## Common Responsibilities",
        "",
    ]
    for r in analysis.common_responsibilities:
        lines.append(f"- {r}")

    lines += [
        "",
        "## Role Patterns",
        "",
        analysis.role_pattern_notes,
        "",
        "## Culture & Industry Trends",
        "",
        analysis.culture_and_industry_trends,
        "",
        "## Notable Observations",
        "",
    ]
    for o in analysis.notable_observations:
        lines.append(f"- {o}")

    return "\n".join(lines)

def save_market_analysis_report(analysis: MarketAnalysis, path: str = "reports/market-analysis.md") -> str:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_market_analysis_report(analysis), encoding="utf-8")
    logger.debug(f"Saved market analysis report to {out_path}")

    return str(out_path)