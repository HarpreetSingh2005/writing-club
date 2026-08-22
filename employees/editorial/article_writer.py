import json
from dataclasses import asdict, is_dataclass

from state import State
from utils.ask_llm import ask_llm
from utils.prompt_loader import get_prompt
from utils.pipeline_logger import log_entry


def _jsonable(value):
    """Convert dataclass instances to dicts for JSON serialization."""
    if is_dataclass(value):
        return asdict(value)
    return value


def article_writer(state: State):
    """
    LangGraph node: drafts the full article using the approved flow,
    summary, perspectives, expert research, curated insights, and style profile.
    """
    if not state.get("flow_approved"):
        return {
            "draft": "",
            "next_action": "awaiting_flow_approval",
        }

    # Serialize perspectives and research reports for the prompt
    perspectives = [_jsonable(p) for p in state.get("discovered_perspectives", [])]
    research_reports = [_jsonable(r) for r in state.get("research_reports", [])]

    prompt = get_prompt(
        "article_writer",
        summary=state["summary"],
        flow=json.dumps(_jsonable(state["proposed_flow"]), ensure_ascii=False, indent=2),
        style_profile=json.dumps(state.get("style_profile", {}), ensure_ascii=False, indent=2),
        perspectives=json.dumps(perspectives, ensure_ascii=False, indent=2),
        research_reports=json.dumps(research_reports, ensure_ascii=False, indent=2),
        insights=json.dumps(state.get("curated_insights", []), ensure_ascii=False, indent=2),
        user_feedback=state.get("user_feedback", ""),
    )
    draft = ask_llm(prompt=prompt, temperature=0.8, task="drafting")

    return {
        "draft": draft,
        "next_action": "review_draft",
        "pipeline_log": [
            log_entry(
                "Article Writer", "✍️",
                f"Drafted article ({len(draft.split())} words)",
                {"preview": draft},
            )
        ],
    }
