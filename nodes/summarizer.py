from state import State
from llm import ask_llm
from utils.prompt_loader import get_prompt

# Reads:
#   transcript

# Writes:
#   summary

# Responsibility:
#   Produce a concise summary without introducing new information.

def summarize(state: State):
    prompt = get_prompt("summarizer", transcript = state["transcript"])

    summary = ask_llm(prompt=prompt)

    return{
        "summary": summary
    }