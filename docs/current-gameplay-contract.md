# Current gameplay contract

## Active runtime

The playable application starts at `microbial_mayhem_main.py:main()`. Its active runtime collaborators are `bacterial_catalog.py`, `catalog_storage.py`, `scoring.py`, `colony_scoring.py`, `presentation.py`, `preview_models.py`, `ui_systems.py`, `audio_manager.py`, `app_settings.py`, `flavor_text.py`, `bacterial_names.py`, `gui_helpers.py`, and `environment_icons.py`.

Legacy terminal/prototype modules at repository root are not part of the active screen dispatch. They remain untouched during the web parity phase.

## Navigation states

`WELCOME → FIGHTER_SELECTION → COLONY_SELECTION → SECRETION_SELECTION → ENVIRONMENT_SELECTION → BATTLE_PREVIEW → BATTLE_ANIMATION → RESULTS`

`SETTINGS` is entered from `WELCOME` and returns there. In local two-player mode, fighter selection and colony/arsenal setup repeat for Player 2. Player 2 cannot select Player 1’s `catalog_id`.

## Battle invariants

- `calculate_battle()` calls `score_battle()` before `BATTLE_PREVIEW`/`BATTLE_ANIMATION` completes.
- `BattleTimeline` and `battle_health()` are presentation only.
- Skipping animation cannot alter winner or totals.
- Both fighters start with +25.
- Colony CFU contributes the shared diminishing-returns score, capped at +10.
- Neutral environment contributes 0.
- Supported environment match contributes +12.
- If neither fighter matches a non-neutral environment, both receive −3.
- Resistance defense is capped at +5.
- Active BGC arsenal adds one per accession, capped at +5.
- Known biological activity is capped at +5.
- Offense total includes arsenal plus activity exactly once.
- Seeded variation is in [−2, +2] and totals are rounded to two decimals.
- Higher total wins; identical totals tie.

## Web-port parity boundary

The TypeScript rules must reproduce every fixture in `tests/fixtures/battle_parity.json`. Presentation may change radically, but fixture inputs, component values, totals, environment status, and winner must remain identical.

