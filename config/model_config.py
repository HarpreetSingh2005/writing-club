from dataclasses import dataclass

from config.env import Env


@dataclass
class ModelConfig:
    """
    Configuration schema for a specific LLM model instance.
    Defines the provider, exact model string, configured API keys, 
    and routing priority.
    """

    provider: str       # e.g., 'gemini', 'openai', 'nvidia'

    model: str          # Model identifier string used by the API client

    api_keys: list[str] # List of API keys available for this provider

    priority: int       # Priority score; lower priority is tried first on failure

    enabled: bool = True # Flag to quickly enable/disable a model configuration

    tasks: tuple[str, ...] = ("general",) # Specific workflow tasks this model is suited for


# List of configured models with their priority rankings and key fallbacks
AVAILABLE_MODELS = [

    ModelConfig(
        provider="gemini",
        model="gemini-3.6-flash",
        api_keys=Env.GEMINI_API_KEYS,
        priority=1,
        tasks=("transcription", "transcription_cleanup", "summarization", "discovery", "outline", "auto_critic", "general"),
    ),

    ModelConfig(
        provider="openai",
        model="gpt-5.6-luna",
        api_keys=Env.OPENAI_API_KEYS,
        priority=2,
        tasks=("transcription_cleanup", "summarization", "discovery", "general"),
    ),

    ModelConfig(
        provider="openai",
        model="gpt-5.6-terra",
        api_keys=Env.OPENAI_API_KEYS,
        priority=3,
        tasks=("drafting", "outline", "critique", "style_learning", "auto_critic", "general"),
    ),

    ModelConfig(
        provider="nvidia",
        model="meta/llama-3.3-70b-instruct",
        api_keys=Env.NVIDIA_API_KEYS,
        priority=4,
        tasks=("research", "critique", "drafting", "general"),
    ),

    # Local Ollama as the absolute last resort fallback.
    # It is intentionally absent from TASK_POLICY, so it always ranks last,
    # and its high priority ensures it sits behind every cloud provider.
    ModelConfig(
        provider="ollama",
        model=Env.OLLAMA_MODEL,
        api_keys=[],
        priority=100,
        enabled=Env.OLLAMA_ENABLED,
        tasks=("general",),
    ),

]


# Task policy defines which provider is preferred for each specific job.
# When a task is executed, the system resolves available models in this order.
# Empty strings act as disabled fallbacks.
TASK_POLICY = {
    # Preferred order of providers for converting speech-to-text or cleaning it up
    "transcription": ("gemini", "openai", "ollama"),
    "transcription_cleanup": ("gemini", "openai", "ollama"),
    
    # Preferred order of providers for summarizing transcripts
    "summarization": ("ollama", "gemini", "openai", "ollama"),

    # Preferred order for discovering creative expert perspectives
    "discovery": ("gemini", "openai", "ollama"),
    
    # Preferred order for researching insights and identifying blind spots
    "research": ("openai", "gemini", "ollama"),
    "critique": ("openai", "gemini", "ollama"),
    
    # Preferred order for outlining articles
    "outline": ("openai", "gemini", "ollama"),
    
    # Preferred order for drafting the prose
    "drafting": ("openai", "", "gemini", "ollama"),
    
    # Preferred order for style modeling and refinement
    "style_learning": ("openai", "gemini", "ollama"),
    
    # Automatic evaluation of flow/draft for AI markers and quality (Gemini first, then GPT)
    "auto_critic": ("gemini", "openai", "ollama"),
    
    # General fallback order
    "general": ("gemini", "openai", "ollama"),
}


