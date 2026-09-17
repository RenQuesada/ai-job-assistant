import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.logging_setup import setup_logging
from phase1.process_postings import process_all_postings
from phase1.market_analysis import generate_market_analysis, save_market_analysis_json, save_market_analysis_report
from phase2.resume import extract_resume, save_resume_data
from phase2.gap_analysis import generate_gap_analysis, save_gap_analysis_json, save_gap_analysis_report

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the job search assistant setup pipeline (Phases 1 & 2): "
                     "process job postings, analyze the market, extract resume data, "
                     "and generate a gap analysis. Run advise.py separately afterward "
                     "to evaluate a specific new posting."
    )
    parser.add_argument(
        "--resume", default=None,
        help="Path to your resume PDF (default: auto-detect the first PDF in raw-resume/)",
    )
    parser.add_argument(
        "--postings-dir", default="raw-postings",
        help="Folder containing job posting PDFs to process (default: raw-postings)",
    )
    parser.add_argument(
        "--skip-postings", action="store_true",
        help="Skip posting extraction + market analysis (reuse existing data/jobs data)",
    )
    parser.add_argument(
        "--skip-resume", action="store_true",
        help="Skip resume extraction (reuse existing data/resume/resume.json)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()

async def run_pipeline(args: argparse.Namespace) -> int:
    if not args.skip_postings:
        print("=== Phase 1: Processing job postings ===")
        await process_all_postings(raw_dir=args.postings_dir)

        print("\n=== Phase 1: Generating market analysis ===")
        analysis = await generate_market_analysis()
        print(f"Saved: {save_market_analysis_json(analysis)}")
        print(f"Saved: {save_market_analysis_report(analysis)}")
    else:
        print("=== Phase 1: Skipped ===")

    if not args.skip_resume:
        print("\n=== Phase 2: Extracting resume data ===")

        if args.resume:
            resume_path = Path(args.resume)
        else:
            candidates = sorted(Path("raw-resume").glob("*.pdf"))
            if not candidates:
                print("Error: no PDF found in raw-resume/. Add your resume there or pass --resume.", file=sys.stderr)
                return 1
            if len(candidates) > 1:
                print(f"Note: multiple PDFs found in raw-resume/, using {candidates[0].name}", file=sys.stderr)
            resume_path = candidates[0]

        if not resume_path.exists():
            print(f"Error: resume not found at {resume_path}", file=sys.stderr)
            return 1
        resume = await extract_resume(str(resume_path))
        print(f"Saved: {save_resume_data(resume)}")

    print("\n=== Phase 2: Generating gap analysis ===")
    gap = await generate_gap_analysis()
    print(f"Saved: {save_gap_analysis_json(gap)}")
    print(f"Saved: {save_gap_analysis_report(gap)}")

    print("\nDone. Run `python advise.py <path-to-posting.pdf>` next to evaluate a specific posting.")
    return 0

def main() -> int:
    args = parse_args()
    setup_logging(verbose=args.verbose)
    return asyncio.run(run_pipeline(args))

if __name__ == "__main__":
    sys.exit(main())