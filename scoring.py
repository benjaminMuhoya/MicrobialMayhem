"""Transparent environment/trait scoring for Microbial Mayhem."""
from __future__ import annotations

import random
from dataclasses import dataclass

from bacterial_catalog import BacteriumCatalogEntry
from colony_scoring import colony_score_from_cfu
from trait_inference import ADAPTATION_TRAITS

MATCHED = "MATCHED"
MISMATCHED = "MISMATCHED"
UNKNOWN = "UNKNOWN"
BASE_SCORE = 25.0
ENV_MATCH_BONUS = 12.0
NO_EVIDENCE_PENALTY = -3.0
BGC_ARSENAL_BONUS = 5.0
ACTIVITY_SCORE_CAP = 5.0
RANDOM_VARIATION_RANGE = 2.0


@dataclass(frozen=True)
class ScoreComponent:
    name: str
    value: float
    explanation: str
    included_in_total: bool = True


@dataclass(frozen=True)
class ScoreBreakdown:
    fighter_name: str
    environment_status: str
    colony_cfu: int
    total: float
    components: tuple[ScoreComponent, ...]

    def component_total(self) -> float:
        return round(sum(c.value for c in self.components if c.included_in_total), 6)


def colony_component(colony_cfu: int) -> ScoreComponent:
    colony_score = colony_score_from_cfu(colony_cfu)
    return ScoreComponent("Colony", float(colony_score), f"{colony_cfu} CFU contributed {colony_score:+.1f} points using the shared dynamic colony formula.")


def bgc_arsenal_score(entry: BacteriumCatalogEntry, brings_bgc_arsenal: bool) -> tuple[float, int]:
    if not brings_bgc_arsenal:
        return 0.0, 0
    active_bgc_count = len(entry.accessions)
    return float(min(active_bgc_count, int(BGC_ARSENAL_BONUS))), active_bgc_count


def activity_score(entry: BacteriumCatalogEntry) -> float:
    """Score documented biological activities with one capped, simple model."""
    activities = " ".join(entry.activities).lower()
    score = 0.0
    matched = False
    if "antibacterial" in activities or "antimicrobial" in activities:
        score += 3.0
        matched = True
    if "antifungal" in activities:
        score += 2.0
        matched = True
    if "cytotoxic" in activities or "toxic" in activities or "toxin" in activities:
        score += 2.0
        matched = True
    if "siderophore" in activities or "iron" in activities:
        score += 2.0
        matched = True
    if entry.activities and not matched:
        score += 1.0
    return min(ACTIVITY_SCORE_CAP, score)


def defensive_score(entry: BacteriumCatalogEntry) -> float:
    """Score resistance evidence only; antimicrobial production is offense."""
    best = 0.0
    for evidence in entry.traits:
        if evidence.trait != "Drug resistant":
            continue
        text = f"{evidence.field} {evidence.explanation}".lower()
        if evidence.evidence_level.startswith("Direct") and ("immunity" in text or "efflux" in text or "resistan" in text):
            best = max(best, 5.0)
        elif "self-resistance" in text:
            best = max(best, 4.0)
        else:
            best = max(best, 2.0)
    return best


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
    colony_cfu: int,
    brings_bgc_arsenal: bool,
    neither_has_match: bool,
    rng: random.Random,
) -> ScoreBreakdown:
    status = environment_status(entry, environment)
    target = ADAPTATION_TRAITS.get(environment, "environmental adaptation")
    components: list[ScoreComponent] = [ScoreComponent("Base", BASE_SCORE, "Every fighter starts from the same neutral base score.")]
    components.append(colony_component(colony_cfu))
    if environment == "Neutral":
        components.append(ScoreComponent("Environment", 0.0, "The neutral environment does not change either fighter's score."))
    elif status == MATCHED:
        components.append(ScoreComponent("Environment", ENV_MATCH_BONUS, f"Supported {target.lower()} evidence matches the {environment} environment."))
    elif neither_has_match:
        components.append(ScoreComponent("Environment", NO_EVIDENCE_PENALTY, f"No supported {target.lower()} match was found; uncertainty applies a modest shared penalty."))
    elif status == MISMATCHED:
        components.append(ScoreComponent("Environment", 0.0, f"Traits are documented, but none match the {environment} environment; no bonus was awarded."))
    else:
        components.append(ScoreComponent("Environment", 0.0, f"No supported {target.lower()} evidence was available; unknown is not treated as a confirmed mismatch."))
    defense = defensive_score(entry)
    components.append(ScoreComponent("Resistance defense", defense, "Resistance, immunity, or efflux evidence contributes defense; antimicrobial production alone does not."))
    arsenal_score, active_bgc_count = bgc_arsenal_score(entry, brings_bgc_arsenal)
    known_activity_score = activity_score(entry)
    components.append(ScoreComponent("BGC arsenal", arsenal_score, f"{active_bgc_count} known MIBiG BGC(s) brought into battle; score is capped at 5.", False))
    components.append(ScoreComponent("Known activity", known_activity_score, "Capped score from documented antibacterial, antifungal, cytotoxic/toxin, siderophore, or other activity.", False))
    components.append(ScoreComponent("Offense total", arsenal_score + known_activity_score, f"Offense subtotal = BGC arsenal {arsenal_score:+.1f} + known activity {known_activity_score:+.1f}."))
    variation = round(rng.uniform(-RANDOM_VARIATION_RANGE, RANDOM_VARIATION_RANGE), 2)
    components.append(ScoreComponent("Battle variation", variation, "Small controlled random variation for close battles."))
    total = round(sum(c.value for c in components if c.included_in_total), 2)
    return ScoreBreakdown(entry.full_name, status, int(colony_cfu), total, tuple(components))


def score_battle(
    player: BacteriumCatalogEntry,
    opponent: BacteriumCatalogEntry,
    environment: str,
    player_colony_cfu: int,
    opponent_colony_cfu: int,
    player_brings_bgc_arsenal: bool,
    opponent_brings_bgc_arsenal: bool,
    seed: int | None = None,
) -> tuple[ScoreBreakdown, ScoreBreakdown]:
    rng = random.Random(seed)
    neither_has_match = environment_status(player, environment) != MATCHED and environment_status(opponent, environment) != MATCHED
    return (
        score_fighter(player, environment, player_colony_cfu, player_brings_bgc_arsenal, neither_has_match, rng),
        score_fighter(opponent, environment, opponent_colony_cfu, opponent_brings_bgc_arsenal, neither_has_match, rng),
    )
