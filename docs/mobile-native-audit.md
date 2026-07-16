# Microbial Mayhem mobile-native audit

Date: 2026-07-16

## Executive summary

The current game is a React 19 / Next-compatible Vinext application packaged with Capacitor 8. React owns the scene flow and setup state, while Phaser 4 is loaded only for the animated battle arena. The scientific catalog, deterministic fighter identity, Python-compatible random generator, and battle scoring are already separated into pure TypeScript modules. That separation makes a substantial visual and interaction redesign safe without changing battle outcomes.

Capacitor is an appropriate native shell for this project. A full engine migration is not warranted: Phaser plus layered DOM/CSS art can already produce the requested 2.5D depth, particles, camera motion, and procedural morphology. The App Store risk is the current presentation, not the packaging technology. The visible prototype navigation, footer, long scrolling roster, fixed battle canvas, inactive settings button, and lack of lifecycle/audio/native controls make the current build feel web-like.

## Current architecture

### Application and rendering

- `web/app/page.tsx`: client-side React scene controller and the complete setup/results flow.
- `web/app/components/PhaserArena.tsx`: dynamically imports Phaser and creates the battle canvas only when the arena scene is active.
- `web/app/globals.css`: DOM fighter art, environment-card art, scene layout, animation, breakpoints, and reduced-motion media query.
- Vinext/Vite produces both the hosted build and the static `dist/pages` package copied into Capacitor.
- Capacitor Android is configured with local packaged assets and an HTTPS-style internal origin. iOS has not yet been added.

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

- The Python application has a modular audio manager and locally generated WAV assets.
- The web/mobile application currently disables Phaser audio and has no web audio service.
- Audio assets are not currently copied into the web public bundle.
- Asset generation and licensing notes exist at `assets/README.md`; these should be extended for every mobile sound and music asset.

### Offline and lifecycle behavior

- Hosted/PWA mode has a network-first service worker with cached fallback.
- Capacitor packages the application and 384-fighter catalog locally, so normal play does not require a server.
- There is no friendly catalog-load recovery UI, explicit online/offline state, foreground/background handling, pause-on-background, audio suspension, or save/resume session behavior yet.

### Scaling and accessibility

- Existing CSS uses `svh`, safe-area environment variables, focus-visible outlines, responsive breakpoints, and `prefers-reduced-motion`.
- The current responsive model largely collapses desktop panels into a vertical phone page.
- There are no explicit phone-landscape, phone-portrait, or iPad layout modes.
- Touch targets are inconsistent, hover styling is sometimes the strongest feedback, modal focus trapping is incomplete, and long names can compete with fixed panels.

### Packaging and App Store suitability

- Capacitor is suitable for Google Play and App Store distribution.
- Android debug packaging works and runs offline.
- iOS/iPadOS packaging still needs `@capacitor/ios`, an Xcode project, signing, icons, launch assets, lifecycle configuration, and device testing.
- The current build exposes no browser chrome inside Capacitor, but it still visually resembles a responsive website.
- Apple review risk remains until prototype navigation/footer are removed, the interface becomes scene-based and touch-first, settings/help/lab become real game spaces, and the experience demonstrates lasting game value beyond a wrapped webpage.

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

- Unit/parity suite: 17 passing tests.
- Packaged static site: approximately 3.2 MiB.
- Largest emitted file: Phaser, approximately 1.38 MiB, already dynamically requested by the arena component.
- Runtime fighter catalog: 384 fighters, approximately 0.37 MiB.
- Current lint command incorrectly scans generated Android build output, producing thousands of irrelevant diagnostics. Source lint has only a small number of warnings; generated directories must be excluded before lint can serve as a release gate.

## Immediate first implementation slice

- Introduce a typed settings/preferences model with reduced motion, haptics, music, and effects controls.
- Add mobile viewport classification and safe-area scene scaffolding.
- Replace the prototype header/footer with a game HUD and real Settings/How to Play/Microbe Lab routes accessible from the opening scene.
- Add skippable opening-sequence state and first-launch persistence.
- Preserve the existing start-game path and all scoring inputs exactly.
