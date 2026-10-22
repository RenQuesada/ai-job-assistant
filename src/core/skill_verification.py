from core.client import client
from core.cost import calculate_cost
from core.extract import MODEL, get_file_contents
from core.logging_setup import logger
from core.schemas import SkillPairJudgments


async def verify_skill_pairs(pairs: list[tuple[str, str]]) -> list[bool]:
    if not pairs:
        return []

    system_prompt = get_file_contents("src/prompts/skill_verification_system_prompt.md")

    # Number each pair for the model
    numbered = "\n".join(f'{i}. "{a}" vs "{b}"' for i, (a, b) in enumerate(pairs))

    completion = await client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Judge these skill pairs:\n\n{numbered}"},
        ],
        response_format=SkillPairJudgments,
    )

    cost = calculate_cost(completion.model_dump(warnings=False))
    logger.debug(f"Verified {len(pairs)} pairs | Cost: ${cost['total']:.6f}")

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Skill verification failed: model returned no parsed result.")

    # Map answers back by index, missing ones count as not same
    decisions = {judgment.index: judgment.same for judgment in parsed.judgments}
    if len(decisions) != len(pairs):
        logger.warning(f"Expected {len(pairs)} judgments, got {len(decisions)}")

    return [decisions.get(i, False) for i in range(len(pairs))]
