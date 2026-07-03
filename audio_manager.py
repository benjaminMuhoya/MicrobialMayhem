"""Phase-aware, fault-tolerant music and sound playback."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MusicTrack:
    path: str
    volume: float
    fade_ms: int = 420
    loop: bool = True


@dataclass(frozen=True)
class SoundCue:
    path: str
    volume: float


MUSIC_TRACKS = {
    "setup": MusicTrack("music/setup_theme.wav", .62, 360),
    "battle": MusicTrack("music/battle_theme.wav", .78, 460),
    "results": MusicTrack("music/results_theme.wav", .52, 520),
}

SOUND_CUES = {
    "click": SoundCue("sfx/click.wav", .55),
    "select": SoundCue("sfx/select.wav", .58),
    "attack": SoundCue("sfx/attack.wav", .55),
    "impact": SoundCue("sfx/impact.wav", .62),
    "ability": SoundCue("sfx/ability.wav", .58),
    "arsenal": SoundCue("sfx/arsenal.wav", .52),
    "clash": SoundCue("sfx/clash.wav", .48),
    "final_hit": SoundCue("sfx/final_hit.wav", .72),
    "victory": SoundCue("sfx/victory.wav", .68),
    "defeat": SoundCue("sfx/defeat.wav", .62),
}

# Layers are deliberately restrained so the music remains the foundation.
BATTLE_CUE_LAYERS = {
    "attack": (("attack", 1.0), ("impact", .52)),
    "counter": (("attack", .82), ("impact", .65)),
    "ability": (("ability", 1.0),),
    "environment": (("clash", .65),),
    "finish": (("final_hit", 1.0), ("impact", .42)),
}

RESULTS_ACCENT_DELAY_MS = 520


class AudioManager:
    """Own one music stream and a small bank of layered sound cues.

    ``requested_phase`` represents the soundtrack the game currently wants.
    Keeping that separate from ``current_phase`` lets mute and missing-device
    states recover without asking screens to replay navigation events.
    """

    def __init__(self, asset_dir: Path, settings, pygame_module=None) -> None:
        self.asset_dir = Path(asset_dir)
        self.settings = settings
        self.sounds: dict[str, object] = {}
        self.enabled = False
        self.mixer = None
        self.current_phase: str | None = None
        self.requested_phase: str | None = None
        self.pending_phase: str | None = None
        self.pending_start_ms = 0
        try:
            if pygame_module is None:
                import pygame as pygame_module
            self.mixer = pygame_module.mixer
            if not self.mixer.get_init():
                self.mixer.init()
            self.enabled = True
        except Exception:
            self.mixer = None
        self.register_defaults()

    def register_defaults(self) -> None:
        for cue, spec in SOUND_CUES.items():
            self.register(cue, spec.path)

    def register(self, cue: str, relative_path: str) -> bool:
        path = self.asset_dir / relative_path
        if not self.enabled or not path.exists():
            return False
        try:
            self.sounds[cue] = self.mixer.Sound(str(path))
            return True
        except Exception:
            return False

    def play(self, cue: str, volume_scale: float = 1.0) -> bool:
        """Play a registered effect once; retained as the simple public hook."""
        if not self.enabled or self.settings.muted or self.settings.sfx_volume <= 0 or cue not in self.sounds:
            return False
        try:
            spec = SOUND_CUES.get(cue, SoundCue("", 1.0))
            volume = self.settings.sfx_volume * spec.volume * volume_scale
            sound = self.sounds[cue]
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play()
            return True
        except Exception:
            return False

    def play_battle_cue(self, kind: str, *, arsenal_active: bool = False) -> int:
        """Play the balanced sound layer associated with a choreography cue."""
        layers = list(BATTLE_CUE_LAYERS.get(kind, ()))
        if kind == "ability" and arsenal_active:
            layers.append(("arsenal", .72))
        return sum(self.play(cue, scale) for cue, scale in layers)

    def set_phase(self, phase: str, now_ms: int = 0, *, accent: str | None = None) -> bool:
        """Request a soundtrack phase without restarting an unchanged track."""
        if phase not in MUSIC_TRACKS:
            raise ValueError(f"Unknown audio phase: {phase}")
        if self.requested_phase == phase and (self.current_phase == phase or self.pending_phase == phase):
            return False
        self.requested_phase = phase
        if not self.enabled or self.settings.muted or self.settings.music_volume <= 0:
            self.pending_phase = None
            self.current_phase = None
            return False

        delay_ms = RESULTS_ACCENT_DELAY_MS if accent else 0
        if accent:
            self.play(accent)
        if self.current_phase is None and self.pending_phase is None and delay_ms == 0:
            return self._start_phase(phase)

        fade_ms = MUSIC_TRACKS[phase].fade_ms if self.current_phase else 0
        if self.current_phase:
            try:
                self.mixer.music.fadeout(fade_ms)
            except Exception:
                try:
                    self.mixer.music.stop()
                except Exception:
                    pass
        self.current_phase = None
        self.pending_phase = phase
        self.pending_start_ms = int(now_ms) + max(fade_ms, delay_ms)
        return True

    def update(self, now_ms: int) -> bool:
        """Start a phase whose fade/accent delay has elapsed."""
        if not self.enabled or self.settings.muted or self.settings.music_volume <= 0 or self.pending_phase is None:
            return False
        if int(now_ms) < self.pending_start_ms:
            return False
        phase = self.pending_phase
        self.pending_phase = None
        return self._start_phase(phase)

    def _start_phase(self, phase: str) -> bool:
        spec = MUSIC_TRACKS[phase]
        path = self.asset_dir / spec.path
        if not self.enabled or self.settings.muted or self.settings.music_volume <= 0 or not path.exists():
            self.current_phase = None
            return False
        try:
            self.mixer.music.load(str(path))
            self._apply_music_volume(phase)
            loops = -1 if spec.loop else 0
            try:
                self.mixer.music.play(loops, fade_ms=min(240, spec.fade_ms))
            except TypeError:
                self.mixer.music.play(loops)
            self.current_phase = phase
            return True
        except Exception:
            self.current_phase = None
            return False

    def _apply_music_volume(self, phase: str | None = None) -> None:
        if not self.enabled:
            return
        phase = phase or self.current_phase or self.requested_phase
        multiplier = MUSIC_TRACKS[phase].volume if phase in MUSIC_TRACKS else 1.0
        volume = 0.0 if self.settings.muted else self.settings.music_volume * multiplier
        try:
            self.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        except Exception:
            pass

    def set_music_volume(self, volume: float) -> None:
        self.settings.music_volume = max(0.0, min(1.0, volume))
        if self.settings.music_volume <= 0:
            self.stop_music(clear_request=False)
            return
        self._apply_music_volume()
        if not self.settings.muted and self.requested_phase and self.current_phase is None:
            self.pending_phase = None
            self._start_phase(self.requested_phase)

    def apply_settings(self, now_ms: int = 0) -> None:
        """Apply mute/volume changes without losing the desired game phase."""
        if not self.enabled:
            return
        if self.settings.muted or self.settings.music_volume <= 0:
            self.stop_music(clear_request=False)
            if self.settings.muted:
                try:
                    self.mixer.stop()
                except Exception:
                    pass
            return
        self._apply_music_volume()
        if self.requested_phase and self.current_phase is None:
            self.pending_phase = None
            self._start_phase(self.requested_phase)

    def play_music(self, relative_path: str, loop=True) -> bool:
        """Compatibility hook for an explicitly supplied track path."""
        path = self.asset_dir / relative_path
        if not self.enabled or self.settings.muted or self.settings.music_volume <= 0 or not path.exists():
            return False
        try:
            self.mixer.music.load(str(path))
            self.mixer.music.set_volume(self.settings.music_volume)
            self.mixer.music.play(-1 if loop else 0)
            return True
        except Exception:
            return False

    def stop_music(self, *, clear_request: bool = True) -> None:
        if self.enabled:
            try:
                self.mixer.music.stop()
            except Exception:
                pass
        self.current_phase = None
        self.pending_phase = None
        if clear_request:
            self.requested_phase = None

    def shutdown(self) -> None:
        """Stop music and all effect channels before Pygame exits."""
        self.stop_music()
        if self.enabled:
            try:
                self.mixer.stop()
            except Exception:
                pass
