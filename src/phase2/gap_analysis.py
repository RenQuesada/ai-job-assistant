import json
from pathlib import Path
from core.client import client
from core.schemas import GapAnalysis, ResumeData, MarketAnalysis
from core.cost import calculate_cost
from core.extract import get_file_contents, MODEL
from core.tools import web_search
from core.logging_setup import logger

web_search_tool = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information - certifications, courses, learning resources, tutorials. Use this to find specific, real, current details for gap recommendations rather than relying on general knowledge.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g. 'AWS Cloud Practitioner certification cost time'"
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
}

tools = [web_search_tool]

def load_resume_data(path: str = "data/resume/resume.json") -> ResumeData:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    return ResumeData(**data)

def load_market_analysis(path: str = "data/analysis/market-analysis.json") -> MarketAnalysis:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    return MarketAnalysis(**data)

async def generate_gap_analysis() -> GapAnalysis:
    resume = load_resume_data()
    market = load_market_analysis()
    system_prompt = get_file_contents("src/prompts/gap_analysis_system_prompt.md")

    logger.debug(f"Generating gap analysis against {market.postings_analyzed} analyzed postings")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            "Here is the candidate's resume data:\n"
            f"{resume.model_dump_json(indent=2)}\n\n"
            "Here is the market analysis of job postings in their target field:\n"
            f"{market.model_dump_json(indent=2)}\n\n"
            "Identify strengths, gaps (triaged by actionability), and unique "
            "value. Use web_search to find specific, current details for "
            "gap recommendations."
        )},
    ]

    max_iterations = 6
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        force_final = iteration == max_iterations

        if force_final:
            messages.append({
                "role": "user",
                "content": (
                    "Return your final GapAnalysis now using only the "
                    "information already gathered - do not call any more tools."
                )
            })

        kwargs = {
            "model": MODEL,
            "messages": messages,
            "response_format": GapAnalysis,
        }
        if not force_final:
            kwargs["tools"] = tools

        completion = await client.beta.chat.completions.parse(**kwargs)

        cost = calculate_cost(completion.model_dump())
        logger.debug(f"Cost: ${cost['total']:.6f} | Tokens: {cost['tokens']['total']}")

        message = completion.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)

                logger.debug(f"Tool call: {tool_call.function.name}")
                logger.debug(f"Arguments: {args}")

                if tool_call.function.name == "web_search":
                    result = web_search(args["query"])
                else:
                    result = f"Error: Unknown tool {tool_call.function.name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            continue

        if message.parsed:
            logger.debug(f"Gap analysis complete: {len(message.parsed.strengths)} strengths, {len(message.parsed.gaps)} gaps identified")
            return message.parsed

        raise ValueError("Model did not return tool calls or a parsed result")

    raise ValueError("Max iterations reached without a final structured result")

def save_gap_analysis_json(analysis: GapAnalysis, path: str = "data/analysis/gap-analysis.json") -> str:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(analysis.model_dump_json(indent=2), encoding="utf-8")
    logger.debug(f"Saved gap analysis JSON to {out_path}")

    return str(out_path)

def _clean_bullet(text: str) -> str:
    return text.lstrip("- ").strip()

def render_gap_analysis_report(analysis: GapAnalysis) -> str:
    lines = [
        "# Resume Gap Analysis",
        "",
        analysis.summary,
        "",
        "## Strengths",
        "",
    ]
    for s in analysis.strengths:
        lines.append(f"- {_clean_bullet(s)}")

    lines += ["", "## Gaps", ""]

    triage_order = ["Quick win", "Short-term", "Medium-term", "Long-term"]
    for level in triage_order:
        level_gaps = [g for g in analysis.gaps if g.triage_level == level]
        if not level_gaps:
            continue
        lines.append(f"### {level}")
        lines.append("")
        for g in level_gaps:
            lines.append(f"**{g.skill}** ({g.frequency_in_postings}/9 postings)")
            lines.append(f"- {_clean_bullet(g.recommendation)}")
            lines.append("")

    lines += ["## Unique Value", ""]
    for u in analysis.unique_value:
        lines.append(f"- {_clean_bullet(u)}")

    return "\n".join(lines)

def save_gap_analysis_report(analysis: GapAnalysis, path: str = "reports/gap-analysis.md") -> str:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_gap_analysis_report(analysis), encoding="utf-8")
    logger.debug(f"Saved gap analysis report to {out_path}")

    return str(out_path)