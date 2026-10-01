import operator
from typing import Annotated, TypedDict

from models.perspective import DiscoveredPerspective, ExpertReport, WritingFlow

class State(TypedDict):
    # User's explicit article brief from the intake form
    user_idea: str

    # Retained for backward compatibility only. Tone is no longer a user-controlled
    # writing requirement: it emerges from the source, the Author Skill, and the subject.
    requested_tone: str

    # Target article length requested by the user
    article_length: str

    # Path to the input audio file (if blank, system assumes text transcript input directly)
    audio_file_path: str

    # Raw transcript content (either generated from audio or pasted by user)
    transcript: str

    # Cleaned, structured version of transcript created by the Summarizer
    summary: str

    # List of perspectives discovered from the summary (Planning team)
    discovered_perspectives: list[DiscoveredPerspective]
    
    # Perspective entries sorted by library departments
    departments_topics: dict[str, list[DiscoveredPerspective]]
    
    # Names of new departments created by planning agents during execution
    new_department: list[str]   
    
    # Inferred writing style name matching a style profile
    writing_style: str
    
    # Dictionary of rules/properties for the target voice and pacing
    style_profile: dict
    
    # The editorial plan/structure of the article proposed to the user
    proposed_flow: WritingFlow
    
    # Feedback provided by the user during flow or draft approval phases
    user_feedback: str
    
    # Flag indicating whether the user approved the proposed flow/structure
    flow_approved: bool
    
    # Flag indicating whether the user approved the final drafted article
    article_approved: bool
    
    # Tracks the current phase under review ("flow" or "draft")
    review_stage: str
    
    # Routing destination computed by the feedback router ("revise_flow", "draft", etc.)
    feedback_route: str
    
    # Counter tracking revision iterations
    revision_count: int

    # Counter tracking automatic revision attempts made by AI critics
    auto_revision_count: int

    # Separate retry budget for truncated/incomplete drafts (Draft Completeness
    # Check). Consumed on regeneration retries; independent of auto_revision_count.
    truncation_retry_count: int

    # Why the current draft was flagged incomplete (empty string when complete).
    incomplete_draft_reason: str

    # Flag set when the last automatic critic verdict was a REJECTION after the
    # max automatic revisions were reached. The draft/flow then still goes to
    # user approval, but it is explicitly marked as needing human review /
    # explicit override — it must never be treated as auto-approved.
    requires_human_review: bool

    # Research reports created by experts analyzing the topic
    research_reports: list[ExpertReport]
    
    # Curated subset of high-impact research observations chosen for inclusion
    curated_insights: list[str]

    # The generated article text/draft
    draft: str

    # Final editorial review notes stored in the project archive after approval
    final_review: dict
    
    # The next action node to run
    next_action: str

    # Merged log of all pipeline node actions (uses operator.add to append entries)
    pipeline_log: Annotated[list[dict], operator.add]
