from pathlib import Path

PROMPTS_DIR = Path("prompts")


def get_prompt(name: str, **kwargs) -> str:
    prompt_path = PROMPTS_DIR / f"{name}.txt"

    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt = file.read()

    return prompt.format(**kwargs)