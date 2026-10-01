from state import State
from utils.ask_llm import ask_llm
from utils.author_skill import load_author_skill
from utils.library import load_style, save_style
from utils.prompt_loader import get_prompt
from utils.pipeline_logger import log_entry


def _merge_lists(old: list, new: list) -> list:
    """
    Merge two lists of rules/items, keeping unique entries from both.
    New items are appended; duplicates (case-insensitive) are skipped.
    """
    seen = {item.strip().lower() for item in old}
    merged = list(old)
    for item in new:
        if item.strip().lower() not in seen:
            merged.append(item)
            seen.add(item.strip().lower())
    return merged


def _select_author_direction(state: State, detected_tone: str) -> dict:
    """
    Read the stable Author Skill and select only the tendencies relevant to the
    current article. Returns a dynamic per-article block:

        {"core_tendencies": [...], "optional_tools": [...], "avoid": [...]}

    The skill file itself is never modified.
    """
    skill = load_author_skill()
    prompt = get_prompt(
        "author_skill_selector",
        detected_tone=detected_tone,
        article_length=state.get("article_length", ""),
        summary=state["summary"],
        user_feedback=state.get("user_feedback", ""),
    )
    direction = ask_llm(
        prompt=f"{skill}\n\n---\n\n{prompt}",
        expect_json=True,
        task="style_learning",
    )
    if not isinstance(direction, dict):
        direction = {}
    return {
        "core_tendencies": direction.get("core_tendencies") or [],
        "optional_tools": direction.get("optional_tools") or [],
        "avoid": direction.get("avoid") or [],
    }


def style_librarian(state: State):
    """
    LangGraph node: detects the speaker's writing style from the transcript,
    merges it with any previously stored style profile to accumulate knowledge
    across multiple runs, and selects per-article author tendencies from the
    stable Author Skill into a dynamic author_skill block.
    """
    prompt = get_prompt(
        "style_detector",
        transcript=state["transcript"],
        summary=state["summary"],
        user_idea=state.get("user_idea", ""),
        article_length=state.get("article_length", ""),
        user_feedback=state.get("user_feedback", ""),
    )

    detected_profile = ask_llm(
        prompt=prompt,
        expect_json=True,
        task="style_learning",
    )
    style_name = detected_profile.get("style_name", "default")
    stored_profile = load_style(style_name)

    # The per-article author direction is never merged into the persistent style
    # profile, so it cannot accumulate across runs.
    stored_profile = {
        key: value for key, value in stored_profile.items() if key != "author_skill"
    }
    detected_profile = {
        key: value for key, value in detected_profile.items() if key != "author_skill"
    }

    # Smart merge: evolve lists (signature_rules, avoid) instead of overwriting
    merged_profile = {
        **stored_profile,
        **detected_profile,
        # Accumulate signature rules from both old and new detections
        "signature_rules": _merge_lists(
            stored_profile.get("signature_rules", []),
            detected_profile.get("signature_rules", []),
        ),
        # Accumulate avoid rules from both old and new detections
        "avoid": _merge_lists(
            stored_profile.get("avoid", []),
            detected_profile.get("avoid", []),
        ),
        # Track how many examples have contributed to this profile
        "examples_seen": stored_profile.get("examples_seen", 0) + 1,
    }
    save_style(style_name, merged_profile)

    # Dynamic per-article Author Skill direction rides in this run's profile only.
    author_direction = _select_author_direction(state, detected_profile.get("tone", ""))
    style_profile = {
        **merged_profile,
        "author_skill": author_direction,
    }

    return {
        "writing_style": style_name,
        "style_profile": style_profile,
        "pipeline_log": [
            log_entry(
                "Style Librarian", "🎨",
                f"Detected style: '{style_name}' (examples seen: {merged_profile['examples_seen']})",
                {
                    "tone": merged_profile.get("tone", "?"),
                    "pacing": merged_profile.get("pacing", "?"),
                    "narrative_distance": merged_profile.get("narrative_distance", "?"),
                    "signature_rules_count": len(merged_profile.get("signature_rules", [])),
                    "avoid_count": len(merged_profile.get("avoid", [])),
                    "author_core_tendencies": len(author_direction.get("core_tendencies", [])),
                    "author_optional_tools": len(author_direction.get("optional_tools", [])),
                    "author_avoid": len(author_direction.get("avoid", [])),
                },
            )
        ],
    }
