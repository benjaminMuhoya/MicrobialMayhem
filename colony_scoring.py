"""Dynamic colony-size scoring shared by player and opponent."""
from __future__ import annotations

import math
import random

MIN_CFU = 0
MAX_CFU = 1000
MIN_COLONY_SCORE = 0.0
MAX_COLONY_SCORE = 10.0


def colony_score_from_cfu(cfu: int | float) -> float:
    """Return a smooth 0..10 score with diminishing returns.

    Formula: score = 10 * log1p(clamped_cfu) / log1p(1000).
    This gives every increase in CFU some value while high-CFU colonies gain
    more slowly, so colony size remains useful without dominating battle scores.
    """
    clamped = max(MIN_CFU, min(MAX_CFU, float(cfu)))
    return round(MAX_COLONY_SCORE * math.log1p(clamped) / math.log1p(MAX_CFU), 1)


def colony_label(cfu: int | float) -> str:
    cfu = max(MIN_CFU, min(MAX_CFU, int(cfu)))
    if cfu < 25:
        return "Very small colony"
    if cfu < 100:
        return "Small colony"
    if cfu < 300:
        return "Moderate colony"
    if cfu < 600:
        return "Large colony"
    if cfu < 850:
        return "Very large colony"
    return "Massive colony"


def colony_growth_score(cfu: int | float) -> tuple[float, str]:
    return colony_score_from_cfu(cfu), colony_label(cfu)


def generate_opponent_cfu(seed: int | None = None) -> int:
    return random.Random(seed).randint(MIN_CFU, MAX_CFU)
