# Microbial Mayhem web visual system

## Concept: living microscopic arena

The interface behaves like a calm observation chamber around a vivid biological specimen. The organism is always the visual hero; controls sit on translucent membrane surfaces and scientific data appears in measured layers rather than dense dashboards.

## Color

- Culture black `#061411`: primary depth/background.
- Membrane green `#0d2620` at 68% opacity: panels.
- Bioluminescent mint `#7bf2bc`: primary action, Player 1, healthy culture.
- Metabolite coral `#ff755f`: opposing fighter, heat, impact.
- Gene violet `#ad8bff`: BGC and specialized chemistry.
- Assay lime `#d7f171`: decisive evidence and score emphasis.
- Specimen white `#f4f7ef`: primary type.
- Mineral gray-green `#a8b6ad`: secondary type.

Use one dominant accent and at most one supporting accent per screen. Glow belongs to living specimens and decisive state changes, not every control.

## Typography

- Interface and numeric display: Geist/system sans, compact and highly legible.
- Scientific names, biological moments, and expressive headlines: Georgia-style serif italic until a licensed production serif is selected.
- Scientific names remain full and readable; truncation must expose the full accessible value.
- Eyebrows use small uppercase sans with generous tracking to orient the player.

## Geometry and spacing

- Base spacing unit: 4 px. Common rhythm: 8, 12, 16, 24, 32, 48, 72.
- Panels use 28 px desktop radii and 18–22 px mobile radii.
- Primary actions use 16 px radii and minimum 48 px height.
- Petri circles and irregular cell membranes soften the rectangular layout.
- Desktop content maximum: 1,400–1,480 px. Mobile side margin: 16 px.

## Surfaces, borders, and shadows

- Membrane panels: translucent deep green, 1 px pale mint border at 16% opacity, strong background blur where supported.
- Shadows are broad and dark (`0 32px 90px rgba(0,0,0,.34)`) rather than stacked neon glows.
- Selected items receive a quiet tinted fill and brighter border.
- Recorded-data status uses a restrained pill; procedural styling must be labeled separately.

## Buttons

1. Primary: solid mint, dark text, directional icon, short lift on hover.
2. Secondary: transparent membrane border, specimen-white text.
3. Quiet/tertiary: text or subtle border, mineral-gray text.
4. Selected mode/card: tinted membrane fill plus mint border.

All controls use visible focus rings and touch targets of at least 44 × 44 CSS pixels.

## Icon language

Use simple geometric marks: cells, rings, metabolite sparks, gene nodes, temperature/salt/ice motifs. Avoid fantasy weapons, shields, and humanoid silhouettes. Production icons should come from one accessible icon family or simple CSS/Phaser geometry; do not mix illustration styles.

## Bacterial visual language

- Cell form comes from recorded morphology when available.
- Membrane, core, division plane, spores, and flagella are procedural geometry.
- Recorded traits and inferred traits receive explicit labels.
- Purely procedural personality styling never appears as a biological fact.
- Motion is elastic, drifting, pulsing, dividing, clustering, recoiling, or flowing—not humanoid punching.

## Environmental visual language

- Neutral: balanced mint particles and slow nutrient drift.
- Hot: coral thermal gradients, refractive haze, rising bubbles.
- Cold: pale blue crystal motes, slower movement, glassy surfaces.
- Salty: faceted crystals and denser blue-green fluid.
- Alkaline: mineral rings and pale green currents.
- Acidic: yellow-green reactive droplets and membrane distortion.
- Antibiotics: violet/coral molecular pulses and scanning pressure bands.

Every environment preview must show both fighters’ actual score modifier before confirmation.

## Motion

- Screen entry: 550 ms, cubic-bezier `.2,.8,.2,1`.
- Control feedback: 160–220 ms.
- Ambient organism drift: 4–6 seconds.
- Environment loops: 7–18 seconds, low amplitude.
- Arena cues follow the authoritative eight-second timeline.
- Impacts use anticipation, contact, recoil, and settle; camera motion is brief and never obscures biology.

## Accessibility and reduced motion

- Maintain WCAG AA contrast for meaningful text and controls.
- Setup UI uses semantic HTML, real labels, buttons, headings, and expanded states.
- Keyboard focus is never communicated by color alone.
- High-contrast mode strengthens borders, removes translucency where necessary, and reduces reliance on glow.
- Reduced motion collapses ambient loops and large movement to short opacity/state transitions while preserving timing and outcome clarity.
- Sound is supplementary; every battle cue has visible text/state feedback.
- Portrait setup screens stack naturally. The arena may request landscape but must provide an understandable portrait fallback.

