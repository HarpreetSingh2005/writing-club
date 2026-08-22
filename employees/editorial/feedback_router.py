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


def feedback_router(state: State):
    """
    LangGraph node: decides which team handles the user's feedback.
    Fast-paths for clean approvals (no feedback). Otherwise, asks the LLM to route.
    """
    review_stage = state.get("review_stage", "flow")
    user_feedback = (state.get("user_feedback") or "").strip()
    has_feedback = bool(user_feedback)

    # Fast-path: Flow approved with NO feedback → go straight to drafting
    if review_stage == "flow" and state.get("flow_approved") and not has_feedback:
        return {
            "feedback_route": "draft",
            "next_action": "drafting",
            "revision_count": 0,  # Reset counter for the new draft phase
            "pipeline_log": [
                log_entry("Feedback Router", "🔀", "Flow approved → drafting", {}),
            ],
        }

    # Fast-path: Draft approved with NO feedback → mark complete
    if review_stage == "draft" and state.get("article_approved") and not has_feedback:
        return {
            "feedback_route": "complete",
            "next_action": "complete",
            "pipeline_log": [
                log_entry("Feedback Router", "🔀", "Draft approved → complete", {}),
            ],
        }

    # LLM-assisted routing: user provided feedback (even if they also clicked approve)
    # Only send a short preview of the draft to save tokens — the router only needs
    # enough context to understand what the user is referring to, not the full text.
    draft_text = state.get("draft", "")
    draft_preview = draft_text[:500] + "..." if len(draft_text) > 500 else draft_text

    flow_data = state.get("proposed_flow")
    flow_preview = json.dumps(_jsonable(flow_data), ensure_ascii=False, indent=2) if flow_data else ""

    prompt = get_prompt(
        "feedback_router",
        review_stage=review_stage,
        approved=state.get("flow_approved", False) if review_stage == "flow" else state.get("article_approved", False),
        proposed_flow=flow_preview,
        draft=draft_preview,
        user_feedback=user_feedback,
    )
    response = ask_llm(prompt=prompt, expect_json=True, task="critique")
    route = response.get("route", "revise_flow")

    updates = {
        "feedback_route": route,
        "user_feedback": response.get("normalized_feedback", user_feedback),
        "next_action": route,
        "revision_count": state.get("revision_count", 0) + 1,
        "pipeline_log": [
            log_entry(
                "Feedback Router", "🔀",
                f"Routing to '{route}' (revision #{state.get('revision_count', 0) + 1})",
                {"reason": response.get("reason", ""), "feedback": response.get("normalized_feedback", "")},
            )
        ],
    }

    # Reset approval flags when routing back to earlier pipeline stages
    if route in {"revise_flow", "revise_style", "revise_research"}:
        updates["flow_approved"] = False
        updates["article_approved"] = False
    elif route in {"draft", "revise_draft"}:
        updates["flow_approved"] = True
        updates["article_approved"] = False

    return updates
