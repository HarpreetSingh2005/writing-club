from state import State
from models.perspective import Department, DiscoveredPerspective

from utils.prompt_loader import get_prompt
from utils.ask_llm import ask_llm
from utils.library import exists, load, save
from utils.pipeline_logger import log_entry


def librarian(state: State):
    departments_topics: dict[str, list[DiscoveredPerspective]] = {}
    new_departments: list[str] = []

    for perspective in state["discovered_perspectives"]:
        if isinstance(perspective, dict):
            p_obj = DiscoveredPerspective(
                name=perspective.get("name", ""),
                department=perspective.get("department", ""),
                reason=perspective.get("reason", "")
            )
        else:
            p_obj = perspective

        dept_name = p_obj.department
        persp_name = p_obj.name
        if not dept_name or not persp_name:
            continue

        # Group by department
        if dept_name not in departments_topics:
            departments_topics[dept_name] = []
        departments_topics[dept_name].append(p_obj)

        # Check library room database
        if exists(dept_name):
            dept_obj = load(dept_name)
            # If the particular sub-department not found, append it
            if persp_name not in dept_obj.sub_departments:
                dept_obj.sub_departments.append(persp_name)
                save(dept_obj)
        else:
            prompt = get_prompt("library_manager", department_name=dept_name)
            response = ask_llm(prompt=prompt, expect_json=True, task="discovery")
            print(f"Generated new department metadata: {response}")

            # Do not guess other sub-departments; initialize with only the discovered perspective
            dept_obj = Department(
                name=response.get("name", dept_name),
                description=response.get("description", ""),
                sub_departments=[persp_name]
            )
            save(dept_obj)
            new_departments.append(dept_name)

    return {
        "departments_topics": departments_topics,
        "new_department": new_departments,
        "pipeline_log": [
            log_entry(
                "Librarian", "📚",
                f"Organized {len(departments_topics)} departments, {len(new_departments)} new",
                {
                    "departments": list(departments_topics.keys()),
                    "new_departments": new_departments,
                },
            )
        ],
    }
