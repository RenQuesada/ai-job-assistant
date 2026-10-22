"""
Prints the most similar skill pairs from saved postings and probe skills,
to help choose SKILL_MERGE_THRESHOLD in core/embeddings.py.

Run from the project root:
    python scripts/explore_skill_similarity.py
"""

import asyncio
from itertools import combinations

from core.embeddings import CANDIDATE_THRESHOLD, dot_product, embed_texts
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

    # Candidate pairs for LLM verification
    candidates = [(score, a, b) for score, a, b in pairs if score >= CANDIDATE_THRESHOLD]
    for score, skill_a, skill_b in candidates:
        print(f"{score:.3f}  {skill_a}  <->  {skill_b}")
    print(f"\n{len(candidates)} candidate pairs out of {len(pairs)} total")

if __name__ == "__main__":
    asyncio.run(main())