import json
import sys
import io
from pathlib import Path

# Force stdout/stderr to use UTF-8 encoding to prevent UnicodeEncodeError in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from langgraph.types import Command

from graph import build_graph
from utils.pipeline_logger import format_log


TRANSCRIPT = """
Okay so this is an article for the idea that why to care about people so this is the incidence where I was doing my exercise so normally I don't go to the gym current team but I wanted to exercise right so I started going to the ab public gym where all the old uncles and arteries come and the first It's really a not the top notch position you should work because it's really know that motivating so one day I was in this mode only like iron module to work rather than I was I really don't want to work there not go to Jim there because obviously that was not my perfect place now the equipments for the great know there were the motivation there were all the old uncles and our design no people know someone of age of my but then I was in the M okay yeah just give this and just talk to in this but at this at the same moment I servant girl so there was this when uncle came with this one a Harshit Harsh small child and she was on the wheelchair so she couldn't really work and observing her I realize that it's not about the uncle and aunty and no one was actually looking for like how is unknown was even even care about her so in the lamps nomenon daily give a shit about her and the point is that moment I saw like who am I showing this particular exercise two even is someone judges me like oh see like this guys but we were working with those artis and make me fun of me but what if in the future I don't work and for that reason my legs or my body stuff stop working out so at that moment these guys won't come to support me or to take care so why the hell should I even here to them even though I would probably shock is my the gym click way I work and how the environment is it's really the like the first environment you could ever go with like for the motivation and all that but the only thing is like these people even if they are making fun of you but when you if you stop working these people want even give a shit if you have really good or review working well a very not and even people don't even care thank you there they might be making fun for few minutes but after that day would forget that see you should just don't care and I just that is the basic idea about this
""".strip()


def get_interrupt_payload(result: dict) -> dict:
    interrupts = result.get("__interrupt__", [])
    if not interrupts:
        return {}

    first_interrupt = interrupts[0]
    return getattr(first_interrupt, "value", first_interrupt)


def print_pipeline_log(pipeline_log: list[dict]) -> None:
    """Print the full pipeline log collected so far."""
    print(format_log(pipeline_log))


def print_review(payload: dict) -> None:
    if "draft" in payload:
        print("\n" + "=" * 60)
        print("  📄 DRAFT FOR APPROVAL")
        print("=" * 60)
        print(payload.get("draft", ""))
    else:
        print("\n" + "=" * 60)
        print("  📐 PROPOSED FLOW FOR APPROVAL")
        print("=" * 60)
        print(json.dumps(payload.get("proposed_flow", payload), indent=4, default=str))
    print("\n❓ Question:", payload.get("question", "Approve this?"))


def ask_for_decision() -> dict:
    answer = input("\nApprove? [y/n]: ").strip().lower()
    feedback = input("Feedback, optional: ").strip()

    return {
        "approved": answer in {"y", "yes", "approve", "approved"},
        "feedback": feedback,
    }


def resolve_input() -> dict:
    """Determine input: audio file (CLI arg or prompt) or hardcoded transcript."""
    # Check for CLI argument: python app.py path/to/audio.mp3
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        p = Path(audio_path)
        if p.exists() and p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".webm", ".mp4"}:
            print(f"🎤 Audio file detected: {p.name}")
            return {"audio_file_path": str(p.resolve()), "transcript": ""}
        else:
            print(f"⚠️  File not found or unsupported format: {audio_path}")
            print("   Falling back to built-in transcript.\n")

    # Interactive prompt
    print("╔══════════════════════════════════════════╗")
    print("║       🖊️  Writing Club — Input Mode       ║")
    print("╠══════════════════════════════════════════╣")
    print("║  1. Paste a text transcript              ║")
    print("║  2. Provide an audio file path           ║")
    print("║  3. Use the built-in demo transcript     ║")
    print("╚══════════════════════════════════════════╝")
    choice = input("\nChoice [1/2/3]: ").strip()

    if choice == "1":
        print("Paste your transcript below (press Enter twice to finish):\n")
        lines = []
        while True:
            line = input()
            if line == "":
                if lines and lines[-1] == "":
                    break
                lines.append(line)
            else:
                lines.append(line)
        transcript = "\n".join(lines).strip()
        if transcript:
            return {"audio_file_path": "", "transcript": transcript}
        print("Empty input — falling back to demo transcript.\n")

    elif choice == "2":
        audio_path = input("Audio file path: ").strip().strip('"').strip("'")
        p = Path(audio_path)
        if p.exists():
            print(f"🎤 Audio file: {p.name}")
            return {"audio_file_path": str(p.resolve()), "transcript": ""}
        print(f"⚠️  File not found: {audio_path}")
        print("   Falling back to demo transcript.\n")

    print("📝 Using built-in demo transcript.\n")
    return {"audio_file_path": "", "transcript": TRANSCRIPT}


def main():
    graph = build_graph()
    config = {"configurable": {"thread_id": "writing-club-cli"}}

    user_input = resolve_input()

    initial_state = {
        "audio_file_path": user_input.get("audio_file_path", ""),
        "transcript": user_input.get("transcript", ""),
        "summary": "",
        "discovered_perspectives": [],
        "flow_approved": False,
        "user_feedback": "",
        "auto_revision_count": 0,
        "pipeline_log": [],
    }

    result = graph.invoke(initial_state, config=config)

    while True:
        payload = get_interrupt_payload(result)

        if payload:
            # Show the item for review
            print_review(payload)
            decision = ask_for_decision()
            result = graph.invoke(Command(resume=decision), config=config)
            continue

        if result.get("next_action") == "stop":
            print("\nStopped without generating an approved draft.")
            return

        if result.get("draft") and result.get("article_approved"):
            print("\n" + "=" * 60)
            print("  ✅ FINAL APPROVED ARTICLE")
            print("=" * 60)
            print(result["draft"])

            # Dump all project details (summary, transcript, perspectives, logs) to a file named after the article
            from utils.project_dumper import save_project_dump
            save_project_dump(result)
            return

        print("\nWorkflow ended without a draft.")
        print(json.dumps(result, indent=4, default=str))
        return


if __name__ == "__main__":
    main()
