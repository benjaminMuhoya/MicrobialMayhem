# Mobile performance baseline

Measured from the static production build on 2026-07-16.

| Asset | Uncompressed | Gzip |
|---|---:|---:|
| Initial HTML | 15.1 KB | — |
| Main game page JavaScript | 85.3 KB | 25.8 KB |
| Fighter catalog (384 fighters) | 387.6 KB | loaded once, then retained locally |
| Phaser battle engine | 1.38 MB | 355 KB |
| Entire packaged web application | approximately 5.1 MB | — |

The Phaser engine is a separate dynamic chunk. It is not requested on the menu, fighter, colony, arsenal, or environment scenes; it loads when the battle arena mounts. Audio and scientific data are local and cacheable, so gameplay does not depend on streaming.

## Runtime safeguards

- Device memory, CPU concurrency, viewport width, and reduced-motion preference select a low, medium, or high quality tier.
- Low quality limits the arena to 8 environmental particles and 7 background colony cells per side, disables antialiasing, removes costly background blur and shadows, and suppresses secondary atmosphere.
- Medium quality limits the arena to 16 particles and 10 colony cells per side.
- High quality uses 24 particles and 14 colony cells per side.
- Phaser is destroyed when leaving the arena, audio nodes are reused by the centralized audio manager, the catalog is fetched once, and background visibility pauses both audio and arena activity.
- The service worker and native package retain required assets for offline startup.

## Verification

- Production build succeeds.
- 29 unit/parity tests pass, including quality-tier limits.
- Three complete Chromium interaction flows pass against the static package without browser errors or missing assets.
- Physical-device frame rate, battery, thermal behavior, launch time, and audio latency still require final measurement on the exact supported iPhone/iPad/Android device matrix before store submission.
