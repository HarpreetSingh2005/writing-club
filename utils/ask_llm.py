import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from config.model_config import AVAILABLE_MODELS as MODELS, TASK_POLICY


# ---------------------------------------------------
# Model Builders
# ---------------------------------------------------
# Registry mapping provider identifier strings to their respective LangChain class instantiations.
MODEL_BUILDERS = {

    # Instantiates Google Gemini models using the langchain_google_genai library
    "gemini": lambda model, api_key, temperature: ChatGoogleGenerativeAI(
        model=model.model,
        google_api_key=api_key,
        temperature=temperature,
    ),

    # Instantiates Nvidia NIM API endpoints using ChatOpenAI mapping to Nvidia base URL
    "nvidia": lambda model, api_key, temperature: ChatOpenAI(
        model=model.model,
        api_key=api_key,
        base_url="https://integrate.api.nvidia.com/v1",
        temperature=temperature,
    ),

    # Instantiates OpenAI/OpenRouter models. If API key is an OpenRouter key (starts with sk-or-),
    # it maps models to OpenRouter's URL format and handles model aliases.
    "openai": lambda model, api_key, temperature: ChatOpenAI(
        model=(
            "openai/gpt-4o-mini" if model.model == "gpt-5.6-luna"
            else "openai/gpt-4o" if model.model == "gpt-5.6-terra"
            else model.model
        ) if api_key.startswith("sk-or-") else model.model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1" if api_key.startswith("sk-or-") else None,
        temperature=temperature,
    ),

}

# Default token limits per task to prevent runaway costs on paid APIs
TASK_TOKEN_LIMITS = {
    "transcription": 4000,
    "transcription_cleanup": 4000,
    "summarization": 2000,
    "discovery": 2000,
    "research": 2000,
    "critique": 2000,
    "outline": 1500,
    "drafting": 4000,
    "style_learning": 1000,
    "general": 2000,
}


def _models_for_task(task: str):
    """
    Resolves the prioritized candidate models for a given task.
    Sorts them based on the TASK_POLICY provider rankings and the model priorities.
    """
    provider_order = TASK_POLICY.get(task, TASK_POLICY["general"])
    provider_rank = {provider: rank for rank, provider in enumerate(provider_order)}

    return sorted(
        [model for model in MODELS if model.enabled and (task in model.tasks or "general" in model.tasks)],
        key=lambda model: (
            provider_rank.get(model.provider, len(provider_order)),
            model.priority,
        ),
    )


def _try_repair_json(raw_text: str, llm) -> dict | list | None:
    """
    Attempt to repair malformed JSON by asking the same LLM to fix it.
    Returns parsed JSON on success, None on failure.
    """
    repair_prompt = (
        "The following text was supposed to be valid JSON but has syntax errors. "
        "Fix ONLY the JSON syntax (missing commas, quotes, brackets, trailing commas, etc.) "
        "and return ONLY the corrected valid JSON. Do not change any content.\n\n"
        f"{raw_text}"
    )
    try:
        response = llm.invoke(repair_prompt)
        content = response.content if isinstance(response.content, str) else str(response.content)
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        return json.loads(cleaned)
    except Exception:
        return None


def ask_llm(
    prompt: str,
    temperature: float = 0.2,
    expect_json: bool = False,
    task: str = "general",
    max_tokens: int | None = None,
    ):
    """
    The main routing query interface. It:
    1. Selects candidate models suitable for the requested task.
    2. Sequentially attempts to query each candidate.
    3. Handles fallback across multiple keys for a model.
    4. Automatically falls back to next preferred provider/model if a service fails.
    5. Cleans and parses the output as JSON if expect_json=True.
    6. Attempts JSON repair before switching providers on parse failures.
    7. Applies per-task token limits to control costs.
    """

    models = _models_for_task(task)

    # Determine the token limit: explicit arg > task default > global fallback
    token_limit = max_tokens or TASK_TOKEN_LIMITS.get(task, 2000)

    for model in models:

        builder = MODEL_BUILDERS.get(model.provider)

        if builder is None:
            continue

        api_keys = model.api_keys if model.api_keys else [""]

        # Loop through each configured key for the current model
        for idx, api_key in enumerate(api_keys):
            key_label = f"key #{idx + 1}" if len(api_keys) > 1 else "default key"
            try:
                print(f"Trying {model.provider} ({model.model}) for {task} using {key_label}...")

                # Initialize the model instance using the registered builder
                llm = builder(model, api_key, temperature)

                # Bind token limit to prevent runaway costs
                if model.provider == "gemini":
                    llm = llm.bind(max_output_tokens=token_limit)
                else:
                    llm = llm.bind(max_tokens=token_limit)

                # Invoke the prompt
                response = llm.invoke(prompt)

                # Extract response text content safely
                if isinstance(response.content, str):
                    content = response.content
                else:
                    content = "".join(
                        block["text"]
                        for block in response.content
                        if block.get("type") == "text"
                    )

                print(f"[OK] Using {model.provider} ({model.model}) for {task} with {key_label}")

                # If JSON response is expected, clean Markdown syntax blocks (e.g. ```json ... ```)
                # and return parsed python dictionary/list
                if expect_json:
                    cleaned = content.strip()
                    if cleaned.startswith("```"):
                        lines = cleaned.split("\n")
                        if lines[0].strip().startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        cleaned = "\n".join(lines).strip()

                    try:
                        return json.loads(cleaned)
                    except json.JSONDecodeError:
                        # JSON parse failed — attempt repair with same LLM before giving up
                        print(f"[!] JSON parse failed, attempting repair...")
                        repaired = _try_repair_json(content, llm)
                        if repaired is not None:
                            print(f"[OK] JSON repair successful")
                            return repaired
                        print(f"[X] JSON repair also failed, trying next provider...")
                        continue

                return content

            except Exception as e:
                # Print failure details and attempt next API key / next model candidate
                print(f"[X] {model.provider} with {key_label} failed.")
                print(e)
                continue

    raise RuntimeError("No available model or API key could process the request.")
