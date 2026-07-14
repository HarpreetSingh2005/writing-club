# Employee Handbook

Every employee follows the same lifecycle.

Input

↓

Read State

↓

Perform ONE responsibility

↓

Update State

↓

Finish

Employees never perform multiple unrelated tasks.

---

# Employee Definition

Every employee consists of:

- Name
- Responsibility
- Model
- System Prompt
- Tools
- Input State
- Output State

---

# Example

Name:
Summarizer

Responsibility:
Summarize raw thoughts.

Reads:

- raw_input

Writes:

- summary

Tools:

None

Model:

GPT-5

---

Name:
Perspective Discovery Specialist

Responsibility:

Discover every possible perspective.

Reads:

summary

Writes:

candidate_perspectives

---

Name:
Perspective Matcher

Responsibility:

Compare discovered perspectives against the Perspective Library.

Reads:

candidate_perspectives

Writes:

matched_perspectives

new_perspectives

---

Name:
Perspective Ranker

Responsibility:

Score each perspective based on relevance.

Writes:

ranked_perspectives

---

Name:
Perspective Librarian

Responsibility:

Create metadata for new perspectives.

Writes:

Perspective Library

---

Name:
Hiring Manager

Responsibility:

Create expert employees.

Writes:

dynamic_employees

---

Name:
Research Employee

Responsibility:

Research ONE perspective.

Writes:

research_report

---

Name:
CEO

Responsibility:

Combine every report into one final narrative.

Writes:

draft
