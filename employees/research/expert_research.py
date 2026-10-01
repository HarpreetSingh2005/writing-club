import json
from dataclasses import asdict

from config.env import Env
from models.perspective import ExpertReport
from state import State
from utils.ask_llm import ask_llm
from utils.library import load
from utils.pipeline_logger import log_entry
from utils.prompt_loader import get_prompt
from utils.searx_client import SearchUnavailableError, search_searxng

# Hard, code-enforced limits on the researcher's optional web-search loop.
MAX_QUERIES_PER_RESEARCHER = 3
MAX_INITIAL_QUERIES = 2
MAX_FOLLOWUP_QUERIES = 1
MAX_RESULTS_PER_QUERY = 5
MAX_SOURCES_PER_REPORT = 10

# Synthesis output (report + web_sources + follow_up_queries) is larger than the
# default research token limit, so the synthesis call gets its own explicit cap.
SYNTHESIS_MAX_TOKENS = 4000


def _perspective_fields(perspective):
    """Return (name, department) for a DiscoveredPerspective or its dict form."""
    if isinstance(perspective, dict):
        return perspective.get("name", "") or "", perspective.get("department", "") or ""
    return (perspective.name or "", perspective.department or "")


def _response_dict(response):
    """Guard against non-dict LLM responses."""
    return response if isinstance(response, dict) else {}


def _build_report(response) -> ExpertReport:
    """Construct an ExpertReport from a dict (analyst or synthesis output)."""
    response = _response_dict(response)
    return ExpertReport(
        perspective=str(response.get("perspective", "") or ""),
        department=str(response.get("department", "") or ""),
        key_observations=list(response.get("key_observations") or []),
        risks_or_blindspots=list(response.get("risks_or_blindspots") or []),
        writing_suggestions=list(response.get("writing_suggestions") or []),
        web_sources=list(response.get("web_sources") or []),
    )


def _run_queries(query_tasks: list[dict]) -> tuple[list[dict], bool]:
    """
    Execute a list of {"query": ..., "reason": ...} tasks against SearXNG.

    Returns (evidence, any_success) where evidence is a list of per-query records:
        [{"query", "reason", "results": [...]}]
    A failed query yields an empty "results" list and never raises.
    """
    evidence = []
    any_success = False

    for task in query_tasks:
        query = (task.get("query") or "").strip()
        if not query:
            continue

        try:
            results = search_searxng(query, max_results=MAX_RESULTS_PER_QUERY)
            any_success = True
        except SearchUnavailableError:
            results = []

        evidence.append({
            "query": query,
            "reason": task.get("reason", "") or "",
            "results": results,
        })

    return evidence, any_success


def _evidence_for_prompt(evidence: list[dict]) -> str:
    """Serialize executed searches into the compact evidence block shown to the researcher."""
    return json.dumps(evidence, ensure_ascii=False, indent=2)


def _synthesize(
    analyst: dict,
    perspective: str,
    department: str,
    department_description: str,
    state: State,
    evidence: list[dict],
) -> tuple[dict, list[dict]]:
    """Synthesis call: merge the analytical draft with web evidence. Returns (report_dict, follow_up_queries)."""
    prompt = get_prompt(
        "expert_researcher_synthesis",
        department=department,
        perspective=perspective,
        department_description=department_description,
        summary=state["summary"],
        transcript=state["transcript"],
        user_feedback=state.get("user_feedback", ""),
        draft=json.dumps(analyst, ensure_ascii=False, indent=2),
        web_evidence=_evidence_for_prompt(evidence),
    )
    response = _response_dict(
        ask_llm(prompt=prompt, expect_json=True, task="research", max_tokens=SYNTHESIS_MAX_TOKENS)
    )

    follow_up = response.get("follow_up_queries") or []
    if not isinstance(follow_up, list):
        follow_up = []

    return response, follow_up


def _ground_sources(sources, evidence: list[dict]) -> list[dict]:
    """
    Code-enforced source grounding:
    - only URLs that were actually returned by SearXNG may remain
    - capped at MAX_SOURCES_PER_REPORT
    """
    returned_urls = {result.get("url") for item in evidence for result in item.get("results", [])}

    grounded = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        url = source.get("url") or ""
        if url not in returned_urls:
            continue
        grounded.append({
            "title": source.get("title") or "",
            "url": url,
            "snippet": source.get("snippet") or "",
            "engine": source.get("engine") or "",
            "query": source.get("query") or "",
            "reason": source.get("reason") or "",
        })
        if len(grounded) >= MAX_SOURCES_PER_REPORT:
            break

    return grounded


def _research_one_perspective(perspective, state: State) -> tuple[ExpertReport, list[dict]]:
    """Run the full Think → (optionally search) → Report flow for a single perspective."""
    perspective_name, department = _perspective_fields(perspective)

    department_description = ""
    try:
        department_description = load(department).description
    except Exception:
        department_description = "Use the broad reasoning style of this department."

    # 1. Analytical call: reason first, optionally plan a search.
    analyst_prompt = get_prompt(
        "expert_researcher",
        department=department,
        perspective=perspective_name,
        department_description=department_description,
        summary=state["summary"],
        transcript=state["transcript"],
        user_feedback=state.get("user_feedback", ""),
    )
    analyst = _response_dict(ask_llm(prompt=analyst_prompt, expect_json=True, task="research"))

    search_plan = analyst.get("search_plan") or []
    if not isinstance(search_plan, list):
        search_plan = []

    # No web research required → the analytical draft is the final report.
    if not search_plan:
        return _build_report(analyst), []

    # SearXNG not configured → proceed without web research.
    if not Env.SEARXNG_ENABLED:
        unavailable_log = log_entry(
            "Web Search", "🔎",
            "Web search skipped — SearXNG not configured (continuing with analytical research)",
            {},
        )
        return _build_report(analyst), [unavailable_log]

    # 2. Run the initial (up to 2) planned queries.
    initial_queries = search_plan[:MAX_INITIAL_QUERIES]
    evidence, any_success = _run_queries(initial_queries)

    # All searches failed → fall back to the pure analytical report.
    if not any_success:
        unavailable_log = log_entry(
            "Web Search", "🔎",
            "Web search unavailable — continuing with analytical research",
            {},
        )
        return _build_report(analyst), [unavailable_log]

    # 3. Synthesis: merge evidence into the final report.
    report, follow_up_queries = _synthesize(
        analyst, perspective_name, department, department_description, state, evidence
    )
    queries_run = len(evidence)

    # 4. Optional single follow-up search (hard-capped by Python).
    follow_up_queries = (follow_up_queries or [])[:MAX_FOLLOWUP_QUERIES]
    if follow_up_queries and queries_run < MAX_QUERIES_PER_RESEARCHER:
        follow_up_tasks = [follow_up_queries[0]]
        follow_evidence, _ = _run_queries(follow_up_tasks)
        evidence.extend(follow_evidence)
        queries_run = len(evidence)

        report, _ = _synthesize(
            analyst, perspective_name, department, department_description, state, evidence
        )

        follow_log = log_entry(
            "Web Search", "🔎",
            f"Web search: {len(follow_up_tasks)} follow-up query",
            {},
        )
    else:
        follow_log = None

    # 5. Ground sources to URLs that SearXNG actually returned, then build the report.
    report["web_sources"] = _ground_sources(report.get("web_sources") or [], evidence)
    source_count = len(report["web_sources"])

    web_logs = []
    if follow_log:
        web_logs.append(follow_log)
    web_logs.append(
        log_entry(
            "Web Search", "🔎",
            f"Web search: {queries_run} queries, {source_count} sources used",
            {"queries": queries_run, "sources": source_count},
        )
    )

    return _build_report(report), web_logs


def expert_research(state: State):
    reports: list[ExpertReport] = []
    logs: list[dict] = []

    for perspective in state["discovered_perspectives"]:
        report, report_logs = _research_one_perspective(perspective, state)
        reports.append(report)
        logs.extend(report_logs)

    logs.append(
        log_entry(
            "Expert Research", "🧪",
            f"Generated {len(reports)} expert reports",
            {"experts": [f"{r.perspective} ({r.department})" for r in reports]},
        )
    )

    return {
        "research_reports": reports,
        "pipeline_log": logs,
    }


def reports_to_json(reports: list[ExpertReport]) -> str:
    return json.dumps([asdict(report) for report in reports], ensure_ascii=False, indent=2)