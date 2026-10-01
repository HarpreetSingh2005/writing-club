# 📖 Employee Handbook

Every employee (agent node) in the Writing Club organization follows the same decoupled lifecycle to maintain architectural simplicity and scalability:

```text
Input (State) ──► Read State ──► Perform ONE Responsibility ──► Update State ──► Finish (Route next)
```

Employees are highly decoupled: they **never** communicate directly with one another. They only read from and write to the shared company workspace (`State.py`).

---

## 👥 Employee Definitions & Directory

### 🎙️ 1. Transcriber (`transcriber`)
*   **Responsibility:** Converts audio speech to text.
*   **Reads:** `audio_file_path`
*   **Writes:** `transcript`, `pipeline_log`
*   **Models:** Local Whisper (base) ──► Gemini Multimodal API ──► OpenAI Whisper API.

### 📝 2. Summarizer (`summarizer`)
*   **Responsibility:** Cleans grammar, removes verbal filler, and condenses the input.
*   **Reads:** `transcript`, `user_idea`, `requested_tone`, `article_length`
*   **Writes:** `summary`, `pipeline_log`
*   **Models:** Gemini 3.6 Flash / GPT-4o-mini.

### 🔍 3. Perspective Discovery Specialist (`perspective_discovery`)
*   **Responsibility:** Discovers useful angles or disciplines to explore the topic.
*   **Reads:** `summary`
*   **Writes:** `discovered_perspectives`, `pipeline_log`
*   **Models:** Gemini 3.6 Flash / GPT-4o-mini.

### 📚 4. Department Librarian (`librarian`)
*   **Responsibility:** Manages the department knowledge library files.
*   **Reads:** `discovered_perspectives`
*   **Writes:** `departments_topics`, `new_department`, `pipeline_log`
*   **Outputs:** Updates persistent files in `library room/*.json`.

### 🎨 5. Writing Style Librarian (`style_librarian`)
*   **Responsibility:** Infers the author's writing style and updates the style library.
*   **Reads:** `transcript`, `summary`, `user_idea`, `requested_tone`, `user_feedback`
*   **Writes:** `writing_style`, `style_profile`, `pipeline_log`
*   **Outputs:** Updates persistent profiles under `library room/writing styles/*.json`.

### 🧪 6. Expert Researcher (`expert_research`)
*   **Responsibility:** Conducts deep analytical research on the topic from a specific department perspective.
*   **Reads:** `discovered_perspectives`, `summary`, `user_feedback`
*   **Writes:** `research_reports`, `pipeline_log`
*   **Models:** Nvidia Llama-3.3-70b-instruct / GPT-4o.

### ✂️ 7. Insight Curator (`insight_curator`)
*   **Responsibility:** Deduplicates and selects high-impact research points.
*   **Reads:** `summary`, `research_reports`, `user_feedback`
*   **Writes:** `curated_insights`, `pipeline_log`

### 📐 8. Flow Architect (`flow_architect`)
*   **Responsibility:** Designs a proposed article outline.
*   **Reads:** `user_idea`, `requested_tone`, `article_length`, `summary`, `curated_insights`, `style_profile`, `user_feedback`
*   **Writes:** `proposed_flow`, `next_action`, `pipeline_log`

### 🤖 9. Auto Flow Critic (`auto_flow_critic`)
*   **Responsibility:** Performs self-correction checks on the outline for quality.
*   **Reads:** `user_idea`, `requested_tone`, `article_length`, `summary`, `style_profile`, `proposed_flow`
*   **Writes:** `user_feedback` (auto critique notes), `auto_revision_count`, `next_action`, `pipeline_log`

### 🤝 10. Flow Approval (`flow_approval`)
*   **Responsibility:** Intercepts execution for human confirmation on the outline.
*   **Reads:** `proposed_flow` (interactive interrupt)
*   **Writes:** `flow_approved`, `user_feedback`, `pipeline_log`

### 🔀 11. Feedback Router (`feedback router`)
*   **Responsibility:** Interprets reviews and routes the workspace to the correct stage.
*   **Reads:** `review_stage`, `user_feedback`, `flow_approved`, `article_approved`, `draft`, `proposed_flow`
*   **Writes:** `feedback_route`, `next_action`, `revision_count`, `flow_approved`, `article_approved`, `pipeline_log`

### ✍️ 12. Article Writer (`article_writer`)
*   **Responsibility:** Composes the full article prose.
*   **Reads:** `user_idea`, `requested_tone`, `article_length`, `summary`, `proposed_flow`, `style_profile`, `discovered_perspectives`, `research_reports`, `curated_insights`, `user_feedback`
*   **Writes:** `draft`, `next_action`, `pipeline_log`

### 🤖 13. Auto Draft Critic (`auto_draft_critic`)
*   **Responsibility:** Performs self-correction checks on the prose (detecting AI tropes).
*   **Reads:** `user_idea`, `requested_tone`, `article_length`, `summary`, `proposed_flow`, `style_profile`, `draft`
*   **Writes:** `user_feedback` (auto draft critique), `auto_revision_count`, `next_action`, `pipeline_log`

### 📄 14. Article Approval (`article_approval`)
*   **Responsibility:** Intercepts execution for human confirmation on the written draft.
*   **Reads:** `draft` (interactive interrupt)
*   **Writes:** `article_approved`, `user_feedback`, `pipeline_log`

### 🗂️ 15. Final Reviewer (`final_article_review`)
*   **Responsibility:** Conducts a post-writing reflection to optimize future generation runs.
*   **Reads:** `user_idea`, `requested_tone`, `article_length`, `summary`, `style_profile`, `draft`
*   **Writes:** `final_review`, `next_action`, `pipeline_log`
