# AI Job Application Assistant

A 3-phase AI pipeline that analyzes job postings, evaluates resume fit against
aggregated market data, screens postings for legitimacy, and generates tailored
application guidance; using structured LLM extraction and an agentic legitimacy check.

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your API keys:
```bash
OPENROUTER_API_KEY=
TAVILY_API_KEY=
```

3. Place raw job posting PDFs in `raw-postings/` (for Phase 1) and your resume PDF in `raw-resume/` (for Phase 2). Neither folder is committed to git, since this is personal data.

## Phases 1 & 2: Market Analysis + Resume Gap Analysis
Run the full setup pipeline with:
```bash
python main.py
```
This processes all postings in `raw-postings/`, generates a market analysis, extracts your resume (auto-detected from `raw-resume/`), and produces a gap analysis.

Add `--verbose` to see extraction decisions, tool calls, and cost at each step.

Useful flags:
- `--resume <path>` - use a specific resume PDF instead of auto-detecting
- `--postings-dir <path>` - use a different postings folder
- `--skip-postings` - reuse existing market analysis, skip re-processing postings
- `--skip-resume` - reuse existing resume data, skip re-extraction

Outputs: `data/analysis/market-analysis.json`, `reports/market-analysis.md`, `data/resume/resume.json`, `data/analysis/gap-analysis.json`, `reports/gap-analysis.md`

## Phase 3: Application Advisor
Requires Phases 1 and 2 to have been run first (uses their output).

```bash
python advise.py <path-to-new-posting.pdf>
```

Add `--verbose` to see legitimacy signals, tool calls, and scoring breakdown.

Output: `reports/application-report.html`