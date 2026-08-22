# API Routing and Key Switching

The project now supports two levels of switching:

1. Multiple keys for the same provider.
2. Multiple providers for the same task.

Configuration lives in `config/model_config.py`.

## Key Format

Each provider can read either a comma-separated list:

```text
GEMINI_API_KEYS=key1,key2,key3
```

or numbered variables:

```text
GEMINI_API_KEY_1=key1
GEMINI_API_KEY_2=key2
```

The same pattern is supported for `NVIDIA_API_KEY` and `OPENAI_API_KEY`.

## Task Routing

`TASK_POLICY` decides provider order for each job:

- `summarization`
- `discovery`
- `research`
- `critique`
- `outline`
- `drafting`
- `style_learning`
- `general`

When a call is made, `ask_llm(..., task="drafting")` chooses the best available model for that task. If the first key fails because of rate limits, quota, or another API issue, the system tries the next key and then the next provider.

## Practical Preference

Current default preference:

- Gemini `gemini-3.6-flash` for fast cleanup, summaries, and discovery.
- OpenAI `gpt-5.6-luna` as a cost-sensitive fallback for high-volume simple work.
- OpenAI `gpt-5.6-terra` for flow, critique, style learning, and drafting.
- NVIDIA-hosted Qwen as a research/critique fallback while you are prototyping.

Use fast and cheaper models for cleanup and summary. Use stronger reasoning models for expert reports and critique. Use the model with the best prose quality for final drafting.

This keeps cost lower while preserving quality where it matters most.
