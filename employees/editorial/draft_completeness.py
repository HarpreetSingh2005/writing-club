"""
Draft Completeness Gate.

Runs between the Article Writer and the Auto Draft Critic. Detects obvious
truncation / incomplete drafts so a known-broken draft never reaches the normal
critic loop or the human reviewer as a normal candidate.

A separate, small retry budget is used: a truncated draft is regenerated
immediately WITHOUT consuming an auto-revision (MAX_AUTO_REVISIONS). Only if
the regeneration also fails is the draft surfaced to human review, clearly
marked as incomplete.
"""

import re

from state import State
from utils.pipeline_logger import log_entry

# Separate budget for generation failures/truncation (per regeneration cycle).
MAX_TRUNCATION_RETRIES = 1

# Terminal sentence punctuation accepted at the end of a finished draft.
_TERMINAL_PUNCTUATION = (".", "!", "?", "…")

# Very short target minimum fraction of the requested word count. A draft well
# below this is either truncated or failed to develop the source.
_MIN_LENGTH_FRACTION = 0.35

# Words that are not meaningful content anchors for the final flow beat.
_FLOW_STOPWORDS = {
    "section", "beat", "step", "begin", "beginning", "start", "starting",
    "end", "ending", "conclude", "concluding", "conclusion", "reach", "reaching",
    "with", "that", "this", "these", "those", "the", "and", "for", "not",
    "into", "onto", "their", "there", "using", "use", "about", "from", "when",
    "what", "who", "whom", "which", "where", "then", "after", "before", "also",
}


def _parse_word_target(article_length: str | None) -> int | None:
    """Parse the requested word count (e.g. '500' or 'about 800 words')."""
    if not article_length:
        return None
    try:
        return int(str(article_length).strip().split()[0])
    except (ValueError, IndexError):
        return None


def _ends_with_terminal_punctuation(text: str) -> bool:
    """True if the text ends on a sentence-level stop."""
    text = text.rstrip()
    if not text:
        return False
    stripped = text.rstrip("\"'”’»)]}>")
    if not stripped:
        return False
    return stripped.endswith(_TERMINAL_PUNCTUATION) or stripped.endswith("...")


def _proposed_sections(flow) -> list[str]:
    """Extract the flow's section beats from a WritingFlow or dict."""
    if not flow:
        return []
    if isinstance(flow, dict):
        return flow.get("sections") or []
    return getattr(flow, "sections", None) or []


def _final_flow_beat_anchors(sections: list[str]) -> list[str]:
    """
    Pull a few distinctive content words from the LAST non-empty flow beat,
    to detect whether the realization/ending of the flow was reached.
    """
    last = ""
    for section in reversed(sections):
        section = (section or "").strip()
        if section:
            last = section
            break
    if not last:
        return []

    tokens = re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*", last)
    candidates: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        t = token.strip(".,!?;:()'\"“”‘’").lower()
        if len(t) >= 5 and t not in _FLOW_STOPWORDS and t not in seen:
            seen.add(t)
            candidates.append(t)

    # Longest, most distinctive words first.
    candidates.sort(key=len, reverse=True)
    return candidates[:6]


def _completeness_issues(state: State, draft: str) -> list[str]:
    """Return a list of detected completeness problems (empty == complete)."""
    draft = draft.strip()
    if not draft:
        return ["draft is empty"]

    issues: list[str] = []

    target = _parse_word_target(state.get("article_length", ""))
    if target and target > 0:
        word_count = len(draft.split())
        if word_count < int(target * _MIN_LENGTH_FRACTION):
            issues.append(
                f"draft too short ({word_count} words vs target ~{target})"
            )

    if not _ends_with_terminal_punctuation(draft):
        issues.append("draft ends without terminal punctuation (likely cut off)")

    anchors = _final_flow_beat_anchors(_proposed_sections(state.get("proposed_flow")))
    if anchors:
        haystack = " ".join(re.findall(r"[A-Za-z]+", draft.lower()))
        if not any(anchor in haystack for anchor in anchors):
            issues.append("draft does not reach the final flow beat / realization")

    return issues


def draft_completeness_check(state: State):
    """
    LangGraph node: gates a generated draft before the Auto Draft Critic.
    - Complete draft      → 'auto draft critic'
    - Incomplete + budget → 'article writer' (regenerate; no auto-revision consumed)
    - Incomplete, exhausted → 'article approval' flagged requires_human_review
    """
    draft = (state.get("draft") or "").strip()
    issues = _completeness_issues(state, draft)

    if not issues:
        return {
            "next_action": "auto draft critic",
            "truncation_retry_count": 0,
            "incomplete_draft_reason": "",
            "pipeline_log": [
                log_entry(
                    "Draft Completeness Check", "🧩",
                    "Draft complete - proceeding to Auto Draft Critic",
                    {},
                )
            ],
        }

    reason = "; ".join(issues)
    retries = state.get("truncation_retry_count", 0)

    if retries < MAX_TRUNCATION_RETRIES:
        new_retries = retries + 1
        print(
            f"\n[!] Incomplete draft detected ({reason})\n"
            f"    Regenerating draft (truncation retry {new_retries}/{MAX_TRUNCATION_RETRIES}) - "
            "NOT consuming an auto-revision.\n"
        )
        return {
            "truncation_retry_count": new_retries,
            "next_action": "draft_truncated_retry",
            "incomplete_draft_reason": reason,
            "pipeline_log": [
                log_entry(
                    "Draft Completeness Check", "🧩",
                    f"Incomplete draft - regenerating (retry {new_retries}/{MAX_TRUNCATION_RETRIES})",
                    {"issues": issues},
                )
            ],
        }

    print(
        f"\n[X] Draft still incomplete after retries - requiring human review.\n"
        f"    Issues: {reason}\n"
    )
    return {
        "truncation_retry_count": 0,
        "incomplete_draft_reason": reason,
        "requires_human_review": True,
        "next_action": "article approval",
        "pipeline_log": [
            log_entry(
                "Draft Completeness Check", "🧩",
                "Draft still incomplete after retries - surfacing to human review",
                {"issues": issues},
            )
        ],
    }