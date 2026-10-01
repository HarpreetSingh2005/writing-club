# 💼 Company Shared Workspace (State)

The `State` is the global, shared workspace of the Writing Club. Direct agent-to-agent messaging is forbidden; instead, agents communicate asynchronously by reading from and writing to this object.

---

## 🔑 State Keys Reference

### 1. User Brief & Intake Input
*   **`user_idea`** (`str`): The core idea or topic outline provided by the user in the initial brief.
*   **`requested_tone`** (`str`): The tone requested by the user (e.g., *poetic*, *candid*, *sharp*, *reflective*).
*   **`article_length`** (`str`): The target word count requested by the user (e.g., *800*).
*   **`audio_file_path`** (`str`): Path to the input audio file (if blank,direct text transcript is assumed).
*   **`transcript`** (`str`): Raw text transcript (either extracted from audio or directly provided).
*   **`summary`** (`str`): Grammatically cleaned and condensed version of the transcript created by the `Summarizer`.

---

### 2. Planning & Library Data
*   **`discovered_perspectives`** (`list[DiscoveredPerspective]`): Candidate academic or professional perspectives discovered from the summary.
*   **`departments_topics`** (`dict[str, list[DiscoveredPerspective]]`): Perspectives grouped by department categories.
*   **`new_department`** (`list[str]`): List of brand new department categories initialized in the library on the current run.
*   **`writing_style`** (`str`): Name of the matched style profile (e.g., *introspective_epiphany*).
*   **`style_profile`** (`dict`): The inferred style profile rules, signature rules (to-dos), and avoid lists.

---

### 3. Research & Insights
*   **`research_reports`** (`list[ExpertReport]`): List of analytical research reports produced by expert agents.
*   **`curated_insights`** (`list[str]`): High-impact, complementary observations selected from the reports by the `Insight Curator`.

---

### 4. Editorial, Outline & Drafts
*   **`proposed_flow`** (`WritingFlow`): The article outline structure containing the title direction, argument, and sections.
*   **`draft`** (`str`): The fully composed article draft.
*   **`final_review`** (`dict`): Post-production review notes stored in the project archive.

---

### 5. Loop Controls & Routing
*   **`flow_approved`** (`bool`): Flag indicating whether the human approved the outline.
*   **`article_approved`** (`bool`): Flag indicating whether the human approved the final draft.
*   **`review_stage`** (`str`): Tracks whether the current human review is for the `"flow"` or `"draft"`.
*   **`user_feedback`** (`str`): Feedback comments left by the user (or critic) for revisions.
*   **`feedback_route`** (`str`): Routing destination computed by the router (e.g., `"revise_flow"`, `"complete"`).
*   **`revision_count`** (`int`): Counter tracking manual human revision loops.
*   **`auto_revision_count`** (`int`): Counter tracking automatic revision attempts made by critics (limits loops to 2).
*   **`next_action`** (`str`): The name of the next node to trigger.
*   **`pipeline_log`** (`list[dict]`): Chronological activity logs recording execution times, metrics, and agent ratings.
