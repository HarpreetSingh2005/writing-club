# 🖊️ Writing Club: AI-Powered Multi-Agent Writing Organization

**Writing Club** is a state-of-the-art, multi-agent editorial pipeline powered by [LangGraph](https://github.com/langchain-ai/langgraph). It emulates a professional publication house, transforming raw ideas, text briefs, or voice transcripts into highly polished, human-sounding articles. 

Instead of generating an article in a single LLM prompt, the project routes inputs through **15 specialized AI agents ("employees")**, implements automated quality-assurance critics, and embeds interactive **human-in-the-loop approvals** to ensure the final output retains your voice and satisfies your editorial goals.

---

## 🏛️ System Architecture & Workflow

Writing Club is built on a modular state graph. The entire workflow consists of **15 distinct steps** organized into five core phases: **Intake**, **Planning**, **Research**, **Editorial**, and **Verification**.

```mermaid
graph TD
    %% Define Styles
    classDef intake fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
    classDef planning fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
    classDef research fill:#EDE7F6,stroke:#651FFF,stroke-width:2px,color:#000;
    classDef editorial fill:#FFF3E0,stroke:#E65100,stroke-width:2px,color:#000;
    classDef verification fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#000;
    classDef human fill:#FFFDE7,stroke:#FBC02D,stroke-width:2px,color:#000;

    %% Nodes & Flow
    START([Start]) --> RouteStart{Audio Provided?}
    
    %% Intake Phase
    subgraph Intake Phase
        transcriber[1. Transcriber<br/>Local Whisper / Gemini / OpenAI]:::intake
        summarizer[2. Summarizer<br/>Contextual Clean-up]:::intake
    end
    
    RouteStart -- Yes --> transcriber
    RouteStart -- No --> summarizer
    transcriber --> summarizer

    %% Planning Phase
    subgraph Planning Phase
        discovery[3. Perspective Discovery<br/>Identify Angles]:::planning
        librarian[4. Department Librarian<br/>Persistent Knowledge]:::planning
        style_lib[5. Style Librarian<br/>Signature & Voice Profile]:::planning
    end
    
    summarizer --> discovery
    discovery --> librarian
    librarian --> style_lib

    %% Research Phase
    subgraph Research Phase
        research[6. Expert Research<br/>Observations & Blindspots]:::research
    end
    
    style_lib --> research

    %% Editorial Phase
    subgraph Editorial Phase
        curator[7. Insight Curator<br/>Select Key Insights]:::editorial
        flow_arch[8. Flow Architect<br/>Propose Outline & Tone]:::editorial
        auto_flow_critic[9. Auto Flow Critic<br/>Critique Outline]:::verification
        flow_app[10. Flow Approval<br/>Human Interrupt]:::human
    end
    
    research --> curator
    curator --> flow_arch
    flow_arch --> auto_flow_critic
    
    auto_flow_critic -- Rejected &lt; 2 times --> flow_arch
    auto_flow_critic -- Approved or Max Retries --> flow_app

    %% Feedback Router
    router[11. Feedback Router<br/>Interpret & Redirect Route]:::editorial
    flow_app --> router
    
    %% Routing Paths
    router -- Approved / Draft Route --> writer[12. Article Writer<br/>Compose Prose Draft]:::editorial
    router -- Revise Outline --> flow_arch
    router -- Revise Research --> research
    router -- Revise Style --> style_lib

    subgraph Drafting Phase
        auto_draft_critic[13. Auto Draft Critic<br/>Scan AI Tropes & Clichés]:::verification
        draft_app[14. Article Draft Approval<br/>Human Interrupt]:::human
        final_review[15. Final Review<br/>Post-publication notes]:::editorial
    end
    
    writer --> auto_draft_critic
    auto_draft_critic -- Rejected &lt; 2 times --> writer
    auto_draft_critic -- Approved or Max Retries --> draft_app
    
    draft_app --> router
    router -- Complete --> final_review
    final_review --> END([Finish])
```

---

## 🔁 Current-Run Correction vs. System Self-Improvement

Writing Club uses **AI Editorial Critique + Adaptive Current-Run Routing**:

- Each stage's output is reviewed by an AI critic.
- The critic evaluates the current output, identifies weaknesses, and decides the appropriate next action for the **current article**.
- The workflow routes back to the relevant agent (Flow Architect, Expert Research, Style Librarian, or Article Writer) for revision, then back through the critic.
- Human flow and article approvals remain part of the loop.

```text
Flow Architect → Flow Critic → revise_flow → Flow Architect
Article Writer → Draft Critic → revise_draft → Article Writer
```

This **current-run correction is intentionally kept**.

Writing Club does **not** perform system-level self-improvement. It does not automatically modify its own prompts, code, graph architecture, State schema, department definitions, or future run behavior based on article feedback.

```text
Current-run correction:   KEEP
System self-improvement:  REMOVED
```

---

## 🗂️ Step-by-Step Employee Nodes (How Each Step Works)

### Phase A: Intake
#### 1. Transcriber (`transcriber`)
*   **What it does:** Converts spoken audio into text.
*   **How it works:** If the user supplies an audio file path, it attempts local transcription using an OpenAI Whisper `base` model. If local resources fail, it falls back to Gemini's multimodal API (uploading the file) or OpenAI's remote Whisper API.

#### 2. Summarizer (`summarizer`)
*   **What it does:** Compresses and cleans the transcription without adding any new or external ideas.
*   **How it works:** It acts as a strict editor, fixing grammar mistakes, removing filler words, and structuring the raw spoken transcript into a coherent, condensed summary containing the core arguments.

---

### Phase B: Planning & Library Management
#### 3. Perspective Discovery (`perspective discovery`)
*   **What it does:** Identifies disciplines and specialized angles (e.g., Sociology, Philosophy, Biology) relevant to the topic.
*   **How it works:** It analyzes the summary and proposes a list of 2–3 academic or expert perspectives to research. This ensures the final article is rich and multi-dimensional.

#### 4. Department Librarian (`librarian`)
*   **What it does:** Manages the persistent library of academic departments (`library room/*.json`).
*   **How it works:** It groups discovered perspectives by department. If a department JSON does not exist in the library, it generates a description and schema metadata via an LLM. It then registers new sub-departments (or perspectives) to compile a growing index of intellectual angles.

#### 5. Style Librarian (`style librarian`)
*   **What it does:** Establishes and updates the author's writing style profile (`library room/writing styles/*.json`).
*   **How it works:** It matches the current text against a specific writing style (e.g., *reflective personal narrative*). It identifies rules for tone, pacing, narrative distance, and lists specific signature rules (things to do) and warnings (things to avoid), merging them into a persistent file across runs to ensure the AI adapts to the author's style over time.

---

### Phase C: Research
#### 6. Expert Research (`expert research`)
*   **What it does:** Conducts research and generates reports from the perspective of each selected department.
*   **How it works:** Armed with the department descriptions, the agent analyzes the summary and writes a structured report containing key academic observations, potential risks/blind spots in the author's argument, and specific writing suggestions.

---

### Phase D: Editorial & Structure
#### 7. Insight Curator (`insight curator`)
*   **What it does:** Selects the most critical research points.
*   **How it works:** It acts as an editorial filter, scanning all expert research reports, deduplicating findings, and selecting the most impactful, non-conflicting points to include in the draft.

#### 8. Flow Architect (`flow architect`)
*   **What it does:** Proposes a structured outline (flow) for the article.
*   **How it works:** Using the curated insights and the style profile, it creates an outline containing a suggested title direction, tone, core argument, section-by-section breakdown, and an approval question for the user.

---

### Phase E: AI Editorial Critique, Current-Run Routing & Human Approvals
#### 9. Auto Flow Critic (`auto flow critic`)
*   **What it does:** Performs an automated quality check on the proposed outline.
*   **How it works:** It evaluates the outline for generic writing structures, weak arguments, or boring section transitions. If it fails, it rejects the outline and loops back to the *Flow Architect* with feedback (capped at 2 automatic revisions to prevent infinite loops).

#### 10. Flow Approval (`flow approval`) — *Human Interrupt*
*   **What it does:** Pauses the graph to seek user approval for the proposed outline.
*   **How it works:** An interactive terminal prompt halts execution, printing the proposed title, tone, argument, and sections. The user can either type `y` to approve and proceed, or reject and provide feedback.

#### 11. Feedback Router (`feedback router`)
*   **What it does:** Determines the routing path based on review stage and user/critic feedback.
*   **How it works:**
    *   **Approved with no feedback:** Fast-paths to the next phase (outline approved → go to `article writer`; draft approved → go to `final article review`).
    *   **Feedback provided:** Uses an LLM to route feedback to the best-suited department (e.g. `style librarian` to adjust voice, `expert research` to gather more facts, `flow architect` to restructure outline, or `article writer` to rewrite draft).

#### 12. Article Writer (`article writer`)
*   **What it does:** Composes the full article draft.
*   **How it works:** Using the approved outline, the intake summary, expert reports, curated insights, and the target style profile, it writes the entire prose piece.

#### 13. Auto Draft Critic (`auto draft critic`)
*   **What it does:** Performs an automated quality check on the written draft.
*   **How it works:** It scans the draft for generic AI tropes (e.g., "in conclusion", "it's crucial to note", "tapestry of life"), sentence monotony, cliches, and tone compliance. If it fails, it sends it back to the *Article Writer* with correction instructions (capped at 2 auto-revisions).

#### 14. Article Approval (`article approval`) — *Human Interrupt*
*   **What it does:** Pauses the graph to seek user approval for the final draft.
*   **How it works:** Halts execution and prints the complete drafted article. The user can approve the draft or suggest edits, which the *Feedback Router* will evaluate and route accordingly.

#### 15. Final Review (`final article review`)
*   **What it does:** Performs a post-mortem review of the final approved article.
*   **How it works:** Compares the final approved article against the initial requirements. It notes what went well, what needed correction, and stores the outcome in the project archive. It does not modify, store, or propose changes to the system.

---

## 💾 Project Dumper & Outputs

Once the final draft is approved, the system generates a detailed archive file inside the `/articles` folder:
- **Article Text & Structure:** Full title, core argument, and sections.
- **Style Profiles:** Saved tone, narrative distance, signature rules, and avoidances.
- **Expert Reports:** Complete academic observation notes, risks, and blind spots.
- **Activity Logs:** Time-stamped logs of every agent action and rating score (e.g., `🤖 [Auto Flow Critic] Rated outline: 9.2/10`).

---

## 🔌 API Key switching & Task Routing

The system includes a resilient model configurator (`config/model_config.py`) that matches specific models to specific tasks:
- **Intake/Summarization/Critique:** Routed to faster, cost-effective models (e.g., Gemini `gemini-3.6-flash`).
- **Research/Critique Fallback:** Routed to larger reasoning models (e.g., Nvidia-hosted `Llama 3.3-70B`).
- **Flow & Drafting:** Routed to models with high-quality prose capabilities (e.g., OpenAI `gpt-5.6-terra` / `gpt-4o`).

### API Key Fallback Formats
You can configure fallback keys in your `.env` file in two ways:

1. **Comma-Separated Values:**
   ```text
   GEMINI_API_KEYS=key1,key2,key3
   OPENAI_API_KEYS=key1,key2
   ```
2. **Numbered Keys:**
   ```text
   GEMINI_API_KEY_1=key1
   GEMINI_API_KEY_2=key2
   ```

If a provider returns a rate limit or API error during execution, `utils/ask_llm.py` automatically retries with the next key, then falls back to the next preferred model in the `TASK_POLICY` matrix.

### Local Fallback (Ollama)

A local **Ollama** model is the final safety net in every task chain. It is only queried when **all** cloud providers fail, so the pipeline never stops. It requires neither an API key nor internet.

To use it: install [Ollama](https://ollama.com), pull a model (e.g. `ollama pull llama3.2`), and keep the server running (`ollama serve`).

```text
OLLAMA_BASE_URL=http://localhost:11434   # local Ollama server
OLLAMA_MODEL=llama3.2                    # any model you have pulled
OLLAMA_ENABLED=true                      # set false to disable the fallback
```

---

## 🔎 Optional Web Research (SearXNG Tool)

Expert Researchers can optionally consult a **local SearXNG** instance for external evidence. SearXNG is a **tool**, not an employee or graph node — researchers reason from their department perspective first, and only request searches when external information (studies, statistics, case studies, verification, competing viewpoints) would materially improve the report.

### How it works
1. Each researcher reasons from its assigned department/perspective and returns an analytics report plus an optional `search_plan`.
2. An empty search plan means no web research is performed (the analyst call alone produces the final report).
3. If searches are planned, the node runs up to **3 queries total** (2 initial + 1 follow-up), capped at **5 results per query**. Search is optional and never blocks the pipeline.
4. Search snippets are treated as **untrusted discovery-level evidence**, never verified facts. Only URLs actually returned by SearXNG may appear in a report's `web_sources`.
5. If SearXNG is unavailable, misconfigured, or times out, the researcher continues with purely analytical research (web research is never a hard dependency).

### Minimal local setup
Run SearXNG separately (not managed by Writing Club), e.g. with Docker:

```bash
docker run -d -p 8080:8080 -v "$PWD/searxng:/etc/searxng" searxng/searxng
```

JSON output must be enabled in the instance's `settings.yml`:

```yaml
search:
  formats:
    - html
    - json
```

Verify it responds with JSON (not HTML):

```bash
curl "http://localhost:8080/search?q=test&format=json"
```

### Configuration (`.env`)
```text
SEARXNG_URL=http://localhost:8080   # leave empty/unset to disable web research
SEARXNG_TIMEOUT=10                   # per-request timeout in seconds
SEARXNG_ENABLED=true                 # auto-detected from SEARXNG_URL; can be forced off
```
Web research is disabled by default unless `SEARXNG_URL` is set in `.env`.

---

## 🛠️ Getting Started

### 1. Installation
Ensure you have `uv` installed, then synchronize the environment:
```bash
uv sync
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```text
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
NVIDIA_API_KEY=your_nvidia_key
OLLAMA_BASE_URL=http://localhost:11434   # optional local fallback
OLLAMA_MODEL=llama3.2                    # optional local fallback
```

### 3. Run the Interactive App
Run the interactive CLI app:
```bash
uv run app.py
```
You can also pass an audio file directly to transcribe it:
```bash
uv run app.py uploads/my_voice_memo.mp3
```
