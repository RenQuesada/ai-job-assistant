import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.logging_setup import setup_logging

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Phase 3 application advisor report for a job posting PDF."
    )
    parser.add_argument("pdf_path", help="Path to the job posting PDF")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging to stderr.",
    )

    return parser.parse_args()

async def main() -> int:
    args = parse_args()
    setup_logging(verbose=args.verbose)
    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    try:
        from phase3.phase3 import build_application_report
    except ModuleNotFoundError as e:
        print(
            f"Error: Missing dependency `{e.name}`. Install project requirements before running Phase 3.",
            file=sys.stderr,
        )
        return 1

    try:
        output_path = await build_application_report(str(pdf_path))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(output_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
