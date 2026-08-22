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

]


# Task policy defines which provider is preferred for each specific job.
# When a task is executed, the system resolves available models in this order.
# Empty strings act as disabled fallbacks.
TASK_POLICY = {
    # Preferred order of providers for converting speech-to-text or cleaning it up
    "transcription": ("gemini", "openai"),
    "transcription_cleanup": ("gemini", "openai", ""),
    
    # Preferred order of providers for summarizing transcripts
    "summarization": ("gemini", "openai", ""),
    
    # Preferred order for discovering creative expert perspectives
    "discovery": ("gemini", "", "openai"),
    
    # Preferred order for researching insights and identifying blind spots
    "research": ("", "openai", "gemini"),
    "critique": ("", "openai", "gemini"),
    
    # Preferred order for outlining articles
    "outline": ("openai", "gemini", ""),
    
    # Preferred order for drafting the prose
    "drafting": ("openai", "", "gemini"),
    
    # Preferred order for style modeling and refinement
    "style_learning": ("openai", "gemini", ""),
    
    # Automatic evaluation of flow/draft for AI markers and quality (Gemini first, then GPT)
    "auto_critic": ("gemini", "openai", ""),
    
    # General fallback order
    "general": ("gemini", "", "openai"),
}


