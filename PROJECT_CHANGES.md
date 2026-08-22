# Project Changes

## Completed

- Extended the LangGraph workflow beyond librarian into style detection, expert research, insight curation, flow approval, and article drafting.
- Added task-aware model routing with provider and API-key fallback.
- Added OpenAI key loading alongside Gemini and NVIDIA keys.
- Added persistent writing-style library support under `library room/writing styles`.
- Fixed the librarian import bug for `DiscoveredPerspective`.
- Added typed dataclasses for expert reports and writing flows.
- Added prompts for style detection, expert research, insight curation, flow planning, and article writing.
- Updated the example app to demonstrate the approval-first workflow.
- Updated project documentation and workflow notes.

## New Files

- `employees/planning/style_librarian.py`
- `employees/research/expert_research.py`
- `employees/editorial/insight_curator.py`
- `employees/editorial/flow_architect.py`
- `employees/editorial/article_writer.py`
- `prompts/style_detector.txt`
- `prompts/expert_researcher.txt`
- `prompts/insight_curator.txt`
- `prompts/flow_architect.txt`
- `prompts/article_writer.txt`
- `API_ROUTING.md`
- `PROJECT_CHANGES.md`

## Suggested Next Improvements

- Add real audio transcription as a separate intake node before summarization.
- Add LangGraph interrupt/checkpoint support so approval can pause and resume cleanly from storage.
- Add a UI that shows proposed flow, accepts feedback, and triggers drafting.
- Add tests with mocked `ask_llm` responses so the graph can be verified without spending API calls.
- Add section-by-section drafting so the user can approve or correct the article as it grows.
