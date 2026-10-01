# 🏛️ Writing Club Organization

**Version:** 2.0  
**Status:** Production (Active LangGraph multi-agent pipeline)

---

## 💡 Organizational Philosophy

Writing Club is not a loose collection of ad-hoc prompt templates. It is a highly structured, state-driven AI organization. 

Every employee (node) has a single, tightly defined responsibility and communicates exclusively by writing to and reading from the shared company workspace (`State`). Direct inter-agent communication is forbidden, preventing chaotic dependency chains and making the pipeline highly maintainable, testable, and robust.

---

## 🏢 Department & Team Structure

```text
Writing Club Board
│
├── 🎙️ Intake Department
│   ├── Transcriber (Speech-to-Text)
│   └── Summarizer (Transcript cleaner & Grammar check)
│
├── 🗺️ Planning & Library Department
│   ├── Perspective Discovery Specialist
│   ├── Department Librarian (Persistent domain knowledge manager)
│   └── Writing Style Librarian (Style profile and voice adaptation)
│
├── 🧪 Research Department
│   └── Expert Researchers (Domain-specific analysts)
│
└── 📰 Editorial & Quality Assurance Department
    ├── Insight Curator (Fact aggregator)
    ├── Flow Architect (Outline designer)
    ├── Auto Flow Critic (Outline verification)
    ├── Flow Approval (Human-in-the-loop interrupt)
    ├── Feedback Router (Intelligent stage coordinator)
    ├── Article Writer (Prose composition)
    ├── Auto Draft Critic (AI trope scanner & quality check)
    ├── Article Approval (Human-in-the-loop interrupt)
    └── Final Reviewer (Post-production analytics)
```

---

## 🎯 Team Responsibilities

### 1. Intake Department
*   **Mission:** Understand and extract exactly what the author wants to express.
*   **Focus:** Removing audio noise, grammatical errors, and filler words without adding external opinions.
*   **Outputs:** Structured `summary` and `transcript`.

### 2. Planning & Library Department
*   **Mission:** Set the strategy, intellectual scope, and voice constraints of the article.
*   **Focus:** Identifying multidisciplinary angles, updating the persistent domain knowledge base, and adapting/saving style patterns across runs.
*   **Outputs:** Relevant department lists, `writing_style`, and `style_profile`.

### 3. Research Department
*   **Mission:** Gather analytical evidence, explore edge cases, and highlight risks.
*   **Focus:** Providing deep academic or domain insight based on the specific perspectives.
*   **Outputs:** Detailed `research_reports`.

### 4. Editorial & Quality Assurance Department
*   **Mission:** Draft, verify, revise, and sign off on the final article.
*   **Focus:** Synthesizing research, defining section-by-section outline structures, correcting generic AI clichés, routing feedback, and archiving project data.
*   **Outputs:** `proposed_flow`, `draft`, `final_review` notes, and complete project dump logs.
