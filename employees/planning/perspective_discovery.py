from models.perspective import DiscoveredPerspective
from state import State
from utils.ask_llm import ask_llm
from utils.prompt_loader import get_prompt
from utils.pipeline_logger import log_entry

#Reads Summary and Writes Discovery_perspective

def perspective_discovery(state: State):
    prompt = get_prompt(
        "perspective_discovery",
        summary=state["summary"],
        transcript=state["transcript"],
    )

    response = ask_llm(prompt=prompt, expect_json=True, task="discovery")
    discovered_perspectives = [
        DiscoveredPerspective(
            name=p.get("name", ""),
            department=p.get("department", ""),
            reason=p.get("reason", "")
        )
        for p in response
    ]
    
    return {
        "discovered_perspectives": discovered_perspectives,
        "pipeline_log": [
            log_entry(
                "Perspective Discovery", "🔍",
                f"Found {len(discovered_perspectives)} perspectives",
                {"perspectives": [f"{p.name} ({p.department})" for p in discovered_perspectives]},
            )
        ],
    }
