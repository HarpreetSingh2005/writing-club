from employees.research.expert_research import reports_to_json
from state import State
from utils.ask_llm import ask_llm
from utils.prompt_loader import get_prompt
from utils.pipeline_logger import log_entry


def insight_curator(state: State):
    prompt = get_prompt(
        "insight_curator",
        summary=state["summary"],
        reports=reports_to_json(state.get("research_reports", [])),
        user_feedback=state.get("user_feedback", ""),
    )
    insights = ask_llm(prompt=prompt, expect_json=True, task="critique")

    return {
        "curated_insights": insights,
        "pipeline_log": [
            log_entry(
                "Insight Curator", "✂️",
                f"Curated {len(insights)} key insights",
                {"insights": insights[:5]},
            )
        ],
    }
