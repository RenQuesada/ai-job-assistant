import asyncio
import argparse
from pathlib import Path
from core.client import client
from core.schemas import ResumeData
from core.cost import calculate_cost
from core.extract import get_file_contents, extract_text_from_pdf, MODEL
from core.logging_setup import logger, setup_logging

async def extract_resume(pdf_path: str) -> ResumeData:
    text = extract_text_from_pdf(pdf_path)
    system_prompt = get_file_contents("src/prompts/resume_extraction_system_prompt.md")

    logger.debug(f"Extracting resume: {pdf_path}")

    completion = await client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract structured data from this resume:\n\n{text}"},
        ],
        response_format=ResumeData,
    )

    cost = calculate_cost(completion.model_dump())
    logger.debug(f"Cost: ${cost['total']:.6f} | Tokens: {cost['tokens']['total']}")

    resume = completion.choices[0].message.parsed
    logger.debug(f"Extracted {len(resume.hard_skills)} hard skills, {len(resume.soft_skills)} soft skills, {len(resume.work_experience)} work experience entries, {len(resume.projects)} projects")

    return resume

def save_resume_data(resume: ResumeData, path: str = "data/resume/resume.json") -> str:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(resume.model_dump_json(indent=2), encoding="utf-8")
    logger.debug(f"Saved resume data to {out_path}")

    return str(out_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", nargs="?", default="raw-resume/resume.pdf")
    parser.add_argument("--verbose", "--debug", action="store_true")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    result = asyncio.run(extract_resume(args.pdf_path))
    filepath = save_resume_data(result)
    print(f"Saved to {filepath}")