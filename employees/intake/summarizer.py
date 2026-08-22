from state import State
from utils.ask_llm import ask_llm
from utils.prompt_loader import get_prompt
from utils.pipeline_logger import log_entry

# Reads:
#   transcript

# Writes:
#   summary

# Responsibility:
#   Produce a concise summary without introducing new information.

def summarize(state: State):
    prompt = get_prompt("summarizer", transcript = state["transcript"])

    summary = ask_llm(prompt=prompt, task="summarization")

    return{
        "summary": summary,
        "pipeline_log": [
            log_entry(
                "Summarizer", "📝",
                f"Cleaned transcript → {len(summary.split())} words",
                {"preview": summary},
            )
        ],
    }
