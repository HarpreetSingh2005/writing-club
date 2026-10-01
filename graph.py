from dataclasses import asdict, is_dataclass

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

# Import employee nodes from their respective modules
from employees.intake.transcriber import transcriber
from employees.intake.summarizer import summarize
from employees.planning import perspective_discovery, librarian, style_librarian
from employees.research.expert_research import expert_research
from employees.editorial.insight_curator import insight_curator
from employees.editorial.flow_architect import flow_architect
from employees.editorial.feedback_router import feedback_router
from employees.editorial.article_writer import article_writer
from employees.editorial.auto_critics import auto_flow_critic, auto_draft_critic
from employees.editorial.draft_completeness import draft_completeness_check
from employees.editorial.final_article_review import final_article_review
from state import State
from models.perspective import DiscoveredPerspective, ExpertReport, WritingFlow
from utils.pipeline_logger import log_entry


def _jsonable(value):
    """Helper function to convert dataclass instances to JSON-compatible dictionaries."""
    if is_dataclass(value):
        return asdict(value)
    return value


def flow_approval(state: State):
    """
    Interrupt node for the Planning phase.
    Prompts the user to approve or reject the proposed article flow (outline, tone, core argument).
    """
    decision = interrupt({
        "question": "Approve this article flow?",
        "proposed_flow": _jsonable(state.get("proposed_flow")),
        "instructions": "Approve to continue drafting, or reject and provide feedback.",
        "auto_critic_status": (
            "rejected — human review required (max auto-revisions reached)"
            if state.get("requires_human_review", False)
            else "passed — auto-approved candidate"
        ),
        "requires_human_review": state.get("requires_human_review", False),
    })

    # Parse user decision (approved or rejected with optional feedback)
    if isinstance(decision, dict):
        approved = bool(decision.get("approved", False))
        feedback = decision.get("feedback", "")
    else:
        approved = bool(decision)
        feedback = ""

    return {
        "flow_approved": approved,
        "article_approved": False,
        "review_stage": "flow",
        "user_feedback": feedback,
        "next_action": "routing_feedback",
        "pipeline_log": [
            log_entry(
                "Flow Approval", "🤝",
                f"User {'approved' if approved else 'rejected'} the flow"
                + (f" — \"{feedback[:80]}\"" if feedback else ""),
                {},
            )
        ],
    }


def article_approval(state: State):
    """
    Interrupt node for the Editorial phase.
    Prompts the user to approve or request revisions for the final article draft.
    """
    from utils.project_dumper import save_review_packet

    review_packet_path = save_review_packet(state)

    decision = interrupt({
        "question": "Approve this article draft? First check the saved draft/review packet, then tell me if the AI understood you correctly or what should change.",
        "draft": state.get("draft", ""),
        "review_packet_path": review_packet_path,
        "instructions": "Approve to finish, or reject and describe exactly what should change. Include whether the AI's understanding of your intent was right.",
        "auto_critic_status": (
            (
                "⚠️ INCOMPLETE DRAFT — flagged as truncated: "
                + state.get("incomplete_draft_reason", "unknown reason")
                + ". Approving means approving an incomplete article."
            )
            if state.get("incomplete_draft_reason")
            else (
                "rejected — human review required (max auto-revisions reached); approving means overriding the critic"
                if state.get("requires_human_review", False)
                else "passed — auto-approved candidate"
            )
        ),
        "requires_human_review": state.get("requires_human_review", False),
    })

    # Parse user decision
    if isinstance(decision, dict):
        approved = bool(decision.get("approved", False))
        feedback = decision.get("feedback", "")
    else:
        approved = bool(decision)
        feedback = ""

    return {
        "article_approved": approved,
        "review_stage": "draft",
        "user_feedback": feedback,
        "next_action": "routing_feedback",
        "pipeline_log": [
            log_entry(
                "Article Approval", "📄",
                f"User {'approved' if approved else 'rejected'} the draft"
                + (f" — \"{feedback[:80]}\"" if feedback else ""),
                {},
            )
        ],
    }


def route_start(state: State):
    """
    Conditional routing at start.
    If a path to an audio file is specified, it goes to 'transcriber'; 
    otherwise, it directly starts with 'summarizer' for text transcripts.
    """
    if state.get("audio_file_path"):
        return "transcriber"
    return "summarizer"


def route_after_feedback(state: State):
    """
    Conditional routing node used by the feedback router.
    Routes to the appropriate department (Writer, Style Librarian, expert research, or Flow Architect)
    based on the AI feedback router analysis, or terminates if the project is complete.
    """
    route = state.get("feedback_route", "revise_flow")

    if route == "complete":
        return "final article review"
    if route in {"draft", "revise_draft"}:
        return "article writer"
    if route == "revise_style":
        return "style librarian"
    if route == "revise_research":
        return "expert research"
    if route == "revise_flow":
        return "flow architect"
    return END


def route_auto_flow(state: State):
    """
    Routes after automatic flow review.
    If rejected, loops back to 'flow architect' with critique feedback.
    If approved (or max auto-revisions reached), proceeds to 'flow approval' for user review.
    """
    return state.get("next_action", "flow_approval")


def route_auto_draft(state: State):
    """
    Routes after automatic draft review.
    If rejected, loops back to 'article writer' with humanity and quality feedback.
    If approved (or max auto-revisions reached), proceeds to 'article approval' for user review.
    """
    return state.get("next_action", "article_approval")


def route_draft_completeness(state: State):
    """
    Routes after the Draft Completeness Check.
    - 'draft_truncated_retry'  → regenerate the draft at 'article writer' (does
      NOT consume an auto-revision).
    - otherwise the node's next_action points at the next node
      ('auto draft critic', or 'article approval' after retries are exhausted).
    """
    next_action = state.get("next_action", "auto draft critic")
    if next_action == "draft_truncated_retry":
        return "article writer"
    return next_action


def build_graph():
    """
    Compiles the state graph for the Writing Club workflow.
    Registers all employee nodes, connects them with edges,
    and configures checkpointers to enable stateful recovery.
    """
    builder = StateGraph(State)
    
    # 1. Define nodes in the workflow
    builder.add_node("transcriber", transcriber)
    builder.add_node("summarizer", summarize)
    builder.add_node("perspective discovery", perspective_discovery.perspective_discovery)
    builder.add_node("librarian", librarian.librarian)
    builder.add_node("style librarian", style_librarian.style_librarian)
    builder.add_node("expert research", expert_research)
    builder.add_node("insight curator", insight_curator)
    builder.add_node("flow architect", flow_architect)
    builder.add_node("auto flow critic", auto_flow_critic)
    builder.add_node("flow approval", flow_approval)
    builder.add_node("feedback router", feedback_router)
    builder.add_node("article writer", article_writer)
    builder.add_node("draft completeness check", draft_completeness_check)
    builder.add_node("auto draft critic", auto_draft_critic)
    builder.add_node("article approval", article_approval)
    builder.add_node("final article review", final_article_review)

    # 2. Define conditional start edge
    builder.add_conditional_edges(START, route_start)
    builder.add_edge("transcriber", "summarizer")

    # 3. Define the sequential flow from summarization to planning and outline architecture
    builder.add_edge("summarizer", "perspective discovery")
    builder.add_edge("perspective discovery", "librarian")
    builder.add_edge("librarian", "style librarian")
    builder.add_edge("style librarian", "expert research")
    builder.add_edge("expert research", "insight curator")
    builder.add_edge("insight curator", "flow architect")
    builder.add_edge("flow architect", "auto flow critic")
    builder.add_conditional_edges("auto flow critic", route_auto_flow)
    
    # 4. Define feedback loops and approvals
    builder.add_edge("flow approval", "feedback router")
    builder.add_conditional_edges("feedback router", route_after_feedback)
    
    builder.add_edge("article writer", "draft completeness check")
    builder.add_conditional_edges("draft completeness check", route_draft_completeness)
    builder.add_conditional_edges("auto draft critic", route_auto_draft)
    builder.add_edge("article approval", "feedback router")
    builder.add_edge("final article review", END)

    # 5. Compile graph with memory saver to support interrupts and resuming state
    serde = JsonPlusSerializer(allowed_msgpack_modules=[
        DiscoveredPerspective,
        ExpertReport,
        WritingFlow
    ])
    graph = builder.compile(checkpointer=MemorySaver(serde=serde))

    return graph
