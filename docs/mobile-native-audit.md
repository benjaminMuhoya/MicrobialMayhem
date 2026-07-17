# Microbial Mayhem mobile-native audit

Date: 2026-07-16

## Executive summary

The current game is a React 19 / Next-compatible Vinext application packaged with Capacitor 8. React owns the scene flow and setup state, while Phaser 4 is loaded only for the animated battle arena. The scientific catalog, deterministic fighter identity, Python-compatible random generator, and battle scoring are already separated into pure TypeScript modules. That separation makes a substantial visual and interaction redesign safe without changing battle outcomes.

Capacitor is an appropriate native shell for this project. A full engine migration was not warranted: Phaser plus layered DOM/CSS art now provides the requested 2.5D depth, particles, camera motion, and procedural morphology. The original presentation and lifecycle risks recorded below were resolved during the refinement phases; the remaining release risks are signing, store-account metadata, and physical-device verification.

## Current architecture

### Application and rendering

- `web/app/page.tsx`: client-side React scene controller and the complete setup/results flow.
- `web/app/components/PhaserArena.tsx`: dynamically imports Phaser and creates the battle canvas only when the arena scene is active.
- `web/app/globals.css`: DOM fighter art, environment-card art, scene layout, animation, breakpoints, and reduced-motion media query.
- Vinext/Vite produces both the hosted build and the static `dist/pages` package copied into Capacitor.
- Capacitor Android and iOS are configured with locally packaged assets and no remote gameplay URL. GitHub verifies Android APK/AAB output and an unsigned iPhone/iPad simulator compilation.

### Screens and navigation

The flow is a single React state machine:

`home -> fighter -> colony -> arsenal -> environment -> preview -> arena -> results`

One-player selection creates a deterministic catalog opponent. Two-player mode locks Player 1, prevents duplicate selection, and gives both players independent fighter, colony, and arsenal choices. Navigation is currently direct `setScreen(...)` state mutation; there is no history stack, unified back behavior, pause overlay, or saved/resumable session.

### Game state

- Setup and session state are local React `useState` values in `page.tsx`.
- Battle results are derived with `useMemo` and the pure `scoreBattle(...)` function.
- IndexedDB is present only for preference helpers; it is not yet connected to settings or session recovery.
- No remote service is required for a match.

### Scientific data and database access

- Runtime catalog: `web/public/data/fighters-core.v2.json`.
- Current mobile catalog: 384 fighters, approximately 0.37 MiB.
- All 384 records currently include `cellShape` and `motility`.
- Search and sampling operate on the in-memory compact catalog.
- The larger source SQLite/MIBiG pipeline remains outside the runtime bundle.
- The service worker caches the baseline catalog and application shell for hosted/PWA use; Capacitor packages the same static files locally.

### Battle calculation — protected boundary

The following files are calculation/data contracts and must not be changed as part of visual polish unless a separately reviewed scientific requirement demands it:

- `web/app/game/scoring.ts`
- `web/app/game/python-random.ts`
- `web/app/game/types.ts` battle/scoring interfaces
- `web/tests/scoring-parity.test.mjs`
- `tests/fixtures/battle_parity.json`

`scoreBattle(...)` determines the winner before the arena is rendered. Phaser receives only the completed result and dramatizes that result. Visual personality, animation timing, sound, haptics, and morphology presentation must never add score or mutate the result.

### Fighter identity

`web/app/game/visual-profile.ts` already creates a stable profile from `catalogId` and scientific name, prioritizes recorded morphology, and supplies deterministic fallbacks. It currently covers 11 silhouette families and five appendage/expression groups. This is the correct foundation, but the profile should be expanded into a richer reusable archetype containing morphology label, proportions, texture, movement, stance, signature presentation, and personality metadata.

### Animation

- DOM/CSS: menu organism, fighter cards, colony particles, environment cards, transitions, and results.
- Phaser: battle entry, projectiles, defense, environment particles, health, camera impulse, and resolution.
- Battle timeline cues are deterministic and independently tested.
- The Phaser canvas is fixed at 1000 x 460 and scaled to fit, so it needs phone/tablet layout profiles rather than one universal composition.

### Audio

- The web/mobile build uses a centralized feedback manager for music, interface, character, ambience, impact, and reveal channels.
- Original WAV assets are packaged locally, with duplicate-sound cooldowns, lifecycle suspension/resume, captions, volume controls, and native haptics where available.
- Sources and licensing are recorded in `docs/asset-credits.md`.

### Offline and lifecycle behavior

- Hosted/PWA mode has a network-first service worker with cached fallback.
- Capacitor packages the application and 384-fighter catalog locally, so normal play does not require a server.
- Friendly recovery, offline status, validated optional updates, last-known-good fallback, foreground/background pausing, audio suspension, and session save/resume are implemented.

### Scaling and accessibility

- CSS uses `svh`, safe-area environment variables, focus-visible outlines, responsive breakpoints, and `prefers-reduced-motion`.
- Explicit phone portrait/landscape and tablet portrait/landscape modes are implemented, including split landscape-iPad two-player selection.
- Automated browser tests cover viewport overflow and touch targets; physical-device safe-area, Dynamic Island, trackpad, and keyboard verification remains a release gate.

### Packaging and App Store suitability

- Capacitor is suitable for Google Play and App Store distribution.
- Android debug APK and unsigned release AAB packaging are continuously built on GitHub and work from local packaged content.
- iOS/iPadOS includes the Capacitor project, modern iPhone/iPad target families, icons, launch assets, privacy manifest, lifecycle integration, and an unsigned simulator-build workflow.
- The native build exposes no browser chrome and presents full-screen, touch-first scenes with real Settings, How to Play, Microbe Lab, Discoveries, tutorial, battle, and results spaces.
- Apple/Google signing, TestFlight/Play internal testing, physical-device verification, and final review metadata remain owner gates.

## Reusable visual systems

- CSS morphology silhouettes and appendages.
- Deterministic palettes, expressions, motion classes, and opponent silhouette differentiation.
- Environment motifs, particularly Acid and Antibiotic.
- Petri-dish, agar, liquid, particle, glow, and translucent membrane treatments.
- Phaser battle cue timeline and current environment particle mapping.
- Colony density preview and CFU-to-score display.
- Results score components and biological explanations.

## Safe refactoring plan

1. Keep `scoreBattle(...)` and catalog contracts immutable.
2. Extract scene navigation/session state from the monolithic page into a typed game-session layer without changing transitions.
3. Add a shared viewport/layout hook that classifies phone portrait, phone landscape, tablet portrait, and tablet landscape.
4. Replace the prototype header/footer with a safe-area-aware game HUD, consistent back control, and native overlays.
5. Expand visual profiles deterministically and reuse them in DOM selection art and Phaser.
6. Add modular preferences, audio, haptics, lifecycle, and persistence services behind narrow interfaces.
7. Improve one scene at a time and run scoring parity plus flow tests after every phase.

## Baseline quality and performance

- Unit/parity suite: 31 passing tests, plus six browser gameplay and responsive flows.
- Packaged static site: approximately 3.2 MiB.
- Largest emitted file: Phaser, approximately 1.38 MiB, already dynamically requested by the arena component.
- Runtime fighter catalog: 384 fighters, approximately 0.37 MiB.
- Current lint command incorrectly scans generated Android build output, producing thousands of irrelevant diagnostics. Source lint has only a small number of warnings; generated directories must be excluded before lint can serve as a release gate.

## Completion status

The implementation slices above are complete. See `docs/final-mobile-refinement-report.md` for the delivered screen-by-screen experience and `docs/mobile-store-release.md` for the remaining signing, device, and submission procedure. Battle scoring remains guarded by Python-parity fixtures and was not changed by the mobile refinement.
