from typing import TypedDict
from models.perspective import DiscoveredPerspective

class State(TypedDict):
    #User input
    raw_input: str

    #Transcription
    transcript: str

    #Intake Team
    summary: str

    #Planning Team
    discovered_perspectives: list[DiscoveredPerspective]
    matched_perspectives: list
    new_perspectives: list
    ranked_perspectives: list

    # Hiring
    employees: list

    # Research
    research_reports: list

    # Editorial
    draft: str