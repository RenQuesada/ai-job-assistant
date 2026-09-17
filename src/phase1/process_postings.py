import argparse
import asyncio
from pathlib import Path
from core.extract import extract_job_posting
from core.storage import save_job_posting, slugify_job_posting
from core.manifest import load_manifest, save_manifest
from core.logging_setup import setup_logging, logger


async def process_all_postings(raw_dir: str = "raw-postings", jobs_dir: str = "data/jobs"):
    pdf_paths = list(Path(raw_dir).glob("*.pdf"))
    manifest = load_manifest()
    results = []

    for path in pdf_paths:
        if path.name in manifest:
            print(f"{path.name} -> skipped (already processed as {manifest[path.name]})")
            continue

        try:
            posting = await extract_job_posting(str(path))
        except Exception as e:
            print(f"{path.name} -> FAILED during extraction: {e}")
            continue

        filepath = save_job_posting(posting, jobs_dir)
        slug_filename = Path(filepath).name

        manifest[path.name] = slug_filename
        save_manifest(manifest)

        print(f"{path.name} -> saved to {filepath}")
        results.append(posting)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "--debug", action="store_true")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    asyncio.run(process_all_postings())