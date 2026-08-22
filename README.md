Writing Club is an AI writing organization that turns a raw voice idea into an article through specialized employees.

The intended flow is:

1. The user provides a spoken transcript.
2. The intake team cleans and summarizes it without adding new ideas.
3. The planning team discovers useful expert perspectives.
4. The librarian stores reusable department knowledge and writing-style knowledge.
5. Expert researchers review the idea from their fields.
6. The insight curator selects the strongest points.
7. The flow architect proposes a small article flow for approval.
8. After approval, the article writer drafts the full piece.
9. The user can provide feedback and rerun drafting with the same approved flow.

## Approval Loop

The graph intentionally stops after creating `proposed_flow` unless `flow_approved` is true.

First pass:

```python
result = graph.invoke({
    "transcript": transcript,
    "flow_approved": False,
    "user_feedback": "",
})
```

Show `result["proposed_flow"]` to the user.

Second pass after approval:

```python
final_result = graph.invoke({
    **result,
    "flow_approved": True,
    "user_feedback": "Keep it raw and personal.",
})
```

The draft will be in `final_result["draft"]`.

## Libraries

The project maintains two persistent libraries:

- `library room/*.json`: broad department knowledge used by expert researchers.
- `library room/writing styles/*.json`: reusable voice and structure rules inferred from the user's writing style.

This means the system can learn both what different disciplines care about and how the user tends to write stories, raw ideas, explanations, or reflective articles.

## API Switching

API keys can be configured as comma-separated values or numbered environment variables:

```text
GEMINI_API_KEYS=key1,key2
NVIDIA_API_KEYS=key1,key2
OPENAI_API_KEYS=key1,key2
```

or:

```text
GEMINI_API_KEY_1=...
GEMINI_API_KEY_2=...
```

The model router in `config/model_config.py` chooses providers by task. If a provider or key fails, `utils/ask_llm.py` automatically tries the next key, then the next provider.

Recommended routing philosophy:

- Summarization and cleanup: prefer fast, low-cost models.
- Perspective discovery: prefer reliable structured JSON models.
- Expert research and critique: prefer stronger reasoning models.
- Flow and drafting: prefer models with the best prose quality.
