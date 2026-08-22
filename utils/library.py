from pathlib import Path
from dataclasses import asdict
import json

from models.perspective import Department

LIBRARY = Path("library room")
STYLE_LIBRARY = LIBRARY / "writing styles"


def get_path(name: str) -> Path:
    """Get the file path for a department JSON file."""
    return LIBRARY / f"{name}.json"


def exists(name: str) -> bool:
    """Check if a department file exists and is non-empty."""
    path = get_path(name)
    return path.exists() and path.stat().st_size > 0


def load(name: str) -> Department:
    """Load a department from the library room. Raises ValueError if missing or empty."""
    path = get_path(name)

    if not path.exists():
        raise ValueError(f"Department file not found: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Department file is empty: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return Department(**json.load(f))


def save(department: Department):
    """Save a department entry to the library room."""
    LIBRARY.mkdir(exist_ok=True)

    with open(get_path(department.name), "w", encoding="utf-8") as f:
        json.dump(
            asdict(department),
            f,
            indent=4,
            ensure_ascii=False,
        )


def get_style_path(style_name: str) -> Path:
    """Get the file path for a writing style JSON file."""
    safe_name = style_name.strip().lower().replace(" ", "_") or "default"
    return STYLE_LIBRARY / f"{safe_name}.json"


def load_style(style_name: str) -> dict:
    """Load a writing style profile. Returns empty dict if not found."""
    path = get_style_path(style_name)
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_style(style_name: str, profile: dict) -> None:
    """Save a writing style profile to the style library."""
    STYLE_LIBRARY.mkdir(parents=True, exist_ok=True)

    with open(get_style_path(style_name), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4, ensure_ascii=False)
