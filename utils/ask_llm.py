import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config.model_config import AVAILABLE_MODELS as MODELS



# ---------------------------------------------------
# Model Builders
# ---------------------------------------------------

MODEL_BUILDERS = {

    "gemini": lambda model, temperature: ChatGoogleGenerativeAI(
        model=model.model,
        google_api_key=model.api_key,
        temperature=temperature,
    ),

    "nvidia": lambda model, temperature: ChatOpenAI(
        model=model.model,
        api_key=model.api_key,
        base_url="https://integrate.api.nvidia.com/v1",
        temperature=temperature,
    ),

}


def ask_llm(
    prompt: str,
    temperature: float = 0.2,
    expect_json: bool = False,
    ):

    models = sorted(
        [model for model in MODELS if model.enabled],
        key=lambda model: model.priority
    )

    for model in models:

        builder = MODEL_BUILDERS.get(model.provider)

        if builder is None:
            continue

        try:

            print(f"Model Key: {model.api_key}")
            print(f"Trying {model.provider} ({model.model})")

            llm = builder(model, temperature)

            response = llm.invoke(prompt)

            if isinstance(response.content, str):
                content = response.content

            else:
                content = "".join(
                    block["text"]
                    for block in response.content
                    if block.get("type") == "text"
                )

            print(f"✓ Using {model.provider} ({model.model})")

            if expect_json:
                return json.loads(content)

            return content

        except Exception as e:

            print(f"✗ {model.provider} failed.")
            print(e)

            continue

    raise RuntimeError("No available model could process the request.")