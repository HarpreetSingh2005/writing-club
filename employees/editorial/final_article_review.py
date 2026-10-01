import json

from state import State
from utils.ask_llm import ask_llm
from utils.prompt_loader import get_prompt
from utils.pipeline_logger import log_entry


def final_article_review(state: State):
    """
    Reviews the approved article against the original brief and stores the
    outcome in the current project's final review for the project archive.
    This is project-level post-production review only: it does not modify,
    store, or propose system-level prompt/code/pipeline learning.
    """
    prompt = get_prompt(
        "final_article_review",
        user_idea=state.get("user_idea", ""),
        article_length=state.get("article_length", ""),
        summary=state.get("summary", ""),
        style_profile=json.dumps(state.get("style_profile", {}), ensure_ascii=False, indent=2),
        pipeline_log=json.dumps(state.get("pipeline_log", []), ensure_ascii=False, indent=2),
        draft=state.get("draft", ""),
    )

    review = ask_llm(prompt=prompt, expect_json=True, task="critique")

    return {
        "final_review": review,
        "next_action": "complete",
        "pipeline_log": [
            log_entry(
                "Final Article Review", "🗂️",
                "Stored final review notes in the project archive",
                {
                    "went_well": review.get("went_well", []),
                    "needs_redo": review.get("needs_redo", []),
                },
            )
        ],
    }