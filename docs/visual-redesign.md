# Microbial Mayhem visual redesign

## Codebase assessment

The playable application is Python 3 with a single-window Pygame 2 interface.
`microbial_mayhem_main.py` is the entry point and owns screen navigation,
application state, input, and rendering. Screens are string-valued states drawn
inside one 60 FPS loop. `bacterial_catalog.py` and `catalog_storage.py` load the
normalized offline SQLite catalog; `scoring.py`, `colony_scoring.py`, and
`trait_inference.py` contain reusable rules. Older terminal menus and prototype
animation files remain in the repository but are not part of the current game.

The principal visual limitation was not Pygame itself, but presentation code
concentrated in one large class: fixed coordinates, repeated colors, list-like
selection, minimal organism silhouettes, an information-table preview, and a
battle represented by two circles and a continuous beam. Resizing currently
enlarges the window without reflowing the fixed 1200 × 820 layout. Audio, save
data, accessibility settings, and platform adapters do not yet have dedicated
services.

Preserve the SQLite organism catalog, name formatting, deterministic seeded
scoring, colony formula, trait evidence, opponent selection, and result
breakdowns. Redesign rendering, navigation transitions, selection cards,
environment presentation, animation states, and interaction feedback.

`presentation.py` is the first extraction: it creates stable visual models from
catalog records without importing Pygame or changing scientific data. Recorded
morphology drives the silhouette when present. A deterministic placeholder is
used only as art when morphology is unknown and is labelled as procedural.

## Visual direction and phases

The direction is a bright microbial arena: deep navy laboratory surfaces,
mint/coral/violet organisms, readable scientific names, chunky cards, and
small expressive procedural sprites. Each environment has a restrained color
gradient and ambient particle language.

The central state now also supports the original one-player flow and a local
two-player flow. Explicit Player 1/Player 2 fighter fields synchronize with the
unchanged scoring aliases; two-player selection never calls random opponent
selection and rejects duplicate organism records through shared validation.
Each player also has independent colony and arsenal fields. The shared scoring
aliases are synchronized only after both local setups are confirmed, while the
environment remains one shared arena choice.

1. Foundation: centralized design tokens, typography and spacing cleanup,
   consistent panels/buttons, transitions, dependency documentation, and pure
   presentation models. Status: first working slice complete.
2. Roster: richer responsive fighter-card grid, morphology and appendage art,
   comparison details, keyboard/controller focus, and the versus screen. Status:
   procedural roster art and versus screen complete; responsive grid remains.
3. Arena: single-screen idle/attack/hit/ability/defeat/victory states connected
   to the already-computed outcome, visible health, particles, environment,
   compact battle log, and skip control. Status: eight-second elapsed-time
   timeline complete, including defense, dodge, status, environment, victory,
   defeat, and skip presentation states.
4. Polish: environment art expansion, result reveal, onboarding, audio service,
   saves, tooltips, reduced-motion/color/accessibility settings, and progression.
   Status: settings, onboarding, tooltips, audio hooks, staged results, and local
   preference persistence complete; progression remains future work.

After each phase, run the full tests and a headless render smoke test. Battle
logic must remain independent of animation timing.

## Mobile readiness

Pygame is effective for this desktop prototype and supports animation, audio,
resizable windows, and custom touch-like input handling. It is not the safest
production path for both Android and iOS: official packaging workflows are not
as mature or predictable as a mobile-first engine, iOS deployment is especially
awkward, and the current fixed coordinate system needs a viewport/layout layer.

For this game, Godot is the strongest long-term client option because its 2D
animation, particles, touch input, responsive UI, audio buses, local saves, and
Android/iOS export are first-class. A migration should not begin as a rewrite.
First stabilize a platform-neutral battle transcript/state model in Python,
export a small fixture of organism data, and build one Godot proof-of-concept
arena that consumes that fixture. Validate feel and packaging before porting
the deterministic formulas from `scoring.py`, `colony_scoring.py`, and
`trait_inference.py`. Catalog build scripts can remain Python tooling; the
runtime client can consume a compact SQLite or generated JSON subset.

Kivy would reuse more Python directly and is a reasonable fallback if minimizing
ported code outweighs game-production tooling, but it is less compelling here
than Godot for a polished sprite-and-effects-heavy battle experience.

## Next improvements by impact

1. Add true reflow layouts for very narrow portrait and touch displays.
2. Add original production sound files to the completed audio-hook system.
3. Expand environment-specific foreground art and effect vocabulary.
4. Add richer focus geometry and controller remapping.
5. Add save-backed progression without coupling it to battle scoring.
6. Build and package the one-arena Godot mobile proof of concept later.
