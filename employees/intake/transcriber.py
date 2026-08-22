import mimetypes
from pathlib import Path

from config.env import Env
from state import State
from utils.pipeline_logger import log_entry


SUPPORTED_AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma", ".webm", ".mp4"}


def _transcribe_with_local_whisper(audio_path: str) -> str:
    """Transcribe audio locally using downloaded OpenAI Whisper base model."""
    import whisper

    print("Loading local Whisper 'base' model (will download on first run)...")
    # Load the base model (downloads to cache if not already present)
    model = whisper.load_model("base")

    print("Running local transcription...")
    result = model.transcribe(audio_path)
    return result.get("text", "").strip()


def _transcribe_with_gemini(audio_path: str) -> str:
    """Transcribe audio using Google Gemini multimodal API."""
    import google.generativeai as genai

    api_keys = Env.GEMINI_API_KEYS
    if not api_keys:
        raise RuntimeError("No Gemini API keys configured for audio transcription.")

    mime_type = mimetypes.guess_type(audio_path)[0] or "audio/mpeg"

    for idx, api_key in enumerate(api_keys):
        try:
            genai.configure(api_key=api_key)
            audio_file = genai.upload_file(audio_path, mime_type=mime_type)

            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content([
                "Transcribe this audio recording completely and accurately. "
                "Include every spoken word exactly as said, including filler words, "
                "repetitions, and informal language. "
                "Return ONLY the raw transcription text, nothing else.",
                audio_file,
            ])

            try:
                genai.delete_file(audio_file.name)
            except Exception:
                pass

            return response.text

        except Exception as e:
            print(f"[X] Gemini transcription with key #{idx + 1} failed: {e}")
            continue

    raise RuntimeError("All Gemini keys failed for audio transcription.")


def _transcribe_with_openai(audio_path: str) -> str:
    """Transcribe audio using OpenAI Whisper API (fallback)."""
    from openai import OpenAI

    api_keys = Env.OPENAI_API_KEYS
    if not api_keys:
        raise RuntimeError("No OpenAI API keys configured for audio transcription.")

    for idx, api_key in enumerate(api_keys):
        try:
            client = OpenAI(api_key=api_key)
            with open(audio_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                )
            return result.text
        except Exception as e:
            print(f"[X] OpenAI Whisper with key #{idx + 1} failed: {e}")
            continue

    raise RuntimeError("All OpenAI keys failed for audio transcription.")


def transcribe_audio(audio_path: str) -> str:
    """Try local Whisper first, then Gemini/OpenAI Whisper as fallbacks."""
    errors = []

    # 1. Try local Whisper model
    try:
        print("Trying local Whisper transcription (base model)...")
        return _transcribe_with_local_whisper(audio_path)
    except Exception as e:
        print(f"[X] Local Whisper transcription failed: {e}")
        errors.append(f"Local Whisper: {e}")

    # 2. Fallback to Gemini
    if Env.GEMINI_API_KEYS:
        try:
            print("Trying Gemini for audio transcription...")
            return _transcribe_with_gemini(audio_path)
        except Exception as e:
            errors.append(f"Gemini: {e}")

    # 3. Fallback to OpenAI Whisper API
    if Env.OPENAI_API_KEYS:
        try:
            print("Trying OpenAI Whisper for audio transcription...")
            return _transcribe_with_openai(audio_path)
        except Exception as e:
            errors.append(f"OpenAI: {e}")

    raise RuntimeError(
        "Audio transcription failed with all providers.\n" + "\n".join(errors)
    )


def transcriber(state: State):
    """LangGraph node: transcribe audio file to text."""
    audio_path = state.get("audio_file_path", "")
    if not audio_path:
        return {}

    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if path.suffix.lower() not in SUPPORTED_AUDIO:
        raise ValueError(
            f"Unsupported format: {path.suffix}. Supported: {', '.join(sorted(SUPPORTED_AUDIO))}"
        )

    print(f"\n🎤 Transcribing: {path.name}")
    transcript = transcribe_audio(audio_path)
    print(f"[OK] Transcription complete ({len(transcript)} characters)")

    return {
        "transcript": transcript,
        "pipeline_log": [
            log_entry(
                "Transcriber", "🎤",
                f"Transcribed {path.name} ({len(transcript)} chars)",
                {"file": path.name, "preview": transcript},
            )
        ],
    }
