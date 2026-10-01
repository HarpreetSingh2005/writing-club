from pathlib import Path

AUTHOR_SKILL_DIR = Path("library room")
AUTHOR_SKILL_PATH = AUTHOR_SKILL_DIR / "author_skill.md"


def author_skill_path() -> Path:
    """Return the absolute path of the stable Author Skill file."""
    return AUTHOR_SKILL_PATH


def load_author_skill() -> str:
    """
    Load the stable Author Skill V1 as raw text.

    The skill is read-only stable configuration: agents may use, interpret,
    select from, or critique against it, but must never rewrite it. This
    module only ever reads the file.
    """
    path = author_skill_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Author Skill not found: {path}. Run the project from the repository root."
        )
    return path.read_text(encoding="utf-8")