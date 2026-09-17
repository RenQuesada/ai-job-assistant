import json
import re
from pathlib import Path
from core.schemas import JobPosting

def slugify_job_posting(job_title: str, company: str) -> str:
    combined = f"{job_title}-{company}".lower()
    combined = re.sub(r"[^a-z0-9\s-]", "", combined)
    combined = re.sub(r"[\s_-]+", "-", combined).strip("-")

    return combined

def save_job_posting(posting: JobPosting, jobs_dir: str = "data/jobs") -> str:
    Path(jobs_dir).mkdir(parents=True, exist_ok=True)
    slug = slugify_job_posting(posting.job_title, posting.company)
    filepath = Path(jobs_dir) / f"{slug}.json"
    filepath.write_text(posting.model_dump_json(indent=2), encoding="utf-8")

    return str(filepath)