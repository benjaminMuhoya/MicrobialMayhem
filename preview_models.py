"""Stable data models for colony and environment previews (no Pygame)."""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass

from colony_scoring import colony_growth_score
from presentation import environment_visual
from scoring import ENV_MATCH_BONUS, MATCHED, NO_EVIDENCE_PENALTY, environment_status


@dataclass(frozen=True)
class PreviewParticle:
    x: float
    y: float
    size: float
    phase: float
    speed: float
    kind: str


@dataclass(frozen=True)
class ColonyPreset:
    cfu: int
    title: str
    flavor: str


COLONY_PRESETS = (
    ColonyPreset(50, "Tiny Squad", "Tiny squad, big attitude."),
    ColonyPreset(250, "Balanced", "Balanced numbers. Balanced chaos."),
    ColonyPreset(500, "Lively Crowd", "A lively microbial crowd."),
    ColonyPreset(750, "Packed Colony", "The whole colony pulled up."),
    ColonyPreset(1000, "Maximum", "This petri dish is getting crowded."),
)


ENVIRONMENT_FLAVOR = {
    "Neutral": "Calm medium. Maximum focus.",
    "Salty": "A sparkling brine brawl.",
    "Alkaline": "Smooth currents and mineral drama.",
    "Hot": "Bubbles up. Temperature up.",
    "Cold": "Frosty arena, sharp reactions.",
    "Acidic": "Reactive droplets. Handle with flair.",
    "In the presence of antibiotics": "Warning lights: very much on.",
}


def animation_time(elapsed: float, reduced_motion: bool) -> float:
    return 0.0 if reduced_motion else elapsed


def _rng(seed: str) -> random.Random:
    digest = hashlib.sha256(seed.encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def colony_particles(cfu: int, seed: str) -> tuple[PreviewParticle, ...]:
    score, _ = colony_growth_score(cfu)
    count = 4 + round(score * 3.2)
    rng = _rng(f"colony:{seed}:{int(cfu)}")
    particles = []
    for index in range(count):
        angle = rng.random() * 6.283
        radius = (rng.random() ** .6) * .43
        particles.append(PreviewParticle(
            .5 + radius * math.cos(angle),
            .5 + radius * math.sin(angle),
            rng.uniform(.025, .052), rng.random() * 6.283,
            rng.uniform(.45, 1.25), "cell" if index % 4 else "dividing",
        ))
    return tuple(particles)


def environment_particles(environment: str, seed: str, count=18) -> tuple[PreviewParticle, ...]:
    visual = environment_visual(environment)
    rng = _rng(f"environment:{environment}:{seed}")
    return tuple(
        PreviewParticle(rng.random(), rng.random(), rng.uniform(.018, .05), rng.random() * 6.283, rng.uniform(.3, 1.1), visual.ambient)
        for _ in range(count)
    )


def environment_effect_text(player, opponent, environment: str) -> str:
    if environment == "Neutral":
        return "Actual modifier: neutral medium adds +0 environment points to both fighters."
    player_status = environment_status(player, environment)
    opponent_status = environment_status(opponent, environment)
    if player_status != MATCHED and opponent_status != MATCHED:
        return f"Actual modifier: neither fighter has a supported match; both receive {NO_EVIDENCE_PENALTY:+.0f} points."
    player_value = ENV_MATCH_BONUS if player_status == MATCHED else 0
    opponent_value = ENV_MATCH_BONUS if opponent_status == MATCHED else 0
    return f"Actual modifier: your fighter {player_value:+.0f}; rival {opponent_value:+.0f} environment points from supported matches."


def environment_flavor(environment: str) -> str:
    return ENVIRONMENT_FLAVOR[environment]


def quadratic_path(start: tuple[float, float], end: tuple[float, float], arc: float, steps=18) -> tuple[tuple[float, float], ...]:
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2 + arc
    points = []
    for index in range(steps + 1):
        t = index / steps
        inv = 1 - t
        points.append((
            inv * inv * start[0] + 2 * inv * t * mid_x + t * t * end[0],
            inv * inv * start[1] + 2 * inv * t * mid_y + t * t * end[1],
        ))
    return tuple(points)
