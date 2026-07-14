from dataclasses import dataclass

from config.env import Env


@dataclass
class ModelConfig:

    provider: str

    model: str

    api_key: str

    priority: int

    enabled: bool = True

AVAILABLE_MODELS = [

    ModelConfig(
        provider="gemini",
        model="gemini-3.5-flash",
        api_key=Env.GEMINI_API_KEY,
        priority=1
    ),

    ModelConfig(
        provider="nvidia",
        model="qwen/qwen3.5-122b-a10b",
        api_key=Env.NVIDIA_API_KEY,
        priority=2
    )

]

