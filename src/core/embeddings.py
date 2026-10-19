from core.client import client

EMBEDDING_MODEL = "openai/text-embedding-3-small"
SKILL_MERGE_THRESHOLD = 0.70

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
) -> dict[str, str]:
    canonicals: list[tuple[str, list[float]]] = []
    skill_map: dict[str, str] = {}

    for skill, vector in zip(skills, vectors):
        # Find closest existing canonical
        best_name, best_score = None, threshold
        for name, canonical_vector in canonicals:
            score = dot_product(vector, canonical_vector)
            if score >= best_score:
                best_name, best_score = name, score

        if best_name is None:
            # Start a new group
            canonicals.append((skill, vector))
            skill_map[skill] = skill
        else:
            skill_map[skill] = best_name

    return skill_map