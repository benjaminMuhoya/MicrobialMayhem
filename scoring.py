"""Transparent environment/trait scoring for Microbial Mayhem."""
from __future__ import annotations

import random
from dataclasses import dataclass

from bacterial_catalog import BacteriumCatalogEntry
from trait_inference import ADAPTATION_TRAITS

MATCHED = "MATCHED"
MISMATCHED = "MISMATCHED"
UNKNOWN = "UNKNOWN"
BASE_SCORE = 25.0
ENV_MATCH_BONUS = 12.0
NO_EVIDENCE_PENALTY = -3.0
SECRETION_YES = 5.0
SECRETION_NO = -5.0
RANDOM_VARIATION_RANGE = 2.0


@dataclass(frozen=True)
class ScoreComponent:
    name: str
    value: float
    explanation: str


@dataclass(frozen=True)
class ScoreBreakdown:
    fighter_name: str
    environment_status: str
    total: float
    components: tuple[ScoreComponent, ...]

    def component_total(self) -> float:
        return round(sum(c.value for c in self.components), 6)


def colony_component(colony_score: int) -> ScoreComponent:
    return ScoreComponent("Colony", float(colony_score), f"Existing colony-size rule contributed {colony_score:+.1f} points.")


def offensive_score(entry: BacteriumCatalogEntry) -> float:
    # Cap the contribution so database-rich organisms do not win merely because
    # they have many linked MIBiG records.
    antimicrobial = 1.5 if entry.has_trait("Antimicrobial production") else 0.0
    product_points = min(4.0, len(entry.products) * 0.5)
    activity_points = min(3.0, len(entry.activities) * 0.5)
    return round(min(8.0, antimicrobial + product_points + activity_points), 2)


def defensive_score(entry: BacteriumCatalogEntry) -> float:
    # Resistance is separate from antimicrobial production.
    return 5.0 if entry.has_trait("Drug resistant") else 0.0


def environment_status(entry: BacteriumCatalogEntry, environment: str) -> str:
    target = ADAPTATION_TRAITS.get(environment)
    if not target:
        return UNKNOWN
    if entry.has_trait(target):
        return MATCHED
    adaptation_traits = set(ADAPTATION_TRAITS.values())
    if any(e.trait in adaptation_traits for e in entry.traits):
        return MISMATCHED
    return UNKNOWN


def score_fighter(
    entry: BacteriumCatalogEntry,
    environment: str,
    colony_score: int,
    has_secretion: bool,
    neither_has_match: bool,
    rng: random.Random,
) -> ScoreBreakdown:
    status = environment_status(entry, environment)
    target = ADAPTATION_TRAITS.get(environment, "environmental adaptation")
    components: list[ScoreComponent] = [ScoreComponent("Base", BASE_SCORE, "Every fighter starts from the same neutral base score.")]
    components.append(colony_component(colony_score))
    if status == MATCHED:
        components.append(ScoreComponent("Environment", ENV_MATCH_BONUS, f"Supported {target.lower()} evidence matches the {environment} environment."))
    elif neither_has_match:
        components.append(ScoreComponent("Environment", NO_EVIDENCE_PENALTY, f"No supported {target.lower()} match was found; uncertainty applies a modest shared penalty."))
    elif status == MISMATCHED:
        components.append(ScoreComponent("Environment", 0.0, f"Traits are documented, but none match the {environment} environment; no bonus was awarded."))
    else:
        components.append(ScoreComponent("Environment", 0.0, f"No supported {target.lower()} evidence was available; unknown is not treated as a confirmed mismatch."))
    components.append(ScoreComponent("Defense", defensive_score(entry), "Resistance-related evidence contributes defensive capability only when present."))
    components.append(ScoreComponent("Offense", offensive_score(entry), "Capped biosynthetic/product/activity evidence contributes offensive potential."))
    components.append(ScoreComponent("Secretion", SECRETION_YES if has_secretion else SECRETION_NO, "Secretion-system choice keeps the original +/-5 behavior."))
    variation = round(rng.uniform(-RANDOM_VARIATION_RANGE, RANDOM_VARIATION_RANGE), 2)
    components.append(ScoreComponent("Battle variation", variation, "Small controlled random variation for close battles."))
    total = round(sum(c.value for c in components), 2)
    return ScoreBreakdown(entry.full_name, status, total, tuple(components))


def score_battle(
    player: BacteriumCatalogEntry,
    opponent: BacteriumCatalogEntry,
    environment: str,
    player_colony_score: int,
    opponent_colony_score: int,
    player_has_secretion: bool,
    opponent_has_secretion: bool,
    seed: int | None = None,
) -> tuple[ScoreBreakdown, ScoreBreakdown]:
    rng = random.Random(seed)
    neither_has_match = environment_status(player, environment) != MATCHED and environment_status(opponent, environment) != MATCHED
    return (
        score_fighter(player, environment, player_colony_score, player_has_secretion, neither_has_match, rng),
        score_fighter(opponent, environment, opponent_colony_score, opponent_has_secretion, neither_has_match, rng),
    )
