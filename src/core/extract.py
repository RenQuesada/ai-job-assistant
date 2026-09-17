import json
from pdfplumber import open as pdf_open
from core.client import client
from core.schemas import JobPosting
from core.cost import calculate_cost
from core.tools import search_company
from core.logging_setup import logger

MODEL = "openai/gpt-5-nano" # "openai/gpt-5-nano"

company_search_tool = {
    "type": "function",
    "function": {
        "name": "search_company",
        "description": "Search the web for information about a company - size, industry, recent news, culture, reviews. Call this one or more times with different queries to research the company behind a job posting.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g. 'Feathery company funding size' or 'CMiC company reviews culture'"
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
}

tools = [company_search_tool]

def get_file_contents(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

def extract_text_from_pdf(pdf_path: str) -> str:
    with pdf_open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

async def extract_job_posting(pdf_path: str) -> JobPosting:
    text = extract_text_from_pdf(pdf_path)
    system_prompt = get_file_contents("src/prompts/extraction_system_prompt.md")

    logger.debug(f"Extracting posting: {pdf_path}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            "Extract structured data from this job posting. Use the "
            "search_company tool to research the company (size, recent "
            "news, culture) before producing your final answer:\n\n" + text
        )},
    ]

    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        completion = await client.beta.chat.completions.parse(
            model=MODEL,
            messages=messages,
            tools=tools,
            response_format=JobPosting,
        )

        cost = calculate_cost(completion.model_dump())
        logger.debug(f"Cost: ${cost['total']:.6f} | Tokens: {cost['tokens']['total']}")

        message = completion.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)

                logger.debug(f"Tool call: {tool_call.function.name}")
                logger.debug(f"Arguments: {args}")

                if tool_call.function.name == "search_company":
                    result = search_company(args["query"])
                else:
                    result = f"Error: Unknown tool {tool_call.function.name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            continue

        if message.parsed:
            logger.debug(f"Extracted {len(message.parsed.required_skills)} required skills, {len(message.parsed.preferred_skills)} preferred skills")
            logger.debug(f"Salary field: {'found' if message.parsed.salary_min else 'not found'} in posting")
            return message.parsed

        raise ValueError("Model did not return tool calls or a parsed result")

    raise ValueError("Max iterations reached without a final structured result")