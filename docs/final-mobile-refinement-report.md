# Microbial Mayhem mobile refinement report

## 1. Original architecture audit

The retained application is a React 19/Vinext single-page game. HTML/CSS renders menus and setup scenes; Phaser is dynamically imported only for the battle arena. State is local React state with IndexedDB persistence. The 384-fighter production catalog is packaged JSON derived from BacDive with MIBiG enrichment. A deterministic TypeScript scoring port is protected by Python parity fixtures. Capacitor wraps the static export for Android and iOS. The original wrapper was appropriate as a delivery mechanism but still exposed website-like layouts; the refinement kept the wrapper and replaced those interactions with full-screen scenes, safe-area HUD navigation, touch controls, native lifecycle behavior, offline assets, Haptics, and platform projects.

Reusable systems retained: scoring, catalog/search, deterministic RNG, environment modifiers, colony/arsenal inputs, result components, scientific explanations, service worker, and Capacitor Android project. Refactored systems: responsive composition, fighter visuals, feedback/audio, battle rendering, persistence, progression, accessibility, and native packaging. No migration to a full 3D engine was necessary; layered CSS and Phaser shapes provide the requested 2.5D depth at substantially lower migration risk.

## 2. Implemented improvements

- Cinematic, skippable microscopic opening with the approved title, subtitle, and description.
- Distinct deterministic morphology/personality profiles across the selection roster and arena.
- Preview/confirm selection, search, taxonomy/morphology filters, comparison, long-press facts, evidence indicators, favorites, and two-player locking.
- Interpolated morphology-aware colony growth with binary-fission staging.
- Animated, directly selectable Acidic, Antibiotic, Cold, Hot, Salty, Alkaline, and Neutral habitats.
- Layered Petri-dish battle with colonies, trait effects, territory, environment pressure, pause/resume, lifecycle suspension, and scientific results.
- Modular locally packaged music/SFX and native Capacitor Haptics with captions and comfort controls.
- First-match interactive tutorial with skip/replay.
- Three-layer results, factor comparison, evidence confidence, tappable adaptation replay, scientific-upset recognition, and limited-data wording.
- Random Match, Daily Challenge, best-of-three, favorites, history, achievements, concept challenges, trait encyclopedia, alternate-environment rematch, and local result-card sharing.
- Offline catalog fallback, validated optional updates, last-known-good rollback, friendly failure state, interrupted-match recovery, privacy/version/credits/data-source scene.
- Color-blind patterns, contrast/focus states, modal focus containment, touch-target guarantees, keyboard/trackpad/controller navigation, long-name wrapping, captions, reduced motion, and no flashing effects.
- Adaptive performance tiers, lazy Phaser loading, bounded particle/colony counts, background suspension, and documented production measurements.
- Native Android and iPhone/iPad projects, app icon, launch art, privacy manifest, Haptics plugin, offline resources, GitHub Pages deployment, and GitHub-built APK artifact.

## 3. Revised screen flow

Home presents the cinematic dish and direct access to modes, settings, tutorial, lab, and discoveries. Fighter selection behaves like a character roster, including a dedicated split composition for independent Player 1 and Player 2 selection on landscape iPad. Colony setup grows a living dish. Arsenal setup only presents documented chemistry. Environment selection previews the shared arena and gives each habitat a distinct audible/captioned cue. Versus introduces both distinct organisms. Battle is a pauseable biological spectacle. Results reveal winner, decisive evidence, and deeper science progressively. Microbe Lab supports taxonomy, inspection, and favorites. Discoveries collects matches, traits, achievements, and concept challenges. Settings controls audio, haptics, captions, motion, color-blind presentation, and tutorial replay. Game Information contains version, privacy, source, update, and credit details.

## 4. File inventory

Key changed or created areas:

- `web/app/page.tsx` and scene CSS files: screen flow and presentation.
- `web/app/components/PhaserArena.tsx`: lazy 2.5D battle presentation.
- `web/app/game/`: scoring-preserving visual profiles, audio feedback, progression, recovery, accessibility, and performance policy.
- `web/public/audio/`, `web/public/data/`, `web/public/privacy.html`, manifest and service worker: offline release assets.
- `web/tests/` and `web/e2e/`: parity, behavior, resilience, accessibility, performance, and full-flow tests.
- `web/android/`, `web/ios/`, and `web/capacitor.config.ts`: native projects and configuration.
- `.github/workflows/`: Pages deployment and downloadable APK construction.
- `assets/mobile/` and `docs/`: original mobile art, credits, performance evidence, and release instructions.

The Git history from `0fa4714` through `08f5437` provides the authoritative phase-by-phase changed-file list.

## 5. Running and testing

From `web`: run `npm ci`, `npm run dev`, and open the shown local URL. Use `npm run lint`, `npm test`, and `npm run test:e2e` for validation. The current suite passes 31 unit/parity/packaging checks and six end-to-end flows, including phone portrait, phone landscape, iPad portrait, iPad landscape two-player selection, one-player, and two-player gameplay. `npm run build:pages` produces `web/dist/pages`. The deployed game is https://benjaminmuhoya.github.io/MicrobialMayhem/.

## 6. Mobile packaging

Run `npm run android:sync` or `npm run android:apk` with Java 21 available. Run `npm run ios:sync`, then open `web/ios/App/App.xcodeproj` in full Xcode. Signing, archive, TestFlight, Play internal testing, and store metadata steps are documented in `docs/mobile-store-release.md`.

## 7. Remaining store risks

These are release-owner gates rather than missing repository implementation: Apple/Google developer enrollment, signing identities and private keys, store records, support contact, screenshots/questionnaires, legal review, and physical-device performance/audio/haptic verification. Full Xcode and a local Java runtime are not installed in the current shell, although GitHub successfully builds the Android APK. Two moderate transitive PostCSS advisories remain pending a safe upstream Next update; no high or critical production findings were reported on 2026-07-16.

## 8. Licensing and attribution

See `docs/asset-credits.md`. Essential audio and launch art are original, local project assets. Scientific source attribution is shown in-game and in documentation. No streamed or unlicensed core asset is required.

## 9. Performance results

See `docs/mobile-performance.md`. The static application is approximately 5.1 MB. Main page JavaScript is 85.3 KB uncompressed/25.8 KB gzip; Phaser is a separate 1.38 MB/355 KB gzip battle-only chunk. The packaged fighter catalog is 387.6 KB. Low/medium/high tiers cap secondary effects without changing gameplay.

## 10. Core-logic preservation checklist

- [x] Python/TypeScript scoring parity fixtures pass.
- [x] Environment, colony, arsenal, tie, and winner calculations remain unchanged.
- [x] Visual morphology and personality never enter scoring.
- [x] Battle animation consumes the determined result and never determines it.
- [x] Scientific component explanations remain sourced from scoring output.
- [x] Missing evidence is labeled as limited rather than invented.
- [x] Forbidden developer wording is absent from player-facing scenes.
- [x] One-player and two-player full browser flows pass.
- [x] Offline data, audio, privacy, manifest, and native packages are present.
