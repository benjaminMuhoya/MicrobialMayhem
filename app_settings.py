"""Persistent, validated player preferences."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_SETTINGS_PATH = Path.home() / ".microbial_mayhem" / "settings.json"


@dataclass
class AppSettings:
    reduced_motion: bool = False
    high_contrast: bool = False
    text_scale: float = 1.0
    music_volume: float = .45
    sfx_volume: float = .7
    muted: bool = False
    onboarding_complete: bool = False

    def normalized(self) -> "AppSettings":
        self.text_scale = max(.85, min(1.3, float(self.text_scale)))
        self.music_volume = max(0.0, min(1.0, float(self.music_volume)))
        self.sfx_volume = max(0.0, min(1.0, float(self.sfx_volume)))
        return self

    @classmethod
    def load(cls, path: Path = DEFAULT_SETTINGS_PATH) -> "AppSettings":
        try:
            raw = json.loads(path.read_text())
            allowed = cls.__dataclass_fields__
            return cls(**{key: value for key, value in raw.items() if key in allowed}).normalized()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return cls()

    def save(self, path: Path = DEFAULT_SETTINGS_PATH) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(self.normalized()), indent=2) + "\n")
            return True
        except OSError:
            return False
