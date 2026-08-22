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

from fastapi import FastAPI, File, Form, UploadFile
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
    transcript: str = Form(default=""),
    audio: UploadFile | None = File(default=None),
):
    thread_id = str(uuid.uuid4())
    audio_file_path = ""

    # Save uploaded audio file
    if audio and audio.filename:
        dest = UPLOAD_DIR / f"{thread_id}_{audio.filename}"
        with open(dest, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        audio_file_path = str(dest.resolve())

    initial_state = {
        "audio_file_path": audio_file_path,
        "transcript": transcript,
        "summary": "",
        "discovered_perspectives": [],
        "flow_approved": False,
        "user_feedback": "",
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
        "draft": values.get("draft", ""),
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
            if "proposed_flow" in payload:
                response["proposed_flow"] = _jsonable(payload.get("proposed_flow"))

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
        else:
            response["proposed_flow"] = _jsonable(payload.get("proposed_flow"))
            response["question"] = payload.get("question", "Approve this flow?")
    else:
        response["awaiting_approval"] = False
        response["draft"] = values.get("draft", "")
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
