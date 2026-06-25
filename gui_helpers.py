"""Small GUI text helpers that can be tested without pygame."""
from __future__ import annotations


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def wrap_text(text: str, max_width: int, measure) -> list[str]:
    """Wrap text using a caller-provided measure(string)->pixel_width function."""
    lines: list[str] = []
    current = ""
    for word in text.replace("\n", " \n ").split():
        if word == "\n":
            lines.append(current)
            current = ""
            continue
        candidate = (current + " " + word).strip()
        if not current or measure(candidate) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
