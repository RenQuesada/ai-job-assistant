import asyncio
import sys
from itertools import combinations
from pathlib import Path

# Make src/ importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.embeddings import dot_product, embed_texts
from phase1.market_analysis import load_all_postings

# Known variants and known traps
PROBE_SKILLS = [
    "React", "React.js", "ReactJS",
    "Java", "JavaScript",
    "SQL", "PostgreSQL", "MySQL",
    "REST APIs", "RESTful services",
    "Docker", "Kubernetes",
]

async def main():
    # Collect skills from saved postings plus probes
    skills = set(PROBE_SKILLS)
    for posting in load_all_postings():
        skills.update(posting.required_skills)
        skills.update(posting.preferred_skills)
    skills = sorted(skills)

    # Embed all skills in one call
    vectors = await embed_texts(skills)

    # Score every pair
    pairs = []
    for (skill_a, vec_a), (skill_b, vec_b) in combinations(zip(skills, vectors), 2):
        pairs.append((dot_product(vec_a, vec_b), skill_a, skill_b))

    # Most similar first
    pairs.sort(reverse=True)
    for score, skill_a, skill_b in pairs[:40]:
        print(f"{score:.3f}  {skill_a}  <->  {skill_b}")

if __name__ == "__main__":
    asyncio.run(main())