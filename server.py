"""
Writing Club — FastAPI Server

Endpoints:
    POST  /api/start          Upload audio or text, start the workflow
    GET   /api/status/{id}    Get current state and pipeline log
    POST  /api/approve/{id}   Approve/reject with feedback
    GET   /api/result/{id}    Get the final draft
"""

import json
import os
import shutil
import uuid
from dataclasses import asdict, is_dataclass
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from langgraph.types import Command

from graph import build_graph

app = FastAPI(title="Writing Club API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory graph instance (shared, stateful via LangGraph checkpointer)
graph = build_graph()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

DEMO_TRANSCRIPT = """
Okay so this is an article for the idea that why to care about people so this is the incidence where I was doing my exercise so normally I don't go to the gym current team but I wanted to exercise right so I started going to the ab public gym where all the old uncles and arteries come and the first It's really a not the top notch position you should work because it's really know that motivating so one day I was in this mode only like iron module to work rather than I was I really don't want to work there not go to Jim there because obviously that was not my perfect place now the equipments for the great know there were the motivation there were all the old uncles and our design no people know someone of age of my but then I was in the M okay yeah just give this and just talk to in this but at this at the same moment I servant girl so there was this when uncle came with this one a Harshit Harsh small child and she was on the wheelchair so she couldn't really work and observing her I realize that it's not about the uncle and aunty and no one was actually looking for like how is unknown was even even care about her so in the lamps nomenon daily give a shit about her and the point is that moment I saw like who am I showing this particular exercise two even is someone judges me like oh see like this guys but we were working with those artis and make me fun of me but what if in the future I don't work and for that reason my legs or my body stuff stop working out so at that moment these guys won't come to support me or to take care so why the hell should I even here to them even though I would probably shock is my the gym click way I work and how the environment is it's really the like the first environment you could ever go with like for the motivation and all that but the only thing is like these people even if they are making fun of you but when you if you stop working these people want even give a shit if you have really good or review working well a very not and even people don't even care thank you there they might be making fun for few minutes but after that day would forget that see you should just don't care and I just that is the basic idea about this
""".strip()


def _jsonable(obj):
    """Recursively convert dataclasses to dicts for JSON serialization."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonable(v) for v in obj]
    return obj


def _get_interrupt_payload(result: dict) -> dict | None:
    interrupts = result.get("__interrupt__", [])
    if not interrupts:
        return None
    first = interrupts[0]
    return getattr(first, "value", first)


def _get_state_interrupt_payload(state) -> dict | None:
    for task in getattr(state, "tasks", []) or []:
        interrupts = getattr(task, "interrupts", ()) or ()
        if interrupts:
            first = interrupts[0]
            return getattr(first, "value", first)
    return None


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


# ─────────────────────────────────────────────
#  POST /api/start
# ─────────────────────────────────────────────
@app.post("/api/start")
async def start_workflow(
    user_idea: str = Form(default=""),
    requested_tone: str = Form(default=""),
    article_length: str = Form(default=""),
    transcript: str = Form(default=""),
    use_default: bool = Form(default=False),
    audio: UploadFile | None = File(default=None),
):
    thread_id = str(uuid.uuid4())
    audio_file_path = ""
    user_idea = user_idea.strip()
    article_length = article_length.strip()

    # The requested_tone form field is accepted only for backward compatibility
    # with older clients and is deliberately ignored: the article's tone is no
    # longer a user-controlled writing requirement. It emerges from the source,
    # the Author Skill, and the subject.
    if not article_length.isdigit() or int(article_length) <= 0:
        raise HTTPException(status_code=422, detail="Target word count must be a positive number.")

    # Save uploaded audio file
    if audio and audio.filename:
        dest = UPLOAD_DIR / f"{thread_id}_{audio.filename}"
        with open(dest, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        audio_file_path = str(dest.resolve())

    source_material = transcript.strip() or user_idea
    if use_default:
        source_material = DEMO_TRANSCRIPT
    if not source_material and not audio_file_path:
        raise HTTPException(status_code=422, detail="Idea, transcript, audio, or demo material is required.")

    initial_state = {
        "user_idea": user_idea or source_material,
        "requested_tone": "",
        "article_length": article_length,
        "audio_file_path": audio_file_path,
        "transcript": source_material,
        "summary": "",
        "discovered_perspectives": [],
        "flow_approved": False,
        "user_feedback": "",
        "final_review": {},
        "pipeline_log": [],
    }

    result = graph.invoke(initial_state, config=_config(thread_id))

    return _build_response(thread_id, result)


# ─────────────────────────────────────────────
#  GET /api/status/{thread_id}
# ─────────────────────────────────────────────
@app.get("/api/status/{thread_id}")
async def get_status(thread_id: str):
    try:
        state = graph.get_state(_config(thread_id))
    except Exception:
        return JSONResponse({"error": "Thread not found"}, status_code=404)

    values = state.values or {}
    pipeline_log = values.get("pipeline_log", [])
    payload = _get_state_interrupt_payload(state)
    next_nodes = tuple(getattr(state, "next", ()) or ())
    awaiting_approval = bool(payload) or any(
        node in {"flow approval", "article approval"} for node in next_nodes
    )
    review_stage = values.get("review_stage", "")

    if not review_stage:
        if "article approval" in next_nodes:
            review_stage = "draft"
        elif "flow approval" in next_nodes:
            review_stage = "flow"

    response = {
        "thread_id": thread_id,
        "pipeline_log": pipeline_log,
        "summary": values.get("summary", ""),
        "writing_style": values.get("writing_style", ""),
        "requested_tone": values.get("requested_tone", ""),
        "article_length": values.get("article_length", ""),
        "draft": values.get("draft", ""),
        "final_review": values.get("final_review", {}),
        "flow_approved": values.get("flow_approved", False),
        "article_approved": values.get("article_approved", False),
        "awaiting_approval": awaiting_approval,
        "review_stage": review_stage or "flow",
        "next_action": values.get("next_action", ""),
        "proposed_flow": _jsonable(values.get("proposed_flow")),
        "revision_count": values.get("revision_count", 0),
    }

    if awaiting_approval:
        response["question"] = (
            (payload or {}).get("question")
            or ("Approve this article draft?" if review_stage == "draft" else "Approve this article flow?")
        )
        if payload:
            if "draft" in payload:
                response["draft"] = payload.get("draft", "")
            if "review_packet_path" in payload:
                response["review_packet_path"] = payload.get("review_packet_path", "")
            if "proposed_flow" in payload:
                response["proposed_flow"] = _jsonable(payload.get("proposed_flow"))
            if "requires_human_review" in payload:
                response["requires_human_review"] = payload.get("requires_human_review", False)
                response["auto_critic_status"] = payload.get("auto_critic_status", "")

    return response


# ─────────────────────────────────────────────
#  POST /api/approve/{thread_id}
# ─────────────────────────────────────────────
@app.post("/api/approve/{thread_id}")
async def approve(
    thread_id: str,
    approved: bool = Form(default=False),
    feedback: str = Form(default=""),
):
    decision = {"approved": approved, "feedback": feedback}

    try:
        result = graph.invoke(Command(resume=decision), config=_config(thread_id))
        
        # If the article is approved, export the complete run details (summary, transcript, logs, etc.)
        state = graph.get_state(_config(thread_id))
        values = state.values or {}
        if values.get("article_approved") and values.get("draft"):
            from utils.project_dumper import save_project_dump
            save_project_dump(values)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    return _build_response(thread_id, result)


# ─────────────────────────────────────────────
#  GET /api/result/{thread_id}
# ─────────────────────────────────────────────
@app.get("/api/result/{thread_id}")
async def get_result(thread_id: str):
    try:
        state = graph.get_state(_config(thread_id))
    except Exception:
        return JSONResponse({"error": "Thread not found"}, status_code=404)

    values = state.values or {}
    return {
        "thread_id": thread_id,
        "draft": values.get("draft", ""),
        "article_approved": values.get("article_approved", False),
        "pipeline_log": values.get("pipeline_log", []),
    }


# ─────────────────────────────────────────────
#  Helper: build a unified response
# ─────────────────────────────────────────────
def _build_response(thread_id: str, result: dict) -> dict:
    payload = _get_interrupt_payload(result)

    # Get latest state from checkpointer
    state = graph.get_state(_config(thread_id))
    values = state.values or {}

    response = {
        "thread_id": thread_id,
        "pipeline_log": values.get("pipeline_log", []),
        "summary": values.get("summary", ""),
        "next_action": values.get("next_action", ""),
        "revision_count": values.get("revision_count", 0),
    }

    if payload:
        response["awaiting_approval"] = True
        response["review_stage"] = values.get("review_stage", "flow")
        if "draft" in payload:
            response["draft"] = payload["draft"]
            response["question"] = payload.get("question", "Approve this draft?")
            response["review_packet_path"] = payload.get("review_packet_path", "")
        else:
            response["proposed_flow"] = _jsonable(payload.get("proposed_flow"))
            response["question"] = payload.get("question", "Approve this flow?")
    else:
        response["awaiting_approval"] = False
        response["draft"] = values.get("draft", "")
        response["final_review"] = values.get("final_review", {})
        response["article_approved"] = values.get("article_approved", False)
        response["flow_approved"] = values.get("flow_approved", False)

    return response


# ─────────────────────────────────────────────
#  Serve frontend static files
# ─────────────────────────────────────────────
frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
