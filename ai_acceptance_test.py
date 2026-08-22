import os
import time

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# =====================================================================
# CONFIGURATION
# =====================================================================
API_KEY = os.getenv("NVIDIA_API_KEY", "")
MODEL_NAME = os.getenv("NVIDIA_TEST_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
BASE_URL = "https://integrate.api.nvidia.com/v1"  # Set to "https://openrouter.ai/api/v1" or similar if needed
PROMPT = "Write a short one-sentence greeting."

if not API_KEY:
    raise SystemExit("NVIDIA_API_KEY is not set. Add it to your .env file.")

print(f"Initializing model: {MODEL_NAME}")
llm = ChatOpenAI(
    model=MODEL_NAME, 
    api_key=API_KEY, 
    base_url=BASE_URL,
    temperature=0.2
)

print(f"Sending prompt: '{PROMPT}'")
print("Response: ", end="", flush=True)

start_time = time.perf_counter()
ttft = None

try:
    # Stream the reply and measure timing
    for chunk in llm.stream(PROMPT):
        if ttft is None:
            ttft = time.perf_counter() - start_time
        print(chunk.content, end="", flush=True)
    print()

    total_time = time.perf_counter() - start_time
    
    print("-" * 50)
    print(f"Time to First Token (TTFT): {ttft:.3f} seconds")
    print(f"Total Response Time:        {total_time:.3f} seconds")
    print("-" * 50)

except Exception as e:
    print(f"\nError occurred: {e}")
