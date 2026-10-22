import argparse
import asyncio

from core.logging_setup import setup_logging
from phase1.market_analysis import load_market_analysis
from phase2.gap_analysis import (
    generate_gap_analysis,
    save_gap_analysis_json,
    save_gap_analysis_report,
)


async def main():
    analysis = await generate_gap_analysis()
    total_postings = load_market_analysis().postings_analyzed
    json_path = save_gap_analysis_json(analysis)
    md_path = save_gap_analysis_report(analysis, total_postings)
    print(f"Saved: {json_path}")
    print(f"Saved: {md_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "--debug", action="store_true")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    asyncio.run(main())
