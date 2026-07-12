# Development Log 001

## Milestone: First Working LangGraph AI Pipeline

**Status:** ✅ Completed

---

# Objective

Build the first end-to-end LangGraph workflow for Writing Club.

The goal was not to build the final product, but to understand how LangGraph orchestrates AI workflows while establishing a clean project architecture.

---

# What We Built

Current pipeline:

```
Transcript
     │
     ▼
Thought Organizer (Summarizer)
     │
     ▼
END
```

The graph successfully accepts a raw transcript, processes it using Gemini, and returns a cleaned, structured narrative.

---

# Architecture

```
writing-club/
│
├── app.py
├── graph.py
├── state.py
├── llm.py
│
├── nodes/
│   └── summarizer.py
│
├── prompts/
│   └── summarizer.txt
│
├── utils/
│   └── prompt_loader.py
│
└── .env
```

---

# Components Created

## 1. State

Shared state between nodes.

Current fields:

- transcript
- summary

---

## 2. Graph

Created the first LangGraph workflow.

```
START
   │
   ▼
Summarizer
   │
   ▼
END
```

---

## 3. LLM Layer

Created a dedicated `ask_llm()` abstraction.

Responsibilities:

- Load Gemini
- Handle model invocation
- Return plain text
- Hide provider-specific implementation details

This ensures future migration to OpenAI, Ollama, Claude, etc. requires changes in only one file.

---

## 4. Prompt Loader

Implemented reusable prompt loading.

```
get_prompt(
    "summarizer",
    transcript=...
)
```

Responsibilities:

- Read prompt files
- Inject variables
- Keep prompts separate from Python code

---

## 5. Prompt Engineering

Moved prompts out of Python into dedicated prompt files.

Current prompt:

- summarizer.txt

Future prompts:

- insight_generator.txt
- outline_generator.txt
- article_writer.txt
- reviewer.txt
- title_generator.txt

---

# Lessons Learned

## Separation of Concerns

Every file has one responsibility.

| File             | Responsibility         |
| ---------------- | ---------------------- |
| app.py           | Starts the application |
| graph.py         | Defines workflow       |
| state.py         | Shared data            |
| llm.py           | Talks to Gemini        |
| summarizer.py    | Cleans transcript      |
| prompt_loader.py | Loads prompts          |

---

## Node Design Philosophy

Every node should answer three questions.

### Reads

Which state variables does it need?

### Writes

Which state variables does it produce?

### Responsibility

What is the single responsibility of this node?

---

## Important Realization

The "Summarizer" is actually closer to a **Thought Organizer** than a traditional summarizer.

Its job is to:

- remove filler words
- remove repetition
- preserve chronology
- preserve conclusions
- preserve intent

It should **not** generate new ideas.

---

# Key Product Discovery

Originally the pipeline was imagined as:

```
Transcript
     │
     ▼
Summary
     │
     ▼
Article
```

Testing with a real transcript revealed an important limitation.

The final published article contained many ideas that were **never spoken** in the original transcript.

Examples:

- Spotlight Effect
- "Nobody pays the price except you."
- Psychological explanations
- Deeper interpretations

These were products of reasoning, not summarization.

This fundamentally changes the architecture of Writing Club.

---

# Proposed New Pipeline

```
Voice Note
      │
      ▼
Speech-to-Text
      │
      ▼
Thought Organizer
      │
      ▼
Insight Generator
      │
      ▼
Outline Generator
      │
      ▼
Article Writer
      │
      ▼
Human Review
      │
      ▼
Final Article
```

---

# Major New Idea — Expert Council

One of the biggest ideas from today's session.

Instead of relying on a single LLM to generate insights, introduce a panel of specialized AI experts.

Each expert receives the same cleaned summary but analyzes it from a different perspective.

Example experts:

- Psychologist
- Philosopher
- Storyteller
- Behavioral Scientist
- Devil's Advocate

---

## Phase 1 — Independent Thinking

Every expert works independently.

No agent can see another agent's answer.

Purpose:

Avoid groupthink and encourage diverse reasoning.

---

## Phase 2 — Council Discussion

Experts review one another's conclusions.

They may:

- agree
- disagree
- refine
- challenge assumptions
- identify missing perspectives

---

## Phase 3 — Council Synthesizer

A final AI agent combines the discussion into a unified Insight Report.

This report becomes the foundation for:

- article outlines
- hooks
- themes
- arguments
- psychological concepts

---

# Future Enhancement

The council should eventually become dynamic.

Instead of always selecting the same experts, the system should first classify the topic and then assemble the most relevant panel.

Examples:

Psychology article

↓

Psychologist
Behavioral Scientist
Storyteller
Devil's Advocate

Startup article

↓

Founder
Product Manager
Investor
Devil's Advocate

Blockchain article

↓

Cryptographer
Economist
Security Engineer
Devil's Advocate

The long-term vision is for Writing Club to dynamically assemble the best AI team for each idea.

---

# Immediate Next Milestone

Build the Insight Generator node.

Responsibilities:

- Read cleaned summary
- Discover hidden ideas
- Identify psychological concepts
- Identify philosophical concepts
- Generate possible article angles
- Produce an Insight Report for downstream nodes

---

# Current Status

✅ Project initialized

✅ LangGraph installed

✅ Gemini integrated

✅ Prompt system implemented

✅ First working LangGraph pipeline completed

✅ Prompt loading abstraction completed

✅ Clean architecture established

🚧 Insight Generator (Next)

🚧 Multi-agent Council

🚧 Outline Generator

🚧 Article Writer

🚧 Human Review

---

## Closing Thought

Today's goal was to learn LangGraph.

Instead, the session evolved into designing the architecture of a true AI writing system.

The biggest realization was that writing is not a single LLM call—it is a sequence of specialized reasoning steps.

Writing Club is no longer envisioned as a chatbot.

It is becoming an AI writing studio composed of specialized agents that collaborate to transform raw human thoughts into meaningful writing.
