import asyncio

from core.extract import extract_job_posting, extract_text_from_pdf
from core.tools import web_search
from phase1.market_analysis import load_market_analysis
from phase3.phase3 import run_legitimacy_agent

CASES = [
    {"path": "test-postings/fake-suspicious-posting.pdf", "expected": {"Red"}},
    {"path": "test-postings/junior-dba-posting.pdf", "expected": {"Green", "Yellow"}},
]
RUNS = 5

async def main():
    # One-time setup
    market_analysis = load_market_analysis()

    for case in CASES:
        # Per-case setup
        raw_text = extract_text_from_pdf(case["path"])
        posting = await extract_job_posting(case["path"])
        company_research = web_search(f"{posting.company} official website LinkedIn recent news company overview")

        print(f"\n{case['path']} (expected: {case['expected']})")
        verdicts = []

        for i in range(RUNS):
            # Run the agent
            result = await run_legitimacy_agent(
                posting=posting,
                raw_posting_text=raw_text,
                market_analysis=market_analysis,
                company_research=company_research,
            )
            verdicts.append(result.verdict)
            print(f"Run {i + 1}: {result.verdict} (confidence {result.confidence_score})")

        # Per-case summary
        passed = sum(1 for v in verdicts if v in case["expected"])
        print(f"Passed: {passed}/{RUNS}")

if __name__ == "__main__":
    asyncio.run(main())