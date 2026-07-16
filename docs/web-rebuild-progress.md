# Microbial Mayhem web rebuild progress

## Current phase

Phase 2 — Radical visual direction and interactive prototype (complete; preparing Phase 3).

## Completed work

- Reviewed the active Pygame runtime and separated it from legacy prototypes.
- Preserved the repository-wide technical/design report produced before implementation.
- Confirmed that battle scores are calculated before animation and that presentation health does not affect results.
- Recorded the existing nine-screen navigation model and one-player/two-player setup differences.
- Initialized an isolated `web/` client so the Python implementation remains authoritative.
- Added deterministic cross-language battle fixtures covering solo/local modes, colony variation, arsenal states, environment matches, wins, losses, and a tie.
- Defined the living-microscopic-arena design system.
- Built an interactive responsive prototype for home, fighter selection, colony selection, battle preview, arena, and results.
- Added progressive scientific disclosure on results and a visibly reactive CFU density control.

## Tests run

- Baseline: `/Users/bm0211/miniconda3/bin/python -m pytest -q`
- Result: 71 passed, 1 third-party Pygame `pkg_resources` deprecation warning.
- Baseline date: July 15, 2026.
- Web production build: passed.
- Web prototype tests: 2 passed.
- Browser checks: desktop home and colony layouts passed; 390 × 844 portrait home layout passed; navigation and colony interaction passed.

## Failures

- None in the Python baseline.

## Design decisions

- The Python rules remain the source of truth until TypeScript fixture parity passes.
- The web client lives under `web/`; no Pygame files are replaced.
- Scoring remains pure and precomputed. The arena will receive a completed result and dramatize it only.
- Text-heavy setup screens will use accessible HTML/CSS; Phaser will own the microscopic arena and procedural fighter motion.
- The first visual direction is “living microscopic arena”: dark fluid depth, translucent membranes, warm scientific typography, restrained bioluminescent accents, and spacious layouts.
- Visual tokens, motion, morphology/environment language, and accessibility rules are recorded in `docs/web-visual-design-system.md`.

## Files changed

- `docs/game-architecture-and-distribution-report.md`
- `docs/Microbial-Mayhem-Technical-and-Design-Report.docx`
- `docs/web-rebuild-progress.md`
- `docs/current-gameplay-contract.md`
- `tests/fixtures/battle_parity.json`
- `scripts/export_battle_fixtures.py`
- `web/` starter project
- `docs/web-visual-design-system.md`
- `web/app/page.tsx`
- `web/app/globals.css`
- `web/app/layout.tsx`
- `web/tests/rendered-html.test.mjs`

## Remaining work

1. Port rules and session models to TypeScript with fixture parity.
2. Replace prototype-only state and copy with authoritative game flow.
3. Add responsive full gameplay flow and Phaser arena.
4. Build compact catalog v2 with retained morphology/motility and web shards.
5. Add PWA/offline storage, browser E2E, responsive, visual, performance, and data tests.
6. Deploy the stable web release, then add the Capacitor Android wrapper.

## Known risks

- The current runtime catalog is 32.4 MiB and reconstructs 47,742 fighters in memory.
- SQLite schema v1 drops cell shape and motility computed by the BacDive builder.
- Python’s seeded random sequence must be reproduced exactly or captured explicitly for cross-language score parity.
- Mobile Safari audio unlock/storage eviction and Android lifecycle behaviour require device validation.
- Source-data and asset licensing must be confirmed before public release.
