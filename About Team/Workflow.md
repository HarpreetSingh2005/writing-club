# Writing Club State Graph Workflow

Below is the complete architectural flow of the 15-step LangGraph multi-agent pipeline:

```text
               [ Start ]
                   │
           Is audio provided?
          /                \
        Yes                 No
        /                     \
       ▼                       ▼
1. Transcriber          2. Summarizer (Clean & condense)
       │                       ▲
       └───────────────────────┘
                               │
                               ▼
                    3. Perspective Discovery
                               │
                               ▼
                    4. Department Librarian
                               │
                               ▼
                    5. Style Librarian
                               │
                               ▼
                    6. Expert Research (Academic reports)
                               │
                               ▼
                    7. Insight Curator
                               │
                               ▼
                    8. Flow Architect (Outline & Title)
                               │
                               ▼
                    9. Auto Flow Critic (Verify transition/argument)
                               │
                      [ Approved? / Retry < 2 ]
                             /          \
                           Yes           No
                           /              \
                          ▼                ▼
                 10. Flow Approval <── Loop feedback to Flow Architect
                     (Human Interrupt)
                          │
                          ▼
                 11. Feedback Router
                  /   /      \    \
        Revise   /   /        \    \   Approved (Draft Route)
        Flow    /   /          \    \
               ▼   ▼            ▼    ▼
     [Flow Architect] [Style] [Research] 12. Article Writer (Draft prose)
               ▲                                 │
               └───────── (Loop if feedback) ─────▼
                                         13. Auto Draft Critic (Tropes/Monotony)
                                                 │
                                        [ Approved? / Retry < 2 ]
                                               /          \
                                             Yes           No
                                             /              \
                                            ▼                ▼
                                   14. Article Approval <── Loop feedback to Writer
                                       (Human Interrupt)
                                            │
                                            ▼
                                   11. Feedback Router ───► Approved / Complete
                                                                  │
                                                                  ▼
                                                         15. Final Review Notes
                                                                  │
                                                                  ▼
                                                               [ End ]
```
