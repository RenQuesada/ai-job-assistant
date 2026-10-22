import asyncio

from core.extract import extract_job_posting
from phase1.market_analysis import load_market_analysis
from phase2.gap_analysis import load_resume_data
from phase3.phase3 import assess_fit

POSTING_PATH = "test-postings/junior-dba-posting.pdf"
RUNS = 5

CATEGORIES = [
    "core_skills_score",
    "experience_relevance_score",
    "experience_level_score",
    "preferred_skills_score",
    "education_domain_score",
]


async def main():
    market_analysis = load_market_analysis()
    resume_data = load_resume_data()
    posting = await extract_job_posting(POSTING_PATH)

    results = []

    # Run fit assessment
    for i in range(RUNS):
        fit = await assess_fit(posting, resume_data, market_analysis)
        results.append(fit)
        categories = " ".join(str(getattr(fit, c)) for c in CATEGORIES)
        print(f"Run {i + 1}: {fit.score} ({fit.tier}) | categories: {categories}")

    # Spread per field
    print("\nSpread across runs (max - min):")
    for field in CATEGORIES + ["score"]:
        values = [getattr(fit, field) for fit in results]
        print(
            f"{field}: {min(values)}-{max(values)} (spread {max(values) - min(values)})"
        )


if __name__ == "__main__":
    asyncio.run(main())
