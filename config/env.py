from dotenv import load_dotenv
import os

load_dotenv()


class Env:
    # ----------------- Gemini API Keys -----------------
    GEMINI_API_KEYS = []
    
    # Check for comma-separated list
    gemini_keys_str = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEYS")
    if gemini_keys_str:
        GEMINI_API_KEYS = [k.strip() for k in gemini_keys_str.split(",") if k.strip()]
    
    # Check for GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
    i = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if not key:
            break
        if key.strip() not in GEMINI_API_KEYS:
            GEMINI_API_KEYS.append(key.strip())
        i += 1

    # Fallback to single GEMINI_API_KEY if list is empty
    if not GEMINI_API_KEYS and os.getenv("GEMINI_API_KEY"):
        GEMINI_API_KEYS = [os.getenv("GEMINI_API_KEY").strip()]

    # ----------------- Nvidia API Keys -----------------
    NVIDIA_API_KEYS = []
    
    # Check for comma-separated list
    nvidia_keys_str = os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEYS")
    if nvidia_keys_str:
        NVIDIA_API_KEYS = [k.strip() for k in nvidia_keys_str.split(",") if k.strip()]
    
    # Check for NVIDIA_API_KEY_1, NVIDIA_API_KEY_2, etc.
    i = 1
    while True:
        key = os.getenv(f"NVIDIA_API_KEY_{i}")
        if not key:
            break
        if key.strip() not in NVIDIA_API_KEYS:
            NVIDIA_API_KEYS.append(key.strip())
        i += 1

    # Fallback to single NVIDIA_API_KEY if list is empty
    if not NVIDIA_API_KEYS and os.getenv("NVIDIA_API_KEY"):
        NVIDIA_API_KEYS = [os.getenv("NVIDIA_API_KEY").strip()]

    # ----------------- OpenAI API Keys -----------------
    OPENAI_API_KEYS = []

    openai_keys_str = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEYS")
    if openai_keys_str:
        OPENAI_API_KEYS = [k.strip() for k in openai_keys_str.split(",") if k.strip()]

    i = 1
    while True:
        key = os.getenv(f"OPENAI_API_KEY_{i}")
        if not key:
            break
        if key.strip() not in OPENAI_API_KEYS:
            OPENAI_API_KEYS.append(key.strip())
        i += 1
