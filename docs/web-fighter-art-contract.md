# Browser fighter sprite-sheet contract

The browser game renders its complete roster procedurally and uses that renderer
as the APK-safe fallback. `web/public/fighters/manifest.json` can progressively
replace any fighter and pose with a transparent sprite sheet without changing
gameplay.

Each manifest entry is keyed by the exact catalog ID, then by pose:
`entrance`, `idle`, `ready`, `move`, `anticipate`, `attack`, `defend`, `impact`,
`arsenal`, `stress`, `decline`, `recover`, `victory`, or `defeat`.

Each definition contains:

- `src`: case-sensitive packaged path below `web/public/fighters/`;
- `frameWidth` and `frameHeight`: 256 pixels;
- `frames`: state frame count from `FIGHTER_ANIMATIONS`;
- `anchor`: bottom-center ground anchor `[128, 218]`.

Sheets are horizontal WebP, PNG, or SVG strips with straight-alpha transparency. Text,
shadows, lighting and environment effects must not be baked into frames. The
loader caches the manifest and decoded images, returns `null` for missing or
invalid sheets, and leaves the procedural morphology renderer active.
