# Original and placeholder assets

The redesigned fighters and battle effects are currently drawn procedurally in
code, so no third-party game art is required. Future replaceable original assets
should be organized under:

- `fighters/` — per-fighter idle, attack, hit, victory, and defeat states
- `environments/` — arena backgrounds and ambient layers
- `effects/` — toxins, projectiles, shields, spores, and status effects
- `interface/` — icons, frames, and controls
- `audio/music/` — original synthesized setup, battle, and results themes
- `audio/sfx/` — original synthesized interface and battle cues

Every temporary file should include `placeholder` in its name until cleared for
production use.

The current audio files are generated entirely from simple waveforms and
deterministic noise by `scripts/generate_audio_assets.py`. They contain no
third-party recordings or copyrighted commercial music and can be regenerated
from source at any time.

The mobile/web build packages identical generated copies under
`web/public/audio/`. `web/app/game/feedback.ts` is the single playback and
lifecycle owner for these copies. No attribution is required; the files and
generator are original project assets.
