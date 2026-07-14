from dotenv import load_dotenv
import os

load_dotenv()


class Env:

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")