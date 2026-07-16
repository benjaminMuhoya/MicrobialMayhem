#!/usr/bin/env python3
"""Export deterministic scoring fixtures for the TypeScript parity suite."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bacterial_catalog import BacteriumCatalogEntry
from scoring import score_battle
from trait_inference import DIRECT, INDIRECT, TraitEvidence

OUTPUT = ROOT / "tests" / "fixtures" / "battle_parity.json"


def trait(name: str, level: str = DIRECT, field: str = "genes") -> TraitEvidence:
    return TraitEvidence(name, level, "BGC-FIXTURE", field, f"Fixture evidence for {name}.")


FIGHTERS = {
    "thermalis": BacteriumCatalogEntry(
        "fixture:thermalis", "Thermus thermalis MM-1", "T. thermalis MM-1", "Thermus", "thermalis", "MM-1",
        accessions=["BGC-HOT-1", "BGC-HOT-2"], products=["thermocin"], activities=["antibacterial"],
        traits=[trait("Thermophile"), trait("Antimicrobial production", INDIRECT, "chem_acts")],
        description="A heat-adapted fixture fighter.", isolation_habitat="Hot spring", cell_shape="rod", motility="motile",
    ),
    "cryonix": BacteriumCatalogEntry(
        "fixture:cryonix", "Psychrobacter cryonix ICE-2", "P. cryonix ICE-2", "Psychrobacter", "cryonix", "ICE-2",
        accessions=["BGC-COLD-1"], products=["cryoprotectin"], activities=["siderophore"],
        traits=[trait("Cryophile")], description="A cold-adapted fixture fighter.", isolation_habitat="Sea ice",
        cell_shape="coccus", motility="non-motile",
    ),
    "halica": BacteriumCatalogEntry(
        "fixture:halica", "Halomonas halica BRINE-7", "H. halica BRINE-7", "Halomonas", "halica", "BRINE-7",
        accessions=["BGC-SALT-1", "BGC-SALT-2", "BGC-SALT-3"], activities=["antifungal"],
        traits=[trait("Halophile")], description="A salt-adapted fixture fighter.", isolation_habitat="Solar saltern",
        cell_shape="curved rod", motility="motile",
    ),
    "resista": BacteriumCatalogEntry(
        "fixture:resista", "Pseudomonas resista ABX-9", "P. resista ABX-9", "Pseudomonas", "resista", "ABX-9",
        accessions=["BGC-ABX-1"], activities=["antimicrobial"],
        traits=[trait("Drug resistant", DIRECT, "genes")], description="A resistance fixture fighter.",
        isolation_habitat="Clinical surface", cell_shape="rod", motility="motile",
    ),
    "plain": BacteriumCatalogEntry(
        "fixture:plain", "Bacterium ordinaria N-0", "B. ordinaria N-0", "Bacterium", "ordinaria", "N-0",
        description="A fighter with no documented combat traits.", isolation_habitat="Soil", cell_shape="unknown", motility="unknown",
    ),
    "twin": BacteriumCatalogEntry(
        "fixture:twin", "Bacillus aequalis TIE", "B. aequalis TIE", "Bacillus", "aequalis", "TIE",
        description="A symmetric tie fixture.", isolation_habitat="Defined medium", cell_shape="rod", motility="non-motile",
    ),
}

CASES = [
    ("solo_hot_advantage_arsenal_on", "1_player", "thermalis", "cryonix", "Hot", 750, 250, True, False, 17),
    ("solo_cold_loss_arsenal_off", "1_player", "thermalis", "cryonix", "Cold", 100, 1000, False, True, 23),
    ("local_salty_colony_tradeoff", "2_players", "halica", "resista", "Salty", 250, 750, True, True, 41),
    ("local_antibiotic_resistance", "2_players", "plain", "resista", "In the presence of antibiotics", 1000, 50, False, True, 73),
    ("neutral_arsenal_comparison", "1_player", "halica", "plain", "Neutral", 500, 500, True, False, 101),
    ("deterministic_tie", "2_players", "twin", "twin", "Neutral", 500, 500, False, False, 449),
]


def fighter_payload(entry: BacteriumCatalogEntry) -> dict:
    return {
        "catalogId": entry.catalog_id, "fullName": entry.full_name,
        "accessions": entry.accessions, "products": entry.products, "activities": entry.activities,
        "traits": [{"trait": t.trait, "evidenceLevel": t.evidence_level, "field": t.field, "explanation": t.explanation} for t in entry.traits],
    }


def breakdown_payload(value) -> dict:
    return {
        "fighterName": value.fighter_name, "environmentStatus": value.environment_status,
        "colonyCfu": value.colony_cfu, "total": value.total,
        "components": [{"name": c.name, "value": c.value, "includedInTotal": c.included_in_total} for c in value.components],
    }


def main() -> None:
    fixtures = []
    for name, mode, left_key, right_key, environment, left_cfu, right_cfu, left_arsenal, right_arsenal, seed in CASES:
        left, right = FIGHTERS[left_key], FIGHTERS[right_key]
        a, b = score_battle(left, right, environment, left_cfu, right_cfu, left_arsenal, right_arsenal, seed)
        winner = "A" if a.total > b.total else "B" if b.total > a.total else "tie"
        fixtures.append({
            "name": name, "mode": mode, "seed": seed, "environment": environment,
            "player": fighter_payload(left), "opponent": fighter_payload(right),
            "playerColonyCfu": left_cfu, "opponentColonyCfu": right_cfu,
            "playerArsenal": left_arsenal, "opponentArsenal": right_arsenal,
            "expected": {"player": breakdown_payload(a), "opponent": breakdown_payload(b), "winner": winner},
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"schemaVersion": 1, "fixtures": fixtures}, indent=2) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(fixtures)} fixtures)")


if __name__ == "__main__":
    main()
