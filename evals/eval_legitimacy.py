import asyncio
import sys
from pathlib import Path

# Make src/ importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.extract import extract_job_posting, extract_text_from_pdf
from core.tools import web_search
from phase1.market_analysis import load_market_analysis
from phase3.phase3 import run_legitimacy_agent

POSTING_PATH = "test-postings/fake-suspicious-posting.pdf"
RUNS = 5

async def main():
    # One-time setup
    market_analysis = load_market_analysis()
    raw_text = extract_text_from_pdf(POSTING_PATH)
    posting = await extract_job_posting(POSTING_PATH)
    company_research = web_search(f"{posting.company} official website LinkedIn recent news company overview")

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

    red_count = sum(1 for v in verdicts if v == "Red")
    print(f"Red: {red_count}/{RUNS}")

if __name__ == "__main__":
    asyncio.run(main())