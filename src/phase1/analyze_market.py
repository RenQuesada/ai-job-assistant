import argparse
import asyncio
from phase1.market_analysis import generate_market_analysis, save_market_analysis_json, save_market_analysis_report
from core.logging_setup import setup_logging

async def main():
    analysis = await generate_market_analysis()
    json_path = save_market_analysis_json(analysis)
    md_path = save_market_analysis_report(analysis)
    print(f"Saved: {json_path}")
    print(f"Saved: {md_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "--debug", action="store_true")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    asyncio.run(main())