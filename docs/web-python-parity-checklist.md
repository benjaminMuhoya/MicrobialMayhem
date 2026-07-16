# Web ↔ Python gameplay parity checklist

Confirmed source-of-truth references: `microbial_mayhem_main.py`, `bacterial_catalog.py`, `colony_scoring.py`, `scoring.py`, `flavor_text.py`, `preview_models.py`, `presentation.py`, and `ui_systems.py`.

## Navigation and setup

- [x] Eight principal states exist in the web shell.
- [ ] Start must reset mode-specific state and sample a fresh catalog roster.
- [ ] Search must match full name, display name, genus, strain, and supported identifiers.
- [ ] Reshuffle must replace the visible sample without losing locked fighters.
- [ ] Solo confirmation must choose a different catalog opponent, seeded opponent CFU, and independent arsenal decision.
- [ ] Local versus must lock Player 1, reject that catalog ID for Player 2, then repeat colony and arsenal setup for each player before one shared environment.
- [ ] Back, rematch, change-fighters, and main-menu behavior must match the Python state transitions.

## Biology and presentation

- [ ] Fighter details must expose morphology, habitat, colony appearance, BGC accessions, products, activities, trait evidence, description/fact, and provenance.
- [ ] Recorded evidence and procedural appearance must be explicitly separated.
- [ ] Every environment card and arena must use the Python environment-specific motif.
- [ ] Preview labels must be mode-aware and show actual chosen fighter/setup data.
- [ ] Results must show Python-equivalent headline, score cards, component explanations, environmental interpretation, biological note, and missing-evidence research wording.

## Battle behavior

- [x] Scoring is precomputed before the arena and matches six fixed Python fixtures.
- [ ] The deterministic eight-second cue sequence must restore entrance, anticipation, attack, defense, counter, dodge, abilities, arena pressure, pause, finish, and resolution.
- [ ] Health must remain competitive until the final 18 percent of the timeline.
- [ ] Natural completion and Skip must enter the same stored result exactly once.
- [ ] Unmount/rematch must destroy timers, tweens, sounds, and listeners.

## Verification gate

- [ ] One-player home → results → rematch/change fighters/main menu passes in a browser.
- [ ] Two-player home → both setups → results → rematch/change fighters/main menu passes in a browser.
- [ ] Python tests, TypeScript unit/parity tests, browser tests, and production build all pass.
