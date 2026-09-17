import html
import json
import logging
import re
from pathlib import Path

from core.client import client
from core.cost import calculate_cost
from core.extract import MODEL, extract_job_posting, extract_text_from_pdf, get_file_contents
from phase2.gap_analysis import load_resume_data
from phase1.market_analysis import load_market_analysis
from core.schemas import (
    ApplicationAdvice,
    ApplicationReport,
    FitAssessment,
    JobPosting,
    LegitimacyAssessment,
    LegitimacySignal,
    MarketAnalysis,
    ResumeData,
)
from core.tools import search_company, web_search, whois_lookup

logger = logging.getLogger("aip444")

web_search_tool = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for evidence about a company's legitimacy, web presence, official careers page, reviews, or recent coverage.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A targeted search query for legitimacy research.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

whois_lookup_tool = {
    "type": "function",
    "function": {
        "name": "whois_lookup",
        "description": "Look up WHOIS registration details for a domain. Use this to check whether a domain is established or very recently registered.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "A bare domain or website URL, such as 'example.com' or 'https://example.com/careers'.",
                }
            },
            "required": ["domain"],
            "additionalProperties": False,
        },
    },
}

legitimacy_tools = [web_search_tool, whois_lookup_tool]


def _log_cost(completion) -> None:
    cost = calculate_cost(completion.model_dump())
    logger.debug(
        "Cost: $%.6f | Tokens: %s",
        cost["total"],
        cost["tokens"]["total"],
    )


def _log_tool_call(name: str, args: dict) -> None:
    logger.debug("Tool call: %s", name)
    logger.debug("Arguments: %s", args)


def _tool_result_content(result) -> str:
    if isinstance(result, str):
        return result
    return json.dumps(result, indent=2)


def _fit_tier_from_score(score: int) -> str:
    if score >= 80:
        return "Strong fit"
    if score >= 50:
        return "Good fit"
    if score >= 30:
        return "Stretch"
    return "Growth target"


def _normalize_fit_assessment(fit: FitAssessment) -> FitAssessment:
    fit.tier = _fit_tier_from_score(fit.score)
    return fit


def _signal_badge_class(signal_type: str) -> str:
    normalized = signal_type.strip().lower()
    badge_classes = {
        "red": "signal-red",
        "green": "signal-green",
        "yellow": "signal-yellow",
        "red_flag": "signal-red",
        "green_flag": "signal-green",
        "yellow_flag": "signal-yellow",
    }
    return badge_classes.get(normalized, "signal-neutral")


def _signal_badge_label(signal_type: str) -> str:
    normalized = signal_type.strip().lower()
    badge_labels = {
        "red": "Red Flag",
        "green": "Green Flag",
        "yellow": "Yellow Flag",
        "red_flag": "Red Flag",
        "green_flag": "Green Flag",
        "yellow_flag": "Yellow Flag",
    }
    return badge_labels.get(normalized, "Signal")


def _fallback_legitimacy_assessment(reason: str) -> LegitimacyAssessment:
    return LegitimacyAssessment(
        verdict="Yellow",
        confidence_score=25,
        signals=[
            LegitimacySignal(
                signal_type="yellow",
                description="Investigation remained inconclusive",
                evidence=reason,
            )
        ],
        recommendation=(
            "Proceed cautiously. The legitimacy investigation was inconclusive, "
            "so verify the company's official site, careers page, and contact "
            "details before sharing sensitive information."
        ),
    )


def _fallback_fit_assessment(reason: str) -> FitAssessment:
    return _normalize_fit_assessment(
        FitAssessment(
            score=35,
            tier="Stretch",
            requirements_met=[
                "Fit assessment could not be completed automatically for this posting."
            ],
            requirements_gap=[
                "Review the posting manually because the automated fit analysis failed."
            ],
            overall_assessment=(
                "Automated fit analysis was unavailable, so this is a conservative placeholder "
                "score. Review the posting and your resume manually before deciding how strongly "
                "to prioritize this application."
            ),
        )
    )


def _fallback_application_advice(reason: str) -> ApplicationAdvice:
    note = f"Automated advice generation was unavailable: {reason}"
    return ApplicationAdvice(
        resume_adaptation=[
            "Review the job's required skills and manually move the most relevant matching experience higher on your resume.",
            note,
        ],
        cover_letter_guidance=[
            "Keep the cover letter specific to the company, role, and your most relevant evidence.",
            note,
        ],
        interview_prep_questions=[
            "Why are you interested in this role and how does your experience align with it?",
            note,
        ],
        interview_prep_skills_to_review=[
            "Review the posting's required skills and responsibilities manually.",
            note,
        ],
        interview_prep_company_research=[
            "Verify the company's official website, products, and recent news before interviewing.",
            note,
        ],
        interview_prep_talking_points=[
            "Prepare two or three concrete examples showing relevant project or work impact.",
            note,
        ],
    )


def _fallback_company_research(reason: str) -> str:
    return (
        "Company research could not be completed automatically. "
        f"Reason: {reason}. Verify the company's official website, careers page, "
        "LinkedIn presence, and recent news manually."
    )


def _read_required_inputs(
    market_path: str = "data/analysis/market-analysis.json",
    resume_path: str = "data/resume/resume.json",
) -> tuple[MarketAnalysis, ResumeData]:
    missing = []
    if not Path(market_path).exists():
        missing.append(
            f"- Missing `{market_path}`. Run Phase 1 first to generate the market analysis."
        )
    if not Path(resume_path).exists():
        missing.append(
            f"- Missing `{resume_path}`. Run Phase 2 first to extract and save your resume data."
        )
    if missing:
        raise FileNotFoundError(
            "Phase 3 requires Phase 1 and Phase 2 outputs:\n" + "\n".join(missing)
        )
    return load_market_analysis(market_path), load_resume_data(resume_path)


async def run_legitimacy_agent(
    posting: JobPosting,
    raw_posting_text: str,
    market_analysis: MarketAnalysis,
    company_research: str,
) -> LegitimacyAssessment:
    system_prompt = get_file_contents("src/prompts/legitimacy_agent_system_prompt.md")
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "Assess whether this job posting appears legitimate.\n\n"
                "Raw posting text from the PDF:\n"
                f"{raw_posting_text}\n\n"
                "Job posting:\n"
                f"{posting.model_dump_json(indent=2)}\n\n"
                "Relevant market analysis:\n"
                f"{market_analysis.model_dump_json(indent=2)}\n\n"
                "Initial company research summary:\n"
                f"{company_research}"
            ),
        },
    ]

    max_iterations = 6
    iteration = 0
    final_prompt_added = False

    try:
        while iteration < max_iterations:
            iteration += 1
            force_final_response = iteration == max_iterations

            if force_final_response and not final_prompt_added:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Return a final LegitimacyAssessment now using only the "
                            "evidence gathered so far. Do not request more tool calls. "
                            "If the company identity is ambiguous or multiple real "
                            "companies share the same name, explicitly say so, use a "
                            "Yellow verdict unless there is stronger evidence otherwise, "
                            "and lower the confidence_score to reflect the unresolved ambiguity. "
                            "For every signal, set signal_type to exactly one of: "
                            "'red', 'green', or 'yellow'."
                        ),
                    }
                )
                final_prompt_added = True

            completion_kwargs = {
                "model": MODEL,
                "messages": messages,
                "response_format": LegitimacyAssessment,
            }
            if not force_final_response:
                completion_kwargs["tools"] = legitimacy_tools

            completion = await client.beta.chat.completions.parse(**completion_kwargs)

            _log_cost(completion)
            message = completion.choices[0].message

            if message.parsed:
                return message.parsed

            if message.tool_calls and not force_final_response:
                messages.append(message)
                for tool_call in message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    _log_tool_call(tool_call.function.name, args)

                    if tool_call.function.name == "web_search":
                        result = web_search(args["query"])
                    elif tool_call.function.name == "whois_lookup":
                        result = whois_lookup(args["domain"])
                    else:
                        result = {"error": f"Unknown tool {tool_call.function.name}"}

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": _tool_result_content(result),
                        }
                    )
                continue

            break
    except Exception as e:
        logger.debug("Legitimacy agent degraded gracefully: %s", e)
        return _fallback_legitimacy_assessment(
            f"The investigation could not be completed cleanly: {e}"
        )

    return _fallback_legitimacy_assessment(
        "The investigation did not converge to a final answer. Available evidence "
        "was insufficient to resolve the company identity or confirm legitimacy."
    )


async def assess_fit(
    posting: JobPosting,
    resume_data: ResumeData,
    market_analysis: MarketAnalysis,
) -> FitAssessment:
    try:
        system_prompt = get_file_contents("src/prompts/fit_assessment_system_prompt.md")
        completion = await client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Evaluate candidate fit for this posting.\n\n"
                        "Job posting:\n"
                        f"{posting.model_dump_json(indent=2)}\n\n"
                        "Resume data:\n"
                        f"{resume_data.model_dump_json(indent=2)}\n\n"
                        "Market analysis:\n"
                        f"{market_analysis.model_dump_json(indent=2)}"
                    ),
                },
            ],
            response_format=FitAssessment,
        )
        _log_cost(completion)
        return _normalize_fit_assessment(completion.choices[0].message.parsed)
    except Exception as e:
        logger.debug("Fit assessment degraded gracefully: %s", e)
        return _fallback_fit_assessment(f"Fit assessment failed: {e}")


async def generate_application_advice(
    posting: JobPosting,
    resume_data: ResumeData,
    market_analysis: MarketAnalysis,
    company_research: str,
    fit_assessment: FitAssessment,
    legitimacy: LegitimacyAssessment,
) -> ApplicationAdvice:
    try:
        system_prompt = get_file_contents("src/prompts/application_advisor_system_prompt.md")
        completion = await client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Create tailored application advice for this opportunity.\n\n"
                        "Job posting:\n"
                        f"{posting.model_dump_json(indent=2)}\n\n"
                        "Resume data:\n"
                        f"{resume_data.model_dump_json(indent=2)}\n\n"
                        "Market analysis:\n"
                        f"{market_analysis.model_dump_json(indent=2)}\n\n"
                        "Company research summary:\n"
                        f"{company_research}\n\n"
                        "Fit assessment:\n"
                        f"{fit_assessment.model_dump_json(indent=2)}\n\n"
                        "Legitimacy assessment:\n"
                        f"{legitimacy.model_dump_json(indent=2)}"
                    ),
                },
            ],
            response_format=ApplicationAdvice,
        )
        _log_cost(completion)
        return completion.choices[0].message.parsed
    except Exception as e:
        logger.debug("Application advisor degraded gracefully: %s", e)
        return _fallback_application_advice(str(e))


def _clean_bullet(text: str) -> str:
    return re.sub(r"^\s*[-*•]+\s*", "", text).strip()


def _render_list(items: list[str]) -> str:
    return "".join(f"<li>{html.escape(_clean_bullet(item))}</li>" for item in items)


def render_application_report_html(
    report: ApplicationReport,
    posting: JobPosting,
) -> str:
    verdict_class = report.legitimacy.verdict.lower()
    signal_cards = "".join(
        (
            "<div class='signal-card'>"
            f"<span class='signal-type {_signal_badge_class(signal.signal_type)}'>"
            f"{html.escape(_signal_badge_label(signal.signal_type))}"
            "</span>"
            f"<h4>{html.escape(signal.description)}</h4>"
            f"<p>{html.escape(signal.evidence)}</p>"
            "</div>"
        )
        for signal in report.legitimacy.signals
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Application Report</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: #fffdf9;
      --ink: #1f2933;
      --muted: #5b6770;
      --border: #d9d2c3;
      --green: #2f6f4f;
      --yellow: #b7791f;
      --red: #b3432f;
      --accent: #154c79;
      --shadow: 0 18px 40px rgba(31, 41, 51, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, rgba(21, 76, 121, 0.16), transparent 30%),
        linear-gradient(180deg, #f8f4ec 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    .page {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 40px 20px 64px;
    }}
    .hero, section {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: var(--shadow);
    }}
    .hero {{
      padding: 28px;
      margin-bottom: 24px;
    }}
    .hero p {{
      color: var(--muted);
      margin-bottom: 0;
    }}
    section {{
      padding: 28px;
      margin-bottom: 20px;
    }}
    h1, h2, h3, h4 {{
      margin-top: 0;
    }}
    .eyebrow {{
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent);
      font-size: 0.8rem;
      font-weight: 700;
    }}
    .verdict-banner {{
      border-left: 8px solid var(--green);
      padding: 20px 22px;
      border-radius: 16px;
      background: rgba(47, 111, 79, 0.08);
      margin: 18px 0 22px;
    }}
    .verdict-banner.yellow {{
      border-left-color: var(--yellow);
      background: rgba(183, 121, 31, 0.12);
    }}
    .verdict-banner.red {{
      border-left-color: var(--red);
      background: rgba(179, 67, 47, 0.12);
    }}
    .verdict-row, .fit-row, .prep-grid, .signal-grid {{
      display: grid;
      gap: 16px;
    }}
    .verdict-row {{
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      align-items: start;
    }}
    .fit-row {{
      grid-template-columns: minmax(220px, 280px) 1fr;
      align-items: start;
    }}
    .prep-grid, .signal-grid {{
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }}
    .metric-card, .prep-card, .signal-card {{
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      background: #fff;
    }}
    .metric-value {{
      font-size: 2.8rem;
      line-height: 1;
      font-weight: 700;
      margin: 10px 0 4px;
    }}
    .metric-label, .muted {{
      color: var(--muted);
    }}
    .signal-type {{
      display: inline-block;
      margin-bottom: 10px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      background: #edf2f7;
    }}
    .signal-type.signal-red {{
      background: rgba(179, 67, 47, 0.14);
      color: var(--red);
    }}
    .signal-type.signal-green {{
      background: rgba(47, 111, 79, 0.14);
      color: var(--green);
    }}
    .signal-type.signal-yellow {{
      background: rgba(183, 121, 31, 0.14);
      color: var(--yellow);
    }}
    .signal-type.signal-neutral {{
      background: #edf2f7;
      color: var(--ink);
    }}
    ul {{
      margin: 0;
      padding-left: 22px;
    }}
    li + li {{
      margin-top: 10px;
    }}
    @media (max-width: 720px) {{
      .page {{
        padding: 20px 14px 40px;
      }}
      section, .hero {{
        padding: 20px;
        border-radius: 16px;
      }}
      .fit-row {{
        grid-template-columns: 1fr;
      }}
      .metric-value {{
        font-size: 2.2rem;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="hero">
      <div class="eyebrow">Phase 3 Application Advisor</div>
      <h1>{html.escape(posting.job_title)} at {html.escape(posting.company)}</h1>
      <p>{html.escape(posting.location or "Location not specified")} | {html.escape(posting.remote or "Work mode not specified")}</p>
    </div>

    <section>
      <div class="eyebrow">Legitimacy Assessment</div>
      <div class="verdict-banner {html.escape(verdict_class)}">
        <div class="verdict-row">
          <div>
            <div class="metric-label">Verdict</div>
            <div class="metric-value">{html.escape(report.legitimacy.verdict)}</div>
          </div>
          <div>
            <div class="metric-label">Confidence</div>
            <div class="metric-value">{report.legitimacy.confidence_score}</div>
          </div>
        </div>
        <p>{html.escape(report.legitimacy.recommendation)}</p>
      </div>
      <div class="signal-grid">
        {signal_cards}
      </div>
    </section>

    <section>
      <div class="eyebrow">Fit Assessment</div>
      <div class="fit-row">
        <div class="metric-card">
          <div class="metric-label">Overall Score</div>
          <div class="metric-value">{report.fit.score}</div>
          <h3>{html.escape(report.fit.tier)}</h3>
        </div>
        <div class="metric-card">
          <h3>Assessment</h3>
          <p>{html.escape(report.fit.overall_assessment)}</p>
          <h4>Requirements Met</h4>
          <ul>{_render_list(report.fit.requirements_met)}</ul>
          <h4>Gaps To Address</h4>
          <ul>{_render_list(report.fit.requirements_gap)}</ul>
        </div>
      </div>
    </section>

    <section>
      <div class="eyebrow">Resume Adaptation</div>
      <ul>{_render_list(report.resume_adaptation)}</ul>
    </section>

    <section>
      <div class="eyebrow">Cover Letter Guidance</div>
      <ul>{_render_list(report.cover_letter_guidance)}</ul>
    </section>

    <section>
      <div class="eyebrow">Interview Prep</div>
      <div class="prep-grid">
        <div class="prep-card">
          <h3>Questions</h3>
          <ul>{_render_list(report.interview_prep_questions)}</ul>
        </div>
        <div class="prep-card">
          <h3>Skills To Review</h3>
          <ul>{_render_list(report.interview_prep_skills_to_review)}</ul>
        </div>
        <div class="prep-card">
          <h3>Company Research</h3>
          <ul>{_render_list(report.interview_prep_company_research)}</ul>
        </div>
        <div class="prep-card">
          <h3>Talking Points</h3>
          <ul>{_render_list(report.interview_prep_talking_points)}</ul>
        </div>
      </div>
    </section>
  </div>
</body>
</html>
"""


def save_application_report_html(
    report: ApplicationReport,
    posting: JobPosting,
    path: str = "reports/application-report.html",
) -> str:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_application_report_html(report, posting),
        encoding="utf-8",
    )
    return str(out_path)


async def build_application_report(pdf_path: str) -> str:
    market_analysis, resume_data = _read_required_inputs()
    raw_posting_text = extract_text_from_pdf(pdf_path)
    posting = await extract_job_posting(pdf_path)

    company_query = (
        f"{posting.company} official website LinkedIn recent news company overview"
    )
    try:
        _log_tool_call("search_company", {"query": company_query})
        company_research = search_company(company_query)
    except Exception as e:
        logger.debug("Company research degraded gracefully: %s", e)
        company_research = _fallback_company_research(str(e))

    legitimacy = await run_legitimacy_agent(
        posting=posting,
        raw_posting_text=raw_posting_text,
        market_analysis=market_analysis,
        company_research=company_research,
    )
    fit = await assess_fit(
        posting=posting,
        resume_data=resume_data,
        market_analysis=market_analysis,
    )
    advice = await generate_application_advice(
        posting=posting,
        resume_data=resume_data,
        market_analysis=market_analysis,
        company_research=company_research,
        fit_assessment=fit,
        legitimacy=legitimacy,
    )

    report = ApplicationReport(
        legitimacy=legitimacy,
        fit=fit,
        **advice.model_dump(),
    )
    return save_application_report_html(report, posting)
