from itertools import combinations

from core.client import client
from core.logging_setup import logger
from core.skill_verification import verify_skill_pairs

EMBEDDING_MODEL = "openai/text-embedding-3-small"
SKILL_MERGE_THRESHOLD = 0.85
CANDIDATE_THRESHOLD = 0.60

async def embed_texts(texts: list[str]) -> list[list[float]]:
    # Embed all texts in one call
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        encoding_format="float",
    )
    return [item.embedding for item in response.data]

def dot_product(vec_a: list[float], vec_b: list[float]) -> float:
    return sum(a * b for a, b in zip(vec_a, vec_b))

def group_skills(
    skills: list[str],
    vectors: list[list[float]],
    threshold: float = SKILL_MERGE_THRESHOLD,
    verified_pairs: set[frozenset[str]] | None = None,
) -> dict[str, str]:
    verified_pairs = verified_pairs or set()
    canonicals: list[tuple[str, list[float]]] = []
    skill_map: dict[str, str] = {}

    for skill, vector in zip(skills, vectors):
        # Find closest existing canonical
        best_name, best_score = None, -1.0
        for name, canonical_vector in canonicals:
            score = dot_product(vector, canonical_vector)
            is_match = score >= threshold or frozenset((skill, name)) in verified_pairs
            if is_match and score > best_score:
                best_name, best_score = name, score

        if best_name is None:
            # Start a new group
            canonicals.append((skill, vector))
            skill_map[skill] = skill
        else:
            skill_map[skill] = best_name

    return skill_map

async def build_skill_map(skills: list[str]) -> dict[str, str]:
    if not skills:
        return {}

    vectors = await embed_texts(skills)

    # Find ambiguous pairs for LLM review
    candidate_pairs = [
        (skill_a, skill_b)
        for (skill_a, vec_a), (skill_b, vec_b) in combinations(zip(skills, vectors), 2)
        if CANDIDATE_THRESHOLD <= dot_product(vec_a, vec_b) < SKILL_MERGE_THRESHOLD
    ]
    verdicts = await verify_skill_pairs(candidate_pairs)

    verified_pairs = {
        frozenset(pair) for pair, same in zip(candidate_pairs, verdicts) if same
    }
    logger.debug(f"Verified {len(verified_pairs)} of {len(candidate_pairs)} candidate pairs as same skill")

    return group_skills(skills, vectors, verified_pairs=verified_pairs)