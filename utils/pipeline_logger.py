from datetime import datetime


def log_entry(stage: str, emoji: str, summary: str, details: dict = None) -> dict:
    """Create a single pipeline log entry."""
    return {
        "stage": stage,
        "emoji": emoji,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "summary": summary,
        "details": details or {},
    }


def format_log(pipeline_log: list[dict]) -> str:
    """Format the full pipeline log for terminal display."""
    if not pipeline_log:
        return "\n  No pipeline activity yet.\n"

    width = 64
    lines = [
        "",
        "┌" + "─" * width + "┐",
        "│" + "  📋 PIPELINE PROGRESS LOG".center(width) + "│",
        "├" + "─" * width + "┤",
    ]

    for i, entry in enumerate(pipeline_log):
        header = f"{entry['emoji']}  {entry['stage']}  ({entry['timestamp']})"
        lines.append("│  " + header.ljust(width - 2) + "│")
        lines.append("│  " + f"→ {entry['summary']}".ljust(width - 2) + "│")

        details = entry.get("details", {})
        for key, value in details.items():
            if isinstance(value, list):
                lines.append("│  " + f"  • {key}:".ljust(width - 2) + "│")
                for item in value[:8]:
                    item_str = str(item)
                    if len(item_str) > width - 10:
                        item_str = item_str[: width - 13] + "..."
                    lines.append("│  " + f"    - {item_str}".ljust(width - 2) + "│")
                if len(value) > 8:
                    remaining = len(value) - 8
                    lines.append("│  " + f"    ... and {remaining} more".ljust(width - 2) + "│")
            else:
                val_str = str(value)
                max_len = width - len(key) - 10
                if len(val_str) > max_len:
                    val_str = val_str[: max_len - 3] + "..."
                lines.append("│  " + f"  • {key}: {val_str}".ljust(width - 2) + "│")

        if i < len(pipeline_log) - 1:
            lines.append("│" + " " * width + "│")

    lines.append("└" + "─" * width + "┘")
    return "\n".join(lines)
