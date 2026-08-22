import json
from dataclasses import asdict

from models.perspective import ExpertReport
from state import State
from utils.ask_llm import ask_llm
from utils.library import load
from utils.prompt_loader import get_prompt
from utils.pipeline_logger import log_entry


def expert_research(state: State):
    reports: list[ExpertReport] = []

    for perspective in state["discovered_perspectives"]:
        if isinstance(perspective, dict):
            perspective_name = perspective.get("name", "")
            department = perspective.get("department", "")
        else:
            perspective_name = perspective.name
            department = perspective.department

        department_description = ""

        try:
            department_description = load(department).description
        except Exception:
            department_description = "Use the broad reasoning style of this department."

        prompt = get_prompt(
            "expert_researcher",
            department=department,
            perspective=perspective_name,
            department_description=department_description,
            summary=state["summary"],
            user_feedback=state.get("user_feedback", ""),
        )
        response = ask_llm(prompt=prompt, expect_json=True, task="research")

        reports.append(
            ExpertReport(
                perspective=response.get("perspective", perspective_name),
                department=response.get("department", department),
                key_observations=response.get("key_observations", []),
                risks_or_blindspots=response.get("risks_or_blindspots", []),
                writing_suggestions=response.get("writing_suggestions", []),
            )
        )

    return {
        "research_reports": reports,
        "pipeline_log": [
            log_entry(
                "Expert Research", "🧪",
                f"Generated {len(reports)} expert reports",
                {"experts": [f"{r.perspective} ({r.department})" for r in reports]},
            )
        ],
    }


def reports_to_json(reports: list[ExpertReport]) -> str:
    return json.dumps([asdict(report) for report in reports], ensure_ascii=False, indent=2)
