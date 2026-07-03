"""Pure presentation models shared by the Pygame renderer and future clients.

This module deliberately has no Pygame dependency.  It turns catalog data into
stable art direction (shape, palette, traits, and arena atmosphere) without
changing any scientific record or battle calculation.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from bacterial_catalog import BacteriumCatalogEntry
from bacterial_names import sanitize_designation
from flavor_text import friendly_value


Color = tuple[int, int, int]


@dataclass(frozen=True)
class Theme:
    ink: Color = (8, 18, 32)
    panel: Color = (13, 31, 49)
    panel_light: Color = (22, 48, 68)
    text: Color = (240, 248, 250)
    muted: Color = (158, 181, 192)
    mint: Color = (111, 239, 190)
    cyan: Color = (72, 207, 217)
    yellow: Color = (255, 221, 107)
    coral: Color = (255, 104, 133)
    violet: Color = (155, 117, 255)


THEME = Theme()


@dataclass(frozen=True)
class FighterVisual:
    morphology: str
    primary: Color
    secondary: Color
    accent: Color
    has_flagella: bool
    has_capsule: bool
    has_pili: bool
    has_spores: bool
    epithet: str
    ability: str
    habitat: str


@dataclass(frozen=True)
class EnvironmentVisual:
    key: str
    title: str
    subtitle: str
    top: Color
    bottom: Color
    particle: Color
    ambient: str


PALETTES: tuple[tuple[Color, Color, Color], ...] = (
    ((74, 226, 173), (24, 137, 145), (255, 222, 103)),
    ((255, 113, 151), (146, 68, 177), (109, 234, 226)),
    ((112, 173, 255), (52, 82, 172), (255, 174, 91)),
    ((238, 189, 88), (199, 83, 80), (120, 241, 187)),
    ((179, 124, 255), (75, 75, 170), (255, 225, 117)),
)


ENVIRONMENT_VISUALS = {
    "Neutral": EnvironmentVisual("Neutral", "Petri Dish", "Balanced growth medium", (20, 57, 77), (8, 28, 45), (114, 232, 201), "nutrients"),
    "Salty": EnvironmentVisual("Salty", "Brine Pool", "Salt crystals drift through dense water", (23, 92, 129), (7, 37, 70), (168, 236, 255), "bubbles"),
    "Alkaline": EnvironmentVisual("Alkaline", "Soda Lake", "A bright, mineral-rich alkaline arena", (55, 117, 118), (13, 49, 66), (196, 255, 188), "rings"),
    "Hot": EnvironmentVisual("Hot", "Hot Spring", "Heat shimmer and rising mineral bubbles", (130, 57, 53), (48, 20, 38), (255, 178, 89), "steam"),
    "Cold": EnvironmentVisual("Cold", "Cryo Chamber", "Ice motes move through frigid fluid", (53, 101, 149), (13, 35, 71), (211, 244, 255), "snow"),
    "Acidic": EnvironmentVisual("Acidic", "Acid Pool", "Reactive droplets pulse in low pH", (104, 112, 38), (39, 44, 24), (222, 255, 91), "bubbles"),
    "In the presence of antibiotics": EnvironmentVisual("In the presence of antibiotics", "Hospital Surface", "Antibiotic pulses sweep the sterile field", (78, 75, 116), (23, 25, 48), (255, 128, 177), "crosses"),
}


def _stable_bytes(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8", "replace")).digest()


def morphology_for(entry: BacteriumCatalogEntry) -> str:
    """Use recorded morphology when present, otherwise stable procedural art."""
    shape = sanitize_designation(entry.cell_shape).casefold()
    if any(word in shape for word in ("coccus", "cocci", "sphere", "spherical")):
        return "coccus"
    if any(word in shape for word in ("rod", "bacill")):
        return "bacillus"
    if any(word in shape for word in ("spir", "helical", "curved")):
        return "spiral"
    if any(word in shape for word in ("filament", "hypha", "mycel")):
        return "filamentous"
    if shape not in {"", "unknown", "not specified", "no"}:
        return "irregular"
    # Missing morphology never becomes catalog data; it only selects a stable
    # placeholder silhouette so a roster of unknowns still looks distinct.
    return ("coccus", "bacillus", "spiral", "filamentous", "irregular")[_stable_bytes(entry.catalog_id)[0] % 5]


def ability_for(entry: BacteriumCatalogEntry) -> str:
    if entry.products:
        return sanitize_designation(entry.products[0])
    if entry.activities:
        return sanitize_designation(entry.activities[0]).title()
    if entry.accessions:
        return f"BGC Arsenal ×{len(entry.accessions)}"
    return friendly_value(None, "ability", key=f"{entry.catalog_id}:ability")


def summary_ability(entry: BacteriumCatalogEntry) -> str:
    """Concise versus-card copy without exposing raw missing-data messages."""
    if entry.products:
        return sanitize_designation(entry.products[0])
    if entry.activities:
        return sanitize_designation(entry.activities[0]).title()
    if entry.accessions:
        return "Still under investigation"
    return "Not yet documented"


def summary_arsenal_status(entry: BacteriumCatalogEntry, active: bool | None) -> str:
    if not entry.accessions:
        return "NONE DOCUMENTED"
    return "ACTIVATED" if active else "DORMANT"


def epithet_for(entry: BacteriumCatalogEntry) -> str:
    traits = {e.trait for e in entry.traits}
    for trait, title in (
        ("Thermophile", "The Heat Seeker"),
        ("Cryophile", "The Cold Specialist"),
        ("Halophile", "The Salt Survivor"),
        ("Acidophile", "The Acid Ace"),
        ("Drug resistant", "The Unyielding"),
        ("Antimicrobial production", "The Chemical Crafter"),
    ):
        if trait in traits:
            return title
    return ("The Quiet Competitor", "The Colony Builder", "The Wild Type", "The Tiny Tactician")[_stable_bytes(entry.catalog_id)[1] % 4]


def fighter_visual(entry: BacteriumCatalogEntry) -> FighterVisual:
    seed = _stable_bytes(entry.catalog_id)
    primary, secondary, accent = PALETTES[seed[2] % len(PALETTES)]
    motility = sanitize_designation(entry.motility).casefold()
    motility_unknown = motility in {"", "unknown", "not specified", "no data"}
    reported_motile = "motile" in motility and not any(term in motility for term in ("non-motile", "nonmotile", "not motile"))
    return FighterVisual(
        morphology=morphology_for(entry),
        primary=primary,
        secondary=secondary,
        accent=accent,
        has_flagella=reported_motile or (motility_unknown and seed[3] % 3 == 0),
        has_capsule="capsul" in entry.colony_appearance.casefold() or seed[4] % 4 == 0,
        has_pili=seed[5] % 3 == 0,
        has_spores="spore" in entry.colony_appearance.casefold() or entry.genus.casefold() in {"bacillus", "clostridium"},
        epithet=epithet_for(entry),
        ability=ability_for(entry),
        habitat=friendly_value(entry.isolation_habitat, "habitat", key=entry.catalog_id),
    )


def environment_visual(environment: str | None) -> EnvironmentVisual:
    return ENVIRONMENT_VISUALS.get(environment or "Neutral", ENVIRONMENT_VISUALS["Neutral"])
