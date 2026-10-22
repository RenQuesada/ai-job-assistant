"""
Scores skill-matching approaches against labelled pairs in evals/skill_pairs.json.

Run from the project root:
    python evals/eval_skill_matching.py
"""

import asyncio
import json
from pathlib import Path

from core.embeddings import CANDIDATE_THRESHOLD

ROOT = Path(__file__).resolve().parent.parent

from core.embeddings import SKILL_MERGE_THRESHOLD, dot_product, embed_texts
from core.skill_verification import verify_skill_pairs

PAIRS_PATH = ROOT / "evals" / "skill_pairs.json"
THRESHOLDS = [0.70, 0.85]

def report(name: str, results: list[tuple[dict, bool]]) -> None:
    # Count each outcome type
    true_merges = sum(1 for pair, merged in results if merged and pair["same"])
    false_merges = sum(1 for pair, merged in results if merged and not pair["same"])
    missed_merges = sum(1 for pair, merged in results if not merged and pair["same"])

    precision = true_merges / (true_merges + false_merges) if true_merges + false_merges else 0.0
    recall = true_merges / (true_merges + missed_merges) if true_merges + missed_merges else 0.0
    print(f"\n{name}: precision {precision:.0%} | recall {recall:.0%}")

    # List every mistake
    for pair, merged in results:
        if merged and not pair["same"]:
            print(f"  False merge:  {pair['a']}  <->  {pair['b']}")
        elif not merged and pair["same"]:
            print(f"  Missed merge: {pair['a']}  <->  {pair['b']}")

async def main():
    pairs = json.loads(PAIRS_PATH.read_text(encoding="utf-8"))

    # Embed each unique name once
    names = sorted({pair["a"] for pair in pairs} | {pair["b"] for pair in pairs})
    vectors = dict(zip(names, await embed_texts(names)))
    scores = [dot_product(vectors[pair["a"]], vectors[pair["b"]]) for pair in pairs]

    # Option A at each threshold
    for threshold in THRESHOLDS:
        results = [(pair, score >= threshold) for pair, score in zip(pairs, scores)]
        report(f"Threshold {threshold}", results)
    
    # Option B: auto-merge clear pairs, LLM verifies the ambiguous zone
    auto_indexes = {i for i, score in enumerate(scores) if score >= SKILL_MERGE_THRESHOLD}
    candidate_indexes = [
        i for i, score in enumerate(scores)
        if CANDIDATE_THRESHOLD <= score < SKILL_MERGE_THRESHOLD
    ]
    candidate_pairs = [(pairs[i]["a"], pairs[i]["b"]) for i in candidate_indexes]
    verdicts = await verify_skill_pairs(candidate_pairs)

    verified_indexes = {i for i, same in zip(candidate_indexes, verdicts) if same}
    merged_indexes = auto_indexes | verified_indexes
    results = [(pair, i in merged_indexes) for i, pair in enumerate(pairs)]
    report("Embeddings + LLM verification", results)

if __name__ == "__main__":
    asyncio.run(main())