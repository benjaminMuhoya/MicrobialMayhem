# Web ↔ Python gameplay parity checklist

Confirmed source-of-truth references: `microbial_mayhem_main.py`, `bacterial_catalog.py`, `colony_scoring.py`, `scoring.py`, `flavor_text.py`, `preview_models.py`, `presentation.py`, and `ui_systems.py`.

## Navigation and setup

- [x] Eight principal states exist in the web shell.
- [x] Start resets mode-specific state and samples a fresh catalog roster.
- [x] Search matches full name, display name, genus, strain, and supported identifiers.
- [x] Reshuffle replaces the visible sample without losing locked fighters.
- [x] Solo confirmation chooses a different catalog opponent, seeded opponent CFU, and independent arsenal decision.
- [x] Local versus locks Player 1, rejects that catalog ID for Player 2, then repeats colony and arsenal setup for each player before one shared environment.
- [x] Rematch, change-fighters, and main-menu behavior use isolated state transitions.

## Biology and presentation

- [x] Fighter details expose morphology, habitat, colony appearance, BGC accessions, products, activities, trait evidence, description/fact, and provenance.
- [x] Recorded evidence and procedural appearance are explicitly separated.
- [x] Every environment card and arena uses a Python-derived environment-specific motif.
- [x] Preview labels are mode-aware and show actual chosen fighter/setup data.
- [x] Results show Python-equivalent headline, score cards, component explanations, environmental interpretation, biological note, and missing-evidence research wording.

## Battle behavior

- [x] Scoring is precomputed before the arena and matches six fixed Python fixtures.
- [x] The deterministic eight-second cue sequence restores entrance, anticipation, attack, defense, counter, dodge, abilities, arena pressure, pause, finish, and resolution.
- [x] Health remains competitive until the final 18 percent of the timeline.
- [x] Natural completion and Skip enter the same stored result exactly once.
- [x] Unmount/rematch destroys Phaser timers, tweens, and listeners.

## Verification gate

- [x] One-player home → results → rematch/change fighters/main menu passes in a browser.
- [x] Two-player home → both setups → results → rematch/change fighters/main menu passes in a browser.
- [x] Python tests, TypeScript unit/parity tests, and production build pass; Playwright cases are present and discovered.
