# Pygame 2.5D visual upgrade

The production Pygame renderer uses deterministic procedural fighter art so the
full offline catalog does not require tens of thousands of image files. Visual
profiles are derived from a stable catalog ID and recorded morphology; they
never enter scoring.

## Implemented presentation layers

- environment background and ambient motes;
- glass rim, fluid surface, highlights, and dish shadow;
- colony entourage behind the principal fighters;
- cached soft fighter shadows;
- vertically sorted, perspective-scaled principal fighters;
- attack trails, anticipation rings, contact effects, and foreground atmosphere;
- HUD, colony momentum, battle log, and controls.

Reduced-motion mode freezes secondary drift, preview signature actions, squash
and stretch, and other nonessential movement. Particle and colony counts are
bounded for mobile-class hardware.

## Fighter profile

`FighterVisual` specifies morphology, morphology variant, movement style,
personality timing, palette, appendages, capsule, spores, epithet, and ability.
The current renderer covers individual, paired, chained, and clustered cocci;
short, long, curved, and paired rods; vibrio/spiral/spirochete forms;
threaded/branched/segmented filaments; and irregular lobed/angular/budding
forms. Flagella, pili, capsules, and spores add secondary silhouettes.

## Optional final sprite-sheet contract

The procedural renderer is production-safe and is not a missing-asset
placeholder. If hand-authored or pre-rendered art later replaces it, preserve
the same data-driven profile and use:

- PNG with straight-alpha transparency and exact case-sensitive filenames;
- 256 × 256 pixel frames in a horizontal strip;
- bottom-center ground anchor at `(128, 218)`;
- no text, shadow, glow, or environment effect baked into a frame;
- states: `idle` (6), `entrance` (8), `ready` (4), `move` (8),
  `anticipate` (4), `attack` (6), `defend` (4), `hit` (4), `arsenal` (8),
  `stress` (6), `decline` (4), `recover` (5), `victory` (8), `defeat` (6);
- filename: `assets/fighters/<catalog-id>/<state>.png`;
- matching frame durations in a future data file, never hardcoded per species.

Missing sheets must continue to fall back to the procedural renderer. Android
asset checks must reject filename-case mismatches before packaging.
