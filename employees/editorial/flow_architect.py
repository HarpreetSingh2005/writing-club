import json

from models.perspective import WritingFlow
from state import State
from utils.ask_llm import ask_llm
from utils.prompt_loader import get_prompt
from utils.pipeline_logger import log_entry


def flow_architect(state: State):
    """LangGraph node: proposes a small article flow (outline) for user approval."""
    prompt = get_prompt(
        "flow_architect",
        summary=state["summary"],
        insights=json.dumps(state.get("curated_insights", []), ensure_ascii=False, indent=2),
        style_profile=json.dumps(state.get("style_profile", {}), ensure_ascii=False, indent=2),
        user_feedback=state.get("user_feedback", ""),
    )
    response = ask_llm(prompt=prompt, expect_json=True, task="outline")

    flow = WritingFlow(
        title_direction=response.get("title_direction", ""),
        tone=response.get("tone", ""),
        core_argument=response.get("core_argument", ""),
        sections=response.get("sections", []),
        approval_question=response.get(
            "approval_question",
            "Does this flow match what you wanted to write?",
        ),
    )

    return {
        "proposed_flow": flow,
        "next_action": "awaiting_flow_approval",
        "pipeline_log": [
            log_entry(
                "Flow Architect", "📐",
                f"Proposed '{flow.title_direction}' with {len(flow.sections)} sections",
                {
                    "tone": flow.tone,
                    "core_argument": flow.core_argument,
                    "sections": flow.sections,
                },
            )
        ],
    }
