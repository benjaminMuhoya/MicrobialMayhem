# Welcome to Microbial Mayhem!

Where battling bacteria teach you some biology.

This is the beta version! Thank you for being our tester :)

## Install

Python 3.11 or newer is recommended. Install the desktop and test dependencies
into the same environment:

```
python3 -m pip install -r requirements.txt
```

## Clone repository
```
git clone git@github.com:htoth99/MicrobialMayhem.git
cd MicrobialMayhem
```

## Alternative with HTTPS

```bash
git clone https://github.com/htoth99/MicrobialMayhem.git
cd MicrobialMayhem
```

## To play the game, simply type:

```
python3 microbial_mayhem_main.py
```

If more than one Python installation is present, activate the environment where
Pygame was installed first. On the original development machine that is:

```bash
/Users/bm0211/miniconda3/bin/python microbial_mayhem_main.py
```

The redesigned Pygame interface includes procedural organism art, fighter
cards, an environment-aware versus screen, and an animated battle arena. The
scientific catalog and scoring calculations remain in their existing modules.

The opening screen supports two local modes:

- **1 Player** keeps the original flow and automatically selects a different
  database rival after Player 1 locks in a fighter.
- **2 Players** lets Player 1 and Player 2 choose distinct fighters on the same
  device, then independently lock colony size and biosynthetic-arsenal status.
  One shared environment is selected after both setups are complete.

The normal battle choreography lasts eight seconds and can be skipped at any
time. Mouse, keyboard, basic controller, and scaled
touch-style pointer input share the same activation system.

## Controls and settings

- Mouse or touch: press and release over the same control.
- Keyboard: arrow keys or Tab move focus; Enter/Space activates; Escape goes back.
- Controller: directional input moves focus; primary button confirms; secondary
  button goes back.
- Settings: reduced motion, high contrast, text scale, mute, music volume, and
  effects volume are saved under `~/.microbial_mayhem/settings.json`.

For input diagnostics, launch with the temporary developer overlay enabled:

```bash
MICROBIAL_MAYHEM_INPUT_DEBUG=1 python3 microbial_mayhem_main.py
```

## Test

```bash
python3 -m pytest -q
```

See [`docs/visual-redesign.md`](docs/visual-redesign.md) for the architecture
assessment, phased visual plan, and mobile-readiness recommendation.


May the best bug win!

## Rebuild the fighter catalog

The game reads the normalized runtime database at
`data/catalog/microbial_mayhem_catalog.sqlite3`.

To migrate an existing generated JSON catalog:

```bash
python3 scripts/migrate_catalog_to_sqlite.py
```

To rebuild from a retained BacDive export with local MIBiG enrichment:

```bash
python3 scripts/build_bacdive_catalog.py \
  --bacdive-json data/bacdive/bacdive_records.json
```

The large BacDive export, legacy generated JSON catalog, and raw API cache are
local rebuild inputs and are intentionally ignored by Git.
