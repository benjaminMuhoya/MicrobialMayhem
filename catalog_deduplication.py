"""Stable deduplication for persisted BacDive-derived fighter catalogs."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from bacterial_names import format_bacterial_name, sanitize_designation

MISSING_VALUES = {"", "no", "none", "null", "unknown", "not specified", "n/a"}


def normalize_identity(value: Any) -> str:
    text = sanitize_designation(str(value or "")).casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def meaningful_strain(value: Any) -> str:
    normalized = normalize_identity(value)
    return "" if normalized in MISSING_VALUES else normalized


def fighter_identity_key(fighter: dict) -> tuple[str, str]:
    """Identify one organism/strain while collapsing unspecified duplicate rows."""
    scientific_designation = format_bacterial_name(fighter.get("full_name", "")).plain
    name = normalize_identity(scientific_designation)
    strain = meaningful_strain(fighter.get("strain"))
    if not name:
        return ("bacdive", normalize_identity(fighter.get("bacdive_id") or fighter.get("catalog_id")))
    return (name, strain)


def completeness_score(fighter: dict) -> tuple[int, int, str]:
    """Prefer populated, information-rich records with a deterministic tie-break."""
    populated = 0
    detail = 0
    for value in fighter.values():
        if isinstance(value, list):
            useful = [item for item in value if normalize_identity(item) not in MISSING_VALUES]
            populated += bool(useful)
            detail += len(useful)
        elif isinstance(value, dict):
            populated += bool(value)
            detail += len(value)
        elif normalize_identity(value) not in MISSING_VALUES:
            populated += 1
            detail += min(len(str(value)), 200)
    bacdive_id = str(fighter.get("bacdive_id") or fighter.get("catalog_id") or "")
    return populated, detail, bacdive_id


def deduplicate_fighters(fighters: list[dict]) -> tuple[list[dict], int]:
    """Keep the most complete representative for each stable identity key."""
    representatives: dict[tuple[str, str], dict] = {}
    order: list[tuple[str, str]] = []
    for fighter in fighters:
        key = fighter_identity_key(fighter)
        if key not in representatives:
            representatives[key] = fighter
            order.append(key)
        elif completeness_score(fighter) > completeness_score(representatives[key]):
            representatives[key] = fighter
    kept = [representatives[key] for key in order]
    return kept, len(fighters) - len(kept)
