from core.client import client

EMBEDDING_MODEL = "openai/text-embedding-3-small"

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