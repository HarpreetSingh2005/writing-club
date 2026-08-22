from state import State
from utils.ask_llm import ask_llm
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


def style_librarian(state: State):
    """
    LangGraph node: detects the speaker's writing style from the transcript,
    then merges it with any previously stored style profile to accumulate
    knowledge across multiple runs.
    """
    prompt = get_prompt(
        "style_detector",
        transcript=state["transcript"],
        summary=state["summary"],
        user_feedback=state.get("user_feedback", ""),
    )

    detected_profile = ask_llm(
        prompt=prompt,
        expect_json=True,
        task="style_learning",
    )
    style_name = detected_profile.get("style_name", "default")
    stored_profile = load_style(style_name)

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

    return {
        "writing_style": style_name,
        "style_profile": merged_profile,
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
                },
            )
        ],
    }
