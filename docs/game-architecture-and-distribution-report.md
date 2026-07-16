# Microbial Mayhem: Current Architecture, Gameplay, and Distribution Report

**Repository reviewed:** `/Users/bm0211/MicrobialMayhem/MicrobialMayhem`  
**Review date:** July 15, 2026  
**Status language:** **Confirmed** means directly supported by current code, assets, database, or tests. **Recommendation** means proposed future work. **Assumption** identifies a decision that still needs product validation.

## Executive summary

Microbial Mayhem is a local educational battle game in which database-derived bacteria are turned into procedural fighters. The active product is a Pygame application launched by `microbial_mayhem_main.py`. Players select bacteria, choose colony size and whether to activate documented biosynthetic gene clusters (BGCs), select an environment, watch an eight-second scripted battle, and receive a transparent score breakdown and biological note.

The present build already has a strong separation between pure gameplay/presentation models and Pygame drawing in several modules (`scoring.py`, `presentation.py`, `preview_models.py`, and `ui_systems.py`). That separation makes a browser or engine port feasible. The principal constraints are the 1,200 × 820 fixed virtual canvas, a very large 47,742-fighter runtime catalog, an oversized monolithic GUI class, desktop-oriented persistence, and no production packaging configuration.

The recommended product direction is:

1. keep the raw BacDive/MIBiG ingestion pipeline developer-only;
2. publish a versioned, validated production catalog with only runtime fields, preferably a curated roster or compressed/sharded catalog;
3. extract a platform-neutral battle/session model;
4. build the web version with Phaser and TypeScript, reusing the scoring rules and procedural-art specification;
5. use the same Phaser client as a downloadable Android/iOS application through Capacitor, unless native-store testing reveals a reason to adopt Godot.

This route produces one responsive client for web and mobile and avoids maintaining separate Python, JavaScript, and native interfaces. A short-term Pygame/WASM prototype is useful for validation, but it is not the recommended long-term release architecture.

## 1. Game overview

### Purpose and core loop

**Confirmed.** The README describes the game as “battling bacteria” that teach biology. The current loop is implemented by `MicrobialMayhemGUI`, `GameState`, and `calculate_battle()` in `microbial_mayhem_main.py`:

1. choose one-player or local two-player mode;
2. select one or two distinct bacterial fighters from the offline catalog;
3. set colony-forming units (CFU) from 0–1,000;
4. activate or decline each fighter’s documented BGC arsenal;
5. choose one shared environment;
6. review a versus summary;
7. watch or skip the eight-second battle;
8. compare score components, winner, and biological context;
9. rematch, change fighters, or return to the main menu.

### One-player mode

**Confirmed.** The player selects one fighter. `confirm_fighter()` assigns it to Player 1 and calls `choose_opponent()` to choose a different catalog entry. The automated rival receives a random arsenal choice and, later, a seeded random CFU via `generate_opponent_cfu()`. The player alone confirms colony and arsenal. The shared environment is selected by the player. UI labels use “You,” “Rival,” or “Automated Rival.”

### Two-player mode

**Confirmed.** This is local pass-and-play on one device, not network multiplayer. Player 1 locks a fighter, then Player 2 chooses a different catalog ID. Each player separately confirms colony size and arsenal status; one shared environment is then chosen. `sync_setup_aliases()` maps Player 1/2 fields into the legacy player/opponent scoring aliases. Results use “Player 1” and “Player 2.” Back navigation deliberately returns through the second player’s setup and prevents selecting Player 1’s fighter twice.

### Fighter selection and biological settings

**Confirmed.** `get_catalog()` loads all fighters from `data/catalog/microbial_mayhem_catalog.sqlite3`. `sample_catalog()` presents ten random choices; `search_catalog()` matches full name, display name, strain, or genus. The detail card shows scientific identity, morphology, procedural epithet, ability, habitat, BGC count/IDs, products, activities, and a biological description/fact.

Colony size changes both presentation and score. `colony_score_from_cfu()` applies a diminishing-returns logarithmic rule capped at +10; `colony_particles()` maps the resulting score to 4 plus roughly 3.2 particles per score point. The Petri dish outline does not resize, but its visible cell density changes.

Arsenal activation adds one point per known MIBiG accession, capped at +5. Choosing “Yes” when no BGC accessions are known is rejected by `choose_bgc_arsenal_yes()` with a popup; the player can choose “No.” Documented activities add offense independently of arsenal activation.

Environment choice uses supported traits inferred from MIBiG annotations. Cold, Hot, Salty, Alkaline, Acidic, and antibiotics map to Cryophile, Thermophile, Halophile, Alkaliphile, Acidophile, and Drug resistant. Neutral adds zero. A supported match adds +12. If neither fighter has a supported match, both receive −3. Otherwise unknown or mismatched evidence receives zero, not a fabricated penalty.

### Scoring and winner determination

**Confirmed.** `score_fighter()` in `scoring.py` builds these components:

- Base: +25 for every fighter.
- Colony: 0 to +10 from CFU.
- Environment: +12, −3, or 0 under the rules above.
- Resistance defense: 0 to +5 from Drug resistant evidence; direct immunity/efflux/resistance can reach +5, self-resistance +4, other evidence +2.
- BGC arsenal: 0 to +5, but displayed as an informational subcomponent.
- Known activity: 0 to +5 (antibacterial/antimicrobial +3; antifungal +2; cytotoxic/toxin +2; siderophore/iron +2; other documented activity +1, capped).
- Offense total: arsenal plus known activity; this is the included total component, preventing double counting.
- Battle variation: seeded uniform random value from −2 to +2.

Totals are rounded to two decimals. `calculate_battle()` compares totals: higher score wins; equal totals tie. The animation’s health bars are dramatic presentation values from `ui_systems.battle_health()` and do not feed scoring. Winner information is intentionally hidden until the final 18% of the animation.

## 2. Screen-by-screen breakdown

### Shared screen and input behavior

**Confirmed.** There are nine reachable screen constants: `WELCOME`, `SETTINGS`, `FIGHTER_SELECTION`, `COLONY_SELECTION`, `SECRETION_SELECTION`, `ENVIRONMENT_SELECTION`, `BATTLE_PREVIEW`, `BATTLE_ANIMATION`, and `RESULTS`. `SUPERPOWER_SELECTION` exists as a constant but is not dispatched and is not a reachable screen. There is no separate “battle summary” constant; `BATTLE_PREVIEW` is the pre-battle summary. Information is embedded in fighter and result panels rather than presented as a separate information screen.

All screens are drawn into a fixed 1,200 × 820 virtual surface and letterboxed by `VirtualViewport`. Mouse/touch requires press and release on the same enabled control. Keyboard supports Tab/arrows, Enter/Space, and Escape. Basic controller hat/buttons are supported. `ScreenTransition` adds a short transition overlay; reduced motion shortens it.

### Home / welcome (`draw_welcome`)

- **Purpose:** choose game mode and start or open settings.
- **Entry/exit:** initial screen; main-menu actions reset here. Start enters fighter selection. Settings enters settings. Escape posts quit.
- **Controls:** 1 Player, 2 Players, Start Game, Settings.
- **Text:** animated title, short premise, mode explanation, and any catalog-load error.
- **Visual/audio:** `lightning.jpeg` is the first available background and therefore normally wins over `Mayhem.png` and `May.png`; dark overlay and procedural drifting particles are added. Setup music plays. The title gently bobs unless reduced motion is enabled.
- **Mode differences:** selected mode changes explanatory copy and enables Start Game; no fighter state exists yet.
- **Generator:** `draw_welcome()`, `draw_background()`, `draw_ambient_particles()`, `start_game()`.

### Settings and accessibility (`draw_settings`)

- **Purpose:** configure motion, contrast, typography, and audio.
- **Entry/exit:** Settings from home; Back returns home. Replay Tips resets onboarding and starts the selected mode if one is already selected.
- **Controls:** toggles for reduced motion, high contrast, and mute; plus/minus for text scale, music volume, and effects volume; Replay Tips; Back.
- **Text:** current on/off states and numeric scales/percentages, with tooltips.
- **Visual/audio:** standard panel/background and setup music. Settings persist to `~/.microbial_mayhem/settings.json` through `AppSettings`.
- **Mode differences:** none except Replay Tips can immediately start the currently chosen mode.
- **Generator:** `draw_settings()`, `toggle_setting()`, `adjust_setting()`, `replay_onboarding()`.

### Fighter selection and embedded information (`draw_fighter_selection`)

- **Purpose:** search/browse, inspect, and lock a bacterial fighter.
- **Entry/exit:** Start Game enters Player 1 selection. In two-player mode, Player 1 confirmation advances to Player 2 selection; Player 2 confirmation enters Player 1 colony setup. One-player confirmation enters colony setup. Escape/back returns to the prior selection or home according to mode.
- **Controls:** keyboard text entry, Search, Show 10 Different Bacteria, scroll wheel for long result lists/BGC lists, fighter cards, View all BGCs/Back, Lock Player.
- **Text:** scientific name/strain, morphology, ability, habitat, BGC count and IDs, products, activities, battle bio, search status, and onboarding guidance.
- **Visual/audio:** each fighter has procedural palette, silhouette, appendages, facial expression, epithet, and selection pop. Click/select sounds play.
- **Mode differences:** Player 2 sees Player 1’s locked badge; Player 1’s catalog ID is disabled. Headings and accents identify the active player.
- **Generator:** `draw_fighter_selection()`, `draw_selected_organism_card()`, `draw_locked_fighter_badge()`, `draw_bacterium_sprite()`, `apply_search()`, `refresh_catalog_choices()`, `confirm_fighter()`.

**Morphology and traits verified.** `morphology_for()` uses recorded `cell_shape` to choose coccus, bacillus, spiral, filamentous, or irregular. Missing shape uses a stable SHA-256-derived fallback and is explicitly described as procedural art, not recorded data. `draw_bacterium_sprite()` changes geometry by morphology. Flagella are shown for reported motility, or occasionally as a stable visual fallback only when motility is unknown; explicitly non-motile entries do not receive them. Capsules are inferred from colony-appearance text or a stable visual fallback; pili are purely stable procedural styling; spores come from colony-appearance text or Bacillus/Clostridium genus. These capsule/pili fallbacks are art direction, not scientific claims, which should be made clearer in a production UI.

### Colony-size selection (`draw_colony`)

- **Purpose:** choose 0–1,000 CFU and expose its exact scoring contribution.
- **Entry/exit:** follows fighter confirmation; Lock enters arsenal selection. Back returns to fighter selection or the prior two-player setup step.
- **Controls:** touch/mouse slider, five preset cards (50, 250, 500, 750, 1,000 CFU), lock button.
- **Text:** selected CFU, dynamic colony label, preset flavor, score contribution, rule explanation, and hover preview.
- **Visual/audio:** a large fixed Petri-dish ellipse contains stable procedural particles. More CFU means more cells; some display a division line. Cells use the chosen fighter’s palette. Density changes visibly, but the dish diameter and colony spread boundary do not change. Preset hover temporarily previews a different density.
- **Mode differences:** heading, accent, stored CFU, confirmation flag, and fighter seed use the current setup player. Each player completes this screen independently.
- **Generator:** `draw_colony()`, `draw_colony_preview()`, `colony_particles()`, `choose_colony_size()`, `update_slider()`, `confirm_colony_setup()`.

### Biosynthetic arsenal selection (`draw_secretion`)

- **Purpose:** choose whether the active fighter brings documented MIBiG BGCs into battle.
- **Entry/exit:** follows colony lock. Continue enters environment selection in solo mode. In two-player mode, Player 1 lock moves to Player 2 colony setup; Player 2 lock moves to the environment screen. Back returns to colony setup.
- **Controls:** Yes, No, and Continue/Lock Arsenal.
- **Text:** both fighter panels, BGC count and IDs, products, activity chips, arsenal status, and an educational BGC explanation.
- **Visual/audio:** procedural fighter sprites and panels; selection/click cues. No separate arsenal animation occurs here. During battle, an active arsenal adds an extra `arsenal.wav` layer to ability cues.
- **Mode differences:** solo shows “Your fighter” and an automated-rival scout report. Two-player labels the active setup and the other locked/previewed fighter.
- **Generator:** `draw_secretion()`, `draw_arsenal_panel()`, `choose_bgc_arsenal_yes()`, `choose_arsenal()`, `confirm_arsenal_setup()`.

### Environment selection (`draw_environment_selection`)

- **Purpose:** select the shared battleground and preview the real environment modifier.
- **Entry/exit:** follows completed arsenal setup. Enter This Arena calculates the battle and enters preview. Back returns to the relevant arsenal screen.
- **Controls:** seven large environment cards and Enter This Arena.
- **Text:** arena name, flavor, internal environment label, and a dynamic explanation of each fighter’s actual modifier.
- **Visual/audio:** each card uses an environment-specific gradient and procedural particles. Cold uses cross-like ice marks, antibiotics uses crosses, salty uses diamonds, alkaline uses rings, hot uses bubbles/steam marks, acidic uses pulsing circles, and neutral uses circles. Selection glows/pulses unless reduced motion is on.
- **Mode differences:** scoring copy says “your fighter/rival” even in two-player mode, a minor copy inconsistency. The selected environment is shared in both modes.
- **Generator:** `draw_environment_selection()`, `draw_environment_card()`, `draw_environment_particles()`, `environment_visual()`, `environment_effect_text()`.

### Battle summary / versus preview (`draw_preview`)

- **Purpose:** confirm matchup, arena, special ability, colony size, and arsenal status before battle.
- **Entry/exit:** environment confirmation enters; Enter the Arena starts animation; Escape returns to environment selection.
- **Controls:** Enter the Arena.
- **Text:** arena title/subtitle; each fighter’s scientific name, epithet, special ability, CFU, and arsenal status.
- **Visual/audio:** fighters slide in, VS badge expands, and details reveal; reduced motion shows the final state. Environment-specific animated background is active. Setup music continues.
- **Mode differences:** labels are Your Fighter/Automated Rival or Player 1/Player 2.
- **Generator:** `draw_preview()`, `draw_versus_fighter()`, `draw_versus_stat()`, `battle_setup_complete()`.

### Arena / battle animation (`draw_animation`)

- **Purpose:** dramatize the already-calculated result without changing it.
- **Entry/exit:** Enter the Arena starts it; completion at eight seconds or Skip enters results. Back is intentionally not mapped from this screen.
- **Controls:** Skip; no combat input.
- **Text:** arena title, fighter HUD names/health, three-line battle log, floating action labels, timer.
- **Visual/audio:** procedural fighters enter, idle, anticipate, attack, defend, counter, dodge, use abilities, react to environment, and finish. Projectile paths use a quadratic arc. Short screen shake, anticipation rings, hit states, shields, stun markers, and finale burst appear. Battle music and layered attack/impact/ability/environment/final-hit effects follow `default_battle_cues()`.
- **Environment differences:** all environments change gradient and particles. Hot adds steam arcs; Cold adds an icy floor veil; antibiotics adds a moving scan band; Acidic adds a reactive floor tint; Salty changes foreground particles to crystals. Neutral and Alkaline rely mainly on their palette/particle language.
- **Health/scores:** health is an animation-only curve, held competitive until the finale. `displayed_player_score` and `displayed_opponent_score` are advanced by cues but are not actually rendered in the current arena HUD. The true final scores appear on results.
- **Mode differences:** HUD labels are You/Rival or Player 1/Player 2. Choreography is otherwise identical.
- **Generator:** `start_animation()`, `draw_animation()`, `draw_battle_foreground()`, `apply_battle_cue()`, `draw_battle_hud()`, `BattleTimeline`, `default_battle_cues()`.

### Results (`draw_results`)

- **Purpose:** announce the outcome, explain component scores, and provide biological context.
- **Entry/exit:** follows battle completion/skip. Rematch immediately recalculates with a new seed; Change Fighters retains mode but resets setup; Main Menu resets everything. Escape also returns to main menu.
- **Controls:** Rematch, Change Fighters, Main Menu.
- **Text:** victory/defeat/tie headline, contextual flavor, winner name, both totals, component score cards, and a biological note with BGC/product/activity/environment/CFU context.
- **Visual/audio:** staggered reveal, bouncing headline, winner/loser sprite states, count-up scores, results theme, and delayed victory/defeat/clash accent.
- **Mode differences:** solo uses Victory/Defeat and You/Automated Rival; local mode announces Player 1 or Player 2.
- **Generator:** `draw_results()`, `result_headline()`, `draw_score_card()`, `draw_biological_note()`, `rematch()`, `change_fighter()`.

### Legacy and non-reachable interfaces

**Confirmed.** `env_menu.py`, `species_menu.py`, `superpower_menu.py`, `option_menu_check.py`, `colony_size.py`, `Env_scoring.py`, `defense_systems.py`, `sec_sys.py`, `microbe_class.py`, `microbe_info_output.py`, `ANIME_simple.py`, and `Plot_animation.py` belong to an older terminal/prototype flow. They are not imported by the active entry point. `May.png`, `Mayhem.png`, `microbial_mayhem_intro.mp3`, `lightning.jpeg`, `pic2.txt`, `pic3.txt`, `species_info.txt`, `types_of_env.txt`, and `defense_files_input/` largely accompany that history; only the three background images are candidates in `load_background()`, with `lightning.jpeg` normally selected first.

## 3. Code architecture

### Active runtime map

- `microbial_mayhem_main.py`: entry point, `GameState`, navigation, all Pygame screen drawing, setup orchestration, battle/result lifecycle.
- `bacterial_catalog.py`: runtime fighter data class, SQLite loading, search/sample/opponent selection, plus older MIBiG-only catalog builders.
- `catalog_storage.py`: normalized SQLite schema, atomic writer, read-only loader.
- `scoring.py`: pure deterministic score components and battle comparison inputs.
- `colony_scoring.py`: CFU formula, labels, opponent CFU generation.
- `presentation.py`: pure visual theme, morphology, palette, appendage flags, abilities, epithets, and environment profiles.
- `preview_models.py`: deterministic colony/environment particles, preview copy, projectile paths.
- `ui_systems.py`: virtual viewport, unified activation/focus, transitions, battle timeline, presentation health.
- `audio_manager.py`: fault-tolerant phase music and effect layering.
- `app_settings.py`: validated JSON preferences.
- `flavor_text.py`: safe missing-data wording and stable contextual result flavor.
- `bacterial_names.py`: sanitization and structured scientific-name display.
- `gui_helpers.py`: pluralization and width-based wrapping.
- `environment_icons.py`: clean labels for environments.
- `trait_inference.py`: MIBiG keyword-to-trait evidence, used primarily during catalog building and tests.
- `taxonomy_filter.py`, `catalog_deduplication.py`: developer-side curation/deduplication logic.

### Entry point, navigation, and execution flow

`main()` constructs `MicrobialMayhemGUI` and calls `run()`. Initialization creates a resizable SDL window, fixed virtual surface, settings, fonts, audio, catalog, background, and first random roster. `run()` processes events, updates audio, draws the active screen through a constant-based `if/elif` dispatch, scales the surface, and flips the display.

Navigation is mutation-based: callbacks change `GameState` and call `set_screen()`. There is no screen class, stack, router object, or serializable session model. `set_screen()` handles transition, focus reset, soundtrack phase, and results start time. Setup values are partly duplicated as explicit Player 1/2 fields and partly mirrored through older `player_*`/`opponent_*` aliases. When the environment is confirmed, `after_choice()` supplies solo opponent defaults, seeds and calculates scores, then shows preview. Animation reads the precomputed winner and ends at results.

### Architectural strengths

- Scoring and several presentation models are Pygame-free and well unit-tested.
- The catalog is offline and opens SQLite read-only.
- Input normalizes mouse, touch, keyboard, and controller activation.
- Random scoring is seedable; procedural visuals use stable hashes.
- Audio and missing assets fail safely.
- Environment copy is derived from the same rules used for scoring.

### Duplication, coupling, and fragility

**Confirmed findings:**

- `MicrobialMayhemGUI` is roughly 1,750 lines and owns application control, rendering, navigation, persistence triggers, content layout, animation, and audio calls.
- `GameState` duplicates player-specific fields and older aliases, requiring `load_setup_player()` and `sync_setup_aliases()`.
- Screen transitions are hard-coded across callbacks and `navigate_back()`.
- `start_animation()` appears twice consecutively in the source; the second definition silently replaces the first.
- `pygame.display.set_caption()` is duplicated.
- `SUPERPOWER_SELECTION`, `draw_choice_grid()`, `draw_microbe()`, and score display interpolation are unused or partly unused.
- Many coordinates are literal and tied to 1,200 × 820.
- `draw_arsenal_panel()` is typed for a non-null entry although solo timing and future error paths could violate that assumption.
- Runtime loads all 47,742 fighters and reconstructed JSON lists into memory, even though only a handful are displayed.
- Settings use a desktop home-directory path unsuitable for browser/mobile sandboxes.
- The database schema omits many `BacteriumCatalogEntry` fields; absent fields silently return dataclass defaults. This is compact but implicit and can obscure whether a value is genuinely unknown or was dropped during storage.
- Legacy modules contain obsolete alternate rules and can confuse maintenance if treated as active.

## 4. Data sources and data flow

### Current production source

**Confirmed.** The shipped runtime source is `data/catalog/microbial_mayhem_catalog.sqlite3` (schema version 1), containing 47,742 fighters. Metadata identifies “BacDive primary; MIBiG BGC enrichment only,” built June 30, 2026 from 59,489 BacDive records, with 11,747 duplicate fighters removed. MIBiG enrichment matched 31,016 fighters by exact NCBI tax ID; 16,726 were unmatched. The database normalizes 395 repeated enrichment profiles.

### Raw-to-runtime pipeline

1. `scripts/build_bacdive_catalog.py` either reads `data/bacdive/bacdive_records.json` or fetches BacDive IDs/details over the BacDive API by configured genera.
2. `scientific_name()`, `strain_text()`, `first_value()`, `all_values()`, and related functions flatten irregular nested BacDive records.
3. `build_mibig_indexes()` reads every `mibig_json/BGC*.json` through `load_mibig_records()` and indexes by NCBI tax ID, exact name, and species.
4. `mibig_matches()` chooses tax-ID, name, species fallback, or unmatched enrichment.
5. `entry_from_bacdive()` combines BacDive identity/phenotype/habitat fields with MIBiG accessions, products, activities, classes, moieties, and inferred traits.
6. `infer_traits()` cautiously finds environmental/resistance/antimicrobial evidence in selected MIBiG fields and stores `TraitEvidence`.
7. `deduplicate_fighters()` normalizes identity and keeps the most complete representative.
8. `write_catalog_database()` moves repeated accessions/products/activities/traits into `enrichment_profiles`, writes fighter rows and metadata, sets `PRAGMA user_version`, and vacuums atomically.
9. At runtime `load_catalog_database()` joins fighters to profiles; `BacteriumCatalogEntry.from_dict()` fills omitted dataclass fields with defaults.

### Field provenance and use

**BacDive-derived:** catalog/BacDive IDs, scientific name, genus/species/strain, description, colony appearance, habitat, gram stain, cell shape, motility, oxygen, temperature, pH, salinity, metabolism, host, biosafety, NCBI tax ID. However, schema v1 persists only identity, description, colony appearance, source, BacDive ID, and habitat among these. Cell shape and motility therefore currently default to `Unknown` after SQLite load, despite the builder computing them. This is a consequential confirmed gap: production fighter morphology usually uses procedural fallback rather than retained BacDive morphology.

**MIBiG-derived:** accession IDs, biosynthetic products, biological activities, cluster/compound classes, and inferred traits. Schema v1 retains accessions, products, activities, and traits; it drops classes.

**Generated:** descriptions and curious facts are builder summaries; epithets, palettes, some appendages, fallback morphology, missing-data flavor, particles, and opponent selection are procedural. Audio WAV files are generated by `scripts/generate_audio_assets.py`.

**Legacy local sources:** `species_info.txt`, `types_of_env.txt`, `defense_files_input/`, `mibig_db.json` (empty), and the old Python modules are not used by the current game.

### Runtime-required versus unnecessary fields

For current gameplay/scoring, required fields are: stable `catalog_id`, `full_name`, display/search identity, strain/genus, accessions, products, activities, `TraitEvidence` fields, description/curious fact, colony appearance, habitat, source, and ideally cell shape/motility. Score calculation does not require BacDive ID, taxonomy group/evidence, gram stain, oxygen, temperature, pH, salinity, metabolism, host, biosafety, biosynthetic classes, compound classes, NCBI tax ID, record count, or BGC match confidence.

Some “unnecessary” fields remain valuable for future educational screens, provenance, filtering, or safety review. Recommendation: define a formal product content contract before dropping them, rather than equating “not currently rendered” with “never needed.”

## 5. Files required to run the game

### Required at runtime today

- Python: `microbial_mayhem_main.py`, `app_settings.py`, `audio_manager.py`, `bacterial_catalog.py`, `bacterial_names.py`, `catalog_deduplication.py` (imported by storage), `catalog_storage.py`, `colony_scoring.py`, `environment_icons.py`, `flavor_text.py`, `gui_helpers.py`, `presentation.py`, `preview_models.py`, `scoring.py`, `taxonomy_filter.py` and `trait_inference.py` (transitive imports), `ui_systems.py`.
- Data: `data/catalog/microbial_mayhem_catalog.sqlite3`.
- Audio: all files under `assets/audio/music/` and `assets/audio/sfx/` for full experience; they are technically optional because `AudioManager` fails safely.
- Images: at least one of `lightning.jpeg`, `Mayhem.png`, or `May.png` for the current background; all are technically optional because a procedural fallback exists. Today `lightning.jpeg` is preferred.
- Dependency: Python 3.11+ recommended; `pygame>=2.5,<3`. `sqlite3`, JSON, hashing, dataclasses, pathlib, and other libraries are standard-library modules.
- Configuration: no build config exists. Runtime preferences are created after launch, not bundled.

### Development/data-update files

- `scripts/build_bacdive_catalog.py`, `build_bacterial_catalog.py`, `migrate_catalog_to_sqlite.py`, `deduplicate_catalog.py`.
- `bacterial_catalog.py` builder helpers, `trait_inference.py`, `taxonomy_filter.py`, `catalog_deduplication.py`, `catalog_storage.py`.
- `data/bacdive/bacdive_records.json`, `mibig_json/`, and legacy generated `data/catalog/microbial_mayhem_catalog.json`.
- `data/catalog/catalog_build_report.csv` and `scripts/generate_audio_assets.py`.
- `requirements.txt` and the complete `tests/` directory; pytest is a development/test dependency.

### Safe to exclude from production mobile/web builds

The raw BacDive export, raw MIBiG directory, legacy catalog JSON, build scripts, tests, caches, `.git`, developer report CSV, old CLI/prototype modules, `defense_files_input/`, `defense_files_output/`, `species_info.txt`, `types_of_env.txt`, `pic2.txt`, `pic3.txt`, empty `mibig_db.json`, `microbial_mayhem_intro.mp3`, and unused background alternatives after choosing one production background. A port will also exclude all Python UI modules if rules/data are translated to the target runtime.

## 6. Lightweight distribution strategy

### Production catalog design

**Recommendation.** Introduce an explicit schema v2 and a build manifest. Keep only fields in a documented `RuntimeFighterV2` contract: ID, names/search key, strain, accessions, products, activities, compact trait tuples, short description/fact, habitat, colony appearance, cell-shape classification, motility classification, and provenance/version. Store normalized enum values instead of repeated “Unknown” strings and avoid verbose evidence explanations in the base download; make extended evidence an optional data pack or on-demand detail shard.

The largest opportunity is roster policy. A 47,742-fighter catalog is scientifically broad but excessive for a casual selector and costs 32.4 MiB before app/runtime overhead. A curated 1,000–5,000 fighter core, with genus/search shards downloadable on demand, would improve discovery and dramatically reduce startup memory. If all fighters must remain offline, use SQLite page-size/vacuum tuning for native clients and Brotli-compressed JSON/MessagePack shards for web delivery; browsers should not download 32 MiB before the home screen.

### Versioning, updates, and compatibility

1. Add `schema_version`, `content_version` (semantic or date-based), `built_at`, source release/API dates, record counts, source checksums, builder commit, and minimum client version to metadata.
2. Retain raw sources in developer storage or a private data-release bucket, not the game package.
3. Run a repeatable update job that fetches BacDive/MIBiG, records licenses/source versions, retries requests, and freezes immutable raw snapshots.
4. Validate required fields, unique IDs, foreign keys, trait enums, score ranges, safe text length/encoding, duplicate rates, MIBiG match confidence, and deterministic build output.
5. Compare the new catalog with the previous release: additions, removals, renamed IDs, changed traits, and score-impacting changes.
6. Publish only a signed/checksummed compact database or shards plus a small manifest. Keep one prior compatible version available for rollback.
7. Save games by stable fighter ID plus content version and setup choices. Maintain an ID alias/tombstone table. If a fighter disappears, preserve its minimal embedded snapshot or substitute only after explicit user notice. Version the saved-game schema independently of catalog schema.

### Release exclusion controls

The `.gitignore` already excludes raw BacDive records, raw API cache, and legacy catalog JSON, but ignores are not a release boundary. Add an allowlist-driven packaging manifest and CI assertion that rejects `data/bacdive/`, `mibig_json/`, raw JSON, tests, caches, and developer scripts. Generate releases into a clean staging directory and produce a size inventory/checksum list.

### Size estimate

Current measured repository contributions are approximately: active/legacy Python under 0.3 MiB; SQLite 32.4 MiB; audio 1.6 MiB; three PNG/JPEG backgrounds 0.46 MiB; raw MIBiG 16 MiB; legacy catalog JSON 260 MiB; BacDive export 549 MiB. A desktop Python bundle will additionally include Python/Pygame/SDL, commonly tens of MiB. A lean native/web client with one background, compressed audio, and a curated catalog could plausibly keep game-owned content under 10–20 MiB; exact installed/download sizes require prototype builds.

Biggest reductions: exclude 825 MiB of raw/legacy data; shrink or shard the 32.4 MiB catalog; convert WAV music/effects to platform-appropriate compressed formats; include one optimized background; remove legacy modules/assets; avoid bundling an entire Python runtime where possible.

## 7. Mobile-app pathway

### Option A: package existing Python/Pygame

Tools such as python-for-android/Buildozer can package Pygame-family applications for Android; iOS support is materially more difficult and toolchain-sensitive. Most game logic and drawing could remain. Touch events already exist, audio/animation are SDL-based, and SQLite is available. Work is still needed for mobile file paths, lifecycle pause/resume, safe areas, orientation, DPI, keyboard/search input, app icons/splash, signed builds, and store privacy/licensing. The fixed landscape canvas can scale but produces small text and letterboxing. Maintenance risk is high because iOS packaging and native SDK changes are outside the repository’s current test surface.

**Use:** internal Android proof of concept, not the preferred cross-store product.

### Option B: mobile Python framework (Kivy)

Pure scoring/data modules could be reused with modest adaptation, but every Pygame drawing function, animation, input layer, and screen layout would be rewritten in Kivy. Android/iOS, touch, scaling, audio, and SQLite are supported, but developer familiarity and Python mobile packaging remain concerns. This trades one UI rewrite for a less transferable web story.

**Use:** viable only if the team strongly prefers Python and accepts separate web work.

### Option C: Godot

Rules and data contracts can be ported; Pygame drawing/navigation must be rebuilt as Godot scenes, controls, shaders/particles, animation players, and GDScript/C#. Godot provides strong Android/iOS packaging, responsive containers, touch, audio, animation, performance, SQLite via plugin or JSON/resources, and a web export. Procedural bacteria map naturally to scene nodes. App-store maintenance is credible, but this creates a second implementation language and web exports can have larger startup payloads/compatibility constraints than a purpose-built browser game.

**Use:** strongest dedicated game-engine alternative, especially if richer animation/content is the priority.

### Option D: Unity

Unity offers excellent stores, tooling, performance, animation, touch, and plugins, but nearly all UI/rendering must be rewritten in C#. Build/runtime size, licensing/tool complexity, and maintenance are disproportionate to this 2D data-driven game. WebGL output is heavier than Phaser.

**Use:** not recommended for the current scope.

### Option E: Flutter or React Native

Scoring/data can be translated to Dart/TypeScript. Standard UI, accessibility, persistence, stores, and responsive layout are excellent, but the animated arena requires CustomPainter/Flame (Flutter) or Skia/game-library work (React Native). React Native shares TypeScript with a web frontend but not necessarily rendering. Flutter web is possible but often heavier and less natural for a canvas game.

**Use:** viable if the product becomes education/content UI first and battle animation second.

### Recommended mobile approach

**Recommendation:** port to TypeScript + Phaser for the game client, package the same responsive web application with Capacitor for Android and iOS. This maximizes code sharing with the recommended web pathway, supports Canvas/WebGL, touch/audio/offline caching, SQLite/native preferences through Capacitor plugins when needed, and conventional store builds. Godot is the fallback if prototype performance, native audio, or future animation complexity exceeds the web stack.

Staged plan:

1. freeze scoring fixtures and define `RuntimeFighterV2`, `BattleSetup`, `BattleResult`, and `SaveGame` schemas;
2. translate pure scoring/presentation models to TypeScript and prove byte-for-byte fixture parity;
3. rebuild setup screens with responsive DOM/UI overlays and arena with Phaser;
4. add touch targets, landscape phone/tablet breakpoints, safe areas, local storage/IndexedDB;
5. deliver a PWA, then wrap with Capacitor;
6. add native lifecycle, haptics (optional), audio focus, privacy, signing, store assets, device testing;
7. beta through Play internal testing and TestFlight before public release.

## 8. Web-game pathway

### Pygame through WebAssembly / pygbag

This offers the fastest visual proof and reuses most Python/Pygame code. The main loop may need asynchronous adaptation; filesystem/settings and SQLite delivery need browser-compatible handling. Large Python/WASM and data payloads increase first load. Browser audio requires user gesture, memory can be tight on mobile Safari, and debugging/platform consistency is weaker. Pyodide is even heavier for a game and should not be the default.

### JavaScript Canvas from scratch

This provides small, controlled output and direct web APIs. Scoring rules and procedural models translate cleanly, but navigation, asset loading, tweens, input, audio mixing, and scene lifecycle must be reinvented. It is appropriate only if the team wants a very small custom engine.

### Phaser

Phaser provides scenes, responsive scaling, Canvas/WebGL, tweens, particles, audio, pointer/keyboard/gamepad input, and asset loading. The current procedural renderer maps well to Phaser Graphics. DOM overlays can handle search, settings, readable data cards, and accessibility better than canvas-only controls. Offline play is available through service workers/PWA caching. Static hosting is enough for local solo/two-player; no backend is required.

### Godot web export

One Godot project could target web and stores. It provides excellent scene tooling, but export size/startup and browser threading/audio limitations need testing, especially on iOS Safari. Integrating accessible/searchable text-heavy catalog UI is less natural than HTML.

### Backend API plus browser frontend

A scoring API could centralize rules, catalog search, telemetry, accounts, and future remote multiplayer. It also creates hosting cost, latency, privacy/security work, cheat authority questions, and loss of offline play. The current local game does not need a backend. If remote multiplayer is added, use a server-authoritative match service and deterministic seeds; local two-player remains device-local.

### Recommended web approach

**Recommendation:** Phaser + TypeScript, with HTML/CSS for text-heavy setup/settings and Phaser for organism/arena rendering. Deliver a small core catalog/search index first and lazy-load fighter detail shards. Host as static versioned files behind a CDN and service worker. Use IndexedDB for catalog cache/settings/saves. Add a backend only for accounts, telemetry with consent, centralized content updates, or true online multiplayer.

Expected properties: smooth 60-fps 2D gameplay on modern browsers; faster loads than Python/WASM when assets/data are sharded; good desktop/mobile-browser support; offline PWA after first cache; no Python installation. Browser compatibility should target current Chrome/Edge/Firefox/Safari and explicitly test iOS audio unlock, storage eviction, WebGL fallback, and reduced-motion preferences.

## 9. Responsive design requirements

The current virtual scaling preserves composition but is not responsive: all controls and text shrink together. Recommendation:

- Define layout tokens and breakpoints instead of literal coordinates.
- Landscape phone: compact setup panels, one-card-at-a-time fighter details, bottom action bar, 44–48 CSS-pixel touch targets, and collapsible evidence.
- Tablet/desktop: retain side-by-side catalog/detail and versus cards.
- Portrait: either support a stacked flow or explicitly require landscape during the arena; do not merely rotate without preserving safe areas.
- Respect notches/home indicators with safe-area insets and keep primary actions away from edges.
- Use dynamic type with tested wrapping and scroll containers; scientific names must never be truncated without an accessible full value.
- Keep Petri dish proportional to available space; scale cell radius and cap particle count based on performance while preserving visible density differences.
- Separate logical world units from pixels for fighter sizes, paths, effects, and HUD.
- Provide reduced motion, high contrast, mute, and platform accessibility labels outside canvas.
- Use texture/audio memory budgets, object pools, capped device pixel ratio, compressed assets, and a 30-fps fallback for low-power devices.
- Make hover-only previews available by focus/tap; current preset hover behavior has no touch equivalent until a card is selected.
- Add on-screen back navigation consistently; today Escape/controller handles some paths that have no visible Back button.

## 10. Testing and release readiness

### Existing coverage

**Confirmed.** The repository has 71 passing tests. They cover bacterial-name sanitization; catalog deduplication; SQLite round trips/profile normalization; MIBiG/BacDive classification and builder failure/retry behavior; search, sampling, opponent exclusion; environment, colony, arsenal, activity, resistance, deterministic variation, and breakdown arithmetic; missing-data flavor; procedural preview stability; morphology/flagella/environment presentation; viewport/input/transition/timeline behavior; settings/audio failure tolerance; one-player scaled navigation; and an end-to-end local two-player selection/back/touch/results/reset flow.

The suite passed on July 15, 2026 using Python 3.11: **71 passed in 5.31 seconds**. One warning reports Pygame’s use of deprecated `pkg_resources`.

### Missing or insufficient tests

- Complete one-player flow from home through results/rematch, including automated rival choices.
- Two-player permutations for both winners, tie, rematch, and every back path.
- Real rendered screenshots/golden images for all screens and environments.
- Phone/tablet aspect ratios, portrait behavior, notches, large text, and 44–48 px touch targets.
- Multi-touch, touch cancellation, drag outside slider, mobile virtual keyboard/search, app background/resume.
- Production DB integrity: schema/user version, row counts, required nonempty values, foreign keys, stable IDs, corrupt/old/new DB handling, and retained morphology fields.
- Startup and graceful fallback for every missing/corrupt image/audio/data asset.
- First-install and repeat-launch offline behavior.
- Save-game migration and missing/tombstoned fighter IDs (no battle save system exists yet).
- Browser matrix, PWA install/cache update, IndexedDB quota/eviction, audio unlock, WebGL/Canvas fallback.
- Android/iOS device performance, memory, thermal/battery use, interruptions, audio focus, and store build smoke tests.
- Accessibility via screen reader, keyboard-only flow, contrast measurement, focus order, and reduced-motion assertions.

### Release checklists

**Desktop:** clean allowlist build; pinned Python/Pygame; Windows/macOS/Linux smoke tests; icons/version/license/attributions; read-only catalog; writable settings path; missing asset/data errors; code signing/notarization where applicable; installer/uninstaller; 60-fps and memory baseline.

**Web:** production bundle and source-map policy; Brotli assets/data; CDN cache/version rules; service-worker update/rollback; browser/device matrix; first-load budget; offline test; audio gesture; accessibility audit; privacy/cookie policy; HTTPS and security headers.

**Android:** responsive device matrix; touch/back button; audio focus/headphones/calls; pause/resume/rotation; storage migration; signed AAB; target SDK/compliance; data safety form; content rating; licenses; internal test track; crash/performance monitoring with consent.

**iOS:** safe areas and orientation; audio session/interruptions; memory on older supported devices; TestFlight; signed archive/provisioning; privacy manifest/labels; export compliance; app review metadata; restore/update/offline tests.

## 11. Recommended roadmap

### Phase 1 — Immediate cleanup

- **Files:** `microbial_mayhem_main.py`, legacy root modules/assets, `README.md`, `requirements.txt`.
- **Changes:** document active/deprecated modules; remove duplicate `start_animation()` and caption call in a later code-change phase; identify unused constants/functions; define navigation diagram and content contract; pin supported Python/Pygame versions.
- **Dependencies:** none.
- **Risks:** accidentally deleting prototype assets still desired by the designer.
- **Completion:** active runtime allowlist is documented; no ambiguous duplicate/dead path remains; all 71+ tests pass.

### Phase 2 — Lightweight data packaging

- **Files:** `catalog_storage.py`, `bacterial_catalog.py`, `scripts/build_bacdive_catalog.py`, `catalog_deduplication.py`, `trait_inference.py`, `data/catalog/`, new schemas/manifests/validators.
- **Changes:** schema v2; retain normalized morphology/motility; trim verbose/non-runtime fields; add content version/checksums; choose curated core vs shards; deterministic validator/diff; release allowlist.
- **Dependencies:** source licensing/version policy and roster decision.
- **Risks:** stable-ID changes, educational detail loss, altered scoring from trait corrections.
- **Completion:** clean rebuild is reproducible; validator passes; old saves resolve through aliases; package contains no raw sources; core data meets an agreed size/load budget.

### Phase 3 — Responsive interface foundation

- **Files:** initially `microbial_mayhem_main.py`, `ui_systems.py`, `presentation.py`, `preview_models.py`; then shared TypeScript design tokens/components.
- **Changes:** extract `BattleSession`/navigation model; replace alias-heavy state; define breakpoints/safe areas/touch sizes; establish portrait/landscape policy; add accessibility semantics.
- **Dependencies:** target stack and design prototypes.
- **Risks:** visual regressions and dense scientific copy on small screens.
- **Completion:** every screen passes desktop, tablet, and phone layout tests at normal/large text, keyboard, and touch.

### Phase 4 — Web prototype

- **Files:** new TypeScript/Phaser client; ports of `scoring.py`, `presentation.py`, `preview_models.py`, `ui_systems.py`; catalog export tool.
- **Changes:** responsive setup UI, Phaser arena, data shards, IndexedDB, PWA caching, audio unlock.
- **Dependencies:** Node toolchain, Phaser, bundler, service worker, static host/CDN.
- **Risks:** rule drift, mobile Safari audio/storage, initial data size.
- **Completion:** full solo and local two-player flows run offline after first load on the supported browser matrix; scoring fixtures match Python exactly; performance/load budgets pass.

### Phase 5 — Mobile prototype

- **Files:** web client plus Capacitor project/native configuration.
- **Changes:** store wrapper, native persistence, lifecycle/audio focus, safe areas, icons/splash, signing, device QA. Run a short Godot spike only if Phaser/Capacitor fails agreed performance or platform criteria.
- **Dependencies:** Android Studio, Xcode/macOS, developer accounts, Capacitor plugins.
- **Risks:** native plugin churn, store policy, iOS audio/memory.
- **Completion:** installable signed internal Android and TestFlight builds complete both modes offline on representative low/mid/high devices.

### Phase 6 — Testing hardening

- **Files:** existing `tests/`, new cross-language fixtures, browser E2E, visual regression, catalog validators, device test plans.
- **Changes:** add missing flows, responsive/golden tests, database/save migrations, offline/update/error tests, accessibility and performance gates.
- **Dependencies:** CI browsers, device lab or cloud devices, representative catalogs.
- **Risks:** flaky animation screenshots and excessive fixture size.
- **Completion:** automated gates cover rules, navigation, data, saves, accessibility, offline/update, and performance with zero critical known defects.

### Phase 7 — Public release

- **Files:** version manifests, release notes, privacy/attribution/license documents, store/web metadata, deployment configuration.
- **Changes:** content freeze, signed catalog/client artifacts, CDN rollout, app-store submission, rollback plan, support/crash process.
- **Dependencies:** source-data and asset licensing confirmation, privacy decision, store approval.
- **Risks:** scientific content corrections, catalog/client mismatch, cache migration, review delays.
- **Completion:** desktop/web/Android/iOS artifacts pass their checklists; catalog checksum/version is visible; rollback is tested; public endpoints and store listings are live.

## Final recommendation

Preserve the Python version as the authoritative reference until cross-language parity is proven. Do not ship raw BacDive or MIBiG inputs. First correct the runtime content contract—especially the loss of BacDive cell shape and motility in SQLite schema v1—then extract session/scoring fixtures. Build a responsive Phaser/TypeScript PWA and package it with Capacitor for mobile. This gives the repository one maintainable web/mobile product while retaining the current game’s strongest qualities: transparent scoring, offline play, deterministic procedural art, local two-player support, and biologically grounded content.
