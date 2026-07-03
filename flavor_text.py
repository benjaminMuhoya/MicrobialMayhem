"""Context-aware, scientifically honest flavor copy for the active interface."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Iterable

from bacterial_names import sanitize_designation


MISSING_MARKERS = {
    "", "unknown", "none", "no", "no data", "not specified", "n/a",
    "no information available", "not available", "habitat not reported",
}

MISSING_MESSAGES = {
    "general": (
        "The microbes are keeping this one classified.",
        "No record surfaced in the lab notes.",
        "Science has not cracked this one yet.",
        "A mystery for the next expedition.",
    ),
    "trait": (
        "This trait is still hiding under the microscope.",
        "The database went quiet on this trait.",
        "No supported trait evidence appears in the lab notes.",
        "This biological detail remains an open question.",
    ),
    "habitat": (
        "Its usual habitat is still off the scientific map.",
        "No habitat record surfaced in the field notes.",
        "The isolation story remains a microbial mystery.",
    ),
    "arsenal": (
        "No matched biosynthetic arsenal appears in these records.",
        "The lab notes list no matched BGC arsenal here.",
        "No documented biosynthetic equipment was found for this bout.",
    ),
    "activity": (
        "No documented biological activity appears in these records.",
        "The activity notes are still hiding under the microscope.",
        "No supported activity description surfaced in the database.",
    ),
    "ability": (
        "Special ability not documented.",
        "Ability record still under study.",
        "Arsenal details remain unresolved.",
    ),
    "result": (
        "The biological explanation is still hiding under the microscope. That is why we need more research.",
        "The database has no clean answer for this detail. That is why we need more research.",
        "Some mysteries survive even after the battle. That is why we need more research.",
    ),
}

WINNER_MESSAGES = (
    "Microscopic menace confirmed.",
    "That colony came ready.",
    "Survival strategy: successful.",
    "The petri dish has a new champion.",
    "Tiny organism. Massive performance.",
    "The lab will be talking about this one.",
)

CLOSE_MESSAGES = (
    "That battle was one flagellum away.",
    "The petri dish barely survived the drama.",
    "A microscopic photo finish.",
    "Both colonies understood the assignment.",
)

DOMINANT_MESSAGES = (
    "That was less a battle and more a microbial announcement.",
    "Complete petri-dish control.",
    "The colony chose chaos.",
    "One organism entered. One organism ran the lab.",
)

TIE_MESSAGES = (
    "The microscope requests a rematch.",
    "Neither colony surrendered the petri dish.",
    "Perfectly balanced microbial mayhem.",
)

ENVIRONMENT_RESULT_FLAVOR = {
    "Neutral": "The calm medium still found room for chaos.",
    "Salty": "The brine arena sparkled through every exchange.",
    "Alkaline": "Mineral currents kept the arena lively.",
    "Hot": "The hot spring kept the pressure bubbling.",
    "Cold": "The cryogenic arena delivered a frosty finish.",
    "Acidic": "The acid pool supplied plenty of reactive drama.",
    "In the presence of antibiotics": "Warning pulses swept the hospital surface to the end.",
}


def is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    text = sanitize_designation(str(value)).strip()
    folded = text.casefold()
    return folded in MISSING_MARKERS or folded.startswith("no curated ") or folded.startswith("no matched ")


@dataclass
class FlavorDeck:
    """Stable per-key choices that avoid repeating copy within a session."""
    seed: str
    remembered: dict[str, str] = field(default_factory=dict)
    used: set[str] = field(default_factory=set)

    def pick(self, key: str, messages: Iterable[str]) -> str:
        if key in self.remembered:
            return self.remembered[key]
        choices = tuple(messages)
        if not choices:
            raise ValueError("Flavor message pool cannot be empty")
        available = tuple(message for message in choices if message not in self.used) or choices
        digest = hashlib.sha256(f"{self.seed}:{key}".encode()).digest()
        choice = available[int.from_bytes(digest[:4], "big") % len(available)]
        self.remembered[key] = choice
        self.used.add(choice)
        return choice


def friendly_value(value, context="general", *, deck: FlavorDeck | None = None, key="value") -> str:
    if not is_missing(value):
        return sanitize_designation(str(value))
    messages = MISSING_MESSAGES.get(context, MISSING_MESSAGES["general"])
    if deck:
        return deck.pick(f"missing:{context}:{key}", messages)
    digest = hashlib.sha256(f"{context}:{key}".encode()).digest()
    return messages[int.from_bytes(digest[:2], "big") % len(messages)]


def result_message(player_score: float, opponent_score: float, winner_flag: str, deck: FlavorDeck, key: str) -> tuple[str, str]:
    difference = abs(player_score - opponent_score)
    relative = difference / max(abs(player_score), abs(opponent_score), 1)
    if winner_flag == "tie":
        category, pool = "tie", TIE_MESSAGES
    elif difference <= 2.5 or relative <= .07:
        category, pool = "close", CLOSE_MESSAGES
    elif difference >= 10 or relative >= .25:
        category, pool = "dominant", DOMINANT_MESSAGES
    else:
        category, pool = "winner", WINNER_MESSAGES
    return category, deck.pick(f"result:{key}:{category}", pool)


def environment_result_flavor(environment: str | None) -> str:
    return ENVIRONMENT_RESULT_FLAVOR.get(environment or "Neutral", ENVIRONMENT_RESULT_FLAVOR["Neutral"])


def environment_status_label(status: str) -> str:
    return {
        "MATCHED": "supported adaptation match",
        "MISMATCHED": "documented traits, but no supported arena match",
        "UNKNOWN": "adaptation evidence still under study",
    }.get(status, "environment evidence still under study")
