from models.perspective import DiscoveredPerspective
from state import State
from utils.ask_llm import ask_llm
from utils.prompt_loader import get_prompt

#Reads Summary and Writes Discovery_perspective

def perspective_discovery(state: State):
    prompt = get_prompt("perspective_discovery",summary = state["summary"])

    response = ask_llm(prompt=prompt, expect_json=True)
    
    discovered_perspectives = [
        DiscoveredPerspective(
            name=item["name"],
            reason=item["reason"]
        )
        for item in response
    ]
    
    return {
        "discovered_perspectives": discovered_perspectives
    }