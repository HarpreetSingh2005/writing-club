# Shared Workspace (State)

The State is the company's shared workspace.

Employees never communicate directly.

Every employee only reads and writes to State.

---

raw_input

Description:

Original user input.

Written by:

Input Receiver

---

summary

Description:

Condensed representation of the user's thoughts.

Written by:

Summarizer

Read by:

Perspective Discovery

CEO

---

keywords

Description:

Important terms.

---

entities

Description:

People

Organizations

Places

Concepts

---

goal

Description:

What the user ultimately wants.

---

candidate_perspectives

Description:

Every possible perspective.

Example

Politics

Psychology

Economics

History

---

matched_perspectives

Description:

Perspectives already existing in the library.

---

new_perspectives

Description:

Perspectives not found in the library.

---

ranked_perspectives

Description:

Perspective

Score

Priority

---

dynamic_employees

Description:

Employees created for this execution.

---

research_reports

Description:

Array of reports.

Example

[
{
perspective:"Psychology",
report:"..."
},

    {
        perspective:"Politics",
        report:"..."
    }

]

---

draft

Description:

Final article.

---

feedback

Description:

Human review.

Future.
