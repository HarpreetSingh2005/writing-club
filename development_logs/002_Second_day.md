# Day 2 - Building the Organization

**Date:** 13 July 2026

---

# Objective

Today's goal was to move beyond a simple LangGraph workflow and begin transforming Writing Club into an AI organization where employees collaborate through a shared state.

---

# Major Changes

## 1. Organizational Thinking

We decided to completely move away from the term **Agent**.

Instead, the project now models an AI company.

Examples:

- Agent → Employee
- Agent Factory → Hiring Manager (Future)
- Agent Prompt → Work Assignment
- Agent Output → Work Report

The focus is no longer "multiple AI agents".

The focus is "multiple employees with specialized responsibilities."

---

## 2. Perspective Library

We redesigned the Perspective Library.

Initially we considered storing prompts.

Instead we concluded that prompts should always be generated dynamically.

The library now stores permanent knowledge.

Each Perspective contains:

- Name
- Thinking Framework
- Keywords

Prompt generation and relevance are execution-specific and should never be stored in the library.

---

## 3. Discovery Pipeline

Current pipeline:

Transcription

↓

Summarizer

↓

Perspective Discovery

Future:

Perspective Resolver

↓

Perspective Library

↓

Parallel Employees

---

## 4. Perspective Discovery

Implemented the Perspective Discovery employee.

Current responsibilities:

- Read summary
- Discover meaningful perspectives
- Explain why each perspective is relevant

Output:

```python
DiscoveredPerspective

name

reason
```

---

## 5. Shared Models

Created models:

```python
Perspective

DiscoveredPerspective
```

Separated permanent knowledge from execution-specific discoveries.

---

## 6. LLM Infrastructure

Completely redesigned the LLM layer.

Current architecture:

```
Employee

↓

ask_llm()

↓

Model Priority

↓

Gemini

↓

NVIDIA (Fallback)

↓

Response
```

Implemented:

- Centralized `ask_llm()`
- Model priority system
- Automatic fallback
- JSON parsing support

Configuration split into:

- `.env`
- `config/env.py`
- `config/model_config.py`

---

## 7. Successful End-to-End Pipeline

Current working flow:

```
Transcription

↓

Summarizer

↓

Perspective Discovery
```

Successfully produces:

- Transcript
- Summary
- Discovered Perspectives

---

# Biggest Architectural Realization

We realized that Writing Club should not simply gather perspectives.

Instead, it should gradually reduce the search space.

Rather than researching everything:

```
Discover

↓

Select

↓

Develop

↓

Curate

↓

Write
```

Every stage should increase signal while reducing noise.

---

# Revised Future Architecture

```
Transcription

↓

Summarizer

↓

Category Discovery
(returns Top Categories)

↓

Perspective Resolver

↓

Perspective Library

↓

Parallel Perspective Employees

↓

Insight Curator

↓

Editorial Team

↓

Final Article
```

---

# Editorial Team Direction

We decided NOT to place these during discovery:

- Analogies
- Storytelling
- Hooks
- Writing Structure

These belong to the Editorial Team.

The research stage should focus only on developing ideas.

---

# Lessons Learned

The biggest lesson from today:

**We over-designed several future components before they were needed.**

Many architectural decisions changed because we were solving problems that did not yet exist.

From tomorrow onward, development will follow a much stricter principle:

> Build only the next required employee.

Design only what is immediately needed.

Future improvements should be added only when the workflow naturally requires them.

This will keep the architecture simpler, reduce unnecessary refactoring, and allow the organization to evolve organically.

---

# Next Goal (Day 3)

Implement the **Perspective Resolver**.

Responsibilities:

- Compare discovered perspectives against the Perspective Library.
- Normalize names.
- Detect genuinely new perspectives.
- Send unknown perspectives to the Perspective Librarian.

This will establish the organization's long-term memory and prepare the system for dynamic learning.
